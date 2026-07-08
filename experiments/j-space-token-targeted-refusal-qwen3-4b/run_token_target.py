#!/usr/bin/env python3
"""Run the J-space token-targeted refusal write experiment.

This runner is deliberately project-side: it consumes this experiment's
token_bundle.yaml plus the predecessor J-space row pool, gates, directions, and
grad/J-lens code. It writes private row-level checkpoints under analysis/ and
only aggregate summaries or fitted directions under analysis-committed/.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import random
import re
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
import yaml


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
TOKEN_DIRECTION_DIR = COMMITTED / "token_directions"
FIT_RECORDS = ANALYSIS / "fit_calibration_records.jsonl"
SMOKE_RECORDS = ANALYSIS / "smoke_records.jsonl"
FULL_RECORDS = ANALYSIS / "full_records.jsonl"
FIT_BASELINE_MODE = "fit_baseline_c_hat_only_hs23"

if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from layers import hs_to_block, layer_dir_name  # noqa: E402
from pipeline import (  # noqa: E402
    BUILD_MANIFEST_PATH,
    EXTRACT_TENSORS,
    GATE_FIT_PATH,
    compute_gate_decisions,
    layer_paths,
    load_direction_vector,
    load_jsonl,
    selected_rows,
    tensor_key,
)
from MechInterp.intervention import get_decoder_layer  # noqa: E402


PRIMARY_LAYERS = [23, 29]
HELD_OUT_ARMS = [
    "c_hat_only_hs23",
    "j_token_only_hs23",
    "c_hat_plus_j_token_hs23",
    "c_hat_plus_random_j_hs23",
    "c_hat_plus_j_token_hs29",
]
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _strip_checkpoint_text(value):
    if isinstance(value, dict):
        return {
            k: _strip_checkpoint_text(v)
            for k, v in value.items()
            if k not in {"answer_value", "raw_output", "text", "prompt", "question", "aliases"}
        }
    if isinstance(value, list):
        return [_strip_checkpoint_text(v) for v in value]
    return value


def _fsync_append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = _strip_checkpoint_text(rec)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _read_done(path: Path, mode: str) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if not path.exists():
        return done
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("mode") == mode:
            done.add((str(rec["arm"]), str(rec["row_key"])))
    return done


def _load_bundle(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _token_weights(bundle: dict) -> list[tuple[int, float, str]]:
    out: list[tuple[int, float, str]] = []
    primary = bundle["primary_bundle"]
    for rec in primary["positive_tokens"]:
        out.append((int(rec["token_id"]), float(rec["weight"]), rec["text"]))
    for rec in primary["negative_tokens"]:
        out.append((int(rec["token_id"]), -float(rec["weight"]), rec["text"]))
    return out


def _fit_rows(n_rows: int | None = None) -> list[dict]:
    rows_path = SOURCE / "analysis" / "rows_with_text.jsonl"
    rows = [
        r for r in load_jsonl(rows_path)
        if r["split"] == "fit" and r["role"] in {"confab", "known_correct_answered"}
    ]
    rows = sorted(rows, key=lambda r: (r["role"], r.get("category_canon") or "", r["row_key"]))
    if n_rows is not None:
        rng = random.Random(20260708)
        rng.shuffle(rows)
        rows = rows[:n_rows]
    return rows


def _row_prompts(tokenizer, rows: Iterable[dict]) -> list[str]:
    return [ml.render(row) for row in rows]


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if not math.isfinite(norm) or norm == 0.0:
        raise ValueError("cannot normalize zero/non-finite direction")
    return v / norm


def _direction_stats(hs_index: int, direction: np.ndarray, rows: list[dict]) -> dict:
    tensors = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(str(EXTRACT_TENSORS))
    vals = []
    for row in rows:
        h = np.asarray(tensors[tensor_key(hs_index, row["row_key"])], dtype=np.float64)
        vals.append(float(h @ direction))
    arr = np.asarray(vals, dtype=np.float64)
    sigma = float(arr.std(ddof=0))
    if sigma <= 1e-12:
        raise ValueError(f"token direction hs{hs_index} has near-zero ambient sigma")
    return {
        "mu": float(arr.mean()),
        "sigma": sigma,
        "min": float(arr.min()),
        "max": float(arr.max()),
        "n": int(arr.shape[0]),
    }


def _random_direction(hs_index: int, token_direction: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(20260708 + hs_index)
    vec = rng.normal(size=token_direction.shape).astype(np.float64)
    vec = vec - float(vec @ token_direction) * token_direction
    return _unit(vec)


def build_token_direction(
    model,
    tokenizer,
    hs_index: int,
    bundle: dict,
    rows: list[dict],
) -> dict:
    device = next(model.parameters()).device
    weights = _token_weights(bundle)
    total: torch.Tensor | None = None
    for i, prompt in enumerate(_row_prompts(tokenizer, rows), start=1):
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.enable_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
            h_l = out.hidden_states[hs_index]
            logits = out.logits[:, -1, :].float()
            objective = torch.zeros((), dtype=torch.float32, device=device)
            for token_id, weight, _text in weights:
                objective = objective + float(weight) * logits[0, token_id]
            (grad,) = torch.autograd.grad(objective, h_l, retain_graph=False)
        grad_vec = grad.detach().float().mean(dim=1).squeeze(0).cpu()
        total = grad_vec if total is None else total + grad_vec
        del out, h_l, logits, grad
        if torch.cuda.is_available() and i % 16 == 0:
            torch.cuda.empty_cache()
        if i % 32 == 0:
            print(f"[token-target] built grad hs{hs_index} {i}/{len(rows)}", flush=True)
    mean_vec = (total / float(len(rows))).numpy().astype(np.float64)
    raw_norm = float(np.linalg.norm(mean_vec))
    direction = _unit(mean_vec)
    stats = _direction_stats(hs_index, direction, rows)
    rand = _random_direction(hs_index, direction)
    rand_stats = _direction_stats(hs_index, rand, rows)
    return {
        "schema": "jspace-token-target-direction/v1",
        "model": bundle["model"],
        "hs_index": hs_index,
        "layer": hs_to_block(hs_index),
        "bundle": bundle["primary_bundle"]["name"],
        "n_fit_rows": len(rows),
        "raw_grad_norm": raw_norm,
        "vector": direction.tolist(),
        "mu": stats["mu"],
        "sigma": stats["sigma"],
        "ambient_projection": stats,
        "random_control": {
            "seed": 20260708 + hs_index,
            "vector": rand.tolist(),
            "mu": rand_stats["mu"],
            "sigma": rand_stats["sigma"],
            "ambient_projection": rand_stats,
        },
        "token_weights": [
            {"token_id": token_id, "weight": weight, "text": text}
            for token_id, weight, text in weights
        ],
        "provenance": {
            "source_rows": "experiments/j-space-midband-write-sweep-qwen3-4b/analysis/rows_with_text.jsonl",
            "split": "fit_only",
            "committed_row_text": "forbidden",
            "method": "mean gradient of weighted final-token logits wrt hidden_states[hs_index], averaged over prompt positions",
        },
    }


def direction_path(hs_index: int) -> Path:
    return TOKEN_DIRECTION_DIR / f"token_target_hs{hs_index}.json"


def load_token_direction(hs_index: int) -> dict:
    path = direction_path(hs_index)
    if not path.exists():
        raise FileNotFoundError(f"missing token direction {path}; run build-directions first")
    return json.loads(path.read_text(encoding="utf-8"))


def run_build_directions(args) -> dict:
    bundle = _load_bundle(Path(args.bundle))
    rows = _fit_rows(args.n_fit_rows)
    model, tokenizer = ml.load_model()
    try:
        TOKEN_DIRECTION_DIR.mkdir(parents=True, exist_ok=True)
        built = {}
        for hs_index in PRIMARY_LAYERS:
            rec = build_token_direction(model, tokenizer, hs_index, bundle, rows)
            direction_path(hs_index).write_text(json.dumps(rec, indent=2), encoding="utf-8")
            built[layer_dir_name(hs_index)] = {
                "path": str(direction_path(hs_index)),
                "sigma": rec["sigma"],
                "raw_grad_norm": rec["raw_grad_norm"],
                "n_fit_rows": rec["n_fit_rows"],
            }
            print(f"[token-target] wrote {direction_path(hs_index)}", flush=True)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    manifest = {
        "schema": "jspace-token-target-direction-manifest/v1",
        "bundle": str(args.bundle),
        "layers": built,
        "row_text_committed": False,
    }
    (COMMITTED / "token_direction_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return manifest


def _setup_vector_controller(vector: list[float], sigma: float, hs_index: int):
    return ml.setup_hook_from_vector(np.asarray(vector, dtype=np.float64), sigma, hs_to_block(hs_index))


def _arm_layer(arm: str) -> int:
    return 29 if arm.endswith("_hs29") else 23


def _arm_writes(arm: str, hs_index: int, j_dose: float) -> list[dict]:
    writes: list[dict] = []
    c_doses = {"hs23": 25.0, "hs29": 125.0}
    if arm.startswith("c_hat_only") or arm.startswith("c_hat_plus"):
        writes.append({"kind": "c_hat", "dose": c_doses[layer_dir_name(hs_index)]})
    if "j_token" in arm:
        writes.append({"kind": "j_token", "dose": j_dose})
    if "random_j" in arm:
        writes.append({"kind": "random_j", "dose": j_dose})
    return writes


def _run_pass_with_writes(model, tokenizer, row: dict, hs_index: int, writes: list[dict], j_dir: dict) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(next(model.parameters()).device)
    handles = []
    controllers = []
    readbacks: dict[str, float | None] = {}
    for write in writes:
        if write["kind"] == "c_hat":
            build = json.loads(BUILD_MANIFEST_PATH.read_text())["layers"][layer_dir_name(hs_index)]
            _hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(layer_paths(hs_index)["c_hat"])
            strength = float(write["dose"]) / float(build["sigma_c"])
        elif write["kind"] == "j_token":
            _hook, controller, layer_idx, sigma = _setup_vector_controller(j_dir["vector"], j_dir["sigma"], hs_index)
            strength = float(write["dose"]) / float(sigma)
        elif write["kind"] == "random_j":
            ctrl = j_dir["random_control"]
            _hook, controller, layer_idx, sigma = _setup_vector_controller(ctrl["vector"], ctrl["sigma"], hs_index)
            strength = float(write["dose"]) / float(sigma)
        else:
            raise ValueError(f"unknown write kind {write['kind']}")
        layer_module = get_decoder_layer(model, layer_idx)
        handles.append(layer_module.register_forward_hook(controller))
        controllers.append((write["kind"], write["dose"], controller, strength))
    try:
        if row["fire"] and writes:
            for _kind, _dose, controller, strength in controllers:
                controller.hook.last_readback = None
                controller.begin_pass("gen_stream", strength, attention_mask=enc["attention_mask"])
            _out, _rb, terminated_naturally, new_tokens = gl.run_pass_fixed(
                model, controllers[0][2], enc, "gen_stream", controllers[0][3], tokenizer
            )
            for kind, _dose, controller, _strength in controllers:
                rb = controller.hook.last_readback
                readbacks[kind] = (
                    float(rb["measured"][0])
                    if rb is not None and rb.get("measured")
                    else None
                )
        else:
            _out, _rb, terminated_naturally, new_tokens = gl.run_pass_fixed(
                model, controllers[0][2] if controllers else _NullController(),
                enc,
                "off",
                0.0,
                tokenizer,
            )
        text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    finally:
        for handle in handles:
            handle.remove()
        for _kind, _dose, controller, _strength in controllers:
            controller.reset()
    ct = gl.grade_clean_tighten(text, terminated_naturally)
    old_grade = grader.grade_one(text, row.get("aliases"))
    return {
        "n_new_tokens": int(new_tokens.shape[0]),
        "terminated_naturally": bool(terminated_naturally),
        "readbacks": readbacks,
        "clean_tighten": bool(ct["clean_tighten"]),
        "semantic_refuse": bool(ct["semantic_refuse"]),
        "malformed_json": not bool(ct["well_formed"]),
        "forced_continuation": not bool(terminated_naturally),
        "non_target_language_drift": bool(_CJK_RE.search(text or "")),
        "well_formed_correct": bool(old_grade["well_formed_correct"]),
        "not_well_formed_correct": not bool(old_grade["well_formed_correct"]),
        "grade": ct,
        "old_grade": old_grade,
    }


class _NullController:
    def __init__(self):
        self.hook = type("_Hook", (), {"last_readback": None})()

    def begin_pass(self, *_args, **_kwargs):
        return None

    def reset(self):
        return None


def _record_for_row(
    model,
    tokenizer,
    mode: str,
    arm: str,
    row: dict,
    j_dose: float,
    gate_cache: dict[int, dict[str, dict]],
    direction_cache: dict[int, dict],
) -> dict:
    hs_index = _arm_layer(arm)
    j_dir = direction_cache[hs_index]
    gated = gate_cache[hs_index][row["row_key"]]
    writes = _arm_writes(arm, hs_index, j_dose)
    outcome = _run_pass_with_writes(model, tokenizer, gated, hs_index, writes, j_dir)
    return {
        "mode": mode,
        "arm": arm,
        "row_key": row["row_key"],
        "role": row["role"],
        "category_canon": row.get("category_canon"),
        "hs_index": hs_index,
        "fire": bool(gated["fire"]),
        "score_neg_z_d": float(gated["score_neg_z_d"]),
        "tau": float(gated["tau"]),
        "writes": writes,
        **outcome,
    }


def _grade_population(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def _arm_summary(records: list[dict]) -> dict:
    confab = [r for r in records if r["role"] == "confab"]
    known = [r for r in records if r["role"] == "known_correct_answered"]
    dosed = [r for r in records if r["fire"]]
    readback_by_kind: dict[str, list[tuple[float, float]]] = {}
    for rec in dosed:
        targets = {w["kind"]: float(w["dose"]) for w in rec.get("writes", [])}
        for kind, measured in rec.get("readbacks", {}).items():
            if measured is None or kind not in targets:
                continue
            readback_by_kind.setdefault(kind, []).append((float(measured), targets[kind]))
    readback_summary = {}
    for kind, vals in readback_by_kind.items():
        measured = [v[0] for v in vals]
        within = [abs(m - t) <= 0.05 * abs(t) + 0.5 for m, t in vals]
        readback_summary[kind] = {
            "n": len(vals),
            "mean": float(np.mean(measured)) if measured else None,
            "frac_within_tol": sum(within) / len(within) if within else None,
        }
    return {
        "n_rows": len(records),
        "n_fired": len(dosed),
        "readbacks": readback_summary,
        "confab_tighten": _grade_population(confab, "clean_tighten"),
        "known_correct_cost_control": _grade_population(known, "not_well_formed_correct"),
        "malformed_json": _grade_population(records, "malformed_json"),
        "forced_continuation": _grade_population(records, "forced_continuation"),
        "non_target_language_drift": _grade_population(records, "non_target_language_drift"),
        "collapse_rate_on_dosed": (
            sum(1 for r in dosed if r["grade"]["degenerate"]) / len(dosed)
            if dosed else None
        ),
    }


def _load_records(path: Path, mode: str) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.open(encoding="utf-8")
        if line.strip() and json.loads(line).get("mode") == mode
    ]


def _contrast_from_arms(arms: dict[str, dict]) -> dict:
    if "c_hat_only_hs23" not in arms or "c_hat_plus_j_token_hs23" not in arms:
        return {}
    base = arms["c_hat_only_hs23"]
    hyb = arms["c_hat_plus_j_token_hs23"]
    ctrl = arms.get("c_hat_plus_random_j_hs23")
    tighten_delta = hyb["confab_tighten"]["rate"] - base["confab_tighten"]["rate"]
    cost_delta = (
        hyb["known_correct_cost_control"]["rate"]
        - base["known_correct_cost_control"]["rate"]
    )
    ctrl_delta = None
    if ctrl:
        ctrl_delta = ctrl["confab_tighten"]["rate"] - base["confab_tighten"]["rate"]
    return {
        "tighten_delta_hybrid_minus_baseline": tighten_delta,
        "cost_delta_hybrid_minus_baseline": cost_delta,
        "random_control_tighten_delta": ctrl_delta,
        "g1_pass": tighten_delta >= 0.04,
        "g2_pass": cost_delta <= 0.02,
        "g3_pass": (ctrl_delta is not None and tighten_delta - ctrl_delta >= 0.03),
        "g4_pass": (
            hyb["malformed_json"]["rate"] - base["malformed_json"]["rate"] <= 0.02
            and hyb["forced_continuation"]["rate"] - base["forced_continuation"]["rate"] <= 0.02
            and hyb["non_target_language_drift"]["rate"] - base["non_target_language_drift"]["rate"] <= 0.02
        ),
    }


def _summarize(records: list[dict], mode: str, j_dose: float) -> dict:
    by_arm: dict[str, list[dict]] = {}
    for rec in records:
        by_arm.setdefault(rec["arm"], []).append(rec)
    arms = {arm: _arm_summary(recs) for arm, recs in sorted(by_arm.items())}
    return {
        "schema": "jspace-token-target-summary/v1",
        "mode": mode,
        "j_token_dose": j_dose,
        "arms": arms,
        "contrast": _contrast_from_arms(arms),
        "row_text_committed": False,
    }


def _summary_with_baseline(summary: dict, baseline_summary: dict) -> dict:
    base = baseline_summary["arms"].get("c_hat_only_hs23")
    if not base:
        raise ValueError("baseline summary missing c_hat_only_hs23")
    summary["arms"]["c_hat_only_hs23"] = base
    summary["contrast"] = _contrast_from_arms(summary["arms"])
    summary["baseline_source_mode"] = baseline_summary["mode"]
    return summary


def _seed_fit_baseline_from_legacy(rows: list[dict]) -> None:
    """Reuse already-computed per-dose c_hat baselines after an interrupted run.

    Earlier runner versions wrote `c_hat_only_hs23` once per dose. Those records
    are dose-independent, so future/resumed calibration can copy one per row into
    FIT_BASELINE_MODE and stop paying that cost six times.
    """
    if not FIT_RECORDS.exists():
        return
    needed = {r["row_key"] for r in rows}
    done = {row_key for _arm, row_key in _read_done(FIT_RECORDS, FIT_BASELINE_MODE)}
    missing = needed - done
    if not missing:
        return
    legacy: dict[str, dict] = {}
    for line in FIT_RECORDS.open(encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("arm") != "c_hat_only_hs23":
            continue
        if not str(rec.get("mode", "")).startswith("fit_dose_"):
            continue
        legacy.setdefault(rec["row_key"], rec)
    for row_key in sorted(missing):
        if row_key not in legacy:
            continue
        rec = dict(legacy[row_key])
        rec["mode"] = FIT_BASELINE_MODE
        rec["baseline_seeded_from_mode"] = legacy[row_key]["mode"]
        _fsync_append(FIT_RECORDS, rec)


def _seed_noop_records(
    path: Path,
    rows: list[dict],
    mode: str,
    arms: list[str],
    j_dose: float,
) -> None:
    """Reuse deterministic no-op generations for gate-inactive rows.

    If the frozen gate does not fire, every write arm runs in off mode for that
    row. Under greedy decoding, the generated outcome is independent of dose and
    arm, so a previously recorded same-layer `fire=false` row can safely seed
    missing records. Fired rows are never copied.
    """
    if not path.exists():
        return
    row_keys = {r["row_key"] for r in rows}
    done: set[tuple[str, str]] = set()
    source_by_row_layer: dict[tuple[str, int], dict] = {}
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        row_key = rec.get("row_key")
        if row_key not in row_keys:
            continue
        if rec.get("mode") == mode:
            done.add((str(rec.get("arm")), str(row_key)))
        if rec.get("fire") is False and rec.get("hs_index") is not None:
            source_by_row_layer.setdefault((str(row_key), int(rec["hs_index"])), rec)

    for arm in arms:
        hs_index = _arm_layer(arm)
        writes = _arm_writes(arm, hs_index, j_dose)
        for row in rows:
            row_key = row["row_key"]
            key = (arm, row_key)
            if key in done:
                continue
            source = source_by_row_layer.get((row_key, hs_index))
            if source is None:
                continue
            rec = dict(source)
            rec.update(
                {
                    "mode": mode,
                    "arm": arm,
                    "writes": writes,
                    "readbacks": {},
                    "noop_seeded_from_mode": source.get("mode"),
                    "noop_seeded_from_arm": source.get("arm"),
                }
            )
            _fsync_append(path, rec)
            done.add(key)


def _run_records(
    mode: str,
    rows: list[dict],
    arms: list[str],
    j_dose: float,
    path: Path,
    resume: bool,
    model=None,
    tokenizer=None,
) -> dict:
    done = _read_done(path, mode) if resume else set()
    needed_layers = sorted({_arm_layer(arm) for arm in arms})
    gate_cache = {
        hs_index: {r["row_key"]: r for r in compute_gate_decisions(rows, hs_index)}
        for hs_index in needed_layers
    }
    direction_cache = {hs_index: load_token_direction(hs_index) for hs_index in needed_layers}
    owns_model = model is None or tokenizer is None
    if owns_model:
        model, tokenizer = ml.load_model()
    try:
        for arm in arms:
            if resume:
                _seed_noop_records(path, rows, mode, [arm], j_dose)
                done = _read_done(path, mode)
            for row in rows:
                key = (arm, row["row_key"])
                if key in done:
                    continue
                print(f"[token-target] {mode} arm={arm} row={row['row_key']}", flush=True)
                rec = _record_for_row(
                    model, tokenizer, mode, arm, row, j_dose, gate_cache, direction_cache
                )
                _fsync_append(path, rec)
    finally:
        if owns_model:
            del model
            gc.collect()
            torch.cuda.empty_cache()
    return _summarize(_load_records(path, mode), mode, j_dose)


def _write_summary(name: str, summary: dict, commit_public: bool) -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    (ANALYSIS / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if commit_public:
        COMMITTED.mkdir(parents=True, exist_ok=True)
        (COMMITTED / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run_smoke(args) -> dict:
    rows = selected_rows(args.n_rows)
    summary = _run_records(
        "smoke",
        rows,
        ["c_hat_only_hs23", "c_hat_plus_j_token_hs23", "c_hat_plus_random_j_hs23"],
        args.j_dose,
        SMOKE_RECORDS,
        args.resume,
    )
    _write_summary("smoke_summary.json", summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_fit_calibration(args) -> dict:
    doses = [float(x) for x in yaml.safe_load(Path(args.cell).read_text())["token_target_direction"]["dose_selection"]["ladder"]]
    rows = _fit_rows(args.n_fit_rows)
    dose_summaries = []
    model, tokenizer = ml.load_model()
    try:
        _seed_fit_baseline_from_legacy(rows)
        baseline_summary = _run_records(
            FIT_BASELINE_MODE,
            rows,
            ["c_hat_only_hs23"],
            0.0,
            FIT_RECORDS,
            args.resume,
            model=model,
            tokenizer=tokenizer,
        )
        for dose in doses:
            mode = f"fit_dose_{dose:g}"
            summary = _run_records(
                mode,
                rows,
                ["j_token_only_hs23", "c_hat_plus_j_token_hs23", "c_hat_plus_random_j_hs23"],
                dose,
                FIT_RECORDS,
                args.resume,
                model=model,
                tokenizer=tokenizer,
            )
            dose_summaries.append(_summary_with_baseline(summary, baseline_summary))
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    selected = select_dose(dose_summaries)
    out = {
        "schema": "jspace-token-target-fit-calibration/v1",
        "doses": dose_summaries,
        "selected_j_token_dose": selected,
        "selection_rule": "max hybrid clean_tighten among zero-collapse doses with known cost <= c_hat_only+0.02; tie chooses lower dose",
        "row_text_committed": False,
    }
    _write_summary("fit_calibration_summary.json", out, commit_public=True)
    print(json.dumps(out, indent=2))
    return out


def select_dose(summaries: list[dict]) -> float:
    viable = []
    for summary in summaries:
        arms = summary["arms"]
        if "c_hat_only_hs23" not in arms or "c_hat_plus_j_token_hs23" not in arms:
            continue
        base = arms["c_hat_only_hs23"]
        hyb = arms["c_hat_plus_j_token_hs23"]
        if hyb["collapse_rate_on_dosed"] not in (0, 0.0):
            continue
        cost_delta = hyb["known_correct_cost_control"]["rate"] - base["known_correct_cost_control"]["rate"]
        if cost_delta > 0.02:
            continue
        viable.append((
            hyb["confab_tighten"]["rate"],
            -float(summary["j_token_dose"]),
            float(summary["j_token_dose"]),
        ))
    if not viable:
        raise ValueError("no viable token dose under calibration rule")
    viable.sort(reverse=True)
    return float(viable[0][2])


def run_full(args) -> dict:
    cal = json.loads((COMMITTED / "fit_calibration_summary.json").read_text(encoding="utf-8"))
    dose = float(cal["selected_j_token_dose"])
    rows = selected_rows(None)
    rng = random.Random(20260708)
    rng.shuffle(rows)
    summary = _run_records("full", rows, HELD_OUT_ARMS, dose, FULL_RECORDS, args.resume)
    summary["fit_calibration_source"] = "analysis-committed/fit_calibration_summary.json"
    summary["overall_pass"] = bool(
        summary["contrast"].get("g1_pass")
        and summary["contrast"].get("g2_pass")
        and summary["contrast"].get("g3_pass")
        and summary["contrast"].get("g4_pass")
    )
    _write_summary("full_summary.json", summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", default=str(HERE / "token_bundle.yaml"))
    parser.add_argument("--cell", default=str(HERE / "cell.yaml"))
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build-directions")
    p_build.add_argument("--n-fit-rows", type=int)
    p_build.add_argument("--i-know-this-runs-on-gpu", action="store_true")

    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--n-rows", type=int, default=8)
    p_smoke.add_argument("--j-dose", type=float, default=5.0)
    p_smoke.add_argument("--i-know-this-runs-on-gpu", action="store_true")

    p_fit = sub.add_parser("fit-calibrate")
    p_fit.add_argument("--n-fit-rows", type=int)
    p_fit.add_argument("--i-know-this-runs-on-gpu", action="store_true")

    p_full = sub.add_parser("full")
    p_full.add_argument("--i-know-this-is-the-held-out-run", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd in {"build-directions", "smoke", "fit-calibrate"} and not args.i_know_this_runs_on_gpu:
        print(f"{args.cmd} uses the local GPU; pass --i-know-this-runs-on-gpu", file=sys.stderr)
        return 2
    if args.cmd == "full" and not args.i_know_this_is_the_held_out_run:
        print("full uses held-out rows; pass --i-know-this-is-the-held-out-run", file=sys.stderr)
        return 2
    if args.cmd == "build-directions":
        run_build_directions(args)
    elif args.cmd == "smoke":
        run_smoke(args)
    elif args.cmd == "fit-calibrate":
        run_fit_calibration(args)
    elif args.cmd == "full":
        run_full(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
