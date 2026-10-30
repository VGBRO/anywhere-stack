"""Google Meet transcript connector for the Teamwork Graph.

Two ingestion modes:
  - Local directory:  scans a folder for .vtt or .txt transcript files
  - Google Drive:     fetches transcript files from a Drive folder via REST API v3
                      (requires GOOGLE_ACCESS_TOKEN env var or access_token kwarg)

Produced objects:  meeting_transcript_raw
Extraction behavior:  meeting_transcript_extractor  (fires on meeting_transcript_raw)
Epistemic state: "observed" — meetings are structured, high-signal sources.

Config in .teamwork_config.json:
  {
    "meet_transcripts_dir": "/path/to/local/vtt-folder",
    "drive_folder_id": "1AbC...",   // optional, requires GOOGLE_ACCESS_TOKEN
    "since_hours": 24
  }
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from activegraph.behaviors.decorators import behavior  # type: ignore


# ── VTT / plain-text parsing ──────────────────────────────────────────────────

def _parse_vtt(text: str) -> str:
    """Convert WebVTT to plain text. Handles Google Meet <v Speaker>text format."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        # Timestamp cues: "00:01:23.456 --> 00:01:27.000"
        if re.match(r'^\d{2}:\d{2}:\d{2}', line) and "-->" in line:
            continue
        # Bare cue ID (all-digit line)
        if re.match(r'^\d+$', line):
            continue
        # Google Meet format: "<v Speaker Name>text</v>"
        if line.startswith("<v ") and ">" in line:
            rest = line[3:]
            speaker, _, text_part = rest.partition(">")
            text_part = re.sub(r"</v>", "", text_part).strip()
            lines.append(f"{speaker.strip()}: {text_part}")
        else:
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if clean:
                lines.append(clean)
    return "\n".join(lines)


