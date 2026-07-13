# Amendment AI cloud verdict cells (CELL A / CELL B), CELL C assessment

Prep doc for the HF Jobs cloud half of the Amendment AI verdict eval. Produces
exactly the inputs the CPU scorer
`archive/experiment/phase1/probe/amendments/amendment_ai_verdict_score.py` consumes for gates
AI-G0 / AI-G1 / AI-G2, per the locked spec section 4 of
`experiments/probe-as-reward/AMENDMENT.md`. CPU-only authoring; no
model was run, no GPU touched, no HF Job submitted, no git command run.

## What the scorer needs (input contract, restated)

Per arm (true, permuted), the scorer takes:

- `--*-fit-states`: an extraction dir (`rows.jsonl` + `{safe_key}__pre.safetensors`
  with tensors L20/L24/L28) of the UNION refit surface re-extracted through the
  arm's FINAL checkpoint in the 4-bit serving config. The scorer refits a fresh
  L24 probe here (Amendment T), excluding the 400 holdout row_keys, and reports
  its 5-fold OOF AUROC as the AI-G0 falsifier. rows.jsonl must carry
  `row_key`, `safe_key`, `label` ("known"/"unknown").
- `--*-holdout-states`: same-format extraction dir for the 400 holdout rows.
  The scorer scores the fresh probe on these to get p_unans per row. rows.jsonl
  must carry `row_key`, `safe_key`.
- `--*-gen`: generation `rows.jsonl` for the 400 holdout rows, fields
  `row_key`, `refused` (bool), `answered` (bool), `schema_valid` (bool).
- `--g2-true` / `--g2-ref`: behavior-panel trio JSONs (CELL C output; the ref
  is already pinned in `experiments/probe-as-reward/artifacts/amendment_ai_g2_reference_grpo_v2.json`).

The scorer reads gold_label / origin / p_unanswerable for each holdout row from
the LOCAL canonical `holdout_eval.jsonl`, NOT from the uploaded dirs, so the
uploaded rows.jsonl deliberately omits question text (NO-LICENSE safe).

## Cell inventory (new / edited files, all uncommitted)

New:
- `archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py` - the GPU entry
  script. `--stage extract --surface {union,holdout}` (CELL A) and
  `--stage generate` (CELL B). Load path is byte-matched to the sensor-v2
  lineage (`experiments/probe-as-reward/scripts/par_sensor_refit_extract_4bit.py`:
  unsloth FastLanguageModel
  load_in_4bit=True, baseline unprimed system prompt,
  render_probe_prompt(enable_thinking=False), anchor prompt_len-1, forward-only
  extraction), and the generation path is byte-matched to the AH harness
  (`amendment_ah_main_generate.py`: greedy do_sample=False num_beams=1
  max_new_tokens=96, refusal via scorers.is_stated_confidence_refusal,
  content-end via _content_end_index). The one deliberate difference from the
  sensor extraction: the arm's TRAINED LoRA adapter is applied
  (PeftModel.from_pretrained with pinned revision), not the identity-at-init
  wrapper, because the verdict measures the trained policy.
- `experiments/probe-as-reward/cloud/hf_jobs_ai_verdict.sh` - in-job wrapper modeled
  on `hf_jobs_cell.sh` (boot-id log capture + periodic log push preserved).
  Fetches the input pool from the private staging repo, runs the stage, uploads
  the WHOLE data dir (tensors are the deliverable here, unlike the X lane).
- `experiments/common/cloud/upload_folder.py` - folder upload helper
  (HfApi.upload_folder to a private dataset repo); the X lane's
  `upload_result.py` only does single files.

Edited (smallest backward-compatible change):
- `experiments/common/cloud/launch_hf_job.py` - added an `--ai-verdict`
  mode (new arg group: --stage/--surface/--arm-tag/--base-model/--adapter-repo/
  --adapter-revision/--staging-repo/--pool-in-repo), a dedicated
  `build_ai_verdict_command`, the pinned stable Unsloth image + a minimal
  CPU-side pip spec, and per-lane required-arg validation. The X/readout lane
  path is unchanged when `--ai-verdict` is absent (its args are now validated in
  code instead of by argparse `required=True`, so the missing-arg error is a
  clean FATAL rather than an argparse usage dump).

## Input pools the lead must stage (prerequisite, not built here)

The union surface (18,496 rows) is derived from NO-LICENSE FalseQA source text
that never enters the public repo, so the cells cannot rebuild it on-box from
the public clone. The lead uploads two input pools to the PRIVATE staging repo
before launch (both already exist locally as byproducts of the pool build):

- `inputs/union_pool.jsonl` - one line per union row:
  `{row_key, question, label, source}`. Source = the local
  `analysis/par_sensor_refit/union_pregen_4bit/rows.jsonl` (already carries
  row_key/label/question/source).
