#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
CAMPAIGN = json.loads((ROOT / "data" / "collibra-campaign.json").read_text(encoding="utf-8"))
PARTICIPANTS = json.loads((ROOT / "outreach" / "proposed_participants.json").read_text(encoding="utf-8"))
CANONICAL = ROOT / CONFIG["content"]["canonical_markdown"]
GRAPH_PATH = ROOT / "graph" / "collibra-support.jsonld"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def heading_nodes(lines: list[str]) -> list[dict]:
    nodes = []
    for idx, line in enumerate(lines, start=1):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            nodes.append(
                {
                    "@id": f"urn:section:collibra:{idx}",
                    "@type": "schema:CreativeWork",
                    "name": line[level + 1 :].strip(),
                    "position": idx,
                    "description": f"Section level {level} in canonical markdown source."
                }
            )
    return nodes


def participant_nodes() -> list[dict]:
    nodes = []
    for item in PARTICIPANTS["participants"]:
        slug = item["name"].lower().replace(".", "").replace(" ", "-")
        nodes.append(
            {
                "@id": f"urn:person:{slug}",
                "@type": "schema:Person",
                "name": item["name"],
                "description": f"Planning-list participant with relationship {item['relationship']}.",
                "knowsAbout": [{"@id": "urn:entity:company:collibra"}]
            }
        )
    return nodes


def build_graph() -> dict:
    lines = CANONICAL.read_text(encoding="utf-8").splitlines()
    graph = json.loads((ROOT / "graph" / "collibra-support.jsonld").read_text(encoding="utf-8"))
    graph["@graph"] = graph["@graph"][:5] + heading_nodes(lines) + participant_nodes() + [
        {
            "@id": "urn:artifact:notifications:pending",
            "@type": "schema:DataFeed",
            "name": "Pending maintainer notifications",
            "description": "Generated after refresh runs to summarize changes that may require maintainers to be informed."
        },
        {
            "@id": CAMPAIGN["campaign"]["id"],
            "@type": "schema:Project",
            "name": CAMPAIGN["campaign"]["title"],
            "description": CAMPAIGN["campaign"]["summary"],
            "url": CONFIG["site_url"],
            "dateModified": now_iso()
        }
    ]
    return graph


def main() -> int:
    GRAPH_PATH.write_text(json.dumps(build_graph(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {GRAPH_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
