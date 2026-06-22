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
response confidence should be highest; unknown high-confidence abstention should
be positive; known over-refusal should be negative, especially if confident;
unknown/known confident wrong answers should be worst; malformed JSON should not
be rewarded like a valid answer. In Amendment B GRPO, `confidence` means
confidence that the answer or abstention is appropriate, not probability that a
factual answer string is correct.

Preserve intermediate confidence signal instead of binarizing the reward. A
wrong answer with low confidence should be penalized less than a confident wrong
answer, and an `I don't know` on a known question with low confidence should be
penalized less than confident over-refusal while still remaining negative. Keep
these cases in the sanity table/tests so reward edits do not collapse the
ordinal ladder.

After any GRPO smoke, inspect the trainer logs for reward variance before
scaling. A micro-run can validate Docker/model/data/reward plumbing while still
logging `rewards/combined_reward/std: 0.0` and `frac_reward_zero_std: 1.0`,
which means the sampled completions within each prompt received identical
reward and GRPO had no useful comparative learning signal on that step. Treat
zero-variance smokes as infrastructure passes only. Before a longer run, add or
run a rollout/reward-variance diagnostic that records raw completions and reward
distributions under the intended generation settings.

For Qwen3 GRPO, use tokenizer-native chat templating when relying on
`enable_thinking: false`; generic ChatML templating can ignore the Qwen thinking
switch and produce clipped `<think>` traces. The working local base-GRPO smoke
pattern used `model.chat_template: "native"` plus
`training.chat_template_kwargs.enable_thinking: false`. Synaptic Tuner GRPO must
thread `chat_template_kwargs` into `tokenizer.apply_chat_template`; if a trainer
copy lacks that support, treat the run as not Qwen3-protocol-equivalent.

For reward-variance bootstrap, a low-temperature or default Qwen3 sampler can
produce four identical JSON completions per prompt, yielding zero GRPO signal
even when parsing is healthy. The 2026-06-21 local base smoke only produced
nonzero trainer reward variance after increasing exploration
(`temperature: 1.6`, `top_p: 1.0`, `top_k: 0`, four generations, 256 completion
tokens). Keep the reward-debug trace opt-in, and enable it when trainer logs
show unexpected zero variance so raw completions, parse status, and per-sample
rewards can be audited.

Do not assume SFT-warmed checkpoints are better GRPO starting points for the
stated-confidence objective. The local SFT seed-1 merged checkpoint preserved
the old answer-only/refusal contract and produced 0% valid answer/confidence
JSON under the same native Qwen prompt, even with eight rollouts. SFT-start GRPO
needs a format bridge or separate prompt-contract adaptation before treating
confidence-reward GRPO as operational.

After an SFT JSON bridge, do not blindly reuse the high-exploration base-GRPO
sampler. In the 2026-06-21 local bridge smoke, `temperature: 1.6` with 256
completion tokens produced nonzero reward variance but many clipped/gibberish
malformed completions. Over-correcting to low temperature kept JSON clean but
collapsed trainer reward variance. The working bridge micro pattern used
`num_generations: 8`, `per_device_train_batch_size: 8`, `temperature: 1.35`,
`top_p: 1.0`, and 128 completion tokens: 48/48 reward-debug completions were
valid JSON, trainer clipping stayed 0.0, and all 6 smoke steps had nonzero
reward variance. Treat sampler choice as a contract-format gate before scaling.

For full SFT-bridge GRPO, remember that one trainer step is effectively one
prompt group when `num_generations` equals the per-device batch size. The
2026-06-21 local full run over 14,395 prompts therefore ran 14,395 steps, not
roughly 1,800 batch steps, and took about 15.9 hours on the RTX 3090 at
~0.25-0.37 steps/sec. Plan monitoring/checkpoint cadence accordingly.

The first completed full SFT-bridge GRPO run showed a real behavior/schema
tradeoff: training completed with low OOM risk and preserved rolling reward
variance, and a 64-row eval-like dev diagnostic improved known accuracy and
unknown abstention relative to the pre-GRPO bridge, but introduced 1 malformed
known JSON output where the pre-GRPO bridge had none. Do not report it as
headline evidence until the standard eval suite quantifies schema validity and
behavior on the full evaluation set.

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
