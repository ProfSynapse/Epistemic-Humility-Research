#!/usr/bin/env python3
"""Interactive dashboard for mechinterp SAE outputs.

A *visualization* over already-computed artifacts. It reads no model and runs no
SAE; it renders the aggregated outputs of the ``mechinterp_sae_*`` scripts. Four
surfaces, auto-discovered under the probe tree and shown as tabs:

* **Feature contrasts** -- per-feature *known vs unknown* and *behavior*
  contrasts with top-activating example questions
  (``sae_feature_analysis`` / ``sae_behavior_feature_analysis``).
* **Training sweep** -- reconstruction loss / sparsity across the topk & L1
  training pilots (``sae_runs``): curves + the sparsity-fidelity tradeoff.
* **Directions** -- pairwise cosine similarity of the exported feature decoder
  vectors + catalog (``sae_feature_directions``).
* **Composites** -- provenance catalog of the combined steering vectors
  (``sae_feature_composites``).

The SAE is example-level (one pooled delta vector per question), so unlike
Neuronpedia / sae_dashboard there is no token axis. This borrows their visual
vocabulary but is faithful to that shape.

Usage
-----
    marimo edit experiments/common/mechinterp/sae_dashboard.py     # interactive dev
    marimo run  experiments/common/mechinterp/sae_dashboard.py     # app server
    marimo export html experiments/common/mechinterp/sae_dashboard.py \
        -o archive/experiment/phase1/probe/sae_dashboard.html        # static snapshot

NOTICE: exploratory pilot, not Phase 1 headline evidence and not causal.
"""

import marimo

__generated_with = "0.23.12"
app = marimo.App(width="full")


@app.cell
def _():
    import ast
    import json
    import re
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    return Path, ast, go, json, mo, np, pd, px, re


@app.cell
def _(Path, json, pd, re):
    # --- Roots ---------------------------------------------------------------
    REPO_ROOT = Path(__file__).resolve().parents[3]
    PROBE_ROOT = REPO_ROOT / "archive/experiment/phase1/probe"

    def layer_of(label: str):
        m = re.search(r"_l(\d+)", label)
        return int(m.group(1)) if m else None

    def arm_of(label: str):
        m = re.search(r"(sft_[a-z0-9]+)", label)
        return m.group(1) if m else label

    # --- Contrast families (feature / behavior) ------------------------------
    _FAMILIES = {
        "feature": {
            "subdir": "sae_feature_analysis",
            "ranking": "feature_rankings.csv",
            "examples": "top_feature_examples.json",
            "examples_key": "top_feature_examples",
        },
        "behavior": {
            "subdir": "sae_behavior_feature_analysis",
            "ranking": "behavior_feature_rankings.csv",
            "examples": "top_behavior_feature_examples.json",
            "examples_key": "top_behavior_feature_examples",
        },
    }

    def discover_candidates(root: Path) -> dict:
        cands: dict = {}
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for fam, spec in _FAMILIES.items():
                base = model_dir / spec["subdir"]
                if not base.is_dir():
                    continue
                for csv in sorted(base.rglob(spec["ranking"])):
                    cdir = csv.parent
                    cid = f"{fam} · {model_dir.name} · {cdir.name}"
                    cands[cid] = {
                        "family": fam, "model": model_dir.name, "label": cdir.name,
                        "layer": layer_of(cdir.name), "dir": cdir,
                        "ranking_path": csv, "examples_path": cdir / spec["examples"],
                        "summary_path": cdir / "summary.json",
                        "examples_key": spec["examples_key"],
                    }
        return cands

    def load_summary(meta):
        p = meta["summary_path"]; return json.loads(p.read_text()) if p.exists() else {}
    def load_ranking(meta):
        return pd.read_csv(meta["ranking_path"])
    def load_examples(meta):
        p = meta["examples_path"]
        if not p.exists():
            return {}
        raw = json.loads(p.read_text())
        return raw.get(meta["examples_key"], raw)

    CANDIDATES = discover_candidates(PROBE_ROOT)
    return (
        CANDIDATES, PROBE_ROOT, REPO_ROOT, arm_of, layer_of,
        load_examples, load_ranking, load_summary,
    )


