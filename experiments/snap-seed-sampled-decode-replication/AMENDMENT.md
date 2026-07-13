# H3: Multi-Seed and Sampled-Decode Replication of the Doubt-Gated Caution Snap

Status: falsified (signed 2026-07-13; run complete on the local RTX 3090; falsifier FIRED, instrument-verified).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The doubt-gated caution snap resolved as an exploratory pass on the raw-base
Qwen3-4B substrate: gated confab clean_tighten 136/185 = 73.5% (Wilson 95% CI
[66.7%, 79.3%]) and gated known-correct false-refusal 8/258 = 3.1% (Wilson 95%
CI [1.6%, 6.0%]), with clean placebo controls
(`experiments/doubt-gated-caution-tighten/AMENDMENT.md` Outcome, lines 305-319,
read in full before drafting this). Every one of those numbers is a SINGLE
GREEDY DECODE: the resolved instrument's generation is
`do_sample=false, max_new_tokens=200, min_new_tokens=1, enable_thinking=false`
(that doc's Design, lines 100-105; `cell.yaml:surface.generation`). The headline
73.5%/3.1% pair is therefore established only under greedy decode on one run.

This experiment closes the cheapest credibility gap on the paper's central
number: it re-measures the SAME frozen instrument under (a) fresh seeds for the
stochastic harness elements and (b) a sampled-decode arm at the checkpoint's own
recommended sampling configuration, so the 73.5%/3.1% pair can be asserted
outside the phrase "one greedy decode" or explicitly re-scoped to it. The Paper 5
review memo names this as hardening item H3
(`docs/review/paper5-actuation-review-2026-07-10.md` lines 251-257). The memo
attributes to the program a precedent that greedy decode UNDERSTATES effects (it
cites a seed-robustness amendment referenced from the AA and AE records); that
precedent is treated here as motivation only and is NOT a gated number. Its
governed source must be read before the motivation is cemented at signing; this
draft does not rely on it.

Posture: exploratory replication, reported separately from the locked Phase 1
headline matrix and never pooled with it. It refits NOTHING. It reuses the frozen
instrument (directions, tau, standardization, held-out split) exactly as pinned
by the resolved snap cell; the only things this experiment varies are the decode
policy and the harness seeds. A replication that refit any direction or re-chose
tau would not be a replication of the resolved number.

## Design

Substrate: identical to the resolved snap cell. Raw-base untrained instruct
`unsloth/Qwen3-4B` (full bf16, no 4-bit quantization), no adapter
(checkpoint_tag "raw-base"), training-free.

Frozen instrument reused verbatim (no refit; consumed via `inputs:`):

- Held-out split: `experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`
  (the promoted ID-only manifest). Held-out sizes: confab 185, known-correct 258
  (`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 133-135).
- Doubt gate sensor `u_d`, snap write direction `c_hat`, and the G3(i) placebo
  `random_direction`: the committed
  `experiments/doubt-gated-caution-tighten/analysis-committed/{u_d_L34.json,c_hat_L34.json,random_direction_L34.json}`.
- Frozen gate threshold: `tau_frozen = 0.3026445054171378`, Youden-J on the FIT
  split, standardized with the FIT-pool `mu_d`/`sigma_d` from
  `analysis-committed/build_manifest.json`
  (`analysis-committed/gate_fit.json`). Not re-derived here.
- Snap law: `erase_write` along `c_hat` to a fixed realized projection
  `dose_target = 200.0` (readback units), scope `anchor_onward`. Fire rule:
  `neg_z_d >= tau`. Identical to the resolved cell.

Row text is materialized at run time by the resolved snap cell's own
`materialize_rows.py` scheme (private HF staging repo + local aliases), kept under
gitignored `analysis/`. No question, alias, or generation text is committed.

Two decode conditions, both over the SAME held-out rows and the SAME frozen
instrument:

1. **Arm R (greedy reproduction, instrument-validity anchor).** Exact re-run of
   the resolved gated pipeline: `do_sample=false`, `max_new_tokens=200`,
   `min_new_tokens=1`, `enable_thinking=false`. Greedy is deterministic given the
   frozen directions, so this arm should reproduce 73.5%/3.1% up to bf16/CUDA
   matmul nondeterminism across hardware. It is the anchor that certifies the
   replication harness is measuring the same instrument before any sampled number
   is interpreted.

2. **Arm S (sampled decode, primary).** Same gated pipeline, decode switched to
   the program's own registered sampled-decode configuration from Amendment SR
   (`experiments/sampled-decode-seed-robustness/AMENDMENT.md` lines 94-102, the
   governed precedent this hardening item invokes): `do_sample=true,
   temperature=0.7, top_p=0.9, num_beams=1` with `enable_thinking=false`
   unchanged from the resolved cell, generation RNG seeded per run. This is the
   established sampled-decode standard for exactly this genre (seed-robustness of
   a training-free readout). NOTE (flagged for signing): the Qwen3 published
   non-thinking sampling recommendation is a slightly different config
   (`top_p=0.8, top_k=20, min_p=0`); the SR precedent is chosen here for
   consistency with the program's other sampled-decode replications, but the
   user/PI may substitute the checkpoint-published config at signing. `N = 8`
   samples per held-out row, drawn under `K = 5` independent sampling seeds
   (20260710, 20260711, 20260712, 20260713, 20260714). Per-row conversion is
   scored three ways, all pre-stated:
   - **majority-vote (primary):** a confab row counts CONVERTED iff `>= 5` of its
     8 samples are `clean_tighten` refusals; a known-correct row counts DAMAGED
     iff `>= 5` of 8 samples are not `well_formed_correct`. A 4-4 tie counts as
     "instrument did not act" (not converted; not damaged).
   - **any-vote (reported envelope):** converted iff `>= 1` of 8 samples is
     `clean_tighten`; damaged iff `>= 1` of 8 is not `well_formed_correct`.
   - **mean per-row fraction (reported supplement):** mean over rows of the
     per-row fraction of samples that converted / were damaged.
   Rates are reported per seed and pooled across the 5 seeds.

The `clean_tighten` and `well_formed_correct` metrics are the resolved cell's own
(`gen_lib.py:grade_clean_tighten`, `grader.py:grade_one`), reused unchanged.

Multi-seed harness robustness (placebo re-draw): under the same K=5 seeds, the
two G3 placebos are re-instantiated fresh each seed - a fresh random unit write
direction (in place of the single frozen `random_direction`) and a fresh
permuted-gate assignment (same total fire count, uniformly random rows across the
combined confab+known held-out pool). This tests whether the resolved
specificity result (random-direction ~ no-op; permuted-gate materially worse
selectivity) was a single-seed artifact of the one committed random vector and
the one committed permutation.

Instrument config files pinned at sign: `cell.yaml`, `gates.yaml`.

## Prediction

The greedy arm reproduces 73.5%/3.1% within band, and the sampled-decode arm's
majority-vote confab conversion stays at or above 63.5% while majority-vote
known-correct cost stays at or below 8%, per seed and pooled, so the resolved
headline pair survives outside a single greedy decode.

## Falsifier

Sampled-decode majority-vote confab conversion falls below 63.5% (pooled, or in a
majority of the K=5 seeds), OR sampled-decode majority-vote known-correct cost
exceeds an 8% point estimate or a 12% Wilson upper CI (pooled), meaning the
resolved 73.5%/3.1% pair is a greedy-decode artifact and must be re-scoped to
"one greedy decode" wherever it is asserted. (A placebo-robustness G3 failure
falsifies only the specificity claim, not the headline conversion.)

## Gates

Band anchored on the resolved headline 73.5% conversion / 3.1% cost
(`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 305-319). All gates
computed over the HELD-OUT split only (confab 185, known-correct 258); the gated
arm decides dosing row by row end to end, never a post-hoc rate multiplication.

- **H3-G0 (greedy reproduction / instrument validity, pre-analysis; failure =>
  STOP, not an outcome).** Arm R greedy gated confab clean_tighten reproduces
  73.5% within +/- 5pp absolute (in [68.5%, 78.5%]) AND its Wilson 95% CI
  overlaps the resolved [66.7%, 79.3%]; greedy gated known-correct false-refusal
  reproduces 3.1% within +/- 3pp absolute (<= 6.1%). If greedy does not
  reproduce, the harness or checkpoint diverges from the resolved run and every
  sampled comparison is uninterpretable: STOP and diagnose, do not report a null.

- **H3-G1 (sampled-decode conversion band, primary).** Arm S majority-vote
  (>= 5/8) confab clean_tighten stays within an absolute margin of 10pp below the
  resolved 73.5%, i.e. `>= 63.5%`, for the pooled result AND for each of the K=5
  sampling seeds individually. Any-vote conversion and mean per-row conversion
  fraction reported alongside. (10pp below the point is ~3pp below the resolved
  Wilson lower bound of 66.7%: the largest degradation still consistent with "the
  headline survives sampling.")

- **H3-G2 (sampled-decode cost ceiling).** Arm S majority-vote (>= 5/8)
  known-correct false-refusal stays at or below an 8% point estimate AND its
  Wilson 95% upper CI stays below 12%, for the pooled result AND each of the K=5
  seeds. (Resolved cost 3.1% [1.6%, 6.0%]; the ceiling gives sampling headroom
  while keeping cost far below the conversion rate, which is what the selectivity
  claim requires.)

- **H3-G3 (placebo seed-robustness).** In every one of the K=5 seeds, the
  freshly-drawn random-direction arm's confab clean_tighten stays below 25%
  (resolved single-seed value 7.0%) AND the freshly-permuted-gate arm's
  known-correct false-refusal stays above 15% (resolved single-seed value 22.9%,
  vs the gated 3.1%). Certifies the specificity result is not an artifact of the
  one committed random vector or the one committed permutation. A G3 failure
  falsifies only the specificity claim.

## Lane and cost

Small GPU job. Arm R greedy is one deterministic pass over 443 held-out rows
(185 confab + 258 known-correct) plus the K=5 placebo re-draws. Arm S sampled is
443 rows x N=8 samples x K=5 seeds = 17,720 generations at `max_new_tokens=200`
plus the K=5 sampled placebo arms. Two options, decide at sign time:

- Local RTX 3090, one evening, after the mid-band dose ladder frees the card
  (free). Batched bf16 4B generation at 200 max tokens fits an evening; if the
  sampled budget overruns, cut to K=3 seeds (the band gates apply per seed and
  pooled, so 3 seeds still adjudicate) rather than moving any gate.
- Modal A10G, roughly 3-5 GPU-hours end to end at an approximate USD 1.10/hour
  on-demand A10G rate, order-of-magnitude a few dollars.

Lane decision at sign (2026-07-13): local RTX 3090, this evening, after the H6
hook-check frees the card. K=5 registered seeds attempted first; the pre-stated
K=3 fallback (slice to the first three registered seeds, no new seed values)
applies only if the sampled budget overruns the evening.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Greedy reproduces 73.5%/3.1% within band; sampled majority-vote conversion ~68-75% (at or slightly above greedy, per the program's greedy-understates precedent), cost ~3-6%; placebo margins hold in all 5 seeds. Headline survives outside greedy. |
| user | H3-G1 and H3-G2 both PASS: the headline survives sampling (recorded 2026-07-11) |

## Outcome

Resolved 2026-07-13. Run: local RTX 3090, all K=5 registered seeds completed
(no K=3 fallback needed). Gate artifacts: `analysis/h3_full_summary.json`
(row-level logs gitignored under `analysis/`), aggregates promoted to
`analysis-committed/h3_summary.json` (verified text-free; booleans, counts,
rates, and readback scalars only).

**Verdict: the falsifier FIRES. H3-G0 PASS, H3-G1 FAIL, H3-G2 PASS, H3-G3
PASS. The resolved 73.5%/3.1% headline pair is greedy-decode-specific and is
re-scoped to "one greedy decode" wherever it is asserted.**

### Gate results

- **H3-G0 (greedy reproduction) PASS.** Arm R reproduces the resolved numbers
  exactly: gated confab clean_tighten 136/185 = 73.5% (Wilson [66.7%, 79.3%])
  and gated known-correct false-refusal 8/258 = 3.1% (Wilson [1.6%, 6.0%]).
  The replication harness measures the same instrument; the sampled comparison
  is interpretable.
- **H3-G1 (sampled conversion band) FAIL, pooled and in all 5 seeds.** Arm S
  majority-vote (>= 5/8) confab clean_tighten conversion: pooled 140/925 =
  15.1% (Wilson [13.0%, 17.6%]) vs the 63.5% floor; per seed 23/27/28/31/31
  per 185 = 12.4% / 14.6% / 15.1% / 16.8% / 16.8%. Reported alongside per
  registration: any-vote 492/925 = 53.2%, mean per-row sample fraction 22.0%.
- **H3-G2 (sampled cost ceiling) PASS, pooled and in all 5 seeds.** Majority-vote
  known-correct false-refusal pooled 60/1290 = 4.65% (Wilson UCB 5.9% < 12%);
  per seed 4.26-5.43%, worst per-seed UCB 8.9%.
- **H3-G3 (placebo seed-robustness) PASS in all 5 seeds.** Freshly drawn
  random-direction confab clean_tighten 10.3-18.4% (< 25% every seed, i.e.
  inert relative to the gated write's greedy 73.5%); freshly permuted-gate
  known-correct false-refusal 22.5-24.8% (> 15% every seed, i.e. materially
  worse than the gated 3.1%). The resolved specificity result is not an
  artifact of the one committed random vector or the one committed
  permutation.

### Instrument verification (why this null is adopted)

Per the program rule extended at H6 (never adopt a paper-changing null from an
uncertified instrument), the verdict was WITHHELD at run completion and an
adversarial instrumentation red-team ran over five surfaces before this
Outcome was written. All five certify the collapse as behavioral:

1. **Dose delivery on the batched sampled path.** Live realized-projection
   readback (hook.last_readback, the direct delivery measure, not the
   cross-trajectory subtraction H6 showed to be divergence-fragile) on all 860
   fired row-seed units: mean 200.026, min 199.842, max 200.197 against
   dose_target 200. Non-fired units correctly read back none. H3 uses the
   plain-HF register_forward_hook path that H6-G1 certified as firing every
   decode step, NOT the Unsloth bespoke path H6 voided; the H6 non-firing
   signature does not apply here and was checked directly.
2. **The write acts under sampling.** Fired confab per-sample clean_tighten
   1618/6720 = 24.1% vs non-fired (undosed) confab 12/680 = 1.8%, a 13x
   contrast; fired known per-sample damage 91.9% vs non-fired 4.7%.
3. **Sampling genuinely ran.** The within-unit clean_tighten count histogram
   over 840 fired confab units is spread across intermediate values
   (0/8: 353, 1: 127, 2: 89, 3: 72, 4: 59, 5: 35, 6: 49, 7: 56, 8/8: 0);
   487/840 units have intermediate counts, which is impossible under a silent
   greedy fallback (identical samples could only populate 0/8 and 8/8). All 5
   seeds are distinct and derive distinct per-row torch seeds.
4. **Termination/grading parity.** The batched path's termination rule
   (`gen_lib._first_eos_position`) is conservative relative to greedy's
   shorter-than-max rule: any bias pushes clean_tighten DOWN, so it cannot
   manufacture a false PASS; it also cannot rescue the gate, since the miss is
   48 points, not marginal. See the provenance-gap note below.
5. **Arithmetic.** The 140/925, per-seed counts, any-vote, mean fraction, G2,
   and G0 numbers were independently recomputed from the raw run logs by both
   the red-team and the lead; all reproduce exactly.

### Scope and reading (binding for Paper 5 and downstream)

1. **What fails and what survives.** The falsifier fires on the CONVERSION
   RATE only. The write still acts under sampling (readback on target; fired
   24.1% vs non-fired 1.8% per-sample), and both safety and specificity
   survive: known-correct cost stays low under sampling (G2 PASS, 4.65%
   pooled) and the placebo margins hold in every seed (G3 PASS). What
   collapses is the strict clean_tighten conjunction under temperature-0.7
   sampling aggregated by >= 5/8 majority vote: per-sample clean conversion
   drops from greedy's 73.5% to ~24.1%, so the majority vote lands at 15.1%.
   Do NOT overstate this as "the snap stops working under sampling"; do not
   understate it either, since 63.5% was pre-registered as the largest
   degradation still consistent with "the headline survives sampling."
2. **Mechanism is NOT decomposable from committed artifacts.** The run logs
   store per-sample booleans (clean_tighten, well_formed_correct) plus
   readback, not generation text or sub-grades. Whether the ~76% of failing
   fired samples stopped refusing or still refuse while breaking the strict
   clean_tighten format (well-formedness, single answer key, trailing-clean,
   termination) is unrecoverable here. Any paper narrative finer than the
   registered clean_tighten metric about WHY sampling collapses conversion
   requires a re-run that persists text or sub-grades. The any-vote rate
   (53.2%) shows a clean refusal is reachable under sampling for about half
   the rows but dominant for few.
3. **Benign warning, recorded so it is not later misread.** `full_run.log`
   line 5 carries the transformers warning that temperature/top_p/top_k "are
   not valid and may be ignored." It fires once, before the Arm R greedy
   banner: it is the warn-once for the checkpoint generation_config sampling
   defaults being ignored on a GREEDY call (do_sample=false). It does not
   apply to Arm S (do_sample=true), where those flags are valid and where the
   vote-spread evidence above proves sampling took effect.

### Predictions adjudication

Both scoreboard calls were WRONG on the primary gate. The orchestrator
predicted sampled majority-vote conversion ~68-75% (at or slightly above
greedy, per the greedy-understates precedent); observed 15.1%. The user
predicted H3-G1 and H3-G2 both PASS; G2 passed but G1 failed, so the
conjunction fails. The orchestrator's greedy-reproduction and placebo-margin
calls were correct; the greedy-understates precedent did not transfer to this
instrument's strict conversion metric.

One-sentence verdict (mirrored in `experiment.yaml:verdict`): the greedy arm
reproduces the resolved 73.5%/3.1% pair exactly, but sampled-decode
majority-vote conversion collapses to 15.1% pooled (all 5 seeds individually
below the 63.5% floor) with delivery, sampling, and arithmetic adversarially
verified, so the falsifier fires and the resolved headline is re-scoped to
"one greedy decode" everywhere it is asserted, while cost (4.65%) and placebo
specificity survive sampling.
