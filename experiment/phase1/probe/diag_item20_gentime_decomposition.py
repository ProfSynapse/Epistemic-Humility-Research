#!/usr/bin/env python3
"""Diagnostics bundle item 20 - generation-time doubt/caution-plane decomposition.

Question
--------
At generation time, how much of the hidden state's movement (relative to the
pre-generation anchor) lies along the DOUBT axis vs the CAUTION axis vs
orthogonal, at each of the captured positions?

The session-0035 off-axis finding (the prime writes ~92-99% off the doubt/caution
plane) was measured at the pre-gen ANCHOR only. This cell re-runs the
displacement decomposition at generation-time positions (first_vis, mid25/50/75,
answer_end) to ask whether the plane stays off-axis once the model is actually
emitting an answer.

Data (item-20 gentime capture, r2)
----------------------------------
- Produced by experiment/phase1/probe/amendment_ak_gentime_positions_extract.py
  (wrapper cloud/runpod_diag_gentime_positions.sh) at commit eb102f7b, on the
  deployed clean-SFT -> GRPO-v2 checkpoint, over pools/a0_pool_v21_questions.jsonl.
- 6 positions per row: anchor, first_vis, mid25, mid50, mid75, answer_end.
  Each is one safetensors holding L0..L36 (fp32, 2560-d).
- Only ANSWERED rows have captured states (refused rows carry positions=None).
  The r2 pool is 100% unknown-label; every answered row is a confabulation, so
  the "answered vs refused" outcome split collapses to a single group here
  (unknown-label confabulations). This is reported as a caveat, not worked around.

Axes (L35, layer-matched, checkpoint-matched to GRPO-v2)
-------------------------------------------------------
Reused from the canonical caution-residual artifacts + a doubt axis built with
the identical construction used inside build_caution_perp_direction.py:
    caution      = mean(known_refused)          - mean(known_correct_answered)
    doubt        = mean(known_correct_answered)  - mean(unknown_refused)
    caution_perp = caution - (caution . doubt_u) * doubt_u   (rank-1 doubt removed)
All three are read from JSON (theta), then unit-normalized here. doubt and
caution_perp are orthogonal by construction and span the 2-D "epistemic plane";
the raw caution direction is ~83% aligned with doubt (cos -0.83) and is reported
alongside for continuity with the raw-theta B1 line.

Gentime capture layers are L0..L36, so L35 (the canonical axis layer) is present:
NO refitting is done and NO nearest-layer fallback is needed.

Outputs
-------
- experiments/diag-item20-gentime-displacement/analysis-committed/gentime_decomposition.json
  (full numeric report, if promoted)
- experiments/diag-item20-gentime-displacement/analysis-committed/gentime_decomposition.md
  (small tables)

Deterministic: fixed row order, seeded bootstrap for the CIs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open

PROBE_DIR = Path(__file__).resolve().parent
AXIS_DIR = PROBE_DIR / "analysis/current_clean_grpo_v2_caution_residual_direction"
DEFAULT_DATA = None  # required arg; points at the extracted gentime data/ dir
OUT_DIR = (
    PROBE_DIR.parents[2]
    / "experiments"
    / "diag-item20-gentime-displacement"
    / "analysis-committed"
)
L = 35
POSITIONS = ["anchor", "first_vis", "mid25", "mid50", "mid75", "answer_end"]
GEN_POSITIONS = ["first_vis", "mid25", "mid50", "mid75", "answer_end"]
BOOT_N = 10000
BOOT_SEED = 20260705


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_axis(name: str) -> np.ndarray:
    d = json.loads((AXIS_DIR / f"{name}_direction_L35.json").read_text())
    assert d["layer"] == L, f"{name} axis is at layer {d['layer']}, expected {L}"
    return unit(np.asarray(d["theta"], dtype=np.float64))


def load_state(data_dir: Path, safe_key: str, pos: str) -> np.ndarray:
    path = data_dir / f"{safe_key}__{pos}.safetensors"
    with safe_open(str(path), "pt") as h:
        return h.get_tensor(f"L{L}").float().numpy().astype(np.float64)


def mean_ci(x: np.ndarray, rng: np.random.Generator) -> dict:
    """Mean with a percentile bootstrap 95% CI."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n": 0}
    idx = rng.integers(0, n, size=(BOOT_N, n))
    boot = x[idx].mean(axis=1)
    return {
        "mean": float(x.mean()),
        "ci_lo": float(np.percentile(boot, 2.5)),
        "ci_hi": float(np.percentile(boot, 97.5)),
        "n": int(n),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path,
                    help="extracted gentime data/ dir (rows.jsonl + *.safetensors)")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    rng = np.random.default_rng(BOOT_SEED)

    axes = {n: load_axis(n) for n in ("doubt", "caution", "caution_perp")}
    # sanity: doubt _|_ caution_perp by construction; caution ~ -0.83 with doubt
    cos_dc = float(axes["doubt"] @ axes["caution"])
    cos_dcp = float(axes["doubt"] @ axes["caution_perp"])
    cos_cp_c = float(axes["caution_perp"] @ axes["caution"])

    rows = [json.loads(l) for l in (args.data_dir / "rows.jsonl").open() if l.strip()]
    answered = [r for r in rows if r.get("answered") and r.get("positions")]
    answered.sort(key=lambda r: r["safe_key"])  # deterministic order
    n_ans = len(answered)
    n_refused = sum(1 for r in rows if r.get("refused"))

    # states[pos] -> [n_ans, 2560]
    states = {p: np.stack([load_state(args.data_dir, r["safe_key"], p)
                           for r in answered]) for p in POSITIONS}
    anchor = states["anchor"]

    # ---- Deliverable 1: absolute projection + residual fraction, per position ----
    # Absolute projection of the raw state onto each unit axis.
    # Residual fraction is defined on the DISPLACEMENT from anchor (deliverable 2's
    # object) since an absolute residual-of-state fraction is dominated by the huge
    # shared component and is uninformative; for the anchor row the displacement is
    # zero, so its residual fraction is reported as null.
    plane = np.stack([axes["doubt"], axes["caution_perp"]])  # [2, 2560] orthonormal

    per_position = {}
    for p in POSITIONS:
        S = states[p]
        proj = {a: (S @ axes[a]) for a in axes}
        disp = S - anchor
        disp_norm = np.linalg.norm(disp, axis=1)
        # component of displacement inside the doubt/caution_perp plane
        in_plane = disp @ plane.T                     # [n, 2]
        in_plane_norm = np.linalg.norm(in_plane, axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            plane_frac = np.where(disp_norm > 0, in_plane_norm / disp_norm, np.nan)
            resid_frac = np.where(disp_norm > 0,
                                  np.sqrt(np.clip(1 - plane_frac ** 2, 0, 1)), np.nan)
        entry = {
            "proj_doubt": mean_ci(proj["doubt"], rng),
            "proj_caution": mean_ci(proj["caution"], rng),
            "proj_caution_perp": mean_ci(proj["caution_perp"], rng),
            "disp_norm": mean_ci(disp_norm, rng),
        }
        if p != "anchor":
            valid = np.isfinite(resid_frac)
            entry["plane_frac_of_disp"] = mean_ci(plane_frac[valid], rng)
            entry["residual_frac_of_disp"] = mean_ci(resid_frac[valid], rng)
        per_position[p] = entry

    # ---- Deliverable 2: delta profile (position-minus-anchor along each axis) ----
    delta_profile = {}
    for p in GEN_POSITIONS:
        disp = states[p] - anchor
        d = {a: mean_ci(disp @ axes[a], rng) for a in axes}
        # signed variance-fraction of the per-row displacement carried by each axis
        disp_sq = (np.linalg.norm(disp, axis=1) ** 2)
        var_frac = {}
        for a in axes:
            comp = (disp @ axes[a]) ** 2
            with np.errstate(invalid="ignore", divide="ignore"):
                vf = np.where(disp_sq > 0, comp / disp_sq, np.nan)
            var_frac[a] = mean_ci(vf[np.isfinite(vf)], rng)
        delta_profile[p] = {"delta_along": d, "variance_frac_of_disp": var_frac}

    # ---- Deliverable 3: cosine of the MEAN displacement vector with each axis ----
    cos_mean_disp = {}
    for p in GEN_POSITIONS:
        mean_disp = (states[p] - anchor).mean(axis=0)
        mdu = unit(mean_disp)
        cos_mean_disp[p] = {a: float(mdu @ axes[a]) for a in axes}
        cos_mean_disp[p]["mean_disp_norm"] = float(np.linalg.norm(mean_disp))

    report = {
        "item": 20,
        "title": "generation-time doubt/caution-plane decomposition",
        "layer": L,
        "checkpoint": "clean-SFT -> GRPO-v2 (seed1)",
        "axes": {
            "source_dir": str(AXIS_DIR.relative_to(PROBE_DIR.parents[2])),
            "doubt": "mean(known_correct_answered) - mean(unknown_refused)",
            "caution": "mean(known_refused) - mean(known_correct_answered)",
            "caution_perp": "caution with rank-1 doubt removed",
            "cos_doubt_caution": cos_dc,
            "cos_doubt_caution_perp": cos_dcp,
            "cos_caution_perp_caution": cos_cp_c,
        },
        "n_pool": len(rows),
        "n_answered_with_states": n_ans,
        "n_refused_no_states": n_refused,
        "outcome_split_note": (
            "r2 pool is 100% unknown-label; all answered rows are confabulations "
            "and refused rows have no captured states -> single-group analysis "
            "(unknown-label confabulations); answered-vs-refused split not possible."),
        "positions": POSITIONS,
        "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED},
        "deliverable_1_per_position": per_position,
        "deliverable_2_delta_profile": delta_profile,
        "deliverable_3_cos_mean_displacement": cos_mean_disp,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "gentime_decomposition.json").write_text(json.dumps(report, indent=2))
    write_markdown(args.out_dir / "gentime_decomposition.md", report)
    print(f"wrote {args.out_dir}/gentime_decomposition.json (+ .md)")
    print(f"n_answered_with_states={n_ans}  n_refused_no_states={n_refused}")
    return 0


def _fmt(ci: dict, prec: int = 2) -> str:
    if ci is None or ci.get("mean") is None:
        return "-"
    return f"{ci['mean']:.{prec}f} [{ci['ci_lo']:.{prec}f}, {ci['ci_hi']:.{prec}f}]"


def write_markdown(path: Path, r: dict) -> None:
    ax = r["axes"]
    L = []
    L.append(f"# Item 20 - generation-time doubt/caution-plane decomposition (L{r['layer']})")
    L.append("")
    L.append(f"Checkpoint: {r['checkpoint']}. Axes from `{ax['source_dir']}`.")
    L.append(f"Axis geometry: cos(doubt, caution) = {ax['cos_doubt_caution']:.4f}, "
             f"cos(doubt, caution_perp) = {ax['cos_doubt_caution_perp']:.4f} "
             f"(orthogonal by construction), "
             f"cos(caution_perp, caution) = {ax['cos_caution_perp_caution']:.4f}.")
    L.append("")
    L.append(f"Rows: {r['n_answered_with_states']} answered (with states) of "
             f"{r['n_pool']} pool; {r['n_refused_no_states']} refused (no states). "
             f"{r['outcome_split_note']}")
    L.append("")
    L.append("## 1. Absolute projection per position (mean [95% CI])")
    L.append("")
    L.append("| position | proj doubt | proj caution | proj caution_perp | disp norm from anchor |")
    L.append("|---|---|---|---|---|")
    for p in r["positions"]:
        e = r["deliverable_1_per_position"][p]
        L.append(f"| {p} | {_fmt(e['proj_doubt'])} | {_fmt(e['proj_caution'])} | "
                 f"{_fmt(e['proj_caution_perp'])} | {_fmt(e['disp_norm'])} |")
    L.append("")
    L.append("Residual fraction of the displacement (fraction of the "
             "position-minus-anchor movement OUTSIDE the doubt/caution_perp plane):")
    L.append("")
    L.append("| position | in-plane frac | residual frac |")
    L.append("|---|---|---|")
    for p in r["positions"]:
        e = r["deliverable_1_per_position"][p]
        if "residual_frac_of_disp" in e:
            L.append(f"| {p} | {_fmt(e['plane_frac_of_disp'], 3)} | "
                     f"{_fmt(e['residual_frac_of_disp'], 3)} |")
    L.append("")
    L.append("## 2. Delta profile: displacement from anchor along each axis (mean [95% CI])")
    L.append("")
    L.append("| position | delta doubt | delta caution | delta caution_perp |")
    L.append("|---|---|---|---|")
    for p in GEN_POSITIONS:
        d = r["deliverable_2_delta_profile"][p]["delta_along"]
        L.append(f"| {p} | {_fmt(d['doubt'])} | {_fmt(d['caution'])} | "
                 f"{_fmt(d['caution_perp'])} |")
    L.append("")
    L.append("Per-row variance fraction of the displacement carried by each axis "
             "(mean [95% CI]):")
    L.append("")
    L.append("| position | var-frac doubt | var-frac caution | var-frac caution_perp |")
    L.append("|---|---|---|---|")
    for p in GEN_POSITIONS:
        v = r["deliverable_2_delta_profile"][p]["variance_frac_of_disp"]
        L.append(f"| {p} | {_fmt(v['doubt'], 4)} | {_fmt(v['caution'], 4)} | "
                 f"{_fmt(v['caution_perp'], 4)} |")
    L.append("")
    L.append("## 3. Cosine of the MEAN displacement vector with each axis")
    L.append("")
    L.append("| position | cos doubt | cos caution | cos caution_perp | mean disp norm |")
    L.append("|---|---|---|---|---|")
    for p in GEN_POSITIONS:
        c = r["deliverable_3_cos_mean_displacement"][p]
        L.append(f"| {p} | {c['doubt']:.4f} | {c['caution']:.4f} | "
                 f"{c['caution_perp']:.4f} | {c['mean_disp_norm']:.2f} |")
    L.append("")
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
