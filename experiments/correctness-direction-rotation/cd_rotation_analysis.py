#!/usr/bin/env python3
"""Correctness-direction rotation (CD) — CPU-only probe-fit + rotation-cosine
analysis across raw -> clean-SFT -> GRPO-v2 -> GRPO-par-true.

Pre-registered in experiments/correctness-direction-rotation/AMENDMENT.md
(SIGNED 2026-07-19); method mirrors
experiments/diag-item9-caution-assembly-timeline/diag_item9_caution_timeline.py
EXACTLY (SEED/PCA_DIM=128/N_FOLDS=5/MIN_CLASS=30, PCA-128 fit once per layer on
the RAW stage's activations reused for every stage, LogisticRegression(saga,
tol=1e-3) in PCA space, coef mapped to residual space, unit-norm, 5-fold
pooled OOF AUROC, consecutive-stage + vs-grpov2 cosines) with the
correctness-specific differences the AMENDMENT states:

  - Labels are per-stage forced-best-guess correct(1)/wrong(0) (not the
    pool-derived known/unknown label item9 used) — each stage's population,
    correct/wrong split, and post-gen tensors differ by construction (the
    confound accepted at sign, bounded by the split-half control below).
  - Position is POST-GENERATION ONLY (the dial's native position); item9's
    canonical cross-family Qwen3.5-4B gate-axis cosine is NOT computed here
    (out of scope for this cell's AMENDMENT/gates.yaml — CD tracks the
    correctness direction against itself across stages, not against an
    unrelated cross-family answerability axis).
  - Two additional CPU-only controls the AMENDMENT pre-registers:
      1. split-half noise floor: the grpov2 correctness direction fit on two
         random stratified halves (in the SAME raw-fit PCA basis), reported
         as the within-stage noise floor a real rotation must sit below.
      2. Instruct(S)->grpov2(T) bracket: a SEPARATE PCA basis fit on the
         Instruct-base (S) stage2 tensors, S and grpov2(T) directions fit in
         that basis, cosine reported (matches the exact checkpoints of the
         0.679 cold-transfer secondary reading; reported, not gated).

Reads four (or five, incl. the S bracket input) stage directories of
`rows.jsonl` + `<safe_key>__post.safetensors` (produced by
cd_stage_extract_gen.py for raw/cleansft/partrue, reused unchanged from
Amendment T for grpov2, reused unchanged from Amendment S for the bracket).

Outputs `cd_rotation_timeline.json` + `.md` (diag_item9 committed shape) plus
per-stage ID-manifests (row_key + label only, no text) under --out-dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from safetensors import safe_open
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SEED = 20260719          # cell.yaml `seed`
PCA_DIM = 128
N_FOLDS = 5
MIN_CLASS = 30
LAYERS = [f"L{i}" for i in range(37)]     # L0..L36
STAGES = ["raw", "cleansft", "grpov2", "partrue"]
BASIS_STAGE = "raw"       # PCA basis fit once per layer on this stage's union
GATE_LAYERS = ["L19", "L20", "L21", "L22", "L23", "L24"]   # CD-G1 window


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8")
            if ln.strip()]


def safe_key_for(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_")


def build_stage_cache(stage_dir: Path, cache_path: Path) -> dict:
    """Read rows.jsonl + <safe_key>__post.safetensors ONCE, stack into one
    .npz: arr[layer, row, 2560] (float32), y[row] correct=1/wrong=0,
    row_keys[row]. Only rows with a resolved label ('correct'/'wrong') and an
    on-disk post tensor are included (unanswered rows are excluded from the
    fit, matching the S/T convention).
    """
    if cache_path.exists():
        data = np.load(cache_path, allow_pickle=True)
        return {"arr": data["arr"], "y": data["y"], "keys": data["keys"]}
    rows = load_jsonl(stage_dir / "rows.jsonl")
    kept = []
    for r in rows:
        if r.get("label") not in ("correct", "wrong"):
            continue
        sk = safe_key_for(r["row_key"])
        tp = stage_dir / f"{sk}__post.safetensors"
        if not tp.exists():
            continue
        kept.append((r, sk, tp))
    n = len(kept)
    if n == 0:
        raise RuntimeError(f"no labeled+tensor rows found under {stage_dir}")
    arr = np.empty((len(LAYERS), n, 2560), dtype=np.float32)
    y = np.empty(n, dtype=np.int64)
    keys = []
    for i, (r, sk, tp) in enumerate(kept):
        with safe_open(str(tp), framework="np") as h:
            for li, layer in enumerate(LAYERS):
                arr[li, i, :] = h.get_tensor(layer)
        y[i] = 1 if r["label"] == "correct" else 0
        keys.append(r["row_key"])
    np.savez(cache_path, arr=arr, y=y, keys=np.array(keys))
    return {"arr": arr, "y": y, "keys": np.array(keys)}


def load_layer(cache: dict, layer: str) -> tuple[np.ndarray, np.ndarray]:
    li = LAYERS.index(layer)
    return cache["arr"][li].astype(np.float64), cache["y"]


def cv_auroc(Xp: np.ndarray, y: np.ndarray) -> float:
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
    sc = StandardScaler().fit(Xp)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000,
                             random_state=SEED)
    clf.fit(sc.transform(Xp), y)
    coef_pca = clf.coef_[0] / sc.scale_
    d = coef_pca @ components
    n = np.linalg.norm(d)
    return d / n if n else d


def cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def mean_over(rc: dict, key: str, layers: list[str]) -> float | None:
    vals = [rc[l][key] for l in layers if l in rc and rc[l].get(key) is not None]
    return float(np.mean(vals)) if vals else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--cleansft-dir", required=True)
    ap.add_argument("--partrue-dir", required=True)
    ap.add_argument("--grpov2-dir", required=True,
                    help="Amendment T stage2 reuse dir (unchanged)")
    ap.add_argument("--s-dir", required=True,
                    help="Amendment S stage2 dir (Instruct base; bracket input)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    stage_dirs = {
        "raw": Path(args.raw_dir), "cleansft": Path(args.cleansft_dir),
        "grpov2": Path(args.grpov2_dir), "partrue": Path(args.partrue_dir),
    }

    caches = {}
    for s, d in stage_dirs.items():
        cp = cache_dir / f"cache_{s}.npz"
        caches[s] = build_stage_cache(d, cp)
        print(f"[cd-analysis] cache {s}: arr={caches[s]['arr'].shape} "
              f"n_correct={int((caches[s]['y']==1).sum())} "
              f"n_wrong={int((caches[s]['y']==0).sum())}", flush=True)
    s_cache = build_stage_cache(Path(args.s_dir), cache_dir / "cache_s.npz")
    print(f"[cd-analysis] cache s(bracket): arr={s_cache['arr'].shape} "
          f"n_correct={int((s_cache['y']==1).sum())} "
          f"n_wrong={int((s_cache['y']==0).sum())}", flush=True)

    balance = {}
    for s in STAGES:
        y = caches[s]["y"]
        n_c, n_w = int((y == 1).sum()), int((y == 0).sum())
        balance[s] = {"n_rows": int(len(y)), "n_correct": n_c, "n_wrong": n_w,
                      "cd_g0_floor_150_150": bool(n_c >= 150 and n_w >= 150)}
    y_s = s_cache["y"]
    balance["s_bracket_input"] = {
        "n_rows": int(len(y_s)), "n_correct": int((y_s == 1).sum()),
        "n_wrong": int((y_s == 0).sum()),
    }

    # Per-stage ID-manifests (row_key + label only; no question/answer/alias
    # text, no token ids, no hidden states).
    for s, d in stage_dirs.items():
        rows = load_jsonl(d / "rows.jsonl")
        manifest = [{"row_key": r["row_key"], "label": r.get("label")}
                    for r in rows if r.get("label") in ("correct", "wrong")]
        (out_dir / f"id_manifest_{s}.json").write_text(
            json.dumps({"stage": s, "n_rows": len(manifest), "rows": manifest},
                       indent=2), encoding="utf-8")

    results = {"layers": {}, "class_balance": balance,
               "config": {"seed": SEED, "pca_dim": PCA_DIM, "n_folds": N_FOLDS,
                          "min_class": MIN_CLASS, "basis_stage": BASIS_STAGE,
                          "label": "correct(1)-vs-wrong(0), per-stage forced-best-guess",
                          "position": "post_generation_only",
                          "gate_layers_L19_L24": GATE_LAYERS}}

    dirs_by_layer_stage: dict[str, dict[str, np.ndarray]] = {}
    split_half_by_layer: dict[str, float | None] = {}
    bracket_by_layer: dict[str, float | None] = {}

    for layer in LAYERS:
        # --- shared basis: PCA fit once on raw-stage post-gen activations ---
        Xb, _ = load_layer(caches[BASIS_STAGE], layer)
        pca = PCA(n_components=PCA_DIM, svd_solver="randomized", random_state=SEED)
        pca.fit(Xb)
        components = pca.components_

        layer_out = {"stages": {}}
        dirs_by_layer_stage[layer] = {}
        for s in STAGES:
            X, y = load_layer(caches[s], layer)
            n_c, n_w = int((y == 1).sum()), int((y == 0).sum())
            Xp = pca.transform(X)
            if min(n_c, n_w) < MIN_CLASS:
                layer_out["stages"][s] = {"auroc": None, "underpowered": True,
                                          "n_correct": n_c, "n_wrong": n_w}
                continue
            auroc = cv_auroc(Xp, y)
            d = full_direction(Xp, y, components)
            dirs_by_layer_stage[layer][s] = d
            layer_out["stages"][s] = {"auroc": round(auroc, 4),
                                      "underpowered": False,
                                      "n_correct": n_c, "n_wrong": n_w}

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

        # --- split-half noise floor (grpov2, same raw-fit PCA basis) ---
        split_half = None
        if "grpov2" in dd:
            Xg, yg = load_layer(caches["grpov2"], layer)
            idx = np.arange(len(yg))
            try:
                ia, ib = train_test_split(idx, test_size=0.5, random_state=SEED,
                                          stratify=yg)
                Xpg = pca.transform(Xg)
                ya, yb = yg[ia], yg[ib]
                if min((ya == 1).sum(), (ya == 0).sum()) >= MIN_CLASS and \
                   min((yb == 1).sum(), (yb == 0).sum()) >= MIN_CLASS:
                    da = full_direction(Xpg[ia], ya, components)
                    db = full_direction(Xpg[ib], yb, components)
                    split_half = round(cos(da, db), 4)
            except ValueError:
                split_half = None
        layer_out["split_half_cosine_grpov2"] = split_half
        split_half_by_layer[layer] = split_half

        results["layers"][layer] = layer_out
        print(f"[cd-analysis] {layer} "
              + " ".join(f"{s}={layer_out['stages'][s]['auroc']}" for s in STAGES)
              + f" split_half={split_half}", flush=True)

    # --- Instruct(S)->grpov2(T) bracket: OWN PCA basis fit on S per layer ---
    for layer in LAYERS:
        Xs, ys = load_layer(s_cache, layer)
        n_cs, n_ws = int((ys == 1).sum()), int((ys == 0).sum())
        pca_s = PCA(n_components=PCA_DIM, svd_solver="randomized", random_state=SEED)
        pca_s.fit(Xs)
        comp_s = pca_s.components_
        Xg, yg = load_layer(caches["grpov2"], layer)
        n_cg, n_wg = int((yg == 1).sum()), int((yg == 0).sum())
        bracket = None
        if min(n_cs, n_ws) >= MIN_CLASS and min(n_cg, n_wg) >= MIN_CLASS:
            d_s = full_direction(pca_s.transform(Xs), ys, comp_s)
            d_t = full_direction(pca_s.transform(Xg), yg, comp_s)
            bracket = round(cos(d_s, d_t), 4)
        bracket_by_layer[layer] = bracket
        results["layers"][layer]["instruct_to_grpov2_bracket_cosine"] = bracket

    # --- summary block (reported straight; adjudication is the lead's) ---
    rc_by_layer = {l: results["layers"][l]["direction_cosines"] for l in LAYERS}
    raw_cleansft_mean = mean_over(rc_by_layer, "raw->cleansft", GATE_LAYERS)
    cleansft_grpov2_mean = mean_over(rc_by_layer, "cleansft->grpov2", GATE_LAYERS)
    grpov2_partrue_mean = mean_over(rc_by_layer, "grpov2->partrue", GATE_LAYERS)
    split_half_mean = float(np.mean([v for l, v in split_half_by_layer.items()
                                     if l in GATE_LAYERS and v is not None])) \
        if any(split_half_by_layer.get(l) is not None for l in GATE_LAYERS) else None
    bracket_mean = float(np.mean([v for l, v in bracket_by_layer.items()
                                  if l in GATE_LAYERS and v is not None])) \
        if any(bracket_by_layer.get(l) is not None for l in GATE_LAYERS) else None
    best_layer_auroc = {}
    for s in STAGES:
        vals = [(l, results["layers"][l]["stages"][s]["auroc"]) for l in LAYERS
                if results["layers"][l]["stages"][s]["auroc"] is not None]
        if vals:
            bl, ba = max(vals, key=lambda t: t[1])
            best_layer_auroc[s] = {"layer": bl, "auroc": ba,
                                   "cd_g2_flag_below_0_60": bool(ba < 0.60)}
        else:
            best_layer_auroc[s] = {"layer": None, "auroc": None,
                                   "cd_g2_flag_below_0_60": True}

    results["summary"] = {
        "raw_to_cleansft_cosine_mean_L19_L24": raw_cleansft_mean,
        "cleansft_to_grpov2_cosine_mean_L19_L24": cleansft_grpov2_mean,
        "grpov2_to_partrue_cosine_mean_L19_L24": grpov2_partrue_mean,
        "split_half_noise_floor_mean_L19_L24": split_half_mean,
        "instruct_to_grpov2_bracket_mean_L19_L24": bracket_mean,
        "best_layer_auroc_by_stage": best_layer_auroc,
        "reported_straight_no_verdict": True,
    }

    (out_dir / "cd_rotation_timeline.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")

    lines = ["# Correctness-direction rotation across training stages", "",
             "Label: correct(1) vs wrong(0), per-stage forced-best-guess",
             "generation (Cheng alias scorer). Probe: PCA-128 (fit once per",
             "layer on raw) then LogisticRegression(saga, tol=1e-3), 5-fold",
             "pooled OOF AUROC. Position: post-generation only.", ""]
    lines.append("## Class balance (per stage)")
    lines.append("")
    lines.append("| stage | rows | correct | wrong | CD-G0 (>=150/150) |")
    lines.append("|---|---|---|---|---|")
    for s in STAGES:
        b = balance[s]
        lines.append(f"| {s} | {b['n_rows']} | {b['n_correct']} | {b['n_wrong']} "
                     f"| {b['cd_g0_floor_150_150']} |")
    b = balance["s_bracket_input"]
    lines.append(f"| s (bracket input) | {b['n_rows']} | {b['n_correct']} | "
                 f"{b['n_wrong']} | n/a (not gated) |")
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
    lines.append("## Direction rotation cosines (shared PCA basis, fit on raw)")
    lines.append("")
    lines.append("| layer | raw->cleansft | cleansft->grpov2 | grpov2->partrue | split-half floor (grpov2) |")
    lines.append("|---|---|---|---|---|")
    for layer in LAYERS:
        rc = results["layers"][layer]["direction_cosines"]
        sh = results["layers"][layer]["split_half_cosine_grpov2"]
        lines.append(f"| {layer} | {rc.get('raw->cleansft','-')} "
                     f"| {rc.get('cleansft->grpov2','-')} "
                     f"| {rc.get('grpov2->partrue','-')} | {sh if sh is not None else '-'} |")
    lines.append("")
    lines.append("## Instruct(S) -> grpov2(T) bracket (own PCA basis fit on S; reported, not gated)")
    lines.append("")
    lines.append("| layer | bracket cosine |")
    lines.append("|---|---|")
    for layer in LAYERS:
        v = results["layers"][layer]["instruct_to_grpov2_bracket_cosine"]
        lines.append(f"| {layer} | {v if v is not None else '-'} |")
    lines.append("")
    lines.append("## Summary (L19-L24 means; reported straight, no verdict)")
    lines.append("")
    for k, v in results["summary"].items():
        if k in ("best_layer_auroc_by_stage", "reported_straight_no_verdict"):
            continue
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("### Best-layer OOF AUROC by stage (CD-G2 readout sanity)")
    lines.append("")
    lines.append("| stage | best layer | AUROC | CD-G2 flag (<0.60) |")
    lines.append("|---|---|---|---|")
    for s in STAGES:
        v = best_layer_auroc[s]
        lines.append(f"| {s} | {v['layer']} | {v['auroc']} | {v['cd_g2_flag_below_0_60']} |")
    lines.append("")
    (out_dir / "cd_rotation_timeline.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[cd-analysis] wrote {out_dir}/cd_rotation_timeline.json and .md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
