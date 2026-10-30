"""File system tools — read, write, list files within a project directory."""

from pathlib import Path


def _safe_path(base: str, rel_path: str) -> Path:
    base_resolved = Path(base).resolve()
    target = (base_resolved / rel_path).resolve()
    if not str(target).startswith(str(base_resolved)):
        raise ValueError(f"Path '{rel_path}' escapes project directory")
    return target


def read_file(base: str, path: str) -> str:
    try:
        p = _safe_path(base, path)
    except ValueError as e:
        return f"Error: {e}"
    if not p.exists():
        return f"File not found: {path}"
    return p.read_text(errors="replace")


def write_file(base: str, path: str, content: str) -> str:
    try:
        p = _safe_path(base, path)
    except ValueError as e:
        return f"Error: {e}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written: {path} ({len(content)} chars)"


def list_files(base: str, directory: str = ".") -> str:
    try:
        p = _safe_path(base, directory)
    except ValueError as e:
        return f"Error: {e}"
    if not p.exists():
        return f"Directory not found: {directory}"
    entries = []
    for f in sorted(p.rglob("*")):
        if f.is_file() and not any(part.startswith(".") for part in f.relative_to(Path(base)).parts):
            entries.append(str(f.relative_to(Path(base))))
    return "\n".join(entries[:100]) if entries else "No files found."
