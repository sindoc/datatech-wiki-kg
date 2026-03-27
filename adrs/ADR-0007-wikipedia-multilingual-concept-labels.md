# ADR-0007: Wikipedia Multilingual Concept Labels

## Status

Accepted

## Context

Local article-support XML must be able to record the labels used for the same concept across languages. Those labels may differ by language, even if the current Collibra case does not. The vocabulary should remain compatible with SKOS.

## Decision

The generated modular article XML will carry a compact SKOS concept block in the article metadata:

- one concept per article subject
- one `skos:prefLabel` per language
- labels sourced from tracked language-page metadata

## Consequences

- multilingual concept labels are reviewable in git
- drift-analysis and cross-language checks can consume a stable local concept model
- Wikidata remains the live sitelink source of truth, while local XML records editorial expectations
