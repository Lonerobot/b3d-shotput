"""
run_tests.py — launch Shotput unit tests inside Blender's Python environment.

Usage (PowerShell / cmd from repo root):
    python tests/run_tests.py

Or invoke Blender directly:
    & "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" `
        --background `
        --python tests/test_shotput.py

The script below wraps the Blender call so you can just run:
    python tests/run_tests.py [--blender PATH]
"""

import subprocess
import sys
import argparse
from pathlib import Path

DEFAULT_BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
TESTS_DIR = Path(__file__).resolve().parent
TEST_SCRIPT = TESTS_DIR / "test_shotput.py"


def main():
    parser = argparse.ArgumentParser(description="Run Shotput tests inside Blender")
    parser.add_argument(
        "--blender",
        default=DEFAULT_BLENDER,
        help="Path to the Blender executable (default: %(default)s)",
    )
    args = parser.parse_args()

    blender_exe = Path(args.blender)
    if not blender_exe.exists():
        print(f"ERROR: Blender not found at: {blender_exe}", file=sys.stderr)
        print("Pass the correct path with --blender, e.g.:", file=sys.stderr)
        print(f"  python tests/run_tests.py --blender \"C:/path/to/blender.exe\"", file=sys.stderr)
        sys.exit(1)

    if not TEST_SCRIPT.exists():
        print(f"ERROR: Test script not found: {TEST_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    cmd = [
        str(blender_exe),
        "--background",           # headless, no window
        "--python", str(TEST_SCRIPT),
    ]

    print("=" * 60)
    print("Shotput Test Runner")
    print("=" * 60)
    print(f"Blender : {blender_exe}")
    print(f"Script  : {TEST_SCRIPT}")
    print("=" * 60)
    print()

    proc = subprocess.run(cmd, cwd=str(TESTS_DIR.parent))

    print()
    print("=" * 60)
    if proc.returncode == 0:
        print("RESULT: ALL TESTS PASSED")
    else:
        print(f"RESULT: TESTS FAILED (exit code {proc.returncode})")
    print("=" * 60)

    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
