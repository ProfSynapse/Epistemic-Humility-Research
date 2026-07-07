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

AMBIENT-RELATIVE DOSE RESOLUTION
---------------------------------
`cell.yaml`'s dose1/dose2/dose3 arms carry k-multipliers (5, 7, 9), not raw
setpoints -- per AMENDMENT.md "Design -> Dose calibration", erase_write writes
an absolute coordinate, so a fixed absolute strength either over- or under-
doses a direction depending on that direction's own ambient (un-intervened)
projection scale. Before running any direction in `--only`/the full sweep,
this script measures each direction's `ambient_dir` (mean absolute projection
of the un-intervened decode-time hidden state onto that direction's unit
vector, over a deterministic ~48-row stratified pool sample -- reusing the
method proven in the pre-flight `dose_escalation_ambient_relative.py`) and
resolves strength = k * ambient_dir / sigma_dir per arm before materializing
that direction's config. Directions sharing a layer (e.g. the smoke's
pos_ctrl_L34 / L34_succ_pc0 / randctrl_L34_succ_pc0, all block 33) share ONE
ambient-measurement generate() pass per row, not one per direction. Resolved
(ambient, sigma, strengths) are recorded per direction in
`analysis/ambient_calibration.json` for provenance. `--dry-run` never performs
this GPU pass -- it reports arm strengths as "ambient-relative (computed at
real-run time)" and leaves `cell.yaml`'s k-multiplier placeholders in the
parsed (never-launched) config.

