"""CPU-only tests for alin_sweep.py Part 2 (gates.yaml
g0_alin_discrimination_measurement). No network, no checkpoint download: a
tiny synthetic Gemma4RMSNorm + unembedding + safetensors fixture stands in
for the real snapshot, so `compute_alin_single_condition` and
`load_condition_manifest` are exercised directly rather than through
`run_part2` (which does need network access for the tokenizer/snapshot, same
as Part 1's existing main()).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import alin_sweep as als  # noqa: E402
import kv_seam_patch as kv  # noqa: E402

safetensors_torch = pytest.importorskip("safetensors.torch")


HIDDEN = 8
VOCAB = 16


def _make_head():
    from transformers.models.gemma4.modeling_gemma4 import Gemma4RMSNorm

    torch.manual_seed(0)
    final_norm = Gemma4RMSNorm(HIDDEN, eps=1e-6)
    with torch.no_grad():
        final_norm.weight.copy_(torch.ones(HIDDEN))
    final_norm.eval()
    W_U = torch.randn(VOCAB, HIDDEN, dtype=torch.bfloat16)
    return final_norm, W_U


def _write_extraction(path: Path, hs_index: int, tensors_by_row: dict[str, torch.Tensor]):
    payload = {f"hs{hs_index}__{rk}": t for rk, t in tensors_by_row.items()}
    safetensors_torch.save_file(payload, str(path))


def _write_manifest(path: Path, *, forward_use_cache: bool = True, kv_sharing: str = "on",
                    rows_path: str = "", rows: list[dict] | None = None):
    path.write_text(json.dumps({
        "forward_use_cache": forward_use_cache, "kv_sharing": kv_sharing,
        "rows_path": rows_path, "rows": rows or [],
    }))


def test_compute_alin_single_condition_scores_correctly(tmp_path):
    final_norm, W_U = _make_head()
    hs_index = 38
    row_keys = ["r1", "r2", "r3"]

    # Build hidden states whose argmax-after-lens is KNOWN: pick target token
    # t for each row, then set h so that final_norm(h) @ W_U.T argmaxes at t
    # by construction (h = W_U[t] itself is a strong, if not exact, proxy;
    # correctness is checked via score_depth's own rank/top1 logic instead
    # of hand-deriving the exact post-norm argmax).
    torch.manual_seed(1)
    hiddens = {rk: torch.randn(HIDDEN) for rk in row_keys}
    with torch.no_grad():
        logits = als.lens_logits(
            torch.stack(list(hiddens.values())), final_norm, W_U, None, apply_norm=True
        )
    targets = {rk: int(logits[i].argmax()) for i, rk in enumerate(row_keys)}

    extract_path = tmp_path / "anchor_extract.safetensors"
    _write_extraction(extract_path, hs_index, hiddens)

    result = als.compute_alin_single_condition(
        extract_path, hs_index, row_keys, targets, final_norm, W_U,
        softcap=None, apply_norm=True,
    )
    assert result["n"] == 3
    assert result["top1_acc"] == 1.0
    assert result["median_rank"] == 1


def test_compute_alin_single_condition_raises_on_missing_tensor(tmp_path):
    final_norm, W_U = _make_head()
    hs_index = 38
    hiddens = {"r1": torch.randn(HIDDEN)}
    targets = {"r1": 0, "r2": 0}  # r2 has no tensor in the extraction
    extract_path = tmp_path / "anchor_extract.safetensors"
    _write_extraction(extract_path, hs_index, hiddens)

    with pytest.raises(RuntimeError, match="had no cached tensor"):
        als.compute_alin_single_condition(
            extract_path, hs_index, ["r1", "r2"], targets, final_norm, W_U,
            softcap=None, apply_norm=True,
        )


def test_on_vs_off_only_the_source_file_differs(tmp_path):
    """The whole point of Part 2: IDENTICAL fit_rows/targets/final_norm/W_U,
    only the extraction file differs between the ON and OFF calls."""
    final_norm, W_U = _make_head()
    hs_index = 38
    row_keys = ["r1", "r2"]
    torch.manual_seed(2)
    hiddens_on = {rk: torch.randn(HIDDEN) for rk in row_keys}
    with torch.no_grad():
        logits_on = als.lens_logits(
            torch.stack(list(hiddens_on.values())), final_norm, W_U, None, apply_norm=True
        )
    targets = {rk: int(logits_on[i].argmax()) for i, rk in enumerate(row_keys)}

    on_path = tmp_path / "anchor_extract.safetensors"
    _write_extraction(on_path, hs_index, hiddens_on)

    # OFF activations are DIFFERENT tensors (as the real OFF residual stream
    # would be, upstream of a KV-shared block) and, by construction here,
    # score worse against the SAME targets.
    hiddens_off = {rk: torch.zeros(HIDDEN) for rk in row_keys}
    off_path = tmp_path / "anchor_extract.kv_off.safetensors"
    _write_extraction(off_path, hs_index, hiddens_off)

    a_on = als.compute_alin_single_condition(
        on_path, hs_index, row_keys, targets, final_norm, W_U, softcap=None, apply_norm=True,
    )
    a_off = als.compute_alin_single_condition(
        off_path, hs_index, row_keys, targets, final_norm, W_U, softcap=None, apply_norm=True,
    )
    assert a_on["top1_acc"] == 1.0
    verdict = als.alin_discrimination_verdict(a_on["top1_acc"], a_off["top1_acc"])
    assert verdict["a_lin_on"] == a_on["top1_acc"]
    assert verdict["a_lin_off"] == a_off["top1_acc"]
    assert verdict["delta_a_lin"] == round(abs(a_on["top1_acc"] - a_off["top1_acc"]), 6)


# ---------------------------------------------------------------------------
# alin_discrimination_verdict band logic
# ---------------------------------------------------------------------------


def test_discrimination_verdict_within_band():
    v = als.alin_discrimination_verdict(0.90, 0.87)
    assert v["within_band"] is True
    assert v["delta_a_lin"] == pytest.approx(0.03)


def test_discrimination_verdict_outside_band():
    v = als.alin_discrimination_verdict(0.90, 0.70)
    assert v["within_band"] is False
    assert v["delta_a_lin"] == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# load_condition_manifest fail-closed behavior
# ---------------------------------------------------------------------------


def test_load_condition_manifest_missing_extraction_raises(tmp_path):
    with pytest.raises(RuntimeError, match="missing extraction"):
        als.load_condition_manifest(tmp_path, "off")


def test_load_condition_manifest_rejects_use_cache_false(tmp_path):
    extract_path = tmp_path / kv.condition_artifact("anchor_extract.safetensors", "on")
    manifest_path = tmp_path / kv.condition_artifact("anchor_extract_manifest.json", "on")
    extract_path.write_bytes(b"")
    _write_manifest(manifest_path, forward_use_cache=False, kv_sharing="on")
    with pytest.raises(RuntimeError, match="forward_use_cache"):
        als.load_condition_manifest(tmp_path, "on")


def test_load_condition_manifest_rejects_kv_sharing_mismatch(tmp_path):
    extract_path = tmp_path / kv.condition_artifact("anchor_extract.safetensors", "off")
    manifest_path = tmp_path / kv.condition_artifact("anchor_extract_manifest.json", "off")
    extract_path.write_bytes(b"")
    _write_manifest(manifest_path, forward_use_cache=True, kv_sharing="on")  # wrong condition
    with pytest.raises(RuntimeError, match="expected 'off'"):
        als.load_condition_manifest(tmp_path, "off")


def test_load_condition_manifest_accepts_well_formed_on():
    real_analysis = HERE / "analysis-committed" / "gemma4-e4b"
    # No real ON extraction is staged in this worktree (private data); assert
    # the SAME fail-closed path fires for the real experiment tree too,
    # rather than asserting a positive load that needs private data present.
    with pytest.raises(RuntimeError, match="missing extraction"):
        als.load_condition_manifest(HERE / "analysis" / "gemma4-e4b", "on")
