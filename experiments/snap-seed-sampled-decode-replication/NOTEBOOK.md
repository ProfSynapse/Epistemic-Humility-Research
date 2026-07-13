# H3: Multi-Seed and Sampled-Decode Replication of the Doubt-Gated Caution Snap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (SIGNED, pre-launch): signed after lead review of the build
  report and harness against the locked AMENDMENT prose. All six builder
  adjudications ACCEPTED, recorded here so the Outcome inherits them:
  (1) Arm R runs one greedy pass per row (dosed-if-fire-else-baseline),
  matching the AMENDMENT's own cost line; equivalence of the derived gated
  arm to an always-both-passes harness was independently certified by the
  resolved H4 red-team (separate generate calls, controller reset between,
  no KV carryover). (2) Arm S reuses Arm R's fire decisions; fire is a
  prompt-anchor property of the frozen instrument and is decode-independent
  by construction. (3) BIGGEST CALL: the H3-G3 placebo re-draw arms decode
  GREEDY, not sampled. The Design section frames the placebo re-draws as
  testing redraw randomness (fresh random direction, fresh permutation per
  seed) against thresholds anchored to the resolved cell's greedy
  single-seed placebo values (7.0% / 22.9%); a greedy re-draw is the
  apples-to-apples comparison, and sampling the placebos would conflate
  decode policy with redraw randomness in one arm. The Lane-and-cost phrase
  "the K=5 sampled placebo arms" is adjudicated a drafting slip describing
  the seed-indexed re-draws, not a decode-policy specification. Adjudicated
  pre-launch, before any GPU data exists; no threshold moves. (4) "Pooled"
  for H3-G1/G2 = concatenate per-row-per-seed majority-vote decisions
  across included seeds into one flat list (n = 185K or 258K rows), then
  rate + Wilson CI; per-seed legs use the same row-level unit. (5) The
  permuted-gate re-draw reassigns the same total fire count (172) uniformly
  over the combined 443-row held-out pool, matching the AMENDMENT's
  combined-pool wording. (6) Arm S batches N=8 identical copies of one
  row's prompt per generate call (same intervention arm and parameters, no
  cross-row composition, no padding variation between batch rows); the
  batched surface only ever carries sampled decode, where kernel-level
  numeric jitter is absorbed by the sampling distribution, and Arm R plus
  both placebo arms stay batch-1 parity-locked to the resolved cell.
  Decode config for Arm S: the Amendment SR registered sampling
  configuration (temperature 0.7, top_p 0.9, num_beams 1) stands as the
  sign-time default per the AMENDMENT's own flag; the user may still
  substitute the Qwen3 published config before launch, which would be
  re-signed, not silently swapped. Lane placeholder resolved to the local
  RTX 3090 this evening (free), K=5 first, pre-stated K=3 fallback only on
  overrun. Real fire-count cross-check at build time (168/185 confab,
  4/258 known, 172/443 total) matches H4's independently derived counts,
  confirming the same frozen gate over the same pool. CPU smoke 10/10 via
  python3 -m pytest; bare python3 exits 0 silently (known gotcha). Launch
  protocol: GPU smoke (--mode smoke --n-rows 8) first to calibrate real
  throughput, then --mode full; the builder's wall-time bracket (roughly
  3-6 h likely at K=5 on the 3090) is unmeasured and treated as a bracket,
  not a commitment.


