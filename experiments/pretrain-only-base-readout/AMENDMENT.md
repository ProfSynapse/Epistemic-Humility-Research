---
amendment: Y
slug: pretrain-only-base-readout
question: >-
  Does the knowledge-boundary signal predate post-training, i.e. is it
  present on pretrain-only base models, not just instruct checkpoints?
predictions:
  orchestrator:
    call: >-
      pretraining-origin supported; base gate near-ceiling, veto present
      pre-post-training
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  COMPLETE — H_B1 SUPPORTED 4/4 (boundary signal predates post-training);
  H_B2 veto SUPPORTED 4/4; H_B3 sharpening NOT SUPPORTED (post-training does
  not sharpen, can dull the readout).
scoreboard: null
---

# Protocol Amendment Y: Pretrain-Only Base-Model Readout (Era / Origin Test)

**Status:** SIGNED 2026-07-02 (user in-session approval; launch approval
SEPARATE and not yet given — see §8)

**Short name:** Amendment Y / base-readout

**Scope:** Runs the identical two-signal readout (answerability gate,
correctness dial, hallucination veto) on *pretrain-only* base models — paired
against their vendor-instruct siblings (Arm A, gated) and across model
generations (Arm B, descriptive) — to test whether the knowledge-boundary
signal predates post-training. Every prior "training-free" result (S/T/U/W/X/
Z/SR) was measured on vendor-post-trained instruct checkpoints; the
pretraining-origin claim in the papers is currently untested in both
directions. Design capture: `docs/plans/base-model-era-readout.md`.

**Session note:** `docs/sessions/20260701T115938Z-paper-reorg-sr-seed-robustness-steering-scaffold-merge.md`

---

## 1. Rationale

The program's closing claim (regimen paper §8 / readout paper framing) is that
the internal knowledge-boundary signal "is already paid for by pretraining."
The supporting evidence never isolated pretraining: Amendment W's "raw,
untrained base" is `Qwen3-4B` **Instruct** (vendor SFT/RLHF included, merely
free of *our* adapters), and X/Z/SR likewise used instruct variants.
"Training-free" so far means *our*-training-free, not post-training-free.

Kadavath et al. (2022) and the GPT-4 report suggest pretrained models are
token-level well-calibrated and post-training damages that channel. If the
linear hidden-state boundary signal shows the same pattern (present before
post-training), the pretraining-origin claim locks. If base models read near
chance while instruct siblings read ~0.99, the two-signal program is a
post-training readout and the papers' framing must be revised. Either outcome
is publishable; the claim is unsupported either way today. This is a genuinely
new evidence cell with a distinct mechanistic question (signal *origin*), not a
knob tune on a prior amendment — hence a new letter.

## 2. Relationship To Existing Protocols

- **Additive.** Does not touch the locked v0.3 headline matrix, PROTOCOL.md
  hypotheses, or any signed amendment. No goalposts move on W/X/Z/SR; their
  results stand as instruct-checkpoint results.
- Reuses the Amendment X extraction + scoring machinery
  (`amendment_x_cross_model_extract.py`, gate/dial/veto scoring) and W's dial
  bar (AUROC >= 0.65) and SR's adequacy-gate concept (underpowered cell =
  INELIGIBLE, not negative).
- If H_B1's falsifier fires, the *interpretation* sections of the regimen and
  readout papers are revised in a governed edit; no locked numeric claim
  changes.

## 3. Design Change

**Arm A — paired base-vs-instruct contrast (primary, gated).** Same family,
same size, same pretraining corpus; the only delta is vendor post-training.
Identical extraction + gate/dial/veto scoring on both siblings:

Model list web-verified 2026-07-02 (user directive: most current base models,
not training-data-era defaults; see the refresh section of the design doc):

| Pair | Base | Instruct | Anchor |
|---|---|---|---|
| Qwen3.5-4B | `Qwen/Qwen3.5-4B-Base` | `Qwen/Qwen3.5-4B` | Z/SR/AA — exact base sibling of the steering checkpoint; priority pair |
| Gemma-4-E4B | `google/gemma-4-E4B` (pt) | `google/gemma-4-E4B-it` | Z/SR |
| Llama-3.2-3B | `unsloth/Llama-3.2-3B` (ungated base mirror) | `Llama-3.2-3B-Instruct` | Z/SR |
| Olmo-3-7B | `allenai/Olmo-3-1025-7B` | `allenai/Olmo-3-7B-Instruct` | new — fully open (Apache 2.0), publishes the full base→instruct training flow |

(Ministral-3-3B, the fourth Z family, has NO true base checkpoint on the hub —
Instruct/Reasoning variants only — so it cannot be paired and is excluded from
Arm A. Recorded here so its absence is not read as a post-hoc drop.)

