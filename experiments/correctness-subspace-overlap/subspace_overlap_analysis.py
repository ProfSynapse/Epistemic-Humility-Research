#!/usr/bin/env python3
"""Correctness discriminative-subspace overlap across training checkpoints (SO).

CPU-only Tier-2 probe-fit successor to correctness-direction-rotation (CD).
Pre-registered in experiments/correctness-subspace-overlap/AMENDMENT.md
(draft; not yet signed at authoring time). Method reference
experiments/correctness-direction-rotation/cd_rotation_analysis.py: this module
reuses `load_jsonl`, `safe_key_for`, `build_stage_cache`, `load_layer`,
`cv_auroc`, `full_direction`, `cos`, `LAYERS`, `PCA_DIM`, `N_FOLDS`, `MIN_CLASS`
verbatim by import (aliased `cd`), and adds the subspace machinery pinned in
cell.yaml / gates.yaml:

  - 4.1 balanced-bootstrap logistic-normal span subspace estimator (per stage
    per layer, own PCA-128), plus a deflation secondary estimator.
  - 4.2 Grassmann projection overlap metric (mean squared cosine of principal
    angles) and the full principal-angle spectrum.
  - 4.3 k grid {1,2,4,8,16,32}.
  - 4.4 disjoint half-split reliability at m in {n/8, n/4, n/2}, pinned 1/m
    OLS extrapolation to n with an R^2 < 0.90 fallback to the m=n/2 median.
  - 4.5 label-permutation null (primary, P=100) and isotropic random-subspace
    null (secondary, N=200), plus raw-span (label-agnostic PCA span) overlap.
  - 4.6 floor/ceiling recovery curve (S-subspace-restricted T probe) at every
    k, with the k=1 ~ 0.679 sanity check.
  - 4.7 per-stage symmetric PCA basis (primary) with retained-variance
    reporting, plus a pooled shared-basis secondary robustness check.
  - 4.8 matched-population S->T and matched-class-balance timeline confound
    bounds.
  - 5.4 two-seed headline (k=8, S->T) robustness rerun.

Outputs `subspace_overlap_timeline.{json,md}` to --out-dir (analysis-committed
shape: per-layer tables plus an L19-L24 summary, no row text, no row keys
beyond counts). All intermediate arrays (bootstrap bases, null draws, caches)
stay under --work-dir (gitignored `analysis/`), never under --out-dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

# --- reuse CD's primitives verbatim (import, not reimplement) ---------------
_CD_DIR = Path(__file__).resolve().parents[1] / "correctness-direction-rotation"
sys.path.insert(0, str(_CD_DIR))
import cd_rotation_analysis as cd  # noqa: E402  (load_jsonl, safe_key_for,
# build_stage_cache, load_layer, cv_auroc, full_direction, cos, LAYERS,
# PCA_DIM, N_FOLDS, MIN_CLASS all reused from here)

# --- pinned constants (cell.yaml / gates.yaml / design packet 4.1-4.8) ------
SEED_PCA_FOLD = 20260719          # CD comparability: PCA random_state, CV folds
SEED_PRIMARY = 20260720           # bootstrap / permutation / isotropic-null RNG
SEED_ROBUST = 20260721            # 2-seed headline rerun
PCA_DIM = cd.PCA_DIM              # 128
N_FOLDS = cd.N_FOLDS              # 5
MIN_CLASS = cd.MIN_CLASS          # 30
B_BOOT = 200                      # balanced bootstrap resamples, core estimator
B_REL = 30                        # balanced bootstrap resamples, reliability
R_PARTITIONS = 15                 # disjoint half-split repeats
M_FRACTIONS = (1 / 8, 1 / 4, 1 / 2)
EXTRAP_R2_FALLBACK = 0.90
P_PERM = 100                      # label-permutation null draws
B_NULL = 40                       # balanced bootstrap resamples inside null refit
N_ISO = 200                       # isotropic random-subspace draws
K_GRID = (1, 2, 4, 8, 16, 32)
K_MAX = max(K_GRID)
GATE_LAYERS = ["L19", "L20", "L21", "L22", "L23", "L24"]
RECOVERY_LAYER = "L20"
TIMELINE_STAGES = ["raw", "cleansft", "grpov2", "partrue"]
TIMELINE_PAIRS = [("raw", "cleansft"), ("cleansft", "grpov2"), ("grpov2", "partrue")]
BRACKET_PAIR = ("s", "grpov2")     # S -> T
ALL_STAGES = ["raw", "cleansft", "grpov2", "partrue", "s"]
K_GATE = 8
MARGIN_015 = 0.15
RELIABILITY_070 = 0.70
RECOVERY_075 = 0.75
DOCUMENTED_COLD_TRANSFER = 0.679   # correctness-readout-deployment-port, L20


# --- deterministic, order-independent sub-seeding ---------------------------
def sub_seed(base_seed: int, *parts: str) -> int:
    """Derive a deterministic child seed from base_seed + labeled parts.

    Keyed by explicit strings rather than call order or dict iteration, so
    output is identical regardless of loop/collection ordering.
    """
    h = hashlib.sha256((str(base_seed) + "|" + "|".join(parts)).encode()).hexdigest()
    return int(h[:16], 16) % (2**31 - 1)


def rng_for(base_seed: int, *parts: str) -> np.random.Generator:
    return np.random.default_rng(sub_seed(base_seed, *parts))


# --- run configuration (full vs smoke) --------------------------------------
@dataclass
class RunConfig:
    smoke: bool
    layers: list
    gate_layers: list
    k_grid: tuple
    b_boot: int
    b_rel: int
    b_null: int
    r_partitions: int
    p_perm: int
    n_iso: int
    recovery_layer: str

    @property
    def k_max(self) -> int:
        return max(self.k_grid)


def make_config(smoke: bool) -> RunConfig:
    if smoke:
        # Toy scale per assignment: 2 layers, B=20, R=3, P=5, k in {1,4}.
        layers = [RECOVERY_LAYER, "L21"]
        return RunConfig(
            smoke=True, layers=layers, gate_layers=layers, k_grid=(1, 4),
            b_boot=20, b_rel=10, b_null=10, r_partitions=3, p_perm=5,
            n_iso=10, recovery_layer=RECOVERY_LAYER,
        )
    return RunConfig(
        smoke=False, layers=list(cd.LAYERS), gate_layers=list(GATE_LAYERS),
        k_grid=K_GRID, b_boot=B_BOOT, b_rel=B_REL, b_null=B_NULL,
        r_partitions=R_PARTITIONS, p_perm=P_PERM, n_iso=N_ISO,
        recovery_layer=RECOVERY_LAYER,
    )


# --- 4.1 balanced bootstrap + subspace estimator ----------------------------
def balanced_bootstrap_indices(y: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Stratified balanced bootstrap: within each class, each original row
    index appears exactly n_boot times total across the n_boot resamples
    (Davison & Hinkley balanced bootstrap), reducing Monte-Carlo variance of
    the estimator without a bias cost (design packet 4.1)."""
    n = len(y)
    classes = np.unique(y)
    per_class_pool = {}
    for c in classes:
        idx_c = np.where(y == c)[0]
        nc = len(idx_c)
        pool = np.tile(idx_c, n_boot)
        rng.shuffle(pool)
        per_class_pool[c] = pool.reshape(n_boot, nc)
    resamples = np.concatenate([per_class_pool[c] for c in classes], axis=1)
    assert resamples.shape == (n_boot, n)
    return resamples


