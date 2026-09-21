"""Audio transcription — converts Slack audio notes to text for the agent pipeline."""

import os
import tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AUDIO_MIME_TYPES = {
    "audio/mp4", "audio/mpeg", "audio/ogg", "audio/webm",
    "audio/x-m4a", "audio/m4a", "audio/wav", "audio/aac",
    "video/mp4",  # Slack sometimes sends audio notes as video/mp4
}

_TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "openai")
_TRANSCRIPTION_API_KEY = os.getenv("TRANSCRIPTION_API_KEY") or os.getenv("OPENAI_API_KEY")
_TRANSCRIPTION_BASE_URL = os.getenv("TRANSCRIPTION_BASE_URL")  # None = use default OpenAI endpoint
_TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")


def _get_transcription_client() -> OpenAI:
    if not _TRANSCRIPTION_API_KEY:
        raise RuntimeError(
            "No transcription API key found. Set TRANSCRIPTION_API_KEY (or OPENAI_API_KEY) in .env.\n"
            "Options: OpenAI (https://platform.openai.com), Groq (https://console.groq.com)"
        )
    kwargs = {"api_key": _TRANSCRIPTION_API_KEY}
    if _TRANSCRIPTION_BASE_URL:
        kwargs["base_url"] = _TRANSCRIPTION_BASE_URL
    return OpenAI(**kwargs)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.m4a") -> str:
    """Transcribe raw audio bytes to text using the configured Whisper endpoint."""
    client = _get_transcription_client()
    suffix = Path(filename).suffix or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model=_TRANSCRIPTION_MODEL,
                file=(filename, f),
                response_format="text",
            )
        return str(result).strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def is_audio_file(mimetype: str) -> bool:
    return mimetype in AUDIO_MIME_TYPES
