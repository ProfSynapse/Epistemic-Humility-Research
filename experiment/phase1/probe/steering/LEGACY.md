# FROZEN FOR PROVENANCE (2026-07-06)

The bespoke steering and extraction machinery in this directory (and the
`amendment_*` scripts under `experiment/phase1/probe/`) is **frozen as of
2026-07-06**. It is retained because it is the registered instrument of signed
amendments and in-flight runs: the exact code that produced a signed result must
stay byte-stable so the result stays reproducible from its recorded config sha.

## What "frozen" means

- **Byte-stable.** Do not refactor, rename, reformat, or "clean up" these files.
  A signed amendment pins the sha of its instrument; a cosmetic edit breaks that
  pin and invalidates the provenance line from evidence to claim.
- **No new features.** New capability goes through the tuner `mechinterp` verbs,
  not by extending this code. See the `mechinterp-cells` skill
  (`.skills/mechinterp-cells/`) for how to author a tuner-backed cell.
- **Bug fixes only if a live arc requires one.** Amendment AN is executing on
  this machinery right now (2026-07-06). If a genuine defect blocks a live,
  signed arc, fix the minimum and record the fix in that amendment's doc plus a
  lab-notebook entry. Do not fold unrelated changes into such a fix.
- **Every NEW cell uses the tuner.** This directory is closed to new cells. The
  next steering / extraction / probe-fit cell is a tuner `mechinterp` recipe.

This file is documentation. It does not change behavior and it does not touch the
frozen files themselves.

## Instrument -> amendment map

Each major file below is the registered (or in-flight) instrument of the listed
amendment. The amendment doc under `experiment/protocol/` is the governing
record; this table is a navigation aid, not the source of truth.

### Steering harness (`experiment/phase1/probe/steering/`)

| File | Serves | Role |
|------|--------|------|
| `steering_common.py` | AA (shared) | Eval pools, grading (abstention / correctness / degenerate), paired bootstrap CIs, cache-aware hook gating, cell-JSON output. CPU-only at import. |
| `confidence_steer.py` | AA Arm A, and the write-side hook reused by AL / AN | Forward-hook activation steering `h <- h + alpha * d`. `SteeringHook` is the legacy analogue of the tuner `additive` law. |
| `cot_inject.py` | AA Arm B | CoT-injection prompt construction (early / late / placebo). String construction only. |
| `run_arm_a.py` | AA-1..AA-4 | Activation-steering orchestration (alpha sweep, anchor vs end, alpha=0 control). GPU inside guarded `main()`; `--dry-run` CPU-only. |
| `run_arm_b.py`, `arm_b_batched.py`, `spot_check_arm_b.py` | AA-5..AA-8 | CoT-injection orchestration (real + placebo paired, early vs late) and batched / spot-check variants. |
| `ab_templates.py`, `analyze_ab_traces.py`, `aa_think_trace_idiom_mining.py` | AA / AB | Arm B template bank and think-trace idiom analysis. |
| `amendment_aa_verdict.py` | AA | Verdict adjudication for the AA cells. |
| `persist_probe_direction.py` | Z-derived direction persistence (feeds AA/AL/AN) | Fits gate + dial probes from an extraction dir and persists unit-normed direction vectors. Legacy analogue of `mechinterp probe-fit`'s frozen-direction output. |
| `gpu_equivalence_cell.py` | AA / AL harness self-check | CPU-vs-GPU hook-equivalence check. Legacy analogue of the tuner smoke readback / built-in equivalence self-check. |
| `directions/` | AA / SR / Z / AL / AN | Frozen direction vectors per checkpoint. These are **data**, not code; going forward new directions are written as `mechinterp-direction/v1` JSON (see the organization principles in the `mechinterp-cells` skill). Existing files stay in place. |

### Amendment scripts (`experiment/phase1/probe/amendment_*`)

These live at the probe root, not in `steering/`. They are frozen on the same
terms. Grouped by amendment (some scripts live only on their amendment branch /
worktree, not on `main`):

| Amendment | Scripts (prefix `amendment_`) | Status |
|-----------|-------------------------------|--------|
| AF (channel-authority) | `af_base_pregen_extract`, `af_generate`, `af_probe_fit_labels`, `af_score` | Resolved (PR #163) |
| AG (asymmetric compliance) | `ag_generate`, `ag_primed_extract`, `ag_score`, `ag_stage0_*`, `ag_state_*`, `ag_neutral_*` | Resolved (PR #165) |
| AH (H-compliance) | `ah_main_*`, `ah_stage0_*`, `ah_addendum_a1_*`, `ah_redesign_collinearity` | Resolved + Addendum A1 |
| AJ (quantified dependency) | `aj_subspace_erasure`, `aj_addendum_gap_distribution` | Resolved (PR #189/#190) |
| AK (commitment point) | `ak_*` (on `amendment-ak-commitment-point`) | Stage 1/2 in disposition |
| AL (radial steering) | `al_prep_*`, `al_select_and_direction`, `al_grade_and_gates` (on `amendment-al-radial-steering`) | Resolved (PR #214), NULL |
| AM (residual catch) | `am_*` (on `amendment-am-residual-catch`) | In disposition |
| AN (selected-setpoint regulator) | `an_build_maps`, `an_build_selector_table`, `an_grade_and_gates`, `an_refit_caution_perp`, `an_steer_generate` (on `amendment-an-selected-setpoint-regulator`) | **EXECUTING 2026-07-06** |
| Q/R (aux-head co-train) | `q_*`, `r_*` | Resolved / falsified |
| S/T/U/V/W/X/Y/Z/SR (readout line) | `s_*`, `t_*`, `u_*`, `v_*`, `w_*`, `x_*`, `y_*`, `z_*`, `sr_*` | Resolved |

The Modal wrappers referenced by AL / AK / AM / AN (`modal_*.py`) live on their
respective amendment branches / worktrees alongside the scripts above; they are
frozen on the same terms. `item-11` and any other in-flight lab-notebook arc that
imports this machinery inherits the freeze.

## Migration pointer

The going-forward home for reading and writing internal activations is the tuner
`mechinterp` family (`extract` / `probe-fit` / `steer` / `score-gates`), driven
by declarative recipe YAML. The authoring guide, organization principles, and a
legacy-to-tuner migration map are in `.skills/mechinterp-cells/SKILL.md`.
