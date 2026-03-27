# Zotero Workflow

The editorial reference source of truth for this repository is the `Collibra` collection in Zotero.

The tracked interchange artifact in git is [Collibra.json](/Users/skh/ws/git/github/sindoc/datatech-wiki-kg/references/zotero/Collibra.json), a CSL-JSON style export/import file that can be reviewed in git and imported into either:

- `My Library/Collibra`
- a dedicated Zotero group library for collaborative curation

## Expected practice

- add and maintain all candidate references in the Zotero collection first
- keep the collection metadata clean enough to export reproducible citation outputs
- keep `Collibra.json` aligned with the collection so that git tracks the reviewable source set
- export tracked derivatives from that Zotero collection into this directory
- review exported changes in git as part of the editorial cycle

## Recommended tracked exports

- `Collibra.json`: CSL-JSON import/export artifact for Zotero and repo-side automation
- `Collibra.bib`: BibTeX export for citation tooling and downstream conversions
- `Collibra.rdf`: RDF export when useful for linked-reference workflows
- `Collibra.wikipedia.txt`: generated Wikipedia citation-template snippets for manual editing support

## Group workflow

If a group should be able to add items collaboratively, the cleanest model is:

1. Create a dedicated Zotero group library for the Collibra editorial work.
2. Import `Collibra.json` into that group library.
3. Curate additions and corrections in the group.
4. Re-export the reviewed collection back to `Collibra.json`.
5. Regenerate the repository outputs from that tracked export.

## Editorial intent

This repository tracks the public editorial process behind the Collibra entry. That includes source selection, draft generation, review, publication artifacts, and community-facing conversation records where appropriate.

The goal is transparent, source-driven publication control rather than ad hoc copy-paste editing.
