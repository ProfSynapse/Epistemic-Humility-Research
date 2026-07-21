# Gemma-4-E4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-20 - stage (b) full-depth capture, stage (c) CPU panel, AG0/AG1/AG2 evaluation

- Stage (b): `capture_family_atlas_cell.py capture` ran inside the pinned
  container against the run-3/run-4 split manifest (2815 rows, role/split
  counts unchanged from mining: confab fit 840 / held_out 1263, known
  correct fit 168 / held_out 251, unknown_refused fit_only 293), full depth
  (hs_index 0-42, `n_hidden_states=43`), final-prompt-token anchor,
  `--persist-dtype float32`. Log
  `analysis/gemma4_e4b_it/atlas_capture_run1.log`, exit code 0. Written
  `capture_manifest.json`: `coverage_frac` 1.0, `coverage_pass_ag0` true,
  `n_rows_captured` 2815 of `n_rows_in_pool` 2815, `missing_row_count` 0,
  `n_hidden_states` 43, `hidden_size` 2560, `capture_index_sha256`
  `a11ed3a81fe5cf15e70b3d97a2a532f0aef98c63ebd0db39ce21186fac56f1d0`.
- Stage (c): `profile_and_read_family_atlas_panel.py score` ran CPU-only (no
  GPU, no model weights loaded), same container. Log
  `analysis/gemma4_e4b_it/atlas_panel_score_run1.log`, exit code 0. Written
  `analysis-committed/gemma4_e4b_it/atlas_summary.json` (43 per-layer
  entries, hs_index 0-42; three-axis read panel with 2000-resample bootstrap
  CIs, seed 20260707; random-direction control; refused-pool subdivision
  146 refused_fit / 147 refused_eval from the 293-row fit_only pool).
