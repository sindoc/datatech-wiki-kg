#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WIKITEXT_PATH = ROOT / "build" / "wikipedia" / "Collibra.wikitext"
ARTICLE_XML_PATH = ROOT / "xml" / "wikipedia" / "collibra" / "article.xml"
REFERENCES_JSON = ROOT / "references" / "zotero" / "Collibra.json"
OUT_DIR = ROOT / "build" / "reference-workbench"
OUT_JSON = OUT_DIR / "collibra-reference-map.json"
OUT_HTML = OUT_DIR / "index.html"
OUT_XML = OUT_DIR / "reference-workbench.xml"
SITE_XML = ROOT / "site" / "src" / "xml" / "en" / "docs" / "reference-workbench.xml"

SECTION_RE = re.compile(r"^==\s+(.+?)\s+==$")
REF_USE_RE = re.compile(r'<ref name="([^"]+)"\s*/>')
REF_DEF_RE = re.compile(r'<ref name="([^"]+)">\{\{cite web\|url=([^|}]+)\|title=([^|}]+)(?:\|website=([^}|]+))?[^}]*\}\}</ref>')
COMMENT_RE = re.compile(r"<!--.*?-->")
DOCBOOK_NS = {"db": "http://docbook.org/ns/docbook", "xi": "http://www.w3.org/2001/XInclude"}

