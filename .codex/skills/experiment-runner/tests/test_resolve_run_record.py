"""Tests for the Q3 aligned_run_record_id resolver (architecture §5).

The divergence matrix (§5.4), verified against the real 2026-06-14 records, is
the test spine: the resolver must FAIL-CLOSED on every disagreement and only LINK
a single verified+completed match.

  Arm | run_record adapter ts        | eval-config mirror ts | verified | expected
  ----|------------------------------|-----------------------|----------|----------
  sft | 20260614_053221              | 20260611_202126       | True     | None (zero-match: timestamps differ)
  dpo | 20260611_211512              | 20260611_211512       | False    | None (matched but unverified)
  kto | 20260613_151337_logging_patch| (no kto arm)          | True     | None via eval-mirror; LINK only via explicit adapter

These fixtures use SYNTHETIC run-record JSON with the same shape + the real
Windows-absolute path format so the normalization is exercised against the actual
on-disk string form, without depending on the live (gitignored) records.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resolve_run_record import (  # noqa: E402  (sys.path set by conftest)
    ResolveResult,
    normalize_adapter_suffix,
    resolve_aligned_run_record_id,
)

# Real Windows-absolute adapter-path format from the 2026-06-14 records.
_WIN_PREFIX = r"F:\Code\Epistemic-Humility-Research"
_ART = r"synaptic-tuner\toolset-training-artifacts\runs\local\4b"


def _win_adapter(run_id: str, ts: str) -> str:
    return rf"{_WIN_PREFIX}\{_ART}\{run_id}\{ts}\final_model"


def _write_record(dir_: Path, run_id: str, ts: str, *, verified: bool,
                  status: str = "completed") -> None:
    record = {
        "run_id": run_id,
        "outcome": {
            "status": status,
            "verified": verified,
            "adapter_path": _win_adapter(run_id, ts),
        },
    }
    (dir_ / f"{run_id}.json").write_text(json.dumps(record), encoding="utf-8")


@pytest.fixture()
def run_records_dir(tmp_path: Path) -> Path:
    """A run_records dir reproducing the real 2026-06-14 divergence matrix."""
    d = tmp_path / "run_records"
    d.mkdir()
    _write_record(d, "sft__4b__headline__seed1", "20260614_053221", verified=True)
    _write_record(d, "dpo__4b__headline__seed1", "20260611_211512", verified=False)
    _write_record(d, "kto__4b__headline__seed1", "20260613_151337_logging_patch",
                  verified=True)
    # A subdir that must be ignored by the record scan.
    (d / "materialized_recipes").mkdir()
    (d / "materialized_recipes" / "noise.json").write_text("{}", encoding="utf-8")
    return d


# --- normalization -----------------------------------------------------------

def test_normalize_strips_windows_prefix_keeps_timestamp():
    win = _win_adapter("sft__4b__headline__seed1", "20260614_053221")
    suffix = normalize_adapter_suffix(win)
    assert suffix == (
        "synaptic-tuner/toolset-training-artifacts/runs/local/4b/"
        "sft__4b__headline__seed1/20260614_053221/final_model"
    )


def test_normalize_host_agnostic_wsl_and_windows_agree():
    win = _win_adapter("dpo__4b__headline__seed1", "20260611_211512")
    wsl = win.replace("\\", "/").replace("F:/Code", "/mnt/f/Code")
    assert normalize_adapter_suffix(win) == normalize_adapter_suffix(wsl)


def test_normalize_returns_none_without_anchor():
    assert normalize_adapter_suffix("/some/other/path/final_model") is None
    assert normalize_adapter_suffix(None) is None


# --- the §5.4 divergence matrix (fail-closed) --------------------------------

def test_sft_zero_match_on_timestamp_divergence(run_records_dir: Path):
    """eval-config sft adapter (older ts) must NOT link the latest run record."""
    eval_mirror = _win_adapter("sft__4b__headline__seed1", "20260611_202126")
    result = resolve_aligned_run_record_id(
        adapter_path=eval_mirror, run_records_dir=run_records_dir,
        research_repo_root=run_records_dir.parent,
    )
    assert result.id is None
    assert "no run record" in result.reason


def test_dpo_matched_but_unverified_skips(run_records_dir: Path):
    """dpo paths agree but outcome.verified is False => fail-closed."""
    eval_mirror = _win_adapter("dpo__4b__headline__seed1", "20260611_211512")
    result = resolve_aligned_run_record_id(
        adapter_path=eval_mirror, run_records_dir=run_records_dir,
        research_repo_root=run_records_dir.parent,
    )
    assert result.id is None
    assert "not verified" in result.reason


def test_dpo_links_when_unverified_allowed(run_records_dir: Path):
    """The documented opt-in escape hatch links the unverified dpo record."""
    eval_mirror = _win_adapter("dpo__4b__headline__seed1", "20260611_211512")
    result = resolve_aligned_run_record_id(
        adapter_path=eval_mirror, run_records_dir=run_records_dir,
        research_repo_root=run_records_dir.parent, require_verified=False,
    )
    assert result.id == "dpo__4b__headline__seed1"


def test_kto_links_only_via_explicit_verified_adapter(run_records_dir: Path):
    """KTO has no eval-config arm; an explicit verified adapter resolves."""
    explicit = _win_adapter("kto__4b__headline__seed1", "20260613_151337_logging_patch")
    result = resolve_aligned_run_record_id(
        adapter_path=explicit, run_records_dir=run_records_dir,
        research_repo_root=run_records_dir.parent,
    )
    assert result.id == "kto__4b__headline__seed1"


def test_verified_match_links(run_records_dir: Path):
    """A verified+completed exact match is the only LINK path."""
    exact = _win_adapter("sft__4b__headline__seed1", "20260614_053221")
    result = resolve_aligned_run_record_id(
        adapter_path=exact, run_records_dir=run_records_dir,
        research_repo_root=run_records_dir.parent,
    )
    assert result.id == "sft__4b__headline__seed1"
    assert result.run_record_path is not None


def test_ambiguous_multiple_matches_skips(tmp_path: Path):
    """Two run records with the same adapter suffix => ambiguous => None."""
    d = tmp_path / "run_records"
    d.mkdir()
    _write_record(d, "arm_a", "20260101_000000", verified=True)
    # Second record points at arm_a's adapter suffix (same run-id + ts).
    dup = {
        "run_id": "arm_b",
        "outcome": {
            "status": "completed", "verified": True,
            "adapter_path": _win_adapter("arm_a", "20260101_000000"),
        },
    }
    (d / "arm_b.json").write_text(json.dumps(dup), encoding="utf-8")
    result = resolve_aligned_run_record_id(
        adapter_path=_win_adapter("arm_a", "20260101_000000"),
        run_records_dir=d, research_repo_root=tmp_path,
    )
    assert result.id is None
    assert "ambiguous" in result.reason


def test_unrecognized_adapter_layout_fails_closed(run_records_dir: Path):
    result = resolve_aligned_run_record_id(
        adapter_path="/opt/models/some_adapter/final_model",
        run_records_dir=run_records_dir, research_repo_root=run_records_dir.parent,
    )
    assert result.id is None
    assert "anchor" in result.reason


def test_result_is_dataclass():
    assert ResolveResult(id=None).id is None
