#!/usr/bin/env python3
"""Tier-1 read-don't-steer test for H_monitor (offline, GPU-free).

Step A.4 INJECTS the per-head failure axis F during generation and finds an
inverted causal sign (adding +F raises refusal). This script asks the dual,
purely READ question -- never steering anything:

    Does the prompt-token projection onto F predict which ANSWERED items the
    model gets WRONG, and does it beat the model's own stated confidence?

That is the selective-prediction framing Ferrando 2411.14257 and the SEP
literature use: a knowledge/uncertainty direction read BEFORE generation should
forecast hallucination. If the internal read out-predicts the verbalised
confidence, the residual stream carries calibration signal the model does not
say out loud.

Method (reuses the exact A.4 machinery so the read is byte-for-byte the axis
that was steered):
- Load the failure artifact: per-head unit theta and ITI sigma.
- Load the SAME extraction; for each row read the final-prompt-token head slice
  and project onto theta. Standardise by the head's sigma (so heads combine on a
  common ITI scale), then average across the localized heads -> one read score
  per row. Higher score == more "unknown-answered-wrong"-like by construction.
- Among ANSWERED items (arm.refused == False), label y = wrong (not correct) and
  compare two wrongness predictors by AUROC: the internal read vs (1 - stated
  confidence).

CIRCULARITY: F's positive pole IS the unknown-answered-wrong rows, so the
``unknown`` answered population is partly in-sample (optimistic). The ``known``
answered population was never touched by F's construction, so it is the clean
generalization headline; ``unknown`` and ``all`` are reported with that caveat.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_behavior_axis_scan import (  # noqa: E402
    load_extraction_rows,
    load_role_cube,
    rank_auc,
)
from phase3_head_localization_scan import validate_head_manifest  # noqa: E402
from phase3_sae_behavior_feature_analysis import row_arm  # noqa: E402
from phase3_sae_smoke import resolve_path  # noqa: E402

DEFAULT_FAILURE = (
    "experiment/phase1/probe/analysis/"
    "current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions/"
    "clean_sft_grpo_v2_seed1_unknown_failure_prompt_matched_steering/steering_directions.json"
)
DEFAULT_OUT = (
    "experiment/phase1/probe/analysis/"
    "current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_projection"
)


def _read_scores(failure: dict[str, Any]) -> tuple[np.ndarray, list[dict[str, Any]], list[dict[str, Any]]]:
    """Per-row aggregate read score onto F, plus the rows and per-head metadata.

    score[i] = mean_h ( (a_ih . theta_h) / sigma_h ) over heads with sigma_h > 0.
    """
    extraction_dir = resolve_path(failure["extraction_dir"])
    manifest_path = resolve_path(failure.get("extraction_manifest", extraction_dir / "manifest.json"))
    arm_role = failure.get("arm_role", "h_lora")
    manifest = validate_head_manifest(manifest_path, roles=[arm_role])
    head_dim = int(manifest["head_dim"])
    layer_count, width = manifest["tensor_shapes"][arm_role]

    override = failure.get("rows_path")
    rows_path = resolve_path(override) if override else None
    rows = load_extraction_rows(extraction_dir, rows_path=rows_path)
    cube = load_role_cube(extraction_dir, rows, role=arm_role, layer_count=layer_count, hidden_dim=width)

    heads: list[dict[str, Any]] = []
    per_head_std = []  # standardized projections, one (n_rows,) vector per usable head
    for d in failure["directions"]:
        layer = int(d["layer"])
        head = int(d["head"])
        sigma = float(d.get("sigma", 0.0))
        theta = np.asarray(d["theta"], dtype=np.float64)
        lo = head * head_dim
        hi = lo + head_dim
        slab = cube[:, layer, lo:hi].astype(np.float64)
        proj = slab @ theta
        usable = sigma > 1e-9
        heads.append({"layer": layer, "head": head, "sigma": sigma, "usable": usable})
        if usable:
            per_head_std.append(proj / sigma)
    if not per_head_std:
        raise RuntimeError("no usable heads (all sigma ~ 0)")
    score = np.mean(np.vstack(per_head_std), axis=0)
    return score, rows, heads


def _population(rows: list[dict[str, Any]], arm: str, *, label: str | None) -> np.ndarray:
    """Mask of ANSWERED rows (optionally within a known/unknown label)."""
    mask = np.zeros(len(rows), dtype=bool)
    for i, row in enumerate(rows):
        if label is not None and row.get("label") != label:
            continue
        payload = row_arm(row, arm)
        if bool(payload.get("refused")):
            continue
        mask[i] = True
    return mask


def _wrong_and_conf(rows: list[dict[str, Any]], arm: str, mask: np.ndarray):
    idx = np.flatnonzero(mask)
    wrong = np.array([not bool(row_arm(rows[i], arm).get("correct")) for i in idx], dtype=bool)
    conf_raw = [row_arm(rows[i], arm).get("stated_confidence") for i in idx]
    has_conf = np.array([c is not None for c in conf_raw], dtype=bool)
    conf = np.array([float(c) if c is not None else np.nan for c in conf_raw], dtype=np.float64)
    return idx, wrong, conf, has_conf


def _auc_pair(score: np.ndarray, rows, arm, mask: np.ndarray) -> dict[str, Any]:
    idx, wrong, conf, has_conf = _wrong_and_conf(rows, arm, mask)
    n = int(idx.size)
    n_wrong = int(np.count_nonzero(wrong))
    out: dict[str, Any] = {
        "n_answered": n,
        "n_wrong": n_wrong,
        "n_correct": n - n_wrong,
        "n_with_stated_confidence": int(np.count_nonzero(has_conf)),
    }
    if n_wrong == 0 or n_wrong == n:
        out["auroc_read_predicts_wrong"] = None
        out["auroc_confidence_predicts_wrong"] = None
        out["read_minus_confidence"] = None
        out["note"] = "degenerate: all-correct or all-wrong; AUROC undefined"
        return out
    auc_read = rank_auc(score[idx].astype(np.float64), wrong)
    out["auroc_read_predicts_wrong"] = round(float(auc_read), 4)
    # Stated confidence: well-calibrated -> low confidence predicts wrong, so the
    # wrongness score is (1 - confidence). Only over rows that carry a confidence.
    conf_idx = np.flatnonzero(has_conf)
    if conf_idx.size > 0 and 0 < int(np.count_nonzero(wrong[conf_idx])) < conf_idx.size:
        auc_conf = rank_auc((1.0 - conf[conf_idx]).astype(np.float64), wrong[conf_idx])
        out["auroc_confidence_predicts_wrong"] = round(float(auc_conf), 4)
        # Recompute read AUROC on the SAME confidence-bearing subset for a fair gap.
        auc_read_conf_subset = rank_auc(score[idx][conf_idx].astype(np.float64), wrong[conf_idx])
        out["auroc_read_on_confidence_subset"] = round(float(auc_read_conf_subset), 4)
        out["read_minus_confidence"] = round(float(auc_read_conf_subset - auc_conf), 4)
    else:
        out["auroc_confidence_predicts_wrong"] = None
        out["read_minus_confidence"] = None
        out["note"] = "stated confidence absent or degenerate on this population"
    return out


def run(failure_path: Path, out_root: Path) -> dict[str, Any]:
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    arm = failure["behavior_arm"]
    score, rows, heads = _read_scores(failure)

    populations = {
        "known_answered_GENERALIZATION": _population(rows, arm, label="known"),
        "unknown_answered_in_sample": _population(rows, arm, label="unknown"),
        "all_answered": _population(rows, arm, label=None),
    }
    results = {name: _auc_pair(score, rows, arm, mask) for name, mask in populations.items()}

    headline = results["known_answered_GENERALIZATION"]
    summary = {
        "ok": True,
        "analysis_type": "phase3_head_read_projection",
        "failure_directions": str(failure_path),
        "behavior_arm": arm,
        "n_rows": len(rows),
        "n_heads_total": len(heads),
        "n_heads_usable": int(sum(h["usable"] for h in heads)),
        "read_score": "mean over usable heads of (final_prompt_token . theta) / sigma",
        "populations": results,
        "verdict": _verdict(headline),
        "circularity_note": (
            "F's positive pole is the unknown-answered-wrong rows; the unknown_answered "
            "population is partly in-sample (optimistic). known_answered is the clean "
            "generalization headline -- F never saw any known row."
        ),
    }
    out_root.mkdir(parents=True, exist_ok=True)
    out_path = out_root / "read_projection.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["_written"] = str(out_path)
    return summary


def _verdict(headline: dict[str, Any]) -> str:
    auc = headline.get("auroc_read_predicts_wrong")
    gap = headline.get("read_minus_confidence")
    if auc is None:
        return (
            "INCONCLUSIVE (generalization): known-answered population is degenerate "
            "(too few wrong answers) -- the clean read test cannot run; rely on the "
            "in-sample unknown population with its optimism caveat."
        )
    if auc <= 0.55:
        base = (
            f"READ DOES NOT GENERALIZE: prompt-token F-projection barely predicts wrongness "
            f"on held-out known-answered items (AUROC={auc:.2f}). The failure axis is a "
            f"decision/output direction, not a pre-generation knowledge read."
        )
    else:
        base = (
            f"READ CARRIES SIGNAL: prompt-token F-projection predicts wrongness on held-out "
            f"known-answered items (AUROC={auc:.2f}) -- selective-prediction evidence the axis "
            f"is read pre-generation, a la Ferrando/SEP."
        )
    if gap is not None:
        if gap > 0.03:
            base += f" It BEATS stated confidence by {gap:+.2f} AUROC (internal > verbalised)."
        elif gap < -0.03:
            base += f" Stated confidence beats it by {-gap:.2f} AUROC (verbalised > internal)."
        else:
            base += f" It roughly ties stated confidence ({gap:+.2f} AUROC)."
    return base


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-directions", type=Path, default=Path(DEFAULT_FAILURE))
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(resolve_path(str(args.failure_directions)), resolve_path(str(args.out)))
    for name, r in summary["populations"].items():
        print(
            f"[{name}] n={r['n_answered']} wrong={r['n_wrong']} "
            f"AUROC(read)={r.get('auroc_read_predicts_wrong')} "
            f"AUROC(conf)={r.get('auroc_confidence_predicts_wrong')} "
            f"read-conf={r.get('read_minus_confidence')}",
            file=sys.stderr,
        )
    print(f"\nVERDICT: {summary['verdict']}", file=sys.stderr)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
