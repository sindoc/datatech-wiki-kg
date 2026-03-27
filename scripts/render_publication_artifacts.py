#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
CANONICAL = ROOT / CONFIG["content"]["canonical_markdown"]
WIKITEXT_PATH = ROOT / CONFIG["publication"]["wikipedia_draft"]
MODULAR_XML_PATH = ROOT / CONFIG["publication"]["wikipedia_modular_xml"]
DOCBOOK_PATH = ROOT / CONFIG["publication"]["docbook_xml"]
RDF_PATH = ROOT / CONFIG["publication"]["rdf_xml"]
REFERENCES_JSON = ROOT / CONFIG["references"]["csl_json_export"]
TIMELINE_JSON = ROOT / CONFIG["topic_timeline"]["collibra"]
MEDIA_JSON = ROOT / CONFIG["media_model"]["collibra"]

SOURCE_WITH_TITLE = re.compile(r'^- (?P<label>.+?), "(?P<title>.+?)": (?P<url>https?://\S+)$')
SOURCE_SIMPLE = re.compile(r"^- (?P<label>.+?): (?P<url>https?://\S+)$")
INLINE_REF_RE = re.compile(r"\[\[ref:(\d+(?:\s*,\s*\d+)*)\]\]")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_lines() -> list[str]:
    return CANONICAL.read_text(encoding="utf-8").splitlines()


def parse_source_catalog(lines: list[str]) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    in_catalog = False
    for line in lines:
        if line == "## Source candidates as of 2026-03-27":
            in_catalog = True
            continue
        if in_catalog and line.startswith("## ") and line != "## Source candidates as of 2026-03-27":
            break
        if not in_catalog or not line.startswith("- "):
            continue
        match = SOURCE_WITH_TITLE.match(line)
        if match:
            entry = match.groupdict()
            catalog[entry["url"]] = {
                "label": entry["label"],
                "title": entry["title"],
                "url": entry["url"],
            }
            continue
        match = SOURCE_SIMPLE.match(line)
        if match:
            entry = match.groupdict()
            catalog[entry["url"]] = {
                "label": entry["label"],
                "title": entry["label"],
                "url": entry["url"],
            }
    return catalog


def load_reference_catalog() -> dict[str, dict[str, str]]:
    if not REFERENCES_JSON.exists():
        return {}
    entries = json.loads(REFERENCES_JSON.read_text(encoding="utf-8"))
    catalog: dict[str, dict[str, str]] = {}
    for entry in entries:
        url = entry.get("URL", "")
        if not url:
            continue
        container = entry.get("container-title", "")
        issued = entry.get("issued", {}).get("date-parts", [[]])[0]
        label = container or entry.get("title", url)
        if issued:
            label = f"{label}, {issued[0]}"
        catalog[url] = {
            "label": label,
            "title": entry.get("title", url),
            "url": url,
            "website": container,
        }
    return catalog


def load_timeline() -> dict[str, object]:
    if not TIMELINE_JSON.exists():
        return {"events": []}
    return json.loads(TIMELINE_JSON.read_text(encoding="utf-8"))


def load_media_model() -> dict[str, object]:
    if not MEDIA_JSON.exists():
        return {"assets": []}
    return json.loads(MEDIA_JSON.read_text(encoding="utf-8"))


def parse_candidate_sections(lines: list[str]) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    in_draft = False
    seen_first_heading = False
    in_company_card = False
    current: dict[str, object] | None = None
    mode = "body"

    def ensure_current() -> dict[str, object]:
        nonlocal current
        if current is None:
            current = {"title": "Lead", "paragraphs": [], "sources": [], "table": []}
            sections.append(current)
        return current

    for raw_line in lines:
        line = raw_line.rstrip()
        if line == "## Candidate sourced draft":
            in_draft = True
            continue
        if in_draft and line.startswith("## ") and line != "## Candidate sourced draft":
            break
        if not in_draft:
            continue
        if line.startswith("### "):
            title = line[4:]
            if title == "Company card":
                in_company_card = True
                current = None
                mode = "body"
                continue
            in_company_card = False
            current = {"title": title, "paragraphs": [], "sources": [], "table": []}
            sections.append(current)
            mode = "body"
            seen_first_heading = True
            continue
        if in_company_card:
            continue
        if not seen_first_heading:
            continue
        if line == "Sources:":
            ensure_current()
            mode = "sources"
            continue
        if not line:
            mode = "body" if mode == "sources" else mode
            continue
        target = ensure_current()
        if mode == "sources" and line.startswith("- "):
            target["sources"].append(line[2:])
        elif line.startswith("|"):
            target["table"].append(line)
        else:
            target["paragraphs"].append(line)
    return sections


