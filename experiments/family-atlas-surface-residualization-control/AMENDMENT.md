# Family Atlas Surface Residualization Control

Status: resolved 2026-07-23. The registered linear prompt-surface
residualization control passed on both substrates; machine state and instrument
hashes are in `experiment.yaml`.

The machine state lives in `experiment.yaml`. This document pre-states the
design and decision rules before any controlled profile is computed.

## Instrument tier and posture

This is Tier 3 analysis-only work under
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`. It loads no
model, introduces no new capture or atlas arm, and re-reads existing private
captures without changing their registered estimators or verdicts. It is
nevertheless scaffolded with `bin/exp` as a registered `lab-diagnostic` because
it is the final paper-facing robustness gate for paper 4 section 6.x. It remains
exploratory evidence and is not pooled with a headline matrix.

No GPU work is authorized or needed. The real CPU analysis remains blocked
until the PI signs this draft and separately approves the run.

## Motivation

The family-atlas program reports an early-exterior peak in representation-
variance effective dimensionality before the later interior band where the
known-unknown (answerability), caution, and raw-refusal contrasts are jointly
readable. Paper 4 section 6.x explicitly withholds finalization while a surface-
diversity account remains open. Prompt length, lexical overlap, source,
category, and formatting may create the early peak without the peak carrying an
epistemic interpretation.

Two prior controls ended without a peak-location result. The resolved
`family-atlas-surface-diversity-control` retained 293 Gemma and 108 Qwen matched
pairs but failed its registered surface-balance gates on both substrates. The
resolved `family-atlas-surface-matched-json-completion-control` successfully
generated complete pools and validated a planted surface-role sensor, but its
fresh matched pools also failed the registered balance gates, so full-depth
capture did not run. These are prerequisite support failures, not evidence that
the early peak survives or moves.

This successor removes matching from the decision path. It uses every eligible
fit row in each existing atlas and directly subtracts the activation component
that a frozen prompt-surface representation predicts out of fold. This tests
Shape A with the data already captured. Shape B is not reopened here because
the two matching-based attempts established that strict surface balance is the
construction bottleneck, while residualization can address the registered
linear surface model on the full observed population.

## Question

Does the early-exterior family-atlas `eff_dim_frac` peak remain at depth at most
0.20 after cross-fitted removal of prompt-surface-predictable activation
variance in the existing Gemma-4-E4B-it and Qwen3-4B atlas fit populations?

## Design

### Existing substrates and population

The primary substrate is `google/gemma-4-E4B-it` at revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`: 2,815 captured rows, 1,301 fit
rows, 43 hidden states, and hidden width 2,560. The independent replication is
`unsloth/Qwen3-4B` at revision
`64033659d5caf1b8ed7f929b29de705e93a4d468`: 1,768 captured rows, 1,325 fit
rows, 37 hidden states, and hidden width 2,560. `cell.yaml` pins each source
manifest, capture index, capture input, estimator module, private row
materialization, and activation-content digest.

The population is exactly the source atlas rows labeled `fit` or `fit_only`
with roles `confab`, `known_correct_answered`, or `unknown_refused`. No row is
discarded for surface overlap. Source by role is used only to balance folds and
subsamples. Role never enters the surface feature matrix or regression.

At each hidden-state index, the harness imports `eff_dim_frac` from the source
atlas's pinned `profile_and_read_family_atlas_panel.py`. It must reproduce every
committed baseline layer to maximum absolute deviation at most `1e-6` before
any controlled result is valid.

### Frozen prompt-surface representation

The low-dimensional block contains rendered-prompt token count; question
character, whitespace-word, and line counts; digit, punctuation, newline, and
uppercase counts and fractions; render/template identifier; dataset source;
and category. The lexical block contains deterministic hashed word 1-2gram and
character 3-5gram TF-IDF features, separately reduced to 32 seeded SVD
components and standardized. The combined block concatenates both.

The surface basis is fit once on the fixed atlas fit-prompt population without
roles or activations. This unsupervised preprocessing is transductive within
that registered population. Every mapping
from a surface block to activations, including ridge-alpha selection, is
activation-out-of-fold.

