# AGENTS

This repository is a public knowledge-work repository for Wikipedia-supporting content.

## Operating rules

- Keep the work neutral, source-driven, and publication-oriented.
- Treat `content/markdown/` as the canonical authored source unless a file says otherwise.
- Regenerate derived assets after editing canonical content:
  - `make refresh`
- Do not place personal contact details in version-controlled files.
- Do not imply endorsement by named participants.
- Keep publishable site assets under `site/src/xml/en/` aligned with the repository content.
- Keep Logseq-facing assets under `content/logseq/pages/` aligned with the canonical Markdown.
- Use `notifications/pending-update.json` as a staging artifact, not as proof that mail was sent.

## Local dependencies

- `singine`: `/Users/skh/ws/github/singine`
- `silkpage`: `/Users/skh/ws/git/github/sindoc/silkpage`
- `singine kernel logseq graph`: `/Users/skh/ws/logseq/singine/kernel`

## Preferred workflows

- Refresh derived assets: `make refresh`
- Install git hook: `make install-hooks`
- Sync kernel graph pages: `python3 scripts/sync_kernel_views.py`
- Preview mail commands: `python3 scripts/send_opt_in_update.py`

## Command surface

The intended high-level shell is:

```bash
singine wikipedia contrib collibra
```

That command should remain a wrapper around this repository, not a replacement for the repository.
