#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
KERNEL = json.loads((ROOT / "config" / "kernel.json").read_text(encoding="utf-8"))


def run(cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": cmd,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def assert_exists(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing {label}: {path}")


def main() -> int:
    errors: list[str] = []
    steps: list[dict] = []

    steps.append(run(["python3", "scripts/refresh_repo.py"], ROOT))
    steps.append(run(["python3", "scripts/sync_kernel_views.py"], ROOT))
    steps.append(run(["python3", "scripts/render_process_visual.py"], ROOT))

    singine_root = Path(PROJECT["dependencies"]["singine_root"]).expanduser()
    steps.append(
        run(
            ["python3", "-m", "singine.command", "wikipedia", "contrib", "collibra", "--json"],
            singine_root,
        )
    )

    for step in steps:
        if step["exit_code"] != 0:
            errors.append(
                f"command failed: {' '.join(step['command'])} (exit {step['exit_code']})"
            )

    assert_exists(ROOT / "content" / "markdown" / "Collibra.md", "canonical markdown", errors)
    assert_exists(ROOT / "content" / "org" / "Collibra.org", "org mirror", errors)
    assert_exists(ROOT / "content" / "logseq" / "pages" / "Collibra.md", "logseq mirror", errors)
    assert_exists(ROOT / "docs" / "plan.md", "plan", errors)
    assert_exists(ROOT / "docs" / "backlog.md", "backlog", errors)
    assert_exists(ROOT / "docs" / "roadmap.md", "roadmap", errors)
    assert_exists(ROOT / "docs" / "process.md", "process", errors)
    assert_exists(ROOT / "adrs" / "ADR-0001-maintainer-repository-location.md", "adr markdown", errors)
    assert_exists(ROOT / "adrs" / "ADR-0001-maintainer-repository-location.xml", "adr xml", errors)
    assert_exists(ROOT / "protocol" / "wikipedia-contrib-process.xml", "process protocol xml", errors)
    assert_exists(ROOT / "visuals" / "wikipedia-contrib-process.mmd", "process mermaid diagram", errors)
    assert_exists(ROOT / "graph" / "collibra-support.jsonld", "json-ld graph", errors)
    assert_exists(ROOT / "feeds" / "datatech-collibra.atom", "atom feed", errors)
    assert_exists(ROOT / "feeds" / "datatech-collibra.rss", "rss feed", errors)
    assert_exists(ROOT / "references" / "zotero" / "Collibra.json", "zotero csl json", errors)
    assert_exists(ROOT / "references" / "zotero" / "Collibra.bib", "bibtex export", errors)
    assert_exists(ROOT / "references" / "zotero" / "Collibra.rdf", "reference rdf export", errors)
    assert_exists(ROOT / "references" / "zotero" / "Collibra.wikipedia.txt", "wikipedia citation export", errors)
    assert_exists(ROOT / "xml" / "wikipedia" / "collibra" / "article.xml", "modular wikipedia xml article", errors)
    assert_exists(ROOT / "xml" / "wikipedia" / "collibra" / "apparatus" / "discussion-points.xml", "discussion points appendix", errors)
    assert_exists(ROOT / "build" / "wikipedia" / "Collibra.wikitext", "wikipedia draft", errors)
    assert_exists(ROOT / "build" / "docbook" / "Collibra.xml", "docbook xml", errors)
    assert_exists(ROOT / "build" / "rdf" / "Collibra.rdf", "rdf xml", errors)
    assert_exists(ROOT / "notifications" / "pending-update.json", "notification manifest", errors)
    assert_exists(ROOT / "site" / "src" / "xml" / "en" / "layout.xml", "site layout", errors)
    assert_exists(ROOT / "site" / "src" / "xml" / "en" / "index.xml", "site index", errors)
    assert_exists(ROOT / "site" / "src" / "xml" / "en" / "docs" / "process.xml", "site process page", errors)

    kernel_pages = Path(KERNEL["kernel_pages_dir"]).expanduser()
    assert_exists(kernel_pages / "Wikipedia___Collibra.md", "kernel Collibra page", errors)
    assert_exists(kernel_pages / "Wikipedia___Plan.md", "kernel plan page", errors)
    assert_exists(kernel_pages / "Wikipedia___Backlog.md", "kernel backlog page", errors)
    assert_exists(kernel_pages / "Wikipedia___Roadmap.md", "kernel roadmap page", errors)

    wrapper_output = steps[-1]["stdout"]
    if wrapper_output:
        try:
            parsed = json.loads(wrapper_output)
            if not parsed.get("ok"):
                errors.append("wrapper command returned ok=false")
        except json.JSONDecodeError:
            errors.append("wrapper command did not return valid JSON")
    else:
        errors.append("wrapper command returned no stdout")

    payload = {
        "ok": not errors,
        "repo_root": str(ROOT),
        "errors": errors,
        "steps": steps,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
