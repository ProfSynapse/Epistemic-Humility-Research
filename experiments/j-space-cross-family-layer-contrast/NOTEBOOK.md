# j-space-cross-family-layer-contrast notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-09 -- draft scaffold written (no GPU work run)

Scaffolded via `bin/exp new --type steer-cell j-space-cross-family-layer-contrast`
on branch `exp/j-space-cross-family-layer-contrast` (worktree
`/home/profsynapse/code/ehr-worktrees/jspace-cross-family`). Read the six
governed docs the lead named (two Qwen3-4B J-space predecessors, the
localization diagnostic + its NOTEBOOK.md, Amendment Z, and the
doubt-gated-caution-tighten gate-and-snap origin) before writing any code, per
the KG-search-first / read-before-you-cite rule.

Wrote per-family config YAMLs (`families/{llama-3.2-3b,ministral-3-3b,qwen35-4b,gemma4-e4b}.yaml`)
transcribing Amendment Z's exact checkpoints, run order, and per-family
loader/VRAM risk notes verbatim, with `band_selection` and `doses` left
`not_yet_run`/`not_yet_calibrated` (no profile or calibration has executed).

Ported the two Qwen3-4B J-space experiments' bespoke scripts into
family-parameterized versions (`mine_eval_pool.py`, `split_fit_heldout.py`,
`jlens_profile.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`cross_family_rollup.py`), plus `family_config.py` as the single read/write
path for each family's YAML (no other script hardcodes a checkpoint, hidden
size, or layer index) and `model_lib.py` porting Amendment Z's own loader
hardening (`AutoModelForCausalLM` -> `AutoModelForImageTextToText` ->
`AutoModelForVision2Seq` fallback chain, `config.text_config` nesting).
`gen_lib.py` and `grader.py` are the generation-contract and grading code,
generalized (EOS resolution) or ported unchanged (grading is already
model-agnostic).

Verified every script with `py_compile` and `--help` (CPU-only, unsloth_env
conda python) -- no model loads, no GPU touched, per the lead's explicit
instruction that the local 3090 is busy with another experiment's
confirmatory and must not be touched at all.

Did NOT run `bin/exp sign` (prediction/falsifier/gates need the lead's
review and the scoreboard rows need the lead + user's calls first). Did NOT
run any HF pull, Modal launch, or GPU work. See `LAUNCH-PLAN.md` for the
per-family run order, GPU-time estimates, and the decision points that need
to come back to the lead before this experiment can launch for real.
