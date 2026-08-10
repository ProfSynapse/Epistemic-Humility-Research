#!/usr/bin/env python3
"""CPU probe sweep for flavor-atlas-gemma-pt-confirmatory (AMENDMENT.md
"Design", "Multiplicity discipline and the layer problem").

Adapted from flavor-atlas-rawbase/flavor_probe_sweep.py: reuses the pinned
item-26 OOF-AUROC protocol UNCHANGED
(`internal_panel_probe_gate._cv_auroc_with_oof`, pin ee3f22ee) and the same
G1/G2/G3/G4 curve/transfer-matrix construction, extended for:

  - 43 hidden states instead of 37 (this substrate's full depth).
  - The dual-leg decision surface (AMENDMENT.md "Multiplicity discipline"):
    Leg A, an externally pre-fixed anchor at hidden state 24 (Amendment Y's
    own best layer on this checkpoint, selected on a different label set and
    estimator -- an external constant with respect to these 12 decisions);
    Leg B, nested split-half selection (best layer chosen on a fixed 50%
    selection split, reported AUROC computed out of fold on the
    complementary 50% evaluation split at that layer, immune to
    max-over-43-layers inflation by construction). 6 flavors x 2 legs = 12
    primary cells; pooled-all-unknowns and selfaware are banded reference
    rows at the same two legs, not decisive.
  - G6, the descriptive dual-render control: the same curve construction
    run against the 1800-row chat-template-rendered subsample extraction,
    for comparison against the primary (k-shot) reading on the same rows.

Output is a counts-only JSON: AUROCs at 4dp, per-flavor n counts, best
layer per flavor, full layer curves, dual-leg decisions, and the transfer
matrix. No row or question text is read into any field of the output.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
GATES_PATH = EXP_DIR / "gates.yaml"
ITEM26_DIR = REPO_ROOT / "experiments" / "ood-breadth-beyond-selfaware"

sys.path.insert(0, str(ITEM26_DIR))

import internal_panel_probe_gate as ipg  # pinned module, unmodified, sha256 ee3f22ee...

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]
M4_FLAVOR_NAMES = KUQ_CATEGORIES + ["selfaware", "ambigqa"]
ALL_SOURCES = ["kuq", "ambigqa", "selfaware"]
N_HIDDEN_STATES = 43
LEG_A_HIDDEN_STATE = 24
LEG_B_SELECTION_FRACTION = 0.50
LEG_B_SEED = 20260810


def load_gates() -> dict:
    with GATES_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def discover_layers(extraction_dir: Path) -> list[int]:
    manifest_path = extraction_dir / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing extraction manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    layers = manifest["layers"]
    if isinstance(layers, list):
        return sorted(int(l) for l in layers)
    if layers == "all":
        return list(range(int(manifest["n_hidden_states"])))
    raise SystemExit(f"unrecognized manifest layers value: {layers!r}")


def require_forward_use_cache(extraction_dir: Path) -> None:
    """GG1: refuse to read any extraction manifest that does not record
    forward_use_cache: true. This is the CPU-side half of the KV-seam gate;
    the GPU-side half is extract_anchor_gemma.py always passing
    use_cache=True and the live paired smoke."""
    manifest_path = extraction_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("forward_use_cache") is not True:
        raise SystemExit(
            f"GG1 STOP: {manifest_path} does not record forward_use_cache: true; "
            "refusing to read a KV-seam-inadmissible extraction on gemma-4-E4B."
        )


def squeeze_singleton(X: np.ndarray) -> np.ndarray:
    if X.ndim == 3:
        if X.shape[1] != 1:
            raise SystemExit(
                f"expected exactly 1 captured position per row for the anchor "
                f"family, got {X.shape[1]}"
            )
        X = X[:, 0, :]
    return X


def row_key_to_tensor_file(extraction_dir: Path, row_key: str, source: str = "anchor") -> Path:
    stem = row_key.replace("::", "__")
    return extraction_dir / f"{stem}__{source}.safetensors"


def load_layers_local(extraction_dir: Path, row_keys: list[str], layers: list[int]) -> dict[int, np.ndarray]:
    """Same schema as latent_knowledge_probe.load_layers, reading this
    cell's own per-row safetensors (source='anchor')."""
    from safetensors import safe_open

    keys = [f"L{L}" for L in layers]
    cols: dict[int, list] = {L: [] for L in layers}
    for rk in row_keys:
        path = row_key_to_tensor_file(extraction_dir, rk)
        if not path.is_file():
            raise SystemExit(f"missing activation file for {rk}: {path}")
        with safe_open(str(path), "pt") as h:
            for L, key in zip(layers, keys):
                cols[L].append(h.get_tensor(key).float().numpy())
    return {L: np.asarray(cols[L], dtype=np.float64) for L in layers}


