#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES_JSON = ROOT / "references" / "zotero" / "Collibra.json"
BIBTEX_PATH = ROOT / "references" / "zotero" / "Collibra.bib"
WIKI_REFS_PATH = ROOT / "references" / "zotero" / "Collibra.wikipedia.txt"
RDF_PATH = ROOT / "references" / "zotero" / "Collibra.rdf"


def load_entries() -> list[dict]:
    return json.loads(REFERENCES_JSON.read_text(encoding="utf-8"))


def issued_date(entry: dict) -> tuple[str, str, str]:
    parts = entry.get("issued", {}).get("date-parts", [[]])[0]
    year = str(parts[0]) if len(parts) > 0 else ""
    month = str(parts[1]) if len(parts) > 1 else ""
    day = str(parts[2]) if len(parts) > 2 else ""
    return year, month, day


def accessed_date(entry: dict) -> tuple[str, str, str]:
    parts = entry.get("accessed", {}).get("date-parts", [[]])[0]
    year = str(parts[0]) if len(parts) > 0 else ""
    month = str(parts[1]) if len(parts) > 1 else ""
    day = str(parts[2]) if len(parts) > 2 else ""
    return year, month, day


def bibtex_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def render_bibtex(entries: list[dict]) -> str:
    blocks: list[str] = []
    for entry in entries:
        year, month, day = issued_date(entry)
        access_year, access_month, access_day = accessed_date(entry)
        fields = [
            f"  title = {{{bibtex_escape(entry['title'])}}}",
            f"  url = {{{entry['URL']}}}",
            f"  year = {{{year}}}",
        ]
        if month:
            fields.append(f"  month = {{{month}}}")
        if day:
            fields.append(f"  day = {{{day}}}")
        if entry.get("container-title"):
            fields.append(f"  howpublished = {{{bibtex_escape(entry['container-title'])}}}")
        if access_year:
            fields.append(
                f"  urldate = {{{access_year}-{access_month.zfill(2)}-{access_day.zfill(2)}}}"
            )
        if entry.get("note"):
            fields.append(f"  note = {{{bibtex_escape(entry['note'])}}}")
        blocks.append("@online{{{id},\n{fields}\n}}".format(id=entry["id"], fields=",\n".join(fields)))
    return "\n\n".join(blocks) + "\n"


def render_wikipedia_templates(entries: list[dict]) -> str:
    lines: list[str] = []
    for entry in entries:
        year, month, day = issued_date(entry)
        access_year, access_month, access_day = accessed_date(entry)
        cite = (
            "{{cite web"
            f"|url={entry['URL']}"
            f"|title={entry['title']}"
            f"|website={entry.get('container-title', '')}"
        )
        if year:
            date = year
            if month:
                date += f"-{month.zfill(2)}"
            if day:
                date += f"-{day.zfill(2)}"
            cite += f"|date={date}"
        if access_year:
            cite += f"|access-date={access_year}-{access_month.zfill(2)}-{access_day.zfill(2)}"
        cite += "}}"
        lines.append(f"* {entry['id']}: <ref>{cite}</ref>")
    return "\n".join(lines) + "\n"


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_rdf(entries: list[dict]) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/">',
    ]
    for entry in entries:
        parts.extend(
            [
                f'  <rdf:Description rdf:about="{xml_escape(entry["URL"])}">',
                f'    <dc:identifier>{xml_escape(entry["id"])}</dc:identifier>',
                f'    <dc:title>{xml_escape(entry["title"])}</dc:title>',
                f'    <dc:source>{xml_escape(entry.get("container-title", ""))}</dc:source>',
                f'    <dc:type>{xml_escape(entry.get("type", "webpage"))}</dc:type>',
                f'    <dc:relation>{xml_escape(entry["URL"])}</dc:relation>',
                "  </rdf:Description>",
            ]
        )
    parts.append("</rdf:RDF>")
    return "\n".join(parts) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    entries = load_entries()
    write(BIBTEX_PATH, render_bibtex(entries))
    write(WIKI_REFS_PATH, render_wikipedia_templates(entries))
    write(RDF_PATH, render_rdf(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
