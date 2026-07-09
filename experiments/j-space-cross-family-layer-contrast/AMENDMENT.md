# j-space-cross-family-layer-contrast

Status: draft (not signed; do not launch as confirmatory evidence). No GPU
work has run for this experiment; every artifact under this directory is a
scaffold, not a result.

Keep this document the prose home for the experiment. The machine state lives
in `experiment.yaml` and is never duplicated here.

## Motivation and posture

The resolved same-model experiment `j-space-calibrated-layer-contrast-qwen3-4b`
found that a calibrated mid-band J-space write site (hs23, absolute setpoint
25) beat the inherited late-layer hs34 write site (absolute setpoint 175) on
held-out confab `clean_tighten` by 22.7 percentage points (89.2% vs 66.5%),
with only a 0.78 percentage-point known-correct false-refusal cost increase,
on raw-base `unsloth/Qwen3-4B` bf16. The signed fresh-pool replication
`j-space-layer-contrast-replication-qwen3-4b` reruns that same contrast on a
private evaluation pool disjoint from the predecessor's fit and held-out
split, freezing the predecessor's directions, gates, and calibrated doses, to
harden the finding as a same-model result.

Both of those experiments are Qwen3-4B only. This experiment asks the open
confound directly: does the mid-band write-site advantage transfer across
model FAMILIES, or is it a Qwen3-4B (or Qwen3-lineage) idiosyncrasy? This
mirrors the shape of `experiment/protocol/AMENDMENT-Z-cross-family-confirmatory.md`,
which asked the same family-confound question for the training-free
two-signal readout (gate/dial/veto) and found the readout's gate and dial are
family-general (4/4) while the veto -- the model-DEPENDENT axis -- replicates
but is fragile (3/4, one clean fail on Llama, one marginal pass on Qwen3.5).
This experiment reuses Amendment Z's exact four checkpoints and Amendment
Z's exact run order (lowest loader/VRAM risk first, Gemma last) because that
amendment already paid the cost of establishing which families load cleanly
on raw-base instruct checkpoints with no adapter and no task training.

Posture: Tier-2 EXPLORATORY-confirmatory hybrid. It is reported separately
from the locked headline matrix (`experiment/protocol/PROTOCOL.md`) and is
NOT pooled with either of the two Qwen3-4B-only same-model J-space
experiments above. Per-family results are exploratory Tier-2 evidence; the
cross-family roll-up rule (see Gates) is the only claim-promoting surface
this experiment can produce, and even a SUCCESS verdict here promotes "the
mid-band advantage is not Qwen3-specific," not a headline number.

## Design

Substrate: four raw-base instruct checkpoints, bf16, no adapter, no 4-bit
quantization, no task training. See the family table below for exact
checkpoints, loader notes, and VRAM risk (transcribed from Amendment Z where
overlapping, extended with this experiment's own J-space-specific notes).

### Family table

| Family | Checkpoint | Scale | Loader / render notes | Risk order |
|--------|-----------|-------|------------------------|-----------|
| Meta Llama | `unsloth/Llama-3.2-3B-Instruct` (fallback `meta-llama/Llama-3.2-3B-Instruct`) | 3B | Text-only `LlamaForCausalLM`, lowest loader risk (Amendment Z). EOS needs `<\|eot_id\|>` in addition to the tokenizer's own `eos_token_id`. | 1 (run first) |
| Mistral | `mistralai/Ministral-3-3B-Instruct-2512` | 3B | Apache-2.0, ungated; **weights shipped FP8 -- dtype-load risk** (Amendment Z). If the bf16 upcast load fails, this is a G0 loader blocker, recorded INELIGIBLE, not silently worked around. | 2 |
| Alibaba Qwen | `Qwen/Qwen3.5-4B` | 4B | **Different checkpoint from this project's usual `unsloth/Qwen3-4B`** -- same lineage, not the same model. Ungated + multimodal (native) -- loader risk (Amendment Z); needs the `AutoModelForImageTextToText`/`AutoModelForVision2Seq` fallback chain and `config.text_config` nesting for `hidden_size`/`num_hidden_layers`. `<\|im_end\|>` EOS convention expected but not assumed identical to Qwen3-4B's tokenizer. | 3 |
| Google Gemma | `google/gemma-4-E4B-it` | E4B (~4B effective) | Apache-2.0, ungated (Amendment Z, verified 2026-06-30) + multimodal (Gemma4 conditional-gen) -- **loader risk only, but also this experiment's own flagged VRAM risk**: the multimodal wrapper may load a vision tower even for text-only prompts, which combined with the J-lens's extra double-backward-JVP activation memory could be tight on a 24GB 3090. `<end_of_turn>` EOS convention. | 4 (run last) |

Per-family config, loader hardening, render contract, EOS resolution, and
(after the profile stage runs) resolved band selection and calibrated doses
all live in `families/<slug>.yaml` -- no other script in this experiment
hardcodes a checkpoint string, hidden size, or layer index; every script
reads a family only through `family_config.py`.

### Per-family pipeline (FIT side, all pre-outcome)

For each family, in Amendment Z's run order (Llama, Ministral, Qwen3.5,
Gemma):