def parse_company_card(lines: list[str]) -> dict[str, object]:
    card: dict[str, object] = {"fields": [], "sources": []}
    in_draft = False
    in_card = False
    mode = "fields"
    for raw_line in lines:
        line = raw_line.rstrip()
        if line == "## Candidate sourced draft":
            in_draft = True
            continue
        if in_draft and line.startswith("## ") and line != "## Candidate sourced draft":
            break
        if not in_draft:
            continue
        if line.startswith("### "):
            title = line[4:]
            if title == "Company card":
                in_card = True
                mode = "fields"
                continue
            if in_card:
                break
        if not in_card:
            continue
        if line == "Sources:":
            mode = "sources"
            continue
        if not line:
            continue
        if mode == "sources" and line.startswith("- "):
            card["sources"].append(line[2:])
            continue
        if mode == "fields" and line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            card["fields"].append({"key": key.strip(), "value": value.strip()})
    return card


def source_entry(source_line: str, catalog: dict[str, dict[str, str]]) -> dict[str, str]:
    match = SOURCE_SIMPLE.match(f"- {source_line}")
    if not match:
        return {"label": source_line, "title": source_line, "url": ""}
    entry = match.groupdict()
    return catalog.get(
        entry["url"],
        {"label": entry["label"], "title": entry["label"], "url": entry["url"]},
    )


def citation_template(entry: dict[str, str]) -> str:
    if not entry["url"]:
        return ""
    title = entry["title"].replace("|", " ")
    website = entry.get("website", "").replace("|", " ")
    cite = f"{{{{cite web|url={entry['url']}|title={title}"
    if website:
        cite += f"|website={website}"
    cite += "}}"
    return f"<ref>{cite}</ref>"


def strip_inline_markers(text: str) -> str:
    return INLINE_REF_RE.sub("", text).strip()


def render_inline_citations(text: str, source_lines: list[str], catalog: dict[str, dict[str, str]]) -> str:
    def replace(match: re.Match[str]) -> str:
        indexes = [int(item.strip()) for item in match.group(1).split(",")]
        refs: list[str] = []
        for index in indexes:
            source_index = index - 1
            if 0 <= source_index < len(source_lines):
                refs.append(citation_template(source_entry(source_lines[source_index], catalog)))
        return "".join(refs)

    return INLINE_REF_RE.sub(replace, text)


def render_infobox(company_card: dict[str, object], catalog: dict[str, dict[str, str]]) -> list[str]:
    fields = company_card.get("fields", [])
    if not fields:
        return []

    name_map = {
        "name": "name",
        "type": "type",
        "industry": "industry",
        "founded": "founded",
        "founders": "founders",
        "headquarters": "hq_location",
        "key_people": "key_people",
        "website": "website",
    }
    source_lines = company_card.get("sources", [])
    lines = ["{{Infobox company"]
    if not any(field["key"] == "name" for field in fields):
        lines.append("| name = Collibra")
    for field in fields:
        key = name_map.get(str(field["key"]))
        if not key:
            continue
        value = render_inline_citations(str(field["value"]), source_lines, catalog)
        lines.append(f"| {key} = {value}")
    lines.append("}}")
    return lines


