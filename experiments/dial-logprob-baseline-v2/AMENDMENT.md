# Dial token-logprob baseline, clean redo (generation-time token-ID cache)

Status: RESOLVED (2026-08-13, machine state in `experiment.yaml`; see
Outcome -- LP-G0 data-stage stop, both arms). Header history: stale
boilerplate reading "draft (not signed)" corrected 2026-08-11 to `signed`;
updated again at resolution.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

Full design rationale, the line-by-line reading of v1's outcome, and the
constants-touched list live in the preparation draft this AMENDMENT was built
from: `docs/preparation/amendment-draft-dial-logprob-baseline-v2.md`. This
document is the condensed, signable form of that draft; where the two differ,
this file governs.

## Motivation and posture

**Builds on** `experiment:dial-logprob-baseline` (v1, resolved 2026-07-18,
verdict DATA-STAGE STOP; `experiments/dial-logprob-baseline/experiment.yaml:30-35`).

v1's own outcome (`experiments/dial-logprob-baseline/AMENDMENT.md:138-182`):
LP-G0's dial-reproduction and row-count sub-criteria both PASSED; the exact
answer-span round-trip sub-criterion FAILED on 30/3324 rows (14/1836 S,
16/1488 T; 0.9%), off by exactly one BPE token each. Root cause, confirmed by
reading the actual generation code (not just the outcome prose):
`experiments/common/readouts/amendment_s_correctness_probe_extract.py:253-266`
computes the exact generation-time answer-span token IDs (`new_ids`) in memory
during `model.generate()`, then discards them -- only the decoded `answer_text`
string is persisted to `rows.jsonl`. v1's harness had to invert that decode by
re-tokenizing text, which is not bit-stable at BPE span boundaries. Nothing
about the dial reproduction, the populations, the metric definitions, the
gates, or the falsifier was wrong in v1; the single defect was upstream of all
of that.

Descriptive-only numbers v1 computed for transparency, NOT gated
(`AMENDMENT.md:154-163`): S base arm (n=1822, 498c/1324w) dial 0.8338 vs
primary logprob 0.8198, margin **+0.014**, paired 95% CI **[-0.011, +0.040]**
(inside the pre-stated ambiguous band). T deployed arm (n=1472, 979c/493w)
dial 0.8183 vs primary logprob 0.6608, margin **+0.158**, CI **[+0.122,
+0.192]**. v1's own pre-run blind guess (logprob AUROC 0.60-0.72) was WRONG
(`AMENDMENT.md:165-175`).

**Motivated by** `papers/paper-4-two-signal-readout/manuscript.md` item 9
(`manuscript.md:1252-1274`), which already carries v1's descriptive numbers
with the round-trip caveat and states the charter for this cell verbatim: "A
gated version of this comparison needs a successor cell that caches
generation-time token IDs; until then, what this paper establishes about the
dial on the raw base remains its cross-model geometry, its post-answer read
advantage, and its veto behavior, not that it beats the model's own logprobs
there." (Note: the commissioning brief for the design draft cited a stale
"limitation 8 / SWAP marker" framing; the splice using v1's descriptive
numbers had already happened by the time this cell was drafted -- it is now
item 9, not a pending marker.)

**Posture:** exploratory Tier-2 lab cell over existing populations, mirroring
v1's own posture verbatim. Never pooled with the locked Phase 1 matrix or with
the S/T headline readings.

**PI ruling (2026-08-11):** registered from the design draft with the draft's
sec.7 recommendation adopted -- this cell is framed as a **confirmation cell**,
not a fresh blind guess (see Prediction below).

## Design

Full method: `cell.yaml` (pinned instrument), condensed here.

**Populations and arms, inherited verbatim from v1** (`experiments/dial-logprob-baseline/AMENDMENT.md:43-56`):

- Arm 1 (primary), `s_base_primary`: amendment S Instruct-base population,
  1836 rows expected (500 correct / 1336 wrong per the source inventory),
  `unsloth/Qwen3-4B-bnb-4bit`, no adapter, dial layer L20, dial signed AUROC
  0.834, gated by LP-G1.
- Arm 2 (deployed, descriptive), `t_deployed_descriptive`: amendment T
  answered population, 1488 rows expected (988 correct / 500 wrong),
  clean-SFT merged-16bit base + GRPO-v2 LoRA adapter, dial layer L22, dial
  signed AUROC 0.819, descriptive only, no gate.

