# Common Patterns

The canonical launch sequence:

```bash
# 1. Dry-run: expand the matrix, confirm the 19/9/2 count assertions pass,
#    eyeball the per-cell seeds/overrides. Launches nothing.
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run

# 2. Check prerequisites for the lane you intend to run. Reports per-cell gate
#    status (datasets present, leakage guard passed, cloud/bridge skips).
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local

# 3. Local smoke: run ONE 4B cell locally to confirm the trainer path before
#    committing the matrix. (Explicit, user-approved launch per CLI Discipline.)
python3 .agents/skills/experiment-runner/scripts/prepare_local_cell.py \
  --run-id sft__4b__headline__seed1 --status launched
cd synaptic-tuner
python tuner.py local-run \
  --job-config ../experiment/phase1/run_records/materialized_recipes/sft__4b__headline__seed1.yaml \
  --yes

# 4. Local 4B pilot, then — once the cloud seed/beta capability lands and the
#    datasets are published to the hub — the cloud matrix.
```

After Docker Desktop/backend trouble, first run the intentionally tiny local
confidence loop before touching any long cell:

```bash
cd synaptic-tuner
python tuner.py local-run \
  --job-config ../experiment/phase1/run_records/materialized_recipes/sft__4b__micro_max2.yaml \
  --yes
```

This runs SFT for `max_steps=2` against the already staged 4B SFT data. It
validates Docker, GPU access, model load, data prep, two optimizer steps, final
adapter save, metrics/logs, lineage/capacity files, and host artifact copy-out
in a few minutes without exercising the currently fragile KTO path.

After the 2026-06-13 successful local recovery, scoped live eval smoke, bounded
SelfAware evidence run, full SelfAware evidence run, broader OOD evidence run,
and KTO seed-1 comparator/evals, treat the evidence as bounded local motivation
for Amendment A, not headline/protocol evidence. The practical pattern is:
SFT learns abstention but over-refuses badly; DPO-from-base and KTO-from-base
remain base-like on refusal behavior. Do not jump from these bounded runs
directly to mixed-stage cells, a headline/full run, or any cloud job without
explicit approval and deliberate materialization.

Headline numbers come ONLY from the pre-registered default cells; the LR/beta
panel is robustness-only and is tagged distinctly in each run-id coordinate so
the eval-side aggregation isolates it.

## Amendment B GRPO Bootstrap Pattern

Before launching any GRPO/RLVR training cell, run a CPU-side reward and dataset
preflight. Treat these as plumbing checks, not reportable Amendment B evidence:

```bash
python experiment/phase1/grpo/build_grpo_dataset.py \
  --model-tag qwen3-4b-instruct \
  --output-dir scratch/grpo_bootstrap/qwen3-4b-instruct

python experiment/phase1/grpo/make_smoke_subset.py \
  --input scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl \
  --output scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train_smoke_32.jsonl \
  --per-label 16

python experiment/phase1/grpo/reward_sanity_table.py \
  --output scratch/grpo_bootstrap/reward_sanity_table.csv

python -m pytest \
  experiment/phase1/grpo/tests/test_humility_reward.py \
  experiment/phase1/grpo/tests/test_build_grpo_dataset.py \
  synaptic-tuner/tests/trainers/grpo/test_fitness_reward.py \
  -q
```

Sanity-check the reward ordering before GPU use: known correct with high
confidence should be highest; unknown low-confidence abstention should be
positive; known over-refusal should be negative; unknown/known confident wrong
answers should be worst; malformed JSON should not be rewarded like a valid
answer.

Custom GRPO reward files are loaded dynamically by Synaptic Tuner. If a custom
reward module uses `@dataclass`, the loader must register the module in
`sys.modules` before `exec_module`; otherwise Python's dataclass machinery can
crash during import. This is a generic tuner concern, not an Epistemic-specific
reward rule.

For first GPU contact, prefer a two-step micro smoke with the checked-in
Amendment B configs:

```bash
python synaptic-tuner/Trainers/grpo/train_grpo.py \
  --config experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml
```

Run the SFT-seed1 micro smoke only after base GRPO plumbing succeeds. Avoid
starting this while a live eval/training container is actively using the GPU
unless the user explicitly prioritizes GRPO over the running job.