GEN_STREAM FIRING PROBE (WIRING CHECK, NOT A DOSE)
----------------------------------------------------
Do not confuse this with the arm doses above. `run_steer`'s smoke gate runs a
gen_stream decode-hook-firing PROBE before any arm executes, at a strength
independent of a recipe's own dose ladder (tuner PR #138 added
`SmokeConfig.gen_stream_probe_strength` to make that strength overridable;
`synaptic-tuner` 56c7c6b). That probe exists ONLY to prove the decode hook is
WIRED -- a global model+mechanism property, already confirmed once for this
substrate -- never to test whether a given direction moves behavior. Most
screened directions (random controls, most dark candidates) are EXPECTED to
be behaviorally inert; if the probe used a direction's own coherent dose, an
expected-null direction's byte-identical output would register as "hook not
wired" and abort that direction, losing the null rows the screen needs. So
this script sets `smoke.gen_stream_probe_strength = GEN_STREAM_PROBE_L /
sigma_dir` per direction -- the SAME absolute over-driven setpoint for every
direction regardless of its own ambient/sigma, guaranteed (per an empirical
sweep against this smoke set's hardest-to-fire direction) to garble output if
the hook fires at all. This is completely separate from `arm_strengths`
above, which stay ambient-relative per direction and are what actually gets
recorded as each arm's dose.

MODEL RELOAD COST: `run_steer` loads the model+tokenizer itself
(`_load_model_and_tokenizer`) inside every call; there is no supported way to
share one loaded model across the 34 calls without editing the tuner (out of
scope -- see the project's mechinterp-cells skill invariants). Each direction
pays its own model-load cost; see the cost estimate in this experiment's build
report, not duplicated here. The ambient-relative dose resolution above adds
exactly ONE extra model load per invocation (shared across every direction
that invocation is about to run, freed before the per-direction run_steer
loop starts), not one per direction.

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

# Ambient-relative dose ladder (AMENDMENT.md "Design -> Dose calibration"):
# strength = k * ambient_dir / sigma_dir, baseline always 0.0 (set directly,
# never resolved from here). k values are the pre-flight-calibrated median
# clean-flip (7) bracketed by its observed range (5, 9); see NOTEBOOK.md.
AMBIENT_K_LADDER: dict[str, float] = {"dose1": 5.0, "dose2": 7.0, "dose3": 9.0}
# ~48-row stratified sample (half confab_on_unanswerable True/False) is the
# pre-flight's own n=24 doubled for a more representative ambient estimate;
# see load_ambient_rows.
AMBIENT_N_ROWS = 48
# Short decode is enough to estimate a stable ambient mean (matches the
# pre-flight dose_escalation_ambient_relative.py MAX_NEW).
AMBIENT_MAX_NEW_TOKENS = 16
AMBIENT_PROVENANCE_PATH = HERE / "analysis" / "ambient_calibration.json"  # gitignored (analysis/)

# gen_stream firing PROBE (wiring check, NOT a dose): tuner PR #138
# (SmokeConfig.gen_stream_probe_strength, synaptic-tuner 56c7c6b) lets a cell
# override the fixed-strength decode-hook-firing check the smoke gate runs
# before any arm executes. That check exists ONLY to prove the decode hook is
# wired (fires on every decode step) -- a global model+mechanism property --
# and must never be conflated with "this direction moves behavior": most
# screened directions (random controls, most dark candidates) are SUPPOSED to
# be behaviorally inert, so probing at a direction's own coherent dose would
# make an expected-null direction's byte-identical probe output register as
# "hook not wired" and abort it, losing the null rows the screen needs. The
# probe must instead be a large, OVER-DRIVEN absolute setpoint guaranteed to
# garble output if the hook fires at all, regardless of whether the direction
# is a real lever. GEN_STREAM_PROBE_L (1000.0) is that absolute setpoint,
# empirically found on the free 3090 against the hardest-to-fire direction
# among the smoke set -- the random control randctrl_L34_succ_pc0 (ambient
# 4.68, the smallest of the three, so the least likely to garble at a given
# strength): a sweep of {300,500,550,600,650,700,800,1200} found unreliable
# firing at <=600 (3/4 or fewer rows garbled) and reliable firing (4/4 rows)
# from 650 upward; 1000 keeps a ~1.5x margin above that empirical threshold.
# Applied per direction as gen_stream_probe_strength = GEN_STREAM_PROBE_L /
# sigma_dir (see compute_ambient_relative_strengths) so every direction's
# PROBE SETPOINT (strength * sigma, the erase_write convention) is the SAME
# absolute value regardless of that direction's own sigma -- unlike the arm
# doses (AMBIENT_K_LADDER), which stay ambient-relative per direction. A
# direction whose real dose ladder ever exceeds this margin would need a
# larger L; not the case for any direction here (top ambient-relative dose
# among the smoke set is pos_ctrl_L34's dose3 ~= 253).
GEN_STREAM_PROBE_L = 1000.0


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
    recipe: dict[str, Any],
    direction: str,
    arm_strengths: dict[str, float] | None = None,
    gen_stream_probe_strength: float | None = None,
) -> dict[str, Any]:
    """Deep copy of the base recipe with `law.readout` overridden to
    `direction`, every arm name prefixed `<direction>__<arm>` (the convention
    `cell.yaml`/`gates.yaml` document), and every repo-root-relative path
    (`surface.rows_path`, `execution.output_path`, every `readouts[*].path`)
    rewritten absolute so the result parses and runs correctly regardless of
    CWD (see module docstring "PATH FIX").

    `arm_strengths`, if given, is `{base_arm_name: resolved_strength}` (e.g.
    from `compute_ambient_relative_strengths`) -- looked up by the arm's BASE
    name (before prefixing) and overwrites `cell.yaml`'s k-multiplier
    placeholder with this direction's actual ambient-relative setpoint. Arms
    absent from the dict (baseline) keep `cell.yaml`'s own value (0.0).

    `gen_stream_probe_strength`, if given, overrides `smoke.gen_stream_probe_
    strength` (tuner PR #138) -- the WIRING-CHECK probe the smoke gate runs
    before any arm, distinct from `arm_strengths` above (see module docstring
    "GEN_STREAM FIRING PROBE"). `None` leaves `cell.yaml`'s own value (unset,
    so the tuner's built-in 100.0 default applies).

    `--dry-run` never passes either override, so a dry-run config keeps the
    unresolved placeholders (see module docstring "AMBIENT-RELATIVE DOSE
    RESOLUTION")."""
    cfg = copy.deepcopy(recipe)

    cfg["law"]["readout"] = direction
    for arm in cfg["arms"]:
        base_name = arm["name"]
        if arm_strengths and base_name in arm_strengths:
            arm["strength"] = float(arm_strengths[base_name])
        arm["name"] = f"{direction}__{base_name}"
    if gen_stream_probe_strength is not None:
        cfg.setdefault("smoke", {})["gen_stream_probe_strength"] = float(gen_stream_probe_strength)

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
            f"arms={arm_names} strengths=ambient-relative (computed at real-run time) "
            f"{'(already complete, would skip)' if complete else ''}"
        )

    print(
        f"dry-run summary: {n_ok}/{len(names)} configs parsed ok, "
        f"{n_already_complete}/{len(names)} already complete in the shared output"
    )
    return 0 if n_ok == len(names) else 1


