#!/usr/bin/env python3
"""Read the CAUTION-axis residual projection ACROSS generated positions (Tier-2).

The A2 within-known control shows the residual stream linearly separates
over-refusals (``known_refused``) from answered knowns (``known_correct_answered``)
at the FINAL PROMPT TOKEN (AUROC ~0.91, peak L35), on an axis orthogonal to the
known/unknown knowledge axis. Because that read is taken before any token is
emitted, it already falsifies a pure *decision-echo* of emitted refusal words.

This harness adds the position-resolved half B2 asks for: does the caution signal
persist across GENERATED positions, and specifically in the **pre-lexical window**
— the generated positions BEFORE the refusal phrase ("I don't know...") surfaces?
A separation that is already present pre-lexically is a held-out (out-of-fit)
*pre-commitment* signal, not an artifact of reading the model's own emitted
refusal tokens. (Whether that pre-committed state *causes* the refusal — monitor
vs. internal decision — is causal and stays B1's territory; a read-only timing
test cannot settle it.)

Two halves, mirroring ``phase3_head_read_trajectory`` but for the residual stream
(full-vector direction at one layer rather than a per-head o_proj segment):

1. A torch forward POST-hook on the target decoder block records, per forward
   call, the projection of the LAST position's residual (the block output) onto a
   raw mass-mean caution direction theta. During ``model.generate`` the prefill
   call captures the final-prompt-token read (forward 0) and each subsequent
   decode call captures one generated position. The GPU wiring lives in the
   runner; this module is unit-tested offline.

2. Pure-numpy direction fit + per-row trajectory summary (prompt / generation /
   pre-lexical / post-lexical) + a pre-commitment-vs-echo verdict over the
   construction groups (known_refused vs known_correct_answered).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

KNOWN_REFUSED = "known_refused"
KNOWN_ANSWERED = "known_correct_answered"

# Refusal-phrase markers used to locate where the abstention lexicon surfaces in
# the generated text. Matched against cumulative lowercased generated text; the
# first generated position whose cumulative text contains any marker is the
# lexical onset. Kept conservative (whole abstention phrases), apostrophe-robust.
REFUSAL_MARKERS = (
    "i don't know",
    "i dont know",
    "i do not know",
    "don't know the answer",
    "dont know the answer",
    "do not know the answer",
    "not known to me",
    "i'm not sure",
    "im not sure",
    "i am not sure",
    "unable to answer",
    "cannot answer",
    "can't answer",
    "no answer",
    "beyond the scope of my knowledge",
    "beyond my knowledge",
    "scope of my knowledge",
    "outside my knowledge",
    "outside the scope",
    "afraid that's beyond",
    "afraid thats beyond",
)


class ResidualReadTrajectoryError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# pure-numpy direction fit (offline-testable)
# ---------------------------------------------------------------------------

def mass_mean_direction(x_pos: np.ndarray, x_neg: np.ndarray) -> np.ndarray:
    """Unit mass-mean difference ``unit(mean(x_pos) - mean(x_neg))`` in RAW space.

    This is the ITI-standard direction (matches the failure-axis F construction)
    and, unlike a whitened logistic normal, applies frame-consistently to
    generation-position residuals the scaler was never fit on.
    """
    if x_pos.ndim != 2 or x_neg.ndim != 2:
        raise ResidualReadTrajectoryError("x_pos/x_neg must be 2-D [n, hidden]")
    if x_pos.shape[1] != x_neg.shape[1]:
        raise ResidualReadTrajectoryError(
            f"hidden dim mismatch: pos {x_pos.shape[1]} vs neg {x_neg.shape[1]}")
    if x_pos.shape[0] == 0 or x_neg.shape[0] == 0:
        raise ResidualReadTrajectoryError("both groups must be non-empty")
    diff = x_pos.mean(axis=0) - x_neg.mean(axis=0)
    norm = float(np.linalg.norm(diff))
    if norm == 0.0:
        raise ResidualReadTrajectoryError("degenerate direction: pos/neg means coincide")
    return (diff / norm).astype(np.float64)


def projection_sigma(x_all: np.ndarray, theta: np.ndarray) -> float:
    """Std of the raw projection over all rows — the standardization scale."""
    proj = x_all @ theta
    sigma = float(np.std(proj))
    return sigma if sigma > 0 else 1.0


def projection_auroc(x_pos: np.ndarray, x_neg: np.ndarray, theta: np.ndarray) -> float:
    """In-sample AUROC of the raw projection separating pos (1) from neg (0).

    Reported as a construction sanity check on the fitted direction, NOT a
    held-out claim (theta is the mass-mean of these same groups).
    """
    p = x_pos @ theta
    n = x_neg @ theta
    try:
        from sklearn.metrics import roc_auc_score

        y = np.concatenate([np.ones(len(p)), np.zeros(len(n))])
        s = np.concatenate([p, n])
        return float(roc_auc_score(y, s))
    except ModuleNotFoundError:
        # Mann-Whitney U / pairwise definition. Ties get half credit.
        greater = (p[:, None] > n[None, :]).sum()
        ties = (p[:, None] == n[None, :]).sum()
        return float((greater + 0.5 * ties) / (len(p) * len(n)))


# ---------------------------------------------------------------------------
# read-hook mechanism (torch tensors used through their own methods)
# ---------------------------------------------------------------------------

def build_residual_read_spec(direction: dict[str, Any]) -> dict[str, Any]:
    """Validate a fitted direction dict -> ``{layer, block, theta, sigma}``.

    ``block`` is the decoder block index whose OUTPUT equals hidden_states[layer]
    (Transformers convention: hidden_states[0] is embeddings, so block = layer-1).
    """
    layer = int(direction["layer"])
    if layer <= 0:
        raise ResidualReadTrajectoryError(
            "caution axis lives in the residual stream of a decoder block; layer 0 is embeddings")
    theta = [float(t) for t in direction["theta"]]
    sigma = float(direction["sigma"])
    if sigma <= 0:
        raise ResidualReadTrajectoryError(f"sigma must be positive, got {sigma}")
    return {"layer": layer, "block": layer - 1, "theta": theta, "sigma": sigma}


def make_residual_read_hook(spec: dict[str, Any], *, store: list[float]):
    """Forward POST-hook recording the LAST position's residual projection onto theta.

    ``store`` accumulates one float per forward call (forward 0 is the prefill =
    final prompt token; forwards 1.. are decode steps). The hook does NOT modify
    the block output — it returns None so generation is the natural baseline.
    """

    def _hook(_module: Any, _args: tuple[Any, ...], output: Any):
        hs = output[0] if isinstance(output, tuple) else output
        last = hs[0, -1, :].float()
        theta = last.new_tensor(spec["theta"])
        store.append(float((last @ theta).item()))
        return None

    return _hook


@contextmanager
def residual_read(model: Any, spec: dict[str, Any], *, store: list[float]):
    """Register a read post-hook on the target decoder block; remove on exit."""
    from phase3_causal_pilot_runner import find_decoder_layers  # noqa: PLC0415

    layers = find_decoder_layers(model)
    block = spec["block"]
    n = len(layers)
    if not (0 <= block < n):
        raise ResidualReadTrajectoryError(
            f"target block {block} out of range for model with {n} decoder layers")
    handle = layers[block].register_forward_hook(make_residual_read_hook(spec, store=store))
    try:
        yield store
    finally:
        handle.remove()


# ---------------------------------------------------------------------------
# lexical onset + per-row summary + offline aggregation/verdict
# ---------------------------------------------------------------------------

def find_lexical_onset(generated_tokens: list[str], markers: tuple[str, ...] = REFUSAL_MARKERS) -> int | None:
    """Trajectory index of the first generated position whose cumulative text hits a marker.

    ``generated_tokens[j]`` is the decoded text of generated token j (j=0 is the
    first generated token). Returns the TRAJECTORY index (j+1, since position 0 is
    the prompt-token prefill read), or None if no refusal phrase is emitted.
    """
    cumulative = ""
    norm_markers = [m.lower() for m in markers]
    for j, tok in enumerate(generated_tokens):
        cumulative += tok
        low = re.sub(r"\s+", " ", cumulative.lower())
        if any(m in low for m in norm_markers):
            return j + 1
    return None


def summarize_row_trajectory(projections: list[float], sigma: float, *,
                             lexical_onset_idx: int | None) -> dict[str, Any]:
    """Per-row trajectory summary from one generate()'s captured projections.

    ``projections[0]`` is the prompt-token read; ``projections[1:]`` are the
    generated positions. Standardized by sigma so rows combine on a common scale.
    The pre-lexical window is generated positions ``[1, onset)``; the post-lexical
    window is ``[onset, end)``. With no refusal phrase, the whole generation is
    "pre-lexical" (the abstention lexicon never surfaced).
    """
    if not projections:
        raise ResidualReadTrajectoryError("empty projection list; no residual hook fired")
    if sigma <= 0:
        raise ResidualReadTrajectoryError(f"sigma must be positive, got {sigma}")
    std = [p / sigma for p in projections]
    n_forward = len(std)
    prompt_std = float(std[0])
    gen = std[1:]
    gen_std = float(np.mean(gen)) if gen else float("nan")
    onset = lexical_onset_idx
    if onset is None:
        pre = gen
        post: list[float] = []
    else:
        pre = std[1:onset]
        post = std[onset:]
    pre_std = float(np.mean(pre)) if pre else float("nan")
    post_std = float(np.mean(post)) if post else float("nan")
    return {
        "n_forward": n_forward,
        "lexical_onset_idx": onset,
        "prompt_read_std": prompt_std,
        "gen_read_std": gen_std,
        "pre_lexical_read_std": pre_std,
        "post_lexical_read_std": post_std,
        "agg_trajectory_std": [round(float(v), 5) for v in std],
    }


def _sep(rows_pos: list[dict[str, Any]], rows_neg: list[dict[str, Any]],
         field: str) -> tuple[float, float, float, int, int]:
    p = np.array([float(r[field]) for r in rows_pos
                  if r.get(field) is not None and np.isfinite(r[field])])
    n = np.array([float(r[field]) for r in rows_neg
                  if r.get(field) is not None and np.isfinite(r[field])])
    if p.size == 0 or n.size == 0:
        return float("nan"), float("nan"), float("nan"), int(p.size), int(n.size)
    return float(p.mean()), float(n.mean()), float(p.mean() - n.mean()), int(p.size), int(n.size)


def analyze_trajectories(rows: list[dict[str, Any]], *, sep_tol: float = 0.10) -> dict[str, Any]:
    """Pre-commitment-vs-echo test on known_refused vs known_correct_answered."""
    pos = [r for r in rows if r.get("behavior_cell") == KNOWN_REFUSED]
    neg = [r for r in rows if r.get("behavior_cell") == KNOWN_ANSWERED]

    fields = ("prompt_read_std", "gen_read_std", "pre_lexical_read_std", "post_lexical_read_std")
    sep: dict[str, dict[str, Any]] = {}
    for f in fields:
        pm, nm, d, np_, nn_ = _sep(pos, neg, f)
        sep[f] = {"pos_mean": round(pm, 4), "neg_mean": round(nm, 4),
                  "separation_pos_minus_neg": round(d, 4), "n_pos": np_, "n_neg": nn_}

    prompt_sep = sep["prompt_read_std"]["separation_pos_minus_neg"]
    pre_sep = sep["pre_lexical_read_std"]["separation_pos_minus_neg"]
    post_sep = sep["post_lexical_read_std"]["separation_pos_minus_neg"]

    return {
        "ok": True,
        "analysis_type": "phase3_residual_read_trajectory",
        "n_rows": len(rows),
        "groups": {KNOWN_REFUSED: len(pos), KNOWN_ANSWERED: len(neg)},
        "separation": sep,
        "verdict": _verdict(prompt_sep, pre_sep, post_sep, sep_tol=sep_tol),
    }


def _verdict(prompt_sep: float, pre_sep: float, post_sep: float, *, sep_tol: float) -> str:
    if not np.isfinite(prompt_sep):
        return "INCONCLUSIVE: a construction group is empty at the prompt token; cannot compare."
    # prompt_sep is positive by construction (theta is the mass-mean of these
    # groups read at the prompt token); the HELD-OUT evidence is the generation
    # window, where theta is applied to positions it was not fit on.
    pre_ok = np.isfinite(pre_sep) and abs(pre_sep) >= sep_tol
    if pre_ok and (pre_sep > 0) == (prompt_sep > 0):
        tail = ""
        if np.isfinite(post_sep):
            tail = (f" Post-lexical separation is {post_sep:+.2f}; the signal "
                    f"{'grows' if abs(post_sep) > abs(pre_sep) else 'persists'} once the "
                    f"abstention phrase surfaces.")
        return (
            f"PRE-COMMITMENT: the caution axis separates known_refused from "
            f"known_correct_answered during generation BEFORE the refusal lexicon "
            f"(pre-lexical sep {pre_sep:+.2f}, same sign as the by-construction prompt "
            f"sep {prompt_sep:+.2f}). The signal is held out-of-fit on generation "
            f"positions and is not an echo of emitted refusal words.{tail}"
        )
    if not np.isfinite(pre_sep) or abs(pre_sep) < sep_tol:
        if np.isfinite(post_sep) and abs(post_sep) >= sep_tol:
            return (
                f"DECISION-ECHO: the caution separation is ~0 pre-lexically "
                f"({pre_sep:+.2f}) but emerges post-lexically ({post_sep:+.2f}); on the "
                f"generation surface the axis tracks the emitted refusal words, not a "
                f"pre-committed state. (Note: the held-out prompt-token A2 result still "
                f"stands independently.)"
            )
        return (
            f"WEAK: pre-lexical separation {pre_sep:+.2f} and post-lexical {post_sep:+.2f} "
            f"are both below tol {sep_tol:.2f}; the generation-position read is uninformative "
            f"(rely on the prompt-token A2 result)."
        )
    return (
        f"SIGN-INCONSISTENT: prompt sep {prompt_sep:+.2f} but pre-lexical sep {pre_sep:+.2f} "
        f"(opposite sign); report both and inspect the per-position trajectory."
    )


def run_analysis(rows_path: Path, out_path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    summary = analyze_trajectories(rows)
    summary["rows"] = str(rows_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["_written"] = str(out_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True, type=Path,
                        help="runner rows.jsonl with per-row trajectory summaries")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = run_analysis(args.rows, args.out)
    s = summary["separation"]
    print(
        f"prompt sep={s['prompt_read_std']['separation_pos_minus_neg']}  "
        f"pre-lexical sep={s['pre_lexical_read_std']['separation_pos_minus_neg']}  "
        f"post-lexical sep={s['post_lexical_read_std']['separation_pos_minus_neg']}\n"
        f"VERDICT: {summary['verdict']}",
        file=sys.stderr,
    )
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
