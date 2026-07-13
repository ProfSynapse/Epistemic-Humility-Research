#!/usr/bin/env python3
"""Stage B: extract FIT anchors at candidate layers on Qwen/Qwen3.5-4B and
fit the doubt gate (u_d) + snap write direction (c_hat) at each, mirroring
doubt-snap-cross-family-confirmatory's own recipe (prep_tuner_cell.py
`fit_directions`) exactly, so the mid-band cells are the SAME instrument
class as the late-site null, differing only in layer.

Recipe (byte-for-byte port of prep_tuner_cell.py's fit_directions /
fit_byte_identical, generalized to loop over multiple layers in one model
load instead of one tuner batch-capture call per layer):
  u_d       = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))
  caution   = unit(mean(H[unknown_refused]) - mean(H[confab FIT]))          (mass-mean)
  u_p       = unit(LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000,
              random_state=SEED).fit(StandardScaler(H[unknown_refused+confab_fit])
              ).coef_ / scale_)                                            (confab propensity)
  c_hat     = unit(caution orthogonalized against span(u_d, u_p))          (QR erase)
  random_direction = unit(np.random.default_rng(SEED+hidden_dim+layer_idx).normal(...))
  mu_d/sigma_d, mu_c/sigma_c computed over FIT (confab_fit + known_fit) projections.

Anchor position: prompt_len - 1 (last prompt token, pre-generation), rendered
with doubt-snap-cross-family-confirmatory's own BASELINE_SYSTEM_PROMPT +
chat template (enable_thinking=False) -- copied from that experiment's
render.py so this experiment's anchors are computed under the IDENTICAL
prompt surface as the reused rows' frozen late-site (hs30) instrument,
keeping any comparison to the cited late-site null apples-to-apples.

Gate: neg_z_d = -z_d, z_d clipped to [-2,2] and standardized with each
layer's own FIT mu_d/sigma_d; tau frozen via Youden-J on FIT confab vs
known_correct_answered (mirrors gate_fit.py).

Reproducibility guard: fits every layer TWICE (independent extraction reuse,
same cached anchors) and asserts byte-identical vectors before writing
anything, exactly mirroring prep_tuner_cell.py's fit_byte_identical check.

Outputs:
  analysis/anchor_extract.safetensors        (gitignored; one tensor per
                                               (hs_index, row_key), FIT rows only)
  analysis-committed/directions/hs{N}/u_d.json, c_hat.json, random_direction.json
  analysis-committed/build_manifest.json      (per-layer mu/sigma/AUC/tau stats)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

MODEL_NAME = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
HIDDEN_DIM = 2560
SEED = 20260707

FIT_ROWS_PATH = ANALYSIS / "fit_rows_for_anchor.jsonl"
ANCHOR_TENSORS_PATH = ANALYSIS / "anchor_extract.safetensors"
ANCHOR_MANIFEST_PATH = ANALYSIS / "anchor_extract_manifest.json"

# doubt-snap-cross-family-confirmatory's render.py, copied verbatim (see its
# provenance note in this module's docstring).
BASELINE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render(tokenizer, question: str) -> str:
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False,
    )


# --------------------------------------------------------------------------
# Stage B.1: anchor extraction (GPU)
# --------------------------------------------------------------------------

def cmd_extract(args) -> int:
    import torch
    from safetensors.torch import save_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    hs_indices = [int(x) for x in args.layers.split(",")]
    rows = load_jsonl(FIT_ROWS_PATH)
    print(f"[extract] {len(rows)} FIT rows, hs_indices={hs_indices}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, dtype=torch.bfloat16,
        device_map="cuda", trust_remote_code=True)
    model.eval()
    device = next(model.parameters()).device
    text_cfg = getattr(model.config, "text_config", model.config)
    n_layers = int(text_cfg.num_hidden_layers)
    hidden_dim = int(text_cfg.hidden_size)
    assert hidden_dim == HIDDEN_DIM, f"expected hidden_dim={HIDDEN_DIM}, got {hidden_dim}"
    assert max(hs_indices) <= n_layers, f"hs_indices {hs_indices} exceed n_layers={n_layers}"

    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    t0 = time.time()
    for i, row in enumerate(rows):
        prompt = render(tokenizer, row["question"])
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        if len(hs) != n_layers + 1:
            raise RuntimeError(
                f"hidden_states length mismatch: got {len(hs)}, expected {n_layers + 1}")
        skey = _sanitize_key(row["row_key"])
        for hs_index in hs_indices:
            vec = hs[hs_index][0, prompt_len - 1, :].float().cpu().contiguous()
            tensors[f"hs{hs_index}__{skey}"] = vec
        row_meta.append({
            "row_key": row["row_key"], "safetensors_key": skey,
            "role": row["role"], "split": row.get("split"),
            "prompt_len": prompt_len,
        })
        if (i + 1) % 200 == 0 or (i + 1) == len(rows):
            print(f"[extract] {i + 1}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    save_file(tensors, str(ANCHOR_TENSORS_PATH))
    manifest = {
        "base_model": MODEL_NAME, "revision": MODEL_REVISION, "substrate": "bf16",
        "hidden_dim": hidden_dim, "n_layers": n_layers,
        "hs_indices": hs_indices, "anchor_position": "prompt_len-1",
        "render": "doubt-snap-cross-family-confirmatory BASELINE_SYSTEM_PROMPT "
                  "+ chat template, enable_thinking=False",
        "n_rows_extracted": len(rows),
        "runtime_sec": round(time.time() - t0, 1),
        "rows": row_meta,
    }
    ANCHOR_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[extract] wrote {ANCHOR_TENSORS_PATH} ({len(tensors)} vectors) and "
          f"{ANCHOR_MANIFEST_PATH}", flush=True)
    return 0


# --------------------------------------------------------------------------
# Stage B.2: direction fit + gate fit (CPU, numpy/sklearn only)
# --------------------------------------------------------------------------

def _tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{_sanitize_key(row_key)}"


def _fit_all(fresh: dict, role_by_key: dict, hs_index: int, hidden_dim: int) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    known_fit = [rk for rk, role in role_by_key.items() if role == "known_correct_answered"]
    confab_fit = [rk for rk, role in role_by_key.items() if role == "confab"]
    unknown = [rk for rk, role in role_by_key.items() if role == "unknown_refused"]
    if not known_fit or not confab_fit or not unknown:
        raise RuntimeError("cannot fit directions with an empty FIT role")

    h_known = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in known_fit])
    h_unknown = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in unknown])
    u_d = unit(h_known.mean(0) - h_unknown.mean(0))

    ak_keys = unknown + confab_fit
    h_ak = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in ak_keys])
    y_confab = np.array([0] * len(unknown) + [1] * len(confab_fit), dtype=int)
    caution = unit(h_ak[y_confab == 0].mean(0) - h_ak[y_confab == 1].mean(0))
    scaler = StandardScaler().fit(h_ak)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0,
                              random_state=SEED)
    clf.fit(scaler.transform(h_ak), y_confab)
    u_p = unit(clf.coef_.ravel() / scaler.scale_)

    q, _ = np.linalg.qr(np.stack([u_d, u_p], axis=1))
    c_hat = unit(caution - q @ (q.T @ caution))

    fit_keys = confab_fit + known_fit
    h_fit = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in fit_keys])
    proj_d = h_fit @ u_d
    proj_c = h_fit @ c_hat
    rng = np.random.default_rng(SEED + hidden_dim + hs_index)
    random_dir = unit(rng.normal(size=hidden_dim))

    labels = np.array([1] * len(confab_fit) + [0] * len(known_fit), dtype=int)

    return {
        "u_d": u_d, "u_p": u_p, "caution_dir": caution, "c_hat": c_hat,
        "random_direction": random_dir,
        "known_fit": known_fit, "confab_fit": confab_fit, "unknown_refused": unknown,
        "stats": {
            "hs_index": hs_index, "hidden_dim": hidden_dim,
            "n_known_fit": len(known_fit), "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown),
            "mu_d": float(proj_d.mean()), "sigma_d": float(proj_d.std() or 1.0),
            "mu_c": float(proj_c.mean()), "sigma_c": float(proj_c.std() or 1.0),
            "cos_u_d_u_p": float(np.dot(u_d, u_p)),
            "cos_caution_c_hat": float(np.dot(caution, c_hat)),
        },
        "proj_d_fit": proj_d, "labels": labels,
    }


def _fit_byte_identical(a: dict, b: dict) -> bool:
    for key in ("u_d", "u_p", "caution_dir", "c_hat", "random_direction"):
        if not np.array_equal(a[key], b[key]):
            return False
    return a["stats"] == b["stats"]


def _roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        count = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
        return float(count / (len(pos) * len(neg)))


def _youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    best_tau, best_j, best_stats = None, -1e9, None
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        j = tpr - fpr
        if j > best_j:
            best_tau, best_j = float(tau), j
            best_stats = {"tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr,
                          "tp": tp, "fn": fn, "fp": fp, "tn": tn, "youden_j": j}
    assert best_tau is not None
    return best_tau, best_stats


def _direction_record(vector: np.ndarray, sigma: float, role: str, hs_index: int,
                       hidden_dim: int, extra: dict) -> dict:
    return {
        "schema_version": "mechinterp-direction/v1",
        "layer": int(hs_index - 1),  # 0-indexed decoder block, matching project convention
        "hidden_dim": int(hidden_dim),
        "normalized": True,
        "vector": [float(x) for x in vector],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * int(hidden_dim),
        "sigma": float(sigma),
        "calibration": {},
        "recipe": {"source": "fit_midband_directions.py",
                  "mirrors": "doubt-snap-cross-family-confirmatory/prep_tuner_cell.py:fit_directions"},
        "provenance": {
            "role": role, "amendment": "qwen35-4b-midband-doubt-snap",
            "base_model": MODEL_NAME, "revision": MODEL_REVISION,
            "fit_population": "FIT split only (reused verbatim from "
                              "doubt-snap-cross-family-confirmatory)",
            "hs_index": hs_index, **extra,
        },
    }


def cmd_fit(args) -> int:
    from safetensors.numpy import load_file

    hs_indices = [int(x) for x in args.layers.split(",")]
    anchor_manifest = json.loads(ANCHOR_MANIFEST_PATH.read_text())
    role_by_key = {rm["row_key"]: rm["role"] for rm in anchor_manifest["rows"]}
    hidden_dim = int(anchor_manifest["hidden_dim"])
    fresh = {k: np.asarray(v, dtype=np.float64)
             for k, v in load_file(str(ANCHOR_TENSORS_PATH)).items()}

    report = {
        "base_model": MODEL_NAME, "revision": MODEL_REVISION, "hidden_dim": hidden_dim,
        "seed": SEED, "reproducibility_verified": True,
        "anchor_manifest_sha256": _sha256_file(ANCHOR_MANIFEST_PATH),
        "fit_rows_sha256": _sha256_file(FIT_ROWS_PATH),
        "layers": {},
    }

    COMMITTED.mkdir(parents=True, exist_ok=True)
    for hs_index in hs_indices:
        fit1 = _fit_all(fresh, role_by_key, hs_index, hidden_dim)
        fit2 = _fit_all(fresh, role_by_key, hs_index, hidden_dim)
        if not _fit_byte_identical(fit1, fit2):
            raise SystemExit(f"REPRODUCIBILITY FAIL at hs{hs_index}: refit is not byte-identical")
        print(f"[fit] hs{hs_index} reproducibility check PASS", flush=True)

        labels = fit1["labels"]
        proj_d_fit = fit1["proj_d_fit"]
        stats = fit1["stats"]
        z_d = np.clip((proj_d_fit - stats["mu_d"]) / stats["sigma_d"], -2.0, 2.0)
        score = -z_d
        auc = _roc_auc(score, labels)
        tau, tau_stats = _youden_tau(score, labels)

        layer_dir = COMMITTED / "directions" / f"hs{hs_index}"
        layer_dir.mkdir(parents=True, exist_ok=True)
        u_d_json = _direction_record(
            fit1["u_d"], 1.0, "doubt_sensor_u_d", hs_index, hidden_dim,
            {"method": "unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))",
             "n_known_fit": stats["n_known_fit"], "n_unknown_refused": stats["n_unknown_refused"]})
        (layer_dir / "u_d.json").write_text(json.dumps(u_d_json, indent=2))
        c_hat_json = _direction_record(
            fit1["c_hat"], stats["sigma_c"], "snap_write_direction_c_hat", hs_index, hidden_dim,
            {"method": "mass-mean caution direction orthogonalized against span(u_d, u_p) via QR",
             "cos_caution_c_hat": stats["cos_caution_c_hat"],
             "n_confab_fit": stats["n_confab_fit"]})
        (layer_dir / "c_hat.json").write_text(json.dumps(c_hat_json, indent=2))
        rand_json = _direction_record(
            fit1["random_direction"], 1.0, "random_direction_placebo", hs_index, hidden_dim,
            {"method": "np.random.default_rng(SEED + hidden_dim + hs_index).normal(...)"})
        (layer_dir / "random_direction.json").write_text(json.dumps(rand_json, indent=2))

        report["layers"][f"hs{hs_index}"] = {
            **stats,
            "auc_neg_z_d_on_fit": auc,
            "tau_frozen": tau,
            "youden_tau_stats": tau_stats,
        }
        print(f"[fit] hs{hs_index}: AUC={auc:.4f} tau={tau:.4f} sigma_c={stats['sigma_c']:.4f} "
              f"mu_c={stats['mu_c']:.4f}", flush=True)

    out_path = COMMITTED / "build_manifest.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[fit] wrote {out_path}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="GPU anchor extraction at chosen hs_indices")
    p_extract.add_argument("--layers", required=True, help="comma-separated hs_index values")
    p_extract.set_defaults(func=cmd_extract)

    p_fit = sub.add_parser("fit", help="CPU direction + gate fit from extracted anchors")
    p_fit.add_argument("--layers", required=True, help="comma-separated hs_index values")
    p_fit.set_defaults(func=cmd_fit)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
