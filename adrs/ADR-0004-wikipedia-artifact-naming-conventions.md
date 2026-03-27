# ADR-0004: Wikipedia Artifact Naming Conventions

Status: accepted
Date: 2026-03-27

## Context

This repository contains canonical content, generated outputs, modular XML sections, and governance documents. Predictable names are required so the workflow remains scriptable and easy to review.

## Decision

The repository uses these naming conventions:

- ADRs: `adrs/ADR-XXXX-slug.md`
- RFCs: `rfcs/RFC-XXXX-slug.md`
- canonical topic source: `content/markdown/<Topic>.md`
- generated Wikipedia draft: `build/wikipedia/<Topic>.wikitext`
- modular article root: `xml/wikipedia/<topic>/article.xml`
- modular article sections: `xml/wikipedia/<topic>/sections/NN-slug.xml`
- generated compiled DocBook: `build/docbook/<Topic>.xml`
- generated RDF: `build/rdf/<Topic>.rdf`
- tracked Zotero exports: `references/zotero/<Topic>.*`

Numbered XML section filenames use two digits to preserve ordering in directory listings and diffs.

## Consequences

- scripts can target stable paths without topic-specific exceptions
- generated artifacts remain visually distinct from canonical authored sources
- editorial and publication files are easier to audit during review
