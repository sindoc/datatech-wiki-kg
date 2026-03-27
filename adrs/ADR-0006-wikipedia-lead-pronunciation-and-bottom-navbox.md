# ADR-0006: Wikipedia Lead, Pronunciation, and Bottom Navbox

## Status

Accepted

## Context

The generated Wikipedia draft should follow ordinary English Wikipedia article shape rather than exposing local workflow structure. Recent editorial requirements clarified three outward-facing expectations:

- the article should begin with lead prose and must not render an explicit `== Lead ==` heading
- the article opening may carry a pronunciation aid where a stable local form is maintained
- the article should include the `{{Data}}` navbox at the bottom

## Decision

The repository will treat these as enforced output rules for generated Wikipedia drafts:

- lead prose is required before the first section heading
- an explicit `Lead` section heading is forbidden in the outward draft
- pronunciation metadata may be stored in topic metadata and rendered in the opening sentence
- the `{{Data}}` template is appended after `{{reflist}}`

## Consequences

- the outward draft looks more like a normal Wikipedia article and less like an internal brief
- lead rendering becomes a quality-check concern rather than a manual cleanup step
- bottom-of-article navigation remains reproducible from source metadata and templates
