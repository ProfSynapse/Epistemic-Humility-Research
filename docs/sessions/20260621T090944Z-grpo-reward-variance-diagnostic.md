---
schema_version: research-session/v1
session_id: 20260621T090944Z-grpo-reward-variance-diagnostic
title: GRPO Reward Variance Diagnostic
status: active
created_at: '2026-06-21T09:09:44Z'
updated_at: '2026-06-22T03:36:58Z'
phase: phase1
question: Can local GRPO rollouts produce parseable completions and nonzero reward
  variance under intended generation/reward settings before scaling training?
tags:
- experiment-runner
run_ids:
- sft_json_bridge_seed1_20260621_102859
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Amendment B / GRPO bootstrap preflight after stated-confidence
    eval layer.
  changed_by_session: GRPO base smoke moved from infrastructure-only to nonzero reward-variance
    proof under native Qwen template plus high-exploration sampling; a bounded 64-step
    base pilot trained and evaluated cleanly but did not move core SelfAware refusal/correctness
    behavior versus the base control; SFT-start remains blocked on answer-only format
    inertia.
checkpoints:
- id: 001-planning
  at: '2026-06-21T09:09:44Z'
  kind: planning
  title: Reward-Variance Gate
  summary: Prior GRPO smokes proved Docker/model/reward plumbing but had zero within-prompt
    reward variance. This session gates longer GRPO on raw rollout inspection, JSON
    parse coverage, and nonzero trainer reward std.
  evidence:
  - experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml
  - experiment/phase1/grpo/humility_reward.py
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py
    -q
  decisions:
  - Do not scale GRPO until sampled completions and trainer logs show a real comparative
    reward signal.
  next_steps: []
  signals: {}
- id: 002-observation
  at: '2026-06-21T09:24:46Z'
  kind: observation
  title: Native Qwen Template Fix
  summary: Base rollout diagnostics with tokenizer-native Qwen templating and enable_thinking=false
    produced high JSON coverage, no clipping, and nonzero reward variance; generic
    ChatML templating ignored the Qwen thinking switch and produced clipped think
    traces.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/base_20260621_052343/summary.json
  - scratch/grpo_bootstrap/diagnostics/base_20260621_052343/rollouts.jsonl
  - https://qwen.readthedocs.io/en/latest/getting_started/quickstart.html
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1
    -Mode base -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256
  decisions:
  - Add generic Synaptic Tuner GRPO support for chat_template_kwargs and native/tokenizer
    chat-template preservation.
  next_steps: []
  signals:
    mean_valid_json_rate: 0.875
    mean_clipped_rate: 0.0
    mean_reward_std: 0.4778972476243142
    zero_std_prompt_rate: 0.25
- id: 003-observation
  at: '2026-06-21T09:28:33Z'
  kind: observation
  title: SFT-Start Format Inertia
  summary: SFT seed 1 retained the old answer-only/refusal behavior and produced zero
    valid JSON even with native Qwen thinking-off templating and eight rollouts per
    prompt. SFT-start GRPO is therefore not ready for the stated-confidence objective
    without a format bridge or separate prompt-contract adaptation.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/sft-seed1_20260621_052656/summary.json
  - scratch/grpo_bootstrap/diagnostics/sft-seed1_20260621_052656/rollouts.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1
    -Mode sft-seed1 -MaxRows 4 -NumRollouts 8 -MaxCompletionLength 256
  decisions:
  - Treat base-start GRPO as the first working GRPO bootstrap target; treat SFT-start
    GRPO as requiring an additional format/alignment bridge before scale.
  next_steps: []
  signals:
    mean_valid_json_rate: 0.0
    mean_clipped_rate: 0.0
    mean_reward_std: 0.18069985738082223
    zero_std_prompt_rate: 0.5
- id: 004-result
  at: '2026-06-21T09:43:51Z'
  kind: result
  title: Trainer Reward Variance Achieved
  summary: Base GRPO micro-smoke with native Qwen template, four generations, 256
    completion tokens, and high-exploration sampling produced nonzero reward std on
    three of six trainer steps, nonzero grad norms, nonzero KL after step 1, no clipping,
    and completed artifact save-out.
  evidence:
  - scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_094323/logs/training_20260621_094351.jsonl
  - scratch/grpo_bootstrap/reward_debug/base_latest.jsonl
  run_ids:
  - grpo_base_micro_smoke_20260621_094323
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode base -Force -DebugReward
  decisions:
  - The GRPO base pipeline is now locally operational as a smoke-tested training path;
    longer runs still need a protocol-scale decision and post-run eval gate.
  - Keep reward debug opt-in only; use it when reward_std unexpectedly collapses.
  next_steps:
  - Decide whether to run a bounded base-GRPO pilot or first build an SFT-format bridge
    for SFT-start GRPO.
  - If scaling base-GRPO, keep native Qwen template and high-exploration sampling,
    then evaluate against the stated-confidence comparison set.
  signals:
    nonzero_reward_std_steps: 3
    total_logged_train_steps: 6
    max_reward_std: 0.8133816123008728
    max_grad_norm: 5.968965530395508
    max_kl: 0.010111197829246521
    max_clipped_ratio: 0.0
- id: 005-launch
  at: '2026-06-21T10:04:00Z'
  kind: launch
  title: Bounded Base-GRPO Pilot
  summary: Proceeding from the successful base smoke to a bounded base-GRPO pilot
    on the full projected GRPO train JSONL with the same native Qwen thinking-off
    template and high-exploration sampler. This remains local Amendment B pilot evidence,
    not headline Phase 1 evidence.
  evidence:
  - experiment/phase1/grpo/configs/grpo_base_pilot.yaml
  - scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl
  run_ids:
  - grpo_base_pilot_pending
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode base-pilot -Force -DebugReward
  decisions:
  - Keep the smoke config separate from the pilot config so the six-step gate remains
    fast and reproducible.
  - Run reward debug for the first pilot so raw candidate diversity can be audited
    if reward variance collapses.
  next_steps:
  - Inspect reward std, clipping, grad norms, KL, train_end, final_model, training_lineage,
    and reward debug trace after completion.
  - If pilot artifacts are healthy, evaluate the pilot adapter against the stated-confidence
    eval layer.
  signals: {}
