# Research Trajectory — Epistemic Humility Program

> **SUPERSEDED 2026-07-03:** the living trajectory is now
> [`docs/research-trajectory.md`](../../../docs/research-trajectory.md). This file is the
> historical staged plan, preserved as a record.

Captured 2026-06-10 from the trajectory conversation. This is the staged
plan that paper 1's §8 will announce and the experiment program executes.
Each phase consumes the previous phase's artifacts.

> **The Phases 1-4 plan below is the original staged design and is preserved as
> the historical record.** For where the program ACTUALLY is, read the update
> immediately below first; it supersedes the dated Publication-shape, Open-decisions,
> and Status sections at the foot of this file.

## Update 2026-06-30 — where the program actually is

> **Numbering note (2026-07-01, second re-steer):** the intermediate four-paper
> RENUMBER (which briefly made this section's labels stale) was itself superseded by
> the five-paper line in "Publication shape" below. Under the five-paper line this
> section's labels are correct as written: Paper 3 = "Knows but Doesn't Say",
> Paper 4 = two-signal readout. File paths updated to the renamed drafts.

The big empirical move since 2026-06-10: the program ran Phase 1, then pivoted into
the Phase 3 mechanism line, and that mechanism work — not the training three-way — now
carries the headline.

- **Phase 1 executed and merged** (full SFT/DPO/KTO pipeline, PR #1, on `main`).
  Model pinned to Qwen3-4B (local) / 8B (cloud), thinking OFF, as planned.
- **Paper 3 — "Knows but Doesn't Say"** (drafted, `papers/paper-3-knows-but-doesnt-say/manuscript.md`):
  the model represents what it does not know on an internal axis (answerability AUROC
  0.997) while its STATED confidence is decoupled (0.52-0.56) and TRAINING-RESISTANT —
  the gap survives DPO, KTO, GRPO v1/v2/v3, and contrastive SFT. Steering relaxes
  over-refusal but cannot install abstention (asymmetric control). This reframes the
  training three-way: preference/RL training moves behavior but does not open the
  internal->stated channel.
- **The two-signal readout (Paper 4, working)** — the current headline thesis:
  *epistemic state in a small LM is largely a READOUT, not a training outcome.* Two
  orthogonal linearly-decodable axes — an answerability **gate** (read at the prompt
  anchor) and a per-answer correctness **dial** (read post-generation) — compose into a
  deployable two-stage trust pipeline, and the correctness dial **vetoes** confident
  hallucinations. Established across Amendments O/P/Q (probe-as-oracle ceiling +
  through-engine replication), S/T (post-gen correctness readout, 0.834 / 0.819), U
  (hallucination veto 0.980), Stage 1.5 (orthogonality — fusing the scalars HURTS), and
  **W (the whole mechanism reads off the RAW base with no task training**: gate 0.997 /
  dial 0.834 / veto 0.754; training only SHARPENS the veto to 0.980). Synthesis:
  `papers/paper-4-two-signal-readout/notes/framework.md`; atomized into the KG as
  `paper:internal-twosignal` + `paper:internal-paper3` and six mechanism atoms. Runnable
  family spec: `archive/notes/experiments/two-signal-readout.md`.
- **Gap status.** Gap 4 (probe-transfer of humility) is RESOLVED in the strong form: the
  answerability axis transfers cross-dataset (Amendment P, KUQ->SelfAware 0.983) and the
  readout works training-free. Gaps 6/7 (small-model + cross-model coverage) are being
  addressed now by **Amendment X** (cross-SIZE generalization within Qwen3: 1.7B/8B/14B;
  `experiments/cross-model-size-sweep/AMENDMENT.md`). Cross-FAMILY
  (Llama/Mistral/Gemma) remains the next generalization axis.
- **Deliverable reframe.** The product the program targets — a surfaced, thresholdable
  trust number that tracks whether THIS answer is correct — does NOT require us to train
  it in; it is a readout. "Training is not needed for the readout" is the headline, with
  the honest nuance that training sharpens the veto.

Episodic record of this arc: `docs/sessions/20260630T180842Z-two-signal-readout-arc-s-t-u-w-cross-size-generalization-amendment-x.md`. The Phases 1-4 staged plan below
remains the canonical description of the training-study spine (Papers 2's core).

## Anchor

The meta-analysis (paper 1) verified these gaps; the program is built to
close them in order of leverage:

1. No KTO-for-abstention study exists (gap 1).
2. No SFT/DPO/KTO three-way comparison exists (gap 2).
3. The recall/over-refusal decomposition is almost never reported (§5.3).
4. The central tension — preference training improves abstention while
   damaging calibration — has never been measured on the same training run.
5. No IDK-fraction dose-response curve exists for epistemic abstention
   (gap 5; the Bianchi curve exists only for safety refusal).
6. Probe-transfer of trained humility is untested (gap 4).
7. Small-model and OOD-transfer coverage is thin (gap 6).

## Dataset strategy: reuse the Cheng recipe, not the Cheng labels

- Cheng et al. (2401.13275) is the anchor: released outputs (reanalyzed
  exactly), test set identified as TriviaQA unfiltered.nocontext/validation
  (100% question match), gold aliases staged locally
  (`datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl`).
- Known/unknown splits are model-specific by construction → regenerate
  labels for our model with their correctness-probing method.
- Mandatory improvement from paper 1's findings: probe with a higher
  sample count than their 10 and run a label-noise sensitivity analysis
  (we measured 43-51% of their "unknown"-labeled questions answered
  correctly).

## Model strategy

- Pin a current open-weights family with a small and a mid size at
  experiment kickoff, then freeze. Criteria: open weights, chat variant,
  two sizes (~3B pilot + ~7-8B confirm), stable HF support. Repo tooling
  currently targets Qwen2.5-3B/7B; substitute the newest equivalent
  generation at kickoff (user note: Llama-2-era models are stale/overused;
  apples-to-oranges vs prior work is acceptable because comparisons are
  within-model across methods).
- PIN DECISION (2026-06-10, frozen for Phase 1 / paper 2): Qwen3, namely
  Qwen3-4B-Instruct (pilot, local RTX 3090) and Qwen3-8B-Instruct (confirm,
  HF Jobs), both Apache 2.0, ungated, text-only; thinking mode pinned OFF
  (enable_thinking=False). Rationale: the only current family that is at once
  text-only, uniformly Apache and ungated, and a near-exact 4B/8B pairing.
  Full survey: `docs/preparation/model-landscape.md`.
- Bridge arm (recommended, pending user confirmation): one replication of
  Idk-SFT + Idk-DPO on Llama-2-7b-chat itself to validate the pipeline
  against Cheng's published numbers before running novel arms on the
  modern model.
- Long-term: the pipeline is re-runnable on any open model (Phase 4).

## Phase 1 — the three-way (paper 2 core)

SFT vs DPO vs KTO on model-specific IDK data, same base model, same data
budget. Fills gaps 1+2 in one design.

Measure everything the literature splits apart, after the same run:
- refusal recall AND over-refusal/abstention precision (the decomposition)
- truthful rate
- token-level ECE / calibration (first study to measure the
  abstention-calibration tension on a single run; KTO unmeasured on both)
- OOD transfer: KUQ, CoCoNot, AbstentionBench subsets (all already local)

Infra: 3B pilot on RTX 3090 (`tuner.py local-run`), 7-8B confirm on HF
Jobs. KTO data per `.skills/fine-tuning/reference/dataset-formats.md`
(interleaving requirement).

## Phase 2 — dose-response and data composition

(a) IDK-fraction sweep on best Phase-1 method + SFT → the field's first
    abstention-precision/over-refusal Pareto curve (gap 5).
(b) C3 boundary-condition test set up by our AbstentionBench reanalysis:
    abstention-targeted SFT vs general SFT mix → is over-refusal a
    data-composition property rather than a method property?
(c) KTO-only ablation no other method supports: desirable/undesirable
    balance is a free knob (unpaired binary labels). First ablation =
    congruence-vs-correctness mapping tension documented in
    `rewardcal-kto-recipe.md` (R1).

## Phase 3 — mechanism

- Protocol pointer (2026-06-19): Phase 3 mechanism/control-system work is now
  governed as `OFFICIAL EXPLORATORY PROTOCOL`, draft v0.1, in
  `docs/protocols/phase3/control-system-protocol.md`. This is separate
  from signed Phase 1 `PROTOCOL.md` v0.3 and amendments unless later promoted
  by explicit signed revision.
- Probe for an "I don't know" direction before/after each training method;
  test whether the probe transfers OOD when behavior does not (gap 4; the
  essay's "form of ignorance without the substance" made empirical).
- Future implementation planning for the LoRA/hidden-state activation tier is
  tracked in `docs/plans/lora-hidden-state-probing-tier.md`; it is exploratory
  mechanism work and does not modify either the locked PROTOCOL v0.3 headline
  matrix or the signed Amendment A / v0.4 prospective sequential-extension
  track.
- Toolkit: raw report 06's probing line (Azaria-Mitchell, CCS, ITI,
  semantic-entropy probes); caution from 2606.02907 (probes can detect
  task format, not reasoning mode) and the TPR-gaming result (probes
  inside RL reward loops get gamed).
- R2 slots here: run HINT-lab PPO-M/PPO-C checkpoints through our
  abstention suite (does reward calibration transfer to abstention?).

## Phase 4 — generalization program (rolling)

- Cross-architecture re-runs of the full pipeline (model-specific labels +
  three-way training + full metric decomposition) as a rolling result;
  release harness + per-model labels + outputs (the reproducibility
  behavior paper 1 documents the field lacking — only ~5 of 31 corpus
  studies released usable artifacts).
- Sycophancy axis: S1 join was a verified negative (n=1 overlap), so
  construct it ourselves — apply Sharma's 4 mechanical framings
  (none / correct-given / incorrect-given / correct-doubted) to our
  knowledge-labeled questions: does capitulation concentrate at the
  knowledge frontier? (Forward paths documented in
  `evidence/sycophancy-cheng-join.md`.)
- Thinking vs non-thinking axis (REGISTERED 2026-06-10, future material, not
  designed yet): Phase 1 pins the Qwen3 thinking toggle OFF for a clean
  non-reasoning study. The toggle is a free, controlled axis: re-run the
  three-way abstention training (or at least the eval suite) with
  enable_thinking=ON vs OFF on the same Qwen3 model. Question: does an
  explicit reasoning trace change where the knowledge frontier sits, whether
  abstention training transfers, and the abstention-calibration tension
  (does a `<think>` trace let the model verbalize uncertainty it cannot
  express in a direct answer)? This is also an agentic metacognition axis:
  uncertainty should help decide when to search and what to trust
  (Yona, Geva, and Matias, "Hallucinations Undermine Trust; Metacognition is a
  Way Forward," arXiv:2605.01428). This connects to the Phase 3 probing line
  and the 2606.02907 caution that probes can detect task format rather than
  reasoning mode. Reasoning-by-default modern families (e.g. Qwen3.5) are
  the natural cross-architecture extension of this axis in the Phase 4
  rolling re-runs.

## Publication shape

Original (2026-06-10): Paper 2 = Phase 1; Paper 3 = Phases 2+3; Phase 4 = artifact.
Revised (2026-06-30): Paper 2 = training three-way; Paper 3 = "Knows but Doesn't Say";
Paper 4 = two-signal readout.

**RE-RENUMBERED (2026-07-01, second user steer — supersedes all above).** After
seeing the unified draft-v2 (synthesis + regimen + confidence/probe arc in one
paper), the user reversed the fold-in: the program is a **FIVE-paper line**, and
this numbering is canonical. Draft files were renamed to match on 2026-07-01
(git mv) and draft-v2 was split (Part I back out as Paper 1; §7–8 depth out to
Paper 3; stacks compressed to a one-sentence null per user direction — "we warm
with SFT then do DPO, KTO, GRPO; that's the paper").

- **Paper 1 = literature review / taxonomy / theoretical framework.** The
  meta-analysis returns to standalone status as the program's framing paper:
  Depths-of-Ignorance taxonomy, claim families C1–C5, six-gap analysis, plus the
  policy-vs-signal framework (three testable propositions) that generates the
  program's agenda. Draft: `papers/paper-1-taxonomy-framework/manuscript.md`;
  source of record: `meta-analysis/paper/draft-v0.md` (un-archived as such).
- **Paper 2 = the training-regimen paper.** The controlled SFT/DPO/KTO/GRPO
  comparison: cold-start failure of bare non-SFT arms (3 seeds), SFT-warmed
  DPO/KTO repositioning (3 seeds), GRPO amplification (single seed, exploratory,
  labeled). Mix-and-match stacks reported as a one-sentence null only. Ends on the
  confidence-tracks-the-decision bridge + forward pointer to Paper 3. Drafts:
  `papers/paper-2-training-regimen/manuscript.md`; superseded v0/v1 drafts are
  archived under `archive/papers/paper-2-training-regimen/drafts/`.
  Figures `fig-p1-*` (legacy prefix), generators
  `papers/paper-2-training-regimen/scripts/build_figures.py` and `build_paper1_v2_figures.py`.
- **Paper 3 = "Knows but Doesn't Say."** The internal-vs-stated confidence gap and
  its training-resistance — including that even GRPO (and a proper-scoring reward,
  and contrastive SFT, per the depth moved in from the old draft-v2 §7–8) does not
  couple the channels — plus the steering asymmetry. Mechanism *diagnosis*. Draft:
  `papers/paper-3-knows-but-doesnt-say/manuscript.md`. Figures `fig-p2-*`
  (legacy prefix), generator `papers/paper-3-knows-but-doesnt-say/scripts/build_figures.py`.
  (KG node `[[internal-paper3--knows-but-doesnt-say]]` keeps its legacy slug.)
- **Paper 4 = the two-signal readout.** The training-free answerability-**gate** +
  correctness-**dial** + hallucination-**veto** pipeline; cross-SIZE (Qwen3
  1.7–14B), cross-FAMILY confirmatory (SUCCESS), and seed-robust under sampled
  decode (Amendment SR, PR #141). Mechanism *solution* / current headline.
  STANDALONE; cites Paper 3 for the diagnosis. Draft:
  `papers/paper-4-two-signal-readout/manuscript.md`; figures `fig-p3-*`
  (legacy prefix), generator `papers/paper-4-two-signal-readout/scripts/build_figures.py`.
- **Paper 5 = steering** (next phase, not yet run). Turn the probe direction around
  from READING to WRITING — activation steering + CoT injection — as a causal test
  of the anchor-vs-end account. Design: `docs/plans/confidence-steering-experiment.md`;
  scaffold parked on the historical confidence-steering branch.
- Phase 4 program work = ongoing infrastructure / community artifact (unchanged).

**Figure/script prefixes are legacy:** `fig-p1-*`/`build_paper1_*` belong to
Paper 2, `fig-p2-*`/`build_paper2_*` to Paper 3, `fig-p3-*`/`build_paper3_*` to
Paper 4. They are referenced from amendment docs and run records and are NOT
renamed; the mapping above is the truth.

**Amendment enumeration:** the reader-facing papers present ONE clean narrative and do
NOT enumerate the internal amendment labels (S/T/U/W/X/Z/O/P/Q/R/SR). Amendment→result-JSON
traceability lives in a methods/provenance appendix, not the prose.

## Open decisions (user)

1. ~~Model family pin~~ — RESOLVED 2026-06-10: Qwen3-4B / 8B, thinking OFF (see Model
   strategy PIN DECISION).
2. ~~Llama-2-7b-chat bridge arm~~ — RESOLVED: in; Llama-2 gated access granted
   2026-06-10 (2 bridge cells in the locked matrix).
3. How much Phase 2 rides along in Paper 2 (still open).
4. ~~KTO label mapping~~ — RESOLVED: correctness-safe = the same four rows as
   congruence, a weights-only 2.0/1.0 ablation (ADR §4.6).
5. NEW (open): cross-FAMILY generalization (Llama/Mistral/Gemma) for the readout, and
   promotion of any exploratory readout result to a headline claim via a pre-registered
   replication — registered before running.

## Status

- Phase 1 pipeline merged to `main` (PR #1). Paper 3 drafted; the two-signal readout
  arc (Amendments O/P/Q/S/T/U/Stage-1.5/W) complete on Qwen3-4B and atomized into the KG.
- In flight: Amendment X (cross-size readout generalization, 1.7B/8B/14B) — gates locked,
  pipeline GREEN, sequential extraction running.
- Paper 1 §8 is stubbed; v0 text parked at
  `archive/docs/protocol/future-work-section-v0.md`.
- Pre-register hypotheses/amendments in governed experiment records before any run (held).
