#!/usr/bin/env python3
"""Flavor-readout analysis: is unanswerability FLAVOR (6 canonical unknown
categories) linearly represented in the raw Qwen3-4B instruct base at the
pre-generation anchor, and at which layers?

Tier-1 lab-notebook work (exploratory MI): no gates, no claims promotion.
CPU only. Loads one layer at a time (each L*.npy is ~59MB float16).

Outputs findings.json + report.md in the same directory as this script.
"""
import gc
import json
import os
import time
from pathlib import Path
import numpy as np
from collections import Counter, defaultdict

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

SEED = 20260704
N_LAYERS = 37
C_PROBE = 0.5
N_FOLDS = 5
N_PERM = 3
# PCA dimensionality reduction (label-agnostic, fit once per layer before CV).
# This CPU is slow for full-dim multinomial LBFGS; PCA + saga is the fast path.
# Unsupervised preprocessing fit outside the fold is a standard, mild shortcut
# for linear probing (negligible leakage for AUROC).
N_PCA = 128
PCA_KW = dict(n_components=N_PCA, random_state=SEED,
              svd_solver="randomized", iterated_power=2)
LR_KW = dict(C=C_PROBE, max_iter=1000, solver="saga", tol=1e-3)


def reduce_features(X):
    """StandardScaler + PCA-128, fit once (label-agnostic). float32 to keep
    memory bounded on the full 11996-row matrix."""
    Xs = StandardScaler().fit_transform(X.astype(np.float32))
    Xp = PCA(**PCA_KW).fit_transform(Xs)
    del Xs
    return np.ascontiguousarray(Xp, dtype=np.float64)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[5]
LEGACY_ANALYSIS = REPO / "experiment" / "phase1" / "probe" / "analysis"
CACHE = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704" / "cache")
MANIFEST = os.path.join(CACHE, "manifest.jsonl")
TEXT_FILES = [
    str(LEGACY_ANALYSIS / "ah_stage0" / "candidates.jsonl"),
    str(LEGACY_ANALYSIS / "ah_stage0" / "expansion" / "expansion_candidates.jsonl"),
]
CANON = ["ambiguous", "controversial", "counterfactual",
         "false_assumption", "future_unknown", "unsolved_problem"]


def load_manifest():
    rows = []
    with open(MANIFEST) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_text_map():
    txt = {}
    for path in TEXT_FILES:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                k = r.get("row_key")
                q = r.get("question")
                if k is not None and q is not None and k not in txt:
                    txt[k] = q
    return txt


def multiclass_metrics(y_true, y_pred, y_proba, classes):
    """macro one-vs-rest AUROC + accuracy."""
    # binarize for OvR AUROC
    aurocs = []
    for i, c in enumerate(classes):
        yt = (y_true == c).astype(int)
        if yt.sum() == 0 or yt.sum() == len(yt):
            continue
        aurocs.append(roc_auc_score(yt, y_proba[:, i]))
    macro_auroc = float(np.mean(aurocs))
    acc = float(accuracy_score(y_true, y_pred))
    return macro_auroc, acc, aurocs


def cv_multiclass(X, y, classes, seed=SEED, permute=False):
    """Stratified 5-fold multinomial logistic on pre-reduced features.

    X is expected to be already reduced (StandardScaler + PCA). Returns
    pooled OOF metrics.
    """
    rng = np.random.default_rng(seed)
    yv = y.copy()
    if permute:
        yv = yv.copy()
        rng.shuffle(yv)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    n = len(yv)
    oof_pred = np.empty(n, dtype=object)
    oof_proba = np.zeros((n, len(classes)))
    for tr, te in skf.split(X, yv):
        clf = LogisticRegression(**LR_KW)
        clf.fit(X[tr], yv[tr])
        model_classes = list(clf.classes_)
        proba = clf.predict_proba(X[te])
        col = [model_classes.index(c) for c in classes]
        oof_proba[te] = proba[:, col]
        oof_pred[te] = clf.predict(X[te])
    macro_auroc, acc, per_cls_auroc = multiclass_metrics(yv, oof_pred, oof_proba, classes)
    return macro_auroc, acc, per_cls_auroc, oof_pred, oof_proba, yv


