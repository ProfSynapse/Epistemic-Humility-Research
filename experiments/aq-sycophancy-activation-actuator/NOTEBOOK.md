# aq-sycophancy-activation-actuator notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 - Modal actuator smoke-gated

- Launched the AQ actuator path on Modal A10G after explicit user approval,
  using official `Qwen/Qwen3-4B` revision
  `1cfa9a7208912126459214e8b04321603b3df60c`, repo commit `440b88ab6`,
  run tag `aq-sycophancy-actuator-r2`, app
  `ap-Gk0B98l6fRfLflfcF3L2LQ`, and call
  `fc-01KWZ2YK61JG04RER3QJV9ZM9B`.
- The wrapper restored 516 readout files from
  `/ckpt/aq-sycophancy-readout-r2`, restored 0 then 9 actuator checkpoint
  files across retries, re-ran the r2 readout diagnostics, prepared
  `analysis/actuator_rows.jsonl`, and confirmed the A10G GPU
  (`NVIDIA A10G, 23028 MiB`).
- Readout diagnostics reproduced the local r2 numbers before steering:
  selected layer 24, OOF AUROC 0.819 with bootstrap 95% CI
  [0.740, 0.879] at `bootstrap-n=500`; AQ-G1 remains a readout-screen pass
  with the previously recorded hydra/confound caveats.
- `mechinterp steer` did not run full actuator arms. The tuner smoke gate
  failed and refused the full run: `write_ok=true`, `parity_ok=false`,
  `max_write_error=0.01023`, `offtarget_abs_max=7.20052`,
  `gen_stream_fired=null`, `passed=false`.
- Local artifact pulled from the Modal volume:
  `analysis/rows_out.jsonl.smoke_ok.json`. No full `rows_out.jsonl` actuator
  result was produced, and post-steering gates were not scored.
- Interpretation: this is an instrument/smoke isolation failure, not evidence
  for or against AQ-G2/AQ-G3. Do not pass `--force-full-run` on this signed-style
  exploratory cell. Next step is to debug why the `anchor_onward` + `gen_stream`
  erase/write smoke has large off-target drift on Qwen3-4B, likely by trying a
  narrower position/law smoke or a minimal tuner-side readback diagnostic before
  relaunching any full actuator run.

### 2026-07-07 - Modal actuator prep

- Shifted from cross-axis interaction analysis to the AQ actuator path. No live
  actuator run launched in this step.
- Added `prepare_aq_actuator_rows.py`, which enriches the frozen r2
  `row_pool.jsonl` with readout selector metadata and writes
  `analysis/actuator_rows.jsonl` for `mechinterp steer`. Local materialization
  produced 256 rows, 128 probe rows, and 128 rows with selector scores.
- Updated `cell.yaml` so the steering cell consumes
  `analysis/actuator_rows.jsonl`. The cell still uses the recovered layer-24
  `sycophancy_answer_direction.json`, `erase_write`, `anchor_onward`,
  `gen_stream`, baseline/subtract/add/permuted-control arms, and the
  correctness/refusal-aware AQ grader.
- Updated `gates.yaml` to score only post-steering actuator behavior. AQ-G1 is
  already adjudicated by the readout diagnostics; keeping it in `gates.yaml`
  would require filtering AUROC to incorrect-hint probe rows while retaining
  neutral guardrail rows in the same output, which the generic gate evaluator
  does not support.
- Added a Modal `--actuator` path to the AQ wrapper. The function restores r2
  readout artifacts from the Modal volume, regenerates readout diagnostics if
  needed, prepares actuator rows, runs `mechinterp steer`, runs
  `mechinterp score-gates`, checkpoints outputs, and uploads under
  `aq-sycophancy-actuator-r2/artifacts`.
- CPU checks passed: Python compile, actuator row materialization, steer config
  parse, gates parse, and local wrapper dry-run spec. Live Modal actuator launch
  remains blocked pending explicit approval naming AQ, Modal A10G, official
  `Qwen/Qwen3-4B`, and the cost cap.
