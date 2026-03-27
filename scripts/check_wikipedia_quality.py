#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "wikipedia_quality_rules.json").read_text(encoding="utf-8"))
WIKITEXT = ROOT / "build" / "wikipedia" / "Collibra.wikitext"
MODULAR_XML = ROOT / "xml" / "wikipedia" / "collibra" / "article.xml"
REPORT_JSON = ROOT / "build" / "quality" / "wikipedia-quality.json"
REPORT_MD = ROOT / "build" / "quality" / "wikipedia-quality.md"

SECTION_RE = re.compile(r"^==\s*(.+?)\s*==\s*$", re.MULTILINE)
REF_RE = re.compile(r'<ref(?:\s+name="[^"]+")?>\{\{cite web\|[^}]*\|website=([^}|]+)')
REF_NAME_RE = re.compile(r'<ref name="([^"]+)"')
ADJ_DUP_REF_RE = re.compile(r'<ref name="([^"]+)"/>\s*<ref name="\1"/>')
WORD_RE = re.compile(r"\b[\w-]+\b")
INFOBOX_RE = re.compile(r"\{\{Infobox company.*?\n\}\}", re.DOTALL)
SEE_ALSO_RE = re.compile(r"==\s*See also\s*==\s*(.*?)(?=^==|\Z)", re.DOTALL | re.MULTILINE)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_sections(text: str) -> list[dict[str, str]]:
    matches = list(SECTION_RE.finditer(text))
    sections: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections.append({"title": match.group(1), "body": text[start:end].strip()})
    return sections


def lead_body(text: str) -> str:
    match = SECTION_RE.search(text)
    end = match.start() if match else len(text)
    return text[:end].strip()


def prose_word_count(text: str) -> int:
    text = re.sub(r"<ref>.*?</ref>", " ", text, flags=re.DOTALL)
    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.DOTALL)
    return len(WORD_RE.findall(text))


def websites(text: str) -> list[str]:
    return [match.strip() for match in REF_RE.findall(text)]


def strip_infobox(text: str) -> tuple[str, str]:
    match = INFOBOX_RE.search(text)
    if not match:
        return "", text
    return match.group(0), text[: match.start()] + text[match.end() :]


def pref_labels(path: Path) -> dict[str, str]:
    ns = {
        "db": "http://docbook.org/ns/docbook",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
    }
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    labels: dict[str, str] = {}
    for node in root.findall(".//skos:prefLabel", ns):
        lang = node.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if lang:
            labels[lang] = (node.text or "").strip()
    return labels


def duplicate_named_refs(text: str) -> list[str]:
    return sorted(set(ADJ_DUP_REF_RE.findall(text)))


def finding(category: str, severity: str, rule: str, message: str) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "rule": rule,
        "message": message,
    }


