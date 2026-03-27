# ADR-0001: Maintainer-Owned Repository Location

Status: accepted
Date: 2026-03-27

## Context

The maintained repositories for this platform family need one predictable canonical location in the local workspace so that Singine, SilkPage, Logseq, Emacs, XML payload generation, and Collibra import flows can refer to them consistently.

The relevant repositories are maintained under a personal namespace and are used by multiple local toolchains:

- git worktrees and shell automation
- Logseq and Org-compatible authoring
- SilkPage XML publication
- Collibra import and governance metadata exchange
- language-specific tooling across Ballerina, Java, Rust, Go, C, and Python

## Decision

Maintainer-owned repositories use this canonical workspace location:

`/Users/skh/ws/git/github/sindoc/<repo_name>`

For this repository, the canonical path is:

`/Users/skh/ws/git/github/sindoc/datatech-wiki-kg`

## Consequences

- repository-backed automation should prefer the canonical path over ad hoc clones
- command wrappers should point to the canonical path by default
- publication and import payloads should record the canonical path as metadata
- temporary or secondary worktrees may exist, but they are not the canonical maintainer path

## Related

- `site_url`: `https://foss.lutino.io/wikipedia/`
- future ADR publication target: `https://adrs.lutino.io/`
- future RFC publication target: `https://rfcs.lutino.io/`
