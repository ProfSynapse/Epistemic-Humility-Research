# qwen35-4b-midband-doubt-snap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-10: Lead adjudication on Stage A's RunLog deviation (recorded here,
  not retrofitted into `jlens_qwen35.py`): Stage A used a per-layer JSON
  flush instead of the tuner's `shared/utilities/run_log.py` RunLog. The lead
  adjudicated this ACCEPTABLE, because the flush gives the crash-resume
  property the RunLog rule exists for, at the natural checkpoint granularity
  of that loop (one profiled layer, not one row) -- a JVP layer profile has
  no per-row structure to key a RunLog on, while a per-item generate+grade
  loop (Stage B extraction, Stage C dose ladder) does and gets RunLog wired
  in directly (see `run_dose_ladder.py`, below). Stage A's own script is not
  changed to add RunLog after the fact.

- 2026-07-10: Wrote and smoke-tested `run_dose_ladder.py` (Stage C harness).
  Instrument files (`grader.py`, `gen_lib.py`, byte-for-byte ports of
  `doubt-snap-cross-family-confirmatory`'s own modules, diffed against the
  sibling `j-space-midband-write-sweep-qwen3-4b` copies before choosing which
  one to mirror -- the two projects' grader.py differ in alias-matching
  dependency, gen_lib.py do not) plus `run_dose_ladder.py` itself are ready
  for `cell.yaml`/`gates.yaml` pinning at sign. See the harness-builder
  task's own report (routed to the team-lead) for the smoke numbers, the
  full-ladder runtime estimate, the batch size validated, and the resolved
  ambiguities (hs30 included as an in-run arm per cell.yaml's own dose-grid
  table; write dose sign is positive along c_hat/random_direction in every
  arm, since the task brief's "negative projection" language matches this
  project's neg_z_d GATE score convention, not the write).

- 2026-07-10: Stage A profile completed (14/14 layers, 2554.0s / ~42.6 min
  total, no crash under `CUDA_LAUNCH_BLOCKING=1`); wrote
  `analysis/profile_full.json` (`status: complete`). `effective_dim_frac_mean`
  peaks at hs23 (0.558), with adjacent profiled layers hs20 (0.530) and hs26
  (0.525); mid-depth points hs5-hs20 oscillate 0.39-0.53, the late-site region
  hs30-31 sits lower (~0.396-0.399), and hs32 collapses to 0.083 (RMSNorm
  degeneracy at the output). Applied the pre-registered band-selection rule
  (peak + immediately adjacent profiled layers) -> `midband_candidates_hs =
  {20, 23, 26}`, written to `cell.yaml` and
  `analysis-committed/profile_summary.json` (aggregate-only, no row text).
  GPU confirmed idle before launch and after completion (0% util, 1 MiB
  used both times).

  Ran Stage B `extract` (GPU, plain forward pass, no grad, no eager/no
  CUDA_LAUNCH_BLOCKING needed for this stage) over all 1,308 FIT rows at
  hs_indices {20, 23, 26, 30} (mid-band candidates plus the late comparator,
  per team-lead instruction to fit u_d/tau/c_hat/random at all four).
  853.9s (~14.2 min), peak GPU memory ~8.3 GiB. Wrote
  `analysis/anchor_extract.safetensors` (5,232 vectors) and
  `analysis/anchor_extract_manifest.json` (both gitignored, contain no row
  text beyond row_key/role/split/prompt_len already present in the reused
  rows manifest). Note an operational near-miss: the extraction was first
  launched with a shell `&`-background inside a Bash-tool `run_in_background`
  call, which caused the harness to report the WRAPPER script (the `echo
  $!`) as complete rather than the actual Python process; caught by checking
  `ps aux` for the real PID and re-arming a monitor against the manifest file
  rather than trusting the first completion notification. No data or
  correctness impact -- the extraction ran to completion regardless -- but a
  process-tracking gotcha worth remembering for future double-backgrounded
  launches.

  Ran Stage B `fit` (CPU, numpy/sklearn only) over the same four hs_indices.
  Every layer's fit was run twice and confirmed byte-identical
  (`_fit_byte_identical`) before any artifact was written. Results (FIT
  AUC / tau_frozen / sigma_c / mu_c): hs20 = 0.9929 / -0.5897 / 1.5760 /
  -4.0313; hs23 = 0.9926 / -0.7017 / 2.1155 / -7.7542; hs26 = 0.9941 /
  -0.7295 / 2.2364 / -5.0889; hs30 (late comparator, refit under this
  experiment's own extraction, not a replay of cached anchors) = 0.9960 /
  -0.5942 / 2.8165 / -7.3884. All four clear the registered min-AUC-0.90
  gate comfortably. hs30's refit numbers closely reproduce
  `doubt-snap-cross-family-confirmatory`'s cited baseline (sigma_c=2.8006,
  AUC=0.99599) -- small residual differences are consistent with an
  independent refit on freshly extracted anchors, not a discrepancy to chase.
  All three mid-band candidates have SMALLER sigma_c than the late site, so
  a coherent write window at mid-band (if one exists) will sit at a SMALLER
  absolute dose than the late site's own dose-40 peak, not larger. Derived
  per-layer dose grids ({2,4,6,8,12,16,20} x sigma_c) recorded in
  `LAUNCH-PLAN.md` and `cell.yaml`'s new `snap.dose_grid_proposal` block
  (still draft-until-sign). Wrote
  `analysis-committed/build_manifest.json` and
  `analysis-committed/directions/hs{20,23,26,30}/{u_d,c_hat,random_direction}.json`.

  Found and fixed a `.gitignore` bug while preparing to commit: a
  top-level `directions/` pattern was shadowing the deliberately-committed
  `analysis-committed/directions/` fit outputs (confirmed via `git status
  --ignored=matching`). Removed the redundant top-level pattern (the
  `analysis/` pattern already covers any scratch `directions/` under
  `analysis/`); `analysis-committed/directions/` is now correctly
  trackable.

- 2026-07-10: Data reuse verified. Downloaded
  `fit_rows_for_dose.jsonl`/`heldout_rows_for_steer.jsonl`/`split_rows_private.jsonl`
  read-only from Modal volume `eh-doubt-snap-cross-family` at
  `doubt-snap-cross-family-r1/qwen35_4b/analysis/` via `modal volume get`.
  `materialize_reused_rows.py` sha256-verified all three
  (`42db19f0...`, `aa9c5294...`, `42659f40...`) and confirmed counts match
  `doubt-snap-cross-family-confirmatory`'s registered
  `g0_prep_summary.json` exactly: 887 confab FIT + 240 known_correct_answered
  FIT + 181 unknown_refused (fit_only) = 1,308 FIT rows; 1,332 confab + 360
  known_correct_answered = 1,692 held-out rows (recorded, untouched).
  Wrote `analysis-committed/reused_rows_manifest.json` (ID-only) and the
  local working file `analysis/fit_rows_for_anchor.jsonl` (1,308 rows,
  gitignored, contains question text).

- 2026-07-10: Loader blocker found and resolved. The task's binding local
  Python pin, `/home/profsynapse/.conda/envs/unsloth_env/bin/python`
  (transformers 4.57.1), raises `KeyError: 'qwen3_5'` inside
  `AutoConfig.from_pretrained` -- this transformers version has never heard
  of the `qwen3_5` model type at all (confirmed: `'qwen3_5' not in
  MODEL_FOR_CAUSAL_LM_MAPPING_NAMES`). The Qwen/Qwen3.5-4B repo ships no
  custom `modeling_*.py` / `auto_map` (`trust_remote_code` cannot help; the
  files list is config.json/tokenizer/safetensors only), so this is a hard
  environment gap, not a `trust_remote_code` oversight. `unsloth_latest`
  (the project's other unsloth conda env) is also transformers 4.57.1 --
  same gap. `/home/profsynapse/miniconda3/bin/python3` (base conda) already
  has transformers 5.5.0 (`'qwen3_5' in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES` is
  True), torch 2.9.0+cu128 with CUDA available, plus numpy/sklearn/
  safetensors -- a complete, working environment for this experiment's GPU
  scripts. Used that env instead of upgrading `unsloth_env`'s transformers
  in place (which would risk breaking other in-flight unsloth-based
  pipelines sharing that env, e.g. the concurrently `in_progress` "Gate-and-
  snap tighten diagnostic" task). Recorded as a documented deviation in
  `cell.yaml`'s `surface.loader_note`, not a silent substitution.

- 2026-07-10: Architecture finding: Qwen3.5-4B is a HYBRID linear-attention
  model. Plain forward pass (`AutoModelForCausalLM.from_pretrained(...,
  dtype=bf16, device_map='cuda')`, no `attn_implementation` override, no
  grad) works cleanly and returns 33 hidden_states (n_layers+1=33,
  confirming 32 decoder blocks, hidden_dim=2560, matching the cross-family
  cell's own `build_manifest.json`). Console output at load time: "The fast
  path is not available because one of the required library is not
  installed. Falling back to torch implementation" -- decoder blocks route
  through `self.linear_attn(...)` -> `torch_chunk_gated_delta_rule`, a
  custom recurrence, not standard SDPA, for (at least some) blocks; the
  `flash-linear-attention` optimized kernel is not installed, so every such
  block runs the slow PyTorch fallback.

  First-order gradient flow through this op works (`torch.autograd.grad`
  with `create_graph=False` succeeded at hs_index=5 with the DEFAULT
  attention implementation). The jlens.py double-backward trick, however,
  needs `create_graph=True` through the *entire* downstream network,
  including any standard-attention blocks; without `attn_implementation=
  "eager"` that failed immediately with `RuntimeError: derivative for
  aten::_scaled_dot_product_flash_attention_backward is not implemented` --
  exactly the reason the original Qwen3-4B jlens.py forces eager attention,
  confirmed to still apply here.

  With `attn_implementation="eager"` set, a plain eager forward pass (no
  grad) is clean. But running `jlens_qwen35.py profile --layers 2,30,32`
  (the actual double-backward JVP path) crashed on the SECOND layer
  (hs_index=30) with `torch.AcceleratorError: CUDA error: unknown error`
  inside `torch_chunk_gated_delta_rule`'s `torch.zeros(...).to(value)` --a
  bare tensor allocation, not obviously autograd-related. Re-running
  `--layers 30` ALONE in a fresh process succeeded cleanly. Re-running the
  IDENTICAL `--layers 2,30,32` sequence with `CUDA_LAUNCH_BLOCKING=1` set
  ALSO succeeded cleanly end to end (hs2: kurt=0.572, hs30: kurt=0.236,
  hs32: kurt=0.156, no error). Read as an async-kernel-ordering hazard in
  this custom op under double-backward specifically (PyTorch's own warning:
  "CUDA kernel errors might be asynchronously reported at some other API
  call"), not a correctness bug in the JVP math or the profiling script.
  `CUDA_LAUNCH_BLOCKING=1` is now a hard requirement for `jlens_qwen35.py`
  and `fit_midband_directions.py extract`, recorded in `cell.yaml`.

  Timing consequence: per-eval JVP cost here (~11.4s/prompt-direction at
  hs_index=2, the worst case -- full-depth backprop through many
  `linear_attn` blocks on the slow fallback path) is roughly 50x the
  Qwen3-4B reference's own full profile (`profile_full.json`:
  1039.2s / (1000 prompts x 5 dirs) = 0.208s/eval at its own hs_index=2).
  Cost decreases toward the final layer (hs30: ~1.15s/eval measured on a
  tiny smoke; hs32: ~0.67s/eval) since less depth needs backprop. This is
  why Stage A here uses `n_prompts=12, n_random_dirs=3` rather than the
  Qwen3-4B reference's `1000x5` -- a screening tool for band selection, not
  a statistically hardened profile; the actual gate (AUC, effect size) sits
  in Stage B/C, not in this profile.

- 2026-07-10: Launched the full Stage A profile
  (`jlens_qwen35.py profile --layers 2,5,7,10,13,15,18,20,23,26,28,30,31,32
  --n-prompts 12 --n-random-dirs 3 --log-every 4 --out
  analysis/profile_full.json`) under `CUDA_LAUNCH_BLOCKING=1`, in the
  background, on the local RTX 3090 (confirmed idle before launch:
  `nvidia-smi` 0% util, 1 MiB used). GPU memory during run: ~9.8 GiB / 24.5
  GiB. Per-layer partial results flush to `analysis/profile_full.json`
  after each layer completes (progress-visible on disk, mirroring
  `j-space-localization-qwen3-4b/jlens.py`'s own `on_layer_done` flush
  convention -- this JVP-profiling method is not row-based, so the
  project's RunLog mechanism does not apply here; the per-layer JSON flush
  is the equivalent checkpoint for this method).

- (add dated entries as the experiment progresses)