# ---------------------------------------------------------------------------
# Ambient-relative dose resolution: one shared model load, measuring every
# about-to-run direction's ambient projection before any run_steer call.
# ---------------------------------------------------------------------------


def _load_callable(spec: str):
    """'module:callable' -> the resolved callable. Mirrors
    `MechInterp.cli._load_callable`, duplicated locally (not imported) so this
    script never depends on a leading-underscore tuner internal across module
    boundaries -- same rationale as `_load_model_and_tokenizer` below."""
    import importlib

    module_path, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module_path), attr)


def _load_model_and_tokenizer(model_name: str, adapter: str | None):
    """Mirrors `MechInterp.cli._load_model_and_tokenizer` exactly (transformers
    5.x dtype-kwarg rename included). Duplicated rather than imported: that
    tuner function is a leading-underscore module-private helper, and this
    script's rule is to touch the tuner only through its public entrypoints
    (`run_steer`, `load_steer_config`, ...), never its internals -- same
    precedent as `dose_escalation_ambient_relative.py`'s own `load_model`."""
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    major = int(transformers.__version__.split(".")[0])
    dtype_kwarg = {"dtype": torch.bfloat16} if major >= 5 else {"torch_dtype": torch.bfloat16}
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", **dtype_kwarg)
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, tokenizer


