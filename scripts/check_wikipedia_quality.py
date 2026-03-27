#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "wikipedia_quality_rules.json").read_text(encoding="utf-8"))
WIKITEXT = ROOT / "build" / "wikipedia" / "Collibra.wikitext"
MODULAR_XML = ROOT / "xml" / "wikipedia" / "collibra" / "article.xml"
REPORT_JSON = ROOT / "build" / "quality" / "wikipedia-quality.json"
REPORT_MD = ROOT / "build" / "quality" / "wikipedia-quality.md"

SECTION_RE = re.compile(r"^==\s*(.+?)\s*==\s*$", re.MULTILINE)
REF_RE = re.compile(r"<ref>\{\{cite web\|[^}]*\|website=([^}|]+)")
WORD_RE = re.compile(r"\b[\w-]+\b")
INFOBOX_RE = re.compile(r"\{\{Infobox company.*?\n\}\}", re.DOTALL)


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

    required = RULES["required_sections"]
    for title in required:
        if title not in titles:
            findings.append(finding("article_shape", "error", "required_section", f"Missing required section: {title}"))

    if titles[: len(RULES["recommended_section_order"])] != RULES["recommended_section_order"]:
        findings.append(finding("article_shape", "warning", "section_order", "Section order differs from the concise company-article template."))

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
        if section["title"] == "References":
            continue
        if "<ref>" not in section["body"]:
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

    if "xml/wikipedia/collibra/article.xml" not in str(MODULAR_XML):
        findings.append(finding("maintainability", "warning", "modular_xml", "Modular XML source path was not found as expected."))
    if not MODULAR_XML.exists():
        findings.append(finding("maintainability", "error", "modular_xml_missing", "Modular XML source is missing."))

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
