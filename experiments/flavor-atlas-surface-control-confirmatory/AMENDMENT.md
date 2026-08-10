# Surface control for the raw-base flavor atlas: does the overt-unanswerability separation survive style removal?

Status: draft (not signed; do not launch as confirmatory evidence). Design
PI-approved 2026-08-10; the OPEN QUESTIONS section carried by the working
draft has been resolved by the lead and is folded into this text rather than
reproduced. `bin/exp sign` still owns pinning the instrument and flipping
this to `signed`.

Keep this document the prose home for the experiment. The machine state lives
in `experiment.yaml` and is never duplicated here.

- Slug: `flavor-atlas-surface-control-confirmatory`
- Type: probe-fit (analysis-only reanalysis of existing captures)
- Tier: 3 (exploratory-confirmatory; nothing here pools with any headline
  matrix)
- Substrate: `unsloth/Qwen3-4B`, revision
  `64033659d5caf1b8ed7f929b29de705e93a4d468`, raw pretrained base, no
  adapter, bf16. No model is loaded by this cell; the substrate is named
  because it is the substrate whose captured activations are re-read.

## Motivation and posture

`flavor-atlas-rawbase` resolved as a mixed atlas: every one of the six KUQ
flavors separates from the KUQ known pool at held-out out-of-fold AUROC
0.9800 to 0.9994 at its best layer on the raw base, SelfAware reads 0.9937,
and AmbigQA is unreadable at all 37 layers (best 0.6590). Its registered
descriptive reading was that the pretrained base carries a broad
unanswerability code across overt flavors and that the operative boundary is
overt versus covert unanswerability.

That cell recorded its own principal threat before any confirmatory use
(`experiments/flavor-atlas-rawbase/NOTEBOOK.md`, RESULT entry
2026-08-10T01:55Z): KUQ and SelfAware unknowns are stylistically
distinctive question types, so a within-dataset known-versus-unknown probe
may partly ride surface style; free cross-dataset transfer argues against a
pure dataset artifact but does not eliminate style as a shared carrier. The
same entry pre-stated that a style-controlled cell must be registered before
any promotion of the atlas to a claim.

Two already-committed quantities sharpen the worry rather than dissolve it.
First, the separation is nearly complete at the shallowest computed depth:
at hidden state 1, one block above the embedding, the six flavors already
read 0.9201 to 0.9888 and SelfAware reads 0.9583, so the best-layer values
of 0.98 and above buy very little over what is available immediately after
the first block. A code that is fully formed at hidden state 1 is exactly
what a lexical or morphological property of the question text would look
like. Second, the anchor position is the last token of a fixed chat
template, so hidden state 0 is byte-identical across every row of a panel
and reads exactly 0.5000 for every flavor; all of the separation therefore
enters through attention over the question tokens, which is the channel a
style account also uses.

The alternative hypothesis this cell exists to kill or confirm, stated
plainly: the flavor-atlas separation is a style artifact, meaning the probe
reads shallow surface markers of the question (interrogative form, length,
punctuation and digit profile, topic vocabulary, KUQ template
regularities) rather than a representation of unanswerability.

