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
this experiment can produce, and even a SUCCESS verdict here promotes "mid-band
actuation is not Qwen3-specific," not a headline number.

### Sign-time revision (2026-07-23, lead-directed, user-approved)

Three structural changes were made at sign-time prep, after the sibling
`doubt-snap-cross-family-confirmatory` experiment RESOLVED (2026-07-12,
confirmatory not promoted -- every launched cell stopped at its registered G0
FIT dose-viability rule at the late 0.94-depth write site). These changes are
reflected throughout the sections below; the numbers they introduce were
ADJUDICATED by lead+user 2026-07-23 (conservative option chosen).

1. **Primary endpoint reframed to ABSOLUTE mid-band actuation.** The primary
   per-family gates are no longer a relative mid-vs-late contrast. They are
   now: the J-lens-selected mid-band site must achieve held-out confab
   `clean_tighten` above a floor (G1) AND keep known-correct false-refusal
   cost below a cap (G2). The late-reference arm is DEMOTED to a secondary
   descriptive comparator with NO gate (old draft G1/G2/G3 relative-contrast
   gates are dropped). This is because doubt-snap already resolved that the
   inherited late 0.94-depth site is weak or dead across these families, so a
   relative "beat the late site" bar would be trivially cleared by any real
   mid-band actuation and tells us nothing about whether mid-band actuation is
   itself useful; the interesting cross-family question is absolute.
2. **Consumes doubt-snap's resolved per-family artifacts** (see the section
   below): each family's mined eval pool, FIT/HELD-OUT split, and frozen
   late-site direction/gate are reused verbatim, hash-pinned. The only new
   work here is per-family J-lens mid-band localization, mid-band direction
   fits + dose calibration, and the outcome runs.
3. **Gemma-4-E4B Modal fallback pre-authorized** (see "Substrate" and
   LAUNCH-PLAN.md): the Gemma cell runs on the local 3090 first; if it OOMs at
   G0 after bounded debugging, a Modal fallback for that cell is pre-authorized
   by the user; a G0 NOT-RUN is recorded only if Modal also fails.

### Mid-run revision R2 (2026-07-24, lead-drafted, user-ratified): norm-scaled dose ladder

**What happened under the original registration.** Llama-3.2-3b and
mistral-7b-v03 both stopped at the registered G0 dose-viability rule: zero
usable doses at any layer on the absolute ladder [25..200] (full dispositions
in NOTEBOOK.md; formal `run_contrast.py --mode smoke` ValueError on record for
both). Diagnosis, corroborated three ways (raw-text collapse samples; per-family
anchor-norm measurements; recovered Qwen3-4B reference norms): the absolute
ladder was implicitly denominated in Qwen3-4B's residual units. Qwen3-4B's
selected doses sat at 0.37-0.60x its per-layer median anchor L2 norm (usable
window 0.20-1.00x, with real failure evidence bracketing both sides: too-weak
at 0.12x, collapse at 1.12-1.20x). The same absolute doses put llama's
mid-band at 1.8-14.6x its norms and mistral's at 3.1-60x — outside the usable
band everywhere, exactly reproducing the observed collapse.

**The change (single knob, user-ratified 2026-07-24).** `calibrate_dose.py`'s
ladder is respecified as RATIOS of per-layer median anchor L2 norm (each
family's own norms, computed at runtime from its own already-frozen
`anchor_extract.safetensors`): 8 geometric rungs
[0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000] (ratio 20^(1/7)).
Rungs r2-r5 cover the Qwen3-4B-validated usable band [0.20, 1.00]; r0/r1 and
r6/r7 are two-sided margin. Sanity check (required pre-registration, PASSED):
the normalized ladder recovers Qwen3-4B's own four selected doses within one
rung (all four in the [r3, r4] bracket, 4-14% from nearest rung). Derivation
artifacts: recovered Qwen3-4B norms (296 FIT rows, provenance-verified against
the committed split manifest, method byte-identical to the pinned extractor)
and the full ratio analysis, retained with the revision evidence.

**What does NOT change.** The usability rule (readback within tolerance, zero
collapse, FIT confab clean_tighten >= 0.5), the selection rule (highest tighten
rate, then lower cost, then lower dose/ratio), G1/G2 gates and their floors,
held-out discipline, the generation contract, and every frozen
direction/gate/split artifact. Llama and mistral's extractions, directions,
and gate fits are dose-independent and carry forward unchanged.

**Scope.** (a) Llama-3.2-3b and mistral-7b-v03 re-run dose calibration under
the normalized ladder; their ladder-v1 NOT-RUN dispositions remain on record
as evidence about the ORIGINAL registration (instrument-resolution-limited),
and their final per-family dispositions are determined by the v2 pipeline
outcome. (b) Gemma-4-e4b, not yet calibrated, calibrates under the normalized
ladder from the start. (c) qwen3.5-4b remains deferred (user decision
2026-07-24) and is outside this revision.

**Roll-up and scoreboard semantics.** The registered roll-up rule is unchanged
and is adjudicated over families as finally disposed under this revision
(a family "runs past G0" if its v2 calibration finds a usable dose and G0
passes). The pre-registered scoreboard calls are NOT reopened: both calls
stand as written and are adjudicated against the final roll-up. This revision
is recorded BEFORE any v2 calibration cell has run; no v2 behavioral result
existed when the ladder was ratified.

