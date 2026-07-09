"""Shared per-family gate-decision / dosed-run machinery for the cross-family
J-space layer contrast.

Ported from `j-space-midband-write-sweep-qwen3-4b/pipeline.py`, generalized
to take `family` as an explicit argument everywhere instead of hardcoding
Qwen3-4B paths, and to resolve EOS ids per-family (`model_lib.resolve_eos_ids`)
instead of the predecessor's Qwen-only `<|im_end|>` lookup. `calibrate_dose.py`
and `run_contrast.py` both import from here so the dosed-row generation loop
is defined exactly once per family, matching the predecessor's own
calibrate_dose.py / pipeline.py split.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from family_config import layer_dir_name, load_family  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402

MAX_NEW = gl.MAX_NEW_CAP


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def load_direction_vector(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def layer_paths(family: str, hs_index: int) -> dict[str, Path]:
    layer_name = layer_dir_name(hs_index)
    root = HERE / "analysis-committed" / family / "layers" / layer_name
    return {"u_d": root / f"u_d_{layer_name}.json", "c_hat": root / f"c_hat_{layer_name}.json"}


def load_rows(family: str, role: str, split: str) -> list[dict]:
    """Join the private materialized eval rows (question/aliases, from
    `mine_eval_pool.py`) against the committed split manifest (row_key ->
    fit|held_out, from `split_fit_heldout.py`) on the fly, so no separate
    "rows_with_split" materialization step is needed per family."""
    rows_path = HERE / "analysis" / family / "eval_rows.jsonl"
    split_path = HERE / "analysis-committed" / family / "split_manifest.json"
    split_by_key = {
        r["row_key"]: r["split"] for r in json.loads(split_path.read_text())["rows"]
    }
    return [
        r for r in load_jsonl(rows_path)
        if r["role"] == role and split_by_key.get(r["row_key"]) == split
    ]


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


def compute_gate_decisions(family: str, rows: list[dict], hs_index: int) -> list[dict]:
    extract_tensors = HERE / "analysis" / family / "anchor_extract.safetensors"
    build_manifest_path = HERE / "analysis-committed" / family / "build_manifest_layers.json"
    gate_fit_path = HERE / "analysis-committed" / family / "gate_fit_layers.json"

    tensors = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(str(extract_tensors))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors.items()}
    layer_name = layer_dir_name(hs_index)
    u_d = load_direction_vector(layer_paths(family, hs_index)["u_d"])
    build = json.loads(build_manifest_path.read_text())["layers"][layer_name]
    gate = json.loads(gate_fit_path.read_text())["layers"][layer_name]
    mu_d, sigma_d, tau = build["mu_d"], build["sigma_d"], gate["tau_frozen"]

    out = []
    for row in rows:
        h = fresh[f"hs{hs_index}__{row['row_key'].replace(':', '_')}"]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        rec = dict(row)
        rec.update({"hs_index": hs_index, "proj_d": proj_d, "z_d": z_d,
                    "score_neg_z_d": score, "tau": tau, "fire": bool(score >= tau)})
        out.append(rec)
    return out


def run_one_row(family: str, model, controller, tokenizer, dev, eos_ids: list[int],
                 row: dict, strength_if_dosed: float) -> dict:
    prompt = ml.render(family, tokenizer, row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, eos_ids, max_new=MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if row["fire"]:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, eos_ids,
            max_new=MAX_NEW,
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text, readback, terminated_naturally, n_new = (
            base_text, None, base_terminated, int(base_new.shape[0])
        )

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = grader.grade_one(out_text, row.get("aliases"))
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"], "fire": row["fire"], "readback_measured": readback,
        "n_new_tokens": n_new, "terminated_naturally": terminated_naturally,
        "clean_tighten": ct["clean_tighten"], "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct, "old_grade": old_grade,
    }


def grade_population(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def run_layer(family: str, model, tokenizer, hs_index: int, rows: list[dict],
              dose_target: float, *, run_log=None) -> dict:
    """Run one family+layer's rows through the dosed pass.

    If `run_log` is given (a tuner `RunLog` opened by the caller at a
    per-family/per-layer path), each row's result is appended and fsynced
    as it completes and rows already recorded on a prior, killed run are
    skipped -- see `experiments/common/README-runlog.md` in the root repo.
    With `run_log=None` (the default, used by `calibrate_dose.py`'s
    per-dose ladder where the same rows repeat under different doses and a
    single run log path would collide), the whole-arm-in-memory behavior is
    unchanged.
    """
    layer_name = layer_dir_name(hs_index)
    build = json.loads((HERE / "analysis-committed" / family / "build_manifest_layers.json").read_text())
    build = build["layers"][layer_name]
    strength = dose_target / build["sigma_c"]
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(
        layer_paths(family, hs_index)["c_hat"]
    )
    dev = next(model.parameters()).device
    eos_ids = ml.resolve_eos_ids(family, tokenizer)
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    try:
        if run_log is not None:
            pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
            for row in pending:
                rec = run_one_row(family, model, controller, tokenizer, dev, eos_ids, row, strength)
                run_log.record(row["row_key"], rec)
            on_disk = {rec["key"]: rec for rec in load_jsonl(run_log.path)}
            records = [on_disk[row["row_key"]] for row in rows]
        else:
            records = [run_one_row(family, model, controller, tokenizer, dev, eos_ids, r, strength)
                       for r in rows]
    finally:
        h_ctrl.remove()
        controller.reset()
    confab = [r for r in records if r["role"] == "confab"]
    known = [r for r in records if r["role"] == "known_correct_answered"]
    dosed = [r for r in records if r["fire"]]
    readbacks = [r["readback_measured"] for r in dosed if r["readback_measured"] is not None]
    within = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    return {
        "hs_index": hs_index, "n_rows": len(records), "n_fired": len(dosed),
        "readback_mean": float(np.mean(readbacks)) if readbacks else None,
        "frac_readback_within_tol": (sum(within) / len(within)) if within else None,
        "collapse_rate_on_dosed": (
            sum(1 for r in dosed if r["grade"]["degenerate"]) / len(dosed) if dosed else None
        ),
        "confab_tighten": grade_population(confab, "clean_tighten"),
        "known_correct_cost_control": grade_population(known, "not_well_formed_correct"),
    }
