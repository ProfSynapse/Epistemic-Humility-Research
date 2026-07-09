# j-space-cross-family-layer-contrast notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-09 -- tokenizer/config verification pass (CPU-only, no GPU work run)

Resolved LAUNCH-PLAN.md decision points #3 (multimodal config nesting), #4
(EOS lists + layer counts), and #5 (Gemma system-role support) by
downloading ONLY `config.json`/`tokenizer_config.json`/
`special_tokens_map.json`/`generation_config.json`/`chat_template.jinja`
per checkpoint via `hf_hub_download` (never `snapshot_download`, no
`*.safetensors`/`*.bin` touched) for all four checkpoints:
`unsloth/Llama-3.2-3B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`,
`Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. All four repos were ungated
(no 403s). Fetch script and cached files live under this experiment's
gitignored `analysis/tokenizer-config-verify/` (fetch script:
`fetch_configs.py`; not tracked, upstream artifacts only).

Also ran a small number of meta-device (`torch.device("meta")`, no weight
download, no GPU) `AutoModelForCausalLM`/`AutoModelForImageTextToText`
construction checks against the downloaded configs to directly test the
multimodal loader-class questions LAUNCH-PLAN.md flagged as unverified
(`attn_implementation="eager"` acceptance, and whether the vision/audio
towers are structurally part of the resolved model class) -- no weights
were downloaded or instantiated with real data for this.

Confirmed: Llama's `n_hidden_layers: 28` guess, Mistral's/Qwen3.5's EOS
guesses, and Qwen3.5's `nested_text_config: true` + `enable_thinking`
kwarg. Filled in previously-`null` layer counts for Mistral (32), Qwen3.5
(32, nested), and Gemma4 (42, nested), each with a recomputed
`round(0.9444 * n_hidden_layers)` late-reference estimate.

Corrected two factually wrong guesses for `google/gemma-4-E4B-it`: (1) its
EOS/end-of-turn token is `<turn|>` (per `tokenizer_config.json`'s own
`eot_token` field and the live chat template), not the classic Gemma
2/3 `<end_of_turn>` the draft assumed; (2) it DOES have a native
`enable_thinking` kwarg (gates a `<|think|>` token injection), contrary to
the draft's "Gemma has no thinking-toggle kwarg" claim. Also resolved
decision point #5 in the affirmative (its template gives `system` its own
turn, not folded into the first user turn -- the flagged concern was
unfounded for this checkpoint) and found it is trimodal (vision + audio
towers, not vision-only) -- both AMENDMENT.md's family table and
`families/gemma4-e4b.yaml` were updated to flag these corrections
prominently. Full detail in each `families/<slug>.yaml`'s per-section
"VERIFIED"/"CORRECTED" notes and LAUNCH-PLAN.md's revised decision points
#3/#4.

Did NOT touch decision point #1 (G3 floor) or the VRAM GB estimates in the
feasibility table (lead-kept); did NOT sign, did NOT run any model
generation, did NOT touch the local 3090.

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
