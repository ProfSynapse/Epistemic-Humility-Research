# Prompt-vs-training disentanglement panel: base counterfactuals and instruction-free abstention notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-14 ~11:55Z — two aborted launch attempts, config repin, relaunch

Attempt 1 (`eh-pvtpanel-prc-20260814T114712Z`): launched without
`--entrypoint python3`; the unsloth image's default entrypoint started its
studio service instead of the eval. Killed at ~30s (exit 137), removed. No
eval code ran.

Attempt 2 (`eh-pvtpanel-prc-20260814T114741Z`): failed run_eval.py's own
validation before engine init (exit 1): each arm's `model` label must equal
the config's `model_tag` (run_eval.py:263-272); the panel configs carried
sibling-config labels. Zero run artifacts (no results dir created,
verified). Both aborts are honest false starts logged here, not silent
restarts.

Repair: arm `model` labels set to each config's own model_tag in all four
configs; status briefly reverted running->signed (no artifact existed) for
`bin/exp repin` (4 files, audit reason recorded in instrument.repins), then
relaunched. No design change: prompts, arms, adapters, generation, and
thresholds untouched.

### 2026-08-14 ~11:50Z — SIGNED; PI launch approval; config-1 launch (P-rc)

Cell signed (6 pins, engine vllm 0.16.1.dev0+g89a77b108.d20260417 read from
the cold-GRPO eval container's own startup log). PI approved the ~4-5
GPU-hour local eval-only launch in this conversation ("Approved",
2026-08-14). GPU verified idle (0 MiB used) before launch.

Launching run-order 1 now: container `eh-pvtpanel-prc-<ts>`, image
unsloth/unsloth:latest, entrypoint python3
`archive/experiment/phase1/eval/run_eval.py --config
experiments/prompt-vs-training-panel/configs/eval_panel_prc_local_4b.yaml
--live-vllm`, repo bind-mounted at /workspace/repo, --gpus all — the same
invocation shape as the cold-GRPO eval container (lead-inspected). Arms:
base_prc, cold_dpo_seed1_prc, cold_kto_seed1_prc. Results land in
archive/experiment/phase1/eval/results_prompt_vs_training_panel_prc_4b/.
Completion watcher: detached docker-wait sentinel in scratch/launch-watch/
plus the session's standing Monitor (armed earlier this session), per the
new launch-turn watcher rule. Configs 2-4 launch sequentially on each
completion wake. This entry precedes the launch verb.

Cell scaffolded (`bin/exp new`), AMENDMENT/gates/cell/configs authored from the
PI-approved plan (`papers/paper-2-training-regimen/notes/prompt-vs-training-disentanglement-plan.md`).
PI approved the lead recommendations verbatim: P-struct wording as drafted,
R1-R4 as interpretation bands (not gates), 11-arm scope, cold-GRPO seeds-2/3
replication deferred until this panel lands.

Checkpoint cell-of-record provenance (lead-verified on disk, all six exist;
paths recorded in the configs beside each arm):

- cold SFT seed 1: `sft__4b__headline__seed1/20260614_053221/final_model` —
  `archive/experiment/phase1/run_records/sft__4b__headline__seed1.json`
  (adapter_path); NOT in postfix-rerun scope (dev-split fix predates its
  launch; postfix cell AMENDMENT scope is DPO/KTO only).
- cold DPO seed 1: `dpo__4b__headline__seed1_postfix/20260807_192026/final_model`
  — postfix cell of record, r2 recipe-honoring retrain
  (`experiments/headline-seed1-postfix-rerun/NOTEBOOK.md` ~162-167,
  AMENDMENT ~330).
- cold KTO seed 1: `kto__4b__headline__seed1_postfix/20260807_124416/final_model`
  — postfix cell, compliant relaunch ruled the record (NOTEBOOK ~128, ~143).
- cold GRPO seed 1: `cold_base_grpo_v2_seed1_full/20260813_182012/final_model`
  — `experiments/grpo-cold-start-induction` training run (audit-verified
  lineage: base_model bnb-4bit, no SFT branch).
- merged clean-SFT seed 1 (warmed base):
  `sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`
  — the amendment-E corrected-base eval pairing
  (`archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`).
- warmed GRPO v2 seed 1 adapter:
  `schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` — same
  cell-of-record config.

Scout-report corrections (path scout's report was evidence, two errors fixed
at lead verification): its "clean_sft merged" path pointed inside the seed-3
GRPO run dir (wrong; correct identity read from the amendment-E seed-1
corrected-base config above), and its item-4 label misnamed the cold-GRPO run
dir prefix (path itself correct).

Instrument note: P-struct is split into cold/warmed configs because
`run_eval.py` loads one `model_name` per config; prompt text byte-identical
across the two (AMENDMENT Design updated accordingly; four pinned configs, not
three). P-plain mirrors the plain-contract cell-of-record generation block
(max_new_tokens 64, no structured outputs) so its base row is comparable with
the cold-start headline rows; P-rc and P-struct mirror the RC-contract
cell-of-record block (128 tokens, structured outputs on).

Next: `bin/exp sign`, then PI launch approval (~4-5 GPU-hours local 3090,
eval-only). Launch will be recorded here BEFORE the launch verb, per standing
directive, with the auto-watcher + Monitor armed in the launch turn.
