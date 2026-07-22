# Fresh-SFT Epistemic Mode Tokens, Then GRPO

**Status:** DRAFT; not signed. No training or scored generation is authorized.

**Tier:** Tier-2 exploratory training cell, separate from the locked PROTOCOL
v0.3 matrix.

## 1. Question

Can a fresh Qwen3-4B SFT learn to emit `<ANSWER>`, `<QUALIFY>`, or `<ABSTAIN>`
as its first assistant token according to frozen empirical evidence of what it
knows, and can a subsequent GRPO stage improve that internal-state-to-action
alignment without sacrificing answer quality?

## 2. Starting point and training order

This experiment starts from the original Qwen3-4B model,
`unsloth/Qwen3-4B-bnb-4bit`, at a pinned upstream revision. It does **not** start
from any existing project SFT, GRPO-v3, contrastive-SFT, or merged checkpoint.

The intended order is:

1. reuse the existing frozen Qwen3-4B 32-generation knowledge labels and
   reconstruct the retained ambiguous-middle question ids from the pinned probe
   subset;
2. train a new SFT from that original Qwen base to learn both the visible
   behavior and the first action token;
3. measure whether the new SFT's token logits align with an independently fitted
   prompt-end knowledge readout;
4. if the SFT gates pass, run GRPO from the newly produced SFT checkpoint to
   improve mode selection and answer utility;
5. compare SFT-only, SFT-to-GRPO with true labels, and a matched permuted-label
   GRPO control.

GRPO-v3 is historical motivation and a comparison checkpoint only. It is not a
training input.

## 3. Mode labels and public behavior

Each assistant response begins with exactly one private control token:

- **`<ANSWER>`**: the model reliably knows the answer; answer normally.
- **`<QUALIFY>`**: knowledge is borderline; explicitly state uncertainty and
  still give the best supported answer.
- **`<ABSTAIN>`**: the model does not know; say so instead of inventing an
  answer.

The token is hidden from the end user after it conditions generation. The
visible response must independently satisfy the corresponding posture; the
literal token earns no reward.

The token is followed by a parseable JSON object:

```text
<ANSWER>{"answer":"Paris.","answer_confidence":0.91}
<QUALIFY>{"answer":"My best answer is Paris, but I am not certain.","answer_confidence":0.44}
<ABSTAIN>{"answer":"I don't know reliably.","answer_confidence":0.03}
```

`answer_confidence` estimates the probability that the model could supply a
correct factual answer. Its SFT target uses pre-registered non-endpoint bands
for the three frozen knowledge classes; exact per-question `p_correct` may
replace the band center only if the original provenance-matching row cache is
recovered before sign. It is distinct
from the historical `response_confidence` field, which estimated whether the
chosen response was appropriate. A correct abstention can have high response
appropriateness while knowledge is low, so silently reusing that field would
make internal-knowledge alignment mathematically incoherent. Response
appropriateness remains externally grader-scored.

### 3.1 Existing frozen empirical knowledge labels

The original Qwen3-4B probe already ran 32 stochastic samples at temperature
1.0/top-p 0.9 plus one greedy decode with thinking disabled. Its preregistered
rule maps directly onto the new modes:

- `P_correct == 0` -> `<ABSTAIN>`;
- neither known nor unknown -> `<QUALIFY>`;
- `greedy_correct AND P_correct >= 0.5` -> `<ANSWER>`.

No new threshold pilot is needed. The tracked `questions_frozen.json` preserves
8,892 known and 7,103 unknown keys, split into 14,395 train and 1,600 dev keys.
The deterministic 20,000-question probe subset can be reconstructed from the
pinned source-selection algorithm; its complement after removing frozen
known/unknown keys is the retained ambiguous-middle `<QUALIFY>` pool.

What is not currently present locally or on the project's Hugging Face dataset
inventory is the approximately 123 MB row-level `probe_results.jsonl` cache with
each exact `p_correct`, sampled answer, and sampled-correct vector. That absence
does not block categorical mode labels. Before sign, choose one of two honest
scalar targets: recover a provenance-matching copy of that cache and use its
per-question `p_correct`, or use fixed non-endpoint confidence bands for
`ABSTAIN`/`QUALIFY`/`ANSWER`. Do not regenerate merely to choose thresholds that
are already governed.

Question/entity clusters are split before generation. Held-out questions and
their gold answers never appear in SFT targets. This prevents the experiment
from calling memorization of its training answers epistemic alignment.