The following are prohibited inputs: role, completion or model-output length,
answer correctness, reference-answer or alias length, answer or alias text,
baseline behavior, generated text, and any post-capture outcome. The lexical
input is question text only. This design tests the registered linear surface
representation and does not claim to remove every nonlinear encoding of a raw
token sequence.

### Cross-fitted residual profiles

For every substrate and hidden-state index, a deterministic five-fold outer
split predicts the multioutput activation matrix `H` from surface matrix `Z`
with ridge regression. Within each outer training fold, three-fold inner
cross-validation selects alpha from `[0.01, 0.1, 1, 10, 100, 1000]` by
activation mean squared error. The controlled matrix is `H - H_hat`, where
every row of `H_hat` was predicted without that row's activation.

The primary profile applies the pinned `eff_dim_frac` estimator to the combined
block residual at every layer. A fixed-seed, source-by-role stratified 50%
subsample of those residual rows is the registered stability profile. The
baseline, low-dimensional residual, lexical residual, and surface-explained
profiles are descriptive and cannot rescue a failed primary endpoint.

Depth is `hs_index / (n_hidden_states - 1)`. A peak at depth at most `0.20` is
early-exterior. Peak margin is always descriptive. Peak location is the only
geometric decision variable.

### Treatment-strength and negative controls

An unchanged peak is interpretable only if the surface model removes a
measurable activation component. The maximum combined-block activation
out-of-fold R2 over non-embedding early-exterior layers must be at least `0.01`
and at least `0.005` above the 95th percentile of maxima from 20 fixed-seed
within-source-by-role permutations of `Z`.

Those same permutations are a negative control against generic variance
removal manufacturing a relocation. At least 18 of 20 permuted profiles must
remain early-exterior, and the median absolute shift from the baseline peak
must be at most one hidden-state index.

### Planted-signal positive control

At predeclared `hs2`, a seeded standardized surface component `S = ZR` is
projected to hidden width and scaled to the centered activation RMS. The
smallest alpha in `[0.25, 0.5, 1, 2, 4, 8]` that makes hs2 the unique raw peak
at least 1.05 times the runner-up is selected only for reachability.

The exact combined-block residualization is then applied with the same outer
and inner partitions used for the unplanted hs2 analysis. The positive control
passes only if hs2 is no longer the controlled peak and the controlled planted
profile differs from the controlled unplanted profile by at most 0.05 after
layerwise normalization. Failure means the control was structurally unable to
remove a surface-caused peak and makes the experiment indeterminate.

### Data exhaust and containment

The run retains enough private, row-aligned exhaust to support later questions
without repeating feature extraction or regression:

- an ID-indexed fit manifest with source row index, role, split, source, and
  category;
- low-dimensional, lexical, combined, and raw-scalar surface matrices;
- per-layer out-of-fold activation predictions for all three surface blocks;
- fold state, selected alphas, configuration fingerprint, and restart metadata;
- baseline, residual, surface-explained, permutation, treatment-strength,
  planted-control, and fixed-subsample profiles.

Later analysts can reconstruct any registered residual as source activation
minus retained out-of-fold prediction. Aggregate output records row counts,
matrix shapes, content digests, profiles, peaks, gates, and the reconstruction
rule. Question text, answer or alias text, generated text, token IDs, row-level
surface matrices, predictions, and activations remain under gitignored
`analysis/`. Nothing row-level may enter `analysis-committed/`. The harness
uses a positive aggregate schema, scans for prohibited private text, and
refuses writes outside this experiment's `analysis/` directory.

## Prediction

For both Gemma-4-E4B-it and Qwen3-4B, the `eff_dim_frac` peak remains early-exterior at depth at most 0.20 in both the full-fit combined-surface residual profile and its fixed-seed 50% stratified stability profile.

## Falsifier

After G0-G4 pass, any required combined-surface residual profile on either substrate whose peak lies beyond depth 0.20 falsifies the surface-robustness prediction and blocks finalizing paper 4 section 6.x with the current geometric interpretation.

## Gates

- **G0, provenance, coverage, containment, and exhaust:** every source pin,
  activation-content digest, row/layer/width count, and coverage value matches
  `cell.yaml`; all writes stay below gitignored `analysis/`; the aggregate
  passes its positive schema and private-text scan; the private exhaust is
  row-aligned and content-addressed.
