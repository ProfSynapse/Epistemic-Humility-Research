---
name: experiment-wrapup
description: Execute the downstream wrap-up after a signed experiment produces its terminal numbers and the LEAD has adjudicated the verdict - write the AMENDMENT Outcome, run bin/exp resolve, update the cross-experiment registries (family-layer-map for atlas cells, prediction-scoreboard for scored cells), open the resolve PR, commit the living tracking docs to main, and hand off KG ingest. This is the mechanical half of a resolve and is delegable to a smaller model, given a locked adjudication packet from the lead. It never decides the verdict, the falsifier call, or the scoreboard scores - those are lead-only judgment and are inputs to this skill, not outputs of it.
allowed-tools: Read, Bash, Write, Edit, Grep, Glob
---

# Experiment wrap-up

When a signed experiment's run has produced its terminal numbers, turning
that into a resolved, registry-consistent, PR-ready state is a fixed
procedure. The judgment in it - what the verdict is, whether the falsifier
fired, who wins the prediction, whether the result needs a red-team pass -
belongs to the lead. Everything after that judgment is mechanical: transcribe
the adjudication into the governed doc, flip the manifest, update the two
cross-experiment registries, open the PR, commit the living docs, hand off KG
ingest. This skill is that mechanical half, written so the lead can delegate it
to a sonnet/haiku subagent instead of spending its own context on it.

## The boundary (read this first)

**The lead KEEPS and supplies as INPUT** (never re-decided here):
- the verdict and terminal status (`resolved` / `null-result` / `falsified` /
  `historical`);
- the falsifier call (fired / not fired) and why;
- the prediction-scoreboard scores (user WIN/LOSS/TIE, orchestrator
  WIN/LOSS/TIE) and the one-line justification for each;
- which numbers are load-bearing and their source artifact;
- whether a red-team pass was required and its outcome;
- any credit/nuance to record (e.g. a losing call whose intuition was right on
  a different measure).

**This skill EXECUTES** against that packet:
1. re-derive the load-bearing numbers from the committed artifact (trust no
   relayed number);
2. write the AMENDMENT `## Outcome`;
3. `bin/exp resolve`;
4. update the cross-experiment registries;
5. `bin/exp regen`, branch commit, push, open PR;
6. commit the living tracking docs to main;
7. hand KG ingest to the librarian.

If any step surfaces a number that contradicts the adjudication packet, STOP
and report to the lead. A mismatch between the packet and the committed
artifact is a lead decision, never a silent reconciliation.

## Adjudication packet (what the lead hands you)

The lead's delegation message must contain, or the subagent must ask for, all
of:

```
slug:            <experiment slug>
worktree:        <path to the branch worktree>   # governed evidence lives here
branch:          exp/<slug>
terminal_status: resolved | null-result | falsified | historical
committed_artifact: <path under analysis-committed/ holding the numbers>
load_bearing_numbers:                # each with the value the lead adjudicated on
  - <name>: <value>  (re-derive from committed_artifact)
falsifier: FIRED | NOT_FIRED  + one-line reason
verdict_oneline: <goes into experiment.yaml verdict: and the Outcome header>
scoreboard:                          # omit rows that do not apply
  user: WIN | LOSS | TIE | (no call - unilateral)  + reason
  orchestrator: WIN | LOSS | TIE | (no call)  + reason
registries_to_touch:                 # lead names them
  - family-layer-map    # atlas cells only
  - prediction-scoreboard
credit_or_nuance: <optional prose the lead wants recorded>
red_team: <not required | done, outcome | required - STOP>
```

## Invariants (binding on every step)

- **READ BEFORE YOU CITE.** The AMENDMENT.md + experiment.yaml of the cell are
  the sole source of truth for its facts; the committed artifact under
  `analysis-committed/` is the sole source for its numbers. Re-derive every
  load-bearing number yourself before writing it anywhere.
