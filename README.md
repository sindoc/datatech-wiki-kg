# DataTech Wikipedia Support KG

This is a standalone repository for Wikipedia-supporting knowledge-graph work on data technology topics, starting with Collibra as both a company and a platform.

The operating model is:

- standalone git repo for public knowledge work
- `singine` for orchestration, feeds, SMTP, and human-led automation
- `silkpage` for publishing paths and site rendering alignment
- project archetype `wikipedia-content` declared in `config/project.json`
- canonical Markdown in git, with generated Org and Logseq mirrors
- Zotero as the maintained reference source of truth for the Collibra topic
- generated publication artifacts for Wikipedia, DocBook XML, and RDF/XML
- commit-time refresh of graph, feeds, publication outputs, and notification manifests

The goal is not promotion. The goal is to maintain a neutral, source-driven, openly reviewable research base that can support better Wikipedia contributions and related public knowledge work.

This repository is also intended to make the editorial process visible. Source selection, draft generation, review, publication artifacts, and community-facing coordination can all be tracked in git so that the history of the Collibra entry is inspectable rather than hidden.

## Scope

- maintain structured facts, entities, and campaign updates
- keep article support material separate from article text
- keep Markdown, Org, and Logseq-compatible views in sync
- keep Zotero-managed references and tracked exports aligned with the drafting workflow
- generate Wikipedia-ready and XML/RDF publication artifacts from canonical content
- publish updates through Atom 1.0 and RSS 1.0
- support manual, opt-in email outreach through `singine smtp`
- avoid private contact data in the public project tree

## Layout

- `config/project.json`: dependency and publication configuration
- `content/markdown/Collibra.md`: canonical article-support source
- `data/topics/collibra-topic.json`: topic-scoped people, terms, and editorial metadata for Collibra
- `data/topics/collibra-timeline.json`: topic timeline with confidence-bearing metadata and regulatory context
- `data/topics/collibra-wikipedia.json`: Wikipedia-facing metadata for categories, cross-language pages, and deterministic drift checks
- `data/media/collibra-media.json`: local media references and publication-status metadata
- `media/README.md`: media workflow for Commons and English Wikipedia
- `media/manifests/`: tracked upload manifests for topic media
- `content/org/Collibra.org`: generated Org mirror
- `content/logseq/pages/Collibra.md`: generated Logseq mirror
- `build/wikipedia/Collibra.wikitext`: generated Wikipedia-facing draft output
- `build/wikipedia/userpages/User-Khakbaz.wikitext`: generated user-page wikitext derived from canonical XML
- `build/wikipedia/templates/Template-Data-technology.wikitext`: generated navbox template draft derived from canonical XML
- `xml/wikipedia/collibra/article.xml`: modular xi:include-driven local XML source
- `xml/wikipedia/users/Khakbaz/profile.xml`: canonical XML source for the `User:Khakbaz` user page
- `xml/wikipedia/templates/data-technology-navbox.xml`: canonical XML source for the local `Data technology` navbox draft
- `build/docbook/Collibra.xml`: generated DocBook article output
- `build/rdf/Collibra.rdf`: generated RDF/XML publication output
- `references/zotero/`: tracked Zotero export workspace for the Collibra subcollection
- `references/zotero/Collibra.json`: tracked CSL-JSON import/export artifact for Zotero
- `references/zotero/Collibra.bib`: generated BibTeX output from the tracked Zotero export
- `references/zotero/Collibra.wikipedia.txt`: generated Wikipedia citation-template snippets
- `docs/plan.md`: public execution plan
- `docs/backlog.md`: public backlog
- `docs/roadmap.md`: staged roadmap
- `docs/process.md`: user-facing draft process
- `adrs/`: architecture decision records in Markdown and XML
- `rfcs/`: request-for-change documents
- `protocol/`: standards-based Singine process payloads
- `visuals/`: visual artifacts such as Mermaid diagrams
- `xml/payloads/`: XML payload shapes for ADR/RFC exchange and Collibra import
- `data/collibra-campaign.json`: campaign metadata and update entries
- `graph/collibra-support.jsonld`: generated knowledge graph in JSON-LD
- `outreach/proposed_participants.json`: named people to invite, without contact details
- `outreach/subscribers.template.json`: opt-in subscriber template for local use
- `templates/email_invitation.txt`: neutral invitation draft
- `scripts/sync_sources.py`: sync Markdown into Org and Logseq representations
- `scripts/build_graph.py`: rebuild the JSON-LD graph
- `scripts/generate_campaign_assets.py`: generates Atom and RSS outputs
- `scripts/render_media_manifest.py`: generates the concrete topic media manifest from tracked assets and template metadata
- `scripts/render_publication_artifacts.py`: generates Wikipedia, DocBook, and RDF publication artifacts
- `scripts/render_user_pages.py`: renders simple Wikipedia user pages from canonical XML sources
- `scripts/render_navboxes.py`: renders Wikipedia navbox drafts from canonical XML sources
- `scripts/analyze_wikipedia_language_drift.py`: compares the `en`, `nl`, and `no` Collibra entries using sections, categories, references, and named fact atoms without an LLM
- `scripts/ingest_wikipedia_changes.py`: ingests live MediaWiki revisions, diffs, and talk-page activity into tracked repo artifacts
- `scripts/check_wikipedia_quality.py`: runs categorized article checks against the generated Wikipedia draft
- `xml/wikipedia/collibra/`: version-managed modular article source and editorial apparatus
- `scripts/refresh_repo.py`: run all refresh steps and prepare a pending notification manifest
- `scripts/install_hooks.py`: install the repo-local `post-commit` hook
- `scripts/sync_kernel_views.py`: project selected content into the Singine kernel Logseq graph
- `scripts/send_opt_in_update.py`: prints or sends individualized updates to opted-in recipients
- `site/src/xml/en/`: SilkPage-style publication source for `foss.lutino.io/wikipedia/`
- `notifications/`: generated pending maintainer notification payloads
- `feeds/`: generated feed output

