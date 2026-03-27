#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import shutil


ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / ".git" / "hooks"
SOURCE = ROOT / "hooks" / "post-commit"
TARGET = HOOKS_DIR / "post-commit"


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, TARGET)
    os.chmod(TARGET, 0o755)
    print(f"installed {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
