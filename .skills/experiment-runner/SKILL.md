---
name: experiment-runner
description: Operational runbook for the Epistemic-Humility Phase 1 experiment runner - expands the PROTOCOL v0.3 (LOCKED) run matrix (3-seed headline + LR/beta sensitivity panel at 4B, 3-seed confirm at 8B, 2 bridge replication cells) into per-cell tuner invocations across two lanes (local RTX 3090 / HF Jobs cloud), with hard pre-registration count assertions, prerequisite gating, data staging, and committed provenance run records. Use when launching, dry-running, or gating the Phase 1 matrix, materializing per-cell recipes, or inspecting run records. This skill is about USING the runner via checked-in scripts; it never modifies the synaptic-tuner submodule.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Phase 1 Experiment Runner

Use the checked-in runner scripts to expand, gate, stage, and inspect Phase 1
experiment cells. This skill is orchestration glue: it talks to the
`synaptic-tuner` submodule only through materialized recipe YAML and public tuner
CLI verbs. It must not add experiment-specific code or config to the tuner.

Amendment A / v0.4 is signed as a prospective extension (user approval,
2026-06-14). Sequential `SFT -> DPO` and `SFT -> KTO` arms are not part of the
locked v0.3 matrix, are not present in `config/matrix.yaml`, and must be
materialized/run only as deliberate Amendment A cells with separate recipes and
run records.

## Start Here

Always choose the narrowest reference needed for the task:

| Task | Load |
|------|------|
| Dry-run, count-check, or explain the locked matrix | [reference/matrix-expansion.md](reference/matrix-expansion.md) |
| Gate/stage/launch a local or cloud cell | [reference/operator-discipline.md](reference/operator-discipline.md), then [reference/lanes.md](reference/lanes.md) |
| Work on HF Jobs/cloud launch details | [reference/cloud-lane.md](reference/cloud-lane.md) |
| Work on Windows, Docker, local training, local eval, or GPU capacity | [reference/local-windows-gotchas.md](reference/local-windows-gotchas.md) |
| Inspect or update run records | [reference/run-records.md](reference/run-records.md) |
| Use common launch command patterns | [reference/common-patterns.md](reference/common-patterns.md) |
| Prepare/gate hidden-state extraction | [reference/hidden-state-probe-smoke.md](reference/hidden-state-probe-smoke.md) |
| Plan Phase 3 causal-pilot sweeps | [reference/phase3-causal-pilot-sweeps.md](reference/phase3-causal-pilot-sweeps.md) |
| Record durable research-session memory | [reference/research-sessions.md](reference/research-sessions.md) |
| Make governed protocol, output-contract, or rerun-scope changes | [reference/protocol-amendments.md](reference/protocol-amendments.md) |

Do not preload all references. Read only the files needed for the user's current
operation, then follow any further routing inside that reference.

## Quick Commands

| Task | Command |
|------|---------|
| Dry-run the matrix (expand + assert counts, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run` |
| Check prerequisites per cell (gate, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local` |
| Standalone prereq report | `python3 .agents/skills/experiment-runner/scripts/check_prereqs.py --matrix .agents/skills/experiment-runner/config/matrix.yaml --data-root experiment/phase1/data --lane local` |
| Prepare one local 4B cell (stage data + materialized recipe + run record) | `python3 .agents/skills/experiment-runner/scripts/prepare_local_cell.py --run-id sft__4b__headline__seed1 --status launched` |
| Inspect a run record | `Get-Content experiment/phase1/run_records/<run_id>.json` |
| Prepare/gate one hidden-state extraction (GPU-free; gate + resolve, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/prepare_extraction_cell.py --config experiment/phase1/probe/config/hidden_state_probe.yaml` |
| Plan Phase 3 causal-pilot sweeps (GPU-free by default) | `python experiment/phase1/probe/phase3_causal_pilot_sweep.py --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml` |

## Core Invariants

- The matrix SSOT is `config/matrix.yaml`; per-arm default recipes live under
  `experiment/phase1/recipes/`; provenance records live under
  `experiment/phase1/run_records/`.
- `run_matrix.py` must assert the pre-registered counts: 19 @ 4B, 9 @ 8B,
  and 2 bridge cells. Never loosen these assertions to absorb a matrix edit.
- Launch/cancel/delete actions require exact user approval in the current
  conversation, especially cost-incurring cloud actions.
- The no-pollution rule is sacrosanct: runner code may not import tuner
  internals, write committed files under `synaptic-tuner/`, or register
  Epistemic-specific tuner behavior. Ephemeral staging under already-gitignored
  tuner scratch space is the only allowed tuner-tree write.
- Do not guess tuner CLI flags. Check `synaptic-tuner/tuner/cli/parser.py` or
  `python tuner.py --help` before relying on a flag.
- Both lanes are safety-gated by live capability probes for per-cell `seed` and
  `beta` forwarding. If the probe fails, skip/flag the cell rather than working
  around the gap in the runner.
- Treat bounded local diagnostics and Amendment A/B evidence as non-headline
  unless a protocol/run record explicitly says otherwise. Headline numbers come
  only from the pre-registered default cells.

## Matrix At A Glance

| Block | Cells | Notes |
|-------|-------|-------|
| Headline 4B | 9 | 3 arms x 3 seeds; the pre-registered numbers |
| LR panel 4B | 6 | per-arm-relative LR x {3.0, 0.333}; robustness only |
| beta panel 4B | 4 | DPO + KTO x {0.05, 0.5}; robustness only |
| Confirm 8B | 9 | 3 arms x 3 seeds (cloud) |
| Bridge | 2 | Cheng Idk-SFT / Idk-DPO replication |

See [reference/matrix-expansion.md](reference/matrix-expansion.md) for the full
mapping and count-assertion contract.

## Skill Maintenance

Edit the canonical tree under `.skills/experiment-runner/` only. `.agents/` and
`.claude/` are generated mirrors. After canonical edits, run:

```bash
python3 bin/sync_skills.py --write --skill experiment-runner
python3 bin/sync_skills.py --check --skill experiment-runner
```

When this skill grows, move details into one-level files under `reference/` and
link them from `Start Here`; keep `SKILL.md` as a progressive-disclosure router.
