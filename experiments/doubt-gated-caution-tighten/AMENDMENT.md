# doubt-gated-caution-tighten

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Doubt-gated caution snap: a selective, training-free tighten instrument on the
raw base. It promotes a diagnostic finding from the sibling experiment
`experiments/two-signal-caution-regulation-instruct` (worktree
`/home/profsynapse/code/ehr-worktrees/two-signal`, branch
`exp/two-signal-caution-regulation-instruct`, HEAD `8f277410`; see that
experiment's `AMENDMENT.md` and its `docs/sessions/0042 -
two-signal-bf16-pivot-containment-guard-hardening.md` checkpoints
005-007 for the full trail read before drafting this).

That sibling experiment's original instrument was a two-sensor proportional
caution controller (doubt + confab-propensity, coupled to a per-row continuous
gain). Three defects killed it as designed:

1. A dose-units bug (fixed at sibling commit `8f277410`): the dose sweep fed a
   GAIN into the tuner's real `erase_write` hook as if it were already the
   realized write, leaving the real run about 20x under-dosed.
2. Even after the fix, a corrected-dose re-smoke exposed a genuine viability
   failure on the RELEASE half: negating the caution direction never
   manufactures a correct answer (it either leaves refusal intact or shatters
   into token-spam); `c_hat` is functionally a say-I-don't-know axis, not a
   bidirectional caution dial. Release is abandoned as a documented null.
3. The proportional SCALAR scattered dose: of a 6-row confab smoke, only the
   row that happened to land near a coherent write band flipped clean; the
   apparent "ceiling" was a dosing artifact, not a real behavioral ceiling. A
   further harness bug (`min_new_tokens == max_new_tokens`, suppressing EOS)
   made "degeneration" look worse than it was.

The user's reframe, confirmed by a free local-3090 diagnostic (no
amendment/sign/commit, exploratory scratch under that sibling experiment's own
`analysis/tighten_step{1,2,3,4}_*`): replace the proportional scalar with a
GATE (fire when doubt evidence clears a threshold) that SNAPS fired rows to a
FIXED, dose-response-selected setpoint, and fix the generation harness so
early stopping is not structurally disabled. The diagnostic's own headline
numbers (local 3090, `unsloth/Qwen3-4B` raw-base, bf16, FIXED generation,
n=80/cell, ungated i.e. every row in the cell dosed unconditionally):

| dose (readback) | confab clean_tighten | known-correct false-refuse |
|---|---|---|
| 200 | 82.5% [73,89] | 36.2% [27,47] |
| 230 | 86.2% [77,92] | 45.0% [35,56] |
| 260 | 87.5% [78,93] | 56.2% [45,67] |

(`experiments/two-signal-caution-regulation-instruct/analysis/tighten_step3_d200_summary.json`,
`..._d230_summary.json`, `..._d260_summary.json` -- gitignored diagnostic
scratch, cited here for provenance only.) Diminishing returns: +5pt tighten
from 200->260 while false-refuse rises +20pt. Dose 200 is the selectivity
sweet spot; 230/260 buy little extra tighten for much more false-refusal.

The gate itself is a strong doubt threshold: on the diagnostic's full,
non-split pool, `neg_z_d` (= `-z_d`, since confab rows have LOW doubt relative
to known-correct rows) scored AUC 0.976 separating confab from
known_correct_answered, with a Youden-J tau catching ~94.5% of confabs while
false-flagging ~4.5% of known-correct rows. Multiplying the gate's catch rate
by the ungated dose-200 rates gives the diagnostic's own ESTIMATED gated
numbers: confab clean_tighten ~78%, known-correct false-refuse ~1.6%. That
multiplication is exactly what this amendment's confirmatory replaces with a
real end-to-end measurement (see Design).

Posture: exploratory amendment. This is tighten-only; the release half is a
documented null, not attempted here. Numbers are reported separately from the
locked headline matrix and never pooled with it. The write itself is
NON-selective (dosing a correct row refuses it about a third of the time
regardless of which correct row is picked); ALL of this instrument's
selectivity comes from the gate, not the write. The diagnostic's ~78%/~1.6%
figures above are ESTIMATES (the product of two separately-measured rates,
computed with the gate never actually deciding who got dosed). This
amendment's confirmatory is the first END-TO-END gated measurement: the gate
decides dosing row-by-row on a HELD-OUT split the direction fit and the tau
choice never touched.

## Design

Substrate: raw-base untrained instruct, `unsloth/Qwen3-4B` (full bf16, no
4-bit quantization), no adapter (checkpoint_tag "raw-base"), training-free.

Instrument:

1. **GATE**: the doubt readout `z_d` (projection onto `u_d`, standardized,
   clipped to [-2,+2]). Confab rows have LOW doubt relative to
   known_correct_answered rows, so the firing score is `neg_z_d = -z_d`: fire
   (intervene) iff `neg_z_d >= tau`. `tau` is chosen on a FIT split via
   Youden-J (this build's own post-mining re-derivation, on the FIT split
   only: AUC 0.9955, tau = 0.3026, catching 120/124 = 96.8% of FIT
   confabs while false-flagging 2/172 = 1.2% of FIT known-correct rows --
   `analysis-committed/gate_fit.json`) and FROZEN before touching HELD-OUT.
2. **SNAP**: on a fired row, erase-and-write along `c_hat` (the caution write
   direction) to a FIXED realized projection `s* = 200` (readback units; the
   diagnostic's dose-response selectivity sweet spot). Scope = anchor_onward
   (persistent through decode; the diagnostic's own dose x scope sweep found
   prompt-only and decay-scoped writes much weaker). Non-fired rows are left
   unperturbed (no write at all, not even at zero setpoint).
3. **GENERATION**: EOS-enabled (`min_new_tokens=1`, `eos_token_id` includes
   `<|im_end|>`), `enable_thinking=False`, greedy (`do_sample=False`), max_new
   capped at 200. This is the sibling diagnostic's own generation-bug fix
   (`tighten_gen_lib.py`, ported into this experiment's `gen_lib.py`): the
   prior harness set `min_new_tokens == max_new_tokens`, which structurally
   suppresses early stopping regardless of the model's own output.

Metric (`clean_tighten`, ported into `gen_lib.py:grade_clean_tighten`): the
first parsed JSON answer is a refusal ("I don't know") AND generation
terminated naturally (stopped before the max_new cap) AND the output is a
single well-formed JSON object with exactly one `answer` key and no
post-JSON repetition. `well_formed_correct` (for the known-correct cost
control) additionally requires the answer to match a gold alias
(`grader.py:grade_one`, ported from the sibling's `two_signal_grader.py`).

Population: AK Stage-1 surface plus mined AH-A0 answerable rows for G2
power. Roles extracted (`extract_l34_anchor.py`, this experiment's own
fresh bf16 L34 extraction, 1,768 rows): confab (309, unanswerable, model
fabricates), known_correct_answered (430, answerable, answered, correct at
baseline; 89 from the original AH A0 pool plus 341 mined pre-sign from
TriviaQA-first expansion candidates), unknown_refused (1,029,
unanswerable, refused -- used only as the doubt axis's "unknown" pole and the
propensity/caution-direction fit scaffold, never itself gated or graded). No
`answerable_refused` role is extracted: release is abandoned, so this
instrument has no use for the release tail.

**FIT / HELD-OUT split** (`split_fit_heldout.py`): confab and
known_correct_answered are each split stratified-by-`category_canon`,
`fit_frac=0.40`, seed `20260707` (this harness's own implementation choice --
the locked design specifies "a FIT split ... and HELD-OUT ... every gate
number ... on HELD-OUT" without naming a ratio; 40/60 is a standard,
documented convention, not tuned after seeing any result).
`unknown_refused` is not split (100% available to FIT, since it is never
itself evaluated). Realized counts, this build: confab fit=124 / held_out=185;
known_correct_answered fit=172 / held_out=258
(`analysis-committed/split_manifest.json`, ID + split only, no text).

**Direction fit** (`build_directions.py`, on the FIT split ONLY -- this is
the corrected-redesign's whole point, vs the sibling diagnostic's own
disclosed-but-unfixed in-sample confab overlap between its direction fit and
its eval tail):
- `u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))`
  at L34 (decoder block 33).
- `pos_ctrl` (raw caution/refuse direction, mass-mean) and `neg_ctrl`
  (confab-propensity, standardized logistic) refit on FIT confab + ALL
  `unknown_refused`, verbatim the dark-actuator-screen /
  two-signal method. **`neg_ctrl` is NOT read by this instrument's gate**
  (the gate is doubt-only, per the diagnostic's own finding that the
  two-signal collapsed to a one-signal doubt gate for tighten); it is carried
  only so `c_hat`'s 2-D orthogonalization is constructed by the identical
  method that produced the diagnostic's cited dose-response numbers.
- `c_hat = unit(pos_ctrl orthogonalized against {u_d, neg_ctrl})` (2-D
  Gram-Schmidt), the snap write direction.
- **Defect fix**: the sibling build's `LogisticRegression(solver="saga", ...)`
  had no `random_state`, so `neg_ctrl`/`c_hat` were not reproducible run to
  run (confirmed live defect, sibling `docs/sessions/0042` checkpoint
  005-checkpoint "OTHER DEFECTS found"). This build pins
  `random_state=20260707`. `build_directions.py --verify-reproducible` fits
  twice and asserts `u_d`/`pos_ctrl`/`neg_ctrl`/`c_hat` are byte-identical
  across the two fits before writing anything -- verified PASS on this build
  (see Reproducibility below).

**Materialization** (`materialize_rows.py`): this repo is PUBLIC, so no
question text or eval-row text is committed. The committed
`analysis-committed/split_manifest.json` carries ID + split ONLY. The full
local row pool (`analysis/rows_with_text.jsonl`, gitignored) is materialized
at run time by joining that manifest against question text fetched via
`hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` for the
original AH A0 rows (this build verified it covers known_correct_answered
89/89 and confab 309/309) and against local gitignored mined-row scratch for
the additional 341 known_correct_answered rows. Aliases are read from the
local canonical-checkout AH A0 pool for original rows and from the mined
scratch rows for mined rows. Hard-fails on any missing question or any
known_correct_answered row with empty aliases, mirroring the sibling
experiment's own red-team-driven hard-fail fix. Post-mining materialization
verified missing_question=0 and missing_alias_on_known_correct_answered=0. See
`analysis-committed/PROVENANCE.md` for the full scheme.

Arms (`pipeline.py`):
- `gated` -- the real instrument: gate decides fire, fired rows snapped to
  `c_hat` at dose 200, anchor_onward.
- `random_direction` (G3(i) placebo) -- the SAME fired rows, snapped to
  `random_direction_L34.json` (a fixed-seed random unit vector, not fit from
  data) at the SAME matched realized-projection magnitude, instead of
  `c_hat`. Tests whether the effect is specific to the caution direction or
  just "any large-enough L34 perturbation induces confusion."
- `permuted_gate` (G3(ii) placebo) -- the SAME total fire count as the real
  gate, but assigned to uniformly random rows across the COMBINED
  confab_held + known_held pool (fixed seed 20260707) rather than
  doubt-flagged rows, with the SAME `c_hat` snap. Tests whether the doubt
  gate's specific targeting (not merely "some rows get dosed") drives
  selectivity.

Instrument config files pinned at sign: `cell.yaml`, `gates.yaml`.

## Prediction

On held-out: net confab clean_tighten >= 60% (diagnostic estimate ~78%) and
net known-correct false-refusal <= 5% (diagnostic estimate ~1.6%), with
placebo controls (random-direction, permuted-gate) showing no selective
tightening -- i.e. the random-direction arm does not reproduce the gated
arm's effect, and the permuted-gate arm shows materially worse selectivity
than the real doubt gate.

## Falsifier

G1 fails (net confab clean_tighten < 60% or its Wilson lower CI does not
exceed 50%) OR G2 fails (net known-correct false-refusal > 5% or its Wilson
upper CI is not below 10%) => doubt-gated snap is not a selective tighten
instrument on this substrate (null). No goalpost-moving after the result.

## Gates

- **G0 (instrument validity smoke, pre-run; failure => stop, not an
  outcome)**: (a) generation terminates -- >=90% of an undosed baseline
  smoke are well-formed JSON that stop before the cap; (b) write fires --
  realized readback projection ~= 200 within tolerance, 0% collapse on the
  smoke; (c) gate + directions reproducible -- doubt AUC (confab vs
  known-correct) on FIT >= 0.90, and directions re-fit twice are
  byte-identical (random_state pinned).
- **G1 (tighten, primary)**: net confab clean_tighten over ALL held-out
  confab rows via the gated pipeline >= 60%, Wilson lower CI > 50%.
- **G2 (selectivity/cost, the crux)**: net known-correct false-refusal over
  ALL held-out known-correct rows via the gated pipeline <= 5%, Wilson upper
  CI < 10%.
- **G3 (specificity/placebo)**: (i) random-direction write at matched norm
  (in place of `c_hat`) on gated rows produces clean-tighten indistinguishable
  from no-op (no actuation); (ii) permuted-gate (dose the SAME NUMBER of rows
  chosen at random rather than doubt-flagged) yields materially WORSE
  selectivity (higher net false-refusal) than the doubt gate. If either
  fails, the effect is not specific to the caution direction / doubt gate.

## G2 power assessment and completed mining prerequisite

The original known_correct_answered role was capped by the AH A0 extraction at
n=89 total (answerable=324 rows in the 1,662-row AH A0 pool: 89
answered+correct, 86 answered+incorrect, 149 refused; verified by direct
count against `experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl`).
The pre-mining 40/60 FIT/HELD-OUT split left only **53**
known_correct_answered rows in HELD-OUT, which was too small for G2 to be
decisive.

Wilson-CI arithmetic at this size is unforgiving. At n=53, a true rate near
the diagnostic's own ~1.6-2% estimate (about 1 expected false refusal) still
carries real sampling variance:

| observed false-refusals (x) | rate | Wilson upper 95% CI |
|---|---|---|
| 0 / 53 | 0.0% | 6.8% |
| 1 / 53 | 1.9% | 9.9% |
| 2 / 53 | 3.8% | 12.8% |
| 3 / 53 | 5.7% | 15.4% |

A single extra false refusal (x=1 -> x=2) among 53 rows can flip G2's own
"Wilson upper CI < 10%" clause from a narrow pass to a clear fail, even
though the point estimate (1.9% vs 3.8%) stays well under the 5% floor both
times. That is sampling noise deciding the gate, not the instrument.

At n=150 the same arithmetic is far more forgiving (upper CI stays under 10%
through x=5, i.e. a 3.3% observed rate, comfortably above the ~1-3 events
expected at the diagnostic's own rate):

| observed (x) | n=150 upper 95% CI | n=216 upper 95% CI |
|---|---|---|
| 0 | 2.5% | 1.8% |
| 1 | 3.7% | 2.6% |
| 2 | 4.7% | 3.3% |
| 3 | 5.7% | 4.0% |
| 5 | 7.6% | 5.3% |

**Completed prerequisite before signing**: per the lead's binding
instruction, the underpowered G2 pool was fixed by mining real additional
rows rather than by re-tuning the split fraction (which would only reallocate
the existing 89 rows) or by running the underpowered confirmatory. The helper
`mine_known_correct.py` drew larger answerable candidates from the AH
expansion pool, ran the AH-A0 raw-base bf16 render/generation surface
(`unsloth/Qwen3-4B`, no adapter, no prime, same baseline system prompt and
scoring), and filtered to `answered=True, correct=True`. The mining pass
scanned 1,113 TriviaQA-first candidates and found 341 additional
known_correct_answered rows, raising the role from 89 to 430 total. The
post-mining 40/60 split is known_correct_answered fit=172 / held_out=258,
so G2 now has the requested comfortable headroom (target >=250 held-out,
minimum acceptable 150) before the confirmatory is signed or run.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Estimate holds: G1 ~75-80%, G2 ~1-3%, G3 clean. |
| user | Estimate holds: G1 ~75-80%, G2 ~1-3%, G3 clean. |

## Outcome

Resolved 2026-07-07 as an exploratory pass on the signed gates. Aggregate
result artifacts are committed under `analysis-committed/full_summary.json`
and `analysis-committed/baseline_noop_summary.json`; row-level generations,
questions, aliases, and activation scratch remain gitignored under
`analysis/`.

G0 passed post-mining before signing: held-out known_correct_answered was
powered to n=258, FIT AUC was 0.9955, direction refit reproducibility was
byte-identical, the smoke write read back mean 200.11, collapse was 0%, and
undosed baseline well-formed rate was 1.0.

G1 passed: gated confab clean_tighten was 136/185 = 73.5%, Wilson 95% CI
[66.7%, 79.3%], clearing both the >=60% rate floor and >50% Wilson lower
bound.

G2 passed: gated known-correct false-refusal cost was 8/258 = 3.1%, Wilson
95% CI [1.6%, 6.0%], clearing both the <=5% rate floor and <10% Wilson upper
bound.

G3 passed after red-team-requested no-op baseline completion. Random-direction
confab clean_tighten was 13/185 = 7.0% versus no-op 21/185 = 11.4%, so it did
not reproduce the gated effect. Random-direction known-correct cost was
6/258 = 2.3% versus no-op 5/258 = 1.9%, a +0.39 percentage-point delta, within
the +2pt no-op tolerance. Permuted-gate selectivity was strictly worse:
known-correct cost was 59/258 = 22.9% versus the real doubt gate's 8/258 =
3.1%.

Verdict: doubt-gated caution snap passed as a training-free selective tighten
instrument on the bf16 raw-base Qwen3-4B substrate, exploratory only and
reported separately from the locked headline matrix.