- **KG-search-first.** Any repo lookup starts with `bin/search <terms>` before
  rg/grep or a search subagent.
- **Governed evidence vs living docs split.** The AMENDMENT.md Outcome,
  experiment.yaml verdict/status, and the regenerated `experiments/REGISTRY.md`
  + `registry.json` are GOVERNED EVIDENCE: they go on the branch worktree and
  into the resolve PR, never straight to main. The cross-experiment tracking
  docs (`docs/atlas/family-layer-map.md`, `docs/prediction-scoreboard.md`) are
  LIVING DOCS committed straight to main from the canonical checkout. KG nodes
  under `library/` also go straight to main.
- **Supersession is decided explicitly, never by omission.** Step 7 emits a
  `SUPERSEDES:` line on every resolve, either naming the superseded node ids or
  stating `none` with the searches that justify it. A resolve that overturns a
  prior reading and adds a node beside it, with no pointer, leaves two live
  claims and is not finished.
- **PR merge needs explicit per-PR user approval.** This skill opens the PR; it
  never merges it.
- **Containment.** Confirm the committed artifact is ID-free (no question /
  answer / alias text, no token_ids, no row_key lists) before it is staged;
  row-level stays gitignored under `analysis/`.
- **Prose hygiene.** No em dashes in committed prose (en dashes for numeric
  ranges are fine); do not use the phrase "load-bearing" in committed prose.
- **Commits** use `git -c core.hooksPath=.githooks commit` with trailers:
  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  Claude-Session: <the session URL the lead passes>
  ```

## Procedure

### 1. Verify the numbers (never trust a relayed number)
Read the `committed_artifact` and independently re-derive every entry in
`load_bearing_numbers`. If the artifact is under a root-owned bind-mount
directory left by a container run, read it directly (read does not need write);
you only need write permission for the commit, which is on tracked files
elsewhere. If any re-derived number disagrees with the packet, STOP and report.

### 2. Write the AMENDMENT `## Outcome`
In `<worktree>/experiments/<slug>/AMENDMENT.md`, replace the placeholder
Outcome with: the verdict header (from `verdict_oneline`), a run-provenance
block, the gate results, the falsifier adjudication, the scoreboard
adjudication (transcribing the lead's scores + reasons verbatim, plus any
`credit_or_nuance`), and a scientific-note paragraph if the packet supplies
one. Also fill the `## Predictions scoreboard` resolution line if the cell has
that section. Mirror the structure of a recent resolved sibling (for atlas
cells, `experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`).

### 3. Resolve the manifest
```
bin/exp resolve <slug> --status <terminal_status> --verdict "<verdict_oneline + the key numbers>"
```
This flips `experiment.yaml` status and stamps the verdict. It prints a
kg-ingest checklist (handled in step 7).

### 4. Update the cross-experiment registries (only those named)
- **family-layer-map** (`docs/atlas/family-layer-map.md`, atlas cells): the
  file's own rule is that a row is added/updated only from a signed AND
  resolved doc - which this now is. Update or add the family row with the
  profile peak, the read band, the best clean-control layers, and the
  provenance (doc path + resolve date). Update the "Cross-family pattern"
  standing summary counts. Add/extend the comparability note if the packet
  flags a confound (e.g. the doubt-axis norm/position confound).
- **prediction-scoreboard** (`docs/prediction-scoreboard.md`): add the row
  (user prediction | orchestrator prediction | outcome | user-score /
  orchestrator-score), transcribing the packet's scores and reasons. Update
  the running tally line. If the cell has no competing user call, say so and
  leave the tally unmoved (unilateral scoring precedent).

