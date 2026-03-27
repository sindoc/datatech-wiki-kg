#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL = json.loads((ROOT / "config" / "kernel.json").read_text(encoding="utf-8"))
PAGES_DIR = Path(KERNEL["kernel_pages_dir"]).expanduser()
NAMESPACE = KERNEL["kernel_namespace"]

SOURCE_MAP = {
    ROOT / "content" / "markdown" / "Collibra.md": f"{NAMESPACE}___Collibra.md",
    ROOT / "docs" / "plan.md": f"{NAMESPACE}___Plan.md",
    ROOT / "docs" / "backlog.md": f"{NAMESPACE}___Backlog.md",
    ROOT / "docs" / "roadmap.md": f"{NAMESPACE}___Roadmap.md",
}


def wrap_logseq(title: str, body: str, tags: str) -> str:
    return "\n".join(
        [
            f"title:: {title}",
            f"tags:: {tags}",
            "",
            body.rstrip(),
            "",
        ]
    )


def main() -> int:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for src, dest_name in SOURCE_MAP.items():
        title = dest_name.removesuffix(".md").replace("___", "/")
        body = src.read_text(encoding="utf-8")
        wrapped = wrap_logseq(title, body, "wikipedia, datatech, collibra")
        dest = PAGES_DIR / dest_name
        dest.write_text(wrapped, encoding="utf-8")
        print(f"wrote {dest}")
    mirror = ROOT / "content" / "logseq" / "pages" / f"{NAMESPACE}___Index.md"
    mirror.write_text(
        wrap_logseq(
            f"{NAMESPACE}/Index",
            "- [[Wikipedia/Collibra]]\n- [[Wikipedia/Plan]]\n- [[Wikipedia/Backlog]]\n- [[Wikipedia/Roadmap]]",
            "wikipedia, datatech"
        ),
        encoding="utf-8",
    )
    print(f"wrote {mirror}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
