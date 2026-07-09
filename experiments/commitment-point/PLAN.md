# Amendment AK Stage 1 - Modal launch plan (prep only, NOT launched)

This note is the one-page runbook for launching AK Stage 1 (commitment-point
position-sweep extraction) on the Modal lane. Everything here is prepared; no
paid compute has run. Launch is gated on the AK doc preconditions plus explicit
user GPU approval and Modal being proven by the in-flight A0 v2 parity run.

Authority for design is `experiments/commitment-point/AMENDMENT.md`.
Where this note and the doc disagree, the doc wins.

## What the AK doc specifies for Stage 1 (§3.1, §4)

- **Surface / pool**: the AH stage-0 question pool rows that produced the arm-B
  matched set = the unanswerable-clean A0 population. Concretely 1,338 rows
  (`gold_class == 'unanswerable'`, not degenerate, not ungradeable) from
  `analysis/ah_main/gen_A0/rows.jsonl`; 309 confab / 1,029 refuse. The M=328
  matched set (164/164) and the ~50-row pilot are derived from this pool by the
  CPU scorer, so the pool is the single source.
- **Checkpoints**: BOTH the raw instruct base (arm-B's native surface) and
  clean-SFT->GRPO-v2 (deployed). **AK-G1 gates on grpo-v2**; the raw-base curve
  is reported descriptively.
- **Positions per row**: the anchor (`prompt_len-1`), each thinking-segment
  boundary, the first visible token (`prompt_len`), and every k-th answer token
  through answer end.
- **Layers / readouts**: per-position readouts of the frozen doubt trunk, frozen
  caution axis, arm-B commitment direction, and the veto/correctness axis. The
  veto/correctness axis is refit per position out-of-fold (item-31: frozen
  correctness axes do not transport across positions); each per-position refit
  carries the AJ equal-rank random-direction control.
- **Pilot**: the first ~50 rows of the sweep are the AK-G2 pilot; they lock the
  G2 floor via the §4 formula (floor = 3 x SE of the slope contrast on the
  pilot) and are then EXCLUDED from the G2 test set. The floor is computed and
  committed to the run record BEFORE the full-run G2 readout.
- **Gates**: AK-G1 veto AUROC(answer-end) - AUROC(first-visible) >= +0.10 on
  grpo-v2. AK-G2 three-way fork, PASS = slope contrast clears the pilot floor
  AND permutation p < 0.01. AK-G3 is Stage 2 (steering), not this run.

## Interpretation notes carried into the build (flag for the user)

1. **Thinking segments.** The frozen serving surface all four axes were fit on
   is `enable_thinking=False` (the AF/AG/AH/AI baseline-unprimed render). Under
   that surface there is normally NO `<think>` segment, so "each thinking-segment
   boundary" typically yields zero extra positions. The runner still captures a
   `think_close{j}` position for every `</think>` token if one is emitted, so it
   is robust to either render mode without changing the frozen surface. If the
   user wants thinking-on trajectories that is a DIFFERENT surface and should be
   a separate, explicitly-approved cell (the axes would need refitting there).
2. **GPU job writes states only.** All axis fitting / projection / AUROC /
   slope-contrast / gate logic is CPU-side and post hoc (mirrors the AI
   GPU-extract + CPU-score split). The GPU runner is therefore
   checkpoint-agnostic: raw-base and grpo-v2 run the same code with different
   `--base-model` / `--adapter-repo`.
3. **Generation stays batch-1 greedy.** The captured positions must be
   decode-identical to the arm-B / AH generations, so generation is batch-1
   greedy. Batching applies only to the state-capture forward pass; the frozen
   generation batch size (1) is recorded in every manifest.

## What was built (this branch)

- `archive/experiment/phase1/probe/amendments/amendment_ak_build_pool.py` - CPU pool builder. Emits
  `analysis/ak_stage1/ak_stage1_pool.jsonl` (1,338 rows, verified) with
  row_key/question/label/gold_class/confab_on_unanswerable/caution_dist_z/
  category_canon/source. Question text is included ONLY for the private staging
  upload (GPU render needs it); extraction outputs never write it back.
- `archive/experiment/phase1/probe/amendments/amendment_ak_stage1_extract.py` - GPU runner. Greedy
  batch-1 generation then a single full-sequence forward with
  `output_hidden_states=True`, slicing anchor / think-close / first-visible /
  every-stride-th / answer-end at the AK layer band (L16,L20,L24,L28,L34,
  configurable). Per-row `<safe_key>.safetensors` with keys `<L>@<pos_name>`;
  rows.jsonl carries the position index map + labels + config_sha; native resume
  guarded by config_sha (AI pattern). NO question/answer text in outputs.
- `experiment/phase1/probe/cloud/modal_ak_stage1.py` - Modal app cloned from the
  AL v2 crash-proof skeleton (detached, Volume checkpoint daemon @120s,
  retries=3 with restore-before-start, DONE marker, staging upload). One stage;
  parameterized by `--checkpoint raw-base|grpo-v2`. Runs a numerics-smoke
  pre-stage (`--limit 20`) and asserts the determinism spot-check passed before
  the full pool.
- `archive/experiment/phase1/probe/amendments/tests/test_ak_stage1_extract.py` - CPU smoke, 8
  tests GREEN: position selection, tiny-fake-model capture, the
  batch-1-vs-batch-N token-level agreement contract, and the pool-builder
  round-trip.

## Numerics smoke (batched-generation reference)

AK Stage 1 is a new generation surface. Generation is batch-1 greedy (frozen and
recorded), so the batched-generation concern reduces to the state-capture
forward pass. Coverage:

- **Unit (CPU, GREEN now)**: `test_batch1_vs_batchN_token_level_agreement`
  proves batch-1 vs left-padded batched capture agree bitwise on the fake model.
- **GPU pre-stage (in the Modal wrapper)**: the runner runs at `--limit 20`
  first; the wrapper asserts `determinism_spot_check.passed` on real GPU states
  before the full pool. The frozen generation batch size (1) is written to the
  manifest.

If a future variant batches the capture forward, run the mandated bisect-down
(12 -> 8 -> 4 -> 2 -> 1) on captured anchor/first-visible states and freeze the
largest batch whose max abs diff vs batch-1 is within tol; record it in the
manifest. Not needed at batch-1.

## Cost / runtime estimate (per checkpoint)

Grounded on the AH main generation record: 1,662 rows in ~2,929 s total on the
local RTX 3090 (batch-1 greedy, comparable max_new_tokens) ~= 1.76 s/row.

- Generation: 1,338 rows x ~1.76 s ~= 2,360 s.
- Capture forward (one full-sequence forward per row, ~150-250 tokens, cheaper
  than the 96-token autoregressive decode): ~+0.3-0.5 s/row ~= +400-670 s.
- Model load + 20-row smoke + upload: ~5-8 min.
- **Per checkpoint: ~0.9-1.3 GPU-hours on A10G.** Two checkpoints:
  **~1.8-2.6 GPU-hours total.**
- A10G on Modal is ~US$1.10/hr => **~US$1-1.5 per checkpoint, ~US$2-3 total.**
  Well within a single A10G session; A10G is sufficient (states are float32 cpu,
  no large-VRAM tensors) so no A100 is justified.

## Cross-check surface (separate run, do NOT fold in)

The lab-diagnostics-bundle branch (commit eb102f7b) ships a SEPARATE script,
`amendment_ak_gentime_positions_extract.py`, that does a COARSE 6-position
re-forward sweep (anchor / first_vis / mid25 / mid50 / mid75 / answer_end) via
the Amendment S/R faithful re-forward, launched on RunPod as run-tag
`diag-item20-gentime-r1` (600 rows, deployed grpo-v2 checkpoint) for backlog
item 20 (displacement geometry). It is NOT the AK-2 token-granular runner and
does NOT replace this Stage 1 work; AK Stage 1 stays token-granular per the AK
doc. Its output lands in the SAME staging repo (`eh-al-prep-staging`, under
`diag-item20-gentime-r1`), so mind the run-tag distinction: AK Stage 1 uses
`ak-stage1-<checkpoint>-r1`. The coarse sweep is a useful cross-check surface for
the AK position curve (its 6 coarse positions should track the AK curve at the
shared anchor / first-visible / answer-end anchors), not an input to the gates.

## Pilot-first requirement (LOCKED, do not skip)

The AK-G2 floor is pilot-locked. Sequence:

1. Launch the full Stage 1 extraction (the pilot rows are the first ~50 rows of
   the same pool; the extraction writes states for all rows).
2. CPU scorer computes the pilot slope-contrast SE on the first ~50 rows, sets
   floor = 3 x SE, and COMMITS it to the run record BEFORE reading G2 on the
   held-out remainder. Pilot rows are then excluded from the G2 test set.

The extraction does not need a separate pilot job (states for the pilot rows are
a subset of the full output), but the SCORER must lock the floor before the
full-run G2 readout. This is the "pilot MUST run before the main cell" contract
for the gate: it is a computation on the pilot subset, committed first.

## Exact launch commands (AWAITING APPROVAL - do not run without user go)

Preconditions before either command:
- Modal proven: A0 v2 DONE marker present in the `eh-al-true-a0` Volume ckpt AND
  staging artifacts verified (see "Modal proven" below).
- `export HF_TOKEN=$(sed -n 's/^HF_TOKEN=//p' \
  /home/profsynapse/code/Epistemic-Humility-Research/.env | tr -d '"\r\n')`
- Build + upload the pool to the private staging repo:
  ```bash
  cd /home/profsynapse/code/ehr-worktrees/amendment-ak-commitment-point/experiment/phase1/probe
  python3 amendment_ak_build_pool.py
  python3 cloud/upload_result.py --repo professorsynapse/eh-al-prep-staging \
    --path-prefix pools \
    --file /home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/analysis/ak_stage1/ak_stage1_pool.jsonl
  ```
- `REPO_COMMIT` in `modal_ak_stage1.py` is pinned to `ac94b70c` (the commit that
  fills the grpo-v2 provenance). Re-pin only if the branch moves before launch.
  Both arms need only on-branch files (runner + pool builder), which this commit
  carries.

BOTH arms are now unblocked (grpo-v2 provenance filled; see below). Remaining
launch gates are identical for both: pool upload above + Modal proven + explicit
user GPU approval.

raw-base arm:
```bash
cd /home/profsynapse/code/ehr-worktrees/amendment-ak-commitment-point/experiment/phase1/probe/cloud
modal run --detach modal_ak_stage1.py --checkpoint raw-base
```

grpo-v2 arm (AK-G1 gate surface):
```bash
modal run --detach modal_ak_stage1.py --checkpoint grpo-v2
```

## "Modal proven" means

- The in-flight `eh-al-true-a0` A0 v2 run wrote its `DONE` marker into the
  Volume checkpoint (`{VOL_MOUNT}/ckpt/al-prep-true-a0-modal/DONE`), AND
- its staging artifacts (gen rows.jsonl + extract tarball under
  `al-prep-true-a0-modal/`) are present and non-empty in
  `professorsynapse/eh-al-prep-staging`.

Only then is the crash-proof skeleton (Volume daemon + retries + native resume +
DONE marker), which AK reuses verbatim, demonstrated end-to-end.

## Blockers

1. **grpo-v2 checkpoint provenance - RESOLVED 2026-07-05.** The deployed
   clean-SFT->GRPO-v2 seed1 LoRA is staged privately and pinned in
   `modal_ak_stage1.py`:
   - `GRPOV2_ADAPTER_REPO = professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora`
   - `GRPOV2_ADAPTER_REV  = 8914081dfcec4f1f025f2dbe4195d4f7aa8d210e`
   - `GRPOV2_BASE_MODEL   = professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`
     (confirmed: the adapter's training config points at the clean-SFT
     merged-16bit base, which is what that published repo is).
   Uploaded from the canonical local run
   `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/
   20260624_095831/final_model` (the checkpoint the probe configs deploy). The
   refuse-to-launch guard now passes for the grpo-v2 arm (unit-tested in
   `tests/test_ak_stage1_extract.py::test_modal_grpo_v2_provenance_filled`).
   Both arms are unblocked.
2. **REPO_COMMIT pin.** Re-pinned to the commit that fills the grpo-v2 provenance
   (reported to the team lead). Re-pin if the branch moves before launch.
3. **Pool upload.** The pool exists locally; it must be uploaded to the private
   staging repo before launch (command above).
