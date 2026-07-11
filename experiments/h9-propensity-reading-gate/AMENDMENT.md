# H9 held-out reading gate for the confab-propensity direction on AI-TRUE

Status: draft (not signed; do not launch as confirmatory evidence). Gates in
section 5 LOCK at signing. The Modal launch in section 6 needs separate explicit
user approval on top of signing; signing this document does not authorize the
GPU spend.

Machine state lives in `experiment.yaml`; it is never duplicated here.

## 1. Motivation and posture

Paper 5 makes a two-part claim about the confabulation-propensity direction on
the AI-TRUE checkpoint: the direction READS (it separates confabulations from
honest refusals as an activation readout) but does NOT ACTUATE (subtracting it
at generation time does not convert confabs into refusals). The actuation half
is governed: Amendment AL resolved it as a use-the-signal null, AL-G2 MISS and
AL-G3 MISS, with a causal readback showing the internal projection moved by the
commanded amount while behavior did not
(`experiments/radial-anti-propensity-steering/AMENDMENT.md:40-51`). The reading
half is NOT yet governed by a registered number. The only separation figure that
exists is an in-sample one: the 5-fold out-of-fold AUROC
`prop_incell_oof_auroc: 0.6802` recorded in AL's own selection manifest
(`experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/selection_manifest.json`,
readout_quality block; construction at
`archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py:156-161`).
That number is cross-validated WITHIN the 1,662-row fit population; the frozen
direction `d_raw` was fit on all 1,662 rows with no split reserved
(`experiments/radial-anti-propensity-steering/AMENDMENT.md:124-132`). A feasibility
inventory confirmed no held-out AI-TRUE extraction exists anywhere on disk, so a
genuine held-out reading number cannot be recovered from cache and requires a new
extraction pass (`docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md:11-23,172-201`).

This experiment supplies the missing registered number. It freezes a portable
scorer that replicates AL's fit pipeline, draws a held-out row population the fit
never saw, extracts and grades those rows on the AI-TRUE checkpoint, and scores
the frozen direction on them. A pass certifies the reading claim on disjoint
rows; a fail kills it. Either way the number becomes citable, which the in-sample
0.6802 is not. This is exploratory evidence for a single checkpoint and a single
seed: a pass licenses a within-checkpoint reading claim, not a portability or
multi-seed headline (mirrors AL's own caveat,
`experiments/radial-anti-propensity-steering/AMENDMENT.md:208-214`).

## 2. Substrate and checkpoint

The checkpoint is the AI-TRUE probe-as-reward GRPO model, identical to the one
AL's A0 surface was extracted on
(`docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md:104-112,204-207`):

- Base (clean-SFT merged, loaded in 4-bit): `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`
- Adapter (the TRUE GRPO LoRA): `scratch/schema_response_confidence/runs/amendment_ai_grpo_true_seed1/20260703_234933/final_model`

Both are local paths, present in the canonical checkout, not on any hub. The
Modal lane in section 6 must therefore SHIP the checkpoint (section 6.2); this is
the one structural difference from the j-lens and doubt-snap Modal harnesses,
both of which pull their model from a hub repo.

The prompt surface is the baseline schema-contract system prompt AL used
(`answer` + `response_confidence` keys), recorded verbatim in
`experiment/phase1/probe/analysis/amendment_al_prep/true_a0/gen/data/manifest.json`,
applied unchanged to the new held-out questions. Extraction is the
pre-generation anchor (`prompt_len-1`), all 37 layers captured per row, of which
only L24 (propensity) and L35 (caution) are consumed
(`docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md:88-101`;
fit layers verified at
`archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py:81-82`).

## 3. The frozen scorer (CPU, no GPU)

AL never persisted its fit objects; the generating script refits PCA, the scaler,
the caution regression, and the mean-diff direction in memory each run and saves
only derived arrays (`d_raw.npy`, `prop_z.npy`, `caution_z.npy`) plus the manifest
(`docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md:57-82`). Step 1
re-derives that pipeline from the pinned generating script and the on-disk fit
extraction, then freezes every object needed to score a genuinely new row:

1. `pca24` (PCA 128, randomized, `random_state=20260705`) and `scaler24`
   (StandardScaler) fit on the 1,662-row L24 matrix.
2. A caution classifier for eval-time residualization. AL's `c` is a 5-fold
   out-of-fold logistic decision function
   (`amendment_al_select_and_direction.py:96-106`), which is a within-training
   construct and cannot be applied to a single new row. Step 1 fits one FINAL
   full-sample caution logistic on PCA-128(L35) over all 1,662 rows and freezes
   it; held-out caution values come from this frozen classifier.
3. The caution-residualization `LinearRegression` (each PCA-24 column regressed
   on the caution score), the full-sample mean-diff direction `d_confab_full`,
   and the z-scale mean/std of the propensity projection on the fit population.

