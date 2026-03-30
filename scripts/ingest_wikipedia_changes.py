#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import difflib


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
MODEL = json.loads((ROOT / "data" / "topics" / "collibra-wikipedia.json").read_text(encoding="utf-8"))
OUT_ROOT = ROOT / "data" / "wikipedia-ingest"
REPORT_PATH = ROOT / "build" / "wikipedia" / "live-sync-report.md"
USER_AGENT = "datatech-wiki-kg/1.0 (live wikipedia ingest)"
EXPECTED_ARCHETYPE = "wikipedia-content"


@dataclass(frozen=True)
class Target:
    title: str
    compare_local: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch live MediaWiki revisions, talk-page changes, and diffs into tracked repo artifacts."
    )
    parser.add_argument(
        "--site",
        default=str(MODEL["language_pages"]["en"]["site"]),
        help="MediaWiki host, default: %(default)s",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="ISO-8601 UTC timestamp to start ingesting from. Defaults to the date produced by singine time.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum revisions / recent changes per title, default: %(default)s",
    )
    parser.add_argument(
        "--page",
        action="append",
        default=[],
        help="Page title to ingest. May be repeated. Defaults to Collibra, Talk:Collibra, and Template:Data.",
    )
    parser.add_argument(
        "--compare-local",
        action="append",
        default=[],
        metavar="TITLE=PATH",
        help="Write a unified diff between live wikitext and a local file. May be repeated.",
    )
    return parser.parse_args()


def mediawiki_get(site: str, params: dict[str, str]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params)
    url = f"https://{site}/w/api.php?{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def slugify(title: str) -> str:
    lowered = title.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "page"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_git_repo(root: Path) -> None:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"repository root is not a git worktree: {root}")


def assert_project_archetype(config: dict[str, Any]) -> str:
    archetype = str(config.get("project_archetype", "")).strip()
    if archetype != EXPECTED_ARCHETYPE:
        raise SystemExit(
            f"unsupported project_archetype={archetype or 'missing'}; expected {EXPECTED_ARCHETYPE}"
        )
    return archetype


