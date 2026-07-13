---
title: "Loss-Averse Humility: Comparing SFT, DPO, and KTO for Teaching Small Language Models to Say \"I Don't Know\""
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v0
date: 2026-06-18
target: arXiv (cs.CL / cs.AI)
evidence_status: >
  First manuscript scaffold. Results prose is intentionally tiered and gated.
  Publication-grade claims require reconciliation against run records, scored
  rows, configs, and the companion provenance inventory.
companion_artifact: archive/papers/retired/results-provenance-inventory.md
---

# Loss-Averse Humility: Comparing SFT, DPO, and KTO for Teaching Small Language Models to Say "I Don't Know"

**Joseph Rosenbaum** - Synaptic Labs - connect2synapse@gmail.com

*Draft v0. Not for distribution. This draft is a scaffold for Paper 2. It
separates locked v0.3 headline evidence, Amendment A sequential evidence,
Amendment B stated-confidence evidence, and exploratory mechanism diagnostics.*

## Abstract

Language models often answer questions they cannot support, but training a
model to abstain can create the opposite failure: over-refusal on questions the
model could answer. This paper studies that tradeoff in a small open-weights
setting by comparing supervised fine-tuning (SFT), direct preference
optimization (DPO), and Kahneman-Tversky optimization (KTO) on model-specific
known/unknown data. The signed v0.3 protocol pre-registers a three-way
comparison on Qwen3-4B-Instruct with seed-level uncertainty, an 8B confirmation
track, a bridge replication against Cheng et al.'s Llama-2-7b-chat IDK setting,
and a sensitivity panel for learning-rate and beta effects. The motivating
hypothesis is that KTO's unpaired desirable/undesirable format and
loss-aversion weighting may offer a practical abstention-training method with a
better refusal/over-refusal operating point than SFT and less calibration damage
than DPO.

[GATED: Replace this paragraph with reconciled headline results from the locked
v0.3 default matrix only. Do not use sensitivity, Amendment A, Amendment B, or
mechanism results as headline evidence.]

Local extension evidence currently suggests a two-stage story: SFT induces an
abstention routine but over-refuses, cold-start DPO/KTO do not reliably induce
abstention on the same local surfaces, and SFT-warmed preference training moves
the abstention boundary. Sequential DPO strongly reduces over-refusal but can
overshoot into confident answering; sequential KTO preserves more abstention but
leaves more over-refusal. Mechanism diagnostics are consistent with SFT creating
stronger known/unknown separability than cold-start preference training, but
causal intervention results are not yet claim-bearing.

## 1. Introduction

Epistemic humility in a language model is not simply politeness. A useful model
should answer when it has enough support, refuse or qualify when it does not,
and avoid replacing uncertainty with fluent guesses. Existing evidence reviewed
in Paper 1 points to a difficult training problem: post-training can improve
abstention and truthfulness behaviors, but it can also damage calibration, teach
overconfident agreement, or create over-refusal.

The abstention version of this problem is concrete. Supervised IDK training can
teach a model to say "I don't know" on unknown questions, but the same behavior
can generalize too broadly to known questions. Preference methods can penalize
that over-refusal, but paired preference construction is costly and preference
optimization has its own calibration risks. KTO is attractive because it accepts
unpaired desirable and undesirable examples, matching the natural shape of
known/unknown supervision: gold answers and abstentions are desirable in the
right contexts, while hallucinations and avoidable refusals are undesirable.

This study asks whether KTO can improve the abstention/over-refusal tradeoff in
a small open model, and whether the comparison against SFT and DPO reveals a
more general tension between behavioral abstention and calibration. The answer
is intentionally constrained by evidence tier. The locked v0.3 protocol supplies
the only source of headline claims. Amendment A sequential runs, Amendment B
stated-confidence reruns, and Phase 3 mechanism probes are reported separately
as extensions and diagnostics.

Contributions:

1. A pre-registered SFT/DPO/KTO comparison for model-specific abstention
   training, with seed-level uncertainty and a held-out known/unknown evaluation
   design.
