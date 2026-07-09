# Diagnostics bundle — launch plan (DO NOT LAUNCH; orchestrator launches)

Four lab-notebook-tier (tier L) GPU cells from the TODO.md prioritized backlog,
prepared as committable wrapper scripts. No amendments, no gates. Prepared on
branch `lab-diagnostics-bundle` off `origin/main`
(pinned commit is this branch's HEAD once pushed — use the FULL 40-char SHA in
`runpod_run_job.py --commit`).

The RunPod launcher is the Synaptic-Tuner submodule script
`synaptic-tuner/.skills/fine-tuning/scripts/runpod_run_job.py` (clones the repo
at a pinned commit, runs a wrapper in a pinned image, terminates in `finally`).
It defaults `HF_HUB_DISABLE_XET=1`. Export the token first, never print it:

    export HF_TOKEN=$(sed -n 's/^HF_TOKEN=//p' \
        /home/profsynapse/code/Epistemic-Humility-Research/.env | tr -d '"\r\n')

Staging (upload target for all cells): `professorsynapse/eh-al-prep-staging`
(AL's private dataset repo; the general staging pattern is fine to reuse — each
cell gets its own `RUN_TAG` namespace, so nothing collides).

Checkpoint provenance (published to HF; verified in TODO + AL session 0038):

| stage       | base_model                                                | adapter                                                        | rev |
|-------------|-----------------------------------------------------------|---------------------------------------------------------------|-----|
| raw base    | `unsloth/Qwen3-4B-bnb-4bit`                               | (none)                                                        | —   |
| clean-SFT   | `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`| (none — merged)                                              | —   |
| GRPO-v2     | `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`| `professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora`     | main|
| PAR/TRUE    | `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`| `professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora` | `7e31d3cf62395275d4ba3d1d9ec8f95287188805` |

GRPO-v2 == the plain-GRPO adapter over clean-SFT (the DEPLOYED checkpoint; the
"v2" name is historical — confirmed in archive/notes/experiments/two-signal-readout.md).

---

## READ FIRST — RunPod community RTX-3090 lane is unproven (session 0038)

AL prep tried this exact lane on 2026-07-05 and **every 3090 community pod
failed to boot**: pods stall at `desiredStatus=RUNNING, uptime=0` pulling the
~20 GB pinned Unsloth image, and the failure survived every isolation probe
(community pool, image pull, entrypoint, fast-exit, even SECURE cloud). Two
launcher bugs were found and **patched in a scratchpad copy that has NOT yet
been merged into the tuner skill**: (1) no `min_download`/`min_upload` floors,
so slow-network hosts win the bid; (2) `booted` was set on an empty-uptime
runtime dict, disarming the 600 s boot timeout. The AL path was reassigned to
LOCAL GPU.

Implication for this bundle: **do not assume the RunPod lane works.** Before
spending the ~$2 budget, either (a) confirm the patched launcher (REST rewrite +
`min_download 700 / min_upload 200`, `booted` requires `uptimeInSeconds > 0`,
900 s boot timeout) has landed in
`synaptic-tuner/.skills/fine-tuning/scripts/runpod_run_job.py`, or (b) run these
cells on the LOCAL 3090, for which every wrapper works unchanged (the wrappers
only assume `nvidia-smi` + the repo checkout + `HF_TOKEN`). Cells 1, 2 have a
natural local home anyway (see below).

---

## Cell readiness

### Cell 1 — item 11 GPU half (batched-steering equivalence). READY.
- Wrapper: `runpod_diag_gpu_equiv.sh`. Script: existing
  `steering/gpu_equivalence_cell.py` (unchanged; the wrapper passes its required
  `--i-know-this-runs-on-gpu` guard flag, which the launch approval satisfies).
- Inputs: the direction JSON is **committed in-repo**
  (`experiments/diag-item11-batched-steering-equivalence/artifacts/directions/qwen3-4b-grpo-v2/direction_caution.json`,
  `best_layer=34`), so no
  pool fetch — only the checkpoint is pulled. It is a pure batched-vs-loop
  numeric self-check at one layer on ~5 fixed prompts.
