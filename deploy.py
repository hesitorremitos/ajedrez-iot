"""Upload files from build/ to an ESP32 over serial."""

import os
import sys
from pathlib import Path

from ampy.files import Files
from ampy.pyboard import Pyboard


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"


def ensure_remote_dir(fs: Files, remote_dir: str) -> None:
    if remote_dir in ("", "/"):
        return
    current = ""
    for part in remote_dir.strip("/").split("/"):
        current += "/" + part
        fs.mkdir(current, exists_okay=True)


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else os.getenv("ESP32_PORT")
    if not port:
        print("Usage: uv run deploy <PORT>", file=sys.stderr)
        print("Or set ESP32_PORT, e.g. COM5", file=sys.stderr)
        return 1

    if not BUILD_DIR.exists():
        print("Missing build/ directory. Run: uv run build", file=sys.stderr)
        return 1

    files_to_upload = sorted(p for p in BUILD_DIR.rglob("*") if p.is_file())
    if not files_to_upload:
        print("No files found in build/. Run: uv run build", file=sys.stderr)
        return 1

    print(f"Connecting to {port}")
    board = Pyboard(port)
    fs = Files(board)

    try:
        print(f"Uploading {len(files_to_upload)} files from build/")
        for local_path in files_to_upload:
            relative = local_path.relative_to(BUILD_DIR)
            remote_path = "/" + relative.as_posix()
            ensure_remote_dir(fs, remote_path.rsplit("/", 1)[0])
            fs.put(remote_path, local_path.read_bytes())
            print(f"- {relative.as_posix()} -> {remote_path}")
    finally:
        board.close()

    print("Deploy completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