## Principles

- neutrality over advocacy
- verifiability over insider memory
- references maintained in Zotero before they are treated as durable editorial inputs
- opt-in communication over broadcast spam
- public facts in repo, private addresses outside repo
- transparent edit, review, and publication cycles over opaque revision handling

Those principles are recorded as ADRs under `adrs/`, including authoring principles, quality-rule categories, naming conventions, and RFC-based synchronization with the live Wikipedia article.

## Dependencies

Local dependency paths are declared in `config/project.json`:

- `singine_root`: `/Users/skh/ws/git/github/sindoc/singine`
- `silkpage_root`: `/Users/skh/ws/git/github/sindoc/silkpage`
- `lutino_site_root`: `/Users/skh/ws/git/lutino.io/lutino`

Kernel and editor alignment is declared in `config/kernel.json`:

- `kernel_graph_root`: `/Users/skh/ws/logseq/singine/kernel`
- `emacsclient_bin`: `emacsclient`
- `logseq_api_url`: `http://127.0.0.1:12315`

The intended publication URL is `https://foss.lutino.io/wikipedia/`.

Reference-management and export expectations are declared in `config/project.json`:

- `references.zotero_collection`: `My Library/Collibra`
- `references.tracked_exports_dir`: `references/zotero`

The expected practice is to maintain all references in the Zotero `Collibra` subcollection under `My Library`, then export tracked derivatives such as BibTeX and structured metadata into `references/zotero/` so they can participate in review and publication workflows.

If collaborative source curation is needed, the same tracked `Collibra.json` artifact can be imported into a Zotero group library and re-exported after review.

Topic-specific people and editorial terms are tracked separately from the article draft in `data/topics/`. That model is intended to be consumable by Singine, SilkPage, and this repository without forcing every tracked person or term directly into the outward-facing Wikipedia article.

The repository also declares an explicit archetype and lightweight metamodel in `config/project.json` so wrappers can verify they are operating inside a `wikipedia-content` project before mutating files or calling external APIs.

The same pattern applies to timeline and media metadata: the repository keeps deeper provenance, confidence, and rights context locally even when the outward article remains short.

Media handling is explicit rather than implicit. Local files, upload targets, non-free rationales, and publication status are tracked before media is referenced in article-facing outputs.

Maintainer-owned repositories use the canonical local path:

- `/Users/skh/ws/git/github/sindoc/<repo_name>`

That decision is captured in [ADR-0001-maintainer-repository-location.md](/Users/skh/ws/git/github/sindoc/datatech-wiki-kg/adrs/ADR-0001-maintainer-repository-location.md).

## Refresh Everything

```bash
make refresh
```

That syncs the canonical Markdown source into Org and Logseq, rebuilds the JSON-LD knowledge graph, regenerates Atom and RSS feeds, renders Wikipedia/DocBook/RDF publication artifacts, renders configured user pages and navboxes from XML, and writes `notifications/pending-update.json`.

