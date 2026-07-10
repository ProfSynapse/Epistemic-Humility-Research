---
name: mech-interp-runner
description: Run, plan, validate, or aggregate Epistemic-Humility local mechanistic-interpretability sweeps, including hidden-state candidate inventories, causal-pilot sweep planning, explicit non-GPU/GPU gates, base-original skip handling, and offline result aggregation. Use when working on local mech-interp sweeps, causal-pilot diagnostics, activation-addition/logit-diagnostic runs, behavior-axis scans, SAE feature screens, or future reruns of the legacy full candidate inventory.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Mech-Interp Runner

> This skill drives the **frozen** bespoke local mech-interp machinery (see
> `archive/experiment/phase1/probe/steering/LEGACY.md`). It mints NO new cells. To author
> a NEW steering / extraction / probe-fit / gate-scoring cell, use the
> `mechinterp-cells` skill (tuner-backed `mechinterp` verbs), not this one.

Use the checked-in scripts and configs to plan, gate, run, and aggregate local
mech-interp work. Do not hand-roll terminal loops. This `SKILL.md` is a
progressive-disclosure router: it carries the invariants and routing only.
Procedural detail lives in `references/`, and current results live in
`docs/sessions/` and experiment-local docs under `experiments/<slug>/` - never
inline run history here.

## Start Here

Always choose the narrowest reference needed for the task:

| Task | Load |
|------|------|
| Decide whether a candidate is a real result; interpret directions | [references/interpretation-invariants.md](references/interpretation-invariants.md) |
| Preflight or configure a hidden-state extraction (incl. attention-head granularity) | [references/extraction-preflight.md](references/extraction-preflight.md) |
| Plan / execute / aggregate / observe a causal-pilot sweep; runtime-identity semantics | [references/sweep-workflow.md](references/sweep-workflow.md) |
| Launch a long GPU sweep that must survive CLI teardown (checkpoint/resume) | [references/resumable-gpu-sweeps.md](references/resumable-gpu-sweeps.md) |
| Choose rows / fixed row keys / rare-cell panels / per-row logit targets | [references/row-selection.md](references/row-selection.md) |
| Run next-token logit diagnostics and required control arms | [references/logit-diagnostics.md](references/logit-diagnostics.md) |
| Run the generated-answer replay behavioral gate | [references/generated-replay.md](references/generated-replay.md) |
| Screen SAE features | [references/sae-path.md](references/sae-path.md) |
| Run behavior-axis scans, plane/multicell readouts, direction transforms, multi-layer candidates | [references/behavior-axis-path.md](references/behavior-axis-path.md) |
| Test answer-sycophancy / helpfulness pressure across regimens | [references/sycophancy-probe-path.md](references/sycophancy-probe-path.md) |
| Test whether a read-side finding generalizes to a second known/unknown dataset | [references/cross-dataset-transfer.md](references/cross-dataset-transfer.md) |
| Test WHEN an axis fires vs the decision token (pre-commitment vs decision-echo, read-only) | [references/read-trajectory-timing.md](references/read-trajectory-timing.md) |

Do not preload all references. Read only the file needed for the current
operation, then follow any further routing inside it.

## Quick Commands

Prefer the skill CLI for common local analyses instead of hand-writing long
PowerShell commands. It delegates to checked-in repo scripts, resolves paths
from the repo root, uses `sys.executable`, and forces UTF-8 subprocess output
(`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1`) to avoid
Windows console encoding failures.

| Task | Command |
|------|---------|
| Discover subcommands | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py --help` |
| Quick non-GPU validation | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py validate --quick` |
| Behavior-axis scan | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py behavior-axis-scan --config <cfg>` |
| Causal sweep (plan/materialize) | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py causal-sweep --config <cfg> --mode-filter logit_diagnostic --write-plan --materialize-configs` |
| Sycophancy generation analysis | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py sycophancy-generation-analysis --generations <jsonl> --output-root <dir>` |
| Cross-dataset panel (step 1) | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py xdataset-build-panel --source <jsonl> --dataset <id> --out-dir <dir> --n-known 600 --n-unknown 400` |
| Cross-dataset behavior rows (step 3) | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py xdataset-behavior --generation <rows.jsonl> --panel-rows <gen_rows.jsonl> --out-dir <dir>` |
| Residual caution direction (read-trajectory step 1) | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py residual-caution-direction --extraction-dir <ext> --behavior-rows <rows.jsonl> --layer 35 --out <dir>/caution_direction_L35.json` |
| Read-trajectory re-analysis (GPU-free) | `python .skills/mech-interp-runner/scripts/mechinterp_cli.py residual-read-trajectory-analysis --rows <rows.jsonl> --out <analysis.json>` |

