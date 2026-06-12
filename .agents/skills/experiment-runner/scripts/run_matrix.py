#!/usr/bin/env python3
"""
Phase 1 experiment-runner — matrix expansion + materialization + lane dispatch.

Location: .claude/skills/experiment-runner/scripts/run_matrix.py
Purpose: Expand the PROTOCOL v0.3 (LOCKED) run matrix (config/matrix.yaml) into
    per-cell tuner invocations on two lanes (local RTX 3090 / HF Jobs cloud),
    with a HARD pre-registration count assertion (19 @ 4B, 9 @ 8B, 2 bridge that
    ABORTS on mismatch), per-cell recipe materialization, data staging, run-record
    emission BEFORE launch, and prerequisite gating.
Used with: scripts/check_prereqs.py (the gate), config/matrix.yaml (the SSOT),
    experiment/phase1/recipes/*.yaml (base recipes), experiment/phase1/run_records/.

This is orchestration GLUE. It NEVER imports tuner internals and adds NO file
under synaptic-tuner/ except ephemeral staged data under the tuner's already
gitignored scratch/ dir. It talks to the tuner ONLY through (1) the materialized
recipe YAML and (2) the tuner's public CLI verbs. See reference/lanes.md.

Import-light: stdlib + PyYAML + the sibling check_prereqs module only. trl /
unsloth / torch are NOT needed; --dry-run and expansion are fully testable
without the ML stack or a network.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_prereqs  # noqa: E402  (sibling module, intentional local import)

# Research-repo (worktree) root, derived from this file's location so the path
# defaults below are CWD-independent: .../.claude/skills/experiment-runner/scripts
# -> parents[4] is the worktree root. The argparse defaults anchor on this rather
# than on relative strings, so `python run_matrix.py` resolves identically whether
# invoked from the repo root or from the skill dir (MT4). All four remain
# caller-overridable for fixtures/tests.
_REPO_ROOT = Path(__file__).resolve().parents[4]

# Pre-registered cell counts (PROTOCOL v0.3 §3.1 / §3.1a). The expansion result
# MUST match these exactly; a mismatch ABORTS — this is the pre-registration
# guard. Do not edit to absorb a matrix change; revise PROTOCOL first.
EXPECTED_COUNT_4B = 19
EXPECTED_COUNT_8B = 9
EXPECTED_COUNT_BRIDGE = 2

# The tuner mounts its own repo root at /workspace/repo; staged data lives under
# the tuner's already-gitignored scratch/ dir, so no tuner-tree edit is needed
# (NOT a committed source addition). dataset.local_file is rewritten to this
# tuner-repo-relative path so local_run_handler.py:502's /workspace/repo join
# resolves. See reference/lanes.md and the §9.2(b.1) data-locality contract.
TUNER_STAGING_SUBDIR = "scratch/eh_staging"


class MatrixError(Exception):
    """Matrix expansion / count-assertion failure — abort the whole run."""


@dataclass(frozen=True)
class Coordinate:
    """Deterministic cell coordinate — becomes the run id and the eval tag."""

    arm: str
    size: str
    cell_type: str  # headline | lr_panel | beta_panel | confirm | bridge
    seed: int
    override: tuple = ()  # ("learning_rate", v) | ("beta", v) | ()

    def run_id(self) -> str:
        override_tag = ""
        if self.override:
            key, value = self.override
            short = "lr" if key == "learning_rate" else key
            override_tag = f"__{short}{value}"
        return f"{self.arm}__{self.size}__{self.cell_type}{override_tag}__seed{self.seed}"

    @property
    def is_bridge(self) -> bool:
        """Bridge replication cell. Bridge data is do-not-redistribute, so these
        are LOCAL-LANE ONLY (never on the hub) — see select_invocation."""
        return self.size == "bridge"


@dataclass
class Cell:
    """An expanded cell: coordinate + the base recipe it materializes from."""

    coordinate: Coordinate
    recipe: str
    method: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def model_tag_from_recipe(recipe: dict) -> str:
    """Derive the WS-2 model_tag from the recipe's dataset.local_file path.

    The builder writes to experiment/phase1/data/<model_tag>/<file>; the recipe's
    dataset.local_file carries that path, so the tag is its parent dir name.
    """
    local_file = (recipe.get("dataset") or {}).get("local_file")
    if not local_file:
        raise MatrixError(f"recipe missing dataset.local_file: {recipe.get('name')}")
    return Path(local_file).parent.name


# ---------------------------------------------------------------------------
# Expansion — matrix.yaml -> cells. Counts asserted against PROTOCOL v0.3.
# ---------------------------------------------------------------------------


def expand_4b(matrix: dict) -> list:
    """Headline (arms x seeds) + LR panel + beta panel. Asserts == 19."""
    cells = []
    seeds = matrix["seeds_headline"]
    arms = matrix["arms_4b"]
    panel = matrix["panel_4b"]

    for arm in arms:
        for seed in seeds:
            cells.append(Cell(
                Coordinate(arm["method"], "4b", "headline", seed),
                arm["recipe"], arm["method"]))

    for arm in arms:
        for mult in panel["lr_multipliers"]:
            cells.append(Cell(
                Coordinate(arm["method"], "4b", "lr_panel", panel["panel_seed"],
                           ("learning_rate", mult)),
                arm["recipe"], arm["method"]))

    for arm in arms:
        if not arm.get("has_beta"):
            continue
        for beta in panel["beta_values"]:
            cells.append(Cell(
                Coordinate(arm["method"], "4b", "beta_panel", panel["panel_seed"],
                           ("beta", beta)),
                arm["recipe"], arm["method"]))

    if len(cells) != EXPECTED_COUNT_4B:
        raise MatrixError(
            f"4B cell count {len(cells)} != pre-registered {EXPECTED_COUNT_4B} "
            f"(PROTOCOL v0.3 §3.1/§3.1a). matrix.yaml drifted from the locked "
            f"design — revise PROTOCOL before changing counts."
        )
    return cells


def expand_8b(matrix: dict) -> list:
    """Confirm arms x confirm_8b_seeds. Asserts == 9."""
    cells = []
    seeds = matrix["seeds_headline"][: matrix["confirm_8b_seeds"]]
    if len(seeds) != matrix["confirm_8b_seeds"]:
        raise MatrixError(
            f"confirm_8b_seeds={matrix['confirm_8b_seeds']} exceeds available "
            f"headline seeds {matrix['seeds_headline']}"
        )
    for arm in matrix["arms_8b"]:
        for seed in seeds:
            cells.append(Cell(
                Coordinate(arm["method"], "8b", "confirm", seed),
                arm["recipe"], arm["method"]))

    if len(cells) != EXPECTED_COUNT_8B:
        raise MatrixError(
            f"8B cell count {len(cells)} != pre-registered {EXPECTED_COUNT_8B} "
            f"(PROTOCOL v0.3 §3.1). If the 8B seed bump was vetoed, update both "
            f"confirm_8b_seeds and EXPECTED_COUNT_8B in a signed PROTOCOL revision."
        )
    return cells


def expand_bridge(matrix: dict) -> list:
    """Bridge replication arms, 1 seed each. Asserts == 2."""
    cells = []
    for arm in matrix["bridge"]:
        cells.append(Cell(
            Coordinate(arm["method"], "bridge", "bridge", 1),
            arm["recipe"], arm["method"]))

    if len(cells) != EXPECTED_COUNT_BRIDGE:
        raise MatrixError(
            f"bridge cell count {len(cells)} != pre-registered {EXPECTED_COUNT_BRIDGE}"
        )
    return cells


def expand_matrix(matrix: dict) -> list:
    """Full expansion with all three hard count assertions."""
    return expand_4b(matrix) + expand_8b(matrix) + expand_bridge(matrix)


def assert_bridge_lane_safety(cells: list, lane: str) -> None:
    """Abort loudly if any bridge cell would resolve to the cloud lane.

    Bridge cells are LOCAL-LANE ONLY: their OpenMOSS training data is
    do-not-redistribute and is never published to the hub, so a bridge cell on
    the cloud lane is a CONFIG ERROR (license containment — vendored data must
    never ride a hub-data lane). This is the expansion-time belt-and-suspenders
    guard; check_prereqs.check_cell and select_invocation enforce the same rule
    at the gate and the dispatcher.
    """
    if lane != "cloud":
        return
    bridge = [c.coordinate.run_id() for c in cells if c.coordinate.is_bridge]
    if bridge:
        raise MatrixError(
            f"bridge cells {bridge} cannot run on the cloud lane: bridge training "
            f"data is do-not-redistribute and is never published to the hub. "
            f"Bridge arms are LOCAL-LANE ONLY — relaunch them with --lane local."
        )


# ---------------------------------------------------------------------------
# Materialization — base recipe + single override -> per-cell recipe.
# ---------------------------------------------------------------------------


def materialize_recipe(base: dict, cell: Cell, lane: str = "local") -> dict:
    """Deep-copy the base recipe and apply this cell's single override.

    Sets training.seed; applies the per-arm-relative LR (multiplier x the recipe's
    OWN default LR) or the beta override; rewrites name + artifacts.output_root to
    embed the coordinate. Materialized recipes stay PURELY DECLARATIVE: any legacy
    run.command/workdir is stripped and none is ever injected.

    Mechanism note (arch §9.2, re-ruled 2026-06-10): the tuner's local-run handler
    is method-generic — its command builder reads run.trainer and forwards the
    training-key list (seed for all methods; beta for dpo/kto) with zero
    SFT-specific logic. The handler-extension (tuner task #34) widens the dispatch
    guard so local-run natively builds sft/dpo/kto commands, so the runner needs
    NO per-method run.command injection. This supersedes the earlier Option-A
    inject design (withdrawn): both lanes drive the tuner purely through the
    declarative materialized recipe + the public CLI verb.
    """
    recipe = copy.deepcopy(base)
    coord = cell.coordinate
    training = recipe.setdefault("training", {})
    training["seed"] = coord.seed

    if coord.override:
        key, value = coord.override
        if key == "learning_rate":
            default_lr = float(training["learning_rate"])
            training["learning_rate"] = default_lr * float(value)
        elif key == "beta":
            training["beta"] = float(value)

    recipe["name"] = coord.run_id().replace("__", "-").replace("_", "-")
    artifacts = recipe.setdefault("artifacts", {})
    artifacts["output_root"] = (
        f"toolset-training-artifacts/runs/{lane}/{coord.size}/{coord.run_id()}"
    )
    # Declarative recipes: drop any legacy run.command/workdir so a materialized
    # recipe is never self-contradictory. Nothing is injected — the handler builds
    # the per-method trainer command from run.method + run.trainer + the training
    # block. We set run.method and run.trainer per cell so the materialized recipe
    # is a complete, self-describing job-config: the handler's widened dispatch
    # guard routes on run.method and its generic builder reads run.trainer (which
    # defaults to the SFT trainer, so DPO/KTO MUST carry the right path). §9.2:1016.
    run_block = recipe.setdefault("run", {})
    if isinstance(run_block, dict):
        run_block.pop("command", None)
        run_block.pop("workdir", None)
        run_block["method"] = cell.method
        run_block["trainer"] = f"Trainers/{cell.method}/train_{cell.method}.py"
    return recipe


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Data staging (local lane) — copy research-repo data into the tuner scratch.
# ---------------------------------------------------------------------------


def stage_local_data(
    *, data_root: Path, model_tag: str, train_file: str, dev_file: str,
    tuner_root: Path, run_id: str,
) -> dict:
    """Copy the per-cell train+dev data into the tuner's gitignored scratch.

    Returns {source_data_file, staged_data_file (tuner-repo-relative), data_sha256}
    so dataset.local_file can be rewritten to the staged path and the run record
    can pin the exact bytes. Idempotent per run_id.
    """
    src_dir = data_root / model_tag
    staged_rel = Path(TUNER_STAGING_SUBDIR) / run_id
    staged_abs = tuner_root / staged_rel
    staged_abs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_dir / train_file, staged_abs / train_file)
    shutil.copy2(src_dir / dev_file, staged_abs / dev_file)
    return {
        "source_data_file": str((src_dir / train_file)),
        "staged_data_file": (staged_rel / train_file).as_posix(),
        "data_sha256": sha256_file(src_dir / train_file),
    }


def dataset_basenames(recipe: dict) -> tuple:
    """(train_file, dev_file) basenames implied by the recipe's local_file."""
    train = Path(recipe["dataset"]["local_file"]).name
    dev = train.replace("_train.jsonl", "_dev.jsonl")
    return train, dev


# ---------------------------------------------------------------------------
# Run records — provenance spine (HANDOFF.md §5).
# ---------------------------------------------------------------------------


def git_head(repo_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def build_run_record(
    *, cell: Cell, recipe: dict, materialized_text: str, lane: str,
    research_repo_root: Path, data_block: dict, status: str,
    tuner_invocation: list, prereq_details: dict,
) -> dict:
    coord = cell.coordinate
    override = {coord.override[0]: coord.override[1]} if coord.override else {}
    return {
        "run_id": coord.run_id(),
        "matrix_version": None,  # filled by caller (knows the matrix)
        "coordinate": {
            "arm": coord.arm, "size": coord.size, "cell_type": coord.cell_type,
            "seed": coord.seed, "override": override,
        },
        "source_recipe": f"experiment/phase1/recipes/{cell.recipe}.yaml",
        "materialized_recipe_sha": sha256_text(materialized_text),
        "method": cell.method,
        "model": (recipe.get("model") or {}).get("name"),
        "lane": lane,
        "data": data_block,
        "research_repo_commit": git_head(research_repo_root),
        "submodule_commit": git_head(research_repo_root / "synaptic-tuner"),
        "prereq_check": prereq_details,
        "launched_at": now_utc(),
        "tuner_invocation": tuner_invocation,
        "outcome": {"status": status, "job_handle": None, "adapter_path": None,
                    "metrics_path": None, "verified": False},
    }


def write_run_record(record: dict, run_records_dir: Path) -> Path:
    run_records_dir.mkdir(parents=True, exist_ok=True)
    path = run_records_dir / f"{record['run_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Lane dispatch — shell out to the tuner's public CLI. No tuner internals.
# ---------------------------------------------------------------------------


def local_invocation(materialized_recipe_path: Path) -> list:
    """Local RTX 3090 lane: config-driven local Docker run via the tuner CLI.

    UNIFORM across all methods (HANDLER EXTENSION resolution, §9.2 lines 994-1013,
    lead-ratified). The tuner's local-run handler builds the per-method trainer
    command from the recipe's `run.trainer` + `training` block; coder-cloud's
    re-scoped #34 widens the handler's method guard to {sft,dpo,kto} and forwards
    beta (method-gated). So SFT, DPO, and KTO all dispatch through the same native
    local-run verb with a purely declarative materialized recipe — WS-5 never
    synthesizes a trainer command or a trainer --config invocation (that path was
    explicitly withdrawn, §9.2 :1175-1176). Until #34 lands, the local capability
    probe keeps DPO/KTO cells SKIPPED (fail-closed), so this never runs prematurely.
    """
    return ["python", "tuner.py", "local-run",
            "--job-config", materialized_recipe_path.as_posix(), "--yes"]


def cloud_invocation(method: str, dataset_name: str, recipe: dict) -> list:
    """HF Jobs lane: cloud train+eval via the tuner CLI, data by hub name.

    NOTE: this constructs the INTENDED cloud invocation, but check_prereqs
    LIVE-PROBES the tuner source for per-cell seed/beta forwarding and SKIPs cloud
    cells until the probe passes (see check_prereqs.cloud_seed_beta_capability_probe).
    Until then no cloud cell launches; this is kept so the contract is written
    down and the lane is one capability away from live.
    """
    return ["python", "tuner.py", "cloud-pipeline", "--method", method,
            "--train-dataset-name", dataset_name, "--yes"]


def select_invocation(cell: Cell, lane: str, *, materialized_recipe_path: Path,
                      dataset_name: Optional[str], recipe: dict) -> list:
    """Pick the tuner invocation for a cell + lane, enforcing lane constraints.

    Bridge cells are LOCAL-LANE ONLY: their OpenMOSS training data is
    do-not-redistribute and is never published to the hub, so a bridge cell on
    the cloud lane is a structurally invalid request and ABORTS (it can never
    become runnable on cloud). This mirrors check_prereqs.check_cell so the
    constraint is enforced at both the gate and the dispatcher.
    """
    if cell.coordinate.is_bridge and lane == "cloud":
        raise MatrixError(
            f"bridge cell '{cell.coordinate.run_id()}' cannot run on the cloud "
            f"lane: bridge training data is do-not-redistribute and is never "
            f"published to the hub. Bridge arms are LOCAL-LANE ONLY."
        )
    if lane == "cloud":
        return cloud_invocation(cell.method, dataset_name, recipe)
    return local_invocation(materialized_recipe_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 run-matrix expander + launcher.")
    parser.add_argument("--matrix",
                        default=str(Path(__file__).resolve().parent.parent / "config" / "matrix.yaml"))
    # Path defaults anchor on _REPO_ROOT (this file's location) so they resolve
    # identically from the repo root or the skill dir (MT4). Callers can override
    # any of them with an explicit (absolute or CWD-relative) path.
    parser.add_argument("--recipes-dir",
                        default=str(_REPO_ROOT / "experiment" / "phase1" / "recipes"))
    parser.add_argument("--data-root",
                        default=str(_REPO_ROOT / "experiment" / "phase1" / "data"))
    parser.add_argument("--run-records-dir",
                        default=str(_REPO_ROOT / "experiment" / "phase1" / "run_records"))
    parser.add_argument("--research-repo-root", default=str(_REPO_ROOT))
    parser.add_argument("--tuner-root", default=str(_REPO_ROOT / "synaptic-tuner"))
    parser.add_argument("--lane", choices=["local", "cloud"], default="local")
    parser.add_argument("--dry-run", action="store_true",
                        help="Expand + materialize + print commands; launch nothing, write nothing.")
    parser.add_argument("--check-only", action="store_true",
                        help="Run the prereq gate per cell and report; launch nothing.")
    return parser


def _expand_with_count_banner(args) -> list:
    """Load the matrix, expand it (asserting the pre-registered counts), and print
    the count banner + bridge-lane safety check. Shared by --dry-run and
    --check-only so both surface the same pre-registration guard before diverging.
    """
    matrix = load_yaml(Path(args.matrix))
    cells = expand_matrix(matrix)
    print(f"Matrix '{matrix['matrix_version']}' expanded to {len(cells)} cells "
          f"({EXPECTED_COUNT_4B} @ 4B + {EXPECTED_COUNT_8B} @ 8B + "
          f"{EXPECTED_COUNT_BRIDGE} bridge). Count assertions PASSED.")
    # Belt-and-suspenders: a bridge cell on the cloud lane is a config error.
    assert_bridge_lane_safety(cells, args.lane)
    return cells


def expand_and_report(args) -> int:
    """--dry-run path: expand + materialize + print per-cell commands. No gate,
    no launch, no writes. This is the cheap preview; --check-only is the gate.
    """
    cells = _expand_with_count_banner(args)
    recipes_dir = Path(args.recipes_dir)
    for cell in cells:
        base = load_yaml(recipes_dir / f"{cell.recipe}.yaml")
        materialized = materialize_recipe(base, cell, args.lane)
        line = f"  [{cell.coordinate.run_id()}] {cell.method} seed={cell.coordinate.seed}"
        if cell.coordinate.override:
            line += f" {cell.coordinate.override[0]}={materialized['training'].get(cell.coordinate.override[0])}"
        print(line)
    return 0


def check_and_report(args) -> int:
    """--check-only path: expand, then run the prereq gate per cell and report
    PASS / SKIP / ABORT. Launches nothing and writes nothing.

    Fail-closed semantics (mirroring check_prereqs.check_cell):
      - a hard PrereqError aborts the WHOLE matrix (return 1) — there is no
        meaningful partial run when a launch precondition is structurally absent;
      - a CellPrereqResult.skip is a per-cell SKIP (not-yet-ready arm degrades
        gracefully: cloud-data-unpublished, bridge-prereqs-absent), the matrix
        gate continues, and the cell is reported SKIPPED.

    Per-cell inputs are derived statically from the base recipe + the cell +
    args — no staging and no tuner execution. The only launch-time-only check
    (hub-dataset revision on the cloud lane) is already handled inside check_cell
    as a SKIP, so nothing here fakes a PASS for a value it cannot verify yet.
    """
    cells = _expand_with_count_banner(args)
    recipes_dir = Path(args.recipes_dir)
    data_root = Path(args.data_root)
    research_repo_root = Path(args.research_repo_root)

    n_pass = n_skip = 0
    print(f"Prereq gate (lane={args.lane}) per cell:")
    for cell in cells:
        base = load_yaml(recipes_dir / f"{cell.recipe}.yaml")
        model_tag = model_tag_from_recipe(base)
        train_file, dev_file = dataset_basenames(base)
        dataset_name = (base.get("dataset") or {}).get("hf_dataset_name")
        try:
            result = check_prereqs.check_cell(
                lane=args.lane,
                method=cell.method,
                model_tag=model_tag,
                train_file=train_file,
                dev_file=dev_file,
                data_root=data_root,
                research_repo_root=research_repo_root,
                dataset_name=dataset_name,
                is_bridge=cell.coordinate.is_bridge,
            )
        except check_prereqs.PrereqError as exc:
            # Hard precondition failure -> abort the WHOLE matrix (fail-closed).
            print(f"  [{cell.coordinate.run_id()}] ABORT: {exc}")
            print("Prereq gate ABORTED the matrix (hard precondition absent). "
                  "Launch nothing until it is resolved.")
            return 1
        if result.skip:
            n_skip += 1
            print(f"  [{cell.coordinate.run_id()}] SKIP: {result.skip_reason}")
        else:
            n_pass += 1
            detail = f" {result.details}" if result.details else ""
            print(f"  [{cell.coordinate.run_id()}] PASS{detail}")
    print(f"Prereq gate complete: {n_pass} PASS, {n_skip} SKIP, 0 ABORT "
          f"(of {len(cells)} cells). No cell launched.")
    return 0


def main(argv: Optional[list] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.check_only:
        # The gate: expand, assert counts, and run check_prereqs per cell.
        return check_and_report(args)
    if args.dry_run:
        # The preview: expand, assert counts, print per-cell commands. No gate.
        return expand_and_report(args)
    # A real launch is a cost-incurring, side-effecting operation. Per the SKILL
    # CLI Discipline it must be an explicit, gated step; this entry point refuses
    # to launch without --dry-run/--check-only having been the operator's path.
    print("Refusing to launch without an explicit confirmed launch flow. Use")
    print("--dry-run to preview, --check-only to gate, then launch per the SKILL")
    print("runbook (Common Patterns). Cost-incurring launches are never implicit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
