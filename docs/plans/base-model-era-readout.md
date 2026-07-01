# Proposed experiment: pretrain-only readout — does the boundary signal predate post-training?

**Status:** DESIGN / PROPOSAL (2026-07-02). NOT registered, NOT launched. This
is the design capture for a NEW experiment line raised by the user during
session 0031 ("we've been doing all this on instruct models that are heavily
post trained but what if we look at some older base models"). It becomes
runnable only after (a) a signed Tier-2 Amendment with locked gates on its OWN
branch off up-to-date `main`, and (b) explicit user launch approval naming
cells and lane.

## One-line thesis

Every "training-free" readout result so far (S/T/U/W/X/Z/SR) was measured on
vendor-post-trained instruct checkpoints; running the identical gate/dial/veto
readout on *pretrain-only* base models tests whether the knowledge-boundary
signal is genuinely a pretraining artifact (Paper 1 §8's closing claim) or a
gift of post-training we have been crediting to pretraining.

## Why now (the intellectual through-line)

- Paper 1's conclusion asserts "the expensive part of epistemic humility (the
  internal knowledge-boundary signal) is already paid for by pretraining."
  Our evidence: linear probes read the boundary at 0.97 on OUR checkpoints and
  the mechanism reads "training-free" on raw bases. But Amendment W's "raw,
  untrained base" is `Qwen3-4B` **Instruct** with no adapter of ours — heavy
  vendor SFT/RLHF included. X (1.7B–14B) and Z/SR (4 families) likewise used
  instruct variants. "Training-free" currently means *our*-training-free.
  The pretraining-origin claim is untested.
- Kadavath et al. (2022) and the GPT-4 report say pretrained models are
  well-calibrated at the token level and post-training damages that channel.
  If the *linear hidden-state* boundary signal shows the same pattern
  (present pre-post-training), the pretraining-origin claim locks. If instead
  base models read at chance while their instruct siblings read at 0.99, the
  entire two-signal program is a post-training readout, and Paper 1 §8 and
  Paper 3's framing both need revision. Either answer is publishable; the
  claim is currently unsupported in both directions.
- Bonus axis: model ERA. X found sharpness is non-monotonic in SIZE; nobody
  has asked whether it is monotonic in generation (GPT-2-era pretraining vs
  2023 vs 2026 corpora) at matched scale.

## Arm A — paired base-vs-instruct contrast (primary, controlled)

Same family, same size, same pretraining corpus; the ONLY delta is vendor
post-training. Run the identical X/Z extraction + gate/dial/veto scoring on
both siblings:

| Pair | Base | Instruct | Notes |
|---|---|---|---|
| Qwen3-4B | `Qwen3-4B-Base` | `Qwen3-4B` (Instruct) | anchors to W/X directly |
| Llama-3.2-3B | `Llama-3.2-3B` | `Llama-3.2-3B-Instruct` | anchors to Z/SR |
| Mistral-7B | `Mistral-7B-v0.1` | `Mistral-7B-Instruct-v0.1` | ungated, older (2023) |

Predictions (from Paper 1 + W): gate ≈ equal across siblings
(pretraining-origin); dial/veto modestly sharper on instruct (post-training
sharpens the veto, as W found for our training: 0.75 → 0.98).

## Arm B — era ladder (exploratory, descriptive)

Pretrain-only models across generations, size held roughly at the smallest
viable scale; no instruct sibling required:

- `gpt2-xl` (1.5B, 2019) — pre-RLHF era entirely
- `pythia-2.8b` (2023, EleutherAI) — fully open pretraining provenance
- `Llama-2-7B` base (2023) — gated access already GRANTED (2026-06-10)
- `OLMo-2-7B` base (2025) — open provenance
- the Arm A modern bases as the ladder's top rungs

Descriptive question only: does linear boundary readability strengthen with
pretraining era/corpus quality at matched-ish scale? No gate on this arm;
report the curve.

## Infra deltas (the real work before registration)

- **No chat template.** `amendment_x_cross_model_extract.py` renders with
  `apply_chat_template`; pretrain-only models need a base-mode path: k-shot
  QA prompt (fixed few-shot block) + plain completion, stop at newline.
  The flag must default off so X/Z/SR reproduce byte-for-byte.
- **Answer parsing.** Base-model continuations are freeform; parse the first
  line after the answer cue. Expect near-zero refusals — fine: this is a
  READOUT-ONLY study (gate = answerability from activations; dial/veto =
  correctness ranking among answered). Behavioral abstention metrics are not
  a target and must not become one after the fact.
- **Per-model labels.** known/unknown labels regenerate per model (same as
  X); weak old models will have few correct rows — pre-state an adequacy
  gate (minimum correct and hallucination row counts per cell) like SR's, so
  an underpowered cell is INELIGIBLE, not a fake negative.
- **Arch coverage.** GPT-2 (1024 ctx, different layer geometry) needs a
  probe-layer rule stated up front (e.g., ~0.55 depth fraction rounded, the
  X convention) rather than hand-picked layers.

## Draft pre-registration skeleton (finalize + sign before any run)

- **H_B1 (pretraining-origin, PRIMARY):** on each Arm A base model, the
  answerability gate reads at AUROC ≥ 0.90 on the SelfAware anchor.
  Falsifier: base gate < 0.75 while its instruct sibling ≥ 0.95 on the same
  rows → post-training creates (not sharpens) the signal → Paper 1 §8 and
  Paper 3 framing revised, no goalpost move.
- **H_B2 (veto exists pre-post-training):** base-fit dial ranks base
  hallucinations below base-correct answers, AUROC ≥ 0.65 (W's bar), on ≥ 2/3
  Arm A bases.
- **H_B3 (sharpening, expected but not required):** instruct minus base veto
  delta > 0 per pair; report only.
- Arm B: descriptive, no gate, reported as a curve with adequacy flags.
- Decode: greedy (X/Z convention); sampled-decode robustness only if SR's
  machinery is reused later — do not fold into this registration.

## Hard limits / caveats (honest scope)

- Base-vs-instruct pairs differ in more than "post-training" for some vendors
  (annealing data, long-context stages); the pair is the cleanest available
  contrast, not a perfect ablation. Say so in the writeup.
- GPT-2-era models may fail adequacy on SelfAware/popqa outright (too few
  correct answers). That is an eligibility outcome, not evidence about the
  signal.
- This does NOT test whether post-training *damages* the internal signal
  (that needs matched pre/post checkpoints of the same run, e.g., OLMo/Tulu
  intermediate checkpoints — note as future work if Arm A shows a gap).

## Dependencies & sequencing

- Blocked behind: SR verdict + PR (in flight, Gemma seed 703 extracting now);
  one-branch-one-PR discipline.
- GPU: single local GPU; era ladder is 5–8 extraction cells at ~1.5–2h per
  3–7B cell (GPT-2 much faster) → two to three overnight queues, same
  dgpu/docker lane as X/Z/SR.
- Extractor change (base-mode prompting) is a small backward-compatible PR
  that can be built and smoke-tested on CPU/GPT-2 before registration.
- Paper fit: extends Paper 3 (training-free → post-training-free) or a short
  standalone; decide at registration time.

## What was captured today (design only)

This document. No amendment minted, no letter assigned, no extraction run, no
recipe or protocol file touched.
