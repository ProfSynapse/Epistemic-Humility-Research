#!/usr/bin/env python3
"""Cross-family J-space layer contrast -- fit one frozen doubt gate threshold
per candidate layer on the FIT split, per family.

Ported from `j-space-midband-write-sweep-qwen3-4b/gate_fit.py`, generalized
to read a family's checkpoint/hs_indices instead of hardcoding Qwen3-4B.
Method is IDENTICAL across families: Youden-J threshold on
`neg_z_d = -z_d` (confab rows have LOW doubt), FIT confab vs FIT
known_correct_answered.

G0 floor (LOCKED, see AMENDMENT.md "Gates"): gate AUC >= 0.90 on FIT for
every candidate layer, per family.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kv_seam_patch as kv  # noqa: E402
from family_config import (  # noqa: E402
    FAMILY_SLUGS, SITE_SETS, layer_dir_name, load_family, resolve_site_set,
    site_set_artifact,
)


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{row_key.replace(':', '_')}"


def load_direction(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score

        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        count = 0.0
        for p in pos:
            count += (p > neg).sum() + 0.5 * (p == neg).sum()
        return float(count / (len(pos) * len(neg)))


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    best_tau, best_j, best_stats = None, -1e9, None
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        j = tpr - fpr
        if j > best_j:
            best_tau, best_j = float(tau), j
            best_stats = {"tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr,
                          "tp": tp, "fn": fn, "fp": fp, "tn": tn, "youden_j": j}
    assert best_tau is not None and best_stats is not None
    return best_tau, best_stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--site-set", default="midband", choices=sorted(SITE_SETS),
                    help="named site set from families/<family>.yaml "
                         "band_selection. Default 'midband' preserves the "
                         "pre-existing behaviour exactly.")
    ap.add_argument("--kv-sharing", default=kv.DEFAULT_KV_SHARING,
                    choices=list(kv.KV_SHARING_CHOICES),
                    help="KV-sharing condition this gate is fit UNDER. "
                         "cell.yaml readouts.refit_policy requires sharing-OFF "
                         "arms to refit their own tau on the SAME FIT rows. "
                         "Reads that condition's extract, directions and build "
                         "manifest, and writes a condition-scoped gate roll-up; "
                         "'on' keeps the historical filenames unchanged.")
    args = ap.parse_args(argv)

    from safetensors.numpy import load_file

    family = args.family

    def cn(name: str) -> str:
        return kv.condition_artifact(name, args.kv_sharing)
    # The selected site set only (default: MID-BAND candidates); the late arm's
    # gate (tau_frozen) is reused verbatim from the doubt-snap artifacts and is
    # not refit here.
    hs_list = resolve_site_set(load_family(family), args.site_set)
    analysis = HERE / "analysis" / family
    committed = HERE / "analysis-committed" / family
    out_path = committed / cn(site_set_artifact("gate_fit_layers.json", args.site_set))

    extract_manifest_path = analysis / cn("anchor_extract_manifest.json")
    extract_manifest = json.loads(extract_manifest_path.read_text())
    extract_cond = extract_manifest.get("kv_sharing", "on")
    if extract_cond != args.kv_sharing:
        print(f"[gate_fit:{family}] extract at {extract_manifest_path.name} was produced "
              f"under kv_sharing={extract_cond!r}, not {args.kv_sharing!r}",
              file=sys.stderr)
        return 1
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}
    split_manifest = json.loads((committed / "split_manifest.json").read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}

    confab_fit = [rk for rk, role in role_by_key.items()
                  if role == "confab" and split_by_key.get(rk) == "fit"]
    known_fit = [rk for rk, role in role_by_key.items()
                 if role == "known_correct_answered" and split_by_key.get(rk) == "fit"]

    fresh = {k: np.asarray(v, dtype=np.float64)
             for k, v in load_file(str(analysis / cn("anchor_extract.safetensors"))).items()}
    build_manifest = json.loads(
        (committed / cn(site_set_artifact("build_manifest_layers.json", args.site_set))).read_text()
    )
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)

    report = {
        "family": family,
        "site_set": args.site_set, "hs_indices": list(hs_list),
        "kv_sharing": args.kv_sharing,
        "population": {"positive_class": f"confab FIT (n={len(confab_fit)})",
                       "negative_class": f"known_correct_answered FIT (n={len(known_fit)})"},
        "score_definition": ("neg_z_d = -z_d; z_d clipped to [-2,+2] and standardized with "
                              "each layer's FIT-pool mu_d/sigma_d"),
        "sign_convention": ("confab rows have LOW doubt; fire iff neg_z_d >= tau, "
                             "equivalently z_d <= -tau"),
        "tau_frozen_method": "youden_j", "g0_auc_floor": 0.90, "layers": {},
    }

    for hs_index in hs_list:
        layer_name = layer_dir_name(hs_index)
        u_d = load_direction(
            committed / "layers" / layer_name / cn(f"u_d_{layer_name}.json"))
        layer_build = build_manifest["layers"][layer_name]
        mu_d, sigma_d = layer_build["mu_d"], layer_build["sigma_d"]

        def z_d_for(keys: list[str]) -> np.ndarray:
            h = np.stack([fresh[tensor_key(hs_index, rk)] for rk in keys])
            proj = h @ u_d
            return np.clip((proj - mu_d) / sigma_d, -2.0, 2.0)

        z_d = np.concatenate([z_d_for(confab_fit), z_d_for(known_fit)])
        score = -z_d
        y_tau, y_stats = youden_tau(score, labels)
        auc = roc_auc(score, labels)
        report["layers"][layer_name] = {
            "hs_index": hs_index, "auc_neg_z_d_on_fit": auc,
            "auc_raw_z_d_on_fit": roc_auc(z_d, labels),
            "youden_tau": {"tau": y_tau, "stats": y_stats}, "tau_frozen": y_tau,
            "g0_auc_pass": bool(auc >= 0.90),
        }

    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
