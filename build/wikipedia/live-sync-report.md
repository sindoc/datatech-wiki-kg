# Live Wikipedia Sync Report

- Generated: 2026-03-30T12:33:04Z
- Site: en.wikipedia.org
- Archetype: wikipedia-content
- Since: 2026-03-28T00:00:00Z
- Since source: singine time date --offset-days -2

## Targets
- `Collibra` latest=1346185994 revisions-since=4 recentchanges=6 artifacts=`data/wikipedia-ingest/collibra`
  local-vs-live diff: `data/wikipedia-ingest/collibra/local-versus-live.diff`
- `Talk:Collibra` latest=1345898747 revisions-since=1 recentchanges=1 artifacts=`data/wikipedia-ingest/talk-collibra`
- `Template:Data` latest=1345923794 revisions-since=2 recentchanges=2 artifacts=`data/wikipedia-ingest/template-data`
  local-vs-live diff: `data/wikipedia-ingest/template-data/local-versus-live.diff`

## Notes
- `prop=revisions` is used for per-page revision history and latest wikitext.
- `list=recentchanges` is used for page-scoped activity within Wikimedia recent-change retention.
- `action=compare` is used to store baseline-to-current diffs when a prior revision exists before the chosen start timestamp.