2. A direct test of whether KTO's loss-aversion framing provides a native dial
   for the abstention versus over-refusal operating point.
3. A prospective sequential extension testing whether preference optimization is
   better used after SFT has induced an abstention routine.
4. A mechanism-facing diagnostic layer that asks whether behavioral abstention
   aligns with known/unknown separability in hidden states.

## 2. Related Work

This paper follows the evidence synthesis in Paper 1. That synthesis frames
epistemic humility as a family of behaviors and measurements: calibration,
abstention, hallucination resistance, sycophancy resistance, and coherence
between stated, token-level, and hidden-state signals.

The immediate empirical lineage is IDK and abstention training. Cheng et al.'s
setting provides both a benchmark target and a bridge replication path:
abstention training improves unknown-question refusal, while over-refusal on
known questions remains a central failure mode. Paper 1's reanalysis reports
the bridge target numbers used by this protocol: Idk-SFT over-refusal at 42.71%
and Idk-DPO over-refusal at 23.27% on the Cheng test set of 11,313 questions.

The method lineage is SFT versus preference optimization. SFT supplies a direct
behavioral target but can teach a broad refusal policy. DPO supplies paired
preference pressure without an explicit reward model. KTO supplies unpaired
binary desirable/undesirable pressure and introduces loss-aversion weighting,
which is a plausible fit for epistemic settings where confident hallucination
and unnecessary refusal have asymmetric costs.

The calibration lineage motivates joint reporting. A model can abstain more
often while becoming less calibrated, or can answer more often while becoming
more confidently wrong. For that reason the protocol measures refusal recall,
over-refusal, truthful rate, answer correctness, and token-level ECE rather than
treating any single metric as sufficient.

[TODO: Convert this section to citation-complete prose after Paper 1 reference
list and Paper 2 bibliography are reconciled. Do not invent bibliographic
details.]

## 3. Study Design

### 3.1 Evidence Tiers

The manuscript uses four claim tiers.

| Tier | Source | Manuscript role |
| --- | --- | --- |
| Locked v0.3 headline | Signed 2026-06-10 protocol, default config matrix, required seeds, pre-registered statistics | Only source for primary tables and headline claims |
| Amendment A sequential | Signed prospective extension for `SFT -> DPO` and `SFT -> KTO` | Separate extension section; not merged into v0.3 |
| Amendment B stated confidence | Unsigned stated-confidence prompt-contract reruns and prospective GRPO framing | Measurement extension only; not a replacement for plain-answer evals |
| Phase 3 mechanism diagnostics | Hidden-state probes and causal-pilot smoke diagnostics | Exploratory mechanism hypotheses only |

### 3.2 Models and Arms

The locked v0.3 study uses Qwen3-4B-Instruct as the primary small-model target
and Qwen3-8B-Instruct as a confirmation scale. Thinking mode is pinned off. The
main arms are base, Idk-SFT, Idk-DPO, and Idk-KTO. Bridge replication uses
Llama-2-7b-chat in the Cheng IDK setting.

[GATED: Confirm final reportable model revisions, adapter identities, and seed
inclusion from run records and the provenance inventory.]

### 3.3 Data Construction

Labels are model-specific. The base model is probed on a TriviaQA train split
with 32 stochastic samples plus one greedy decode. Known questions are those
with greedy-correct output and sufficient sample correctness; unknown questions
are those with zero sample correctness. Ambiguous middle cases are discarded for
the primary contrast and retained for sensitivity analysis.

Training examples are constructed from the same frozen question set across arms.
SFT uses direct targets: gold answers for known questions and abstention
phrases for unknown questions. DPO uses chosen/rejected pairs: gold answer over
abstention for known questions, abstention over the model's own hallucinated
sample for unknown questions. KTO uses desirable and undesirable single
responses, including anti-over-refusal signals where abstention on known
questions is undesirable.

The protocol includes leakage guards: probe/train questions must be disjoint
from the Cheng held-out test questions under normalized text, and train/dev
splits are grouped by normalized question text.