- id: 006-result
  at: '2026-06-21T10:08:00Z'
  kind: result
  title: Base-GRPO Pilot Completed
  summary: The 64-step base-GRPO pilot completed locally, saved a final LoRA adapter
    and lineage, maintained nonzero reward variance on most logged steps, and showed
    no clipping or OOM pressure. Reward-debug rollouts were mostly parseable JSON
    and frequently had within-group diversity, so the GRPO training signal exists
    under this setup.
  evidence:
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/logs/training_20260621_095545.jsonl
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/final_model/adapter_model.safetensors
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/training_lineage.json
  - scratch/grpo_bootstrap/reward_debug/base-pilot_latest.jsonl
  run_ids:
  - grpo_base_pilot_20260621_095511
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode base-pilot -Force -DebugReward
  decisions:
  - Treat reward variance as a training-plumbing gate only; behavioral movement must
    be checked by same-slice eval before interpreting the pilot as scientific evidence.
  next_steps:
  - Evaluate the pilot adapter on the 192-row SelfAware stated-confidence slice and
    compare against the same prompt-contract base control.
  signals:
    steps: 64
    nonzero_reward_std_steps: 40
    zero_std_rate: 0.375
    mean_reward_std: 0.415088304085657
    max_reward_std: 1.6887495517730713
    mean_reward: -0.30478515452705324
    max_clipped_ratio: 0.0
    max_grad_norm: 11.482610702514648
    max_kl: 0.03641607612371445
    valid_json_rate: 0.9453125
    multi_unique_group_rate: 0.78125
    refusal_text_rate: 0.5078125
- id: 007-result
  at: '2026-06-21T10:08:00Z'
  kind: result
  title: Base-GRPO Pilot Eval Was Base-Like
  summary: 'Live vLLM eval of the 64-step base-GRPO pilot on the 192-row SelfAware
    stated-confidence slice completed successfully, but the scored behavior was unchanged
    from the base prompt-contract control: refusal recall 1.05%, over-refusal 1.03%,
    correct-on-known 23.96%, truthful 12.5%. Row-level comparison showed 52/192 answer
    texts changed, but 0 refusal decisions changed and only 2 correctness labels moved,
    one improvement and one regression.'
  evidence:
  - experiment/phase1/eval/config/eval_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_local_4b.yaml
  - experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b/base_grpo_pilot_64__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b/base_grpo_pilot_64__selfaware/scored_rows.jsonl
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b/base_seed1_smoke__selfaware/metrics.json
  run_ids:
  - eval_base_grpo_pilot_64_selfaware_20260621
  commands:
  - docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo"
    -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config
    experiment/phase1/eval/config/eval_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_local_4b.yaml
    --live-vllm
  decisions:
  - Do not treat this pilot as evidence that GRPO improved humility yet; it is evidence
    that local base-GRPO training/eval plumbing works and that 64 low-LR steps are
    behaviorally too weak on the current slice.
  - Next GRPO scaling should change one of duration, reward strength, curriculum,
    or starting policy, and should keep same-slice behavioral comparators as a hard
    gate.
  next_steps:
  - Decide whether the next GRPO step is a longer base-start pilot, a prompt-contract/format
    bridge for SFT-start GRPO, or reward-weight/curriculum tuning before another pilot.
  signals:
    n: 192
    refusal_recall_pct: 1.05
    over_refusal_pct: 1.03
    correct_on_known_pct: 23.96
    truthful_pct: 12.5
    stated_confidence_coverage_pct: 100.0
    mean_stated_confidence: 0.901562
    changed_answer_text_rows: 52
    changed_refusal_rows: 0
    changed_correctness_rows: 2
- id: 008-planning
  at: '2026-06-21T10:16:21Z'
  kind: planning
  title: Merged-SFT GRPO Start
  summary: Proceeding to test GRPO with the merged SFT seed1 model as the base policy,
    rather than stacking the SFT LoRA through model.lora_path. The goal is to preserve
    the SFT abstention behavior while training a fresh GRPO LoRA on the answer/confidence
    reward contract.
  evidence:
  - experiment/phase1/grpo/configs/grpo_sft_merged_seed1_micro_smoke.yaml
  - experiment/phase1/grpo/configs/grpo_sft_merged_seed1_pilot.yaml
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1
    -Mode sft-merged-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256 -Temperature
    1.6 -TopP 1.0
  decisions:
  - Gate SFT-merged GRPO on rollout parseability and reward variance before running
    the micro-smoke or bounded pilot.
  next_steps:
  - Run the rollout/reward diagnostic for sft-merged-seed1; if JSON coverage and reward
    variance are viable, run the micro-smoke with reward debug.
  signals: {}
- id: 009-launch
  at: '2026-06-21T10:21:04Z'
  kind: launch
  title: SFT JSON Bridge Launch
  summary: The merged-SFT rollout diagnostic had nonzero reward variance but 0% valid
    answer/confidence JSON, so direct GRPO is deferred. Launching a 64-step SFT format
    bridge on top of the merged SFT seed1 base using 256 projected GRPO rows with
    assistant JSON targets.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_061629/summary.json
  - scratch/grpo_bootstrap/qwen3-4b-instruct/sft_json_bridge_smoke_256.jsonl
  - experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge.yaml
  run_ids: []
  commands:
  - docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v ${PWD}:/workspace/repo
    -w /workspace/repo unsloth/unsloth:latest synaptic-tuner/Trainers/sft/train_sft.py
    --config experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge.yaml --max-steps
    64 --no-dashboard --quiet
  decisions:
  - Use a supervised format bridge before GRPO because malformed merged-SFT completions
    make direct confidence-reward GRPO a weak indirect format correction.
  next_steps:
  - After the bridge completes, patch the GRPO bridge config to its final_model path
    and rerun rollout diagnostics before GRPO training.
  signals: {}
- id: 010-amendment
  at: '2026-06-21T10:23:01Z'
  kind: amendment
  title: Response-Confidence Reward Correction
  summary: 'Corrected Amendment B GRPO confidence semantics before bridge training.
    Confidence now means probability that the answer or abstention is the appropriate
    response: high for known-correct answers and unknown abstentions, low for wrong
    guesses and inappropriate known-question refusals. Regenerated GRPO and bridge
    scratch datasets with the updated prompt/targets.'
  evidence:
  - experiment/phase1/grpo/humility_reward.py
  - experiment/phase1/grpo/build_grpo_dataset.py
  - experiment/phase1/grpo/build_sft_json_bridge_dataset.py
  - scratch/grpo_bootstrap/reward_sanity_table.csv
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py
    synaptic-tuner/tests/trainers/grpo/test_data_loader_chat_template_kwargs.py -q
  decisions:
  - Do not launch the bridge or GRPO run under the old factual-answer confidence target;
    use response-confidence targets for Amendment B GRPO.
  next_steps:
  - Rerun merged-SFT rollout diagnostics with regenerated prompts, then train the
    JSON bridge if parseability still fails.
  signals: {}