- **G1, exact baseline reproduction:** every source-atlas `eff_dim_frac` value
  is reproduced with maximum absolute deviation `<= 1e-6`. Failure stops the
  analysis as indeterminate.
- **G2, treatment strength:** for each substrate, early-layer maximum observed
  activation OOF R2 is `>= 0.01` and exceeds the 20-permutation 95th percentile
  by `>= 0.005`. Failure is indeterminate, never a pass or falsification.
- **G3, planted reachability:** the fixed hs2 plant reaches the registered raw
  peak criterion, residualization moves the controlled peak away from hs2, and
  maximum normalized deviation from the unplanted controlled profile is
  `<= 0.05`. Failure is indeterminate.
- **G4, permutation negative control:** at least 18 of 20 permuted combined
  residual profiles remain early-exterior and median absolute peak shift is
  `<= 1` hidden-state index. Failure is indeterminate.
- **G5, peak location:** only after G0-G4 pass, both substrates' full-fit
  combined residual and fixed-seed 50% stability profiles must peak at depth
  `<= 0.20`. All four valid profiles early is a pass. Any one beyond `0.20` is
  the pre-stated falsifier. Peak margins and descriptive profiles do not decide.

## Predictions scoreboard

| Predictor | Call |
|---|---|
| orchestrator | Both substrates retain an early-exterior peak in both required residual profiles. |
| Joseph Rosenbaum | Both substrates retain an early-exterior peak in both required residual profiles. |

## Run boundary

Before signing, only schema validation, source preflight, static tests, and the
synthetic planted-signal check are allowed. Preflight may verify private source
metadata and checksums but may not load activation tensors or compute a profile.
The real CPU run requires a separate PI approval after signing. Processes
expected to exceed 15 minutes must use
`experiments/common/launch_detached.sh` with an exit-code watch.

## Outcome

**RESOLVED, SURFACE-ROBUSTNESS PREDICTION PASSED.** The CPU-only run exited
zero and wrote the positive-schema aggregate at
`analysis-committed/aggregate_results.json` with SHA-256
`dbc496ba8a5fb905fabd7a73a4f76252e2ce98e8b72ab5c9ea5b1a3e006bfede`.
No model was loaded and no GPU was used. The retained private matrices,
row-aligned out-of-fold predictions, fold state, and checkpoints remain under
gitignored `analysis/` for later reanalysis.

All registered gates G0-G5 passed for both substrates. G0 verified provenance,
coverage, containment, and the private data exhaust. G1 reproduced the source
profiles within the registered `1e-6` tolerance. The baseline and full-fit
combined-residual peaks were unchanged in location:

| Substrate | Baseline peak | Full residual peak | 50% stability peak |
|---|---:|---:|---:|
| Gemma-4-E4B-it | hs4, depth 0.095 | hs4, depth 0.095 | hs4, depth 0.095 (n=650) |
| Qwen3-4B | hs5, depth 0.139 | hs5, depth 0.139 | hs5, depth 0.139 (n=660) |

G2 established treatment strength rather than a vacuous unchanged profile.
Gemma's maximum early combined-surface activation OOF R2 was 0.6722 against a
20-permutation p95 of 0.2039, an excess of 0.4682. Qwen's was 0.4468 against
0.0418, an excess of 0.4050. G3 also passed: the planted surface component
moved the raw peak to hs2 for both substrates, then residualization restored
the controlled peak to hs4 for Gemma and hs5 for Qwen. Maximum normalized
deviation from the corresponding unplanted controlled profile was 0.0081 and
0.0071, both below the registered 0.05 ceiling.

G4 passed with all 20 of 20 permuted profiles early-exterior for each
substrate and median absolute peak shift 0. G5 therefore decides the result:
all four required controlled profiles remained at depth at most 0.20. The
pre-stated falsifier did not fire.

This rejects the registered linear prompt-surface account as an explanation
for the early-peak location on these Gemma and Qwen populations. It does not
exclude every nonlinear encoding of the raw token sequence, and the result
must not be generalized beyond that stated scope. Within that scope, the final
surface-diversity gate for paper 4 section 6.x is satisfied.

Prediction scoring: Joseph Rosenbaum **WIN** and orchestrator **WIN**. Both
pre-registered the same call that Gemma and Qwen would retain early-exterior
peaks in the full residual and 50% stability profiles, and all four required
profiles did so.
