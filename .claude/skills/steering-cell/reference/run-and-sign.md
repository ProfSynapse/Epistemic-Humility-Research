# Running a cell: smoke-first discipline + sign-then-pin-the-sha

## The arc

1. **Author** the `cell.yaml` (see cell-schema.md) and a `gates.yaml` (see
   gates-schema.md). Pre-state the prediction, falsifier, and gate thresholds in
   the amendment doc before any run - the gates.yaml IS the falsifier, in code.

2. **Plan (CPU, no GPU/torch):**
   ```bash
   python3 steering/steer_cell.py plan --config steering/configs/my_cell.yaml
   ```
   Echoes the parsed cell (row count, readouts + shas, arms, out_dir, smoke
   block). Use it to confirm selection/actuation before spending GPU.

3. **Smoke one arm (enforced before any full arm):**
   ```bash
   python3 steering/steer_cell.py run --config .../my_cell.yaml --arm primary --smoke
   ```
   The smoke generates `smoke.n` rows AND, for a steering arm, re-reads the
   post-write anchor coordinate: it asserts the observed coordinate landed at the
   commanded value (`g*sigma` for setpoint; `alpha` move for additive) within
   `readback_tolerance`, and records the result in `readback.json`. On pass it
   writes `smoke_state.json` marking that arm smoke-passed at the current config
   sha. A readout-only arm records a trivial pass (no hook to read back).

4. **Run the full arm(s):**
   ```bash
   python3 steering/steer_cell.py run --config .../my_cell.yaml --arm primary
   # or every arm:
   python3 steering/steer_cell.py run --config .../my_cell.yaml
   ```
   The runner **refuses** a full arm whose smoke has not passed
   (`smoke_state.json`), returning exit 3. Override only knowingly with
   `--force-no-smoke`. Resume is automatic: rows already present in the arm's
   `gen/rows.jsonl` are skipped (use `--overwrite` to regenerate).

5. **Grade** the arm rows with the amendment's byte-pinned grader (the same grader
   as the frozen baseline), then **score gates:**
   ```bash
   python3 steering/score_gates.py --config .../my_cell.yaml --gates .../my_gates.yaml
   ```

6. **Record the verdict** in the amendment doc: gates PASS/MISS with the numbers,
   the readback, and the config sha.

## Sign, then pin the config sha

The amendment's confirmatory surface is the exact `cell.yaml` the user signed. To
make a run provably that config:

1. Compute the sha256 of the signed file:
   ```bash
   sha256sum steering/configs/my_cell.yaml
   ```
2. Put it in the config as `surface.generation.expected_config_sha: <64-hex>` and
   record the same sha in the amendment doc at signing.
3. The runner's `run` path is FATAL (exit 2) when the file's sha no longer matches
   `expected_config_sha` - before any model load - so an edit-after-signing can
   never silently run. `plan` only WARNS (so an author can inspect an edited cell).

Because `expected_config_sha` is itself part of the file, set it, then re-hash and
paste the final value; a later whitespace edit changes the sha and trips the guard
(intended). Treat the pinned sha as the identity of the confirmatory run.

## What is untracked

Everything under the out_dir (`analysis/steer_cells/<name>/` by default):
`gen/rows.jsonl`, `readback.json`, `smoke_state.json`, `manifest.json`,
`gates_report.json`. Never commit them; never commit FalseQA question text. Commit
only the `cell.yaml`, the `gates.yaml`, and the amendment doc.
