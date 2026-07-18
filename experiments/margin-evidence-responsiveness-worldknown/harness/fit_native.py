#!/usr/bin/env python3
"""NATIVE world-known direction fit for margin-evidence-responsiveness-
worldknown (M4-WK) (cell.yaml `directions.native.fit_procedure`).

Wraps `fit_midband_directions.py`'s verbatim recipe (extract + fit
subcommands, read in full before writing this), run on the native_fit_split
(from selection.py) with roles remapped: correct_on_answerable ->
known_correct_answered, refused_on_answerable -> unknown_refused,
confab_on_answerable -> confab. Same recipe:

  u_d       = unit(mean(H[known]) - mean(H[unknown_refused]))
  caution   = unit(mean(H[unknown_refused]) - mean(H[confab]))
  u_p       = unit(LogisticRegression(...).coef_ / scale_)
  c_hat     = unit(caution orthogonalized against span(u_d, u_p))   (QR erase)
  reproducibility: fit TWICE, assert byte-identical before writing anything.

Two subcommands:
  extract   GPU. hs20 anchor (prompt_len-1) for every native_fit_split row,
            baseline render (no context injection -- the c_hat fit,
            mirroring KUQ, is on the plain question prompt).
  fit       CPU. Direction fit + MINOR m2 sign assertion (mean_raw_proj
            (confab) < mean_raw_proj(refused), raw pre-negation projection)
            + fork-1 reference-dose derivation (8x native sigma_c). Writes
            `analysis-committed/directions/hs20/c_hat_worldknown.json`
            (mechinterp-direction/v1) and a stats-only build manifest
            alongside it (no row text).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import popqa_pool  # noqa: E402
import batching  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
ANCHOR_TENSORS_PATH = ANALYSIS / "native_fit" / "anchor_extract.safetensors"
ANCHOR_MANIFEST_PATH = ANALYSIS / "native_fit" / "anchor_extract_manifest.json"
NATIVE_DIR = COMMITTED / "directions" / "hs20"

SEED = 20260707  # SAME seed fit_midband_directions.py uses (SEED constant), carried verbatim (recipe reuse, not a new registered seed)

ROLE_REMAP = {"confab": "confab", "correct": "known_correct_answered", "refused": "unknown_refused"}


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_native_fit_split_rows() -> list[dict[str, Any]]:
    path = SELECTION_DIR / "native_fit_split.json"
    if not path.is_file():
        raise SystemExit(f"fit_native FAIL: no {path}; run selection.py first.")
    payload = common.load_json(path)
    pool = popqa_pool.load_pool()
    rows: list[dict[str, Any]] = []
    for short, row_keys in payload["row_keys"].items():
        role = ROLE_REMAP[short]
        for rk in row_keys:
            if rk not in pool:
                raise SystemExit(f"fit_native FAIL: row_key {rk!r} not found in PopQA pool")
            r = pool[rk]
            rows.append({"row_key": rk, "role": role, "question": r["question"]})
    return rows


# ---------------------------------------------------------------------------
# extract (GPU)
# ---------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[fit_native extract] this loads the model and runs a forward pass on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os

    import torch
    from safetensors.torch import save_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["M4WK_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M4WK_RENDER_REVISION"] = config.MODEL_REVISION
    import render as render_mod

    config.assert_pinned_hashes()
    rows = load_native_fit_split_rows()
    rows_sorted = sorted(rows, key=lambda r: batching._popqa_numeric_id(r["row_key"]))
    print(f"[fit_native extract] {len(rows_sorted)} native_fit_split rows, hs_index={config.NATIVE_HS_INDEX}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_REPO, revision=config.MODEL_REVISION, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(config.MODEL_REPO, revision=config.MODEL_REVISION, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True)
    model.eval()
    device = next(model.parameters()).device
    text_cfg = getattr(model.config, "text_config", model.config)
    n_layers = int(text_cfg.num_hidden_layers)
    hidden_dim = int(text_cfg.hidden_size)
    if hidden_dim != config.HIDDEN_DIM:
        raise SystemExit(f"fit_native extract FAIL: hidden_dim {hidden_dim} != expected {config.HIDDEN_DIM}")

    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    t0 = time.time()
    for i, row in enumerate(rows_sorted):
        prompt = render_mod.render({"row_key": row["row_key"], "question": row["question"], "context": None})
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        if len(hs) != n_layers + 1:
            raise RuntimeError(f"hidden_states length mismatch: got {len(hs)}, expected {n_layers + 1}")
        vec = hs[config.NATIVE_HS_INDEX][0, prompt_len - 1, :].float().cpu().contiguous()
        tensors[_sanitize_key(row["row_key"])] = vec
        row_meta.append({"row_key": row["row_key"], "safetensors_key": _sanitize_key(row["row_key"]), "role": row["role"], "prompt_len": prompt_len})
        if (i + 1) % 100 == 0 or (i + 1) == len(rows_sorted):
            print(f"[fit_native extract] {i + 1}/{len(rows_sorted)} ({time.time() - t0:.0f}s)", flush=True)

    ANCHOR_TENSORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_file(tensors, str(ANCHOR_TENSORS_PATH))
    manifest = {
        "base_model": config.MODEL_REPO, "revision": config.MODEL_REVISION, "substrate": "bf16",
        "hidden_dim": hidden_dim, "n_layers": n_layers, "hs_index": config.NATIVE_HS_INDEX,
        "anchor_position": "prompt_len-1", "render": "M4-WK baseline render (no context), byte-identical prompt contract to M1/M2/doubt-snap",
        "n_rows_extracted": len(rows_sorted), "runtime_sec": round(time.time() - t0, 1),
        "rows": row_meta,
    }
    common.write_json(ANCHOR_MANIFEST_PATH, manifest)
    print(f"[fit_native extract] wrote {ANCHOR_TENSORS_PATH} ({len(tensors)} vectors) and {ANCHOR_MANIFEST_PATH}", flush=True)

    del model
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return 0


# ---------------------------------------------------------------------------
# fit (CPU)
# ---------------------------------------------------------------------------

def _fit_all(fresh: dict, role_by_key: dict, hidden_dim: int) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    known_fit = [rk for rk, role in role_by_key.items() if role == "known_correct_answered"]
    confab_fit = [rk for rk, role in role_by_key.items() if role == "confab"]
    unknown = [rk for rk, role in role_by_key.items() if role == "unknown_refused"]
    if not known_fit or not confab_fit or not unknown:
        raise RuntimeError("cannot fit directions with an empty FIT role")

    def vec(rk: str) -> np.ndarray:
        return fresh[_sanitize_key(rk)]

    h_known = np.stack([vec(rk) for rk in known_fit])
    h_unknown = np.stack([vec(rk) for rk in unknown])
    u_d = unit(h_known.mean(0) - h_unknown.mean(0))

    ak_keys = unknown + confab_fit
    h_ak = np.stack([vec(rk) for rk in ak_keys])
    y_confab = np.array([0] * len(unknown) + [1] * len(confab_fit), dtype=int)
    caution = unit(h_ak[y_confab == 0].mean(0) - h_ak[y_confab == 1].mean(0))
    scaler = StandardScaler().fit(h_ak)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0, random_state=SEED)
    clf.fit(scaler.transform(h_ak), y_confab)
    u_p = unit(clf.coef_.ravel() / scaler.scale_)

    q, _ = np.linalg.qr(np.stack([u_d, u_p], axis=1))
    c_hat = unit(caution - q @ (q.T @ caution))

    fit_keys = confab_fit + known_fit
    h_fit = np.stack([vec(rk) for rk in fit_keys])
    proj_c_fit = h_fit @ c_hat
    labels = np.array([1] * len(confab_fit) + [0] * len(known_fit), dtype=int)

    proj_c_confab = (np.stack([vec(rk) for rk in confab_fit]) @ c_hat)
    proj_c_unknown = (np.stack([vec(rk) for rk in unknown]) @ c_hat)

    return {
        "u_d": u_d, "u_p": u_p, "caution_dir": caution, "c_hat": c_hat,
        "known_fit": known_fit, "confab_fit": confab_fit, "unknown_refused": unknown,
        "stats": {
            "hidden_dim": hidden_dim, "n_known_fit": len(known_fit), "n_confab_fit": len(confab_fit), "n_unknown_refused": len(unknown),
            "mu_c": float(proj_c_fit.mean()), "sigma_c": float(proj_c_fit.std() or 1.0),
            "cos_u_d_u_p": float(np.dot(u_d, u_p)), "cos_caution_c_hat": float(np.dot(caution, c_hat)),
            "mean_raw_proj_confab": float(proj_c_confab.mean()), "mean_raw_proj_unknown_refused": float(proj_c_unknown.mean()),
        },
        "proj_c_fit": proj_c_fit, "labels": labels,
    }


def _fit_byte_identical(a: dict, b: dict) -> bool:
    for key in ("u_d", "u_p", "caution_dir", "c_hat"):
        if not np.array_equal(a[key], b[key]):
            return False
    return a["stats"] == b["stats"]


def _roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    count = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return float(count / (len(pos) * len(neg)))


def cmd_fit(args: argparse.Namespace) -> int:
    from safetensors.numpy import load_file

    config.assert_pinned_hashes()
    if not ANCHOR_MANIFEST_PATH.is_file():
        raise SystemExit(f"fit_native fit FAIL: no {ANCHOR_MANIFEST_PATH}; run `fit_native.py extract` first.")
    anchor_manifest = common.load_json(ANCHOR_MANIFEST_PATH)
    role_by_key = {rm["row_key"]: rm["role"] for rm in anchor_manifest["rows"]}
    hidden_dim = int(anchor_manifest["hidden_dim"])
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in load_file(str(ANCHOR_TENSORS_PATH)).items()}

    fit1 = _fit_all(fresh, role_by_key, hidden_dim)
    fit2 = _fit_all(fresh, role_by_key, hidden_dim)
    if not _fit_byte_identical(fit1, fit2):
        raise SystemExit("fit_native fit FAIL: reproducibility check failed -- refit is not byte-identical")
    print("[fit_native fit] reproducibility check PASS", flush=True)

    stats = fit1["stats"]

    # MINOR m2: sign assertion BEFORE pinning the negative-z sign. If this
    # fails, the fit is inverted relative to the confab-negative raw-
    # projection convention transfer/KUQ established; halt rather than
    # silently pin a flipped sign.
    sign_ok = stats["mean_raw_proj_confab"] < stats["mean_raw_proj_unknown_refused"]
    if not sign_ok:
        raise SystemExit(
            f"fit_native fit FAIL (MINOR m2 sign assertion): mean_raw_proj(confab)="
            f"{stats['mean_raw_proj_confab']} is NOT < mean_raw_proj(unknown_refused)="
            f"{stats['mean_raw_proj_unknown_refused']}. This would flip the confab-"
            f"positive orientation if pinned; halting rather than proceeding."
        )
    print(f"[fit_native fit] MINOR m2 sign assertion PASS: mean_raw_proj(confab)={stats['mean_raw_proj_confab']:.4f} < mean_raw_proj(unknown_refused)={stats['mean_raw_proj_unknown_refused']:.4f}", flush=True)

    auc_raw_neg = _roc_auc(-fit1["proj_c_fit"], fit1["labels"])  # confab-positive orientation (negative raw proj), fit-split AUROC

    reference_dose_abs = config.NATIVE_REFERENCE_DOSE_MULTIPLIER * stats["sigma_c"]

    c_hat_record = {
        "schema_version": "mechinterp-direction/v1",
        "layer": config.NATIVE_LAYER_INDEX,
        "hidden_dim": hidden_dim,
        "normalized": True,
        "vector": [float(x) for x in fit1["c_hat"]],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * hidden_dim,
        "sigma": stats["sigma_c"],
        "calibration": {"mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"]},
        "recipe": {"source": "fit_native.py (this experiment), wrapping fit_midband_directions.py's verbatim recipe", "mirrors": "qwen35-4b-midband-doubt-snap/fit_midband_directions.py:_fit_all"},
        "provenance": {
            "role": "snap_write_direction_c_hat_worldknown", "amendment": "margin-evidence-responsiveness-worldknown",
            "base_model": config.MODEL_REPO, "revision": config.MODEL_REVISION,
            "fit_population": "native_fit_split (confab 400 / known_correct_answered 240 / unknown_refused 180), disjoint from test",
            "hs_index": config.NATIVE_HS_INDEX,
            "sign_convention": "registered score = NEGATIVE raw projection (confab-positive); MINOR m2 sign assertion PASSED at fit time",
            "reference_dose_abs": reference_dose_abs,
            "reference_dose_derivation": f"fork 1: {config.NATIVE_REFERENCE_DOSE_MULTIPLIER}x native sigma_c (same 8x multiplier that set the transfer/KUQ reference dose)",
        },
    }
    NATIVE_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(config.NATIVE_C_HAT_PATH, c_hat_record)

    build_manifest = {
        "seed": SEED, "reproducibility_verified": True,
        "anchor_manifest_sha256": common.sha256_of_file(ANCHOR_MANIFEST_PATH),
        "stats": stats, "auc_confab_vs_known_fit_split_negz": auc_raw_neg,
        "sign_assertion_passed": sign_ok, "reference_dose_abs": reference_dose_abs,
        "c_hat_worldknown_sha256": common.sha256_of_file(config.NATIVE_C_HAT_PATH),
    }
    common.write_json(NATIVE_DIR / "native_direction_build_manifest.json", build_manifest)

    print(json.dumps(build_manifest, indent=2), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="GPU: hs20 anchor extraction on the native_fit_split")
    p_extract.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_extract.set_defaults(func=cmd_extract)

    p_fit = sub.add_parser("fit", help="CPU: direction fit + sign assertion + reference-dose derivation")
    p_fit.set_defaults(func=cmd_fit)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
