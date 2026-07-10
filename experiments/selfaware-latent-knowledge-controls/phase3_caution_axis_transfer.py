#!/usr/bin/env python3
"""Cross-regimen agreement of the over-refusal CAUTION axis (GPU-free).

C2 showed every regimen (SFT, GRPO+DPO, GRPO v2) carries a deep, lexically-clean
internal axis that predicts which KNOWN questions get over-refused, orthogonal to
the knowledge axis. That establishes "an axis of similar strength exists in each"
— but not that it is the SAME axis. This asks the stronger question: do the
independently-fit caution directions POINT THE SAME WAY across regimens?

Method. For each regimen, load the KNOWN rows' residual at one layer (default
L35), label over-refused (known_refused=1) vs answered (known_*_answered=0). Fit
all directions in a SHARED whitened frame (one StandardScaler fit on the POOLED
known activations of all regimens, so the coordinate system is common), then
report the pairwise |cosine| of the unit normals. High pairwise cosine ⇒ a single
shared caution mechanism the regimens inherit and reuse; low ⇒ regimen-specific
directions that merely happen to be similarly decodable.

Why cosine, not train-A/test-B transfer AUROC: the SelfAware questions are
identical across regimens (only the behavioral over-refusal labels differ), so a
transfer AUROC could ride question identity. The geometry of the fitted direction
vectors in residual space is not confounded that way.

A random-direction floor (shuffled labels, same fit) calibrates how much cosine
is expected by chance at this dimensionality. Tier 2 exploratory; no steering.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import phase3_latent_knowledge_probe as lkp

KNOWN_REFUSED = lkp.KNOWN_REFUSED


class TransferError(RuntimeError):
    pass


def load_known(extraction_dir: Path, behavior_rows: Path, *, layer: int,
               source: str = "h_lora") -> tuple[np.ndarray, np.ndarray, list[str]]:
    """KNOWN rows' residual at `layer` + over-refusal labels (1=known_refused)."""
    rows = []
    for line in behavior_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("label") != "known":
            continue
        rk = r.get("probe_pool_row_key")
        if rk is None:
            continue
        rows.append((rk, 1 if r.get("behavior_cell") == KNOWN_REFUSED else 0))
    if not rows:
        raise TransferError(f"no known rows in {behavior_rows}")
    keys = [k for k, _ in rows]
    y = np.array([v for _, v in rows])
    X = lkp.load_layer_matrix(extraction_dir, keys, layer, source=source)
    return X, y, keys


def _unit_direction(Xw: np.ndarray, y: np.ndarray, *, C: float = 0.5) -> np.ndarray:
    from sklearn.linear_model import LogisticRegression

    w = LogisticRegression(C=C, max_iter=2000).fit(Xw, np.asarray(y).astype(int)).coef_[0]
    n = np.linalg.norm(w)
    return w / n if n > 0 else w


def caution_axis_transfer(arms: list[dict[str, Any]], *, layer: int = 35,
                          source: str = "h_lora", seed: int = 0) -> dict[str, Any]:
    """arms: [{name, extraction_dir, behavior_rows}]. Returns the cross-regimen cosine matrix."""
    from sklearn.preprocessing import StandardScaler

    loaded = []
    for a in arms:
        X, y, keys = load_known(Path(a["extraction_dir"]), Path(a["behavior_rows"]),
                                layer=layer, source=source)
        loaded.append({"name": a["name"], "X": X, "y": y, "n": len(keys),
                       "n_refused": int(y.sum())})

    scaler = StandardScaler().fit(np.vstack([d["X"] for d in loaded]))  # shared frame
    rng = np.random.default_rng(seed)
    for d in loaded:
        Xw = scaler.transform(d["X"])
        d["dir"] = _unit_direction(Xw, d["y"])
        yshuf = d["y"].copy()
        rng.shuffle(yshuf)
        d["dir_rand"] = _unit_direction(Xw, yshuf)

    names = [d["name"] for d in loaded]
    cos = {}
    rand_cos = {}
    offdiag, offdiag_rand = [], []
    for i, di in enumerate(loaded):
        for j, dj in enumerate(loaded):
            c = round(float(abs(np.dot(di["dir"], dj["dir"]))), 4)
            cr = round(float(abs(np.dot(di["dir_rand"], dj["dir_rand"]))), 4)
            cos[f"{names[i]}|{names[j]}"] = c
            rand_cos[f"{names[i]}|{names[j]}"] = cr
            if i < j:
                offdiag.append(c)
                offdiag_rand.append(cr)

    mean_off = float(np.mean(offdiag)) if offdiag else 0.0
    mean_rand = float(np.mean(offdiag_rand)) if offdiag_rand else 0.0
    if mean_off > 0.5 and mean_off > 3 * max(mean_rand, 1e-6):
        verdict = "SHARED-AXIS"
        msg = (f"mean cross-regimen |cos|={mean_off:.3f} (random floor {mean_rand:.3f}); the "
               f"caution directions POINT THE SAME WAY across regimens — one shared mechanism "
               f"the regimens inherit, not regimen-specific axes.")
    elif mean_off > 2 * max(mean_rand, 1e-6):
        verdict = "PARTIAL-SHARED"
        msg = (f"mean cross-regimen |cos|={mean_off:.3f} vs random floor {mean_rand:.3f}; the "
               f"caution directions partially agree across regimens.")
    else:
        verdict = "REGIMEN-SPECIFIC"
        msg = (f"mean cross-regimen |cos|={mean_off:.3f} ~ random floor {mean_rand:.3f}; the "
               f"caution directions do NOT agree across regimens beyond chance.")
    return {
        "ok": True,
        "analysis_type": "phase3_caution_axis_transfer",
        "layer": layer,
        "source": source,
        "arms": [{"name": d["name"], "n_known": d["n"], "n_refused": d["n_refused"]} for d in loaded],
        "cosine_matrix": cos,
        "random_floor_matrix": rand_cos,
        "mean_cross_cosine": round(mean_off, 4),
        "mean_random_floor": round(mean_rand, 4),
        "verdict": verdict,
        "verdict_msg": msg,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", action="append", required=True, metavar="NAME:EXTRACTION_DIR:BEHAVIOR_ROWS",
                   help="repeatable; colon-joined regimen spec")
    p.add_argument("--layer", type=int, default=35)
    p.add_argument("--source", default="h_lora", choices=["h_lora", "h_base", "delta"])
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def _parse_arm(spec: str) -> dict[str, str]:
    name, ext, beh = spec.split(":", 2)
    return {"name": name, "extraction_dir": ext, "behavior_rows": beh}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    arms = [_parse_arm(s) for s in args.arm]
    result = caution_axis_transfer(arms, layer=args.layer, source=args.source)
    print(f"\nL{result['layer']} caution-axis cross-regimen agreement", file=sys.stderr)
    for k, v in result["cosine_matrix"].items():
        print(f"  |cos| {k:>28} = {v:.4f}  (rand {result['random_floor_matrix'][k]:.4f})",
              file=sys.stderr)
    print(f"VERDICT [{result['verdict']}]: {result['verdict_msg']}", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
