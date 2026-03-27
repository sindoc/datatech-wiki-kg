# ADR-0008: Wikipedia Reference Deduplication

## Status

Accepted

## Context

Repeated rendering of the same source as multiple full citations makes the draft noisy and harder to review. The explicit requirement is that identical sources should not appear as duplicate full references when the same source supports multiple facts.

## Decision

The wikitext generator will emit reusable named references keyed to stable source identifiers. The first use of a source defines the citation body; later uses reuse the named reference. Citation groups must also be deduplicated so the same source is not emitted twice in the same local fact cluster.

## Consequences

- reference output becomes closer to normal Wikipedia editing practice
- repeated source use remains visible without citation-body duplication
- quality checks can detect duplicate reference misuse as a repository policy violation
