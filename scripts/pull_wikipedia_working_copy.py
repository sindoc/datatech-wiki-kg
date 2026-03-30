#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INGEST_ROOT = ROOT / "data" / "wikipedia-ingest"
BUILD_ROOT = ROOT / "build" / "wikipedia"
SECTION_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote live Wikipedia snapshots into local working-copy files."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing working copies if they already exist.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return
    path.write_text(text, encoding="utf-8")


def section_map(wikitext: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(wikitext))
    if not matches:
        return {"Lead": wikitext.strip()}

    sections: dict[str, str] = {}
    lead = wikitext[: matches[0].start()].strip()
    if lead:
        sections["Lead"] = lead

    for index, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(wikitext)
        sections[title] = wikitext[start:end].strip()
    return sections


def summarize_section_diffs(local_text: str, live_text: str) -> list[str]:
    local_sections = section_map(local_text)
    live_sections = section_map(live_text)
    names = sorted(set(local_sections) | set(live_sections))
    lines: list[str] = []
    for name in names:
        if name not in local_sections:
            lines.append(f"- `{name}` exists only in live article")
            continue
        if name not in live_sections:
            lines.append(f"- `{name}` exists only in local generated draft")
            continue
        if local_sections[name] == live_sections[name]:
            lines.append(f"- `{name}` matches")
        else:
            local_len = len(local_sections[name].splitlines())
            live_len = len(live_sections[name].splitlines())
            lines.append(
                f"- `{name}` differs: local lines={local_len}, live lines={live_len}"
            )
    return lines


def unified_diff(local_path: Path, local_text: str, live_label: str, live_text: str) -> str:
    diff = difflib.unified_diff(
        local_text.splitlines(),
        live_text.splitlines(),
        fromfile=str(local_path),
        tofile=live_label,
        lineterm="",
    )
    return "\n".join(diff) + ("\n" if local_text != live_text else "")


def main() -> int:
    args = parse_args()

    local_article = BUILD_ROOT / "Collibra.wikitext"
    live_article = INGEST_ROOT / "collibra" / "latest.wikitext"
    local_template = BUILD_ROOT / "templates" / "Template-Data-technology.wikitext"
    live_template = INGEST_ROOT / "template-data" / "latest.wikitext"

    if not live_article.exists() or not live_template.exists():
        raise SystemExit("live ingest artifacts missing; run make wiki-ingest first")

    local_article_text = read_text(local_article)
    live_article_text = read_text(live_article)
    local_template_text = read_text(local_template)
    live_template_text = read_text(live_template)

    write_text(BUILD_ROOT / "live" / "Collibra.current.wikitext", live_article_text, force=True)
    write_text(BUILD_ROOT / "live" / "Template-Data.current.wikitext", live_template_text, force=True)
    write_text(BUILD_ROOT / "working" / "Collibra.working.wikitext", live_article_text, force=args.force)
    write_text(BUILD_ROOT / "working" / "Template-Data.working.wikitext", live_template_text, force=args.force)

    article_diff = unified_diff(local_article, local_article_text, "live:Collibra", live_article_text)
    template_diff = unified_diff(local_template, local_template_text, "live:Template:Data", live_template_text)
    write_text(BUILD_ROOT / "working" / "Collibra.generated-vs-live.diff", article_diff, force=True)
    write_text(BUILD_ROOT / "working" / "Template-Data.generated-vs-live.diff", template_diff, force=True)

    report_lines = [
        "# Wikipedia Pull Report",
        "",
        "## Purpose",
        "- Promote the current live Wikipedia article and template into local editable working copies.",
        "- Keep the generated draft next to the pulled live baseline so new edits can be made locally.",
        "",
        "## Files",
        "- Live article snapshot: `build/wikipedia/live/Collibra.current.wikitext`",
        "- Live template snapshot: `build/wikipedia/live/Template-Data.current.wikitext`",
        "- Editable article working copy: `build/wikipedia/working/Collibra.working.wikitext`",
        "- Editable template working copy: `build/wikipedia/working/Template-Data.working.wikitext`",
        "- Draft-vs-live article diff: `build/wikipedia/working/Collibra.generated-vs-live.diff`",
        "- Draft-vs-live template diff: `build/wikipedia/working/Template-Data.generated-vs-live.diff`",
        "",
        "## Article section comparison",
    ]
    report_lines.extend(summarize_section_diffs(local_article_text, live_article_text))
    report_lines.extend(
        [
            "",
            "## Template comparison",
            "- Review `build/wikipedia/working/Template-Data.generated-vs-live.diff` for line-level differences.",
            "",
            "## Working rule",
            "- Treat `build/wikipedia/working/*.working.wikitext` as the pulled on-wiki baseline for manual reconciliation.",
            "- Treat `build/wikipedia/Collibra.wikitext` and `build/wikipedia/templates/Template-Data-technology.wikitext` as the generated local draft outputs.",
            "- After reconciling changes, update the canonical source or XML/navbox source rather than only editing generated files.",
            "",
        ]
    )
    write_text(BUILD_ROOT / "working" / "pull-report.md", "\n".join(report_lines), force=True)

    print(f"wrote {BUILD_ROOT / 'live' / 'Collibra.current.wikitext'}")
    print(f"wrote {BUILD_ROOT / 'live' / 'Template-Data.current.wikitext'}")
    print(f"wrote {BUILD_ROOT / 'working' / 'Collibra.working.wikitext'}")
    print(f"wrote {BUILD_ROOT / 'working' / 'Template-Data.working.wikitext'}")
    print(f"wrote {BUILD_ROOT / 'working' / 'pull-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
