# RFC-0002: Reference Workbench and Support-Health Model

Status: draft
Date: 2026-03-30

## Summary

Introduce a repository-generated reference workbench that makes article support
 visible at the claim level and exposes reusable source nodes, coverage-health
 signals, and credibility-method lineage for review.

## Proposed change

Add a generated artifact set for the current built article:

- claim-to-reference graph in structured JSON
- semantic XML page for SilkPage publication
- local inspection HTML for immediate review during implementation

The model should represent:

- claim text or claim line
- article section and line context
- attached references
- reference reuse across claims
- local support-health metric for each claim
- local credibility metric for each source
- the calculation lineage and factor breakdown for those metrics

## Repository split

- `datatech-wiki-kg`: emit semantic data and publication inputs
- `silkpage`: render visual workbench pages from semantic XML
- `singine`: orchestrate builds and serve the generated pages locally

## Acceptance considerations

- the generated semantic XML must be suitable for SilkPage publication
- support-health and credibility metrics must disclose their calculation method
- source reuse must be visible without reading raw wikitext
- the workbench must remain review support, not publication truth