Substrate: four raw-base instruct checkpoints, bf16, no adapter, no 4-bit
quantization, no task training. See the family table below for exact
checkpoints, loader notes, and VRAM risk (transcribed from Amendment Z where
overlapping, extended with this experiment's own J-space-specific notes).

Lane: local RTX 3090 for all four families. **Gemma-4-E4B Modal fallback,
pre-authorized (user, 2026-07-23):** the Gemma cell runs locally first; if it
OOMs at G0 after bounded debugging (its trimodal loader materializes vision +
audio towers even for text-only prompts, and the J-lens profile stage's
eager-attention double-backward adds activation memory on top -- see the family
table and LAUNCH-PLAN.md VRAM section), a Modal fallback for the Gemma cell
only is pre-authorized; a G0 NOT-RUN is recorded for Gemma only if the Modal
fallback also fails. The other three families are local-only.

### Family table

| Family | Checkpoint | Scale | Loader / render notes | Risk order |
|--------|-----------|-------|------------------------|-----------|
| Meta Llama | `unsloth/Llama-3.2-3B-Instruct` (fallback `meta-llama/Llama-3.2-3B-Instruct`) | 3B | Text-only `LlamaForCausalLM`, lowest loader risk (Amendment Z). EOS needs `<\|eot_id\|>` in addition to the tokenizer's own `eos_token_id`. | 1 (run first) |
| Mistral | `mistralai/Mistral-7B-Instruct-v0.3` | 7B | Apache-2.0, ungated, plain `MistralForCausalLM`, bf16-native. **Substituted pre-outcome for Amendment Z's `Ministral-3-3B-Instruct-2512`**: the doubt-snap-cross-family confirmatory found before any Mistral-family behavioral outcome that Ministral-3 exposes `Mistral3ForConditionalGeneration`, not a causal-LM substrate for the activation WRITE path (Amendment Z only read, so it never hit this). This experiment also writes, so it inherits that substitution and the same pinned replacement checkpoint. 7B is the VRAM-heaviest family here; the J-lens profile stage needs batching headroom (see `families/mistral-7b-v03.yaml`). | 2 |
| Alibaba Qwen | `Qwen/Qwen3.5-4B` | 4B | **Different checkpoint from this project's usual `unsloth/Qwen3-4B`** -- same lineage, not the same model. Ungated + multimodal (native) -- loader risk (Amendment Z); needs the `AutoModelForImageTextToText`/`AutoModelForVision2Seq` fallback chain and `config.text_config` nesting for `hidden_size`/`num_hidden_layers`. `<\|im_end\|>` EOS convention expected but not assumed identical to Qwen3-4B's tokenizer. | 3 |
| Google Gemma | `google/gemma-4-E4B-it` | E4B (~4B effective) | Apache-2.0, ungated (Amendment Z, verified 2026-06-30) + **CORRECTED 2026-07-09: trimodal** (Gemma4 conditional-gen carries both a `vision_config` AND an `audio_config`, not vision-only as this row previously implied) -- **loader risk only, but also this experiment's own flagged VRAM risk**: CPU-only config/class-registration verification (no weights, no GPU) confirmed the resolved loader class structurally includes both towers, so a real load DOES materialize vision- and audio-tower parameters for text-only prompts (previously "may load", now confirmed), which combined with the J-lens's extra double-backward-JVP activation memory could be tight on a 24GB 3090. **CORRECTED 2026-07-09: EOS convention is `<turn|>`, NOT `<end_of_turn>`** -- verified against the actual `chat_template.jinja` and `tokenizer_config.json`'s own `eot_token` field; the classic Gemma 2/3 `<start_of_turn>`/`<end_of_turn>` tokens do not appear anywhere in this checkpoint's template. See `families/gemma4-e4b.yaml` for full verification detail. | 4 (run last) |

Per-family config, loader hardening, render contract, EOS resolution, and
(after the profile stage runs) resolved band selection and calibrated doses
all live in `families/<slug>.yaml` -- no other script in this experiment
hardcodes a checkpoint string, hidden size, or layer index; every script
reads a family only through `family_config.py`.

### Consumed doubt-snap artifacts (resolved; hash-pinned)

`doubt-snap-cross-family-confirmatory` RESOLVED 2026-07-12 (read its
AMENDMENT.md Outcome section: confirmatory NOT promoted; every launched cell
stopped at the registered pre-outcome G0 FIT dose-viability rule at the late
`round(0.94 * (num_hidden_layers - 1))` write site; Gemma-4-E4B's cell had its
FIT prep committed but was never behaviorally launched). Its small tier shares
all four of this experiment's checkpoints. This experiment CONSUMES its
resolved per-family committed artifacts under
`experiments/doubt-snap-cross-family-confirmatory/analysis-committed/<cell>/`,
each pinned by sha256 in the corresponding `families/<slug>.yaml` `reuse` block:

- **Eval pool + FIT/HELD-OUT split, reused verbatim (three families; gemma
  fresh-mines).** For **llama-3.2-3b, mistral-7b-v03, qwen35-4b**, each family's
  role labels (confab / known_correct_answered / unknown_refused) and its
  FIT/HELD-OUT partition are the doubt-snap cell's own `split_manifest.json`
  (ID-only: row_key + role + split + source + category_canon). This SUPERSEDES
  this experiment's own `mine_eval_pool.py` + `split_fit_heldout.py` for those
  three families -- no re-mining, no re-splitting. The private row TEXT lives on
  the Modal volume `eh-doubt-snap-cross-family` (committed artifacts are ID-only)
  and is pulled read-only, sha256-verified, into this experiment's gitignored
  `analysis/<family>/from_doubt_snap/` by `materialize_reused_rows.py`, exactly
  the mechanism `experiments/qwen35-4b-midband-doubt-snap/materialize_reused_rows.py`
  used for the qwen35_4b cell. **Source note:** doubt-snap's pools are mined
  from TriviaQA/PopQA (answerable) + KUQ (unanswerable), NOT this experiment's
  own draft "AH expansion candidate pool" -- reusing the split means adopting
  doubt-snap's source, which is the intended consequence of the reuse.
  **gemma4-e4b is the exception (adjudicated lead+user 2026-07-23,
  `pool_provenance: fresh_mine`):** its doubt-snap row text is absent from the
  Modal volume, so its pool/split are mined FRESH here (`mine_eval_pool.py` +
  `split_fit_heldout.py`, lead-authorized) -- reuse provenance for gemma's pool
  is LOST and recorded as such. Only the frozen late-site direction/gate (next
  bullet) are reused for gemma; see "Open questions at sign" #3.
- **Late-reference arm = doubt-snap's frozen late site, reused verbatim.** The
  secondary late arm loads that cell's committed `c_hat.json` (write direction),
  `u_d.json` (doubt sensor), `gate_fit.json` (`tau_frozen`), and
  `build_manifest.json` (`mu_d`/`sigma_d`/`mu_c`/`sigma_c`, `layer`, `hidden_dim`,
  `revision`) -- nothing about the late arm is refit here. The late site's
  decoder-block index is the reused `build_manifest.json` `layer`
  (llama 25, mistral 29, qwen35-4b 29, gemma 39); this experiment's `hs_index`
  for it is `block + 1` (26 / 30 / 30 / 40). This happens to equal this
  experiment's own `round(0.9444 * n_hidden_layers)` late estimate for all four
  families, but the SITE is DEFINED as doubt-snap's frozen block, not
  re-derived. Per-family frozen scalars, counts, and artifact hashes are pinned
  in each `families/<slug>.yaml` `reuse.doubt_snap` block. For **gemma4-e4b**
  (fresh-mine pool) this frozen late-site direction/gate is applied to gemma's
  OWN fresh rows as a frozen operating point -- the same
  frozen-direction-on-fresh-activations discipline as `qwen35-4b-midband-heldout`
  -- and it is the ONLY reuse gemma keeps; its late DOSE is still calibrated
  fresh (option B).

Only genuinely new work remains in THIS experiment: per-family J-lens mid-band
band localization, mid-band direction fits + dose calibration, and the outcome
runs. The mid-band directions/gate are fit fresh on the FIT split; the primary
is scored on the HELD-OUT split -- the REUSED doubt-snap split for
llama/mistral/qwen35-4b, and gemma's OWN fresh-mined split for gemma -- the same
reuse discipline `qwen35-4b-midband-doubt-snap` / `qwen35-4b-midband-heldout`
used.

**Two gaps found while pinning the artifacts (flagged, not guessed around;
carried to "Open questions at sign"):**

- **No family has a calibrated late-site DOSE to reuse.** Every doubt-snap cell
  stopped at G0 dose-viability with `selected_dose: null`; the committed
  `dose_fit.json` (present for llama/mistral/qwen35-4b, ABSENT for gemma) records
  a FIT dose SWEEP but no selected dose. So "reuse its late-site ... calibrated
  dose" (the sign-time instruction) cannot be satisfied literally. See the
  open-questions section for the two resolution options and the drafter's
  recommendation.
- **Gemma-4-E4B was never behaviorally launched in doubt-snap.** Its FIT-prep
  artifacts (pool, split, frozen late-site direction/gate) ARE committed and
  reusable, but there is no `dose_fit.json`, no `modal_status.json`, and its
  frozen late-site direction/gate were never dose-exercised against a real
  generation. Its late-site gate AUC (0.9472) is the weakest of the four (still
  >= the 0.90 G0 floor) and its held-out known count (251) is a ~1-row margin
  over the 250 power bar.

The reuse depends on the `eh-doubt-snap-cross-family` Modal volume still
retaining each family's `analysis/` row-text files; `qwen35-4b-midband-doubt-snap`
proved this works for the qwen35_4b cell, but the llama / mistral / gemma cells'
row text on that volume is not yet re-verified (open question).

### Per-family pipeline (FIT side, all pre-outcome)

For each family, in Amendment Z's run order (Llama, Mistral, Qwen3.5,
Gemma):

