# Token-logprob baseline for the correctness dial: inventory result

**Date:** 2026-07-10. **Scope:** CPU-only inventory of cached artifacts for the
Amendment S ("correctness-confidence-probe") dial cell. Answers the reviewer
objection "why not just use output logprobs" for the correctness-dial claim
(post-gen AUROC 0.834; see `experiments/correctness-confidence-probe/AMENDMENT.md`
§7). No model was loaded, no GPU was touched, no generation was run.

## Result: NOT COMPUTABLE FROM CACHE

The cached extraction for Amendment S does not contain per-token logprobs,
logits, or generation scores anywhere in its outputs. A token-logprob
baseline over the dial's exact scored population cannot be derived from what
is on disk; it would require a new extraction run.

## What was checked

**Amendment doc read first (per program rule):**
`experiments/correctness-confidence-probe/AMENDMENT.md` §7 ("Result"). Dial
headline: best post-gen correctness-AUROC **0.834** (L20), best pre-gen
0.769 (L22), post−pre delta +0.065 (bootstrap 95% CI [0.040, 0.090], 2000
resamples paired over rows). Population: `n_answered = 1836` → **500
correct / 1336 wrong**, from a pooled PopQA + TriviaQA-gold set (25,580
questions, shuffled seed `20260630`), Qwen3-4B Instruct base
(`unsloth/Qwen3-4B-bnb-4bit`, no adapter), greedy decode, graded by the
verbatim Cheng alias scorer.

**Cached artifact location (canonical checkout, gitignored — not present in
a fresh worktree):**
`experiment/phase1/probe/qwen3-4b-instruct/amendment_s/stage2/`
- `manifest.json` — confirms `n_answered=1836`, `n_correct=500`,
  `n_wrong=1336`, matching the amendment doc exactly (same run).
- `rows.jsonl` — 1836 lines, one per attempt. Full field set (enumerated by
  script, see below): `aliases_norm, answer_text, answer_tok_len, answered,
  config_sha, correct, dataset, label, prompt_len, question, refused,
  row_key`. **No logprob, logit, or score field of any kind.**
- `3672` `*.safetensors` files (2 per answered row: `__pre.safetensors`,
  `__post.safetensors`), each holding tensor keys `L0..L36` — the full
  residual-stream hidden-state vector (hidden_dim 2560) at exactly **two**
  token positions per row (the pre-gen anchor and the post-gen final content
  token). **No logits tensor, no per-position vocabulary distribution, no
  probability of any kind.**

**Extraction script read for what it computes vs. what it persists:**
`experiments/common/readouts/amendment_s_correctness_probe_extract.py`
- The generation call (`model.generate(..., do_sample=False, num_beams=1,
  return_dict_in_generate=True)`) does **not** pass `output_scores=True` or
  `output_logits=True`. Per-token generation scores were never materialized
  during decoding.
- The subsequent single re-forward pass over `[prompt + answer]`
  (`model(..., output_hidden_states=True, use_cache=False)`) does compute
  logits as an ordinary side effect of any causal-LM forward call, but the
  script reads only `out.hidden_states` — `out.logits` is never touched,
  never saved, and is discarded when the tensor goes out of scope. The
  information existed transiently in GPU memory during the original run and
  was not written to disk.

**Scoring script read for the same reason:**
`experiments/common/readouts/amendment_s_correctness_probe_score.py` — grep
for `logprob|logit|log_prob|output_scores` returns zero matches. The CPU
probe-fit stage never receives or expects probability information either.

**Verification script (deterministic, re-runnable):**
`experiments/correctness-confidence-probe/analysis-committed/inventory_logprob_baseline.py`
— read-only field/key enumeration over `rows.jsonl` and one representative
`*.safetensors` file. Output committed at
`experiments/correctness-confidence-probe/analysis-committed/inventory_result_2026_07_10.json`;
`conclusion: "NOT_COMPUTABLE_FROM_CACHE"`.

## What a future run would need to record

The re-forward pass in `amendment_s_correctness_probe_extract.py` already
walks the full `[prompt + answer]` sequence with `output_hidden_states=True`
— adding logprob capture there is nearly free (no additional forward pass
needed beyond what already runs):

1. In that same forward call, also read `out.logits` at each generated-answer
   position (`prompt_len .. content_end`), take `log_softmax` over the
   vocabulary dimension, and gather the log-probability of the actual
   generated token id at each position.