- `inputs/holdout_pool.jsonl` - the 400-row holdout: the pool build's
  `analysis/amendment_ai/pool/holdout_eval.jsonl` verbatim
  (`{row_key, question, gold_label, source, ...}`; the entry script maps
  gold_label -> label).

Both contain FalseQA question text, so they live ONLY in the private staging
repo (HF_TOKEN-gated, use-only) and never in git or any publication.

## Dry-run launcher command lines (verified: print spec, do not submit)

Placeholders: `<COMMIT>` = the pinned public-remote sha (lead sets at launch);
`<TRUE_REV>` = 7e31d3cf62395275d4ba3d1d9ec8f95287188805 (locked TRUE adapter);
`<PERM_REPO>`/`<PERM_REV>` = the permuted-arm adapter + revision (lead fills).
Base = `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`.
TRUE adapter = `professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora`.
Staging repo default = `professorsynapse/eh-ai-verdict-staging` (private).

CELL A (extract) - TRUE, union fit surface:

    python3 experiments/common/cloud/launch_hf_job.py --ai-verdict \
        --stage extract --surface union --arm-tag true \
        --base-model professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit \
        --adapter-repo professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora \
        --adapter-revision 7e31d3cf62395275d4ba3d1d9ec8f95287188805 \
        --pool-in-repo inputs/union_pool.jsonl \
        --commit <COMMIT> --timeout 2h --log-push-interval 300 --dry-run

CELL A (extract) - TRUE, 400-row holdout:

    python3 experiments/common/cloud/launch_hf_job.py --ai-verdict \
        --stage extract --surface holdout --arm-tag true \
        --base-model professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit \
        --adapter-repo professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora \
        --adapter-revision 7e31d3cf62395275d4ba3d1d9ec8f95287188805 \
        --pool-in-repo inputs/holdout_pool.jsonl \
        --commit <COMMIT> --timeout 30m --dry-run

CELL B (generate) - TRUE, 400-row holdout (greedy batch-1):

    python3 experiments/common/cloud/launch_hf_job.py --ai-verdict \
        --stage generate --arm-tag true \
        --base-model professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit \
        --adapter-repo professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora \
        --adapter-revision 7e31d3cf62395275d4ba3d1d9ec8f95287188805 \
        --pool-in-repo inputs/holdout_pool.jsonl \
        --commit <COMMIT> --timeout 90m --dry-run

The PERMUTED arm is the same three commands with `--arm-tag permuted`,
`--adapter-repo <PERM_REPO>`, `--adapter-revision <PERM_REV>`. Six cells total
(3 stages x 2 arms). Drop `--dry-run` to submit (cost-incurring; needs explicit
user approval per the lane rule, and HF_TOKEN in the launch env).

The staging upload lands under `ai-verdict-<arm>-<stage>-<surface>/data/` in the
staging repo; that dir path is what the lead passes to the scorer's
`--true-fit-states` / `--true-holdout-states` / `--true-gen` (and permuted).

## Runtime + cost estimates (a10g-small, per cell)

Measured local references: the union 4-bit pre-gen extraction ran at 9.9 rows/s
(18,496 rows in 1,868s = 31 min, base-only). The AH greedy batch-1 generation
(max_new_tokens=96) ran at 0.56-0.62 rows/s.

- CELL A union (18,496 rows, +trained adapter): ~35-45 min of forward passes.
  The applied LoRA adds a little over base-only; still well inside the 2h lane
  rule. Set --timeout 2h for headroom. The extractor has tensor-level
  checkpoint/resume (skips safe_keys whose tensor already exists, config-sha
  guarded), so a preemption restart is cheap. Per arm.
- CELL A holdout (400 rows): ~1-2 min. --timeout 30m is generous.
- CELL B generate (400 rows greedy batch-1 max96): ~12 min at the AH rate.
  --timeout 90m covers slow-decode tails; row-level resume present.
- Cost: a10g-small is the standard lane flavor; each cell is well under an hour
  of GPU wall (union the longest at ~<=45 min). Six cells ~ 2-2.5 GPU-hours
  total across both arms. No cell approaches the 2h atomic ceiling, so no split
  is needed; the union cell carries resume anyway as belt-and-suspenders.

## Upload contract

- CELLs A/B upload the WHOLE `data/` dir (hidden-state tensors + rows.jsonl +
  manifest.json) to the PRIVATE staging repo. This is the deliberate exception
  to the X-lane "tensors stay ephemeral" convention: the scorer refits a fresh
  probe on these tensors, so they ARE the deliverable.
