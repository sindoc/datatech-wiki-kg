# ADR-0005: RFC-Based Synchronization With the Live Wikipedia Article

Status: accepted
Date: 2026-03-27

## Context

Once a live Wikipedia article exists, it may be updated by other editors outside this repository. The local source must remain reviewable without pretending that off-repo changes do not exist.

## Decision

When the live Wikipedia article materially diverges from the locally maintained source, the repository records the reconciliation as an RFC before changing the canonical source or quality rules.

An RFC should capture:

- the observed live-article change
- the relevant talk-page or edit-summary context when available
- the proposed local-source update
- any required citation, structure, or wording changes
- any required updates to quality rules or generation logic

After RFC review, the canonical source and derived artifacts are updated, then `make refresh` and `make quality` are rerun.

## Consequences

- live Wikipedia changes become inspectable repository events
- discussion and article maintenance remain linked
- rule changes and content changes are reviewed together when needed
