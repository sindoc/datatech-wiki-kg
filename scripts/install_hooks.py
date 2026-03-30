#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SINGINE_ROOT = Path("/Users/skh/ws/git/github/sindoc/singine")


def main() -> int:
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SINGINE_ROOT}:{current_pythonpath}" if current_pythonpath else str(SINGINE_ROOT)
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "singine.command",
            "git",
            "hooks",
            "install",
            "datatech-wiki-kg",
        ],
        cwd=SINGINE_ROOT,
        env=env,
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
