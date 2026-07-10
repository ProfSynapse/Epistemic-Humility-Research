"""Tests for the per-head (attention_head granularity) extraction surface.

Location: experiments/common/knowledge_probe/tests/test_hidden_state_head_extraction.py
Run:      py -3.12 -m pytest experiments/common/knowledge_probe/tests -q

Covers Step A sub-step 1 (ITI-grounded per-head capture):
  - schema: granularity validation, the pure o_proj-input -> per-head reshape,
    and validate_head_state_shape (positive + negative branches),
  - StubExtractionBackend.forward_head_states (shape / determinism / base!=active),
  - TransformersPeftBackend.forward_head_states against a TINY real torch model:
    proves the o_proj forward-hook captures the final-token attention-output-
    projection input and that reshape splits it into the right per-head vectors.

The tiny-model test reuses the REAL backend method (bound to an instance built
with __new__, no __init__) so it exercises the shipped capture/hook code, not a
reimplementation. It runs on CPU with a few-parameter model, so it is GPU-free.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import hidden_state_probe as hsp  # noqa: E402
import hidden_state_schema as schema  # noqa: E402


# ---------------------------------------------------------------------------
# schema: granularity + reshape + head-shape validator
# ---------------------------------------------------------------------------

def test_validate_granularity_accepts_both_supported():
    schema.validate_granularity(schema.GRANULARITY_RESIDUAL_STREAM)
    schema.validate_granularity(schema.GRANULARITY_ATTENTION_HEAD)


def test_validate_granularity_rejects_unknown():
    with pytest.raises(ValueError, match="not supported"):
        schema.validate_granularity("whole_layer")


def test_expected_attention_layer_count_is_n_not_n_plus_one():
    # Residual is N+1 (embeddings + blocks); per-head is N (one o_proj per block).
    assert schema.expected_attention_layer_count(28) == 28
    assert schema.expected_layer_count(28) == 29


def test_reshape_splits_in_natural_concatenation_order():
    # head h occupies slots h*head_dim : (h+1)*head_dim
    flat = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    heads = schema.reshape_o_proj_input_to_heads(flat, num_attention_heads=3, head_dim=2)
    assert heads == {0: [0.0, 1.0], 1: [2.0, 3.0], 2: [4.0, 5.0]}


def test_reshape_rejects_width_mismatch():
    with pytest.raises(ValueError, match="does not match the configured head layout"):
        schema.reshape_o_proj_input_to_heads([0.0, 1.0, 2.0], num_attention_heads=2, head_dim=2)


def test_reshape_rejects_nonpositive_layout():
    with pytest.raises(ValueError, match="must both be positive"):
        schema.reshape_o_proj_input_to_heads([0.0], num_attention_heads=0, head_dim=2)


def _head_layer_vectors(num_hidden_layers: int, num_attention_heads: int, head_dim: int):
    width = num_attention_heads * head_dim
    return {block: [float(block)] * width
            for block in range(schema.expected_attention_layer_count(num_hidden_layers))}


def test_head_shape_accepts_well_formed_stack():
    schema.validate_head_state_shape(
        layer_vectors=_head_layer_vectors(4, 3, 2),
        num_hidden_layers=4, num_attention_heads=3, head_dim=2,
        token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
    )


def test_head_shape_rejects_residual_style_layer_count():
    # N+1 layers (the residual contract) must be rejected for the head surface.
    bad = _head_layer_vectors(4, 3, 2)
    bad[4] = [0.0] * 6  # add an Nth+1 id -> count N+1
    with pytest.raises(ValueError, match="layer count"):
        schema.validate_head_state_shape(
            layer_vectors=bad, num_hidden_layers=4,
            num_attention_heads=3, head_dim=2,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
        )


def test_head_shape_rejects_missing_block_id():
    bad = _head_layer_vectors(4, 3, 2)
    del bad[2]
    bad[99] = [0.0] * 6
    with pytest.raises(ValueError, match="layer ids mismatch"):
        schema.validate_head_state_shape(
            layer_vectors=bad, num_hidden_layers=4,
            num_attention_heads=3, head_dim=2,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
        )


def test_head_shape_rejects_wrong_vector_width():
    bad = _head_layer_vectors(4, 3, 2)
    bad[1] = [0.0] * 5  # not num_attention_heads*head_dim = 6
    with pytest.raises(ValueError, match="vector length"):
        schema.validate_head_state_shape(
            layer_vectors=bad, num_hidden_layers=4,
            num_attention_heads=3, head_dim=2,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
        )


# ---------------------------------------------------------------------------
# StubExtractionBackend.forward_head_states
# ---------------------------------------------------------------------------

def test_stub_head_states_match_head_shape_contract():
    backend = hsp.StubExtractionBackend(
        num_hidden_layers=3, hidden_dim=8, num_attention_heads=4, head_dim=2)
    vectors = backend.forward_head_states("p", schema.ADAPTER_STATE_ACTIVE, "adpt")
    schema.validate_head_state_shape(
        layer_vectors=vectors, num_hidden_layers=3,
        num_attention_heads=4, head_dim=2,
        token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
    )


def test_stub_head_states_are_deterministic():
    b1 = hsp.StubExtractionBackend(num_hidden_layers=2, num_attention_heads=4, head_dim=2)
    b2 = hsp.StubExtractionBackend(num_hidden_layers=2, num_attention_heads=4, head_dim=2)
    assert (b1.forward_head_states("q", schema.ADAPTER_STATE_ACTIVE, "a")
            == b2.forward_head_states("q", schema.ADAPTER_STATE_ACTIVE, "a"))


def test_stub_head_states_differ_between_base_and_active():
    backend = hsp.StubExtractionBackend(num_hidden_layers=2, num_attention_heads=4, head_dim=2)
    base = backend.forward_head_states("q", schema.ADAPTER_STATE_DISABLED, None)
    active = backend.forward_head_states("q", schema.ADAPTER_STATE_ACTIVE, "a")
    assert base != active  # arm_state seeds different vectors (h_base != h_lora)


def test_stub_head_states_do_not_collide_with_residual_vectors():
    # The "head" hash tag must keep per-head vectors distinct from the residual
    # stub's per-layer vectors at the same width, so the two surfaces never alias.
    backend = hsp.StubExtractionBackend(
        num_hidden_layers=2, hidden_dim=8, num_attention_heads=4, head_dim=2)
    resid = backend.forward_hidden_states("q", schema.ADAPTER_STATE_ACTIVE, "a")
    head = backend.forward_head_states("q", schema.ADAPTER_STATE_ACTIVE, "a")
    assert head[0] != resid[0]


# ---------------------------------------------------------------------------
# TransformersPeftBackend.forward_head_states on a tiny real torch model
# ---------------------------------------------------------------------------

torch = pytest.importorskip("torch")
import torch.nn as nn  # noqa: E402


class _Enc(dict):
    """Minimal tokenizer output: a mapping with a no-op .to(device)."""

    def to(self, _device):
        return self


class _FakeTokenizer:
    def __init__(self, seq_len: int):
        self._ids = torch.arange(1, seq_len + 1).unsqueeze(0)

    def __call__(self, _text, return_tensors=None):
        return _Enc(input_ids=self._ids)


class _TinySelfAttn(nn.Module):
    """Produces a deterministic o_proj input (the concatenated per-head context).

    to_context maps the block input hidden state to width
    num_attention_heads*head_dim; o_proj is the real attention output projection
    whose INPUT the backend hook captures.
    """

    def __init__(self, hidden: int, heads: int, head_dim: int):
        super().__init__()
        self.to_context = nn.Linear(hidden, heads * head_dim, bias=False)
        self.o_proj = nn.Linear(heads * head_dim, hidden, bias=False)

    def forward(self, hidden):
        return self.o_proj(self.to_context(hidden))


class _TinyBlock(nn.Module):
    def __init__(self, hidden, heads, head_dim):
        super().__init__()
        self.self_attn = _TinySelfAttn(hidden, heads, head_dim)

    def forward(self, hidden):
        return self.self_attn(hidden)


class _TinyInner(nn.Module):
    def __init__(self, vocab, hidden, heads, head_dim, n_layers):
        super().__init__()
        self.embed = nn.Embedding(vocab, hidden)
        self.layers = nn.ModuleList(
            [_TinyBlock(hidden, heads, head_dim) for _ in range(n_layers)])

    def forward(self, input_ids=None, **_kw):
        # Each block reads the SAME embedding (no residual chaining) so every
        # block's o_proj input is exactly to_context(emb) -- trivially verifiable.
        emb = self.embed(input_ids)
        for block in self.layers:
            block(emb)
        return None


class _TinyModel(nn.Module):
    """Stands in for the PeftModel: exposes layers.<i>.self_attn.o_proj + config."""

    def __init__(self, vocab, hidden, heads, head_dim, n_layers):
        super().__init__()
        self.layers = nn.ModuleList(
            [_TinyBlock(hidden, heads, head_dim) for _ in range(n_layers)])
        self.embed = nn.Embedding(vocab, hidden)
        import types
        self.config = types.SimpleNamespace(
            num_hidden_layers=n_layers, hidden_size=hidden,
            num_attention_heads=heads, head_dim=head_dim)

    def forward(self, input_ids=None, **_kw):
        emb = self.embed(input_ids)
        for block in self.layers:
            block(emb)
        return None

    def set_adapter(self, _name):
        return None

    @contextlib.contextmanager
    def disable_adapter(self):
        yield


def _make_fake_backend(model, seq_len):
    """Build a TransformersPeftBackend WITHOUT __init__, wiring only what the
    per-head path touches, so the test runs the SHIPPED method."""
    backend = hsp.TransformersPeftBackend.__new__(hsp.TransformersPeftBackend)
    backend._torch = torch
    backend.device = "cpu"
    cfg = model.config
    backend.num_hidden_layers = cfg.num_hidden_layers
    backend.hidden_dim = cfg.hidden_size
    backend.num_attention_heads = cfg.num_attention_heads
    backend.head_dim = cfg.head_dim
    backend.tokenizer = _FakeTokenizer(seq_len)
    backend.model = model
    return backend


def test_real_hook_captures_final_token_o_proj_input_and_reshapes_per_head():
    torch.manual_seed(0)
    vocab, hidden, heads, head_dim, n_layers, seq_len = 16, 6, 3, 2, 2, 4
    model = _TinyModel(vocab, hidden, heads, head_dim, n_layers).eval()
    backend = _make_fake_backend(model, seq_len)

    captured = backend.forward_head_states("ignored", schema.ADAPTER_STATE_ACTIVE, "a")

    # One vector per attention block, full head-shape contract holds.
    schema.validate_head_state_shape(
        layer_vectors=captured, num_hidden_layers=n_layers,
        num_attention_heads=heads, head_dim=head_dim,
        token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT,
    )

    # Recompute the expected o_proj input at the final token for each block.
    ids = torch.arange(1, seq_len + 1).unsqueeze(0)
    emb = model.embed(ids)
    final_hidden = emb[0, -1, :]
    for block_id, block in enumerate(model.layers):
        expected_flat = block.self_attn.to_context(final_hidden).detach().tolist()
        assert captured[block_id] == pytest.approx(expected_flat)
        # And the schema reshape splits it into the right per-head slices.
        heads_split = schema.reshape_o_proj_input_to_heads(
            captured[block_id], heads, head_dim)
        assert heads_split[0] == pytest.approx(expected_flat[:head_dim])
        assert heads_split[heads - 1] == pytest.approx(expected_flat[-head_dim:])


def test_real_hook_handles_removed_after_forward():
    # No lingering hooks: a second forward must not double-capture or error.
    torch.manual_seed(1)
    model = _TinyModel(16, 6, 3, 2, 2).eval()  # vocab,hidden,heads,head_dim,n_layers
    backend = _make_fake_backend(model, 4)
    first = backend.forward_head_states("x", schema.ADAPTER_STATE_ACTIVE, "a")
    second = backend.forward_head_states("x", schema.ADAPTER_STATE_ACTIVE, "a")
    assert first == second
    # Every o_proj module has zero registered forward hooks afterwards.
    for _name, module in model.named_modules():
        if hasattr(module, "_forward_hooks"):
            assert len(module._forward_hooks) == 0


def test_o_proj_discovery_rejects_unexpected_naming():
    # A model missing a block's o_proj must fail loudly, not capture a partial stack.
    model = _TinyModel(16, 6, 3, 2, 2).eval()  # vocab,hidden,heads,head_dim,n_layers
    del model.layers[1].self_attn.o_proj  # break contiguity
    backend = _make_fake_backend(model, 4)
    with pytest.raises(RuntimeError, match="expected contiguous"):
        backend.forward_head_states("x", schema.ADAPTER_STATE_ACTIVE, "a")


# ---------------------------------------------------------------------------
# End-to-end stub run with granularity=attention_head (run_extraction wiring)
# ---------------------------------------------------------------------------

FIXTURE_FROZEN = PROBE_DIR / "tests" / "fixtures" / "hidden_state_frozen.json"
FIXTURE_RESULTS = PROBE_DIR / "tests" / "fixtures" / "hidden_state_probe_results.jsonl"


def _head_stub_config(granularity=schema.GRANULARITY_ATTENTION_HEAD) -> dict:
    """GPU-free config pointing selection at the checked-in fixtures, head mode."""
    return {
        "model": {"model_tag": "stub-model", "model_name": "stub",
                  "enable_thinking": False},
        "extraction": {"layer_list": None,
                       "token_position_rule": schema.TOKEN_POSITION_FINAL_PROMPT,
                       "granularity": granularity,
                       "compute_dtype": "float32", "persist_dtype": "float32",
                       "persistence_format": "safetensors", "device": "cpu",
                       "persist_delta": True},
        "arms": [{"name": "base", "adapter_state": "disabled", "adapter": None},
                 {"name": "sft", "adapter_state": "active", "adapter": "/fake/adapter"}],
        "eval_arms_source": None,
        "selection": {"questions_frozen": str(FIXTURE_FROZEN),
                      "probe_results": str(FIXTURE_RESULTS),
                      "n_known": 2, "n_unknown": 2, "selection_seed": 20260614},
        "output": {"hidden_states_subdir": "hidden_states",
                   "manifest_filename": "manifest.json", "rows_filename": "rows.jsonl"},
        "manifest_provenance": {"aligned_run_record_id": "stub-run-record",
                                "source_split": "fixture"},
    }


def test_head_granularity_run_extraction_end_to_end(tmp_path, monkeypatch):
    """Stub run with granularity=attention_head: N-block tensors, head-layout
    manifest, finalize gate passes. Mirrors the residual smoke test."""
    import json

    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _head_stub_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    assert len(slice_rows) == 4

    n_layers, heads, head_dim = 3, 4, 2
    backend = hsp.StubExtractionBackend(
        num_hidden_layers=n_layers, hidden_dim=8,
        num_attention_heads=heads, head_dim=head_dim)
    out_dir = tmp_path / "out"
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    manifest = json.loads(manifest_path.read_text())
    schema.validate_manifest(manifest, require_populated=True)
    assert manifest["status"] == schema.STATUS_OK
    assert manifest["verified"] is True
    # Head-layout provenance present and correct.
    assert manifest["granularity"] == schema.GRANULARITY_ATTENTION_HEAD
    assert manifest["num_attention_heads"] == heads
    assert manifest["head_dim"] == head_dim
    # tensor_shapes: N attention blocks (not N+1), width heads*head_dim.
    assert manifest["tensor_shapes"]["h_base"] == [n_layers, heads * head_dim]

    rows = [json.loads(line) for line in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 4
    for row in rows:
        assert row["granularity"] == schema.GRANULARITY_ATTENTION_HEAD
        assert row["layer_count"] == n_layers  # N, no embedding layer
        assert row["num_attention_heads"] == heads
        assert row["head_dim"] == head_dim
    assert list(out_dir.glob("*_delta.safetensors"))


def test_residual_run_extraction_leaves_head_fields_null(tmp_path, monkeypatch):
    """The default (residual) path keeps granularity=residual_stream and null
    head-layout dims — the additive change does not perturb the existing path."""
    import json

    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _head_stub_config(granularity=schema.GRANULARITY_RESIDUAL_STREAM)
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    out_dir = tmp_path / "out"
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    manifest = json.loads(manifest_path.read_text())
    schema.validate_manifest(manifest, require_populated=True)
    assert manifest["granularity"] == schema.GRANULARITY_RESIDUAL_STREAM
    assert manifest["num_attention_heads"] is None
    assert manifest["head_dim"] is None
    # Residual layer_count is N+1 (embeddings + blocks); no head fields on rows.
    rows = [json.loads(line) for line in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert rows[0]["layer_count"] == schema.expected_layer_count(2)
    assert "num_attention_heads" not in rows[0]


def test_parse_config_rejects_unknown_granularity(tmp_path):
    import yaml
    config = _head_stub_config(granularity="whole_layer")
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="granularity"):
        hsp.parse_config(path)


def test_finalize_gate_rejects_head_extraction_missing_layout():
    # An attention_head manifest finalized without head dims must RAISE.
    manifest = schema.build_manifest(
        config={"extraction": {"granularity": schema.GRANULARITY_ATTENTION_HEAD},
                "manifest_provenance": {}},
        extraction_config_sha="x", status=schema.STATUS_OK)
    # Populate everything the generic gate needs, but leave head dims None.
    for field in schema.REQUIRED_MANIFEST_FIELDS:
        if manifest.get(field) is None and field not in (
                "num_attention_heads", "head_dim", "layer_list"):
            manifest[field] = "x"
    manifest["tensor_shapes"] = {"h_base": [3, 8]}
    manifest["verified"] = False
    with pytest.raises(ValueError, match="head-layout field"):
        schema.validate_manifest(manifest, require_populated=True)
