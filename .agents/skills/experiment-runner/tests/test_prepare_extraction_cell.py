"""Tests for prepare_extraction_cell.py — the GPU-free default path (§4.2 / §10).

The default path (no --run-extraction) must:
  * print a SKIP report + exit 0 when the gate SKIPs (exploratory degrade);
  * print a PASS report with a TEMP effective config carrying the resolved
    aligned_run_record_id when the gate PASSes — WITHOUT invoking the harness and
    WITHOUT mutating the committed config (link-never-mutate, §5.5).

The harness invocation (--run-extraction) is the GPU-required path and is NOT
exercised here; we assert the default never shells out.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import prepare_extraction_cell as pec  # noqa: E402  (sys.path set by conftest)


def _make_config(tmp_path: Path, *, with_results: bool, resolvable: bool) -> Path:
    """Build a probe layout + config; toggle E1 (results) and E3 (run record)."""
    probe = tmp_path / "experiment" / "phase1" / "probe"
    (probe / "config").mkdir(parents=True)
    records = tmp_path / "experiment" / "phase1" / "run_records"
    records.mkdir(parents=True)

    # Adapter dir under the artifact anchor so the resolver (E3) can match it.
    adapter = (tmp_path / "synaptic-tuner" / "toolset-training-artifacts" / "runs"
               / "local" / "4b" / "sft__4b__headline__seed1" / "20260614_053221"
               / "final_model")
    adapter.mkdir(parents=True)
    (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")

    if resolvable:
        (records / "sft__4b__headline__seed1.json").write_text(json.dumps({
            "run_id": "sft__4b__headline__seed1",
            "outcome": {"status": "completed", "verified": True,
                        "adapter_path": str(adapter)},
        }), encoding="utf-8")

    if with_results:
        rdir = probe / "qwen3-4b-instruct"
        rdir.mkdir()
        (rdir / "probe_results.jsonl").write_text(
            json.dumps({"probe_pool_row_key": "k1", "probe_config_sha": "SHA"}) + "\n",
            encoding="utf-8")

    config = {
        "model": {"model_tag": "qwen3-4b-instruct", "revision": None},
        "arms": [
            {"name": "base", "adapter_state": "disabled", "adapter": None},
            {"name": "sft", "adapter_state": "active", "adapter": str(adapter)},
        ],
        "selection": {
            "probe_results": "qwen3-4b-instruct/probe_results.jsonl",
            "expected_probe_config_sha": "SHA",
        },
        "manifest_provenance": {"aligned_run_record_id": None},
    }
    config_path = probe / "config" / "hidden_state_probe.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_default_path_skip_exits_zero(tmp_path, capsys, monkeypatch):
    """Missing probe_results => SKIP report, exit 0, harness NOT invoked."""
    config_path = _make_config(tmp_path, with_results=False, resolvable=True)
    monkeypatch.setattr(pec.subprocess, "run",
                        lambda *a, **k: pytest.fail("harness must not run on SKIP"))
    rc = pec.main(["--config", str(config_path), "--research-repo-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["status"] == "SKIP"
    assert "probe_results.jsonl absent" in out["skip_reason"]


def test_default_path_pass_writes_effective_config(tmp_path, capsys, monkeypatch):
    """Gate PASS => PASS report + temp effective config with resolved id; no harness."""
    config_path = _make_config(tmp_path, with_results=True, resolvable=True)
    monkeypatch.setattr(pec.subprocess, "run",
                        lambda *a, **k: pytest.fail("harness must not run by default"))
    rc = pec.main(["--config", str(config_path), "--research-repo-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["status"] == "PASS"
    assert out["resolved_run_record_ids"] == {"sft": "sft__4b__headline__seed1"}

    # The temp effective config carries the resolved id; committed config does NOT.
    effective = yaml.safe_load(Path(out["effective_config"]).read_text(encoding="utf-8"))
    assert effective["manifest_provenance"]["aligned_run_record_id"] == "sft__4b__headline__seed1"
    committed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert committed["manifest_provenance"]["aligned_run_record_id"] is None


def test_committed_config_never_mutated_on_skip(tmp_path, capsys):
    """A SKIP path must not touch the committed config."""
    config_path = _make_config(tmp_path, with_results=False, resolvable=True)
    before = config_path.read_text(encoding="utf-8")
    pec.main(["--config", str(config_path), "--research-repo-root", str(tmp_path)])
    assert config_path.read_text(encoding="utf-8") == before
