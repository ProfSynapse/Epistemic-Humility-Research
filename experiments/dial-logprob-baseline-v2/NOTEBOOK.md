# Dial token-logprob baseline, clean redo (generation-time token-ID cache) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)
- 2026-08-11: SCAFFOLD + HARNESS BUILD (draft, worktree
  `/home/profsynapse/code/ehr-worktrees/lp-baseline-v2`, branch
  `exp/dial-logprob-baseline-v2`), delegated build task. Not signed, not
  launched, nothing committed by this task.
  - Scaffolded via `bin/exp new dial-logprob-baseline-v2 --type probe-fit`.
  - `AMENDMENT.md`, `cell.yaml`, `gates.yaml`, `experiment.yaml` populated from
    `docs/preparation/amendment-draft-dial-logprob-baseline-v2.md` (copied into
    this worktree's `docs/preparation/` so the PR carries it), with the PI's
    2026-08-11 ruling adopting the draft's sec.7 recommendation: the prediction
    is framed as a confirmation cell (v1's descriptive read holds at exact
    precision), not a fresh blind guess, plus a new confirmation_falsifier in
    `gates.yaml` alongside the verbatim dial-novelty falsifier.
  - `lp_v2_harness.py` built: `run_arm` (regenerate-and-capture, incremental
    resumable persistence), `score_arm` (CPU-only dial refit + AUROC + paired
    bootstrap margin, reusing `oof_probe`/`load_position_layers`/
    `paired_bootstrap_delta` from `amendment_s_correctness_probe_score.py`
    UNCHANGED), `dry_run` (real-input existence check), `main` (CLI: `--dry-run`,
    `--arm`, `--timing-smoke`). System prompts imported by reference from the
    S/T extractor modules (`amendment_s_correctness_probe_extract.SYSTEM_PROMPT`,
    `amendment_t_correctness_readout_deployment_extract.SYSTEM_PROMPT`), never
    retyped, so the render cannot silently drift from what the cached rows were
    produced under.
  - `RunLog` (synaptic-tuner `shared/utilities/run_log.py`) checked and found
    UNAVAILABLE on the current submodule pin (branch `feature/runlog`, HEAD here
    is `04dfe98f` on `main`, no `run_log.py` on disk). Per the binding
    instruction not to touch `synaptic-tuner/`, did not check out a different
    branch; `run_arm` reimplements the same append+flush+resume contract
    locally (own JSONL, own done-set scan on start) instead.
  - **Worktree data-visibility gotcha, worth recording for future worktree
    builds:** `archive/experiment/phase1-data/` and `scratch/` are gitignored
    local data (`.gitignore:93` for the former); a fresh `git worktree` gets its
    own working directory and does NOT inherit gitignored content from the
    canonical checkout or other worktrees. Both are absent from this worktree.
    sha256 pins (below) were computed against the canonical checkout
    `/home/profsynapse/code/Epistemic-Humility-Research` where the real files
    physically live, since that is where they will actually be read from at
    real-run time. For a real existence-check demonstration (not just a
    theoretical one), symlinked `archive/experiment/phase1-data/` and
    `scratch/` from the canonical checkout into this worktree (gitignored on
    both sides, no git state touched, safely removable) so `--dry-run` could be
    exercised against the REAL data paths end-to-end, not only against the
    already-known-to-fail case.
  - sha256 pins computed 2026-08-11 for the frozen inputs named in the design
    draft sec.5 (computed against the canonical checkout; ready for `bin/exp
    sign`, which the lead runs -- `instrument.pins` in `experiment.yaml` is
    left empty, as scaffolded, since signing is not this task's job):
    - `archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2/rows.jsonl`
      sha256 `b8ced7c1adbb43185e8b4667944d3f113192d6923fd044d2e5bb05fd01aca1fb`
      (1836 lines)
    - `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/rows.jsonl`
      sha256 `b8810be3bf9eac58a643f936280e8686636d6d04da4077a21fc29f94ba8436d3`
      (8548 lines, all attempts; harness filters to the 1488 answered rows)
    - S checkpoint: `unsloth/Qwen3-4B-bnb-4bit` is an HF hub id, not a local
      path (no local sha256; pinned by hub id + `torch_dtype=bfloat16` load,
      "as-cached" per v1's own checkpoint field).
    - T base (merged-16bit), representative files:
      `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit/config.json`
      sha256 `c0597b0790b79d72e767442216e7542d23e4d251e27780471f05c4fd882a13f2`;
      `.../merged-16bit/model.safetensors.index.json` sha256
      `e36bba5af4706cfd22ecf7eedb5fd8f4d2559b92f2414b932651b9ed6495921a`
      (index + config hashed as an identity fingerprint rather than the
      multi-GB sharded weights themselves).
    - T adapter (LoRA, small enough to hash in full):
      `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model/adapter_config.json`
      sha256 `e86ddf492103b0308570e0b6199143ae42cda5bbf6489dee2810888d7316d27a`;
      `.../final_model/adapter_model.safetensors` (253M) sha256
      `9dc02eefcd3c510af376465e90d53ed6475556ac9189d1d7be478fdaf83622ca`.
    - Dial refit module (unchanged, reused):
      `experiments/common/readouts/amendment_s_correctness_probe_score.py`
      sha256 `bce50f56a07ee46295cc1ad9eabae098999db22d694a1d92b317932c0ccf3ba6`
      (verified byte-identical between the canonical checkout and this
      worktree, since it is git-tracked at the same commit).
  - Smoke (`test_lp_v2_smoke.py`) and dry-run results: see this task's report
    to the lead (not duplicated here to avoid a second source of truth; rerun
    `python3 -m pytest experiments/dial-logprob-baseline-v2/test_lp_v2_smoke.py -v`
    and `python3 experiments/dial-logprob-baseline-v2/lp_v2_harness.py --dry-run`
    to reproduce).
