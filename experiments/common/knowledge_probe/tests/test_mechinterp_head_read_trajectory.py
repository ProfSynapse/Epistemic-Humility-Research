from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import head_read_trajectory as traj  # noqa: E402

NUM_HEADS = 2
HEAD_DIM = 3
WIDTH = NUM_HEADS * HEAD_DIM
NUM_LAYERS = 2


class _OProj(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(WIDTH, WIDTH, bias=False)
        torch.nn.init.eye_(self.linear.weight)

    def forward(self, x):
        return self.linear(x)


class _Attn(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.o_proj = _OProj()


class _Block(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = _Attn()


class _Model(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList([_Block() for _ in range(NUM_LAYERS)])

    def forward(self, x):
        for block in self.layers:
            block.self_attn.o_proj(x)
        return x


def _directions():
    # Target head 1 in each layer; theta picks out slot0 of that head.
    out = []
    for layer in range(NUM_LAYERS):
        out.append({"layer": layer, "head": 1, "head_dim": HEAD_DIM,
                    "theta": [1.0, 0.0, 0.0], "sigma": 2.0})
    return out


def test_read_hook_captures_last_position_projection():
    model = _Model()
    directions = _directions()
    by_block = traj.build_block_read_specs(directions)
    sigma_map = {(int(d["layer"]), int(d["head"])): float(d["sigma"]) for d in directions}

    store: dict[tuple[int, int], list[float]] = {}
    with traj.per_head_read(model, by_block, num_hidden_layers=NUM_LAYERS, store=store):
        # Two forwards: a "prefill" (seq=2, last position slot0 of head1 = 5.0)
        # and a "decode" (seq=1, slot0 of head1 = 9.0).
        prefill = torch.zeros(1, 2, WIDTH)
        prefill[0, -1, HEAD_DIM + 0] = 5.0  # head1 slot0 at final position
        model(prefill)
        decode = torch.zeros(1, 1, WIDTH)
        decode[0, -1, HEAD_DIM + 0] = 9.0
        model(decode)

    # Each target head saw two forwards; projection == slot0 value (theta=e0).
    for layer in range(NUM_LAYERS):
        assert store[(layer, 1)] == pytest.approx([5.0, 9.0])

    summary = traj.summarize_row_trajectory(store, sigma_map)
    assert summary["n_forward"] == 2
    # standardized by sigma=2.0: prompt 5/2=2.5, gen mean 9/2=4.5.
    assert summary["prompt_read_std"] == pytest.approx(2.5)
    assert summary["gen_read_std"] == pytest.approx(4.5)
    assert summary["agg_trajectory_std"] == pytest.approx([2.5, 4.5])


def test_analyze_sign_flip_confirmed():
    # unknown-wrong projects HIGH at prompt, LOW during generation; unknown-refused
    # the reverse -> prompt separation +, generation separation -.
    rows = []
    for i in range(5):
        rows.append({"label": "unknown", "refused": False, "correct": False,
                     "prompt_read_std": 1.0, "gen_read_std": -1.0})
        rows.append({"label": "unknown", "refused": True, "correct": False,
                     "prompt_read_std": -1.0, "gen_read_std": 1.0})
    summary = traj.analyze_trajectories(rows)
    assert summary["prompt_token"]["separation_pos_minus_neg"] == pytest.approx(2.0)
    assert summary["generation"]["separation_pos_minus_neg"] == pytest.approx(-2.0)
    assert "SIGN FLIP CONFIRMED" in summary["verdict"]


def test_analyze_no_flip():
    rows = []
    for i in range(4):
        rows.append({"label": "unknown", "refused": False, "correct": False,
                     "prompt_read_std": 1.0, "gen_read_std": 0.8})
        rows.append({"label": "unknown", "refused": True, "correct": False,
                     "prompt_read_std": -1.0, "gen_read_std": -0.7})
    summary = traj.analyze_trajectories(rows)
    assert "NO FLIP" in summary["verdict"]


def test_run_analysis_roundtrip(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for i in range(3):
            fh.write(json.dumps({"label": "unknown", "refused": False, "correct": False,
                                 "prompt_read_std": 1.0, "gen_read_std": -1.0}) + "\n")
            fh.write(json.dumps({"label": "unknown", "refused": True, "correct": False,
                                 "prompt_read_std": -1.0, "gen_read_std": 1.0}) + "\n")
    out = tmp_path / "out" / "trajectory.json"
    summary = traj.run_analysis(rows_path, out)
    assert out.exists()
    assert summary["groups"]["unknown_answered_wrong"] == 3
    assert summary["groups"]["unknown_refused"] == 3
