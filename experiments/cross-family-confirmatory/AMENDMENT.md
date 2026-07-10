---
amendment: Z
slug: cross-family-confirmatory
question: >-
  Does the training-free two-signal readout replicate across model
  families, or is it a Qwen3-lineage idiosyncrasy?
predictions:
  orchestrator:
    call: readout holds across families; veto PASS on at least 3 of 4
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  COMPLETE — SUCCESS; veto PASS 3/4 (Ministral, Qwen3.5, Gemma; Llama fails),
  gate and dial 4/4; readout promoted to a cross-family claim, veto the
  fragile model-dependent axis.
scoreboard: null
---

# Amendment Z — Cross-FAMILY confirmatory of the training-free two-signal readout

**Status:** PRE-REGISTERED (2026-06-30), training-free readout, local Docker GPU
lane. Registered BEFORE any extraction. This is the governed confirmatory
replication that would promote the [[AMENDMENT-W-base-model-training-free]] /
[[AMENDMENT-X-cross-model-size-sweep]] exploratory finding to a CLAIM.

Tier-2 amendment. One branch (`pr/amendment-z-cross-family`, stacked on the
unmerged X branch because the cross-model extraction/scoring scripts live there),
one PR. Gates LOCKED below before the first run; goalposts do not move after the
result.

## Why this experiment

W established (training-free) and X confirmed (size-robust 1.7B–14B) that the
two-signal trust readout — answerability **gate** (pre-gen) + correctness
**dial** (post-gen) + the dial **veto** on confident hallucinations — reads off a
**raw, untrained** instruct base. Every checkpoint tested so far is **Qwen3**.

The open confound is **family**: the readout's generality could be a Qwen3
architectural / pre-training idiosyncrasy rather than a property of instruct LMs
in general. X explicitly named cross-family as the deferred next axis. This
amendment is that axis: re-run the identical training-free readout on four
**different model families**, each a raw instruct base with NO adapter and NO
task training.

If the readout holds across families, the W/X mechanism graduates from
"Qwen3-specific" to a cross-family property — the condition for promoting it to a
claim.

## Models (the locked confirmatory set)

