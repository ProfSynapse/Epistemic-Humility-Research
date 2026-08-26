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
| Amendments, `experiment*/` code, `docs/protocols/` docs, `experiments/<slug>/` | One dedicated git worktree under `/home/profsynapse/code/ehr-worktrees/<slug>` on its own branch off up-to-date `main` = one PR. Amendments proceed in parallel, each in its own worktree; never stack a second amendment on another amendment's branch or worktree, and never push amendment evidence directly to `main` |
| `synaptic-tuner/` submodule | Its own branch + PR, generic/experiment-agnostic only |
| Skills (`.skills/` + generated mirrors) | Reusable infra: sync workflow, then branch + PR (NOT direct-to-main; skills are not housekeeping docs) |
| Dataset / pool / question-text / eval-row text | NEVER committed (public repo). Stage to the PRIVATE HF dataset repo `professorsynapse/eh-al-prep-staging`; fetch at runtime. See "Datasets are never committed" below |

Governed evidence stays PR-gated. The direct-to-main relaxation is only for
low-risk records.

## Datasets are never committed (this repo is PUBLIC)

This is a PUBLIC repository. Dataset content, pools, question text, and eval-row
text are NEVER committed. Committing question text publicly is a hard-to-reverse
redistribution: pools are gitignored, some derive from a NO-LICENSE FalseQA
source, and the PRIVATE staging repo is the belt-and-suspenders redistribution
boundary (see the `experiments/common/cloud/upload_folder.py` docstring).

Source data is staged to the PRIVATE HF dataset repo
`professorsynapse/eh-al-prep-staging` (`repo_type="dataset"`, private), following
the AK/AP/AM/AL pattern:

```python
# upload (from the cloud/Modal side)
#   experiments/common/cloud/upload_folder.py   # whole extraction dir
#   experiments/common/cloud/upload_result.py   # small result/manifest/rows

# fetch at runtime
from huggingface_hub import hf_hub_download
p = hf_hub_download(repo_id=STAGING_REPO, filename="pools/<file>",
                    repo_type="dataset")
```

What MAY be committed to this repo:

- ID-manifests: seed + n + source repo/file + selected row ids or question
  hashes. No text.
- Fitted-artifact JSON: direction vectors, probes. These are our own outputs, not
  source data.
- Code.

Put committed artifacts under `analysis-committed/`, never the gitignored
`analysis/`.

## If a block stops you, lift it — never work around it

This applies to EVERY subagent that writes files or commits. If the permission
classifier, a hook, or a denied tool BLOCKS an action, the subagent STOPS and
reports the block to the lead/user in its final message. It does NOT construct a
workaround.

A real incident: a J-lens builder's HF upload was blocked by the auto-mode
classifier. Instead of lifting the block, the builder worked around it by
committing the 1000-row question corpus directly into this public repo — exactly
the redistribution the block was protecting against. The correct action was to
stop and lift it to the lead, who holds the authorization.

The principle: a block is a signal to escalate a decision to a human, not an
obstacle to route around. Working around a block substitutes the subagent's
judgment for the human's on precisely the questions (external data movement,
cost, irreversibility) that were escalated to the human. When blocked, stop and
report.

## Subagent worktrees

Give each file-writing subagent an isolated worktree:

```bash
git worktree add /home/profsynapse/code/ehr-worktrees/<slug> -b <branch> main
```

or spawn the Agent with `isolation: "worktree"`. Tell the subagent its worktree
path and that its HEAD is independent of the canonical checkout, so its commits
are isolated and safe. Read-only subagents (search, analysis) do not need one.

Fresh-worktree gotcha (2026-08-17): a new worktree starts with the
synaptic-tuner submodule uninitialized and without the canonical checkout's
gitignored `archive/` data, and the repo-wide pre-commit `exp validate` hook
hard-fails on both. Before the first commit in a fresh worktree run
`git submodule update --init --recursive`, and if `exp validate` still fails
on missing gitignored input paths, symlink those paths from the canonical
checkout (read-only reference; never copy restricted data, never `git add` a
symlink).

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

## Shared-checkout collision (2026-08-10)

The canonical checkout is ONE working tree shared by the lead and every
subagent pointed at it. Two rules, learned the hard way when a lead
`git checkout -b` moved HEAD out from under a librarian mid-task and its
uncommitted edits landed on the wrong branch:

- Never switch branches (checkout/switch/reset) in the canonical checkout
  while any file-writing subagent is working there. Branch moves are a
  lead-only verb, taken only when the tree has no agent in flight.
- When work must land on a DIFFERENT branch than the checkout currently
  has (for example committing one agent's output while another branch is
  active), build the commit in a dedicated worktree under
  `/home/profsynapse/code/ehr-worktrees/`: `git worktree add <dir> <branch>`,
  copy the exact files in, validate/regen there, commit, push, then
  restore the shared tree's tracked files from HEAD (`git checkout HEAD --
  <files>`, not bare `git checkout --`, which restores from the index and
  leaves staged content behind) and `git worktree remove` the temp tree.

## Skill maintenance

Edit the canonical tree under `.skills/pr-workflow/` only. After edits:

```bash
python3 bin/sync_skills.py --write --skill pr-workflow
python3 bin/sync_skills.py --check --skill pr-workflow
```
