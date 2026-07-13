"""Gate-decision / dosed-run machinery for the rep2 multi-source layer
contrast.

Ported from `j-space-midband-write-sweep-qwen3-4b/pipeline.py` (the frozen
instrument all J-space layer-site experiments to date have imported
unmodified). This fork exists for two reasons the frozen file cannot absorb
without breaking its other consumers:

1. Anchor tensors for this run are split across TWO safetensors files: the
   fresh multi-source confab anchors extracted by
   `extract_multisource_confab_anchor.py` (this experiment's own analysis/)
   and the known_correct_answered anchors REUSED verbatim from rep1
   (`materialize_known_side_reuse.py`'s output). `compute_gate_decisions`
   here merges both.
2. Per-row persistence through the tuner's resumable RunLog (see
   `experiments/common/README-runlog.md`), ported from the cross-family
   scaffold's `pipeline.py:run_layer`. Rep1's own Outcome flagged the
   missing-per-row-persistence gap as a known limitation to fix before this
   successor's sign (its NOTEBOOK.md pre-outcome commitment 3 / Outcome
   consequence-carried-forward item (5)).

`load_run_log_class` availability note: `shared/utilities/run_log.py` lives
on the tuner branch `feature/runlog` (Synaptic-Tuner PR #141), not yet
merged to `synaptic-tuner`'s `main`. The submodule pin must be bumped to
include that branch (or its merge) before `bin/exp sign` on this
experiment, since a signed instrument cannot be patched mid-run to add
resumability after a crash has already happened. Until then this module's
RunLog import fails loudly at call time (never silently degrades to an
unlogged loop).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"

for p in (str(SOURCE),):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from layers import layer_dir_name  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402

MAX_NEW = gl.MAX_NEW_CAP


def load_run_log_class():
    """Import the tuner's resumable per-item RunLog, at call time (not at
    module import time) so a checkout without it only fails when resume
    support is actually needed. See this module's docstring and
    `experiments/common/README-runlog.md`."""
    tuner_str = str(TUNER_DIR)
    if tuner_str not in sys.path:
        sys.path.insert(0, tuner_str)
    try:
        from shared.utilities.run_log import RunLog, RunLogError
    except ImportError as exc:
        raise ImportError(
            "shared.utilities.run_log.RunLog is not available in this "
            "synaptic-tuner checkout. It lives on the tuner branch "
            "'feature/runlog' (Synaptic-Tuner PR #141), not yet merged to "
            "main. Check out that branch inside synaptic-tuner/, or bump "
            "this repo's submodule pin once it merges, before running with "
            "resume support here. This pin bump must happen before "
            "`bin/exp sign` on this experiment."
        ) from exc
    return RunLog, RunLogError


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def load_direction_vector(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{sanitize_key(row_key)}"


def layer_paths(hs_index: int) -> dict[str, Path]:
    layer_name = layer_dir_name(hs_index)
    root = SOURCE / "analysis-committed" / "layers" / layer_name
    return {
        "u_d": root / f"u_d_{layer_name}.json",
        "c_hat": root / f"c_hat_{layer_name}.json",
    }


def load_tensors(tensor_paths: list[Path]) -> dict[str, np.ndarray]:
    """Merge tensors from multiple safetensors files (confab-side fresh
    extract + known-side reused extract) into one lookup dict, keyed the
    same way both extractors write them (`hs{H}__{sanitized_row_key}`)."""
    from safetensors.numpy import load_file

    merged: dict[str, np.ndarray] = {}
    for p in tensor_paths:
        for k, v in load_file(str(p)).items():
            merged[k] = np.asarray(v, dtype=np.float64)
    return merged


def compute_gate_decisions(
    rows: list[dict], hs_index: int, tensors: dict[str, np.ndarray]
) -> list[dict]:
    layer_name = layer_dir_name(hs_index)
    u_d = load_direction_vector(layer_paths(hs_index)["u_d"])
    build = json.loads(
        (SOURCE / "analysis-committed" / "build_manifest_layers.json").read_text()
    )["layers"][layer_name]
    gate = json.loads(
        (SOURCE / "analysis-committed" / "gate_fit_layers.json").read_text()
    )["layers"][layer_name]
    mu_d, sigma_d, tau = build["mu_d"], build["sigma_d"], gate["tau_frozen"]

    out = []
    for row in rows:
        h = tensors[tensor_key(hs_index, row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        rec = dict(row)
        rec.update({
            "hs_index": hs_index,
            "proj_d": proj_d,
            "z_d": z_d,
            "score_neg_z_d": score,
            "tau": tau,
            "fire": bool(score >= tau),
        })
        out.append(rec)
    return out


def run_one_row(model, controller, tokenizer, dev, row: dict, strength_if_dosed: float) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, max_new=MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if row["fire"]:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, max_new=MAX_NEW
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text = base_text
        readback = None
        terminated_naturally = base_terminated
        n_new = int(base_new.shape[0])

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = grader.grade_one(out_text, row.get("aliases"))
    return {
        "row_key": row["row_key"],
        "role": row["role"],
        "category_canon": row.get("category_canon"),
        "source": row.get("source"),
        "hs_index": row["hs_index"],
        "fire": row["fire"],
        "readback_measured": readback,
        "n_new_tokens": n_new,
        "terminated_naturally": terminated_naturally,
        "clean_tighten": ct["clean_tighten"],
        "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct,
        "old_grade": old_grade,
    }


def grade_population(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def run_layer(
    model,
    tokenizer,
    hs_index: int,
    rows: list[dict],
    dose_target: float,
    *,
    run_log=None,
) -> dict:
    """Run one layer's rows through the dosed pass.

    If `run_log` is given (a tuner `RunLog` opened by the caller at a
    per-layer path), each row's result is appended and fsynced as it
    completes, and rows already recorded on a prior, killed run are skipped
    -- see `experiments/common/README-runlog.md`. With `run_log=None` the
    whole-arm-in-memory behavior of the frozen predecessor's `run_layer` is
    unchanged (used only for ad hoc CPU-side testing; the sign-pinned
    `run_contrast.py` always passes a `run_log`).
    """
    layer_name = layer_dir_name(hs_index)
    build = json.loads(
        (SOURCE / "analysis-committed" / "build_manifest_layers.json").read_text()
    )["layers"][layer_name]
    strength = dose_target / build["sigma_c"]
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(
        layer_paths(hs_index)["c_hat"]
    )
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    try:
        if run_log is not None:
            pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
            for row in pending:
                rec = run_one_row(model, controller, tokenizer, dev, row, strength)
                run_log.record(row["row_key"], rec)
            on_disk = {rec["key"]: rec for rec in load_jsonl(run_log.path)}
            records = [on_disk[row["row_key"]] for row in rows]
        else:
            records = [
                run_one_row(model, controller, tokenizer, dev, r, strength) for r in rows
            ]
    finally:
        h_ctrl.remove()
        controller.reset()
    confab = [r for r in records if r["role"] == "confab"]
    known = [r for r in records if r["role"] == "known_correct_answered"]
    dosed = [r for r in records if r["fire"]]
    readbacks = [r["readback_measured"] for r in dosed if r["readback_measured"] is not None]
    within = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    return {
        "hs_index": hs_index,
        "n_rows": len(records),
        "n_fired": len(dosed),
        "readback_mean": float(np.mean(readbacks)) if readbacks else None,
        "frac_readback_within_tol": (sum(within) / len(within)) if within else None,
        "collapse_rate_on_dosed": (
            sum(1 for r in dosed if r["grade"]["degenerate"]) / len(dosed) if dosed else None
        ),
        "confab_tighten": grade_population(confab, "clean_tighten"),
        "known_correct_cost_control": grade_population(known, "not_well_formed_correct"),
        "records": records,
    }


def stratified_subset(rows: list[dict], n: int) -> list[dict]:
    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in sorted(rows, key=lambda rec: rec["row_key"]):
        cat = r.get("category_canon")
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(r)
    out: list[dict] = []
    idx = 0
    while len(out) < n:
        added = False
        for cat in order:
            if idx < len(by_cat[cat]):
                out.append(by_cat[cat][idx])
                added = True
                if len(out) >= n:
                    break
        if not added:
            break
        idx += 1
    return out[:n]