- 2026-07-13 -- HARNESS BUILD (harness-builder agent, CPU-only; GPU launch NOT
  run). Wrote `materialize_rows.py`, `gen_lib.py`/`grader.py`/`model_lib.py`
  (verbatim copies of the resolved doubt-gated-caution-tighten cell's own
  modules, plus additions local to this experiment: batched sampled decode
  in `gen_lib.py`, Wilson-CI-overlap and per-seed placebo-redraw helpers in
  `model_lib.py`), and `pipeline.py` (Arm R greedy, Arm S sampled-decode
  batched N=8, two greedy placebo re-draw arms, H3-G0/G1/G2/G3 gate
  computation, RunLog-resumable per phase).

  Same reuse strategy as sibling H4: the resolved cell's own gitignored
  extraction artifacts (`l34_anchor_extract.safetensors`, `rows_with_text.jsonl`)
  still exist on disk in the worktree where that cell was actually run
  (`/home/profsynapse/code/ehr-worktrees/gate-snap-tighten/experiments/doubt-gated-caution-tighten/analysis/`);
  since the L34 anchor is a function of the prompt only, those tensors are
  valid input here with no fresh GPU extraction. Ran `materialize_rows.py`
  against the real artifacts: 443 held-out rows (185 confab + 258
  known_correct_answered), 0 missing question, 0 missing alias, 0 missing
  tensor.

  Ran `load_rows_and_gate_decisions()` against the real frozen instrument:
  held-out fire counts are confab 168/185 (90.8%) and known_correct_answered
  4/258 (1.55%) -- identical to H4's build-time numbers, confirming this is
  the same frozen gate applied to the same held-out pool.

  Adjudications made during the build (none of these move a gate; flagged
  for the lead to confirm at sign):
  1. Arm R computes exactly ONE greedy pass per row (dosed if fire else
     baseline), not the resolved cell's own always-compute-both pattern.
     AMENDMENT.md's own cost line ("one deterministic pass over 443
     held-out rows") reads as this leaner form; the discarded baseline pass
     in the resolved cell's pipeline has no causal effect on the dosed
     pass's outcome (separate generate() calls, controller.reset() between),
     so this is a cost optimization, not a metric change.
  2. Arm S's fire decision is the SAME frozen-gate decision as Arm R (a
     property of the row's L34 anchor and the frozen tau, independent of
     decode policy); only the decode mode changes between arms.
  3. Placebo re-draws (H3-G3) use GREEDY batch-1 decode, not sampled decode,
     despite AMENDMENT.md's Lane-and-cost line mentioning "K=5 sampled
     placebo arms." Adjudicated as greedy because: (a) H3-G3's thresholds
     are anchored to the resolved cell's own GREEDY single-seed placebo
     values (7.0%, 22.9%), so a greedy re-draw is the direct apples-to-apples
     comparison; (b) sampling would conflate two independent variables
     (decode policy and direction/permutation randomness) in one placebo,
     muddying the specificity test H3-G3 is designed to isolate. Flagged as
     an interpretive call on genuinely ambiguous prose, not resolved by
     cell.yaml/gates.yaml text.
  4. "Pooled" for H3-G1/G2 is adjudicated as concatenating the per-row-per-
     seed majority-vote decisions across all included seeds into one flat
     list (n = 185*K or 258*K), then computing rate + Wilson CI over that
     combined set -- not re-running majority-vote over a larger 8*K raw-
     sample pool. Flagged as an interpretive call.
  5. Permuted-gate re-draw (H3-G3(ii)) reassigns the SAME total fire count
     as the real gate (172, confab+known combined) to indices drawn
     uniformly over the full 443-row combined held-out pool, per the lead's
     explicit task instruction.
  6. Arm S batching: N=8 identical copies of ONE row's prompt in a single
     `model.generate()` call (no padding heterogeneity, no cross-row
     composition), which the project's batching policy
     (`.skills/experiment-runner/reference/batched-generation.md`) treats as
     the "steered/hooked generation: batch rows sharing the same
     intervention arm and parameters" carve-out, not a new-surface numerics
     smoke case (that smoke targets greedy token-agreement, meaningless for
     inherently stochastic sampled decode). Arm R and both placebo arms stay
     strictly batch-1 (parity-locked vs the resolved cell, per that same
     policy doc and `library/concepts/mechanisms/qwen35-batch-composition-flips-greedy-decode-outcomes.md`).

  CPU smoke (`smoke_cpu.py`, 10 checks): gate-decision math (shared with
  H4), per-row-per-seed majority/any-vote/mean-fraction scoring including
  the 4-4 tie case, Wilson-CI overlap, `derive_seed`/`draw_random_direction`/
  `draw_permuted_gate_indices` determinism-given-seed and correct fired
  counts, the batched termination-detection primitive
  (`gen_lib._first_eos_position`) on synthetic token tensors, all four gate
  computations (H3-G0/G1/G2/G3) on both a predicted-shape PASS case and a
  falsifier-shape FAIL case, the REAL `gen_lib.grade_clean_tighten` /
  `grader.grade_one` on synthetic text, and a RunLog resume round-trip using
  the pinned synaptic-tuner submodule's `shared/utilities/run_log.py`. All
  10 checks PASS. No model load, no GPU.

  Did NOT run `pipeline.py --mode smoke` (GPU) or `--mode full` (GPU,
  confirmatory) -- both are gated behind the lead's sign-off and launch
  approval, per this build task's scope.

  synaptic-tuner submodule was uninitialized in this worktree at build start
  (same recurring pattern as every fresh worktree so far this session);
  `git submodule update --init synaptic-tuner` produced no diff against the
  already-pinned commit.

