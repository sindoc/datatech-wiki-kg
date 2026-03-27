#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "collibra-campaign.json"
FEEDS_DIR = ROOT / "feeds"


def load_campaign() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atom_feed(payload: dict) -> str:
    campaign = payload["campaign"]
    updates = payload["updates"]
    entries = []
    for entry in updates:
        tags = "".join(
            f'\n    <category term="{escape(tag)}"/>'
            for tag in entry.get("tags", [])
        )
        entries.append(
            f"""  <entry>
    <id>{escape(entry["id"])}</id>
    <title>{escape(entry["title"])}</title>
    <updated>{escape(entry["updated"])}</updated>
    <summary>{escape(entry["summary"])}</summary>
    <link href="{escape(entry["link"])}" rel="alternate"/>{tags}
  </entry>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f'  <id>{escape(campaign["id"])}</id>\n'
        f'  <title>{escape(campaign["title"])}</title>\n'
        f'  <updated>{iso_now()}</updated>\n'
        f'  <subtitle>{escape(campaign["summary"])}</subtitle>\n'
        f'  <author><name>{escape(campaign["maintainer"])}</name></author>\n'
        f'  <link href="{escape(campaign["public_base_url"])}/feeds/datatech-collibra.atom" rel="self"/>\n'
        + "\n".join(entries)
        + "\n</feed>\n"
    )


def rss10_feed(payload: dict) -> str:
    campaign = payload["campaign"]
    updates = payload["updates"]
    item_refs = []
    items = []
    for entry in updates:
        link = entry["link"]
        item_refs.append(f'        <rss:item rdf:resource="{escape(link)}"/>')
        items.append(
            f"""  <rss:item rdf:about="{escape(link)}">
    <rss:title>{escape(entry["title"])}</rss:title>
    <rss:link>{escape(link)}</rss:link>
    <rss:description>{escape(entry["summary"])}</rss:description>
    <dc:date>{escape(entry["updated"])}</dc:date>
  </rss:item>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rdf:RDF\n'
        '  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n'
        '  xmlns:rss="http://purl.org/rss/1.0/"\n'
        '  xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'  <rss:channel rdf:about="{escape(campaign["id"])}">\n'
        f'    <rss:title>{escape(campaign["title"])}</rss:title>\n'
        f'    <rss:link>{escape(campaign["public_base_url"])}</rss:link>\n'
        f'    <rss:description>{escape(campaign["summary"])}</rss:description>\n'
        f'    <dc:date>{iso_now()}</dc:date>\n'
        '    <rss:items>\n'
        '      <rdf:Seq>\n'
        + "\n".join(item_refs)
        + '\n      </rdf:Seq>\n'
        '    </rss:items>\n'
        '  </rss:channel>\n'
        + "\n".join(items)
        + "\n</rdf:RDF>\n"
    )


def main() -> int:
    payload = load_campaign()
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    (FEEDS_DIR / "datatech-collibra.atom").write_text(atom_feed(payload), encoding="utf-8")
    (FEEDS_DIR / "datatech-collibra.rss").write_text(rss10_feed(payload), encoding="utf-8")
    print(f"wrote {(FEEDS_DIR / 'datatech-collibra.atom')}")
    print(f"wrote {(FEEDS_DIR / 'datatech-collibra.rss')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
