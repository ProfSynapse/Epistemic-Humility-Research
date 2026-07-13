# H3: Multi-Seed and Sampled-Decode Replication of the Doubt-Gated Caution Snap

Status: resolved (signed 2026-07-13; resolved 2026-07-13 falsified on the original instrument, REVISED to resolved same day after a verified termination-rule instrument correction and full K=5 re-run; falsifier does NOT fire).

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

Resolved 2026-07-13, REVISED same day after an instrument correction (full
history below; the superseded falsified verdict and its voiding are part of
this record). Run: local RTX 3090, all K=5 registered seeds completed, twice:
once on the original harness and once on the corrected harness after the
batched termination rule was fixed and repinned. Gate artifacts:
`analysis/h3_full_summary.json` (row-level logs gitignored under `analysis/`,
now persisting per-sample text and full sub-grade dicts per the data-exhaust
build-time rule), aggregates promoted to `analysis-committed/h3_summary.json`
(verified text-free). Pre-fix run logs and the superseded gate summary are
archived under `analysis/prefix-termination-artifact-20260713/`.

**Verdict: the falsifier does NOT fire. H3-G0 PASS, H3-G1 PASS, H3-G2 PASS,
H3-G3 PASS on the corrected instrument. The resolved 73.5%/3.1% headline
survives temperature-0.7 sampled decoding: pooled majority-vote conversion
69.5% against the 63.5% floor, above the floor in every seed individually.**

### Gate results (corrected instrument, full K=5 re-run)

- **H3-G0 (greedy reproduction) PASS.** Arm R reproduces the resolved numbers
  exactly and identically to the pre-fix run: gated confab clean_tighten
  136/185 = 73.5% (Wilson [66.7%, 79.3%]), gated known-correct false-refusal
  8/258 = 3.1% (Wilson [1.6%, 6.0%]). Greedy grading was never affected by the
  termination defect.
- **H3-G1 (sampled conversion band) PASS, pooled and in all 5 seeds.** Arm S
  majority-vote (>= 5/8) confab clean_tighten conversion: pooled 643/925 =
  69.5% (Wilson [66.5%, 72.4%]) vs the 63.5% floor; per seed
  130/126/127/129/131 per 185 = 70.3% / 68.1% / 68.6% / 69.7% / 70.8%.
  Reported alongside per registration: any-vote 82.5%, mean per-row sample
  fraction 71.4%. The sampled conversion sits ~4 points under greedy's 73.5%,
  inside the registered tolerance.
- **H3-G2 (sampled cost ceiling) PASS, pooled and in all 5 seeds.**
  Majority-vote known-correct false-refusal pooled 60/1290 = 4.65% (Wilson UCB
  5.9% < 12%). The counts are IDENTICAL to the pre-fix run: the cost grader
  (`grade_one`) has no termination conjunct, and the regeneration is a
  bit-faithful replay, so only the termination boolean changed between runs.
- **H3-G3 (placebo seed-robustness) PASS in all 5 seeds.** Freshly drawn
  random-direction confab clean_tighten 10.3-18.4% (< 25% every seed);
  freshly permuted-gate known-correct false-refusal 22.5-24.8% (> 15% every
  seed). Identical to the pre-fix run.

### Instrument correction history (binding provenance for this verdict)

1. The original K=5 run resolved FALSIFIED: G1 read 140/925 = 15.1% pooled
   against the 63.5% floor, adversarially red-teamed and adopted. That
   verdict is superseded, not erased: it was correct arithmetic on a defective
   conjunct.
2. The run logs stored only booleans, so the failure anatomy was
   unrecoverable. Under the PI's data-exhaust directive a text-persisting
   single-seed diagnostic (seed 20260710) was registered and run. It replayed
   the pinned run bit-exactly (same 290/1344 per-sample cleans, same 23
   majority conversions), then decomposed the failures: 764/769
   refused-but-messy fired samples failed ONLY the `terminated_naturally`
   conjunct, with eos emitted at the final position of the generated block and
   complete, clean refusal texts.
3. Root cause: the batched rule (`gen_lib`, previously requiring
   `eos_pos < n - 1`) contradicted the registered metric text "terminated
   naturally (stopped before max_new)". Arm S batches 8 identical copies; the
   write compresses refusals to near-identical ~26-token lengths; members
   tying for longest-in-batch carry eos at the block's last position and were
   misgraded as not-terminated. Greedy's batch-1 rule was correct, which is
   why G0 reproduced while G1 collapsed. The original red-team's surface-4
   inference (termination bias "cannot rescue the gate") is refuted: the bias
   was 57 points of fired samples, not marginal.
4. The fix (`is_terminated_naturally`: terminated iff eos anywhere in the
   block, or block shorter than max_new; not-terminated only when no eos and
   the full budget was used) matches the registered text, changed no gate,
   seed, threshold, or other grader semantics, carries 16 regression tests
   including the exact batch-tie geometry, and was repinned with an audit
   trail in `experiment.yaml`. A parity recompute applying the fixed rule to
   the diagnostic's persisted inputs reproduced 1056/1480 per-sample and
   130/185 majority-vote exactly.
5. The full K=5 re-run on the corrected harness produced seed-20260710
   majority-vote conversion of exactly 130/185, matching the independent
   diagnostic prediction; G0 and the placebo arms reproduced identically; G2
   counts are byte-identical. The reopened instrument-verification is closed
   by this triple agreement (diagnostic replay, parity recompute, independent
   re-run).

### Scope and reading (binding for Paper 5 and downstream)

1. **The headline is decode-robust.** The resolved 73.5%/3.1% pair reproduces
   under greedy and degrades only ~4 points under temperature-0.7 sampling
   with majority-vote aggregation (69.5% pooled, every seed above the floor).
   Cost stays low (4.65%) and placebo specificity holds in every seed. The
   prior re-scoping of the headline to "one greedy decode" is withdrawn.
2. **Mechanism is now decomposable.** The corrected run persists per-sample
   text, full sub-grade dicts, eos position, and raw token counts in the
   gitignored row-level logs, so any downstream narrative about sampling
   behavior can be audited directly rather than inferred from booleans.
3. **Benign warning, recorded so it is not later misread.** `full_run.log`
   carries the transformers warn-once that sampling flags "may be ignored" on
   the GREEDY Arm R call (do_sample=false); it does not apply to Arm S, where
   the within-unit vote spread proves sampling took effect.

### Predictions adjudication

Both scoreboard calls are CORRECT on the corrected instrument, after both
were provisionally scored wrong against the defective one. The orchestrator
predicted sampled majority-vote conversion ~68-75%; observed 69.5% pooled,
per-seed 68.1-70.8%, entirely inside the band. The user predicted H3-G1 and
H3-G2 both PASS; both pass. The greedy-understates precedent transferred
approximately (sampling sits slightly below greedy here, but within
tolerance); the earlier adjudication against both calls is void with the
instrument that produced it.

One-sentence verdict (mirrored in `experiment.yaml:verdict`): the resolved
73.5%/3.1% headline survives sampled decoding on the corrected instrument,
with pooled majority-vote conversion 69.5% (all 5 seeds above the 63.5%
floor), cost 4.65%, and placebo margins intact, after a batched
termination-rule defect that misgraded eos-at-final-position refusals was
diagnosed from persisted text, fixed, repinned, and verified by
diagnostic-parity-rerun triple agreement.