- id: 011-gate
  at: '2026-06-21T10:25:11Z'
  kind: gate
  title: Merged-SFT JSON Gate Failed
  summary: Rerunning the merged-SFT rollout diagnostic after the response-confidence
    prompt correction still produced 0% valid JSON, with nonzero reward variance and
    no clipping. This confirms direct GRPO from merged SFT remains format-blocked
    and should go through the SFT JSON bridge first.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_062309/summary.json
  - scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_062309/rollouts.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1
    -Mode sft-merged-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256 -Temperature
    1.6 -TopP 1.0
  decisions:
  - Proceed with the supervised JSON bridge before any SFT-start GRPO training.
  next_steps:
  - Run the 64-step SFT JSON bridge on the merged SFT seed1 base.
  signals: {}
- id: 012-result
  at: '2026-06-21T10:31:23Z'
  kind: result
  title: SFT JSON Bridge Completed
  summary: The 64-step SFT JSON bridge on top of merged SFT seed1 completed successfully
    on 256 bridge rows, saved final_model, training_lineage, and capacity artifacts.
    Loss fell quickly, indicating the adapter learned the narrow answer/confidence
    JSON format target.
  evidence:
  - scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/final_model/adapter_model.safetensors
  - scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/training_lineage.json
  - scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/logs/training_20260621_103002.jsonl
  run_ids:
  - sft_json_bridge_seed1_20260621_102859
  commands:
  - docker run --rm --gpus all --ipc=host --entrypoint python3 ... synaptic-tuner/Trainers/sft/train_sft.py
    --config experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge_config.py
    --max-steps 64 --no-dashboard --quiet
  decisions:
  - Use the bridge final_model as model.lora_path for the next GRPO rollout diagnostic
    and micro-smoke, with the merged SFT seed1 model remaining the base model.
  next_steps:
  - Run rollout diagnostics through the bridge adapter to verify JSON coverage and
    reward variance before GRPO micro-smoke.
  signals: {}
- id: 013-gate
  at: '2026-06-21T10:38:10Z'
  kind: gate
  title: SFT JSON Bridge GRPO Gate Passed
  summary: The SFT JSON bridge rollout diagnostic improved valid answer/confidence
    JSON coverage from 0% to 68.75%, retained nonzero reward variance on all four
    sampled prompts, and had 0% clipping. This clears the local gate for an SFT-start
    GRPO micro-smoke through the bridge adapter.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/sft-json-bridge-seed1_20260621_063133/summary.json
  - scratch/grpo_bootstrap/diagnostics/sft-json-bridge-seed1_20260621_063133/rollouts.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1
    -Mode sft-json-bridge-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256
    -Temperature 1.6 -TopP 1.0
  decisions:
  - Proceed to GRPO micro-smoke with reward debug using the merged SFT seed1 base
    plus JSON bridge adapter.
  next_steps:
  - Run experiment/phase1/grpo/run_micro_smoke.ps1 -Mode sft-json-bridge-seed1 -Force
    -DebugReward.
  signals: {}
- id: 014-decision
  at: '2026-06-21T10:47:35Z'
  kind: decision
  title: Response-Confidence Reward Ladder Locked
  summary: 'Reward confidence now means confidence that the answer or abstention is
    appropriate. The reward keeps intermediate signal: low-confidence wrong answers
    and low-confidence known-question abstentions are penalized less than confident
    wrong or confident over-refusal, while remaining below correct confident answers.'
  evidence:
  - 'reward_sanity_table now includes known_over_refusal_low_conf. Current ordering:
    known_correct_high_conf 1.248750; known_over_refusal_low_conf -0.351250; known_wrong_low_conf
    -0.776250; known_over_refusal_high_conf -0.801250; known_wrong_high_conf -1.676250;
    unknown_abstain_high_conf 0.498750.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Rerun bridge GRPO micro-smoke with temp=1.0, top_p=0.95, max_completion_length=128.
  signals: {}
- id: 015-observation
  at: '2026-06-21T10:47:35Z'
  kind: observation
  title: Bridge GRPO High-Temperature Smoke Exposed Clipping
  summary: SFT JSON bridge made GRPO operational, but the first bridge micro-smoke
    reused the high-exploration base-GRPO sampler and produced nonzero reward variance
    together with frequent clipped/gibberish malformed completions. This validates
    plumbing but is not a scaling setting.
  evidence:
  - Run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_micro_smoke/20260621_103852
    completed 6 steps with reward std > 0 on every logged step, but clipped_ratio
    reached 0.75 on multiple steps in trainer logs/reward debug.
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Use a cleaner bridge sampler before pilot scale: lower temperature and shorter
    completion budget, then rerun the micro-smoke.'
  signals: {}
- id: 016-result
  at: '2026-06-21T11:05:53Z'
  kind: result
  title: SFT-Bridge GRPO 8-Generation Smoke Passed
  summary: 'Using the SFT seed-1 merged model plus a 256-row JSON bridge adapter,
    the GRPO micro-smoke passed the practical gate with 8 generations per prompt:
    valid schema, no clipping, and nonzero comparative reward signal on every step.'
  evidence:
  - 'Run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_micro_smoke/20260621_110345
    completed 6 GRPO steps. Trainer aggregate: nonzero_reward_std_steps=6/6, mean_reward_std=1.099736,
    max_clipped_ratio=0.0, max_completion_length_seen=22. Reward debug: 48/48 valid
    JSON. Capacity: peak reserved VRAM 4.174GB, OOM risk low.'
  run_ids: []
  commands: []
  decisions:
  - For SFT-bridge GRPO micro/pilot bootstrapping, prefer num_generations=8, per_device_train_batch_size=8,
    temperature=1.35, top_p=1.0, max_completion_length=128 over either low-temp 4-generation
    deterministic settings or high-temp 256-token settings.
  next_steps:
  - Validate touched code/docs, then commit/PR the GRPO bootstrap changes before moving
    to a longer SFT-bridge GRPO pilot.
  signals: {}
- id: 017-launch
  at: '2026-06-21T11:17:23Z'
  kind: launch
  title: SFT-Bridge GRPO Full Run Launched
  summary: Launched the full local SFT-bridge GRPO seed-1 run after a Docker dry-run
    validated model load and all 14,395 GRPO train rows.
  evidence:
  - Container grpo_sft_json_bridge_seed1_full_20260621_071711 launched from config
    experiment/phase1/grpo/configs/grpo_sft_json_bridge_seed1_full.yaml. Dry run loaded
    merged SFT seed-1 + JSON bridge adapter and formatted 14,395 examples.
  run_ids: []
  commands:
  - docker run -d --name grpo_sft_json_bridge_seed1_full_20260621_071711 ... train_grpo.py
    --config experiment/phase1/grpo/configs/grpo_sft_json_bridge_seed1_full.yaml
  decisions: []
  next_steps:
  - Monitor logs, GPU, and training_lineage/log files until completion; fix issues
    if the full run fails.
  signals: {}