The frozen scorer maps a new row's raw L24/L35 to a propensity z-score:
PCA-128 -> standardize -> caution-residualize (frozen caution + frozen
regression) -> project onto `d_confab_full` -> z-scale by the frozen fit-population
mean/std. All objects and a SHA-256 manifest of them are persisted to the
experiment's gitignored `directions/` tree.

### 3.1 Scorer-fidelity gate (pre-stated tolerances)

Two checks assert the re-derivation matches AL's frozen construction. See the
spec-conflict note in section 8 on why the hard target is `d_raw.npy`, not
`prop_z.npy`.

- FID-1 (hard, exact-replication): the re-derived full-sample raw-space direction
  reproduces the on-disk `d_raw.npy`
  (`.../amendment_al_run/d_raw.npy`) at cosine >= 1 - 1e-6 AND maximum absolute
  elementwise difference <= 1e-5. This is the identical deterministic full-sample
  computation from the pinned script
  (`amendment_al_select_and_direction.py:197-204`), same seed, same 1,662-row
  matrix; a larger deviation means the re-derivation diverged from the governed
  fit and the scorer is not AL's scorer.
- FID-2 (consistency, frozen vs OOF readout): the frozen full-sample propensity
  z-score on the 1,662 fit rows correlates with the on-disk OOF `prop_z.npy` at
  Pearson r >= 0.98, AND the frozen scorer's in-cell AUROC (contrast defined in
  section 4.1) lands within 0.02 of AL's OOF 0.6802. Justification: AL states
  full-sample refits of these cells shift AUROC well under 0.01
  (`experiments/radial-anti-propensity-steering/AMENDMENT.md:129-132`); a 0.02
  band gives margin while still catching a genuine pipeline mismatch.

If either fidelity check fails, the held-out gate is not run: a scorer that does
not reproduce AL's construction cannot certify AL's direction.

## 4. Held-out draw

The candidate population is the complement of AL's fit surface inside the 18,496
-row AH union pool: 16,834 rows recoverable by set arithmetic on two on-disk
JSONL files, with zero exact-text collisions against the fit surface and full
question, answerability, and source coverage
(`docs/review/h9-holdout-candidate-inventory-2026-07-10.md:12-25,64-94,153-172`).

- Draw size: 500 rows, fixed seed (recorded in `cell.yaml`).
- Stratification: match the fit surface's per-source proportions. Target counts
  (fit-surface share of 1,662, applied to 500, largest-remainder rounded):
  kuq_ku_unknown_x 226, kuq_ku_unknown 137, selfaware_unanswerable 40,
  selfaware_answerable 35, triviaqa 24, popqa 23, kuq_ku_known 15. Every target
  is far below the complement's per-source supply
  (`docs/review/h9-holdout-candidate-inventory-2026-07-10.md:85-94`), so the
  stratified draw is feasible without replacement.
- Output: an ID-manifest of the 500 `row_key` values plus their source and gold
  answerability label, committed under `analysis-committed/`. No question text,
  aliases, or generations are ever committed (containment, section 8).

The reading contrast (section 4.1) lives inside the unanswerable rows of the
draw. The three unanswerable sources contribute 226 + 137 + 40 = 403 rows; at the
fit surface's confab-among-unanswerable rate (116 confab / 1,338 unanswerable
= 8.7%, `experiments/radial-anti-propensity-steering/AMENDMENT.md:116-120`), the
expected yield is about 35 graded confabulations. That drives the AUROC's power
and motivates the evaluability floor in section 5.

### 4.1 The scored contrast

The propensity AUROC uses AL's exact readout_quality contrast
(`amendment_al_select_and_direction.py:149-158`): positives are confabulations
(gold_class unanswerable AND answered), negatives are honest unanswerable
refusals (gold_class unanswerable AND refused). Answerable rows and degenerate
rows do not enter the propensity contrast. Behavior labels come from generating
each held-out question on the AI-TRUE checkpoint and grading it with the
byte-identical AL A0 grader (section 6.1).

## 5. Gates (LOCK at signing)

The honest prior is the in-cell 5-fold OOF AUROC 0.6802. Its excess over chance
is 0.1802. The pass and fail lines below anchor to fractions of that excess so
they are derived from AL's own number, not rounded to a convenient default.

- H9-G1 (reading, PASS): held-out propensity AUROC (contrast in 4.1) >= 0.62 AND
  the lower bound of its 1,000-resample row-bootstrap 95% CI > 0.55. Rationale:
  0.62 is chance plus about two-thirds of the in-cell excess, so a pass means the
  direction keeps most of its separation on rows it never saw, with a CI that
  clears chance by a margin.
