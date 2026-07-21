# Family Atlas Surface-Diversity Control

Status: running (CPU analysis complete; PI verdict adjudication pending).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The capture-only family atlas has now produced the same geometric ordering on
four model families: the representation-variance participation-ratio profile
peaks early-exterior, while the known-unknown (answerability), caution, and raw
refusal readouts become jointly readable later in a broad interior band. The
governed outcomes are recorded in `experiments/jspace-family-atlas/AMENDMENT.md`,
`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`, and
`experiments/qwen3-4b-family-atlas/AMENDMENT.md`. The standing registry and its
comparability limits are in `docs/atlas/family-layer-map.md`.

One deflationary account remains open. The early `eff_dim_frac` peak may be a
surface-diversity artifact: prompt length, character and punctuation structure,
lexical overlap, dataset origin, category, or rendering conventions may account
for the variance that peaks near the input. The Gemma anisotropy control already
showed that whitening, top-eigendirection removal, winsorizing, a spectral-
entropy estimator, and a seeded subsample do not relocate Gemma's peak. That
analysis established the relevant rigor rule for this control: peak location is
the invariant; margin or prominence is descriptive.

Instrument tier is selected first. This is Tier 3, analysis-only work under
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`: it re-reads
existing captures, introduces no atlas cell or arm, changes no registered atlas
metric, and changes no prior verdict. At the PI's explicit request it is still
registered through `bin/exp` as a `lab-diagnostic`, with a prediction, falsifier,
and gates frozen before any result is computed. It is not a protocol revision,
not a confirmatory headline cell, and not a basis for changing an atlas verdict.

## Tier and shape decision

Shape A is warranted. Both required substrates already have full-depth,
final-prompt-token captures and private local row materializations. The threat is
associational and can be tested directly by asking how much of each layer's
hidden-state matrix is predictable from a frozen surface feature matrix, then
recomputing the pinned atlas estimator on cross-fitted residuals. A KUQ-only
matched sensitivity separately holds dataset origin fixed. These two analyses
attack different weaknesses of either one alone: residualization can adjust a
wide feature set on the whole fit pool, while matching gives a formula-preserving
sensitivity whose retained rows have demonstrably low role predictability from
surface features.

Shape B, a newly captured surface-matched pool, is not authorized here. It is the
pre-stated escalation only if overlap, balance, or planted-signal reachability
fails. Such an escalation requires a separate amendment, explicit PI approval,
and a new GPU launch decision.

## Design

### Substrates and existing inputs

The primary substrate is `google/gemma-4-E4B-it` at revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`, using the resolved
`gemma-4-e4b-family-atlas` capture: 2,815 rows, 43 hidden states, hidden size
2,560. The independent replication is `unsloth/Qwen3-4B` at revision
`64033659d5caf1b8ed7f929b29de705e93a4d468`, using the resolved
`qwen3-4b-family-atlas` capture: 1,768 rows, 37 hidden states, hidden size
2,560. Those counts and pins come from each atlas cell's governed Amendment
Outcome and committed capture manifest.

No model is loaded and no capture is run. `cell.yaml` names logical committed
sources and expected dimensions. The harness resolves the two source atlas roots
from `GEMMA4_E4B_ATLAS_ROOT` and `QWEN3_4B_ATLAS_ROOT`, and the private local row
materializations from `GEMMA4_E4B_SURFACE_ROWS` and
`QWEN3_4B_SURFACE_ROWS`. It refuses a missing or dimension-mismatched source.
All commands expected to exceed 15 minutes must run through
`experiments/common/launch_detached.sh`; no direct long-running invocation is
authorized.

### Population and pinned estimator

The full-pool analysis uses exactly the source atlas fit population: rows whose
source split is `fit` or `fit_only`. At every hidden-state index the harness
imports `eff_dim_frac` directly from the source atlas's pinned
`profile_and_read_family_atlas_panel.py`. Before any controlled result is
computed, it reproduces every committed baseline layer to maximum absolute
deviation at most `1e-6`. A mismatch stops the run.

Depth is classified from hidden-state index as
`hs_index / (n_hidden_states - 1)`. A peak at depth at most `0.20` is
early-exterior. This fixed boundary applies to baseline, controls, planted
validation, permutations, and subsamples. Peak margin is reported but never
decides the result.

### Frozen surface covariates

The surface matrix `Z` is constructed without role labels and without any model
behavior or completion field. Its low-dimensional block contains:

- rendered-prompt token count, read only as the length of the private capture
  input's `token_ids` and immediately reduced to a scalar;
- question character, whitespace-word, and line counts;
- digit, punctuation, newline, and uppercase counts and fractions;
- render/template identifier;
- dataset-of-origin and category dummy variables, with origin deterministically
  inferred from the row key only when the private row lacks an explicit source.

Each source atlas used one fixed renderer/template for all rows, so the
render/template identifier is an audited substrate-constant rather than a
row-varying adjustment. Row-varying formatting is represented by prompt token
count and question character, line, punctuation, case, word, and character
n-gram features. This control therefore tests the registered linear
question-surface model plus prompt length; it does not claim to exclude every
nonlinear encoding of rendered token sequence structure.