- id: 018-heartbeat
  at: '2026-06-21T11:26:19Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Early Health
  summary: The full SFT-bridge GRPO run has entered training and early metrics are
    healthy enough to continue.
  evidence:
  - At step 150/14395, throughput ~0.352 steps/sec, reward_std ~0.879, frac_reward_zero_std
    ~0.12, clipped_ratio 0.0, reserved VRAM ~4.176GB, OOM risk low. Current estimate
    is roughly 11 hours remaining.
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue timed local monitoring until completion; first stronger gate after checkpoint-500
    appears.
  signals: {}
- id: 019-heartbeat
  at: '2026-06-21T11:46:40Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Checkpoint 500 Healthy
  summary: The full SFT-bridge GRPO run passed the first checkpoint gate and remains
    healthy enough to continue.
  evidence:
  - At step 600/14395, checkpoint-500 exists, throughput ~0.371 steps/sec, reward_std
    ~0.487, frac_reward_zero_std ~0.52 on the latest 25-step window, clipped_ratio
    ~0.005, reserved VRAM ~4.176GB, OOM risk low.
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue hourly monitoring through subsequent checkpoints; watch for reward variance
    collapse or sustained clipping.
  signals: {}
- id: 020-heartbeat
  at: '2026-06-21T12:47:21Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 1600 Watchpoint
  summary: The full run remains stable through step 1600, but reward variance is lower
    and clipping higher than the micro-smoke, so continue with watchpoints rather
    than treating settings as final.
  evidence:
  - 'Through step 1600: checkpoints 500/1000/1500 saved; last-20 reward_std mean 0.386,
    frac_reward_zero_std mean 0.58, clipped_ratio mean 0.072, KL mean 0.447, reserved
    VRAM ~4.176GB, OOM risk low. ETA ~11.7h from step 1600.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue full run; intervene if reward_std collapses near zero, clipped_ratio
    sustains materially above ~0.15-0.20, KL spikes, or container exits.
  signals: {}
- id: 021-heartbeat
  at: '2026-06-21T13:48:00Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 2500 Continuing
  summary: The full run remains stable through step 2500 and has not hit OOM or clipping
    failure, though reward variance is weaker than the micro-smoke.
  evidence:
  - 'At step 2500/14395: checkpoints 1500/2000/2500 present; last-20 reward_std mean
    0.3635, latest reward_std 0.1282; last-20 frac_reward_zero_std mean 0.596, latest
    0.8; last-20 clipped_ratio mean 0.0548, latest 0.01; KL last-20 mean 0.451; VRAM
    ~4.176GB reserved, OOM risk low.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring; do not call this final until post-run eval shows behavioral
    movement.
  signals: {}
- id: 022-heartbeat
  at: '2026-06-21T14:48:31Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 3375 Stable
  summary: The full SFT-bridge GRPO run remains stable through step 3375, with reward
    variance rebounding after the step-2500 watchpoint.
  evidence:
  - 'At step 3375/14395: checkpoint-3000 exists; last-20 reward_std mean 0.373, latest
    0.649; last-20 frac_reward_zero_std mean 0.616, latest 0.4; last-20 clipped_ratio
    mean 0.047; KL last-20 mean 0.410; VRAM ~4.176GB reserved.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue hourly monitoring through the full epoch.
  signals: {}
- id: 023-heartbeat
  at: '2026-06-21T15:48:59Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 4300 Stable
  summary: The full run remains stable through step 4300 with modest clipping and
    nonzero rolling reward variance.
  evidence:
  - 'At step 4300/14395: checkpoints 3000/3500/4000 present; last-20 reward_std mean
    0.305, latest 0.277; last-20 frac_reward_zero_std mean 0.67; last-20 clipped_ratio
    mean 0.039; KL last-20 mean 0.301; VRAM ~4.176GB reserved.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue hourly monitoring.
  signals: {}
- id: 024-heartbeat
  at: '2026-06-21T16:49:30Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 5150 Stable
  summary: The full run remains stable through step 5150; reward variance persists
    and checkpoint-5000 exists.
  evidence:
  - 'At step 5150/14395: checkpoints 4000/4500/5000 present; last-20 reward_std mean
    0.357, latest 0.499; last-20 frac_reward_zero_std mean 0.634; last-20 clipped_ratio
    mean 0.0675 with max20 0.165; KL last-20 mean 0.283; VRAM ~4.176GB reserved.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring, with longer intervals unless clipping or variance worsens.
  signals: {}
- id: 025-heartbeat
  at: '2026-06-21T18:20:02Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 6450 Stable
  summary: The full run remains stable through step 6450, almost halfway through the
    epoch.
  evidence:
  - 'At step 6450/14395: checkpoints 5000/5500/6000 present; last-20 reward_std mean
    0.303, latest 0.207; last-20 frac_reward_zero_std mean 0.692; last-20 clipped_ratio
    mean 0.0778, max20 0.16; KL last-20 mean 0.222; VRAM ~4.176GB reserved.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring through full completion; run post-training eval/diagnostic
    after final_model is saved.
  signals: {}
- id: 026-heartbeat
  at: '2026-06-21T19:50:31Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 7850 Stable
  summary: The full run is past the halfway point and remains stable enough to continue.
  evidence:
  - 'At step 7850/14395: checkpoints 6500/7000/7500 present; last-20 reward_std mean
    0.266, latest 0.528; last-20 frac_reward_zero_std mean 0.724; last-20 clipped_ratio
    mean 0.068, max20 0.145; KL last-20 mean 0.190; VRAM ~4.9GB used by nvidia-smi.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring to completion.
  signals: {}
- id: 027-heartbeat
  at: '2026-06-21T21:21:01Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 9100 Stable
  summary: The full run remains stable through step 9100 with persistent reward variance
    and modest clipping.
  evidence:
  - 'At step 9100/14395: checkpoints 8000/8500/9000 present; last-20 reward_std mean
    0.331, latest 0.415; last-20 frac_reward_zero_std mean 0.654; last-20 clipped_ratio
    mean 0.0825, max20 0.14; KL last-20 mean 0.205; ETA about 5.8h.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue to completion and then inspect final artifacts/evaluate.
  signals: {}
- id: 028-heartbeat
  at: '2026-06-21T22:51:38Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 10425 Stable
  summary: The full run remains stable past 10k steps and is roughly 72% through the
    epoch.
  evidence:
  - 'At step 10425/14395: checkpoints 9000/9500/10000 present; last-20 reward_std
    mean 0.346, latest 0.412; last-20 frac_reward_zero_std mean 0.67; last-20 clipped_ratio
    mean 0.0648; KL last-20 mean 0.253; ETA about 4.4h.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring to completion.
  signals: {}