It also regenerates `media/manifests/collibra-assets.json` from the files present under `media/assets/` and the tracked template metadata.

## Generate reference exports

```bash
make refs
```

That renders tracked derivatives from `references/zotero/Collibra.json`, including BibTeX and Wikipedia citation-template output.

## Generate reference workbench artifacts

```bash
make publish
make ref-workbench
```

That renders:

- `build/reference-workbench/collibra-reference-map.json`
- `build/reference-workbench/reference-workbench.xml`
- `build/reference-workbench/index.html`
- `site/src/xml/en/docs/reference-workbench.xml`

The split is intentional:

- this repository emits semantic content and support metadata
- SilkPage is the intended HTML rendering layer for the semantic XML page
- Singine is the intended execution and serving layer

The generated workbench includes:

- claim-to-source links from the built article
- reference reuse across multiple claim lines
- a local coverage-health metric for claim support
- a local credibility metric for sources
- factor lineage for both metrics on the same page

These metrics are editorial support heuristics only. They do not replace source
 review, publication judgment, or Wikipedia policy analysis.

## Generate media manifest

```bash
make media
```

That detects topic media under `media/assets/` and writes the concrete manifest to `media/manifests/collibra-assets.json`.

## Generate publication artifacts

```bash
make publish
```

That renders:

- `build/wikipedia/Collibra.wikitext`
- `build/wikipedia/userpages/User-Khakbaz.wikitext`
- `xml/wikipedia/collibra/article.xml`
- `build/docbook/Collibra.xml`
- `build/rdf/Collibra.rdf`

The intent is to keep Wikipedia-facing and XML/RDF-facing publication outputs derivable from the canonical research brief at all times.

The publication path is DocBook-first: the modular local XML source uses `xi:include` so sections, apparatus, and bibliography can evolve independently, while the compiled article XML remains the stable intermediate for HTML, SVG, MathML, and LaTeX-aware downstream processing.

The draft metadata for Collibra also carries explicit `See also` links and candidate category tags so broader context such as `[[Data governance]]` can be kept in the generated wikitext rather than added ad hoc.

## Run article quality checks

```bash
make quality
```

That evaluates the generated article against categorized checks for article shape, sourcing, neutrality and tone, due weight and scope, stability, and maintainability. The report is written under `build/quality/`.

The governing rule set lives in `config/wikipedia_quality_rules.json`. If the policy contract changes, update the ADRs and rules together.

## Analyze cross-language drift

```bash
make drift
```

That compares the configured `Collibra` entries across `en.wikipedia.org`, `nl.wikipedia.org`, and `no.wikipedia.org` without an LLM. The current implementation uses deterministic signals only: section structure, category overlap, reference counts, Wikidata linkage presence, and coverage of named fact atoms such as founders and acquisition names.

## Ingest live Wikipedia changes

```bash
make wiki-ingest
```

That fetches live MediaWiki state for `Collibra`, `Talk:Collibra`, and `Template:Data` using the official Action API and stores the results under `data/wikipedia-ingest/`.

The ingest includes:

- latest wikitext snapshots
- revision history since the configured timestamp
- page-scoped recent-changes entries
- baseline-to-current compare output when a prior revision exists
- a repo-local diff between live article/template text and the corresponding local draft when configured

The default start timestamp is conservative and can be overridden:

```bash
python3 scripts/ingest_wikipedia_changes.py --since 2026-03-29T00:00:00Z
```

You can also target specific pages and override local comparisons:

```bash
python3 scripts/ingest_wikipedia_changes.py \
  --page Collibra \
  --page Talk:Collibra \
  --page Template:Data \
  --compare-local "Collibra=build/wikipedia/Collibra.wikitext" \
  --compare-local "Template:Data=build/wikipedia/templates/Template-Data-technology.wikitext"
```

This workflow uses `prop=revisions`, `list=recentchanges`, and `action=compare` from the MediaWiki Action API rather than screen-scraping with `curl` or `wget`.

By default, the ingest cutoff is derived from Singine's time surface:

```bash
python3 -m singine.command time date --offset-days -2 --json
```

That value is then normalized to a UTC day boundary for the MediaWiki fetch.

The same workflow is available through the documented Singine wrapper:

```bash
python3 -m singine.command wikipedia contrib collibra --action ingest-live --json
```

## Pull live changes into local working copies

