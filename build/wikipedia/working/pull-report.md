# Wikipedia Pull Report

## Purpose
- Promote the current live Wikipedia article and template into local editable working copies.
- Keep the generated draft next to the pulled live baseline so new edits can be made locally.

## Files
- Live article snapshot: `build/wikipedia/live/Collibra.current.wikitext`
- Live template snapshot: `build/wikipedia/live/Template-Data.current.wikitext`
- Editable article working copy: `build/wikipedia/working/Collibra.working.wikitext`
- Editable template working copy: `build/wikipedia/working/Template-Data.working.wikitext`
- Draft-vs-live article diff: `build/wikipedia/working/Collibra.generated-vs-live.diff`
- Draft-vs-live template diff: `build/wikipedia/working/Template-Data.generated-vs-live.diff`

## Article section comparison
- `Acquisitions` differs: local lines=34, live lines=34
- `History` differs: local lines=3, live lines=3
- `Lead` differs: local lines=15, live lines=15
- `Market position and reception` differs: local lines=3, live lines=1
- `Products` matches
- `References` differs: local lines=27, live lines=25
- `See also` matches

## Template comparison
- Review `build/wikipedia/working/Template-Data.generated-vs-live.diff` for line-level differences.

## Working rule
- Treat `build/wikipedia/working/*.working.wikitext` as the pulled on-wiki baseline for manual reconciliation.
- Treat `build/wikipedia/Collibra.wikitext` and `build/wikipedia/templates/Template-Data-technology.wikitext` as the generated local draft outputs.
- After reconciling changes, update the canonical source or XML/navbox source rather than only editing generated files.