2. Persist per-row: the vector of per-token logprobs for the answer span (or
   at minimum the three summary statistics needed for a sequence baseline —
   mean, sum, min token logprob over the answer span), alongside the existing
   `rows.jsonl` record.
3. Alternatively, pass `output_scores=True` (or `output_logits=True`) directly
   to `model.generate`, which gives per-step scores at generation time without
   needing the second forward pass at all — but the current script structure
   already does a second forward, so option 1 costs nothing extra.

Either change would let a logprob baseline be computed on the exact same
1836-row population (same correct/wrong labels, same 500/1336 split) as the
dial, enabling a same-population comparison against the 0.834 headline. No
such run exists yet.

## Decode-sensitivity context (read before citing, per instruction)

`library/notes/2606.27359--when-likely-answers-right-sequence-probability-correctness.md`
("When are likely answers right? On Sequence Probability and Correctness in
LLMs", Zenn & Geiping) is relevant context for interpreting a future
computed baseline, not for this inventory result (nothing was computed
here). Its claims, as recorded in the library note:

- Within a fixed dataset and decode method, higher sequence probability is
  "often predictive of correctness" across different prompt-answer pairs,
  and this within-dataset probability-correctness correlation scales with
  task accuracy (Pearson r=0.66 base models, r=0.59 posttrained, regressing
  accuracy against within-dataset Spearman correlation across 12 models, 6
  datasets, 8 decoding methods — Figure 6).
- This does **not** transfer to decoding decisions: increasing sequence
  probability by changing decode hyperparameters or methods does not
  reliably improve accuracy.
- Sequence probability is **not** a good indicator of correctness for
  *repeated* responses to the *same* prompt (within-sample correlations are
  symmetric around zero, mean zero, across base and posttrained models;
  MATH500 is the only dataset with positive average within-sample
  correlation).

Amendment S used a single fixed decode setting (greedy, one attempt per
question) across many distinct questions — structurally the "within-dataset,
across prompt-answer pairs, fixed decode method" comparison type the note
reports as often positive, not the "within-sample, repeated-response" type
the note reports as null. This does not predict a specific AUROC; it only
says a future computed baseline is not a priori expected to be null under
this note's own findings. It should be read alongside the eventual computed
number, not substituted for it.

## Other baselines already in the program (for contrast, already computed — not this task's output)

`AMENDMENT.md` §4 records, as pre-existing anchors already in the program
(not computed in this task): chance 0.50, model's own **verbalized**
confidence 0.504, a **base emitted scalar** head 0.559, and the
**pre-generation answerability probe read as correctness** ≈0.64 (noisy, 27
wrong examples). None of these is a plain output-token-logprob baseline —
verbalized confidence is a self-report, the emitted scalar is a trained head,
and the pre-gen probe reads answerability not correctness. The reviewer's
specific objection (plain sequence logprob of the generated answer) has not
been computed anywhere in this program yet; this task established only that
it cannot be computed from what is currently cached.

## Files touched by this task

- `experiments/correctness-confidence-probe/analysis-committed/inventory_logprob_baseline.py`
  (new, committed) — deterministic, read-only inventory script.
- `experiments/correctness-confidence-probe/analysis-committed/inventory_result_2026_07_10.json`
  (new, committed) — its output against the canonical checkout's cached
  Amendment S stage2 artifact. Aggregate counts and field/key names only; no
  question text, answer text, or row-level content.
- This report.

No `AMENDMENT.md`, `NOTEBOOK.md`, `experiment.yaml`, or `gates.yaml` was
edited. No row-level data (questions, answers, aliases) appears in any
committed file above — only manifest counts and field/tensor-key names.

## Proposed NOTEBOOK.md entry (drafted here; not landed — lead lands it)

```
- 2026-07-10: CPU-only inventory (analysis/dial-logprob-baseline branch):
  checked whether a plain output-token-logprob baseline is computable from
  the cached Amendment S stage2 extraction
  (experiment/phase1/probe/qwen3-4b-instruct/amendment_s/stage2/) for
  comparison against the 0.834 post-gen dial headline. Result: NOT
  COMPUTABLE FROM CACHE — rows.jsonl and the safetensors hidden-state
  tensors carry no logits/logprobs/scores anywhere (extraction script never
  requests output_scores at generation time and discards out.logits from
  the post-hoc hidden-state forward pass). See
  analysis-committed/logprob_baseline_report_2026_07_10.md for the full
  inventory and what a future extraction would need to record to make this
  baseline computable on the same population.
```