- Checkpoint: pass a merged 4B-Qwen checkpoint of matching layer count. The
  migrated caution direction targets the clean-SFT -> GRPO-v2 lineage at
  `best_layer=34`; the parity result is architecture-numeric, independent of
  the direction's semantic meaning.
- Un-gates: AK Stage 2 + backlog items 3/5.
- Runtime (3090): model load ~2-3 min + ~5 prompts x 2 passes ≈ **< 5 min
  compute**; dominated by the checkpoint download (a few min). Budget ~10 min.
- CPU-side after: none — the cell prints (and the wrapper uploads) the per-row
  and OVERALL max-abs divergence; PASS = divergence at the bf16 batched-vs-
  unbatched floor (<< the steering magnitude).

### Cell 2 — item 21 sentence-panel neutral control. READY (LOCAL lane).
- Script: new `amendment_ag_neutral_panel.py` (generalizes the PR #166
  single-sentence `amendment_ag_neutral_control.py` to a locked 6-sentence
  panel; reuses its analysis primitives verbatim). No RunPod wrapper — see below.
- Panel: 6 surface-varied, epistemically-inert sentences (n1 = the PR #166
  sentence, kept as anchor). Extraction: one pre-gen anchor forward per
  (sentence, AE-pool row), all layers, byte-identical tensor contract to
  `af_base_pregen`.
- **Why LOCAL, not RunPod:** the analysis inputs — `af_base_pregen`,
  `ag_primed_pregen/{high,low}`, the AE census rows — are untracked analysis
  outputs that live ONLY in the canonical checkout / AG worktree; they are NOT
  on git or HF, so a fresh pod cannot fetch them. The AE pool likewise is local.
  The extraction is a small forward-only pass (6 x 600 rows). Run extraction +
  analysis together on the local 3090.