1. **Materialize the reused eval pool + split** (`materialize_reused_rows.py
   --family <slug>`): pull the doubt-snap cell's FIT/HELD-OUT rows read-only,
   sha256-verified, from the Modal volume `eh-doubt-snap-cross-family` into
   gitignored `analysis/<family>/from_doubt_snap/`, and verify the committed
   `split_manifest.json` against the sha256 pinned in `families/<slug>.yaml`
   `reuse.doubt_snap.artifacts.split_manifest`. Role labels (confab /
   known_correct_answered / unknown_refused) and the FIT/HELD-OUT partition are
   doubt-snap's own, reused verbatim -- this experiment does NOT re-mine or
   re-split. (`mine_eval_pool.py` / `split_fit_heldout.py` are retained only as
   a fallback if a family's Modal row text is gone and the lead authorizes a
   fresh mine; a fresh mine would NOT be the reused pool and loses the reuse
   provenance.) Text/aliases/generations stay private; committed output is the
   ID-only `analysis-committed/<family>/reused_rows_manifest.json`.
2. **J-lens layer_profile** (`jlens_profile.py --family <slug>`) to locate
   that family's own workspace-like band. Reuses
   `j-space-localization-qwen3-4b/jlens.py`'s `layer_profile()` UNCHANGED
   (it is already parameterized by model and layer list); this script only
   adds a depth-sweep default and the band-selection rule below. Writes the
   resolved band back into `families/<slug>.yaml` in place.

   **Band-selection rule (LOCKED, pre-stated)**: midband candidates = the
   profiled hs_index at the effective-dimensionality-fraction peak, plus the
   profiled hs_indices immediately adjacent to it in the depth sweep (one on
   each side, where available). Do NOT assume Qwen3-4B's own hs23-29 band
   transfers; each family's own `n_hidden_layers` and its own profile
   determine its own absolute mid-band indices. The **late reference site is
   NOT localized here** -- it is doubt-snap's frozen late site (decoder block =
   the reused `build_manifest.json` `layer`; hs_index = block + 1; llama 26 /
   mistral 30 / qwen35-4b 30 / gemma 40), consumed verbatim per the reuse
   section above.