- Modal CLI dry-run from pushed commit `e108f15f4` succeeded as app
  `ap-34vtwn4UfC8VAH01CqgdKN` after setting `PYTHONUTF8=1` and
  `PYTHONIOENCODING=utf-8`; it printed the resolved actuator spec and exited
  without spawning GPU work.

### 2026-07-07 - r2 hydra isolation panel

- Extended `analyze_aq_readout.py` with the planned local readout-only
  isolation panel: raw anchor, incorrect-minus-neutral paired deltas,
  condition-axis projection, fold-local residualization for behavior/length
  covariates, incorrect-only refits, length/confidence-matched incorrect-only
  slices, and a one-vs-rest hydra component map.
- Raw L24 anchor OOF AUROC remains 0.819. The matched paired-delta readout
  survives at AUROC 0.778, with a layer pattern that still peaks at L24
  (L12=0.507, L16=0.522, L17=0.550, L20=0.657, L24=0.778).
- Projecting out the broad `incorrect_hint` vs neutral condition axis leaves
  AUROC 0.815, so the broad prompt-condition axis alone does not explain the
  readout. However, adding fold-local residualization for baseline correctness,
  refusal, answer length, prompt length, and parsed confidence attenuates the
  readout to AUROC 0.600.
- Incorrect-only refits are weaker than the original all-probe readout:
  raw AUROC 0.626 and condition-residualized AUROC 0.614. A deterministic
  22/22 length/prompt/confidence-matched incorrect-only slice is stronger
  (raw AUROC 0.729, condition-residualized AUROC 0.725) but small enough to
  treat as hypothesis-shaping rather than a stable estimate.
- Hydra map over all r2 rows: raw one-vs-rest probes mostly re-read prompt
  condition. After condition residualization, `hint_resisted_correct` remains
  stronger (AUROC 0.784), `hint_followed` is moderate (0.691), neutral correct
  and neutral wrong are weak (~0.59/0.56), and `hint_other_wrong` collapses
  below chance (0.435). Interpretation: the L24 AQ signal looks like mixed
  prompt-conflict / correctness-resistance structure, not a clean standalone
  sycophancy actuator.

### 2026-07-07 - r2 local activation diagnostics

- Pulled the r2 Modal volume artifacts locally rather than retrying public/private
  publication: `analysis/row_pool.jsonl`, `analysis/probe_fit_labels.jsonl`,
  `analysis/extraction/*.safetensors`, and
  `directions/sycophancy_answer_direction.json` remain gitignored local
  artifacts.
- Added `analyze_aq_readout.py`, a CPU-only diagnostic script that recomputes
  the PCA/logistic held-out readout scores and writes ignored diagnostics under
  `analysis/readout_diagnostics/`.
- AQ-G1 passes on the selected layer-24 anchor readout using out-of-fold scores:
  OOF AUROC 0.819 with bootstrap 95% CI [0.742, 0.886], clearing the pre-stated
  point and lower-bound floors. The full fitted-direction AUROC is 1.00, but
  that is in-sample and is retained only as a calibration/projection check.
- Confound checks are mixed. The selected anchor score separates
  `incorrect_hint` from neutral prompts almost perfectly (AUROC 0.988), so it
  is not a clean prompt-condition-invariant sycophancy axis. At `answer_end`,
  the same layer does not preserve the label signal (OOF AUROC 0.529) and does
  not separate hinted from neutral prompts (AUROC 0.453).
- Within baseline-incorrect rows only, the held-out score still separates
  wrong-hint-followed from other wrong answers (OOF AUROC 0.723; 68 positive vs
  22 negative), so the readout is not merely generic wrongness, but it remains
  confounded enough that actuator results would need strict neutral/correctness
  guardrails and manual audit.

### 2026-07-07 - r2 scaled smoke/readout partial result

- Modal r2 smoke completed on A10G at repo commit `9f661c015`, run tag
  `aq-sycophancy-actuator-smoke-r2`, against official `Qwen/Qwen3-4B` revision
  `1cfa9a7208912126459214e8b04321603b3df60c`.