class SourcePanel:
    def __init__(self, name: str, panel_rows: list[dict], extraction_dir: Path):
        self.name = name
        self.rows = panel_rows
        self.row_keys = [r["row_key"] for r in panel_rows]
        self.y_known = np.array([1 if r["label"] == "known" else 0 for r in panel_rows])
        self.flavor = np.array([r["flavor"] for r in panel_rows])
        self.extraction_dir = extraction_dir
        self._cache: dict[int, np.ndarray] = {}

    def matrix_at(self, layer: int) -> np.ndarray:
        if layer not in self._cache:
            mats = load_layers_local(self.extraction_dir, self.row_keys, [layer])
            self._cache[layer] = squeeze_singleton(mats[layer])
        return self._cache[layer]


def fit_full_probe(X: np.ndarray, y: np.ndarray):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=0.5, max_iter=2000)
    clf.fit(sc.transform(X), y)
    return sc, clf


def score_frozen(sc, clf, X: np.ndarray, y: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    s = clf.decision_function(sc.transform(X))
    return float(roc_auc_score(y, s))


def m1_flavor_mask(panel: SourcePanel, flavor_name: str | None) -> np.ndarray:
    known_mask = panel.y_known == 1
    if flavor_name is None:
        unknown_mask = panel.y_known == 0
    else:
        unknown_mask = panel.flavor == flavor_name
    return known_mask | unknown_mask


def sweep_source_curve(panel: SourcePanel, layers: list[int], mask_fn, log_prefix: str) -> dict:
    mask = mask_fn(panel)
    y_sub = panel.y_known[mask]
    n_known = int((y_sub == 1).sum())
    n_unknown = int((y_sub == 0).sum())

    aurocs, stds = [], []
    for L in layers:
        t0 = time.monotonic()
        X_sub = panel.matrix_at(L)[mask]
        mean_auc, std_auc, _oof = ipg._cv_auroc_with_oof(X_sub, y_sub, folds=5, C=0.5, seed=0)
        aurocs.append(round(float(mean_auc), 4))
        stds.append(round(float(std_auc), 4))
        print(f"  [{log_prefix}] layer={L} auroc={mean_auc:.4f} ({time.monotonic()-t0:.1f}s)", file=sys.stderr)

    best_idx = int(np.argmax(aurocs))
    return {
        "n_known": n_known, "n_unknown": n_unknown,
        "layers": layers, "auroc": aurocs, "auroc_std": stds,
        "best_layer": layers[best_idx], "best_auroc": aurocs[best_idx],
    }


def stratified_half_split(y: np.ndarray, flavor: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    """Boolean mask, True = selection split. Stratified by (label, flavor)
    so both halves keep the same known/unknown and (within-flavor) balance."""
    rng = np.random.default_rng(seed)
    strata = [f"{y[i]}::{flavor[i]}" for i in range(len(y))]
    selection_mask = np.zeros(len(y), dtype=bool)
    for stratum in sorted(set(strata)):
        idx = np.array([i for i, s in enumerate(strata) if s == stratum])
        n_sel = max(1, int(round(len(idx) * fraction))) if len(idx) > 1 else (1 if fraction >= 0.5 else 0)
        chosen = rng.choice(idx, size=min(n_sel, len(idx)), replace=False)
        selection_mask[chosen] = True
    return selection_mask


def dual_leg_decision(panel: SourcePanel, layers: list[int], mask_fn, log_prefix: str) -> dict:
    """Leg A (hs24 externally-fixed anchor) + Leg B (nested split-half
    selection). See module docstring and AMENDMENT.md "Multiplicity
    discipline and the layer problem"."""
    mask = mask_fn(panel)
    idx = np.where(mask)[0]
    y_sub = panel.y_known[idx]
    flavor_sub = panel.flavor[idx]

    # --- Leg A: externally fixed hidden state 24 ---
    if LEG_A_HIDDEN_STATE not in layers:
        raise SystemExit(f"Leg A anchor hidden state {LEG_A_HIDDEN_STATE} not in extracted layers")
    X_a = panel.matrix_at(LEG_A_HIDDEN_STATE)[idx]
    leg_a_auc, leg_a_std, _oof = ipg._cv_auroc_with_oof(X_a, y_sub, folds=5, C=0.5, seed=0)
    leg_a = {"hidden_state": LEG_A_HIDDEN_STATE, "auroc": round(float(leg_a_auc), 4)}

    # --- Leg B: nested split-half selection ---
    selection_mask = stratified_half_split(y_sub, flavor_sub, LEG_B_SELECTION_FRACTION, LEG_B_SEED)
    evaluation_mask = ~selection_mask
    sel_idx = idx[selection_mask]
    eval_idx = idx[evaluation_mask]
    if len(np.unique(panel.y_known[sel_idx])) < 2 or len(np.unique(panel.y_known[eval_idx])) < 2:
        raise SystemExit(f"[{log_prefix}] Leg B split degenerate: one split has a single class")

    selection_curve = []
    for L in layers:
        X_sel = panel.matrix_at(L)[sel_idx]
        y_sel = panel.y_known[sel_idx]
        mean_auc, _std, _oof = ipg._cv_auroc_with_oof(X_sel, y_sel, folds=5, C=0.5, seed=0)
        selection_curve.append(round(float(mean_auc), 4))
    selected_layer = layers[int(np.argmax(selection_curve))]

    X_eval = panel.matrix_at(selected_layer)[eval_idx]
    y_eval = panel.y_known[eval_idx]
    eval_auc, eval_std, _oof = ipg._cv_auroc_with_oof(X_eval, y_eval, folds=5, C=0.5, seed=0)

    leg_b = {
        "selection_fraction": LEG_B_SELECTION_FRACTION,
        "n_selection": int(len(sel_idx)), "n_evaluation": int(len(eval_idx)),
        "selection_split_curve": selection_curve,
        "selected_layer": selected_layer,
        "auroc": round(float(eval_auc), 4),
    }
    print(f"  [{log_prefix}] leg_a(hs{LEG_A_HIDDEN_STATE})={leg_a['auroc']:.4f} "
          f"leg_b(hs{selected_layer})={leg_b['auroc']:.4f}", file=sys.stderr)
    return {"leg_a": leg_a, "leg_b": leg_b}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panels-dir", type=Path, default=EXP_DIR / "analysis" / "panels")
    ap.add_argument("--extraction-root", type=Path, default=EXP_DIR / "analysis" / "extraction")
    ap.add_argument("--extraction-dir-override", action="append", default=[])
    ap.add_argument("--control-panel", type=Path, default=None,
                     help="dual-render subsample panel jsonl (G6, descriptive)")
    ap.add_argument("--control-extraction-dir", type=Path, default=None)
    ap.add_argument("--sources", default="kuq,ambigqa,selfaware")
    ap.add_argument("--layers", default=None)
    ap.add_argument("--out", type=Path, default=EXP_DIR / "analysis" / "probe" / "gemma_flavor_atlas_result.json")
    args = ap.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    for s in sources:
        if s not in ALL_SOURCES:
            raise SystemExit(f"unknown source '{s}', expected one of {ALL_SOURCES}")

    overrides: dict[str, Path] = {}
    for item in args.extraction_dir_override:
        k, v = item.split("=", 1)
        overrides[k] = Path(v)

    panel_files = {s: args.panels_dir / f"{s}_panel.jsonl" for s in sources}
    for s, p in panel_files.items():
        if not p.is_file():
            print(f"REFUSING TO RUN: panel for source '{s}' missing ({p}).", file=sys.stderr)
            return 1

    panels: dict[str, SourcePanel] = {}
    for s in sources:
        rows = load_jsonl(panel_files[s])
        ext_dir = overrides.get(s, args.extraction_root / s)
        if not ext_dir.is_dir():
            print(f"REFUSING TO RUN: extraction dir for source '{s}' missing ({ext_dir}).", file=sys.stderr)
            return 1
        require_forward_use_cache(ext_dir)
        panels[s] = SourcePanel(s, rows, ext_dir)

    layer_override = None
    if args.layers is not None:
        layer_override = sorted(int(x) for x in args.layers.split(","))
    layers_by_source: dict[str, list[int]] = {}
    for s, panel in panels.items():
        layers_by_source[s] = layer_override if layer_override is not None else discover_layers(panel.extraction_dir)

    result: dict = {
        "cell": "flavor-atlas-gemma-pt-confirmatory",
        "protocol": "internal_panel_probe_gate._cv_auroc_with_oof unchanged (folds=5, C=0.5, seed=0)",
        "primary_render": "base_mode_kshot",
        "sources_processed": sources,
        "layers_by_source": layers_by_source,
    }

    # --- G1 (kuq) + dual-leg decision ---
    if "kuq" in panels:
        kuq_panel = panels["kuq"]
        kuq_layers = layers_by_source["kuq"]
        g1 = {"known_pool_n": int((kuq_panel.y_known == 1).sum()), "flavors": {}}
        dual_leg = {}
        for cat in KUQ_CATEGORIES:
            g1["flavors"][cat] = sweep_source_curve(
                kuq_panel, kuq_layers, lambda p, c=cat: m1_flavor_mask(p, c), f"g1:{cat}"
            )
            dual_leg[cat] = dual_leg_decision(
                kuq_panel, kuq_layers, lambda p, c=cat: m1_flavor_mask(p, c), f"legs:{cat}"
            )
        g1["flavors"]["pooled_all_unknowns"] = sweep_source_curve(
            kuq_panel, kuq_layers, lambda p: m1_flavor_mask(p, None), "g1:pooled"
        )
        dual_leg["pooled_all_unknowns_reference"] = dual_leg_decision(
            kuq_panel, kuq_layers, lambda p: m1_flavor_mask(p, None), "legs:pooled"
        )
        result["g1_kuq"] = g1
        result["dual_leg_decision"] = dual_leg

    # --- G2 (ambigqa), whole-curve, no leg decision ---
    if "ambigqa" in panels:
        ambigqa_panel = panels["ambigqa"]
        result["g2_ambigqa"] = sweep_source_curve(
            ambigqa_panel, layers_by_source["ambigqa"],
            lambda p: np.ones(len(p.y_known), dtype=bool), "g2:ambigqa"
        )

    # --- G3 (selfaware) + reference dual-leg ---
    if "selfaware" in panels:
        selfaware_panel = panels["selfaware"]
        result["g3_selfaware"] = sweep_source_curve(
            selfaware_panel, layers_by_source["selfaware"],
            lambda p: np.ones(len(p.y_known), dtype=bool), "g3:selfaware"
        )
        result.setdefault("dual_leg_decision", {})["selfaware_reference"] = dual_leg_decision(
            selfaware_panel, layers_by_source["selfaware"],
            lambda p: np.ones(len(p.y_known), dtype=bool), "legs:selfaware"
        )

    # --- G4 transfer matrix ---
    if set(ALL_SOURCES) <= set(panels.keys()):
        def flavor_source_and_mask(flavor_name: str):
            if flavor_name in KUQ_CATEGORIES:
                return panels["kuq"], m1_flavor_mask(panels["kuq"], flavor_name)
            if flavor_name == "selfaware":
                p = panels["selfaware"]
                return p, np.ones(len(p.y_known), dtype=bool)
            if flavor_name == "ambigqa":
                p = panels["ambigqa"]
                return p, np.ones(len(p.y_known), dtype=bool)
            raise ValueError(flavor_name)

        best_layers = {cat: result["g1_kuq"]["flavors"][cat]["best_layer"] for cat in KUQ_CATEGORIES}
        best_layers["selfaware"] = result["g3_selfaware"]["best_layer"]
        best_layers["ambigqa"] = result["g2_ambigqa"]["best_layer"]

        matrix: dict[str, dict[str, float]] = {}
        for src_flavor in M4_FLAVOR_NAMES:
            src_panel, src_mask = flavor_source_and_mask(src_flavor)
            L = best_layers[src_flavor]
            X_src = src_panel.matrix_at(L)[src_mask]
            y_src = src_panel.y_known[src_mask]
            sc, clf = fit_full_probe(X_src, y_src)
            row: dict[str, float] = {}
            for tgt_flavor in M4_FLAVOR_NAMES:
                if tgt_flavor == src_flavor:
                    continue
                tgt_panel, tgt_mask = flavor_source_and_mask(tgt_flavor)
                X_tgt = tgt_panel.matrix_at(L)[tgt_mask]
                y_tgt = tgt_panel.y_known[tgt_mask]
                row[tgt_flavor] = round(score_frozen(sc, clf, X_tgt, y_tgt), 4)
            matrix[src_flavor] = row
            print(f"  [g4] source={src_flavor} layer={L} -> {row}", file=sys.stderr)

        result["g4_transfer_matrix"] = {"source_best_layers": best_layers, "matrix": matrix}
    else:
        missing = sorted(set(ALL_SOURCES) - set(panels.keys()))
        result["g4_transfer_matrix"] = {"status": "skipped", "reason": f"sources not processed: {missing}"}

    # --- G6 dual-render control (descriptive, chat-template on subsample) ---
    if args.control_panel is not None and args.control_extraction_dir is not None:
        require_forward_use_cache(args.control_extraction_dir)
        control_rows = load_jsonl(args.control_panel)
        control_panel = SourcePanel("control", control_rows, args.control_extraction_dir)
        control_layers = layer_override if layer_override is not None else discover_layers(args.control_extraction_dir)
        g6 = {"role": "descriptive_only_cannot_pass_falsify_or_rescue", "flavors": {}}
        for cat in KUQ_CATEGORIES:
            g6["flavors"][cat] = sweep_source_curve(
                control_panel, control_layers, lambda p, c=cat: m1_flavor_mask(p, c), f"g6:{cat}"
            )
        g6["flavors"]["pooled_all_unknowns"] = sweep_source_curve(
            control_panel, control_layers, lambda p: m1_flavor_mask(p, None), "g6:pooled"
        )
        result["g6_dual_render_control_chat_template"] = g6

    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, indent=2)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
