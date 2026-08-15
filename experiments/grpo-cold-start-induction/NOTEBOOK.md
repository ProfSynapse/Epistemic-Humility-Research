# Cold-start GRPO: can the appropriateness reward induce abstention from the base model? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-08-13 LAUNCH (lead; authorization recorded at signing). GPU confirmed
  free after `dial-logprob-t-deployed-confirmatory` completed (LT-G0/LT-G1
  both pass, report received and spot-verified). Launch plan: background
  harness-builder replicates the `grpo-three-seed-confirmatory` launch method
  verbatim (same container/mount stack per that cell's run records) with this
  cell's pinned `configs/grpo_cold_base_seed1_full.yaml`; GRPO_REWARD_DEBUG_PATH
  set so the pre-registered diagnostics JSONL is captured (CG-G0 requires all
  three diagnostics; a missing diagnostic is a stop); TRL per-prompt group
  ordering to be confirmed against the first logged groups before diagnostics
  are trusted; then the standard SelfAware eval with the adapter path filled
  from the completed run dir, then `grpo_cold_diagnostics.py`, then CG-G0/CG-G1
  evaluation. Training is hours-scale on the 3090.


- 2026-08-13 SIGNED (lead, PI approval on record: "ok proceed with our
  experiments"). `bin/exp sign` pinned cell.yaml, gates.yaml, both configs, and
  grpo_cold_diagnostics.py (shas in `experiment.yaml`). Launch AUTHORIZED but
  QUEUED behind `dial-logprob-t-deployed-confirmatory` on the single local
  3090; training launch entry will be appended here before the training verb.
  At launch, before trusting diagnostics: confirm TRL per-prompt completion
  ordering in the real GRPO_REWARD_DEBUG_PATH JSONL (builder flag) against the
  first few logged groups.


- 2026-08-13 harness-builder build task: instrument built to signable state,
  no GPU/training work run.
  - `configs/grpo_cold_base_seed1_full.yaml` materialized by cloning
    `experiments/grpo-three-seed-confirmatory/configs/grpo_schema_clean_sft_merged_seed2_v2_full.yaml`
    (itself cloned from the seed-1 precedent) and changing only
    `model.model_name` (raw base hub id `unsloth/Qwen3-4B-bnb-4bit` instead of
    a merged clean-SFT run directory), `training.output_dir`, `seed` (1), and
    `lora.random_state` (1, mirroring the seed per the established
    convention). `model.lora_path` stays `null` in both configs -- the warmed
    sibling's SFT merge is already baked into its `model_name`, so `lora_path`
    was never the field that distinguishes cold from warmed; verified this is
    the ONLY divergence with a structural diff test
    (`test_cold_trainer_config_differs_from_warmed_sibling_only_in_source_and_seed`),
    green.
  - Diagnostics capture mechanism found WITHOUT any synaptic-tuner change and
    WITHOUT a new trainer callback: `archive/experiment/phase1/grpo/
    humility_reward_v2.py`'s `epistemic_humility_reward` (a project reward
    file already loaded unmodified by
    `synaptic-tuner/Trainers/grpo/src/rewards.py`'s
    `build_combined_reward_function`) already writes one JSON debug event per
    reward call when `GRPO_REWARD_DEBUG_PATH` is set (`_write_debug_rows`,
    pre-existing, not added by this build). Each debug row already carries
    `reward`, `valid_json`, and `refused` -- exactly the three fields needed
    for all three pre-registered diagnostics. `grpo_cold_diagnostics.py`
    reads that JSONL post hoc: chunks each event's flat `rows` list into
    groups of `num_generations` (TRL's own per-prompt completions ordering,
    a documented GRPOTrainer invariant not re-verified here since trl is not
    installed in any local venv -- confirmed via `pip show trl` in
    `/home/profsynapse/.venvs/vllm`, not found; the assumption is standard and
    load-bearing only for group reconstruction, flagged for the lead to
    confirm against the real trainer at launch time) to compute (i) the
    zero-advantage fraction from `reward` range per group, (ii) valid-
    contract-parse fraction from `valid_json` across all rollouts, (iii)
    abstention rate from `refused` across all rollouts.
  - `grpo_cold_diagnostics.py` implements `cg_g0_checklist` and `cg_g1_call`
    matching gates.yaml's transcribed CG-G0/CG-G1 exactly (90/10/20
    thresholds). CG-G0's "training completed OR degenerate-reward stop"
    check is an exclusive-or, not an either-branch pass, per AMENDMENT.md
    ("no silent restarts, no reward retuning").
  - `configs/eval_grpo_cold_start_selfaware_full_local_4b.yaml` materialized
    by cloning the SAME `run_eval.py` config schema every GRPO-matrix arm
    uses (`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_
    ..._clean_sft_grpo_v2_seed2_full_local_4b.yaml`); `model_name` is the raw
    foundation hub id (no merge exists for this arm); relative paths
    (`gold_path`, `eval_sets.selfaware.path`) verified against
    `archive/experiment/phase1/eval/run_eval.py:49` (`EVAL_DIR =
    Path(__file__).resolve().parent`) to resolve relative to the EVAL
    SCRIPT's own directory, not the config file's directory -- confirmed
    4 `../` levels from `archive/experiment/phase1/eval/` reaches repo root,
    matching every sibling config's own path depth exactly.
  - **FLAGGED FOR THE LEAD -- known incompleteness, not hidden:**
    `configs/eval_grpo_cold_start_selfaware_full_local_4b.yaml`'s
    `arms[0].adapter` is a placeholder (`<FILLED_AFTER_TRAINING>/final_model`)
    because the real adapter path embeds a training-run timestamp that does
    not exist until training actually runs -- exactly the same incremental-
    materialization gap every sibling arm in
    `experiments/grpo-three-seed-confirmatory/configs/` went through (those
    eval configs were added to the repo only after their training run
    completed). A smoke test
    (`test_cold_eval_config_loads_and_flags_its_own_placeholder`) pins this
    so the placeholder cannot silently start looking like a real path.
  - **FLAGGED FOR THE LEAD -- diagnostics/eval hand-off gap:**
    `grpo_cold_diagnostics.py` does not parse `run_eval.py`'s results
    directory itself (out of scope for this build; the results-directory
    schema was not traced in depth). The CLI accepts
    `--eval-refusal-recall-pct` as a caller-supplied number; the launcher
    must read it from the standard eval summary (same `refusal_recall_pct`
    field name `grpo-three-seed-confirmatory/gates.yaml` itself derives its
    thresholds from) before calling `cg_g1_call`.
  - Persistence: `grpo_cold_diagnostics.py` declared `short-run` (not
    incremental -- it is a fast, idempotent, non-GPU post-hoc pass over an
    already-written JSONL; a kill mid-run just means rerun it once the debug
    JSONL and eval summary exist). Measured wall clock 0.207s over a
    realistically-sized synthetic fixture (465 events x 128 rows/event,
    15.66MB, matching the ~465-step budget); declared 2.0s in
    `experiment.yaml` with safety margin.
  - `instrument.engine_exception: {kind: parity-locked, reason: ...}` claimed
    per the AMENDMENT's own registered carve-out (not relitigated): the
    rollout engine must stay `train_grpo.py`'s own TRL GRPOTrainer generation
    path, not vLLM, or the cold-vs-warmed comparison is confounded by an
    instrument change. Did not attempt to verify vLLM capability limits here
    since the exception is already ruled in the AMENDMENT and does not turn
    on any vLLM capability question.
  - Ran `python3 -m pytest experiments/grpo-cold-start-induction/
    test_grpo_cold_diagnostics_smoke.py -v` -> 20 passed (base conda env).
    Covers: per-group advantage stats (zero/nonzero groups, malformed-event
    flagging, all-zero Null-B shape), contract-parse/abstention fractions,
    empty-input None-not-crash, CG-G0 pass/fail on each individual check
    (training-status xor, partial eval coverage, missing diagnostic,
    malformed capture), CG-G1 across all four bands including exact boundary
    values (10.0 lands in the ambiguous band, not Null-A), end-to-end CLI over
    a fixture debug JSONL, missing-debug-path exit code, and the two config-
    materialization diff tests. No CPU smoke of the trainer/eval launch
    itself was run (no training step, per the harness-builder brief) --
    config LOADS and PARSES correctly; the diagnostics module's real-data
    behavior against an actual trainer-produced debug JSONL is unverified
    until a real launch.
  - `experiment.yaml` filled: `instrument.configs` lists both materialized
    configs plus cell.yaml/gates.yaml; `instrument.modules: [grpo_cold_
    diagnostics.py]` with its persistence declaration; `instrument.
    engine_exception` satisfies the generation-engine sign gate for a
    training-run type. `pins: {}` left empty -- this build task does NOT
    sign; `bin/exp sign` is the lead/PI's call.

## 2026-08-14 -- training complete; eval launch

- Training container exited 0 after the full 1,861-step run (launched
  2026-08-13T18:19:49Z, ~8.2h wall clock, longer than the warmed
  precedent's 7.2h). final_model present in the run dir; reward-debug
  JSONL complete at 1,861 step records. No restarts, no reward retuning.
- Eval launch (this entry precedes the launch verb): full 3,369-row
  SelfAware eval under the matrix parity instrument, via a COPY of the
  pinned eval config under analysis/ with the authorized
  <FILLED_AFTER_TRAINING>/final_model placeholder resolved to the real
  run-dir path (pinned file untouched). Diagnostics
  (grpo_cold_diagnostics.py, pinned) run after eval with
  --eval-refusal-recall-pct from the eval summary. Gate adjudication
  (CG-G0/CG-G1) stays with the lead after both complete.