3. **Fit MID-BAND directions + gate** (`build_directions.py`,
   `gate_fit.py --family <slug>`): identical method to
   `j-space-midband-write-sweep-qwen3-4b/build_directions.py` /
   `gate_fit.py`, on that family's REUSED FIT split only, for the MID-BAND
   candidate layers only. `u_d` (doubt), `pos_ctrl`/`neg_ctrl`
   (caution/propensity), `c_hat` (orthogonalized caution write direction), and
   a Youden-J frozen `tau` on `neg_z_d`, per mid-band candidate layer.
   `random_state=20260707`, pinned identically across families;
   `--verify-reproducible` byte-identical refit check required before trusting
   any family's mid-band directions. The LATE arm is NOT fit here -- its
   `c_hat`/`u_d`/`tau`/standardization are loaded frozen from the reused
   doubt-snap artifacts (reuse section). Anchor extraction and the render/anchor
   convention (BASELINE_SYSTEM_PROMPT, anchor at `prompt_len - 1`,
   `enable_thinking=False`) must match doubt-snap's own convention so the frozen
   late direction/gate are valid on this experiment's fresh activations -- this
   is the same constraint `qwen35-4b-midband-doubt-snap` observed when reusing
   this cell's rows; see "Open questions at sign".
4. **Per-MID-BAND-layer dose calibration** (`calibrate_dose.py --family <slug>`):
   identical method to `j-space-midband-dose-calibration-qwen3-4b/calibrate_dose.py`
   (same dose ladder `[25, 50, 75, 100, 125, 150, 175, 200]`, same usability
   rule, same selection rule), on that family's REUSED FIT rows at that
   family's own resolved MID-BAND layers. Does NOT assume Qwen3-4B's own
   selected setpoints transfer. The late arm's dose is NOT set here -- it is an
   open question (doubt-snap selected no late dose for any family; see the reuse
   section and "Open questions at sign").
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

**Primary (gating):** the best mid-band site's held-out confab `clean_tighten`
(G1 floor) and its held-out known-correct `not_well_formed_correct` cost (G2
cap), over that family's REUSED held-out confab and known_correct_answered
rows (`run_contrast.py --family <slug> --mode full`). "Best mid-band site" =
the mid-band candidate with the highest held-out confab `clean_tighten`, ties
broken by lower known-correct cost.

**Secondary (descriptive, non-gating):** the frozen late-reference arm's
held-out confab `clean_tighten` and known-correct cost, and the
best-mid-band-minus-late delta on both metrics, reported alongside for contrast
with doubt-snap's resolved late-site null. No late-arm gate.

Metrics identical to both Qwen3-4B predecessors: confab `clean_tighten`,
known-correct `not_well_formed_correct` cost.

