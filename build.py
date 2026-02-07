"""Compile lib/*.py files to build/lib/*.mpy."""

import subprocess
import sys
import shutil
from pathlib import Path

try:
    import mpy_cross
except ImportError:  # pragma: no cover
    mpy_cross = None


ROOT = Path(__file__).resolve().parent
LIB_DIR = ROOT / "lib"
OUT_DIR = ROOT / "build" / "lib"


def main() -> int:
    if mpy_cross is None:
        print("Missing dependency: mpy-cross", file=sys.stderr)
        print("Run: uv sync --group dev", file=sys.stderr)
        return 1

    if not LIB_DIR.exists():
        print(f"Missing directory: {LIB_DIR}", file=sys.stderr)
        return 1

    source_files = sorted(
        path for path in LIB_DIR.rglob("*.py") if "__pycache__" not in path.parts
    )
    if not source_files:
        print("No Python files found in lib/")
        return 0

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    print(f"Compiling {len(source_files)} files from lib/ into build/lib/")
    for src in source_files:
        relative = src.relative_to(LIB_DIR).with_suffix(".mpy")
        out = OUT_DIR / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        result = mpy_cross.run(
            str(src),
            "-o",
            str(out),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = result.communicate()
        if result.returncode != 0:
            if stdout:
                print(stdout.rstrip())
            if stderr:
                print(stderr.rstrip(), file=sys.stderr)
            print(f"Failed compiling {src}", file=sys.stderr)
            return 1
        print(f"- {src.relative_to(ROOT)} -> {out.relative_to(ROOT)}")

    print("Build completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
