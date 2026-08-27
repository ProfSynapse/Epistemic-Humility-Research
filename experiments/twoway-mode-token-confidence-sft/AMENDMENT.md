# Two-Way Native Mode Token plus Answer-Confidence SFT

Status: **draft (not signed; do not launch as confirmatory evidence).** No sign,
no GPU, no training authorized. Held-out (1,201 rows) stays sealed and
unreferenced. Leave uncommitted for lead review.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

**Tier:** Tier-2 exploratory training cell, separate from the locked PROTOCOL
v0.3 matrix. This is the lead+user adjudicated successor (option 2) to the
falsified `fresh-sft-epistemic-mode-token-grpo` Stage-S.

## 1. Question

Can a fresh Qwen3-4B SFT imitate a frozen empirical epistemic *action* policy
reduced to **two** native first-token modes — `<ANSWER>` (attempt) vs
`<ABSTAIN>` (decline) — while, in the same head, emitting a calibrated
`answer_confidence` scalar, such that the checkpoint (a) avoids the Stage-S
QUALIFY void by construction, (b) does **not** over-abstain, and (c) supports a
graded, product-layer "qualify" presentation from the scalar rather than from a
trained class?

This amendment governs the single SFT stage and its dev qualification only. Any
downstream GRPO or held-out evaluation requires a separate, prospectively signed
experiment.

## 2. Motivation and posture (read-before-cite grounding)

Two governed prior results ground this design; both were read directly, not
recalled.

**Stage-S falsification** (`fresh-sft-epistemic-mode-token-grpo/AMENDMENT.md`
§10, verdict-bearing run `stage-s-dev-20260723-rerun-f6f1229`). A three-way
native mode-token SFT (`<ANSWER>`/`<QUALIFY>`/`<ABSTAIN>`) installed the
mechanism perfectly (all format/mechanism gates 1.0; first token 602/602;
forced-posture 1806/1806; confidence SD 0.4845) but **FALSIFIED on two limbs**:

- **QUALIFY void:** native per-mode recall QUALIFY **0/200 = 0.00** (predicted
  counts ABSTAIN 290 / ANSWER 312 / QUALIFY 0). ABSTAIN 154/200=0.77 and ANSWER
  160/202=0.792 both passed; the middle class simply never emitted.