def ensure_utc_timestamp(raw: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return f"{raw}T00:00:00Z"
    if raw.endswith("Z"):
        return raw
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_title(raw: str) -> str:
    return raw.replace("_", " ").strip()


def default_targets() -> list[Target]:
    return [
        Target("Collibra", ROOT / CONFIG["publication"]["wikipedia_draft"]),
        Target("Talk:Collibra"),
        Target("Template:Data", ROOT / CONFIG["templates"]["data_technology_navbox"]["wikitext_output"]),
    ]


def default_since_from_singine(config: dict[str, Any]) -> tuple[str, str]:
    singine_root = Path(config["dependencies"]["singine_root"]).expanduser()
    cmd = [
        "python3",
        "-m",
        "singine.command",
        "time",
        "date",
        "--offset-days",
        "-2",
        "--json",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(singine_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
            iso_date = payload.get("iso_date")
            if isinstance(iso_date, str) and iso_date:
                return ensure_utc_timestamp(iso_date), "singine time date --offset-days -2"
        except json.JSONDecodeError:
            pass
    fallback = "2026-03-28T00:00:00Z"
    return fallback, "static fallback"


def parse_compare_local(values: list[str]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--compare-local expects TITLE=PATH, got: {value}")
        title, raw_path = value.split("=", 1)
        mapping[normalize_title(title)] = (ROOT / raw_path).resolve() if not raw_path.startswith("/") else Path(raw_path)
    return mapping


def build_targets(args: argparse.Namespace) -> list[Target]:
    compare_map = parse_compare_local(args.compare_local)
    if args.page:
        titles = [normalize_title(page) for page in args.page]
        return [Target(title, compare_map.get(title)) for title in titles]
    targets = default_targets()
    if not compare_map:
        return targets
    merged: list[Target] = []
    seen: set[str] = set()
    for target in targets:
        merged.append(Target(target.title, compare_map.get(target.title, target.compare_local)))
        seen.add(target.title)
    for title, path in compare_map.items():
        if title not in seen:
            merged.append(Target(title, path))
    return merged


def first_page(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["query"]["pages"][0]


def fetch_current_page(site: str, title: str) -> dict[str, Any]:
    payload = mediawiki_get(
        site,
        {
            "action": "query",
            "prop": "info|revisions",
            "titles": title,
            "rvslots": "main",
            "rvprop": "ids|timestamp|user|comment|content",
            "inprop": "url",
            "formatversion": "2",
            "format": "json",
        },
    )
    return first_page(payload)


def fetch_revisions_since(site: str, title: str, since: str, limit: int) -> list[dict[str, Any]]:
    payload = mediawiki_get(
        site,
        {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvslots": "main",
            "rvprop": "ids|timestamp|user|comment|tags|size|content",
            "rvdir": "newer",
            "rvstart": since,
            "rvlimit": str(limit),
            "formatversion": "2",
            "format": "json",
        },
    )
    return first_page(payload).get("revisions", [])


def fetch_baseline_revision(site: str, title: str, since: str) -> dict[str, Any] | None:
    payload = mediawiki_get(
        site,
        {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvslots": "main",
            "rvprop": "ids|timestamp|user|comment|size|content",
            "rvdir": "older",
            "rvstart": since,
            "rvlimit": "1",
            "formatversion": "2",
            "format": "json",
        },
    )
    revisions = first_page(payload).get("revisions", [])
    return revisions[0] if revisions else None


def fetch_recent_changes(site: str, title: str, since: str, limit: int) -> list[dict[str, Any]]:
    payload = mediawiki_get(
        site,
        {
            "action": "query",
            "list": "recentchanges",
            "rctitle": title,
            "rcstart": since,
            "rcdir": "newer",
            "rclimit": str(limit),
            "rcprop": "title|timestamp|ids|sizes|flags|user|comment|tags|loginfo",
            "rctype": "edit|new|log|categorize",
            "formatversion": "2",
            "format": "json",
        },
    )
    return payload["query"].get("recentchanges", [])


def fetch_compare(site: str, from_rev: int, to_rev: int) -> dict[str, Any]:
    payload = mediawiki_get(
        site,
        {
            "action": "compare",
            "fromrev": str(from_rev),
            "torev": str(to_rev),
            "prop": "diff|diffsize|ids|title|user|comment|timestamp|size",
            "difftype": "unified",
            "formatversion": "2",
            "format": "json",
        },
    )
    return payload.get("compare", {})


def revision_content(revision: dict[str, Any]) -> str:
    slots = revision.get("slots", {})
    main = slots.get("main", {})
    return main.get("content", "")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unified_diff(left_name: str, left_text: str, right_name: str, right_text: str) -> str:
    diff = difflib.unified_diff(
        left_text.splitlines(),
        right_text.splitlines(),
        fromfile=left_name,
        tofile=right_name,
        lineterm="",
    )
    return "\n".join(diff) + ("\n" if left_text != right_text else "")


def ingest_target(site: str, target: Target, since: str, limit: int) -> dict[str, Any]:
    slug = slugify(target.title)
    out_dir = OUT_ROOT / slug
    current_page = fetch_current_page(site, target.title)
    revisions = fetch_revisions_since(site, target.title, since, limit)
    baseline = fetch_baseline_revision(site, target.title, since)
    changes = fetch_recent_changes(site, target.title, since, limit)

    current_revision = current_page.get("revisions", [{}])[0]
    current_content = revision_content(current_revision)

    write_json(out_dir / "current.json", current_page)
    write_json(out_dir / "revisions-since.json", revisions)
    write_json(out_dir / "recentchanges.json", changes)
    write_text(out_dir / "latest.wikitext", current_content)

    compare_payload: dict[str, Any] | None = None
    if baseline and current_revision.get("revid") and baseline.get("revid") != current_revision.get("revid"):
        compare_payload = fetch_compare(site, int(baseline["revid"]), int(current_revision["revid"]))
        write_json(out_dir / "baseline-to-current.compare.json", compare_payload)
        write_text(out_dir / "baseline.wikitext", revision_content(baseline))
        write_text(out_dir / "baseline-to-current.diff", compare_payload.get("body", ""))
    elif baseline:
        write_text(out_dir / "baseline.wikitext", revision_content(baseline))

    local_diff_path: str | None = None
    if target.compare_local and target.compare_local.exists():
        local_text = target.compare_local.read_text(encoding="utf-8")
        diff_text = unified_diff(str(target.compare_local), local_text, f"{site}:{target.title}", current_content)
        local_diff = out_dir / "local-versus-live.diff"
        write_text(local_diff, diff_text)
        local_diff_path = str(local_diff.relative_to(ROOT))

    return {
        "title": target.title,
        "slug": slug,
        "site": site,
        "url": current_page.get("fullurl", ""),
        "pageid": current_page.get("pageid"),
        "since": since,
        "latest_revid": current_revision.get("revid"),
        "latest_timestamp": current_revision.get("timestamp", ""),
        "revision_count_since": len(revisions),
        "recentchange_count": len(changes),
        "baseline_revid": baseline.get("revid") if baseline else None,
        "compare_generated": bool(compare_payload),
        "local_compare_path": local_diff_path,
        "artifact_dir": str(out_dir.relative_to(ROOT)),
    }


def render_report(run_manifest: dict[str, Any]) -> str:
    lines = [
        "# Live Wikipedia Sync Report",
        "",
        f"- Generated: {run_manifest['generated_at']}",
        f"- Site: {run_manifest['site']}",
        f"- Archetype: {run_manifest['project_archetype']}",
        f"- Since: {run_manifest['since']}",
        f"- Since source: {run_manifest['since_source']}",
        "",
        "## Targets",
    ]
    for result in run_manifest["targets"]:
        lines.append(
            "- `{title}` latest={latest} revisions-since={revisions} recentchanges={changes} artifacts=`{dir}`".format(
                title=result["title"],
                latest=result["latest_revid"] or "missing",
                revisions=result["revision_count_since"],
                changes=result["recentchange_count"],
                dir=result["artifact_dir"],
            )
        )
        if result["local_compare_path"]:
            lines.append(f"  local-vs-live diff: `{result['local_compare_path']}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("- `prop=revisions` is used for per-page revision history and latest wikitext.")
    lines.append("- `list=recentchanges` is used for page-scoped activity within Wikimedia recent-change retention.")
    lines.append("- `action=compare` is used to store baseline-to-current diffs when a prior revision exists before the chosen start timestamp.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    assert_git_repo(ROOT)
    archetype = assert_project_archetype(CONFIG)
    if args.since:
        since = ensure_utc_timestamp(args.since)
        since_source = "explicit --since"
    else:
        since, since_source = default_since_from_singine(CONFIG)
    targets = build_targets(args)
    results = [ingest_target(args.site, target, since, args.limit) for target in targets]
    manifest = {
        "generated_at": now_iso(),
        "site": args.site,
        "project_archetype": archetype,
        "since": since,
        "since_source": since_source,
        "targets": results,
    }
    write_json(OUT_ROOT / "manifest.json", manifest)
    write_text(REPORT_PATH, render_report(manifest))
    subprocess.run(
        ["python3", str(ROOT / "scripts" / "render_wikipedia_audit_registry.py")],
        cwd=str(ROOT),
        check=True,
    )
    print(f"wrote {OUT_ROOT / 'manifest.json'}")
    print(f"wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"http error: {exc.code} {exc.reason}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"url error: {exc.reason}", file=sys.stderr)
        raise SystemExit(1)
