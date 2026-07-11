# BB: base-model confab-propensity fit and held-out reading gate on untrained Qwen3-4B

Status: SIGNED 2026-07-11. The phase-0 decision rule (section 5) and the
phase-1 gates (section 6) are LOCKED as adjudicated in section 10; predictions
recorded in section 11. The user approved sign plus the phase-0 Modal launch
(cap $15) at sign-off. Phase 1 GPU work requires its own explicit launch
approval on top of this signing.

Machine state lives in `experiment.yaml`; it is never duplicated here.

## 1. Motivation and posture

The program's overarching goal, restated by the PI on 2026-07-11 (TODO.md row
BB), is epistemic humility WITHOUT training: the trained checkpoints are the
CONTRAST condition and the product is inference-time humility on an untrained
model. This experiment is phase 1 of that base-model loop: fit and CERTIFY the
reads on untrained Qwen3-4B. Actuation (gating a caution write on the base
model's own doubt readout) is a later phase and is explicitly out of scope here.

The specific gap this fills is recorded in the direction-provenance audit: the
confabulation-propensity direction "is defined and only ever validated on the
AI-TRUE deeply-trained checkpoint ... There is no base or instruct reading
claim" (`docs/review/paper3-direction-provenance-2026-07-10.md`, "Base /
instruct validation: NO"). It is caution-residualized by construction, refits
per checkpoint, and transfers across checkpoints at only cosine 0.17
(`experiments/radial-anti-propensity-steering/AMENDMENT.md:212-214`). So this
experiment does NOT test whether the AI-TRUE direction transfers to base (AL §7
predicts that would fail); it FITS the base model's own propensity direction
with AL's recipe and asks whether THAT reads out on held-out rows.

This pairs directly with H9. H9 asked the same held-out reading question on the
AI-TRUE checkpoint and resolved INCONCLUSIVE-BY-POWER: the trained model refuses
99.3% of held-out unanswerable rows and produced only 4 confabulations in 605
unanswerable rows, so the propensity contrast (confab vs honest refusal) had no
positive mass and the reading gate H9-G1 was never read
(`experiments/h9-propensity-reading-gate/AMENDMENT.md:338-351`, on the H9
branch; the outcome is also summarised in `TODO.md` row H9). BB is the
before-training bookend: an untrained base model is expected to confabulate far
more, which should give the positive cell the mass H9 lacked. Whether it ALSO
retains enough honest refusals to populate the negative cell is exactly what
phase 0 measures rather than assumes.

This is exploratory evidence for a single model and a single seed. A phase-1
pass certifies a within-checkpoint base reading claim, not portability or a
multi-seed headline (same caveat AL and H9 carry,
`experiments/radial-anti-propensity-steering/AMENDMENT.md:208-214`;
`experiments/h9-propensity-reading-gate/AMENDMENT.md:38-41`).

## 2. Substrate and surfaces

### 2.1 Model

Untrained base `Qwen/Qwen3-4B`, pulled straight from the hub. No adapter, no
clean-SFT merge, no GRPO. The base weights are public, so unlike H9 (which had
to stage a LOCAL AI-TRUE checkpoint to a private repo,
`experiments/h9-propensity-reading-gate/AMENDMENT.md:228-237`) there is NO model
staging upload for BB. The exact hub revision is pinned in `cell.yaml`
(`model.revision`) at signing.

ADJUDICATED at sign (section 10): 4-bit, for serving-config parity
with the AI-TRUE bookend, and the archived entry script's default) or bf16 (a
cleaner untrained substrate, the choice the bf16 two-signal line made to drop
the cross-quant caveat, TODO.md row 36). This draft defaults to 4-bit for
bookend parity and flags it.

### 2.2 Prompt surface

