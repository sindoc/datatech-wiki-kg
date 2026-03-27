#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
SILKPAGE_ROOT = Path(CONFIG["dependencies"]["silkpage_root"]).expanduser()
TEMPLATES = CONFIG.get("templates", {})
PIPELINE = ROOT / "xpl" / "render-navbox.xpl"
STYLESHEET = ROOT / "xsl" / "wikipedia-navbox.xsl"
CALABASH_JAR = SILKPAGE_ROOT / "tools" / "calabash" / "xmlcalabash-1.5.7-120.jar"
CALABASH_LIB_DIR = SILKPAGE_ROOT / "tools" / "calabash" / "lib"


def calabash_classpath() -> str:
    jars = [str(CALABASH_JAR)]
    jars.extend(str(path) for path in sorted(CALABASH_LIB_DIR.glob("*.jar")))
    return ":".join(jars)


def render_template(xml_source: Path, wikitext_output: Path) -> None:
    wikitext_output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "java",
        "-cp",
        calabash_classpath(),
        "com.xmlcalabash.drivers.Main",
        str(PIPELINE),
        f"source={xml_source}",
        f"stylesheet={STYLESHEET}",
        f"output={wikitext_output}",
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True, capture_output=True, text=True)
    print(f"wrote {wikitext_output}")


def main() -> int:
    for _, template in TEMPLATES.items():
        render_template(ROOT / template["xml_source"], ROOT / template["wikitext_output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
