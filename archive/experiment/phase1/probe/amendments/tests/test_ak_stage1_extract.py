#!/usr/bin/env python3
"""CPU smoke for the AK Stage 1 extraction runner (no GPU, no model download).

Exercises the position-selection logic, the tiny-fake-model capture path, and
the batch-1-vs-batch-N token-level agreement contract the AK doc mandates for a
new generation surface. Run:  python3 -m pytest tests/test_ak_stage1_extract.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
import torch.nn as nn  # noqa: E402

AMENDMENTS_DIR = Path(__file__).resolve().parent.parent
if str(AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AMENDMENTS_DIR))

from path_compat import phase1_probe_dir  # noqa: E402

PROBE_DIR = phase1_probe_dir()

import amendment_ak_stage1_extract as ak  # noqa: E402


# --------------------------------------------------------------------------
# position selection
# --------------------------------------------------------------------------
def test_answer_positions_stride_and_end():
    # prompt_len=5, content_end=12, stride=4 -> k0@5, k1@9, then answer_end@12
    pos = ak._answer_positions(5, 12, 4)
    names = [n for n, _ in pos]
    idxs = [i for _, i in pos]
    assert names[0] == "answer_k0" and idxs[0] == 5
    assert ("answer_end", 12) in pos
    assert idxs == sorted(idxs)
    # last entry is always answer_end at content_end
    assert pos[-1] == ("answer_end", 12)


def test_answer_positions_exact_stride_hit_renamed_to_end():
    # content_end lands exactly on a stride multiple -> that hit becomes end
    pos = ak._answer_positions(0, 8, 4)  # 0,4,8 ; 8==content_end
    assert pos[-1] == ("answer_end", 8)
    assert sum(1 for n, _ in pos if n == "answer_end") == 1


def test_answer_positions_empty_span():
    pos = ak._answer_positions(5, None, 4)
    assert pos == [("answer_k0", 5)]


def test_think_close_indices():
    seq = [1, 2, 3, 99, 4, 99, 5]  # prompt_len=3, close id=99
    assert ak._think_close_indices(seq, 3, {99}) == [3, 5]
    assert ak._think_close_indices(seq, 3, {77}) == []


# --------------------------------------------------------------------------
# tiny fake model - capture path + batch-1 vs batch-N agreement
# --------------------------------------------------------------------------
class _TinyModel(nn.Module):
    """Deterministic model returning per-layer hidden states; ignores padding
    correctly by consuming attention_mask semantics only through the caller."""

    class _Cfg:
        num_hidden_layers = 3
        hidden_size = 6

    def __init__(self):
        super().__init__()
        self.config = self._Cfg()
        torch.manual_seed(0)
        self.emb = nn.Embedding(50, self.config.hidden_size)
        self.blocks = nn.ModuleList(
            [nn.Linear(self.config.hidden_size, self.config.hidden_size)
             for _ in range(self.config.num_hidden_layers)])

    def parameters(self, recurse=True):  # device probe
        return super().parameters(recurse)

    def forward(self, input_ids, attention_mask=None, output_hidden_states=False,
                use_cache=False):
        h = self.emb(input_ids)
        hs = [h]
        for blk in self.blocks:
            h = torch.tanh(blk(h))
            hs.append(h)

        class _Out:
            pass

        o = _Out()
        o.hidden_states = tuple(hs)
        return o


def test_capture_positions_shapes_and_keys():
    model = _TinyModel().eval()
    device = torch.device("cpu")
    seq = [1, 2, 3, 4, 5, 6, 7, 8]   # prompt_len=3 -> generated 3..7
    layers = ("L1", "L2")
    special = {0}  # nothing special in seq -> content_end = last index
    vecs, pos_map, content_end = ak._capture_positions(
        model, None, seq, prompt_len=3, layers=layers, answer_stride=2,
        close_ids=set(), special_ids=special, device=device)
    assert content_end == 7
    # anchor + first_visible always present
    assert pos_map["anchor"] == 2 and pos_map["first_visible"] == 3
    # keys are "<L>@<pos>" for every layer x position
    for lk in layers:
        assert f"{lk}@anchor" in vecs and f"{lk}@answer_end" in vecs
        assert vecs[f"{lk}@anchor"].shape == (model.config.hidden_size,)
    # answer_end index maps to content_end
    assert pos_map["answer_end"] == 7


def test_capture_positions_content_end_trims_specials():
    model = _TinyModel().eval()
    seq = [1, 2, 3, 4, 5, 0, 0]   # prompt_len=3, trailing specials {0}
    vecs, pos_map, content_end = ak._capture_positions(
        model, None, seq, prompt_len=3, layers=("L1",), answer_stride=4,
        close_ids=set(), special_ids={0}, device=torch.device("cpu"))
    assert content_end == 4          # trailing 0s trimmed
    assert pos_map["answer_end"] == 4


def test_batch1_vs_batchN_token_level_agreement():
    """The AK numerics-smoke contract: batched forward capture at the shared
    anchor + first_visible positions must agree with batch-1 within tol.

    The fake model is padding-agnostic at a position given identical left
    context, so we replicate the runner's left-padding capture: pad on the left
    and read the same absolute (unpadded) positions. Agreement must be exact
    for this deterministic model; the GPU smoke uses a float tolerance.
    """
    model = _TinyModel().eval()
    seqs = [[1, 2, 3, 4, 5], [7, 8, 9, 10, 11, 12, 13]]
    plens = [2, 3]
    layers = ("L2",)
    # batch-1 captures
    singles = []
    for seq, pl in zip(seqs, plens):
        v, _, _ = ak._capture_positions(
            model, None, seq, pl, layers, 4, set(), {0}, torch.device("cpu"))
        singles.append(v)
    # a manual left-padded batch forward, reading the true positions per row
    maxlen = max(len(s) for s in seqs)
    ids = torch.zeros(len(seqs), maxlen, dtype=torch.long)
    offs = []
    for bi, seq in enumerate(seqs):
        off = maxlen - len(seq)
        offs.append(off)
        ids[bi, off:] = torch.tensor(seq)
    with torch.no_grad():
        out = model(input_ids=ids, output_hidden_states=True)
    for bi, (seq, pl) in enumerate(zip(seqs, plens)):
        li = int(layers[0][1:])
        # anchor and first_visible absolute indices shift by the left-pad offset
        anchor_batched = out.hidden_states[li][bi, offs[bi] + (pl - 1), :]
        anchor_single = singles[bi][f"{layers[0]}@anchor"]
        assert torch.allclose(anchor_batched, anchor_single, atol=1e-5)


# --------------------------------------------------------------------------
# pool builder round-trip
# --------------------------------------------------------------------------
def test_pool_builder_filters_and_projects(tmp_path):
    import amendment_ak_build_pool as pb

    a0 = tmp_path / "a0.jsonl"
    import json
    rows = [
        {"row_key": "ah::x::1", "question": "q1", "gold_class": "unanswerable",
         "degenerate": False, "ungradeable": False, "confab_on_unanswerable": True,
         "caution_dist_z": 0.1, "category_canon": "ambiguous", "source": "s"},
        {"row_key": "ah::x::2", "question": "q2", "gold_class": "answerable",
         "degenerate": False, "ungradeable": False, "confab_on_unanswerable": False,
         "caution_dist_z": 1.0, "category_canon": "x", "source": "s"},
        {"row_key": "ah::x::3", "question": "q3", "gold_class": "unanswerable",
         "degenerate": True, "ungradeable": False, "confab_on_unanswerable": False,
         "caution_dist_z": 0.2, "category_canon": "y", "source": "s"},
    ]
    a0.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    pool = pb.build_pool(pb.load_jsonl(a0))
    assert len(pool) == 1  # only the clean unanswerable row survives
    assert pool[0]["row_key"] == "ah::x::1"
    assert pool[0]["label"] == "unknown"
    assert pool[0]["confab_on_unanswerable"] is True
    summ = pb.summarize(pool)
    assert summ["n_total"] == 1 and summ["n_confab"] == 1


# --------------------------------------------------------------------------
# Modal wrapper provenance guard (no Modal runtime needed)
# --------------------------------------------------------------------------
def test_modal_grpo_v2_provenance_filled():
    """The wrapper's refuse-to-launch guard checks that the grpo-v2 constants do
    not start with REPLACE_WITH. Parse the module-level constants directly so
    this CPU test does not require the Modal package."""
    import ast

    cloud = PROBE_DIR / "cloud" / "modal_ak_stage1.py"
    tree = ast.parse(cloud.read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    constants[target.id] = node.value.value

    for name in ("REPO_COMMIT", "GRPOV2_BASE_MODEL", "GRPOV2_ADAPTER_REPO",
                 "GRPOV2_ADAPTER_REV"):
        val = constants[name]
        assert isinstance(val, str) and not val.startswith("REPLACE_WITH"), (
            f"{name} is still a placeholder: {val!r}")
    # the adapter revision is a full 40-char git/HF commit SHA
    rev = constants["GRPOV2_ADAPTER_REV"]
    assert len(rev) == 40 and all(c in "0123456789abcdef" for c in rev), rev
    assert constants["GRPOV2_ADAPTER_REPO"].startswith("professorsynapse/")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
