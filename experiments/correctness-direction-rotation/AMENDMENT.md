# Correctness-direction rotation across training stages

Status: signed 2026-07-19 (exploratory Tier-2; instrument pins in experiment.yaml).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Does the correctness (dial) direction rotate across the four training stages
the way the answerability direction does: one near-orthogonal rotation at
instruction SFT, then stability through both GRPO stages? The
answerability-rotation diagnostic
(`experiments/diag-item9-caution-assembly-timeline/`, script
`diag_item9_caution_timeline.py`, committed table
`analysis-committed/diag_item9_caution_timeline.md`) tracked the
known-vs-unknown answerability direction across raw -> clean-SFT -> GRPO-v2 ->
GRPO-par-true in a shared PCA-128-on-raw basis and found readout strength flat
(raw CV AUROC ~0.951, peaks 0.956-0.959), one near-orthogonal rotation at SFT
(raw->cleansft cosine 0.05-0.27 at mid/late layers, e.g. L18 0.0505, L22
0.0857), then stability (cleansft->grpov2 >= 0.96; grpov2->partrue 0.69-0.94,
weakening only at the latest layers).

The dial's cross-checkpoint cold transfer is 0.679 (S-fit Instruct-base
direction applied cold to the deployed checkpoint,
`experiments/correctness-readout-deployment-port/AMENDMENT.md` section 7
secondary reading; paper 4 `manuscript.md` section 4.2). The manuscript
explicitly flags that the diagnostic tracked the ANSWERABILITY direction and
"the correctness direction's own rotation has not been tracked, so its
application to the dial's 0.679 cold transfer is an inference, not a
measurement." This cell converts that inference into a measurement.

Posture: exploratory Tier-2 probe-fit cell. Never pooled with the locked
Phase 1 matrix or the S/T headline readings. PI approved the cell 2026-07-18
(signature packet "Approved"); local RTX 3090 launches pre-approved the same
day for this arc.

## Design

### Stages and checkpoints

