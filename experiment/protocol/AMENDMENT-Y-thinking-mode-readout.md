# Amendment Y — The Two-Signal Readout Under Thinking (and What the Thinking Says)

**Status:** DRAFT (2026-06-30) — pre-registration. Gates §4 PROPOSED, to be LOCKED
at user sign-off. Tier-2 exploratory cell (new evidence, falsifier pre-stated;
reported separately from the locked PROTOCOL v0.3 matrix). Not yet authorized to run.

**Instrument rationale:** Tier-2 Amendment per
`experiment-runner/reference/amendment-vs-lab-notebook.md`. New evidence surface
(a generation *mode* we have never probed) with a pre-stated falsifier. Every prior
cell (S/T/U/V/W/X) ran with **thinking OFF** (`enable_thinking=False` in the probe
extractor and the runtime CLI). This cell asks two questions that mode never could:
(A) does the readout survive when the model reasons first, and (B) does the chain of
thought *verbalize* the internal signal the probe reads off activations.

**Why this is on-thesis.** The program's central finding is *"it knows, it won't
say"* — an internal answerability/correctness signal the model does not surface in
its stated confidence. Thinking is the obvious channel where the model **can** say
more. So this cell is a direct test of whether reasoning closes that gap or leaves it
open.

**Design decisions (chosen with user, 2026-06-30):**
- **Checkpoint:** RAW `unsloth/Qwen3-4B-bnb-4bit`, no adapter — matches Amendments
  S/W/X, keeps the training-free spine, isolates the thinking effect from any
  abstention training.
- **Content method:** BOTH — a deterministic lexicon over the think trace AND an
  LLM-judge "expressed-confidence" scalar per trace (the latter is the head-to-head
  comparator against the probe).
- **Scope:** 4B anchor only. Cross-size / cross-family thinking is a later question,
  not part of this first probe.

**Compute:** GPU — one mixed-pool generation pass with thinking ON (long traces; raise
`max_new_tokens`) + dual-position extraction on the RAW base. No training. Plus CPU /
LLM-judge calls for the content analysis. Launch requires explicit user approval per
operator discipline, and sequences AFTER Amendment X merges (one amendment per branch
off an up-to-date `main`).

## 1. Facts this builds on

- The training-free two-signal readout on the raw Qwen3-4B base, **thinking OFF**:
  answerability gate ~0.997 (pre-gen anchor), post-gen correctness dial ~0.834,
  hallucination veto ~0.75 (correct ranked above confident confabulation). The full
  mechanism reads off the raw base; training only sharpens the veto.
- The gate reads answerability at the prompt anchor (last prompt token); the dial
  reads per-answer correctness post-generation; the two axes are orthogonal (fusing
  the scalars hurts correctness).
- The internal→stated gap: the probe reads the signal off activations far better than
  the model states it in emitted confidence. Thinking has never been in the loop.

## 2. Hypotheses and predictions

### Arm A — does the readout survive thinking? (falsifier-bearing)

**H_Y-A.** On the raw Qwen3-4B base with `enable_thinking=True`, a linear probe still
recovers (a) an answerability gate at the prompt anchor, (b) a post-generation
correctness dial, and (c) a hallucination veto.

- **Y-G1 (gate):** AUROC(known vs unknown) at the prompt anchor ≥ **0.65**, CI excl
  0.50. **Predicted near-unchanged** vs thinking-OFF (~0.997): the gate is read
  *before any generation*, so thinking — which happens after the anchor — should not
  move it. A large move here is an internal-validity flag on the rendering, not a
  finding.
- **Y-G2 (dial):** AUROC(correct vs wrong) post-generation ≥ **0.65**, CI excl 0.50,
  at the better of two candidate tap points (see §3).
- **Y-G3 (veto — PRIMARY):** AUROC(correct vs hallucination) ≥ **0.65**, CI excl 0.50.

**Predicted direction:** PASS. Thinking is expected to *raise* answer correctness
(shifting base rates, so we report AUROC + selective prediction, not raw accuracy) and
should not destroy the readout. Sub-question (descriptive): the correctness signal may
already be present at **end-of-think**, before the answer token is emitted.