- id: 029-heartbeat
  at: '2026-06-22T00:22:11Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 11775 Stable
  summary: The full run remains stable through step 11775 and is in the final third
    of the epoch.
  evidence:
  - 'At step 11775/14395: checkpoints 10500/11000/11500 present; last-20 reward_std
    mean 0.326, latest 0.349; last-20 frac_reward_zero_std mean 0.656; last-20 clipped_ratio
    mean 0.0845; KL last-20 mean 0.220; ETA about 2.9h.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Continue monitoring; after completion verify final_model, lineage, capacity, and
    run aggregate metrics.
  signals: {}
- id: 030-heartbeat
  at: '2026-06-22T01:52:40Z'
  kind: heartbeat
  title: SFT-Bridge GRPO Full Run Step 13150 Stable
  summary: The full run is in the final stretch and remains stable through step 13150.
  evidence:
  - 'At step 13150/14395: checkpoints 12000/12500/13000 present; last-20 reward_std
    mean 0.271, latest 0.391; last-20 frac_reward_zero_std mean 0.726; last-20 clipped_ratio
    mean 0.068; KL last-20 mean 0.207; ETA about 1.4h.'
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Run a shorter final monitor interval, then verify final artifacts and aggregate
    metrics after container exit.
  signals: {}
- id: 031-result
  at: '2026-06-22T03:36:58Z'
  kind: result
  title: SFT-Bridge GRPO Full Run Completed
  summary: The full local SFT-bridge GRPO seed-1 run completed successfully and produced
    a final adapter. A same-slice pre/post dev diagnostic shows behavioral movement
    in the intended direction, with a small schema-format regression.
  evidence:
  - 'Training run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743
    exited 0 with final_model, training_lineage.json, capacity_features.json, checkpoint-14395,
    final_step=14395, train_runtime=57126.097s, peak reserved VRAM 4.191GB, OOM risk
    low. Train aggregate over 575 logged windows: reward_std mean 0.338, frac_reward_zero_std
    mean 0.652, clipped_ratio mean 0.061, KL mean 0.286. Eval-like 64-row dev comparison
    at temp=0.7/top_p=0.95/max_completion=96: pre-bridge known valid 1.000/refusal
    0.344/mean_reward 0.153/correct_known 17/32; post-GRPO known valid 0.969/refusal
    0.281/mean_reward 0.339/correct_known 19/32. Pre-bridge unknown valid 1.000/refusal
    0.812/mean_reward 0.078; post-GRPO unknown valid 1.000/refusal 0.844/mean_reward
    0.148.'
  run_ids: []
  commands: []
  decisions:
  - 'Treat SFT-bridge GRPO as operational and promising on this bounded dev diagnostic,
    but not finalized: full evaluation should quantify schema failures and behavior
    over the full eval suite before interpreting as headline evidence.'
  next_steps:
  - Commit/PR full-run config and diagnostics; then run the standard eval pipeline
    for the completed GRPO adapter.
  signals: {}
legacy_session:
  id: grpo-reward-variance-diagnostic
  path: docs/sessions/0015 - grpo-reward-variance-diagnostic.md
---
# GRPO Reward Variance Diagnostic

## Question

Can local GRPO rollouts produce parseable completions and nonzero reward variance under intended generation/reward settings before scaling training?

## Trajectory Position

This sits in Amendment B / GRPO bootstrap after the stated-confidence evaluation layer. The goal is not headline evidence yet; it is proving that local GRPO can produce parseable answer/confidence rollouts and a nonzero comparative reward signal before any longer pilot.

## Summary

Base-start GRPO now works as a local smoke-tested training path when Qwen uses its tokenizer-native chat template with `enable_thinking: false` and high-exploration sampling. The 64-step base pilot trained and evaluated cleanly, but the same-slice SelfAware behavior remained base-like: wording moved, but refusal behavior did not. SFT-start GRPO is not ready for the same objective because the SFT seed 1 checkpoint keeps producing answer-only outputs with zero valid JSON; it likely needs a small format bridge or separate prompt-contract adaptation before confidence-reward GRPO.

## Checkpoints

### 001-planning - Reward-Variance Gate

- at: `2026-06-21T09:09:44Z`
- kind: `planning`
- summary: Prior GRPO smokes proved Docker/model/reward plumbing but had zero within-prompt reward variance. This session gates longer GRPO on raw rollout inspection, JSON parse coverage, and nonzero trainer reward std.

### 002-observation - Native Qwen Template Fix

- at: `2026-06-21T09:24:46Z`
- kind: `observation`
- summary: Base rollout diagnostics with tokenizer-native Qwen templating and `enable_thinking: false` produced high JSON coverage, no clipping, and nonzero reward variance. Generic ChatML templating ignored the Qwen thinking switch and produced clipped think traces.

### 003-observation - SFT-Start Format Inertia

- at: `2026-06-21T09:28:33Z`
- kind: `observation`
- summary: SFT seed 1 retained the old answer-only/refusal behavior and produced zero valid JSON even with native Qwen thinking-off templating and eight rollouts per prompt.

### 004-result - Trainer Reward Variance Achieved

- at: `2026-06-21T09:43:51Z`
- kind: `result`
- summary: Base GRPO micro-smoke with native Qwen template, four generations, 256 completion tokens, and high-exploration sampling produced nonzero reward std on three of six trainer steps, nonzero grad norms, nonzero KL after step 1, no clipping, and completed artifact save-out.

### 005-launch - Bounded Base-GRPO Pilot

- at: `2026-06-21T10:04:00Z`
- kind: `launch`
- summary: Proceeding from the successful base smoke to a bounded base-GRPO pilot on the full projected GRPO train JSONL with the same native Qwen thinking-off template and high-exploration sampler. This remains local Amendment B pilot evidence, not headline Phase 1 evidence.

### 006-result - Base-GRPO Pilot Completed

- at: `2026-06-21T10:08:00Z`
- kind: `result`
- summary: The 64-step base-GRPO pilot completed locally, saved `final_model`, lineage, and reward-debug artifacts, and produced nonzero reward std on 40/64 logged steps with no clipping or OOM pressure.

### 007-result - Base-GRPO Pilot Eval Was Base-Like

- at: `2026-06-21T10:08:00Z`
- kind: `result`
- summary: Live vLLM eval of the pilot on the 192-row SelfAware stated-confidence slice matched the base control on core metrics: refusal recall 1.05%, over-refusal 1.03%, correct-on-known 23.96%, truthful 12.5%. Row-level comparison found 52 changed answer texts but zero changed refusal decisions.
### 008-planning - Merged-SFT GRPO Start

