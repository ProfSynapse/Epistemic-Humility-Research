# Launch plan: j-space-layer-contrast-rep2-multisource

Not a claims surface. Operational notes for getting from this draft scaffold
to a signable instrument. See `AMENDMENT.md` for the design and `NOTEBOOK.md`
for the dated run log.

## Rebase-before-sign requirement (lead directive, 2026-07-09)

This branch (`exp/j-space-layer-contrast-rep2-multisource`) was cut from
`main` at commit `6c70bb33`. Since then, `main` has moved: PR #262
(`infra/checkpointed-runner`) and PR #263 (`agent/jspace-full-run`, rep1's
own resolve) both merged, and a further commit
(`15722fb9 Bump synaptic-tuner to merged RunLog (Synaptic-Tuner PR #141)`)
bumped this repo's `synaptic-tuner` submodule pin to `cd30d482` on `main`.

Verified directly (read-only `git fetch`, no local state changed): `origin/main`
is now at `a3e7599d`, three commits ahead of this branch's fork point, and the
submodule tree at `cd30d482` DOES contain `shared/utilities/run_log.py`
(confirmed via `git ls-tree cd30d482... shared/utilities/`).

**Consequence:** `pipeline_multisource.py:load_run_log_class`'s current
availability-gate message (documented in `AMENDMENT.md`'s "Per-row
persistence (RunLog)" section) describes a state that is already stale for
`main`, though it remains accurate for THIS branch until it rebases. Concretely:

1. **This branch must rebase onto current `main` before `bin/exp sign`.**
   After the rebase, this repo's `synaptic-tuner` submodule pointer will be
   `cd30d482` (or later), and `shared/utilities/run_log.py` resolves directly
   from the pinned submodule -- no separate checkout of the tuner's
   `feature/runlog` branch is needed at that point.
2. `pipeline_multisource.py:load_run_log_class` needs no code change for
   this: it already imports `from shared.utilities.run_log import RunLog,
   RunLogError` off whatever `synaptic-tuner/` is checked out at `TUNER_DIR`
   (`REPO_ROOT / "synaptic-tuner"`). The import failure it currently raises
   (submodule not yet bumped in this worktree) will resolve on its own once
   the rebase lands the new pin. Do not hand-patch the error message before
   sign; let the rebase make it moot.
3. The rebase is NOT done as part of this scaffold. Per the standing rule
   (no signing, no pushing, no PRs from this task), only the lead/user
   decides when to rebase and re-verify `bin/exp validate` + the smoke
   command against the post-rebase submodule pin.

## Mining / extraction / smoke: already run in this scaffold pass (2026-07-09)

Mining, anchor extraction, and the 8-row smoke are DONE, not pending -- see
`NOTEBOOK.md` for the full dated log. Summary: the bare default invocation
(`mine_multisource_pool.py`, no args, per-source stop-targets 70/80/70)
under-provisioned the total G0 floor (146 confabs < 200, though both
harder-source floors were already met at 70/70). Diagnosis showed
`kuq_ku_unknown_x` was genuinely exhausted at its full post-exclusion pool
(2,491/2,491, 6 confabs), while `kuq_ku_unknown` and `selfaware_unanswerable`
had simply stopped early at their own operational stop-targets with ample
unscanned supply remaining (1,830 and 89 candidates respectively). Resumed
the SAME script (row-level cache skips already-scanned rows) with
`--target-kuq-ku-unknown 999 --target-selfaware-unanswerable 999` to exhaust
remaining supply in those two sources under the unchanged loaders/exclusion
rule/floors. Final: `total=221 by_source={'kuq_ku_unknown': 139,
'kuq_ku_unknown_x': 6, 'selfaware_unanswerable': 76}` -- G0 mining floors
PASS (221 >= 200; 139 >= 40 and 76 >= 40 for the two harder sources).
Anchor extraction covers 221/221. The 8-row smoke passed
(`g0_smoke_pass: true`; exact doses; readback within tol on all four arms;
zero collapse) and RunLog per-row persistence was confirmed operative
(`analysis/runlog/smoke/hs{23,26,29,34}.jsonl`, 8 lines each, incrementing
mtimes across the run). The smoke required a TEMPORARY, non-committed
detached checkout of the submodule to the already-merged `cd30d482`
(tuner `main`, PR #141) to resolve `shared.utilities.run_log`, since this
worktree's own submodule pin (`e4ca5d4`) predates that merge; the submodule
was restored to `e4ca5d4` immediately after and verified clean
(`git status --short -- synaptic-tuner`) before any commit. This is a
one-time manual workaround for smoke-testing ahead of sign, not a
substitute for the rebase below.

If mining/extraction/smoke ever need to be rerun from scratch on this
branch (e.g. after the rebase), use the corrected invocation, not the bare
default:

```
python experiments/j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py \
  --target-kuq-ku-unknown 999 --target-kuq-ku-unknown-x 80 \
  --target-selfaware-unanswerable 999
python experiments/j-space-layer-contrast-rep2-multisource/materialize_known_side_reuse.py
python experiments/j-space-layer-contrast-rep2-multisource/extract_multisource_confab_anchor.py
PYTHONPATH=synaptic-tuner python experiments/j-space-layer-contrast-rep2-multisource/run_contrast.py --mode smoke --n-rows 8
```

## Full run: NOT authorized by this scaffold

```
PYTHONPATH=synaptic-tuner python experiments/j-space-layer-contrast-rep2-multisource/run_contrast.py --mode full --i-know-this-is-the-multisource-replication-run
python experiments/j-space-layer-contrast-rep2-multisource/analyze_paired_outcomes.py --mode full
```

The full-mode command is gated behind `--i-know-this-is-the-multisource-replication-run`
and is NOT authorized by this scaffold; it requires `bin/exp sign` first (and,
per above, a rebase onto current `main` first).
