---
amendment: AJ
slug: knowledge-subspace-erasure
question: >-
  Does the caution readout (refuse vs answer among known questions) survive
  certified erasure of the full linearly readable knowledge/answerability
  content, or was its separability carried by that content all along?
predictions:
  orchestrator:
    call: SURVIVES (AJ-G2 PASS)
    confidence: "~85%"
    recorded: 2026-07-04
    basis: >-
      Three converging priors: B1 held rank-1 doubt projection at 0.825
      held-out; the session 0035 hydra result kept refuse/answer AUROC ~0.90
      through 40 iterative direction removals; and the paper3 Section 5
      knowledge-orthogonality check found |cos| ~ 0.04-0.09 between
      caution_perp and the knowledge probe axis. Residual risk: LEACE's
      whitened rank-1 erasure is strictly stronger than the raw mass-mean
      projection those priors used.
  user:
    call: SURVIVES (AJ-G2 PASS)
    recorded: 2026-07-04
    quote: "AJ survived I agree worth being optimistic here."
outcome: null
---

# Amendment AJ — Knowledge-Subspace Erasure (rank-1 → certified linear erasure)

Status: SIGNED 2026-07-04 — dual predictions recorded (both SURVIVES); user
sign-off given; CPU-only analysis run launched 2026-07-04. Instrument note:
a row-key sanitization bug in the harness loader (`::` vs `__`) was found and
fixed pre-launch (PR #187); gates untouched.

## 1. Motivation and strategic position

Paper 3 (Section 9) carries this caveat on the two-axis separability result:

> we projected out only the rank-1 mass-mean doubt direction; removing a full
> multi-dimensional knowledge-probe subspace is the stronger reducibility test
> and is not yet done.

This amendment is that stronger test, upgraded past "multi-dimensional
projection" to a *certified* erasure: LEACE (Belrose et al. 2023,
arXiv:2306.03819) removes, in closed form, everything any linear classifier
can use to recover a concept, with the erasure verified empirically rather
than assumed. If the caution readout still separates refuse from answer after
the gold-answerability concept is provably linearly unreadable, then caution's
linear separability is not an echo of the knowledge readout, and the Section 5
two-axis claim loses its main reducibility caveat. If it collapses, the
caveat was load-bearing and Section 5 must be weakened accordingly.

Backlog item 29 (TODO.md); research base ingested in PR #182 (INLP, RLACE,
LEACE, amnesic probing). Exploratory precedent: the session 0035 hydra
analysis (`experiment/phase1/probe/analysis/mi_exploration_20260703/mi-caution-rank/`)
found caution survives 40 iterative direction removals, but that analysis
removed caution-fit directions, not knowledge-fit ones, and carried no
erasure certificate; it motivates but does not answer this question.

## 2. Hypotheses and pre-stated prediction

- **H-independent**: caution has linear structure independent of the linearly
  readable answerability content; erasing that content leaves refuse/answer
  separability approximately intact (matching an equal-rank random-erasure
  control).
- **H-carried**: caution's apparent separability rides on the knowledge
  readout; certified erasure collapses it toward chance.

Orchestrator prediction (sealed above): H-independent, ~85%. Per the standing
dual-prediction practice, the user records an independent prediction in the
frontmatter before launch; ledger `docs/prediction-scoreboard.md`.

## 3. Design

### 3.1 Data surface (frozen, all cached; no new generation)

- Hidden states: `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/`,
  per-row `{probe_pool_row_key}__h_lora.safetensors`, layer **L35** (the
  paper3 Section 5 anchor), 2560 dims.
- Labels: `experiment/phase1/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl`
  (n = 1233). Concept to erase: gold answerability `label`
  (known = 0 / unknown = 1), all rows. Caution readout rows: `behavior_cell`
  = `known_refused` (pos, 168) vs `known_correct_answered` (neg, 373);
  `known_answered_wrong` (15) and `unknown_answered_wrong` (1) are excluded
  from the caution contrast (matching the B1 convention) but included in the
  concept fit via their gold label.

### 3.2 Procedure (all out-of-fold; harness is the SSOT)

Harness: `experiment/phase1/probe/amendment_aj_subspace_erasure.py`
(committed with this doc; locked gate constants are mirrored at the top of
the file). 5-fold stratified CV (strata = label × caution-cell), seed
20260704. Within each fold, fit on train only, evaluate on test only; all
reported AUROCs are pooled OOF:

1. **Baselines**: knowledge probe (logistic, standardized, C = 0.5) and
   caution probe, no erasure.
2. **LEACE erasure** of the answerability concept (rank-1 in whitened space,
   shrinkage-regularized whitening, shrink = 1e-2 of mean eigenvalue), then:
   - **certificate**: a freshly fit knowledge probe on erased train rows,
     scored on erased test rows;
   - **primary**: a freshly fit caution probe on erased train known-cells,
     scored on erased test known-cells.