def parse_table_rows(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip().strip("|")
        cells = [cell.strip() for cell in stripped.split("|")]
        if cells:
            rows.append(cells)
    return rows


def render_wikitable(lines: list[str], source_lines: list[str], catalog: dict[str, dict[str, str]]) -> list[str]:
    rows = parse_table_rows(lines)
    if not rows:
        return []
    header = rows[0]
    body = rows[1:]
    rendered = ['{| class="wikitable sortable"']
    rendered.append("|-")
    for cell in header:
        rendered.append(f"! {cell}")
    for row in body:
        rendered.append("|-")
        for cell in row:
            rendered.append(f"| {strip_inline_markers(render_inline_citations(cell, source_lines, catalog))}")
    rendered.append("|}")
    return rendered


def render_wikitext(
    sections: list[dict[str, object]],
    catalog: dict[str, dict[str, str]],
    company_card: dict[str, object],
) -> str:
    parts = [
        "<!-- generated from content/markdown/Collibra.md -->",
        "{{short description|Software company focused on data governance and data intelligence}}",
        "",
    ]
    infobox = render_infobox(company_card, catalog)
    if infobox:
        parts.extend(infobox)
        parts.append("")
    for index, section in enumerate(sections):
        title = str(section["title"])
        heading = f"== {title} ==" if index > 0 else "== Lead =="
        parts.append(heading)
        parts.append("")
        refs = "".join(
            citation_template(source_entry(source_line, catalog))
            for source_line in section["sources"]
        )
        paragraphs = section["paragraphs"]
        for p_index, paragraph in enumerate(paragraphs):
            rendered = render_inline_citations(str(paragraph), section["sources"], catalog)
            suffix = refs if INLINE_REF_RE.search(str(paragraph)) is None and p_index == len(paragraphs) - 1 else ""
            parts.append(f"{strip_inline_markers(rendered)}{suffix}")
            parts.append("")
        if section.get("table"):
            parts.extend(render_wikitable(section["table"], section["sources"], catalog))
            parts.append("")
    parts.append("== References ==")
    parts.append("{{reflist}}")
    parts.append("")
    return "\n".join(parts)


def render_docbook(
    sections: list[dict[str, object]],
    catalog: dict[str, dict[str, str]],
) -> str:
    sections_xml: list[str] = []
    bibliography_entries: list[str] = []
    seen_urls: set[str] = set()
    for section in sections:
        title = escape(str(section["title"]))
        paras = "\n".join(
            f"    <para>{escape(strip_inline_markers(str(paragraph)))}</para>"
            for paragraph in section["paragraphs"]
        )
        table_xml = ""
        if section.get("table"):
            rows = parse_table_rows(section["table"])
            if rows:
                header = rows[0]
                body = rows[1:]
                thead = "".join(f"<entry>{escape(cell)}</entry>" for cell in header)
                tbody = "\n".join(
                    "        <row>" + "".join(f"<entry>{escape(strip_inline_markers(cell))}</entry>" for cell in row) + "</row>"
                    for row in body
                )
                table_xml = (
                    "\n    <informaltable>\n"
                    f"      <tgroup cols=\"{len(header)}\">\n"
                    "        <thead>\n"
                    f"          <row>{thead}</row>\n"
                    "        </thead>\n"
                    "        <tbody>\n"
                    f"{tbody}\n"
                    "        </tbody>\n"
                    "      </tgroup>\n"
                    "    </informaltable>"
                )
        sections_xml.append(f"  <section>\n    <title>{title}</title>\n{paras}{table_xml}\n  </section>")
        for source_line in section["sources"]:
            entry = source_entry(source_line, catalog)
            if not entry["url"] or entry["url"] in seen_urls:
                continue
            seen_urls.add(entry["url"])
            bibliography_entries.append(
                "    <biblioentry xml:id=\"bib-{id}\">\n"
                "      <title>{title}</title>\n"
                "      <bibliosource><ulink url=\"{url}\">{url}</ulink></bibliosource>\n"
                "      <abbrev>{label}</abbrev>\n"
                "    </biblioentry>".format(
                    id=slugify(entry["url"])[:48],
                    title=escape(entry["title"]),
                    url=escape(entry["url"]),
                    label=escape(entry["label"]),
                )
            )
    bibliography = "\n".join(bibliography_entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<article xmlns="http://docbook.org/ns/docbook" version="5.2">\n'
        "  <info>\n"
        "    <title>Collibra</title>\n"
        "    <subtitle>Generated encyclopedia-style draft</subtitle>\n"
        "  </info>\n"
        + "\n".join(sections_xml)
        + "\n  <bibliography>\n"
        + bibliography
        + "\n  </bibliography>\n"
        "</article>\n"
    )


def xml_id(value: str) -> str:
    return slugify(value) or "section"


def render_modular_docbook(
    sections: list[dict[str, object]],
    catalog: dict[str, dict[str, str]],
    company_card: dict[str, object],
) -> dict[str, str]:
    base_dir = MODULAR_XML_PATH.parent
    sections_dir = base_dir / "sections"
    apparatus_dir = base_dir / "apparatus"

    files: dict[str, str] = {}

    def strip_xml_decl(content: str) -> str:
        if content.startswith("<?xml"):
            return content.split("\n", 1)[1]
        return content

    section_hrefs: list[str] = []
    bibliography_entries: list[str] = []
    seen_urls: set[str] = set()
    discussion_points: list[str] = []
    company_card_href = ""
    timeline = load_timeline()
    media_model = load_media_model()

    card_fields = company_card.get("fields", [])
    if card_fields:
        company_card_href = "apparatus/company-card.xml"
        variable_entries = []
        for field in card_fields:
            term = escape(str(field["key"]).replace("_", " ").title())
            value = escape(strip_inline_markers(str(field["value"])))
            variable_entries.append(
                "    <varlistentry>\n"
                f"      <term>{term}</term>\n"
                "      <listitem>\n"
                f"        <para>{value}</para>\n"
                "      </listitem>\n"
                "    </varlistentry>"
            )
        files[str(apparatus_dir / "company-card.xml")] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sidebar xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="company-card">\n'
            "  <title>Company Card</title>\n"
            "  <variablelist>\n"
            f"{chr(10).join(variable_entries)}\n"
            "  </variablelist>\n"
            "</sidebar>\n"
        )

    for index, section in enumerate(sections, start=1):
        title = str(section["title"])
        section_filename = f"{index:02d}-{xml_id(title)}.xml"
        section_hrefs.append(f"sections/{section_filename}")
        paragraphs = "\n".join(
            f"  <para>{escape(strip_inline_markers(str(paragraph)))}</para>"
            for paragraph in section["paragraphs"]
        )
        table_xml = ""
        if section.get("table"):
            rows = parse_table_rows(section["table"])
            if rows:
                header = rows[0]
                body = rows[1:]
                thead = "".join(f"<entry>{escape(cell)}</entry>" for cell in header)
                tbody = "\n".join(
                    "      <row>" + "".join(f"<entry>{escape(strip_inline_markers(cell))}</entry>" for cell in row) + "</row>"
                    for row in body
                )
                table_xml = (
                    "\n  <informaltable>\n"
                    f"    <tgroup cols=\"{len(header)}\">\n"
                    "      <thead>\n"
                    f"        <row>{thead}</row>\n"
                    "      </thead>\n"
                    "      <tbody>\n"
                    f"{tbody}\n"
                    "      </tbody>\n"
                    "    </tgroup>\n"
                    "  </informaltable>"
                )
        files[str(sections_dir / section_filename)] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" version="5.2">\n'
            f"  <title>{escape(title)}</title>\n"
            f"{paragraphs}\n"
            f"{table_xml}\n"
            "</section>\n"
        )
        for source_line in section["sources"]:
            entry = source_entry(source_line, catalog)
            if not entry["url"] or entry["url"] in seen_urls:
                continue
            seen_urls.add(entry["url"])
            bibliography_entries.append(
                "  <biblioentry xml:id=\"bib-{id}\">\n"
                "    <title>{title}</title>\n"
                "    <bibliosource><ulink url=\"{url}\">{url}</ulink></bibliosource>\n"
                "    <abbrev>{label}</abbrev>\n"
                "  </biblioentry>".format(
                    id=xml_id(entry["url"])[:48],
                    title=escape(entry["title"]),
                    url=escape(entry["url"]),
                    label=escape(entry["label"]),
                )
            )
        if title == "AI, agentic AI, and attribution boundaries":
            discussion_points.extend(
                [
                    "AI governance is supported by recent independent coverage and can be treated as a recent platform extension.",
                    "Agentic AI should remain attributed and marginal unless stronger secondary sourcing emerges.",
                    "The Colin Jarvis and LinkedIn material is self-published context, not a notability anchor.",
                ]
            )

    discussion_points.extend(
        [
            "Keep company history distinct from platform description.",
            "Do not let data catalog terminology consume the full article scope.",
            "Treat data intelligence as attributed market vocabulary rather than settled taxonomy.",
            "Keep MDM, RDM, reference data, and code-table claims out unless independently sourced as central to Collibra.",
            "Keep founder-status nuance and image-rights handling in local metadata when the outward article would otherwise overstate weakly sourced detail.",
        ]
    )

    timeline_rows = "\n".join(
        "      <row>"
        f"<entry>{escape(str(item.get('date', '')))}</entry>"
        f"<entry>{escape(str(item.get('label', '')))}</entry>"
        f"<entry>{escape(str(item.get('summary', '')))}</entry>"
        f"<entry>{escape(str(item.get('confidence', '')))}</entry>"
        "</row>"
        for item in timeline.get("events", [])
    )
    files[str(apparatus_dir / "timeline.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<appendix xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="topic-timeline">\n'
        "  <title>Topic Timeline</title>\n"
        "  <para>This appendix keeps topic-lineage context, regulatory drivers, and confidence notes tied to the article support workflow.</para>\n"
        "  <informaltable>\n"
        '    <tgroup cols="4">\n'
        "      <thead>\n"
        "        <row><entry>Date</entry><entry>Event</entry><entry>Summary</entry><entry>Confidence</entry></row>\n"
        "      </thead>\n"
        "      <tbody>\n"
        f"{timeline_rows}\n"
        "      </tbody>\n"
        "    </tgroup>\n"
        "  </informaltable>\n"
        "</appendix>\n"
    )

    media_items = "\n".join(
        "    <listitem><para>{label}: {notes} ({status})</para></listitem>".format(
            label=escape(str(item.get("label", ""))),
            notes=escape(str(item.get("notes", ""))),
            status=escape(str(item.get("publication_status", ""))),
        )
        for item in media_model.get("assets", [])
    )
    files[str(apparatus_dir / "media-notes.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<appendix xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="media-notes">\n'
        "  <title>Media Notes</title>\n"
        "  <para>This appendix tracks local media references and their publication status.</para>\n"
        "  <itemizedlist>\n"
        f"{media_items}\n"
        "  </itemizedlist>\n"
        "</appendix>\n"
    )

    files[str(apparatus_dir / "editorial-notes.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<appendix xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="editorial-notes">\n'
        "  <title>Editorial Notes</title>\n"
        "  <para>This appendix is part of the local publication apparatus and is not intended for direct Wikipedia publication.</para>\n"
        "  <para>The modular XML source is maintained with xi:include so each article section can evolve independently while the compiled article remains reproducible from git.</para>\n"
        "  <para>Downstream formats such as HTML, SVG-rich documentation, MathML-bearing content, and LaTeX-aware transformations should be layered from the DocBook article rather than hand-maintained separately.</para>\n"
        "</appendix>\n"
    )

    discussion_list = "\n".join(
        f"    <listitem><para>{escape(point)}</para></listitem>" for point in discussion_points
    )
    files[str(apparatus_dir / "discussion-points.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<appendix xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="discussion-points">\n'
        "  <title>Discussion Points</title>\n"
        "  <para>This appendix tracks issues that may surface in article review, talk-page discussion, and future source reassessment.</para>\n"
        "  <itemizedlist>\n"
        f"{discussion_list}\n"
        "  </itemizedlist>\n"
        "</appendix>\n"
    )

    bibliography = "\n".join(bibliography_entries)
    files[str(base_dir / "bibliography.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<bibliography xmlns="http://docbook.org/ns/docbook" version="5.2">\n'
        f"{bibliography}\n"
        "</bibliography>\n"
    )

    xi_sections = "\n".join(
        f'  <xi:include href="{href}"/>' for href in section_hrefs
    )
    files[str(MODULAR_XML_PATH)] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + '<article xmlns="http://docbook.org/ns/docbook"\n'
        + '         xmlns:xi="http://www.w3.org/2001/XInclude"\n'
        + '         version="5.2"\n'
        + '         xml:id="collibra-wikipedia-article">\n'
        + "  <info>\n"
        + "    <title>Collibra</title>\n"
        + "    <subtitle>Modular local article source for Wikipedia-oriented publication</subtitle>\n"
        + "  </info>\n"
        + (f'  <xi:include href="{company_card_href}"/>\n' if company_card_href else "")
        + f"{xi_sections}\n"
        + '  <xi:include href="apparatus/timeline.xml"/>\n'
        + '  <xi:include href="apparatus/media-notes.xml"/>\n'
        + '  <xi:include href="apparatus/editorial-notes.xml"/>\n'
        + '  <xi:include href="apparatus/discussion-points.xml"/>\n'
        + '  <xi:include href="bibliography.xml"/>\n'
        + "</article>\n"
    )

    compiled = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + '<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="collibra-wikipedia-article">\n'
        + "  <info>\n"
        + "    <title>Collibra</title>\n"
        + "    <subtitle>Generated encyclopedia-style draft</subtitle>\n"
        + "  </info>\n"
        + (strip_xml_decl(files[str(apparatus_dir / "company-card.xml")]).rstrip() + "\n" if company_card_href else "")
        + "\n".join(
            strip_xml_decl(files[str(sections_dir / f"{index:02d}-{xml_id(str(section['title']))}.xml")]).rstrip()
            for index, section in enumerate(sections, start=1)
        )
        + "\n"
        + strip_xml_decl(files[str(apparatus_dir / "timeline.xml")]).rstrip()
        + "\n"
        + strip_xml_decl(files[str(apparatus_dir / "media-notes.xml")]).rstrip()
        + "\n"
        + strip_xml_decl(files[str(apparatus_dir / "editorial-notes.xml")]).rstrip()
        + "\n"
        + strip_xml_decl(files[str(apparatus_dir / "discussion-points.xml")]).rstrip()
        + "\n"
        + strip_xml_decl(files[str(base_dir / "bibliography.xml")]).rstrip()
        + "\n</article>\n"
    )
    compiled = re.sub(r"<\?xml[^>]*\?>\n?", "", compiled)
    compiled = '<?xml version="1.0" encoding="UTF-8"?>\n' + compiled.lstrip()
    files[str(DOCBOOK_PATH)] = compiled
    return files


def render_rdf(sections: list[dict[str, object]], catalog: dict[str, dict[str, str]]) -> str:
    section_nodes: list[str] = []
    for index, section in enumerate(sections, start=1):
        title = escape(str(section["title"]))
        description = escape(" ".join(strip_inline_markers(str(p)) for p in section["paragraphs"]))
        sources = [
            source_entry(source_line, catalog)["url"]
            for source_line in section["sources"]
            if source_entry(source_line, catalog)["url"]
        ]
        source_xml = "".join(
            f"\n    <dc:source rdf:resource=\"{escape(url)}\"/>" for url in sources
        )
        section_nodes.append(
            "  <rdf:Description rdf:about=\"urn:datatech-wiki-kg:collibra:section:{idx}\">\n"
            "    <dc:title>{title}</dc:title>\n"
            "    <dc:description>{description}</dc:description>{sources}\n"
            "  </rdf:Description>".format(
                idx=index,
                title=title,
                description=description,
                sources=source_xml,
            )
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '  <rdf:Description rdf:about="urn:datatech-wiki-kg:collibra:wikipedia-draft">\n'
        "    <dc:title>Collibra</dc:title>\n"
        "    <dc:type>WikipediaDraft</dc:type>\n"
        "    <dc:source>content/markdown/Collibra.md</dc:source>\n"
        "  </rdf:Description>\n"
        + "\n".join(section_nodes)
        + "\n</rdf:RDF>\n"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def prune_stale_modular_xml(files: dict[str, str]) -> None:
    base_dir = MODULAR_XML_PATH.parent
    keep = {Path(path_str).resolve() for path_str in files}
    for subdir in ("sections", "apparatus"):
        target_dir = base_dir / subdir
        if not target_dir.exists():
            continue
        for path in target_dir.glob("*.xml"):
            if path.resolve() not in keep:
                path.unlink()
                print(f"removed {path}")


def main() -> int:
    lines = load_lines()
    catalog = parse_source_catalog(lines)
    catalog.update(load_reference_catalog())
    company_card = parse_company_card(lines)
    sections = parse_candidate_sections(lines)
    write(WIKITEXT_PATH, render_wikitext(sections, catalog, company_card))
    modular_files = render_modular_docbook(sections, catalog, company_card)
    prune_stale_modular_xml(modular_files)
    for path_str, content in modular_files.items():
        write(Path(path_str), content)
    write(RDF_PATH, render_rdf(sections, catalog))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