- The scaled smoke produced 512 scored rows: 128 each for `neutral`,
  `incorrect_hint`, `correct_hint`, and `correct_answer_denial`. The frozen
  row pool has 256 rows, 128 probe labels, 68 positive
  `wrong_hint_followed` and 60 negative
  `wrong_hint_not_followed_or_refused`. AQ-G0 clears with margin.
- Modal r2 readout app `ap-AhHmUkNR7ruGzGW66vikmM`, call
  `fc-01KWYTYS8F050TK9E072C14JAZ`, extracted and fit a direction, but the final
  HF artifact publication failed during per-file upload with Hugging Face
  `429 Too Many Requests` after exceeding the repository commit limit
  (`256 per hour`). The final wrapper `DONE` marker was therefore not written.
- The fitted direction was recovered from the Modal volume at
  `/ckpt/aq-sycophancy-readout-r2/data/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json`.
  Probe-fit selected a normalized layer-24 direction (`hidden_dim=2560`) with
  AUROC by layer: 12=0.589, 16=0.605, 17=0.657, 20=0.801, 24=0.846.
  Calibration at the selected layer: positive mean 3.83, negative mean -3.80,
  separation 7.63, sigma 4.15.
- Interpretation: the scaled run preserves an above-chance answer-sycophancy
  readout and clears AQ-G0, but the r1 perfect AUROC was small-n instability.
  This is still a readout/smoke result only; actuator launch remains blocked
  pending explicit approval. The Modal wrapper now batch-uploads directories via
  `upload_folder` to avoid the HF commit-limit failure on larger runs.

### 2026-07-07 - r2 scale-up planned

- User requested a larger AQ pool, closer to 500 source rows rather than the
  64-row pilot. Updated the next eval pass to `limit: 512`, which corresponds
  to about 128 complete neutral/incorrect-hint pairs under the SycophancyEval
  answer-row ordering.
- Modal staging tags were moved to `aq-sycophancy-actuator-smoke-r2` and
  `aq-sycophancy-readout-r2` so scaled artifacts do not overwrite or restore
  from the r1 pilot.
- Expected effect: if the pilot's 9/7 class rate roughly holds, the scaled pool
  should clear AQ-G0 with substantial margin. The actual 20/20 gate must still
  be evaluated from the r2 scored rows before any actuator launch.

### 2026-07-07 - Modal row-pool smoke and readout pilot

- Modal row-pool smoke completed on A10G against official `Qwen/Qwen3-4B` at
  revision `1cfa9a7208912126459214e8b04321603b3df60c` using commit
  `3a0a7e097` plus wrapper recovery/fix commits through `d5f26f4cb`.
- Smoke artifacts were uploaded to private HF staging at
  `professorsynapse/eh-al-prep-staging:aq-sycophancy-actuator-smoke-r1/artifacts/`.
  The smoke produced 64 scored rows, 32 row-pool rows, and 16 probe labels:
  9 positive `wrong_hint_followed` and 7 negative
  `wrong_hint_not_followed_or_refused`.
- The readout/probe run completed as Modal app `ap-JqoCvvgwbGHSKqkCux9CcM`
  with call `fc-01KWYMPM3A5P5QFPZD29AGXS9M`, run tag
  `aq-sycophancy-readout-r1`, and DONE marker
  `repo_commit=d5f26f4cb`. Artifacts were uploaded to
  `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/`.
- Extraction captured 32/32 answered rows at layers 12, 16, 17, 20, and 24
  for `anchor` and `answer_end` positions. The frozen probe direction selected
  layer 20, hidden dim 2560, with AUROC by layer: 12=0.70, 16=0.80, 17=0.90,
  20=1.00, 24=0.90. Direction calibration: positive mean 2.93, negative mean
  -2.72, separation 5.65, sigma 2.92.
- Governance caveat: this is a pilot/smoke readout, not a gate pass or actuator
  verdict. Pre-stated AQ-G0 requires at least 20 positive and 20 negative
  incorrect-hint rows; this run produced 9/7, so the registered AQ gate is
  underpowered/void and steering should not launch from this row pool without a
  revised/scaled row-pool plan.
