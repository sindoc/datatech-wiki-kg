# ADR-0009: SilkPage and Singine Boundaries for Reference Workbenches

Status: accepted
Date: 2026-03-30

## Context

This repository needs richer reference-management features for Wikipedia-supporting
 work, including claim-to-source linking, source reuse visibility, support-health
 metrics, and credibility-method disclosure.

Those features cross three systems:

- this repository for canonical content, article-support metadata, and generated
  publication inputs
- SilkPage for semantic-XML-to-HTML rendering and visual presentation
- Singine for command orchestration, execution, auth, and local web serving

Without an explicit boundary, the content repository risks accumulating runtime UI
 behavior and server concerns that belong elsewhere.

## Decision

The repository boundary is:

- `datatech-wiki-kg` emits semantic content artifacts, including claim/reference
  graphs, article-support metadata, and SilkPage-facing XML source pages
- `silkpage` renders those semantic XML sources into HTML, using its XSLT and CSS
  layers as the default presentation system
- `singine` owns execution workflows, command surfaces, authentication, local
  serving, and publication orchestration

Reference workbench features in this repository may generate:

- structured JSON for local tooling and inspections
- semantic XML suitable for SilkPage rendering
- RDF-oriented metadata and lineage-bearing publication inputs

They must not become the long-term home of runtime UI or server orchestration.

## Consequences

- feature work stays aligned with the metamodel and project archetype
- the content repository remains publication-oriented rather than application-oriented
- SilkPage becomes the default visual layer for claim/source workbenches
- Singine becomes the stable operational entry point for serving and automation