1. **Mine a private eval pool** (`mine_eval_pool.py --family <slug>`): generate
   on that family's OWN raw-base checkpoint over the shared AH expansion
   candidate pool (question/alias text is family-agnostic; the resulting
   role labels are family-specific, since "does this family answer or
   refuse" is exactly what defines confab / known_correct_answered /
   unknown_refused). No predecessor split to exclude (each family's pool is
   fresh from scratch). Same selection rules as the Qwen3-4B replication:
   confab = gold-unanswerable + answered; known_correct_answered =
   gold-answerable + answered + correct; unknown_refused = gold-unanswerable
   + refused + not degenerate (fitting scaffold only, never itself graded).
   Text/aliases/generations stay private under `analysis/<family>/`;
   committed output is an ID-only manifest under
   `analysis-committed/<family>/eval_pool_manifest.json`.
2. **J-lens layer_profile** (`jlens_profile.py --family <slug>`) to locate
   that family's own workspace-like band. Reuses
   `j-space-localization-qwen3-4b/jlens.py`'s `layer_profile()` UNCHANGED
   (it is already parameterized by model and layer list); this script only
   adds a depth-sweep default and the band-selection rule below. Writes the
   resolved band back into `families/<slug>.yaml` in place.

   **Band-selection rule (LOCKED, pre-stated)**: midband candidates = the
   profiled hs_index at the effective-dimensionality-fraction peak, plus the
   profiled hs_indices immediately adjacent to it in the depth sweep (one on
   each side, where available). Late reference = `round((34/36) *
   n_hidden_layers)` -- the depth-FRACTION analog of Qwen3-4B's own hs34
   write site over its 36 hidden layers, not the same absolute index. Do
   NOT assume Qwen3-4B's own hs23-29 band or hs34 late site transfers to any
   other family; each family's own `n_hidden_layers` and its own profile
   determine its own absolute layer indices.
3. **Fit per-layer directions + gate** (`build_directions.py`,
   `gate_fit.py --family <slug>`): identical method to
   `j-space-midband-write-sweep-qwen3-4b/build_directions.py` /
   `gate_fit.py`, on that family's own FIT split only. `u_d` (doubt),
   `pos_ctrl`/`neg_ctrl` (caution/propensity), `c_hat` (orthogonalized
   caution write direction), and a Youden-J frozen `tau` on `neg_z_d`, per
   candidate layer. `random_state=20260707`, pinned identically across
   families; `--verify-reproducible` byte-identical refit check required
   before trusting any family's directions.
4. **Per-layer dose calibration** (`calibrate_dose.py --family <slug>`):
   identical method to `j-space-midband-dose-calibration-qwen3-4b/calibrate_dose.py`
   (same dose ladder `[25, 50, 75, 100, 125, 150, 175, 200]`, same usability
   rule, same selection rule), on that family's own FIT rows at that
   family's own resolved layers. Does NOT assume Qwen3-4B's own selected
   setpoints (hs23=25, hs26=75, hs29=125, hs34=175) transfer.
5. **G0 instrument smoke per family** (`run_contrast.py --family <slug> --mode
   smoke`): readback within tolerance, 0 collapse, gate AUC >=0.90 on FIT,
   identical generation contract to the two Qwen3-4B predecessors
   (`min_new_tokens=1`, `max_new_tokens=200`, greedy, `enable_thinking=False`
   or that family's equivalent, EOS resolved per-family via
   `model_lib.resolve_eos_ids`).

### Generation contract (identical across families)

`min_new_tokens=1`, `max_new_tokens=200`, `do_sample=False`, `num_beams=1`,
`enable_thinking=False` (or the family's own equivalent -- most families
have no native thinking toggle, so this is a documented no-op, see each
`families/<slug>.yaml` "render" block), EOS ids = tokenizer's own
`eos_token_id` plus that family's own named end-of-turn token(s) (never
assumed to be `<\|im_end\|>` outside the Qwen lineage). `clean_tighten` and
`not_well_formed_correct` metrics are BYTE-IDENTICAL to the two Qwen3-4B
predecessors (`gen_lib.py:grade_clean_tighten`, `grader.py:grade_one`,
ported unchanged).

### Outcome (held-out, per family)