- at: `2026-06-21T10:16:21Z`
- kind: `planning`
- summary: Proceeding to test GRPO with the merged SFT seed1 model as the base policy, rather than stacking the SFT LoRA through model.lora_path. The goal is to preserve the SFT abstention behavior while training a fresh GRPO LoRA on the answer/confidence reward contract.
- evidence:
  - `experiment/phase1/grpo/configs/grpo_sft_merged_seed1_micro_smoke.yaml`
  - `experiment/phase1/grpo/configs/grpo_sft_merged_seed1_pilot.yaml`
- commands:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1 -Mode sft-merged-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256 -Temperature 1.6 -TopP 1.0`
- decisions:
  - Gate SFT-merged GRPO on rollout parseability and reward variance before running the micro-smoke or bounded pilot.
- next steps:
  - Run the rollout/reward diagnostic for sft-merged-seed1; if JSON coverage and reward variance are viable, run the micro-smoke with reward debug.
### 009-launch - SFT JSON Bridge Launch

- at: `2026-06-21T10:21:04Z`
- kind: `launch`
- summary: The merged-SFT rollout diagnostic had nonzero reward variance but 0% valid answer/confidence JSON, so direct GRPO is deferred. Launching a 64-step SFT format bridge on top of the merged SFT seed1 base using 256 projected GRPO rows with assistant JSON targets.
- evidence:
  - `scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_061629/summary.json`
  - `scratch/grpo_bootstrap/qwen3-4b-instruct/sft_json_bridge_smoke_256.jsonl`
  - `experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge.yaml`
- commands:
  - `docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v ${PWD}:/workspace/repo -w /workspace/repo unsloth/unsloth:latest synaptic-tuner/Trainers/sft/train_sft.py --config experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge.yaml --max-steps 64 --no-dashboard --quiet`
- decisions:
  - Use a supervised format bridge before GRPO because malformed merged-SFT completions make direct confidence-reward GRPO a weak indirect format correction.
- next steps:
  - After the bridge completes, patch the GRPO bridge config to its final_model path and rerun rollout diagnostics before GRPO training.
### 010-amendment - Response-Confidence Reward Correction

- at: `2026-06-21T10:23:01Z`
- kind: `amendment`
- summary: Corrected Amendment B GRPO confidence semantics before bridge training. Confidence now means probability that the answer or abstention is the appropriate response: high for known-correct answers and unknown abstentions, low for wrong guesses and inappropriate known-question refusals. Regenerated GRPO and bridge scratch datasets with the updated prompt/targets.
- evidence:
  - `experiment/phase1/grpo/humility_reward.py`
  - `experiment/phase1/grpo/build_grpo_dataset.py`
  - `experiment/phase1/grpo/build_sft_json_bridge_dataset.py`
  - `scratch/grpo_bootstrap/reward_sanity_table.csv`
- commands:
  - `python -m pytest experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py synaptic-tuner/tests/trainers/grpo/test_data_loader_chat_template_kwargs.py -q`
- decisions:
  - Do not launch the bridge or GRPO run under the old factual-answer confidence target; use response-confidence targets for Amendment B GRPO.
- next steps:
  - Rerun merged-SFT rollout diagnostics with regenerated prompts, then train the JSON bridge if parseability still fails.
### 011-gate - Merged-SFT JSON Gate Failed

- at: `2026-06-21T10:25:11Z`
- kind: `gate`
- summary: Rerunning the merged-SFT rollout diagnostic after the response-confidence prompt correction still produced 0% valid JSON, with nonzero reward variance and no clipping. This confirms direct GRPO from merged SFT remains format-blocked and should go through the SFT JSON bridge first.
- evidence:
  - `scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_062309/summary.json`
  - `scratch/grpo_bootstrap/diagnostics/sft-merged-seed1_20260621_062309/rollouts.jsonl`
- commands:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1 -Mode sft-merged-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256 -Temperature 1.6 -TopP 1.0`
- decisions:
  - Proceed with the supervised JSON bridge before any SFT-start GRPO training.
- next steps:
  - Run the 64-step SFT JSON bridge on the merged SFT seed1 base.
### 012-result - SFT JSON Bridge Completed

- at: `2026-06-21T10:31:23Z`
- kind: `result`
- summary: The 64-step SFT JSON bridge on top of merged SFT seed1 completed successfully on 256 bridge rows, saved final_model, training_lineage, and capacity artifacts. Loss fell quickly, indicating the adapter learned the narrow answer/confidence JSON format target.
- run ids:
  - `sft_json_bridge_seed1_20260621_102859`
- evidence:
  - `scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/final_model/adapter_model.safetensors`
  - `scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/training_lineage.json`
  - `scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/logs/training_20260621_103002.jsonl`
- commands:
  - `docker run --rm --gpus all --ipc=host --entrypoint python3 ... synaptic-tuner/Trainers/sft/train_sft.py --config experiment/phase1/grpo/configs/sft_merged_seed1_json_bridge_config.py --max-steps 64 --no-dashboard --quiet`
- decisions:
  - Use the bridge final_model as model.lora_path for the next GRPO rollout diagnostic and micro-smoke, with the merged SFT seed1 model remaining the base model.
- next steps:
  - Run rollout diagnostics through the bridge adapter to verify JSON coverage and reward variance before GRPO micro-smoke.
### 013-gate - SFT JSON Bridge GRPO Gate Passed

- at: `2026-06-21T10:38:10Z`
- kind: `gate`
- summary: The SFT JSON bridge rollout diagnostic improved valid answer/confidence JSON coverage from 0% to 68.75%, retained nonzero reward variance on all four sampled prompts, and had 0% clipping. This clears the local gate for an SFT-start GRPO micro-smoke through the bridge adapter.
- evidence:
  - `scratch/grpo_bootstrap/diagnostics/sft-json-bridge-seed1_20260621_063133/summary.json`
  - `scratch/grpo_bootstrap/diagnostics/sft-json-bridge-seed1_20260621_063133/rollouts.jsonl`
