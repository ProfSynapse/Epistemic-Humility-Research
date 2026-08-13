# Dial vs token-logprob on the deployed checkpoint: gated confirmation at adequate power notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-08-13 RUN COMPLETE (harness-builder execution), all four stages, rc=0
  end-to-end. Env pins used throughout: VLLM_WSL2_ENABLE_PIN_MEMORY=1,
  VLLM_BATCH_INVARIANT=1, HF_HUB_OFFLINE=1, CUDA_HOME=/usr/local/cuda,
  /usr/local/cuda/bin prepended to PATH -- no host repair was needed this run
  (these pins, given up front, preempted v3's nvcc EPERM issue before it
  could occur).
  1. CPU smoke suite (`test_lp_t_smoke.py`): 7/7 passed, re-run before launch.
  2. `--dry-run`: exit 0, all real inputs resolved (matches build-task record).
  3. Pre-launch real-generation smoke: scratchpad script (not a registered
     instrument file, not committed) reusing the harness's own
     `build_vllm_engine`/`build_sampling_params`/`build_lora_request`/
     `render_probe_prompt` on 4 dummy non-evidence prompts, mirroring v3's
     documented pre-launch smoke methodology verbatim. PASS: all 4 rows
     returned token IDs with per-token logprobs aligned at every generated
     step; engine + LoRA adapter loaded cleanly. Wall clock ~11:57:34-11:59:29.
  4. Generation (`--phase generate`, separate process): capped pool 12,000
     attempts, all captured. Wall clock 12:00:04-12:04:20 (~4m16s).
  5. `select_attempted` post-hoc replay (target_correct=500, target_wrong=500,
     max_attempts=12000): stopped at 8,621 attempted items in pool order
     (target reached before the cap) -- 1,501 of those labeled
     correct/wrong (answered rate ~17.4%, consistent with v3's ~17.75%
     observed rate on the same checkpoint/pool convention).
  6. Extraction (`--phase extract`, separate process, teacher-forced HF+PEFT
     over the phase-1 capture's own token IDs, dial layer L22): rc=0, 8,621
     extraction records (one per attempted row; 1,501 with
     `extracted: true` + a safetensors shard, the rest `extracted: false` by
     design for non-answered rows). Extraction runlog finalized 14:02:10 (a
     long real-world gap separates this from generation's 12:04 finish --
     that gap is agent turn-taking overhead across this session, not GPU or
     model compute time; the GPU-side extraction work itself, from
     `tensors/rows.jsonl` being (re)written to the runlog finalizing, took
     ~1m33s for 1,501 forward passes).
  7. Scoring (`--phase score`, CPU-only): rc=0, result written to
     `analysis-committed/lp_t_t_deployed_confirmatory_result.json`.
     LT-G0 (a) capture integrity 0 failures across all extracted rows, (b)
     coverage OK (8,621 attempted == 8,621 distinct recorded dispositions),
     (c) power floor 1,501 >= 1,000, (d) fresh T dial OOF AUROC 0.7962 >=
     0.75 sanity bound -- all four hold. LT-G1: dial AUROC minus
     mean_answer_span-logprob AUROC margin +0.1393, paired bootstrap 95% CI
     [0.1031, 0.1755] (n_boot 2000, seed 20260813). Floor +0.05 met and CI
     excludes 0 on the positive side -- `LT_G1_pass: true`,
     `falsifier_fired: false`, `ambiguous_band: false`. Descriptive-only
     secondary variants: sum_answer_span AUROC 0.7706, min_answer_span AUROC
     0.7536 (both n=1501, not gated).
  Containment: `analysis-committed/lp_t_t_deployed_confirmatory_result.json`
  key-scanned (grep for text/question/prompt/answer_text/generation/aliases/
  token_ids/row_key, plus a full recursive key listing) -- zero matches,
  only `arm`, `lt_g0.*`, `variant_aurocs.*`,
  `dial_minus_primary_logprob_margin`, `margin_bootstrap_ci.*`,
  `gate_verdict.*` keys present (counts/AUROCs/CIs/booleans only). No pinned
  file (cell.yaml/gates.yaml/lp_t_harness.py) was touched; no git operation
  performed.

- 2026-08-13 SIGNED and LAUNCH AUTHORIZED (lead, PI approval on record: "ok
  proceed with our experiments"). `bin/exp sign` pinned cell.yaml, gates.yaml,
  lp_t_harness.py (shas in `experiment.yaml`). Launch plan, recorded before
  launch: background harness-builder agent runs, in order, (1) the registered
  real-generation vLLM smoke on the deployed checkpoint (small prompt batch,
  capture-integrity check end to end), (2) full generation at the registered
  12,000-attempt cap, (3) teacher-forced HF extraction over captured token IDs,
  (4) scoring + LT-G0/LT-G1 gate evaluation. Env pins per v3 precedent:
  vllm venv, VLLM_WSL2_ENABLE_PIN_MEMORY=1, VLLM_BATCH_INVARIANT=1,
  HF_HUB_OFFLINE=1, CUDA_HOME=/usr/local/cuda with /usr/local/cuda/bin on
  PATH. Signed files are immutable during the run; any instrument defect is a
  stop-and-report, not an in-place fix. GPU order: this cell first (short),
  cold-GRPO training queued behind it.


- 2026-08-13 harness-builder build task: instrument built to signable state,
  no GPU work run.
  - `lp_t_harness.py` copied verbatim from
    `experiments/dial-logprob-baseline-v3/lp_v3_harness.py` and parameterized
    to this cell's single arm (`t_deployed_confirmatory`): `ARM_SYSTEM_PROMPTS`
    reduced to the T system prompt only; `score_arm_v3` renamed `score_arm_t`
    with LP3-G0/LP3-G1 result keys renamed LT-G0/LT-G1 (`lt_g0`,
    `stopped_at_lt_g0`, `LT_G1_pass`) to match this cell's own gates.yaml gate
    ids; instrument-sanity check (LT-G0d) now unconditional on the single
    gated arm rather than v3's "S arm only" scoping. No v3 file modified
    (diffed against `git diff --stat` after the copy: only this cell's own
    files changed).
  - `cell.yaml` / `gates.yaml` filled by transcription from AMENDMENT.md
    "Design"/"Gates", byte-consistent with the amendment prose. Checkpoint
    identity (merged-16bit + LoRA adapter paths), dial layer 22, engine block
    (vllm 0.27.1, venv, env vars, batch-invariance, scheduler), prompt
    inventory module/datasets/pool_seed/targets all copied verbatim from
    v3's `t_deployed_descriptive` arm; only `max_attempts` changed
    (4000 -> 12000) and `gate` changed (`descriptive-only` -> `LT-G1`).
  - `test_lp_t_smoke.py` adapted from v3's smoke (fixture arm id/gate
    renamed, `score_arm_v3` -> `score_arm_t`, `lp3_g0` -> `lt_g0` result-key
    renames, dry-run missing-adapter test index fixed from `arms[1]` to
    `arms[0]` since this cell has one arm not two). Ran green:
    `python3 -m pytest experiments/dial-logprob-t-deployed-confirmatory/test_lp_t_smoke.py -v`
    -> 7 passed (base conda env: torch 2.9.0+cu128, transformers/sklearn/yaml
    present; the pinned vllm venv lacks pytest, so the smoke -- CPU-only,
    no vllm import on this path -- ran there instead). Covers: generation +
    resume, `select_attempted` stopping-rule replay, extraction + resume +
    full score pass, each LT-G0 criterion firing on synthetic failures
    (a capture-integrity corruption, c power-floor-n=1000 on a 12-row
    fixture, d unreachable AUROC floor), and dry-run present/missing-input
    detection.
  - `python3 experiments/dial-logprob-t-deployed-confirmatory/lp_t_harness.py --dry-run`
    exit 0, "all real inputs resolved": both the merged-16bit checkpoint and
    the GRPO LoRA adapter directories exist on disk at the paths copied from
    v3's cell.yaml; `datasets/popqa/test.jsonl` and
    `datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl` both present;
    `pool_size_uncapped: 25580` (matches AMENDMENT.md's stated uncapped pool)
    and `pool_size_capped: 12000` (matches the registered cap). No GPU/model
    work was performed -- this only resolves file paths.
  - `experiment.yaml` filled: `instrument.configs: [cell.yaml, gates.yaml]`,
    `instrument.modules: [lp_t_harness.py]`, `instrument.engine: {name: vllm,
    version: 0.27.1}` (generation-engine gate satisfied for `bin/exp sign`),
    `instrument.persistence.lp_t_harness.py` declared incremental with
    checkpoint_path under `analysis/`, mirroring v3's declaration shape.
    `pins: {}` left empty -- this build task does NOT sign; `bin/exp sign` is
    the lead/PI's call.
  - Not done by this build task (flagging for the lead): no real vLLM
    generation smoke was run over actual S/T prompts on this checkpoint
    (registered pre-launch step per
    `.skills/experiment-runner/reference/batched-generation.md`); the
    scheduler block (`max_model_len`/`max_num_seqs`/`max_num_batched_tokens`)
    is carried from v3 unvalidated for real generation, same caveat v3 itself
    carried.

## 2026-08-13 -- resolved

- PI approval received ("yes resolve it") after lead verification of the
  committed result JSON (margin re-derived 0.7962 - 0.6569 = 0.1393; CI and
  gate booleans read directly from
  `analysis-committed/lp_t_t_deployed_confirmatory_result.json`).
- Outcome written into AMENDMENT.md; `bin/exp resolve` run with status
  `resolved`. Registry regenerated via `bin/exp regen`.
- Downstream edit in the same PR: paper 4 limitation 9 upgraded from the
  ungated descriptive +0.158 caveat to this cell's gated +0.1393
  (95% CI [0.1031, 0.1755], n=1,501).
- KG ingest of the resolution (typed claim/evidence nodes + manifest `kg:`
  ids) deferred to a follow-up ingest pass, per the resolve checklist.