@app.cell
def _(PROBE_ROOT, REPO_ROOT, arm_of, json, np, pd):
    # --- Discovery for training / directions / composites --------------------
    def discover_training(root):
        rows, hist = [], []
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            base = model_dir / "sae_runs"
            if not base.is_dir():
                continue
            for mfile in sorted(base.rglob("metrics.json")):
                try:
                    m = json.loads(mfile.read_text())
                except Exception:
                    continue
                pilot = mfile.parent.parent.name
                tag = pilot.replace("mechinterp_selfaware_delta_sae_pilot", "").lstrip("_") or "base"
                cand = m.get("candidate_label", mfile.parent.name)
                arm = arm_of(cand)
                run_label = f"{tag} · {arm}"
                tr, va = m.get("train", {}), m.get("validation", {})
                rows.append({
                    "run": run_label, "pilot": tag, "arm": arm, "candidate": cand,
                    "activation": m.get("activation"), "top_k": m.get("top_k"),
                    "l1": m.get("l1_coefficient"), "epochs": m.get("epochs"),
                    "train_mse": tr.get("mse"), "val_mse": va.get("mse"),
                    "val_code_density": va.get("code_density"),
                    "val_mean_active": va.get("mean_active_features"),
                })
                hfile = mfile.parent / "training_history.json"
                if hfile.exists():
                    try:
                        h = json.loads(hfile.read_text()).get("history", [])
                    except Exception:
                        h = []
                    for e in h:
                        hist.append({
                            "run": run_label, "pilot": tag, "arm": arm,
                            "epoch": e.get("epoch"),
                            "train_mse": e.get("train_mse"),
                            "val_mse": e.get("validation_mse"),
                        })
        return pd.DataFrame(rows), pd.DataFrame(hist)

    def discover_direction_groups(root):
        groups = {}
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            base = model_dir / "sae_feature_directions"
            if not base.is_dir():
                continue
            for csv in sorted(base.glob("*/sae_feature_directions.csv")):
                groups[f"{model_dir.name} · {csv.parent.name}"] = csv
        return groups

    def load_direction_vectors(csv_path):
        """Return (catalog_df, labels, cosine_matrix) for a directions group."""
        from safetensors.numpy import load_file
        cat = pd.read_csv(csv_path)
        cat = cat[cat.get("status", "ok") == "ok"] if "status" in cat else cat
        vecs, labels, keep = [], [], []
        for _, r in cat.iterrows():
            vpath = REPO_ROOT / str(r["vector_file"])
            if not vpath.exists():
                continue
            try:
                arr = load_file(vpath)[r.get("tensor_key", "direction")]
            except Exception:
                continue
            vecs.append(np.asarray(arr, dtype=np.float64))
            labels.append(f"f{int(r['feature'])} ({r.get('feature_skew_label','?')})")
            keep.append(r)
        if not vecs:
            return cat, [], np.zeros((0, 0))
        M = np.vstack(vecs)
        n = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
        cos = n @ n.T
        return pd.DataFrame(keep), labels, cos

    def discover_composites(root):
        frames = []
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            base = model_dir / "sae_feature_composites"
            if not base.is_dir():
                continue
            for csv in sorted(base.glob("*/sae_feature_composite_directions.csv")):
                try:
                    frames.append(pd.read_csv(csv))
                except Exception:
                    pass
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    TRAIN_SUMMARY, TRAIN_HISTORY = discover_training(PROBE_ROOT)
    DIRECTION_GROUPS = discover_direction_groups(PROBE_ROOT)
    COMPOSITES = discover_composites(PROBE_ROOT)
    return (
        COMPOSITES, DIRECTION_GROUPS, TRAIN_HISTORY, TRAIN_SUMMARY,
        load_direction_vectors,
    )


# ===========================================================================
#  TAB 1 — Feature contrasts
# ===========================================================================
@app.cell
def _(CANDIDATES, mo):
    _fams = {"feature": "known vs unknown", "behavior": "behavior contrasts"}
    _present = sorted({m["family"] for m in CANDIDATES.values()})
    family = mo.ui.dropdown(
        options={f"{_fams.get(f, f)}  ({f})": f for f in _present},
        value=(f"{_fams.get(_present[0], _present[0])}  ({_present[0]})" if _present else None),
        label="**Analysis family**",
    )
    return (family,)


