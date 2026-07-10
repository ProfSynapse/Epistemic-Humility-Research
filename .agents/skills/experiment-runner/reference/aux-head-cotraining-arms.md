# Preparing aux_head co-training arms

Plug-and-play runbook for staging an `aux_head` scalar-readout co-training
experiment (the Amendment R shape: does jointly co-training a readout
head on an unfrozen base change *native* model behavior?). Follow this instead of
re-deriving the data/recipe/engine integration each time.

The canonical worked instance is **Amendment R** (answerability readout at L35);
the steps below generalize to any per-row scalar target.

## Summary — the four steps

1. **Build the aux dataset** (real + shuffled-placebo target columns) → gitignored scratch.
2. **Draft three recipes** from the templates: A0 (head off), A1 (joint, real), A2 (joint, placebo).
3. **Clear the two launch prerequisites** (engine `prompt_render` mode + runner aux_head forwarding).
4. **Re-smoke** joint-loss + faithful token, **lock the falsifier threshold**, get sign-off, launch.

## 1. Build the aux dataset (CLI)

```bash
python3 archive/experiment/phase1/probe/amendments/amendment_r_build_phase_b_aux_dataset.py \
  --src archive/experiment/phase1/data/qwen3-4b-instruct/sft_train.jsonl \
  --out-dir scratch/amendment_r/phase_b \
  --shuffle-seed 20260629
```

Emits two JSONL files (rows = `{"conversations": [...], "aux_target": 0.0|1.0}`):
`phase_b_aux_train.jsonl` (real) and `phase_b_aux_train_shuffled.jsonl` (placebo).

Key properties (all enforced/printed by the builder):
- **Target derivation is reliable, not heuristic.** The answerability label is
  derived from the assistant completion using the canonical `REFUSAL_PATTERNS`
  (copied from `build_schema_response_confidence_datasets.py`); the builder asserts
  every phrasing in `abstention_bank.json` is detected before writing. Target = 0.0
  if the completion is a refusal/abstention (unknown), else 1.0 (known/answered).
- **Placebo integrity.** The shuffle is a deterministic seeded Fisher–Yates
  permutation (no `Math.random`/`Date`): it preserves the marginal exactly and
  breaks the question↔target correspondence. The coincidental-match fraction
  ≈ `p² + (1-p)²` for answerable-fraction `p` (≈0.51 at p=0.554) — that residual is
  expected, not a bug.
- **Outputs are gitignored.** The source SFT data is restricted/untracked, so
  derived copies go to `scratch/` and are NEVER committed. Only the builder,
  recipes, and run records are committed.

LM-training data is held **constant** across all three arms (same `conversations`);
only the aux supervision varies (off / real / shuffled). That is what makes A1 vs A2
attributable to the *information in the target* and A1 vs A0 attributable to the
*head*.

## 2. Recipe templates

Three checked-in recipes under `archive/experiment/phase1/recipes/`:

| Arm | Recipe | aux_head | dataset |
|-----|--------|----------|---------|
| A0 (reference) | `eh_phase1_qwen3_4b_amendment_r_a0_lm_only.yaml` | OMITTED (off) | real file (column ignored) |
| A1 (treatment) | `eh_phase1_qwen3_4b_amendment_r_a1_joint_real.yaml` | enabled | real file |
| A2 (placebo) | `eh_phase1_qwen3_4b_amendment_r_a2_joint_placebo.yaml` | enabled | shuffled file |

The `aux_head:` block mirrors `synaptic-tuner/Trainers/sft/configs/aux_head_phase_b_example.yaml`:
`enabled / layer / token_position / target_field / loss / head_type / out_activation /
input_norm / freeze_base / lm_loss_weight / head_lr`, plus `prompt_render:
prompt_completion` (see prerequisite (1)). Hold LM hyperparameters identical to the
headline SFT seed so A0 doubles as a comparability check and A1/A2 isolate the head.

A0 has **no engine/runner dependency** — it runs on the current tuner lane today.
A1/A2 are launch-blocked until both prerequisites below land.

## 3. The two launch prerequisites (engine + runner)

`aux_head` is configured **only via the trainer config file** (`train_sft.py` reads
`config.aux_head` via `load_config()`; there is **no argparse** for it). And the
tuner's `local_run_handler._build_trainer_command` forwards recipe keys to the
trainer as `--flags` but does **not** forward any `aux_head` block. So a recipe's
`aux_head:` is **inert on the standard lane** until:

1. **ENGINE - `prompt_render: prompt_completion` mode** (token-faithfulness handoff).
   The default full-conversation render diverges from `add_generation_prompt=True`
   at the `</think>` newlines, so `end_of_prompt` lands one token short of the
   validated gen-prompt axis (cos 0.54 / AUROC 0.85 vs the 0.96 axis). The verified
   fix tokenizes rows prompt/completion-style (`prompt =
   render(sys+user, add_generation_prompt=True)`, `++ completion ++ <|im_end|>`,
   `labels = [-100]*len(prompt) ++ completion`) so the existing `end_of_prompt`
   helper lands on the faithful token (400/400 rows, cos 0.9998). No head-code
   change — it is a preprocessing render mode, default unchanged.