- commands:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1 -Mode sft-json-bridge-seed1 -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256 -Temperature 1.6 -TopP 1.0`
- decisions:
  - Proceed to GRPO micro-smoke with reward debug using the merged SFT seed1 base plus JSON bridge adapter.
- next steps:
  - Run experiment/phase1/grpo/run_micro_smoke.ps1 -Mode sft-json-bridge-seed1 -Force -DebugReward.
### 014-decision - Response-Confidence Reward Ladder Locked

- at: `2026-06-21T10:47:35Z`
- kind: `decision`
- summary: Reward confidence now means confidence that the answer or abstention is appropriate. The reward keeps intermediate signal: low-confidence wrong answers and low-confidence known-question abstentions are penalized less than confident wrong or confident over-refusal, while remaining below correct confident answers.
- evidence:
  - `reward_sanity_table now includes known_over_refusal_low_conf. Current ordering: known_correct_high_conf 1.248750; known_over_refusal_low_conf -0.351250; known_wrong_low_conf -0.776250; known_over_refusal_high_conf -0.801250; known_wrong_high_conf -1.676250; unknown_abstain_high_conf 0.498750.`
- next steps:
  - Rerun bridge GRPO micro-smoke with temp=1.0, top_p=0.95, max_completion_length=128.
### 015-observation - Bridge GRPO High-Temperature Smoke Exposed Clipping

- at: `2026-06-21T10:47:35Z`
- kind: `observation`
- summary: SFT JSON bridge made GRPO operational, but the first bridge micro-smoke reused the high-exploration base-GRPO sampler and produced nonzero reward variance together with frequent clipped/gibberish malformed completions. This validates plumbing but is not a scaling setting.
- evidence:
  - `Run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_micro_smoke/20260621_103852 completed 6 steps with reward std > 0 on every logged step, but clipped_ratio reached 0.75 on multiple steps in trainer logs/reward debug.`
- next steps:
  - Use a cleaner bridge sampler before pilot scale: lower temperature and shorter completion budget, then rerun the micro-smoke.
### 016-result - SFT-Bridge GRPO 8-Generation Smoke Passed

- at: `2026-06-21T11:05:53Z`
- kind: `result`
- summary: Using the SFT seed-1 merged model plus a 256-row JSON bridge adapter, the GRPO micro-smoke passed the practical gate with 8 generations per prompt: valid schema, no clipping, and nonzero comparative reward signal on every step.
- evidence:
  - `Run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_micro_smoke/20260621_110345 completed 6 GRPO steps. Trainer aggregate: nonzero_reward_std_steps=6/6, mean_reward_std=1.099736, max_clipped_ratio=0.0, max_completion_length_seen=22. Reward debug: 48/48 valid JSON. Capacity: peak reserved VRAM 4.174GB, OOM risk low.`
- decisions:
  - For SFT-bridge GRPO micro/pilot bootstrapping, prefer num_generations=8, per_device_train_batch_size=8, temperature=1.35, top_p=1.0, max_completion_length=128 over either low-temp 4-generation deterministic settings or high-temp 256-token settings.
- next steps:
  - Validate touched code/docs, then commit/PR the GRPO bootstrap changes before moving to a longer SFT-bridge GRPO pilot.
### 017-launch - SFT-Bridge GRPO Full Run Launched

- at: `2026-06-21T11:17:23Z`
- kind: `launch`
- summary: Launched the full local SFT-bridge GRPO seed-1 run after a Docker dry-run validated model load and all 14,395 GRPO train rows.
- evidence:
  - `Container grpo_sft_json_bridge_seed1_full_20260621_071711 launched from config experiment/phase1/grpo/configs/grpo_sft_json_bridge_seed1_full.yaml. Dry run loaded merged SFT seed-1 + JSON bridge adapter and formatted 14,395 examples.`
- commands:
  - `docker run -d --name grpo_sft_json_bridge_seed1_full_20260621_071711 ... train_grpo.py --config experiment/phase1/grpo/configs/grpo_sft_json_bridge_seed1_full.yaml`
- next steps:
  - Monitor logs, GPU, and training_lineage/log files until completion; fix issues if the full run fails.
### 018-heartbeat - SFT-Bridge GRPO Full Run Early Health

- at: `2026-06-21T11:26:19Z`
- kind: `heartbeat`
- summary: The full SFT-bridge GRPO run has entered training and early metrics are healthy enough to continue.
- evidence:
  - `At step 150/14395, throughput ~0.352 steps/sec, reward_std ~0.879, frac_reward_zero_std ~0.12, clipped_ratio 0.0, reserved VRAM ~4.176GB, OOM risk low. Current estimate is roughly 11 hours remaining.`
- next steps:
  - Continue timed local monitoring until completion; first stronger gate after checkpoint-500 appears.
### 019-heartbeat - SFT-Bridge GRPO Full Run Checkpoint 500 Healthy

- at: `2026-06-21T11:46:40Z`
- kind: `heartbeat`
- summary: The full SFT-bridge GRPO run passed the first checkpoint gate and remains healthy enough to continue.
- evidence:
  - `At step 600/14395, checkpoint-500 exists, throughput ~0.371 steps/sec, reward_std ~0.487, frac_reward_zero_std ~0.52 on the latest 25-step window, clipped_ratio ~0.005, reserved VRAM ~4.176GB, OOM risk low.`
- next steps:
  - Continue hourly monitoring through subsequent checkpoints; watch for reward variance collapse or sustained clipping.
### 020-heartbeat - SFT-Bridge GRPO Full Run Step 1600 Watchpoint

- at: `2026-06-21T12:47:21Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 1600, but reward variance is lower and clipping higher than the micro-smoke, so continue with watchpoints rather than treating settings as final.
- evidence:
  - `Through step 1600: checkpoints 500/1000/1500 saved; last-20 reward_std mean 0.386, frac_reward_zero_std mean 0.58, clipped_ratio mean 0.072, KL mean 0.447, reserved VRAM ~4.176GB, OOM risk low. ETA ~11.7h from step 1600.`
- next steps:
  - Continue full run; intervene if reward_std collapses near zero, clipped_ratio sustains materially above ~0.15-0.20, KL spikes, or container exits.
### 021-heartbeat - SFT-Bridge GRPO Full Run Step 2500 Continuing

- at: `2026-06-21T13:48:00Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 2500 and has not hit OOM or clipping failure, though reward variance is weaker than the micro-smoke.
- evidence:
  - `At step 2500/14395: checkpoints 1500/2000/2500 present; last-20 reward_std mean 0.3635, latest reward_std 0.1282; last-20 frac_reward_zero_std mean 0.596, latest 0.8; last-20 clipped_ratio mean 0.0548, latest 0.01; KL last-20 mean 0.451; VRAM ~4.176GB reserved, OOM risk low.`
- next steps:
  - Continue monitoring; do not call this final until post-run eval shows behavioral movement.
### 022-heartbeat - SFT-Bridge GRPO Full Run Step 3375 Stable

- at: `2026-06-21T14:48:31Z`
- kind: `heartbeat`
- summary: The full SFT-bridge GRPO run remains stable through step 3375, with reward variance rebounding after the step-2500 watchpoint.
- evidence:
  - `At step 3375/14395: checkpoint-3000 exists; last-20 reward_std mean 0.373, latest 0.649; last-20 frac_reward_zero_std mean 0.616, latest 0.4; last-20 clipped_ratio mean 0.047; KL last-20 mean 0.410; VRAM ~4.176GB reserved.`
- next steps:
  - Continue hourly monitoring through the full epoch.
### 023-heartbeat - SFT-Bridge GRPO Full Run Step 4300 Stable

- at: `2026-06-21T15:48:59Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 4300 with modest clipping and nonzero rolling reward variance.
- evidence:
  - `At step 4300/14395: checkpoints 3000/3500/4000 present; last-20 reward_std mean 0.305, latest 0.277; last-20 frac_reward_zero_std mean 0.67; last-20 clipped_ratio mean 0.039; KL last-20 mean 0.301; VRAM ~4.176GB reserved.`