- H9-G1 (reading, FALSIFIER/FAIL): held-out propensity AUROC <= 0.55 OR the upper
  bound of its bootstrap 95% CI < 0.60. Rationale: 0.55 is chance plus about a
  quarter of the in-cell excess; at or below it the reading has not generalized
  and the "the direction reads" claim for paper 5 is not supported on held-out
  data.
- H9-G1 INCONCLUSIVE band: a point estimate strictly between 0.55 and 0.62, or a
  CI that straddles the boundaries, is reported as inconclusive: separation is
  present but too weak or too uncertain to certify or kill. No goalpost moves; an
  inconclusive result is reported as such.
- H9-G2 (caution positive control, FLOOR): held-out caution AUROC (refused vs not,
  over all graded held-out rows, using the frozen full-sample caution classifier)
  >= 0.90. Rationale: the in-cell OOF caution AUROC is 0.9561
  (`selection_manifest.json` readout_quality); caution is the strong signal and
  should transfer nearly intact. This control certifies the extraction, grading,
  and scoring pipeline is healthy, so a weak propensity read can be trusted as a
  genuine null rather than a broken pipeline. If G2 falls below 0.90, the whole
  held-out draw is treated as a pipeline failure and G1 is not adjudicated.
- H9-G0 (evaluability precondition): the graded held-out draw must yield at least
  20 confabulations and at least 20 honest unanswerable refusals. Below either
  count the propensity AUROC is underpowered; the result is inconclusive-by-power
  and the draw is enlarged (a pre-stated remedy, not a goalpost move). This
  precondition is checked before G1 is read.

## 6. Modal lane (GPU; separate launch approval required)

The GPU step extracts pre-generation L24/L35 states and generates plus grades the
500 held-out rows on the AI-TRUE checkpoint. Its process shape ports the detached
-app, Volume-checkpoint, DONE-marker, launch-guard pattern from
`experiments/j-space-localization-qwen3-4b/cloud/modal_jlens.py` and the repo-clone
plus pinned-commit shape from
`experiments/doubt-snap-cross-family-confirmatory/cloud/modal_doubt_snap_cross_family.py`.

### 6.1 Steps inside the container

1. Clone the repo at the pinned signed commit; no submodule needed (the harness
   is plain transformers extraction plus generation, not a tuner cell).
2. Pull the AI-TRUE base and adapter from the private staging repo (section 6.2).
3. Extract pre-generation anchor states (all 37 layers, `prompt_len-1`,
   batch_size 1, forward-only) for the 500 rows.
