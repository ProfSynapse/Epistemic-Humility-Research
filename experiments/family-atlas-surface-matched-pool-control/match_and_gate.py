#!/usr/bin/env python3
"""Assign roles, build deterministic cross-original triads, and evaluate G0-G2."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from instrument_common import (
    ANALYSIS, COMMITTED, ROOT, atomic_json, atomic_jsonl, containment_lint, gate,
    instrument_fingerprint, load_jsonl, load_yaml, sha256_file,
)
from source_and_generate import (
    BaselineRunLog, assign_role, derive_finish_evidence,
    validate_source_materialization,
)
from grader_port import grade_generation

ROLES = ("known_correct_answered", "confab", "unknown_refused")


def _stable_rank(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def _hungarian(left: list[dict[str, Any]], right: list[dict[str, Any]], vector_key: str, forbidden) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    from scipy.optimize import linear_sum_assignment

    left = sorted(left, key=lambda r: r["row_key"])
    right = sorted(right, key=lambda r: r["row_key"])
    if not left or not right:
        return []
    a = np.asarray([row[vector_key] for row in left], dtype=np.float64)
    b = np.asarray([row[vector_key] for row in right], dtype=np.float64)
    cost = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
    finite_max = float(np.max(cost)) if cost.size else 1.0
    blocked = np.zeros_like(cost, dtype=bool)
    for i, lrow in enumerate(left):
        for j, rrow in enumerate(right):
            if forbidden(lrow, rrow):
                blocked[i, j] = True
    cost[blocked] = finite_max + 1e12
    # A tiny row-major perturbation makes equal finite costs lexicographic.
    cost += np.arange(cost.size, dtype=np.float64).reshape(cost.shape) * 1e-12
    ii, jj = linear_sum_assignment(cost)
    return [(left[i], right[j]) for i, j in zip(ii, jj) if not blocked[i, j]]


def build_triads(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    unknown_pairs: list[dict[str, Any]] = []
    blocks = sorted({(r["native_source"], r["category_canon"]) for r in rows if r["role"] in {"confab", "unknown_refused"}})
    for source, category in blocks:
        confab = [r for r in rows if r["role"] == "confab" and (r["native_source"], r["category_canon"]) == (source, category)]
        refused = [r for r in rows if r["role"] == "unknown_refused" and (r["native_source"], r["category_canon"]) == (source, category)]
        for c, u in _hungarian(confab, refused, "matching_vector", lambda x, y: x["original_pair_id"] == y["original_pair_id"]):
            unknown_pairs.append({
                "row_key": f"{c['row_key']}|{u['row_key']}", "native_source": source,
                "category_canon": category, "confab": c, "unknown_refused": u,
                "original_pair_ids": {c["original_pair_id"], u["original_pair_id"]},
                "matching_vector": ((np.asarray(c["matching_vector"]) + np.asarray(u["matching_vector"])) / 2).tolist(),
            })
    triads: list[dict[str, Any]] = []
    for source in sorted({p["native_source"] for p in unknown_pairs}):
        pairs = [p for p in unknown_pairs if p["native_source"] == source]
        known = [r for r in rows if r["role"] == "known_correct_answered" and r["native_source"] == source]
        for pair, k in _hungarian(pairs, known, "matching_vector", lambda p, row: row["original_pair_id"] in p["original_pair_ids"]):
            ordered_ids = [k["row_key"], pair["confab"]["row_key"], pair["unknown_refused"]["row_key"]]
            triad_id = "triad:" + hashlib.sha256("|".join(ordered_ids).encode()).hexdigest()[:16]
            triads.append({
                "triad_id": triad_id, "native_source": source,
                "rows": {"known_correct_answered": k, "confab": pair["confab"], "unknown_refused": pair["unknown_refused"]},
            })
    # Partition intact triads within source with a deterministic seeded order.
    for source in sorted({t["native_source"] for t in triads}):
        group = [t for t in triads if t["native_source"] == source]
        group.sort(key=lambda t: _stable_rank(seed, t["triad_id"]))
        n_fit = len(group) // 2
        for i, triad in enumerate(group):
            triad["split"] = "fit" if i < n_fit else "held_out"
    return sorted(triads, key=lambda t: t["triad_id"])


def _smd(x: np.ndarray, y: np.ndarray) -> float:
    denom = np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2.0) if len(x) > 1 and len(y) > 1 else 0.0
    return float(abs(x.mean() - y.mean()) / denom) if denom > 0 else float(abs(x.mean() - y.mean()) > 0)


def scalar_balance(flat_rows: list[dict[str, Any]]) -> dict[str, Any]:
    names = sorted(next(iter(flat_rows))["scalars"]) if flat_rows else []
    pairwise: dict[str, Any] = {}
    maximum = 0.0
    for a, b in itertools.combinations(ROLES, 2):
        values: dict[str, float] = {}
        for name in names:
            x = np.asarray([r["scalars"][name] for r in flat_rows if r["role"] == a])
            y = np.asarray([r["scalars"][name] for r in flat_rows if r["role"] == b])
            values[name] = _smd(x, y)
            maximum = max(maximum, values[name])
        pairwise[f"{a}_vs_{b}"] = values
    return {"maximum_pairwise_scalar_abs_smd": maximum, "pairwise": pairwise}


def rank_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    from scipy.stats import rankdata
    pos = labels == 1
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    if not n_pos or not n_neg:
        raise ValueError("AUROC requires both classes")
    ranks = rankdata(scores, method="average")
    u = ranks[pos].sum() - n_pos * (n_pos + 1) / 2
    return float(u / (n_pos * n_neg))


def grouped_pairwise_classifier(features: Any, flat_rows: list[dict[str, Any]], *, plant_role_tag: bool = False, folds: int = 5) -> dict[str, float]:
    from scipy import sparse
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold

    role_to_col = {role: i for i, role in enumerate(ROLES)}
    if plant_role_tag:
        tag = sparse.csr_matrix(([1.0] * len(flat_rows), ([*range(len(flat_rows))], [role_to_col[r["role"]] for r in flat_rows])), shape=(len(flat_rows), 3))
        features = sparse.hstack([features, tag], format="csr")
    output: dict[str, float] = {}
    for a, b in itertools.combinations(ROLES, 2):
        idx = np.asarray([i for i, r in enumerate(flat_rows) if r["role"] in {a, b}], dtype=int)
        labels = np.asarray([1 if flat_rows[i]["role"] == a else 0 for i in idx])
        groups = np.asarray([flat_rows[i]["triad_id"] for i in idx])
        n_splits = min(folds, len(set(groups)))
        if n_splits < 2:
            raise ValueError("grouped classifier needs at least two triads")
        pred = np.empty(len(idx), dtype=np.float64)
        for train, test in GroupKFold(n_splits=n_splits).split(idx, labels, groups):
            clf = LogisticRegression(C=1.0, solver="liblinear", max_iter=2000, random_state=0)
            clf.fit(features[idx[train]], labels[train])
            pred[test] = clf.predict_proba(features[idx[test]])[:, 1]
        auc = rank_auroc(pred, labels)
        output[f"{a}_vs_{b}"] = max(auc, 1.0 - auc)
    return output


def _full_classifier_features(source_rows: list[dict[str, Any]], flat_rows: list[dict[str, Any]], basis_path: Path):
    from joblib import load
    from scipy import sparse

    basis = load(basis_path)
    source_by_key = {r["row_key"]: r for r in source_rows}
    questions = [source_by_key[r["row_key"]]["question"] for r in flat_rows]
    word = basis["word_tfidf"].transform(basis["word"].transform(questions))
    char = basis["char_tfidf"].transform(basis["char"].transform(questions))
    scalars = np.asarray([[r["scalars"][name] for name in basis["scalar_names"]] for r in flat_rows])
    scalars = sparse.csr_matrix((scalars - scalars.mean(axis=0)) / np.where(scalars.std(axis=0) > 0, scalars.std(axis=0), 1.0))
    return sparse.hstack([scalars, word, char], format="csr")


def validate_generation_inputs(
    model_id: str,
    cfg: dict[str, Any],
    source_rows: list[dict[str, Any]],
    generations: list[dict[str, Any]],
    coords: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_audit = validate_source_materialization(cfg)
    exclusions_path = ANALYSIS / model_id / "prior_atlas_exclusions_private.jsonl"
    if not exclusions_path.is_file():
        raise ValueError("prior-atlas exclusion manifest is missing")
    exclusion_rows = load_jsonl(exclusions_path)
    excluded = {r["row_key"] for r in exclusion_rows}
    if len(excluded) != len(exclusion_rows):
        raise ValueError("prior-atlas exclusion manifest has duplicate row keys")
    prior_cfg = cfg["models"][model_id]["prior_atlas_pool"]
    exclusion_summary = json.loads((ANALYSIS / model_id / "prior_atlas_exclusion_summary_private.json").read_text())
    if (
        exclusion_summary.get("prior_artifact_sha256") != prior_cfg["sha256"]
        or exclusion_summary.get("prior_source_experiment") != prior_cfg["source_experiment"]
        or exclusion_summary.get("n_excluded") != len(excluded)
    ):
        raise ValueError("prior-atlas exclusion provenance does not match cell.yaml")
    source_by_key = {r["row_key"]: r for r in source_rows}
    eligible = set(source_by_key) - excluded
    generation_keys = [r["row_key"] for r in generations]
    if len(generation_keys) != len(set(generation_keys)) or set(generation_keys) != eligible:
        raise ValueError(
            f"generation coverage is not exact: source=5200 excluded={len(excluded)} "
            f"eligible={len(eligible)} generated={len(generation_keys)}"
        )
    if set(coords) != eligible:
        raise ValueError("surface coordinates do not exactly cover eligible rows")
    if excluded & (set(generation_keys) | set(coords)):
        raise ValueError("excluded prior-atlas key reached a downstream artifact")
    model_cfg = cfg["models"][model_id]
    for rec in generations:
        missing = BaselineRunLog.REQUIRED - set(rec)
        if missing:
            raise ValueError(f"generation record {rec['row_key']} missing {sorted(missing)}")
        expected_provenance = {
            "source": "umwp", "model": model_cfg["repo"],
            "model_revision": model_cfg["revision"], "renderer_id": model_cfg["render_contract"],
            "seed": cfg["seed"],
        }
        for key, expected in expected_provenance.items():
            if rec.get(key) != expected:
                raise ValueError(f"generation record {rec['row_key']} has invalid {key}")
        source = source_by_key[rec["row_key"]]
        for key in ("native_source", "original_pair_id", "category_canon", "umwp_id", "answerable"):
            if rec.get(key) != source.get(key):
                raise ValueError(f"generation record {rec['row_key']} differs from source field {key}")
        finish_reason, terminated = derive_finish_evidence(
            int(rec["n_new_tokens"]), int(cfg["generation"]["max_new_tokens"]),
            rec["last_completion_token_id"], [int(v) for v in rec["eos_token_ids"]],
        )
        if rec["finish_reason"] != finish_reason or rec["terminated_naturally"] is not terminated:
            raise ValueError(f"generation record {rec['row_key']} fails finish-evidence parity")
        aliases = source["aliases"] if source["answerable"] else None
        regraded = grade_generation(rec["generation_text"], aliases, terminated)
        if rec["answer_value"] != regraded["answer_value"] or rec["full_grader_dict"] != regraded["full_grader_dict"]:
            raise ValueError(f"generation record {rec['row_key']} fails complete regrade parity")
        if any(rec.get(key) != value for key, value in regraded["full_grader_dict"].items()):
            raise ValueError(f"generation record {rec['row_key']} fails flattened grade parity")
        if rec["role"] != assign_role(source["answerable"], regraded):
            raise ValueError(f"generation record {rec['row_key']} fails role parity")
    return {
        **source_audit, "n_excluded_prior_atlas": len(excluded),
        "n_eligible": len(eligible), "n_generations": len(generations),
        "exact_generation_coverage": True, "regrade_parity": True,
    }


def _flatten(triads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for triad in triads:
        for role in ROLES:
            row = dict(triad["rows"][role])
            row.update({"role": role, "triad_id": triad["triad_id"], "split": triad["split"]})
            flat.append(row)
    return flat


def stage_row_exhaust(
    model_id: str,
    generations: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    out_path: Path | None = None,
) -> Path:
    """Stage standard row exhaust for pass, falsified, or indeterminate runs."""
    matched_by_key = {row["row_key"]: row for row in matched_rows}
    enriched = []
    for rec in generations:
        row = dict(rec)
        row.pop("last_completion_token_id", None)
        row.pop("eos_token_ids", None)
        match = matched_by_key.get(rec["row_key"])
        if match is not None:
            row.update({"role": match["role"], "split": match["split"], "triad_id": match["triad_id"]})
        enriched.append(row)
    destination = out_path or ANALYSIS / "exhaust" / "rows" / f"{model_id}.jsonl"
    atomic_jsonl(destination, enriched)
    return destination


def registered_fit_subsample_indices(rows: list[dict[str, Any]], seed: int) -> list[int]:
    triads: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        if row["split"] == "fit":
            triads.setdefault(row["triad_id"], []).append(i)
    selected: list[int] = []
    for source in sorted({rows[members[0]]["native_source"] for members in triads.values()}):
        ids = [tid for tid, members in triads.items() if rows[members[0]]["native_source"] == source]
        ids.sort(key=lambda tid: _stable_rank(seed, tid))
        for tid in ids[:max(1, len(ids) // 2)]:
            selected.extend(triads[tid])
    return sorted(selected)


def surface_support(features: Any, rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    partitions: dict[str, Any] = {}
    for split in ("fit", "held_out"):
        idx = np.asarray([i for i, row in enumerate(rows) if row["split"] == split], dtype=int)
        part_rows = [rows[i] for i in idx]
        balance = scalar_balance(part_rows)
        aucs = grouped_pairwise_classifier(features[idx], part_rows)
        planted = grouped_pairwise_classifier(features[idx], part_rows, plant_role_tag=True)
        partitions[split] = {
            "scalar_balance": balance, "pairwise_best_orientation_aurocs": aucs,
            "maximum_pairwise_best_orientation_auroc": max(aucs.values()),
            "surface_role_tag_pairwise_aurocs": planted,
        }
    return {
        "partitions": partitions,
        "maximum_pairwise_scalar_abs_smd": max(v["scalar_balance"]["maximum_pairwise_scalar_abs_smd"] for v in partitions.values()),
        "maximum_pairwise_best_orientation_auroc": max(v["maximum_pairwise_best_orientation_auroc"] for v in partitions.values()),
        "surface_role_tag_pass": all(min(v["surface_role_tag_pairwise_aurocs"].values()) >= cfg["surface_classifier"]["positive_control_min_each_pairwise_auroc"] for v in partitions.values()),
    }


def subsample_surface_support(features: Any, rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    idx = np.asarray(registered_fit_subsample_indices(rows, cfg["profile"]["subsample"]["seed"]), dtype=int)
    part_rows = [rows[i] for i in idx]
    balance = scalar_balance(part_rows)
    aucs = grouped_pairwise_classifier(features[idx], part_rows)
    max_smd = balance["maximum_pairwise_scalar_abs_smd"]
    max_auc = max(aucs.values())
    return {
        "n_rows": len(part_rows), "scalar_balance": balance,
        "pairwise_best_orientation_aurocs": aucs,
        "maximum_pairwise_best_orientation_auroc": max_auc,
        "pass": max_smd <= cfg["surface_classifier"]["max_pairwise_scalar_abs_smd"] and max_auc <= cfg["surface_classifier"]["max_auroc"],
    }


def build_pool(model_id: str) -> dict[str, Any]:
    cfg = load_yaml(ROOT / "cell.yaml")
    source_rows = load_jsonl(ANALYSIS / "source" / "rows.jsonl")
    generations = load_jsonl(ANALYSIS / model_id / "generation_rows.jsonl")
    coords = {r["row_key"]: r for r in load_jsonl(ANALYSIS / model_id / "surface" / "coordinates.jsonl")}
    input_audit = validate_generation_inputs(model_id, cfg, source_rows, generations, coords)
    source_by_key = {r["row_key"]: r for r in source_rows}
    candidates: list[dict[str, Any]] = []
    for rec in generations:
        if rec.get("role") not in ROLES or rec["row_key"] not in coords:
            continue
        row = {**rec, **{k: v for k, v in source_by_key[rec["row_key"]].items() if k not in rec}, **coords[rec["row_key"]]}
        candidates.append(row)
    pdir = ANALYSIS / model_id
    cdir = COMMITTED / model_id
    checkpoint_path = pdir / "matching_checkpoint.json"
    fingerprint = instrument_fingerprint()
    consumed = [
        ANALYSIS / "source" / "StandardDataset.jsonl",
        ANALYSIS / "source" / "rows.jsonl",
        ANALYSIS / model_id / "generation_rows.jsonl",
        ANALYSIS / model_id / "prior_atlas_exclusions_private.jsonl",
        ANALYSIS / model_id / "surface" / "coordinates.jsonl",
        ANALYSIS / model_id / "surface" / "basis.joblib",
    ]
    input_digest = hashlib.sha256(json.dumps({
        "files": {str(path.relative_to(ROOT)): sha256_file(path) for path in consumed},
        "seed": cfg["seed"], "instrument_fingerprint": fingerprint,
    }, sort_keys=True).encode()).hexdigest()
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.is_file() else None
    if checkpoint and checkpoint.get("input_digest") == input_digest:
        triads = checkpoint["triads"]
    else:
        triads = build_triads(candidates, cfg["seed"])
        atomic_json(checkpoint_path, {"input_digest": input_digest, "stage": "triads_complete", "triads": triads})
    flat = _flatten(triads)
    fit_triads = sum(t["split"] == "fit" for t in triads)
    held_triads = sum(t["split"] == "held_out" for t in triads)
    minimum = cfg["matching"]["minimum_fit_triads"]
    private_texts = [r["question"] for r in source_rows] + [r["generation_text"] for r in generations]
    lint = containment_lint(COMMITTED, private_texts=private_texts)
    g0 = gate(
        "pass" if lint["status"] == "pass" else "fail",
        {
            "source_and_generation_audit": input_audit,
            "prior_atlas_exclusion_count": input_audit["n_excluded_prior_atlas"],
            "containment": lint,
        },
        lint["errors"],
    )
    g1_reasons = [] if fit_triads >= minimum and held_triads >= minimum else [f"triad floor failed: fit={fit_triads}, held_out={held_triads}, floor={minimum}"]
    g1 = gate("pass" if not g1_reasons else "fail", {"fit_triads": fit_triads, "held_out_triads": held_triads, "role_counts": {role: sum(r["role"] == role for r in flat) for role in ROLES}}, g1_reasons)
    stage_row_exhaust(model_id, generations, flat)
    if g1["status"] != "pass":
        summary = {
            "schema_version": 1, "model_id": model_id,
            "decision_state": "indeterminate_hard_stop",
            "instrument_fingerprint": fingerprint,
            "gates": {
                "g0": g0, "g1": g1,
                "g2": gate("not_run", {}, ["G1 yield failed"]),
                "g3": gate("not_run", {}), "g4": gate("not_run", {}),
                "g5": gate("not_run", {}),
            },
        }
        atomic_json(pdir / "g0_g2_private.json", summary)
        atomic_json(cdir / "g0_g2_summary.json", summary)
        return summary
    features = _full_classifier_features(source_rows, flat, ANALYSIS / model_id / "surface" / "basis.joblib")
    support = surface_support(features, flat, cfg)
    subsample_support = subsample_surface_support(features, flat, cfg)
    atomic_json(pdir / "support_checkpoint.json", {"input_digest": input_digest, "instrument_fingerprint": fingerprint, "support": support, "subsample_support": subsample_support})
    max_auc = support["maximum_pairwise_best_orientation_auroc"]
    max_smd = support["maximum_pairwise_scalar_abs_smd"]
    g2_reasons = []
    if max_auc > cfg["surface_classifier"]["max_auroc"]:
        g2_reasons.append(f"surface AUROC {max_auc:.6f} exceeds ceiling")
    if max_smd > cfg["surface_classifier"]["max_pairwise_scalar_abs_smd"]:
        g2_reasons.append(f"scalar SMD {max_smd:.6f} exceeds ceiling")
    g2 = gate("pass" if not g2_reasons else "fail", support, g2_reasons)
    atomic_jsonl(pdir / "matched_rows_private.jsonl", flat)
    atomic_jsonl(cdir / "split_manifest.jsonl", [
        {"row_id": r["row_key"], "role": r["role"], "split": r["split"], "native_source": r["native_source"]}
        for r in flat
    ])
    lint = containment_lint(COMMITTED, private_texts=private_texts)
    if lint["status"] == "fail":
        g0 = gate("fail", {**g0["checks"], "containment": lint}, g0["reasons"] + lint["errors"])
    summary = {
        "schema_version": 1, "model_id": model_id, "decision_state": "ready_for_capture" if all(g["status"] == "pass" for g in (g0, g1, g2)) else "indeterminate_hard_stop",
        "gates": {"g0": g0, "g1": g1, "g2": g2, "g3": gate("not_run", {}), "g4": gate("not_run", {}), "g5": gate("not_run", {})},
        "positive_controls": {"surface_role_tag_pass": support["surface_role_tag_pass"]},
        "registered_fit_subsample_surface_support": subsample_support,
        "prior_atlas_exclusion_count": input_audit["n_excluded_prior_atlas"],
        "instrument_fingerprint": fingerprint,
    }
    atomic_json(pdir / "g0_g2_private.json", summary)
    atomic_json(cdir / "g0_g2_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    args = parser.parse_args()
    print(json.dumps(build_pool(args.model_id), indent=2))


if __name__ == "__main__":
    main()