Cross-family roll-up (`cross_family_rollup.py`): combines every family's
`full_summary.json` (or records NOT-RUN for a family that failed G0) into
the single cross-family verdict per the Gates section below.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, `family_config.py`,
`model_lib.py`, `gen_lib.py`, `grader.py`, `materialize_reused_rows.py`,
`mine_eval_pool.py`, `split_fit_heldout.py` (the last two retained as
fallback-only), `jlens_profile.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `run_contrast.py`, `cross_family_rollup.py`,
and every `families/<slug>.yaml`.

## Prediction

SUCCESS means: for at least 3 of the families that actually run past G0, that
family's own best calibrated mid-band write site clears BOTH primary gates on
held-out -- confab `clean_tighten` at or above the G1 floor AND known-correct
`not_well_formed_correct` cost at or below the G2 cap. This would mean useful,
selective mid-band actuation is a property of instruct LMs writing near their
own workspace-like band in general, not an artifact of Qwen3 lineage. The late
reference arm is expected to be weak or dead across families (doubt-snap's
resolved late-site null), reported descriptively; it does not gate the primary.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | SUCCESS: >=3 of the run families clear both primary gates (G1+G2). Basis: the c_hat audit in doubt-snap-cross-family-confirmatory shows the caution encoding reads in every family, and its nulls were late-site-specific; Llama is the most likely single miss. |
| user | MIXED: exactly 2 of the run families clear both primary gates. |

(Registered at sign time, 2026-07-23, before any GPU work for this
experiment; neither call moves after results per the no-goalpost rule.)

## Falsifier

If at most 1 of the families that run past G0 clears both primary gates,
useful mid-band actuation does NOT generalize across families (the Qwen3-lineage
mid-band actuation is family-specific or an artifact) -- FALSIFIED. If exactly
2 of the run families clear both primary gates, the result is MIXED and no
claim is promoted either way. This falsifier is defined over the ABSOLUTE
primary gates on held-out; unlike doubt-snap's own falsifier (which could not
fire because every cell stopped at G0 before its held-out surface), a G0 stop
here removes a family from the denominator rather than leaving the result
between prediction and falsifier -- the roll-up covers every family disposition
(pass / fail / NOT-RUN) explicitly.

## Gates

The gate numbers below were ADJUDICATED by lead+user 2026-07-23 (conservative
option chosen); the drafter's derivation is preserved under "Gates ->
derivation". They are pinned identically across families in each
`families/<slug>.yaml` `primary_gate` block.

- **G0 (per-family instrument validity; stop, not outcome)**: that family's
  checkpoint loads via the hardened loader and yields a valid hidden-states
  tuple; the pinned reuse artifacts this family actually consumes hash
  byte-identical to `families/<slug>.yaml` `reuse` (for the REUSED-POOL families
  llama/mistral/qwen35-4b: the doubt-snap `split_manifest.json` AND the frozen
  late-site direction/gate `c_hat`/`u_d`/`random_direction`/`gate_fit`/
  `build_manifest`; for the FRESH-MINE family gemma4-e4b: ONLY the frozen
  late-site direction/gate artifacts -- gemma mines its own pool/split, so its
  split_manifest/g0_prep_summary are reference-only and not hash-checked, per
  `family_config.integrity_artifact_names`); the pool has at least 150 held-out
  confab rows AND at least 250 held-out known_correct_answered rows (doubt-snap's
  own power bar; for llama/mistral/qwen35-4b this is the reused pool, for gemma
  it is gemma's OWN fresh mine); no restricted text/generations are committed;
  that family's
  `band_selection.status == resolved` before extraction; MID-BAND direction
  refits are byte-identical (`--verify-reproducible`); gate AUC (`neg_z_d`, FIT
  confab vs FIT known_correct_answered) >=0.90 at every MID-BAND candidate
  layer; smoke readback within 5%+0.5 absolute of each layer's calibrated dose;
  smoke collapse on dosed rows is 0 for every mid-band candidate and the late
  arm. **A family that fails G0 after bounded debugging (including a Gemma cell
  that OOMs both locally and on the pre-authorized Modal fallback) is recorded
  as NOT-RUN with the explicit blocker and excluded from the cross-family
  denominator -- neither a PASS nor a FALSIFIER hit for that family**, matching
  Amendment Z's / doubt-snap's INELIGIBLE disposition.
- **G1 (PRIMARY -- mid-band actuation floor, per family)**: the best mid-band
  site's held-out confab `clean_tighten` rate **>= 0.50** AND its Wilson 95%
  lower CI **> 0.40** (adjudicated lead+user 2026-07-23).
- **G2 (PRIMARY -- mid-band selectivity cap, per family)**: that same best
  mid-band site's held-out known-correct `not_well_formed_correct` cost
  **<= 0.05** AND its Wilson 95% upper CI **< 0.10** (adjudicated lead+user
  2026-07-23).
- **Secondary late reference (descriptive, NOT a gate)**: the frozen late arm's
  held-out confab `clean_tighten` and known-correct cost, plus the
  best-mid-band-minus-late delta, are reported for contrast with doubt-snap's
  resolved late-site null. There is no late-viability gate; a dead late arm is
  expected and is not disqualifying. (This replaces the draft's G1/G2 relative
  contrast and its G3 late-reference-viability floor, all dropped.)

### Gates -> derivation (adjudicated lead+user 2026-07-23, conservative option chosen)

Every number is derived from resolved predecessor operating points, read from
their governed docs; no round number without stated provenance.

- **G1 floor = clean_tighten >= 0.50, Wilson lower > 0.40.** Two same-lineage
  MID-BAND held-out operating points bracket the plausible range:
  `unsloth/Qwen3-4B` hs23 = **0.892** clean_tighten (Wilson [0.839, 0.929],
  `j-space-calibrated-layer-contrast-qwen3-4b` Outcome), and `Qwen/Qwen3.5-4B`
  hs20 held-out ~**0.66** (refused 0.678 AND well-formed 0.977 =>
  clean_tighten conjunction lower bound 0.655, `qwen35-4b-midband-heldout`
  Outcome). The observed LATE-site clean_tighten this experiment demotes is
  **<= 0.33** everywhere (doubt-snap FIT peaks: llama 0.184, mistral 0.000,
  qwen35-4b 0.326). A cross-family ABSOLUTE floor must sit below the weaker
  same-lineage mid-band point (0.66) to allow genuine cross-family attenuation,
  yet far above the dead late-site region (<= 0.33) so it cannot be cleared by
  a late-style non-actuating write. **0.50** (a majority of fired confabs
  cleanly tighten) with Wilson-lower **0.40** (set 0.10 below the point floor,
  mirroring the `qwen35-4b-midband-heldout` gate shape of 0.60 point / 0.50
  Wilson-lower) satisfies both. **Stricter alternative for the lead:** 0.60
  point / 0.50 Wilson-lower -- the exact floor the one non-original Qwen sibling
  (Qwen3.5-4B) actually cleared on held-out (refused 0.678, Wilson-lower 0.652),
  applied here to the stricter `clean_tighten` conjunction (~0.655, clears with
  little margin). The drafter RECOMMENDS the conservative 0.50/0.40 because
  clean_tighten is stricter than the `refused` metric 0.60 was set against, and
  cross-family attenuation is expected; the point is to detect real mid-band
  actuation, not to demand Qwen-level performance.
- **G2 cap = not_well_formed_correct <= 0.05, Wilson upper < 0.10.** Directly
  inherits the `qwen35-4b-midband-heldout` G1 cost gate (<= 0.05 point, Wilson
  upper < 0.10). Both same-lineage mid-band operating points clear it: Qwen3-4B
  hs23 **0.035** (9/258, `j-space-calibrated-layer-contrast-qwen3-4b`) and
  Qwen3.5-4B hs20 held-out **0.039** (14/360, `qwen35-4b-midband-heldout`).

**CROSS-FAMILY SUCCESS = the PRIMARY (G1 AND G2) passes in >= 3 of the families
that run past G0.** If a family did not run (G0 stop), the denominator is "the
families that ran"; if fewer than 3 families ran at all, the experiment is
**INCONCLUSIVE**, not a pass.

**FALSIFIER: the PRIMARY passes in <= 1 of the families that run past G0** =>
mid-band actuation is Qwen-lineage-specific or an artifact. **Exactly 2 => MIXED,
no claim promoted.**

## Open questions at sign (for the lead)

0. **This branch is 677 commits behind `main`; the reused artifacts are not on
   it yet.** The entire reuse design depends on
   `doubt-snap-cross-family-confirmatory` (and its qwen35-4b-midband successors),
   which resolved on `main` AFTER this experiment's branch
   (`exp/j-space-cross-family-layer-contrast`) was created. The doubt-snap
   committed artifacts, the pinned hashes' target files, and the predecessor
   AMENDMENTs are all present on `main` and were read there to author this
   revision, but they are ABSENT from this worktree. The branch MUST be brought
   up to date with `main` (rebase or merge -- a lead/git decision) before
   `materialize_reused_rows.py` or the G0 reuse-integrity check can resolve any
   reused path. All pinned sha256 in the `families/<slug>.yaml` `reuse` blocks
   were computed from `main` and are authoritative; they simply cannot be
   verified in this worktree until it carries `main`'s content.
1. **[RESOLVED 2026-07-23, lead+user] Primary gate NUMBERS (G1 floor / G2 cap).**
   ADOPTED the conservative option: G1 floor `clean_tighten` >= 0.50 point /
   Wilson lower > 0.40, G2 cap `not_well_formed_correct` <= 0.05 point / Wilson
   upper < 0.10. The stricter 0.60/0.50 alternative was NOT elected. Numbers are
   pinned in `gates.yaml` and every `families/<slug>.yaml` `primary_gate` block;
   the derivation is preserved under "Gates -> derivation".
2. **[RESOLVED 2026-07-23, lead+user -> option (B)] Late-arm DOSE gap.**
   doubt-snap selected NO late-site dose for any family
   (all G0 dose-viability stops; `selected_dose: null`). "Reuse the frozen
   late-site ... calibrated dose" (the sign-time instruction) cannot be
   satisfied literally. Options: **(A)** report the late arm at each family's
   doubt-snap FIT peak-`clean_tighten` dose from the committed `dose_fit.json`
   (llama 19, mistral 30, qwen35-4b 40) -- already computed, hash-pinned, but a
   sub-viability "best case" on per-cell-recalibrated grids, and UNAVAILABLE for
   gemma (no `dose_fit.json`). **(B)** calibrate the late-site dose fresh here
   with the same `calibrate_dose.py` ladder used for the mid-band arm, on the
   reused FIT rows -- apples-to-apples with the mid-band arm and covers gemma,
   but deviates from "reuse verbatim." **Drafter recommends (B):** the late arm
   is now non-gating and descriptive, so verbatim dose reuse buys nothing for
   confirmatory integrity, and a same-ladder late dose makes the mid-vs-late
   delta fair and uniform across all four families.
   **RESOLUTION (2026-07-23, lead+user): option (B) adopted.** The late-site
   scalar dose is calibrated FRESH here with the same `calibrate_dose.py` ladder
   as the mid-band arm, on the reused FIT rows, for all four families (including
   gemma, which has no committed `dose_fit.json`). This is a DELIBERATE
   deviation from verbatim dose reuse: because the late arm is
   non-gating/descriptive, verbatim dose reuse buys nothing for confirmatory
   integrity, while a same-ladder late dose makes the mid-vs-late delta fair and
   uniform across families. The frozen late-site DIRECTION and GATE
   (`c_hat`/`u_d`/`tau`/standardization from `build_manifest`/`gate_fit`) are
   still reused VERBATIM and remain hash-pinned in the `reuse` block; only the
   scalar write dose is recalibrated here. Plumbing: `calibrate_dose.py` now
   sweeps the late site alongside the mid-band candidates, and
   `run_contrast.py` (`resolve_late_dose`) reads the fresh late dose from the
   calibration summary (CLI `--late-dose` still overrides).
3. **[RESOLVED 2026-07-23, lead+user] Modal-volume retention -> gemma fresh
   mine.** The reuse pulls private row text from the `eh-doubt-snap-cross-family`
   Modal volume. `modal volume ls` (existence-only, no downloads) on 2026-07-23:
   **llama32_3b_instruct/analysis PRESENT** (full analysis set incl.
   `split_rows_private.jsonl`, `candidate_pool_private.jsonl`,
   `fit_rows_for_dose.jsonl`, `heldout_rows_for_steer.jsonl`);
   **mistral7b_instruct_v03/analysis PRESENT** (same set); **qwen35_4b PRESENT**
   (already proven); **gemma4_e4b_it ABSENT** -- no gemma directory exists
   anywhere on the volume (root holds only qwen35_9b, qwen35_4b,
   llama32_3b_instruct, mistral7b_instruct_v03, plus `_archive`/`_live`, neither
   containing gemma). Consistent with gemma `never_behaviorally_launched: true`.
   **DISPOSITION (lead-authorized):** gemma's pool/split CANNOT be reused, so the
   fresh-mine fallback is authorized for **gemma ONLY** -- `mine_eval_pool.py` +
   `split_fit_heldout.py` run fresh on gemma's own checkpoint at launch. **Reuse
   provenance for gemma's pool is LOST and is recorded as such**
   (`families/gemma4-e4b.yaml reuse.doubt_snap.pool_provenance: fresh_mine`;
   pool_counts + split_manifest + g0_prep_summary marked reference-only). The
   frozen late-site DIRECTION / tau / standardization (`c_hat`, `u_d`,
   `random_direction`, `gate_fit`, `build_manifest`) are STILL reused verbatim --
   committed + hash-pinned -- and applied to gemma's fresh rows as a FROZEN
   OPERATING POINT, mirroring `qwen35-4b-midband-heldout`'s
   frozen-direction-on-fresh-activations pattern. Gemma's late-arm DOSE is
   calibrated fresh on its fresh FIT rows (option B), uniform with the other
   three families. Gemma's G0 reuse-integrity hash check is scoped to the frozen
   late-site artifacts only (see gates.yaml `reused_rows_integrity` and
   `family_config.integrity_artifact_names`); the >=150 / >=250 held-out power
   bar applies to gemma's own fresh mine. llama/mistral/qwen35-4b reuse is
   unaffected (row text PRESENT; full pool reuse).
4. **[RESOLVED 2026-07-23, lead+user] Gemma reuse caveats.** Gemma's frozen
   late-site artifacts are FIT-prep only (never dose-exercised; no
   `dose_fit.json`); its late gate AUC is 0.9472 (weakest, still >= 0.90). These
   frozen late-site direction/gate files are the ONLY reuse gemma keeps, applied
   to gemma's fresh rows as a frozen operating point (see #3). The doubt-snap
   held-out-known count of 251 (~1-row margin) is now MOOT: gemma fresh-mines its
   own pool, so the >=250 held-out-known power bar applies to gemma's OWN mine,
   not to that reference count. Gemma proceeds: fresh pool/split + frozen
   late-site operating point + fresh late dose (option B).
5. **Render/anchor reconciliation.** The frozen late direction/gate are valid
   only if this experiment's anchors at the late site use doubt-snap's own
   render/anchor convention (BASELINE_SYSTEM_PROMPT, anchor at `prompt_len - 1`,
   `enable_thinking=False`); this must be smoke-verified at first run
   (cannot be GPU-tested pre-sign).
6. **[RESOLVED 2026-07-23] RunLog dependency (carried from the draft).**
   `run_contrast.py` requires the tuner branch `feature/runlog`. After merging
   `main` (2026-07-23) this experiment's submodule gitlink pin is
   `901dbe803699e0bf00b73426526babdaf8598cf3` (main's pointer). Verified
   read-only that `feature/runlog` (tip `8d95786`, `shared/utilities/run_log.py`
   + `tests/shared/utilities/test_run_log.py`) IS an ancestor of `901dbe8`
   (0 commits on runlog not in `901dbe8`; `run_log.py` blob present in the
   `901dbe8` tree; `901dbe8` is on `origin/main`). **No further submodule
   pointer bump is needed** -- the RunLog dependency is already satisfied by the
   pinned pointer. NOTE (not a pointer bump): this worktree's submodule working
   tree is still checked out at the older `e4ca5d4`; a routine `git submodule
   update` to materialize `901dbe8` is required before launch, but the pinned
   pointer itself needs no change. The submodule was not modified.

## Outcome

**VERDICT: INCONCLUSIVE.** Signed 2026-07-24 (lead + user). Instrument of
record: `cross_family_rollup.py`, output at
`analysis-committed/cross_family_rollup.json`.

Only 2 of the 4 registered families ran past G0. Per the roll-up rule stated
above at "if fewer than 3 families ran at all, the experiment is INCONCLUSIVE,
not a pass", the cross-family question is **not answered in either direction**:
2 families supports neither "generalizes" nor "does not generalize".

### Per-family primary gates (held-out)

| family | best mid site | G1 confab `clean_tighten` | Wilson 95% | G1 | G2 known-correct | Wilson 95% | G2 | primary |
|---|---|---|---|:--:|---|---|:--:|:--:|
| llama-3.2-3b | hs17 | 647/872 = **0.7420** | [0.7119, 0.7699] | PASS | 4/334 = 0.0120 (fired 0/334) | [0.0047, 0.0304] | PASS (non-diagnostic) | PASS |
| mistral-7b-v03 | hs15 | 642/1312 = **0.4893** | [0.4624, 0.5164] | FAIL | 2/382 = 0.0052 (fired 0/382) | [0.0014, 0.0189] | PASS (non-diagnostic) | FAIL |
| qwen35-4b | -- | not run | | | | | | not run |
| gemma4-e4b | -- | not run (G0: instrument invalid, see below) | | | | | | not run |

Mistral fails G1 on the **floor** only (0.4893 < 0.50); its Wilson lower
(0.4624) clears the 0.40 sub-criterion, and the interval straddles the floor
(upper 0.5164). This is a marginal miss, not a collapse, and should not be
reported as "mistral does not actuate".

Late-reference arm (non-gating, descriptive): SKIPPED on both run families --
no usable late-arm dose was found in fresh calibration, as anticipated by
`doubt-snap-cross-family-confirmatory`'s late-site null. The primary does not
depend on the late arm.

### Registered-instrument defects found at resolve

Three defects were found while resolving. All are recorded here rather than
worked around, and none of them changes the INCONCLUSIVE verdict.

1. **G2 is non-diagnostic here: its PASS stands, but carries a caveat.** Dosing
   occurs only when the KU readout gate fires, and the gate correctly does not
   fire on known-correct rows. The dosed known-correct denominator is therefore
   **0 on every family measured** (llama hs17: 0/334; mistral hs15: 0/382;
   mistral hs12: 1/382). The G2 numerator's failure events are drawn entirely
   from never-dosed rows -- confirmed by `successes=2` being identical at two
   different mistral layers under different doses, i.e. the metric is invariant
   to the intervention it claims to measure.

   Per the standing rule in
   `.skills/experiment-runner/reference/gate-diagnosticity.md` -- "a locked
   gate's PASS stands exactly as registered even when it is later shown to be
   non-diagnostic; that caveat travels forward with the result, it does not
   reopen the verdict" -- **the registered G2 PASSes are NOT re-labelled.** They
   stand as PASS, reported here with their fire rates (0/334 and 0/382), and
   must never be cited as evidence that the write is selective or safe: at 0
   dosed rows they are evidence about baseline malformedness only. An earlier
   draft of the Outcome proposed retroactive re-labelling to NOT-ADJUDICABLE;
   that was withdrawn as goalpost movement in the direction of severity. The
   replacement gates (G2a gate-selectivity, G2b forced-dose write-selectivity,
   with a computed minimum-N floor of 35) are forward-looking only and are
   specified in the pending Tier 1 revision at
   `docs/protocols/2026-07-24-jspace-gate-and-instrument-revision.md`.
2. **The registered success/falsifier rule is stated inconsistently across two
   registered documents.** `AMENDMENT.md` (this file, above) contains the
   "fewer than 3 families ran => INCONCLUSIVE" floor; `experiment.yaml`'s
   `falsifier:` field does not, stating only "<=1 clears => FALSIFIED, exactly
   2 => MIXED". At the observed n_run=2 / n_passed=1 both texts fire, giving
   INCONCLUSIVE and FALSIFIED respectively. Resolved in favour of INCONCLUSIVE:
   the roll-up script implements the floor, and the floor is the conservative
   reading (2 families can no more establish "does not generalize" than
   "generalizes"). Folded into the same Tier 1 revision.
3. **gemma4-e4b activations were corrupted by `use_cache=False`** (G0 stop, so
   excluded from the denominator rather than counted as a failure). On
   gemma-4-E4B, blocks 24-41 read donor K/V from blocks 22/23
   (`first_kv_shared_layer_idx = 24`) *through the cache object*; disabling the
   cache starves them. hs00-hs24 were bit-identical to a correct run; hs25
   collapsed to cos 0.732 and decayed to 0.075 by hs42. The family's 0/176
   write null was fit on corrupt activations and is therefore
   **uninterpretable, not negative**. Re-extraction at full depth with
   `use_cache=True` is complete and verified both negatively (all previously
   cached indices changed) and positively (no discontinuity at the hs24/hs25
   seam: cos 0.658 vs median 0.900, robust z -2.52). llama/mistral/qwen are
   unaffected (min cos 1.000000) and their results stand.

### Descriptive finding not covered by the gates

gemma-4-E4B is **readable at every depth**: held-out KU-direction AUC >= 0.977
from hs5 through hs42, peaking at hs18 (relative depth 0.429) at 0.9999. The
read profile is therefore **saturated** and supplies no site-selection signal
for this family. Combined with the write null, this sharpens the read/write
dissociation already visible in llama and mistral: sites chosen by a READ
criterion are not thereby good WRITE sites, and on gemma the read criterion
cannot choose at all.

One unexplained observation, recorded so it is not lost: in the *corrected*
gemma data, `cos(hs23, hs24) = 0.012484` -- near-orthogonal, at the donor-block
boundary. Read AUC shows no disruption across it (hs23 0.9998, hs24 0.9980), so
it is not destructive, but it is uncharacterized.

### Status

The experiment is **not resolved**. qwen35-4b is being run to reach the minimum
denominator of 3 registered by the roll-up rule; this is protocol-following
under the INCONCLUSIVE verdict, not a post-hoc denominator change. This Outcome
will be re-adjudicated on the roll-up instrument once that family completes,
and any revision will be recorded as an amendment to this section rather than
by overwriting it.