- **Answer-quality noninferiority FAIL:** paired StageS−base correctness
  **−0.239, 95% CI [−0.281, −0.196]** vs the −0.10 floor, via **over-abstention**
  (290 predicted ABSTAIN vs 200 true; abstentions on answerable rows score 0
  against base's correct answers).

The §10 post-hoc (non-binding) mechanism note: QUALIFY was ~8% of training
sources (937 of 18,197 train rows) and "a successor design should address class
balance and pre-test QUALIFY's in-representation separability before any
retrain."

**Separability pre-test** (`qualify-mode-separability-base-readout/AMENDMENT.md`
Outcome, resolved 2026-07-23). That pre-test read out the QUALIFY band from the
base model's own pre-generation representation. Result **INCONCLUSIVE**: the
banded k-regression QUALIFY-vs-rest AUROC peaked at 0.5690 [0.5228, 0.6138] (hs27,
75% depth) — between the FAIL ceiling (0.55) and PASS floor (0.62). `k` is only
moderately encoded (Spearman rising to ~0.44 with depth); the scale **ends** read
substantially better than the middle (ABSTAIN-vs-rest up to 0.716, ANSWER-vs-rest
up to 0.758) while the QUALIFY band stays weak (0.54–0.62) under every readout
class. The naive linear floor did **not** underperform the band-aware readouts,
so the "middle band is present but linearly inseparable" hypothesis was not
supported. Its explicit non-binding reading for the successor decision: *"the
evidence pattern — graded k signal real but weak in the middle, crisp band
absent — favors an ordinal-aware redesign of the QUALIFY supervision (or a 2-way
policy plus the already-working confidence scalar) over a plain class-rebalanced
retrain of the same discrete 3-way rule."*

**This design takes exactly that fork:** drop QUALIFY as a trained *class* (the
representation does not support a crisp middle category, and a plain rebalance
would not be expected to install one), keep the middle band alive through the
already-working graded `answer_confidence` scalar (Stage-S proved the scalar
channel is well-formed and non-collapsed), and move the "qualify" surface to an
inference-time rendering rule over that scalar (§7). The action becomes a clean
binary the ends of the k-axis already encode well.

## 3. Starting point, data boundary, and the frozen-split reuse rule

Starting model: the original `unsloth/Qwen3-4B-bnb-4bit` at the pinned upstream
revision `cad0bedfdd862093a12af478cb974ab2addd0e0a` — the exact Stage-S starting
checkpoint. No project SFT/GRPO/contrastive/adapter/merged checkpoint is an input.

**Frozen evidence reuse (binding).** This experiment reuses, byte-for-byte, the
frozen artifacts of Stage-S — it re-derives nothing upstream:

- the recovered frozen Qwen3-4B 32-generation probe cache
  (`probe_results` sha256 `f8b4b893…635c43`, manifest `52f374db…eb18b4`, config
  SHA `893861257973170b`, n=32, seed 20260610, thinking disabled);
- the deterministic component-disjoint split already materialized by the Stage-S
  builder: `train.jsonl` (18,197, sha256 `da473bc0…46268`), `dev.jsonl` (602,
  sha256 `dcff3134…f68661`), `heldout.jsonl` (1,201, sha256 `495a908f…9b7839`).

**The successor does NOT re-run the split.** Re-running the union-find allocator
with a two-class stratification objective would change component→split assignment
and therefore change held-out membership — violating both the reuse constraint
and the held-out seal. Instead the new builder is a **relabel-in-place pass** over
the frozen split files: it reads each frozen `train`/`dev` row's `row_key`,
`correct_count` (k), `greedy_correct`, `answer_value`, and aliases, verifies the
source file sha256, keeps every row in its existing split, and recomputes only
(i) the two-way `mode_label` and (ii) the rendered assistant completion. Held-out
is not rebuilt or opened at all; the frozen sealed file is carried forward
untouched for the future downstream experiment. This guarantees identical
component-disjoint membership and a byte-identical sealed held-out.

## 3.1 The two-way action rule and the QUALIFY-mapping decision

The Stage-S three-way rule was an ordinal band over k (correct count / 32):
ABSTAIN k≤10, ANSWER k≥22 ∧ greedy-correct, QUALIFY otherwise (k=11..21, plus 53
program-wide k≥22-but-greedy-wrong rows). The central design question is **how the
1,537-source QUALIFY band (train: 937 rows; dev: 200 rows) maps into two-way
supervision.** Three options were analysed against the two Stage-S failure modes
(over-abstention; noninferiority drag). The winning mapping must predict *less*
over-abstention than Stage-S, not more.

Exact k-histogram of the frozen QUALIFY sources (computed from the frozen
train/dev split; held-out never opened):

| split | QUALIFY total | k=11–16 | k=17–21 | k≥22 (greedy-wrong) |
|---|---|---|---|---|
| train | 937 | 520 | 380 | 37 |
| dev   | 200 |  97 | 101 |  2 |

**Option (i) — threshold split at some k\*** (a new derived design constant).
Rows k≥k\* → ANSWER, k<k\* → ABSTAIN. The only k\* that reduces over-abstention is
one at or below the *existing* ABSTAIN boundary k≤10; any k\*>10 moves part of the
middle band into ABSTAIN and **grows** the abstain class. Worked example at the
p=0.5 majority point (k\*=17): train ABSTAIN 9,556→10,076 (+520), dev ABSTAIN
200→297. That relabels rows the model answers correctly 34–50% of the time as
"decline," which is exactly the Stage-S noninferiority-drag mechanism recreated by
construction. A threshold at k\*=11 folds the entire band into ANSWER and is
therefore identical to option (ii). Verdict: no threshold strictly dominates the
existing k≤10 boundary; every k\*>10 moves the wrong way. **Rejected.**

**Option (ii) — fold the entire QUALIFY band into ANSWER; the confidence scalar
carries the hedging. [RECOMMENDED]** The two-way boundary is the *already-derived,
already-validated* Clopper-Pearson ABSTAIN boundary: **ABSTAIN iff k≤10 (one-sided
95% upper bound below 0.5, U(10)=0.472140); ANSWER otherwise.** The answer_min=22
upper boundary is retired (no upper class). The 53 high-k-greedy-wrong rows become
ANSWER naturally (they are k≥22, high capability; the greedy miss is decode
noise, and the gold answer teacher-forced on them is correct). This introduces
**no new constant** — it reuses an existing one and drops one. Row projections
(relabel of the frozen split):

| split | ABSTAIN (k≤10) | ANSWER (k≥11) | balance |
|---|---|---|---|
| train (18,197) | 9,556 | 8,641 | 0.525 / 0.475 |
| dev (602)      |   200 |   402 | 0.332 / 0.668 |
| heldout (1,201, sealed) | not rebuilt | not rebuilt | — |

Against the two failure modes:
- **Over-abstention:** the ABSTAIN class share is **unchanged** (still exactly
  k≤10 = 9,556 train / 200 dev — we do not grow abstain). The middle band is now
  *explicitly trained as ANSWER*, directly teaching "attempt" on precisely the
  rows where the Stage-S three-way model defaulted to ABSTAIN. Predicts **less**
  over-abstention. ✓ (meets the lead's criterion)
- **Noninferiority drag:** middle-band rows are attempted (as base does), so
  paired StageS−base deltas on them move from ≈−1 toward ≈0. Combined with the
  rethought gate (§6.6, restricting the paired comparison to attempted rows plus
  an abstention-rate band), abstention can no longer mechanically eat the diff. ✓
- **QUALIFY void:** impossible by construction — there is no QUALIFY class to
  void. The graded middle survives in the scalar (§3.2) and the rendering rule
  (§7).

**Option (iii) — exclude the middle band from action supervision, keep it for
confidence supervision only.** Trains the first-token head only on crisp
ABSTAIN (k≤10) and crisp ANSWER (k≥22 ∧ greedy-correct); the 937 middle rows feed
only the scalar. Rejected: it leaves the model's first-token behavior on
middle-band inputs *untrained*, so at inference those rows route arbitrarily —
Stage-S's untrained three-way routing already showed such rows split toward
ABSTAIN, contributing to over-abstention — and it still forces a separate
definition of the two-way eval ground truth on those rows. Option (ii) dominates:
it keeps the middle band for confidence supervision (it always did) *and* uses it
as informative ANSWER action supervision.

**Recommendation: option (ii).** It is the minimal, most defensible change
(reuses one derived constant, retires one), attacks both Stage-S failure
mechanisms directly, and makes the confidence scalar — not a doomed discrete
class — the home of graded uncertainty.

## 3.2 The confidence scalar (unchanged target, promoted to a gated surface)

Each response is `<MODE>{"answer": ..., "answer_confidence": c}` with exactly the
two required fields. `answer_confidence` estimates the probability the model could
supply a correct factual answer under the frozen 32-sample probe; its SFT target
is the **unchanged** Jeffreys posterior mean `(k + 0.5) / 33`. Because the middle
band (k=11–21) is retained (now inside the ANSWER class), the scalar still spans
its full range and populates the middle densely — which is what makes both the
calibration gate (§6.7) and the qualify-rendering rule (§7) meaningful. Stage-S
already proved this channel is well-formed and non-collapsed (SD 0.4845 ≫ the 0.05
floor); this design keeps that and adds a real calibration gate on top.

## 4. Training

Single SFT stage from the original Qwen3-4B base. Supervised target:

```text
<ANSWER>   + {best supported direct answer, answer_confidence=(k+0.5)/33}
<ABSTAIN>  + {honest "I don't know reliably.", answer_confidence=(k+0.5)/33}
```

The mode token is the first supervised assistant token; answer text, posture, and
scalar are trained together in one fresh SFT. For ABSTAIN rows (k≤10) no gold
answer is placed in the completion (unchanged from Stage-S). For ANSWER rows the
completion carries the gold answer (`answer_value`); this includes the former
middle band, where the honest posture is "attempt, with a middle
`answer_confidence`." No fabricated samples are ever teacher-forced.

**Two tokens only.** The tokenizer registers exactly `<ANSWER>` and `<ABSTAIN>` as
additional special tokens (mean-existing-rows init, trainable embedding + lm_head
rows). A dead `<QUALIFY>` token is **not** carried into the vocab. Realized token
IDs are recorded and roundtrip-verified at runtime; no fixed IDs in the governed
instrument.

**Instrument-history note (one line, binding on the lane).** Stage-S's first dev
qualification was an INVALID instrument failure — the tuner's `hf_batched` engine
loaded the adapter via a bare `AutoModelForCausalLM.from_pretrained` and silently
dropped the `trainable_tokens` embedding delta (the sole mode-token mechanism);
this design **mandates the repaired tuner at commit `f6f1229` or later** on
`feature/configurable-special-tokens` (PEFT-aware adapter-dir loading,
regression-tested) for both training and qualification.

Canonical output: adapter + tokenizer + exact base-model lineage (a merged model
is not retained; merge/save/reload is a bounded compatibility smoke only).

### 4.1 Changes from the pinned Stage-S recipe (each flagged)

Everything not listed here is carried **verbatim** from the Stage-S recipe:
`unsloth` image `sha256:0e57d91e…cc3133`, the exact pip pin set, LoRA r32/α64
dropout 0.05 on the seven attention+MLP projections, LR 2e-4, batch 2 ×
grad-accum 4, 1 epoch, max_seq 2048, `enable_thinking: false`, mean-existing-rows
special-token init with trainable embedding + lm_head rows.

1. **Two special tokens** instead of three (`<ANSWER>`, `<ABSTAIN>`); no dead
   `<QUALIFY>`. *(vocab change — necessary)*
2. **Two-way labeling** in `dataset_builder.yaml` (ABSTAIN iff k≤10, else ANSWER;
   answer_min retired; QUALIFY answer-template removed). *(necessary)*
3. **Relabel-in-place builder** (does not re-split; §3). *(necessary; preserves
   frozen membership + sealed held-out)*
4. **No training-side class rebalancing.** The 8%-minority condition that
   motivated a rebalance in the Stage-S post-mortem is gone — two-way train is
   0.525/0.475. Natural distribution kept; no class weights added. *(flagged: a
   deliberate non-change)*
5. **Tuner pinned at `f6f1229`+** (repaired loader), not Stage-S's signed
   `ef4e45e6`. *(necessary; §4 instrument-history note)*
6. Optimizer-step budget is **unchanged**: 18,197 train rows are only relabeled,
   not added/removed, so ~2,275 steps at batch-effective-8 stands (~3.5 h).
7. **Lane: local RTX 3090** (user-locked 2026-07-24), queued behind the j-space
   cross-family pipeline. The Modal lane is out of scope and `modal_qualify.py` is
   dropped. Precedent: Stage-S's verdict-bearing dev qualification ran on the
   local RTX 3090 at explicit user direction (Stage-S §10, "LANE DEVIATION,
   recorded"); this experiment adopts local as the primary lane prospectively.

## 5. Native action channel

No separate router or action head. At the prompt boundary Qwen's normal LM head
maps the hidden state to full-vocabulary next-token logits, including the two
configured mode-token rows. Primary qualification uses an **unconstrained greedy
first token over the full vocabulary**; mode-restricted decoding is diagnostic
only. Token strings and order are configuration-driven (source of truth: the
pinned upstream tokenizer plus the ordered two-string list).

## 6. Dev-only qualification and gate table

Qualified on the 602-row dev split under the two-way relabel (**200 ABSTAIN / 402
ANSWER**). The 1,201-row held-out split stays sealed. Every threshold below is
pre-stated and **LOCKED (2026-07-24; lead + user ratification, changelog §12)**.
All gates are dev qualification gates — none is a held-out calibration claim.

Format/mechanism gates are carried **verbatim** from Stage-S §6 where they apply,
adapted only for two tokens.

| # | Gate | Threshold | Provenance / derivation |
|---|---|---|---|
| 1 | Native first-token validity | greedy first token ∈ {`<ANSWER>`,`<ABSTAIN>`} on ≥ **95%** dev rows | verbatim Stage-S §6.1 (two tokens) |
| 2 | JSON validity | remainder parses AND fields == {`answer`,`answer_confidence`} on ≥ **95%**; parse and exact-field coverage gated separately at 95% | verbatim Stage-S §6.2 |
| 3 | Per-mode Wilson recall (2 modes) | two-sided 95% Wilson lower bound **> 0.5** for each mode. Min successes: **ABSTAIN ≥ 114/200**, **ANSWER ≥ 221/402** | verbatim Stage-S §6.3 rule; ANSWER threshold re-derived for n=402 (Wilson-lower(221,402)=0.5009; 220 gives 0.4984) |
| 4 | Forced-posture contract (2 tokens) | forcing each configured token yields the registered structure + visible posture on ≥ **95%** of forced continuations. ANSWER: nonempty/substantive, no configured ignorance/uncertainty phrases. ABSTAIN: exact "I don't know reliably." | verbatim Stage-S §6.4; **QUALIFY exact-match posture check removed** (no QUALIFY token). Gold correctness stays a descriptive sub-grade |
| 5 | Anti-collapse | every per-mode majority gate (#3) PASS **and** max single predicted-mode count ≤ **542/602** *(LOCKED)* | Stage-S used 374/602 (62%) for 3 modes; that ceiling is **below** the two-way true ANSWER base rate (0.668) and is inapplicable. Re-derived as ⌈0.90·602⌉=542; secondary to #3, which already blocks true collapse (all-ANSWER fails ABSTAIN recall) |
| 6 | Answer-quality noninferiority (rethought) | **(a)** on rows where StageS emits `<ANSWER>`: paired StageS−base correctness two-sided 95% percentile-bootstrap CI lower > **−0.10** (seed 20260722, 10,000 resamples). **(b)** dev abstention rate ∈ **[0.22, 0.42]** *(LOCKED)* | §6.6 below |
| 7 | Confidence validity + non-collapse | ≥ **95%** finite `answer_confidence` ∈ [0,1]; population SD ≥ **0.10** *(LOCKED; raised from Stage-S 0.05)* | Stage-S §6.7 validity; SD floor raised to the calibration-surface precedent (`contrastive-sft-behavior-conditional-confidence` §4.1 emitted std ≥ 0.10). Stage-S measured 0.4845, so this is not a stretch |
| 8 | **Confidence calibration (NEW, first-class, HARD co-equal)** | on attempted (`<ANSWER>`) rows: **(a)** `answer_confidence`→emitted-answer-correctness AUROC ≥ **0.62** *(LOCKED)*; **(b)** ECE(stated confidence vs empirical correctness) < **0.30** *(LOCKED)* | §6.7 below; bars copied verbatim from the program's only confidence-calibration precedent, `contrastive-sft-behavior-conditional-confidence` §4.1 (AUROC ≥ 0.62, ECE < 0.30, itself from the AL/H9/BB readout-quality bar). **HARD success requirement, co-equal with recall and noninferiority** (user ratification §12). Dev qualification only, not a held-out calibration claim |
| 9 | Private-token stripping | configured special-token strings absent from **100%** of native and forced visible texts after the leading control token is stripped; tokenizer registers each configured string as special with the exact runtime ID/atomic encoding in the artifact lineage | verbatim Stage-S §6.8 (two tokens) |

### 6.6 The rethought noninferiority gate (attacks the §10 drag mechanism)

Stage-S let abstention mechanically eat the paired diff: an over-abstaining policy
scores 0 on answerable rows against base's correct answers, so the paired
StageS−base metric went −0.239 largely *because of the abstention rate*, not
because attempted answers were worse. This design separates the two concerns:

- **(a) Attempted-row paired correctness.** Restrict the paired comparison to the
  dev rows where StageS chooses `<ANSWER>`. On that identical row subset, compare
  StageS's emitted-answer correctness to base's — both evaluated on the same
  questions (`experiments/common/knowledge_probe/scoring.py:is_correct`). This
  answers the honest question: *when the policy attempts, is its answer quality
  noninferior to base?* Bootstrap construction, seed, resamples, and the −0.10
  floor are carried verbatim from Stage-S §6.6.
- **(b) Abstention-rate band [0.22, 0.42] (LOCKED).** The band is the guard that
  makes (a) legitimate: without it, a policy could abstain on 90% of rows and pass
  (a) on a tiny cherry-picked attempted subset. Derivation: true dev ABSTAIN rate
  = 200/602 = 0.332; Stage-S over-abstained at 290/602 = 0.482. Upper bound 0.42
  (253 rows) sits strictly below the Stage-S failure and keeps the attempted
  subset ≥ ~349 rows (representative, not cherry-picked); lower bound 0.22 (133
  rows) preserves genuine abstention (well above zero) so the policy has not
  simply become answer-everything. Locked as drafted (user ratification §12).

Rationale for splitting the gate: an abstaining policy has two independent virtues
— *quality when it answers* (a) and *not abstaining too much or too little* (b).
Folding them into one paired metric (Stage-S) let one silently destroy the other.

### 6.7 The confidence calibration gate (promotes the scalar to a gated surface)

Stage-S gated the scalar only for validity + non-collapse. Because the redesign
makes the scalar the sole carrier of graded uncertainty (and the driver of the
§7 rendering rule), the scalar must now demonstrably *rank and calibrate*:

- **(a) Discrimination — AUROC ≥ 0.62 (LOCKED).** On attempted rows, AUROC of
  `answer_confidence` against `is_correct(emitted answer, gold)`. Tests whether
  higher stated confidence ranks correct attempts above wrong ones — the property
  the rendering band (§7) relies on. This is *not* circular: the scalar's SFT
  target came from the frozen probe's k, but the discrimination label is the
  *freshly decoded SFT model's own answer* graded against gold.
- **(b) Calibration — ECE < 0.30 (LOCKED).** Bucket attempted rows by stated
  confidence; ECE = Σ (n_b/N)·|mean_conf_b − empirical_correctness_b|. Reference is
  the model's own emitted-answer correctness (a fresh draw, not the training k),
  so this is a genuine calibration test.

Both bars are the verbatim precedent from `contrastive-sft-behavior-conditional-confidence`
§4.1 (a **borrowed anchor for cross-experiment comparability**, following the same
convention the separability pre-test used for its BB bar; not a claim the two
constructions have matched statistical power). Aspirational tightenings (AUROC
0.70, ECE 0.15) are noted but are **not** the bar. **This gate is a HARD success
requirement, co-equal with recall and noninferiority** (user ratification §12):
the working confidence scalar is a design pillar — it feeds the §7 rendering rule
— so non-discriminating confidence is a design failure, not a soft miss.
Monotonic-bucket-accuracy (empirical correctness non-decreasing across confidence
buckets, with tolerance) is reported as a descriptive companion.

## 7. QUALIFY as an inference-time rendering rule (product layer, ungated)

QUALIFY is **not** a trained class, not a token, and not a gated surface. It is a
documented product-layer convention applied *after* generation, entirely outside
the trained/gated instrument:

> On an `<ANSWER>` response, inspect `answer_confidence`. If it falls in the hedge
> band **[0.35, 0.65)**, wrap the visible answer in the hedged rendering ("My best
> answer is ⟨answer⟩, but I am not certain."); at ≥ 0.65 render the answer plainly;
> `<ABSTAIN>` responses render the honest decline (no answer to hedge).

The band's default endpoints are the former QUALIFY k-range mapped through the
Jeffreys target: k=11 → 11.5/33 = 0.348, k=21 → 21.5/33 = 0.652, i.e. ≈ [0.35,
0.65). This reproduces a **three-tier presentation** (decline / hedged-answer /
plain-answer) from a **two-tier policy plus one scalar**. It is explicitly out of
scope for every gate in §6, carries no falsifier, and can be re-tuned as a
product decision without touching the trained checkpoint. Documented here so the
provenance of the hedge band is on record.

## 8. Prediction

The two-way fresh SFT will, on the dev split: emit valid native `<ANSWER>`/
`<ABSTAIN>` tokens and JSON (≥95%); achieve two-sided 95% Wilson recall lower
bound > 0.5 for **both** modes while abstaining **less** than Stage-S (dev
abstention rate near the true 0.332, inside [0.22, 0.42]); preserve the two-token
forced-posture contract; pass answer-quality noninferiority **on attempted rows**
(paired CI lower > −0.10) because it attempts the middle band as base does; keep
the confidence scalar valid and non-collapsed (SD ≥ 0.10); and clear the new
confidence calibration gate (AUROC ≥ 0.62, ECE < 0.30) because the retained middle
band populates the scalar's mid-range. Net: removing the impossible QUALIFY class
while preserving the middle in the scalar eliminates **both** Stage-S failure
modes.

## 9. Falsifier

Stop this SFT checkpoint (it does not qualify for any downstream experiment) if
any of: either mode's two-sided 95% Wilson recall lower bound ≤ 0.5; the native
first-token / JSON / two-token forced-posture contract fails; the dev abstention
rate falls outside the pre-registered band; attempted-row noninferiority CI lower
≤ −0.10; or the confidence calibration gate fails (discrimination AUROC < 0.62 or
ECE ≥ 0.30 at the locked bars).

**Distinguishing negative:** if the checkpoint *still* over-abstains (abstention
rate above the band's upper bound) even with the middle band trained as ANSWER,
that is an informative result — it would show the over-abstention is a deeper
training dynamic, not a labeling artifact, and would redirect the program away
from label-mapping fixes.

This falsifier adjudicates only checkpoint qualification, not any GRPO hypothesis.

## 10. Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | (registered pre-CODE 2026-07-24, recorded verbatim at sign) FULL SUCCESS — all hard gates pass: per-mode recall, attempted-row noninferiority + abstention band, calibration AUROC/ECE, anti-collapse, format. If anything misses, the calibration limb (AUROC ≥ 0.62 / ECE < 0.30) is the most likely single miss. |
| user | (registered pre-CODE 2026-07-24 via lead AskUserQuestion, recorded verbatim at sign) OVER-ABSTENTION RECURS — the abstention-rate band [0.22, 0.42] or the attempted-row noninferiority limb fails again despite the option-(ii) relabel, i.e. the Stage-S drag was not just a labeling artifact. |
| drafter | (registered at CODE-complete 2026-07-24, unsigned) Builder reproduces the frozen split exactly (train 9,556/8,641, dev 200/402), zero `<QUALIFY>` tokens, held-out sealed (0 rows parsed); 40/40 CPU tests green; awaits sign + local RTX 3090 slot behind the j-space pipeline. |

Head-to-head split (orchestrator vs user), as on the qwen3-4b atlas cell.
Adjudication at resolve is against the locked §6 gates only; these calls are
directional bets, never gate modifications.

## 11. Instrument (files `exp sign` will pin)

Config drafts written in this directory (design-complete, review-ready):
`dataset_builder.yaml`, `training.yaml`, `sft_recipe.yaml`, `qualification.yaml`,
`cell.yaml`, `gates.yaml`.

Modules (each a copy-and-modify of the named Stage-S source; declared with
persistence in `experiment.yaml`): `build_dataset.py` (relabel-in-place two-way
builder — §3, §3.1), `test_build_dataset.py`, `prepare_training.py` (from
`prepare_stage_s.py`), `test_prepare_training.py`, `qualify.py` (from
`qualify_stage_s.py`; adds gates #6a/#6b/#8), `test_qualify.py`. No
`modal_qualify.py` — local RTX 3090 lane (§4.1 item 7).

## 12. Ratifications and changelog

**2026-07-24 — design ratified; all bars LOCKED (lead adjudication + user
ratification, relayed via lead).** No goalpost may move after this without a new
signed revision with changelog.

- **QUALIFY-mapping: option (ii) ENDORSED** — fold the band into ANSWER at the
  existing k≤10 Clopper-Pearson boundary. The (i) and (iii) rejections (§3.1)
  are accepted as written.
- **All PROPOSED bars LOCKED as drafted:** anti-collapse ≤ 542/602;
  abstention-rate band [0.22, 0.42]; confidence population-SD floor 0.10;
  calibration discrimination AUROC ≥ 0.62; calibration ECE < 0.30.
- **Calibration gate (§6.7) is a HARD success requirement, co-equal** with
  per-mode recall and answer-quality noninferiority (not a demotable secondary).
  Rationale: the working confidence scalar is a design pillar — it feeds the §7
  QUALIFY rendering rule — so non-discriminating confidence is a design failure.
- **Calibration-gate row scope: attempted (`<ANSWER>`) rows only** — the clean,
  non-circular correctness label. Recording an ABSTAIN-appropriateness metric as
  a possible future secondary is fine as prose, not as a gate.
- **Hedge band [0.35, 0.65)** (§7) stays as documented — an ungated rendering
  rule, tunable post-hoc without a revision.
- **Lane: LOCAL RTX 3090**, queued behind the j-space cross-family pipeline. The
  Modal lane and `modal_qualify.py` are out of scope. Stage-S local-lane
  precedent recorded (§4.1 item 7).

Instrument bytes locked at these values in `gates.yaml`, `qualification.yaml`,
`training.yaml`, `dataset_builder.yaml`, `cell.yaml`. Scoreboard registration and
`exp sign` happen with the lead; training then waits its GPU turn behind j-space.

## 13. Outcome

Filled at resolve. Leave blank.
