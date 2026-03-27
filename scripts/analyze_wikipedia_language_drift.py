#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "topics" / "collibra-wikipedia.json"
USER_AGENT = "datatech-wiki-kg/1.0 (language drift analysis)"
SECTION_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.MULTILINE)


@dataclass
class ArticleSnapshot:
    lang: str
    site: str
    title: str
    timestamp: str
    wikibase_item: str
    wikitext: str
    categories: list[str]
    langlinks: list[str]
    sections: list[str]
    section_keys: list[str]
    ref_count: int
    text_length: int
    fact_hits: dict[str, bool]


def load_model() -> dict[str, object]:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def fetch_json(site: str, params: dict[str, str]) -> dict[str, object]:
    query = urllib.parse.urlencode(params)
    url = f"https://{site}/w/api.php?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return re.sub(r"\s+", " ", text)


def strip_wikitext(text: str) -> str:
    stripped = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    stripped = re.sub(r"<ref[^>]*>.*?</ref>", " ", stripped, flags=re.DOTALL)
    stripped = re.sub(r"<ref[^/]*/>", " ", stripped)
    stripped = re.sub(r"\{\{.*?\}\}", " ", stripped, flags=re.DOTALL)
    stripped = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", stripped)
    stripped = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", stripped)
    stripped = re.sub(r"'{2,}", "", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip()


def extract_sections(wikitext: str) -> list[str]:
    return [match.group(2).strip() for match in SECTION_RE.finditer(wikitext)]


def section_keys(sections: list[str], aliases: dict[str, list[str]]) -> list[str]:
    norm_aliases = {
        key: {normalize(alias) for alias in values}
        for key, values in aliases.items()
    }
    keys: list[str] = []
    for section in sections:
        normalized = normalize(section)
        mapped = next((key for key, values in norm_aliases.items() if normalized in values), normalized)
        keys.append(mapped)
    return keys


def detect_facts(wikitext: str, facts: list[dict[str, object]]) -> dict[str, bool]:
    haystack = normalize(strip_wikitext(wikitext))
    hits: dict[str, bool] = {}
    for fact in facts:
        aliases = [normalize(alias) for alias in fact.get("aliases", [])]
        hits[str(fact["id"])] = any(alias and alias in haystack for alias in aliases)
    return hits


def fetch_snapshot(lang: str, site: str, title: str, aliases: dict[str, list[str]], facts: list[dict[str, object]]) -> ArticleSnapshot:
    data = fetch_json(
        site,
        {
            "action": "query",
            "prop": "revisions|pageprops|categories|langlinks",
            "titles": title,
            "rvslots": "main",
            "rvprop": "timestamp|content",
            "cllimit": "max",
            "lllimit": "max",
            "format": "json",
            "formatversion": "2",
        },
    )
    page = data["query"]["pages"][0]
    revision = page["revisions"][0]
    wikitext = revision["slots"]["main"]["content"]
    categories = [entry["title"].split(":", 1)[-1] for entry in page.get("categories", [])]
    langlinks = [entry["lang"] for entry in page.get("langlinks", [])]
    sections = extract_sections(wikitext)
    return ArticleSnapshot(
        lang=lang,
        site=site,
        title=title,
        timestamp=revision["timestamp"],
        wikibase_item=page.get("pageprops", {}).get("wikibase_item", ""),
        wikitext=wikitext,
        categories=categories,
        langlinks=langlinks,
        sections=sections,
        section_keys=section_keys(sections, aliases),
        ref_count=len(re.findall(r"<ref\b", wikitext)),
        text_length=len(strip_wikitext(wikitext)),
        fact_hits=detect_facts(wikitext, facts),
    )


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def summarize(snapshots: list[ArticleSnapshot], facts: list[dict[str, object]]) -> dict[str, object]:
    fact_ids = [str(fact["id"]) for fact in facts]
    fact_labels = {str(fact["id"]): str(fact["label"]) for fact in facts}
    page_rows = []
    for snapshot in snapshots:
        covered = [fact_id for fact_id in fact_ids if snapshot.fact_hits.get(fact_id)]
        missing = [fact_id for fact_id in fact_ids if not snapshot.fact_hits.get(fact_id)]
        page_rows.append(
            {
                "lang": snapshot.lang,
                "site": snapshot.site,
                "title": snapshot.title,
                "timestamp": snapshot.timestamp,
                "wikibase_item": snapshot.wikibase_item,
                "langlinks": snapshot.langlinks,
                "section_keys": snapshot.section_keys,
                "section_count": len(snapshot.sections),
                "category_count": len(snapshot.categories),
                "categories": snapshot.categories,
                "ref_count": snapshot.ref_count,
                "text_length": snapshot.text_length,
                "fact_coverage": len(covered),
                "fact_coverage_ratio": round(len(covered) / len(fact_ids), 3) if fact_ids else 0.0,
                "facts_present": covered,
                "facts_missing": missing,
            }
        )

    pairwise = []
    for left in snapshots:
        for right in snapshots:
            if left.lang >= right.lang:
                continue
            left_facts = {fact_id for fact_id, hit in left.fact_hits.items() if hit}
            right_facts = {fact_id for fact_id, hit in right.fact_hits.items() if hit}
            pairwise.append(
                {
                    "pair": f"{left.lang}-{right.lang}",
                    "section_similarity": round(
                        jaccard(set(left.section_keys), set(right.section_keys)), 3
                    ),
                    "category_similarity": round(
                        jaccard({normalize(cat) for cat in left.categories}, {normalize(cat) for cat in right.categories}),
                        3,
                    ),
                    "fact_similarity": round(jaccard(left_facts, right_facts), 3),
                    "facts_only_in_left": sorted(left_facts - right_facts),
                    "facts_only_in_right": sorted(right_facts - left_facts),
                    "left_timestamp": left.timestamp,
                    "right_timestamp": right.timestamp,
                }
            )

    leaderboard = sorted(page_rows, key=lambda row: (-row["fact_coverage"], -row["ref_count"], -row["text_length"]))
    best = leaderboard[0] if leaderboard else None
    behind = []
    if best:
        best_facts = set(best["facts_present"])
        for row in leaderboard[1:]:
            missing_against_best = sorted(best_facts - set(row["facts_present"]))
            behind.append(
                {
                    "lang": row["lang"],
                    "behind_best_lang": best["lang"],
                    "missing_against_best": missing_against_best,
                    "missing_labels": [fact_labels[fact_id] for fact_id in missing_against_best],
                }
            )

    return {
        "topic": "collibra",
        "pages": page_rows,
        "pairwise": pairwise,
        "behind_best": behind,
        "fact_labels": fact_labels,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# Wikipedia Language Drift Report", ""]
    lines.append("## Page summary")
    for row in report["pages"]:
        lines.append(
            "- {lang}: refs={refs}, sections={sections}, facts={facts}, updated={updated}, wikidata={wikidata}".format(
                lang=row["lang"],
                refs=row["ref_count"],
                sections=row["section_count"],
                facts=f"{row['fact_coverage']}/{len(report['fact_labels'])}",
                updated=row["timestamp"],
                wikidata=row["wikibase_item"] or "missing",
            )
        )
    lines.append("")
    lines.append("## Pairwise drift")
    for row in report["pairwise"]:
        lines.append(
            "- {pair}: section={section}, category={category}, fact={fact}".format(
                pair=row["pair"],
                section=row["section_similarity"],
                category=row["category_similarity"],
                fact=row["fact_similarity"],
            )
        )
        if row["facts_only_in_left"]:
            lines.append(f"  left-only facts: {', '.join(row['facts_only_in_left'])}")
        if row["facts_only_in_right"]:
            lines.append(f"  right-only facts: {', '.join(row['facts_only_in_right'])}")
    lines.append("")
    lines.append("## Behind-best summary")
    for row in report["behind_best"]:
        lines.append(
            f"- {row['lang']} trails {row['behind_best_lang']} on: {', '.join(row['missing_labels']) or 'nothing'}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    model = load_model()
    aliases = model.get("section_aliases", {})
    facts = model.get("fact_atoms", [])
    snapshots = [
        fetch_snapshot(lang, page["site"], page["title"], aliases, facts)
        for lang, page in model["language_pages"].items()
    ]
    report = summarize(snapshots, facts)
    print(json.dumps(report, indent=2))
    print()
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
