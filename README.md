# DataTech Wikipedia Support KG

This is a standalone repository for Wikipedia-supporting knowledge-graph work on data technology topics, starting with Collibra as both a company and a platform.

The operating model is:

- standalone git repo for public knowledge work
- `singine` for orchestration, feeds, SMTP, and human-led automation
- `silkpage` for publishing paths and site rendering alignment
- canonical Markdown in git, with generated Org and Logseq mirrors
- commit-time refresh of graph, feeds, and notification manifests

The goal is not promotion. The goal is to maintain a neutral, source-driven, openly reviewable research base that can support better Wikipedia contributions and related public knowledge work.

## Scope

- maintain structured facts, entities, and campaign updates
- keep article support material separate from article text
- keep Markdown, Org, and Logseq-compatible views in sync
- publish updates through Atom 1.0 and RSS 1.0
- support manual, opt-in email outreach through `singine smtp`
- avoid private contact data in the public project tree

## Layout

- `config/project.json`: dependency and publication configuration
- `content/markdown/Collibra.md`: canonical article-support source
- `content/org/Collibra.org`: generated Org mirror
- `content/logseq/pages/Collibra.md`: generated Logseq mirror
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
- opt-in communication over broadcast spam
- public facts in repo, private addresses outside repo

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

Maintainer-owned repositories use the canonical local path:

- `/Users/skh/ws/git/github/sindoc/<repo_name>`

That decision is captured in [ADR-0001-maintainer-repository-location.md](/Users/skh/ws/git/github/sindoc/datatech-wiki-kg/adrs/ADR-0001-maintainer-repository-location.md).

## Refresh Everything

```bash
make refresh
```

That syncs the canonical Markdown source into Org and Logseq, rebuilds the JSON-LD knowledge graph, regenerates Atom and RSS feeds, and writes `notifications/pending-update.json`.

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