Use `--dry-run` on any subcommand to print the delegated command before running
it. For live Docker/GPU execution the same approval rule applies: do not pass
`--execute` unless the user has approved that live run.

## Core Invariants

- The research target is coherent epistemic-humility expression, not a raw
  refusal axis. A candidate is promising only if it improves one damaged
  behavior without degrading the paired desired behavior. See
  [references/interpretation-invariants.md](references/interpretation-invariants.md).
- Generated-answer replay is the behavioral gate. Offline separability (AUC, d,
  readout recall) and first-token answer-start movement are screening evidence,
  never a steering claim.
- Treat outputs as Tier 2 exploratory local mechanism evidence.
- Do not edit `synaptic-tuner/`.
- Do not run Docker/GPU unless the user explicitly approves that live run.
- Keep base-original `h_base` adapterless work fail-closed until the live runner
  explicitly supports adapterless base execution. In DPO/KTO extractions
  `h_base` is the SFT-merged pre-adapter model, not original Qwen base.
- Keep generated outputs gitignored by default unless a governed publication
  decision explicitly whitelists them.
- Stay local to this repository for mech-interp work. Do not use external
  workflow or memory systems unless the user explicitly asks in the current turn.

## Validation

Run focused non-GPU checks after runner/config/skill edits:

```bash
python -m pytest experiments/common/phase1_probe/tests/test_phase3_causal_pilot_sweep.py \
  experiments/common/phase1_probe/tests/test_phase3_causal_pilot_runner.py \
  experiments/common/phase1_probe/tests/test_phase3_causal_pilot_dry_run.py -q
python -m pytest experiments/common/phase1_probe/tests/test_phase3_behavior_axis_scan.py \
  experiments/common/phase1_probe/tests/test_phase3_behavior_axis_directions.py \
  experiments/common/phase1_probe/tests/test_phase3_calibrated_expression_plane.py \
  experiments/common/phase1_probe/tests/test_phase3_logit_cell_analysis.py -q
python -m pytest experiments/common/phase1_probe/tests/test_phase3_sae_smoke.py \
  experiments/common/phase1_probe/tests/test_phase3_sae_train.py \
  experiments/common/phase1_probe/tests/test_phase3_sae_feature_analysis.py \
  experiments/common/phase1_probe/tests/test_phase3_sae_feature_directions.py \
  experiments/common/phase1_probe/tests/test_phase3_sae_behavior_feature_analysis.py -q
python -m pytest .skills/mech-interp-runner/tests/test_mechinterp_cli.py -q
python bin/sync_skills.py --check
```

## Compact Recovery Loop

After context compaction or degraded memory:

1. Re-read this skill; drill into `references/` only as needed.
2. Re-read the latest relevant `docs/sessions/` note and local KG/search
   results if they affect the next experiment.
3. Set up or run the current local experiment with checked-in scripts/configs.
4. Analyze outputs against the research target (interpretation-invariants).
5. Update session notes, experiment-local runbooks/plans, and this skill when a
   durable procedure or gotcha changes.
6. Choose the next highest-ROI local slice from the evidence and repeat.

## Skill Maintenance

Edit the canonical tree under `.skills/mech-interp-runner/` only; `.agents/` and
`.claude/` are generated mirrors. Keep this contract intact:

- Put timeless rules, routing, commands, and validation gates in `SKILL.md`.
- Put durable procedure and gotchas in one-level `references/*.md` files and
  link them from `Start Here`.
- Put current findings, numeric results, and interpretation snapshots in
  `docs/sessions/*.md` and experiment-local docs under `experiments/<slug>/` -
  not in the skill.
- Put reusable analysis logic in checked-in scripts/configs, not prose.
- If a section grows because of one experiment, move the details to a session or
  experiment note and leave only the general rule plus the reference path.

Before adding a paragraph here, ask: "Will this still guide a future agent six
months from now without loading today's run history?" If not, it belongs in a
reference or a note. After canonical edits, run:

```bash
python bin/sync_skills.py --write --skill mech-interp-runner
python bin/sync_skills.py --check --skill mech-interp-runner
```
