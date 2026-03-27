# ADR-0003: Wikipedia Quality Rule Categories

Status: accepted
Date: 2026-03-27

## Context

Editorial review alone is too easy to apply inconsistently. The repository needs explicit quality-rule categories so that generated article drafts can be checked repeatedly after source updates or text changes.

## Decision

The Wikipedia quality gate is organized into these categories:

- article shape
- sourcing
- neutrality and tone
- due weight and scope
- stability
- maintainability

The rule set is stored in `config/wikipedia_quality_rules.json`. The executable check is `scripts/check_wikipedia_quality.py`. The gate runs against the generated Wikipedia draft, not against notes or apparatus.

## Consequences

- rule changes are visible and reviewable in git
- article revisions can be validated repeatedly with `make quality`
- policy interpretation remains explicit instead of implicit
- quality failures become a normal part of the editorial workflow, not an exceptional event