Its lexical block contains deterministic text-only hashed word 1-2gram and
character 3-5gram TF-IDF features, reduced separately by seeded truncated SVD
and standardized. `cell.yaml` pins hashing dimensions, SVD ranks, seeds, and all
ridge alphas. The text-only lexical block uses question text, never reference
answers or model output.

The prompt-only feature basis, including TF-IDF weighting, truncated SVD,
scalar scaling, and category expansion, is fit once on the fixed prompt
population without role labels or activations. This preprocessing is
transductive. The inferential protection is on the surface-to-activation map:
every mapping from `Z` to `H`, and every ridge-alpha choice, is activation-out-
of-fold. The design does not claim that unsupervised prompt preprocessing is
fold-local.

The following are excluded from `Z` by construction: role labels, completion or
model-output length, answer correctness, reference-answer or alias lengths,
answer and alias text, baseline behavior fields, generated text, and any
post-capture outcome. No completion existed at the final-prompt-token anchor in
the source capture instrument.

Question text, answer or alias text, token IDs, row-level surface matrices, and
row-level activations remain under gitignored `analysis/`. They are never
written to `analysis-committed/`. The harness permits only a fixed aggregate
JSON schema for later deliberate promotion and rejects output containing a
prohibited field name or any private question string.

### Primary full-pool control

For each substrate and hidden-state index, a deterministic five-fold outer
split predicts the multioutput activation matrix `H` from `Z` by ridge
regression. For each outer training fold, the ridge alpha is selected from the
fixed grid in `cell.yaml` using three-fold inner cross-validation on activation
mean squared error. Neither the outer test activations nor role labels enter
alpha selection. Source by role labels stratify fold membership only to preserve
partition balance; neither field enters `Z` or the ridge mapping. The residual
matrix is `H - H_hat`, with every activation row predicted out of fold. The
pinned atlas estimator is then applied to the residual.

Four profiles are reported: low-dimensional-only residual, lexical-only
residual, combined-`Z` residual, and the surface-explained `H_hat` profile. The
combined-`Z` residual is the sole primary full-pool control. The other profiles
diagnose which surface block carries an effect and cannot rescue a failed
primary result.

### KUQ-only matched sensitivity

The sensitivity population contains only explicitly recognized KUQ rows with
roles `confab` and `unknown_refused`. A deterministic logistic surface-only
propensity model uses the frozen combined `Z`; Hungarian minimum-distance
assignment performs 1:1 matching without replacement on propensity logit
distance separately inside each source block. Cross-source assignment is
forbidden and checked after matching. Role is used only to define the two sides
of the match and to balance classifier folds; it is never a covariate.

The match is viable only with at least 100 pairs per substrate, maximum absolute
standardized mean difference at most `0.10` across every scalar surface
covariate, and deterministic five-fold held-out surface-only role-classifier
best-orientation AUROC at most `0.60` on matched rows. Classifier folds group
intact pairs so counterparts never cross the train/test boundary. Failure of any
condition is an overlap failure, not evidence for or against the geometric
prediction. The run stops as indeterminate and prescribes Shape B.

On a viable match, the unweighted pinned `eff_dim_frac` estimator is computed on
the matched rows at every layer as a descriptive estimator-preserving profile.
The primary matched endpoint is the combined-residual profile on those same
matched rows. The raw matched profile cannot by itself pass or falsify the
prediction. Matching weights, pair IDs, text, and row keys remain private under
`analysis/`; only counts, balance maxima, AUROC, profiles, and peak summaries may
be promoted.

### Surface treatment-strength requirement

An unchanged residual peak is informative only when the registered surface
model predicts a nontrivial amount of activation variance. For each substrate,
compute activation-out-of-fold combined-`Z` R2 at every layer. Across the
non-embedding early-exterior indices from hs1 through
`floor(0.20 * (n_hidden_states - 1))`, the observed maximum must be at least
`0.01` and at least `0.005` above the 95th percentile of the corresponding
maximum-R2 values from the 20 within-source by role `Z` permutations. Failure is
indeterminate and escalates to Shape B. A pass licenses only the statement that
peak location survived this registered linear surface model with measured
treatment strength; it does not exclude every nonlinear surface encoding.

### Planted-signal positive control

At predeclared hidden-state index `hs2`, construct a deterministic standardized
surface component `S = ZR`, where `R` is a fixed seeded Gaussian projection into
hidden-state width. Scale `S` to the centered target-layer activation RMS, then
try `alpha` in `[0.25, 0.5, 1, 2, 4, 8]`. Choose the smallest alpha for which
hs2 is the unique raw-profile peak and its value is at least `1.05` times the
runner-up. This selection tests reachability only and is frozen to hs2 and the
listed grid.

