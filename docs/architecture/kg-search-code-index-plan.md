# KG Search and Code/Config Index Plan

## Goal

Build a low-upkeep search layer for the research repo that works out of the box:

- no embedding model required for v0
- no long-running daemon required
- no manual reindex step required before normal search
- deterministic typed extraction for code, configs, docs, and existing KG notes
- bounded results that make `rg` more targeted instead of replacing it outright

The first implementation should be boring: SQLite + FTS5 + AST/config parsers.
Embeddings can be added later as an optional candidate source, not as the source
of truth.

## V0 Architecture

The index lives in `.kg/index.sqlite` and is regenerated incrementally. The
directory is gitignored. Dot-directories are skipped by default unless explicitly
allowlisted later; the index should focus on source, configs, docs, datasets,
and the curated library rather than editor/plugin state.

Tables:

- `files`: path, kind, size, mtime, sha256, parser version.
- `chunks`: searchable text spans with path, kind, symbol, title, and line range.
- `chunks_fts`: SQLite FTS5 mirror of `chunks`.
- `nodes`: typed graph nodes such as files, Python symbols, config keys, and KG notes.
- `edges`: typed graph edges such as `contains`, `defined_in`, `imports`,
  `calls`, `contains_key`, and `references_path`.
- `search_log`: query/result audit trail reserved for later feedback mining.
- `feedback_events`: read/edit/test events reserved for later learning.

Search flow:

1. `kg_search "query"` calls the indexer in changed-file mode.
2. The indexer scans tracked plus untracked non-ignored source files, hashes
   changed files, removes deleted file rows, and reparses only changed files.
3. Search queries FTS5 for seed chunks.
4. Seed files/nodes are expanded through the typed graph with edge-type weights
   so code/config traversal is in the first version, not a later bolt-on.
5. Search reranks FTS hits plus graph-expanded candidates and prints bounded
   results.
6. If raw text search is still needed, the wrapper prints scoped `rg` commands
   against the highest-ranked files.

## Extraction Scope

Python:

- file node: `file:<path>`
- symbol nodes: `code:<path>:<qualname>`
- import nodes: `external:<module>`
- edges: `contains`, `defined_in`, `imports`, local `calls`
- chunks: module summary, class/function bodies, import blocks

YAML / JSON:

- file node: `file:<path>`
- config key nodes: `config:<path>:<key.path>`
- edges: `contains_key`, `references_path` for string values that look like repo
  paths
- chunks: compact key/value summaries
- `.jsonl` / `.csv` artifacts are graph-visible as `data` files but are
  metadata-only by default: size, approximate row count, CSV columns, or sampled
  JSONL keys
- small fixture data is the exception: bounded full-text chunks are indexed so
  tests and smoke examples remain searchable
- large JSON/YAML config-like files are not exploded into key nodes; they fall
  back to bounded text/data handling to avoid hundreds of thousands of low-value
  graph nodes

Markdown / text:

- file node and section chunks
- existing KG note metadata is mirrored into `nodes` when frontmatter contains
  `kg.id`
- edges from existing KG `relationships` are mirrored when available

## Why Embeddings Are Deferred

Most early queries in this repo should be solved by exact structural signals:
paths, config keys, symbols, tests, run records, paper IDs, method names, and
typed KG edges. Embeddings add upkeep: model download, vector dependency,
chunking policy, stale vector handling, and degraded behavior when the vector
extension is unavailable.

V1 can add `sqlite-vec` and MiniLM for prose chunks if FTS+graph misses
conceptual queries. It should remain optional:

- FTS/code graph must work when vectors are absent.
- exact symbol/config/path matches must outrank semantic matches.
- vectors should be updated opportunistically in the same lazy-on-query path.

## Freshness Strategy

Lowest-upkeep trigger:

- lazy update on every `kg_search`
- optional `post-commit` / `post-checkout` hooks later
- no watcher daemon in v0

This keeps the happy path automatic without creating a background service to
debug.

## Learning Later

The `search_log` table is reserved for Nexus-style retrieval feedback:

- log query and returned candidates
- observe later file reads/edits/test runs as implicit positives
- mine skip-above pairs only when the used result was ranked below another
  candidate
- bake off simple rerankers on held-out traces
- promote only when MRR/Recall improve and diversity does not collapse

Feedback signal policy:

| Signal | Meaning | Default weight |
| --- | --- | --- |
| `read` | user or agent opened/read a returned file | weak positive |
| `edit` | user or agent edited a returned file | medium positive |
| `test_pass` | relevant test passed after using/editing returned files | strong positive |
| `test_fail` | relevant test failed after using/editing returned files | weak negative or no label |
| `repeat_query` | user re-queried immediately after result set | possible weak negative |

Reward-hacking guards:

- Never reward a file globally just because it was edited or tests passed.
- Join feedback to a specific search result set and time window.
- Use skip-above negatives only: candidates ranked above the used file become
  negatives; candidates below it are not assumed bad.
- Drop rank-0 uses from training because they only confirm the current ranker.
- Test-pass credit requires a nearby prior read/edit and should be capped.
- Hold out newer traces and require promotion margins before changing rankers.
- Keep exact symbol/path/config-match floors so learning cannot suppress
  deterministic hits.

Candidate rerankers, in likely order:

1. weighted hybrid FTS/graph/path fusion
2. pairwise linear reranker
3. LambdaMART / ranker once enough traces exist
4. optional query-vector adapter if embeddings are enabled