def load_ambient_rows(rows_path: Path, n: int = AMBIENT_N_ROWS) -> list[dict]:
    """Deterministic sample of `n` pool rows, half confab_on_unanswerable=True
    / half False (category-diverse first pass, then backfill) -- the exact
    stratification `dose_escalation_ambient_relative.py::load_mixed_rows` used
    for the pre-flight sweep, generalized from its n=24 to n=48 here so the
    measured ambient is representative of the whole pool this screen scores."""
    by_confab: dict[bool, list[dict]] = {True: [], False: []}
    seen_cat: dict[bool, set] = {True: set(), False: set()}
    with rows_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            confab = bool(row.get("confab_on_unanswerable"))
            cat = row.get("category_canon")
            bucket = by_confab[confab]
            seen = seen_cat[confab]
            if cat not in seen and len(bucket) < n // 2:
                bucket.append(row)
                seen.add(cat)
    if any(len(by_confab[k]) < n // 2 for k in (True, False)):
        with rows_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                confab = bool(row.get("confab_on_unanswerable"))
                bucket = by_confab[confab]
                if len(bucket) < n // 2 and row not in bucket:
                    bucket.append(row)
    rows = by_confab[True][: n // 2] + by_confab[False][: n // 2]
    return rows[:n]


class _AmbientCapture:
    """Forward hook: records the un-intervened decode-step hidden-state
    vector at this layer. `hidden.shape[1] == 1` identifies a decode step (one
    new token under KV-cached generation), not the multi-token prefill forward
    pass -- the same discriminator
    `dose_escalation_ambient_relative.py::AmbientHook` uses. Returns `output`
    unchanged: this only observes, it never intervenes (there is no "off" to
    turn off -- no InterventionHook is registered during this pass at all)."""

    def __init__(self) -> None:
        self.vectors: list = []

    def __call__(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if hidden.shape[1] == 1:
            self.vectors.append(hidden[0, 0, :].detach().to("cpu"))
        return output


def measure_ambient(
    model, tokenizer, render_fn, rows: list[dict], direction_records: dict[str, dict]
) -> dict[str, float]:
    """Mean absolute projection of the un-intervened decode-time hidden state
    onto each direction's unit vector, pooled over `rows`.

    Groups directions by layer and registers one `_AmbientCapture` hook per
    DISTINCT layer, so directions sharing a layer (e.g. the smoke's
    pos_ctrl_L34 / L34_succ_pc0 / randctrl_L34_succ_pc0, all block 33) are
    measured from the SAME generate() pass per row, not one pass per
    direction."""
    import torch
    from MechInterp.intervention import get_decoder_layer

    dev = next(model.parameters()).device
    layers = sorted({int(rec["layer"]) for rec in direction_records.values()})
    captures = {layer: _AmbientCapture() for layer in layers}
    handles = [
        get_decoder_layer(model, layer).register_forward_hook(cap)
        for layer, cap in captures.items()
    ]
    try:
        for row in rows:
            prompt = render_fn(row)
            enc = tokenizer(prompt, return_tensors="pt").to(dev)
            with torch.no_grad():
                model.generate(
                    **enc,
                    max_new_tokens=AMBIENT_MAX_NEW_TOKENS,
                    min_new_tokens=AMBIENT_MAX_NEW_TOKENS,
                    do_sample=False,
                    num_beams=1,
                )
    finally:
        for h in handles:
            h.remove()

    ambient_by_name: dict[str, float] = {}
    for name, rec in direction_records.items():
        layer = int(rec["layer"])
        vecs = captures[layer].vectors
        if not vecs:
            raise RuntimeError(
                f"no decode-step captures at layer {layer} for direction {name!r}; "
                "cannot measure ambient (did generate() run at least one decode step?)"
            )
        stacked = torch.stack(vecs, dim=0).to(torch.float64)
        unit_vec = torch.tensor(rec["vector_np"], dtype=torch.float64)
        proj = stacked @ unit_vec
        ambient_by_name[name] = float(proj.abs().mean())
    return ambient_by_name


def resolve_ambient_strengths(
    direction_records: dict[str, dict], ambient_by_name: dict[str, float]
) -> dict[str, dict]:
    """{name: {"ambient": a, "sigma": s, "strengths": {"dose1": k5*a/s, ...},
    "gen_stream_probe_strength": L/s}}.

    `strengths` (the arm doses) follow AMENDMENT.md "Design -> Dose
    calibration": strength = k * ambient_dir / sigma_dir for k in
    AMBIENT_K_LADDER. Baseline is NOT resolved here -- it stays cell.yaml's
    own 0.0, applied by materialize_direction_config.

    `gen_stream_probe_strength` is UNRELATED to ambient (see module docstring
    "GEN_STREAM FIRING PROBE"): it is GEN_STREAM_PROBE_L / sigma_dir, the same
    fixed absolute wiring-check setpoint for every direction regardless of its
    own ambient scale."""
    out: dict[str, dict] = {}
    for name, rec in direction_records.items():
        ambient = ambient_by_name[name]
        sigma = float(rec.get("sigma", 1.0))
        if sigma == 0.0:
            raise ValueError(
                f"direction {name!r}: sigma is 0.0, cannot resolve an ambient-relative strength"
            )
        strengths = {arm: k * ambient / sigma for arm, k in AMBIENT_K_LADDER.items()}
        out[name] = {
            "ambient": ambient,
            "sigma": sigma,
            "strengths": strengths,
            "gen_stream_probe_strength": GEN_STREAM_PROBE_L / sigma,
        }
    return out


def _record_ambient_provenance(resolved: dict[str, dict], ambient_n_rows: int) -> None:
    """Merge this invocation's per-direction (ambient, sigma, strengths,
    gen_stream_probe_strength) into the shared provenance file
    (read-modify-write, so e.g. a 3-direction smoke followed later by the full
    34-direction run accumulates rather than clobbers the smoke's record)."""
    import datetime

    AMBIENT_PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if AMBIENT_PROVENANCE_PATH.is_file():
        with AMBIENT_PROVENANCE_PATH.open() as f:
            existing = json.load(f)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for name, info in resolved.items():
        existing[name] = {
            "ambient": info["ambient"],
            "sigma": info["sigma"],
            "strengths": info["strengths"],
            "gen_stream_probe_strength": info["gen_stream_probe_strength"],
            "ambient_n_rows": ambient_n_rows,
            "computed_at": now,
        }
    with AMBIENT_PROVENANCE_PATH.open("w") as f:
        json.dump(existing, f, indent=2, sort_keys=True)


def compute_ambient_relative_strengths(
    recipe: dict[str, Any], directions: list[str], args: argparse.Namespace
) -> dict[str, dict]:
    """Load the model ONCE (shared across every direction in `directions`,
    regardless of how many distinct layers they span), measure each
    direction's ambient projection, resolve the k*ambient/sigma dose ladder,
    free the model, and record provenance. See AMENDMENT.md "Design -> Dose
    calibration" for the k values and dose_escalation_ambient_relative.py for
    the measurement method this reuses."""
    import gc

    import torch

    from MechInterp.probe import load_frozen_direction

    readout_path_by_name = {r["name"]: _to_repo_abs(r["path"]) for r in recipe["readouts"]}
    direction_records = {
        name: load_frozen_direction(readout_path_by_name[name]) for name in directions
    }

    render_fn = _load_callable(args.render_fn)
    rows_path = Path(_to_repo_abs(recipe["surface"]["rows_path"]))
    ambient_rows = load_ambient_rows(rows_path, AMBIENT_N_ROWS)
    n_true = sum(1 for r in ambient_rows if r.get("confab_on_unanswerable"))
    n_layers = len({int(rec["layer"]) for rec in direction_records.values()})
    print(
        f"Ambient calibration: {len(ambient_rows)} rows "
        f"(confab=True: {n_true}, confab=False: {len(ambient_rows) - n_true}), "
        f"{len(directions)} direction(s) across {n_layers} distinct layer(s)"
    )

    model, tokenizer = _load_model_and_tokenizer(args.model, args.adapter)
    try:
        ambient_by_name = measure_ambient(model, tokenizer, render_fn, ambient_rows, direction_records)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    resolved = resolve_ambient_strengths(direction_records, ambient_by_name)
    _record_ambient_provenance(resolved, ambient_n_rows=len(ambient_rows))
    for name, info in resolved.items():
        rounded = {k: round(v, 4) for k, v in info["strengths"].items()}
        print(
            f"  [{name}] layer={direction_records[name]['layer']} "
            f"ambient={info['ambient']:.4f} sigma={info['sigma']:.4f} strengths={rounded} "
            f"gen_stream_probe_strength={info['gen_stream_probe_strength']:.4f}"
        )
    return resolved


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

    # Ambient-relative dose resolution: measure every direction that is not
    # already complete, in ONE shared model load, before the per-direction
    # run_steer loop below (each iteration of which pays its own reload cost
    # regardless -- see module docstring "MODEL RELOAD COST").
    membership = load_arm_membership(output_path)
    to_run = [d for d in names if not direction_complete(d, recipe, membership, n_rows)]
    arm_strengths_by_direction: dict[str, dict[str, float]] = {}
    probe_strength_by_direction: dict[str, float] = {}
    if to_run:
        resolved = compute_ambient_relative_strengths(recipe, to_run, args)
        arm_strengths_by_direction = {name: info["strengths"] for name, info in resolved.items()}
        probe_strength_by_direction = {
            name: info["gen_stream_probe_strength"] for name, info in resolved.items()
        }

    n_run = 0
    n_skipped = 0
    for direction in names:
        membership = load_arm_membership(output_path)
        if direction_complete(direction, recipe, membership, n_rows):
            print(f"[{direction}] already complete ({n_rows} rows x 4 arms) -- skipping")
            n_skipped += 1
            continue

        cfg_dict = materialize_direction_config(
            recipe,
            direction,
            arm_strengths_by_direction.get(direction),
            probe_strength_by_direction.get(direction),
        )
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
