#!/usr/bin/env python3
"""CPU-only profile, read panel, planted control, and fixed aggregate gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from capture_full_depth import validate_activation_bundle
from instrument_common import (
    ANALYSIS, COMMITTED, ROOT, atomic_json, gate, instrument_fingerprint,
    load_jsonl, load_yaml, sha256_file, terminal_containment_scan,
)
from match_and_gate import _full_classifier_features, rank_auroc, subsample_surface_support


def participation_ratio(matrix: np.ndarray) -> float:
    x = matrix.astype(np.float64)
    x -= x.mean(axis=0, keepdims=True)
    gram = (x @ x.T) / max(len(x) - 1, 1)
    eig = np.clip(np.linalg.eigvalsh(gram), 0.0, None)
    s1, s2 = eig.sum(), (eig ** 2).sum()
    return 1.0 if s2 <= 1e-30 else float(s1 * s1 / s2)


def eff_dim_frac(matrix: np.ndarray) -> float:
    if len(matrix) < 2:
        raise ValueError("eff_dim_frac needs at least two rows")
    return participation_ratio(matrix) / len(matrix)


class ActivationReader:
    def __init__(self, root: Path):
        self.root = root
        self.index = load_jsonl(root / "activation_index.jsonl")
        self.lookup = {(r["row_key"], int(r["hs_index"])): r for r in self.index}
        self.cache: dict[str, dict[str, np.ndarray]] = {}

    def get(self, row_key: str, hs_index: int) -> np.ndarray:
        from safetensors.numpy import load_file
        rec = self.lookup[(row_key, hs_index)]
        shard = rec["shard_key"]
        if shard not in self.cache:
            self.cache[shard] = load_file(str(self.root / shard))
        return np.asarray(self.cache[shard][f"hs_{hs_index:03d}"], dtype=np.float64)

    def matrix(self, row_keys: list[str], hs_index: int) -> np.ndarray:
        return np.stack([self.get(key, hs_index) for key in row_keys])


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def bootstrap_auroc_ci(scores: np.ndarray, labels: np.ndarray, n_resamples: int = 2000, seed: int = 20260707) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    pos_idx, neg_idx = np.where(labels == 1)[0], np.where(labels == 0)[0]
    point = rank_auroc(scores, labels)
    sampled = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        bp = rng.choice(pos_idx, size=len(pos_idx), replace=True)
        bn = rng.choice(neg_idx, size=len(neg_idx), replace=True)
        idx = np.concatenate([bp, bn])
        sampled[i] = rank_auroc(scores[idx], np.concatenate([np.ones(len(bp), dtype=int), np.zeros(len(bn), dtype=int)]))
    lo, hi = np.percentile(sampled, [2.5, 97.5])
    return {"point": point, "ci95_lo": float(lo), "ci95_hi": float(hi), "n_resamples": n_resamples, "seed": seed, "n_pos": len(pos_idx), "n_neg": len(neg_idx)}


def _axis(reader: ActivationReader, hs: int, pos_fit: list[str], neg_fit: list[str], pos_eval: list[str], neg_eval: list[str], *, n_resamples: int, seed: int) -> dict[str, Any]:
    direction = _unit(reader.matrix(pos_fit, hs).mean(axis=0) - reader.matrix(neg_fit, hs).mean(axis=0))
    scores = np.concatenate([reader.matrix(pos_eval, hs) @ direction, reader.matrix(neg_eval, hs) @ direction])
    labels = np.concatenate([np.ones(len(pos_eval), dtype=int), np.zeros(len(neg_eval), dtype=int)])
    result = bootstrap_auroc_ci(scores, labels, n_resamples=n_resamples, seed=seed)
    result["direction_norm_check"] = float(np.linalg.norm(direction))
    return result


def random_unit_direction(hidden_dim: int, hs: int, seed: int) -> np.ndarray:
    return _unit(np.random.default_rng([seed, hs]).normal(size=hidden_dim))


def _random_contrast(direction: np.ndarray, pos: np.ndarray, neg: np.ndarray) -> float:
    scores = np.concatenate([pos, neg]) @ direction
    labels = np.concatenate([np.ones(len(pos), dtype=int), np.zeros(len(neg), dtype=int)])
    auc = rank_auroc(scores, labels)
    return max(auc, 1.0 - auc)


def read_panel(reader: ActivationReader, rows: list[dict[str, Any]], n_states: int, *, n_resamples: int = 2000, seed: int = 20260707, existing: list[dict[str, Any]] | None = None, on_layer=None) -> list[dict[str, Any]]:
    keys = lambda role, split: [r["row_key"] for r in rows if r["role"] == role and r["split"] == split]
    known_fit, known_eval = keys("known_correct_answered", "fit"), keys("known_correct_answered", "held_out")
    confab_fit, confab_eval = keys("confab", "fit"), keys("confab", "held_out")
    refused_fit, refused_eval = keys("unknown_refused", "fit"), keys("unknown_refused", "held_out")
    panel = list(existing or [])
    done = {int(row["hs_index"]) for row in panel}
    for hs in range(n_states):
        if hs in done:
            continue
        known_eval_mat = reader.matrix(known_eval, hs)
        confab_eval_mat = reader.matrix(confab_eval, hs)
        refused_eval_mat = reader.matrix(refused_eval, hs)
        random_direction = random_unit_direction(known_eval_mat.shape[1], hs, seed)
        item = {
            "hs_index": hs,
            "doubt": _axis(reader, hs, known_fit, refused_fit, known_eval, refused_eval, n_resamples=n_resamples, seed=seed),
            "caution": _axis(reader, hs, refused_fit, confab_fit, refused_eval, confab_eval, n_resamples=n_resamples, seed=seed),
            "raw_refusal": _axis(reader, hs, refused_fit, known_fit + confab_fit, refused_eval, known_eval + confab_eval, n_resamples=n_resamples, seed=seed),
            "random_direction_control": {
                "ref_vs_known": _random_contrast(random_direction, refused_eval_mat, known_eval_mat),
                "ref_vs_confab": _random_contrast(random_direction, refused_eval_mat, confab_eval_mat),
                "ref_vs_answered": _random_contrast(random_direction, refused_eval_mat, np.vstack([known_eval_mat, confab_eval_mat])),
            },
        }
        panel.append(item)
        if on_layer:
            on_layer(sorted(panel, key=lambda row: row["hs_index"]))
    return sorted(panel, key=lambda row: row["hs_index"])


def _profile(reader: ActivationReader, row_keys: list[str], n_states: int, *, existing: list[dict[str, Any]] | None = None, on_layer=None) -> list[dict[str, Any]]:
    profile = list(existing or [])
    done = {int(row["hs_index"]) for row in profile}
    for hs in range(n_states):
        if hs in done:
            continue
        profile.append({"hs_index": hs, "eff_dim_frac": eff_dim_frac(reader.matrix(row_keys, hs))})
        if on_layer:
            on_layer(sorted(profile, key=lambda row: row["hs_index"]))
    return sorted(profile, key=lambda row: row["hs_index"])


def _peak(profile: list[dict[str, Any]], n_states: int) -> dict[str, Any]:
    values = np.asarray([r["eff_dim_frac"] for r in profile])
    index = int(np.argmax(values))
    runner = float(np.partition(values, -2)[-2]) if len(values) > 1 else 0.0
    return {
        "hs_index": index, "depth": index / (n_states - 1), "eff_dim_frac": float(values[index]),
        "runner_up": runner, "peak_to_runner_up_ratio": float(values[index] / runner) if runner > 0 else None,
        "tie_count": int(np.sum(np.isclose(values, values[index], rtol=1e-12, atol=1e-15))),
    }


def _subsample_rows(rows: list[dict[str, Any]], seed: int) -> list[str]:
    triads: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["split"] == "fit":
            triads.setdefault(row["triad_id"], []).append(row)
    selected: list[str] = []
    sources = sorted({members[0]["native_source"] for members in triads.values()})
    for source in sources:
        ids = [tid for tid, members in triads.items() if members[0]["native_source"] == source]
        ids.sort(key=lambda tid: hashlib.sha256(f"{seed}:{tid}".encode()).hexdigest())
        take = max(1, len(ids) // 2)
        for tid in ids[:take]:
            selected.extend(r["row_key"] for r in triads[tid])
    return sorted(selected)


def planted_location_control(reader: ActivationReader, fit_keys: list[str], base_profile: list[dict[str, Any]], planted_hs: int, scales: list[float], seed: int) -> dict[str, Any]:
    base = reader.matrix(fit_keys, planted_hs)
    centered = base - base.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(centered ** 2))) or 1.0
    rng = np.random.default_rng(seed)
    noise = rng.normal(size=base.shape)
    noise -= noise.mean(axis=0, keepdims=True)
    noise /= float(np.sqrt(np.mean(noise ** 2))) or 1.0
    for scale in scales:
        values = [r["eff_dim_frac"] for r in base_profile]
        values[planted_hs] = eff_dim_frac(base + float(scale) * rms * noise)
        order = np.argsort(values)
        peak, runner = int(order[-1]), float(values[order[-2]])
        ratio = float(values[peak] / runner) if runner > 0 else float("inf")
        if peak == planted_hs and values.count(values[peak]) == 1 and ratio >= 1.05:
            return {"status": "pass", "selected_scale": float(scale), "planted_hs_index": planted_hs, "peak_to_runner_up_ratio": ratio}
    return {"status": "fail", "selected_scale": None, "planted_hs_index": planted_hs, "peak_to_runner_up_ratio": None}


def analyze_model(model_id: str) -> dict[str, Any]:
    cfg = load_yaml(ROOT / "cell.yaml")
    model_cfg = cfg["models"][model_id]
    prior = json.loads((COMMITTED / model_id / "g0_g2_summary.json").read_text())
    if any(prior["gates"][name]["status"] != "pass" for name in ("g0", "g1", "g2")):
        raise RuntimeError("analysis hard-stopped: G0-G2 did not pass")
    rows = load_jsonl(ANALYSIS / model_id / "matched_rows_private.jsonl")
    expected_rows = {r["row_key"] for r in rows}
    activation_root = ANALYSIS / "exhaust" / "activations" / model_id
    capture_manifest = json.loads((COMMITTED / model_id / "capture_manifest.json").read_text())
    current_fingerprint = instrument_fingerprint()
    if capture_manifest["instrument_fingerprint"] != current_fingerprint:
        raise RuntimeError("capture fingerprint differs from the current verified signed instrument")
    inputs_log = ANALYSIS / model_id / "capture_inputs_private.jsonl"
    validation = validate_activation_bundle(
        activation_root, model_cfg["n_hidden_states"], model_cfg["repo"],
        model_cfg["revision"], current_fingerprint, inputs_log, expected_rows,
    )
    reader = ActivationReader(activation_root)
    fit_keys = sorted(r["row_key"] for r in rows if r["split"] == "fit")
    checkpoint_path = ANALYSIS / model_id / "analysis_checkpoint.json"
    consumed = [
        activation_root / "activation_index.jsonl", inputs_log,
        ANALYSIS / model_id / "matched_rows_private.jsonl",
        ANALYSIS / model_id / "surface" / "basis.joblib",
        ANALYSIS / "source" / "rows.jsonl",
        COMMITTED / model_id / "g0_g2_summary.json",
    ]
    checkpoint_digest = hashlib.sha256(json.dumps({
        "files": {str(path.relative_to(ROOT)): sha256_file(path) for path in consumed},
        "seed": cfg["seed"], "instrument_fingerprint": current_fingerprint,
        "bundle": validation["bundle_digest"],
    }, sort_keys=True).encode()).hexdigest()
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.is_file() else {}
    if checkpoint.get("input_digest") != checkpoint_digest:
        checkpoint = {"input_digest": checkpoint_digest, "full_profile": [], "subsample_profile": [], "read_panel": []}
    def save_part(name: str, value: list[dict[str, Any]]) -> None:
        checkpoint[name] = value
        atomic_json(checkpoint_path, checkpoint)
    profile = _profile(reader, fit_keys, model_cfg["n_hidden_states"], existing=checkpoint["full_profile"], on_layer=lambda value: save_part("full_profile", value))
    subsample_keys = _subsample_rows(rows, cfg["profile"]["subsample"]["seed"])
    subsample = _profile(reader, subsample_keys, model_cfg["n_hidden_states"], existing=checkpoint["subsample_profile"], on_layer=lambda value: save_part("subsample_profile", value))
    panel = read_panel(
        reader, rows, model_cfg["n_hidden_states"],
        n_resamples=cfg["read_panel"]["bootstrap_resamples"],
        seed=cfg["read_panel"]["bootstrap_seed"],
        existing=checkpoint["read_panel"], on_layer=lambda value: save_part("read_panel", value),
    )
    source_rows = load_jsonl(ANALYSIS / "source" / "rows.jsonl")
    features = _full_classifier_features(source_rows, rows, ANALYSIS / model_id / "surface" / "basis.joblib")
    registered_subsample_support = subsample_surface_support(features, rows, cfg)
    plant = planted_location_control(reader, fit_keys, profile, model_cfg["planted_hs_index"], cfg["planted_location_control"]["rms_scale_grid"], cfg["planted_location_control"]["seed"])
    surface_plant_pass = bool(prior["positive_controls"]["surface_role_tag_pass"])
    g3_reasons = []
    if not surface_plant_pass:
        g3_reasons.append("surface one-hot plant failed")
    if plant["status"] != "pass":
        g3_reasons.append("interior location plant failed")
    g3 = gate("pass" if not g3_reasons else "fail", {"surface_one_hot_pass": surface_plant_pass, "location_plant": plant}, g3_reasons)
    lo, hi = cfg["read_panel"]["strict_interior_depth"]
    joint = [r["hs_index"] for r in panel if lo < r["hs_index"] / (model_cfg["n_hidden_states"] - 1) < hi and min(r[a]["point"] for a in cfg["read_panel"]["axes"]) >= cfg["read_panel"]["minimum_auroc"]]
    indexed_rows = {r["row_key"] for r in reader.index}
    g4_reasons = []
    if validation["status"] != "pass" or expected_rows != indexed_rows:
        g4_reasons.append("activation bundle integrity or row join failed")
    if not joint:
        g4_reasons.append("no strict-interior joint read-panel layer")
    if not registered_subsample_support["pass"]:
        g4_reasons.append("registered 50% FIT subsample lost surface support")
    g4 = gate("pass" if not g4_reasons else "fail", {"bundle_validation": validation, "exact_row_join": expected_rows == indexed_rows, "joint_interior_layers": joint, "registered_fit_subsample_surface_support": registered_subsample_support}, g4_reasons)
    full_peak, sub_peak = _peak(profile, model_cfg["n_hidden_states"]), _peak(subsample, model_cfg["n_hidden_states"])
    prereq = g3["status"] == "pass" and g4["status"] == "pass"
    if prereq:
        threshold = cfg["profile"]["early_exterior_max_depth"]
        if cfg["profile"]["require_unique_real_peak"] and (full_peak["tie_count"] != 1 or sub_peak["tie_count"] != 1):
            g5 = gate("not_run", {"full_peak": full_peak, "subsample_peak": sub_peak}, ["real profile peak is not unique"])
        else:
            passed = full_peak["depth"] <= threshold and sub_peak["depth"] <= threshold
            g5 = gate("pass" if passed else "fail", {"full_peak": full_peak, "subsample_peak": sub_peak}, [] if passed else ["a valid peak moved beyond depth 0.20"])
    else:
        g5 = gate("not_run", {"full_peak": None, "subsample_peak": None}, ["G3 or G4 failed"])
    if g5["status"] == "pass":
        decision = "pass"
    elif g5["status"] == "fail":
        decision = "falsified"
    else:
        decision = "indeterminate"
    result = {
        "schema_version": 1, "model_id": model_id, "decision": decision,
        "gates": {"g0": prior["gates"]["g0"], "g1": prior["gates"]["g1"], "g2": prior["gates"]["g2"], "g3": g3, "g4": g4, "g5": g5},
        "profiles": {"full": profile, "subsample": subsample}, "read_panel": panel,
        "descriptive": {"n_fit_rows": len(fit_keys), "n_subsample_rows": len(subsample_keys)},
    }
    atomic_json(COMMITTED / model_id / "aggregate_results.json", result)
    return result


def combine() -> dict[str, Any]:
    model_ids = ["gemma4_e4b_it", "qwen3_4b_raw_base"]
    results = {}
    for model_id in model_ids:
        path = COMMITTED / model_id / "aggregate_results.json"
        results[model_id] = json.loads(path.read_text()) if path.is_file() else None
    decisions = [value["decision"] for value in results.values() if value]
    if len(decisions) < len(model_ids) or "indeterminate" in decisions:
        decision = "indeterminate"
    elif "falsified" in decisions:
        decision = "falsified"
    else:
        decision = "pass"
    payload = {"schema_version": 1, "experiment": ROOT.name, "decision": decision, "models": results}
    atomic_json(COMMITTED / "aggregate_results.json", payload)
    source_rows = load_jsonl(ANALYSIS / "source" / "rows.jsonl")
    private_texts = [row["question"] for row in source_rows]
    for model_id in model_ids:
        private_texts.extend(row["generation_text"] for row in load_jsonl(ANALYSIS / model_id / "generation_rows.jsonl"))
    packaging_gate = terminal_containment_scan(private_texts=private_texts)
    payload["packaging_gate"] = packaging_gate
    atomic_json(COMMITTED / "aggregate_results.json", payload)
    atomic_json(COMMITTED / "containment_report.json", packaging_gate)
    final_scan = terminal_containment_scan(private_texts=private_texts)
    if final_scan["status"] != "pass":
        raise RuntimeError(f"terminal containment gate failed: {final_scan['errors']}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("model")
    one.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    sub.add_parser("combine")
    args = parser.parse_args()
    print(json.dumps(analyze_model(args.model_id) if args.command == "model" else combine(), indent=2))


if __name__ == "__main__":
    main()
