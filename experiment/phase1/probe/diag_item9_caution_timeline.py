#!/usr/bin/env python3
"""Diagnostics item 9 - caution readout across the training trajectory.

Lab-notebook diagnostic (NOT an amendment). Traces how the caution/abstention
readout develops across four training stages:

    raw base -> clean-SFT -> clean-SFT+GRPO-v2 -> clean-SFT+GRPO-par-true

using the full-stack (L0..L36) pre-generation anchor states produced by
amendment_ai_verdict_extract_gen.py --stage extract --surface union --layers
L0,...,L36 at pinned commit d5a90b3b over pools/a0_pool_v21_questions.jsonl.

WHAT THE LABEL IS. The four extract tarballs are forward-only (no generation),
so their rows.jsonl carry NO answered/refused behavior field - only the
POOL-DERIVED answerability label ("known" vs "unknown"), which is identical
across all four stages (same pool, same row_keys). The caution/abstention axis
in this program IS the known-vs-unknown answerability gate (the doubt axis the
gate/dial decomposition calls the caution signal). So the probe here is a
known(0)-vs-unknown(1) answerability probe fit per stage per layer; "caution
sharpening" = the answerability readout getting more separable with training.
This is documented as a divergence from the task's answered-vs-refused framing
because the extract cells emitted no behavior field to build that label from.

METHOD (per stage, per layer, deterministic + seeded):
  1. Randomized PCA-128 fit ONCE per layer on the RAW-stage union of activations
     (label-agnostic), then REUSED for every stage at that layer - so the fitted
     directions all live in the SAME basis and are cosine-comparable across
     stages (the cpu-probe recipe: PCA-128 then saga logistic, never full-dim
     lbfgs which is unusably slow on this box). PCA-on-raw is the documented
     basis choice; raw is the fixed reference frame the trajectory rotates away
     from.
  2. LogisticRegression(solver="saga", tol=1e-3) with StratifiedKFold(5) CV;
     report pooled out-of-fold AUROC per stage per layer.
  3. Fit a full-data direction per stage per layer (same PCA basis), map the
     PCA-space coefficient back to the 2560-dim residual space (via the shared
     PCA components), unit-norm, and report:
       - consecutive-stage cosines (raw->cleansft->grpov2, and ->partrue)
       - each stage vs grpov2 cosine
  4. Cosine of each stage's residual-space direction against the checked-in
     canonical answerability axis (steering/directions/qwen3.5-4b/
     direction_gate.safetensors, best_layer 14) at matched layer index. This is
     a CROSS-FAMILY axis (Qwen3.5-4B, not the Qwen3-4B extracted here) so it is
     a heuristic alignment check, flagged as such.
  5. Class-balance guard: report AUROC only where BOTH classes have >= 30 rows;
     otherwise mark the cell underpowered. Never silently drop a stage.

Outputs (UNTRACKED, under analysis/): diag_item9_caution_timeline.json plus a
small markdown table diag_item9_caution_timeline.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from safetensors import safe_open
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SEED = 20260705
PCA_DIM = 128
N_FOLDS = 5
MIN_CLASS = 30
LAYERS = [f"L{i}" for i in range(37)]  # L0..L36
STAGES = ["raw", "cleansft", "grpov2", "partrue"]
BASIS_STAGE = "raw"  # PCA basis fit once per layer on this stage's union


def build_stage_cache(stage_dir: Path, cache_path: Path) -> None:
    """Read every per-row safetensors ONCE, stack all layers into one .npz.

    Reloading 1662 files per layer is the runtime killer; instead load each
    file once (all 37 layers) and persist a single array of shape
    (n_layers, n_rows, 2560) plus the label vector and row_keys.
    """
    if cache_path.exists():
        return
    rows = [json.loads(ln) for ln in (stage_dir / "rows.jsonl").open(encoding="utf-8")
            if ln.strip()]
    n = len(rows)
    arr = np.empty((len(LAYERS), n, 2560), dtype=np.float32)
    y = np.empty(n, dtype=np.int64)
    keys = []
    for i, r in enumerate(rows):
        st = stage_dir / f"{r['safe_key']}__pre.safetensors"
        with safe_open(str(st), framework="np") as h:
            for li, layer in enumerate(LAYERS):
                arr[li, i, :] = h.get_tensor(layer)
        y[i] = 1 if r["label"] == "unknown" else 0
        keys.append(r["row_key"])
    np.savez(cache_path, arr=arr, y=y, keys=np.array(keys))


def load_stage_layer(cache: dict, layer: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (X [n,2560] float64, y [n] unknown=1/known=0) from an in-mem cache."""
    li = LAYERS.index(layer)
    return cache["arr"][li].astype(np.float64), cache["y"]