```bash
make wiki-pull
```

That does the next step after ingest:

- copies the current live article snapshot into `build/wikipedia/live/Collibra.current.wikitext`
- copies the current live template snapshot into `build/wikipedia/live/Template-Data.current.wikitext`
- creates local editable working baselines under `build/wikipedia/working/`
- writes draft-vs-live diffs and a pull report for manual reconciliation

The intended cycle is:

```bash
make wiki-ingest
make wiki-pull
```

Then review and edit:

- `build/wikipedia/working/Collibra.working.wikitext`
- `build/wikipedia/working/Template-Data.working.wikitext`
- `build/wikipedia/working/pull-report.md`

Those working copies represent the latest on-wiki baseline pulled back into the repo. Once you decide which live edits should become durable local truth, fold them back into the canonical Markdown or XML/navbox sources and regenerate derived artifacts.

## Keep an audit trail

```bash
make wiki-audit
```

The live-ingest flow also runs this automatically. It writes a registry under `data/wikipedia-audit/`:

- `registry.json`: structured audit payload with metadata and rows
- `registry.jsonl`: append-friendly row format for downstream tooling
- `registry.csv`: spreadsheet-friendly export
- `registry.md`: concise summary

This audit registry stores change metadata only:

- title
- timestamp
- user
- temporary-account flag
- revision id
- parent revision id
- recent-change id
- change type
- size delta
- edit summary / log comment
- tags

It does not duplicate the full textual page content or compare bodies. Those remain under `data/wikipedia-ingest/`.

## Install Commit Hook

```bash
make install-hooks
```

After that, each local commit refreshes the derived artifacts automatically. The hook does not send mail.

## Sync the kernel graph view

```bash
make kernel-sync
```

That projects selected repository content into the existing Singine kernel Logseq graph namespace.

## Run the end-to-end test case

```bash
make test-case
```

That runs refresh, kernel sync, and the `singine wikipedia contrib collibra` wrapper, then verifies that the expected derived artifacts and kernel pages exist.

## Editorial workflow

The recommended cycle for the Collibra entry is:

1. Maintain and curate sources in Zotero under `My Library/Collibra`.
2. Keep `references/zotero/Collibra.json` aligned with the curated Zotero collection, whether personal or group-managed.
3. Run `make refs` to regenerate tracked reference derivatives.
4. Update `content/markdown/Collibra.md` as the canonical editorial brief.
5. Run `make refresh` to regenerate mirrors and publication artifacts.
6. Review the generated reference, Wikipedia, DocBook, RDF, graph, and feed outputs in git.
7. Capture review comments and publication decisions in the repository history.
8. Use the generated outputs for Wikipedia drafting, PDF production, XML/RDF publication, and community-facing discussion support.
9. For images, complete the media manifest and upload workflow before referencing any uploaded filename in article-facing outputs.

If the live Wikipedia article later changes in a way that should be reflected locally, record the reconciliation first as an RFC under `rfcs/`, then update the canonical source and rerun the checks.

Naming conventions used by this workflow are stable and intentional:

- `ADR-XXXX-slug.md` for decisions
- `RFC-XXXX-slug.md` for proposed change records
- `NN-slug.xml` for ordered modular article sections

This is intentionally a visible editorial connection between references, draft text, review, and publication. The aim is to keep the Collibra entry's edit and review process transparent and reproducible.

The local XML model is intentionally richer than the pasteable Wikipedia draft. It can carry discussion points, editorial notes, annotations, and other publication apparatus without forcing those materials into the outward-facing encyclopedia text.

## Visualize the draft process

```bash
make visualize
```

That reads `protocol/wikipedia-contrib-process.xml` as the canonical Singine protocol payload and writes the derived process diagram to `visuals/wikipedia-contrib-process.mmd`.

## Generate feeds

```bash
python3 scripts/generate_campaign_assets.py
```

## Sync content representations

```bash
python3 scripts/sync_sources.py
```

## Rebuild the graph

```bash
python3 scripts/build_graph.py
```

## Render publication outputs

```bash
python3 scripts/render_publication_artifacts.py
```

## Preview outreach

```bash
python3 scripts/send_opt_in_update.py
```

## Send outreach to opted-in recipients

The sender is intentionally manual. By default the script prints commands only.

```bash
python3 scripts/send_opt_in_update.py --send
```

That command expects a local `outreach/subscribers.json` file based on the provided template and an operational `singine smtp` configuration.