@app.cell
def _(CANDIDATES, family, mo):
    _opts = {cid: cid for cid, m in CANDIDATES.items() if m["family"] == family.value}
    candidate = mo.ui.dropdown(
        options=_opts, value=(next(iter(_opts)) if _opts else None),
        label="**Candidate** (arm · layer · width)",
    )
    return (candidate,)


@app.cell
def _(CANDIDATES, candidate, family, load_ranking, mo):
    contrast = None
    if candidate.value is not None and family.value == "behavior":
        _df = load_ranking(CANDIDATES[candidate.value])
        _contrasts = sorted(_df["contrast"].dropna().unique().tolist())
        contrast = mo.ui.dropdown(
            options={c: c for c in _contrasts},
            value=(_contrasts[0] if _contrasts else None),
            label="**Behavior contrast**",
        )
    return (contrast,)


@app.cell
def _(CANDIDATES, candidate, contrast, family, load_examples, load_ranking, pd):
    def build_view():
        if candidate.value is None:
            return None
        meta = CANDIDATES[candidate.value]
        df = load_ranking(meta)
        ex = load_examples(meta)
        if family.value == "feature":
            side_a, side_b = "known", "unknown"
            norm = pd.DataFrame({
                "feature": df["feature"].astype(int),
                "mean_a": df["known_mean"], "mean_b": df["unknown_mean"],
                "freq_a": df["known_activation_frequency"],
                "freq_b": df["unknown_activation_frequency"],
                "mean_diff": df["mean_diff_unknown_minus_known"],
                "cohen_d": df["cohen_d_unknown_minus_known"],
                "abs_cohen_d": df["abs_cohen_d"],
                "max_activation": df["max_activation"], "active_count": df["active_count"],
            })
            ex_for = lambda feat: {"single": ex.get(str(feat), [])}
        else:
            sel = df[df["contrast"] == (contrast.value if contrast is not None else None)]
            side_a = sel["negative_label"].iloc[0] if len(sel) else "negative"
            side_b = sel["positive_label"].iloc[0] if len(sel) else "positive"
            norm = pd.DataFrame({
                "feature": sel["feature"].astype(int),
                "mean_a": sel["negative_mean"], "mean_b": sel["positive_mean"],
                "freq_a": sel["negative_activation_frequency"],
                "freq_b": sel["positive_activation_frequency"],
                "mean_diff": sel["mean_diff_positive_minus_negative"],
                "cohen_d": sel["cohen_d_positive_minus_negative"],
                "abs_cohen_d": sel["abs_cohen_d"],
                "max_activation": sel["max_activation"], "active_count": sel["active_count"],
            })
            _c = contrast.value if contrast is not None else None
            _by = ex.get(_c, {}) if _c else {}
            ex_for = lambda feat: {
                side_b: _by.get(str(feat), {}).get("positive", []),
                side_a: _by.get(str(feat), {}).get("negative", []),
            }
        norm = norm.sort_values("abs_cohen_d", ascending=False).reset_index(drop=True)
        return {"meta": meta, "norm": norm, "side_a": side_a, "side_b": side_b, "ex_for": ex_for}

    view = build_view()
    return (view,)


@app.cell
def _(candidate, load_summary, mo, view):
    if view is None:
        contrast_header = mo.md("_No SAE contrast candidates discovered under the probe tree._")
    else:
        s = load_summary(view["meta"]); m = view["meta"]
        contrast_header = mo.md(
            f"""### {candidate.value}

**model** `{m['model']}` · **layer** `{m['layer']}` · **axis** `{view['side_a']}` → `{view['side_b']}`

| dictionary_size | top_k | activation | mean_active_features | rows |
|---|---|---|---|---|
| {s.get('dictionary_size','—')} | {s.get('top_k','—')} | `{s.get('activation','—')}` | {round(s.get('mean_active_features',0),2) if s.get('mean_active_features') else '—'} | {s.get('row_count','—')} |
"""
        )
    return (contrast_header,)


