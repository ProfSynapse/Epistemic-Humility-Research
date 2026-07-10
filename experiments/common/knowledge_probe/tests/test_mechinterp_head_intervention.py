from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import head_intervention as intervention  # noqa: E402

NUM_HEADS = 2
HEAD_DIM = 3
WIDTH = NUM_HEADS * HEAD_DIM
NUM_LAYERS = 2


class _OProj(torch.nn.Module):
    """Identity-ish o_proj that records the (possibly steered) input it receives."""

    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(WIDTH, WIDTH, bias=False)
        torch.nn.init.eye_(self.linear.weight)
        self.seen_input = None

    def forward(self, x):  # noqa: D401
        self.seen_input = x.detach().clone()
        return self.linear(x)


class _Attn(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.o_proj = _OProj()


class _Block(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = _Attn()

    def forward(self, x):
        return self.self_attn.o_proj(x)


class _Model(torch.nn.Module):
    """Names submodules `layers.<i>.self_attn.o_proj` so discovery matches."""

    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList([_Block() for _ in range(NUM_LAYERS)])

    def forward(self, x):
        for block in self.layers:
            x = block(x)
        return x


def _directions_artifact(tmp_path: Path) -> Path:
    # One target: block 1, head 1 (cols 3:6), theta=[1,0,0], sigma=2.0.
    artifact = {
        "artifact_type": "head_steering_directions",
        "directions": [
            {"layer": 1, "head": 1, "head_dim": HEAD_DIM, "theta": [1.0, 0.0, 0.0], "sigma": 2.0},
        ],
    }
    path = tmp_path / "steering_directions.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def test_build_block_deltas_scales_theta_by_alpha_sigma(tmp_path):
    artifact = intervention.load_steering_directions(_directions_artifact(tmp_path))
    by_block = intervention.build_block_deltas(artifact["directions"], alpha=-3.0)
    assert set(by_block) == {1}
    spec = by_block[1][0]
    assert spec["lo"] == 3 and spec["hi"] == 6
    # delta = alpha * sigma * theta = -3.0 * 2.0 * [1,0,0] = [-6,0,0]
    assert spec["delta"] == pytest.approx([-6.0, 0.0, 0.0])


def test_pre_hook_shifts_only_the_target_head_slice(tmp_path):
    model = _Model()
    artifact = intervention.load_steering_directions(_directions_artifact(tmp_path))
    by_block = intervention.build_block_deltas(artifact["directions"], alpha=-3.0)

    x = torch.zeros(1, 4, WIDTH)  # batch 1, seq 4
    with intervention.per_head_intervention(model, by_block, torch=torch, num_hidden_layers=NUM_LAYERS) as states:
        model(x)

    # Block 1's o_proj must have seen the steered input; block 0 unchanged.
    seen_block1 = model.layers[1].self_attn.o_proj.seen_input
    seen_block0 = model.layers[0].self_attn.o_proj.seen_input

    expected = torch.zeros(1, 4, WIDTH)
    expected[..., 3] = -6.0  # head 1 slot 0 shifted by alpha*sigma across ALL positions
    assert torch.allclose(seen_block1, expected)
    assert torch.allclose(seen_block0, torch.zeros(1, 4, WIDTH))  # block 0 had no target
    # Hook fired exactly once (one forward).
    assert sum(s["calls"] for s in states) == 1


def test_hooks_removed_after_context(tmp_path):
    model = _Model()
    artifact = intervention.load_steering_directions(_directions_artifact(tmp_path))
    by_block = intervention.build_block_deltas(artifact["directions"], alpha=1.0)

    x = torch.ones(1, 2, WIDTH)
    with intervention.per_head_intervention(model, by_block, torch=torch, num_hidden_layers=NUM_LAYERS):
        model(x)
    # After the context, a fresh forward must NOT be steered (hooks removed).
    model(x)
    seen = model.layers[1].self_attn.o_proj.seen_input
    assert torch.allclose(seen, torch.ones(1, 2, WIDTH))


def test_rejects_wrong_artifact_type(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"artifact_type": "something_else", "directions": []}), encoding="utf-8")
    with pytest.raises(intervention.HeadInterventionError, match="artifact_type"):
        intervention.load_steering_directions(bad)


def test_discovery_rejects_noncontiguous_blocks(tmp_path):
    model = _Model()
    artifact = intervention.load_steering_directions(_directions_artifact(tmp_path))
    by_block = intervention.build_block_deltas(artifact["directions"], alpha=1.0)
    # Claim 3 layers but the model only has 2 -> discovery must fail loudly.
    with pytest.raises(intervention.HeadInterventionError, match="expected contiguous"):
        with intervention.per_head_intervention(model, by_block, torch=torch, num_hidden_layers=3):
            pass
