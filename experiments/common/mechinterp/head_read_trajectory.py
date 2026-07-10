#!/usr/bin/env python3
"""Read the failure-axis projection ACROSS generated positions (Tier-2 trajectory).

Step A.4 INJECTS the per-head failure axis F at every generated token and finds
an inverted causal sign (adding +F raises refusal), while the Tier-1 geometry
test showed F *is* the refuse<->answer decision axis read at the prompt token.
The open puzzle is a READ/WRITE sign mismatch: F is built from prompt-token reads
but injected during generation. This harness closes the loop by READING (never
steering) the natural projection onto F at each generated position.

Two halves:

1. A torch forward-PRE-hook on each target ``self_attn.o_proj`` that, per forward
   call, records the projection of the LAST position's per-head o_proj input onto
   that head's theta. During ``model.generate`` the prefill call captures the
   final-prompt-token read (forward 0) and each subsequent decode call captures
   one generated position. Mirrors ``phase3_head_intervention`` so it reads the
   SAME surface A.4 wrote to. The GPU wiring lives in the runner; this module is
   unit-tested offline against a tiny torch model.

2. Pure-numpy aggregation + a sign-flip verdict over the per-row trajectories the
   runner emits. The headline contrast is F's own construction groups
   (unknown-answered-wrong vs unknown-refused): if their separation along F is
   POSITIVE at the prompt token (in-sample, by construction) but flips NEGATIVE
   across generated positions, that read/write sign flip mechanically explains why
   +F injected during generation pushes toward refusal.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from head_intervention import discover_o_proj_modules  # noqa: E402


class HeadReadTrajectoryError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# read-hook mechanism (torch tensors used through their own methods)
# ---------------------------------------------------------------------------

def build_block_read_specs(directions: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    """Group target heads by block: ``{block: [{layer, head, lo, hi, theta, sigma}]}``."""
    by_block: dict[int, list[dict[str, Any]]] = {}
    for entry in directions:
        layer = int(entry["layer"])
        head = int(entry["head"])
        head_dim = int(entry["head_dim"])
        theta = [float(t) for t in entry["theta"]]
        sigma = float(entry["sigma"])
        if len(theta) != head_dim:
            raise HeadReadTrajectoryError(
                f"L{layer}H{head}: theta length {len(theta)} != head_dim {head_dim}"
            )
        lo = head * head_dim
        hi = lo + head_dim
        by_block.setdefault(layer, []).append(
            {"layer": layer, "head": head, "lo": lo, "hi": hi, "theta": theta, "sigma": sigma}
        )
    return by_block


def make_oproj_read_hook(head_specs: list[dict[str, Any]], *, store: dict[tuple[int, int], list[float]]):
    """Forward PRE-hook recording each head's LAST-position projection onto theta.

    ``store[(layer, head)]`` accumulates one float per forward call (forward 0 is
    the prefill = final prompt token; forwards 1.. are decode steps). The hook
    does NOT modify the input — it returns None so o_proj sees the natural input.
    """

    def _hook(_module: Any, args: tuple[Any, ...]):
        x = args[0]  # [batch, seq, num_heads*head_dim]
        last = x[0, -1, :].float()
        for spec in head_specs:
            seg = last[spec["lo"]:spec["hi"]]
            theta = seg.new_tensor(spec["theta"])
            proj = float((seg @ theta).item())
            store.setdefault((spec["layer"], spec["head"]), []).append(proj)
        return None

    return _hook


@contextmanager
def per_head_read(model: Any, by_block: dict[int, list[dict[str, Any]]], *, num_hidden_layers: int,
                  store: dict[tuple[int, int], list[float]]):
    """Register read pre-hooks on every target block's o_proj; remove on exit."""
    modules = discover_o_proj_modules(model, num_hidden_layers=num_hidden_layers)
    handles = []
    try:
        for block_id, head_specs in by_block.items():
            if block_id not in modules:
                raise HeadReadTrajectoryError(f"target block {block_id} not found among o_proj modules")
            handles.append(modules[block_id].register_forward_pre_hook(make_oproj_read_hook(head_specs, store=store)))
        yield store
    finally:
        for handle in handles:
            handle.remove()


# ---------------------------------------------------------------------------
# pure-numpy per-row summary + offline aggregation/verdict
# ---------------------------------------------------------------------------