### 5. Regenerate, commit governed evidence, push, open PR
```
cd <worktree>
bin/exp regen                      # refresh REGISTRY.md + registry.json (stale after a status flip)
git add -A experiments/<slug> experiments/REGISTRY.md experiments/registry.json
git -c core.hooksPath=.githooks commit -m "<slug>: RESOLVED - <one-line verdict + score>" # + trailers
git push -u origin exp/<slug>
gh pr create --base main --head exp/<slug> --title "..." --body "..."   # do NOT merge
```
The pre-commit hook runs `bin/exp validate` + registry-staleness + KG
validation; a non-zero exit is a real failure (usually a stale registry - run
`bin/exp regen` and re-stage). Watch for the misleading rtk "ok" prefix; verify
`git log --oneline -1` actually advanced.

### 6. Commit the living tracking docs to main
From the canonical checkout (NOT the worktree):
```
cd <canonical checkout>
git add docs/atlas/family-layer-map.md docs/prediction-scoreboard.md   # whichever were touched
git -c core.hooksPath=.githooks commit -m "Atlas + scoreboard: <slug> resolved ..." # + trailers
git push origin main
```

### 7. Hand off KG ingest
Delegate to the `librarian` (kg-ingest skill): create/extend the typed nodes
for the resolved result, run the Move-4 finalize tail (validate is the gate),
record the returned node ids in the branch `experiment.yaml` `kg:` list
(committed on the branch, not main), and commit the `library/` node files to
main. Restate READ-BEFORE-CITE and KG-search-first in the delegation. This is a
separate task, not something this skill's own subagent does inline, because it
edits `library/` on main and the branch `kg:` list in two different checkouts.

**The supersession decision is mandatory and explicit.** Every resolve either
supersedes prior graph nodes or does not, and the wrap-up must say WHICH in
writing. Do not leave it implicit: a resolve that overturns a prior reading and
silently adds a node beside it leaves two live claims and no pointer, which is
how the graph tells a future reader a false thing.

Before handing off, run:

```bash
bin/search <the question this result answers, phrased 3 ways> --limit 10
bin/search <same> --include-deprecated --limit 10
```

Then record one of these two lines in the handoff packet and in the report to
the lead:

- `SUPERSEDES: <old kg.id> -> <new kg.id>` (one line per superseded node), or
- `SUPERSEDES: none — <one sentence on what you searched and why nothing is
  overturned>`.

For each superseded node the librarian sets `kg.status: deprecated` and
`kg.deprecated_by: <successor kg.id>` per the Supersession convention in the
knowledge-graph skill's `references/relationship-schema.md`, then re-runs the
retrieval check to confirm the successor now ranks at or above where the stale
node ranked (kg-ingest Move 4e).

Scope note: a result that holds only at a new site, family, or dose does NOT
supersede the earlier one. It narrows it. Add the scope qualifier to both nodes
rather than deprecating a result that is still true where it was measured. If
the two genuinely cannot both hold and you cannot tell which wins, add a
`contradicts` edge and escalate to the lead. `contradicts` is a flag for
adjudication, not a verdict, and the conflict pass in `analyze_kg.py` keeps
reporting it until it is resolved. Choosing the verdict is lead-only.

### 8. Report to the lead
Report: the re-derived numbers (confirming they match the packet), the resolve
status, the PR number, the main commit sha for the living docs, the
`SUPERSEDES:` line from step 7, and that KG ingest is delegated. State plainly
that PR merge awaits the user's approval.

## What this skill does NOT do
- decide the verdict, falsifier, or scores (lead-only inputs);
- merge the PR (explicit user approval);
- upgrade an exploratory result to a claim (confirmatory-replication rule);
- move a goalpost or reconcile a packet/artifact mismatch (STOP and report);
- edit pinned instrument files (a post-run edit voids pins; if the wrap-up
  reveals an instrument bug, that is a lead-adjudicated repin, not a wrap-up
  step).

## Skill maintenance
Edit the canonical tree under `.skills/experiment-wrapup/` only. `.agents/` and
`.claude/` are generated mirrors. After canonical edits:
```
python3 bin/sync_skills.py --write --skill experiment-wrapup
python3 bin/sync_skills.py --check --skill experiment-wrapup
```
