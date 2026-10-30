"""Audio transcription — converts Slack audio notes to text for the agent pipeline.

Default: mlx-whisper (on-device, Apple Silicon M-series, no API key needed)
Fallback: OpenAI-compatible Whisper API (Groq, OpenAI, or custom endpoint)
"""

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AUDIO_MIME_TYPES = {
    "audio/mp4", "audio/mpeg", "audio/ogg", "audio/webm",
    "audio/x-m4a", "audio/m4a", "audio/wav", "audio/aac",
    "video/mp4",  # Slack sometimes sends audio notes as video/mp4
}

_TRANSCRIPTION_API_KEY = os.getenv("TRANSCRIPTION_API_KEY") or os.getenv("OPENAI_API_KEY")
_TRANSCRIPTION_BASE_URL = os.getenv("TRANSCRIPTION_BASE_URL")
_TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")
_MLX_MODEL = os.getenv("MLX_WHISPER_MODEL", "mlx-community/whisper-base-mlx")


def _transcribe_mlx(audio_path: str) -> str:
    import mlx_whisper
    result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=_MLX_MODEL)
    return result.get("text", "").strip()


def _transcribe_api(audio_bytes: bytes, filename: str) -> str:
    from openai import OpenAI
    if not _TRANSCRIPTION_API_KEY:
        raise RuntimeError(
            "No transcription key found. Either install mlx-whisper (pip install mlx-whisper) "
            "or set TRANSCRIPTION_API_KEY in .env (Groq: console.groq.com — free tier)."
        )
    kwargs = {"api_key": _TRANSCRIPTION_API_KEY}
    if _TRANSCRIPTION_BASE_URL:
        kwargs["base_url"] = _TRANSCRIPTION_BASE_URL
    client = OpenAI(**kwargs)
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


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.m4a") -> str:
    """Transcribe raw audio bytes. Uses mlx-whisper if available, otherwise API."""
    suffix = Path(filename).suffix or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        try:
            return _transcribe_mlx(tmp_path)
        except ImportError:
            return _transcribe_api(audio_bytes, filename)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def is_audio_file(mimetype: str) -> bool:
    return mimetype in AUDIO_MIME_TYPES
