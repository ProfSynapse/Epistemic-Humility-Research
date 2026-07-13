# qwen35-4b-midband-doubt-snap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-12 (resolve): Full ladder completed 22:35 (74,753 generations,
  ~59.2h wall, batch_size=8, RunLog per row throughout, runner exited
  cleanly after writing `dose_ladder_full_summary.json`). Lead recomputed
  the headline aggregates independently from the raw RunLogs BEFORE the
  red-team pass; recompute matched the runner's official summary at every
  spot-checked cell. Red-team review (seven attack surfaces) returned
  G1 SURVIVES with no invalidating finding; the three items lifted for lead
  adjudication were all accepted: (1) the cost gate's registered population
  is all 240 FIT knowns (10/240 = 0.042 passes; the 10/13 fired-known
  conditional is reported alongside in the Outcome), (2) the result is
  framed as in-sample FIT-only existence evidence, never held-out, (3) the
  official aggregate `dose_ladder_full_summary.json` (verified row-text
  free) was promoted into `analysis-committed/` at resolve. Verdict written
  into AMENDMENT.md: G1 PASSES at hs20 dose 8 x sigma_c (refused 0.684,
  well-formed 0.980, known false-refusal 0.042), the unique clearing cell in
  the locked 4x7 grid; falsifier does not fire; late-site comparator hs30
  reproduces its entangled failure in-grid. Layer potency is monotone toward
  earlier layers (hs20 > hs23 > hs26 > hs30). Two stale draft-era passages
  in AMENDMENT.md (the header status line and the "run_dose_ladder.py has
  NOT been written" sentence) were corrected at resolve with explicit
  correction notes; no registered content changed. Hygiene note from the
  red-team, recorded so nobody quotes the wrong number: build_manifest.json
  Youden `tp` counts (hs20 870, hs23 865) differ by ~1 row from the
  frozen-tau operating fire counts Stage C uses (869, 864); boundary
  rounding at fit time, Stage C internally consistent.

- 2026-07-10: Batch-size probe (post-sign, pre-full-launch). Bounded probe at
  n=30 rows, hs23, dose_mult=8.0 (all four arms: baseline, gated,
  permuted_gate, random_direction), batch sizes {8 (reference), 16, 32}, run
  via unmodified `smoke` mode with `--n-rows`/`--batch-size` CLI args only (no
  pinned file touched). GPU idle before starting (0% util, 1 MiB used).
  Memory passed at every size: bs=8 9002 MiB, bs=16 9628 MiB, bs=32 10836 MiB,
  all well under the 24 GiB card. Semantic parity FAILED at bs=16 and bs=32
  vs the bs=8 reference: 61/240 (row x field) comparisons diverged across the
  four RunLogs. Most were pure wording drift (same semantic content,
  different phrasing -- consistent with bf16 batched-matmul reduction-order
  changing greedy-decoding tie-breaks when a row is batched alongside a
  different set of co-batched rows). One row was a categorical flip on the
  primary gate metrics, reproduced identically at both larger batch sizes:
  `smoke__hs23__gated.jsonl` row `kuq_unknowns_all:1041` -- at bs=8 the model
  refuses ("I don't know the answer": `refused=True`, `clean_tighten=True`);
  at bs=16 AND bs=32 the same row gets a substantive answer
  (`refused=False`, `clean_tighten=False`). This confirms, on the local
  3090, the same Qwen3.5 batch-composition non-determinism hazard previously
  seen on the Modal A100 cells (doubt-snap-cross-family-confirmatory
  precedent) -- batch composition alone can flip the G1 primary metrics
  (refused_rate, clean_tighten) for individual rows. Per the pre-stated
  fallback rule (parity failure at 16 -> fall back to 8), the full ladder
  runs at **batch_size=8**. Caveat not tested: residual bs=8-vs-1 drift; bs=8
  is treated as the validated reference state, not verified against a
  single-row baseline. Probe scratch outputs (`analysis/probe_bs{8,16,32}/`,
  `analysis/runlog/smoke__*`, `/tmp/probe_*`) were cleared after extracting
  the comparison, so they never persisted as real RunLog data.

  Full ladder launched 2026-07-10 11:20 (host time) as a harness-tracked
  background process (`run_dose_ladder.py full
  --i-know-this-launches-the-full-stage-c-ladder --batch-size 8`), verified
  as the real Python process (not a stray wrapper) via `ps`, with the first
  RunLog batch (`analysis/runlog/baseline.jsonl`) confirmed persisted shortly
  after start. Revised runtime estimate from measured throughput and real
  per-layer fire counts (hs20=882, hs23=878, hs26=881, hs30=865 fired /
  1,127 FIT rows): ~48-55 hours total (74,753 generations: 1,127 shared
  baseline + 3 arms x 7 doses x fired-row-count per layer, summed over the
  four candidate layers).

- 2026-07-10 (SIGNED): Experiment signed after user review. Predictions
  registered pre-outcome: user predicts G1 passes (decouples; the late-site
  failure was a write-site problem, not a family problem); orchestrator
  predicts G1 passes, most likely at hs23 in the 6-12 sigma_c range. Dose
  grids and G1/falsifier floors locked as registered in cell.yaml/gates.yaml.
  Pin-set note: `bin/exp sign` pinned the five files listed in the scaffold's
  instrument block; the three Stage C modules (`run_dose_ladder.py`,
  `grader.py`, `gen_lib.py`, committed and smoke-tested pre-sign at 8b26cfa3)
  were added to instrument.modules and instrument.pins by hand immediately
  after sign, before any Stage C launch, using the established sha256sum
  mechanism. Nothing had run and no outcome existed at the time of the
  addition. Launch plan approved by user: bounded batch-size probe (16 then
  32, memory + output parity vs batch 8) then the full ladder on the local
  3090 at the best validated batch size.

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
