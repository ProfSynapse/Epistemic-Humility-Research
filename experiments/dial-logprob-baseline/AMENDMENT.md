# Dial token-logprob baseline (LP)

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 4 limitation 8 (`papers/paper-4-two-signal-readout/manuscript.md`, "No
token-logprob baseline for the dial") states the open gap this cell closes: the
correctness dial has a question-surface text baseline below it (0.75-0.78 per
family, paper 4 section 4.11) but has never been benchmarked against the
cheapest internal competitor, the model's own token log-probabilities on the
answer span. Sequence probability is a real within-dataset correctness signal
(Zenn and Geiping 2026: within-dataset probability-correctness Pearson r 0.66
base / 0.59 post-trained across 12 models x 6 datasets x 8 decode methods;
recorded in
`experiments/correctness-confidence-probe/analysis-committed/logprob_baseline_report_2026_07_10.md`).
Until this baseline is computed, the dial's margin over sequence probability is
unquantified.

The baseline is not computable from cache: the 2026-07-10 CPU inventory
(same report) established that the amendment S extraction saved hidden states
but never output scores or logits, so a new teacher-forced forward pass is
required. Under greedy decode, teacher-forced logprobs equal the
generation-time token logprobs exactly, so the re-forward reproduces sequence
probability deterministically.

Reference dial numbers this cell compares against (read this session):
post-generation correctness AUROC 0.834 on the Qwen3-4B Instruct base at L20
(`experiments/correctness-confidence-probe/AMENDMENT.md` section 7) and 0.819
on the deployed clean-SFT to GRPO-v2 checkpoint at L22
(`experiments/correctness-readout-deployment-port/AMENDMENT.md` section 7).

Posture: exploratory Tier-2 lab cell over existing populations. Never pooled
with the locked Phase 1 matrix or with the S/T headline readings. The
deliverable, gated or not, is the dial-minus-logprob margin with CI, which is
exactly what paper 4 limitation 8 asks to quantify.

## Design

Substrate and populations (both arms, PI-adjudicated 2026-07-18):

- Arm 1 (primary): the amendment S Instruct-base population. Rows:
  `archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2/rows.jsonl`
  (1836 answered rows, 500 correct / 1336 wrong per
  `experiments/correctness-confidence-probe/analysis-committed/inventory_result_2026_07_10.json`;
  fields `question`, `answer_text`, `answer_tok_len`, `prompt_len`, `correct`
  verified present). Model: the same Instruct base the S run used, at the
  revision recorded in the S run manifest (pinned at sign).
- Arm 2 (deployed): the amendment T answered population (988 correct / 500
  wrong) from
  `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/rows.jsonl`,
  scored under the clean-SFT merged-16bit base plus GRPO-v2 adapter (both on
  disk under `scratch/schema_response_confidence/runs/`, pinned at sign).

Method per arm:

1. Reconstruct the exact prompt+answer token sequence per row from the cached
   fields using the same chat template and system prompt recorded in the run
   manifest of the source cell.
2. One teacher-forced forward pass per row; log-softmax over the vocabulary;
   gather the log-probability of each realized answer-span token (positions
   `prompt_len` through `prompt_len + answer_tok_len`).
3. Logprob variants, pre-registered: PRIMARY is the length-normalized mean
   answer-span token logprob (the dial's own veto decomposition controls for
   answer length, paper 4 section 4.4, so the fair competitor must not win or
   lose on length alone). Secondary, descriptive only: sum (raw sequence
   logprob, length-confounded) and min token logprob (weakest link).
4. Each variant scored as AUROC for correct(1) vs wrong(0), higher logprob
   read as more likely correct, over all rows in the arm. No fit, so no CV.
5. Dial per-row scores recovered by re-fitting the source cell's probe on the
   cached hidden states with the source cell's own out-of-fold procedure
   (`amendment_s_correctness_probe_score.py` lineage), at the source cell's
   best layer (S: L20; T: L22), asserted to reproduce the signed AUROC before
   any comparison is made (integrity precondition, mirrors the corrigendum
   discipline).
6. Paired comparison: dial AUROC minus primary-logprob AUROC with a paired
   bootstrap 95% CI (2000 resamples over rows, seed pinned at sign), mirroring
   amendment S's own delta-CI method.

Containment: committed artifacts are aggregate AUROC/margin/CI JSON plus a
per-variant table under `analysis-committed/`, and an ID-manifest (row_key
list). Per-row logprobs, answer text, and per-row dial scores stay gitignored
under `analysis/`. No question, answer, alias, or token-id content in any
committed file. No OpenMOSS or bridge data is involved.

Cost: 1836 + 1488 teacher-forced forwards on the local RTX 3090, batched;
about 1 GPU-hour total including model and adapter loads and the mandatory
GPU smoke. GPU launch pre-approved by the PI (2026-07-18).

## Prediction

The length-normalized answer-span logprob baseline lands meaningfully above
chance but well below the dial on the primary arm: logprob AUROC roughly
0.60-0.72, and the dial-minus-logprob margin is positive with the paired 95%
CI excluding 0. Rationale: Zenn and Geiping predict a real within-dataset
signal (hence above 0.50), but the dial reads a post-answer self-evaluation
state that raw output probability does not encode (amendment S section 7
scientific reading), hence a positive margin.

## Falsifier

Primary-variant logprob AUROC at or above the dial AUROC on the primary arm
(margin at or below 0) with the paired 95% CI excluding 0 in that direction.
This would show the dial's separation is largely redundant with free sequence
probability and would materially weaken the dial's novelty claim; it is
reported straight.

## Gates

- LP-G0 (integrity precondition, pre-outcome stop): the re-fit dial reproduces
  the signed source AUROC on each arm (S 0.834, T 0.819) within reporting
  precision before any logprob comparison is unblinded; row counts match the
  source inventories (1836; 1488); the reconstructed sequences round-trip the
  cached `prompt_len`/`answer_tok_len` fields exactly for every row (any
  mismatch is a data-stage stop, not a result).
- LP-G1 (primary): dial AUROC minus primary-logprob AUROC >= +0.05 on the
  primary arm, paired 95% CI excluding 0. The +0.05 floor matches the
  self-eval-gain convention of amendments S and T (S section 4 G2; T section 4
  T-G2), keeping the "meaningful margin" bar consistent across the dial's
  cells.
- Ambiguous band, pre-stated: 0 < margin < +0.05 or CI straddling 0 is
  reported as "small or uncertain margin over sequence probability" and paper
  4 carries that hedge verbatim; the gate is not retuned after the result.
- Arm 2 is reported with the same statistics, descriptive (no separate gate);
  it exists so the deployed dial 0.819 carries the same baseline context as
  the base dial 0.834.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | LP-G1 passes: primary logprob AUROC 0.60-0.72, dial margin positive with CI excluding 0. (recorded pre-run) |
| user | Approved the cell and pre-approved the GPU launch (2026-07-18) without recording a separate quantitative call. |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