Four stages, checkpoints pinned identical to the answerability diagnostic
(open decision A3 resolved at staging: the harness-build assignment pins the
exact raw-base identity and GRPO-par-true timestamp that the diagnostic's
extraction commit d5a90b3b used, records both in NOTEBOOK.md, and asserts
them against the diagnostic's committed provenance before any generation):

- raw base (diagnostic's raw anchor, pinned at staging)
- clean-SFT merged-16bit
  (`scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/.../merged-16bit`)
- GRPO-v2 adapter
  (`scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`)
- GRPO-par-true adapter (timestamp pinned at staging per A3)

### The stated difference from the answerability diagnostic

The answerability diagnostic used forward-only extraction with a pool-derived
label IDENTICAL across all four stages (only activations changed). Correctness
is stage-dependent: each checkpoint must GENERATE answers (forced-best-guess
to defeat abstention, exactly as the T cell's section 3 protocol), which are
graded per stage (verbatim Cheng alias scorer), giving different answered
populations, different correct/wrong labels, and different post-gen answer
tokens per stage. Each stage's correctness direction is therefore fit on its
own data. This confound is accepted at sign as an interpretive limit
(PI-adjudicated 2026-07-18) and bounded by the pre-registered split-half
control below; the write-up carries the caveat explicitly.

### Method (mirrors diag_item9_caution_timeline.py)

1. Position: POST-GENERATION (last answer content token), the dial's native
   position and where 0.679 was measured. Pre-gen anchor is an optional
   secondary, reported descriptively if computed.
2. Shared basis: PCA-128 fit once per layer on the RAW stage's post-gen
   activations (label-agnostic), reused for every stage.
3. Per stage/layer: LogisticRegression(saga, tol=1e-3) on correct(1)/wrong(0)
   in PCA space; coef mapped back to 2560-dim residual space, unit-norm.
   SEED, PCA_DIM=128, N_FOLDS=5, MIN_CLASS=30 copied from the diagnostic for
   exact comparability; no stage silently dropped.
4. Report per layer L0..L36: 5-fold pooled OOF AUROC per stage; consecutive
   stage cosines (raw->cleansft, cleansft->grpov2, grpov2->partrue); each
   stage vs grpov2.
5. grpov2 stage reuses the T cell's existing post-gen tensors and labels
   (CPU-only, no regeneration):
   `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/`
   (2976 post-gen tensors, 988 correct / 500 wrong, verified on disk
   2026-07-18).
6. Pre-registered confound control: split-half stability of the grpov2
   correctness direction (fit on two random halves; report the split-half
   cosine as the within-stage noise floor). A rotation cosine counts as real
   rotation only if it sits well below this noise floor.
7. CPU-only direct bracket of the 0.679 transfer (PI-adjudicated in scope):
   the Instruct-base (S) -> grpov2 (T) correctness-direction cosine in a
   shared basis from the two existing on-disk extractions
   (`archive/.../amendment_s/stage2/`, 3672 tensors, 500/1336;
   `archive/.../amendment_t/stage2/`). Zero GPU. This matches the exact
   checkpoints of the 0.679 cold transfer (raw is not the Instruct base).

### Populations and generation

QA pool identical to S/T (datasets/popqa/test.jsonl +
datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl). Forced-best-guess
generation per stage for raw, clean-SFT, and GRPO-par-true; grading with the
verbatim Cheng alias scorer. The abstention-trained stages need a large
attempt budget (the T cell needed 8550 attempts for 500 wrong, ~82% refusal);
the harness sizes attempt budgets accordingly and reports yield per stage.

### Containment

Committed: aggregate per-layer AUROC and rotation-cosine tables (JSON + md,
exactly the diag_item9 committed shape, which carries no row text) and
per-stage ID-manifests under `analysis-committed/`. Per-row generations,
answers, labels, and hidden states stay gitignored under `analysis/`; hidden
states and RunLogs staged to the durable exhaust store
`/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/` before
any worktree teardown (A6 rule, mechinterp-cells skill). No dataset, question,
answer, or alias text and no token ids in any committed file. No OpenMOSS or
bridge data.

## Prediction

Orchestrator call (recorded pre-run, adopted from the adjudicated design
packet the PI approved 2026-07-18): correctness rotates at SFT but LESS
completely than answerability. Raw->cleansft correctness cosine lands in a
middle band ~0.3-0.6 at the dial's best layers (L19-L24), not answerability's
~0.06; both later transitions stay >= 0.85; the Instruct->grpov2 bracket
cosine is consistent with the partial (0.679, well above chance) cold
transfer. Both readings pre-stated so no result falls off the table:

- Rotation-confirmed reading: raw->cleansft cosine <= 0.50 (mean over
  L19-L24) AND both later transitions >= 0.85 AND the raw->cleansft cosine is
  below the split-half noise floor: the single-rotation-at-SFT account
  extends to correctness and explains the partial cold transfer.
- No-rotation reading: raw->cleansft cosine >= 0.80 at the dial's best
  layers: the rotation account does NOT transfer to correctness and the 0.679
  degradation needs another explanation (forced-answer distribution shift,
  gradual drift, or population/label shift).

## Falsifier

Raw->cleansft correctness cosine >= 0.80 averaged over the dial's best layers
(L19-L24): no orthogonal rotation at SFT, killing the "rotation explains the
dial's cold transfer" line; reported straight. Results between 0.50 and 0.80
land in the pre-stated middle ground: reported as "partial rotation,
mechanism unresolved," with neither reading adopted.

## Gates

Per-cell gates in `gates.yaml`.

- CD-G0 (data adequacy, pre-outcome stop, per stage): >= 150 correct AND
  >= 150 wrong answered rows (the S/T section 4 floor). A stage below floor
  is reported "rotation not measurable at this stage," a data-stage stop for
  that stage, never a probe verdict (the 27-wrong lesson, S section 1.2).
  Checkpoint identity assertions (A3 pins) must pass before any generation.
- CD-G1 (rotation-confirmed, primary): raw->cleansft cosine <= 0.50 (mean
  over L19-L24) AND cleansft->grpov2 >= 0.85 AND grpov2->partrue >= 0.85 AND
  raw->cleansft below the grpov2 split-half noise floor. Floors justified
  against the answerability numbers: 0.50 sits between answerability's SFT
  drop (0.05-0.27) and no-rotation (~1.0); 0.85 mirrors answerability's
  stable GRPO transitions (>= 0.96 and 0.69-0.94).
- CD-G2 (readout sanity, reported): per-stage OOF AUROC at the best layer
  must be materially above chance for a direction to enter any cosine
  comparison; a stage with best-layer AUROC < 0.60 is flagged and its
  cosines reported as unreliable.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Partial rotation: raw->cleansft cosine 0.3-0.6 at L19-L24 (below the split-half noise floor), later transitions >= 0.85, bracket cosine consistent with 0.679. (recorded pre-run) |
| user | Approved the cell (2026-07-18 signature packet) and pre-approved the local GPU launch without recording a separate quantitative call. |

Scoreboard adjudication (at resolve, 2026-07-20): the orchestrator call was
WRONG on both counts. Observed raw->cleansft 0.192 fell below the predicted
0.3-0.6 band, and the later transitions (0.449, 0.330) fell far below the
predicted >= 0.85. Recorded straight.

## Lane and cost

Local RTX 3090 (free, PI pre-approved 2026-07-18). grpov2 stage: 0 GPU
(T reuse). Raw base: ~1.5-2 GPU-hr (generation + post-gen extraction).
Clean-SFT and GRPO-par-true (abstention-trained, large attempt budgets):
~3-4 GPU-hr each. Total ~8-12 GPU-hr including the mandatory GPU smoke. CPU
stages (PCA/logistic/cosines, split-half control, S->T bracket): minutes.
Any paid Modal launch needs fresh user approval.

## Outcome

Resolved 2026-07-20 (status: null-result). Every number below was re-derived by
the lead from `analysis-committed/cd_rotation_timeline.json` before recording,
and the adjudication passed adversarial red-team review (8 findings, no
blockers; sign-off conditional on wording fixes F1/F2/F6, applied here). All
cosine and floor figures are L19-L24 means unless a layer is named.

Gate results, as signed:

- CD-G0 PASS, all four stages: raw 500 correct / 1323 wrong, cleansft 750/500,
  grpov2 988/500, partrue 500/717 (floor 150/150). A3 checkpoint identity
  assertions passed before generation; run manifests carry seed 20260719,
  greedy decode, and the Amendment T forced-best-guess prompt verbatim.
- CD-G2 PASS, all four stages: best-layer OOF AUROC raw 0.860 (L24), cleansft
  0.809 (L33), grpov2 0.811 (L21), partrue 0.817 (L24); no stage below 0.60,
  so every cosine is admissible.
- CD-G1 NOT MET: rotation-confirmed requires the full conjunction and it fails
  decisively on the later transitions. cleansft->grpov2 0.449 and
  grpov2->partrue 0.330 are both far below the 0.85 stability floor.
  raw->cleansft 0.192 is itself low, but the pre-registered "then stable"
  pattern is absent.
- Falsifier does not fire: raw->cleansft 0.192 is far below 0.80.
- Middle ground not applicable: 0.192 is below the (0.50, 0.80) band.
- The pre-registered readings are therefore exhausted without a positive
  determination.

Post-hoc interpretation (explicitly not a pre-registered outcome): the
within-stage split-half control returns a floor of 0.174, a half-sample lower
bound that understates full-sample reliability, meaning the correctness
direction is only weakly identified by this probe: AUROC is stable near 0.80
while the hyperplane normal is not, even though the same PCA-on-raw basis let
the answerability diagnostic reach >= 0.96 cross-stage. At these sample sizes
the cosine instrument cannot discriminate rotation from identifiability noise,
so direction identity is not measurable at any transition; the
answerability-style single-rotation-at-SFT account is neither confirmed nor
falsified for correctness, and the mechanism behind the dial's 0.679 cold
transfer stays open. The S->grpov2 bracket cosine (0.170, fit in S's own PCA
basis and not magnitude-comparable to the raw-basis cross-stage cosines) shows
a low direction-cosine coexisting with the known well-above-chance 0.679
transfer AUROC, consistent with a weakly-identified-but-real direction rather
than evidence of rotation.

Caveats carried with the result:

- The low cross-stage cosines conflate three contributions: genuine rotation,
  identifiability noise, and the accepted per-stage population/label shift.
  The split-half control bounds only the second; the population confound is
  not bounded by any control in this cell.
- The near-equality of raw->cleansft (0.192) with the split-half floor (0.174)
  carries no interpretive weight: the floor is a half-sample estimate and the
  comparison is between differently-powered fits. The CD-G1 fail rests on the
  later-transition limb alone. This also explains, rather than contradicts,
  cleansft->grpov2 (0.449) exceeding the floor.
- Raw-basis PCA truncation is an unquantified but bounded threat: later-stage
  AUROC of 0.78-0.82 in the raw basis shows the discriminative signal
  survives, and the answerability diagnostic reached >= 0.96 in the same
  basis, so truncation does not explain the low cosines. Per-stage explained
  variance in the raw basis was not recorded.
- The raw stage's ~0.05 AUROC edge over later stages is partly a basis
  artifact (the basis is optimal for raw) and is not evidence that
  correctness is most decodable in the base model.
- Reproducibility: exact regeneration of the tables requires the gitignored
  row-level artifacts and tensors in the durable exhaust store
  (/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/, staged
  and count-verified before teardown per A6). The cleansft and grpov2
  checkpoints are pinned as local scratch paths without a public mirror
  revision; raw and partrue have HF pins.

One-sentence verdict (mirrors the manifest): CD-G1 not met (later transitions
0.449/0.330 vs the 0.85 floor) and the falsifier did not fire (raw->cleansft
0.192); pre-registered readings exhausted, and the post-hoc reading is that
the correctness direction is too weakly identified (split-half floor 0.174)
for the cosine instrument to resolve rotation, leaving the 0.679
cold-transfer mechanism open.
