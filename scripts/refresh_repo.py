#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
NOTIFICATIONS = ROOT / "notifications" / "pending-update.json"


def run(script_name: str) -> None:
    subprocess.run(["python3", str(ROOT / "scripts" / script_name)], check=True)


def git_commit() -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def git_changed_paths() -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_notification_manifest() -> None:
    NOTIFICATIONS.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now_iso(),
        "site_url": CONFIG["site_url"],
        "mailing_list_name": CONFIG["mailing_list_name"],
        "commit": git_commit(),
        "changed_paths": git_changed_paths(),
        "next_action": "Review and optionally send an opt-in maintainer update."
    }
    NOTIFICATIONS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    run("sync_sources.py")
    run("build_graph.py")
    run("generate_campaign_assets.py")
    run("render_reference_exports.py")
    run("render_media_manifest.py")
    run("render_publication_artifacts.py")
    write_notification_manifest()
    print(f"wrote {NOTIFICATIONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