4. Generate greedily (max_new_tokens 96, matching AL's A0 generation config) and
   grade with the byte-identical AL A0 grader.
5. Write per-row `.safetensors` extraction, `rows_graded.jsonl`, and an extraction
   manifest to the Modal Volume. No external upload of outputs; results are pulled
   with `modal volume get`.

### 6.2 Shipping the local checkpoint

Neither exemplar ships a local checkpoint. The design: one-time upload of the
AI-TRUE base (merged-16bit, roughly 8 GB) and adapter (264 MB) to a private HF
staging repo (`professorsynapse/eh-h9-aitrue-staging`, mirroring the private
`eh-al-prep-staging` pattern j-lens uses for its pool,
`experiments/j-space-localization-qwen3-4b/cloud/modal_jlens.py:14-33`). The
container fetches both with `hf_hub_download` under a scoped HF_TOKEN secret.
Model weights are not dataset or question text, so staging them is not a
containment violation. The upload is a manual pre-launch step by the user, noted
in section 7; it is not performed by this draft.

### 6.3 GPU and cost estimate

- GPU: A10G (24 GB), the proven choice for a 4B model at this budget in both
  exemplars (`modal_jlens.py:152-153`, `modal_doubt_snap_cross_family.py:21`).
- Compute scaling from the feasibility memo's measured 3090 rates
  (`docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md:225-237`):
  extraction 0.099 s/row, generation 1.685 s/row, so 500 rows is about 50 s
  extraction plus about 14 min generation, roughly 15 GPU-min of active compute
  on a 3090. An A10G is in the same class and typically somewhat slower for this
  4B forward and generate shape; budget about 20 to 30 GPU-min of active compute
  plus 5 to 10 min to pull and load the roughly 8 GB checkpoint. Wall time about
  30 to 40 min.
- Cost: at roughly $1.10 to $1.50/hr for an A10G, active plus load time of about
  0.5 to 0.7 hr is about $0.75 to $1.05. Pre-registered cost cap
  `MODAL_COST_CAP_USD=15`, generous headroom for cold start, the checkpoint pull,
  and up to two Modal retries. Expected spend $1 to $2.
- Launch guard (refuses to spawn unless all set, mirroring the exemplars):
  `EHR_LAUNCH_OK=h9-propensity-reading-gate`, `MODAL_COST_CAP_USD=15`,
  `EHR_REPO_COMMIT=<signed commit sha>`, plus `HF_TOKEN` for the staging pull.
  This draft does not run `modal run`; the launch is reserved for the lead after
  the user approves the spend.

## 7. Preconditions and approvals

1. User sign-off on this document, with a recorded user prediction (dual-prediction
   practice; the orchestrator prediction is in section 9, the user slot is left
   empty for signing).
2. Scorer-fidelity gate (section 3.1) PASSES on CPU before any GPU work. FID
   failure blocks the launch.
3. Held-out ID-manifest drawn and committed (section 4) before launch, so the
   scored population is fixed in advance.
4. One-time upload of the AI-TRUE base and adapter to the private staging repo
   (section 6.2), by the user.
5. Explicit user approval of the Modal spend, relayed to the lead, on top of
   signing. Signing does not authorize the GPU launch.
6. Grader byte-identical to the AL A0 cell; grading config pinned.

## 8. Interpretive caveats and spec-conflict notes (pre-stated)

- Single checkpoint, single seed. A pass licenses a within-checkpoint reading
  claim only; portability (the direction refits per checkpoint, reference axes
  transferred at cosine 0.17,
  `experiments/radial-anti-propensity-steering/AMENDMENT.md:212-214`) and
  multi-seed replication are separate questions and are not claimed here.
- FIDELITY-TARGET conflict (flagged, not silently resolved): the task framing asks
  the frozen scorer to reproduce AL's `prop_z.npy` to numerical tolerance.
  `prop_z.npy` is the z-scored OUT-OF-FOLD mean-diff projection
  (`amendment_al_select_and_direction.py:153-154,313`); a frozen scorer that can
  score a single new row must be a FULL-SAMPLE fit, which by construction does not
  reproduce the OOF array bit-for-bit. The object that IS exactly reproducible
  from the full-sample fit is `d_raw.npy` (the frozen steering direction,
  `amendment_al_select_and_direction.py:197-204,312`). This design therefore makes
  `d_raw.npy` the hard fidelity target (FID-1) and treats `prop_z.npy` as a
  high-correlation consistency check (FID-2). The signer should confirm this
  reading of the fidelity requirement.
- CAUTION-SCORE train/serve mismatch: the residualization at fit time used the OOF
  caution score, while held-out rows are residualized with the frozen full-sample
  caution score. The two caution scores are near-identical in rank (in-cell OOF
  AUROC 0.9561), so the residualization is stable, but this is a real deviation
  from AL's exact in-memory construction. The registered sensitivity check
  (section 8.1) does not cover this; it is bounded instead by FID-2, which
  requires the frozen full-sample readout to track the OOF readout at r >= 0.98.
- Confab yield is modest (about 35 expected). The evaluability precondition
  H9-G0 and the bootstrap CI in G1 carry this uncertainty explicitly rather than
  hiding it.

### 8.1 Registered sensitivity check

One sensitivity check is pre-registered: paraphrase-level near-duplicates between
the two KUQ mining passes (`kuq_ku_unknown` and `kuq_ku_unknown_x`) were never
swept, only exact-text duplicates were ruled out
(`docs/review/h9-holdout-candidate-inventory-2026-07-10.md:189-196`). After the
draw, a cosine or token-overlap similarity sweep runs between the held-out KUQ
questions and the fit-surface KUQ questions; any held-out row above a pre-stated
similarity threshold (recorded in `cell.yaml`) is flagged, and the propensity
AUROC is recomputed with those rows excluded. If the gate verdict flips between
the full and the near-duplicate-excluded draw, the result is reported as
sensitive to near-duplicate contamination rather than as a clean pass or fail.
This is low severity (exact-text collisions are already zero) and is reported
alongside the headline AUROC, not pooled into it.

## 9. Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | H9-G1 PASS (~55%); H9-G2 floor PASS (~90%); H9-G0 met (~85%) |
| user | H9-G1 INCONCLUSIVE band (recorded 2026-07-10 at sign-off approval) |

Orchestrator basis: the in-cell OOF 0.6802 is a real but modest separation, and
held-out numbers on a disjoint draw usually degrade rather than improve, so the
point estimate most likely lands in the low-to-mid 0.6s, near the 0.62 pass line
rather than comfortably above it. That makes G1 close to a coin flip leaning
slightly toward pass, with a real chance of landing in the inconclusive band. The
caution floor (G2) is near-certain given the 0.9561 in-cell strength and its
demonstrated robustness. G0 is likely met but the modest confab yield leaves a
tail where the draw underpowers.

## 10. Outcome

Filled at resolve. Record the held-out propensity AUROC and its bootstrap CI, the
caution control AUROC, the confab and refusal counts, the fidelity-gate result,
the near-duplicate sensitivity result, and the one-sentence verdict that also
goes into `verdict:` in the manifest.