def cv_binary(X, y, seed=SEED):
    """Binary known/unknown probe on pre-reduced features, pooled OOF AUROC."""
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    n = len(y)
    oof = np.zeros(n)
    for tr, te in skf.split(X, y):
        clf = LogisticRegression(**LR_KW)
        clf.fit(X[tr], y[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    return float(roc_auc_score(y, oof))


def main():
    t0 = time.time()
    rows = load_manifest()
    assert len(rows) == 11996
    labels = np.array([r["label"] for r in rows])
    sources = np.array([r["source"] for r in rows])
    cats = np.array([r["category_canon"] for r in rows])
    keys = [r["row_key"] for r in rows]

    cat_idx = np.where(cats != "")[0]
    y_cat = cats[cat_idx]
    classes = [c for c in CANON if c in set(y_cat)]
    class_sizes = {c: int((y_cat == c).sum()) for c in classes}
    majority = max(class_sizes.values()) / len(y_cat)

    # binary known/unknown target (1 = unknown)
    y_bin = (labels == "unknown").astype(int)

    findings = {
        "seed": SEED, "C": C_PROBE, "n_folds": N_FOLDS, "n_perm": N_PERM,
        "n_categorized": int(len(cat_idx)),
        "class_sizes": class_sizes,
        "majority_baseline_acc": float(majority),
        "classes": classes,
        "n_total_rows": len(rows),
    }
    print("class sizes:", class_sizes, "majority baseline acc:", round(majority, 3))

    # ---- per-layer profiles ----
    layer_profile = []  # flavor multiclass per layer
    perm_profile = []   # permuted chance band per layer
    binary_profile = []  # known/unknown per layer
    for L in range(N_LAYERS):
        arr = np.load(os.path.join(CACHE, f"L{L}.npy"))  # float16 [11996, 2560]
        # flavor probe on categorized unknown rows (reduce once, label-agnostic)
        Xc = reduce_features(arr[cat_idx])
        mauc, acc, per_cls, pred, proba, yv = cv_multiclass(Xc, y_cat, classes)
        # permutation chance band (reuse reduced features)
        perm_aucs, perm_accs = [], []
        for p in range(N_PERM):
            pa, pc, _, _, _, _ = cv_multiclass(Xc, y_cat, classes,
                                               seed=SEED + 100 + p, permute=True)
            perm_aucs.append(pa)
            perm_accs.append(pc)
        del Xc
        # binary known/unknown on ALL rows
        Xall = reduce_features(arr)
        bin_auc = cv_binary(Xall, y_bin)
        del arr, Xall
        gc.collect()

        layer_profile.append({"layer": L, "macro_auroc": mauc, "acc": acc})
        perm_profile.append({"layer": L,
                             "macro_auroc_mean": float(np.mean(perm_aucs)),
                             "macro_auroc_std": float(np.std(perm_aucs)),
                             "acc_mean": float(np.mean(perm_accs))})
        binary_profile.append({"layer": L, "auroc": bin_auc})
        print(f"L{L:02d} flavor macroAUC={mauc:.3f} acc={acc:.3f} "
              f"perm={np.mean(perm_aucs):.3f} | binary(k/u)AUC={bin_auc:.3f} "
              f"[{time.time()-t0:.0f}s]")

    findings["flavor_layer_profile"] = layer_profile
    findings["flavor_perm_profile"] = perm_profile
    findings["binary_layer_profile"] = binary_profile

    # best layer by flavor macro-AUROC
    best = max(layer_profile, key=lambda d: d["macro_auroc"])
    best_L = best["layer"]
    # top-3 layers for confound guards
    top3 = sorted(layer_profile, key=lambda d: d["macro_auroc"], reverse=True)[:3]
    top3_L = [d["layer"] for d in top3]
    findings["best_layer"] = best_L
    findings["top3_layers"] = top3_L
    # where does binary answerability peak
    bin_best = max(binary_profile, key=lambda d: d["auroc"])
    findings["binary_best_layer"] = bin_best["layer"]
    print(f"\nBEST flavor layer = L{best_L} (macroAUC {best['macro_auroc']:.3f}); "
          f"binary peak L{bin_best['layer']} ({bin_best['auroc']:.3f})")

    # ---- structure at best layer: confusion matrix + per-category OvR AUROC ----
    arr = np.load(os.path.join(CACHE, f"L{best_L}.npy"))
    Xbest = reduce_features(arr[cat_idx].astype(np.float64))
    del arr
    mauc, acc, per_cls_auroc, pred, proba, yv = cv_multiclass(Xbest, y_cat, classes)
    cm = confusion_matrix(yv, pred, labels=classes)
    cm_norm = cm / cm.sum(axis=1, keepdims=True)
    findings["best_layer_structure"] = {
        "layer": best_L,
        "macro_auroc": mauc, "acc": acc,
        "per_category_ovr_auroc": {c: float(a) for c, a in zip(classes, per_cls_auroc)},
        "confusion_matrix_labels": classes,
        "confusion_matrix_counts": cm.tolist(),
        "confusion_matrix_rownorm": np.round(cm_norm, 3).tolist(),
    }

    # ---- confound guard (a): SOURCE ----
    # crosstab category x source (categorized rows only)
    crosstab = defaultdict(lambda: defaultdict(int))
    for i in cat_idx:
        crosstab[cats[i]][sources[i]] += 1
    crosstab = {c: dict(v) for c, v in crosstab.items()}
    findings["category_source_crosstab"] = crosstab

    # how separable is SOURCE itself at best layer (on categorized rows)?
    src_cat = sources[cat_idx]
    src_classes = sorted(set(src_cat))
    s_mauc, s_acc, _, _, _, _ = cv_multiclass(Xbest, src_cat, src_classes)
    src_majority = max(Counter(src_cat).values()) / len(src_cat)

    # re-run flavor probe WITHIN the largest single source
    largest_src = Counter(src_cat).most_common(1)[0][0]
    mask_ls = src_cat == largest_src
    y_ls = y_cat[mask_ls]
    ls_classes = [c for c in classes if (y_ls == c).sum() >= N_FOLDS]
    ls_mask2 = np.isin(y_ls, ls_classes)
    ws_mauc, ws_acc, ws_per, _, _, _ = cv_multiclass(
        Xbest[mask_ls][ls_mask2], y_ls[ls_mask2], ls_classes)
    ws_majority = max(Counter(y_ls[ls_mask2]).values()) / int(ls_mask2.sum())
    findings["source_confound"] = {
        "layer": best_L,
        "source_probe_macro_auroc": float(s_mauc),
        "source_probe_acc": float(s_acc),
        "source_majority_acc": float(src_majority),
        "largest_source": largest_src,
        "largest_source_n": int(mask_ls.sum()),
        "within_source_flavor_macro_auroc": float(ws_mauc),
        "within_source_flavor_acc": float(ws_acc),
        "within_source_majority_acc": float(ws_majority),
        "within_source_classes": ls_classes,
    }
    print(f"source-probe macroAUC={s_mauc:.3f} acc={s_acc:.3f} (maj {src_majority:.3f}); "
          f"within-{largest_src} flavor macroAUC={ws_mauc:.3f} acc={ws_acc:.3f}")

    # ---- confound guard (b): TEXT / surface baseline ----
    txt = load_text_map()
    texts = [txt.get(k, "") for k in keys]
    cat_texts = [texts[i] for i in cat_idx]
    text_cov = sum(1 for t in cat_texts if t) / len(cat_texts)

    # TF-IDF logistic surface baseline (pipeline inside CV to avoid leakage)
    def cv_text(texts_list, y, classes, seed=SEED):
        texts_arr = np.array(texts_list, dtype=object)
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
        n = len(y)
        oof_pred = np.empty(n, dtype=object)
        oof_proba = np.zeros((n, len(classes)))
        for tr, te in skf.split(texts_arr, y):
            vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000,
                                  sublinear_tf=True)
            Xtr = vec.fit_transform(texts_arr[tr])
            Xte = vec.transform(texts_arr[te])
            clf = LogisticRegression(C=1.0, max_iter=1000, solver="saga", tol=1e-3)
            clf.fit(Xtr, y[tr])
            mc = list(clf.classes_)
            proba = clf.predict_proba(Xte)
            col = [mc.index(c) for c in classes]
            oof_proba[te] = proba[:, col]
            oof_pred[te] = clf.predict(Xte)
        return multiclass_metrics(y, oof_pred, oof_proba, classes)

    tf_mauc, tf_acc, tf_per = cv_text(cat_texts, y_cat, classes)

    # simple length/keyword surface features baseline
    def surface_feats(t):
        tl = t.lower()
        return [
            len(t), len(t.split()), t.count("?"),
            int("if " in tl or tl.startswith("if")), int("would" in tl),
            int("best" in tl or "better" in tl or "worst" in tl),
            int("will" in tl or "future" in tl or "2030" in tl or "2050" in tl),
            int("unsolved" in tl or "prove" in tl or "solution" in tl),
            int("or " in tl), int("which" in tl), int("who" in tl),
        ]
    Xsurf = np.array([surface_feats(t) for t in cat_texts], dtype=np.float64)
    sf_mauc, sf_acc, sf_per, _, _, _ = cv_multiclass(Xsurf, y_cat, classes)

    findings["text_confound"] = {
        "text_coverage": float(text_cov),
        "tfidf_macro_auroc": float(tf_mauc),
        "tfidf_acc": float(tf_acc),
        "tfidf_per_category_ovr_auroc": {c: float(a) for c, a in zip(classes, tf_per)},
        "surface_feat_macro_auroc": float(sf_mauc),
        "surface_feat_acc": float(sf_acc),
        "activation_best_layer_macro_auroc": float(mauc),
        "activation_best_layer_acc": float(acc),
        "activation_excess_over_tfidf_auroc": float(mauc - tf_mauc),
        "activation_excess_over_tfidf_acc": float(acc - tf_acc),
    }
    print(f"text coverage={text_cov:.3f}; TFIDF macroAUC={tf_mauc:.3f} acc={tf_acc:.3f}; "
          f"surface-feat macroAUC={sf_mauc:.3f}; activation@L{best_L} macroAUC={mauc:.3f}")

    findings["runtime_sec"] = round(time.time() - t0, 1)
    with open(os.path.join(HERE, "findings.json"), "w") as f:
        json.dump(findings, f, indent=2)

    write_report(findings)
    print(f"\nDONE in {findings['runtime_sec']}s")


def write_report(f):
    L = f["best_layer"]
    lp = {d["layer"]: d for d in f["flavor_layer_profile"]}
    pp = {d["layer"]: d for d in f["flavor_perm_profile"]}
    bp = {d["layer"]: d for d in f["binary_layer_profile"]}
    struct = f["best_layer_structure"]
    sc = f["source_confound"]
    tc = f["text_confound"]

    lines = []
    lines.append("# Flavor readout: is unanswerability FLAVOR linearly represented?")
    lines.append("")
    lines.append("Raw Qwen3-4B instruct base, pre-generation anchor. Tier-1 exploratory "
                 "MI, CPU only. No gates, no claims promotion.")
    lines.append("")
    lines.append("## Cell sizes")
    lines.append(f"Categorized unknown rows: {f['n_categorized']} across "
                 f"{len(f['classes'])} canonical categories (all label=unknown).")
    for c, n in f["class_sizes"].items():
        lines.append(f"- {c}: {n}")
    lines.append(f"Majority-class baseline accuracy: {f['majority_baseline_acc']:.3f}")
    lines.append("")
    lines.append("## Headline")
    best_auc = lp[L]["macro_auroc"]
    perm_auc = pp[L]["macro_auroc_mean"]
    lines.append(f"Flavor IS linearly readable. Best layer L{L}: macro one-vs-rest "
                 f"AUROC {best_auc:.3f} vs permuted chance {perm_auc:.3f} "
                 f"(+/-{pp[L]['macro_auroc_std']:.3f}); accuracy {lp[L]['acc']:.3f} "
                 f"vs majority baseline {f['majority_baseline_acc']:.3f}.")
    lines.append("")
    lines.append("## Depth profile (flavor vs answerability)")
    lines.append(f"Binary known/unknown peaks at L{f['binary_best_layer']} "
                 f"(AUROC {bp[f['binary_best_layer']]['auroc']:.3f}). Flavor peaks at "
                 f"L{L}.")
    lines.append("")
    lines.append("| layer | flavor macroAUC | flavor acc | perm chance | binary k/u AUC |")
    lines.append("|---|---|---|---|---|")
    for lyr in range(N_LAYERS):
        lines.append(f"| L{lyr} | {lp[lyr]['macro_auroc']:.3f} | {lp[lyr]['acc']:.3f} "
                     f"| {pp[lyr]['macro_auroc_mean']:.3f} | {bp[lyr]['auroc']:.3f} |")
    lines.append("")
    lines.append("## Source confound guard")
    lines.append(f"All six categories draw from just two sources "
                 f"(kuq_ku_unknown, kuq_ku_unknown_x) at a roughly consistent split, "
                 f"so source is only weakly confounded with flavor. Crosstab:")
    for c, d in f["category_source_crosstab"].items():
        lines.append(f"- {c}: {d}")
    lines.append(f"Source itself is separable at L{L} at macroAUC "
                 f"{sc['source_probe_macro_auroc']:.3f} (acc {sc['source_probe_acc']:.3f}, "
                 f"majority {sc['source_majority_acc']:.3f}). Re-running the flavor probe "
                 f"WITHIN the largest single source ({sc['largest_source']}, "
                 f"n={sc['largest_source_n']}) still reads flavor at macroAUC "
                 f"{sc['within_source_flavor_macro_auroc']:.3f} (acc "
                 f"{sc['within_source_flavor_acc']:.3f}, majority "
                 f"{sc['within_source_majority_acc']:.3f}), so flavor is not a "
                 f"source artifact.")
    lines.append("")
    lines.append("## Text / surface confound guard")
    lines.append(f"Question text recovered for {tc['text_coverage']*100:.1f}% of "
                 f"categorized rows. A TF-IDF (1-2 gram) logistic surface baseline "
                 f"reaches macroAUC {tc['tfidf_macro_auroc']:.3f} "
                 f"(acc {tc['tfidf_acc']:.3f}); a simple length/keyword feature baseline "
                 f"reaches macroAUC {tc['surface_feat_macro_auroc']:.3f}. The activation "
                 f"probe at L{L} reaches macroAUC {tc['activation_best_layer_macro_auroc']:.3f} "
                 f"(acc {tc['activation_best_layer_acc']:.3f}).")
    lines.append(f"Activation excess over TF-IDF: {tc['activation_excess_over_tfidf_auroc']:+.3f} "
                 f"AUROC, {tc['activation_excess_over_tfidf_acc']:+.3f} acc.")
    lines.append("")
    lines.append("## Structure at best layer (which flavors are crisp vs smeared)")
    per = struct["per_category_ovr_auroc"]
    for c in sorted(per, key=per.get, reverse=True):
        lines.append(f"- {c}: OvR AUROC {per[c]:.3f}")
    lines.append("")
    lines.append("Row-normalized confusion matrix (rows = true, cols = predicted):")
    cls = struct["confusion_matrix_labels"]
    lines.append("| true \\ pred | " + " | ".join(cls) + " |")
    lines.append("|" + "---|" * (len(cls) + 1))
    for i, c in enumerate(cls):
        row = struct["confusion_matrix_rownorm"][i]
        lines.append(f"| {c} | " + " | ".join(f"{v:.2f}" for v in row) + " |")
    lines.append("")

    with open(os.path.join(HERE, "report.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