@app.cell
def _(go, mo, view):
    if view is None:
        contrast_volcano = mo.md("")
    else:
        d = view["norm"]
        fig = go.Figure(go.Scatter(
            x=d["mean_diff"], y=d["abs_cohen_d"], mode="markers",
            marker=dict(
                size=8 + 14 * (d["max_activation"] / max(d["max_activation"].max(), 1e-9)),
                color=d["cohen_d"], colorscale="RdBu", cmid=0, showscale=True,
                colorbar=dict(title="Cohen's d"), line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
            ),
            text=[f"feature {int(f)}" for f in d["feature"]],
            hovertemplate="%{text}<br>mean_diff=%{x:.3f}<br>|d|=%{y:.3f}<extra></extra>",
        ))
        fig.add_vline(x=0, line_width=1, line_dash="dot", line_color="gray")
        fig.update_layout(
            title=f"Feature map — x: mean_diff ({view['side_b']}−{view['side_a']}), y: |Cohen's d|, size: max act",
            xaxis_title=f"← {view['side_a']}   mean_diff   {view['side_b']} →",
            yaxis_title="|Cohen's d|", height=400, template="plotly_white",
            margin=dict(l=60, r=20, t=60, b=50),
        )
        contrast_volcano = mo.ui.plotly(fig)
    return (contrast_volcano,)


@app.cell
def _(mo, view):
    if view is None:
        feat_table = mo.ui.table(data=[], selection="single")
    else:
        _t = view["norm"].round(
            {"mean_a": 3, "mean_b": 3, "freq_a": 3, "freq_b": 3,
             "mean_diff": 3, "cohen_d": 3, "abs_cohen_d": 3, "max_activation": 2}
        ).rename(columns={
            "mean_a": f"mean[{view['side_a']}]", "mean_b": f"mean[{view['side_b']}]",
            "freq_a": f"freq[{view['side_a']}]", "freq_b": f"freq[{view['side_b']}]",
        })
        feat_table = mo.ui.table(
            data=_t, selection="single", page_size=12,
            label="**Features** (ranked by |Cohen's d| — select a row)",
        )
    return (feat_table,)


@app.cell
def _(feat_table, mo, view):
    def _chip(txt, bg):
        return (f"<span style='background:{bg};border-radius:6px;padding:1px 6px;"
                f"margin:0 3px;font-size:11px;white-space:nowrap'>{txt}</span>")

    def _block(title, items):
        if not items:
            return f"**{title}** — _no examples_\n"
        out = [f"**{title}**  ({len(items)} shown)\n"]
        for it in items[:8]:
            c = _chip(it.get("label", "?"), "#e3ecff")
            if "correct" in it:
                c += _chip("correct" if it.get("correct") else "wrong",
                           "#d7f5dd" if it.get("correct") else "#ffe0e0")
            if it.get("refused"):
                c += _chip("refused", "#fff0d0")
            if it.get("stated_confidence") is not None:
                c += _chip(f"conf {it['stated_confidence']}", "#eee")
            for st in (it.get("strata") or [])[:3]:
                c += _chip(st, "#f0e6ff")
            q = str(it.get("question", "")).replace("|", "\\|")
            out.append(f"- `{it.get('activation', 0):.2f}`  {q}  {c}")
        return "\n".join(out) + "\n"

    _sel = feat_table.value
    if view is None:
        contrast_detail = mo.md("")
    elif _sel is None or len(_sel) == 0:
        contrast_detail = mo.callout(mo.md("Select a feature row to see its top-activating examples."), kind="neutral")
    else:
        row = _sel[0] if isinstance(_sel, list) else _sel.iloc[0].to_dict()
        feat = int(row["feature"]); n = view["norm"].set_index("feature").loc[feat]
        bars = mo.md(
            f"""#### Feature {feat}

|  | {view['side_a']} | {view['side_b']} |
|---|---|---|
| mean activation | {n['mean_a']:.3f} | {n['mean_b']:.3f} |
| active frequency | {n['freq_a']:.3f} | {n['freq_b']:.3f} |

Cohen's d = **{n['cohen_d']:+.3f}** · max act **{n['max_activation']:.2f}** · active in **{int(n['active_count'])}** rows
"""
        )
        ex = view["ex_for"](feat)
        blocks = ([_block("Top-activating questions", ex["single"])] if "single" in ex
                  else [_block(f"Top: {k}", v) for k, v in ex.items()])
        contrast_detail = mo.vstack([bars, mo.md("\n\n".join(blocks))])
    return (contrast_detail,)