### Arm B — what does the thinking say, and does the probe still beat it?

**H_Y-B.** The think trace carries *some* verbalized confidence signal, but the probe
reads correctness information the trace does not state.

Define per answered item: `cot_conf` = LLM-judge expressed-confidence scalar (0–1)
over the think trace; `probe_dial` = the activation readout (calibrated dial). Both as
predictors of correctness.

- **Primary content metric:** incremental AUROC of `probe_dial` over `cot_conf` for
  predicting correctness (ΔAUROC = AUROC(cot_conf + probe) − AUROC(cot_conf alone)),
  with bootstrap CI.
- **Predicted direction:** ΔAUROC > 0, CI excludes 0 — *even given room to reason, the
  model knows more than it says.*
- **Two-sided interpretation (pre-stated, both informative — no goalpost):**
  - If ΔAUROC > 0 (CI excl 0): the readout still adds signal beyond the verbalized
    chain of thought → strengthens "readout, not a lesson" under reasoning.
  - If ΔAUROC ≈ 0 (CI incl 0) AND `cot_conf` AUROC ≥ `probe_dial` AUROC: thinking
    **verbalizes** the internal axis → reasoning is the channel that surfaces what the
    model knows. A different, equally publishable finding.

**Specific content prediction (descriptive, on-thesis):** on *unanswerable* questions
the model answers anyway (hallucinations), the think trace expresses **low** verbalized
doubt (confident confabulation) while the probe veto still flags them — i.e. the
internal doubt signal is not verbalized even with reasoning. Measured as
`cot_conf(hallucination)` ≈ `cot_conf(correct)` while `probe_dial(hallucination)` ≪
`probe_dial(correct)`.

## 3. Method (GPU extraction + CPU/LLM-judge score)

**Checkpoint load.** RAW `unsloth/Qwen3-4B-bnb-4bit`, NO adapter. **Thinking ON**
(`enable_thinking=True`). Amendment S's answer-encouraging system prompt VERBATIM (so
the base answers freely and a wrong/hallucination class exists; identical surface to
S/W/X except the thinking flag). `max_new_tokens` raised to budget the full
`<think>…</think>` + answer (target ≥ 1024; tune in the smoke so traces are not
truncated mid-think).

**Pool.** ONE mixed pool (reuses the Amendment V builder): PopQA + TriviaQA answerable
(graded correct/wrong vs gold aliases) + SelfAware-unknown (unanswerable; hallucination
if answered). Same pool construction as Amendment X for comparability.

**Generation & parsing.** Greedy decode. Split each generation into the think block and
the post-`</think>` answer. **Grade on the answer text only** (not the think block).
Persist BOTH strings per item (think trace + answer) for the content analysis — this is
new vs prior cells, which kept no generated text.

**Tap points (dual-position, all layers, fp32).**
- **Gate:** pre-gen anchor = last prompt token (unchanged definition).
- **Dial:** extract at TWO candidate positions and report both: (1) **end-of-think**
  (last token of the `<think>` block — the "decision point"), and (2) **end-of-answer**
  (last answer content token — matches the thinking-OFF dial). The Y-G2/Y-G3 gates use
  the better of the two, position reported (not cherry-picked across a gate set).

**Score (CPU), Arm A.** Fit the correctness dial on this model's correct/wrong (OOF for
the honest reference, full-fit applied to its hallucinations); sweep layers for the best
gate (known vs unknown, pre-gen) and best dial (correct vs wrong, each candidate
position); report Y-G1/G2/G3 + the within-SelfAware control + a head-to-head vs the
thinking-OFF 4B numbers.

**Content analysis, Arm B.**
- **Lexicon (deterministic):** per think trace, count uncertainty markers ("not sure",
  "I think", "might", "possibly", "don't know"), self-correction / backtracking events
  ("wait", "actually", "no,"), explicit-abstention reasoning ("cannot be answered",
  "no way to know"), and trace length (tokens). Report distributions stratified by
  outcome class (correct / wrong / hallucination / known-answered).
