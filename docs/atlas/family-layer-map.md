# Family layer map

Standing registry for the `family-atlas` skill (`.skills/family-atlas/`).

## Working hypothesis

This program's actuation work assumes, without yet having proven, that three
read axes -- doubt (known-vs-refused), caution (refused-vs-confab), and raw
refusal (refused-vs-answered) -- are linearly readable in every
instruction-tuned model, but that WHERE they read (the layer band) is
relative to the model's family and size, not a portable constant. Rows in
this table are the evidence for or against that hypothesis, substrate by
substrate.

**Rule**: a row is added, or a row's numbers are updated, only after the
governed experiment doc it cites is signed AND resolved. This table never
carries a number that is not traceable to a specific `AMENDMENT.md` /
`experiment.yaml` at a specific resolve date. Do not add or edit a row from
memory, from a session note, or from this file's own prior contents; open
the cited doc first.

## Registry

| Family | Model id + revision | n_layers | Atlas experiment (status) | Profile peak (layer / depth) | Band, all 3 axes >= 0.80 held-out (interior) | Best 3-axis layers | Best AUROC per axis (doubt / caution / raw_refusal) | Provenance |
|---|---|---|---|---|---|---|---|---|
| llama | `unsloth/Llama-3.2-3B-Instruct` @ `006f5dcd1393c3add266de40994ba96225e9689d` | 28 | `experiments/jspace-family-atlas` (resolved) | layer 4 of 28 (0.14 depth) | layers 15-23 | ~L20-23 | 1.00 (confounded, see note) / 0.84 (L28) / 0.90 (L25) | `experiments/jspace-family-atlas/AMENDMENT.md`, resolved 2026-07-12 |
| mistral | `mistralai/Mistral-7B-Instruct-v0.3` @ `c170c708c41dac9275d15a8fff4eca08d52bab71` | 32 | `experiments/jspace-family-atlas` (resolved) | layer 3 of 32 (0.09 depth) | layers 7-27 | ~L15-17 | 1.00 (confounded, see note) / 0.91 (L17) / 0.925 (L17) | `experiments/jspace-family-atlas/AMENDMENT.md`, resolved 2026-07-12 |
| qwen3 | `unsloth/Qwen3-4B` (bf16 sibling of the raw-base; no revision pin recorded) | 36 | `experiments/j-space-localization-qwen3-4b` (resolved, lab-diagnostic) | hs=26 (peak), band hs23-29 (0.64-0.81 depth) | not measured -- see comparability note | not measured -- see comparability note | not measured -- see comparability note | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`, resolved 2026-07-07 |
| qwen3.5 | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 32 (hybrid linear-attention) | `experiments/qwen35-4b-midband-doubt-snap` (**pending** -- draft, not signed; Stage C dose ladder not executed) | -- | -- | -- | -- | `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md`, status draft as of this table's writing; do not cite numbers from it until it resolves |
| gemma | `google/gemma-4-E4B-it` @ `fee6332c1abaafb77f6f9624236c63aa2f1d0187` | 42 blocks (hs_index 0-42 incl. embedding state) | `experiments/gemma-4-e4b-family-atlas` (resolved) | hs 4 of 42 (0.095 depth) | hs 13-42 contiguous (hs 4-6 clear marginally, broken by a raw_refusal dip at hs 7-12); interior portion hs 13-35 | hs 14-18 and hs 36-40 (clean-control set; see note) | 0.9949 / 0.9223 / 0.9272 (all at hs 40, clean control 0.592; naive per-axis maxima 1.00 / 0.9305 / 0.9345 at hs 21/25/26 are control-confounded, see note) | `experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`, resolved 2026-07-20 |

Vocabulary note (2026-07-20): running prose in this file uses the renamed
program vocabulary of `papers/common/terminology.md`; the table's axis
column headers (`doubt` / `caution` / `raw_refusal`) are artifact keys from
`atlas_summary.json` and keep their names verbatim under that file's usage
rule 1. In prose, `doubt` is the known-unknown (KU, answerability) axis.

## Cross-family pattern (standing summary, updated 2026-07-20)

Three families measured with the same instrument now show the same shape,
and the registered interior-workspace prediction has failed in all three
(each row's cited AMENDMENT.md is the source of truth):

1. **The eff_dim_frac peak is early-exterior everywhere**: llama layer 4 of
   28 (0.14 depth), mistral layer 3 of 32 (0.09), gemma hs 4 of 42 (0.095).
   In each family the profile collapses after the early peak and stays in a
   low flat band through the remaining depth.
2. **The three-axis readable band is mid-band and wide**: llama 15-23,
   mistral 7-27, gemma 13-42. Readability (all three axes >= 0.80 held-out
   AUROC) begins only AFTER the dimensionality peak has collapsed.
3. **The two properties are decoupled**: no family shows the predicted
   coincidence of dimensionality peak and readable band. Effective
   dimensionality marks the early surface/lexical regime; the epistemic
   axes (KU, caution, raw refusal) become linearly readable in the
   compression regime that follows.
4. **Coordinates do not port; the motif does**: absolute and relative layer
   indices differ family to family (the original ported-layer null that
   motivated these atlases), but the early-peak-then-readable-plateau shape
   has replicated 3 of 3 times.

Interpretation beyond these four observations (consolidation/crystallization
accounts, post-decision-report hypotheses) is NOT settled by this table and
lives in the KG hypothesis nodes and paper drafts. Deflationary-alternative
status: **anisotropy artifact TESTED AND SURVIVED 2026-07-20** (the gemma
layer-4 peak persists under whitening, top-1/2/4/8 eigendirection removal,
winsorizing, a rank-based spectral-entropy estimator, and a 50% subsample
guard; margin over the best interior candidate compresses 1.53x -> 1.12x
but the peak never relocates -- see
`experiments/gemma-4-e4b-family-atlas/analysis-committed/gemma4_e4b_it/anisotropy_control/`
and that cell's NOTEBOOK.md, lab-notebook tier); pool-composition
(surface-diversity) artifact UNTESTED; small-N coincidence under test via
the qwen3-4b-family-atlas cell (in preparation).

## Comparability notes

- **llama / mistral doubt axis**: both cells' doubt (known-vs-refused) AUROC
  reads ~1.00 from the earliest layers onward, but the resolved amendment's
  own random-direction control shows this contrast is norm/position
  confounded at the final-prompt-token anchor (a fixed random direction
  reads up to ~0.97 best-orientation at some layers). Read the doubt column
  above against that elevated baseline, not against 0.5. Caution and
  raw_refusal did not show this confound in the resolved run (random
  baseline stayed ~0.5-0.75).
- **qwen3 row**: `j-space-localization-qwen3-4b` is a different instrument,
  not a family-atlas cell. It computes a workspace-location signal (rising
  kurtosis / Hoyer sparsity / effective linear dimensionality) from a
  gradient-based J-lens (corpus-averaged JVP push vectors), not the
  family-atlas's capture-only representation-variance participation ratio,
  and it measured direction verbalization (do the project's four fitted
  epistemic directions read as uncertainty/abstention tokens under the
  J-lens), not the family-atlas's three-axis held-out AUROC read panel. Its
  profile peak (hs=26, band hs23-29) is reported here for completeness but
  is NOT numerically comparable to the llama/mistral eff_dim_frac peaks, and
  its "best 3-axis layers" / "best AUROC per axis" columns are marked "not
  measured" because that read panel was never run on this substrate. A
  proper family-atlas cell for Qwen3-4B (capture-only eff_dim_frac profile
  plus the three-axis read panel, run through this skill's own scripts) has
  not been registered as of this table's writing.
- **qwen3.5 row**: `qwen35-4b-midband-doubt-snap` is still draft (Status:
  draft, not signed, per its own `AMENDMENT.md`). Its Stage A J-lens profile
  (same JVP-based instrument as the qwen3 row, not the family-atlas's
  participation-ratio profile) found a peak at hs23 (0.558) among 14
  profiled `hs_index` points, distinct from the registered late 0.94-depth
  comparator hs30; Stage B fit directions at the three midband candidates
  {20, 23, 26} plus the late comparator hs30. Stage C (the dose ladder that
  would test whether refusal induction and JSON well-formedness decouple at
  a midband layer) has not been written or run. No numbers from this
  amendment belong in this table's numeric columns until it is signed and
  resolved; the row exists only to mark it as in-flight so the next reader
  does not re-scaffold a duplicate atlas for this substrate.
- **gemma random-direction control**: the norm/position confound that
  llama/mistral showed on the known-unknown (KU) axis appears in gemma as a LAYER-PATCHY
  elevation of the whole random-direction baseline: max-over-contrasts
  0.83-0.87 at hs 10-12, up to 0.97 at hs 24, 0.85-0.94 at hs 28-34, 0.89
  at hs 42, while staying near chance (<= 0.64) at hs 0-8, hs 14-18, and
  hs 36-40. The "best 3-axis layers" column above therefore lists the
  clean-control set, not the raw per-axis argmax layers; the argmax layers
  (hs 21/25/26) sit exactly where the random baseline is 0.80-0.97 and
  must not be used for per-family actuation layer choices. Source:
  `experiments/gemma-4-e4b-family-atlas/AMENDMENT.md` Outcome, resolved
  2026-07-20.

## See also

- `.skills/family-atlas/SKILL.md` -- the procedure that produces new rows.
- `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` -- the
  fleet whose ported-layer null motivated this atlas in the first place.