Layer contrast: best mid-band site vs late reference site, gated snap at
calibrated doses, over that family's own held-out confab and
known_correct_answered rows (`run_contrast.py --family <slug> --mode full`).
Metrics identical to both Qwen3-4B predecessors: confab `clean_tighten`,
known-correct `not_well_formed_correct` cost.

Cross-family roll-up (`cross_family_rollup.py`): combines every family's
`full_summary.json` (or records NOT-RUN for a family that failed G0) into
the single cross-family verdict per the Gates section below.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, `family_config.py`,
`model_lib.py`, `gen_lib.py`, `grader.py`, `mine_eval_pool.py`,
`split_fit_heldout.py`, `jlens_profile.py`, `extract_anchor.py`,
`build_directions.py`, `gate_fit.py`, `calibrate_dose.py`, `run_contrast.py`,
`cross_family_rollup.py`, and every `families/<slug>.yaml`.

## Prediction

SUCCESS means: for at least 3 of the 4 families that actually run past G0,
that family's own best calibrated mid-band write site beats that family's own
calibrated late-reference site by at least 10 percentage points on held-out
confab `clean_tighten`, without increasing known-correct false-refusal cost
by more than 2 percentage points (G1 AND G2 both pass). This would mean the
mid-band write-site advantage found on Qwen3-4B is a property of instruct
LMs writing near their own workspace-like band in general, not an artifact
of Qwen3-4B's own architecture or pretraining.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

(Left blank at draft time; the lead fills both rows at sign time, per the
lead's explicit instruction for this scaffold.)

## Falsifier

If at most 1 of the 4 (or of however many run past G0) families passes G1
AND G2, the mid-band write-site advantage is Qwen-specific or an artifact of
the same-model experiments' own setup -- FALSIFIED, and the J-space
actuation-bridge layer-site claim does NOT generalize across families. If
exactly 2 of 4 pass, the result is MIXED and no claim is promoted either way.

## Gates

- **G0 (per-family instrument validity; stop, not outcome)**: that family's
  checkpoint loads via the hardened loader and yields a valid hidden-states
  tuple; the family's eval pool has at least 200 confab rows and at least
  300 known_correct_answered rows; no restricted text/generations are
  committed; that family's `band_selection.status == resolved` before
  extraction; direction refits are byte-identical
  (`--verify-reproducible`); gate AUC (`neg_z_d`, FIT confab vs FIT
  known_correct_answered) >=0.90 at every candidate layer; smoke readback is
  within 5%+0.5 absolute of each layer's calibrated dose; smoke collapse on
  dosed rows is 0 for every candidate layer. **A family that fails G0 after
  bounded debugging is recorded as NOT-RUN with the explicit blocker and
  excluded from the cross-family denominator -- it is neither a PASS nor a
  FALSIFIER hit for that family**, matching Amendment Z's own INELIGIBLE
  disposition.
- **G1 (mid-band tighten improvement, per family)**: that family's best
  mid-band confab `clean_tighten` rate minus that family's late-reference
  `clean_tighten` rate >= 10 percentage points.
- **G2 (no selectivity regression, per family)**: that family's best
  mid-band known-correct false-refusal cost minus that family's
  late-reference cost <= 2 percentage points.
- **G3 (late-reference viable, per family)**: that family's late-reference
  confab `clean_tighten` rate >= 0.40 AND Wilson lower 95% CI > 0.30. **This
  floor is intentionally LOWER than the Qwen3-4B predecessors' own G3 floor
  (rate >=0.60, CI lower >0.50)** because instruct families may differ in
  how viable an inherited late-layer write site is at all -- **this 0.40/0.30
  floor is a decision point flagged to the lead (see LAUNCH-PLAN.md), not an
  independently re-derived number.** If G3 fails for a family, that family's
  G1/G2 numbers are read as a reference-replication problem for that family
  specifically, not evidence against mid-band superiority in general.

**CROSS-FAMILY SUCCESS = G1 AND G2 pass in >=3 of 4 run families.** If a
family did not run (G0 stop), the denominator becomes ">=3 of the families
that ran"; if fewer than 3 families ran at all, the experiment is
**INCONCLUSIVE**, not a pass.

**FALSIFIER: G1 AND G2 pass in <=1 of 4 run families** => the mid-band
advantage is Qwen-specific or an artifact. **2 of 4 => MIXED, no claim
promoted.**

## Outcome

Filled at resolve. Record the verdict, the per-family gate results, the
cross-family roll-up, and the one-sentence summary that also goes into
`verdict:` in the manifest. No GPU work has run for this experiment as of
this draft; every artifact under `analysis-committed/` at draft time (if
any) is a scaffold placeholder, not a result.