- Runtime (3090): 3600 anchor forwards ≈ **~20-30 min** + a few min CPU analysis.
- Launch (local, from the canonical checkout with the worktree's script on path):

      cd /home/profsynapse/code/ehr-worktrees/lab-diagnostics-bundle
      python experiment/phase1/probe/amendment_ag_neutral_panel.py --full

  (smoke first without `--full`: 6 rows x panel, no analysis.) Outputs go to
  `analysis/ag_neutral_panel_pregen/` (untracked). If the AE pool / AF tensors
  are not under the paths the reused module expects, point `--pool` at the AE
  pool and confirm `AF_PREGEN_DIR` in `amendment_ag_neutral_control.py` resolves
  in this checkout before the full run.

### Cell 3 — item 20 generation-time displacement geometry (also AK Stage 1 read). READY (scoped).
- Wrapper: `runpod_diag_gentime_positions.sh`. Script: new
  `amendment_ak_gentime_positions_extract.py`.
- Method: greedy batch-1 generation, then the **Amendment S/R faithful
  re-forward** of `[prompt + answer]` capturing all-layer states at 6 positions
  (anchor / first_vis / mid25 / mid50 / mid75 / answer_end). rows.jsonl carries
  label/refused/answered/confab/positions; **no question text, no answer_text by
  default** (NO-LICENSE safe — `--keep-answer-text` only on a confirmed-licensed
  pool).
- **Scoping decision (important):** AK-2 (task #76) specifies TOKEN-GRANULAR
  decode-step capture. This cell instead uses the validated re-forward at a
  COARSE 6-position sweep. That is the right instrument for item 20 (does the
  92-99% off-plane geometry hold mid-generation) and gives AK Stage 1 its
  position curve at 6 points; it is NOT the full per-token AK-2 runner and does
  not reproduce KV-cached per-decode-step activations. If AK Stage 1 needs the
  full token-by-token curve, that is separate, larger work (the AK-1..AK-4 task
  line) — flag to the orchestrator rather than treating this cell as AK-2 done.
- Checkpoint: the AF/AG prime surface = deployed clean-SFT→GRPO-v2 (base +
  `-clean-sft-grpo-seed1-lora`). Axes refit per checkpoint downstream (Amendment T).
- Pool: needs a ~300-600 row known/unknown pool in the staging repo. The AL A0
  pool (`pools/a0_pool_v21_questions.jsonl`, 1,662 rows KUQ/SelfAware/TriviaQA/
  PopQA) works if capped via `[limit]`; confirm the exact staging path with the
  orchestrator before launch (see the OPEN ITEM below).
- Runtime (3090): 600 rows x (1 greedy gen ≤96 tok + 1 re-forward) ≈
  **~1.5-2.5 h** (generation dominates; abstention-trained checkpoint refuses a
  lot, so many rows skip the re-forward).
- CPU-side after: run the `analyze_displacement.py`-style decomposition
  (`analysis/mi_exploration_20260703/mi-prime-direction/`) onto the doubt/
  caution axes at each of the 6 positions; compare off-plane variance fraction
  vs the anchor.

### Cell 4 — item 9 cross-checkpoint caution assembly timeline. READY.
- Wrapper: `runpod_diag_caution_timeline.sh` (ONE `--stage extract` pass per
  checkpoint; a pod chains the 3-4 stages). Script: existing
  `amendment_ai_verdict_extract_gen.py --stage extract --surface union` with the
  full L0..L36 layer list.
- Checkpoints (each a separate invocation with its own `stage_tag`): raw,
  clean-sft, grpo-v2, par-true. All published to HF (table above).
- Pool: one FIXED pool for all stages (reuse the AL A0 pool or any known/unknown
  pool in the staging repo; confirm the path — same OPEN ITEM as cell 3).
- Runtime (3090): pre-gen anchor extraction, all layers, ~1,662 rows/stage ≈
  **~25-40 min/stage** → **~1.5-2.5 h for all 4 stages** chained on one pod.
- CPU-side after: fit the caution direction (refused-vs-answered) + doubt axis
  per stage on the fixed pool; plot AUROC + direction cosine vs training stage.

---

## OPEN ITEM before launching cells 3 & 4

Cells 3 & 4 need a known/unknown QA pool present IN the staging dataset repo at a
known path. The AL A0 pool (`pools/a0_pool_v21_questions.jsonl`) exists in
`professorsynapse/eh-al-prep-staging` and fits (row schema: `row_key`,
`question`, `label`/`gold_label`, `source`). **Confirm this path is still in the
staging repo (it is external state) before launch**, or stage a fresh pool. If
the pool is not present, cells 3 & 4 are BLOCKED on pool staging (not on code).

---

## Pod grouping and cost

The four cells split cleanly by lane:

- **Cell 2 → LOCAL only** (analysis inputs are local-only). Not a pod.
- **Cell 1 → LOCAL preferred** (tiny; < 5 min compute; a whole pod's setup
  overhead dwarfs it). Runnable on a pod if desired but wasteful.
- **Cells 3 & 4 → ONE RunPod pod, chained** (both are HF-fetchable extraction
  cells on the same staging repo; grouping amortizes the ~20 GB image pull +
  checkpoint downloads across both). Cell 4's 4 stages + cell 3 ≈ **~3.5-5 GPU-h
  on one 3090**.

**Recommended: one pod running cells 4 (×4 stages) then 3**, ~3.5-5 GPU-h. At
RTX-3090 community ~$0.20-0.34/hr that is **~$0.70-1.70**, inside the ~$2 budget.
Cells 1 & 2 run locally at no pod cost. **BUT** the 3090 boot-failure caveat
above applies — verify the patched launcher first or run everything local.

Total estimated GPU time if all four run: cell 1 ~10 min + cell 2 ~30 min
(local) + cell 3 ~2 h + cell 4 ~2 h (pod) ≈ **~4.5-5 GPU-h**; pod cost
**~$0.70-1.70**.

---

## Exact launch commands (placeholders only for the env token)

Set the token once (never printed):

    export HF_TOKEN=$(sed -n 's/^HF_TOKEN=//p' \
        /home/profsynapse/code/Epistemic-Humility-Research/.env | tr -d '"\r\n')
    LAUNCHER=synaptic-tuner/.skills/fine-tuning/scripts/runpod_run_job.py
    REPO=https://github.com/ProfSynapse/Epistemic-Humility-Research.git
    SHA=<full-40-char-sha of this branch's HEAD after push>
    STAGING=professorsynapse/eh-al-prep-staging
    POOL=pools/a0_pool_v21_questions.jsonl   # confirm present in STAGING first

### Recommended grouped pod (cells 4 then 3), one wrapper that chains — OR run each wrapper as its own pod.
Because `runpod_run_job.py` runs ONE `--wrapper`, chaining multiple cells on one
pod needs a tiny chain wrapper OR separate `--dry-run`→launch calls per stage.
Simplest is one pod PER wrapper invocation; the per-stage commands below are
each a full pod. To truly co-locate, add a one-line chain wrapper later — not
minted here to avoid an untested orchestration script.

Cell 4 (repeat per stage — raw / clean-sft / grpo-v2 / par-true):

    # raw base (no adapter)
    python $LAUNCHER --run-tag diag-item9-raw-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_caution_timeline.sh \
      --wrapper-args "$STAGING unsloth/Qwen3-4B-bnb-4bit - - $POOL raw diag-item9-raw-r1 36" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 90 --dry-run

    # clean-SFT (merged; no adapter)
    python $LAUNCHER --run-tag diag-item9-cleansft-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_caution_timeline.sh \
      --wrapper-args "$STAGING professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit - - $POOL cleansft diag-item9-cleansft-r1 36" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 90 --dry-run

    # GRPO-v2 (deployed)
    python $LAUNCHER --run-tag diag-item9-grpov2-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_caution_timeline.sh \
      --wrapper-args "$STAGING professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora main $POOL grpov2 diag-item9-grpov2-r1 36" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 90 --dry-run

    # PAR/TRUE
    python $LAUNCHER --run-tag diag-item9-partrue-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_caution_timeline.sh \
      --wrapper-args "$STAGING professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora 7e31d3cf62395275d4ba3d1d9ec8f95287188805 $POOL partrue diag-item9-partrue-r1 36" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 90 --dry-run

Cell 3 (generation-time positions, deployed checkpoint):

    python $LAUNCHER --run-tag diag-item20-gentime-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_gentime_positions.sh \
      --wrapper-args "$STAGING professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora main $POOL diag-item20-gentime-r1 600" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 180 --dry-run

Cell 1 (LOCAL preferred; RunPod form if wanted):

    # LOCAL (recommended):
    python experiment/phase1/probe/steering/gpu_equivalence_cell.py \
      --model professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit \
      --direction experiments/diag-item11-batched-steering-equivalence/artifacts/directions/qwen3-4b-grpo-v2/direction_caution.json \
      --device cuda --dtype bfloat16 --i-know-this-runs-on-gpu

    # RunPod form:
    python $LAUNCHER --run-tag diag-item11-gpuequiv-r1 \
      --repo-url $REPO --commit $SHA \
      --wrapper experiment/phase1/probe/cloud/runpod_diag_gpu_equiv.sh \
      --wrapper-args "$STAGING professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit experiments/diag-item11-batched-steering-equivalence/artifacts/directions/qwen3-4b-grpo-v2/direction_caution.json diag-item11-gpuequiv-r1" \
      --gpu "NVIDIA GeForce RTX 3090" --cloud-type COMMUNITY --timeout-min 30 --dry-run

Cell 2 (LOCAL only):

    python experiment/phase1/probe/amendment_ag_neutral_panel.py --full

Every RunPod command shows `--dry-run`; the orchestrator removes it to launch
after reviewing the pod spec. Keep `terminate-in-finally` behavior (built into
the launcher). Redact `hf_`/`rpa_` tokens in any pasted output.
