# ADR-0002: Wikipedia Entry Authoring Principles

Status: accepted
Date: 2026-03-27

## Context

This repository exists to support a Wikipedia entry through a local, reviewable, source-driven workflow. The repository needs a short, stable statement of authoring principles so that article edits, quality checks, and later publication decisions are evaluated against the same contract.

## Decision

Wikipedia-facing article authoring in this repository follows these principles:

- accuracy over length
- neutrality over advocacy
- verifiability over insider knowledge
- due weight over topic sprawl
- stable wording over time-sensitive phrasing
- modular local source over ad hoc manual edits to generated outputs

For company articles, the default target is a short, accurate article that can be defended from independent sources rather than a comprehensive market essay.

## Consequences

- canonical prose is maintained in `content/markdown/`
- generated Wikipedia-facing output is derived, not hand-maintained
- first-party and self-published sources may inform research, but they do not anchor article notability or evaluative claims
- article sections should stay close to a concise encyclopedic structure unless independent sources justify expansion