## 4. Stage S: new SFT

Stage S trains directly from the original Qwen3-4B base. The supervised target
is:

```text
<ANSWER>   + {correct direct answer, high answer_confidence}
<QUALIFY>  + {explicit uncertainty + best supported answer, middle answer_confidence}
<ABSTAIN>  + {honest "I don't know", low answer_confidence}
```

The mode token is the first supervised assistant token. The answer text and
posture are trained in the same new SFT, because the stated hypothesis is that
SFT teaches both the action vocabulary and what each action does.

For `<ABSTAIN>` rows, no gold answer is placed in the completion. For
`<QUALIFY>` rows, the target answer must be supported by a correct sampled answer
or the gold answer on the training split; fabricated samples are never
teacher-forced. Evaluation remains entity-disjoint so these targets cannot
directly teach the scored facts.

## 5. Where the "head" and internal readout live

No separate action head is required in the primary experiment. At the prompt
boundary, Qwen already computes a hidden state `h` and its normal language-model
head maps `h` to next-token logits. The three rows for `<ANSWER>`, `<QUALIFY>`,
and `<ABSTAIN>` are therefore the action head:

```text
prompt-end hidden state h
        -> normal LM head
        -> logits for ANSWER / QUALIFY / ABSTAIN
        -> chosen token
        -> visible continuation
```

A separate linear internal readout is fitted on a disjoint probe split to
predict the frozen 32-generation success statistic from the prompt-end hidden
state. It is a **measurement instrument**, not the runtime controller and not a
reward source in the primary cell.

This separation is deliberate. Prior aux-head co-training showed that a
separate head can learn the latent target without propagating it to the model's
own emitted behavior. The present experiment instead supervises the model's
native next-token channel directly, while the independent readout tests whether
the outward token is genuinely ordered by internal knowledge.

If ordinary token logits fail despite a valid independent readout, a custom
router head becomes a successor hypothesis. It is not part of this first cell.

## 6. Stage G: GRPO from the new SFT

Only after Stage S passes its token-semantic, behavior, and internal-readout
gates does Stage G begin. GRPO loads the new Stage-S checkpoint, not GRPO-v3, and
optimizes:

- factual correctness and supportedness of the visible answer;
- correct use of `<ANSWER>`, `<QUALIFY>`, and `<ABSTAIN>` against a frozen
  capability bank;
- costs for unnecessary qualification/refusal on reliably known questions;
- stronger costs for unsupported confident answers than qualified mistakes;
- a zero reward for merely emitting the expected literal token.

The GRPO target bank is generated once from the frozen Stage-S checkpoint and is
not recomputed from the live policy being optimized. This prevents the policy
from changing the evidence used to label its own action. The independent
internal readout remains outside the reward to reduce direct readout gaming.

### 6.1 Arms

| Arm | Training | Purpose |
|---|---|---|
| BASE | original pinned Qwen3-4B | starting behavior and knowledge reference |
| SFT | fresh mode-token SFT | tests whether SFT alone teaches both selection and posture |
| SFT-GRPO-TRUE | GRPO from the fresh SFT with real frozen capability labels | treatment |
| SFT-GRPO-PERMUTED | identical GRPO with labels permuted within source and capability-count strata | tests whether real epistemic correspondence matters |

## 7. Evaluation and anti-gaming controls

Primary serving evaluation is greedy. The mode token is stripped before blinded
external grading. Report separately:

1. **Token validity:** the first action is one of the three registered tokens.
2. **Mode behavior:** each token actually causes its promised visible posture.
3. **External utility:** factual correctness, truthful abstention, over-refusal,
   and qualified-wrong harm.
4. **Stated calibration:** `answer_confidence` is calibrated to held-out factual
   correctness/capability and does not collapse to an endpoint or mode constant.
5. **Internal alignment:** the independent readout and empirical 32-generation
   success rate monotonically order `answer_confidence`, the model's three token
   logits, and greedy choices on held-out questions.
6. **Treatment differential:** true-label GRPO beats both SFT-only and the
   permuted-label GRPO control.

Required defenses include entity-disjoint splits, a prompt-text-only baseline,
within-stratum permutation, blinded posture/refusal adjudication, exact token
stripping, per-mode coverage reporting, fixed and fresh post-training readouts,
and persistence of all generation text and sub-grades.

### 7.1 Deterministic screen plus blinded LLM response review

The registered response instrument has two stages:

