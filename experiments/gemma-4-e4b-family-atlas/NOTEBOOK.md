# Gemma-4-E4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-20 - mining authorized, pre-sign GPU sizing probe, ROOT-resolution bug fix

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
