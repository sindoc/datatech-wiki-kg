# CLAUDE

This repository maintains a public-facing, source-driven support graph for Wikipedia contributions on data technology topics.

## Primary goals

- maintain a canonical git history of article-support material
- keep Markdown, Org, Logseq, XML, RDF, JSON-LD, Atom, and RSS aligned
- publish process and progress under `https://foss.lutino.io/wikipedia/`
- support human-led automation through `singine`

## Repository shape

- `content/markdown/` is the canonical authored layer
- `content/org/` and `content/logseq/pages/` are generated mirrors
- `graph/` contains generated JSON-LD and related graph artifacts
- `feeds/` contains generated Atom and RSS outputs
- `site/src/xml/en/` contains SilkPage-style publication source
- `notifications/` contains pending update manifests

## Tone

Use a precise, public-documentation tone aligned with existing `markupware.com` and `silkpage` documentation:

- neutral
- architectural
- explicit about process
- cautious about claims and provenance

## Safety

- no automated bulk email
- no personal emails in public files
- no unverifiable historical claims presented as facts
- no direct edits to Wikipedia article text in this repository without source notes