User-specified set (cross-family, ~3–4B scale to match X's small end). Exact HF
repos resolved 2026-06-30:

| Family | HF repo | Scale | Notes / risk |
|--------|---------|-------|--------------|
| Meta Llama | `unsloth/Llama-3.2-3B-Instruct` (ungated mirror; `meta-llama/Llama-3.2-3B-Instruct` accepted by user as fallback) | 3B | text-only, standard `LlamaForCausalLM` — lowest risk |
| Mistral | `mistralai/Ministral-3-3B-Instruct-2512` | 3B | Apache-2.0 (ungated); weights shipped FP8 — dtype-load risk |
| Google Gemma | `google/gemma-4-E4B-it` | E4B (~4B eff.) | Apache-2.0 (**ungated**, verified 2026-06-30) + **multimodal** (Gemma4 conditional-gen) — loader risk only |
| Alibaba Qwen | `Qwen/Qwen3.5-4B` | 4B | ungated + **multimodal** (native) — loader risk; cross-GENERATION control within Qwen |

**No HF token required for any of the four** (all ungated, verified 2026-06-30).
Remaining risk is purely technical (multimodal loader for Gemma/Qwen; FP8 dtype
for Ministral; whether the container's `transformers` recognizes the post-cutoff
Gemma4 / Qwen3.5 architecture classes), all caught by the per-model compat smoke.

Risk handling (pre-stated, not goalpost-moving): each model first passes a fast
**compat smoke** (small `--max-attempts`) that must (a) load, (b) emit a
hidden-states tuple of length `n_layers+1` with `hidden_dim == config hidden
size`, and (c) produce a non-degenerate answered pool. A model that fails the
smoke (gated 401, multimodal class mismatch the hardened loader cannot resolve,
FP8 dtype failure, or a degenerate pool) is **recorded as INELIGIBLE with the
explicit blocker** and excluded from the denominator — it is neither a PASS nor a
FALSIFIER hit. Silent substitution is forbidden; the blocker is logged in the
results JSON and the §7 roll-up.

## Hypothesis

**H-Z:** The training-free two-signal readout is family-general: on a raw instruct
base from a previously-untested family, the answerability gate, the correctness
dial, and the confident-hallucination veto each read out above chance.

## Locked gates (per ELIGIBLE model, identical to X)

- **Z-G1 (gate):** answerability AUROC ≥ 0.65, bootstrap 95% CI excludes 0.50.
- **Z-G2 (dial):** post-gen correctness AUROC (correct vs wrong answered) ≥ 0.65,
  CI excludes 0.50.
- **Z-G3 (veto, PRIMARY):** confident-hallucination veto AUROC (known-answered vs
  unknown-hallucination, dial trusts the former over the latter) ≥ 0.65, CI
  excludes 0.50.
- **Adequacy (per model):** ≥ 30 wrong AND ≥ 50 hallucination answered rows;
  otherwise the affected gate is UNDERPOWERED, not PASS/FAIL (reported, excluded
  from the verdict denominator for that gate only).

## Success / falsifier (LOCKED before running)

- **SUCCESS (promotes to a claim):** Z-G3 (PRIMARY veto) PASSES on **≥ 3 of 4**
  ELIGIBLE families, AND Z-G1 + Z-G2 PASS on those same families. (If fewer than
  4 are eligible, the bar is "all-but-one of the eligible set, minimum 3.")
- **FALSIFIER:** the PRIMARY veto FAILS its gate on **≥ 2 of 4** ELIGIBLE
  families. This would localize the W/X mechanism to Qwen3 / contradict
  family-generality, and the training-free readout would NOT be promoted to a
  cross-family claim.
- Scaling sharpness is **descriptive only** (X already showed it is
  non-monotonic); no sharpness threshold gates this amendment.

## Method (identical readout to X — no new training)

For each model, `amendment_x_cross_model_extract.py --base-model <repo>` (the only
per-model knob) builds the same mixed pool and persists pre/post hidden states:

- **Pool:** PopQA + TriviaQA answerable (graded → correct/wrong = the DIAL pool)
  + SelfAware known (gate positives + within-family control) + SelfAware unknown
  (forced answers → hallucinations = the VETO pool). Gate question set + known/
  unknown labels come from the shared SelfAware rows
  (`…/extraction__55254a04aa1f/rows.jsonl`); they are model-agnostic text, re-run
  through each new model.
- **Decode:** greedy, `enable_thinking=False`, system prompt identical to X,
  chat template via the model's own tokenizer.
- **Readout positions:** pre = anchor token (prompt_len−1); post = last answer
  content token. Hidden states float32 on CPU.
- **Scoring:** `amendment_x_cross_model_score.py --x-dir <out>` — CV linear
  readouts, layer-swept, 2000-bootstrap AUROC + CI per gate. CPU only.

`--seed 20260630`, `--n-answerable 2000`, `--max-attempts 3000`,
`--max-new-tokens 48`, `--wrong-floor 30`, `--hallucination-floor 50` (same as X).

### Loader hardening (this amendment)

`amendment_x_cross_model_extract.py` gains a backward-compatible
`load_model_and_config()` that (1) tries `AutoModelForCausalLM`, then falls back
to `AutoModelForImageTextToText` / `AutoModelForVision2Seq` for multimodal
families, and (2) reads `num_hidden_layers` / `hidden_size` from
`config.text_config` when the top-level config lacks them. Qwen3 behavior is
byte-for-byte unchanged (it loads via the first path). The compat smoke validates
the hidden-states shape so a wrong wrapper cannot masquerade as success.

## Run order (single GPU, sequential)

1. `unsloth/Llama-3.2-3B-Instruct` (lowest risk — first real data point)
2. `mistralai/Ministral-3-3B-Instruct-2512`
3. `Qwen/Qwen3.5-4B`
4. `google/gemma-4-E4B-it`

Each: compat smoke → (if eligible) full extraction → CPU score → append result +
update session/experiment notes. Failures logged; the queue continues.

## §7 Results (filled per model as runs complete)

**Status: COMPLETE — 4 of 4 scored (2026-06-30 overnight queue). VERDICT: SUCCESS.**
Veto PASS 3/4 (≥3/4 bar met). The training-free two-signal readout replicates
across model families and is promoted to a cross-family CLAIM.

### Cross-family roll-up (FINAL)

| model | hidden_dim | gate (G1) | dial (G2) | **veto (G3, PRIMARY)** | adequacy | verdict |
|---|---|---|---|---|---|---|
| Llama-3.2-3B | 3072 | 0.997 ✓ [.995,.999] | 0.861 ✓ [.844,.879] | **0.633 ✗ [.603,.665]** | ✓ (wrong 1205 / halluc 629) | **PARTIAL** |
| Ministral-3-3B | 3072 | 0.997 ✓ [.995,.999] | 0.818 ✓ [.797,.839] | **0.733 ✓ [.703,.762]** | ✓ (wrong 1314 / halluc 629) | **PASS** |
| Qwen3.5-4B | 2560 | 0.998 ✓ [.997,.999] | 0.827 ✓ [.806,.848] | **0.666 ✓ [.634,.695]** (marginal) | ✓ (wrong 1277 / halluc 629) | **PASS** |
| Gemma-4-E4B | 2560 | 0.998 ✓ [.997,.999] | 0.818 ✓ [.794,.840] | **0.871 ✓ [.850,.893]** | ✓ (wrong 1390 / halluc 629) | **PASS** |

**Veto tally (FINAL): 3 PASS (Ministral, Qwen3.5, Gemma-4) / 1 FAIL (Llama-3.2).**
Gate and dial pass on ALL FOUR families (gate saturated 0.997–0.998; dial
0.82–0.86) — those two axes are fully family-general (4/4). The veto passes 3/4,
meeting the pre-registered ≥3/4 SUCCESS bar. Honest notes, no goalpost moved:
Qwen3.5's veto is a **marginal** pass (point 0.666 ≥ 0.65 but CI lower bound 0.634
dips below the bar; it satisfies the locked criterion — point ≥0.65 AND CI
excludes 0.50 — but is not a clean margin); Llama-3.2 is a clean **fail** (real
signal, CI excludes 0.50, but below 0.65). Gemma-4 is the cleanest veto of the
set (0.871).