## 2026-07-13 - RESOLVED: falsifier fires, instrument-verified (lead)

Run completed on the local RTX 3090, all K=5 registered seeds (no K=3
fallback). Gate results: G0 PASS (greedy reproduces 73.5%/3.1% exactly),
G1 FAIL pooled and in all 5 seeds (majority-vote sampled conversion 140/925 =
15.1% vs the 63.5% floor), G2 PASS (pooled cost 4.65%, worst per-seed Wilson
UCB 8.9%), G3 PASS (fresh random directions inert, fresh permutations worse,
every seed).

The verdict was deliberately WITHHELD at run completion (the AK/H6 rule:
never adopt a paper-changing null from an uncertified instrument) and an
adversarial instrumentation red-team was dispatched over five surfaces:
batched-path dose delivery, fired-vs-non-fired behavioral contrast,
sampling-config execution + seed distinctness, batched termination/grading
parity, and independent arithmetic recompute. All five certified the collapse
as BEHAVIORAL: readback 200.026 mean on all 860 fired units, fired-vs-non-fired
per-sample contrast 24.1% vs 1.8% (confab) and 91.9% vs 4.7% (known), the
within-unit vote histogram spread across intermediate counts (487/840 units,
impossible under a silent greedy fallback), the termination rule conservative
(biases toward MORE collapse, cannot manufacture the fail), and every number
reproducing exactly under independent recompute by both the red-team and the
lead. The transformers "flags not valid" warning in full_run.log line 5 was
chased to the greedy arm's warn-once (do_sample=false ignores the checkpoint
generation_config sampling defaults); it does not apply to the sampled arm.

Adjudication: falsifier fires straight, no goalpost moves. The Outcome
records the two binding scope points (conversion-rate-only failure with the
write still acting and G2/G3 surviving; collapse mechanism not decomposable
from committed booleans-only logs, finer narrative needs a text-persisting
re-run) plus the benign-warning note. Both scoreboard calls wrong on G1;
orchestrator right on greedy reproduction and placebo margins. Downstream:
every assertion of the 73.5% headline re-scopes to "one greedy decode";
Paper 5 rewrite must carry this.

## 2026-07-13 - Lab-notebook: boolean-level failure decomposition + text-persistence gap (lead)

CPU-only re-slice of the existing run logs; no new claims, no gate changes.

The run logs violate the program's data-exhaust principle: the harness
computed full sub-grades (well_formed, single_answer_key, trailing_clean,
semantic_refuse, degenerate, terminated_naturally) inside
grade_clean_tighten and discarded them, persisting only final booleans and
no generation text. Decomposition of the G1 collapse from what survives:
fired confab samples (n=6720) split 24.1% clean_tighten / 0.0%
answered-with-gold-alias (expected for confab-selected rows) / 75.9%
NEITHER, vs a non-fired sampled baseline of 1.8% / 0.0% / 98.2% and a
greedy fired split of 81.0% / 0.0% / 19.0%. The NEITHER bucket cannot be
split into answered-wrong vs refused-but-messy vs degenerate without text.

Open instrumentation question this leaves live (red-team surface 4 caveat):
the batched sampled path's termination rule (_first_eos_position) was not
auditable against greedy's rule, clean_tighten requires
terminated_naturally, and the size of that conjunct's contribution to the
collapse is unbounded from stored booleans. Successor registered as a
lab-notebook diagnostic: single-seed (20260710) Arm S re-run with the same
pinned generation/grading stack, persisting per-sample generation text and
the full sub-grade dict under gitignored analysis/, to decompose the
failure anatomy and bound the termination-rule conjunct. Verdict
implication is one-directional as registered: the G1 falsifier fired on the
locked clean_tighten metric and stands unless the diagnostic reveals the
batched path misgraded terminated_naturally at a magnitude material to the
48-point miss, in which case the instrument-verification section is
reopened before any merge of the resolve PR.

PR #283 merge recommendation: HOLD until this diagnostic lands.

## 2026-07-13 - DIAGNOSTIC RESULT: G1 collapse is an instrumentation artifact; falsified verdict REOPENED (lead)

