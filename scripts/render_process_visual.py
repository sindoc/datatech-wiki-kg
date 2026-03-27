#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol" / "wikipedia-contrib-process.xml"
OUT = ROOT / "visuals" / "wikipedia-contrib-process.mmd"
NS = {"sp": "urn:singine:protocol:wikipedia"}

def _node_id(prefix: str, index: int) -> str:
    return f"{prefix}{index}"


def _safe_label(text: str) -> str:
    return text.replace('"', "'").strip()


def build_mermaid() -> str:
    tree = ET.parse(PROTOCOL)
    root = tree.getroot()
    stages = root.findall("sp:stage", NS)
    lines = ["flowchart TD"]

    stage_nodes: list[str] = []
    artifact_index = 0
    command_index = 0

    for idx, stage in enumerate(stages, start=1):
        label = stage.findtext("sp:label", default=stage.get("id", f"stage-{idx}"), namespaces=NS)
        stage_node = _node_id("S", idx)
        stage_nodes.append(stage_node)
        lines.append(f'    {stage_node}["{_safe_label(label)}"]')

        for command in stage.findall("sp:command", NS):
            command_index += 1
            command_node = _node_id("C", command_index)
            command_text = (command.text or "").strip()
            lines.append(f'    {command_node}["{_safe_label(command_text)}"]')
            lines.append(f"    {stage_node} --> {command_node}")

        for artifact in stage.findall("sp:artifact", NS):
            artifact_index += 1
            artifact_node = _node_id("A", artifact_index)
            artifact_text = (artifact.text or "").strip()
            artifact_format = artifact.get("format", "artifact")
            lines.append(f'    {artifact_node}["{artifact_format}: {_safe_label(artifact_text)}"]')
            lines.append(f"    {stage_node} --> {artifact_node}")

    for left, right in zip(stage_nodes, stage_nodes[1:]):
        lines.append(f"    {left} --> {right}")

    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_mermaid(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
