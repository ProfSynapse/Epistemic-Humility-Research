#!/usr/bin/env python3
"""Prep and score one doubt-snap cross-family cell around tuner verbs.

This script owns project-specific data transforms and statistics only. GPU
model work goes through Synaptic-Tuner public CLIs:

* `batch-generate` mines baseline roles.
* `batch-capture` captures prompt-anchor hidden states.
* `mechinterp steer` runs FIT dose sweeps and held-out interventions.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
for p in (str(ROOT), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_lib  # noqa: E402
import grader  # noqa: E402
import render as render_mod  # noqa: E402


SEED = 20260707
DEFAULT_MAX_ANSWERABLE = 1600
DEFAULT_MAX_UNANSWERABLE = 2400


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a mapping")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as an object")
    return data


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def parse_jsonish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            obj = json.loads(s)
            if isinstance(obj, list):
                return [str(x) for x in obj if str(x).strip()]
        except json.JSONDecodeError:
            pass
        return [s]
    return [str(value)]


def cell_by_id(cell_id: str) -> dict[str, Any]:
    matrix = load_yaml(ROOT / "model_matrix.yaml")
    for cell in matrix.get("cells", []):
        if cell.get("cell_id") == cell_id:
            return cell
    raise SystemExit(f"unknown cell_id: {cell_id}")


def private_dir(cell_id: str) -> Path:
    return ROOT / "analysis" / cell_id


def committed_dir(cell_id: str) -> Path:
    return ROOT / "analysis-committed" / cell_id


def unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    return v / norm if norm else v


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> dict[str, Any]:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n,
        "successes": successes,
        "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }


def sh(cmd: list[str], *, cwd: Path = REPO_ROOT, env: dict[str, str] | None = None) -> None:
    print(f"[prep] $ {' '.join(cmd)}", flush=True)
    merged = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, cwd=str(cwd), env=merged)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def build_candidate_pool(max_answerable: int, max_unanswerable: int) -> list[dict[str, Any]]:
    answerable: list[dict[str, Any]] = []
    trivia = REPO_ROOT / "datasets" / "triviaqa-rc-nocontext" / "validation.jsonl"
    for r in load_jsonl(trivia):
        aliases = list(r.get("answer", {}).get("aliases") or [])
        value = r.get("answer", {}).get("value")
        if value:
            aliases.append(value)
        answerable.append(
            {
                "row_key": f"triviaqa:{r.get('question_id')}",
                "source": "triviaqa",
                "role_candidate": "answerable",
                "category_canon": "triviaqa",
                "question": r["question"],
                "aliases": sorted(set(str(a) for a in aliases if str(a).strip())),
            }
        )
        if len(answerable) >= max_answerable // 2:
            break

    popqa = REPO_ROOT / "datasets" / "popqa" / "test.jsonl"
    for r in load_jsonl(popqa):
        aliases = parse_jsonish(r.get("possible_answers")) + [str(r.get("obj", ""))]
        answerable.append(
            {
                "row_key": f"popqa:{r.get('id')}",
                "source": "popqa",
                "role_candidate": "answerable",
                "category_canon": "popqa",
                "question": r["question"],
                "aliases": sorted(set(str(a) for a in aliases if str(a).strip())),
            }
        )
        if len(answerable) >= max_answerable:
            break

    unanswerable: list[dict[str, Any]] = []
    for name, filename in (
        ("kuq_unknowns_all", REPO_ROOT / "datasets" / "kuq" / "unknowns_all.jsonl"),
        ("kuq_knowns_unknowns", REPO_ROOT / "datasets" / "kuq" / "knowns_unknowns.jsonl"),
    ):
        if len(unanswerable) >= max_unanswerable:
            break
        for i, r in enumerate(load_jsonl(filename)):
            if name == "kuq_knowns_unknowns" and not r.get("unknown"):
                continue
            unanswerable.append(
                {
                    "row_key": f"{name}:{i}",
                    "source": name,
                    "role_candidate": "unanswerable",
                    "category_canon": str(r.get("category") or r.get("categories_mv") or "kuq_unknown"),
                    "question": r["question"],
                    "aliases": [],
                }
            )
            if len(unanswerable) >= max_unanswerable:
                break

    pool = answerable + unanswerable
    random.Random(SEED).shuffle(pool)
    return pool


def model_shape(cell: dict[str, Any]) -> tuple[int, int, int]:
    from transformers import AutoConfig

    cfg = AutoConfig.from_pretrained(
        cell["repo"],
        revision=cell.get("revision"),
        token=os.environ.get("HF_TOKEN") or None,
        trust_remote_code=True,
    )
    text_cfg = getattr(cfg, "text_config", cfg)
    n_layers = int(getattr(text_cfg, "num_hidden_layers"))
    hidden_dim = int(getattr(text_cfg, "hidden_size"))
    layer_idx = int(round(0.94 * (n_layers - 1)))
    return n_layers, hidden_dim, layer_idx


def tokenizer_for(cell: dict[str, Any]):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        cell["repo"],
        revision=cell.get("revision"),
        token=os.environ.get("HF_TOKEN") or None,
        trust_remote_code=True,
    )
    if tok.pad_token_id is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token
    return tok


def render_pool(cell: dict[str, Any], rows: list[dict[str, Any]], out_path: Path) -> None:
    env_model = cell["repo"]
    os.environ["DOUBT_SNAP_RENDER_MODEL"] = env_model
    os.environ["DOUBT_SNAP_RENDER_REVISION"] = cell["revision"]
    rendered = []
    for row in rows:
        rendered.append({"id": row["row_key"], "prompt": render_mod.render(row)})
    write_jsonl(out_path, rendered)


def run_baseline(cell: dict[str, Any], rows: list[dict[str, Any]], batch_size: int) -> list[dict[str, Any]]:
    pdir = private_dir(cell["cell_id"])
    prompts = pdir / "baseline_prompts.jsonl"
    gen_dir = pdir / "baseline_gen"
    render_pool(cell, rows, prompts)
    sh(
        [
            sys.executable,
            str(TUNER),
            "batch-generate",
            "--prompts",
            str(prompts),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--out-dir",
            str(gen_dir),
            "--engine",
            "hf-batched",
            "--batch-size",
            str(batch_size),
            "--max-new-tokens",
            "200",
            "--min-new-tokens",
            "1",
            "--extra-eos-token",
            "<|im_end|>",
            "--resume",
        ]
    )
    completions = {r["id"]: r for r in load_jsonl(gen_dir / "completions.jsonl")}
    graded: list[dict[str, Any]] = []
    for row in rows:
        comp = completions[row["row_key"]]
        terminated = comp.get("finish_reason") != "length"
        semantic = grader.grade_one(comp.get("completion_text", ""), row.get("aliases"))
        clean = gen_lib.grade_clean_tighten(comp.get("completion_text", ""), terminated)
        graded.append(
            {
                **row,
                "baseline_text": comp.get("completion_text", ""),
                "baseline_token_ids": comp.get("completion_token_ids", []),
                "baseline_terminated_naturally": terminated,
                "baseline_finish_reason": comp.get("finish_reason"),
                "baseline_clean": clean,
                "baseline_old_grade": semantic,
            }
        )
    write_jsonl(pdir / "baseline_graded_private.jsonl", graded)
    return graded


def run_batch_parity_smoke(cell: dict[str, Any], reference_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pdir = private_dir(cell["cell_id"])
    smoke_rows = reference_rows[:8]
    if not smoke_rows:
        return {"passed": False, "n_rows": 0, "mismatches": ["empty smoke slice"]}
    prompts = pdir / "batch_parity_seq_prompts.jsonl"
    gen_dir = pdir / "batch_parity_seq_gen"
    render_pool(cell, smoke_rows, prompts)
    sh(
        [
            sys.executable,
            str(TUNER),
            "batch-generate",
            "--prompts",
            str(prompts),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--out-dir",
            str(gen_dir),
            "--engine",
            "hf-batched",
            "--batch-size",
            "1",
            "--max-new-tokens",
            "200",
            "--min-new-tokens",
            "1",
            "--extra-eos-token",
            "<|im_end|>",
            "--resume",
        ]
    )
    seq = {r["id"]: r for r in load_jsonl(gen_dir / "completions.jsonl")}
    mismatches = []
    for row in smoke_rows:
        ref_answer = parsed_answer_value(row.get("baseline_text", ""))
        seq_row = seq[row["row_key"]]
        seq_answer = parsed_answer_value(seq_row.get("completion_text", ""))
        if ref_answer != seq_answer or row.get("baseline_finish_reason") != seq_row.get("finish_reason"):
            mismatches.append(row["row_key"])
    return {
        "passed": not mismatches,
        "n_rows": len(smoke_rows),
        "mismatches": mismatches[:10],
    }


def parsed_answer_value(text: str) -> str | None:
    obj, _ = gen_lib._find_first_json_object(str(text or ""))
    if isinstance(obj, dict) and "answer" in obj:
        return str(obj["answer"])
    return None


def assign_roles(graded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in graded:
        cand = r["role_candidate"]
        old = r["baseline_old_grade"]
        if cand == "answerable" and old["well_formed_correct"]:
            role = "known_correct_answered"
        elif cand == "unanswerable" and old["refused"]:
            role = "unknown_refused"
        elif cand == "unanswerable" and old["answered"]:
            role = "confab"
        else:
            continue
        rows.append({**r, "role": role})
    return rows


def stratified_split(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    out: list[dict[str, Any]] = []
    for role in ("known_correct_answered", "confab"):
        by_cat: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if row["role"] == role:
                by_cat.setdefault(str(row.get("category_canon")), []).append(row)
        for cat_rows in by_cat.values():
            cat_rows.sort(key=lambda x: x["row_key"])
            rng.shuffle(cat_rows)
            n_fit = max(1, int(round(len(cat_rows) * 0.40)))
            for i, row in enumerate(cat_rows):
                out.append({**row, "split": "fit" if i < n_fit else "held_out"})
    for row in rows:
        if row["role"] == "unknown_refused":
            out.append({**row, "split": "fit_only"})
    out.sort(key=lambda x: (x["role"], x.get("split", ""), x["row_key"]))
    return out


def capture_anchor(cell: dict[str, Any], rows: list[dict[str, Any]], layer_idx: int, batch_size: int) -> dict[str, np.ndarray]:
    from safetensors.torch import load_file

    pdir = private_dir(cell["cell_id"])
    tok = tokenizer_for(cell)
    os.environ["DOUBT_SNAP_RENDER_MODEL"] = cell["repo"]
    os.environ["DOUBT_SNAP_RENDER_REVISION"] = cell["revision"]
    cap_rows = []
    for row in rows:
        prompt = render_mod.render(row)
        token_ids = tok(prompt, add_special_tokens=True)["input_ids"]
        cap_rows.append(
            {
                "id": row["row_key"],
                "token_ids": token_ids,
                "positions": {"anchor": len(token_ids) - 1},
            }
        )
    cap_in = pdir / "anchor_capture_rows.jsonl"
    cap_dir = pdir / "anchor_capture"
    write_jsonl(cap_in, cap_rows)
    sh(
        [
            sys.executable,
            str(TUNER),
            "batch-capture",
            "--rows",
            str(cap_in),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--out-dir",
            str(cap_dir),
            "--engine",
            "hf-batched",
            "--layers",
            str(layer_idx + 1),
            "--persist-dtype",
            "float32",
            "--batch-size",
            str(batch_size),
            "--resume",
        ]
    )
    index = load_jsonl(cap_dir / "capture.jsonl")
    H: dict[str, np.ndarray] = {}
    key = f"anchor__L{layer_idx + 1}"
    for rec in index:
        tensors = load_file(str(cap_dir / rec["file"]))
        H[rec["id"]] = tensors[key].float().cpu().numpy().astype(np.float64)
    return H


def fit_directions(rows: list[dict[str, Any]], H: dict[str, np.ndarray], layer_idx: int, hidden_dim: int) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    known_fit = [r["row_key"] for r in rows if r["role"] == "known_correct_answered" and r["split"] == "fit"]
    confab_fit = [r["row_key"] for r in rows if r["role"] == "confab" and r["split"] == "fit"]
    unknown = [r["row_key"] for r in rows if r["role"] == "unknown_refused"]
    if not known_fit or not confab_fit or not unknown:
        raise RuntimeError("cannot fit directions with an empty FIT role")
    h_known = np.stack([H[k] for k in known_fit])
    h_unknown = np.stack([H[k] for k in unknown])
    u_d = unit(h_known.mean(0) - h_unknown.mean(0))
    ak_keys = unknown + confab_fit
    h_ak = np.stack([H[k] for k in ak_keys])
    y_confab = np.array([0] * len(unknown) + [1] * len(confab_fit), dtype=int)
    caution = unit(h_ak[y_confab == 0].mean(0) - h_ak[y_confab == 1].mean(0))
    scaler = StandardScaler().fit(h_ak)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0, random_state=SEED)
    clf.fit(scaler.transform(h_ak), y_confab)
    u_p = unit(clf.coef_.ravel() / scaler.scale_)
    q, _ = np.linalg.qr(np.stack([u_d, u_p], axis=1))
    c_hat = unit(caution - q @ (q.T @ caution))
    fit_keys = confab_fit + known_fit
    h_fit = np.stack([H[k] for k in fit_keys])
    proj_d = h_fit @ u_d
    proj_c = h_fit @ c_hat
    rng = np.random.default_rng(SEED + hidden_dim + layer_idx)
    random_dir = unit(rng.normal(size=hidden_dim))
    return {
        "u_d": u_d,
        "u_p": u_p,
        "caution_dir": caution,
        "c_hat": c_hat,
        "random_direction": random_dir,
        "stats": {
            "layer": layer_idx,
            "hidden_dim": hidden_dim,
            "n_known_fit": len(known_fit),
            "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown),
            "mu_d": float(proj_d.mean()),
            "sigma_d": float(proj_d.std() or 1.0),
            "mu_c": float(proj_c.mean()),
            "sigma_c": float(proj_c.std() or 1.0),
        },
    }


def fit_byte_identical(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("u_d", "u_p", "caution_dir", "c_hat", "random_direction"):
        if not np.array_equal(left[key], right[key]):
            return False
    return left["stats"] == right["stats"]


def direction_record(vector: np.ndarray, sigma: float, role: str, layer_idx: int, hidden_dim: int, cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "mechinterp-direction/v1",
        "layer": int(layer_idx),
        "hidden_dim": int(hidden_dim),
        "normalized": True,
        "vector": [float(x) for x in vector],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * int(hidden_dim),
        "sigma": float(sigma),
        "calibration": {},
        "recipe": {"source": "doubt-snap-cross-family-confirmatory/prep_tuner_cell.py"},
        "provenance": {
            "role": role,
            "amendment": "doubt-snap-cross-family-confirmatory",
            "cell_id": cell["cell_id"],
            "base_model": cell["repo"],
            "revision": cell["revision"],
            "fit_population": "FIT split only",
        },
    }


def save_directions(cell: dict[str, Any], fit: dict[str, Any]) -> None:
    cdir = committed_dir(cell["cell_id"])
    stats = fit["stats"]
    write_json(cdir / "u_d.json", direction_record(fit["u_d"], 1.0, "doubt_sensor_u_d", stats["layer"], stats["hidden_dim"], cell))
    write_json(cdir / "c_hat.json", direction_record(fit["c_hat"], stats["sigma_c"], "snap_write_direction", stats["layer"], stats["hidden_dim"], cell))
    write_json(cdir / "random_direction.json", direction_record(fit["random_direction"], 1.0, "random_direction_placebo", stats["layer"], stats["hidden_dim"], cell))
    write_json(cdir / "build_manifest.json", {**stats, "cell_id": cell["cell_id"], "base_model": cell["repo"], "revision": cell["revision"]})


def attach_gate(rows: list[dict[str, Any]], H: dict[str, np.ndarray], fit: dict[str, Any], cell_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from sklearn.metrics import roc_auc_score

    u_d = fit["u_d"]
    mu = fit["stats"]["mu_d"]
    sigma = fit["stats"]["sigma_d"] or 1.0
    scored = []
    for row in rows:
        proj = float(H[row["row_key"]] @ u_d)
        z_d = float(np.clip((proj - mu) / sigma, -2.0, 2.0))
        scored.append({**row, "proj_d": proj, "z_d": z_d, "score_neg_z_d": -z_d})
    fit_rows = [r for r in scored if r.get("split") == "fit" and r["role"] in ("confab", "known_correct_answered")]
    scores = np.array([r["score_neg_z_d"] for r in fit_rows])
    labels = np.array([1 if r["role"] == "confab" else 0 for r in fit_rows])
    auc = float(roc_auc_score(labels, scores))
    best_tau = float(scores[0])
    best_j = -1e9
    best = {}
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if tp + fn else 0.0
        fpr = fp / (fp + tn) if fp + tn else 0.0
        if tpr - fpr > best_j:
            best_j = tpr - fpr
            best_tau = float(tau)
            best = {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr, "youden_j": best_j}
    out = [{**r, "fire": bool(r["score_neg_z_d"] >= best_tau), "tau": best_tau} for r in scored]
    gate_summary = {"auc_neg_z_d_on_fit": auc, "tau_frozen": best_tau, "youden_tau": best}
    write_json(committed_dir(cell_id) / "gate_fit.json", gate_summary)
    return out, gate_summary


def counts_by_role(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        role: {
            split: sum(1 for r in rows if r["role"] == role and r["split"] == split)
            for split in ("fit", "held_out", "fit_only")
        }
        for role in ("known_correct_answered", "confab", "unknown_refused")
    }


def dose_grid_for_cell(cfg: dict[str, Any], cell_id: str) -> list[float]:
    sel = cfg["snap"]["dose_selection"]
    per_cell = sel.get("per_cell_candidate_realized_projection_targets") or {}
    return [float(x) for x in per_cell.get(cell_id, sel["candidate_realized_projection_targets"])]


def materialize_dose_sweep(cell: dict[str, Any], rows_path: Path, batch_size: int) -> Path:
    cfg = load_yaml(ROOT / "cell.yaml")
    dose_grid = dose_grid_for_cell(cfg, cell["cell_id"])
    cdir = committed_dir(cell["cell_id"])
    pdir = private_dir(cell["cell_id"])
    c_hat = load_json(cdir / "c_hat.json")
    sigma = float(c_hat.get("sigma") or 1.0)
    arms = [{"name": "baseline", "strength": 0.0}]
    for dose in dose_grid:
        arms.append({"name": f"dose_{int(dose)}", "strength": dose / sigma, "flag_field": "fire"})
    recipe = {
        "surface": {
            "rows_path": str(rows_path),
            "seed": SEED,
            "generation": {"max_new_tokens": 200, "min_new_tokens": 1, "do_sample": False, "extra_eos_tokens": ["<|im_end|>"]},
        },
        "readouts": [{"name": "c_hat", "path": str(cdir / "c_hat.json")}],
        "law": {"kind": "erase_write", "readout": "c_hat", "position": "anchor_onward", "generation_mode": "gen_stream"},
        "arms": arms,
        "execution": {
            "output_path": str(pdir / "rows_out_dose_fit.jsonl"),
            "resume": True,
            "render_fn": "render:render",
            "grader": "grader:grade",
            "batch_size": batch_size,
        },
        "smoke": {"n_rows": 8, "write_rel_tol": 0.05, "write_abs_floor": 0.5, "offtarget_tol": 0.001, "gen_stream_probe_strength": max(dose_grid)},
    }
    out = pdir / "steer_dose_fit.yaml"
    out.write_text(yaml.safe_dump(recipe, sort_keys=False), encoding="utf-8")
    return out


def prepare(args: argparse.Namespace) -> None:
    cell = cell_by_id(args.cell_id)
    pdir = private_dir(args.cell_id)
    cdir = committed_dir(args.cell_id)
    pdir.mkdir(parents=True, exist_ok=True)
    cdir.mkdir(parents=True, exist_ok=True)
    pool = build_candidate_pool(args.max_answerable, args.max_unanswerable)
    write_jsonl(pdir / "candidate_pool_private.jsonl", pool)
    graded = run_baseline(cell, pool, args.batch_size)
    parity = run_batch_parity_smoke(cell, graded)
    split_rows = stratified_split(assign_roles(graded))
    write_jsonl(pdir / "split_rows_private.jsonl", split_rows)
    counts = counts_by_role(split_rows)
    n_layers, hidden_dim, layer_idx = model_shape(cell)
    H = capture_anchor(cell, split_rows, layer_idx, args.batch_size)
    fit = fit_directions(split_rows, H, layer_idx, hidden_dim)
    fit2 = fit_directions(split_rows, H, layer_idx, hidden_dim)
    directions_byte_identical = fit_byte_identical(fit, fit2)
    save_directions(cell, fit)
    fired, gate_summary = attach_gate(split_rows, H, fit, args.cell_id)
    fit_rows = [strip_private(r) for r in fired if r["split"] == "fit" and r["role"] in ("confab", "known_correct_answered")]
    heldout_rows = [strip_private(r) for r in fired if r["split"] == "held_out" and r["role"] in ("confab", "known_correct_answered")]
    write_jsonl(pdir / "fit_rows_for_dose.jsonl", fit_rows)
    write_jsonl(pdir / "heldout_rows_for_steer.jsonl", heldout_rows)
    dose_cfg = materialize_dose_sweep(cell, pdir / "fit_rows_for_dose.jsonl", args.batch_size)
    g0 = {
        "counts": counts,
        "held_out_power": counts["confab"]["held_out"] >= 150 and counts["known_correct_answered"]["held_out"] >= 250,
        "generation_terminates_rate": sum(1 for r in split_rows if r["baseline_terminated_naturally"]) / max(1, len(split_rows)),
        "generation_terminates_pass": sum(1 for r in split_rows if r["baseline_terminated_naturally"]) / max(1, len(split_rows)) >= 0.90,
        "gate_auc_on_fit": gate_summary["auc_neg_z_d_on_fit"],
        "gate_auc_pass": gate_summary["auc_neg_z_d_on_fit"] >= 0.90,
        "directions_byte_identical": directions_byte_identical,
        "batched_parity_smoke": parity,
        "n_layers": n_layers,
        "hidden_dim": hidden_dim,
        "layer_idx": layer_idx,
        "dose_sweep_config": str(dose_cfg),
    }
    write_json(cdir / "g0_prep_summary.json", g0)
    write_json(cdir / "split_manifest.json", {"cell_id": args.cell_id, "rows": [{"row_key": r["row_key"], "role": r["role"], "split": r["split"], "source": r["source"], "category_canon": r.get("category_canon")} for r in split_rows]})
    print(json.dumps(g0, indent=2), flush=True)
    if not (
        g0["held_out_power"]
        and g0["generation_terminates_pass"]
        and g0["gate_auc_pass"]
        and g0["directions_byte_identical"]
        and g0["batched_parity_smoke"]["passed"]
    ):
        raise SystemExit(3)


def strip_private(row: dict[str, Any]) -> dict[str, Any]:
    keep = {
        "row_key", "question", "aliases", "role", "split", "source",
        "category_canon", "fire", "tau", "score_neg_z_d", "z_d",
        "baseline_terminated_naturally",
    }
    return {k: row[k] for k in keep if k in row}


def pop_summary(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    return wilson(sum(1 for r in rows if bool(r.get(metric))), len(rows))


def select_dose(args: argparse.Namespace) -> None:
    cfg = load_yaml(ROOT / "cell.yaml")
    dose_grid = dose_grid_for_cell(cfg, args.cell_id)
    rows = load_jsonl(private_dir(args.cell_id) / "rows_out_dose_fit.jsonl")
    reports = []
    selected = None
    for dose in dose_grid:
        arm = f"dose_{int(dose)}"
        arm_rows = [r for r in rows if r.get("arm") == arm]
        confab = [r for r in arm_rows if r.get("role") == "confab"]
        known = [r for r in arm_rows if r.get("role") == "known_correct_answered"]
        report = {
            "dose": dose,
            "confab_tighten": pop_summary(confab, "clean_tighten"),
            "known_correct_cost_control": pop_summary(known, "not_well_formed_correct"),
        }
        reports.append(report)
        if selected is None and report["confab_tighten"]["rate"] >= 0.60 and report["known_correct_cost_control"]["rate"] <= 0.10:
            selected = dose
    payload = {"selected_dose": selected, "reports": reports}
    write_json(committed_dir(args.cell_id) / "dose_fit.json", payload)
    print(json.dumps(payload, indent=2), flush=True)
    if selected is None:
        raise SystemExit(4)


def score_heldout(args: argparse.Namespace) -> None:
    pdir = private_dir(args.cell_id)
    cdir = committed_dir(args.cell_id)
    c_rows = load_jsonl(pdir / "rows_out_c_hat.jsonl")
    r_rows = load_jsonl(pdir / "rows_out_random_dir.jsonl")

    def arm(name: str, rows: list[dict[str, Any]] = c_rows) -> list[dict[str, Any]]:
        return [r for r in rows if r.get("arm") == name]

    def by_pop(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        return [r for r in rows if r.get("role") == "confab"], [r for r in rows if r.get("role") == "known_correct_answered"]

    base_confab, base_known = by_pop(arm("baseline"))
    gated_confab, gated_known = by_pop(arm("gated"))
    perm_confab, perm_known = by_pop(arm("permuted_gate"))
    rand_confab, rand_known = by_pop(arm("random_direction", r_rows))
    summary = {
        "baseline": {"confab_tighten": pop_summary(base_confab, "clean_tighten"), "known_correct_cost_control": pop_summary(base_known, "not_well_formed_correct")},
        "gated": {"confab_tighten": pop_summary(gated_confab, "clean_tighten"), "known_correct_cost_control": pop_summary(gated_known, "not_well_formed_correct")},
        "permuted_gate": {"confab_tighten": pop_summary(perm_confab, "clean_tighten"), "known_correct_cost_control": pop_summary(perm_known, "not_well_formed_correct")},
        "random_direction": {"confab_tighten": pop_summary(rand_confab, "clean_tighten"), "known_correct_cost_control": pop_summary(rand_known, "not_well_formed_correct")},
    }
    g1 = summary["gated"]["confab_tighten"]
    g2 = summary["gated"]["known_correct_cost_control"]
    rd_confab_delta = summary["random_direction"]["confab_tighten"]["rate"] - summary["baseline"]["confab_tighten"]["rate"]
    rd_known_delta = summary["random_direction"]["known_correct_cost_control"]["rate"] - summary["baseline"]["known_correct_cost_control"]["rate"]
    gates = {
        "g1_pass": g1["rate"] >= 0.60 and g1["wilson_ci_95"][0] > 0.50,
        "g2_pass": g2["rate"] <= 0.05 and g2["wilson_ci_95"][1] < 0.10,
        "g3i_pass": rd_confab_delta <= 0.02 and rd_known_delta <= 0.02,
        "g3ii_pass": summary["permuted_gate"]["known_correct_cost_control"]["rate"] > summary["gated"]["known_correct_cost_control"]["rate"],
        "g3i_random_minus_baseline": {"confab_clean_tighten": rd_confab_delta, "known_false_refusal": rd_known_delta},
    }
    gates["cell_pass"] = bool(gates["g1_pass"] and gates["g2_pass"] and gates["g3i_pass"] and gates["g3ii_pass"])
    payload = {"cell_id": args.cell_id, "summary": summary, "gates": gates, "status": "passed" if gates["cell_pass"] else "failed"}
    write_json(cdir / "summary.json", payload)
    print(json.dumps(payload, indent=2), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--cell-id", required=True)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--max-answerable", type=int, default=DEFAULT_MAX_ANSWERABLE)
    p.add_argument("--max-unanswerable", type=int, default=DEFAULT_MAX_UNANSWERABLE)
    s = sub.add_parser("select-dose")
    s.add_argument("--cell-id", required=True)
    h = sub.add_parser("score-heldout")
    h.add_argument("--cell-id", required=True)
    args = parser.parse_args()
    if args.cmd == "prepare":
        prepare(args)
    elif args.cmd == "select-dose":
        select_dose(args)
    elif args.cmd == "score-heldout":
        score_heldout(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
