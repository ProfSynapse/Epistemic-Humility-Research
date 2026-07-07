# PR and Git Workflow (pr-workflow)

Keep the repo free of PR spread and shared-checkout git races. This skill is the
standing discipline for branches, worktrees, commits, and PR merges in the
Epistemic-Humility-Research repo. Read it before spawning a subagent that writes
files, before committing housekeeping docs, and before merging PRs.

## Two standing rules (user, 2026-07-07)

1. **Every subagent gets its own git worktree — ingests included.** Never let a
   subagent run `git checkout` / branch / commit inside the canonical checkout.
   Concurrent agents sharing one working tree cause `git checkout` races that put
   commits on the wrong branch and momentarily corrupt local `main` (the
   transformer-circuits ingest hit exactly this and had to self-recover). The
   canonical checkout stays on `main` and is the LEAD's workspace only.

2. **Housekeeping docs commit straight to `main` — no branch, no PR.** Session
   notes, `TODO.md`, `docs/ideas/`, and similar records were spawning a PR each,
   which is the PR spread. Commit them directly to `main`. This RELAXES the older
   blanket "never push main; PR only" rule, but ONLY for housekeeping docs.

## What goes where

| Artifact | Flow |
|----------|------|
| Session notes, `TODO.md`, `docs/ideas/`, backlog edits | Commit directly to `main` |
| Amendments, `experiment*/` code, `experiment/protocol/` docs, `experiments/<slug>/` | One branch = one PR = MERGED before the next amendment branches |
| `synaptic-tuner/` submodule | Its own branch + PR, generic/experiment-agnostic only |
| Skills (`.skills/` + generated mirrors) | Reusable infra: sync workflow, then branch + PR (NOT direct-to-main; skills are not housekeeping docs) |

Governed evidence stays PR-gated. The direct-to-main relaxation is only for
low-risk records.

## Subagent worktrees

Give each file-writing subagent an isolated worktree:

```bash
git worktree add /home/profsynapse/code/ehr-worktrees/<slug> -b <branch> main
```

or spawn the Agent with `isolation: "worktree"`. Tell the subagent its worktree
path and that its HEAD is independent of the canonical checkout, so its commits
are isolated and safe. Read-only subagents (search, analysis) do not need one.

## Merging PRs (a LEAD-kept action)

```bash
gh pr merge <n> --merge --delete-branch      # server-side; safe regardless of local HEAD
gh pr view <n> --json state,mergedAt          # verify it actually merged
```

- The `git: 'remote-https' is not a git command` warning during `gh pr merge` is
  a benign environment quirk in the local-sync step, NOT a merge failure. Always
  confirm with `gh pr view --json state`.
- `--delete-branch` fails if a worktree still holds the branch. Remove the
  worktree first: `git worktree remove [--force] <path>`.
- Batch-merge and keep the open-PR count near zero; PRs left open rot into TODO
  and session-note conflicts.

## Resolving the common TODO / generated-index conflict

`TODO.md` conflicts constantly because many branches touch it. Recipe:

```bash
git checkout --theirs TODO.md                 # take main's version as the base
# re-add ONLY your unique backlog line(s) with an Edit
python3 bin/build_backlog_index.py --write     # regenerate the GENERATED amendment index
python3 bin/build_backlog_index.py --check      # verify up to date
```

The amendment status index block is generated from each `AMENDMENT-*.md` `Status:`
line; never hand-edit inside its fenced block, always regen.

**Session-note numbering:** two parallel sessions collided on `0040` (2026-07-07).
Before creating `docs/sessions/NNNN`, check the directory for the next free number;
if a merge brings in a duplicate, renumber the later one (rename the file AND its
`session_id:` frontmatter).

## Commit conventions

```bash
git -c core.hooksPath=.githooks commit          # hooks are required
```

Trailer on every commit:

```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: <the session URL>
```

No em dashes in committed prose; never use the phrase "load-bearing".

## Direct-to-main commit (housekeeping docs)

Work in the canonical checkout (kept on `main`) or a dedicated `main` worktree:

```bash
git pull --ff-only
# write/edit the session note or TODO
git add docs/sessions/... TODO.md
git -c core.hooksPath=.githooks commit           # with trailer
git push
```

Never push `main` for governed evidence; that stays PR-gated.

## Skill maintenance

Edit the canonical tree under `.skills/pr-workflow/` only. After edits:

```bash
python3 bin/sync_skills.py --write --skill pr-workflow
python3 bin/sync_skills.py --check --skill pr-workflow
```