# ===========================================================================
#  TAB 2 — Training sweep
# ===========================================================================
@app.cell
def _(TRAIN_SUMMARY, mo):
    _arms = sorted(TRAIN_SUMMARY["arm"].dropna().unique().tolist()) if len(TRAIN_SUMMARY) else []
    train_arm = mo.ui.dropdown(
        options={a: a for a in _arms}, value=(_arms[0] if _arms else None),
        label="**Arm** (for the loss curves)",
    )
    return (train_arm,)


@app.cell
def _(TRAIN_HISTORY, TRAIN_SUMMARY, mo, px, train_arm):
    if not len(TRAIN_SUMMARY):
        training_content = mo.md("_No SAE training runs (`sae_runs`) discovered._")
    else:
        h = TRAIN_HISTORY[TRAIN_HISTORY["arm"] == train_arm.value] if len(TRAIN_HISTORY) else TRAIN_HISTORY
        curve = px.line(
            h, x="epoch", y="val_mse", color="pilot", markers=True,
            title=f"Validation reconstruction MSE vs epoch — {train_arm.value}",
            template="plotly_white",
        )
        curve.update_layout(height=360, margin=dict(l=60, r=20, t=50, b=40),
                            yaxis_title="validation MSE")
        trade = px.scatter(
            TRAIN_SUMMARY, x="val_mean_active", y="val_mse", color="pilot", symbol="arm",
            hover_data=["run", "top_k", "l1", "val_code_density"],
            title="Sparsity–fidelity tradeoff — x: mean active features, y: validation MSE",
            template="plotly_white",
        )
        trade.update_traces(marker=dict(size=13, line=dict(width=0.5, color="rgba(0,0,0,.3)")))
        trade.update_layout(height=360, margin=dict(l=60, r=20, t=50, b=40))
        _tbl = TRAIN_SUMMARY.round(
            {"train_mse": 4, "val_mse": 4, "val_code_density": 4, "val_mean_active": 2}
        )[["run", "top_k", "l1", "train_mse", "val_mse", "val_mean_active", "val_code_density"]]
        _cap = lambda t: mo.md(f"<span style='color:#667;font-size:13px'>{t}</span>")
        training_content = mo.vstack([
            mo.md("Each SAE pilot trains an example-level SAE on the delta activations. "
                  "Lower MSE = better reconstruction; fewer active features = sparser code."),
            train_arm, mo.ui.plotly(curve),
            _cap("Each line is one training run: how well it reconstructs the activations "
                 "(lower = better) as training progresses. Dropping then flattening = trained cleanly."),
            mo.ui.plotly(trade),
            _cap("Each dot is a finished SAE, placed by sparsity (fewer active features →) vs "
                 "reconstruction error (lower MSE ↑ is better, so bottom-left is the sweet spot). "
                 "Shows what accuracy you pay for forcing sparser codes."),
            mo.ui.table(data=_tbl, selection=None, label="**Run summary**"),
        ])
    return (training_content,)


# ===========================================================================
#  TAB 3 — Directions (cosine heatmap)
# ===========================================================================
@app.cell
def _(DIRECTION_GROUPS, mo):
    dir_group = mo.ui.dropdown(
        options={k: k for k in DIRECTION_GROUPS},
        value=(next(iter(DIRECTION_GROUPS)) if DIRECTION_GROUPS else None),
        label="**Directions group**",
    )
    return (dir_group,)


