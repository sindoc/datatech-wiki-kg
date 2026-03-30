#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INGEST_ROOT = ROOT / "data" / "wikipedia-ingest"
AUDIT_ROOT = ROOT / "data" / "wikipedia-audit"
MANIFEST = INGEST_ROOT / "manifest.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_target_events(slug: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_dir = INGEST_ROOT / slug
    revisions = load_json(target_dir / "revisions-since.json") if (target_dir / "revisions-since.json").exists() else []
    changes = load_json(target_dir / "recentchanges.json") if (target_dir / "recentchanges.json").exists() else []
    return revisions, changes


def build_registry_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in manifest.get("targets", []):
        slug = target["slug"]
        revisions, changes = read_target_events(slug)

        for revision in revisions:
            rows.append(
                {
                    "scope": "revision",
                    "title": target["title"],
                    "slug": slug,
                    "site": target["site"],
                    "pageid": target.get("pageid"),
                    "timestamp": revision.get("timestamp", ""),
                    "user": revision.get("user", ""),
                    "temp_user": bool(revision.get("temp", False)),
                    "revid": revision.get("revid"),
                    "parent_revid": revision.get("parentid"),
                    "rcid": None,
                    "event_type": "revision",
                    "change_type": "edit",
                    "size_old": None,
                    "size_new": revision.get("size"),
                    "size_delta": None,
                    "comment": revision.get("comment", ""),
                    "tags": revision.get("tags", []),
                }
            )

        for change in changes:
            oldlen = change.get("oldlen")
            newlen = change.get("newlen")
            delta = None
            if isinstance(oldlen, int) and isinstance(newlen, int):
                delta = newlen - oldlen
            rows.append(
                {
                    "scope": "recentchange",
                    "title": target["title"],
                    "slug": slug,
                    "site": target["site"],
                    "pageid": target.get("pageid"),
                    "timestamp": change.get("timestamp", ""),
                    "user": change.get("user", ""),
                    "temp_user": bool(change.get("temp", False)),
                    "revid": change.get("revid"),
                    "parent_revid": change.get("old_revid"),
                    "rcid": change.get("rcid"),
                    "event_type": change.get("type", ""),
                    "change_type": change.get("logaction") or change.get("type", ""),
                    "size_old": oldlen,
                    "size_new": newlen,
                    "size_delta": delta,
                    "comment": change.get("comment", ""),
                    "tags": change.get("tags", []),
                }
            )

    rows.sort(
        key=lambda row: (
            row.get("timestamp", ""),
            row.get("title", ""),
            str(row.get("rcid") or ""),
            str(row.get("revid") or ""),
            row.get("scope", ""),
        )
    )
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "scope",
        "title",
        "slug",
        "site",
        "pageid",
        "timestamp",
        "user",
        "temp_user",
        "revid",
        "parent_revid",
        "rcid",
        "event_type",
        "change_type",
        "size_old",
        "size_new",
        "size_delta",
        "comment",
        "tags",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serializable = dict(row)
            serializable["tags"] = ";".join(row.get("tags", []))
            writer.writerow(serializable)


def write_markdown(path: Path, rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Wikipedia Audit Registry",
        "",
        f"- Generated: {manifest.get('generated_at', '')}",
        f"- Site: {manifest.get('site', '')}",
        f"- Since: {manifest.get('since', '')}",
        "",
        "## Summary",
    ]
    titles = sorted({row["title"] for row in rows})
    for title in titles:
        title_rows = [row for row in rows if row["title"] == title]
        revisions = sum(1 for row in title_rows if row["scope"] == "revision")
        recentchanges = sum(1 for row in title_rows if row["scope"] == "recentchange")
        latest = max((row["timestamp"] for row in title_rows), default="")
        lines.append(f"- `{title}` revisions={revisions} registry-events={recentchanges} latest={latest}")
    lines.extend(
        [
            "",
            "## Registry contract",
            "- This registry records change metadata, not full textual diffs.",
            "- Use the ingest payloads for detailed page snapshots and compare output.",
            "- Use this audit layer as the stable system-of-record index for article, talk-page, and template activity.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not MANIFEST.exists():
        raise SystemExit("missing ingest manifest; run make wiki-ingest first")
    manifest = load_json(MANIFEST)
    rows = build_registry_rows(manifest)
    payload = {
        "generated_at": manifest.get("generated_at", ""),
        "site": manifest.get("site", ""),
        "since": manifest.get("since", ""),
        "since_source": manifest.get("since_source", ""),
        "project_archetype": manifest.get("project_archetype", ""),
        "row_count": len(rows),
        "rows": rows,
    }
    write_json(AUDIT_ROOT / "registry.json", payload)
    write_jsonl(AUDIT_ROOT / "registry.jsonl", rows)
    write_csv(AUDIT_ROOT / "registry.csv", rows)
    write_markdown(AUDIT_ROOT / "registry.md", rows, manifest)
    print(f"wrote {AUDIT_ROOT / 'registry.json'}")
    print(f"wrote {AUDIT_ROOT / 'registry.jsonl'}")
    print(f"wrote {AUDIT_ROOT / 'registry.csv'}")
    print(f"wrote {AUDIT_ROOT / 'registry.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
