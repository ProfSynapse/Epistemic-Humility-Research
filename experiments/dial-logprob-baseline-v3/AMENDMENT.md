# Dial token-logprob baseline v3: fresh self-consistent generation, no reproduction bet

Status: DRAFT — not signed. Registered content below is frozen at signing.

## Question

Verbatim from v1 and v2, unchanged: does the fitted correctness dial beat the
model's own sequence probability (primary variant: length-normalized mean
answer-span token logprob) at ranking the correctness of the model's own
answers, by at least the registered margin?

## Why a v3, and what it changes

v1 (resolved 2026-07-18) and v2 (resolved 2026-08-13) both recorded
data-stage stops without a reportable comparison, and both failed the same
way: each bet on exactly reproducing PAST generations. v1 re-tokenized
decoded text (30/3324 rows off by one token at BPE span boundaries); v2
regenerated months-old cached rows byte-for-byte under a newer
torch/CUDA/quantization stack and missed on 282/1836 (S) and 93/1488 (T)
rows, with the dial-refit reproduction outside its 0.002 tolerance on both
arms (0.0055 / 0.0026). The failure point is the reproduction bet, never the
comparison itself.

v3 removes the bet: ONE self-consistent run generates fresh answers under
the current pinned stack, capturing generation-time token IDs and per-token
logprobs in the same `model.generate(..., output_scores=True)` call and
extracting the dial's hidden states from the same run. Every quantity —
answer text, correctness label, dial score, logprob variants — derives from
one generation event on one stack. There is no external artifact to
round-trip against, so the entire v1/v2 failure class is designed out
rather than tolerated.

What does NOT change (no-goalpost discipline): the question, the primary
gate LP3-G1 (threshold, direction, CI rule verbatim from v1/v2), the
ambiguous band, the primary/secondary logprob variant definitions, the
paired-bootstrap statistic, and the T arm's descriptive-only posture.

## Design

- Arms, verbatim population sources: S base (`unsloth/Qwen3-4B-bnb-4bit`,
  as-cached snapshot, offline load) over the amendment-S prompt inventory;
  T deployed (clean-SFT merged-16bit + GRPO-v2 adapter, the pinned local
  dirs from v2's cell.yaml) over the amendment-T prompt inventory. Prompts,
  chat template, and system prompt imported by reference from the source
  extractors, as in v2.
- Generation engine: pinned vLLM (version frozen at signing), per the
  standing backend-selection discipline (experiment-runner
  reference/batched-generation.md: new unsteered generation surfaces
  default to pinned vLLM; v1/v2's HF-batch-1 inheritance was a
  parity-locked requirement that dies with the reproduction bet). Greedy
  decode, EOS-enabled, batch invariance enabled, `enable_thinking=False`
  pinned explicitly through the chat template (the known VLLMGenerator
  enable_thinking pin concern). Generation-time token IDs are native vLLM
  outputs; per-token logprobs captured via the engine's logprobs interface
  in the same request. S arm loads the as-cached bnb-4bit checkpoint via
  vLLM bitsandbytes quantization; T arm loads merged-16bit plus the pinned
  LoRA adapter via vLLM LoRA support.
- Hidden-state extraction, primary path: the SAME vLLM call returns
  per-token hidden states at the arm's signed dial layer (S L20, T L22) —
  the current vLLM release exposes intermediate hidden states at
  generation time (PI, 2026-08-13), so IDs, logprobs, and dial inputs all
  come from one pass of one engine. The harness build verifies this
  capability against the pinned vLLM version BEFORE signing; the verified
  path is frozen into cell.yaml.
- Hidden-state extraction, registered fallback (used only if the build
  verification finds the pinned version cannot expose the dial layer's
  per-token hidden states): a teacher-forced transformers forward pass
  over each row's captured token IDs (prompt + generated, verbatim) at the
  same layer. The pass consumes the IDs as given — nothing is regenerated,
  so no reproduction bet enters either way; which path ran is recorded in
  the provenance header.
- Labels: correctness scored on the fresh answers with the source cells'
  own scorer, imported by reference, unmodified.
- Dial: out-of-fold refit on the fresh rows' hidden states, reusing
  `oof_probe` / `load_position_layers` from
  `experiments/common/readouts/amendment_s_correctness_probe_score.py`
  UNCHANGED.
- Comparison: dial OOF AUROC vs primary logprob AUROC over the identical
  answered-row set; paired bootstrap margin (`paired_bootstrap_delta`,
  unchanged; n_boot and seed pinned in cell.yaml). Secondary variants (sum,
  min) descriptive only.
- Environment: single pinned stack recorded in the run provenance header
  (vllm/torch/transformers/bitsandbytes versions + checkpoint
  fingerprints); generation, extraction, and scoring all execute inside
  one run on one stack — nothing spans a stack boundary or a calendar
  boundary.

## Gates

- **LP3-G0 (integrity precondition, pre-outcome stop; internal consistency,
  no reproduction clause).** (a) capture integrity: for every row, the
  answer text decoded from the captured vLLM token IDs is the same object
  scored and logprob'd, and the teacher-forced extraction pass consumed
  exactly those IDs (asserted per row) — any divergence is a harness bug
  and a stop; (b) coverage: every prompt in each arm's source inventory is
  attempted and receives a recorded disposition; (c) power floor,
  pre-stated: at least 1,000 answered (label in {correct, wrong}) rows per
  arm, else the arm records a data-stage stop (source answered counts were
  1836 / 1488; 1000 is a power floor, not a tuned threshold); (d) instrument
  sanity, pre-stated: the fresh S-arm dial OOF AUROC is at least 0.75, else
  the cell records instrument-void (the signed June value was 0.834; 0.75 is
  a sanity bound on "the dial reads at all on fresh data").
- **LP3-G1 (primary, verbatim from v1/v2).** Dial AUROC minus primary-
  logprob AUROC >= +0.05 on the S base arm, paired 95% CI excluding 0.
- **Ambiguous band (verbatim).** 0 < margin < +0.05, or CI straddling 0 ->
  "small or uncertain margin over sequence probability"; not retuned after
  the result.
- **T arm (verbatim).** Identical statistics, descriptive only, no gate.

## Prediction

Disclosure, per the v2 precedent: a fresh blind guess is not possible. v1's
descriptive read and v2's non-result unblinded numbers (computed behind the
LP-G0 stop and not citable as results) have both been seen by the
registrants. The stated prediction: the S base margin lands inside the
ambiguous band (near +0.02, between 0 and +0.05) with LP3-G1 most likely
NOT passing; the T deployed margin lands clearly positive, near +0.15.

## Falsifier

(1) Dial-novelty falsifier, verbatim from v1/v2: primary-variant logprob
AUROC at or above the dial AUROC on the S base arm (margin <= 0), paired
95% CI excluding 0 in that direction. (2) The fresh-generation posture
fails its own integrity gate (LP3-G0) — which would show the failure class
was never reproduction at all and send the design back for diagnosis
rather than a fourth run of the same shape.

## Budget

vLLM batched greedy generation over ~3,324 prompts across two arms plus a
teacher-forced extraction pass, local RTX 3090: estimated well under 2 GPU
hours (vLLM collapses the generation cost; the extraction pass is
forward-only). CPU scoring and bootstrap: minutes. vLLM is not installed
in the current local env; the harness build pins and installs the frozen
version (or runs in a pinned image) before the run.

## Outcome

Filled at resolve.