Apply the exact combined-`Z` cross-fitted control to the planted tensor. The
planted and unplanted hs2 fits use the identical registered outer and inner
partitions and alpha-selection seed (`seed + hs2`); only `H` differs. The
positive control passes only if hs2 is no longer the controlled peak and the
controlled planted profile differs from the controlled unplanted profile by at
most `0.05` after layerwise normalization by the unplanted controlled value. If
the grid cannot plant the registered peak, or the control cannot remove it, the
surface control is structurally unvalidated and the experiment stops as
indeterminate.

### Permutation and subsample controls

For 20 fixed seeds, permute rows of `Z` within dataset-origin by role strata,
breaking row-level surface-to-activation alignment while preserving gross pool
composition. Re-run the combined residualization. At least 18 of 20 permuted
profiles must retain an early-exterior peak, and the median absolute peak shift
from the unpermuted baseline must be at most one hidden-state index. This is a
negative control against generic variance removal manufacturing a relocation.

Finally, take a fixed-seed 50% stratified subsample of the full-pool combined
residual and a fixed-seed 50% sample of intact matched pairs from the matched
combined residual. Never sample the two match sides independently. Recheck the
registered scalar-balance and held-out surface-role AUROC thresholds on the
retained pairs; a failed subsample support check is indeterminate. Each valid
subsample peak must remain early-exterior. The seed, strata, retained counts,
balance diagnostics, peak locations, and profiles are aggregate outputs.

The analysis harness checkpoints completed substrate, layer, fold, alpha, and
permutation units under this experiment's gitignored `analysis/`. Restart must
verify a configuration fingerprint before reusing a checkpoint.

## Prediction

For both Gemma-4-E4B-it and Qwen3-4B, the `eff_dim_frac` peak remains early-exterior at depth at most 0.20 in both the full-fit-pool combined-surface residual profile and the viable KUQ-only matched combined-residual profile, including the fixed-seed 50% full-row and intact-matched-pair subsamples.

## Falsifier

After G0-G4 pass, any valid primary controlled profile or registered subsample on either substrate whose peak moves beyond depth 0.20 falsifies the surface-robustness prediction and blocks finalizing paper 4 section 6.x with the current geometric interpretation.

## Gates

- **G0 provenance, containment, and coverage:** model revision, capture manifest,
  hidden-state count, hidden width, row count, split roles, and capture coverage
  match `cell.yaml`; private inputs remain local; all writes resolve beneath this
  experiment's `analysis/`; aggregate output passes the prohibited-key and
  private-text scan.
- **G1 exact baseline reproduction:** imported pinned estimator reproduces every
  committed atlas layer with maximum absolute deviation `<= 1e-6`. Failure is
  indeterminate and stops all controlled analysis.
- **G2 surface sensor and matching support:** frozen covariate construction
  completes with no excluded field; each exact-within-source KUQ match has
  `>= 100` pairs, maximum scalar `|SMD| <= 0.10`, and held-out surface-only role
  best-orientation AUROC `<= 0.60`. In addition, the observed maximum combined-`Z` activation-
  out-of-fold R2 over non-embedding early-exterior layers is `>= 0.01` and
  exceeds the 95th percentile of the 20 permutation maxima by `>= 0.005`.
  Failure is indeterminate and triggers the Shape B recommendation.
- **G3 planted reachability:** the smallest successful alpha from the fixed grid
  makes hs2 a unique raw peak at least `1.05` times the runner-up; exact combined
  residualization removes hs2 as the peak; maximum normalized controlled-profile
  deviation from unplanted is `<= 0.05`. Failure is indeterminate.
- **G4 permutation negative control:** at least 18 of 20 within-origin by role
  permutations remain early-exterior and median absolute peak shift is `<= 1`
  hidden-state index. Failure is indeterminate.
- **G5 location decision:** only after G0-G4 pass, both substrates' full-pool
  combined-residual and KUQ matched combined-residual primary profiles peak at
  depth `<= 0.20`, and the fixed-seed full-row and intact-pair 50% subsamples
  pass support rechecks and peak at depth `<= 0.20`. The raw matched unweighted
  profile is descriptive only.
  If all hold, the registered surface-robustness prediction passes. Any valid
  controlled peak beyond `0.20` falsifies it. A gate or integrity failure is
  indeterminate, never a pass or falsification.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Early-exterior location survives all valid primary controls on both substrates. |
| user | |

## Outcome

The signed CPU analysis completed with exit code 0. G0 and G1 passed on both
substrates. G2 matching support failed on both substrates: Gemma retained 293
pairs but had best-orientation surface-role AUROC 0.643 and maximum scalar SMD
0.154; Qwen retained 108 pairs but had AUROC 0.610 and maximum scalar SMD 0.174.
The registered thresholds were AUROC at most 0.60 and maximum scalar SMD at most
0.10. The hard stop therefore fired before G3-G5, and no controlled peak profile
was computed. The aggregate instrument status is `indeterminate` with the
pre-stated Shape B escalation. PI verdict adjudication remains pending.

Aggregate artifact:
`analysis-committed/aggregate_results.json`, sha256
`df21b826a041c015657832468bf922f119398f483b7dc528b5a27526d742ebb5`.
This experiment authorizes no GPU work. Any later fresh capture or
surface-matched pool requires separate PI approval and a separately governed
Shape B design.