## 4. Methods

### 4.1 Training

All main training arms use identical LoRA budgets within model scale, with
method-specific learning-rate and beta defaults taken from shipped trainer
conventions. The v0.3 default matrix supplies headline runs. A separate
sensitivity panel varies learning rate for SFT, DPO, and KTO and beta for DPO
and KTO, but the panel is robustness-only and cannot supply headline numbers.

### 4.2 Evaluation

Primary behavioral metrics are truthful rate, refusal recall on unknown
questions, over-refusal on known questions, correctness on answered known
questions, answer-on-unknown rate, and capability retention. Calibration metrics
include token-level ECE on multiple-choice evaluation and confidence-ranked
answer metrics where available.

Evaluation domains include the held-out in-domain TriviaQA/Cheng surface and
OOD surfaces including SelfAware, KUQ, CoCoNot, AbstentionBench, MMLU, PopQA,
and TruthfulQA. Some local extension evidence below uses SelfAware and KUQ
because those were the completed, row-aligned local surfaces available at draft
time.

### 4.3 Statistics

The pre-registered analysis separates two sources of uncertainty:
within-run evaluation-question uncertainty via paired bootstrap over questions,
and across-seed training-stochasticity uncertainty via seed-level intervals for
headline arms. Between-arm binary outcomes are compared with matched-seed
McNemar tests.

[GATED: Insert final statistical outputs only after reconciling seed inclusion,
run identity, config identity, and scored-row availability.]

## 5. Results

### 5.1 Locked v0.3 Headline Results

[GATED: This section must be filled only from the signed v0.3 default matrix:
SFT, DPO, and KTO at pre-registered defaults, with required seed treatment and
the protocol's statistics. Do not import numbers from Amendment A, Amendment B,
mechanism diagnostics, smoke runs, bad-merge attempts, sensitivity cells, or
local exploratory summaries.]

Planned primary result table:

| Arm | Truthful rate | Refusal recall | Over-refusal | Correct known | Token ECE | Seed CI | Provenance |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Base | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] |
| SFT | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] |
| DPO | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] |
| KTO | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] | [GATED] |

Candidate headline interpretations to test after reconciliation:

- Whether SFT reliably induces abstention on unknown questions.
- Whether KTO reduces SFT over-refusal enough to satisfy H1.
- Whether DPO and KTO differ in calibration damage relative to SFT.
- Whether KTO beta or balance settings provide a monotonic operating-point dial
  under H4.

### 5.2 Local Cold-Start Pattern: SFT Induces Abstention, DPO/KTO Stay Base-Like

Claim tier: bounded local evidence; not v0.3 headline until reconciled.

The current local scaffold reports a consistent cold-start pattern on SelfAware
and KUQ. SFT from the base model induces refusal on unknown questions, but the
induced boundary is too broad and produces high over-refusal on known questions.
Cold-start DPO and KTO remain closer to the base model on refusal behavior in
the same local evidence.

Representative local numbers from the Phase 1 results skeleton:

| Surface | Arm | Truthful | Refusal recall | Over-refusal | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| SelfAware full | SFT | 39.51 | 89.73 | 66.07 | pre-grouped comparator |
| SelfAware full | grouped SFT | 37.99 | 83.82 | 64.18 | grouped-split rerun |
| KUQ balanced | grouped SFT | 51.82 | 97.92 | 82.29 | broader OOD slice |
| SelfAware full | base | 19.26 | 0.00 | 0.04 | local comparator |
| SelfAware full | DPO | 15.08 | 0.00 | 0.04 | local comparator |
| SelfAware full | KTO | 18.73 | 0.00 | 0.21 | local comparator |

Interpretation: SFT appears to teach an abstention policy, but not a calibrated
abstention boundary. Cold-start preference optimization does not yet appear to
be the mechanism that creates abstention behavior on this small-model local
slice.

[GATED: Reconcile these local numbers against run records and result inventory
before deciding whether any belong in the final manuscript body versus appendix.]