### VERDICT: SUCCESS

Per the pre-registered criterion (SUCCESS = veto PASS ≥3/4), the confirmatory
**PASSES**. The two-signal trust readout — answerability gate + correctness dial +
confident-hallucination veto, read training-free off a frozen base — **replicates
across four model families** (Qwen, Llama, Mistral, Gemma) and is promoted from
the W/X exploratory finding to a **cross-family claim**. Scope of the claim:
- **Gate + dial: robust (4/4).** Answerability at the anchor and correctness at
  the post-answer token are family-general, near-saturated for the gate.
- **Veto: replicates but is the fragile axis (3/4, one clean fail + one marginal).**
  Catching *confident* hallucination is the model-dependent capability — mirrors
  Amendment X, where the veto (not gate/dial) dipped non-monotonically with size.
  The claim is "the veto replicates across families," honestly qualified by the
  Llama miss and the Qwen marginality; it is NOT "the veto is uniformly strong."

### Emerging read (descriptive, no goalpost moved)

The **veto is the model-dependent axis**; gate + dial are family-general. The
descriptive dial means explain the split:

- **Llama (veto FAIL):** `dial_mean_hallucination = 0.476` sits near
  `dial_mean_correct = 0.707` — confident confabulations read almost as
  trustworthy as correct answers, so the dial cannot separate them. Within-
  SelfAware control weak (known-vs-halluc AUROC 0.575 [.543,.607]). The veto CI
  excludes 0.50 (a real but weak signal), it just misses the 0.65 pass bar.
- **Ministral (veto PASS):** `dial_mean_hallucination = 0.278` sits far below
  `dial_mean_correct = 0.605` — hallucinations read as low-trust. Control
  stronger (0.682 [.652,.712]).
- **Qwen3.5 (veto marginal PASS):** `dial_mean_hallucination = 0.425` vs
  `dial_mean_correct = 0.636` — intermediate separation, between Ministral's clean
  split and Llama's collapse. Control 0.649 [.617,.680].
- **Gemma-4 (veto strong PASS):** `dial_mean_hallucination = 0.089` vs
  `dial_mean_correct = 0.593` — the widest split of the set; confabulations read as
  near-zero trust. Strongest control too (0.816 [.790,.842]).

The four families order by exactly the quantity the veto measures — the
correct-vs-hallucination gap in the dial mean: Gemma 0.504 (strong pass) >
Ministral 0.327 (clean pass) > Qwen3.5 0.211 (marginal) ≈ Llama 0.231 (fail).
Note Llama's mean *gap* (0.707−0.476 = 0.231) slightly exceeds Qwen's yet Llama
fails and Qwen marginally passes — the veto AUROC depends on full distribution
overlap, not just the mean gap, so read the low end as directional, not a strict
rank. The stable conclusion: gate + dial are family-general (4/4); the veto
replicates (3/4) but is the fragile, model-specific axis.

This mirrors Amendment X, where the veto (not the gate/dial) was the axis that
dipped non-monotonically (softest at 14B). Consistent story: the answerability
gate and the correctness dial generalize across families; catching *confident*
hallucination is the fragile, model-specific capability.

### Data & provenance

- Scored result JSONs (tracked, at probe root), one per family:
  `amendment_z_{llama-3.2-3b,ministral-3-3b,qwen3.5-4b,gemma-4-e4b}_result.json`
  under `archive/experiment/phase1/probe/` (full per-layer AUROC surfaces + CIs +
  descriptives inside).
- Extraction outputs (local only, gitignored `z_<tag>/`): rows.jsonl +
  per-row `{pre,post}.safetensors` + manifest.json under
  `experiment/phase1/probe/z_{llama-3.2-3b,ministral-3-3b,qwen3.5-4b,gemma-4-e4b}/`.
- Queue log: `experiment/phase1/probe/z_logs/PROGRESS.log`
  (smoke → full → score milestones, timestamps, INELIGIBLE handling).