Posture. This is the surface leg of the promotion path for the
flavor-atlas discovery. It gates promotion of exactly one claim: that the
raw pretrained Qwen3-4B base carries a broad, freely transferring
unanswerability code covering all six overt KUQ flavors and SelfAware.
It does not by itself complete the program's promotion rule, which names
fresh seeds, a larger model, or held-out material. This cell is a surface
control on the same captures: it removes one named alternative and
supplies a held-out-dataset leg through S3, but it adds no fresh seed and
no fresh substrate, so passing it removes one named alternative without
licensing the claim on its own. A cell that would complete promotion in one
step -- re-running the atlas plus this control on a second substrate that
already has a resolved family atlas, `google/gemma-4-E4B-it` at revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187` -- would cost new GPU extraction
and is out of scope here; it is a separate registered cell if the lead wants
it.

## Design

### Primary method and why it is the one chosen

Primary method is cross-fitted linear surface residualization applied to the
existing `flavor-atlas-rawbase` extractions, followed by the atlas's own
pinned probe protocol run unchanged on the residualized activations. The
program already owns this instrument: `family-atlas-surface-residualization-control`
resolved 2026-07-23 with the identical construction (frozen unsupervised
prompt-surface representation, ridge prediction of the activation matrix
out of fold, controlled matrix `H - H_hat`), and its registered treatment
strength, permutation-null, and planted-signal constants are reused here
verbatim rather than reinvented.

The alternative method, a surface-matched fresh pool, is not chosen. It
requires new generation and new full-depth capture, and the program's two
attempts at construction-based surface balance both ended without a
controlled result: `family-atlas-surface-diversity-control` failed its
balance gates on both substrates, and `family-atlas-surface-matched-pool-control`
hard-stopped at G1 with 74 matched triads against a floor of 64 per
partition. Residualization removes matching from the decision path, uses
every row already captured, and costs no GPU time. If this cell returns the
ambiguous or collapse branch, the fresh matched pool is the registered
escalation, not the first move.

### Inputs, pinned by path and sha256

All inputs already exist on disk. Nothing is regenerated.

Captured activations, `unsloth/Qwen3-4B` raw base, anchor family, all 37
hidden states, float32, one safetensors file per row:

- `experiments/flavor-atlas-rawbase/analysis/extraction/kuq/` with
  `manifest.json` sha256
  `718aa477a1026f9db4f86d7983701cb10c8f91d2f537ec03842d8f4edec5fa00`,
  n_rows 5540, n_answered 5540, n_hidden_states 37, hidden_dim 2560.
- `experiments/flavor-atlas-rawbase/analysis/extraction/ambigqa/` with
  `manifest.json` sha256
  `11789967714e11b83b9816645570e088f26ee023ad43bd35fbb3ef4e1e17af1e`,
  n_rows 2748, n_answered 2748, n_hidden_states 37, hidden_dim 2560.
- `experiments/flavor-atlas-rawbase/analysis/extraction/selfaware/` with
  `manifest.json` sha256
  `f3b421fefefd252cae6fc008d583ec6308a1a128c6b19c246f58bc5f14733d60`,
  n_rows 3369, n_answered 3369, n_hidden_states 37, hidden_dim 2560.

Panels supplying `row_key`, `question`, `label`, `flavor`:

- `experiments/flavor-atlas-rawbase/analysis/panels/kuq_panel.jsonl` sha256
  `69433a777d40b76544b7f4575bc042bb2a9d4d159ca6e8a8bf20d133cf0a8eef`
- `experiments/flavor-atlas-rawbase/analysis/panels/ambigqa_panel.jsonl` sha256
  `ee60cbf9115eefc18a997a0a81600ce627789c6f710f9905fe959936ba33d7f2`
- `experiments/flavor-atlas-rawbase/analysis/panels/selfaware_panel.jsonl` sha256
  `378762ac7cd703743b7b4edc54bdbdd86fa47e1cd8657688f4dbf5d43aa186f0`
- `experiments/flavor-atlas-rawbase/analysis/panels/panels_manifest.json` sha256
  `6a58e429c930723c9e6c29afa76821cacbdc9a92b053ec4975c8618f8a5225d0`

Baseline numbers this cell must reproduce:

- `experiments/flavor-atlas-rawbase/analysis-committed/atlas_sweep.json`
  sha256 `d3327f7346908492814459566e27682df369c38eee8429f4f13ddecadd83ec10`

Pinned probe protocol, imported unchanged:

- `experiments/ood-breadth-beyond-selfaware/internal_panel_probe_gate.py`
  sha256 `ee3f22eed5f8b4fe8f260c5b3335c565156eadfcf083473bb445921d29885b08`
  (`_cv_auroc_with_oof`: StandardScaler plus L2 LogisticRegression C=0.5,
  StratifiedKFold 5, seed 0, held-out out-of-fold AUROC)

Reference implementation for the surface machinery, read but not imported
across experiment boundaries:

- `experiments/family-atlas-surface-residualization-control/reanalyze_surface_residualization.py`
  sha256 `d8cacf172d7b4571978105fb40579393d0fed519d024cfa794789b30722b174f`

### Frozen prompt-surface representation

One surface basis is fitted, unsupervised and without any label, on the
union of the three panels' question strings (11657 questions). Fitting on
the union rather than per panel is what makes the cross-dataset transfer
readings in S3 comparable. The basis is then frozen.

Scalar block, all derived from the question string and the rendered prompt:
rendered-prompt token count; question character, whitespace-word, and line
counts; digit, punctuation, newline, and uppercase counts and fractions.

Interrogative-form block, added here because interrogative form is a named
suspect in the style account and the parent instrument did not carry it
explicitly: a one-hot over the normalized leading interrogative token,
bucketed as what, which, who, whom, whose, when, where, why, how, an
auxiliary or copula lead (is, are, was, were, do, does, did, can, could,
will, would, should, has, have, had), and other; plus indicators for a
terminal question mark and for the presence of any digit.

Lexical block: deterministic hashed word 1-2gram and character 3-5gram
TF-IDF over question text only, 4096 hash features each, reduced to 32
seeded SVD components each and standardized, matching the parent
instrument's pinned lexical settings.

Combined block is the concatenation of all three. Adding the
interrogative-form block strengthens the surface model relative to the
parent, which makes it remove more, which is the conservative direction for
this cell's prediction.

Prohibited inputs, and this is a deliberate and load-bearing deviation from
the parent instrument: dataset source, KUQ category, flavor, the panel
identity of a row, and the label itself may not enter the surface matrix.
In the parent cell, source and category were legitimate covariates because
roles there were behavior-derived. Here the label is exactly pool
membership and flavor is exactly the KUQ category, so admitting either
would hand the surface model the answer and make the residualization
vacuous. Also prohibited: any model output, generation text, completion
length, correctness, or any post-capture outcome. The lexical input is
question text only. This prohibition is enforced structurally in the
harness, not by a post-hoc scan: the featurization functions take only bare
question strings and integer token counts, never a row dict, so no
prohibited field is reachable from inside them.

### Cross-fitted residualization

For each panel independently and for every one of the 37 hidden-state
indices, a deterministic five-fold outer split predicts the multioutput
activation matrix `H` (rows by 2560) from the frozen surface matrix `Z`
with ridge regression. Within each outer training fold, three-fold inner
cross-validation selects alpha from `[0.01, 0.1, 1, 10, 100, 1000]` by
activation mean squared error. The controlled matrix is `H - H_hat`, where
every row of `H_hat` was predicted without that row's own activation.
Outer folds are stratified by (label, flavor) so every flavor is represented
in every fold. Fold assignment is fixed by seed and is identical across
layers, across surface blocks, and across all controls, so every comparison
in this cell is within one partition.

Cross-fitting is what keeps this leakage-free: no row's residual is computed
using a surface-to-activation mapping that saw that row's activations. The
unsupervised basis fit (TF-IDF vocabulary, SVD, scaling) is transductive
within the fixed 11657-question population, as in the parent cell, and
never sees a label.

Ridge alphas, per-layer fraction of activation variance removed, and
per-layer activation out-of-fold R2 are retained for every panel and layer.

### Readouts

S1, primary. The pinned probe protocol, run unchanged, on the combined-block
residualized activations, for every panel and every layer. Reported as full
37-layer curves for all nine rows of the atlas (six KUQ flavors, pooled all
unknowns, SelfAware, AmbigQA). Each KUQ flavor probe is that flavor's
unknowns against the full 3071-row KUQ known pool, byte-identical to the
atlas construction.

S2, secondary, banded but not deciding. The same probe protocol applied to
the surface matrix `Z` alone, no activations, for every row of the atlas.
This measures how much of the label the registered style model explains on
its own. It is layer-free, one number per row of the atlas. It exists to
tell a survival apart from a vacuous survival: if the surface model cannot
separate the labels at all, then there was no style carrier to remove and
the alternative dies at its source rather than at the residualization step.

S3, secondary, descriptive. Residualized cross-dataset transfer, restricted
before any number exists to twelve pre-declared cells: each of the six KUQ
flavor probes fitted on the full residualized KUQ flavor pool at that
flavor's committed best layer and evaluated frozen on residualized SelfAware
rows at the same layer, and the SelfAware probe fitted at L25 and evaluated
frozen on each of the six residualized KUQ flavors at L25. Frozen-probe
evaluation follows the atlas M4 construction. This is the leg that speaks to
a style carrier shared across datasets. It is descriptive: it cannot pass,
falsify, or rescue S1, and it is not promoted to a banded secondary -- the
decision surface stays fixed at the twelve S1 primary cells.

Descriptive-only additions, explicitly non-deciding: the low-dimensional-block
residual and lexical-block residual curves, the surface-explained variance
curves, and the maximum-over-layer residualized AUROC per flavor reported
next to its full curve.

### Controls

C1, treatment strength. An unchanged AUROC is interpretable only if the
surface model removed a measurable activation component. At each primary
layer, the combined-block activation out-of-fold R2 must be at least `0.01`
and at least `0.005` above the 95th percentile of the maxima from 20
fixed-seed permutations of `Z`. Both constants are the parent cell's
registered values, reused verbatim.

C2, permutation negative control. The same 20 permutations of `Z`, permuted
within (panel, label, flavor) blocks so the label-conditional surface
distribution is preserved while row-level surface-to-activation alignment is
destroyed, are each run through the identical residualization and probe.
This asks whether generic variance removal alone can produce a collapse. At
least 18 of 20 permuted runs must leave every one of the six KUQ flavors at
or above `0.90` at both of its primary layers. The 18-of-20 requirement is
the parent cell's registered value.

C3, planted style channel, positive control. Hidden state 0 is the only
layer with a committed exactly-null baseline: the anchor is the final token
of a fixed chat template, hidden state 0 is byte-identical across every row
of a panel, and the atlas records exactly 0.5000 there for all six flavors,
for SelfAware, and for AmbigQA. Any readability planted there is
unambiguously the planted channel and nothing else.

Construction: fit the pinned probe family (same scaler, same C=0.5) on `Z`
alone over the full KUQ panel with the pooled unknown-versus-known label to
obtain weights `w`; form the scalar `s = Z_std w`, which is by construction
exactly linear in `Z`; add `gamma * s` along a seeded random unit direction
`u` in R^2560 to the KUQ hidden-state-0 matrix, with `gamma` the smallest
value on the fixed grid `[0.25, 0.5, 1, 2, 4, 8]` times the hidden-state-1
centered activation RMS that makes the planted pooled hidden-state-0 OOF
AUROC reach at least `0.90`. Hidden state 0 has zero row variance, so
`gamma` is expected to be a scale nuisance rather than a real knob; it is
gridded anyway so the reachability step is mechanical and pre-stated.

Pass condition: applying the identical residualization, with the identical
fold assignment used for the unplanted analysis, must return the planted
hidden-state-0 pooled AUROC to at most `0.75`, and the residualized
hidden-state-0 curves for the six flavors must not move by more than `0.05`
from their unplanted residualized values. `0.75` is the atlas's own
registered unreadable ceiling and `0.05` is the parent cell's registered
maximum controlled-profile deviation. Failure means the instrument was
structurally unable to remove a surface-carried separation, and the cell is
indeterminate, never a pass and never a falsification.

The plant is linear in `Z` by construction, so ridge residualization is
expected to remove it almost perfectly: this control verifies reachability
within the surface model's own span, not removal of a nonlinear style
encoding. That is an honest scope limit and belongs in the outcome
write-up, not only here.

### Containment

Committed output is a counts-only JSON at
`analysis-committed/surface_control.json`: AUROCs at 4dp, per-flavor n
counts, layer curves, R2 and variance-removed curves, permutation and
planted-control summaries, gate records, input shas. No question text, no
row-level surface matrix, no row-level prediction, and no activation enters
the committed surface. Row-level surface matrices, out-of-fold predictions,
fold state, and selected alphas are retained under gitignored `analysis/`
so a later analyst can reconstruct any registered residual as source
activation minus retained out-of-fold prediction without recomputing
features. `experiments/flavor-atlas-rawbase/.gitignore` already excludes
`analysis/`; this cell carries the same exclusion.

## Multiplicity discipline

The atlas grid is 9 rows by 37 layers. This cell does not re-decide on that
grid. The decision surface is fixed before any residualized number exists at
twelve cells: the six KUQ flavors, each at two layers.

Layer one is the flavor's own committed best layer from the atlas
(ambiguous L26, controversial L20, counterfactual L19, false assumption
L29, future unknown L17, unsolved problem L28). These layers were selected
post hoc by maximum over layers in the atlas, which is precisely why they
are the right target here: they are the layers the atlas actually reports,
so they are the numbers a promoted claim would rest on.

Layer two is L35, the anchor layer fixed by
`rawbase-ambigqa-boundary-readout` before the flavor atlas existed and
therefore not selected on this data at all. The atlas reports every flavor
at L35 (0.9766 to 0.9990). L35 is the statistically clean leg; the
best-layer cells are the claim-relevant leg. Both must hold: P1 is a strict
conjunction over all twelve primary cells, with no tolerance for a single
flavor failing, because the claim being promoted is "all six overt
flavors," which is exactly what the atlas verdict says.

Decisions are per flavor. There is no pooled single-number verdict for the
six. The pooled all-unknowns row (best L27), SelfAware (best L25), and
AmbigQA (best L25) are each read at their own best layer and at L35 as
banded reference rows: they contextualize and sanity-check, they do not
decide P1 or F1.

Full 37-layer residualized curves are reported for every row so that no
max-over-layer selection is hidden. Any maximum-over-layer residualized
value is printed next to its full curve and is descriptive.

## Bands and where every number comes from

Every band below is one of two constants already committed in
`experiments/flavor-atlas-rawbase/gates.yaml` before this cell existed. No
new threshold is invented, and neither band is retuned to a relative
measure: `0.90` is a low bar against baselines of 0.98 and above (a flavor
could drop from 0.9994 to 0.9010 and still count as surviving), but
traceability to an already-committed number is chosen over a
higher-sensitivity band that would itself be a new invention.

- `0.90` is that cell's registered `p1_discovery_floor_heldout_auroc`. All
  twelve primary baselines sit at 0.9766 or above, so this floor leaves
  between 0.077 and 0.099 of headroom.
- `0.75` is that cell's registered `p2_ambiguity_ceiling_all_layers`. It
  sits above the highest AmbigQA reading anywhere in the atlas (0.6590),
  which is the program's operational level for an unanswerability surface
  the base cannot read. A residualized flavor at or below 0.75 has fallen to
  the covert-unanswerability level.

Baselines the residualized numbers are compared against, all from
`atlas_sweep.json`:

| Row | n unknown | best layer | AUROC at best | AUROC at L35 | AUROC at L1 |
|---|---:|---:|---:|---:|---:|
| ambiguous | 411 | 26 | 0.9800 | 0.9766 | 0.9201 |
| controversial | 490 | 20 | 0.9960 | 0.9949 | 0.9625 |
| counterfactual | 403 | 19 | 0.9963 | 0.9952 | 0.9773 |
| false assumption | 368 | 29 | 0.9918 | 0.9912 | 0.9432 |
| future unknown | 490 | 17 | 0.9994 | 0.9990 | 0.9888 |
| unsolved problem | 307 | 28 | 0.9937 | 0.9915 | 0.9295 |
| pooled all unknowns | 2469 | 27 | 0.9887 | 0.9874 | 0.9449 |
| SelfAware | 1032 | 25 | 0.9937 | 0.9925 | 0.9583 |
| AmbigQA | 1503 | 25 | 0.6590 | 0.6338 | 0.5935 |

All KUQ flavor probes use the same 3071-row known pool.

## Prediction

- P1 (primary): after cross-fitted combined-surface residualization, all six
  KUQ flavors retain held-out out-of-fold AUROC at or above 0.90 at both of
  their two primary layers, that is at the flavor's committed best layer and
  at L35, for all twelve primary cells.
- P2 (reference): SelfAware retains AUROC at or above 0.90 at both L25 and
  L35, and AmbigQA stays at or below 0.75 at both L25 and L35.
- P3 (secondary, S2): the surface-only probe on `Z` alone reaches at least
  0.75 for at least one of the six KUQ flavors, that is a style carrier
  demonstrably exists in this pool and the residualization has something
  real to remove.

## Falsifier

- F1 (style artifact confirmed): with C1, C2, and C3 passing, all six KUQ
  flavors fall to 0.75 or below at both primary layers. Then the flavor-atlas
  separation is carried by the registered linear surface model, the atlas
  discovery may not be promoted to a claim, and the atlas write-up is revised
  in the same pass to state that the raw-base readout rides prompt surface
  on these pools. That write-up revision touches a resolved experiment's
  outcome text, which is a governed edit and remains the lead's call at
  resolve time, not a delegated one.
- F2 (partial style dependence, blocks promotion): with C1, C2, and C3
  passing, any one of the twelve primary cells reads below 0.90. P1 is false.
  Promotion is blocked. The result is reported per flavor with no pooled
  rescue and no band retuning.

F1 and F2 are nested by construction: F2 fires whenever F1 fires. They are
kept separate because they carry different write-ups. F1 is a positive
finding about the atlas. F2 is a blocked promotion.

## Ambiguous zone

Any flavor reading strictly between 0.75 and 0.90 at either primary layer is
partial attenuation. It is reported at its measured value, per flavor, with
no promotion and no single-number verdict, exactly as the atlas reported its
mixed result. The registered consequence of landing anywhere in the
ambiguous zone, or of a split where some flavors survive and others collapse,
is the Shape B escalation: a fresh surface-matched pool with new capture,
registered separately.

A further asymmetry is stated here, before any number exists, because it
governs how a collapse may be written up. Residualization removes activation
variance predictable from surface, not label variance. If style and overt
unanswerability are close to collinear in KUQ and SelfAware, then a collapse
is consistent with two different worlds: the probe was reading style, or the
model does encode unanswerability but its encoding is inseparable from style
on these pools. F1 firing therefore licenses exactly two statements, "the
atlas separation is not promotable on these pools" and "the fresh
surface-matched pool is the next instrument". It does not license "the raw
base has no unanswerability code". Survival is the asymmetrically stronger
outcome: it kills the style account within the registered surface model's
scope without any such caveat.

## Gates

Integrity gates first, fail-closed. Any SG failure voids the dependent S
readings before they are looked at. See `gates.yaml` for the machine-readable
thresholds; the eight gates in order are:

- **SG0 input integrity.** Every input sha256 in the Design section matches
  byte for byte; the three extraction manifests report n_rows equal to
  n_answered equal to 5540, 2748, 3369 with n_hidden_states 37 and
  hidden_dim 2560; panel row counts and the six locked KUQ flavor counts
  match `flavor-atlas-rawbase/gates.yaml` fg0 exactly; every panel row_key
  has exactly one anchor safetensors file with 37 keys L0 to L36.
- **SG1 no new capture.** Zero GPU verbs. No model is loaded. No file under
  any `extraction/` directory is created, modified, or deleted; the
  directory content digest is recorded before and after and must be
  identical.
- **SG2 baseline reproduction.** Running the pinned probe on the RAW
  (non-residualized) activations must reproduce every one of the eighteen
  banded baseline cells in the table above to the committed 4dp exactly, and
  must reproduce hidden state 0 as exactly 0.5000 for all nine rows. Failure
  stops the analysis as indeterminate; it means this cell is not reading the
  same instrument the atlas read.
- **SG3 surface-model hygiene.** The realized surface matrix contains no
  prohibited input: no source, panel, category, flavor, label, generation,
  correctness, or completion field. Fold assignment is identical across all
  layers, blocks, and controls. Every reported residual is out of fold.
- **SG4 treatment strength (C1).** At each of the twelve primary layers, the
  combined-block activation OOF R2 is at least 0.01 and at least 0.005 above
  the 20-permutation 95th percentile. Failure is indeterminate, never a pass
  and never a falsification.
- **SG5 planted-channel reachability (C3).** The plant reaches pooled
  hidden-state-0 AUROC at least 0.90; residualization returns it to at most
  0.75; the six flavors' residualized hidden-state-0 values move by at most
  0.05 from unplanted. Failure is indeterminate.
- **SG6 permutation negative control (C2).** At least 18 of 20 permuted-`Z`
  residualized runs leave all six flavors at or above 0.90 at both primary
  layers. Failure is indeterminate.
- **SG7 containment and provenance.** Committed JSON passes a positive
  schema check and a prohibited-text scan; no question text, row-level
  matrix, prediction, or activation appears in `analysis-committed/`; all
  other writes stay under gitignored `analysis/`; the run log carries a
  provenance JSON line.
- **SG8 decision.** Only after SG0 to SG7 pass, adjudicate P1, P2, P3, F1,
  F2, and the ambiguous zone against the bands above. Nothing else decides.

## Compute budget

Zero GPU. No model is loaded, no tokenizer forward pass is run beyond the
prompt-length feature, which is computed from the already-rendered prompts
recorded at extraction time or, if not recorded, from the cached tokenizer
on CPU. No new extraction, no generation, no cloud.

CPU cost is dominated by the ridge fits. Per panel and per layer the design
is one multioutput ridge over roughly 200 surface features and 2560 outputs
on at most 5540 rows, with 5 outer folds and a 3-fold by 6-alpha inner
selection. Because `Z` is shared across layers and across folds, the fold
Gram factorization is computed once per fold and reused for every alpha and
every layer, so the per-layer marginal cost is a small number of
matrix multiplies. 111 panel-layer combinations for the main pass, plus 20
permutation replicates and one planted replicate restricted to the primary
layers and hidden state 0. Peak memory is one panel-layer activation matrix,
5540 by 2560 float32, about 57 MB.

Expected wall clock is tens of minutes to a small number of hours on one CPU
box. The harness is incremental and resumable per (panel, layer, block) so
an interruption never forces a full recompute, and any process expected to
exceed 15 minutes launches through
`experiments/common/launch_detached.sh` with an exit-code watch.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | (left for the lead, to be filled before any residualized number exists) |
| user | (left for the PI, to be filled before any residualized number exists) |

## Outcome

Filled at resolve. Record the twelve primary cells, the reference and
secondary readouts, every gate result, and the one-sentence summary that
also goes into `verdict:` in the manifest.
