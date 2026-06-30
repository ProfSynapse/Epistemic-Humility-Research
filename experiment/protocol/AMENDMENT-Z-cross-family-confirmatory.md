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

_pending — runner appends one PASS/FAIL/INELIGIBLE block per family + a
cross-family roll-up table and the SUCCESS/FALSIFIER verdict._
