#!/usr/bin/env python3
"""Anisotropy-correction reanalysis of gemma-4-e4b-family-atlas eff_dim_frac.

READ-ONLY over existing captures. Reuses the pinned participation_ratio /
eff_dim_frac functions from profile_and_read_family_atlas_panel.py (imported
directly, not reimplemented) for the baseline reproduce check, then computes
anisotropy descriptives and estimator variants on the SAME fit-row matrices.

No writes outside this scratch dir. No model loading, no GPU.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

WORKTREE_CELL = Path(
    "/home/profsynapse/code/ehr-worktrees/gemma-atlas/experiments/gemma-4-e4b-family-atlas"
)
CANON_CELL = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/gemma-4-e4b-family-atlas"
)
ANALYSIS_DIR = WORKTREE_CELL / "analysis" / "gemma4_e4b_it"
COMMITTED_DIR = WORKTREE_CELL / "analysis-committed" / "gemma4_e4b_it"
CAPTURE_DIR = ANALYSIS_DIR / "atlas_capture"
OUT_DIR = Path(__file__).resolve().parent
SEED = 20260707

# --- import the pinned estimator module directly (byte-identical to canon) ---
spec = importlib.util.spec_from_file_location(
    "panel", str(WORKTREE_CELL / "profile_and_read_family_atlas_panel.py")
)
panel = importlib.util.module_from_spec(spec)
sys.modules["panel"] = panel
spec.loader.exec_module(panel)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    split_manifest = json.loads((COMMITTED_DIR / "split_manifest.json").read_text())
    rowmeta = split_manifest["rows"]
    capture_manifest = json.loads((COMMITTED_DIR / "capture_manifest.json").read_text())
    n_hidden_states = capture_manifest["n_hidden_states"]
    hidden_dim = capture_manifest["hidden_size"]

    fit_rows = sorted(
        r["row_key"] for r in rowmeta if r["split"] in ("fit", "fit_only")
    )
    print(f"[load] n_fit_rows={len(fit_rows)} n_hidden_states={n_hidden_states} hidden_dim={hidden_dim}", flush=True)

    # id -> file, from capture.jsonl (avoid loading captures for non-fit rows)
    index = load_jsonl(CAPTURE_DIR / "capture.jsonl")
    id_to_file = {rec["id"]: rec["file"] for rec in index}
    missing = [k for k in fit_rows if k not in id_to_file]
    if missing:
        print(f"[FLAG] {len(missing)} fit rows missing from capture.jsonl, e.g. {missing[:5]}", flush=True)
    fit_rows = [k for k in fit_rows if k in id_to_file]

    # Load full (n_fit, n_hidden_states, hidden_dim) float64 tensor.
    n_fit = len(fit_rows)
    cache_path = OUT_DIR / "fit_matrix_full.npy"
    if cache_path.exists():
        full = np.load(cache_path)
        print(f"[load] loaded cached full matrix from {cache_path} shape={full.shape}", flush=True)
        assert full.shape == (n_fit, n_hidden_states, hidden_dim)
    else:
        from safetensors.numpy import load_file

        full = np.empty((n_fit, n_hidden_states, hidden_dim), dtype=np.float64)
        prefix = "anchor__L"
        layer_seen_counts = np.zeros(n_hidden_states, dtype=np.int64)
        for i, key in enumerate(fit_rows):
            tensors = load_file(str(CAPTURE_DIR / id_to_file[key]))
            for tkey, vec in tensors.items():
                if tkey.startswith(prefix):
                    layer = int(tkey[len(prefix):])
                    full[i, layer, :] = vec.astype(np.float64)
                    layer_seen_counts[layer] += 1
            if (i + 1) % 300 == 0:
                print(f"[load] {i+1}/{n_fit} rows loaded", flush=True)

        bad_layers = [l for l in range(n_hidden_states) if layer_seen_counts[l] != n_fit]
        if bad_layers:
            print(f"[FLAG] layers with incomplete coverage: {bad_layers}", flush=True)
        else:
            print(f"[load] all {n_hidden_states} layers fully covered across {n_fit} fit rows", flush=True)

        np.save(cache_path, full)  # cache for reruns
        print(f"[load] cached full matrix to {cache_path} shape={full.shape}", flush=True)

    # ---------------------------------------------------------------
    # Step 1: reproduce baseline eff_dim_frac against atlas_summary.json
    # ---------------------------------------------------------------
    baseline = json.loads((COMMITTED_DIR / "atlas_summary.json").read_text())
    reproduced = {}
    max_abs_dev = 0.0
    dev_by_layer = {}
    for layer in range(n_hidden_states):
        mat = full[:, layer, :]
        val = panel.eff_dim_frac(mat)
        reproduced[layer] = val
        committed_val = baseline["per_layer"][str(layer)]["profile"]["eff_dim_frac"]
        dev = abs(val - committed_val)
        dev_by_layer[layer] = dev
        max_abs_dev = max(max_abs_dev, dev)

    print(f"[reproduce] max abs deviation vs atlas_summary.json across {n_hidden_states} layers: {max_abs_dev:.3e}", flush=True)
    reproduce_report = {
        "max_abs_dev": max_abs_dev,
        "dev_by_layer": dev_by_layer,
        "reproduced_eff_dim_frac": reproduced,
        "n_fit_rows_used": n_fit,
        "n_fit_rows_committed": baseline["per_layer"]["0"]["profile"]["n_fit_rows"],
    }
    (OUT_DIR / "reproduce_check.json").write_text(json.dumps(reproduce_report, indent=2, default=float))

    if max_abs_dev > 1e-6:
        print(f"[STOP] reproduce check FAILED (max_abs_dev={max_abs_dev:.3e} > 1e-6). Not proceeding to variants.", flush=True)
        return

    print("[reproduce] PASSED. Proceeding to anisotropy descriptives + variants.", flush=True)

    # ---------------------------------------------------------------
    # Step 2: per-layer anisotropy descriptives
    # ---------------------------------------------------------------
    def centered_gram_eigvals(mat: np.ndarray) -> np.ndarray:
        x = mat.astype(np.float64)
        x = x - x.mean(axis=0, keepdims=True)
        n = x.shape[0]
        gram = (x @ x.T) / max(n - 1, 1)
        eigvals = np.linalg.eigvalsh(gram)
        return np.clip(eigvals, 0.0, None)

    aniso = {}
    eigvals_by_layer = {}
    for layer in range(n_hidden_states):
        mat = full[:, layer, :]
        eigvals = centered_gram_eigvals(mat)  # ascending
        eigvals_by_layer[layer] = eigvals
        sorted_desc = eigvals[::-1]
        total = sorted_desc.sum()
        top1_share = float(sorted_desc[0] / total) if total > 0 else float("nan")
        top8_share = float(sorted_desc[:8].sum() / total) if total > 0 else float("nan")
        pr_raw = panel.participation_ratio(mat)  # unnormalized PR

        # rogue-dimension check: per-dimension mean activation z-score
        dim_means = mat.mean(axis=0)
        mu, sigma = dim_means.mean(), dim_means.std()
        z = (dim_means - mu) / sigma if sigma > 0 else np.zeros_like(dim_means)
        max_abs_z = float(np.max(np.abs(z)))

        aniso[layer] = {
            "top1_eigval_share": top1_share,
            "top8_eigval_share": top8_share,
            "participation_ratio_raw": float(pr_raw),
            "max_abs_mean_activation_zscore": max_abs_z,
        }
    (OUT_DIR / "anisotropy_descriptives.json").write_text(json.dumps(aniso, indent=2))
    print(f"[aniso] wrote {OUT_DIR / 'anisotropy_descriptives.json'}", flush=True)

    # ---------------------------------------------------------------
    # Step 3: variants
    # ---------------------------------------------------------------
    def pr_from_eigvals(eigvals: np.ndarray) -> float:
        eigvals = np.clip(eigvals, 0.0, None)
        s1 = eigvals.sum()
        s2 = (eigvals ** 2).sum()
        if s2 <= 1e-30:
            return 1.0
        return float((s1 * s1) / s2)

    def eff_dim_frac_from_eigvals(eigvals: np.ndarray, n: int) -> float:
        return pr_from_eigvals(eigvals) / float(n)

    def variant_whitened(mat: np.ndarray) -> float:
        x = mat.astype(np.float64)
        x = x - x.mean(axis=0, keepdims=True)
        std = x.std(axis=0, ddof=1)
        std_safe = np.where(std > 1e-12, std, 1.0)
        x_white = x / std_safe
        return panel.eff_dim_frac(x_white)

    def variant_drop_top_k(eigvals_asc: np.ndarray, n: int, k: int) -> float:
        eigvals_desc = np.sort(eigvals_asc)[::-1].copy()
        eigvals_desc[:k] = 0.0
        return eff_dim_frac_from_eigvals(eigvals_desc, n)

    def variant_winsorized(mat: np.ndarray, pct: float = 0.5) -> float:
        lo = np.percentile(mat, pct, axis=0)
        hi = np.percentile(mat, 100 - pct, axis=0)
        clipped = np.clip(mat, lo, hi)
        return panel.eff_dim_frac(clipped)

    def variant_spectral_entropy(eigvals_asc: np.ndarray, n: int) -> tuple[float, float]:
        eigvals = np.clip(eigvals_asc, 0.0, None)
        total = eigvals.sum()
        # Degenerate-spectrum fallback, matching the pinned participation_ratio's
        # own s2<=1e-30 -> PR=1.0 convention (rank-collapsed layer, e.g. an
        # embedding layer whose fit-row anchor vectors are float32-identical
        # after centering): effective rank -> 1 rather than NaN.
        if total <= 1e-30:
            return 1.0, 1.0 / float(n)
        p = eigvals / total
        p_nz = p[p > 0]
        H = -float(np.sum(p_nz * np.log(p_nz)))
        eff_rank = float(np.exp(H))
        return eff_rank, eff_rank / float(n)

    variants = {
        "baseline": {},
        "whitened_correlation": {},
        "drop_top_k1": {},
        "drop_top_k2": {},
        "drop_top_k4": {},
        "drop_top_k8": {},
        "winsorized_0.5pct": {},
        "spectral_entropy_effrank": {},
        "spectral_entropy_effrank_norm": {},
    }

    for layer in range(n_hidden_states):
        mat = full[:, layer, :]
        n = mat.shape[0]
        eigvals_asc = eigvals_by_layer[layer]

        variants["baseline"][layer] = reproduced[layer]
        variants["whitened_correlation"][layer] = variant_whitened(mat)
        for k in (1, 2, 4, 8):
            variants[f"drop_top_k{k}"][layer] = variant_drop_top_k(eigvals_asc, n, k)
        variants["winsorized_0.5pct"][layer] = variant_winsorized(mat)
        eff_rank, eff_rank_norm = variant_spectral_entropy(eigvals_asc, n)
        variants["spectral_entropy_effrank"][layer] = eff_rank
        variants["spectral_entropy_effrank_norm"][layer] = eff_rank_norm

    def classify_depth(layer: int, n_layers: int) -> tuple[float, str]:
        depth = layer / (n_layers - 1)
        if depth <= 0.20:
            return depth, "early-exterior"
        if depth >= 0.85:
            return depth, "late-exterior"
        return depth, "interior"

    summary_rows = []
    for name, profile in variants.items():
        layers_sorted = sorted(profile.keys())
        vals = [profile[l] for l in layers_sorted]
        peak_layer = max(layers_sorted, key=lambda l: profile[l])
        peak_val = profile[peak_layer]
        depth, cls = classify_depth(peak_layer, n_hidden_states)
        summary_rows.append({
            "variant": name,
            "peak_layer": peak_layer,
            "peak_depth_frac": depth,
            "peak_value": peak_val,
            "classification": cls,
        })

    (OUT_DIR / "variant_profiles.json").write_text(json.dumps(variants, indent=2, default=float))
    (OUT_DIR / "variant_summary.json").write_text(json.dumps(summary_rows, indent=2, default=float))
    print(f"[variants] wrote {OUT_DIR / 'variant_profiles.json'} and variant_summary.json", flush=True)
    for row in summary_rows:
        print(f"  {row['variant']:28s} peak_layer={row['peak_layer']:3d} depth={row['peak_depth_frac']:.4f} "
              f"class={row['classification']:14s} val={row['peak_value']:.6g}", flush=True)

    # ---------------------------------------------------------------
    # Step 5: sanity guard - drop_top_k8 on random 50% row subsample
    # ---------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    sub_idx = rng.choice(n_fit, size=n_fit // 2, replace=False)
    sub_idx.sort()
    sub_full = full[sub_idx, :, :]

    subsample_profile = {}
    for layer in range(n_hidden_states):
        mat = sub_full[:, layer, :]
        n = mat.shape[0]
        eigvals_asc = centered_gram_eigvals(mat)
        subsample_profile[layer] = variant_drop_top_k(eigvals_asc, n, 8)

    layers_sorted = sorted(subsample_profile.keys())
    peak_layer_sub = max(layers_sorted, key=lambda l: subsample_profile[l])
    depth_sub, cls_sub = classify_depth(peak_layer_sub, n_hidden_states)
    guard_report = {
        "n_subsample": int(len(sub_idx)),
        "subsample_seed": SEED,
        "profile": subsample_profile,
        "peak_layer": peak_layer_sub,
        "peak_depth_frac": depth_sub,
        "classification": cls_sub,
        "full_sample_drop_top_k8_peak_layer": summary_rows[[r["variant"] for r in summary_rows].index("drop_top_k8")]["peak_layer"],
    }
    (OUT_DIR / "guard_subsample_k8.json").write_text(json.dumps(guard_report, indent=2, default=float))
    print(f"[guard] 50% subsample (n={len(sub_idx)}) drop_top_k8 peak_layer={peak_layer_sub} "
          f"depth={depth_sub:.4f} class={cls_sub} "
          f"(full-sample drop_top_k8 peak_layer={guard_report['full_sample_drop_top_k8_peak_layer']})", flush=True)

    print("[done]", flush=True)


if __name__ == "__main__":
    main()