- Destination: `<staging-repo>/ai-verdict-<arm>-<stage>-<surface>/data/`.
- The staging repo is created PRIVATE (upload_folder.py --private default)
  because union rows derive from NO-LICENSE FalseQA. Defense in depth: the
  uploaded extraction rows.jsonl carries NO question text (only
  row_key/safe_key/label/prompt_len/config_sha); generation rows.jsonl carries
  the model's own answer_text (its emission, not source text) plus the boolean
  flags. If even model emissions on FalseQA rows are a concern, the lead can
  post-filter answer_text for falseqa-origin holdout rows before any downstream
  publication; nothing the scorer needs is lost (it reads only the booleans).
- Logs push under `<run-tag>/logs/job_log_<boot>.txt`; two files under one run
  tag = a preemption/restart (the boot-id oracle from the cloud lane).

## CELL C verdict (SelfAware behavior panel, AI-G2): KEEP LOCAL

Recommendation: run CELL C on the LOCAL dgpu lane, not cloud. Do not force it
cloud-side.

Why:
- The pinned reference `experiments/probe-as-reward/artifacts/amendment_ai_g2_reference_grpo_v2.json` was produced by
  the Amendment E FULL SelfAware eval (n=3,369) via
  `archive/experiment/phase1/eval/run_eval.py` with config
  `eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`.
- That pipeline serves through vLLM (run_eval.py imports `vllm.LLM`,
  `LoRARequest`, `StructuredOutputsParams`) with structured-outputs stated-
  confidence decoding (response_confidence field, JSON retries), max_new_tokens
  128, a 200-resample bootstrap, and a specific gold_path
  (triviaqa-rc-nocontext cheng_test_gold) + SelfAware.json surface.
- AI-G2 parity is REQUIRED: the spec says the TRUE-arm panel must be "the same
  pipeline + config on the same surface, checkpoint swapped." The prereg is
  explicit that a wrong-pipeline G2 is worse than a late G2.
- The cloud lane in this repo is the unsloth/transformers readout stack, NOT
  vLLM. Standing up a byte-parity vLLM run_eval on HF Jobs would be a NEW,
  unvalidated pipeline surface (vLLM version, structured-outputs backend, LoRA
  request path, gold/surface data staging) - exactly the parity risk the spec
  warns against, and none of it is exercised by the validated probe cloud lane.
- The local lane already has the exact config that generated the reference; the
  parity-safe move is to swap the arm's adapter into that same local config and
  re-run run_eval.py. n=3,369 with max_new_tokens 128 under vLLM is fast locally
  and does not need the cloud lane's preemption protection.

So: CELL C stays local, reusing the E config with the TRUE-arm adapter swapped;
its output trio JSON becomes `--g2-true`. This is a build-not-here item; flagged
as an assessment per the task.

## Open risks / spec ambiguities

1. Adapter application vs sensor extraction: the sensor v2 was fit through the
   base + an IDENTITY-at-init LoRA (get_peft_model). The verdict cells apply the
   arm's TRAINED adapter via PeftModel.from_pretrained. This is correct (the
   verdict measures the trained policy and Amendment T refits a FRESH probe on
   the trained-checkpoint states), but it means the fit-states distribution is
   the TRAINED model's, not the sensor's frozen surface - by design. Worth a
   one-line confirmation from the lead that the staged base+adapter reproduce
   the trainer's `final_model` load (trainer used unsloth get_peft_model then
   trained; the HF adapter should be the saved LoRA from run_dir/final_model).
2. Merged-vs-adapter serving: the trainer loads clean-SFT 4-bit then trains a
   LoRA on top. The cells replicate that (4-bit base + PeftModel adapter). If
   the staged TRUE adapter was instead saved as a merged 16-bit model, the cell
   should be launched with --adapter-repo "-" and the merged repo as
   --base-model. The dry-runs above assume the adapter-on-4bit-base layout
   (matches the trainer and the sensor lineage); confirm the staged artifact
   form before launch.
3. render_probe_prompt mode discovery runs per-call at batch-1 (mode=None). It
   is deterministic and matches the sensor extractor's path; no caching needed.
4. schema_valid definition: taken as
   `scorers.parse_stated_confidence(answer_text).stated_confidence is not None`
   (the required answer+confidence JSON parsed well-formed). This is the natural
   schema-contract read and matches how the reward's humility_reward.valid_json
   is conceptually defined; if the lead wants schema_valid tied to a stricter
   check, it is a one-line change in run_generate.
5. The two input pools must be staged by the lead before launch (they are not
   built here; they are byproducts of the already-run pool build). The default
   staging repo `professorsynapse/eh-ai-verdict-staging` is created by
   upload_folder.py on first upload if absent, but the lead should pre-create it
   PRIVATE and put the input pools under `inputs/` first.
6. The launcher edit relaxed the X-lane's argparse `required=True` on
   --model/--gate-rows/--run-tag to in-code validation. Behavior for a correct
   X-lane invocation is unchanged; only the error message for a missing arg
   changed (clean FATAL instead of argparse usage). Confirmed by dry-run that
   the X-lane guard still fires.
