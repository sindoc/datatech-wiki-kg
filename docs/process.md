# Process

Date: 2026-03-27
Surface: foss.lutino.io/wikipedia

## Goal

Make the Wikipedia-support draft understandable to contributors through one user-friendly and standards-based process.

## Process stages

1. Author the canonical Markdown source and related ADR or RFC material.
2. Refresh derived artifacts such as Org, Logseq, JSON-LD, Atom, and RSS.
3. Synchronize the visual working surface into the Singine kernel Logseq graph.
4. Expose public process and progress through SilkPage-style XML publication sources.
5. Prepare pending notifications without sending them automatically.
6. Verify the full chain with one end-to-end command-line test case.

## Standards and payloads

- Markdown for authored narrative and ADRs
- XML for the canonical Singine process payload exchange
- JSON-LD for graph publication
- Atom 1.0 and RSS 1.0 for updates
- Logseq-compatible Markdown for the visual graph surface
- Mermaid derived from the XML protocol for a user-friendly process view

## Main commands

```bash
make refresh
make kernel-sync
make visualize
make test-case
python3 -m singine.command wikipedia contrib collibra --action test-case --json
python3 -m singine.command wikipedia contrib collibra --action visualize --json
```