2. **RUNNER — aux_head forwarding.** Add `aux_head` argparse to `train_sft.py` and
   forward the recipe block (incl. `prompt_render`) in
   `tuner/handlers/local_run_handler.py::_build_trainer_command` (alongside the
   existing `--chat-template-kwargs` / lora-scalar forwarding). This is generic
   engine work and belongs in the **submodule's own** `fine-tuning` skill +
   the builder PR — NOT installed from the root project (ownership boundary).

Both are tracked in the Amendment R aux-head co-training record and the run records'
`prereq_check`/`blocked_on`.

## 4. Smoke, lock the falsifier, launch

- **Faithfulness already smoke-verified** (lab-notebook): scripts
  `amendment_r_phase_b_{smoke,offset_diag,promptcompletion_proto}.py` confirmed the
  gen-prompt token reproduces the cached axis and the prompt/completion render fixes
  `end_of_prompt`. Don't burn the falsifier on a plumbing bug (faithfulness clause).
- After the two prerequisites land: **re-smoke** the joint loss + the A0 baseline,
  then **lock** the falsifier threshold (candidate `A1 emitted AUROC-to-
  appropriateness > A2 by +0.05`) in the Amendment doc **before** the scored run.
- Primary metric is the existing non-circular scorer: `calibration_gap_report.py`
  Analysis A (`auroc_emitted_to_appropriateness`); A0-analog baseline 0.561.
- These are **exploratory Amendment cells**, never pooled with the locked headline
  matrix. Promote a win only via a registered confirmatory replication.

## 5. Eval, score, and evaluate the falsifier (after each arm trains)

The primary metric is the model's **emitted** stated-confidence, NOT the aux_head
sidecar — so eval is a standard SelfAware response-confidence generation on the
arm's LoRA, and the sidecar is irrelevant to scoring. Per arm, after `train_end`:

1. **Merge the adapter to 16-bit** (the SFT trainer saves only `final_model/`; the
   downstream eval base must be a standalone 16-bit model — same primitive the
   clean-SFT/GRPO bases use). Runs inside the unsloth container (GPU, ~1-2 min):
   ```
   python3 archive/experiment/phase1/grpo/merge_sft_adapter_16bit.py \
     <run>/final_model  <run>/Qwen3-4B-bnb-4bit/merged-16bit
   ```
   The R arms train directly on `unsloth/Qwen3-4B-bnb-4bit` with no prior
   merged-SFT substrate, so the merge of the arm's OWN adapter IS the eval base and
   the eval arm's `adapter:` is EMPTY (base only) — like Amendment A's `sft_merged`
   arm. Do NOT stack the adapter on a different merged base (double-counts SFT).
2. **Generate scored rows** with the response-confidence SelfAware eval (mirror the
   B0/Amendment-J config exactly; only the merged base differs per arm). Instantiate
   `eval/config/eval_amendment_r_response_confidence_selfaware_full_local_4b.template.yaml`:
   ```
   python archive/experiment/phase1/eval/run_eval.py --config <arm-config>.yaml --live-vllm
   ```
   `scored_rows.jsonl` must carry `stated_confidence`, `refused`, `correct`, `label`,
   `id` for Analysis A.
3. **Score** the non-circular metric:
   ```
   python archive/experiment/phase1/eval/analysis/calibration_gap_report.py \
     --scored <results_dir>/<arm>__selfaware/scored_rows.jsonl \
     --out archive/experiment/phase1/eval/analysis/calibration_gap_amendment_r_<arm>.json
   ```
   The headline number is `A_full_eval.auroc_emitted_to_appropriateness`.
4. **Evaluate the locked falsifier** once all three arms are scored:
   ```
   python archive/experiment/phase1/eval/analysis/amendment_r_falsifier_check.py \
     --a0 <...a0.json> --a1 <...a1.json> --a2 <...a2.json>
   ```
   PRIMARY gate = A1 − A2 ≥ +0.05 (placebo contrast); §4 also requires A1 > A0.
   The margin is pre-stated/locked — never edit it to fit a result.

## Provenance / governance checklist

- [ ] Builder run; real + shuffled files in gitignored scratch; marginal + placebo
      integrity printed.
- [ ] Three recipes committed; LM hyperparameters identical across arms.
- [ ] Run records committed with data SHAs, repo+submodule commits, and
      `prereq_check`/`blocked_on` reflecting reality.
- [ ] Amendment doc states prediction + falsifier + gates BEFORE the run; threshold
      locked only after the re-smoke; goalposts never moved after the result.