**Arm B — era ladder (exploratory, descriptive, NO gate).** Pretrain-only
models across generations at small-viable scale: `gpt2-xl` (2019),
`pythia-2.8b` (2023), `Llama-2-7B` base (2023, access granted 2026-06-10),
`OLMo-2-7B` base (2025), topping out at the current generation via the Arm A
bases (`Olmo-3-1025-7B`, `Qwen3.5-4B-Base`, 2026 — no rerun; reused as top
rungs). Reported as a curve with adequacy flags only.

**Hypotheses / gates (frozen at sign-off):**

- **H_B1 (pretraining-origin, PRIMARY):** on each Arm A base model, the
  answerability gate reads AUROC >= 0.90 on the SelfAware anchor; pass on
  >= 3/4 Arm A bases.
  **Falsifier:** base gate < 0.75 while its instruct sibling >= 0.95 on that
  model-pair's rows, on >= 3/4 pairs → post-training *creates* (not sharpens)
  the signal → papers' origin framing revised; no goalpost move.
- **H_B2 (veto exists pre-post-training):** base-fit dial ranks base-model
  hallucinations below base-correct answers at AUROC >= 0.65 (W's bar) on
  >= 3/4 Arm A bases.
- **H_B3 (sharpening, expected, report-only):** instruct-minus-base veto delta
  > 0 per pair. No pass/fail.
- **Adequacy gate (pre-stated, SR-style):** a cell needs minimum row counts
  (correct and hallucination classes) to be scoreable; numeric minimums frozen
  at sign-off (proposed: >= 50 correct and >= 50 wrong/hallucination rows).
  A cell below the floor is INELIGIBLE, excluded from H_B1/H_B2 denominators.

**Decode:** greedy (X/Z convention). Sampled-decode robustness is NOT folded
into this registration.

**Known confound (stated up front):** base-vs-instruct pairs can differ in
more than post-training (annealing data, long-context stages). This is the
cleanest available contrast, not a perfect ablation; the writeup must say so.
This amendment does NOT test whether post-training *damages* the signal (that
needs matched pre/post checkpoints of one run, e.g. OLMo/Tulu intermediates —
future work).

## 4. Rerun / Launch Requirement

- **Reusable:** instruct-side extractions already on disk from Amendment Z
  (greedy: `Qwen3.5-4B`, `Llama-3.2-3B-Instruct`, `gemma-4-E4B-it`) IF decode
  and prompt config are identical to this amendment's cells; verify config
  equality per-cell in the run record rather than assuming.
- **New runs required:** all base-model cells (both arms) plus ONE new
  instruct cell (`Olmo-3-7B-Instruct`, no prior extraction). Known/unknown
  labels regenerate per model (X convention) — no label reuse across models.
  New GPU cells: 4 Arm A bases + 1 Olmo instruct + 4 Arm B historical rungs
  = 9 (+1 optional descriptive sub-cell below).
- Old artifacts cannot answer the base-model question at all; there is no
  base-model extraction anywhere in the archive.

## 5. Metrics And Interpretation

Gate/dial/veto AUROCs exactly as X/Z/SR define them. Interpretation rules:

- H_B1 pass on >= 2/3 Arm A bases with no falsifier fire → the boundary
  signal predates post-training (origin claim supported on these families).
- Falsifier fire on >= 2/3 pairs → post-training creates the readout; papers'
  framing revised.
- Mixed / mid-zone results (e.g. base gate 0.75–0.90, or pass/falsifier each
  on fewer than 3/4 pairs) are reported as ambiguous. No post-hoc threshold
  adjustment.
- Arm B is descriptive only; no claim may be minted from the era curve
  without a later confirmatory registration.
- All results are exploratory amendment evidence: never pooled with the v0.3
  headline, reported separately.

## 6. Implementation Boundary

- Extractor change: a **backward-compatible base-mode prompting path** in
  `experiments/common/readouts/amendment_x_cross_model_extract.py` — no chat
  template, fixed k-shot QA block, plain completion parsed at first line
  after the answer cue. Flag **default off** so X/Z/SR cells reproduce
  byte-for-byte. Probe-layer rule for odd geometries (GPT-2): depth fraction
  ~0.55 rounded (X convention), stated before running.
- **Prompting-surface rule (pre-stated):** ALL base cells (both arms) use the
  base-mode k-shot surface uniformly, even where a base checkpoint happens to
  ship a chat template (Qwen3.5-4B-Base does); instruct cells use the chat
  template (X/Z convention). The base-vs-instruct contrast therefore differs
  in prompt surface as well as weights — named confound, echoing the
  anchor-vs-end surface lesson from Amendment AA. **Optional descriptive
  sub-cell (report-only, no gate):** `Qwen3.5-4B-Base` rendered BOTH ways
  (k-shot and its shipped chat template) to measure how much of any
  base-instruct gap is prompt surface rather than weights.
- No `synaptic-tuner/` writes; this line is extraction + scoring only, no
  training.
- Base checkpoints pulled to the HF cache; Llama-2 base is gated (access
  already granted, via HF_TOKEN) — do not redistribute weights or gated data.
- **Lane:** cloud HF Jobs is the registered primary lane — one A10G job per
  cell in parallel, via the tracked wrapper
  `experiments/common/cloud/hf_jobs_cell.sh` (clone public repo at a
  pinned commit → extract → score → upload only the small result JSON +
  manifest to `professorsynapse/epistemic-humility-cloud-results`; tracked
  gate-rows pool `experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl`).
  Plumbing validated by the 2026-07-02 Qwen3.5-0.8B-Base smoke (lab-notebook
  instrument). Local single-GPU Docker (dgpu) is the fallback lane
  (~9 cells × 1.5–2h → 2–3 overnight queues) if cloud misbehaves.

## 7. Launch And Reporting Rules

- **Branch discipline:** this amendment gets its OWN branch off up-to-date
  `main` AFTER the in-flight Amendment AA PR merges (one amendment = one
  branch = one merged PR at a time). This draft is not committed on the AA
  branch; the cloud-lane wrapper/pools land separately on
  `cloud-lane-y-smoke` (infrastructure, not evidence).
- **Sign-off before anything runs.** The extractor base-mode change may be
  built and CPU/GPT-2 smoke-tested pre-registration (lab-notebook work), but
  no evidence cell runs before this document is SIGNED OFF.
- **Launch approval is separate from sign-off** and must name exact
  cells/models/lane (single local GPU; no parallel GPU cells; no overnight
  queue without explicit approval).
- Every cell gets a run record; results labeled `amendment-y` exploratory;
  session-note checkpoints per milestone.
- **Paper fit (decided at sign-off, user 2026-07-02):** NO standalone paper.
  Y's results fold into the existing program papers. Effective immediately
  (pre-result, user-directed), the regimen paper's §8 "already paid for by
  pretraining" strategy reading is downgraded from claim to OPEN QUESTION,
  with Amendment Y named as the registered instrument that answers it in
  either direction. Y's results then answer that question in the paper text.

## 8. Sign-Off Checklist

- approval date: 2026-07-02 (user in-session: "Overall amendment sounds good
  I think we add this into the paper and becomes a question in paper 1
  instead of a claim")
- approved scope: Arm A paired base↔instruct contrast (4 pairs, gated) +
  Arm B era ladder (descriptive, no gate) + optional Qwen3.5-4B-Base
  dual-render sub-cell (report-only); results fold into program papers, no
  standalone; regimen-paper §8 origin claim downgraded to open question at
  registration (user-directed, pre-result)
- approved cells/seeds/lane: 9 new GPU cells (+1 optional dual-render) —
  Arm A bases `Qwen3.5-4B-Base`, `gemma-4-E4B` (pt), `unsloth/Llama-3.2-3B`,
  `Olmo-3-1025-7B`; new instruct `Olmo-3-7B-Instruct`; Arm B rungs `gpt2-xl`,
  `pythia-2.8b`, `Llama-2-7B`, `OLMo-2-7B`. Single seed 20260630, greedy
  (X convention). Lane: cloud HF Jobs primary (wrapper + pools on
  `cloud-lane-y-smoke`; plumbing smoke GREEN 2026-07-02, job
  6a463f46fb6818a83db30027), local dgpu fallback. LAUNCH APPROVAL SEPARATE:
  no evidence cell runs until the user names cells + lane in-conversation.
- excluded cells/seeds: Ministral-3-3B (no true base checkpoint on the hub);
  sampled-decode robustness (not folded into this registration); any
  pre/post-damage intermediate-checkpoint arm (future amendment; OLMo 3
  publishes the needed checkpoints)
- schema/metric definitions frozen: gate/dial/veto AUROCs exactly as
  X/Z/SR define them (`amendment_x_cross_model_score.py`); prompting-surface
  rule per §6 (all bases k-shot base-mode; instruct chat-template)
- adequacy-gate row minimums frozen: >= 50 correct AND >= 50
  wrong/hallucination rows per cell; below floor = INELIGIBLE (excluded from
  H_B1/H_B2 denominators), never a negative

## 9. Result — fleet COMPLETE 2026-07-02, H_B1 SUPPORTED 4/4

All 10 evidence cells scored (9 cloud A10G + OLMo-2-7B run locally on the 3090
after two cloud preemptions benched the cloud cell; identical extractor,
engine `tuner-batched`, seed 20260630, greedy). Every cell clears the adequacy
floors by wide margins (min class count 234; floor 50). Per-cell artifacts:
`papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_y_results/`.

### Arm A — paired base-vs-instruct (gated)

| Cell | best L | gate | dial | veto | within-SA ctrl |
|---|---|---|---|---|---|
| Qwen3.5-4B-Base (r3, k-shot) | 17 | 0.9984 | 0.8725 | 0.6657 | 0.6196 |
| Qwen3.5-4B-Base (chat-render control) | 21 | 0.9977 | 0.8511 | 0.8672 | 0.7961 |
| Gemma-4-E4B (pt, r2) | 24 | 0.9975 | 0.8633 | 0.8743 | 0.7824 |
| Llama-3.2-3B (base) | 14 | 0.9972 | 0.8235 | 0.8354 | 0.7712 |
| Olmo-3-7B (base) | 17 | 0.9975 | 0.8442 | 0.8029 | 0.7912 |
| Olmo-3-7B-Instruct | 21 | 0.9979 | 0.8103 | 0.7306 | 0.6741 |

- **H_B1 (pretraining origin, PRIMARY): SUPPORTED 4/4.** Every Arm A base
  reads the answerability gate at 0.997+ (bar 0.90 on >= 3/4). The falsifier
  (base < 0.75 while instruct >= 0.95) fires on 0/4 pairs. The boundary
  signal predates post-training on all four families.
- **H_B2 (veto pre-post-training): SUPPORTED 4/4.** Base-fit veto 0.666
  (Qwen3.5, marginal — mirrors its Z greedy margin) / 0.874 (Gemma) / 0.835
  (Llama-3.2) / 0.803 (Olmo-3); bar 0.65 on >= 3/4.
- **H_B3 (post-training sharpens, report-only): NOT SUPPORTED — deltas <= 0
  on every pair.** The clean within-Y pair (Olmo-3 base->instruct, same seed
  and scorer) moves veto 0.803 -> 0.731 and within-SA control 0.791 -> 0.674.
  Z-anchored instruct siblings (greedy) sit at or below their Y bases too
  (Qwen3.5 0.666 vs 0.666; Gemma 0.871 vs 0.874; Llama-3.2 0.633 vs 0.835).
  Caveat: cross-run pairs differ in render (base k-shot vs instruct chat
  template) so those deltas are render-confounded; the Olmo-3 pair is the
  supported statement. Direction consistent with X's non-monotonicity:
  post-training does not sharpen the trust readout, and can dull it.
- **Render sensitivity (descriptive):** the dual-render control shows
  Qwen3.5-Base's veto is render-sensitive (k-shot 0.666 vs chat-render
  0.867), while its gate is render-invariant (0.998 both). The veto's
  fragility (Z finding) is partly a prompting-surface effect, not purely a
  model property.

### Arm B — era ladder (descriptive only, no gate, no claim)

| Rung (year) | best L | gate | dial | veto | within-SA ctrl |
|---|---|---|---|---|---|
| GPT-2-XL (2019) | 23 | 0.9911 | 0.7940 | 0.7936 | 0.5886 |
| Pythia-2.8B (2023) | 10 | 0.9927 | 0.8206 | 0.7511 | 0.5955 |
| Llama-2-7B (2023) | 15 | 0.9977 | 0.8267 | 0.8666 | 0.8184 |
| OLMo-2-7B (2025, LOCAL) | 16 | 0.9982 | 0.8580 | 0.7752 | 0.7107 |
| (top rungs = Arm A bases, 2026) | — | 0.997+ | 0.82-0.87 | 0.67-0.87 | 0.62-0.79 |

- Even GPT-2-XL carries all three readouts above W's 0.65 bar. The raw gate
  AUROC is nearly era-flat (0.991 -> 0.998); the era signal lives in the
  within-SelfAware control (~0.59 on 2019-2023-era GPT-2/Pythia rising to
  ~0.71-0.82 from Llama-2 onward), i.e. what improves across eras is the
  in-distribution separation of confident hallucinations from known answers,
  not the gross answerable/unanswerable split.
- **Text baseline bound (report rule):** a TF-IDF question-surface classifier
  reads the frozen gate pool at 0.964 +/- 0.016, and question-surface predicts
  dial correctness at 0.75-0.78 per family. The hidden-state gate (0.991-0.998)
  and dial (0.79-0.87) sit above these bounds, but the margins — not the raw
  AUROCs — are the honest effect sizes: much of the gate is
  surface-predictable on SelfAware.
- Engine equivalence: `y-equiv-pythia-batched` (batched engine re-run of the
  sequential Pythia cell) matches within noise (gate 0.9938 vs 0.9927, dial
  0.8277 vs 0.8206, veto 0.7887 vs 0.7511), supporting the batched-engine
  adoption for the fleet.

Per §5, Arm B stays descriptive: no era claim is minted here; a confirmatory
registration would be required. Per §7's paper rule, these results answer the
regimen paper's §8 open question (origin of the boundary signal) in the
"already present from pretraining" direction — paper text update tracked
separately on the paper line.