**The fix (design draft sec.3.2/3.3), the only substantive method change from
v1:** replace v1's two-step "reconstruct sequence from decoded text, then a
separate teacher-forced forward pass" with ONE
`model.generate(..., output_scores=True, return_dict_in_generate=True)` call
per row. `gen.sequences` gives the exact generation-time answer-span token IDs
directly (never re-tokenized); `gen.scores` gives the per-step logits a
separate teacher-forced pass would otherwise have to recompute, and under
greedy decode (`do_sample=False`) these are mathematically identical. Every
other generation kwarg (`max_new_tokens=48`, `do_sample=False`, `num_beams=1`,
the per-arm `eos_token_id`/`pad_token_id` discovery, the render: same chat
template and system prompt as the source cell's own run manifest, imported by
reference from `amendment_s_correctness_probe_extract.SYSTEM_PROMPT` /
`amendment_t_correctness_readout_deployment_extract.SYSTEM_PROMPT` rather than
retyped) is inherited verbatim from the S/T extractors so regeneration
reproduces the original generation, not a different one. Generation runs
batch-1, matching the source extractors' own batch-1 loop, to maximize the
chance of exact bit-for-bit reproduction under greedy decode.

**LP-G0's round-trip sub-criterion, redefined (design draft sec.3.3):** the
regenerated `answer_text` (decoded from `new_ids`, the harness's own
generation-time output, never re-tokenized) must equal the row's cached
`answer_text` field byte-for-byte, for every row. Any mismatch is a
data-stage stop, not a result -- the same no-tolerance-improvised-after-seeing-
results discipline v1 used. This is a *stronger* check than v1's: v1's
round-trip could pass on a row whose token *identities* differed as long as
the *count* matched; v2's compares content directly.

**Everything else in the method -- logprob variants (primary: length-
normalized mean answer-span token logprob; secondary, descriptive only: sum
and min), AUROC scoring, the dial refit (reusing `oof_probe` /
`load_position_layers` from `amendment_s_correctness_probe_score.py`
UNCHANGED, at the source cell's own dial layer, asserted to reproduce the
signed AUROC before any comparison is unblinded), and the paired bootstrap
dial-minus-logprob margin (`paired_bootstrap_delta`, reused unchanged) --
transfers verbatim from v1** (`AMENDMENT.md:58-82`).

**Harness module:** `lp_v2_harness.py` (this directory). `run_arm` performs
the regenerate-and-capture step with incremental, resumable per-row
persistence (`analysis/<arm>/runlog/<arm>.jsonl`, append+flush per row --
`RunLog` from the synaptic-tuner submodule is unavailable on the current pin,
see `experiment.yaml:instrument.persistence` note, so this reimplements the
same append+resume contract locally rather than checking out a different
submodule branch). `score_arm` is CPU-only and reads the arm's EXISTING
cached hidden-state tensors for the dial refit -- it needs no model and does
not touch the GPU. `--dry-run` resolves every real input named in `cell.yaml`
and prints the execution plan without loading a model or computing anything
(exit 0 if every input resolved, exit 2 if any did not -- see the module's
own docstring for the full CLI contract).

**Containment (verbatim from v1):** committed artifacts are aggregate
AUROC/margin/CI JSON plus a per-variant table under `analysis-committed/`, and
an ID-manifest (row_key list only). Per-row logprobs, per-row token IDs,
regenerated text, per-step logits, and per-row dial scores stay gitignored
under `analysis/`. No question, answer, alias, or token-id content in any
committed file or fixture -- this repo is public. No OpenMOSS or bridge data
is involved.

## Prediction

**Confirmation cell, not a fresh blind guess (PI-adopted, design draft sec.7).**
A fresh blind prediction is not honestly possible here: v1's own descriptive
numbers are already known and are cited above in Motivation, so re-stating
v1's already-falsified blind call (0.60-0.72) as this cell's prediction would
not be a genuine pre-registration. The stated prediction is instead that v1's
descriptive read holds at exact (gated) precision: the S base arm's primary
logprob AUROC lands close to v1's descriptive 0.8198 (+/-0.02), landing margin
near +0.014 -- most likely still inside the pre-stated LP-G1 ambiguous band,
i.e. LP-G1 most likely does NOT pass. The T deployed arm (descriptive only)
is expected to confirm v1's +0.158 [+0.122, +0.192] margin within noise.
Falsifier and LP-G1's threshold/ambiguous band are untouched by this framing
(see Gates) -- only what counts as "the orchestrator's guess" changes, from a
re-guess to an explicit statement that the redo is expected to confirm v1's
own descriptive read at exact precision.