### 5.3 Amendment A Sequential Extension

Claim tier: signed Amendment A / v0.4 prospective extension only.

Amendment A tests a different hypothesis: preference optimization may work
better as boundary refinement after SFT has taught the model an abstention
routine. The sequential arms train DPO or KTO from a merged SFT model, with the
reference model also set to the merged SFT model.

Local SelfAware and KUQ transition analyses support a tradeoff rather than a
clean win. Sequential DPO sharply reduces known-question over-refusal but also
answers many unknown questions that SFT had correctly refused. Sequential KTO is
more conservative: it preserves more unknown refusal and loses fewer truthful
rows, but leaves more known-question over-refusal.

Representative row-aligned SelfAware seed-1 transition counts:

| Pair | Unknown SFT refusals lost | Known SFT refusals converted to answers | Known SFT refusals converted to correct answers | Truthful A not B | Truthful B not A |
| --- | ---: | ---: | ---: | ---: | ---: |
| `sft_merged -> sft_dpo` | 377 | 1113 | 95 | 429 | 145 |
| `sft_merged -> sft_kto` | 91 | 322 | 37 | 125 | 70 |

The three-clean-seed DPO SelfAware expansion reported mean local values of
52.81 refusal recall, 14.58 over-refusal, 25.38 correct-known, and 31.21
truthful. That aggregate includes a reconciliation note: one supplied
refusal-recall mean differed from the arithmetic mean in the report and must be
resolved before publication.

Interpretation: sequential preference training changes the operating point
after SFT. DPO is the aggressive over-refusal reducer and can overshoot; KTO is
the abstention-preserving follow-on and may under-correct over-refusal.

[GATED: Fill final Amendment A table only after seed inclusion, bad-merge
exclusion, and row-level provenance are reconciled.]

### 5.4 Amendment B Stated-Confidence Extension

Claim tier: unsigned stated-confidence prompt-contract evidence only.

Amendment B adds a JSON answer/confidence output contract. The measurement
result is itself important: an earlier schema that exposed an explicit
answer/abstain decision enum induced base-model over-refusal on the smoke slice.
The final answer/confidence-only schema preserved the base-model behavioral
shape while keeping confidence coverage near 100%. This means stated-confidence
results should be compared within the same prompt contract and not substituted
directly for earlier plain-answer evaluations.

Three-seed local SelfAware stated-confidence summary:

| Arm | Refusal recall | Over-refusal | Correct known | Truthful | Confidence coverage | Mean stated confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| merged SFT | 73.323 | 48.137 | 41.060 | 37.143 | 99.940 | 0.417 |
| `SFT -> DPO` | 37.890 | 11.683 | 25.553 | 27.260 | 99.840 | 0.760 |
| `SFT -> KTO` | 65.730 | 34.417 | 33.433 | 35.333 | 99.920 | 0.500 |

Interpretation: under this prompt contract, sequential DPO becomes much more
confident while reducing over-refusal and losing many unknown refusals.
Sequential KTO preserves more of SFT's refusal behavior and raises confidence
less. These are local prompt-contract results, not v0.3 headline results.

### 5.5 Exploratory Mechanism Diagnostics

Claim tier: exploratory mechanism evidence only.

Hidden-state diagnostics on balanced 128 known / 128 unknown slices show a
behaviorally suggestive pattern. SFT active-adapter and LoRA-delta states show
stronger known/unknown separability than cold-start DPO/KTO. Sequential DPO/KTO
use merged SFT as the base, so their base states already contain the SFT shift;
their sequential deltas preserve high separability.

Representative diagnostic probe results:

| Arm | Best `h_base` | Best `h_lora` | Best `delta` | Caveat |
| --- | ---: | ---: | ---: | --- |
| SFT | 0.753906 L25 | 0.863281 L36 | 0.855469 L35 | original Qwen base |
| DPO | 0.753906 L25 | 0.773438 L35 | 0.750000 L35 | original Qwen base |
| KTO | 0.753906 L25 | 0.765625 L36 | 0.750000 L26 | original Qwen base |
| `sft_dpo` | 0.843750 L36 | 0.855469 L34 | 0.859375 L35 | merged SFT base |
| `sft_kto` | 0.843750 L36 | 0.859375 L35 | 0.855469 L36 | merged SFT base |

