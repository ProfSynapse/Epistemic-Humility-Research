"""Tests for the hidden-state extraction gate (architecture §4 + §6 + §8).

Spine:
  * E1..E4 each SKIP (never abort) when their prereq is absent (§4.3).
  * A null model.revision is a WARN, not a SKIP (§8).
  * cloud_extract_capability_probe / cloud_extract_prereqs fail-closed SKIP (§6.5).
  * REGRESSION: check_cell (train/eval gate) is unchanged — same PASS/SKIP/ABORT
    for the same inputs after the additive extraction code (§4.6 / §11.2).

The gate resolves active-arm adapters via the merged harness's
resolve_eval_arm_adapters, so these tests build a minimal probe-dir layout
(config/ + eval/config/) with synthetic adapters + run records.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import check_prereqs  # noqa: E402  (sys.path set by conftest)

_WIN = r"F:\Code\Epistemic-Humility-Research\synaptic-tuner\toolset-training-artifacts\runs\local\4b"


def _adapter(run_id: str, ts: str) -> str:
    return rf"{_WIN}\{run_id}\{ts}\final_model"


@pytest.fixture()
def probe_layout(tmp_path: Path):
    """A minimal repo layout the gate + harness mirror can resolve against.

    Returns (config_path, repo_root). The probe dir is <root>/experiment/phase1/
    probe with config/ and eval/config/ subtrees; run_records under
    <root>/experiment/phase1/run_records.
    """
    root = tmp_path
    probe = root / "experiment" / "phase1" / "probe"
    (probe / "config").mkdir(parents=True)
    (probe / "eval" / "config").mkdir(parents=True)
    records = root / "experiment" / "phase1" / "run_records"
    records.mkdir(parents=True)

    # Real adapter dir on disk (so E4 can find adapter_config.json), located UNDER
    # a path containing the artifact anchor so the resolver's reverse-lookup (E3)
    # can normalize + match it (the resolver requires the
    # synaptic-tuner/toolset-training-artifacts/ anchor, §5.3).
    sft_adapter = (root / "synaptic-tuner" / "toolset-training-artifacts" / "runs"
                   / "local" / "4b" / "sft__4b__headline__seed1" / "20260614_053221"
                   / "final_model")
    sft_adapter.mkdir(parents=True)
    (sft_adapter / "adapter_config.json").write_text("{}", encoding="utf-8")

    # A verified+completed run record whose adapter_path == the on-disk adapter.
    (records / "sft__4b__headline__seed1.json").write_text(json.dumps({
        "run_id": "sft__4b__headline__seed1",
        "outcome": {
            "status": "completed", "verified": True,
            "adapter_path": str(sft_adapter),
        },
    }), encoding="utf-8")

    # eval config mirrors the active arm's adapter by name.
    eval_cfg = probe / "eval" / "config" / "eval.yaml"
    eval_cfg.write_text(yaml.safe_dump({
        "arms": [
            {"name": "base", "adapter": None},
            {"name": "sft", "adapter": str(sft_adapter)},
        ]
    }), encoding="utf-8")

    # probe_results.jsonl with a known probe_config_sha.
    probe_results = probe / "qwen3-4b-instruct"
    probe_results.mkdir()
    (probe_results / "probe_results.jsonl").write_text(
        json.dumps({"probe_pool_row_key": "k1", "probe_config_sha": "SHA_GOOD"}) + "\n",
        encoding="utf-8")

    config = {
        "model": {"model_tag": "qwen3-4b-instruct", "revision": None},
        "arms": [
            {"name": "base", "adapter_state": "disabled", "adapter": None},
            {"name": "sft", "adapter_state": "active", "adapter": None},
        ],
        "eval_arms_source": "eval/config/eval.yaml",
        "selection": {
            "probe_results": "qwen3-4b-instruct/probe_results.jsonl",
            "expected_probe_config_sha": "SHA_GOOD",
        },
        "manifest_provenance": {"aligned_run_record_id": None},
    }
    config_path = probe / "config" / "hidden_state_probe.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path, root


def _load(config_path: Path) -> dict:
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def _add_harness_to_path(repo_root: Path, monkeypatch):
    """Stub the harness's resolve_eval_arm_adapters import the gate uses.

    The real harness lives at experiment/phase1/probe/hidden_state_probe.py and
    imports torch lazily; for a GPU-free unit test we install a tiny stub module
    exposing only resolve_eval_arm_adapters with the by-name mirror behavior.
    """
    import sys
    import types

    probe_dir = repo_root / "experiment" / "phase1" / "probe"

    def resolve_eval_arm_adapters(config, config_path):
        src = config.get("eval_arms_source")
        mirror = {}
        if src:
            eval_path = (probe_dir / src).resolve()
            eval_cfg = yaml.safe_load(eval_path.read_text(encoding="utf-8"))
            mirror = {a["name"]: a.get("adapter") for a in eval_cfg.get("arms", [])}
        for arm in config["arms"]:
            if arm.get("adapter") is None and arm.get("adapter_state") == "active":
                arm["adapter"] = mirror.get(arm["name"])
        return config

    stub = types.ModuleType("hidden_state_probe")
    stub.resolve_eval_arm_adapters = resolve_eval_arm_adapters
    monkeypatch.setitem(sys.modules, "hidden_state_probe", stub)


# --- happy path --------------------------------------------------------------

def test_gate_passes_when_all_prereqs_present(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    result = check_prereqs.check_extraction_cell(
        config=_load(config_path), config_path=config_path, research_repo_root=root)
    assert result.ok and not result.skip
    assert result.details["resolved_run_record_ids"] == {"sft": "sft__4b__headline__seed1"}


def test_gate_resolves_common_config_paths_against_probe_dir(probe_layout, monkeypatch):
    config_path, root = probe_layout
    common_dir = root / "experiments/common/configs/phase1-probe"
    common_dir.mkdir(parents=True)
    common_config = common_dir / "hidden_state_probe.yaml"
    common_config.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")

    _add_harness_to_path(root, monkeypatch)
    result = check_prereqs.check_extraction_cell(
        config=_load(common_config), config_path=common_config, research_repo_root=root)

    assert result.ok and not result.skip
    assert result.details["probe_results_path"] == str(
        root / "experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl"
    )


def test_null_revision_is_warn_not_skip(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    result = check_prereqs.check_extraction_cell(
        config=_load(config_path), config_path=config_path, research_repo_root=root)
    assert not result.skip
    assert any("revision is null" in w for w in result.details["warnings"])


# --- E1..E4 each SKIP --------------------------------------------------------

def test_e1_skip_when_probe_results_absent(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    (root / "experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl").unlink()
    result = check_prereqs.check_extraction_cell(
        config=_load(config_path), config_path=config_path, research_repo_root=root)
    assert result.skip and "probe_results.jsonl absent" in result.skip_reason


def test_e2_skip_on_sha_mismatch(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    cfg = _load(config_path)
    cfg["selection"]["expected_probe_config_sha"] = "SHA_DIFFERENT"
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root)
    assert result.skip and "probe_config_sha mismatch" in result.skip_reason


def test_e2_null_expectation_warns_not_skip(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    cfg = _load(config_path)
    cfg["selection"]["expected_probe_config_sha"] = None
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root)
    assert not result.skip
    assert any("presence-only" in w for w in result.details["warnings"])


def test_e3_skip_when_run_record_unresolvable(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    # Remove the run record so the reverse-lookup zero-matches.
    (root / "experiment/phase1/run_records/sft__4b__headline__seed1.json").unlink()
    result = check_prereqs.check_extraction_cell(
        config=_load(config_path), config_path=config_path, research_repo_root=root)
    assert result.skip and "aligned_run_record_id unresolvable" in result.skip_reason


# --- E3 explicit-id validator branch (M3): the pin does NOT bypass the gate ----
#
# The reverse-lookup (honoring require_verified) is the single source of truth for
# the verified gate. An explicitly-pinned manifest_provenance.aligned_run_record_id
# is an ADDITIONAL constraint (must equal the verified reverse-lookup), never an
# escape hatch. Before the M3 fix, a pinned id whose record existed-but-was-
# unverified fell through to PASS because the disagree-check only fired when the
# reverse-lookup returned a (different) non-None id — a fail-OPEN hole. These tests
# pin the verified-gate so a pinned-but-unverified id fails closed exactly like an
# unpinned one (require_verified is the only opt-out).

def test_e3_explicit_id_verified_passes(probe_layout, monkeypatch):
    """A pinned id that equals the verified reverse-lookup resolves + passes."""
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    cfg = _load(config_path)
    cfg["manifest_provenance"]["aligned_run_record_id"] = "sft__4b__headline__seed1"
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root)
    assert result.ok and not result.skip
    assert result.details["resolved_run_record_ids"] == {"sft": "sft__4b__headline__seed1"}


def test_e3_explicit_id_pointing_at_unverified_fails_closed(probe_layout, monkeypatch):
    """The M3 hole-closer: a pinned id whose record is UNVERIFIED must SKIP, not
    pass. The reverse-lookup returns id=None under require_verified, so the pin
    cannot rescue it (no pin-based override of the verified gate)."""
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    # Flip the on-disk record to unverified while keeping the explicit pin.
    rec = root / "experiment/phase1/run_records/sft__4b__headline__seed1.json"
    data = json.loads(rec.read_text(encoding="utf-8"))
    data["outcome"]["verified"] = False
    rec.write_text(json.dumps(data), encoding="utf-8")
    cfg = _load(config_path)
    cfg["manifest_provenance"]["aligned_run_record_id"] = "sft__4b__headline__seed1"
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root)
    assert result.skip
    # Assert BOTH the gate's E3 fail-closed prefix AND the specifically-verified
    # rejection reason. The adapter suffix DOES line up with the record's
    # outcome.adapter_path (probe_layout builds them equal), so the reverse-lookup
    # MATCHES the record and rejects it on the verified check — proving this is the
    # verified-gate branch ("matched ... but outcome is not verified+completed"),
    # NOT a zero-match ("no run record's ... adapter_path matches"). Without the
    # second substring this test would false-green on an accidental zero-match.
    assert "unresolvable" in result.skip_reason
    assert "not verified+completed" in result.skip_reason


def test_e3_explicit_id_unverified_links_with_allow_unverified(probe_layout, monkeypatch):
    """The documented escape hatch: require_verified=False (--allow-unverified)
    links the pinned unverified record — the ONLY way to bypass the gate."""
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    rec = root / "experiment/phase1/run_records/sft__4b__headline__seed1.json"
    data = json.loads(rec.read_text(encoding="utf-8"))
    data["outcome"]["verified"] = False
    rec.write_text(json.dumps(data), encoding="utf-8")
    cfg = _load(config_path)
    cfg["manifest_provenance"]["aligned_run_record_id"] = "sft__4b__headline__seed1"
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root,
        require_verified=False)
    assert result.ok and not result.skip
    assert result.details["resolved_run_record_ids"] == {"sft": "sft__4b__headline__seed1"}


def test_e3_explicit_id_disagreeing_with_reverse_lookup_fails_closed(probe_layout, monkeypatch):
    """A pinned id that disagrees with the verified reverse-lookup SKIPs."""
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    cfg = _load(config_path)
    cfg["manifest_provenance"]["aligned_run_record_id"] = "some_other_run_id"
    result = check_prereqs.check_extraction_cell(
        config=cfg, config_path=config_path, research_repo_root=root)
    assert result.skip
    assert "disagrees" in result.skip_reason


def test_e4_skip_when_adapter_config_missing(probe_layout, monkeypatch):
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    (root / "synaptic-tuner/toolset-training-artifacts/runs/local/4b/"
     "sft__4b__headline__seed1/20260614_053221/final_model/adapter_config.json"
     ).unlink()
    result = check_prereqs.check_extraction_cell(
        config=_load(config_path), config_path=config_path, research_repo_root=root)
    assert result.skip and "adapter_config.json missing" in result.skip_reason


def test_gate_never_raises_prereqerror(probe_layout, monkeypatch):
    """Every failing path must SKIP, never raise PrereqError (§4.3)."""
    config_path, root = probe_layout
    _add_harness_to_path(root, monkeypatch)
    (root / "experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl").unlink()
    try:
        result = check_prereqs.check_extraction_cell(
            config=_load(config_path), config_path=config_path, research_repo_root=root)
    except check_prereqs.PrereqError:  # pragma: no cover
        pytest.fail("extraction gate raised PrereqError; it must SKIP-not-abort")
    assert result.skip


# --- cloud-extract runner-side gating ----------------------------------------

def test_cloud_extract_capability_probe_false_without_verb(tmp_path):
    """No tuner source => probe False (fail-closed)."""
    assert check_prereqs.cloud_extract_capability_probe(tmp_path) is False


def test_cloud_extract_capability_probe_true_when_present(tmp_path, monkeypatch):
    def fake_read(root, rel):
        if rel.endswith("parser.py"):
            return "subparsers.add_parser('cloud-extract')"
        if rel.endswith("_hf_command_builder.py"):
            return '"--adapter-repo-id" "--slice-dataset-name" "--output-dataset-name"'
        return None
    monkeypatch.setattr(check_prereqs, "_read_tuner_source", fake_read)
    assert check_prereqs.cloud_extract_capability_probe(tmp_path) is True


def test_cloud_extract_prereqs_skip_pre_build(tmp_path):
    result = check_prereqs.cloud_extract_prereqs(research_repo_root=tmp_path)
    assert result.skip and "capability probe failed" in result.skip_reason


# --- REGRESSION: check_cell (train/eval gate) unchanged (§4.6 / §11.2) --------

def _train_cell_kwargs(tmp_path: Path) -> dict:
    """A representative train cell with datasets + leakage-guard present."""
    data_root = tmp_path / "data"
    arm_dir = data_root / "qwen3-4b-instruct"
    arm_dir.mkdir(parents=True)
    (arm_dir / "sft_train.jsonl").write_text("{}", encoding="utf-8")
    (arm_dir / "sft_dev.jsonl").write_text("{}", encoding="utf-8")
    (arm_dir / "build_manifest.json").write_text(
        json.dumps({"leakage_guard": {"passed": True}}), encoding="utf-8")
    return dict(
        lane="local", method="sft", model_tag="qwen3-4b-instruct",
        train_file="sft_train.jsonl", dev_file="sft_dev.jsonl",
        data_root=data_root, research_repo_root=tmp_path,
    )


def test_check_cell_aborts_on_missing_capability(tmp_path, monkeypatch):
    """check_cell still ABORTS (PrereqError) when the local capability is absent.

    This is the unchanged train/eval behavior: a missing seed/beta/LoRA sink is a
    whole-matrix abort, NOT a skip. The extraction additions must not have
    softened it.
    """
    kwargs = _train_cell_kwargs(tmp_path)
    monkeypatch.setattr(check_prereqs, "local_seed_beta_capability_probe",
                        lambda root: False)
    with pytest.raises(check_prereqs.PrereqError):
        check_prereqs.check_cell(**kwargs)


def test_check_cell_passes_when_capability_present(tmp_path, monkeypatch):
    """check_cell returns ok (no skip) when the local capability probe passes."""
    kwargs = _train_cell_kwargs(tmp_path)
    monkeypatch.setattr(check_prereqs, "local_seed_beta_capability_probe",
                        lambda root: True)
    result = check_prereqs.check_cell(**kwargs)
    assert result.ok and not result.skip


def test_check_cell_bridge_cloud_still_aborts(tmp_path, monkeypatch):
    """Bridge-on-cloud is still a hard abort (structurally invalid)."""
    kwargs = _train_cell_kwargs(tmp_path)
    kwargs.update(lane="cloud", is_bridge=True)
    monkeypatch.setattr(check_prereqs, "lane_capability_ready", lambda lane, root: True)
    with pytest.raises(check_prereqs.PrereqError):
        check_prereqs.check_cell(**kwargs)
