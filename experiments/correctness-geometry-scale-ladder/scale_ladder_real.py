#!/usr/bin/env python3
"""Real-label correctness-geometry ladder driver (correctness-geometry
scale-ladder cell), plus its G0 data-adequacy precondition check.

Pre-registered in experiments/correctness-geometry-scale-ladder/AMENDMENT.md.
TWO modes, deliberately separated for containment (never touch real labels
before sign):

  --mode g0    Loads only rows.jsonl (row_key, correct/outcome fields) for
               each scale, verifies per-class counts against the packet's
               table and the identical-pool row_key intersection, and checks
               the matched-n floor N*=377/377 is achievable. No tensors, no
               fitting. SAFE PRE-SIGN (explicitly allowed by the task).

  --mode real  Loads the per-layer post-generation activation tensors and
               fits the matched-n E1-E4 ladder on REAL correct/wrong labels.
               NOT authorized before sign. Pass --synthetic-smoke to run the
               identical code path against shape-and-count-matched SYNTHETIC
               stand-in activations instead of the real caches, for the
               pre-sign smoke / kill-resume / workers-equivalence drills --
               this proves the harness (persistence, parallelism, estimator
               wiring) without reading a single real per-row label.

`persistence: incremental` (experiment.yaml); checkpoint at
analysis/runlog/real_ladder{,_smoke}.jsonl.

=== v3 (2026-07-20): full-n E1 PRIMARY wired in, E1 split-half-averaged ===
`fit_one_draw` now fits a SEPARATE full-rank PCA-128 on each layer's FULL
(imbalanced) real population -- not just the matched-n N*=377/377
subsample -- and reports E1 there as `e1_full_n` (PRIMARY, matches
scale_ladder_planted_sim.py's run_one_rep convention); the matched-n E1
(`e1_matched_n`) remains a reported secondary (v2 ruling 21.2, unchanged).
Both E1 readings are now averaged over `lib.R_SH` independent split-half
draws (v3 fix (i)) instead of one noisy draw. This closes the gap the v2
build flagged: "E1's v2 full-n-primary regime is NOT yet wired into
scale_ladder_real.py's real-mode draw loop."
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from safetensors import safe_open
from sklearn.decomposition import PCA

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
if str(TUNER_DIR) not in sys.path:
    sys.path.insert(0, str(TUNER_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from shared.utilities.run_log import RunLog  # noqa: E402
import scale_ladder_lib as lib  # noqa: E402

MODULE_VERSION = 2
SEED_PRIMARY_DRAWS = 20260720
SEED_ROBUST_DRAWS = 20260721


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def safe_key_for(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_")


# --- G0: data-adequacy precondition (rows.jsonl only, no tensors) ----------
def g0_check() -> dict:
    problems = []
    keysets = {}
    counts = {}
    for scale in lib.SCALES:
        p = Path(lib.DATA_DIRS[scale]) / "rows.jsonl"
        rows = load_jsonl(p)
        n_c = sum(1 for r in rows if r.get("correct") is True)
        n_w = sum(1 for r in rows if r.get("correct") is False)
        counts[scale] = (n_c, n_w)
        exp_c, exp_w = lib.EXPECTED_CLASS_COUNTS[scale]
        if (n_c, n_w) != (exp_c, exp_w):
            problems.append(f"{scale}: expected correct={exp_c}/wrong={exp_w}, got {n_c}/{n_w}")
        if min(n_c, n_w) < lib.MIN_CLASS:
            problems.append(f"{scale}: below MIN_CLASS floor ({n_c}/{n_w})")
        keysets[scale] = set(r["row_key"] for r in rows)
    inter = set.intersection(*keysets.values())
    if len(inter) != 3000 or any(len(v) != 3000 for v in keysets.values()):
        problems.append(f"row_key pool mismatch: sizes={{s: len(v) for s,v in keysets.items()}} "
                         f"intersection={len(inter)}")
    matched_n_ok = all(min(c) >= lib.N_STAR for c in counts.values())
    if not matched_n_ok:
        problems.append(f"matched-n floor N*={lib.N_STAR} not achievable at every scale: {counts}")
    return {"problems": problems, "counts": counts, "pool_intersection": len(inter),
            "matched_n_achievable": matched_n_ok, "pass": len(problems) == 0}


# --- real / synthetic per-scale, per-layer activation loaders --------------
def real_layer_cache(scale: str, layers: list[int]) -> dict:
    data_dir = Path(lib.DATA_DIRS[scale])
    rows = load_jsonl(data_dir / "rows.jsonl")
    kept = [r for r in rows if r.get("correct") in (True, False)]
    n = len(kept)
    hidden = lib.HIDDEN_DIM[scale]
    arr = np.empty((len(layers), n, hidden), dtype=np.float32)
    y = np.empty(n, dtype=np.int64)
    keys = []
    for i, r in enumerate(kept):
        sk = safe_key_for(r["row_key"])
        tp = data_dir / f"{sk}__post.safetensors"
        with safe_open(str(tp), framework="np") as h:
            for li, layer in enumerate(layers):
                arr[li, i, :] = h.get_tensor(f"L{layer}")
        y[i] = 1 if r["correct"] else 0
        keys.append(r["row_key"])
    return {"arr": arr, "y": y, "keys": np.array(keys), "layers": layers}


def synthetic_layer_cache(scale: str, layers: list[int], seed: int) -> dict:
    """Shape-and-count-matched synthetic stand-in: same per-scale n_correct/
    n_wrong as EXPECTED_CLASS_COUNTS, same hidden_dim, a mild class-mean
    shift so downstream fits are non-degenerate. NEVER reads any real row,
    label, or tensor -- used only for the pre-sign smoke / kill-resume /
    workers-equivalence drills."""
    n_c, n_w = lib.EXPECTED_CLASS_COUNTS[scale]
    n = n_c + n_w
    hidden = lib.HIDDEN_DIM[scale]
    rng = np.random.default_rng(seed)
    y = np.array([1] * n_c + [0] * n_w)
    shift = rng.standard_normal(hidden) * 0.15
    arr = np.empty((len(layers), n, hidden), dtype=np.float32)
    for li, layer in enumerate(layers):
        base = rng.standard_normal((n, hidden)).astype(np.float32)
        base[y == 1] += shift
        arr[li] = base
    keys = np.array([f"synthetic::{scale}::{i}" for i in range(n)])
    return {"arr": arr, "y": y, "keys": keys, "layers": layers}


# --- per-(scale, layer-policy, draw) fit unit -------------------------------
def fit_one_draw(X_amb: np.ndarray, y: np.ndarray, draw_seed: int, compute_e3_e4: bool) -> dict:
    idx = lib.stratified_subsample_indices(y, lib.N_STAR, draw_seed)
    Xs, ys = X_amb[idx].astype(np.float64), y[idx]
    pca_seed = lib.sub_seed(draw_seed, "pca")
    pca = PCA(n_components=lib.PCA_DIM, svd_solver="randomized", random_state=pca_seed)
    Xp = pca.fit_transform(Xs)
    fit_seed = lib.sub_seed(draw_seed, "fit")

    # v3 item 7 (teammate message): wire full-n E1 PRIMARY into the real
    # driver, identically to scale_ladder_planted_sim.py's run_one_rep --
    # `X_amb` here is ALREADY the scale's full, imbalanced real population
    # for this layer (synthetic_layer_cache/real_layer_cache never
    # subsamples before calling fit_one_draw; only `idx` above draws the
    # matched-n secondary). Fit a SEPARATE full-rank PCA-128 on the full
    # population (not the matched-n subsample `Xs`) and report E1 there as
    # primary; the matched-n E1 below stays a reported secondary (v2 ruling
    # 21.2, unchanged by v3).
    pca_full_seed = lib.sub_seed(draw_seed, "pca_full")
    pca_full = PCA(n_components=lib.PCA_DIM, svd_solver="randomized", random_state=pca_full_seed)
    Xp_full = pca_full.fit_transform(X_amb.astype(np.float64))
    fit_full_seed = lib.sub_seed(draw_seed, "fit_full")

    out = {
        "explained_variance_128": float(np.sum(pca.explained_variance_ratio_)),
        # v3 fix (i): both E1 readings averaged over lib.R_SH split-half
        # draws (was a single draw pre-v3), applied identically to the
        # planted sim and here.
        "e1_full_n": lib.e1_split_half_reliability_avg(Xp_full, y, fit_full_seed),
        "e1_matched_n": lib.e1_split_half_reliability_avg(Xp, ys, fit_seed),
        "e2": lib.e2_concentration_ratio(Xp, ys, fit_seed),
    }
    if compute_e3_e4:
        out["e3_k1"] = lib.e3_random_slice_margin(Xp, ys, 1, fit_seed)
        out["e3_k8"] = lib.e3_random_slice_margin(Xp, ys, 8, fit_seed)
        out["e4"] = lib.e4_participation_ratio(Xp, ys, fit_seed)
    return out


def _draw_worker(scale, tag, layer, draw, X_amb, y, draw_seed, compute_e3_e4):
    return scale, tag, layer, draw, fit_one_draw(X_amb, y, draw_seed, compute_e3_e4)


def key_for(scale, tag, layer, draw) -> str:
    return f"{scale}|{tag}|L{layer}|{draw}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["g0", "real"], default="g0")
    ap.add_argument("--synthetic-smoke", action="store_true",
                     help="mode=real only: use shape-matched synthetic data, never real labels")
    ap.add_argument("--smoke", action="store_true", help="toy scale: fewer draws, no window/robustness")
    ap.add_argument("--out-dir", default=str(HERE / "analysis-committed"))
    ap.add_argument("--work-dir", default=str(HERE / "analysis"))
    ap.add_argument("--workers", type=int, default=lib.default_workers())
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    if args.mode == "g0":
        result = g0_check()
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["pass"] else 1

    if not args.synthetic_smoke:
        manifest_path = HERE / "experiment.yaml"
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except OSError:
            manifest = {}
        if manifest.get("status") not in ("signed", "running"):
            raise SystemExit(
                "mode=real without --synthetic-smoke touches real per-row correctness "
                "labels and is NOT authorized before bin/exp sign. This build is a "
                "pre-sign deliverable; re-run with --synthetic-smoke for the drill, "
                "or wait for the lead to lock G1 thresholds and sign the cell."
            )

    t0 = time.time()
    out_dir = Path(args.out_dir)
    work_dir = Path(args.work_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    n_workers = max(1, args.workers)
    r_draws = 4 if args.smoke else lib.R_DRAWS

    run_config = {
        "module": "scale_ladder_real", "version": MODULE_VERSION,
        "smoke": args.smoke, "synthetic_smoke": args.synthetic_smoke, "r_draws": r_draws,
        "seed_primary_draws": SEED_PRIMARY_DRAWS, "seed_robust_draws": SEED_ROBUST_DRAWS,
        "n_star": lib.N_STAR, "pca_dim": lib.PCA_DIM,
    }
    # Real and synthetic-smoke resume logs are DISJOINT files -- a real run
    # must never be able to resume from (or be contaminated by) a synthetic
    # drill's checkpoint, and vice versa (build-defect remediation,
    # 2026-07-20: see NOTEBOOK.md).
    log_base = "real_ladder_synthetic" if args.synthetic_smoke else "real_ladder"
    log_name = f"{log_base}_smoke.jsonl" if args.smoke else f"{log_base}.jsonl"
    log_path = work_dir / "runlog" / log_name
    run_log = RunLog(log_path, run_config=run_config, fresh=args.fresh)

    results: dict = {}
    for scale in lib.SCALES:
        gl = lib.gate_layers(scale)
        needed_layers = sorted(set(gl.values()) | (set() if args.smoke else set(lib.best_dial_window(scale))))
        if args.synthetic_smoke:
            cache_seed = lib.sub_seed(20260722, scale, "synthetic_cache")
            cache = synthetic_layer_cache(scale, needed_layers, cache_seed)
        else:
            cache = real_layer_cache(scale, needed_layers)
        layer_pos = {l: i for i, l in enumerate(needed_layers)}

        tasks = []
        for tag, layer in gl.items():
            for d in range(r_draws):
                draw_seed = lib.sub_seed(SEED_PRIMARY_DRAWS, scale, tag, f"L{layer}", f"draw{d}")
                tasks.append((scale, tag, layer, d, cache["arr"][layer_pos[layer]], cache["y"],
                              draw_seed, True))
        if not args.smoke:
            for layer in lib.best_dial_window(scale):
                if layer in gl.values():
                    continue
                for d in range(r_draws):
                    draw_seed = lib.sub_seed(SEED_PRIMARY_DRAWS, scale, "window", f"L{layer}", f"draw{d}")
                    tasks.append((scale, "window", layer, d, cache["arr"][layer_pos[layer]],
                                  cache["y"], draw_seed, False))
            for d in range(r_draws):
                draw_seed = lib.sub_seed(SEED_ROBUST_DRAWS, scale, "robust", f"L{gl['best_dial']}", f"draw{d}")
                tasks.append((scale, "robust", gl["best_dial"], d, cache["arr"][layer_pos[gl["best_dial"]]],
                              cache["y"], draw_seed, False))

        pending = list(run_log.iter_pending(tasks, key_fn=lambda t: key_for(t[0], t[1], t[2], t[3])))
        print(f"[real-ladder] scale={scale} needed_layers={needed_layers} "
              f"{len(tasks)} tasks, {len(pending)} pending", flush=True)

        # Batch per (tag, layer): fine-grained checkpointing, independent tasks.
        by_batch: dict[tuple, list] = {}
        for t in pending:
            by_batch.setdefault((t[1], t[2]), []).append(t)
        for (tag, layer), batch_tasks in by_batch.items():
            batch_out = lib.parallel_map(_draw_worker, batch_tasks, n_workers)
            for s, tg, ly, d, payload in batch_out:
                run_log.record(key_for(s, tg, ly, d), payload)
            print(f"[real-ladder] scale={scale} tag={tag} L{layer} batch done "
                  f"({len(batch_tasks)} draws)", flush=True)

    all_records = {k: v for k, v in run_log._records.items()}
    wall_s = time.time() - t0
    summary = {"config": run_config, "wall_clock_s": wall_s, "n_records": len(all_records)}
    run_log.finalize(summary)
    run_log.close()

    out = {"config": run_config, "wall_clock_s": wall_s, "records": all_records}
    out_name = "real_ladder_synthetic_smoke.json" if args.synthetic_smoke else "real_ladder.json"
    (out_dir / out_name).write_text(json.dumps(out, indent=2), encoding="utf-8")
    marker = " (SYNTHETIC-SMOKE -- no real labels touched)" if args.synthetic_smoke else ""
    print(f"[real-ladder] done in {wall_s:.1f}s, {len(all_records)} records{marker}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