The first causal-pilot smoke on the SFT `h_lora` layer-36 known/unknown
direction was an initial null for behavior. The hook applied a large vector and
changed logits, but greedy generation and greedy next-token top-1 did not
change on the tested smoke rows, even at high coefficient. This narrows the
mechanism hypothesis but does not rule it out.

Interpretation: SFT may create or expose a known/unknown representation that
cold-start preference training does not create in the same way. That statement
remains correlational. The causal evidence so far is a narrow null for one
intervention design, not evidence that no mechanism exists.

## 6. Sequential Extension

The sequential extension is best framed as a second experimental question, not
as a rescue of the original hypothesis after seeing results. The signed
Amendment A premise is prospective: if SFT is required to teach the abstention
routine, then DPO and KTO should be tested as second-stage boundary refiners.

The useful scientific output is a tradeoff curve. DPO appears to push strongly
against refusal, which can recover some known answers but also discards useful
unknown abstentions. KTO appears to push less strongly, preserving abstention
but leaving a larger over-refusal tax. The next recipe question is therefore
not whether preference optimization "works" in the abstract. It is how much
preference pressure should be applied after SFT and whether that pressure can be
tuned without collapsing the unknown-question refusal learned in stage one.

[GATED: Decide whether this section remains an extension in the main text, moves
to an appendix, or becomes part of a later signed v0.4 manuscript after
protocol-level decision.]

## 7. Exploratory Mechanism Diagnostics

The mechanism section should remain modest. The current evidence can motivate
candidate hypotheses:

- SFT creates a stronger known/unknown readout in late-layer hidden states.
- Cold-start DPO/KTO do not produce the same active-adapter separability on the
  initial local slice.
- Sequential preference training operates on an SFT-shaped representation
  rather than creating the initial separability from scratch.
- A simple final-prompt-token activation addition/subtraction intervention on
  the SFT layer-36 direction did not change greedy behavior in the first smoke.

The mechanism section should not claim that abstention has been internalized,
that a causal refusal direction has been found, or that hidden-state probes are
valid reward signals. Those would require a later signed protocol revision and
stronger causal controls.

## 8. Limitations and Reproducibility

The main limitation of this draft is provenance state. Several candidate
results are useful for manuscript structure but not yet publication-grade. The
final manuscript must reconcile run records, materialized recipes, scored rows,
config identities, excluded runs, and seed inclusion before promoting any
number.

Other limitations:

- Small open-model setting; Qwen3-4B is the main local evidence base.
- Sequential evidence is Amendment A, not locked v0.3 headline evidence.
- Amendment B stated-confidence results are prompt-contract dependent.
- Some OOD surfaces are better suited for refusal/over-refusal pressure than
  exact correctness transitions.
- Mechanism diagnostics are local, small-slice, and mostly correlational.
- The bridge arm and 8B confirmation must be handled according to their
  protocol status before final claims.

Reproducibility commitments:

- Report exact run IDs, config paths, adapter identities, seed treatment, and
  scored-row availability for every table.
- Preserve raw generations and compact scored rows where allowed.
- Keep sensitivity-panel cells out of headline tables.
- Keep restricted or license-gated artifacts out of redistributed outputs.
- Release scripts and manifests needed to recompute all manuscript tables.

## 9. References

[TODO: Build Paper 2 reference list from Paper 1 bibliography, protocol
references, and cited method papers. Do not copy unverified citation metadata.
Likely required entries include Cheng et al. on IDK training, Rafailov et al. on
DPO, Ethayarajh et al. on KTO, Guo et al. on calibration, Qwen3 model
references, TriviaQA, SelfAware, KUQ, CoCoNot, AbstentionBench, MMLU, PopQA,
TruthfulQA, and the Paper 1 synthesis.]
