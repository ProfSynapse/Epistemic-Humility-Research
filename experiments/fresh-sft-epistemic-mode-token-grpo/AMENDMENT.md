# Fresh-SFT Epistemic Mode Tokens (Stage S)

**Status:** DRAFT; not signed. No full training or scored qualification is
authorized.

**Tier:** Tier-2 exploratory training cell, separate from the locked PROTOCOL
v0.3 matrix.

## 1. Question

Can a fresh Qwen3-4B SFT imitate a frozen empirical epistemic action policy by
emitting `<ANSWER>`, `<QUALIFY>`, or `<ABSTAIN>` as its first assistant token,
while preserving the corresponding visible posture and answer quality?

This amendment governs Stage S only. GRPO and any downstream held-out
evaluation require a separate, prospectively signed experiment.

## 2. Starting point and data boundary

This experiment starts from the original Qwen3-4B model,
`unsloth/Qwen3-4B-bnb-4bit`, at the pinned upstream revision
`cad0bedfdd862093a12af478cb974ab2addd0e0a`. It does **not** start from any
existing project SFT, GRPO-v3, contrastive-SFT, adapter, or merged checkpoint.

The Stage-S sequence is:

1. reuse the recovered frozen Qwen3-4B 32-generation row cache and apply the
   locked three-way binomial-evidence rule to the pinned 20,000-question subset;
2. train a new SFT from the original Qwen base to learn the visible behavior and
   first action token together;
3. qualify the resulting checkpoint on the 602-row dev split only; and
4. stop and report the pre-stated Stage-S gates without using held-out row
   content or scoring the 1,201-row held-out split.

The held-out split is sealed for a separately registered downstream GRPO
experiment. Hash-only integrity verification remains allowed, but held-out row
content is not a Stage-S tuning, selection, qualification, or reporting surface.

## 3. Mode labels and public behavior

Each assistant response begins with exactly one private control token:

- **`<ANSWER>`**: the model reliably knows the answer; answer normally.
- **`<QUALIFY>`**: knowledge is borderline; explicitly state uncertainty and
  still give the best supported answer.
- **`<ABSTAIN>`**: the model does not know; say so instead of inventing an
  answer.

The token is hidden from the end user after it conditions generation. The
visible response must independently satisfy the corresponding posture.

The token is followed by a parseable JSON object:

```text
<ANSWER>{"answer":"Paris.","answer_confidence":0.91}
<QUALIFY>{"answer":"My best answer is Paris, but I am not certain.","answer_confidence":0.44}
<ABSTAIN>{"answer":"I don't know reliably.","answer_confidence":0.03}
```

`answer_confidence` estimates the probability that the model could supply a
correct factual answer under the frozen 32-sample probe. Its SFT target is the
Jeffreys posterior mean `(k + 0.5) / 33`, where `k` is the number of correct
probe samples. This preserves within-mode variation without teaching exact
zero or one. The Stage-S qualification checks the field's validity and
non-collapse; it does not claim held-out calibration.

### 3.1 Frozen empirical evidence and the three-way rule

The original Qwen3-4B probe ran 32 stochastic samples at temperature 1.0/top-p
0.9 plus one greedy decode with thinking disabled. Its complete 20,000-row cache
is available locally and provenance-matches the probe manifest:

- probe-cache SHA-256
  `f8b4b89345f15b89fa40fd834c3d9249e0a5417b67d2cf7da7eee6f936635c43`;
- probe-manifest SHA-256
  `52f374db01b4e60c55784ae7bfa3b9353e4830ac73628457fd858b0707eb18b4`;
- probe config SHA `893861257973170b`, `n=32`, seed `20260610`, thinking
  disabled.

The operational reference is a 50% probability of answering correctly. Rather
than split `k=16` from `k=17` by a raw vote, the experiment uses exact one-sided
95% Clopper-Pearson evidence around `p=0.5`:

- `<ABSTAIN>` when `k <= 10`;
- `<ANSWER>` when `k >= 22` **and** the frozen greedy answer is correct; and
- `<QUALIFY>` otherwise: `k=11..21`, plus `k>=22` rows whose frozen greedy
  answer is wrong.

For `n=32`, the boundary values are `U(10)=0.472140`, `U(11)=0.504191`,
`L(21)=0.495809`, and `L(22)=0.527860`. Applied before training outcomes are
observed, the rule yields 10,156 ABSTAIN, 1,537 QUALIFY, and 8,307 ANSWER rows.
Fifty-three high-evidence rows have a wrong greedy answer and remain QUALIFY.

Rows are grouped before SFT by transitive overlap of canonical normalized
answer/alias identities and exact normalized-question duplicates. Whole
components, never individual rows, enter train, dev, or held-out. The frozen
build produces 18,197 train rows, 602 dev rows, and 1,201 held-out rows with zero
normalized answer/alias or normalized-question overlap.

## 4. Stage S training

Stage S trains directly from the original Qwen3-4B base. The supervised target
is:

```text
<ANSWER>   + {correct direct answer, high answer_confidence}
<QUALIFY>  + {explicit uncertainty + best supported answer, middle answer_confidence}
<ABSTAIN>  + {honest "I don't know", low answer_confidence}
```

The mode token is the first supervised assistant token. Answer text and posture
are trained in the same fresh SFT because the hypothesis is that SFT can imitate
both the action vocabulary and what each action means.

For `<ABSTAIN>` rows, no gold answer is placed in the completion. For
`<QUALIFY>` rows, the target answer must be supported by a correct sampled answer
or the gold answer on the training split; fabricated samples are never
teacher-forced.

The canonical Stage-S output is an adapter plus tokenizer and exact base-model
lineage. A merged model is not the retained checkpoint. Merge/save/reload is a
bounded compatibility smoke only.

## 5. Native action channel

No separate router or action head is part of this experiment. At the prompt
boundary, Qwen's normal language-model head maps the hidden state to
full-vocabulary next-token logits, including the three configured mode-token
rows. Primary qualification uses an unconstrained greedy first token over the
full vocabulary. Mode-restricted decoding is diagnostic only.

The token strings and their order are configuration-driven. The pinned upstream
tokenizer plus that ordered list are the source of truth; realized token IDs are
recorded and roundtrip-verified at runtime rather than hard-coded into the
governed instrument.

## 6. Dev-only qualification

Stage S is qualified on the 602-row dev split: 200 ABSTAIN, 200 QUALIFY, and 202
ANSWER rows. The 1,201-row held-out split remains sealed.

The qualification reports:

1. **Native token validity:** the unconstrained greedy first token is one of the
   three configured tokens.
2. **JSON validity:** the remainder parses and contains exactly `answer` and
   `answer_confidence` under the registered schema.
3. **Per-mode recall:** for every frozen source mode, the two-sided 95% Wilson
   lower bound on dev recall is greater than 0.5. At `n=200`, this requires at
   least 114 successes; the 202-row ANSWER class is evaluated at its actual
   denominator.
4. **Deterministic forced-token posture contract:** forcing each configured
   first token produces the corresponding registered response structure and
   visible posture under a pinned deterministic checker.
5. **Anti-collapse:** success requires every per-mode majority gate and an
   additional pre-signed maximum single-mode share.
6. **Answer-quality noninferiority:** the Stage-S checkpoint must satisfy a
   pre-signed paired dev answer-quality floor against the original pinned base.

All numeric thresholds other than the Wilson majority gate remain explicit
pre-sign decisions. No Stage-S result may be used to set them.

## 7. Prediction and falsifier

**Prediction:** The fresh SFT will imitate the frozen empirical three-way action
policy on the dev split: it will emit valid native mode tokens and JSON, achieve
better-than-majority recall for every mode, preserve the deterministic
forced-token posture contract, avoid single-mode collapse, and retain answer
quality relative to the original pinned base.

**Falsifier:** Stop this SFT checkpoint if any mode's two-sided 95% Wilson recall
lower bound is less than or equal to 0.5, if the native token/JSON/causal posture
contract fails, if choices collapse to one mode, or if answer quality falls
below the pre-signed noninferiority floor.

This falsifier adjudicates only whether the Stage-S checkpoint qualifies for a
separate downstream experiment. It is not evidence for or against any GRPO
hypothesis.

## 8. Pre-sign blockers

Before signing this Stage-S-only amendment:

- retain the recovered cache/manifest/model/tokenizer hashes, deterministic
  dataset-builder pins, exact three-way evidence rule, and Jeffreys target;
- retain the reproduced 18,197/602/1,201 private-build hashes and zero-overlap
  assertions while sealing held-out from Stage-S qualification;
- pin the exact Stage-S runtime config, recipe, preparer, dataset builder, and
  their focused tests;
- reconcile the runtime-derived special-token lineage across every config and
  enforce string/order/tokenizer-based roundtrip checks without fixed token IDs;
- implement and pin the dev-only qualification runner and deterministic
  forced-token posture checker;
- lock every remaining numeric Stage-S threshold, including token/JSON validity,
  forced-posture compliance, maximum single-mode share, confidence non-collapse,
  and answer-quality noninferiority;
- implement incremental, resumable dev-generation logs and complete the
  kill-resume smoke;
- add and test an authorization-gated full Stage-S launch path while retaining
  `launch_authorized: false` and a no-launch default; and
- replace every `remaining_pre_sign` field in the Stage-S instrument.

The bounded six-row/two-step Modal tokenizer/adapter/merge compatibility smoke
is recorded in `NOTEBOOK.md`. It is a pre-sign smoke, not an evidence run, and
does not authorize full Stage S.

## 9. Predictions scoreboard

| Predictor | Call |
|---|---|
| orchestrator | fresh SFT learns valid native tokens and their deterministic visible posture, with the rare QUALIFY mode carrying the highest qualification risk |
| user | SFT teaches the behavior and special tokens |

## 10. Outcome

Not run. At resolution, report every pre-signed Stage-S qualification gate on
the dev split without using or scoring sealed held-out row content.