def full_direction_pca_space(Xp: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Unit-normed separating normal IN PCA-space coordinates. Reuses CD's
    full_direction verbatim with components=I so the ambient-mapping matmul
    is a no-op identity map (isometry), giving exactly the PCA-space normal
    packet 4.1 wants for the B x pca_dim matrix (no reimplementation of the
    logistic-fit/scale/normalize machinery)."""
    return cd.full_direction(Xp, y, np.eye(Xp.shape[1]))


def bootstrap_normals(Xp: np.ndarray, y: np.ndarray, n_boot: int,
                       rng: np.random.Generator) -> np.ndarray:
    idx_resamples = balanced_bootstrap_indices(y, n_boot, rng)
    normals = np.empty((n_boot, Xp.shape[1]), dtype=np.float64)
    for b in range(n_boot):
        idx = idx_resamples[b]
        normals[b] = full_direction_pca_space(Xp[idx], y[idx])
    return normals


def subspace_from_normals(normals_pca: np.ndarray, k: int, components: np.ndarray) -> np.ndarray:
    """Top-k right singular vectors of the B x pca_dim normals matrix, mapped
    to the ambient 2560-dim residual space through the PCA components and
    QR-orthonormalized (packet 4.1)."""
    _, _, vt = np.linalg.svd(normals_pca, full_matrices=False)
    vk = vt[:k].T                       # pca_dim x k
    u_ambient = components.T @ vk       # (2560 x pca_dim) @ (pca_dim x k)
    q, _ = np.linalg.qr(u_ambient)
    return q[:, :k]


def estimate_stage_subspace(Xp: np.ndarray, y: np.ndarray, components: np.ndarray,
                             n_boot: int, rng: np.random.Generator, k_max: int) -> np.ndarray:
    """Returns the ambient 2560 x k_max orthonormal basis; callers slice
    [:, :k] for any k <= k_max (nested by construction, k grid is nearly free)."""
    normals = bootstrap_normals(Xp, y, n_boot, rng)
    return subspace_from_normals(normals, k_max, components)


def deflation_subspace(Xp: np.ndarray, y: np.ndarray, k: int,
                        components: np.ndarray) -> np.ndarray:
    """Secondary robustness estimator (packet 4.1): fit direction 1 on the
    full sample, project it out of the PCA-space features, refit on the
    residual, repeat k times. Deterministic given Xp, y (no RNG)."""
    directions = []
    x_work = Xp.copy()
    for _ in range(k):
        d = full_direction_pca_space(x_work, y)
        directions.append(d)
        proj = x_work @ d
        x_work = x_work - np.outer(proj, d)
    v = np.array(directions).T          # pca_dim x k
    q_pca, _ = np.linalg.qr(v)
    u_ambient = components.T @ q_pca[:, :k]
    q, _ = np.linalg.qr(u_ambient)
    return q[:, :k]


# --- 4.2 Grassmann projection overlap metric --------------------------------
def grassmann_overlap(u: np.ndarray, v: np.ndarray, k: int | None = None):
    """Mean squared cosine of principal angles between two orthonormal
    ambient bases (Krzanowski 1979); returns (scalar, full cosine spectrum)."""
    if k is None:
        k = min(u.shape[1], v.shape[1])
    uk, vk = u[:, :k], v[:, :k]
    s = np.linalg.svd(uk.T @ vk, compute_uv=False)
    s = np.clip(s, -1.0, 1.0)
    overlap = float(np.mean(s ** 2))
    return overlap, s.tolist()


# --- isotropic random-subspace draw (secondary null + recovery floor) -----
def random_ambient_subspace(components: np.ndarray, k: int,
                             rng: np.random.Generator) -> np.ndarray:
    pca_dim = components.shape[0]
    g = rng.standard_normal((pca_dim, k))
    q_pca, _ = np.linalg.qr(g)
    u_ambient = components.T @ q_pca[:, :k]
    q, _ = np.linalg.qr(u_ambient)
    return q[:, :k]


# --- 4.4 disjoint half-split reliability ------------------------------------
def two_disjoint_stratified_samples(y: np.ndarray, m: int, seed: int):
    """Two disjoint, class-stratified index sets of size m each, drawn
    directly per class rather than via sklearn's train_test_split. Built
    manually because the leftover discard (n - 2m) can be 0 or 1 row at the
    m=n/2 grid point (or when n is odd), and sklearn's stratified splitter
    rejects a test/remainder partition smaller than the number of classes;
    a manual per-class slice has no such lower bound."""
    rng = np.random.default_rng(seed)
    classes, counts = np.unique(y, return_counts=True)
    props = counts / len(y)
    m_per_class = {c: int(round(m * p)) for c, p in zip(classes, props)}
    diff = m - sum(m_per_class.values())
    if diff:
        largest_c = classes[np.argmax(counts)]
        m_per_class[largest_c] += diff
    pos_a, pos_b = [], []
    for c in classes:
        idx_c = rng.permutation(np.where(y == c)[0])
        k = m_per_class[c]
        if 2 * k > len(idx_c):
            raise ValueError(f"class {c} has only {len(idx_c)} rows, cannot draw "
                              f"two disjoint sets of {k} (m={m})")
        pos_a.append(idx_c[:k])
        pos_b.append(idx_c[k:2 * k])
    return np.concatenate(pos_a), np.concatenate(pos_b)


def disjoint_reliability(X_amb: np.ndarray, y: np.ndarray, m: int, cfg: RunConfig,
                          base_seed: int, tag: str, k_grid) -> dict:
    """Median disjoint-pair overlap at fit-size m, per k (packet 4.4). Each
    half gets its OWN PCA-128 fit (no shared basis leakage across the
    'independent' halves; see basis-hygiene reasoning in the report)."""
    overlaps_by_k = {k: [] for k in k_grid}
    for r in range(cfg.r_partitions):
        split_seed = sub_seed(base_seed, tag, f"m{m}", f"r{r}", "split")
        idx_a, idx_b = two_disjoint_stratified_samples(y, m, split_seed)
        rng_a = rng_for(base_seed, tag, f"m{m}", f"r{r}", "boot_a")
        rng_b = rng_for(base_seed, tag, f"m{m}", f"r{r}", "boot_b")
        pca_a = PCA(n_components=PCA_DIM, svd_solver="randomized",
                    random_state=SEED_PCA_FOLD).fit(X_amb[idx_a])
        pca_b = PCA(n_components=PCA_DIM, svd_solver="randomized",
                    random_state=SEED_PCA_FOLD).fit(X_amb[idx_b])
        xa_p, xb_p = pca_a.transform(X_amb[idx_a]), pca_b.transform(X_amb[idx_b])
        u_a = estimate_stage_subspace(xa_p, y[idx_a], pca_a.components_, cfg.b_rel, rng_a, max(k_grid))
        u_b = estimate_stage_subspace(xb_p, y[idx_b], pca_b.components_, cfg.b_rel, rng_b, max(k_grid))
        for k in k_grid:
            ov, _ = grassmann_overlap(u_a, u_b, k)
            overlaps_by_k[k].append(ov)
    return {k: float(np.median(v)) for k, v in overlaps_by_k.items()}


def extrapolate_reliability(m_values: list, overlap_values: list, n: int) -> dict:
    """Pinned 1/m OLS extrapolation to full n (packet 4.4); falls back to the
    m=n/2 conservative median if the fit R^2 < EXTRAP_R2_FALLBACK."""
    x = 1.0 / np.array(m_values, dtype=float)
    y_arr = 1.0 - np.array(overlap_values, dtype=float)
    design = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(design, y_arr, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    pred = design @ coef
    ss_res = float(np.sum((y_arr - pred) ** 2))
    ss_tot = float(np.sum((y_arr - y_arr.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    extrapolated = 1.0 - (a + b / n)
    max_m_idx = int(np.argmax(m_values))
    m_half_median = float(overlap_values[max_m_idx])
    used_fallback = r2 < EXTRAP_R2_FALLBACK
    reliability = m_half_median if used_fallback else extrapolated
    return {
        "a": a, "b": b, "r2": r2, "extrapolated": float(extrapolated),
        "m_half_median": m_half_median, "used_fallback": bool(used_fallback),
        "reliability": float(np.clip(reliability, 0.0, 1.0)),
    }


# --- 4.5 label-permutation null (primary) + isotropic null (secondary) -----
def permuted_subspace(Xp: np.ndarray, y: np.ndarray, components: np.ndarray,
                       n_boot: int, k_max: int,
                       perm_rng: np.random.Generator, boot_rng: np.random.Generator) -> np.ndarray:
    """Shuffle labels (stratified count preserved by construction of a
    permutation), refit the entire bootstrap-SVD subspace estimator on the
    shuffled labels. Activations/PCA are label-agnostic and unchanged."""
    y_perm = perm_rng.permutation(y)
    return estimate_stage_subspace(Xp, y_perm, components, n_boot, boot_rng, k_max)


# --- 4.6 recovery curve (floor / ceiling) -----------------------------------
def recovery_auroc(x_amb_target: np.ndarray, y_target: np.ndarray, subspace: np.ndarray) -> float:
    proj = x_amb_target @ subspace
    return cd.cv_auroc(proj, y_target)


# --- data plumbing -----------------------------------------------------------
def load_all_caches(cache_dir: Path, work_dir: Path) -> dict:
    """SO-G0: load the five prebuilt CD caches. Never regenerate; if a cache
    is missing, fall back to cd.build_stage_cache from the tensor dirs listed
    in cell.yaml (never re-extract)."""
    stage_dirs = {
        "raw": Path("/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/gen_raw"),
        "cleansft": Path("/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/gen_cleansft"),
        "partrue": Path("/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/gen_partrue"),
        "grpov2": Path("archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2"),
        "s": Path("archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2"),
    }
    caches = {}
    for stage, tdir in stage_dirs.items():
        cache_path = cache_dir / f"cache_{stage}.npz"
        if cache_path.exists():
            data = np.load(cache_path, allow_pickle=True)
            caches[stage] = {"arr": data["arr"], "y": data["y"], "keys": data["keys"]}
        else:
            work_dir.mkdir(parents=True, exist_ok=True)
            caches[stage] = cd.build_stage_cache(tdir, work_dir / f"cache_{stage}.npz")
    return caches


EXPECTED_COUNTS = {
    "raw": (500, 1323), "cleansft": (750, 500), "grpov2": (988, 500),
    "partrue": (500, 717), "s": (500, 1336),
}


def verify_so_g0(caches: dict) -> list:
    """SO-G0 pre-outcome stop: cache counts must match the CD committed table
    before any fit. Abort loudly on mismatch."""
    problems = []
    for stage, (exp_c, exp_w) in EXPECTED_COUNTS.items():
        y = caches[stage]["y"]
        n_c, n_w = int((y == 1).sum()), int((y == 0).sum())
        if (n_c, n_w) != (exp_c, exp_w):
            problems.append(f"{stage}: expected correct={exp_c}/wrong={exp_w}, got {n_c}/{n_w}")
        if min(n_c, n_w) < MIN_CLASS:
            problems.append(f"{stage}: below MIN_CLASS floor ({n_c}/{n_w})")
    return problems


def restrict_to_keys(cache: dict, keys_subset: set) -> tuple:
    mask = np.array([k in keys_subset for k in cache["keys"]])
    return mask


# --- per-stage-layer fit bundle ---------------------------------------------
@dataclass
class LayerFit:
    pca: PCA
    Xp: np.ndarray
    y: np.ndarray
    n_correct: int
    n_wrong: int
    underpowered: bool
    auroc_pca: float | None
    subspace: np.ndarray | None       # ambient 2560 x k_max, None if underpowered


def fit_stage_layer(X_amb: np.ndarray, y: np.ndarray, cfg: RunConfig, stage: str, layer: str) -> LayerFit:
    n_c, n_w = int((y == 1).sum()), int((y == 0).sum())
    underpowered = min(n_c, n_w) < MIN_CLASS
    pca = PCA(n_components=PCA_DIM, svd_solver="randomized", random_state=SEED_PCA_FOLD).fit(X_amb)
    Xp = pca.transform(X_amb)
    if underpowered:
        return LayerFit(pca, Xp, y, n_c, n_w, True, None, None)
    auroc = cd.cv_auroc(Xp, y)
    rng = rng_for(SEED_PRIMARY, stage, layer, "core_bootstrap")
    subspace = estimate_stage_subspace(Xp, y, pca.components_, cfg.b_boot, rng, cfg.k_max)
    return LayerFit(pca, Xp, y, n_c, n_w, False, float(auroc), subspace)


# --- markdown rendering helpers ---------------------------------------------
def fmt(v, nd=4):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        if not np.isfinite(v):
            return "nan"
        return f"{v:.{nd}f}"
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default="/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/cache")
    ap.add_argument("--out-dir", default=str(Path(__file__).parent / "analysis-committed"))
    ap.add_argument("--work-dir", default=str(Path(__file__).parent / "analysis"))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    cfg = make_config(args.smoke)
    out_dir = Path(args.out_dir)
    work_dir = Path(args.work_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)

    print(f"[so-analysis] smoke={cfg.smoke} layers={cfg.layers} k_grid={cfg.k_grid} "
          f"b_boot={cfg.b_boot} r_partitions={cfg.r_partitions} p_perm={cfg.p_perm} "
          f"n_iso={cfg.n_iso}", flush=True)

    # --- SO-G0: load + verify caches (pre-outcome stop) ---------------------
    caches = load_all_caches(cache_dir, work_dir)
    problems = verify_so_g0(caches)
    if problems and not cfg.smoke:
        for p in problems:
            print(f"[so-analysis] SO-G0 FAILED: {p}", flush=True)
        raise SystemExit("SO-G0 data-adequacy gate failed; aborting before any fit. "
                          "See printed mismatches above.")
    if problems and cfg.smoke:
        print(f"[so-analysis] SO-G0 note (smoke mode continues): {problems}", flush=True)
    else:
        print("[so-analysis] SO-G0 passed: all five caches match the CD committed table.", flush=True)

    results = {
        "config": {
            "smoke": cfg.smoke, "seed_pca_fold": SEED_PCA_FOLD, "seed_primary": SEED_PRIMARY,
            "seed_robust": SEED_ROBUST, "pca_dim": PCA_DIM, "n_folds": N_FOLDS,
            "min_class": MIN_CLASS, "b_boot": cfg.b_boot, "b_rel": cfg.b_rel,
            "b_null": cfg.b_null, "r_partitions": cfg.r_partitions, "p_perm": cfg.p_perm,
            "n_iso": cfg.n_iso, "k_grid": list(cfg.k_grid), "gate_layers": cfg.gate_layers,
            "recovery_layer": cfg.recovery_layer, "layers_run": cfg.layers,
            "so_g0_problems": problems, "metric": "grassmann_projection",
            "position": "post_generation_only",
        },
        "class_balance": {},
        "layers": {},
        "reliability": {},
        "null": {"permutation": {}, "isotropic": {}},
        "recovery": {},
        "deflation": {},
        "raw_span_overlap": {},
        "confound_bounds": {},
        "secondary_basis": {},
        "robustness_two_seed": {},
    }

    for stage in ALL_STAGES:
        y = caches[stage]["y"]
        n_c, n_w = int((y == 1).sum()), int((y == 0).sum())
        results["class_balance"][stage] = {
            "n_rows": int(len(y)), "n_correct": n_c, "n_wrong": n_w,
            "floor_150_150": bool(n_c >= 150 and n_w >= 150),
        }

    # --- per-stage per-layer core fits (subspace estimator, 4.1) -----------
    fits: dict[str, dict[str, LayerFit]] = {s: {} for s in ALL_STAGES}
    for stage in ALL_STAGES:
        arr = caches[stage]["arr"]
        y = caches[stage]["y"]
        for layer in cfg.layers:
            li = cd.LAYERS.index(layer)
            X_amb = arr[li].astype(np.float64)
            lf = fit_stage_layer(X_amb, y, cfg, stage, layer)
            fits[stage][layer] = lf
            print(f"[so-analysis] core {stage} {layer} auroc={fmt(lf.auroc_pca)} "
                  f"underpowered={lf.underpowered}", flush=True)

    # --- 4.7 retained variance + full-dim AUROC at the recovery layer ------
    full_dim_auroc = {}
    for stage in ALL_STAGES:
        if cfg.recovery_layer in cfg.layers:
            li = cd.LAYERS.index(cfg.recovery_layer)
            X_amb = caches[stage]["arr"][li].astype(np.float64)
            y = caches[stage]["y"]
            full_dim_auroc[stage] = float(cd.cv_auroc(X_amb, y))

    for layer in cfg.layers:
        layer_out = {"stages": {}}
        for stage in ALL_STAGES:
            lf = fits[stage][layer]
            layer_out["stages"][stage] = {
                "auroc_pca128": lf.auroc_pca,
                "auroc_full_dim": full_dim_auroc.get(stage) if layer == cfg.recovery_layer else None,
                "retained_variance_fraction": float(np.sum(lf.pca.explained_variance_ratio_)),
                "n_correct": lf.n_correct, "n_wrong": lf.n_wrong,
                "underpowered": lf.underpowered,
            }
        # timeline pairwise overlap (primary, per-stage-symmetric ambient basis)
        timeline_overlap = {}
        timeline_spectrum = {}
        for a, b in TIMELINE_PAIRS:
            ua, ub = fits[a][layer].subspace, fits[b][layer].subspace
            if ua is not None and ub is not None:
                per_k = {}
                spec = {}
                for k in cfg.k_grid:
                    ov, s = grassmann_overlap(ua, ub, k)
                    per_k[str(k)] = ov
                    spec[str(k)] = s
                timeline_overlap[f"{a}->{b}"] = per_k
                timeline_spectrum[f"{a}->{b}"] = spec
        # S->T bracket
        us, ut = fits["s"][layer].subspace, fits["grpov2"][layer].subspace
        bracket_overlap, bracket_spectrum = {}, {}
        if us is not None and ut is not None:
            for k in cfg.k_grid:
                ov, s = grassmann_overlap(us, ut, k)
                bracket_overlap[str(k)] = ov
                bracket_spectrum[str(k)] = s
        layer_out["timeline_overlap"] = timeline_overlap
        layer_out["timeline_principal_angle_spectrum"] = timeline_spectrum
        layer_out["bracket_s_to_t_overlap"] = bracket_overlap
        layer_out["bracket_s_to_t_spectrum"] = bracket_spectrum

        # raw-span overlap: label-agnostic PCA-128 span overlap per pair (4.5)
        raw_span = {}
        for a, b in TIMELINE_PAIRS + [BRACKET_PAIR]:
            comp_a, comp_b = fits[a][layer].pca.components_, fits[b][layer].pca.components_
            ua_full, ub_full = comp_a.T, comp_b.T   # ambient 2560 x pca_dim, already orthonormal
            ov, _ = grassmann_overlap(ua_full, ub_full, min(cfg.k_max, PCA_DIM))
            raw_span[f"{a}->{b}"] = ov
        results["raw_span_overlap"][layer] = raw_span

        # deflation secondary estimator (reported, not gated)
        deflation_layer = {}
        for stage in ALL_STAGES:
            lf = fits[stage][layer]
            if lf.underpowered:
                continue
            u_defl = deflation_subspace(lf.Xp, lf.y, cfg.k_max, lf.pca.components_)
            ov_at_kgate, _ = grassmann_overlap(lf.subspace, u_defl, min(K_GATE, cfg.k_max))
            deflation_layer[stage] = {"overlap_vs_primary_at_k_gate": ov_at_kgate}
        results["deflation"][layer] = deflation_layer

        results["layers"][layer] = layer_out
        print(f"[so-analysis] layer {layer} timeline/bracket overlaps computed", flush=True)

    # --- 4.4 disjoint half-split reliability (gate layers only) ------------
    for stage in ALL_STAGES:
        results["reliability"][stage] = {}
        for layer in cfg.gate_layers:
            if layer not in cfg.layers:
                continue
            y = caches[stage]["y"]
            if min(int((y == 1).sum()), int((y == 0).sum())) < MIN_CLASS:
                continue
            n = len(y)
            li = cd.LAYERS.index(layer)
            X_amb = caches[stage]["arr"][li].astype(np.float64)
            m_values = sorted({max(MIN_CLASS, int(round(n * f))) for f in M_FRACTIONS})
            per_m = {}
            for m in m_values:
                if 2 * m > n:
                    continue
                per_m[m] = disjoint_reliability(X_amb, y, m, cfg, SEED_PRIMARY,
                                                 f"{stage}_{layer}", cfg.k_grid)
            if len(per_m) < 2:
                results["reliability"][stage][layer] = {"not_computable": True, "m_values_used": list(per_m)}
                continue
            m_sorted = sorted(per_m.keys())
            per_k_extrap = {}
            for k in cfg.k_grid:
                overlap_at_m = [per_m[m][k] for m in m_sorted]
                per_k_extrap[str(k)] = extrapolate_reliability(m_sorted, overlap_at_m, n)
            results["reliability"][stage][layer] = {
                "m_values_used": m_sorted,
                "overlap_by_m_by_k": {str(k): {str(m): per_m[m][k] for m in m_sorted} for k in cfg.k_grid},
                "extrapolation_by_k": per_k_extrap,
            }
            print(f"[so-analysis] reliability {stage} {layer} m={m_sorted} done", flush=True)

    # --- 4.5 label-permutation null (primary) + isotropic null (secondary) -
    pairs_for_null = TIMELINE_PAIRS + [BRACKET_PAIR]
    stages_needed = sorted({s for pair in pairs_for_null for s in pair})
    perm_subspaces: dict[str, dict[str, list]] = {s: {} for s in stages_needed}
    iso_subspaces: dict[str, dict[str, list]] = {s: {} for s in stages_needed}
    for stage in stages_needed:
        for layer in cfg.gate_layers:
            if layer not in cfg.layers:
                continue
            lf = fits[stage][layer]
            if lf.underpowered:
                continue
            perm_list, iso_list = [], []
            for p in range(cfg.p_perm):
                perm_rng = rng_for(SEED_PRIMARY, stage, layer, "perm_label", f"p{p}")
                boot_rng = rng_for(SEED_PRIMARY, stage, layer, "perm_boot", f"p{p}")
                perm_list.append(permuted_subspace(lf.Xp, lf.y, lf.pca.components_,
                                                    cfg.b_null, cfg.k_max, perm_rng, boot_rng))
            for i in range(cfg.n_iso):
                iso_rng = rng_for(SEED_PRIMARY, stage, layer, "iso", f"i{i}")
                iso_list.append(random_ambient_subspace(lf.pca.components_, cfg.k_max, iso_rng))
            perm_subspaces[stage][layer] = perm_list
            iso_subspaces[stage][layer] = iso_list
            print(f"[so-analysis] null draws {stage} {layer}: perm={len(perm_list)} iso={len(iso_list)}", flush=True)

    for a, b in pairs_for_null:
        pair_key = f"{a}->{b}"
        results["null"]["permutation"][pair_key] = {}
        results["null"]["isotropic"][pair_key] = {}
        for layer in cfg.gate_layers:
            if layer not in cfg.layers:
                continue
            if layer not in perm_subspaces.get(a, {}) or layer not in perm_subspaces.get(b, {}):
                continue
            n_draws = min(len(perm_subspaces[a][layer]), len(perm_subspaces[b][layer]))
            perm_by_k = {k: [] for k in cfg.k_grid}
            for i in range(n_draws):
                ua, ub = perm_subspaces[a][layer][i], perm_subspaces[b][layer][i]
                for k in cfg.k_grid:
                    ov, _ = grassmann_overlap(ua, ub, k)
                    perm_by_k[k].append(ov)
            results["null"]["permutation"][pair_key][layer] = {
                str(k): {"mean": float(np.mean(v)), "p95": float(np.percentile(v, 95)),
                          "n_draws": len(v)}
                for k, v in perm_by_k.items()
            }
            n_iso_draws = min(len(iso_subspaces[a][layer]), len(iso_subspaces[b][layer]))
            iso_by_k = {k: [] for k in cfg.k_grid}
            for i in range(n_iso_draws):
                ua, ub = iso_subspaces[a][layer][i], iso_subspaces[b][layer][i]
                for k in cfg.k_grid:
                    ov, _ = grassmann_overlap(ua, ub, k)
                    iso_by_k[k].append(ov)
            results["null"]["isotropic"][pair_key][layer] = {
                str(k): {"mean": float(np.mean(v)), "p95": float(np.percentile(v, 95)),
                          "n_draws": len(v)}
                for k, v in iso_by_k.items()
            }

    # --- 4.6 recovery curve (floor / ceiling), S -> T, gate layers ---------
    for layer in cfg.gate_layers:
        if layer not in cfg.layers:
            continue
        lf_s, lf_t = fits["s"].get(layer), fits["grpov2"].get(layer)
        if lf_s is None or lf_t is None or lf_s.underpowered or lf_t.underpowered:
            continue
        li = cd.LAYERS.index(layer)
        X_t_amb = caches["grpov2"]["arr"][li].astype(np.float64)
        y_t = caches["grpov2"]["y"]
        layer_recovery = {}
        for k in cfg.k_grid:
            u_s_k = lf_s.subspace[:, :k]
            u_t_k = lf_t.subspace[:, :k]
            recov = recovery_auroc(X_t_amb, y_t, u_s_k)
            ceiling = recovery_auroc(X_t_amb, y_t, u_t_k)
            iso_draws = iso_subspaces.get("s", {}).get(layer, [])
            if iso_draws:
                floor_vals = [recovery_auroc(X_t_amb, y_t, d[:, :k]) for d in iso_draws]
                floor = float(np.mean(floor_vals))
            else:
                floor = None
            denom = (ceiling - floor) if floor is not None else None
            closed_fraction = float((recov - floor) / denom) if denom and abs(denom) > 1e-9 else None
            layer_recovery[str(k)] = {
                "recovery_auroc": float(recov), "floor_auroc": floor,
                "ceiling_auroc": float(ceiling), "closed_fraction": closed_fraction,
            }
        results["recovery"][layer] = layer_recovery
        print(f"[so-analysis] recovery curve {layer} done", flush=True)

    # --- 4.8 matched-population S->T confound bound -------------------------
    if cfg.recovery_layer in cfg.layers:
        keys_s = set(caches["s"]["keys"].tolist())
        keys_t = set(caches["grpov2"]["keys"].tolist())
        shared = keys_s & keys_t
        li = cd.LAYERS.index(cfg.recovery_layer)
        mask_s = restrict_to_keys(caches["s"], shared)
        mask_t = restrict_to_keys(caches["grpov2"], shared)
        y_s_m, y_t_m = caches["s"]["y"][mask_s], caches["grpov2"]["y"][mask_t]
        n_cs, n_ws = int((y_s_m == 1).sum()), int((y_s_m == 0).sum())
        n_ct, n_wt = int((y_t_m == 1).sum()), int((y_t_m == 0).sum())
        matched_out = {"n_shared": len(shared), "s_correct": n_cs, "s_wrong": n_ws,
                       "t_correct": n_ct, "t_wrong": n_wt}
        if min(n_cs, n_ws) >= MIN_CLASS and min(n_ct, n_wt) >= MIN_CLASS:
            x_s_m = caches["s"]["arr"][li][mask_s].astype(np.float64)
            x_t_m = caches["grpov2"]["arr"][li][mask_t].astype(np.float64)
            lf_s_m = fit_stage_layer(x_s_m, y_s_m, cfg, "s_matched", cfg.recovery_layer)
            lf_t_m = fit_stage_layer(x_t_m, y_t_m, cfg, "t_matched", cfg.recovery_layer)
            if lf_s_m.subspace is not None and lf_t_m.subspace is not None:
                overlap_by_k = {}
                for k in cfg.k_grid:
                    ov, _ = grassmann_overlap(lf_s_m.subspace, lf_t_m.subspace, k)
                    overlap_by_k[str(k)] = ov
                matched_out["overlap_by_k"] = overlap_by_k
                full_pop_overlap = results["layers"][cfg.recovery_layer]["bracket_s_to_t_overlap"]
                matched_out["delta_vs_full_population"] = {
                    k: overlap_by_k[k] - full_pop_overlap[k]
                    for k in overlap_by_k if k in full_pop_overlap
                }
        else:
            matched_out["not_computable"] = True
        results["confound_bounds"]["matched_population_st"] = matched_out
        print("[so-analysis] matched-population S->T bound done", flush=True)

    # --- 4.8 matched-class-balance timeline (secondary) ---------------------
    if cfg.recovery_layer in cfg.layers:
        li = cd.LAYERS.index(cfg.recovery_layer)
        common_n = min(min(int((caches[s]["y"] == 1).sum()), int((caches[s]["y"] == 0).sum()))
                       for s in TIMELINE_STAGES)
        matched_fits = {}
        for stage in TIMELINE_STAGES:
            y = caches[stage]["y"]
            idx_c = np.where(y == 1)[0]
            idx_w = np.where(y == 0)[0]
            bal_rng = np.random.default_rng(sub_seed(SEED_PRIMARY, "matched_class_balance", stage))
            sel_c = bal_rng.choice(idx_c, size=common_n, replace=False)
            sel_w = bal_rng.choice(idx_w, size=common_n, replace=False)
            idx = np.concatenate([sel_c, sel_w])
            x_amb = caches[stage]["arr"][li][idx].astype(np.float64)
            y_bal = y[idx]
            matched_fits[stage] = fit_stage_layer(x_amb, y_bal, cfg, f"{stage}_balanced", cfg.recovery_layer)
        mcb_out = {"common_n_per_class": int(common_n), "overlap_by_pair_by_k": {}}
        for a, b in TIMELINE_PAIRS:
            if matched_fits[a].subspace is not None and matched_fits[b].subspace is not None:
                per_k = {}
                for k in cfg.k_grid:
                    ov, _ = grassmann_overlap(matched_fits[a].subspace, matched_fits[b].subspace, k)
                    per_k[str(k)] = ov
                mcb_out["overlap_by_pair_by_k"][f"{a}->{b}"] = per_k
        full_pop = results["layers"][cfg.recovery_layer]["timeline_overlap"]
        mcb_out["delta_vs_full_population"] = {
            pair: {k: mcb_out["overlap_by_pair_by_k"][pair][k] - full_pop[pair][k]
                   for k in mcb_out["overlap_by_pair_by_k"][pair] if pair in full_pop}
            for pair in mcb_out["overlap_by_pair_by_k"]
        }
        results["confound_bounds"]["matched_class_balance_timeline"] = mcb_out
        print("[so-analysis] matched-class-balance timeline done", flush=True)

    # --- 4.7 secondary robustness: pooled shared symmetric basis ------------
    if cfg.recovery_layer in cfg.layers:
        li = cd.LAYERS.index(cfg.recovery_layer)
        pool_n = min(len(caches[s]["y"]) for s in TIMELINE_STAGES)
        pooled_X, pooled_idx_by_stage = [], {}
        cursor = 0
        for stage in TIMELINE_STAGES:
            n_stage = len(caches[stage]["y"])
            pool_rng = np.random.default_rng(sub_seed(SEED_PRIMARY, "pooled_basis", stage))
            sel = pool_rng.choice(n_stage, size=min(pool_n, n_stage), replace=False)
            x = caches[stage]["arr"][li][sel].astype(np.float64)
            pooled_X.append(x)
            pooled_idx_by_stage[stage] = (cursor, cursor + len(sel), sel)
            cursor += len(sel)
        pooled_X = np.concatenate(pooled_X, axis=0)
        pooled_pca = PCA(n_components=PCA_DIM, svd_solver="randomized",
                          random_state=SEED_PCA_FOLD).fit(pooled_X)
        shared_fits = {}
        for stage in TIMELINE_STAGES:
            start, end, sel = pooled_idx_by_stage[stage]
            y_sel = caches[stage]["y"][sel]
            x_amb = caches[stage]["arr"][li][sel].astype(np.float64)
            xp = pooled_pca.transform(x_amb)
            if min(int((y_sel == 1).sum()), int((y_sel == 0).sum())) < MIN_CLASS:
                shared_fits[stage] = None
                continue
            rng = rng_for(SEED_PRIMARY, "pooled_basis_subspace", stage)
            u = estimate_stage_subspace(xp, y_sel, pooled_pca.components_, cfg.b_boot, rng, cfg.k_max)
            shared_fits[stage] = u
        pooled_overlap = {}
        for a, b in TIMELINE_PAIRS:
            if shared_fits.get(a) is not None and shared_fits.get(b) is not None:
                per_k = {}
                for k in cfg.k_grid:
                    ov, _ = grassmann_overlap(shared_fits[a], shared_fits[b], k)
                    per_k[str(k)] = ov
                pooled_overlap[f"{a}->{b}"] = per_k
        full_pop = results["layers"][cfg.recovery_layer]["timeline_overlap"]
        agreement = {
            pair: {k: pooled_overlap[pair][k] - full_pop[pair][k]
                   for k in pooled_overlap[pair] if pair in full_pop}
            for pair in pooled_overlap
        }
        results["secondary_basis"] = {
            "pooled_shared_basis_overlap": pooled_overlap,
            "delta_vs_primary_per_stage_symmetric": agreement,
        }
        print("[so-analysis] pooled shared-basis secondary robustness done", flush=True)

    # --- 5.4 two-seed headline robustness rerun (k=8, S->T, gate layers) ---
    # "seed_primary" reuses the already-computed core subspaces (same seed
    # SEED_PRIMARY, same "core_bootstrap" derivation) rather than recomputing
    # them under a different derived sub-seed; only SEED_ROBUST is a fresh
    # fit, matching the packet's cost table ("1 extra seed").
    seed_rerun_layers = [l for l in cfg.gate_layers if l in cfg.layers]
    two_seed = {"seed_primary": {}, "seed_robust": {}}
    k_use = min(K_GATE, cfg.k_max)
    bracket_pair_key_early = f"{BRACKET_PAIR[0]}->{BRACKET_PAIR[1]}"
    for layer in seed_rerun_layers:
        lf_s, lf_t = fits["s"].get(layer), fits["grpov2"].get(layer)
        if lf_s is None or lf_t is None or lf_s.underpowered or lf_t.underpowered:
            continue
        ov, _ = grassmann_overlap(lf_s.subspace, lf_t.subspace, k_use)
        null_k = results["null"]["permutation"].get(bracket_pair_key_early, {}).get(layer, {}).get(str(k_use), {})
        margin = (ov - null_k["mean"]) if null_k else None
        passes_margin = bool(null_k and ov > null_k.get("p95", 1.0) and margin is not None and margin >= MARGIN_015)
        two_seed["seed_primary"][layer] = {
            "overlap_k8_or_kmax": ov, "k_used": k_use,
            "margin_vs_perm_null_mean": margin, "so_g1_i_pass_this_seed": passes_margin,
        }
    for layer in seed_rerun_layers:
        li = cd.LAYERS.index(layer)
        per_stage_subspace = {}
        per_stage_pca = {}
        for stage in ("s", "grpov2"):
            y = caches[stage]["y"]
            x_amb = caches[stage]["arr"][li].astype(np.float64)
            pca = PCA(n_components=PCA_DIM, svd_solver="randomized",
                      random_state=SEED_PCA_FOLD).fit(x_amb)
            xp = pca.transform(x_amb)
            rng = rng_for(SEED_ROBUST, stage, layer, "core_bootstrap")
            u = estimate_stage_subspace(xp, y, pca.components_, cfg.b_boot, rng, cfg.k_max)
            per_stage_subspace[stage] = u
            per_stage_pca[stage] = (pca, xp)
        ov, _ = grassmann_overlap(per_stage_subspace["s"], per_stage_subspace["grpov2"], k_use)
        # rerun the permutation-null margin too, under SEED_ROBUST, restricted
        # to this one pair/k (spec 5.4: "...and its permutation-null margin
        # rerun under a second pinned seed... for the bootstrap, permutation,
        # and fold RNGs"). Not budgeted in the packet's cost table; flagged.
        null_vals = []
        for p in range(cfg.p_perm):
            draws = {}
            for stage in ("s", "grpov2"):
                pca, xp = per_stage_pca[stage]
                y = caches[stage]["y"]
                perm_rng = rng_for(SEED_ROBUST, stage, layer, "perm_label", f"p{p}")
                boot_rng = rng_for(SEED_ROBUST, stage, layer, "perm_boot", f"p{p}")
                draws[stage] = permuted_subspace(xp, y, pca.components_, cfg.b_null, k_use, perm_rng, boot_rng)
            ov_null, _ = grassmann_overlap(draws["s"], draws["grpov2"], k_use)
            null_vals.append(ov_null)
        null_k = {"mean": float(np.mean(null_vals)), "p95": float(np.percentile(null_vals, 95)),
                  "n_draws": len(null_vals)}
        margin = ov - null_k["mean"]
        passes_margin = bool(ov > null_k["p95"] and margin >= MARGIN_015)
        two_seed["seed_robust"][layer] = {
            "overlap_k8_or_kmax": ov, "k_used": k_use,
            "perm_null_mean": null_k["mean"], "perm_null_p95": null_k["p95"],
            "margin_vs_perm_null_mean": margin, "so_g1_i_pass_this_seed": passes_margin,
        }
    agree = all(
        two_seed["seed_primary"][l]["so_g1_i_pass_this_seed"] == two_seed["seed_robust"][l]["so_g1_i_pass_this_seed"]
        for l in seed_rerun_layers
    ) if seed_rerun_layers else None
    two_seed["seeds_agree_on_so_g1_i"] = agree
    results["robustness_two_seed"] = two_seed
    print(f"[so-analysis] two-seed robustness rerun done, agree={agree}", flush=True)

    # --- gate-relevant summary (k=8, L19-L24; reported straight) -----------
    k_gate_str = str(min(K_GATE, cfg.k_max))
    bracket_pair_key = f"{BRACKET_PAIR[0]}->{BRACKET_PAIR[1]}"

    def summary_mean(getter):
        vals = [getter(l) for l in cfg.gate_layers if l in cfg.layers]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None

    overlap_mean = summary_mean(lambda l: results["layers"].get(l, {}).get("bracket_s_to_t_overlap", {}).get(k_gate_str))
    null_mean_mean = summary_mean(
        lambda l: results["null"]["permutation"].get(bracket_pair_key, {}).get(l, {}).get(k_gate_str, {}).get("mean"))
    null_p95_mean = summary_mean(
        lambda l: results["null"]["permutation"].get(bracket_pair_key, {}).get(l, {}).get(k_gate_str, {}).get("p95"))
    rel_s_mean = summary_mean(
        lambda l: results["reliability"].get("s", {}).get(l, {}).get("extrapolation_by_k", {}).get(k_gate_str, {}).get("reliability"))
    rel_t_mean = summary_mean(
        lambda l: results["reliability"].get("grpov2", {}).get(l, {}).get("extrapolation_by_k", {}).get(k_gate_str, {}).get("reliability"))
    closed_fraction_mean = summary_mean(
        lambda l: results["recovery"].get(l, {}).get(k_gate_str, {}).get("closed_fraction"))

    so_g1_i_pass = bool(
        overlap_mean is not None and null_mean_mean is not None and null_p95_mean is not None
        and overlap_mean > null_p95_mean and (overlap_mean - null_mean_mean) >= MARGIN_015
    )
    so_g1_ii_pass = bool(
        rel_s_mean is not None and rel_t_mean is not None
        and rel_s_mean >= RELIABILITY_070 and rel_t_mean >= RELIABILITY_070
    )
    so_g1_iii_pass = bool(closed_fraction_mean is not None and closed_fraction_mean >= RECOVERY_075)
    so_g1_conjunction = bool(so_g1_i_pass and so_g1_ii_pass and so_g1_iii_pass)

    null_indist = bool(
        overlap_mean is not None and null_mean_mean is not None and null_p95_mean is not None
        and overlap_mean <= null_p95_mean and abs(overlap_mean - null_mean_mean) <= 0.10
    )
    reading_b = bool(
        null_indist and rel_s_mean is not None and rel_t_mean is not None
        and rel_s_mean >= RELIABILITY_070 and rel_t_mean >= RELIABILITY_070
        and closed_fraction_mean is not None and closed_fraction_mean <= 0.25
    )
    if so_g1_conjunction:
        reading = "A"
    elif reading_b:
        reading = "B"
    else:
        reading = "middle_ground"

    k1_recovery = results["recovery"].get(RECOVERY_LAYER, {}).get("1", {}).get("recovery_auroc")
    k1_near_0679 = bool(k1_recovery is not None and abs(k1_recovery - DOCUMENTED_COLD_TRANSFER) <= 0.10)

    results["gate_relevant_summary"] = {
        "k_gate": int(k_gate_str),
        "so_g1_i_overlap_mean": overlap_mean,
        "so_g1_i_perm_null_mean": null_mean_mean,
        "so_g1_i_perm_null_p95": null_p95_mean,
        "so_g1_i_margin": (overlap_mean - null_mean_mean) if (overlap_mean is not None and null_mean_mean is not None) else None,
        "so_g1_i_pass": so_g1_i_pass,
        "so_g1_ii_reliability_s": rel_s_mean,
        "so_g1_ii_reliability_t": rel_t_mean,
        "so_g1_ii_pass": so_g1_ii_pass,
        "so_g1_iii_closed_fraction": closed_fraction_mean,
        "so_g1_iii_pass": so_g1_iii_pass,
        "so_g1_conjunction_pass": so_g1_conjunction,
        "reading": reading,
        "k1_sanity_recovery_auroc_L20": k1_recovery,
        "k1_sanity_near_documented_0679": k1_near_0679,
        "two_seed_agree": agree,
    }

    wall_time_s = time.time() - t_start
    results["config"]["wall_time_seconds"] = wall_time_s

    # --- schema completeness assertion (required for --smoke) --------------
    if cfg.smoke:
        checks = []

        def check(name, cond):
            checks.append((name, bool(cond)))

        gs = results["gate_relevant_summary"]
        for field_name in ("so_g1_i_overlap_mean", "so_g1_i_perm_null_mean", "so_g1_i_perm_null_p95",
                           "so_g1_ii_reliability_s", "so_g1_ii_reliability_t",
                           "so_g1_iii_closed_fraction", "k1_sanity_recovery_auroc_L20"):
            v = gs.get(field_name)
            check(f"gate_relevant_summary.{field_name} present+finite", v is not None and np.isfinite(v))
        check("reading in {A,B,middle_ground}", gs["reading"] in ("A", "B", "middle_ground"))
        k1_val = gs["k1_sanity_recovery_auroc_L20"]
        check("k=1 recovery within [0.5, 0.9] loose sanity", k1_val is not None and 0.5 <= k1_val <= 0.9)
        check("recovery block non-empty", len(results["recovery"]) > 0)
        check("reliability block non-empty for s and grpov2",
              len(results["reliability"].get("s", {})) > 0 and len(results["reliability"].get("grpov2", {})) > 0)
        check("permutation null non-empty for S->T bracket",
              len(results["null"]["permutation"].get(bracket_pair_key, {})) > 0)
        check("isotropic null non-empty for S->T bracket",
              len(results["null"]["isotropic"].get(bracket_pair_key, {})) > 0)
        check("confound_bounds.matched_population_st present", "matched_population_st" in results["confound_bounds"])
        check("confound_bounds.matched_class_balance_timeline present",
              "matched_class_balance_timeline" in results["confound_bounds"])
        check("secondary_basis pooled overlap present", "pooled_shared_basis_overlap" in results["secondary_basis"])
        check("robustness_two_seed both seeds present",
              len(results["robustness_two_seed"]["seed_primary"]) > 0 and len(results["robustness_two_seed"]["seed_robust"]) > 0)
        check("deflation block non-empty", any(len(v) > 0 for v in results["deflation"].values()))
        check("raw_span_overlap block non-empty", any(len(v) > 0 for v in results["raw_span_overlap"].values()))

        results["smoke_schema_assertions"] = [{"name": n, "passed": p} for n, p in checks]
        n_fail = sum(1 for _, p in checks if not p)
        print(f"[so-analysis] SMOKE schema assertions: {len(checks)-n_fail}/{len(checks)} passed", flush=True)
        for n, p in checks:
            print(f"[so-analysis]   {'OK ' if p else 'FAIL'} {n}", flush=True)
        if n_fail:
            print(f"[so-analysis] SMOKE FAILED: {n_fail} assertion(s) failed", flush=True)

    # --- write outputs -------------------------------------------------------
    (out_dir / "subspace_overlap_timeline.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = ["# Correctness discriminative-subspace overlap across training checkpoints", "",
              f"Smoke mode: {cfg.smoke}. Metric: Grassmann projection (mean squared cosine of",
              "principal angles). Position: post-generation only. Seeds: PCA/fold "
              f"{SEED_PCA_FOLD}, bootstrap/permutation/isotropic {SEED_PRIMARY}, "
              f"robustness {SEED_ROBUST}.", ""]
    lines.append("## Class balance (per stage)")
    lines.append("")
    lines.append("| stage | rows | correct | wrong | floor (>=150/150) |")
    lines.append("|---|---|---|---|---|")
    for stage in ALL_STAGES:
        b = results["class_balance"][stage]
        lines.append(f"| {stage} | {b['n_rows']} | {b['n_correct']} | {b['n_wrong']} | {b['floor_150_150']} |")
    lines.append("")
    lines.append("## Core AUROC and retained variance by layer by stage (PCA-128)")
    lines.append("")
    lines.append("| layer | " + " | ".join(ALL_STAGES) + " |")
    lines.append("|---|" + "---|" * len(ALL_STAGES))
    for layer in cfg.layers:
        cells = [fmt(results["layers"][layer]["stages"][s]["auroc_pca128"]) for s in ALL_STAGES]
        lines.append(f"| {layer} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"## S->T bracket overlap by k (gate layers, k_gate={k_gate_str})")
    lines.append("")
    lines.append("| layer | " + " | ".join(f"k={k}" for k in cfg.k_grid) + " |")
    lines.append("|---|" + "---|" * len(cfg.k_grid))
    for layer in cfg.gate_layers:
        if layer not in cfg.layers:
            continue
        row = results["layers"].get(layer, {}).get("bracket_s_to_t_overlap", {})
        cells = [fmt(row.get(str(k))) for k in cfg.k_grid]
        lines.append(f"| {layer} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"## S->T label-permutation null, mean / p95 at k={k_gate_str}")
    lines.append("")
    lines.append("| layer | null mean | null p95 | overlap | margin vs mean | passes SO-G1(i) |")
    lines.append("|---|---|---|---|---|---|")
    for layer in cfg.gate_layers:
        if layer not in cfg.layers:
            continue
        null_k = results["null"]["permutation"].get(bracket_pair_key, {}).get(layer, {}).get(k_gate_str, {})
        ov = results["layers"].get(layer, {}).get("bracket_s_to_t_overlap", {}).get(k_gate_str)
        mean_, p95_ = null_k.get("mean"), null_k.get("p95")
        margin = (ov - mean_) if (ov is not None and mean_ is not None) else None
        passes = bool(ov is not None and p95_ is not None and margin is not None and ov > p95_ and margin >= MARGIN_015)
        lines.append(f"| {layer} | {fmt(mean_)} | {fmt(p95_)} | {fmt(ov)} | {fmt(margin)} | {passes} |")
    lines.append("")
    lines.append(f"## Within-stage full-n reliability at k={k_gate_str} (S, T)")
    lines.append("")
    lines.append("| layer | reliability (S) | R^2 (S) | fallback (S) | reliability (T) | R^2 (T) | fallback (T) |")
    lines.append("|---|---|---|---|---|---|---|")
    for layer in cfg.gate_layers:
        if layer not in cfg.layers:
            continue
        s_e = results["reliability"].get("s", {}).get(layer, {}).get("extrapolation_by_k", {}).get(k_gate_str, {})
        t_e = results["reliability"].get("grpov2", {}).get(layer, {}).get("extrapolation_by_k", {}).get(k_gate_str, {})
        lines.append(f"| {layer} | {fmt(s_e.get('reliability'))} | {fmt(s_e.get('r2'))} | "
                     f"{s_e.get('used_fallback')} | {fmt(t_e.get('reliability'))} | {fmt(t_e.get('r2'))} | "
                     f"{t_e.get('used_fallback')} |")
    lines.append("")
    lines.append(f"## Recovery curve at k={k_gate_str} (floor / ceiling / closed fraction)")
    lines.append("")
    lines.append("| layer | recovery AUROC | floor | ceiling | closed fraction |")
    lines.append("|---|---|---|---|---|")
    for layer in cfg.gate_layers:
        if layer not in cfg.layers:
            continue
        rc = results["recovery"].get(layer, {}).get(k_gate_str, {})
        lines.append(f"| {layer} | {fmt(rc.get('recovery_auroc'))} | {fmt(rc.get('floor_auroc'))} | "
                     f"{fmt(rc.get('ceiling_auroc'))} | {fmt(rc.get('closed_fraction'))} |")
    lines.append("")
    lines.append("## k=1 pipeline sanity check (recovery vs documented 0.679 cold transfer)")
    lines.append("")
    lines.append(f"- k=1 recovery AUROC at {RECOVERY_LAYER}: {fmt(k1_recovery)}")
    lines.append(f"- documented cold transfer: {DOCUMENTED_COLD_TRANSFER}")
    lines.append(f"- within 0.10: {k1_near_0679}")
    lines.append("")
    lines.append("## Gate-relevant summary (L19-L24 means; reported straight, no goalpost moves)")
    lines.append("")
    for k, v in results["gate_relevant_summary"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Two-seed headline robustness rerun (k=8 or k_max, S->T)")
    lines.append("")
    lines.append("| seed | layer | overlap | margin vs perm-null mean | passes SO-G1(i) this seed |")
    lines.append("|---|---|---|---|---|")
    for tag in ("seed_primary", "seed_robust"):
        for layer in seed_rerun_layers:
            v = two_seed[tag][layer]
            lines.append(f"| {tag} | {layer} | {fmt(v['overlap_k8_or_kmax'])} | "
                         f"{fmt(v['margin_vs_perm_null_mean'])} | {v['so_g1_i_pass_this_seed']} |")
    lines.append(f"\nSeeds agree on SO-G1(i): {agree}")
    lines.append("")
    if cfg.smoke:
        lines.append("## Smoke schema assertions")
        lines.append("")
        for entry in results["smoke_schema_assertions"]:
            lines.append(f"- [{'OK' if entry['passed'] else 'FAIL'}] {entry['name']}")
        lines.append("")
    (out_dir / "subspace_overlap_timeline.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"[so-analysis] wrote {out_dir}/subspace_overlap_timeline.json and .md "
          f"in {wall_time_s:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
