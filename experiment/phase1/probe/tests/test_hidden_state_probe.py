"""Tests for the hidden-state probing tier.

Location: experiment/phase1/probe/tests/test_hidden_state_probe.py
Run:      cd experiment/phase1/probe && python -m pytest tests/ -q

OWNERSHIP NOTE (CODE -> TEST handoff): the backend-coder created this file with
ONLY (a) the shared GPU-free fixtures and a smoke check that the stub pipeline
runs, and (b) the clearly-marked GPU-only skip stubs below. The full GPU-free
suite (Step 7 of the plan: adapter-state positive+NEGATIVE pre-flight, tensor-
shape schema incl. negative branches, manifest completeness + hash stamping,
config-sha stability, prompt identity across arms, leakage/frozen-split
alignment, safetensors round-trip, enable_thinking recorded, delta bookkeeping)
is the TEST-ENGINEER's to build out here against hidden_state_schema +
StubExtractionBackend. The fixtures and the injectable stub seam (the one hard
prerequisite the plan put on the coder) are ready for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import hidden_state_probe as hsp  # noqa: E402
import hidden_state_schema as schema  # noqa: E402

FIXTURE_FROZEN = PROBE_DIR / "tests" / "fixtures" / "hidden_state_frozen.json"
FIXTURE_RESULTS = PROBE_DIR / "tests" / "fixtures" / "hidden_state_probe_results.jsonl"


def _stub_config() -> dict:
    """Minimal GPU-free config pointing selection at the checked-in fixtures."""
    return {
        "model": {"model_tag": "stub-model", "model_name": "stub",
                  "enable_thinking": False},
        "extraction": {"layer_list": None,
                       "token_position_rule": schema.TOKEN_POSITION_FINAL_PROMPT,
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
        "provenance": {"aligned_run_record_id": None,
                       "aligned_probe_config_sha": None, "source_split": "fixture"},
    }


# --- one coder smoke check: the GPU-free stub pipeline runs end to end ---

def test_stub_pipeline_runs_gpu_free(tmp_path, monkeypatch):
    """Sanity: select fixture slice + stub-extract + write manifest/rows/tensors.

    This is the coder's "does the happy path hold without a GPU" gate; the
    test-engineer expands the focused unit coverage (Step 7) around it.
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    assert len(slice_rows) == 4  # 2 known + 2 unknown; discard row excluded

    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    out_dir = tmp_path / "out"
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    import json
    manifest = json.loads(manifest_path.read_text())
    schema.validate_manifest(manifest)
    assert manifest["status"] == schema.STATUS_OK
    assert manifest["verified"] is True
    rows = [json.loads(line) for line in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 4
    assert list((out_dir).glob("*_delta.safetensors"))


# ---------------------------------------------------------------------------
# GPU-only smoke assertions (built later; SKIPPED in CI). The test-engineer
# fleshes these out to run on the RTX 3090 after the first-GPU-run gates close.
# They require a real Qwen3-4B load + a real PEFT adapter, so they CANNOT run on
# a CPU/no-network host. Documented here so the contract is not lost.
# ---------------------------------------------------------------------------

GPU_ONLY_REASON = "GPU-only: requires real Qwen3-4B + PEFT adapter load (RTX 3090)"


@pytest.mark.skip(reason=GPU_ONLY_REASON)
def test_gpu_h_base_differs_from_h_lora():
    """Second tier of the confound guard: real h_base != h_lora, non-trivial delta."""


@pytest.mark.skip(reason=GPU_ONLY_REASON)
def test_gpu_hidden_states_length_is_num_layers_plus_one():
    """len(out.hidden_states) == model.config.num_hidden_layers + 1 on real Qwen3-4B."""


@pytest.mark.skip(reason=GPU_ONLY_REASON)
def test_gpu_prompt_byte_identical_and_no_think_block_on_real_template():
    """Same rendered bytes across arms; real template honors enable_thinking=False."""


@pytest.mark.skip(reason=GPU_ONLY_REASON)
def test_gpu_forward_is_deterministic_across_two_passes():
    """Two forwards of the same prompt/arm produce identical hidden states."""


@pytest.mark.skip(reason=GPU_ONLY_REASON)
def test_gpu_manifest_adapter_hash_matches_loaded_adapter():
    """Manifest adapter hash/name + peft/transformers versions match the load."""