- **LLM-judge (`cot_conf`):** a fixed judge model + frozen prompt scores each think
  trace's expressed confidence in its own answer on [0,1], blind to the gold label and
  to the probe. Judge model + prompt + version recorded for reproducibility.
- **Head-to-head:** the ΔAUROC test in §2 Arm B, plus the hallucination-doubt
  comparison.

**Caveats.** Single-seed, greedy (one trajectory per item); structural ungraded
hallucination label (unknown ∧ answered); cross-dataset correctness reference
(PopQA/TriviaQA vs SelfAware) with the within-SelfAware control reported to bound
dataset shift — identical to W/X. The think trace is one sampled reasoning path, not the
model's full reasoning distribution. `cot_conf` depends on the judge; the lexicon is the
judge-independent backstop. Best layer/position chosen per signal from its own surface
(reported, not cross-set cherry-picked).

## 4. Gates and falsifier (PROPOSED — to be LOCKED at sign-off)

**Data-adequacy precondition (BEFORE scoring; not a result).** ≥ **30 wrong** AND ≥ **50
hallucinations** among answered rows. The raw base answers freely, so expected to clear;
below floor is a DATA-STAGE stop, not a probe verdict. Additional thinking-mode
precondition: traces are not systematically truncated mid-think (checked in the smoke;
raise `max_new_tokens` until the truncation rate is negligible).

**Metrics (threshold-free):**
- **Y-G3 — PRIMARY:** AUROC(correct vs hallucination) ≥ **0.65**, CI excl 0.50.
- **Y-G1:** AUROC(known vs unknown) ≥ **0.65**, CI excl 0.50.
- **Y-G2:** AUROC(correct vs wrong) ≥ **0.65**, CI excl 0.50.
- **Content (Arm B, reported with CI; two-sided interpretation per §2, NOT a pass/fail
  threshold):** ΔAUROC(probe over cot_conf); `cot_conf` standalone AUROC; the
  hallucination-doubt comparison; lexicon distributions by outcome class.

**SUCCESS — the readout survives thinking:** Y-G1 AND Y-G2 AND Y-G3 pass.

**FALSIFIER — the readout is thinking-OFF-specific:** Y-G3 < 0.65 AND its CI includes
0.50 (the veto does not survive reasoning) — a bounding negative reported as such.

**Arm B is exploratory and two-sided:** both ΔAUROC outcomes are pre-registered as
informative (readout-still-wins vs thinking-verbalizes-it). The *direction and its
interpretation* are fixed here; the result is reported against this map with no
goalpost-moving.

**No goalpost-moving.** Thresholds and the Arm-B interpretation map fixed at sign-off;
descriptive numbers do not move the verdicts; an ambiguous straddle is reported as
ambiguous.

## 5. Reporting and promotion

Exploratory, single-model, single-seed, thinking-ON; reported separately from the locked
matrix. A SUCCESS extends the two-signal readout to reasoning mode and, via Arm B, gives
the "it knows, it won't say" diagnosis its sharpest test: whether reasoning surfaces the
internal signal. Written into the paper series as the thinking-mode section of Paper 2
(the internal-vs-stated gap) and/or Paper 3 (the readout). **Remaining limitations:**
one family, one size, one sampled reasoning path; cross-size/cross-family thinking and
sampled (multi-path) reasoning are named as next axes, not claimed here.

## 6. Sign-off checklist
- [x] Two arms, predictions, and a falsifier stated before any run (this doc).
- [x] Arm-B interpretation map (both ΔAUROC directions) pre-stated as informative.
- [x] Design decisions recorded (raw 4B base; lexicon + LLM-judge; 4B-only).
- [x] Data-adequacy + truncation preconditions stated before scoring.
- [x] Distinct rationale vs prior cells (generation MODE never probed before).
- [x] Scope limitation stated (one family/size/path).
- [ ] Judge model + frozen judge prompt fixed and recorded (before any judge call).
- [ ] User sign-off recorded; gates LOCKED.
- [ ] GPU launch authorization (explicit), sequenced AFTER Amendment X merges.

## 7. Result

Pending sign-off and run.
