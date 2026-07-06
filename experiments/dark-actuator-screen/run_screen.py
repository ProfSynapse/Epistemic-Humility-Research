#!/usr/bin/env python3
"""Launch wrapper for the dark-actuator-screen: sweeps all 34 directions
declared in `cell.yaml`'s `readouts:` block through the SAME baseline+dose
ladder arms, landing every direction's rows in the ONE shared output JSONL
`gates.yaml` reads, with each direction's arm names prefixed by the direction
name (`<direction>__baseline`, `<direction>__dose1`, ...) -- exactly the
arm-naming convention `cell.yaml`/`gates.yaml`/NOTEBOOK.md already document.
This is the launch-time wrapper both docs describe as "not yet built."

WHY A WRAPPER, NOT A NEW TUNER PRIMITIVE
-----------------------------------------
`synaptic-tuner`'s `SteerCellConfig` binds exactly one `law.readout` per run
(MechInterp/config.py `LawConfig.readout`); there is no multi-direction sweep
primitive. This script never reimplements the intervention-hook or generation
logic -- it materializes 34 per-direction copies of the base recipe (readout
overridden, arm names prefixed) and calls the tuner's own PUBLIC entrypoint,
`MechInterp.cli.run_steer`, once per direction. Nothing in `synaptic-tuner/` is
modified.

PATH FIX (why this matters): `cell.yaml`'s own paths (`surface.rows_path`,
`execution.output_path`, every `readouts[*].path`) are written REPO-ROOT
relative, matching every other cell in `experiments/` (see
`experiments/example-cell/cell.yaml`). The tuner's own code resolves those
strings via a plain `open()` at whatever the process CWD happens to be when
`run_steer` runs -- `MechInterp/probe/fit.py::load_frozen_direction`,
`MechInterp/cell.py::load_jsonl`. The mechinterp-cells skill's documented
workflow (`cd synaptic-tuner && python tuner.py mechinterp steer --mi-config
../experiments/<slug>/cell.yaml ...`) would resolve those internal repo-root-
relative strings against `synaptic-tuner/` as CWD, silently missing every
file. This wrapper sidesteps the whole question: every per-direction
materialized config gets its three path families rewritten to ABSOLUTE paths
(anchored at this repo's root, computed from `__file__`) before being handed
to `load_steer_config`, so the run is correct regardless of the CWD it is
launched from.

RESUMABILITY
------------
Before calling `run_steer` for a direction, this script reads the shared
output JSONL ONCE and checks whether every one of that direction's 4 prefixed
arms already has a completed row for every row_key in the pool; if so, the
whole direction is skipped (no model reload). A partially-completed direction
still calls `run_steer`, which resumes at the row level itself
(`execution.resume: true` -> `MechInterp/cell.py::pending_rows`).

SMOKE GATING
------------
Every direction's config_sha differs (law.readout and every arm name change
per direction), and the tuner's smoke-state file
(`MechInterp/cell.py::smoke_state_path`, one file per `execution.output_path`)
only records a pass for an EXACT config_sha match
(`MechInterp/cell.py::smoke_passed`). Since every direction's sha is distinct,
each direction re-smoke-gates before its own arms automatically -- this
wrapper does not need its own smoke bookkeeping, it inherits the tuner's
fail-closed guard once per direction for free.

MODEL RELOAD COST: `run_steer` loads the model+tokenizer itself
(`_load_model_and_tokenizer`) inside every call; there is no supported way to
share one loaded model across the 34 calls without editing the tuner (out of
scope -- see the project's mechinterp-cells skill invariants). Each direction
pays its own model-load cost; see the cost estimate in this experiment's build
report, not duplicated here.

Usage
-----
  cd experiments/dark-actuator-screen
  python run_screen.py --dry-run                       # CPU-only, no GPU

  python run_screen.py \\
      --model unsloth/Qwen3-4B-bnb-4bit \\
      --render-fn ak_stage1_raw_base_render:render \\
      --i-know-this-runs-on-gpu

  # Restrict to one or a few directions (repeatable), e.g. for a first smoke:
  python run_screen.py --only L34_succ_pc0 --only randctrl_L34_succ_pc0 \\
      --model unsloth/Qwen3-4B-bnb-4bit \\
      --render-fn ak_stage1_raw_base_render:render \\
      --i-know-this-runs-on-gpu

Run from anywhere -- every path this script touches is resolved from
`__file__`, not the process CWD.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
COMMON_GRADERS = REPO_ROOT / "experiments" / "common" / "graders"
COMMON_RENDERS = REPO_ROOT / "experiments" / "common" / "renders"
CELL_YAML = HERE / "cell.yaml"
GENERATED_DIR = HERE / "analysis" / "generated_configs"  # gitignored (analysis/)

for _p in (TUNER_DIR, COMMON_GRADERS, COMMON_RENDERS):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# Base arm order in cell.yaml today: baseline, dose1, dose2, dose3. The
# wrapper does not hardcode this list for correctness (it prefixes whatever
# arms cell.yaml declares); it is named here only for the docstring/report.
_DOCUMENTED_BASE_ARMS = ("baseline", "dose1", "dose2", "dose3")


# ---------------------------------------------------------------------------
# Recipe loading and per-direction materialization
# ---------------------------------------------------------------------------


def load_base_recipe() -> dict[str, Any]:
    with open(CELL_YAML) as f:
        return yaml.safe_load(f)


def direction_names(recipe: dict[str, Any]) -> list[str]:
    return [r["name"] for r in recipe["readouts"]]


def _to_repo_abs(rel_path: str) -> str:
    """Resolve a repo-root-relative path string (as written in cell.yaml) to
    an absolute path anchored at REPO_ROOT, independent of process CWD."""
    p = Path(rel_path)
    return str(p) if p.is_absolute() else str((REPO_ROOT / p).resolve())


def prefixed_arm_names(direction: str, recipe: dict[str, Any]) -> list[str]:
    return [f"{direction}__{arm['name']}" for arm in recipe["arms"]]


def materialize_direction_config(
    recipe: dict[str, Any], direction: str
) -> dict[str, Any]:
    """Deep copy of the base recipe with `law.readout` overridden to
    `direction`, every arm name prefixed `<direction>__<arm>` (the convention
    `cell.yaml`/`gates.yaml` document), and every repo-root-relative path
    (`surface.rows_path`, `execution.output_path`, every `readouts[*].path`)
    rewritten absolute so the result parses and runs correctly regardless of
    CWD (see module docstring "PATH FIX")."""
    cfg = copy.deepcopy(recipe)

    cfg["law"]["readout"] = direction
    for arm in cfg["arms"]:
        arm["name"] = f"{direction}__{arm['name']}"

    cfg["surface"]["rows_path"] = _to_repo_abs(cfg["surface"]["rows_path"])
    cfg["execution"]["output_path"] = _to_repo_abs(cfg["execution"]["output_path"])
    for r in cfg["readouts"]:
        r["path"] = _to_repo_abs(r["path"])

    return cfg


def write_generated_config(cfg: dict[str, Any], direction: str) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    out = GENERATED_DIR / f"{direction}.yaml"
    with open(out, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    return out


# ---------------------------------------------------------------------------
# Resumability: direction-level completeness check against the shared output
# ---------------------------------------------------------------------------


def load_arm_membership(output_path: Path) -> dict[str, set[str]]:
    """One pass over the shared output JSONL -> {arm_name: {row_key, ...}}.

    Read once per invocation of this script (not once per direction/arm --
    `MechInterp.cell.completed_keys` re-reads the whole file per call, which
    would be quadratic over 34 directions x 4 arms as the shared file grows)."""
    membership: dict[str, set[str]] = {}
    if not output_path.exists():
        return membership
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            arm = rec.get("arm")
            rk = rec.get("row_key")
            if arm is None or rk is None:
                continue
            membership.setdefault(str(arm), set()).add(str(rk))
    return membership


def direction_complete(
    direction: str,
    recipe: dict[str, Any],
    membership: dict[str, set[str]],
    n_rows: int,
) -> bool:
    """True iff every one of this direction's prefixed arms already has
    n_rows completed rows in the shared output. n_rows is the pool size:
    every arm in this cell is fixed-strength, so a complete arm has exactly
    one row per pool row_key (MechInterp.cell._active_keys_for_arm)."""
    for arm_name in prefixed_arm_names(direction, recipe):
        if len(membership.get(arm_name, set())) < n_rows:
            return False
    return True


# ---------------------------------------------------------------------------
# Dry run: materialize + parse every per-direction config, never touch a GPU
# ---------------------------------------------------------------------------


def dry_run(recipe: dict[str, Any], names: list[str]) -> int:
    from MechInterp.config import load_steer_config  # noqa: E402  (needs TUNER_DIR on sys.path)

    print(f"dark-actuator-screen dry-run: {len(names)} direction(s)")
    n_rows = None
    rows_path = Path(_to_repo_abs(recipe["surface"]["rows_path"]))
    if rows_path.is_file():
        with rows_path.open() as f:
            n_rows = sum(1 for line in f if line.strip())
    else:
        print(f"  (pool not staged yet at {rows_path}; row-count checks skipped)")

    output_path = Path(_to_repo_abs(recipe["execution"]["output_path"]))
    membership = load_arm_membership(output_path)

    n_ok = 0
    n_already_complete = 0
    for direction in names:
        cfg_dict = materialize_direction_config(recipe, direction)
        cfg_path = write_generated_config(cfg_dict, direction)
        try:
            config = load_steer_config(cfg_path)
        except Exception as exc:  # noqa: BLE001 -- report every failure, don't stop at the first
            print(f"  [{direction}] FAILED to parse {cfg_path}: {exc}")
            continue
        n_ok += 1
        arm_names = [a.name for a in config.arms]
        complete = (
            n_rows is not None
            and direction_complete(direction, recipe, membership, n_rows)
        )
        if complete:
            n_already_complete += 1
        print(
            f"  [{direction}] ok: law.readout={config.law.readout!r} "
            f"arms={arm_names} "
            f"{'(already complete, would skip)' if complete else ''}"
        )

    print(
        f"dry-run summary: {n_ok}/{len(names)} configs parsed ok, "
        f"{n_already_complete}/{len(names)} already complete in the shared output"
    )
    return 0 if n_ok == len(names) else 1


# ---------------------------------------------------------------------------
# Real run: one run_steer call per direction, resumable at the direction and
# row level.
# ---------------------------------------------------------------------------


def run_screen(recipe: dict[str, Any], names: list[str], args: argparse.Namespace) -> int:
    from MechInterp.cli import run_steer  # noqa: E402
    from MechInterp.config import load_steer_config  # noqa: E402

    rows_path = Path(_to_repo_abs(recipe["surface"]["rows_path"]))
    if not rows_path.is_file():
        print(f"rows pool not staged at {rows_path}; run stage_pool first.")
        return 2
    with rows_path.open() as f:
        n_rows = sum(1 for line in f if line.strip())

    output_path = Path(_to_repo_abs(recipe["execution"]["output_path"]))

    n_run = 0
    n_skipped = 0
    for direction in names:
        membership = load_arm_membership(output_path)
        if direction_complete(direction, recipe, membership, n_rows):
            print(f"[{direction}] already complete ({n_rows} rows x 4 arms) -- skipping")
            n_skipped += 1
            continue

        cfg_dict = materialize_direction_config(recipe, direction)
        cfg_path = write_generated_config(cfg_dict, direction)
        config = load_steer_config(cfg_path)
        print(f"[{direction}] launching run_steer (config at {cfg_path})")
        rc = run_steer(
            config,
            model_name=args.model,
            adapter=args.adapter,
            render_fn_spec=args.render_fn,
            gpu_ack=args.i_know_this_runs_on_gpu,
            force=args.force_full_run,
        )
        if rc != 0:
            print(f"[{direction}] run_steer exited {rc}; stopping the sweep.")
            return rc
        n_run += 1

    print(f"Screen sweep complete: {n_run} direction(s) run, {n_skipped} already complete.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--model", default=None,
        help="Model name/path passed through to run_steer (required unless --dry-run)",
    )
    ap.add_argument(
        "--render-fn", default="ak_stage1_raw_base_render:render",
        help="Render callable spec 'module:callable' passed through to run_steer "
             "(default: this screen's AK Stage-1 raw-base render plug-in)",
    )
    ap.add_argument("--adapter", default=None, help="Optional PEFT adapter path/id")
    ap.add_argument(
        "--i-know-this-runs-on-gpu", dest="i_know_this_runs_on_gpu",
        action="store_true",
        help="Acknowledge each direction's run_steer call loads a model and uses a GPU",
    )
    ap.add_argument(
        "--force-full-run", dest="force_full_run", action="store_true",
        help="Skip the per-direction smoke gate (do not use for a signed run)",
    )
    ap.add_argument(
        "--only", action="append", default=None,
        help="Restrict the sweep to this direction name (repeatable)",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="CPU-only: materialize + parse every per-direction config and print "
             "the plan; never calls run_steer or touches a GPU",
    )
    args = ap.parse_args()

    recipe = load_base_recipe()
    names = direction_names(recipe)
    if args.only:
        unknown = sorted(set(args.only) - set(names))
        if unknown:
            print(f"Unknown direction(s): {unknown}")
            return 2
        only = set(args.only)
        names = [n for n in names if n in only]

    if args.dry_run:
        return dry_run(recipe, names)

    if not args.model:
        print("--model is required unless --dry-run")
        return 2

    return run_screen(recipe, names, args)


if __name__ == "__main__":
    raise SystemExit(main())