def run_checks() -> dict:
    text = load_text(WIKITEXT)
    infobox_text, body_text = strip_infobox(text)
    sections = split_sections(body_text)
    titles = [section["title"] for section in sections]
    findings: list[dict[str, str]] = []
    lead = lead_body(body_text)

    required = RULES["required_sections"]
    for title in required:
        if title not in titles:
            findings.append(finding("article_shape", "error", "required_section", f"Missing required section: {title}"))

    if titles[: len(RULES["recommended_section_order"])] != RULES["recommended_section_order"]:
        findings.append(finding("article_shape", "warning", "section_order", "Section order differs from the concise company-article template."))

    if RULES.get("require_lead_prose") and not lead:
        findings.append(finding("article_shape", "error", "lead_prose", "Lead prose is missing before the first section heading."))
    if RULES.get("require_pronunciation_in_lead") and "{{IPAc-en" not in lead:
        findings.append(finding("article_shape", "warning", "lead_pronunciation", "Lead does not include the configured pronunciation marker."))
    for heading in RULES.get("forbidden_headings", []):
        if heading in titles:
            findings.append(finding("article_shape", "error", "forbidden_heading", f"Forbidden heading present: {heading}"))

    words = prose_word_count(text)
    if words < RULES["thresholds"]["min_words"]:
        findings.append(finding("article_shape", "warning", "min_words", f"Article prose is short at {words} words."))
    if words > RULES["thresholds"]["max_words"]:
        findings.append(finding("article_shape", "error", "max_words", f"Article prose is long at {words} words."))

    distinct_publishers = sorted(set(websites(text)))
    body_publishers = sorted(set(websites(body_text)))
    if len(distinct_publishers) < RULES["thresholds"]["min_distinct_publishers"]:
        findings.append(finding("sourcing", "error", "publisher_diversity", f"Only {len(distinct_publishers)} distinct cited publishers detected."))

    for section in sections:
        if section["title"] in {"References", "See also"}:
            continue
        if "<ref>" not in section["body"]:
            if '<ref name="' not in section["body"]:
                findings.append(finding("sourcing", "error", "inline_citations", f"Section lacks inline citations: {section['title']}"))

    for website in RULES["self_published_websites"]:
        if website in body_publishers:
            findings.append(finding("sourcing", "error", "self_published_source", f"Self-published or first-party source present in article citations: {website}"))
    for website in RULES["weak_context_websites"]:
        if website in body_publishers:
            findings.append(finding("sourcing", "warning", "weak_source_context", f"Use {website} with care for notability or evaluative claims."))

    lowered = text.lower()
    for token in RULES["promotional_words"]:
        if token.lower() in lowered:
            findings.append(finding("neutrality_and_tone", "error", "promotional_language", f"Promotional term detected: {token}"))
    for phrase in RULES["editorial_phrases"]:
        if phrase.lower() in lowered:
            findings.append(finding("neutrality_and_tone", "error", "editorial_voice", f"Editorial/meta phrase detected: {phrase}"))
    for word in RULES["relative_time_words"]:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            findings.append(finding("stability", "warning", "relative_time", f"Relative time term detected: {word}"))

    if "AI, agentic AI, and attribution boundaries" in titles:
        findings.append(finding("due_weight_and_scope", "warning", "section_scope", "Dedicated AI/agentic-AI boundary section may be too meta for first-version article prose."))

    see_also_match = SEE_ALSO_RE.search(body_text)
    see_also_body = see_also_match.group(1) if see_also_match else ""
    for item in RULES.get("required_see_also", []):
        if f"[[{item}]]" not in see_also_body:
            findings.append(finding("due_weight_and_scope", "warning", "see_also", f"See also entry missing: {item}"))

    for template in RULES.get("required_bottom_templates", []):
        if template not in text:
            findings.append(finding("maintainability", "warning", "bottom_template", f"Required bottom template missing: {template}"))

    if RULES.get("deduplicate_references"):
        duplicates = duplicate_named_refs(text)
        for name in duplicates:
            findings.append(finding("sourcing", "error", "duplicate_reference", f"Duplicate reference reused in same citation cluster: {name}"))

    if "xml/wikipedia/collibra/article.xml" not in str(MODULAR_XML):
        findings.append(finding("maintainability", "warning", "modular_xml", "Modular XML source path was not found as expected."))
    if not MODULAR_XML.exists():
        findings.append(finding("maintainability", "error", "modular_xml_missing", "Modular XML source is missing."))
    elif RULES.get("require_skos_labels"):
        labels = pref_labels(MODULAR_XML)
        for lang in RULES.get("required_article_languages", []):
            if lang not in labels:
                findings.append(finding("maintainability", "error", "skos_language_label", f"Missing SKOS prefLabel for language: {lang}"))

    ok = not any(item["severity"] == "error" for item in findings)
    return {
        "ok": ok,
        "article_class": RULES["article_class"],
        "policy_pages": RULES["policy_pages"],
        "exemplar_articles": RULES["exemplar_articles"],
        "word_count": words,
        "distinct_publishers": distinct_publishers,
        "findings": findings,
    }


def write_reports(payload: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Wikipedia Quality Report",
        "",
        f"- Article class: `{payload['article_class']}`",
        f"- Word count: `{payload['word_count']}`",
        f"- Distinct publishers: `{', '.join(payload['distinct_publishers'])}`",
        f"- Status: `{'ok' if payload['ok'] else 'needs work'}`",
        "",
        "## Findings",
        "",
    ]
    if not payload["findings"]:
        lines.append("- No findings.")
    else:
        for item in payload["findings"]:
            lines.append(f"- `{item['severity']}` `{item['category']}` `{item['rule']}`: {item['message']}")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    payload = run_checks()
    write_reports(payload)
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