The baseline schema-contract system prompt AL used (`answer` +
`response_confidence` keys), recorded verbatim in
`experiment/phase1/probe/analysis/amendment_al_prep/true_a0/gen/data/manifest.json`
and resolved in the harness by `load_baseline_system_prompt()`, applied
UNCHANGED to base (`experiments/h9-propensity-reading-gate/AMENDMENT.md:57-59`).
Using the identical prompt is what keeps BB comparable to H9/AL; it also creates
the schema-follow feasibility risk in section 3 (the prompt was designed for a
schema-trained checkpoint, and base was never SFT'd to emit that JSON).

### 2.3 Fit and read surfaces (disjoint by construction, inherited from H9/AL)

- FIT surface: AL's 1,662-row A0 surface (the exact rows AL fit its direction
  on, `experiments/radial-anti-propensity-steering/AMENDMENT.md:116-118`).
  Behavior labels for the base fit come from generating these 1,662 questions on
  BASE, not from AL's AI-TRUE grades. The propensity/caution directions are
  fit on the base grades.
- READ surface: H9's 750-row enlarged held-out draw, vendored ID-manifest at
  `analysis-committed/read_surface_h9_vendored/holdout_ids.jsonl` (byte-identical
  to the H9 branch manifest, sha256 `86e2dc00...`; see the PROVENANCE.md there).
  This draw is the COMPLEMENT of AL's fit surface inside the 18,496-row AH union
  pool, with zero exact-text collisions against the fit surface
  (`experiments/h9-propensity-reading-gate/AMENDMENT.md:127-131`). So the BB fit
  (1,662) and read (750) surfaces are disjoint by construction, inherited from
  H9's draw. 605 of the 750 are unanswerable, 145 answerable.

Reusing H9's exact populations (rather than a fresh draw) is deliberate: BB and
H9 become the SAME rows on the SAME staged text, differing only in the model
under test, which is what makes them a clean before/after-training bookend.

## 3. The feasibility problem this design centers on

H9's null was a starvation of the POSITIVE cell (the trained model almost never
confabulates). The base model faces the MIRROR risks, none of which can be
assumed away:

1. Positive cell (confab) mass: expected to be fine on base (the PI's "base is
   confab-rich"), but not measured yet.
2. NEGATIVE cell (honest unanswerable refusal) mass: an untrained base model may
   rarely refuse at all, in which case the propensity contrast (confab vs honest
   refusal) starves on the negative side, exactly as H9 did on the positive
   side, and the reading gate is just as dead.
3. Schema-follow: base was never SFT'd on the `answer`/`response_confidence`
   JSON contract. If it cannot emit gradeable schema, the AL grader marks rows
   degenerate and BOTH cells starve regardless of the model's epistemic
   behavior. This is a real and distinct failure mode with no prior on base.

Phase 0 exists to measure all three BEFORE any fit or gate work, and to
pre-commit to a registered negative-feasibility record for each starvation mode
rather than moving goalposts. The caution positive control (the strong signal
that certified H9's pipeline, `experiments/h9-propensity-reading-gate/AMENDMENT.md:182-189`)
also needs refusal mass to be fittable on base, so risk 2 is doubly important.

## 4. Phase 0: feasibility density probe (runs BEFORE gates lock)

Phase 0 generates and grades the already-staged 750-row H9 read pool on BASE
Qwen/Qwen3-4B under the section 2.2 prompt, and reports aggregate cell counts
only. NO extraction, NO scorer, NO direction fit in phase 0. Output is five cell
counts plus a schema-validity count, no text, no per-row generations committed.

### 4.1 What is produced

An aggregate JSON report (`analysis-committed/phase0/density_report.json`,
counts only) with, over the 750 graded rows:

- `confab`: gold unanswerable AND answered (not refused, not degenerate)
- `honest_unanswerable_refusal`: gold unanswerable AND refused
- `known_answered`: gold answerable AND answered
- `known_refused`: gold answerable AND refused
- `degenerate`: schema-invalid (not gradeable as answered/refused)
- `schema_valid_frac`: (750 - degenerate) / 750

Plus the same breakdown split by gold class, and the stated-confidence
distribution of the confab rows (for the record; non-gating).

### 4.2 Phase-0 decision rule (LOCKS at signing; pre-stated, no goalpost moves)

Phase 1 (section 5) is authorized only if ALL THREE floors below are met on the
750-row base run. If ANY floor fails, the experiment stops at a registered
negative-feasibility record naming the specific starved condition, and phase 1
does NOT run. There is no draw enlargement remedy: H9 proved that when the
limiting factor is a behavior RATE, adding more rows from the same pool does not
help (`experiments/h9-propensity-reading-gate/AMENDMENT.md:344-347`), and BB's
pool is fixed at H9's 750.

- BB-P0-A (schema-follow floor): `schema_valid_frac >= 0.60`. Below this, the
  schema-contract prompt does not elicit gradeable behavior from untrained base
  Qwen3-4B; that is itself a publishable negative-feasibility finding, and any
  prompt-family redesign is a SEPARATE new amendment, not a goalpost move here.
  [Floor value UNCERTAIN, flagged in section 10: there is no base schema-follow
  prior anywhere in the program.]
- BB-P0-B (positive-cell floor): `confab >= 20`. Below this the propensity
  contrast is underpowered on the positive side (H9's exact failure, mirrored);
  record inconclusive-by-power, stop. [Mirrors H9-G0 min_confabs=20.]
- BB-P0-C (negative-cell floor): `honest_unanswerable_refusal >= 20`. Below this
  the propensity contrast starves on the negative side AND the caution positive
  control cannot be fit; record inconclusive-by-power naming refusal starvation,
  stop. [Mirrors H9-G0 min_unanswerable_refusals=20.]

Rationale for 20/20: identical to H9-G0, so the two bookends share an
evaluability bar. A pass on all three means both propensity cells and the
caution control have enough mass for the phase-1 fit and read to be powered.

### 4.3 Inference to the fit surface (pre-stated caveat)

Phase 0 measures density on the 750-row READ surface. The 1,662-row FIT surface
is a different (disjoint) row set, so its cell counts are inferred by proxy, not
directly measured, in phase 0. The proxy is sound (same source mixture, same
model, same prompt), but it is an inference. Phase 1 step 1 generates the fit
surface on base and therefore measures its cell counts directly; a fit-surface
evaluability re-check (BB-P1-G0, section 6) gates the fit before the read is
adjudicated, so a fit surface that unexpectedly starves is caught rather than
silently producing a degenerate direction.

## 5. Phase 1: base fit + held-out reading gate (only if phase 0 passes)

Phase 1 runs only after phase 0 meets all three floors and the lead re-confirms.
It reuses the H9 instrument STACK as code (`freeze_scorer.py`, `draw_holdout.py`
in read-only manifest-consume mode, `score_holdout.py`, `near_dup_sweep.py`,
`cloud/modal_*`), but RE-FITS every object on base inputs. It does NOT reuse
H9's frozen scorer objects: those are AI-TRUE-fit and would answer a different
(transfer) question. The base-fit objects are what BB certifies.

### 5.1 Fit-pool builder and staging (authored at phase-1 gate-open, not now)

A `build_fit_pool.py`, modelled on H9's `build_holdout_pool.py`, emits the
1,662 fit-surface questions from the gitignored AL source JSONLs (via
`--data-root`), verifies each row's qhash against a committed fit ID-manifest,
and writes a gitignored `fit_pool.jsonl` (text) that the user stages to a NEW
private dataset repo (proposed `professorsynapse/eh-bb-fit-pool`). Question text
NEVER enters a committed file (containment, section 9). This builder and the
committed fit ID-manifest are produced when phase 1 opens, not in this draft
(the draft's committed harness is phase-0 only, per the task scope).

### 5.2 Fit recipe (AL §3.2, applied to base grades)

On the base fit extraction (L24/L35 pre-generation anchor, all 37 layers
captured), fit with AL's exact recipe
(`experiments/radial-anti-propensity-steering/AMENDMENT.md:122-142`): L24
PCA-128 (randomized, `random_state=20260705`), standardize, caution-residualize
(L35 logistic refused-vs-not, full-sample frozen), mean-diff of
confab-vs-unanswerable-refused, z-scaled by the base fit-population
distribution. Freeze `pca24`, `scaler24`, the frozen full-sample caution
logistic, the residualization regression, `d_raw`, and the z-scale, exactly as
H9's `freeze_scorer.py` does, into the gitignored `directions/` tree with a
sha256 object manifest.

### 5.3 Held-out reading gate

Score the frozen base direction on the 750-row base read extraction. Contrast
(AL's readout_quality contrast, `experiments/h9-propensity-reading-gate/AMENDMENT.md:152-158`):
positives are confabulations (unanswerable AND answered), negatives are honest
unanswerable refusals (unanswerable AND refused). Report the propensity AUROC
with a 1,000-resample row-bootstrap 95% CI. Caution positive control: caution
AUROC (refused vs not over all graded read rows, base frozen full-sample caution
classifier). Near-dup sensitivity sweep (section 8) re-run for the record.

### 5.4 What CAN be pinned (no prior base direction exists to reproduce)

H9's FID-1/FID-2 reproduced AL's on-disk `d_raw.npy`/`prop_z.npy`
(`experiments/h9-propensity-reading-gate/AMENDMENT.md:100-120`). There is NO
prior base direction on disk, so cross-reference fidelity does not apply.
What CAN be pinned instead:

- BB-FID-1 (determinism): re-running the frozen-scorer fit twice on the same
  base fit-extraction with the same `pca_seed` reproduces `d_raw` at cosine
  >= 1 - 1e-6 AND maxabs elementwise diff <= 1e-5. This proves the fit is
  deterministic given pinned inputs.
- BB-FID-2 (recipe parity): the fit uses the byte-identical `freeze_scorer.py`
  (pinned sha256 equal to H9's proven scorer) and AL §3.2 knobs asserted from
  `cell.yaml`. The base in-cell 5-fold OOF AUROC is recorded as the HONEST BASE
  PRIOR (non-gating; it is the base analog of AL's in-cell 0.6802 and is not
  known until the fit runs).
- Recorded SHAs: base hub revision, fit-pool and read-pool qhashes, extraction
  manifest SHAs, frozen-scorer object SHAs.

**Correction note, 2026-07-11 (pre-launch, red-team finding F2):** the
BB-FID-2 wording above (byte-identical `freeze_scorer.py`, pinned sha256 equal
to H9's proven scorer) is unachievable by construction: BB's scorer file
necessarily differs from H9's in I/O (it reads BB's own base extraction and
base grades, not AL's `al_run_dir`/`al_extract_dir`/`al_graded`) and in
fidelity-reporting logic (no on-disk prior direction exists on base to
cross-reference, as this section already states). `gates.yaml` was repinned
pre-launch (sha256 `3f23b51f...` -> `33fe08ad...`, `bin/exp repin`, full
reason in `experiment.yaml` repins) to redefine BB-FID-2 as: the fit-math
functions (PCA / standardize / caution-residualize / mean-diff / z-scale) are
verbatim-identical to H9's pinned `freeze_scorer.py`, checked both by a knob
assertion against `cell.yaml` and by a normalized-source (comments/docstrings
stripped) sha256 comparison of the copied function bodies, plus AL §3.2 knobs
asserted from `cell.yaml`; both whole-file sha256 values are recorded in the
fidelity report for the record. This preserves the fidelity INTENT (identical
fit math) without claiming an impossible whole-file hash match. No outcome
gate (BB-P1-G0/G1/G2) changed.

## 6. Gates (DRAFT; LOCK at signing; values flagged for lead adjudication)

Phase-0 floors are in section 4.2 (they gate whether phase 1 runs). The phase-1
gates below adjudicate the reading claim. Because the base direction is fit
fresh, there is no pre-existing base number to anchor to; the honest base prior
(base in-cell OOF AUROC) is measured in phase 1 step 1. Two anchoring choices
were possible; the lead ADJUDICATED Choice A at sign (section 10):

- Choice A (proposed default): absolute lines equal to H9's, so "does the base
  direction read at a useful, certifiable level" has the same bar as the trained
  bookend. This is fully pre-registerable at signing.
- Choice B: derive the lines from base's measured in-cell OOF excess (pass =
  chance + two-thirds of that excess), mirroring H9's derivation METHOD rather
  than its numbers. Defensible but the numeric line floats until the fit runs.

Proposed gates under Choice A:

- BB-P1-G0 (fit-surface evaluability, precondition): the base fit generation
  yields >= 20 confabs AND >= 20 honest unanswerable refusals on the 1,662-row
  fit surface. Below either, the direction cannot be fit at power; stop at a
  negative-feasibility record. [Mirrors H9-G0 on the fit surface.]
- BB-P1-G1 (reading, PASS): held-out propensity AUROC >= 0.62 AND bootstrap 95%
  CI lower bound > 0.55.
- BB-P1-G1 (reading, FAIL/FALSIFIER): held-out propensity AUROC <= 0.55 OR
  bootstrap 95% CI upper bound < 0.60.
- BB-P1-G1 INCONCLUSIVE band: point estimate strictly between 0.55 and 0.62, or
  a CI straddling the lines, is reported as inconclusive. No goalpost moves.
- BB-P1-G2 (caution positive control, FLOOR): held-out caution AUROC >= 0.80.
  [Floor UNCERTAIN, flagged section 10: H9 used 0.90 anchored to AL's 0.9561
  in-cell, but that prior is AI-TRUE; base caution sharpness is unknown. 0.80 is
  a proposed lower floor for an untrained model. The base in-cell caution OOF
  AUROC is recorded in phase 1 step 1 as the honest prior and the held-out value
  should sit within ~0.10 of it; the lead may prefer to set G2 relative to that
  measured prior instead of an absolute 0.80.] Below floor, treat the read draw
  as a pipeline failure and do not adjudicate G1 (same logic as H9-G2).

FALSIFIER (manifest): held-out propensity AUROC <= 0.55, OR the bootstrap 95% CI
upper bound < 0.60, means the base model's own confab-propensity direction does
not read out on held-out rows, and the "the base model carries a readable
confab-propensity signal" claim is not supported.

## 7. Modal lane (phase 0 only in this draft; separate launch approval required)

`cloud/modal_bb_phase0.py` is cloned from H9's `modal_h9_holdout.py` (current
version on the H9 branch, after repairs 2 and 3) with the minimum diff:

- base model pulled from the hub (`Qwen/Qwen3-4B` at the pinned revision), no
  adapter, no staging model repo;
- reuses the already-staged private pool `professorsynapse/eh-h9-holdout-pool`,
  file `holdout_pool_enlarged.jsonl` (750 rows), verified against BB's vendored
  ID-manifest by exact row_key set AND per-row qhash (C3/C4, unchanged from H9);
- generate + grade ONLY: the extraction stage is dropped (phase 0 needs behavior
  labels, not activations);
- the import-environment block (legacy-wrapper-tree install, AC config shim,
  PYTHONPATH, fail-fast preflight) is kept EXACTLY as the H9 repair-2/3 version
  landed it, because the same archived entry script and grader are used;
- same launch guards (`EHR_LAUNCH_OK=bb-base-propensity-fit-read`,
  `MODAL_COST_CAP_USD`, `EHR_REPO_COMMIT`, `HF_TOKEN` for the pool read), same
  in-run tree checkpoint/resume and DONE marker;
- writes an aggregate `density_report.json` (counts only) plus the gitignored
  per-row graded rows (pulled back, never committed).

Phase 1's extraction + fit-surface generation harness is a separate file
authored at phase-1 gate-open (it re-adds the extraction stage and the fit-pool
staging); it is not in this draft.

### 7.1 GPU and cost estimate (phase 0)

Generation only, 750 rows on base Qwen3-4B, A10G. From H9's measured 3090 rate
(~1.685 s/row generation, `experiments/h9-propensity-reading-gate/AMENDMENT.md:244-249`),
750 rows is ~21 min generation, plus base download and load (~3-5 GB in 4-bit).
Wall time ~30-40 min. Cost at ~$1.10-1.50/hr A10G: ~$1-2. Pre-registered
`MODAL_COST_CAP_USD=15`, generous headroom. This draft does not run `modal run`.

## 8. Registered sensitivity check (phase 1)

The H9 near-duplicate KUQ sweep (`near_dup_sweep.py`, token-overlap Jaccard,
threshold 0.90, `experiments/h9-propensity-reading-gate/AMENDMENT.md:305-318`)
re-runs on BB's read surface. Because BB reuses H9's exact read draw AND AL's
exact fit surface, the KUQ populations compared are identical to H9's, which
flagged 0 rows (max overlap 0.75, `experiments/h9-propensity-reading-gate/AMENDMENT.md:358-359`).
BB re-runs it for the record; if any row flags, the propensity AUROC is
recomputed excluding flagged rows and reported alongside, never pooled.

## 9. Containment (binding)

Question text, generations, and raw activations are NEVER committed. Committed
artifacts are ID-manifests (row_key/source/gold_label/qhash), fitted JSON, and
aggregate reports under `analysis-committed/` only. The private HF staging pool
is the sanctioned channel for text to reach Modal; base weights are public and
pulled from the hub (no model staging). The experiment `.gitignore` (safetensors,
`**/rows*.jsonl`, `**/*pool*.jsonl`, generations) is the belt-and-suspenders net,
carried over from H9.

## 10. Open questions -- ADJUDICATED by the lead at sign (2026-07-11)

1. Load precision: 4-BIT. Bookend parity with H9/AI-TRUE (same entry script,
   same serving shape) outweighs substrate purity; a bf16 base run would add a
   cross-precision confound to every H9 comparison. [section 2.1]
2. Phase-1 reading-gate anchoring: CHOICE A (absolute H9 lines). Fully
   pre-registerable at signing and makes the before/after-training bookends
   directly comparable; Choice B's floating line invites goalpost suspicion.
   [section 6]
3. BB-P0-A schema-follow floor: 0.60 ACCEPTED as proposed. No base prior
   exists; 0.60 is low enough not to fake-fail a usable surface and high
   enough that grading below it is untrustworthy. [section 4.2]
4. BB-P1-G2 caution-control floor: ABSOLUTE 0.80, with the base in-cell
   caution OOF recorded alongside as the honest prior (non-gating). [section 6]
5. Predictions recorded in section 11 at sign.
6. Vendored-manifest approach CONFIRMED. The vendored copy was verified
   byte-identical to H9's committed enlarged manifest at sign time
   (sha256 prefix 86e2dc00400792ef, 750 rows); BB does not depend on PR #273
   merge order. [section 2.3 / PROVENANCE.md]

## 11. Predictions scoreboard (recorded at sign, 2026-07-11)

| Predictor | Call |
|-----------|------|
| orchestrator | Phase 0: all three floors pass, weakly held (~50%); the single most likely failure is BB-P0-C (honest-refusal floor), given the Qwen3.5 ladder baseline refused 0/1,127 under a similar contract prompt. Schema-follow passes comfortably (release model, simple JSON contract). |
| user | Phase 0: ALL THREE FLOORS PASS (recorded at sign-off approval). |

## 12. Outcome

Filled at resolve. Records the verdict, the phase-0 floors, and (if phase 1 ran)
the reading-gate result, with the one-sentence summary that also goes into
`verdict:` in the manifest.