The registered text-persisting diagnostic (single seed 20260710, 443 rows x 8
samples) replayed the pinned Arm S bit-exactly (290/1344 fired-confab
per-sample clean and 23 majority conversions, identical to the pinned run),
certifying it as a faithful instrument. The anatomy then decomposed the
collapse: of 1344 fired confab samples, 21.6% clean, 20.5% genuinely
answered (write sub-dominant on those samples), 0.7% degenerate, and 57.2%
refused-but-messy - of which 764/769 fail on the terminated_naturally
conjunct ALONE (semantic refusal, well-formed JSON, single key, trailing
clean). Their persisted termination inputs show eos emitted at the FINAL
position of the generated block (eos_pos 25, n_new 26 for the dominant
cluster), and the texts are complete clean refusals. Mechanism: Arm S
batches 8 identical copies; the write compresses refusals to near-identical
short lengths; samples tying for longest-in-batch have eos at the block's
last position, and the batched rule (gen_lib._first_eos_position: "not
terminated if eos only at the last position or never") misgrades exactly
those. The registered metric text ("terminated naturally (stopped before
max_new)") is unambiguous: a 26-token refusal ending in an emitted eos
stopped before max_new=200. The batched implementation contradicts the
registered definition; greedy's batch-1 rule (shorter than max_new) graded
these correctly, which is why G0 reproduced while G1 collapsed.

Corrected preview for seed 20260710 (terminated iff eos emitted, or block
shorter than max_new): per-sample clean 1056/1480 = 71.4%; majority-vote
conversion 130/185 = 70.3%, ABOVE the 63.5% floor and near greedy's 73.5%.
The earlier red-team's surface-4 inference that the termination bias "cannot
rescue the gate" is falsified - the bias was 57pp of fired samples, not
marginal. Its own caveat (the conjunct was unauditable from booleans) is
what this diagnostic closed. Credit where due: the PI's data-exhaust
directive ("always save text") is what made this discoverable at all.

Adjudication: the falsifier-fired verdict is VOIDED AS INSTRUMENTATION (the
AK/H6 pattern). PR #283 is converted to draft; the resolve will be revised
after the registered correction: fix gen_lib._first_eos_position semantics
to match the registered metric text (terminated iff eos emitted anywhere;
not-terminated only when no eos and the block hit max_new), repin with
audit trail, re-run the full Arm S (K=5 registered seeds, unchanged
everything else) on the fixed harness, recompute G1/G2 as registered, and
re-resolve. No gate, threshold, seed, or metric-definition changes - this
is an implementation corrected to match already-registered text. G0/G3
stand (batch-1 arms, unaffected rule). Re-run queues on the 3090 behind the
RR mistral cell.

## 2026-07-13 - Corrected K=5 re-run: ALL GATES PASS; verdict revised to resolved (lead)

The full K=5 Arm S re-run on the fixed, repinned harness completed cleanly
(smoke passed first; chain launched by the lead on the freed local card).
Gate results: G0 PASS (136/185 = 73.5% and 8/258 = 3.1%, identical to both
prior runs), G1 PASS pooled 643/925 = 69.5% (Wilson [66.5%, 72.4%]) with
every seed individually above the 63.5% floor (68.1-70.8%), G2 PASS pooled
60/1290 = 4.65% with counts byte-identical to the pre-fix run (grade_one has
no termination conjunct; the regeneration is a bit-faithful replay), G3 PASS
with placebo numbers identical to the pre-fix run.

Triple-agreement closure of the reopened instrument verification: the
independent diagnostic predicted seed-20260710 majority-vote conversion
130/185; the parity recompute on the fixed rule reproduced 130/185; the
corrected re-run produced exactly 130/185. Pre-fix artifacts remain archived
under analysis/prefix-termination-artifact-20260713/.

Verdict revised: falsifier does NOT fire; the resolved 73.5%/3.1% headline
survives sampled decoding (~4-point degradation, inside the registered
tolerance). The superseded falsified verdict and its voiding are preserved in
the Outcome's instrument-correction history. Predictions adjudication
flipped with the instrument: both scoreboard calls (orchestrator ~68-75%;
user G1+G2 both PASS) are correct on the corrected instrument. Committed
aggregate analysis-committed/h3_summary.json regenerated from the corrected
run and re-verified text-free. PR #283 returns to ready with the revised
resolve.
