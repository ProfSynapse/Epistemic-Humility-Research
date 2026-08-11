# Dial token-logprob baseline (LP)

Status: resolved 2026-07-18 (machine state in `experiment.yaml`); verdict
DATA-STAGE STOP, exactly as pre-registered (see AMENDMENT.md "Outcome" and
experiment.yaml `verdict:`). This header was stale boilerplate reading
"draft (not signed)" until 2026-08-11; corrected to match the machine
state, which was already `resolved`.

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

Resolved 2026-07-18. **LP-G0 DATA-STAGE STOP, exactly as pre-registered.**

LP-G0 sub-results: dial reproduction PASSED both arms (S re-fit 0.8342 vs
signed 0.834; T re-fit 0.8186 vs signed 0.819); row inventories matched
(1836; 1488); the exact sequence round-trip FAILED on both arms: 14/1836 (S)
and 16/1488 (T) rows, 0.9% pooled, re-tokenize the cached answer_text with an
answer-span length off by exactly one BPE token (prompt side exact on every
row, 28 of 30 short by one). The mechanism is the one the 2026-07-10
inventory pre-identified: generation-time token IDs were never cached, and
BPE re-tokenization of decoded text in isolation is not bit-stable at span
boundaries. Per the gate's own wording ("any mismatch is a data-stage stop,
not a result"), the stop fires; the harness made no attempt to force a match
and the gate is not reinterpreted after the fact.

Descriptive numbers (computed for transparency on the round-trip-clean rows,
NOT a gated result; independently re-derived by the lead from the per-row
artifacts, byte-identical):

- S base arm (n=1822, 498 correct / 1324 wrong): dial 0.8338, primary
  length-normalized logprob 0.8198, margin +0.014, paired 95% CI [-0.011,
  +0.040]. Inside the pre-stated ambiguous band; LP-G1 would not have passed
  and the falsifier would not have fired.
- T deployed arm (n=1472, 979 / 493): dial 0.8183, primary logprob 0.6608,
  margin +0.158, CI [+0.122, +0.192].

Prediction assessment, reported straight: the orchestrator call (base logprob
0.60-0.72) was WRONG on the base arm; sequence probability on the raw
Instruct base captures nearly all of the dial's separation (0.820 vs 0.834).
The directional picture the descriptive numbers suggest, subject to the
integrity caveat above: the dial's clear margin over the model's own sequence
probability appears on the DEPLOYED checkpoint (where training degrades the
logprob signal to 0.661 while the dial holds 0.818), not on the raw base.
Paper 4 limitation 8 may cite these as descriptive-with-caveat only; any
gated version of this claim needs a successor cell with generation-time token
IDs cached (or a tolerance pre-registered BEFORE seeing data), registered
fresh.

Gate ledger: LP-G0 FAIL (round-trip sub-criterion) -> data-stage stop; LP-G1
not evaluated as a gate (computed value margin +0.014, ambiguous band);
falsifier not fired. Artifacts:
`analysis-committed/lp_logprob_baseline_result.json` and
`lp_logprob_baseline_id_manifest.json` (aggregates and row_key lists only);
per-row artifacts gitignored under `analysis/`.