1. **Enumerated detector screen.** Reuse the current detector-v2 implementation
   and frozen abstention-pattern inventory from
   `abstention-wide-instrument-calibration`, or a hash-audited promoted copy.
   Report its pattern ids and detector-only rates for every arm and population.
   It is a screen and diagnostic, not the final posture label.
2. **Blinded LLM posture review.** Review every held-out response from every arm,
   not only detector-negative rows. The reviewer receives only the decoded
   `answer` text: mode token, `answer_confidence`, arm, source, capability bucket,
   gold answer, and expected posture are removed. It returns exactly one of
   `ANSWER`, `QUALIFY`, `ABSTAIN`, or `OTHER` under the pinned rubric in
   `posture_reviewer_rubric.yaml`.

Reviewing all rows is required here because the wide abstention inventory
contains phrases such as "I'm not sure." Those are valid abstentions when no
answer follows, but they are also expected language inside `<QUALIFY>` responses.
A detector-positive shortcut would therefore systematically misclassify the
middle mode.

The lane adopts the current RR3/Llama safeguards:

- all scored arms and both benefit/cost populations enter a salted,
  opaque-id, seeded-shuffle pool with class-balanced held-back decoys;
- pool sha256 and opaque-id list are committed before any review;
- each context-free reviewer sees only its private shard and writes only to a
  pre-assigned private directory and unique output path;
- the lead verifies line count, positional opaque-id agreement, enum-only
  labels, and exact output keys before hash commitment;
- each graded shard's sha256 is committed before the id map may be read;
- per-shard and pooled decoy-calibration gates are applied before unblinding;
- one fresh-agent regrade is allowed for a void shard; a second failure voids
  the cell; there is no reviewer or rescoring lane behind this lane.

The final token/posture match compares the hidden mode token with the blinded
LLM label only after unblinding. Regex-only and LLM-reviewed rates are both
reported so the detector's misses and false positives remain visible.

## 8. Prediction and falsifier

**Prediction:** The fresh SFT will learn valid and causally effective mode
tokens, and true-label GRPO will improve held-out mode selection and external
utility over both SFT-only and permuted-label GRPO while preserving a monotonic
relationship between the independent knowledge readout and token choice.

**Falsifier:** Falsify this SFT-to-GRPO alignment path if the true-label GRPO arm
does not beat both SFT-only and the matched permuted-label control on held-out
mode appropriateness, if improvements come only from collapsing to one mode, or
if behavior improves while the independent internal readout ceases to order the
mode-token logits and choices.

A Stage-S causal-token failure is an upstream feasibility stop, not evidence for
or against GRPO. A token-accuracy win without visible behavior or independent
internal alignment is behavioral mimicry, not success.

## 9. Pre-sign blockers

Before signing:

- pin the original Qwen3-4B upstream revision and tokenizer;
- verify the candidate dataset has gold/alias coverage and an entity-disjoint
  split before reading scored outcomes;
- reproduce the pinned 20,000-question subset and recover the retained
  ambiguous-middle ids by set difference against the frozen known/unknown keys;
- decide and pin whether `answer_confidence` uses recovered per-row `p_correct`
  or fixed non-endpoint class bands;
- select token IDs and verify tokenizer, adapter, merge, save, and reload paths;
- build the fresh Stage-S dataset without gold-answer leakage into held-out
  clusters;
- pin the exact SFT and GRPO recipes and reward table;
- fit and pin the independent prompt-end readout on a disjoint probe split;
- lock numeric SFT, GRPO, anti-collapse, and internal-alignment gates;
- pin the current enumerated detector implementation/pattern inventory and the
  multi-class `posture_reviewer_rubric.yaml`;
- implement and smoke manifest-before-review, graded-hash-before-unblinding,
  class-balanced held-back decoys, private per-reviewer directories, positional
  joins, and the no-rescoring closure;
- implement incremental, resumable generation logs and complete kill-resume
  smokes;
- replace every `pending_pre_sign` field in `cell.yaml` and `gates.yaml`.

## 10. Predictions scoreboard

| Predictor | Call |
|---|---|
| orchestrator | fresh SFT passes token semantics; GRPO improves selection, but internal-alignment differential over the permuted control is the highest-risk gate |
| user | SFT teaches the behavior and special tokens; GRPO aligns their use with what the model knows |

## 11. Outcome

Not run. At resolution, report every gate for BASE, SFT, SFT-GRPO-TRUE, and
SFT-GRPO-PERMUTED without moving the registered thresholds.
