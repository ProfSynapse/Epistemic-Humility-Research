# doubt-gated-caution-tighten notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s header claimed a draft/not-signed (or otherwise stale) status that contradicted `experiment.yaml`'s machine state (`status: resolved`), which has read verdict "doubt-gated caution snap passed as a training-free selective tighten instrument" on record. Corrected the AMENDMENT.md header ("Status:" line) to match the machine state. Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction. No signed content (question, prediction, falsifier, gates, Outcome) touched.

- 2026-07-07 -- HARNESS BUILD (harness-builder agent, local 3090, free). Scaffolded
  via `bin/exp new doubt-gated-caution-tighten --type steer-cell`. Ported the fixed
  generation contract and gate/snap logic from the sibling
  `two-signal-caution-regulation-instruct` diagnostic (worktree
  `/home/profsynapse/code/ehr-worktrees/two-signal`, branch
  `exp/two-signal-caution-regulation-instruct`, HEAD `8f277410`), which is not
  merged, so every reused module is a logic-port into this experiment's own
  files (`gen_lib.py`, `grader.py`, `model_lib.py`,
  `experiments/common/renders/ah_a0_raw_base_render.py`), not a cross-worktree
  import.

  Ran, on the local free 3090:
  1. `extract_l34_anchor.py` -- fresh bf16 L34 extraction, 1,427 rows
     (known_correct_answered=89, unknown_refused=1029, confab=309; no
     answerable_refused -- release is abandoned). ~61s.
  2. `split_fit_heldout.py` -- stratified FIT/HELD-OUT split, fit_frac=0.40,
     seed=20260707. confab fit=124/held_out=185; known_correct_answered
     fit=36/held_out=53. `analysis-committed/split_manifest.json` (ID-only).
  3. `build_directions.py --verify-reproducible` -- refit u_d/pos_ctrl/neg_ctrl/c_hat
     on the FIT split only, `LogisticRegression(random_state=20260707)` PINNED
     (defect fix vs the sibling's unreproducible saga fit). Reproducibility check
     PASS: two independent fits byte-identical on all four vectors.
  4. `build_random_direction.py` -- fixed-seed random unit direction for the
     G3(i) placebo (sigma=1.0, not fit from data).
  5. `gate_fit.py` -- Youden-J tau on `neg_z_d` (FIT split only): AUC 0.9854,
     tau=-0.4213, tp=120/124 (96.8% confab caught), fp=2/36 (5.6% known-correct
     false-flagged). Consistent with the sibling diagnostic's own non-split-pool
     AUC 0.976.
  6. `materialize_rows.py` (HF_TOKEN set, `HF_HUB_DISABLE_XET=1
     HF_HUB_ENABLE_HF_TRANSFER=0`) -- joined the committed split manifest against
     the private staging pool's question text (398/398 covered) and local AH A0
     aliases (0 missing).
  7. `pipeline.py --mode smoke --n-rows 8 --dose 200` -- END-TO-END 8-row smoke
     (4 confab held-out + 4 known_correct_answered held-out, stratified). G0 PASS:
     write_fires=True, readback mean 200.05 (min 199.99, max 200.14), 4/4 dosed
     rows within 5% tolerance, collapse_rate_on_dosed=0.0,
     baseline_well_formed_rate_on_undosed=1.0 (4/4), gate AUC 0.985 (>=0.90). 3/4
     confab rows fired (2 clean_tighten among them); 1/4 known rows fired (that
     one row's well_formed_correct flipped False after dosing -- the expected
     false-refusal mechanism on a tiny sample). Full row detail:
     `analysis/smoke_rows.jsonl`, `analysis/smoke_summary.json` (both gitignored).

  Did NOT run `pipeline.py --mode full` (the confirmatory end-to-end held-out
  sweep + G3 placebo arms) -- that is gated behind sign-off and is not launched
  by this build task. The G2 power assessment (AMENDMENT.md) found the current
  known_correct_answered held-out population (n=53) below a decisive floor for
  the G2 Wilson-CI clause and wrote a mining plan rather than tuning the split
  or running the underpowered confirmatory.

  Committed on this build: `AMENDMENT.md`/`experiment.yaml` intentionally LEFT
  UNCOMMITTED per the lead's task (lead commits at sign); every other file
  (scripts, `cell.yaml`, `gates.yaml`, committed direction/manifest JSON,
  `analysis-committed/PROVENANCE.md`, the shared render module) is committed on
  branch `exp/doubt-gated-caution-tighten`.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 2 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 13 files / ~0.56 MB, built at repo commit fab3cad6.

- HF repo: `professorsynapse/eh-doubt-gated-caution-tighten` (dataset)
- HF revision: `21da8c1d8316298b97c72871b635eded5f66bd5e`