@app.cell
def _(DIRECTION_GROUPS, dir_group, go, load_direction_vectors, mo):
    if not DIRECTION_GROUPS or dir_group.value is None:
        directions_content = mo.md("_No exported feature directions (`sae_feature_directions`) discovered._")
    else:
        cat, labels, cos = load_direction_vectors(DIRECTION_GROUPS[dir_group.value])
        if not labels:
            directions_content = mo.vstack([dir_group, mo.md("_Vectors could not be loaded for this group._")])
        else:
            hm = go.Figure(go.Heatmap(
                z=cos, x=labels, y=labels, zmin=-1, zmax=1, colorscale="RdBu", reversescale=True,
                colorbar=dict(title="cosine"),
                text=[[f"{v:.2f}" for v in row] for row in cos],
                texttemplate="%{text}", textfont=dict(size=10),
            ))
            hm.update_layout(
                title="Pairwise cosine similarity of exported feature decoder directions",
                height=460, template="plotly_white", margin=dict(l=90, r=20, t=50, b=90),
                yaxis=dict(autorange="reversed"),
            )
            _cols = [c for c in ["feature", "feature_skew_label", "abs_cohen_d",
                                 "mean_diff_unknown_minus_known", "norm", "candidate_label"]
                     if c in cat.columns]
            _cap = lambda t: mo.md(f"<span style='color:#667;font-size:13px'>{t}</span>")
            directions_content = mo.vstack([
                dir_group, mo.ui.plotly(hm),
                _cap("Each cell = angle-agreement between two exported feature directions: "
                     "+1 identical, 0 unrelated, −1 opposite. Values near 0 mean the directions are "
                     "independent (not redundant), each carrying distinct information."),
                mo.ui.table(data=cat[_cols].round(4), selection=None, label="**Direction catalog**"),
                _cap("Which features were promoted to exported vectors, their known/unknown skew, "
                     "effect size, and norm — the provenance behind each heatmap row."),
            ])
    return (directions_content,)


# ===========================================================================
#  TAB 4 — Composites catalog
# ===========================================================================
@app.cell
def _(COMPOSITES, ast, mo, pd):
    if not len(COMPOSITES):
        composites_content = mo.md("_No composite directions (`sae_feature_composites`) discovered._")
    else:
        def _fmt(v):
            try:
                return ", ".join(str(x) for x in ast.literal_eval(v))
            except Exception:
                return v
        c = COMPOSITES.copy()
        for col in ("source_features", "weights", "source_candidate_labels"):
            if col in c:
                c[col] = c[col].map(_fmt)
        _cols = [x for x in ["candidate_label", "contrast", "source_features", "weights",
                             "combine", "rescale", "norm", "layer"] if x in c.columns]
        composites_content = mo.vstack([
            mo.ui.table(data=c[_cols].round(4) if _cols else c, selection=None, label="**Composite directions**"),
            mo.md("<span style='color:#667;font-size:13px'>"
                  "Engineered steering vectors built by combining features "
                  "(e.g. <code>f047 + f051 − f064 − f065</code> = an <i>unknown − known</i> composite); "
                  "<code>weights</code> lines up with <code>source_features</code>. Documents how each "
                  "composite was assembled, so a steering result can be traced to its recipe.</span>"),
        ])
    return (composites_content,)


# ===========================================================================
#  Layout — assemble tabs
# ===========================================================================
@app.cell
def _(
    candidate, composites_content, contrast, contrast_detail, contrast_header,
    contrast_volcano, directions_content, family, feat_table, mo, training_content,
):
    _selectors = mo.hstack(
        [x for x in (family, candidate, contrast) if x is not None],
        justify="start", gap=1, wrap=True,
    )
    _cap = lambda t: mo.md(f"<span style='color:#667;font-size:13px'>{t}</span>")
    contrast_tab = mo.vstack([
        _selectors, contrast_header, contrast_volcano,
        _cap("Each dot is one SAE feature. Left–right = which questions make it fire more "
             "(right = unknown/unanswerable, left = known); up = how cleanly it separates the two "
             "(Cohen's d). Top-right ≈ a reliable “I don’t know this” detector."),
        feat_table,
        _cap("The same features as a sortable list, ranked by separation strength (|Cohen's d|), "
             "with average activation and firing rate per group. Click a row to inspect it."),
        contrast_detail,
        _cap("The mini-table contrasts one feature’s mean activation and firing rate between groups; "
             "the questions below are what make it fire hardest — this is where you read the feature’s meaning."),
    ])
    mo.vstack([
        mo.md("# SAE feature dashboard\n"
              "_Example-level SAE analysis over mechinterp delta activations — exploratory, "
              "not headline evidence._"),
        mo.ui.tabs({
            "🔬 Feature contrasts": contrast_tab,
            "📉 Training sweep": training_content,
            "🧭 Directions": directions_content,
            "🧩 Composites": composites_content,
        }),
    ])
    return


if __name__ == "__main__":
    app.run()