## Falsifier

Two independent falsifiers, both reported straight regardless of which fires:

1. **Dial-novelty falsifier (verbatim from v1,
   `experiments/dial-logprob-baseline/gates.yaml:16`).** Primary-variant
   logprob AUROC at or above the dial AUROC on the S base arm (margin at or
   below 0), paired 95% CI excluding 0 in that direction. This would show the
   dial's separation is largely redundant with free sequence probability.
2. **Confirmation falsifier (new for v2, PI-adopted).** The gated S-arm
   margin/CI lands materially outside v1's descriptive band
   [-0.011, +0.040], OR the gated T-arm margin/CI lands materially outside
   v1's descriptive band [+0.122, +0.192] (materiality: a gated point
   estimate outside the cited band, or a gated CI that does not overlap it).
   Either would mean this redo's own exact-precision measurement overturns,
   rather than confirms, the read that motivated running it -- itself a real
   and reportable finding (it would mean the round-trip-failing 0.9% of rows
   were disproportionately informative), not a design failure.

## Gates

Full thresholds: `gates.yaml`. In summary:

- **LP-G0 (integrity precondition, pre-outcome stop).** (a) refit dial
  reproduces signed source AUROC per arm (S 0.834 at L20, T 0.819 at L22)
  within reporting precision (tolerance 0.002, matching v1's own observed
  0.0002/0.0004 reproduction gap) -- unchanged from v1. (b) row counts match
  source inventories (1836 S; 1488 T) -- unchanged. (c) **redefined**:
  regenerated `answer_text` matches cached `answer_text` byte-for-byte for
  every row (see Design) -- any mismatch is a data-stage stop, not a result.
- **LP-G1 (primary, verbatim from v1).** dial AUROC minus primary-logprob
  AUROC >= +0.05 on the S base arm, paired 95% CI excluding 0. Floor matches
  the S/T self-eval-gain convention.
- **Ambiguous band (verbatim from v1).** 0 < margin < +0.05, or CI straddling
  0 -> reported as "small or uncertain margin over sequence probability"; the
  gate is not retuned after the result.
- **Arm 2 (verbatim from v1).** Reported with identical statistics,
  descriptive only, no gate.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Confirmation framing (see Prediction): S base margin near +0.014, inside the ambiguous band, LP-G1 most likely does NOT pass; T deployed margin confirms near +0.158. (recorded pre-run) |
| user | PI ruling 2026-08-11: adopted the confirmation-cell framing from the design draft's sec.7 recommendation; falsifier and LP-G1 bands transfer verbatim. |

## Outcome

Resolved 2026-08-13, PI-approved. **LP-G0 data-stage stop, both arms — no
result, per the registered pre-outcome rule.** The confirmation question
remains open.

- S base: LP-G0 (a) FAIL, dial refit 0.8395 vs signed 0.834 (|diff| 0.0055
  against the 0.002 tolerance); (b) PASS, 1836/1836 rows; (c) FAIL, 282/1836
  rows (15.4%) fail the byte-for-byte answer_text round-trip.
- T deployed: (a) FAIL, 0.8164 vs signed 0.819 (|diff| 0.0026); (b) PASS,
  1488/1488; (c) FAIL, 93/1488 (6.3%) round-trip failures.

Per the registered discipline ("any mismatch is a data-stage stop, not a
result"), the downstream margins the harness computed before halting are not
results and are not cited here; both committed JSONs carry
gate_verdict.stopped_at_lp_g0 = true as the sole reportable verdict.

Reading, recorded as hypothesis and not finding: the cached generations date
from the June stack; the run executed under torch 2.10.0+cu128 with the S
checkpoint loaded offline from the as-cached snapshot. Exact greedy-decode
reproduction through 4-bit quantized kernels across a stack upgrade is the
natural suspect for both the round-trip failures and the refit tolerance
misses. No diagnostic was run behind the stop.

One-sentence summary (manifest `verdict:`): both arms stopped at the LP-G0
integrity gate (dial-refit reproduction outside tolerance; 15.4% / 6.3%
byte-for-byte round-trip failures), so the cell records a data-stage stop
with no reportable comparison, the same verdict class as v1.
