# Plan

Date: 2026-03-27
Surface: foss.lutino.io/wikipedia

## Objective

Establish a public, neutral, git-based knowledge graph that supports Wikipedia contributions on data technology topics, beginning with Collibra as a company and as a platform.

## Editorial direction

- keep the repository focused on support material, not advocacy
- synchronize public process, public backlog, and public roadmap
- keep canonical authored content in Markdown
- generate compatible Org, Logseq, XML, RDF, JSON-LD, Atom, and RSS views
- make maintainers aware of changes without creating spam or private-data leakage

## Execution model

- `singine` handles orchestration, refresh, feeds, SMTP preview, and command abstraction
- `silkpage` provides the publication shape for the public website
- the Singine kernel Logseq graph provides the visual working surface
- Emacs and `emacsclient` remain valid local transformation and authoring endpoints

## Initial phases

1. Seed the repository, graph, feeds, and publishable site structure.
2. Create a canonical Collibra support page with plan, backlog, roadmap, and process pages.
3. Synchronize Markdown into Org and Logseq views.
4. Publish the website source under the `foss.lutino.io/wikipedia/` surface.
5. Add the high-level `singine wikipedia contrib collibra` wrapper command.
6. Expand from Collibra to adjacent Data Tech topics only after the initial process is stable.

## Public process commitments

- all public progress should be visible from the website
- all generated artifacts should be reproducible from git
- mailing-list updates remain opt-in
- private notes, credentials, and direct contact details stay outside this repository
