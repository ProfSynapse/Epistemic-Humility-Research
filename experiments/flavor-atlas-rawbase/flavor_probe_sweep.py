#!/usr/bin/env python3
"""CPU probe sweep for flavor-atlas-rawbase (AMENDMENT.md Design M1-M4).

Reuses the pinned item-26 OOF-AUROC protocol UNCHANGED:
`internal_panel_probe_gate._cv_auroc_with_oof` (StandardScaler + L2
LogisticRegression(C=0.5) + StratifiedKFold(5, seed 0), held-out
out-of-fold AUROC; pin ee3f22ee). Imported via the same sys.path insert
`rawbase_probe_fit.py` uses. Activations are loaded per layer via
`latent_knowledge_probe.load_layers`, one source-panel-wide read per
layer (never all 37 layers of a panel held in memory at once); the
(n, 1, hidden) singleton position axis is squeezed with the identical
guard both reference scripts use.

Four statistics, per AMENDMENT Design:
  M1 per-KUQ-flavor: for each of the 6 KUQ categories, flavor-unknowns vs
     the full KUQ known pool, at every layer, plus a pooled all-unknowns row.
  M2 AmbigQA: unknown vs known at every layer.
  M3 SelfAware: unknown (unanswerable) vs known (answerable) at every layer.
  M4 transfer matrix: for each of the 8 source flavors (6 KUQ + selfaware +
     ambigqa), fit ONE full-data probe (same scaler/C, no CV) at that
     source's own best layer (argmax of its own OOF curve), then evaluate
     the frozen probe on every other flavor's rows at that SAME layer
     (target unknowns vs the target's own known pool), scored by
     roc_auc_score.

Output is a counts-only JSON: AUROCs at 4dp, per-flavor n counts, best
layer per flavor, full layer curves, and the transfer matrix. No row or
question text is read into any field of the output.
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
LATENT_CONTROLS_DIR = REPO_ROOT / "experiments" / "selfaware-latent-knowledge-controls"

sys.path.insert(0, str(ITEM26_DIR))
sys.path.insert(0, str(LATENT_CONTROLS_DIR))

import internal_panel_probe_gate as ipg  # pinned module, unmodified
import latent_knowledge_probe as lkp

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


def reverify_fg0(gates: dict, panels_manifest: dict) -> dict:
    checks = gates["fg0_panel_integrity"]["checks"]
    problems: list[str] = []
    counts = panels_manifest.get("counts", {})

    kuq = counts.get("kuq", {})
    if kuq.get("n") != checks["kuq_rows_must_equal"]:
        problems.append(f"kuq n mismatch: manifest={kuq.get('n')}, gate={checks['kuq_rows_must_equal']}")
    kuq_labels = kuq.get("by_label", {})
    if kuq_labels.get("known") != checks["kuq_known_must_equal"]:
        problems.append(f"kuq known mismatch: manifest={kuq_labels.get('known')}, gate={checks['kuq_known_must_equal']}")
    if kuq_labels.get("unknown") != checks["kuq_unknown_must_equal"]:
        problems.append(f"kuq unknown mismatch: manifest={kuq_labels.get('unknown')}, gate={checks['kuq_unknown_must_equal']}")
    kuq_flavors = kuq.get("by_flavor", {})
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        got = kuq_flavors.get(cat, 0)
        if got != expected:
            problems.append(f"kuq flavor '{cat}' mismatch: manifest={got}, gate={expected}")

    ambigqa = counts.get("ambigqa", {})
    if ambigqa.get("n") != checks["ambigqa_rows_must_equal"]:
        problems.append(f"ambigqa n mismatch: manifest={ambigqa.get('n')}, gate={checks['ambigqa_rows_must_equal']}")
    ambigqa_labels = ambigqa.get("by_label", {})
    if ambigqa_labels.get("known") != checks["ambigqa_known_must_equal"]:
        problems.append(f"ambigqa known mismatch: manifest={ambigqa_labels.get('known')}, gate={checks['ambigqa_known_must_equal']}")
    if ambigqa_labels.get("unknown") != checks["ambigqa_unknown_must_equal"]:
        problems.append(f"ambigqa unknown mismatch: manifest={ambigqa_labels.get('unknown')}, gate={checks['ambigqa_unknown_must_equal']}")

    selfaware = counts.get("selfaware", {})
    if selfaware.get("n") != checks["selfaware_rows_must_equal"]:
        problems.append(f"selfaware n mismatch: manifest={selfaware.get('n')}, gate={checks['selfaware_rows_must_equal']}")
    selfaware_labels = selfaware.get("by_label", {})
    if selfaware_labels.get("known") != checks["selfaware_answerable_must_equal"]:
        problems.append(f"selfaware known mismatch: manifest={selfaware_labels.get('known')}, gate={checks['selfaware_answerable_must_equal']}")
    if selfaware_labels.get("unknown") != checks["selfaware_unanswerable_must_equal"]:
        problems.append(f"selfaware unknown mismatch: manifest={selfaware_labels.get('unknown')}, gate={checks['selfaware_unanswerable_must_equal']}")

    status = "PASS" if not problems else "STOP"
    return {"status": status, "problems": problems}


def discover_layers(extraction_dir: Path) -> list[int]:
    manifest_path = extraction_dir / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing extraction manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    layers = manifest["layers"]
    if isinstance(layers, list):
        return sorted(int(l) for l in layers)
    # all-layer extractions record layers as the string "all"; the manifest's
    # n_hidden_states is the authoritative count (keys L0..L{n-1} per row)
    if layers == "all":
        return list(range(int(manifest["n_hidden_states"])))
    raise SystemExit(f"unrecognized manifest layers value: {layers!r}")


def squeeze_singleton(X: np.ndarray) -> np.ndarray:
    """Same singleton-position squeeze+guard as rawbase_probe_fit.py /
    internal_panel_probe_gate.compute (anchor family -> exactly 1 captured
    position per row)."""
    if X.ndim == 3:
        if X.shape[1] != 1:
            raise SystemExit(
                f"expected exactly 1 captured position per row for the anchor "
                f"family, got {X.shape[1]}; extraction spec drifted from "
                "extract_kuq.yaml/extract_ambigqa_alllayers.yaml/extract_selfaware.yaml "
                "(families: [anchor])"
            )
        X = X[:, 0, :]
    return X


class SourcePanel:
    """One source's panel rows (row_key/label/flavor), its extraction dir,
    and a per-layer activation-matrix cache aligned to panel row order."""

    def __init__(self, name: str, panel_rows: list[dict], extraction_dir: Path):
        self.name = name
        self.rows = panel_rows
        self.row_keys = [r["row_key"] for r in panel_rows]
        # y=1 known, y=0 unknown -- same convention as rawbase_probe_fit.py's M1.
        self.y_known = np.array([1 if r["label"] == "known" else 0 for r in panel_rows])
        self.flavor = np.array([r["flavor"] for r in panel_rows])
        self.extraction_dir = extraction_dir
        self._cache: dict[int, np.ndarray] = {}

    def matrix_at(self, layer: int) -> np.ndarray:
        if layer not in self._cache:
            mats = lkp.load_layers(self.extraction_dir, self.row_keys, [layer], source="anchor")
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
    """flavor_name=None -> pooled all-unknowns. Returns boolean mask over
    (flavor-unknowns OR known-pool) rows."""
    known_mask = panel.y_known == 1
    if flavor_name is None:
        unknown_mask = panel.y_known == 0
    else:
        unknown_mask = panel.flavor == flavor_name
    return known_mask | unknown_mask


def sweep_source_curve(panel: SourcePanel, layers: list[int], mask_fn, log_prefix: str) -> dict:
    """mask_fn(panel) -> boolean mask selecting the rows for this curve.
    Returns {"n": ..., "layers": [...], "auroc": [...], "std": [...], "best_layer": ..., "best_auroc": ...}."""
    mask = mask_fn(panel)
    y_sub = panel.y_known[mask]
    n_known = int((y_sub == 1).sum())
    n_unknown = int((y_sub == 0).sum())

    aurocs = []
    stds = []
    for L in layers:
        t0 = time.monotonic()
        X_full = panel.matrix_at(L)
        X_sub = X_full[mask]
        mean_auc, std_auc, _oof = ipg._cv_auroc_with_oof(X_sub, y_sub, folds=5, C=0.5, seed=0)
        aurocs.append(round(float(mean_auc), 4))
        stds.append(round(float(std_auc), 4))
        print(f"  [{log_prefix}] layer={L} auroc={mean_auc:.4f} ({time.monotonic()-t0:.1f}s)", file=sys.stderr)

    best_idx = int(np.argmax(aurocs))
    return {
        "n_known": n_known,
        "n_unknown": n_unknown,
        "layers": layers,
        "auroc": aurocs,
        "auroc_std": stds,
        "best_layer": layers[best_idx],
        "best_auroc": aurocs[best_idx],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panels-dir", type=Path, default=EXP_DIR / "analysis" / "panels")
    ap.add_argument("--extraction-root", type=Path, default=EXP_DIR / "analysis" / "extraction")
    ap.add_argument("--extraction-dir-override", action="append", default=[],
                     help="SOURCE=PATH, repeatable; overrides the default {extraction-root}/{source} dir")
    ap.add_argument("--sources", default="kuq,ambigqa,selfaware",
                     help="comma list restricting which of kuq/ambigqa/selfaware are processed")
    ap.add_argument("--layers", default=None,
                     help="comma list of layer indices; default is every layer present per source's own extraction manifest")
    ap.add_argument("--out", type=Path, default=EXP_DIR / "analysis" / "probe" / "flavor_atlas_result.json")
    args = ap.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    for s in sources:
        if s not in ALL_SOURCES:
            raise SystemExit(f"unknown source '{s}', expected one of {ALL_SOURCES}")

    overrides: dict[str, Path] = {}
    for item in args.extraction_dir_override:
        if "=" not in item:
            raise SystemExit(f"--extraction-dir-override expects SOURCE=PATH, got '{item}'")
        k, v = item.split("=", 1)
        if k not in ALL_SOURCES:
            raise SystemExit(f"unknown source '{k}' in --extraction-dir-override")
        overrides[k] = Path(v)

    gates = load_gates()

    # --- fg0 re-verification (panel manifest counts) ---
    manifest_path = args.panels_dir / "panels_manifest.json"
    if not manifest_path.is_file():
        print(f"REFUSING TO RUN: panels manifest missing ({manifest_path}); run build_flavor_panels.py first.", file=sys.stderr)
        return 1
    panels_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fg0 = reverify_fg0(gates, panels_manifest)
    if fg0["status"] != "PASS":
        print("FG0 RE-VERIFY STOP:", file=sys.stderr)
        for p in fg0["problems"]:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # --- refuse to run if requested panels are missing ---
    panel_files = {s: args.panels_dir / f"{s}_panel.jsonl" for s in sources}
    for s, p in panel_files.items():
        if not p.is_file():
            print(f"REFUSING TO RUN: panel for source '{s}' missing ({p}); run build_flavor_panels.py first.", file=sys.stderr)
            return 1

    # --- build SourcePanel objects for requested sources ---
    panels: dict[str, SourcePanel] = {}
    for s in sources:
        rows = load_jsonl(panel_files[s])
        ext_dir = overrides.get(s, args.extraction_root / s)
        if not ext_dir.is_dir():
            print(f"REFUSING TO RUN: extraction dir for source '{s}' missing ({ext_dir}).", file=sys.stderr)
            return 1
        panels[s] = SourcePanel(s, rows, ext_dir)

    layer_override = None
    if args.layers is not None:
        layer_override = sorted(int(x) for x in args.layers.split(","))

    layers_by_source: dict[str, list[int]] = {}
    for s, panel in panels.items():
        layers_by_source[s] = layer_override if layer_override is not None else discover_layers(panel.extraction_dir)

    result: dict = {
        "cell": "flavor-atlas-rawbase",
        "protocol": "internal_panel_probe_gate._cv_auroc_with_oof unchanged (folds=5, C=0.5, seed=0); M4 uses one full-data fit, no CV, same scaler/C",
        "sources_processed": sources,
        "layers_by_source": layers_by_source,
        "fg0_reverify": fg0,
    }

    # --- M1 (kuq) ---
    if "kuq" in panels:
        kuq_panel = panels["kuq"]
        kuq_layers = layers_by_source["kuq"]
        m1 = {"known_pool_n": int((kuq_panel.y_known == 1).sum()), "flavors": {}}
        for cat in KUQ_CATEGORIES:
            m1["flavors"][cat] = sweep_source_curve(
                kuq_panel, kuq_layers, lambda p, c=cat: m1_flavor_mask(p, c), f"m1:{cat}"
            )
        m1["flavors"]["pooled_all_unknowns"] = sweep_source_curve(
            kuq_panel, kuq_layers, lambda p: m1_flavor_mask(p, None), "m1:pooled"
        )
        result["m1_kuq"] = m1

    # --- M2 (ambigqa) ---
    if "ambigqa" in panels:
        ambigqa_panel = panels["ambigqa"]
        result["m2_ambigqa"] = sweep_source_curve(
            ambigqa_panel, layers_by_source["ambigqa"], lambda p: np.ones(len(p.y_known), dtype=bool), "m2:ambigqa"
        )

    # --- M3 (selfaware) ---
    if "selfaware" in panels:
        selfaware_panel = panels["selfaware"]
        result["m3_selfaware"] = sweep_source_curve(
            selfaware_panel, layers_by_source["selfaware"], lambda p: np.ones(len(p.y_known), dtype=bool), "m3:selfaware"
        )

    # --- M4 transfer matrix (needs all three sources present) ---
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

        best_layers = {}
        for cat in KUQ_CATEGORIES:
            best_layers[cat] = result["m1_kuq"]["flavors"][cat]["best_layer"]
        best_layers["selfaware"] = result["m3_selfaware"]["best_layer"]
        best_layers["ambigqa"] = result["m2_ambigqa"]["best_layer"]

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
            print(f"  [m4] source={src_flavor} layer={L} -> {row}", file=sys.stderr)

        result["m4_transfer_matrix"] = {"source_best_layers": best_layers, "matrix": matrix}
    else:
        missing = sorted(set(ALL_SOURCES) - set(panels.keys()))
        result["m4_transfer_matrix"] = {"status": "skipped", "reason": f"sources not processed: {missing}"}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, indent=2)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