def _parse_transcript(path: Path) -> str:
    """Parse .vtt or .txt transcript file to plain text."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".vtt":
        return _parse_vtt(text)
    return text.strip()


# ── Connector ─────────────────────────────────────────────────────────────────

class GoogleMeetConnector:
    """Ingest Google Meet transcripts into the Teamwork Graph.

    Args:
        project_root:    Path to project repo (dedup file + run log).
        graph:           ActiveGraph Graph instance.
        transcripts_dir: Local directory with .vtt / .txt files.
        drive_folder_id: Google Drive folder ID to sweep via REST API v3.
        access_token:    Google OAuth2 access token (or GOOGLE_ACCESS_TOKEN env).
    """

    def __init__(
        self,
        project_root: str,
        graph,
        transcripts_dir: Optional[str] = None,
        drive_folder_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self._root = project_root
        self._graph = graph
        self._transcripts_dir = Path(transcripts_dir) if transcripts_dir else None
        self._drive_folder_id = drive_folder_id
        self._access_token = access_token or os.getenv("GOOGLE_ACCESS_TOKEN", "")
        self._dedup_file = Path(project_root) / ".meet_ingested.json"
        self._ingested: dict[str, bool] = {}
        if self._dedup_file.exists():
            try:
                self._ingested = json.loads(self._dedup_file.read_text())
            except Exception:
                pass

    def _save_dedup(self) -> None:
        self._dedup_file.write_text(json.dumps(self._ingested, indent=2))

    def ingest_transcript(self, path: Path, source_url: str = "") -> bool:
        """Parse and add one transcript as a meeting_transcript_raw object.

        Returns True if newly ingested, False if already seen or empty.
        """
        key = source_url or str(path)
        if key in self._ingested:
            return False

        try:
            plain_text = _parse_transcript(path)
        except Exception as exc:
            from anywhere.state.canonical import append_event
            append_event(self._root, {
                "type":   "meet.ingest.error",
                "source": key,
                "error":  str(exc),
            })
            return False

        if not plain_text.strip():
            return False

        filename = path.name
        # Extract meeting date from filename if present (YYYY-MM-DD pattern)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        meeting_date = date_match.group(1) if date_match else ""

        obj_id = f"meet#{abs(hash(key)) % 100_000_000:08d}"
        self._graph.add_object(
            "meeting_transcript_raw",
            data={
                "id":           obj_id,
                "filename":     filename,
                "meeting_date": meeting_date,
                "source":       key,
                "project_root": self._root,
                "plain_text":   plain_text[:8000],
            },
        )

        self._ingested[key] = True
        self._save_dedup()
        return True

    def _sweep_local(self, since_iso: Optional[str] = None) -> int:
        if not self._transcripts_dir or not self._transcripts_dir.exists():
            return 0
        ingested = 0
        for ext in ("*.vtt", "*.txt"):
            for f in sorted(self._transcripts_dir.glob(ext)):
                if since_iso:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime.isoformat() < since_iso:
                        continue
                if self.ingest_transcript(f):
                    ingested += 1
        return ingested

    def _sweep_drive(self, since_iso: Optional[str] = None) -> int:
        """Fetch new transcript files from a Google Drive folder via REST API v3."""
        if not self._drive_folder_id or not self._access_token:
            return 0
        try:
            import urllib.request
            import urllib.parse

            q = (
                f"'{self._drive_folder_id}' in parents"
                f" and mimeType != 'application/vnd.google-apps.folder'"
                f" and trashed = false"
            )
            if since_iso:
                q += f" and modifiedTime > '{since_iso}'"

            params = urllib.parse.urlencode({
                "q":        q,
                "fields":   "files(id,name,mimeType,webViewLink,modifiedTime)",
                "pageSize": "100",
            })
            list_url = f"https://www.googleapis.com/drive/v3/files?{params}"
            req = urllib.request.Request(
                list_url,
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                items = json.loads(resp.read().decode()).get("files", [])

            ingested = 0
            for item in items:
                file_id  = item["id"]
                filename = item["name"]
                view_url = item.get("webViewLink", f"https://drive.google.com/file/d/{file_id}")

                if view_url in self._ingested:
                    continue

                # Download file content
                dl_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                dl_req = urllib.request.Request(
                    dl_url,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                with urllib.request.urlopen(dl_req, timeout=30) as resp:
                    content = resp.read().decode("utf-8", errors="replace")

                suffix = Path(filename).suffix.lower() or ".txt"
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, mode="w", delete=False, encoding="utf-8"
                ) as tmp:
                    tmp.write(content)
                    tmp_path = Path(tmp.name)

                try:
                    if self.ingest_transcript(tmp_path, source_url=view_url):
                        ingested += 1
                finally:
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass

            return ingested

        except Exception as exc:
            from anywhere.state.canonical import append_event
            append_event(self._root, {
                "type":  "meet.drive.error",
                "error": str(exc),
            })
            return 0

    def sweep(self, since_iso: Optional[str] = None) -> dict:
        """Ingest all new transcripts from configured sources.

        Returns: {"ingested": int}
        """
        n = self._sweep_local(since_iso) + self._sweep_drive(since_iso)
        return {"ingested": n}


# ── Extraction behavior ───────────────────────────────────────────────────────

@behavior(on=["object.created"], where={"object.type": "meeting_transcript_raw"})
def meeting_transcript_extractor(event, graph, ctx):
    """Extract teamwork entities from a meeting transcript.

    Meetings are structured, high-signal sources → epistemic_state = "observed".
    Uses the same extraction schema and entity types as slack_thread_extractor.
    """
    from anywhere.connectors.slack import _call_extractor, _write_entities
    from anywhere.state.canonical import append_event

    data = event.payload.get("object", {}).get("data", {})
    plain_text  = data.get("plain_text", "")
    source      = data.get("source", "")
    project_root = data.get("project_root", "")
    meeting_date = data.get("meeting_date", "")
    filename    = data.get("filename", "")

    if not plain_text.strip():
        return

    date_hint = f" (meeting date: {meeting_date})" if meeting_date else ""
    source_label = f"meet:{filename or source}"
    prompt = (
        f"Extract teamwork entities from this meeting transcript{date_hint}.\n\n"
        f"{plain_text[:6000]}"
    )

    extraction = _call_extractor(prompt, source_label=source_label)
    if not extraction.get("ingest_worthy", False):
        append_event(project_root, {
            "type":      "behavior.failed",
            "behavior":  "meeting_transcript_extractor",
            "reason":    "extraction_empty",
            "source":    source,
        })
        return

    written = _write_entities(
        extraction,
        source_url=source,
        graph=graph,
        project_root=project_root,
        base_epistemic_state="observed",
        ctx=ctx,
    )

    if sum(written.values()) == 0:
        append_event(project_root, {
            "type":      "behavior.failed",
            "behavior":  "meeting_transcript_extractor",
            "reason":    "extraction_empty",
            "source":    source,
        })
