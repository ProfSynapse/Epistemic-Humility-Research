---
name: experiment-runner
description: Operational runbook for the Epistemic-Humility Phase 1 experiment runner — expands the PROTOCOL v0.3 (LOCKED) run matrix (3-seed headline + LR/beta sensitivity panel at 4B, 3-seed confirm at 8B, 2 bridge replication cells) into per-cell tuner invocations across two lanes (local RTX 3090 / HF Jobs cloud), with hard pre-registration count assertions, prerequisite gating, data staging, and committed provenance run records. Use when launching, dry-running, or gating the Phase 1 matrix, materializing per-cell recipes, or inspecting run records. This skill is about USING the runner via its checked-in scripts — it never modifies the synaptic-tuner submodule.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Phase 1 Experiment Runner

Expand the PROTOCOL v0.3 run matrix into per-cell tuner runs on two lanes, with
full provenance and prerequisite gating. This is orchestration GLUE: the runner
talks to the `synaptic-tuner` submodule ONLY through the materialized recipe YAML
and the tuner's public CLI verbs. It adds nothing to the tuner.

## Quick Reference

| Task | Command |
|------|---------|
| Dry-run the matrix (expand + assert counts, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run` |
| Check prerequisites per cell (gate, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local` |
| Standalone prereq report | `python3 .agents/skills/experiment-runner/scripts/check_prereqs.py --matrix .agents/skills/experiment-runner/config/matrix.yaml --data-root experiment/phase1/data --lane local` |
| Launch the local smoke/pilot lane | see Common Patterns (gated, explicit; seed/beta capability-probed — see CLI Discipline) |
| Launch the cloud matrix | see Common Patterns (both lanes safety-gated by a live capability probe — see CLI Discipline) |
| Inspect a run record | `cat experiment/phase1/run_records/<run_id>.json` |

The matrix SSOT is `config/matrix.yaml`; the per-arm DEFAULT recipes are repo
content at `experiment/phase1/recipes/`; the provenance records are committed at
`experiment/phase1/run_records/`.

## Run Matrix at a Glance

| Block | Cells | Notes |
|-------|-------|-------|
| Headline 4B | 9 | 3 arms × 3 seeds — the pre-registered numbers |
| LR panel 4B | 6 | per-arm-relative LR × {3.0, 0.333}; robustness only |
| beta panel 4B | 4 | DPO + KTO × {0.05, 0.5}; robustness only |
| Confirm 8B | 9 | 3 arms × 3 seeds (cloud) |
| Bridge | 2 | Cheng Idk-SFT / Idk-DPO replication |

`run_matrix.py` ASSERTS 19 @ 4B / 9 @ 8B / 2 bridge and ABORTS on mismatch — the
pre-registration guard. See [matrix-expansion.md](reference/matrix-expansion.md).

## CLI Discipline

These are non-negotiables, inherited in spirit from the tuner's fine-tuning
skill:

- **Never** launch a cost-incurring cloud run, cancel a job, or delete artifacts
  unless the user has explicitly approved that exact action in the current
  conversation. Treat launch/cancel/delete as irreversible operator actions; do
  not infer permission from a broader goal.
- **No-pollution rule (SACROSANCT).** The runner communicates with the tuner
  ONLY through (1) the materialized recipe YAML and (2) the tuner's public CLI
  verbs. It imports NO tuner internals, adds NO committed file under
  `synaptic-tuner/`, and registers NO experiment-specific method/config there.
  The only tuner-tree write is ephemeral per-cell data staged under the tuner's
  ALREADY gitignored `scratch/eh_staging/<run_id>/` — scratch, never source. If
  the runner needs a tuner behavior the CLI does not expose, the correct move is
  to FLAG it (it indicates a missing GENERAL tuner capability), never to reach
  into tuner internals from this repo.
- **Do not guess tuner CLI flags.** Check `synaptic-tuner/tuner/cli/parser.py`
  or `python tuner.py --help` before relying on a flag.
- **Prefer the checked-in `run_matrix.py`** over ad hoc per-cell loops.
- **Never loosen the count assertions** to absorb a `matrix.yaml` edit. The
  counts are pre-registered; a change needs a NEW signed PROTOCOL revision first.
- **BOTH lanes are safety-gated by a LIVE capability probe.** A cell is only safe
  once the tuner forwards per-cell `seed` / `beta` on the lane it runs; otherwise
  cells silently train at defaults. The gap spans both lanes (cloud command
  builder + local run handler + trainer flags); `check_prereqs` PROBES the actual
  tuner source surface for that lane — not a flag or SHA — and SKIPs cells until
  the probe passes. The local probe currently fails on missing beta forwarding.
  Do not work around this in the runner; the capability is a general tuner change
  (Task #32, coder-cloud owns the reconciliation). See [lanes.md](reference/lanes.md).

## Local Windows/Desktop Gotchas

- Native Windows vLLM can import `vllm` while still failing at runtime with
  `ModuleNotFoundError: vllm._C`; use Docker/WSL Linux vLLM for real WS-1 probe
  runs.
- The `vllm/vllm-openai` image has a server entrypoint. Override it for checks
  and probe execution, e.g. `--entrypoint nvidia-smi` for GPU smoke and
  `--entrypoint python3` for `probe.py`.
- Docker may require an unsandboxed/escalated command from Codex. On the desktop
  run, Docker engine `29.3.1` was reachable outside the sandbox.
- Redirect Hugging Face caches to repo-local `.cache/hf` during local runs to
  avoid Windows permission failures under `C:\Users\Joseph\.cache\huggingface`.
- `.env` may contain `HF_TOKEN` while the current process environment does not.
  Load it process-locally or pass `--env-file .env`; never print token values.
- Windows default text encoding broke the TriviaQA fetch before the script used
  explicit UTF-8 writes. Keep UTF-8 mode/path handling in mind for fetch retries.
- TriviaQA train `question_id` is not unique. WS-1 resumability/subsetting must
  use `probe_pool_row_key` (source index plus question_id), not bare
  `question_id`, or duplicate source rows will be silently skipped.
- Qwen3 prompt rendering can look thinking-off while generated answers still
  contain `<think>...</think>`. Treat any generated thinking tags in
  `probe_results.jsonl` as contaminated output: stop the container, archive the
  output directory, and retry only after the generated-output guard fails before
  writing rows or the backend suppression path is fixed. Do not strip tags and
  continue.
- `git submodule status` can fail if Git Unix helpers such as `basename` or
  `sed` are missing. Verify the submodule SHA with the gitlink plus
  `git -C synaptic-tuner rev-parse HEAD`.

## Common Patterns

The canonical launch sequence:

```bash
# 1. Dry-run: expand the matrix, confirm the 19/9/2 count assertions pass,
#    eyeball the per-cell seeds/overrides. Launches nothing.
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run

# 2. Check prerequisites for the lane you intend to run. Reports per-cell gate
#    status (datasets present, leakage guard passed, cloud/bridge skips).
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local

# 3. Local smoke: run ONE 4B cell locally to confirm the trainer path before
#    committing the matrix. (Explicit, user-approved launch per CLI Discipline.)

# 4. Local 4B pilot, then — once the cloud seed/beta capability lands and the
#    datasets are published to the hub — the cloud matrix.
```

Headline numbers come ONLY from the pre-registered default cells; the LR/beta
panel is robustness-only and is tagged distinctly in each run-id coordinate so
the eval-side aggregation isolates it.

## Progressive Reference

| Topic | Doc |
|-------|-----|
| How `matrix.yaml` maps to PROTOCOL v0.3 cells + the count-assertion table | [reference/matrix-expansion.md](reference/matrix-expansion.md) |
| Local staging vs cloud hub-name; the data-locality contract; the cloud capability gap | [reference/lanes.md](reference/lanes.md) |
| Run-record schema + provenance discipline (dual SHAs, data block, verified flag) | [reference/run-records.md](reference/run-records.md) |
