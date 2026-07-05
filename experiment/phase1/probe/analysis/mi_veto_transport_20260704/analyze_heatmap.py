"""TEST 4: position x layer transfer heatmap.

For each layer in a grid, and each construct:
  (a) answerability on W (known vs hallucination)
  (b) correctness on S (correct vs wrong)
Fit a fresh PCA-128+saga probe at PRE and at POST (in-position CV AUROC).
Then evaluate each fitted probe (fit on ALL of one position) at the OTHER
position (cross-position transfer AUROC, out-of-position so not CV-circular).

Reports where post-beats-pre emerges in depth, and where the pre-fit axis
stops transferring to post.
"""
import os, json
import numpy as np
from sklearn.metrics import roc_auc_score
import vt_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
LAYERS = [8, 14, 18, 20, 22, 26, 30, 34]


def run_construct(name, d, rows, y):
    print(f"=== {name} ===", flush=True)
    # Load all needed layers per position (one pass each)
    Xpre, mpre = L.load_all_layers(d, rows, "pre", LAYERS)
    Xpost, mpost = L.load_all_layers(d, rows, "post", LAYERS)
    assert mpre.all() and mpost.all()
    res = {}
    for lay in LAYERS:
        Xp = Xpre[lay]
        Xq = Xpost[lay]
        # in-position CV
        auc_pre, sd_pre, _ = L.cv_auroc(Xp, y, layer_seed=lay)
        auc_post, sd_post, _ = L.cv_auroc(Xq, y, layer_seed=lay)
        # cross-position transfer (fit on ALL of one position, eval other)
        fp_pre = L.fit_full_probe(Xp, y, seed=lay)
        fp_post = L.fit_full_probe(Xq, y, seed=lay)
        s_prefit_at_post = L.score_full_probe(fp_pre, Xq)
        s_postfit_at_pre = L.score_full_probe(fp_post, Xp)
        auc_prefit_at_post = float(roc_auc_score(y, s_prefit_at_post))
        auc_postfit_at_pre = float(roc_auc_score(y, s_postfit_at_pre))
        res[lay] = {
            "cv_pre": [auc_pre, sd_pre],
            "cv_post": [auc_post, sd_post],
            "post_minus_pre": auc_post - auc_pre,
            "prefit_axis_at_post": auc_prefit_at_post,
            "postfit_axis_at_pre": auc_postfit_at_pre,
        }
        print(lay, "cv_pre", round(auc_pre, 3), "cv_post", round(auc_post, 3),
              "d", round(auc_post - auc_pre, 3),
              "prefit@post", round(auc_prefit_at_post, 3),
              "postfit@pre", round(auc_postfit_at_pre, 3), flush=True)
    return res


findings = {"layers": LAYERS}

# (a) answerability on W
rowsW = L.load_rows(L.W_DIR)
yW = np.array([1 if r["label"] == "known" else 0 for r in rowsW])
findings["answerability_W"] = run_construct("answerability_W (known vs unknown)", L.W_DIR, rowsW, yW)

# (b) correctness on S
rowsS = L.load_rows(L.S_DIR)
yS = np.array([1 if r["correct"] else 0 for r in rowsS])
findings["correctness_S"] = run_construct("correctness_S (correct vs wrong)", L.S_DIR, rowsS, yS)

with open(os.path.join(OUT, "findings_heatmap.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings_heatmap.json", flush=True)