3. **Equal-rank random control**: 20 random whitened unit directions erased
   through the identical machinery; caution AUROC per repeat.
4. **INLP rank curve** (descriptive): k = 1..40 iterative logistic nullspace
   projection of the answerability concept, certificate + caution AUROC per
   k, plus a matched random-rank curve (5 repeats).
5. **Uncertainty**: 2000-resample row bootstrap on the post-LEACE caution
   AUROC and on the gap (random-control mean − post-LEACE).

### 3.3 Authorized instrument knobs (certificate-facing ONLY)

If and only if AJ-G1 fails (certificate > 0.55), the following may be tried,
in order, without touching any gate value: shrinkage in {1e-3, 1e-1}; a
second LEACE application on the erased states. If the certificate still
fails, the primary instrument falls back to INLP at the smallest k whose
certificate passes, pre-stated here. No knob may be turned after AJ-G1
passes.

## 4. Gates (LOCKED at signing)

- **AJ-G1 (erasure certificate, validity gate)**: post-LEACE fresh knowledge
  probe OOF AUROC ≤ **0.55**. If G1 fails after the Section 3.3 ladder, the
  run is INVALID (no verdict, no falsifier).
- **AJ-G2 (primary, caution survives)**: post-LEACE caution OOF AUROC ≥
  **0.70** AND (random-control mean − post-LEACE) ≤ **0.05** (5 points).
  PASS ⇒ H-independent; the paper3 Section 9 rank-1 caveat is lifted.
- **Falsifier (H-carried)**: post-LEACE caution OOF AUROC < **0.65** ⇒
  caution's linear separability was carried by the erased knowledge content;
  Section 5's two-axis claim must be weakened, and the compound-caution
  theory loses its "independent block" support at this layer.
- **Ambiguous zone**: 0.65 ≤ AUROC < 0.70, or AUROC ≥ 0.70 with a gap >
  0.05: verdict AMBIGUOUS, adjudicated by the user; no goalposts move.

Expected baseline reference (not a gate): un-erased caution OOF AUROC in the
0.83–0.91 band seen in prior fits on these rows.

## 5. Smoke (run 2026-07-04, pre-signing; synthetic only, no real data read)

`--smoke` plants both regimes at d = 64, n = 1200:

- Regime A (caution partially independent): certificate 0.515, caution
  0.843 → 0.813 post-LEACE vs random control 0.835 → G2 PASS detected.
- Regime B (caution ≡ knowledge): certificate 0.496, caution 0.553 → 0.441
  post-LEACE → falsifier detected. (Regime B's synthetic baseline is modest
  because the refuse threshold is applied within a label-restricted range;
  the collapse contrast is what the assertion tests.)

Both regimes correctly classified; instrument validated end-to-end.

## 6. Instrumentation (descriptive, gate-free)

- INLP rank curve k = 1..40 with per-k certificate: at what rank does the
  concept become unreadable, and what does caution do on the way (hydra-style
  plot, now with the erasure direction being *knowledge*, not caution).
- Random-rank matched curve: separates "damage from removing k dimensions"
  from "damage from removing the knowledge subspace specifically".
- Post-LEACE knowledge AUROC vs baseline (0.997 expected baseline) as the
  effect-size display of what was erased.

## 7. Preconditions and approvals

1. This doc merged to main via PR (prereg-first pattern, as Amendment AD).
2. User prediction recorded in frontmatter + explicit sign-off. **Launch
   does not require GPU approval** (CPU-only on cached tensors), but per the
   amendment discipline it still requires the sign-off.
3. Analysis outputs land untracked under
   `experiment/phase1/probe/analysis/amendment_aj_subspace_erasure/`.
4. Verdict adjudication is the user's.

## 8. Interpretive caveats (pre-stated)

- **Linear-only guarantee.** LEACE certifies no *linear* recovery; a
  nonlinear probe could still read answerability (Ravfogel et al. 2020 showed
  exactly this pattern for INLP). The claim under test is about the *linear*
  reducibility of the caution readout, matching the linear readouts used
  throughout paper3.
- **Concept = gold answerability, not "knowledge" writ large.** We erase
  what a linear probe of the gold known/unknown label reads at L35. Other
  operationalizations (per-item correctness, confidence axes at other
  layers) are out of scope.
- **Single checkpoint, single layer, single dataset.** Clean-SFT → GRPO-v2
  seed 1, L35, SelfAware rows; generalization is a follow-up, and the
  cross-family program (backlog item 28) is the vehicle.
- **Anchor position only.** These are pre-generation anchor states; the
  session 0035 finding that primes write off-axis at generation time is
  untouched by this design.
- **Erasure is representational surgery on cached states**, not an
  intervention on the running model; no behavioral claim follows directly
  (that is the steering line's job).

## 9. Result

(To be filled after the run; gates as locked in Section 4.)
