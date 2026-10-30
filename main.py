"""Compatibility entry point; the managed API workflow uses the artifact entry point."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).parent / "artifacts/api-server/main.py"), run_name="__main__")
