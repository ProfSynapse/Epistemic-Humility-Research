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
| qwen3 | `unsloth/Qwen3-4B` @ `64033659d5caf1b8ed7f929b29de705e93a4d468` | 36 (hs_index 0-36 incl. embedding state) | `experiments/qwen3-4b-family-atlas` (resolved) | hs 5 of 36 (0.139 depth) | hs 22-36 contiguous; interior portion (strict 20-85% depth) hs 22-30 | hs 22-30 (clean-control interior set; avoid hs 24/32/36 where the doubt control spikes, see note) | 1.000 (confounded, see note) / 0.913 (hs30) / 0.975 (hs32-34) | `experiments/qwen3-4b-family-atlas/AMENDMENT.md`, resolved 2026-07-21 |
| qwen3 (prior lab-diagnostic, different instrument) | `unsloth/Qwen3-4B` (bf16 sibling; no revision pin recorded) | 36 | `experiments/j-space-localization-qwen3-4b` (resolved, lab-diagnostic) | J-lens hs=26 (peak), band hs23-29 (0.64-0.81 depth) | not measured (different instrument) | not measured | not measured | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`, resolved 2026-07-07; superseded for the eff_dim_frac profile + read panel by the family-atlas row above, retained as the J-lens comparator (see comparability note) |
| qwen3.5 | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 32 (hybrid linear-attention) | `experiments/qwen35-4b-midband-doubt-snap` (**pending** -- draft, not signed; Stage C dose ladder not executed) | -- | -- | -- | -- | `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md`, status draft as of this table's writing; do not cite numbers from it until it resolves |
| gemma | `google/gemma-4-E4B-it` @ `fee6332c1abaafb77f6f9624236c63aa2f1d0187` | 42 blocks (hs_index 0-42 incl. embedding state) | `experiments/gemma-4-e4b-family-atlas` (resolved) | hs 4 of 42 (0.095 depth) | hs 13-42 contiguous (hs 4-6 clear marginally, broken by a raw_refusal dip at hs 7-12); interior portion hs 13-35 | hs 14-18 and hs 36-40 (clean-control set; see note) | 0.9949 / 0.9223 / 0.9272 (all at hs 40, clean control 0.592; naive per-axis maxima 1.00 / 0.9305 / 0.9345 at hs 21/25/26 are control-confounded, see note) | `experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`, resolved 2026-07-20 |

Vocabulary note (2026-07-20): running prose in this file uses the renamed
program vocabulary of `papers/common/terminology.md`; the table's axis
column headers (`doubt` / `caution` / `raw_refusal`) are artifact keys from
`atlas_summary.json` and keep their names verbatim under that file's usage
rule 1. In prose, `doubt` is the known-unknown (KU, answerability) axis.

## Cross-family pattern (standing summary, updated 2026-07-23)

Four families measured with the same instrument now show the same shape,
and the registered interior-workspace prediction has failed in all four
(each row's cited AMENDMENT.md is the source of truth):

1. **The eff_dim_frac peak is early-exterior everywhere**: llama layer 4 of
   28 (0.14 depth), mistral layer 3 of 32 (0.09), gemma hs 4 of 42 (0.095),
   qwen3-4b hs 5 of 36 (0.139). In each family the profile collapses after
   the early peak and stays in a low flat band through the remaining depth.
2. **The three-axis readable band is mid-band and wide**: llama 15-23,
   mistral 7-27, gemma 13-42, qwen3-4b 22-36. Readability (all three axes
   >= 0.80 held-out AUROC) begins only AFTER the dimensionality peak has
   collapsed.
3. **The two properties are decoupled**: no family shows the predicted
   coincidence of dimensionality peak and readable band. Effective
   dimensionality marks the early surface/lexical regime; the epistemic
   axes (KU, caution, raw refusal) become linearly readable in the
   compression regime that follows.
4. **Coordinates do not port; the motif does**: absolute and relative layer
   indices differ family to family (the original ported-layer null that
   motivated these atlases), but the early-peak-then-readable-plateau shape
   has replicated 4 of 4 times.
5. **eff_dim_frac and the read panel are distinct instruments**: qwen3-4b
   is the cleanest demonstration -- its own prior J-lens diagnostic
   (`j-space-localization-qwen3-4b`) found an interior peak at hs 23-29,
   which the read-axis panel reproduces (the epistemic axes peak hs 22-36)
   but the eff_dim_frac profile does NOT (it peaks hs5, early-exterior).
   The J-lens was reading the interior readable regime, not the early
   dimensionality peak; the two instruments dissociate on peak location and
   both are reported per family. This was a pre-registered head-to-head
   (orchestrator: early-exterior + J-lens-non-reproduction; PI: interior
   peak); the orchestrator's call was correct on the eff_dim_frac profile,
   and the PI's interior intuition was correct on the read panel.

Interpretation beyond these four observations (consolidation/crystallization
accounts, post-decision-report hypotheses) is NOT settled by this table and
lives in the KG hypothesis nodes and paper drafts. Deflationary-alternative
status: **anisotropy artifact TESTED AND SURVIVED 2026-07-20** (the gemma
layer-4 peak persists under whitening, top-1/2/4/8 eigendirection removal,
winsorizing, a rank-based spectral-entropy estimator, and a 50% subsample
guard; margin over the best interior candidate compresses 1.53x -> 1.12x
but the peak never relocates -- see
`experiments/gemma-4-e4b-family-atlas/analysis-committed/gemma4_e4b_it/anisotropy_control/`
and that cell's NOTEBOOK.md, lab-notebook tier); **registered linear
pool-composition and prompt-surface account TESTED AND SURVIVED 2026-07-23**
on Gemma and Qwen. Cross-fitted residualization removed a measurable
surface-predictable activation component, passed planted-signal and permutation
controls, and left the required peaks at Gemma hs4 (0.095 depth) and Qwen hs5
(0.139) in both full and 50% profiles. This closes the registered linear
surface-diversity alternative, not every nonlinear raw-token surface encoding;
see `experiments/family-atlas-surface-residualization-control/AMENDMENT.md`.
Small-N coincidence is now weaker as a concern with the qwen3-4b replication
(4 of 4 families, resolved 2026-07-21) but not formally tested.

## Comparability notes

- **llama / mistral doubt axis**: both cells' doubt (known-vs-refused) AUROC
  reads ~1.00 from the earliest layers onward, but the resolved amendment's
  own random-direction control shows this contrast is norm/position
  confounded at the final-prompt-token anchor (a fixed random direction
  reads up to ~0.97 best-orientation at some layers). Read the doubt column
  above against that elevated baseline, not against 0.5. Caution and
  raw_refusal did not show this confound in the resolved run (random
  baseline stayed ~0.5-0.75).
- **qwen3 rows (family-atlas vs prior J-lens diagnostic)**: the top qwen3
  row is now the resolved `experiments/qwen3-4b-family-atlas` cell -- the
  capture-only eff_dim_frac profile plus the three-axis held-out AUROC read
  panel, run through this skill's own scripts, directly comparable to the
  llama/mistral/gemma rows. The second qwen3 row
  (`j-space-localization-qwen3-4b`) is retained as the different-instrument
  comparator: it computes a workspace-location signal (rising kurtosis /
  Hoyer sparsity / effective linear dimensionality) from a gradient-based
  J-lens (corpus-averaged JVP push vectors) and measured direction
  verbalization, NOT the participation-ratio profile or the AUROC read
  panel. The two instruments dissociate on peak location on this family and
  that is the point (see cross-family observation 5): the family-atlas
  eff_dim_frac profile peaks early-exterior (hs5), while both the J-lens
  (hs23-29) and the family-atlas read panel (hs22-36) peak interior. The
  J-lens hs=26 peak is therefore NOT numerically comparable to the
  eff_dim_frac column of the top row; it lines up with the read-panel
  column instead.
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
- **qwen3-4b random-direction control**: the same known-unknown (KU / doubt)
  norm/position confound appears a fourth time, again layer-patchy: the
  doubt axis's own `ref_vs_known` control spikes to 0.87-0.98 at hs 21, 24,
  32, and 36 while staying <= 0.79 at the other interior layers, and
  `ref_vs_confab` (caution's control) stays <= 0.79 and `ref_vs_answered`
  (raw_refusal's control) mostly <= 0.72 everywhere. The interior all-three
  read band (hs 22-36) is therefore carried by caution and raw_refusal,
  which clear >= 0.80 with real margins over their own controls; the "best
  3-axis layers" column lists hs 22-30 and flags hs 24/32/36 as the
  doubt-confounded layers to avoid for any per-family actuation site choice.
  Source: `experiments/qwen3-4b-family-atlas/AMENDMENT.md` Outcome, resolved
  2026-07-21.

## See also

- `.skills/family-atlas/SKILL.md` -- the procedure that produces new rows.
- `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` -- the
  fleet whose ported-layer null motivated this atlas in the first place.