KNOWN_SOURCES = {
    "techcrunch.com": {"class": "trade-press", "label": "TechCrunch", "delta": 18},
    "cnbc.com": {"class": "news", "label": "CNBC", "delta": 22},
    "techtarget.com": {"class": "trade-press", "label": "TechTarget", "delta": 18},
    "venturebeat.com": {"class": "trade-press", "label": "VentureBeat", "delta": 16},
    "siliconangle.com": {"class": "trade-press", "label": "SiliconANGLE", "delta": 12},
    "vub.be": {"class": "institution", "label": "Vrije Universiteit Brussel", "delta": 10},
    "research.vub.be": {"class": "institution", "label": "Vrije Universiteit Brussel", "delta": 10},
    "techtransfer.research.vub.be": {"class": "institution", "label": "VUB TechTransfer", "delta": 10},
    "collibra.com": {"class": "company", "label": "Collibra", "delta": -28},
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_reference_inventory() -> dict[str, dict[str, object]]:
    if not REFERENCES_JSON.exists():
        return {}
    entries = json.loads(read_text(REFERENCES_JSON))
    by_url: dict[str, dict[str, object]] = {}
    for entry in entries:
        url = entry.get("URL")
        if not url:
            continue
        by_url[url] = entry
    return by_url


def strip_markup(text: str) -> str:
    clean = COMMENT_RE.sub("", text)
    clean = REF_USE_RE.sub("", clean)
    clean = re.sub(r"<br\s*/?>", "; ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\{\{[^{}]+\}\}", "", clean)
    clean = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", clean)
    clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", clean)
    clean = clean.replace("'''", "").replace("''", "")
    clean = re.sub(r"\(\s*\)", "", clean)
    clean = clean.replace("|", "")
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def normalize_claim_key(text: str) -> str:
    clean = strip_markup(text).lower()
    clean = re.sub(r"[^a-z0-9]+", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def classify_source(url: str, website: str) -> dict[str, object]:
    domain = domain_of(url)
    parts = domain.split(".")
    root = ".".join(parts[-2:]) if len(parts) >= 2 else domain
    source = KNOWN_SOURCES.get(domain) or KNOWN_SOURCES.get(root)

    score = 50
    factors: list[dict[str, object]] = [
        {"label": "Base score", "delta": 50, "reason": "Neutral starting point for a published web source."}
    ]
    if url.startswith("https://"):
        score += 5
        factors.append({"label": "HTTPS", "delta": 5, "reason": "Transport security is present."})

    source_class = "web"
    source_label = website or domain
    independence = "independent"
    if source:
        source_class = str(source["class"])
        source_label = str(source["label"])
        delta = int(source["delta"])
        score += delta
        factors.append(
            {
                "label": f"Publisher class: {source_class}",
                "delta": delta,
                "reason": f"Domain matched known source profile for {source_label}.",
            }
        )
        if source_class == "company":
            independence = "primary"
        elif source_class == "institution":
            independence = "contextual"
    elif domain.endswith(".edu") or domain.endswith(".ac.uk"):
        score += 12
        source_class = "institution"
        independence = "contextual"
        factors.append(
            {
                "label": "Academic domain",
                "delta": 12,
                "reason": "Institutional domain suggests a non-commercial academic source.",
            }
        )

    if re.search(r"/press|/newsroom|/company/", url):
        score -= 6
        factors.append(
            {
                "label": "Promotional path heuristic",
                "delta": -6,
                "reason": "URL path suggests a publisher-owned or promotional context.",
            }
        )

    score = max(0, min(100, score))
    band = "high" if score >= 75 else "medium" if score >= 55 else "low"
    return {
        "domain": domain,
        "publisher_class": source_class,
        "publisher_label": source_label,
        "independence": independence,
        "score": score,
        "band": band,
        "method": {
            "id": "heuristic-web-credibility-v1",
            "lineage": [
                "base score",
                "transport security",
                "known publisher class mapping",
                "institutional domain heuristic",
                "promotional-path penalty",
            ],
            "factors": factors,
            "note": "This is a local editorial support metric, not a public truth score.",
        },
    }


def parse_reference_definitions(text: str, inventory: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    refs: dict[str, dict[str, object]] = {}
    for name, url, title, website in REF_DEF_RE.findall(text):
        zotero = inventory.get(url, {})
        issued = zotero.get("issued", {}).get("date-parts", [[]])[0]
        accessed = zotero.get("accessed", {}).get("date-parts", [[]])[0]
        credibility = classify_source(url, website)
        refs[name] = {
            "id": name,
            "url": url,
            "title": title,
            "website": website or zotero.get("container-title", ""),
            "issued": issued,
            "accessed": accessed,
            "credibility": credibility,
            "supported_claim_ids": [],
            "supported_sections": [],
        }
    return refs


def parse_claims(text: str, refs: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    current_section = "Lead"
    in_references = False
    in_infobox = False
    line_number = 0

    for raw_line in text.splitlines():
        line_number += 1
        line = raw_line.rstrip()
        if line == "== References ==":
            in_references = True
            continue
        if in_references:
            continue
        heading = SECTION_RE.match(line)
        if heading:
            current_section = heading.group(1)
            continue
        if line == "{{Infobox company":
            in_infobox = True
            continue
        if in_infobox and line == "}}":
            in_infobox = False
            continue
        ref_names = list(dict.fromkeys(REF_USE_RE.findall(line)))
        if not ref_names:
            continue
        text_value = strip_markup(line)
        if not text_value:
            continue
        claim_type = "infobox" if in_infobox else "article"
        if line.startswith("|-") or line.startswith("| ") or line.startswith("! "):
            claim_type = "table"
        claim_id = f"claim-{len(claims) + 1:03d}"
        claim = {
            "id": claim_id,
            "section": current_section,
            "line_number": line_number,
            "claim_type": claim_type,
            "text": text_value,
            "reference_ids": ref_names,
        }
        claims.append(claim)
        for ref_name in ref_names:
            if ref_name not in refs:
                continue
            refs[ref_name]["supported_claim_ids"].append(claim_id)
            refs[ref_name]["supported_sections"].append(current_section)
    return claims


def resolve_includes() -> list[Path]:
    tree = ET.parse(ARTICLE_XML_PATH)
    root = tree.getroot()
    base = ARTICLE_XML_PATH.parent
    paths: list[Path] = []
    for include in root.findall("xi:include", DOCBOOK_NS):
        href = include.get("href")
        if href:
            paths.append((base / href).resolve())
    return paths


def text_content(elem: ET.Element) -> str:
    return "".join(elem.itertext()).strip()


def parse_xml_claims() -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    counter = 0
    for path in resolve_includes():
        tree = ET.parse(path)
        root = tree.getroot()
        local = root.tag.split("}")[-1]
        if local == "sidebar" and root.get("{http://www.w3.org/XML/1998/namespace}id") == "company-card":
            section = "Lead"
            for entry in root.findall(".//db:varlistentry", DOCBOOK_NS):
                term_elem = entry.find("db:term", DOCBOOK_NS)
                para_elem = entry.find(".//db:para", DOCBOOK_NS)
                term = text_content(term_elem) if term_elem is not None else ""
                para = text_content(para_elem) if para_elem is not None else ""
                if not term or not para:
                    continue
                counter += 1
                claims.append(
                    {
                        "id": f"claim-{counter:03d}",
                        "section": section,
                        "line_number": counter,
                        "claim_type": "infobox",
                        "text": f"{term}: {para}",
                        "reference_ids": [],
                    }
                )
            continue
        if local != "section":
            continue
        title_elem = root.find("db:title", DOCBOOK_NS)
        title = text_content(title_elem) if title_elem is not None else "Section"
        if not title:
            title = "Section"
        for para in root.findall("db:para", DOCBOOK_NS):
            value = text_content(para)
            if value:
                counter += 1
                claims.append(
                    {
                        "id": f"claim-{counter:03d}",
                        "section": title,
                        "line_number": counter,
                        "claim_type": "article",
                        "text": value,
                        "reference_ids": [],
                    }
                )
        for row in root.findall(".//db:tbody/db:row", DOCBOOK_NS):
            entries = [text_content(entry) for entry in row.findall("db:entry", DOCBOOK_NS)]
            if not entries:
                continue
            if len(entries) == 2:
                text = f"{entries[0]}: {entries[1]}"
            else:
                text = " | ".join(entries)
            counter += 1
            claims.append(
                {
                    "id": f"claim-{counter:03d}",
                    "section": title,
                    "line_number": counter,
                    "claim_type": "table",
                    "text": text,
                    "reference_ids": [],
                }
            )
    return claims


def attach_refs_from_wikitext(xml_claims: list[dict[str, object]], wikitext_claims: list[dict[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str], dict[str, object]] = {}
    for claim in wikitext_claims:
        key = (claim["section"], normalize_claim_key(claim["text"]))
        by_key[key] = claim
    enriched: list[dict[str, object]] = []
    for claim in xml_claims:
        key = (claim["section"], normalize_claim_key(claim["text"]))
        match = by_key.get(key)
        if not match:
            for other_key, other_claim in by_key.items():
                if other_key[0] != claim["section"]:
                    continue
                if key[1] and (key[1] in other_key[1] or other_key[1] in key[1]):
                    match = other_claim
                    break
        merged = dict(claim)
        merged["reference_ids"] = list(match["reference_ids"]) if match else []
        enriched.append(merged)
    return enriched


def claim_coverage_health(claim: dict[str, object], refs: dict[str, dict[str, object]]) -> dict[str, object]:
    supported = [refs[ref_id] for ref_id in claim["reference_ids"] if ref_id in refs]
    independent = [ref for ref in supported if ref["credibility"]["independence"] == "independent"]
    primary = [ref for ref in supported if ref["credibility"]["independence"] == "primary"]
    high = [ref for ref in independent if int(ref["credibility"]["score"]) >= 75]
    score = 35
    reasons = ["Base support score for a cited claim line."]
    if supported:
        score += 10
        reasons.append("At least one reference is attached to the claim.")
    if independent:
        score += 20
        reasons.append("The claim has independent source support.")
    if len(independent) >= 2:
        score += 10
        reasons.append("The claim has multiple independent supporting references.")
    if high:
        score += 10
        reasons.append("At least one supporting reference is from a stronger known publisher class.")
    if primary and not independent:
        score -= 18
        reasons.append("Support depends on primary or publisher-owned material.")
    score = max(0, min(100, score))
    band = "strong" if score >= 70 else "moderate" if score >= 50 else "weak"
    return {"score": score, "band": band, "reasons": reasons}


def finalize_refs(refs: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    ordered = []
    for ref in refs.values():
        ref["supported_sections"] = sorted(set(ref["supported_sections"]))
        ref["use_count"] = len(ref["supported_claim_ids"])
        ordered.append(ref)
    ordered.sort(key=lambda item: (-int(item["use_count"]), item["title"]))
    return ordered


def build_payload() -> dict[str, object]:
    text = read_text(WIKITEXT_PATH)
    inventory = load_reference_inventory()
    refs = parse_reference_definitions(text, inventory)
    wikitext_claims = parse_claims(text, refs)
    claims = attach_refs_from_wikitext(parse_xml_claims(), wikitext_claims)
    for claim in claims:
        for ref_name in claim["reference_ids"]:
            if ref_name not in refs:
                continue
            refs[ref_name]["supported_claim_ids"].append(claim["id"])
            refs[ref_name]["supported_sections"].append(claim["section"])
    for claim in claims:
        claim["coverage_health"] = claim_coverage_health(claim, refs)
    ref_list = finalize_refs(refs)
    return {
        "article": {
            "title": "Collibra",
            "source_wikitext": str(WIKITEXT_PATH.relative_to(ROOT)),
            "source_xml": str(ARTICLE_XML_PATH.relative_to(ROOT)),
        },
        "summary": {
            "claim_count": len(claims),
            "reference_count": len(ref_list),
            "multi_use_reference_count": sum(1 for ref in ref_list if int(ref["use_count"]) > 1),
        },
        "credibility_method": {
            "id": "heuristic-web-credibility-v1",
            "description": "Local weighted heuristic for editorial triage. It rewards recognized independent publications and penalizes publisher-owned company sources.",
            "lineage": [
                {"factor": "Base score", "effect": "+50"},
                {"factor": "HTTPS", "effect": "+5"},
                {"factor": "Known publisher mapping", "effect": "variable"},
                {"factor": "Academic domain heuristic", "effect": "+12"},
                {"factor": "Promotional path heuristic", "effect": "-6"},
            ],
            "warning": "The score is for support tooling inside this repo. It is not a substitute for editorial judgment or Wikipedia sourcing policy.",
        },
        "claims": claims,
        "references": ref_list,
    }


def render_html(payload: dict[str, object]) -> str:
    article_title = payload["article"]["title"]
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{article_title} Reference Workbench</title>
  <style>
    :root {{
      --bg: #f6f1e8;
      --paper: #fffdf8;
      --ink: #1d2a30;
      --muted: #5d6b73;
      --line: #d5c8b6;
      --accent: #0f6c81;
      --accent-soft: #dff1f4;
      --low: #9e2a2b;
      --mid: #9a6b00;
      --high: #216e39;
      --shadow: 0 12px 30px rgba(52, 39, 20, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      background:
        radial-gradient(circle at top left, rgba(15,108,129,0.08), transparent 28%),
        linear-gradient(180deg, #f8f4ec 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    header {{
      padding: 24px 28px 12px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,253,248,0.86);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 5;
    }}
    h1 {{ margin: 0 0 6px; font-size: 2rem; }}
    .subtitle {{ color: var(--muted); max-width: 70rem; }}
    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }}
    .stat {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      box-shadow: var(--shadow);
      font-size: 0.95rem;
    }}
    main {{
      display: grid;
      grid-template-columns: 1.2fr 0.9fr 1fr;
      gap: 18px;
      padding: 20px 22px 24px;
      min-height: calc(100vh - 120px);
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
      min-height: 40rem;
      display: flex;
      flex-direction: column;
    }}
    .panel-head {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(15,108,129,0.08), rgba(15,108,129,0.02));
    }}
    .panel-head h2 {{ margin: 0 0 6px; font-size: 1.1rem; }}
    .panel-head p {{ margin: 0; color: var(--muted); font-size: 0.95rem; }}
    .panel-body {{ padding: 12px; overflow: auto; flex: 1; }}
    .claim, .ref {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      margin-bottom: 10px;
      background: #fffdfa;
      transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
      cursor: pointer;
    }}
    .claim:hover, .ref:hover, .claim.active, .ref.active {{
      transform: translateY(-1px);
      border-color: var(--accent);
      background: var(--accent-soft);
    }}
    .meta {{ color: var(--muted); font-size: 0.88rem; margin-bottom: 8px; }}
    .claim-text {{ line-height: 1.45; }}
    .chips {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
    .chip {{
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 0.8rem;
      border: 1px solid var(--line);
      background: #f5efe5;
    }}
    .score-high {{ color: var(--high); }}
    .score-medium {{ color: var(--mid); }}
    .score-low {{ color: var(--low); }}
    .support-list {{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px dashed var(--line);
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .detail-block {{ padding: 14px 16px; border-bottom: 1px solid var(--line); }}
    .detail-block:last-child {{ border-bottom: 0; }}
    .detail-block h3 {{ margin: 0 0 8px; font-size: 1rem; }}
    .detail-block p, .detail-block li {{ line-height: 1.45; }}
    .detail-block ul {{ margin: 8px 0 0 18px; padding: 0; }}
    iframe {{ width: 100%; min-height: 24rem; border: 0; background: white; }}
    input[type="search"] {{
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      font: inherit;
      background: #fffdfa;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    @media (max-width: 1100px) {{
      main {{ grid-template-columns: 1fr; }}
      .panel {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{article_title} Reference Workbench</h1>
    <div class="subtitle">Visual claim-to-source workspace generated from the article build. It shows which statements each reference supports, lets you inspect likely replacement candidates, and explains the lineage of the local credibility heuristic on the same page.</div>
    <div class="stats" id="stats"></div>
  </header>
  <main>
    <section class="panel">
      <div class="panel-head">
        <h2>Claims</h2>
        <p>Article lines backed by references in the current built wikitext.</p>
      </div>
      <div class="panel-body">
        <input id="claim-search" type="search" placeholder="Filter claims by text or section" />
        <div id="claims"></div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <h2>References</h2>
        <p>Reusable source nodes with support counts and editorial credibility breakdown.</p>
      </div>
      <div class="panel-body">
        <input id="ref-search" type="search" placeholder="Filter references by title, domain, or section" />
        <div id="refs"></div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <h2>Inspector</h2>
        <p>Selection details, credibility lineage, and optional source preview iframe.</p>
      </div>
      <div class="panel-body" id="inspector"></div>
    </section>
  </main>
  <script>
    const payload = {payload_json};

    function esc(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }}

    function scoreClass(score) {{
      if (score >= 75) return "score-high";
      if (score >= 55) return "score-medium";
      return "score-low";
    }}

    {{
      const claimsEl = document.getElementById("claims");
      const refsEl = document.getElementById("refs");
      const inspectorEl = document.getElementById("inspector");
      const statsEl = document.getElementById("stats");
      const claimSearch = document.getElementById("claim-search");
      const refSearch = document.getElementById("ref-search");
      const refsById = Object.fromEntries(payload.references.map((ref) => [ref.id, ref]));
      const claimsById = Object.fromEntries(payload.claims.map((claim) => [claim.id, claim]));

      statsEl.innerHTML = `
        <div class="stat">${{payload.summary.claim_count}} claim lines</div>
        <div class="stat">${{payload.summary.reference_count}} references</div>
        <div class="stat">${{payload.summary.multi_use_reference_count}} reused references</div>
        <div class="stat">Method: ${{payload.credibility_method.id}}</div>
      `;

      function renderClaims(filter = "") {{
        const q = filter.toLowerCase();
        claimsEl.innerHTML = payload.claims
          .filter((claim) => !q || claim.text.toLowerCase().includes(q) || claim.section.toLowerCase().includes(q))
          .map((claim) => `
            <article class="claim" data-claim-id="${{claim.id}}">
              <div class="meta">${{esc(claim.section)}} · line ${{claim.line_number}} · ${{esc(claim.claim_type)}} · coverage ${{claim.coverage_health.score}} (${{esc(claim.coverage_health.band)}})</div>
              <div class="claim-text">${{esc(claim.text)}}</div>
              <div class="chips">
                ${{claim.reference_ids.map((id) => `<span class="chip">${{esc(refsById[id]?.website || id)}}</span>`).join("")}}
              </div>
            </article>
          `)
          .join("");
        document.querySelectorAll(".claim").forEach((node) => {{
          node.addEventListener("click", () => selectClaim(node.dataset.claimId));
        }});
      }}

      function renderRefs(filter = "") {{
        const q = filter.toLowerCase();
        refsEl.innerHTML = payload.references
          .filter((ref) => {{
            const hay = [ref.title, ref.url, ref.website, ref.supported_sections.join(" ")].join(" ").toLowerCase();
            return !q || hay.includes(q);
          }})
          .map((ref) => `
            <article class="ref" data-ref-id="${{ref.id}}">
              <div class="meta">${{esc(ref.website || ref.credibility.domain)}} · <span class="${{scoreClass(ref.credibility.score)}}">credibility ${{ref.credibility.score}}</span></div>
              <div class="claim-text">${{esc(ref.title)}}</div>
              <div class="chips">
                <span class="chip">${{esc(ref.credibility.publisher_class)}}</span>
                <span class="chip">${{esc(ref.credibility.independence)}}</span>
                <span class="chip">${{ref.use_count}} supporting claims</span>
              </div>
              <div class="support-list">Used in: ${{esc(ref.supported_sections.join(", "))}}</div>
            </article>
          `)
          .join("");
        document.querySelectorAll(".ref").forEach((node) => {{
          node.addEventListener("click", () => selectRef(node.dataset.refId));
        }});
      }}

      function setActive(selector, id, dataKey) {{
        document.querySelectorAll(selector).forEach((node) => {{
          node.classList.toggle("active", node.dataset[dataKey] === id);
        }});
      }}

      function clearActive(selector) {{
        document.querySelectorAll(selector).forEach((node) => node.classList.remove("active"));
      }}

      function selectClaim(id) {{
        const claim = claimsById[id];
        if (!claim) return;
        setActive(".claim", id, "claimId");
        clearActive(".ref");
        claim.reference_ids.forEach((refId) => {{
          const node = document.querySelector(`.ref[data-ref-id="${{refId}}"]`);
          if (node) node.classList.add("active");
        }});
        const supportedRefs = claim.reference_ids.map((refId) => refsById[refId]).filter(Boolean);
        inspectorEl.innerHTML = `
          <section class="detail-block">
            <h3>Selected claim</h3>
            <p><strong>${{esc(claim.section)}}</strong> · line ${{claim.line_number}} · ${{esc(claim.claim_type)}} · coverage ${{claim.coverage_health.score}} (${{esc(claim.coverage_health.band)}})</p>
            <p>${{esc(claim.text)}}</p>
          </section>
          <section class="detail-block">
            <h3>Coverage health</h3>
            <ul>
              ${{claim.coverage_health.reasons.map((reason) => `<li>${{esc(reason)}}</li>`).join("")}}
            </ul>
          </section>
          <section class="detail-block">
            <h3>Supporting references</h3>
            <ul>
              ${{supportedRefs.map((ref) => `<li><a href="${{esc(ref.url)}}" target="_blank" rel="noreferrer">${{esc(ref.title)}}</a> (${{esc(ref.website || ref.credibility.domain)}}, credibility ${{ref.credibility.score}}, used by ${{ref.use_count}} claim${{ref.use_count === 1 ? "" : "s"}})</li>`).join("")}}
            </ul>
          </section>
        `;
      }}

      function selectRef(id) {{
        const ref = refsById[id];
        if (!ref) return;
        setActive(".ref", id, "refId");
        clearActive(".claim");
        ref.supported_claim_ids.forEach((claimId) => {{
          const node = document.querySelector(`.claim[data-claim-id="${{claimId}}"]`);
          if (node) node.classList.add("active");
        }});
        inspectorEl.innerHTML = `
          <section class="detail-block">
            <h3>Selected reference</h3>
            <p><a href="${{esc(ref.url)}}" target="_blank" rel="noreferrer">${{esc(ref.title)}}</a></p>
            <p>${{esc(ref.website || ref.credibility.domain)}} · <span class="${{scoreClass(ref.credibility.score)}}">credibility ${{ref.credibility.score}}</span> · ${{esc(ref.credibility.independence)}}</p>
            <div class="chips">
              <span class="chip">${{ref.use_count}} supporting claims</span>
              <span class="chip">${{esc(ref.credibility.publisher_class)}}</span>
            </div>
          </section>
          <section class="detail-block">
            <h3>Claims covered by this reference</h3>
            <ul>
              ${{ref.supported_claim_ids.map((claimId) => {{
                const claim = claimsById[claimId];
                return `<li><strong>${{esc(claim.section)}}</strong>: ${{esc(claim.text)}}</li>`;
              }}).join("")}}
            </ul>
          </section>
          <section class="detail-block">
            <h3>Credibility metric lineage</h3>
            <p>${{esc(payload.credibility_method.description)}}</p>
            <ul>
              ${{ref.credibility.method.factors.map((factor) => `<li><strong>${{esc(factor.label)}}</strong> (${{factor.delta >= 0 ? "+" : ""}}${{factor.delta}}): ${{esc(factor.reason)}}</li>`).join("")}}
            </ul>
            <p><strong>Method note:</strong> ${{esc(ref.credibility.method.note)}}</p>
          </section>
          <section class="detail-block">
            <h3>Source preview</h3>
            <p>Some external sites block iframe embedding. If this panel stays blank, open the source in a new tab.</p>
            <iframe src="${{esc(ref.url)}}" loading="lazy"></iframe>
          </section>
        `;
      }}

      claimSearch.addEventListener("input", (event) => renderClaims(event.target.value));
      refSearch.addEventListener("input", (event) => renderRefs(event.target.value));

      renderClaims();
      renderRefs();
      if (payload.references[0]) selectRef(payload.references[0].id);
    }}
  </script>
</body>
</html>
"""


def xml_escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_silkpage_xml(payload: dict[str, object]) -> str:
    claim_items: list[str] = []
    for claim in payload["claims"][:24]:
        refs = ", ".join(claim["reference_ids"])
        claim_items.append(
            "    <listitem>\n"
            f"      <para>{xml_escape(claim['text'])}</para>\n"
            f"      <sidebar><para>Section: {xml_escape(claim['section'])}. Coverage health: {claim['coverage_health']['score']} ({xml_escape(claim['coverage_health']['band'])}). References: {xml_escape(refs)}.</para></sidebar>\n"
            "    </listitem>"
        )

    ref_items: list[str] = []
    for ref in payload["references"][:24]:
        ref_items.append(
            "    <listitem>\n"
            f"      <para><link xlink:href=\"{xml_escape(ref['url'])}\">{xml_escape(ref['title'])}</link></para>\n"
            f"      <sidebar><para>Publisher: {xml_escape(ref['website'] or ref['credibility']['domain'])}. Credibility: {ref['credibility']['score']}. Independence: {xml_escape(ref['credibility']['independence'])}. Used by {ref['use_count']} claim(s).</para></sidebar>\n"
            "    </listitem>"
        )

    lineage_items = "\n".join(
        f"    <listitem><para>{xml_escape(item['factor'])}: {xml_escape(item['effect'])}</para></listitem>"
        for item in payload["credibility_method"]["lineage"]
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<article xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        '  <title>Reference Workbench</title>\n'
        '  <subtitle>Claim-to-source support graph for the current Collibra article build</subtitle>\n'
        '  <para>This page is the SilkPage-facing semantic view of the current reference graph. Runtime serving and orchestration belong in Singine; page rendering and visual treatment belong in SilkPage; this repository emits the underlying content model.</para>\n'
        '  <section>\n'
        '    <title>Summary</title>\n'
        f"    <para>The current build exposes {payload['summary']['claim_count']} claim lines, {payload['summary']['reference_count']} references, and {payload['summary']['multi_use_reference_count']} references that support more than one claim.</para>\n"
        '  </section>\n'
        '  <section>\n'
        '    <title>Coverage Health</title>\n'
        '    <para>Coverage health is a local editorial triage metric for how well a claim line is supported by the attached references. It favors independent support and multiple corroborating references.</para>\n'
        '  </section>\n'
        '  <section>\n'
        '    <title>Credibility Method Lineage</title>\n'
        f"    <para>{xml_escape(payload['credibility_method']['description'])}</para>\n"
        '    <itemizedlist>\n'
        f"{lineage_items}\n"
        '    </itemizedlist>\n'
        f"    <sidebar><para>{xml_escape(payload['credibility_method']['warning'])}</para></sidebar>\n"
        '  </section>\n'
        '  <section>\n'
        '    <title>Claim Sample</title>\n'
        '    <itemizedlist>\n'
        f"{chr(10).join(claim_items)}\n"
        '    </itemizedlist>\n'
        '  </section>\n'
        '  <section>\n'
        '    <title>Reference Sample</title>\n'
        '    <itemizedlist>\n'
        f"{chr(10).join(ref_items)}\n"
        '    </itemizedlist>\n'
        '  </section>\n'
        '</article>\n'
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    payload = build_payload()
    write(OUT_JSON, json.dumps(payload, indent=2) + "\n")
    write(OUT_HTML, render_html(payload))
    write(OUT_XML, render_silkpage_xml(payload))
    write(SITE_XML, render_silkpage_xml(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
