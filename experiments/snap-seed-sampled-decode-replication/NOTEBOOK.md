# H3: Multi-Seed and Sampled-Decode Replication of the Doubt-Gated Caution Snap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