- next steps:
  - Continue hourly monitoring.
### 024-heartbeat - SFT-Bridge GRPO Full Run Step 5150 Stable

- at: `2026-06-21T16:49:30Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 5150; reward variance persists and checkpoint-5000 exists.
- evidence:
  - `At step 5150/14395: checkpoints 4000/4500/5000 present; last-20 reward_std mean 0.357, latest 0.499; last-20 frac_reward_zero_std mean 0.634; last-20 clipped_ratio mean 0.0675 with max20 0.165; KL last-20 mean 0.283; VRAM ~4.176GB reserved.`
- next steps:
  - Continue monitoring, with longer intervals unless clipping or variance worsens.
### 025-heartbeat - SFT-Bridge GRPO Full Run Step 6450 Stable

- at: `2026-06-21T18:20:02Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 6450, almost halfway through the epoch.
- evidence:
  - `At step 6450/14395: checkpoints 5000/5500/6000 present; last-20 reward_std mean 0.303, latest 0.207; last-20 frac_reward_zero_std mean 0.692; last-20 clipped_ratio mean 0.0778, max20 0.16; KL last-20 mean 0.222; VRAM ~4.176GB reserved.`
- next steps:
  - Continue monitoring through full completion; run post-training eval/diagnostic after final_model is saved.
### 026-heartbeat - SFT-Bridge GRPO Full Run Step 7850 Stable

- at: `2026-06-21T19:50:31Z`
- kind: `heartbeat`
- summary: The full run is past the halfway point and remains stable enough to continue.
- evidence:
  - `At step 7850/14395: checkpoints 6500/7000/7500 present; last-20 reward_std mean 0.266, latest 0.528; last-20 frac_reward_zero_std mean 0.724; last-20 clipped_ratio mean 0.068, max20 0.145; KL last-20 mean 0.190; VRAM ~4.9GB used by nvidia-smi.`
- next steps:
  - Continue monitoring to completion.
### 027-heartbeat - SFT-Bridge GRPO Full Run Step 9100 Stable

- at: `2026-06-21T21:21:01Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 9100 with persistent reward variance and modest clipping.
- evidence:
  - `At step 9100/14395: checkpoints 8000/8500/9000 present; last-20 reward_std mean 0.331, latest 0.415; last-20 frac_reward_zero_std mean 0.654; last-20 clipped_ratio mean 0.0825, max20 0.14; KL last-20 mean 0.205; ETA about 5.8h.`
- next steps:
  - Continue to completion and then inspect final artifacts/evaluate.
### 028-heartbeat - SFT-Bridge GRPO Full Run Step 10425 Stable

- at: `2026-06-21T22:51:38Z`
- kind: `heartbeat`
- summary: The full run remains stable past 10k steps and is roughly 72% through the epoch.
- evidence:
  - `At step 10425/14395: checkpoints 9000/9500/10000 present; last-20 reward_std mean 0.346, latest 0.412; last-20 frac_reward_zero_std mean 0.67; last-20 clipped_ratio mean 0.0648; KL last-20 mean 0.253; ETA about 4.4h.`
- next steps:
  - Continue monitoring to completion.
### 029-heartbeat - SFT-Bridge GRPO Full Run Step 11775 Stable

- at: `2026-06-22T00:22:11Z`
- kind: `heartbeat`
- summary: The full run remains stable through step 11775 and is in the final third of the epoch.
- evidence:
  - `At step 11775/14395: checkpoints 10500/11000/11500 present; last-20 reward_std mean 0.326, latest 0.349; last-20 frac_reward_zero_std mean 0.656; last-20 clipped_ratio mean 0.0845; KL last-20 mean 0.220; ETA about 2.9h.`
- next steps:
  - Continue monitoring; after completion verify final_model, lineage, capacity, and run aggregate metrics.
### 030-heartbeat - SFT-Bridge GRPO Full Run Step 13150 Stable

- at: `2026-06-22T01:52:40Z`
- kind: `heartbeat`
- summary: The full run is in the final stretch and remains stable through step 13150.
- evidence:
  - `At step 13150/14395: checkpoints 12000/12500/13000 present; last-20 reward_std mean 0.271, latest 0.391; last-20 frac_reward_zero_std mean 0.726; last-20 clipped_ratio mean 0.068; KL last-20 mean 0.207; ETA about 1.4h.`
- next steps:
  - Run a shorter final monitor interval, then verify final artifacts and aggregate metrics after container exit.
### 031-result - SFT-Bridge GRPO Full Run Completed

- at: `2026-06-22T03:36:58Z`
- kind: `result`
- summary: The full local SFT-bridge GRPO seed-1 run completed successfully and produced a final adapter. A same-slice pre/post dev diagnostic shows behavioral movement in the intended direction, with a small schema-format regression.
- evidence:
  - `Training run scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743 exited 0 with final_model, training_lineage.json, capacity_features.json, checkpoint-14395, final_step=14395, train_runtime=57126.097s, peak reserved VRAM 4.191GB, OOM risk low. Train aggregate over 575 logged windows: reward_std mean 0.338, frac_reward_zero_std mean 0.652, clipped_ratio mean 0.061, KL mean 0.286. Eval-like 64-row dev comparison at temp=0.7/top_p=0.95/max_completion=96: pre-bridge known valid 1.000/refusal 0.344/mean_reward 0.153/correct_known 17/32; post-GRPO known valid 0.969/refusal 0.281/mean_reward 0.339/correct_known 19/32. Pre-bridge unknown valid 1.000/refusal 0.812/mean_reward 0.078; post-GRPO unknown valid 1.000/refusal 0.844/mean_reward 0.148.`
- decisions:
  - Treat SFT-bridge GRPO as operational and promising on this bounded dev diagnostic, but not finalized: full evaluation should quantify schema failures and behavior over the full eval suite before interpreting as headline evidence.
- next steps:
  - Commit/PR full-run config and diagnostics; then run the standard eval pipeline for the completed GRPO adapter.
