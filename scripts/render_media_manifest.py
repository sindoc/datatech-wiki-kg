#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "media" / "assets"
TEMPLATE_PATH = ROOT / "media" / "manifests" / "collibra-assets.template.json"
OUTPUT_PATH = ROOT / "media" / "manifests" / "collibra-assets.json"


def now_iso_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def asset_files() -> list[Path]:
    return sorted(
        path for path in ASSETS_DIR.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


def infer_file(asset_id: str, expected: str, files: list[Path]) -> str:
    if expected:
        expected_path = ASSETS_DIR / expected
        if expected_path.exists():
            return expected

    if asset_id == "collibra-logo":
        for path in files:
            if "logo" in path.name.lower():
                return path.name
        for path in files:
            if path.suffix.lower() == ".svg":
                return path.name

    if asset_id == "collibra-product-screenshot":
        for path in files:
            lowered = path.name.lower()
            if "screenshot" in lowered:
                return path.name
        for path in files:
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                return path.name

    return expected


def fill_asset(item: dict, files: list[Path]) -> dict:
    filled = dict(item)
    filename = infer_file(item["id"], item.get("local_filename", ""), files)
    filled["local_filename"] = filename

    if not filled.get("captured_or_published_date") and filename:
        timestamp = datetime.fromtimestamp((ASSETS_DIR / filename).stat().st_mtime, tz=timezone.utc)
        filled["captured_or_published_date"] = timestamp.date().isoformat()

    if not filled.get("notes"):
        if filename:
            filled["notes"] = f"Auto-detected local asset file: {filename}."
        else:
            filled["notes"] = f"No local asset file detected as of {now_iso_date()}."
    return filled


def main() -> int:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    files = asset_files()
    payload = {
        "topic": template["topic"],
        "generated_at": now_iso_date(),
        "assets": [fill_asset(item, files) for item in template["assets"]],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
