# Media Workflow

This repository tracks media as part of the editorial process, but does not assume that a local media file is automatically publishable on Wikipedia or Wikimedia Commons.

## Goals

- keep media provenance and intended use reviewable in git
- separate `reference-only` assets from `publication-safe` assets
- make Wikipedia upload decisions explicit
- keep article, XML apparatus, and media metadata aligned

## Local layout

- `media/assets/`: local working files that are not automatically published
- `media/manifests/`: per-topic upload and rights metadata
- `data/media/`: topic-level media model consumed by the repo, graph, and XML apparatus

## Upload targets

- Wikimedia Commons: use only for files that are freely licensed and acceptable on Commons
- English Wikipedia: use for non-free files only when a valid non-free rationale exists

## Practical rule for this repo

- A company logo is usually tracked here as a non-free logo candidate unless a clearly free license is documented.
- A product screenshot is tracked here as `reference-only` until a Wikipedia-specific non-free rationale is prepared and the intended article use is explicit.

## Minimal metadata required before upload

- local filename
- who created the file
- where it came from
- date created or captured
- rights basis
- intended upload target
- intended article
- intended encyclopedic purpose
- whether a separate non-free rationale is required

## Wikipedia notes

Wikimedia Commons says uploads must be freely licensed and educational, and recommends using the Upload Wizard:
- https://commons.wikimedia.org/wiki/Commons:First_steps/Uploading_files
- https://commons.wikimedia.org/wiki/Commons:Upload_Wizard

English Wikipedia allows non-free content only under strict conditions, including no free equivalent, minimal use, contextual significance, and a file-page rationale:
- https://en.wikipedia.org/wiki/Wikipedia:Non-free_content_criteria
- https://en.wikipedia.org/wiki/Wikipedia:Non-free_use_rationale_guideline
- https://en.wikipedia.org/wiki/Wikipedia:Logos

## Recommended flow

1. Add or update the topic entry in `data/media/`.
2. Create a manifest in `media/manifests/` from the template.
3. Decide `Commons` or `English Wikipedia non-free`.
4. Upload the file manually.
5. Record the uploaded filename and page URL in the manifest and `data/media/`.
6. Only then reference the uploaded filename from article or XML-facing outputs.
