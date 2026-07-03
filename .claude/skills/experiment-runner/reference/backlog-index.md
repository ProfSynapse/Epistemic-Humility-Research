# Backlog index — keeping TODO.md current

`TODO.md` at the repo root is the single prioritized view of amendment status and
open work. It has two parts, and the split is what keeps it cheap to maintain:

1. **Amendment status index** — GENERATED. A fenced block
   (`<!-- BEGIN GENERATED: amendment-index ... -->` … `<!-- END GENERATED: ... -->`)
   built by `bin/build_backlog_index.py` from the `Status:` line of every
   `experiment/protocol/AMENDMENT-*.md`, plus any `## 8. Result` / `### Verdict`
   verdict the doc declares. Never hand-edit inside the fence.
2. **Prioritized backlog** — HAND-CURATED prose below the fence. One line per
   item: what/why, tier (A = amendment / L = lab-notebook / P = paper-infra),
   blocker, cost (CPU / GPU / cloud). Survives regeneration.

The generated block also carries a **`WT` (checked-out)** column, derived live
from `git worktree list`: an amendment shows 🔨 when a worktree has its
`amendment-<letter>-*` branch open, and a "Checked out now" line summarizes the
live worktrees. See "Checking out an amendment" below.

Design rationale and status vocabulary: `docs/backlog/PLAN.md`.

## Checking out an amendment (worktree = checkout)

One amendment = one branch = one worktree. **Creating the worktree IS the
check-out** — there is no separate ledger to maintain, so the index can never
drift from reality. The convention:

```bash
# CHECK OUT amendment AF: make its branch + worktree off up-to-date main
git worktree add ../ehr-worktrees/amendment-af -b amendment-af-<slug> main
python3 bin/build_backlog_index.py --write   # AF now shows 🔨 in TODO.md
```

```bash
# CHECK IN when the PR merges: remove the worktree, then regen
git worktree remove ../ehr-worktrees/amendment-af
python3 bin/build_backlog_index.py --write   # 🔨 clears on AF
```

Because the `WT` column reflects *live* worktree state, `--write` / `--check`
results depend on which worktrees exist right now. Regenerate after any
`git worktree add`/`remove` so the committed `TODO.md` matches what is actually
in flight. Branches that are not `amendment-*` (infra branches, detached HEADs)
are listed under "Other worktrees", never mapped to an amendment row.

## When to run the script

The doc's committed `Status:` line is the source of truth — the script does NOT
read session notes or PR state. So re-run it whenever a doc's status changes:

```bash
python3 bin/build_backlog_index.py --write   # rewrite the generated block
python3 bin/build_backlog_index.py --check   # exit 1 if TODO.md is stale (CI-friendly)
python3 bin/build_backlog_index.py --selftest  # parsing/splice unit checks
```

- After you sign, resolve, shelve, or add an amendment doc → `--write`, commit
  the refreshed `TODO.md` in the SAME PR as the status change.
- When a new follow-up is minted in a session → add one hand-written line to the
  `## Prioritized backlog` section. Do not put it in the generated block.

## Gotchas the parser already handles (don't regress them)

- A `Status:` line often quotes user text (`SIGNED — "draft amendment..."`); the
  classifier only reads the leading keyword region, so the quoted "draft" does
  not flip it to DRAFT.
- `FALSIFIER-N` (a numbered kill-condition that fired) → `FALSIFIED`, but
  "falsifier dead / did not fire" → NOT falsified (these read as SUCCESS).
- A doc that cross-references *another* amendment's verdict (e.g. AD citing AB's
  "ambiguous-leaning-negative") must not inherit it — only line-leading verdict
  declarations in *this* doc count.
- A doc `SIGNED` in its `Status:` line may already carry a verdict elsewhere (run
  in a session, verdict in the session note). The table shows `SIGNED` with an
  empty Verdict — that is the honest committed-doc state, not a bug. Update the
  doc's own Status line if you want the table to reflect resolution.

`--selftest` locks in these cases; run it if you touch the parsing regexes.