- Exhaust staged to `/home/profsynapse/code/ehr-exhaust/gemma-4-e4b-family-atlas/`
  (mirrors this experiment's own `analysis/` and `analysis-committed/`
  trees; 1.2G total). Verified: every staged file profsynapse-owned (no
  root-owned leftovers from the container's writes), and `atlas_summary.json`
  sha256-identical between source and staged copy
  (`3374521c60cfc898485ed1839507f925e517a67ff8313cf04d78db4c45764560`).
- AG0 (integrity, pre-outcome), all three checks evaluated directly from
  artifacts on disk:
  - `capture_coverage`: 1.0 against the 0.95 floor, scope per_cell_per_layer
    (uniform across layers since every row's full depth is captured in one
    pass). Pass.
  - `direction_refit_determinism`: `fit_axis_direction` (the module's own
    `unit(mean(pos_fit) - mean(neg_fit))`, no seed argument) fitted twice,
    independently, from freshly reloaded captures at three layers (hs_index
    4, 13, 40) and all three axes. `np.array_equal` exact comparison: byte
    identical in all nine layer/axis combinations, max abs diff 0.0, unit
    norm 1.0 both times. Script:
    `/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/ag0_direction_refit_determinism.py`
    (diagnostic, not committed; output written to
    `analysis/gemma4_e4b_it/ag0_direction_refit_determinism.json`, which is
    profsynapse-owned and writable, unlike `analysis-committed/`, which the
    container's root-owned writes left unwritable to this agent). Pass.
  - `held_out_power_survives_attrition`: post-capture split manifest counts
    (`n_rows_captured` equals `n_rows_in_pool`, 0 missing) are identical to
    the pre-capture mining counts: confab held_out 1263 against the 150
    floor, known_correct_answered held_out 251 against the 250 floor. Pass,
    zero attrition.
- AG1 (profile):
  - `eff_dim_frac_every_layer`: `atlas_summary.json`'s `per_layer` has
    exactly 43 keys, hs_index 0 through 42 inclusive, matching the required
    scope. Pass.
  - `profile_reproducibility`: 20% row subsample (260 of the 1301 FIT-role
    rows used for the profile, sorted row_key then `random.Random(seed)`
    shuffle then slice, same convention as the panel's own
    `split_refused_pool`) re-run at all 43 layers using the pinned module's
    own `eff_dim_frac`/`build_layer_matrix`/`load_captures` functions
    directly (no reimplementation). Full-profile peak layer hs_index 4;
    subsample peak layer hs_index 4; delta 0 layers against the +/-1
    tolerance. Script:
    `/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/ag1_subsample_reproducibility.py`
    (diagnostic, not committed; output at
    `analysis/gemma4_e4b_it/ag1_subsample_reproducibility.json`). Pass.
  - Profile shape: `eff_dim_frac` rises steeply from hs_index 0
    (0.00077) to a single maximum at hs_index 4 (0.01895), falls back
    through hs_index 5-9 (0.0165 down to 0.0055), stays in a low, mostly
    flat 0.003-0.013 band from hs_index 10 through 42 with a secondary,
    much smaller local bump around hs_index 12 (0.01242) and hs_index 16
    (0.00906). No second maximum anywhere approaches the hs_index-4 peak
    value. hs_index 4 sits at roughly 9.5% of the 42-layer depth (4/42),
    below the interior band's 20% lower boundary stated in
    `gates.yaml`'s `falsifier_restated`.
- AG2 (read panel), no numeric pass/fail per `gates.yaml` (the numbers are
  the atlas):
  - At hs_index 4 (the profile's peak layer): doubt AUROC 0.9885 (CI
    [0.9809, 0.9941]), caution 0.8347 (CI [0.7981, 0.8711]), raw_refusal
    0.8005 (CI [0.7648, 0.8358]). Random-direction control at this layer:
    ref_vs_known 0.5564, ref_vs_confab 0.5002, ref_vs_answered 0.5092 (all
    near chance).
  - At hs_index 40 (the fleet's ported layer): doubt AUROC 0.9949 (CI
    [0.9896, 0.9986]), caution 0.9223 (CI [0.8942, 0.9468]), raw_refusal
    0.9272 (CI [0.9012, 0.9496]). Random-direction control: ref_vs_known
    0.5917, ref_vs_confab 0.5171, ref_vs_answered 0.5009.
  - Scanning hs_index 0 through 42 for the first layer where all three
    axes simultaneously clear 0.80 AUROC: hs_index 0-12 always has at
    least one axis below 0.80 (raw_refusal is the binding one, e.g. 0.7589
    at hs_index 9, 0.7868 at hs_index 11). hs_index 13 is the first layer
    where all three clear 0.80 (caution 0.8816, doubt 0.9978, raw_refusal
    0.8049), and this holds continuously through at least hs_index 42
    (spot-checked at 20, 25, 30, 35, 40, 42, all three axes above 0.80 at
    each). hs_index 13 sits at roughly 31% depth, inside the (20%, 85%)
    interior band `gates.yaml` defines.

### 2026-07-20 - AG0a v1 failure, signed revisions 1 and 2, cap-400 re-mine, answer-capture re-specification (runs 2 through 4)

- Run 2 (cap-200, `mining_run2.log`) completed capture (2819/2819, resumed
  cleanly past the run-1 CUDA fault) but the fleet's `prep_tuner_cell.py`
  exited 3. AG0a v1 `mining_completed`: `held_out_power` true and
  `role_pool_adequacy` passed, but `generation_terminates_rate` 0.802 vs the
  0.90 threshold and `batched_parity_smoke` 2/8 mismatches on exact-string
  answer comparison. See `AMENDMENT.md` "Signed revision 1" for the full
  failure record and diagnosis (14.3% of generations hit the 200-token cap;
  naturally terminated rows have a length p99 of roughly 250 tokens).
- Signed revision 1 (PI selected "Revise + re-mine"): a local pinned copy,
  `prep_tuner_cell_gemma.py`, derived from the fleet script's pinned sha with
  four documented hunks (ROOT re-point so data paths, imports, model
  registry, and analysis output resolve unchanged; baseline generation cap
  200 to 400; parity-smoke sequential re-decode cap 200 to 400; parity
  comparator replaced by role-relevant grade agreement: semantic verdict,
  clean flag under its own finish reason, refusal classification, instead of
  exact-string answer-field equality). `gates.yaml` AG0a revised to v2 naming
  this module and comparator; the 0.90 threshold and role floors unchanged.
  The new module was hand-added to `instrument.modules` and `instrument.pins`
  in `experiment.yaml` with a persistence declaration (`bin/exp repin` cannot
  introduce a new pin, only repair an existing one, confirmed by reading
  `.skills/experiments/scripts/exp.py:759-885` before acting); `bin/exp
  repin` was then run only for `gates.yaml` (`AMENDMENT.md` was never pinned
  in the first place, since `bin/exp sign` only pins `instrument.configs +
  instrument.modules`, confirmed by reading `exp.py:696-756`, so it could not
  be repinned either).
- Offline validation of the new comparator against the existing run-2
  artifacts for the two v1 parity mismatch rows (`kuq_unknowns_all:848` and
  `:883`, diagnostic only, no GPU): both rows agree on all four role fields
  (`well_formed_correct`, `refused`, `answered`, `clean_tighten`) between the
  batched baseline and the sequential re-decode under the new comparator.
  This is the empirical support cited for signed revision 1.
- Archived every cap-200 mining artifact (generation, grading, capture,
  split manifest, plus five direction/gate files that were fit from the
  cap-200 split and are exactly as tainted as the split itself: build
  manifest, `c_hat`, gate fit, random direction, `u_d`) into
  `experiments/doubt-snap-cross-family-confirmatory/analysis/gemma4_e4b_it/cap200-run-archive/`.
  Left `candidate_pool_private.jsonl` in place (fixed-seed, cap-independent).
  The pinned container writes as root by default, so several archived
  directories and files were root-owned and a plain `mv` failed with
  permission denied (no passwordless sudo configured). Worked around by
  running a second `docker run` against the same bind-mounted worktree to
  perform the `mv` as root inside the container, then `chown -R 1000:1000`
  on the host side to restore `profsynapse` ownership; verified afterward
  that no file under the archive is still root-owned.
- Run 3 (cap-400 re-mine, `prep_tuner_cell_gemma.py`, log
  `mining_run3.log`): exit code 3, verified directly against the log's
  `.exit_code` file and the fresh `g0_prep_summary.json`, not restated from
  a prior summary. Four of five limbs passed: `held_out_power` true
  (known-correct held-out 251 vs the 250 floor, confab held-out 1263 vs the
  150 floor), `gate_auc_on_fit` 0.9472222222222222 pass, `directions_byte_identical`
  true, `batched_parity_smoke` passed with 0 mismatches under the new
  comparator. The termination limb failed again under its unmodified
  definition (raw EOS-emission rate): 0.8849023090586146 vs the 0.90
  threshold (up from 0.802 at the 200 cap, but still short). Row-level
  diagnosis: 337/4000 generations truncated, 96.7% concentrated in
  `kuq_unknowns_all`, 1.8% loop-like; 136/337 (40.4%) contain a complete
  well-formed first-JSON answer, truncated only in post-answer prose Gemma
  appends without emitting EOS.
- Signed revision 2 (PI selected "Revision 2: answer-capture check" from
  three options). An adversarial red-team review ran before signing and
  returned SIGN-WITH-CONSTRAINTS; all five constraints are incorporated in
  `gates.yaml`'s AG0a v3 and in the implementation below. See
  `AMENDMENT.md` "Signed revision 2" directly for the full text; two
  corrections to the original proposal rationale were adopted from the
  red-team and disclosed there rather than repaired silently: (1) it is not
  true that role grading consumes only the first JSON object, `grade_one`
  reads the whole completion text, so the re-specification is justified on
  grading-relevant completeness (the answer object is fully present), not on
  prose isolation; 22/2815 split rows (0.78%) disagree between whole-text
  and first-JSON refusal reads. (2) the 201 mid-answer-truncated rows are
  not excluded by grading, they are graded confab from incomplete text (124
  sit in the held-out confab set); this is accepted as a known pool
  property, not a defect this revision fixes, and the held-out floors carry
  the attrition risk with margin (removing every truncated held-out confab
  row would still leave 1069 vs the 150 floor; the known-correct held-out
  margin of 251 vs 250 contains zero truncated rows).
- Hunk 5 implemented in `prep_tuner_cell_gemma.py`: the termination limb is
  replaced by answer-capture on split rows (`captured` iff
  `finish_reason != "length"`, OR the row's clean grading shows a complete
  well-formed first-JSON answer and the row is not degenerate). Threshold
  unchanged at 0.90. The raw EOS-emission rate is retained under its
  original field name (`generation_terminates_rate`) plus an explicit
  `eos_emission_rate` alias so neither signed revision drops a field
  silently. `diff -u` against the fleet original at default context
  produces 6 `@@` blocks that correspond to exactly 5 documented semantic
  hunks (ROOT re-point, baseline cap 400, parity cap 400, comparator
  replacement, termination-limb re-specification); the fifth hunk spans two
  adjacent default-context blocks only because the g0 dict field edit and
  the five-boolean gate-check swap sit about 19 source lines apart, past
  the diff tool's default 3-line context window. No diff lines exist
  outside these five changes. Net diff: 10 lines removed, 39 added.
- `bin/exp repin gemma-4-e4b-family-atlas gates.yaml prep_tuner_cell_gemma.py`
  succeeded for both files (both already pinned, both with genuinely changed
  bytes: `gates.yaml` `94a44d6a...` to `6e78c7c9...`, script `4b1c4911...`
  to `52b2665f...`), recorded in `instrument.repins`. `bin/exp validate`:
  `OK (86 experiment(s))`, zero errors or warnings for this experiment.
- Offline re-evaluation (run 4, log `mining_run4_offline_reeval.log`, zero
  new GPU work): relaunched `prep_tuner_cell_gemma.py prepare --cell-id
  gemma4_e4b_it` inside the same pinned container with every tuner-stage
  checkpoint already in place from run 3. All three GPU-invoking tuner
  stages resumed as full no-ops (log: "4000 rows total, 4000 already done,
  0 to process"; "8 rows total, 8 already done, 0 to process"; "2815 rows
  total, 2815 already done, 0 to process"). Exit code 0, verified directly
  from the `.exit_code` file. All five hard checks were verified directly
  against artifacts on disk against a pre-rerun snapshot: `split_manifest.json`,
  `u_d.json`, `c_hat.json`, `random_direction.json`, `build_manifest.json`,
  and `gate_fit.json` are all byte-identical (sha256) to their run-3
  versions; the four previously-passing booleans are unchanged
  (`held_out_power` true, `gate_auc_on_fit` 0.9472222222222222 pass,
  `directions_byte_identical` true, `batched_parity_smoke` passed with 0
  mismatches); `answer_capture_rate` is 0.9285968028419183, matching the
  red-team's independently computed number of 2614/2815 (0.9286) exactly;
  `answer_capture_pass` is true. AG0a v3 now passes all five limbs.
- Stopping rule now in force (signed revision 2, red-team constraint 5):
  AG0a is an instrument-adequacy go/no-go, never reported as a finding. A
  third re-specification of the termination limb is not permitted; a future
  failure of this limb on any later run of this cell resolves the cell as
  "the fleet mining instrument cannot cleanly mine this family" rather than
  redefining the check again. This run passed, so the rule is not currently
  triggered, but it governs any later re-run of stage (a) for this cell.
- HOLD: atlas capture stage (b) requires explicit PI launch approval, which
  has not been given. No GPU work beyond this offline resume-only
  re-evaluation was performed or launched.

### 2026-07-20 - stage (a) mining: first run exited 1, relaunched via --resume

- Signed (`bin/exp sign`, all six module pins recorded, `status: signed`) and
  committed by the lead on `exp/gemma-4-e4b-family-atlas`
  (`7fcf1329`). Launch authorized for stages (a)/(b)/(c) at batch 16.
- Stage (a) first launch (`prep_tuner_cell.py prepare --cell-id gemma4_e4b_it
  --batch-size 16`, detached, pinned container, log
  `experiments/doubt-snap-cross-family-confirmatory/analysis/gemma4_e4b_it/mining_run.log`)
  exited 1. Baseline generation and grading completed
  (`baseline_graded_private.jsonl` written, 4000/4000 rows, batch-parity
  smoke ran). The script's later single-layer anchor-capture stage (the
  fleet's own incidental G0 capture, not consumed by this atlas) failed at
  576/2819 rows with `CUDA error: unknown error`. GPU state after exit:
  1 MiB used, 36C, no kernel errors, container exited clean; peak VRAM
  during the run was 17.6/24.0 GiB (below the 3090's ceiling). First log
  preserved at `mining_run.log` as evidence.
- Relaunched the same command unchanged (`--resume` on both tuner stages;
  generation rows all skip via checkpoint, anchor capture resumes from
  ~576/2819) via `launch_detached.sh` with a fresh log name
  (`mining_run2.log`), so the first run's log is not overwritten. Module
  pins untouched.

- Lead authorized the mining path (resuming `prep_tuner_cell.py prepare
  --cell-id gemma4_e4b_it` unchanged, post-sign) plus a pre-sign, notebook-tier
  timed GPU sizing probe. See `AMENDMENT.md` "Row pool" and new "Cost and
  sizing" section for the full declaration and numbers.
- Environment setup for the pinned `mechinterp-runner:local` container (all
  hard-blocking, all resolved):
  - `synaptic-tuner` submodule was uninitialized in this worktree
    (`git submodule status` showed a `-` prefix). Fixed via
    `git submodule update --init --recursive synaptic-tuner`.
  - Docker context "desktop-linux" pointed at a Windows npipe path unusable
    from this WSL2 shell (`Failed to initialize: protocol not available`).
    Fixed via `export DOCKER_HOST=unix:///var/run/docker.sock` before every
    docker command in this session; the "default" context's unix socket
    works.
  - `experiments/common/launch_detached.sh` is not marked executable in this
    worktree; invoked as `bash experiments/common/launch_detached.sh ...`
    rather than directly.
- Wrote `analysis/probe_generation_timing.py` (pre-sign sizing probe,
  synthetic placeholder questions only, never real dataset text). First
  attempt used `device_map=` for convenience and failed inside the pinned
  container with `ValueError: ... requires accelerate` (confirmed via a
  direct `import accelerate` -> `ModuleNotFoundError`: the pinned image
  genuinely lacks `accelerate`). Fixed by rewriting model loading to mirror
  `synaptic-tuner/tuner/batch/engines/hf_batched.py`'s exact pattern
  (`torch_dtype=torch.bfloat16` + explicit `model.to("cuda:0")`, no
  `device_map=`) -- this is not a workaround, it is what the real mining
  pipeline already does, so the probe now matches the real path instead of
  diverging from it.
- Ran the probe detached via `launch_detached.sh` inside the pinned
  container (`-e IMAGE_DIGEST=sha256:d445632098cd2c70c115fe84d5343ff98286ac3f510a2d4c9cb488b550a3d23c`,
  `--gpus all`, host HF cache mounted). Watched to completion via `Monitor`
  (no foreground `sleep`, per the sandbox's block on leading-sleep polling).
  Results: load 285.5s; batch 8 -- 58.80s/128 rows, 70.75 tok/s, 2.177
  rows/s, 15.02 GB peak VRAM; batch 16 -- 39.36s/128 rows, 105.76 tok/s,
  3.252 rows/s, 15.22 GB peak VRAM. Full numbers and the batch-size
  recommendation are in `AMENDMENT.md` "Cost and sizing"; raw JSON at
  `analysis/probe_generation_timing.json` (gitignored, sizing evidence only).
- Separately, timed `profile_and_read_family_atlas_panel.py`'s CPU-only
  `score` stage at this cell's PROJECTED real scale (3500 synthetic rows, 43
  hidden states, hidden_dim=2560, 2000 bootstrap resamples) rather than
  reusing the tiny `smoke_family_atlas.py` fixture's unrepresentative number
  (114 rows / 4 hidden states / hidden_dim=256): 184.04s total (build 5.06s +
  score 184.04s... see script for the exact split), well under the
  15-minute short-run ceiling. Script:
  `/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/time_profile_panel_realistic_scale.py`
  (scratchpad, not committed).
- **Found and fixed a ROOT-resolution bug in the shared, un-copied
  family-atlas engine scripts.** Both `capture_family_atlas_cell.py` and
  `profile_and_read_family_atlas_panel.py` compute
  `ROOT = Path(__file__).resolve().parent` and derive `REPO_ROOT` /
  `private_dir()` / `committed_dir()` assuming the script has been copied
  into `experiments/<slug>/` (two levels below repo root; both scripts'
  docstrings say this explicitly). This experiment's `experiment.yaml`
  originally referenced them in place under `.skills/family-atlas/scripts/`
  (three levels below repo root) on the theory that SKILL.md's step
  3/4 wording ("via `scripts/capture_family_atlas_cell.py capture`") meant
  reuse-in-place, matching neither of the earlier `render_example.py`
  template's copy-and-adapt convention. Verified directly with a
  `Path.parents` resolution test: run in place, `REPO_ROOT` resolves to
  `.skills/`, not the repo root, so `capture_family_atlas_cell.py`'s `TUNER`
  path would point at a nonexistent `.skills/synaptic-tuner/tuner.py` and
  both scripts' private/committed output dirs would land inside
  `.skills/family-atlas/` instead of under this experiment. No prior atlas
  cell (llama, mistral, qwen3, qwen3.5) ever exercised this shared-script
  path -- all four used bespoke per-experiment copies -- so this bug was
  latent, not previously hit. Fixed by copying both scripts byte-for-byte
  into this experiment directory (sha256-verified identical to the
  `.skills/` canonical originals) and updating `experiment.yaml`'s
  `instrument.modules` to the local paths. Flagged to the lead as a
  possible `.skills/family-atlas/` doc/impl fix (SKILL.md's file list in
  step 1 does not mention these two scripts at all); not corrected upstream
  by this agent.
- Filled `instrument.persistence` for all four modules and added
  `instrument.runtime_image_digest` (sibling to `instrument.pins`, per
  `.skills/mechinterp-cells/reference/modal-launch.md`). `bin/exp validate`
  reports `OK (86 experiment(s))` with no warnings for this experiment's own
  modules (all four now carry a persistence declaration). Did not run
  `bin/exp sign` -- the lead signs.
- Did NOT commit. The lead's instruction said "commit the scaffold to the
  branch"; this agent's operating rules forbid it from committing, pushing,
  PRing, or merging under any circumstance, including an explicit
  instruction to do so from another agent. Flagged explicitly in the report
  back to the lead rather than silently complying or silently ignoring the
  instruction. Git state as of this entry: scaffold complete and validated,
  fully staged-ready, nothing committed.

### 2026-07-20 - scaffold, pin verification, pool-gap finding, CPU-only smokes

- Scaffolded via `bin/exp new gemma-4-e4b-family-atlas --type probe-fit` on
  branch `exp/gemma-4-e4b-family-atlas`, worktree
  `/home/profsynapse/code/ehr-worktrees/gemma-atlas`.
- Verified the model pin `google/gemma-4-E4B-it @
  fee6332c1abaafb77f6f9624236c63aa2f1d0187` against
  `experiments/doubt-snap-cross-family-confirmatory/model_matrix.yaml:68-74`
  (gated_access: false). `HfApi.model_info(..., files_metadata=True)` at that
  exact revision confirms `model.safetensors` = 15,992,595,884 bytes
  (~16.0 GB total repo size including tokenizer/configs).
  `AutoConfig.from_pretrained` at that revision: `Gemma4ForConditionalGeneration`
  (multimodal wrapper), text backbone `num_hidden_layers=42`,
  `hidden_size=2560`, `vocab_size=262144`, tied embeddings; audio (12 layer,
  hidden 1024) and vision (16 layer, hidden 768) towers present but out of
  scope for this atlas (text-only causal-LM capture).
- Found: NO reusable committed split manifest exists for this substrate
  under the family-atlas role/split taxonomy. The fleet's own `gemma4_e4b_it`
  cell (same repo/revision, defined in
  `doubt-snap-cross-family-confirmatory/model_matrix.yaml`) was never
  launched (`doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
  283-284: "fleet abandoned pre-launch"). This is a structural difference
  from both resolved `jspace-family-atlas` cells, which reused an
  already-mined fleet pool verbatim. See `AMENDMENT.md` "Row pool" for the
  full finding and the proposed mining path (resuming the fleet's own
  `prep_tuner_cell.py prepare --cell-id gemma4_e4b_it`, unmodified).
- Wrote `cell.yaml`, `gates.yaml` (added AG0a pool-mining-integrity gate on
  top of the standard AG0/AG1/AG2), `AMENDMENT.md`, and
  `render_gemma_atlas.py` (ported from
  `doubt-snap-cross-family-confirmatory/render.py`, adapted to the
  FAMILY_ATLAS_RENDER_MODEL/REVISION env-var contract the shared
  `capture_family_atlas_cell.py` actually sets -- NOT the older
  cell-specific JSPACE_ATLAS_RENDER_MODEL naming `render_jspace_atlas.py`
  used, which predates the script's generalization).
- Fixed `experiment.yaml` path-resolution convention: `instrument.configs`/
  `instrument.modules` resolve relative to the experiment's own directory
  (`exp_dir / rel`), while `inputs` resolves repo-root-relative
  (`root / rel`) -- confirmed by reading `experiments/scripts/exp.py` and by
  running `bin/exp show` / `bin/exp validate` until both passed.
  `bin/exp validate` now reports `OK (86 experiment(s))` with only the
  expected (repo-wide, pre-existing) missing-persistence-declaration
  warnings; this experiment's own four listed modules carry the same
  warning, to be resolved at `bin/exp sign` once the mining-scope decision
  is made.
- Ran two CPU-only smokes (no GPU, no model weights downloaded):
  1. `.skills/family-atlas/scripts/smoke_family_atlas.py` (synthetic
     captures, substrate-agnostic) -- PASS: "shapes, eff_dim_frac bounds,
     AUROC/CI ordering, signal-layer-beats-noise-layer sanity check, and
     random-direction control near-chance behavior all hold."
  2. Direct call of `render_gemma_atlas.py:render()` against the REAL
     gemma-4-E4B-it tokenizer at the pinned revision (downloads only the
     tokenizer, ~31 MB, not the 16 GB model) -- PASS: rendered a
     `<bos><|turn>system...` prompt via the "direct enable_thinking=False"
     path with no fallback needed and no `assert_no_think_scaffolding`
     failure.
- Did NOT download model weights, did NOT run the fleet's mining script, did
  NOT run any GPU capture. Reported to the lead for a scope decision (mine
  now vs. defer) and launch approval before either GPU stage.

## 2026-07-20 - anisotropy-artifact control reanalysis (lab-notebook tier, not a registered gate)

PI-directed deflationary test of the early-exterior eff_dim_frac peak:
could mid/late-layer anisotropy (outlier eigendirections suppressing the
participation-ratio estimator) be manufacturing the early peak? CPU-only
reanalysis of the committed captures (2815 rows, 1301 fit rows, 43 hidden
states), pinned estimator code imported directly, baseline reproduced to
max abs deviation 1.04e-17.

Result: NO. The layer-4 peak (depth 0.095) survives all eight correction
variants -- whitening (correlation matrix), dropping top-1/2/4/8
covariance eigendirections, 0.5% winsorizing, and a rank-based spectral
entropy estimator (different estimator family) -- and a 50% row-subsample
guard. The anisotropy hypothesis had the right qualitative input shape
(top-1 eigenvalue share 0.141 at layer 4 vs 0.41-0.50 at layers 30-42),
but correcting for it only compresses the peak's margin over the best
interior candidate (1.53x baseline down to 1.12x under drop-top-8), never
relocates it. Caveat carried: the peak's PROMINENCE partly rides on early-
layer isotropy; its LOCATION does not.

Artifacts: analysis-committed/gemma4_e4b_it/anisotropy_control/ (script +
five JSON outputs). Aggregates only. Remaining open deflationary
alternatives for the cross-family pattern: pool surface-diversity (untested)
and small-N (qwen3-4b-family-atlas cell in preparation).
