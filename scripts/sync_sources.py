#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
CANONICAL = ROOT / CONFIG["content"]["canonical_markdown"]
ORG_PATH = ROOT / CONFIG["content"]["org_export"]
LOGSEQ_PATH = ROOT / CONFIG["content"]["logseq_export"]


def markdown_to_org(lines: list[str]) -> str:
    converted: list[str] = [
        "#+TITLE: Collibra",
        "#+AUTHOR: datatech-wiki-kg",
        "",
        "# generated from content/markdown/Collibra.md",
        "",
    ]
    for line in lines:
        if line.startswith("### "):
            converted.append("*** " + line[4:])
        elif line.startswith("## "):
            converted.append("** " + line[3:])
        elif line.startswith("# "):
            converted.append("* " + line[2:])
        else:
            converted.append(line)
    return "\n".join(converted).rstrip() + "\n"


def markdown_to_logseq(lines: list[str]) -> str:
    converted: list[str] = [
        "title:: Collibra",
        "tags:: wikipedia, datatech, collibra",
        "",
        "- generated from content/markdown/Collibra.md",
    ]
    for line in lines:
        if line.startswith("# "):
            converted.append(f"- {line[2:]}")
        elif line.startswith("## "):
            converted.append(f"  - {line[3:]}")
        elif line.startswith("### "):
            converted.append(f"    - {line[4:]}")
        elif line.startswith("- "):
            converted.append(f"    - {line[2:]}")
        elif line.strip():
            converted.append(f"    - {line}")
        else:
            converted.append("")
    return "\n".join(converted).rstrip() + "\n"


def main() -> int:
    lines = CANONICAL.read_text(encoding="utf-8").splitlines()
    ORG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOGSEQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    ORG_PATH.write_text(markdown_to_org(lines), encoding="utf-8")
    LOGSEQ_PATH.write_text(markdown_to_logseq(lines), encoding="utf-8")
    print(f"wrote {ORG_PATH}")
    print(f"wrote {LOGSEQ_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