def cv_auroc(Xp: np.ndarray, y: np.ndarray) -> float:
    """Pooled out-of-fold AUROC, PCA-space features, saga logistic."""
    oof = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for tr, te in skf.split(Xp, y):
        sc = StandardScaler().fit(Xp[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000,
                                 random_state=SEED)
        clf.fit(sc.transform(Xp[tr]), y[tr])
        oof[te] = clf.decision_function(sc.transform(Xp[te]))
    return float(roc_auc_score(y, oof))


def full_direction(Xp: np.ndarray, y: np.ndarray, components: np.ndarray) -> np.ndarray:
    """Fit full-data logistic in PCA space, map coef back to 2560-dim, unit-norm.

    components: PCA components_ (PCA_DIM, 2560). The logistic operates on
    standardized PCA features; the residual-space direction is
    (coef / scale) @ components, which is the gradient of the decision function
    in the original residual coordinates.
    """
    sc = StandardScaler().fit(Xp)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000,
                             random_state=SEED)
    clf.fit(sc.transform(Xp), y)
    coef_pca = clf.coef_[0] / sc.scale_          # undo standardization
    d = coef_pca @ components                     # back to 2560-dim
    n = np.linalg.norm(d)
    return d / n if n else d


def cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def load_canonical_gate(repo: Path) -> tuple[np.ndarray | None, int | None]:
    p = repo / ("experiment/phase1/probe/steering/directions/qwen3.5-4b/"
                "direction_gate.safetensors")
    j = repo / ("experiment/phase1/probe/steering/directions/qwen3.5-4b/"
                "direction_gate.json")
    if not p.exists():
        return None, None
    with safe_open(str(p), framework="np") as h:
        d = h.get_tensor("d").astype(np.float64)
    best_layer = None
    if j.exists():
        best_layer = json.loads(j.read_text()).get("best_layer")
    return d, best_layer


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract-root", required=True,
                    help="dir holding ex_<stage>/data/ for the four stages")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cache-dir", required=True,
                    help="scratch dir for per-stage activation caches (.npz)")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args()

    root = Path(args.extract_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    repo = Path(args.repo)

    stage_dirs = {s: root / f"ex_{s}" / "data" for s in STAGES}
    for s, d in stage_dirs.items():
        if not (d / "rows.jsonl").exists():
            raise SystemExit(f"missing rows.jsonl for stage {s} at {d}")

    gate_d, gate_layer = load_canonical_gate(repo)

    # Build one activation cache per stage (all layers, read each file once),
    # then hold in memory for the layer sweep.
    caches = {}
    for s in STAGES:
        cp = Path(args.cache_dir) / f"cache_{s}.npz"
        cp.parent.mkdir(parents=True, exist_ok=True)
        build_stage_cache(stage_dirs[s], cp)
        caches[s] = np.load(cp, allow_pickle=True)
        print(f"[item9] cache {s}: arr={caches[s]['arr'].shape}", flush=True)

    # class balance (label is pool-derived, identical across stages, but verify)
    balance = {}
    for s in STAGES:
        y = caches[s]["y"]
        n_unknown = int((y == 1).sum())
        n_known = int((y == 0).sum())
        balance[s] = {"n_rows": int(len(y)), "n_known": n_known,
                      "n_unknown": n_unknown,
                      "underpowered": bool(min(n_known, n_unknown) < MIN_CLASS)}

    results = {"layers": {}, "class_balance": balance,
               "config": {"seed": SEED, "pca_dim": PCA_DIM, "n_folds": N_FOLDS,
                          "min_class": MIN_CLASS, "basis_stage": BASIS_STAGE,
                          "label": "unknown(1)-vs-known(0) answerability",
                          "extract_root": str(root)},
               "canonical_gate": {"present": gate_d is not None,
                                  "best_layer": gate_layer,
                                  "note": ("Qwen3.5-4B cross-family answerability "
                                           "axis; heuristic alignment only")}}

    dirs_by_layer_stage: dict[str, dict[str, np.ndarray]] = {}

    for layer in LAYERS:
        # PCA basis: fit once on the raw-stage activations for this layer.
        Xb, _ = load_stage_layer(caches[BASIS_STAGE], layer)
        pca = PCA(n_components=PCA_DIM, svd_solver="randomized", random_state=SEED)
        pca.fit(Xb)
        components = pca.components_  # (PCA_DIM, 2560)

        layer_out = {"stages": {}}
        dirs_by_layer_stage[layer] = {}
        for s in STAGES:
            X, y = load_stage_layer(caches[s], layer)
            n_known = int((y == 0).sum())
            n_unknown = int((y == 1).sum())
            Xp = pca.transform(X)
            if min(n_known, n_unknown) < MIN_CLASS:
                layer_out["stages"][s] = {"auroc": None, "underpowered": True,
                                          "n_known": n_known, "n_unknown": n_unknown}
                continue
            auroc = cv_auroc(Xp, y)
            d = full_direction(Xp, y, components)
            dirs_by_layer_stage[layer][s] = d
            layer_out["stages"][s] = {"auroc": round(auroc, 4),
                                      "underpowered": False,
                                      "n_known": n_known, "n_unknown": n_unknown}

        # direction rotation cosines (same PCA basis => residual-space comparable)
        dd = dirs_by_layer_stage[layer]
        rot = {}
        seq = [("raw", "cleansft"), ("cleansft", "grpov2"), ("grpov2", "partrue")]
        for a, b in seq:
            if a in dd and b in dd:
                rot[f"{a}->{b}"] = round(cos(dd[a], dd[b]), 4)
        for s in STAGES:
            if s != "grpov2" and s in dd and "grpov2" in dd:
                rot[f"{s}_vs_grpov2"] = round(cos(dd[s], dd["grpov2"]), 4)
        layer_out["direction_cosines"] = rot

        # canonical cross-family gate cosine at matched layer index
        if gate_d is not None:
            gc = {}
            for s in STAGES:
                if s in dd:
                    gc[s] = round(cos(dd[s], gate_d), 4)
            layer_out["canonical_gate_cosine"] = gc

        results["layers"][layer] = layer_out
        print(f"[item9] {layer} "
              + " ".join(f"{s}={layer_out['stages'][s]['auroc']}" for s in STAGES),
              flush=True)

    (out_dir / "diag_item9_caution_timeline.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")

    # markdown table
    lines = ["# Diagnostics item 9 - caution readout across training stages", "",
             "Label: unknown(1) vs known(0) answerability (pool-derived, identical",
             "across stages). Probe: PCA-128 (fit once per layer on raw) then",
             "LogisticRegression(saga, tol=1e-3), 5-fold pooled OOF AUROC.", ""]
    lines.append("## Class balance (per stage)")
    lines.append("")
    lines.append("| stage | rows | known | unknown | underpowered |")
    lines.append("|---|---|---|---|---|")
    for s in STAGES:
        b = balance[s]
        lines.append(f"| {s} | {b['n_rows']} | {b['n_known']} | {b['n_unknown']} "
                     f"| {b['underpowered']} |")
    lines.append("")
    lines.append("## CV AUROC by layer by stage")
    lines.append("")
    lines.append("| layer | raw | cleansft | grpov2 | partrue |")
    lines.append("|---|---|---|---|---|")
    for layer in LAYERS:
        cells = []
        for s in STAGES:
            v = results["layers"][layer]["stages"][s]["auroc"]
            cells.append("underpwr" if v is None else f"{v:.3f}")
        lines.append(f"| {layer} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Direction rotation cosines (same PCA basis)")
    lines.append("")
    lines.append("| layer | raw->cleansft | cleansft->grpov2 | grpov2->partrue |")
    lines.append("|---|---|---|---|")
    for layer in LAYERS:
        rc = results["layers"][layer].get("direction_cosines", {})
        lines.append(f"| {layer} | {rc.get('raw->cleansft','-')} "
                     f"| {rc.get('cleansft->grpov2','-')} "
                     f"| {rc.get('grpov2->partrue','-')} |")
    lines.append("")
    lines.append("## Cosine vs canonical Qwen3.5-4B gate axis (cross-family, heuristic)")
    lines.append("")
    lines.append("| layer | raw | cleansft | grpov2 | partrue |")
    lines.append("|---|---|---|---|---|")
    for layer in LAYERS:
        gc = results["layers"][layer].get("canonical_gate_cosine", {})
        lines.append(f"| {layer} | {gc.get('raw','-')} | {gc.get('cleansft','-')} "
                     f"| {gc.get('grpov2','-')} | {gc.get('partrue','-')} |")
    lines.append("")
    (out_dir / "diag_item9_caution_timeline.md").write_text("\n".join(lines),
                                                            encoding="utf-8")
    print(f"[item9] wrote {out_dir}/diag_item9_caution_timeline.json and .md",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