def summarize_row_trajectory(store: dict[tuple[int, int], list[float]],
                             sigma_map: dict[tuple[int, int], float]) -> dict[str, Any]:
    """Per-row trajectory summary from one generate()'s captured store.

    Returns prompt-token vs generation-position reads, standardized by per-head
    sigma so heads combine on a common ITI scale.
    """
    keys = sorted(store)
    if not keys:
        raise HeadReadTrajectoryError("empty read store; no o_proj hooks fired")
    lengths = {len(store[k]) for k in keys}
    if len(lengths) != 1:
        raise HeadReadTrajectoryError(f"ragged trajectories across heads: lengths={lengths}")
    n_forward = lengths.pop()
    # [n_head, n_forward] standardized projections.
    std = np.array([[p / sigma_map[k] for p in store[k]] for k in keys], dtype=np.float64)
    agg = std.mean(axis=0)  # mean over heads, per forward
    prompt_std = float(agg[0])
    gen_std = float(agg[1:].mean()) if n_forward > 1 else float("nan")
    return {
        "n_forward": n_forward,
        "prompt_read_std": prompt_std,
        "gen_read_std": gen_std,
        "agg_trajectory_std": [round(float(v), 5) for v in agg],
        "prompt_read_per_head": {f"L{l}H{h}": round(float(std[i, 0]), 5) for i, (l, h) in enumerate(keys)},
    }


def _is_unknown_answered_wrong(row: dict[str, Any]) -> bool:
    return row.get("label") == "unknown" and not bool(row.get("refused")) and not bool(row.get("correct"))


def _is_unknown_refused(row: dict[str, Any]) -> bool:
    return row.get("label") == "unknown" and bool(row.get("refused"))


def analyze_trajectories(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Sign-flip test on F's construction groups across prompt vs generation."""
    pos = [r for r in rows if _is_unknown_answered_wrong(r)]
    neg = [r for r in rows if _is_unknown_refused(r)]

    def _sep(field: str) -> tuple[float, float, float]:
        p = np.array([float(r[field]) for r in pos if r.get(field) is not None and np.isfinite(r[field])])
        n = np.array([float(r[field]) for r in neg if r.get(field) is not None and np.isfinite(r[field])])
        if p.size == 0 or n.size == 0:
            return float("nan"), float("nan"), float("nan")
        return float(p.mean()), float(n.mean()), float(p.mean() - n.mean())

    prompt_pos, prompt_neg, prompt_sep = _sep("prompt_read_std")
    gen_pos, gen_neg, gen_sep = _sep("gen_read_std")

    summary = {
        "ok": True,
        "analysis_type": "phase3_head_read_trajectory",
        "n_rows": len(rows),
        "groups": {
            "unknown_answered_wrong": len(pos),
            "unknown_refused": len(neg),
        },
        "prompt_token": {"pos_mean": round(prompt_pos, 4), "neg_mean": round(prompt_neg, 4),
                         "separation_pos_minus_neg": round(prompt_sep, 4)},
        "generation": {"pos_mean": round(gen_pos, 4), "neg_mean": round(gen_neg, 4),
                       "separation_pos_minus_neg": round(gen_sep, 4)},
        "verdict": _verdict(prompt_sep, gen_sep),
    }
    return summary


def _verdict(prompt_sep: float, gen_sep: float) -> str:
    if not (np.isfinite(prompt_sep) and np.isfinite(gen_sep)):
        return "INCONCLUSIVE: one construction group is empty; cannot compare prompt vs generation."
    flipped = (prompt_sep > 0) != (gen_sep > 0)
    if flipped and prompt_sep > 0 and gen_sep < 0:
        return (
            f"SIGN FLIP CONFIRMED: unknown-wrong vs unknown-refused separate +{prompt_sep:.2f} along F at "
            f"the prompt token (in-sample, by construction) but {gen_sep:.2f} during generation. The axis "
            f"reverses meaning between read-time and write-time, mechanically explaining why +F injected at "
            f"generation pushes toward REFUSAL (A.4's inverted causal sign)."
        )
    if flipped:
        return (
            f"PARTIAL FLIP: prompt separation {prompt_sep:+.2f}, generation separation {gen_sep:+.2f} "
            f"(signs differ but not in the predicted prompt+/gen- direction); report both and inspect the "
            f"per-position trajectory."
        )
    return (
        f"NO FLIP: separation keeps its sign (prompt {prompt_sep:+.2f}, generation {gen_sep:+.2f}). The "
        f"read/write-mismatch explanation is NOT supported by the trajectory; the inversion lives elsewhere."
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
    parser.add_argument("--rows", required=True, type=Path, help="runner rows.jsonl with per-row trajectory summaries")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = run_analysis(args.rows, args.out)
    p, g = summary["prompt_token"], summary["generation"]
    print(
        f"prompt sep={p['separation_pos_minus_neg']}  generation sep={g['separation_pos_minus_neg']}\n"
        f"VERDICT: {summary['verdict']}",
        file=sys.stderr,
    )
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
