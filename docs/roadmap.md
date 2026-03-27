# Roadmap

Date: 2026-03-27
Basis: existing Singine, SilkPage, kernel-graph, and public backlog direction

## Phase 1. Repository and publication baseline

Goal:
- make the repository publishable and regenerable from one place

Deliverables:
- canonical Markdown source
- generated Org and Logseq mirrors
- JSON-LD graph
- Atom and RSS feeds
- SilkPage-style XML source tree

Success criteria:
- a single refresh run updates all derived assets
- public process pages exist for plan, backlog, roadmap, and contribution flow

## Phase 2. Collibra article-support layer

Goal:
- establish neutral support material for the Collibra article

Deliverables:
- Collibra source page
- process page
- citation-tracking placeholders
- participant-planning list without private contact data

Success criteria:
- contributors can understand scope, process, and current work without private context

## Phase 3. Kernel and editing-surface synchronization

Goal:
- keep Logseq, Markdown, and Org in practical alignment

Deliverables:
- kernel page sync
- repo-local Logseq mirrors
- Emacs-friendly workflow documentation
- visual graph source artifacts

Success criteria:
- changes in canonical content can be projected into the kernel graph with one command
- maintainers can work from git, Logseq, or Emacs without losing structure

## Phase 4. Command abstraction

Goal:
- expose the main workflow behind one Singine command family

Deliverables:
- `singine wikipedia contrib collibra`
- status, refresh, kernel-sync, site-sync, and mail-preview actions

Success criteria:
- one command can explain and execute the common maintenance flow

## Phase 5. Public website maturity

Goal:
- publish a legible public process and progress surface under `foss.lutino.io/wikipedia`

Deliverables:
- index page
- docs index
- plan, backlog, roadmap, and process pages
- feed links

Success criteria:
- participants and observers can follow the process from the public site
- the website reflects the repository state without hidden steps
