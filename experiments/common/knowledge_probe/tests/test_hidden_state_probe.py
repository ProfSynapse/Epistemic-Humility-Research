"""Tests for the hidden-state probing tier.

Location: experiments/common/knowledge_probe/tests/test_hidden_state_probe.py
Run:      py -3.12 -m pytest experiments/common/knowledge_probe/tests -q

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
REPO_ROOT = PROBE_DIR.parents[2]
if REPO_ROOT.name == "experiments":
    REPO_ROOT = REPO_ROOT.parent
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
        # B1 fix: the config key build_manifest/collect_static_provenance reads is
        # `manifest_provenance` (NOT the legacy `provenance`). Both static fields
        # are non-None so a finalized stub run passes the require_populated gate;
        # `aligned_run_record_id` MUST be non-None for finalize (a real run links
        # the run record that trained the adapter). _under_populated_config() below
        # nulls it to drive the NEGATIVE finalize-gate test.
        "manifest_provenance": {"aligned_run_record_id": "stub-run-record",
                                "source_split": "fixture"},
    }


def _under_populated_config() -> dict:
    """Stub config whose manifest_provenance leaves a Decision-D field None.

    Drives the NEGATIVE finalize-gate test: a finalized status=ok run over this
    config must RAISE under validate_manifest(require_populated=True) rather than
    silently shipping verified=True over a None provenance field (the B2 bug).
    """
    config = _stub_config()
    config["manifest_provenance"] = {"aligned_run_record_id": None,
                                     "source_split": "fixture"}
    return config


# --- one coder smoke check: the GPU-free stub pipeline runs end to end ---

def test_stub_pipeline_runs_gpu_free(tmp_path, monkeypatch):
    """Sanity: select fixture slice + stub-extract + write manifest/rows/tensors.

    This is the coder's "does the happy path hold without a GPU" gate; the
    test-engineer expands the focused unit coverage (Step 7) around it.

    B2 fix: `verified is True` is now asserted over a manifest that PASSED the
    require_populated finalize gate (run_extraction:551). Previously this asserted
    verified=True over a None-provenance manifest (the gate was dead code), so the
    test encoded the bug. The extra assertions below pin that the finalized
    manifest actually carries its Decision-D provenance (static + backend) non-None
    — i.e. verified=True is earned, not stamped over missing fields.
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
    # The persisted manifest survives the strict finalize gate, not just the
    # lenient default validate — proving the populated path, not the dead one.
    schema.validate_manifest(manifest, require_populated=True)
    assert manifest["status"] == schema.STATUS_OK
    assert manifest["verified"] is True
    # Decision-D provenance is genuinely populated (config-sourced + backend-sourced).
    assert manifest["aligned_run_record_id"] == "stub-run-record"
    assert manifest["source_split"] == "fixture"
    assert manifest["base_model_id"] == "stub/base-model"
    assert manifest["transformers_version"] == "stub-transformers"
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


# ===========================================================================
# Step-7 GPU-FREE SUITE (test-engineer). All tests below run with ZERO torch /
# transformers / peft against hidden_state_schema + StubExtractionBackend. The
# auditor's TEST note: the schema validators are present and correct but their
# NEGATIVE branches were exercised only by the coder's single end-to-end smoke;
# the suite below authors the thorough negative coverage. Tests assert on the
# CONTRACT (declared adapter state, tensor shape, manifest field-set + crash-safe
# lifecycle) so they survive whichever DI seam shape persists.
# ===========================================================================

import json  # noqa: E402

# numpy + safetensors are HARD test requirements (M4): the persistence-contract
# tests below (the 2-D shape footgun, the safetensors byte round-trip) assert the
# on-disk contract and MUST run — they are NOT pytest.importorskip-gated. A host
# missing them is a misconfigured env (requirements-hidden-state.txt declares them
# mandatory), so these imports error at collection rather than letting the
# round-trip silently vanish from the suite.
import numpy as np  # noqa: E402
import safetensors.numpy as safetensors_numpy  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures / builders for the schema-level units (no model, no stub needed)
# ---------------------------------------------------------------------------


def _valid_arms() -> list[dict]:
    """One disabled base arm + one active arm: the only valid MVP shape."""
    return [
        {"name": "base", "adapter_state": schema.ADAPTER_STATE_DISABLED, "adapter": None},
        {"name": "sft", "adapter_state": schema.ADAPTER_STATE_ACTIVE, "adapter": "/fake/a"},
    ]


def _layer_vectors(num_hidden_layers: int, hidden_dim: int) -> dict:
    """A well-formed final-token stack: N+1 layers, each a 1-D hidden_dim vec."""
    count = schema.expected_layer_count(num_hidden_layers)
    return {layer: [float(layer)] * hidden_dim for layer in range(count)}


def _full_manifest_config() -> dict:
    """A config whose manifest_provenance populates EVERY Decision-D field.

    build_manifest pulls free-form provenance from config['manifest_provenance']
    and owns a handful of fields itself; this fixture supplies non-None values
    for every required field so the finalize-time populated gate can be tested.
    """
    provenance_fields = sorted(schema.REQUIRED_MANIFEST_FIELDS)
    prov = {f: f"val_{f}" for f in provenance_fields}
    # merged_sanity is a bool in the real contract (False, not a string).
    prov["merged_sanity"] = False
    prov["enable_thinking"] = False
    return {
        "model": {"enable_thinking": False},
        "extraction": {
            "layer_list": [0, 1, 2],
            "token_position_rule": schema.TOKEN_POSITION_FINAL_PROMPT,
            "compute_dtype": "bfloat16",
            "persist_dtype": "float32",
            "persistence_format": "safetensors",
        },
        "manifest_provenance": prov,
    }


# ---------------------------------------------------------------------------
# P0 — adapter-state pre-flight (GPU-free tier of the two-tier confound guard)
# Each negative is a DISTINCT test so a regression localizes to one breach.
# ---------------------------------------------------------------------------


def test_arm_states_accepts_one_base_one_active():
    """Positive: exactly one disabled base + one active arm validates."""
    schema.validate_arm_states(_valid_arms())  # must not raise


def test_arm_states_accepts_unloaded_base():
    """`unloaded` is the second valid base form (base model, no adapter loaded)."""
    arms = _valid_arms()
    arms[0]["adapter_state"] = schema.ADAPTER_STATE_UNLOADED
    schema.validate_arm_states(arms)  # must not raise


def test_arm_states_rejects_both_active_two_arm_via_missing_base():
    """Both 2-arm arms active => ZERO base arms; rejected (no h_base anchor).

    With exactly two arms both `active`, the base-arm check fires FIRST (found 0
    base arms), so the confound is caught here on the missing-base branch rather
    than the active-count branch. Either way the dangerous config is refused
    before any forward pass — that is the safety property under test.
    """
    arms = _valid_arms()
    arms[0]["adapter_state"] = schema.ADAPTER_STATE_ACTIVE  # base now also active
    with pytest.raises(ValueError, match="EXACTLY ONE base arm"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_two_active_arms_confound_branch():
    """THE confound branch: one base + TWO active arms hits the active-count guard.

    This is the only arm shape that reaches the `len(active_arms) != 1` check
    with its 'adapter-active-vs-adapter-active confound' message (a 2-arm
    both-active config trips the base-count guard first). Three arms — one
    disabled base plus two distinct active arms — exercises it directly.
    """
    arms = [
        {"name": "base", "adapter_state": schema.ADAPTER_STATE_DISABLED, "adapter": None},
        {"name": "sft", "adapter_state": schema.ADAPTER_STATE_ACTIVE, "adapter": "/a"},
        {"name": "dpo", "adapter_state": schema.ADAPTER_STATE_ACTIVE, "adapter": "/b"},
    ]
    with pytest.raises(ValueError, match="adapter-active-vs-adapter-active confound"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_merged_arm_deferred():
    """`merged` is a reserved enum slot but the path is DEFERRED in the MVP."""
    arms = _valid_arms()
    arms[1]["adapter_state"] = schema.ADAPTER_STATE_MERGED
    with pytest.raises(ValueError, match="merged"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_duplicate_arm_names():
    """Duplicate names collide in the per-arm output tree; rejected pre-flight."""
    arms = _valid_arms()
    arms[1]["name"] = "base"  # collides with the base arm's name
    with pytest.raises(ValueError, match="duplicate arm name"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_missing_base_arm():
    """Zero base arms: nothing anchors h_base; every delta would be poisoned."""
    arms = _valid_arms()
    arms[0]["adapter_state"] = schema.ADAPTER_STATE_ACTIVE
    arms[0]["name"] = "lora2"  # two distinct active arms, zero base
    with pytest.raises(ValueError, match="EXACTLY ONE base arm"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_two_base_zero_active():
    """Two base arms + zero active: the base-count guard fires (found 2)."""
    arms = _valid_arms()
    arms[1]["adapter_state"] = schema.ADAPTER_STATE_DISABLED
    arms[1]["name"] = "base2"  # two distinct base arms, zero active
    with pytest.raises(ValueError, match="EXACTLY ONE base arm"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_missing_active_arm_one_base_only():
    """Exactly one base arm and NO active arm hits the active-count guard.

    A single disabled arm passes the base-count check (found 1) and then fails
    the active-count check (found 0) — the branch that guards 'no LoRA pass to
    contrast against the base'.
    """
    arms = [{"name": "base", "adapter_state": schema.ADAPTER_STATE_DISABLED,
             "adapter": None}]
    with pytest.raises(ValueError, match="EXACTLY ONE active arm"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_empty_arm_list():
    """A non-list / empty arms config is rejected before anything else."""
    with pytest.raises(ValueError, match="non-empty list"):
        schema.validate_arm_states([])


def test_arm_states_rejects_missing_name():
    """An arm without a non-empty `name` is rejected (it keys the output tree)."""
    arms = _valid_arms()
    arms[0]["name"] = ""
    with pytest.raises(ValueError, match="missing a non-empty"):
        schema.validate_arm_states(arms)


def test_arm_states_rejects_invalid_state_value():
    """An adapter_state outside the enum is rejected with the valid set named."""
    arms = _valid_arms()
    arms[1]["adapter_state"] = "frobnicated"
    with pytest.raises(ValueError, match="invalid"):
        schema.validate_arm_states(arms)


# ---------------------------------------------------------------------------
# P0 — tensor-shape + token-position validation (model-free)
# ---------------------------------------------------------------------------


def test_hidden_state_shape_accepts_well_formed_stack():
    """Positive: N+1 contiguous layers, each a 1-D hidden_dim vector."""
    schema.validate_hidden_state_shape(
        layer_vectors=_layer_vectors(num_hidden_layers=3, hidden_dim=8),
        num_hidden_layers=3, hidden_dim=8,
        token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_expected_layer_count_is_n_plus_one():
    """Transformers contract: hidden_states length is num_hidden_layers + 1."""
    assert schema.expected_layer_count(3) == 4
    assert schema.expected_layer_count(28) == 29


def test_hidden_state_shape_rejects_wrong_layer_count():
    """A stack with N (not N+1) layers means the wrong layers were captured."""
    vecs = _layer_vectors(num_hidden_layers=3, hidden_dim=8)
    del vecs[3]  # now 3 layers for num_hidden_layers=3 (want 4)
    with pytest.raises(ValueError, match="layer count"):
        schema.validate_hidden_state_shape(
            layer_vectors=vecs, num_hidden_layers=3, hidden_dim=8,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_hidden_state_shape_rejects_noncontiguous_layer_ids():
    """Right count but a gap in the ids (missing 2, extra 99) is rejected."""
    vecs = _layer_vectors(num_hidden_layers=3, hidden_dim=8)
    vecs[99] = vecs.pop(2)  # 4 entries, ids {0,1,3,99}
    with pytest.raises(ValueError, match="layer ids mismatch"):
        schema.validate_hidden_state_shape(
            layer_vectors=vecs, num_hidden_layers=3, hidden_dim=8,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_hidden_state_shape_rejects_wrong_hidden_dim():
    """A layer vector whose length != hidden_dim is rejected."""
    vecs = _layer_vectors(num_hidden_layers=3, hidden_dim=8)
    vecs[1] = [0.0] * 7  # wrong width
    with pytest.raises(ValueError, match="vector length"):
        schema.validate_hidden_state_shape(
            layer_vectors=vecs, num_hidden_layers=3, hidden_dim=8,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_hidden_state_shape_rejects_2d_vector_via_numpy_shape():
    """The left-padding footgun: a [seq, hidden] 2-D array must NOT length-match.

    _vector_length inspects .shape and rejects rank != 1, so a 2-D tensor
    slipping in is caught as a shape error rather than silently passing because
    its first axis happens to equal hidden_dim.
    """
    vecs = _layer_vectors(num_hidden_layers=2, hidden_dim=4)
    # Replace one layer with a 2-D array whose first axis == hidden_dim (4).
    vecs[1] = np.zeros((4, 4))
    with pytest.raises(ValueError, match="1-D"):
        schema.validate_hidden_state_shape(
            layer_vectors=vecs, num_hidden_layers=2, hidden_dim=4,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_hidden_state_shape_rejects_scalar_layer():
    """A scalar (non-sequence) layer entry is rejected, not treated as length-1."""
    vecs = _layer_vectors(num_hidden_layers=2, hidden_dim=4)
    vecs[0] = 3.14  # scalar
    with pytest.raises(ValueError, match="1-D vector"):
        schema.validate_hidden_state_shape(
            layer_vectors=vecs, num_hidden_layers=2, hidden_dim=4,
            token_position_rule=schema.TOKEN_POSITION_FINAL_PROMPT)


def test_token_position_rule_rejects_unsupported():
    """Only final_prompt_token is supported in the MVP; others rejected."""
    with pytest.raises(ValueError, match="not supported in the MVP"):
        schema.validate_token_position_rule("answer_token_window")


def test_token_position_rule_accepts_final_prompt_token():
    schema.validate_token_position_rule(schema.TOKEN_POSITION_FINAL_PROMPT)


# ---------------------------------------------------------------------------
# P0 — manifest exact-field-set + crash-safe lifecycle (Decision D + D-bis)
# ---------------------------------------------------------------------------


def test_build_manifest_carries_exact_field_set():
    """A built manifest has EXACTLY the Decision-D field set (no more, no less)."""
    config = _full_manifest_config()
    manifest = schema.build_manifest(config=config, extraction_config_sha="deadbeef")
    assert set(manifest.keys()) == schema.REQUIRED_MANIFEST_FIELDS
    schema.validate_manifest(manifest)  # presence-only check passes


def test_build_manifest_defaults_to_launched_unverified():
    """Write-before-invoke: a fresh manifest is status=launched, verified=False."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="deadbeef")
    assert manifest["status"] == schema.STATUS_LAUNCHED
    assert manifest["verified"] is False
    assert manifest["tensor_shapes"] is None  # patched post-forward


def test_build_manifest_rejects_invalid_status():
    with pytest.raises(ValueError, match="status"):
        schema.build_manifest(config=_full_manifest_config(),
                              extraction_config_sha="x", status="bogus")


def test_validate_manifest_rejects_missing_field():
    """A manifest missing a required field is rejected (closed schema)."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    del manifest["base_model_id"]
    with pytest.raises(ValueError, match="missing required field"):
        schema.validate_manifest(manifest)


def test_validate_manifest_rejects_extra_field():
    """The manifest schema is CLOSED: an unexpected field is rejected too."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["surprise_field"] = "oops"
    with pytest.raises(ValueError, match="unexpected field"):
        schema.validate_manifest(manifest)


def test_validate_manifest_rejects_verified_true_when_not_ok():
    """Crash-safe invariant: verified=True is illegal unless status=ok."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["verified"] = True  # but status is still launched
    with pytest.raises(ValueError, match="verified.*True but status"):
        schema.validate_manifest(manifest)


def test_validate_manifest_rejects_nonbool_verified():
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["verified"] = "yes"
    with pytest.raises(ValueError, match="must be bool"):
        schema.validate_manifest(manifest)


def test_validate_manifest_rejects_invalid_status_value():
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["status"] = "running"
    with pytest.raises(ValueError, match="status"):
        schema.validate_manifest(manifest)


def test_validate_manifest_populated_gate_rejects_none_provenance():
    """finalize-time: a None provenance field fails require_populated."""
    config = _full_manifest_config()
    config["manifest_provenance"]["base_model_hash"] = None
    manifest = schema.build_manifest(config=config, extraction_config_sha="x")
    manifest["status"] = schema.STATUS_OK
    manifest["tensor_shapes"] = {"h_base": [4, 8]}
    manifest["verified"] = True
    with pytest.raises(ValueError, match="still None"):
        schema.validate_manifest(manifest, require_populated=True)


def test_validate_manifest_populated_gate_rejects_ok_without_tensor_shapes():
    """finalize-time: status=ok but tensor_shapes None is rejected."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["status"] = schema.STATUS_OK
    manifest["verified"] = True
    manifest["tensor_shapes"] = None
    with pytest.raises(ValueError, match="tensor_shapes is None"):
        schema.validate_manifest(manifest, require_populated=True)


def test_validate_manifest_populated_gate_accepts_complete_ok():
    """finalize-time positive: fully populated, status=ok, tensor_shapes set."""
    manifest = schema.build_manifest(
        config=_full_manifest_config(), extraction_config_sha="x")
    manifest["status"] = schema.STATUS_OK
    manifest["tensor_shapes"] = {"h_base": [4, 8], "h_lora": [4, 8]}
    manifest["verified"] = True
    schema.validate_manifest(manifest, require_populated=True)  # must not raise


# ---------------------------------------------------------------------------
# P0 — config_sha stability (probe.py idiom; key-order-insensitive)
# ---------------------------------------------------------------------------


def test_config_sha_same_config_same_sha():
    config = _stub_config()
    assert schema.config_sha(config) == schema.config_sha(config)


def test_config_sha_is_key_order_insensitive():
    """Reordering dict keys must NOT change the sha (sort_keys=True)."""
    config = _stub_config()
    reordered = dict(reversed(list(config.items())))
    assert schema.config_sha(reordered) == schema.config_sha(config)


def test_config_sha_changes_with_config():
    config = _stub_config()
    sha1 = schema.config_sha(config)
    config["extraction"]["compute_dtype"] = "float16"
    assert schema.config_sha(config) != sha1


def test_config_sha_is_16_hex():
    sha = schema.config_sha(_stub_config())
    assert len(sha) == 16
    int(sha, 16)  # parses as hex (raises ValueError otherwise)


def test_prompt_hash_byte_sensitive():
    """A one-byte prompt difference yields a different prompt hash."""
    assert schema.prompt_hash("abc") != schema.prompt_hash("abd")
    assert schema.prompt_hash("abc") == schema.prompt_hash("abc")


def test_corpus_prompt_hash_order_sensitive():
    """Corpus hash depends on prompt ORDER (it is a per-row identity stream)."""
    assert (schema.corpus_prompt_hash(["a", "b"])
            != schema.corpus_prompt_hash(["b", "a"]))


# ---------------------------------------------------------------------------
# Local model directory provenance (sequential SFT -> DPO/KTO base identity)
# ---------------------------------------------------------------------------


def _write_local_model_dir(root: Path, *, shard_text: str = "weights") -> None:
    root.mkdir()
    (root / "config.json").write_text('{"model_type":"qwen3"}', encoding="utf-8")
    (root / "tokenizer_config.json").write_text(
        '{"tokenizer_class":"Qwen2TokenizerFast"}', encoding="utf-8")
    (root / "model.safetensors.index.json").write_text(
        '{"weight_map":{"layer":"model-00001-of-00001.safetensors"}}',
        encoding="utf-8")
    (root / "model-00001-of-00001.safetensors").write_text(
        shard_text, encoding="utf-8")


def test_local_model_dir_sha256_returns_stable_prefixed_identity(tmp_path):
    """A complete local merged model dir produces populated deterministic provenance."""
    model_dir = tmp_path / "merged_sft_model"
    _write_local_model_dir(model_dir)

    first = hsp._local_model_dir_sha256(str(model_dir))
    second = hsp._local_model_dir_sha256(str(model_dir))

    assert first is not None
    assert first.startswith("local-sha256:")
    assert second == first


def test_local_model_dir_sha256_changes_when_stable_file_changes(tmp_path):
    """The local identity is content-derived, not just path-derived."""
    model_dir = tmp_path / "merged_sft_model"
    _write_local_model_dir(model_dir)
    before = hsp._local_model_dir_sha256(str(model_dir))

    (model_dir / "model-00001-of-00001.safetensors").write_text(
        "changed weights", encoding="utf-8")

    assert hsp._local_model_dir_sha256(str(model_dir)) != before


def test_local_model_dir_sha256_returns_none_for_hub_id():
    """Hub ids are left to transformers _commit_hash / configured revision handling."""
    assert hsp._local_model_dir_sha256("Qwen/Qwen3-4B") is None


def test_local_model_dir_sha256_raises_for_missing_explicit_dir(tmp_path):
    missing = tmp_path / "missing_model"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        hsp._local_model_dir_sha256(str(missing))


def test_local_model_dir_sha256_raises_for_missing_config(tmp_path):
    model_dir = tmp_path / "bad_model"
    model_dir.mkdir()
    (model_dir / "model.safetensors").write_text("weights", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="missing config.json"):
        hsp._local_model_dir_sha256(str(model_dir))


def test_local_model_dir_sha256_raises_for_missing_weight_identity(tmp_path):
    model_dir = tmp_path / "bad_model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="no stable weight identity"):
        hsp._local_model_dir_sha256(str(model_dir))


def test_transformers_backend_provenance_uses_local_hash_without_hub_revision(tmp_path):
    """Local model dirs populate base_model_revision/hash without weakening finalize."""
    model_dir = tmp_path / "merged_sft_model"
    _write_local_model_dir(model_dir)
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text('{"r":8}', encoding="utf-8")

    class _Config:
        _name_or_path = str(model_dir)
        _commit_hash = None

    class _Model:
        config = _Config()

    class _Tokenizer:
        name_or_path = str(model_dir)

    backend = hsp.TransformersPeftBackend.__new__(hsp.TransformersPeftBackend)
    backend.model = _Model()
    backend.model_name = str(model_dir)
    backend.model_revision = None
    backend.active_adapter_path = str(adapter_dir)
    backend.tokenizer = _Tokenizer()
    backend._peft = type("Peft", (), {"__version__": "test-peft"})
    backend._transformers = type("Transformers", (), {"__version__": "test-transformers"})

    prov = backend.provenance()

    assert prov["base_model_revision"].startswith("local-sha256:")
    assert prov["base_model_hash"] == prov["base_model_revision"]
    assert prov["base_model_id"] == str(model_dir)


def test_transformers_backend_provenance_preserves_hub_commit_behavior(tmp_path):
    """A hub-resolved commit remains the base revision; no local hash is substituted."""
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text('{"r":8}', encoding="utf-8")

    class _Config:
        _name_or_path = "Qwen/Qwen3-4B"
        _commit_hash = "abc123hubcommit"

    class _Model:
        config = _Config()

    class _Tokenizer:
        name_or_path = "Qwen/Qwen3-4B"

    backend = hsp.TransformersPeftBackend.__new__(hsp.TransformersPeftBackend)
    backend.model = _Model()
    backend.model_name = "Qwen/Qwen3-4B"
    backend.model_revision = None
    backend.active_adapter_path = str(adapter_dir)
    backend.tokenizer = _Tokenizer()
    backend._peft = type("Peft", (), {"__version__": "test-peft"})
    backend._transformers = type("Transformers", (), {"__version__": "test-transformers"})

    prov = backend.provenance()

    assert prov["base_model_revision"] == "abc123hubcommit"
    assert prov["base_model_hash"] == "Qwen/Qwen3-4B"


# ---------------------------------------------------------------------------
# safetensors persistence contract (metadata is string-only; round-trip)
# ---------------------------------------------------------------------------


def test_safetensors_metadata_is_string_only():
    md = schema.safetensors_metadata("cfgsha", "base_key", "h_base")
    assert all(isinstance(v, str) for v in md.values())
    schema.validate_safetensors_metadata(md)  # must not raise


def test_safetensors_metadata_rejects_bad_role():
    with pytest.raises(ValueError, match="tensor_role"):
        schema.safetensors_metadata("cfgsha", "key", "not_a_role")


def test_validate_safetensors_metadata_rejects_nonstring_value():
    with pytest.raises(ValueError, match="must be str"):
        schema.validate_safetensors_metadata({"k": 123})


def test_safetensors_round_trip_via_persist(tmp_path):
    """A persisted shard round-trips cleanly (numpy+safetensors hard-required, M4).

    Exercises _persist_row_tensors (the stub-reachable persistence path): write
    h_base/h_lora/delta shards, then load one back and confirm the layer keys,
    the values, and the string-only metadata survive the round-trip.

    numpy + safetensors are HARD requirements (M4): this round-trip is no longer
    importorskip-gated, so a CI env missing them errors here rather than skipping.
    """
    config = _stub_config()
    h_base = _layer_vectors(num_hidden_layers=2, hidden_dim=8)
    h_lora = {k: [v + 1.0 for v in vec] for k, vec in h_base.items()}
    delta = hsp._vector_delta(h_lora, h_base)
    shapes: dict = {}
    hsp._persist_row_tensors(
        tmp_path, "000000000000|fix_known_1", "cfgsha12345678",
        h_base, h_lora, delta, config, shapes)

    base_shard = tmp_path / "000000000000_fix_known_1__h_base.safetensors"
    assert base_shard.exists()
    loaded = safetensors_numpy.load_file(str(base_shard))
    assert set(loaded.keys()) == {f"L{i}" for i in range(len(h_base))}
    assert list(loaded["L1"]) == h_base[1]
    # delta shard exists and equals h_lora - h_base (== 1.0 per element here).
    delta_shard = tmp_path / "000000000000_fix_known_1__delta.safetensors"
    assert delta_shard.exists()
    delta_loaded = safetensors_numpy.load_file(str(delta_shard))
    assert all(abs(x - 1.0) < 1e-6 for x in delta_loaded["L0"])
    # tensor_shapes recorded as [n_layers, hidden_dim].
    assert shapes["h_base"] == [len(h_base), 8]


# ---------------------------------------------------------------------------
# Leakage / frozen-split alignment (align by probe_pool_row_key ONLY)
# ---------------------------------------------------------------------------


def _select_config(monkeypatch, **overrides) -> dict:
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    for k, v in overrides.items():
        config["selection"][k] = v
    return config


def test_select_matched_slice_aligns_by_key_and_excludes_discard(monkeypatch):
    """4 selected (2 known + 2 unknown); the discard fixture row is excluded."""
    config = _select_config(monkeypatch)
    rows = hsp.select_matched_slice(config)
    assert len(rows) == 4
    keys = {r["probe_pool_row_key"] for r in rows}
    assert "000000000004|fix_discard_1" not in keys
    # Frozen labels propagate from the frozen split, not the probe row's label.
    labels = {r["probe_pool_row_key"]: r["label"] for r in rows}
    assert labels["000000000000|fix_known_1"] == "known"
    assert labels["000000000002|fix_unknown_1"] == "unknown"


def test_select_matched_slice_carries_alignment_identity(monkeypatch):
    """Each row carries the by-key alignment identity, never loose text only."""
    config = _select_config(monkeypatch)
    rows = hsp.select_matched_slice(config)
    row = rows[0]
    assert set(row) >= {"probe_pool_row_key", "question", "label",
                        "frozen_label", "probe_label", "aligned_probe_config_sha"}
    assert row["aligned_probe_config_sha"] == "fixturesha000001"


def test_select_matched_slice_honors_n_known_cap(monkeypatch):
    """A smaller n_known deterministically selects a subset (frozen-split cap)."""
    config = _select_config(monkeypatch, n_known=1, n_unknown=1)
    rows = hsp.select_matched_slice(config)
    assert len(rows) == 2
    labels = sorted(r["label"] for r in rows)
    assert labels == ["known", "unknown"]


def test_select_matched_slice_honors_exact_row_keys_file(monkeypatch, tmp_path):
    """Exact row-key files select a fixed slice in file order."""
    row_keys_file = tmp_path / "row_keys.txt"
    row_keys_file.write_text(
        "\n".join([
            "# fixed targeted panel",
            "000000000003|fix_unknown_2",
            "",
            "000000000000|fix_known_1",
        ]),
        encoding="utf-8",
    )
    config = _select_config(
        monkeypatch,
        row_keys_file=str(row_keys_file),
    )

    rows = hsp.select_matched_slice(config)

    assert [r["probe_pool_row_key"] for r in rows] == [
        "000000000003|fix_unknown_2",
        "000000000000|fix_known_1",
    ]
    assert [r["label"] for r in rows] == ["unknown", "known"]


def test_select_matched_slice_row_keys_file_rejects_duplicate(monkeypatch, tmp_path):
    row_keys_file = tmp_path / "row_keys.txt"
    row_keys_file.write_text(
        "000000000000|fix_known_1\n000000000000|fix_known_1\n",
        encoding="utf-8",
    )
    config = _select_config(monkeypatch, row_keys_file=str(row_keys_file))

    with pytest.raises(ValueError, match="duplicate row key"):
        hsp.select_matched_slice(config)


def test_select_matched_slice_row_keys_file_rejects_outside_frozen(
        monkeypatch, tmp_path):
    row_keys_file = tmp_path / "row_keys.txt"
    row_keys_file.write_text("000000000004|fix_discard_1\n", encoding="utf-8")
    config = _select_config(monkeypatch, row_keys_file=str(row_keys_file))

    with pytest.raises(ValueError, match="outside the frozen"):
        hsp.select_matched_slice(config)


def test_select_matched_slice_raises_on_key_absent_from_results(monkeypatch, tmp_path):
    """A frozen key with no matching probe_results row aborts (must be probed)."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({
        "known_question_keys": ["key_present", "key_missing"],
        "unknown_question_keys": [],
    }))
    results = tmp_path / "results.jsonl"
    results.write_text(json.dumps({
        "probe_pool_row_key": "key_present", "question": "q",
        "label": "known", "probe_config_sha": "s"}) + "\n")
    config = _stub_config()
    config["selection"] = {"questions_frozen": "frozen.json",
                           "probe_results": "results.jsonl",
                           "n_known": 2, "n_unknown": 0, "selection_seed": 1}
    with pytest.raises(ValueError, match="not found"):
        hsp.select_matched_slice(config)


def test_select_matched_slice_raises_on_absent_results_file(monkeypatch, tmp_path):
    """A missing probe_results.jsonl is an actionable FileNotFoundError."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"known_question_keys": ["k"],
                                  "unknown_question_keys": []}))
    config = _stub_config()
    config["selection"] = {"questions_frozen": "frozen.json",
                           "probe_results": "does_not_exist.jsonl",
                           "n_known": 1, "n_unknown": 0, "selection_seed": 1}
    with pytest.raises(FileNotFoundError, match="alignment source"):
        hsp.select_matched_slice(config)


def _selfaware_manifest_payload(rows: list[dict]) -> dict:
    return {
        "schema_version": "mechinterp-selfaware-frozen-row-manifest/v1",
        "scope": {"not_probe_pool_runner_ready": True},
        "rows": rows,
    }


def _selfaware_manifest_row(row_key: str, label: str, strata: list[str]) -> dict:
    return {
        "row_key": row_key,
        "stable_identity": {
            "eval_set": "selfaware",
            "row_index": 1,
            "id": "selfaware-2",
            "source": "selfaware",
        },
        "question": "SelfAware question?",
        "prompt": "SelfAware question?",
        "label": label,
        "answer_value": None,
        "aliases": [],
        "strata": strata,
        "source_arms": {
            "sft_merged_seed1": {"refused": True, "truthful": True},
        },
    }


def test_select_matched_slice_loads_selfaware_manifest_rows(monkeypatch, tmp_path):
    """SelfAware selection preserves frozen row identity and metadata."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    manifest_path = tmp_path / "manifests" / "selfaware.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(_selfaware_manifest_payload([
        _selfaware_manifest_row(
            "selfaware::selfaware::000001::selfaware-2",
            "unknown",
            ["stable_unknown_refusal"],
        ),
        _selfaware_manifest_row(
            "selfaware::selfaware::000002::selfaware-3",
            "known",
            ["stable_known_correct"],
        ),
    ])), encoding="utf-8")
    config = _stub_config()
    config["selection"] = {
        "source": "selfaware_manifest",
        "manifest": "manifests/selfaware.json",
        "strata": ["stable_unknown_refusal"],
    }

    rows = hsp.select_matched_slice(config)

    assert len(rows) == 1
    row = rows[0]
    assert row["probe_pool_row_key"] == "selfaware::selfaware::000001::selfaware-2"
    assert row["row_key"] == "selfaware::selfaware::000001::selfaware-2"
    assert row["stable_identity"]["id"] == "selfaware-2"
    assert row["strata"] == ["stable_unknown_refusal"]
    assert row["probe_label"] is None
    assert (
        row["aligned_probe_config_sha"]
        == hsp.selfaware_manifest_provenance_sha(manifest_path)
    )


def test_selfaware_manifest_loader_fails_on_duplicate_row_key(tmp_path):
    manifest_path = tmp_path / "selfaware.json"
    row = _selfaware_manifest_row(
        "selfaware::selfaware::000001::selfaware-2",
        "unknown",
        ["stable_unknown_refusal"],
    )
    manifest_path.write_text(
        json.dumps(_selfaware_manifest_payload([row, row])),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate SelfAware manifest row_key"):
        hsp.load_selfaware_manifest_rows(manifest_path)


def test_selfaware_manifest_row_conversion_requires_identity_fields():
    row = _selfaware_manifest_row(
        "selfaware::selfaware::000001::selfaware-2",
        "unknown",
        ["stable_unknown_refusal"],
    )
    del row["stable_identity"]

    with pytest.raises(ValueError, match="missing"):
        hsp.convert_selfaware_manifest_row(row, index=0)


def test_selfaware_tensor_key_is_filesystem_safe():
    assert (
        hsp.safe_tensor_key("selfaware::selfaware::000001::selfaware-2")
        == "selfaware__selfaware__000001__selfaware-2"
    )


def test_selfaware_manifest_config_parses_and_selects_no_gpu():
    config_path = (
        REPO_ROOT
        / "archive"
        / "experiment"
        / "phase1"
        / "probe"
        / "config"
        / "selfaware-hs"
        / "hidden_state_selfaware_manifest_sft_dpo_seed1.yaml"
    )
    config, cfg_sha = hsp.parse_config(config_path)
    rows = hsp.select_matched_slice(config)

    assert len(cfg_sha) == 16
    assert config["selection"]["source"] == "selfaware_manifest"
    assert len(rows) == 128
    assert rows[0]["row_key"].startswith("selfaware::selfaware::")
    assert rows[0]["strata"]
    assert rows[0]["aligned_probe_config_sha"].startswith(
        "selfaware-manifest-sha256:"
    )


def test_repo_relative_manifest_config_parses_and_selects_no_gpu():
    """Migrated experiment-local manifests can be referenced repo-relatively."""
    config_path = (
        REPO_ROOT
        / "experiments"
        / "xdataset-probe-transfer"
        / "hidden_state_kuq_manifest_clean_sft_grpo_v2_seed1_full.yaml"
    )
    config, cfg_sha = hsp.parse_config(config_path)
    rows = hsp.select_matched_slice(config)

    assert len(cfg_sha) == 16
    assert config["selection"]["manifest"].startswith("experiments/")
    assert len(rows) == 1000
    assert rows[0]["row_key"].startswith("kuq::kuq::")
    assert rows[0]["aligned_probe_config_sha"].startswith(
        "selfaware-manifest-sha256:"
    )


def test_selfaware_manifest_stub_extraction_finalizes_with_manifest_provenance(
        monkeypatch, tmp_path):
    """SelfAware manifest selection supplies non-null finalize provenance."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    manifest_path = tmp_path / "manifests" / "selfaware.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(_selfaware_manifest_payload([
        _selfaware_manifest_row(
            "selfaware::selfaware::000001::selfaware-2",
            "unknown",
            ["stable_unknown_refusal"],
        ),
    ])), encoding="utf-8")
    config = _stub_config()
    config["selection"] = {
        "source": "selfaware_manifest",
        "manifest": "manifests/selfaware.json",
        "strata": ["stable_unknown_refusal"],
    }
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    expected_sha = hsp.selfaware_manifest_provenance_sha(manifest_path)

    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    out_dir = tmp_path / "out"
    manifest_out = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    manifest = json.loads(manifest_out.read_text())
    schema.validate_manifest(manifest, require_populated=True)
    assert manifest["aligned_probe_config_sha"] == expected_sha
    row = json.loads((out_dir / "rows.jsonl").read_text().strip())
    assert row["aligned_probe_config_sha"] == expected_sha


# ---------------------------------------------------------------------------
# parse_config — model-free pre-flight at parse time
# ---------------------------------------------------------------------------


def test_parse_config_runs_preflight_and_returns_sha(tmp_path):
    """parse_config validates arms + token rule and returns a stable sha."""
    config = _stub_config()
    config_path = tmp_path / "hidden_state_probe.yaml"
    import yaml
    config_path.write_text(yaml.safe_dump(config))
    parsed, cfg_sha = hsp.parse_config(config_path)
    assert cfg_sha == schema.config_sha(parsed)
    assert len(cfg_sha) == 16


def test_parse_config_rejects_both_active_at_parse_time(tmp_path):
    """A malformed (both-active) config fails at PARSE, before any model load.

    The base arm flipped to `active` has no adapter path, so adapter resolution
    rejects it first ("active arm has no adapter path"); the dangerous config
    never reaches a model load. (A both-active config that DID carry adapter
    paths on both arms would instead trip the validate_arm_states base-count
    guard a few lines later — both are parse-time rejections.)
    """
    config = _stub_config()
    config["arms"][0]["adapter_state"] = "active"
    config_path = tmp_path / "bad.yaml"
    import yaml
    config_path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="no adapter path"):
        hsp.parse_config(config_path)


def test_parse_config_rejects_both_active_with_adapters_via_preflight(tmp_path):
    """Both-active WITH adapter paths reaches and trips the validate_arm_states guard."""
    config = _stub_config()
    config["arms"][0]["adapter_state"] = "active"
    config["arms"][0]["adapter"] = "/fake/base_adapter"  # so resolution passes
    config_path = tmp_path / "bad2.yaml"
    import yaml
    config_path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="EXACTLY ONE base arm"):
        hsp.parse_config(config_path)


# ---------------------------------------------------------------------------
# M2 — resolve_eval_arm_adapters BY-VALUE mirror resolution
# (the PROD path: prod config sets eval_arms_source; this was green-by-omission)
# ---------------------------------------------------------------------------


def _write_eval_config(tmp_path, name_to_adapter: dict) -> str:
    """Write a tiny eval-config fixture with an arms[] name->adapter mapping.

    Returns the path RELATIVE to tmp_path (the test monkeypatches PROBE_DIR to
    tmp_path, and resolve_eval_arm_adapters anchors eval_arms_source at PROBE_DIR).
    """
    import yaml
    eval_cfg = {"arms": [{"name": n, "adapter": a}
                         for n, a in name_to_adapter.items()]}
    eval_path = tmp_path / "eval_smoke.yaml"
    eval_path.write_text(yaml.safe_dump(eval_cfg))
    return "eval_smoke.yaml"


def test_resolve_eval_arm_adapters_backfills_active_arm_by_value(tmp_path, monkeypatch):
    """The PROD mirror path: an active arm with adapter=None back-fills from the
    eval config's name->adapter mapping (this is what the production config does
    via eval_arms_source, and was previously exercised by NO test).
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    eval_source = _write_eval_config(tmp_path, {"sft": "/mirror/sft_adapter"})
    config = _stub_config()
    config["eval_arms_source"] = eval_source
    config["arms"][1]["adapter"] = None  # active arm relies on the mirror

    resolved = hsp.resolve_eval_arm_adapters(config, tmp_path / "unused.yaml")

    active = next(a for a in resolved["arms"]
                 if a["adapter_state"] == schema.ADAPTER_STATE_ACTIVE)
    assert active["adapter"] == "/mirror/sft_adapter"  # filled BY VALUE from eval


def test_resolve_eval_arm_adapters_explicit_overrides_mirror(tmp_path, monkeypatch):
    """An explicit arms[].adapter takes precedence over the eval-config mirror."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    eval_source = _write_eval_config(tmp_path, {"sft": "/mirror/sft_adapter"})
    config = _stub_config()
    config["eval_arms_source"] = eval_source
    config["arms"][1]["adapter"] = "/explicit/override"  # explicit wins

    resolved = hsp.resolve_eval_arm_adapters(config, tmp_path / "unused.yaml")

    active = next(a for a in resolved["arms"]
                 if a["adapter_state"] == schema.ADAPTER_STATE_ACTIVE)
    assert active["adapter"] == "/explicit/override"  # mirror did NOT clobber it


def test_resolve_eval_arm_adapters_raises_when_active_unresolvable(tmp_path, monkeypatch):
    """An active arm with no explicit adapter AND no eval-config mapping aborts."""
    monkeypatch.setattr(hsp, "PROBE_DIR", tmp_path)
    eval_source = _write_eval_config(tmp_path, {"other_arm": "/mirror/x"})
    config = _stub_config()
    config["eval_arms_source"] = eval_source
    config["arms"][1]["adapter"] = None  # active arm "sft" not in the mapping

    with pytest.raises(ValueError, match="no adapter path"):
        hsp.resolve_eval_arm_adapters(config, tmp_path / "unused.yaml")


# ---------------------------------------------------------------------------
# End-to-end stub pipeline: select -> extract -> persist -> verify -> resume
# ---------------------------------------------------------------------------


def _run_stub_extraction(tmp_path, monkeypatch, *, num_hidden_layers=2,
                         hidden_dim=8):
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    backend = hsp.StubExtractionBackend(
        num_hidden_layers=num_hidden_layers, hidden_dim=hidden_dim)
    out_dir = tmp_path / "out"
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)
    return config, cfg_sha, slice_rows, backend, out_dir, manifest_path


def test_run_extraction_marks_ok_and_verified(tmp_path, monkeypatch):
    """A clean stub run finishes status=ok, verified=True, with tensor_shapes."""
    _c, _s, _r, _b, out_dir, manifest_path = _run_stub_extraction(tmp_path, monkeypatch)
    manifest = json.loads(manifest_path.read_text())
    schema.validate_manifest(manifest)
    assert manifest["status"] == schema.STATUS_OK
    assert manifest["verified"] is True
    assert manifest["tensor_shapes"] is not None


def test_run_extraction_finalize_gate_raises_on_underpopulated_provenance(
        tmp_path, monkeypatch):
    """NEGATIVE finalize gate (B2): an under-populated manifest RAISES at finalize.

    Drives a full run whose config nulls a Decision-D field (aligned_run_record_id).
    The rows + tensors get written, but the require_populated gate at
    run_extraction:551 must reject the finalize and re-raise rather than ship
    verified=True over a None field. This is the regression that the original
    line-80 smoke could NOT catch (the gate was dead code).
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _under_populated_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    out_dir = tmp_path / "out"

    with pytest.raises(ValueError, match="aligned_run_record_id"):
        hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    # The gate fired at FINALIZE (after extraction), so no verified manifest was
    # shipped: any manifest on disk is the pre-finalize launched/ok-but-rejected
    # write, never a status=ok+verified=True artifact over None provenance.
    manifest_path = out_dir / config["output"]["manifest_filename"]
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assert not (manifest.get("status") == schema.STATUS_OK
                    and manifest.get("verified") is True)


def test_run_extraction_finalize_gate_passes_on_full_provenance(tmp_path, monkeypatch):
    """POSITIVE finalize gate: a fully-populated run survives require_populated=True.

    The companion to the negative test: with every Decision-D field non-None the
    finalize gate passes, the persisted manifest itself re-validates under the
    STRICT gate, and verified=True is earned over populated provenance.
    """
    _c, _s, _r, _b, out_dir, manifest_path = _run_stub_extraction(tmp_path, monkeypatch)
    manifest = json.loads(manifest_path.read_text())
    # The on-disk manifest passes the strict gate, not merely the lenient default.
    schema.validate_manifest(manifest, require_populated=True)
    assert manifest["status"] == schema.STATUS_OK
    assert manifest["verified"] is True
    assert manifest["aligned_run_record_id"] is not None
    assert manifest["source_split"] is not None


def test_run_extraction_writes_one_row_per_selected_key(tmp_path, monkeypatch):
    _c, _s, slice_rows, _b, out_dir, _m = _run_stub_extraction(tmp_path, monkeypatch)
    rows = [json.loads(l) for l in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == len(slice_rows) == 4
    assert {r["probe_pool_row_key"] for r in rows} == {
        r["probe_pool_row_key"] for r in slice_rows}


def test_run_extraction_persists_all_three_tensor_roles(tmp_path, monkeypatch):
    """Each row writes h_base, h_lora, delta shards (delta persisted, not recomputed)."""
    _c, _s, _r, _b, out_dir, _m = _run_stub_extraction(tmp_path, monkeypatch)
    assert list(out_dir.glob("*__h_base.safetensors"))
    assert list(out_dir.glob("*__h_lora.safetensors"))
    assert list(out_dir.glob("*__delta.safetensors"))


def test_run_extraction_persist_delta_false_writes_no_delta_shard(tmp_path, monkeypatch):
    """M3: persist_delta=False persists only h_base/h_lora, NO delta shard.

    Every other config uses persist_delta=True; this is the previously-untested
    branch where _extract_rows passes delta=None and _persist_row_tensors skips
    the delta role. h_base/h_lora must still be written and the run still ok.
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    config["extraction"]["persist_delta"] = False
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    out_dir = tmp_path / "out"
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)

    assert list(out_dir.glob("*__h_base.safetensors"))
    assert list(out_dir.glob("*__h_lora.safetensors"))
    assert not list(out_dir.glob("*__delta.safetensors"))  # delta suppressed
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == schema.STATUS_OK


def test_run_extraction_row_stamps_prompt_hash_and_cfg_sha(tmp_path, monkeypatch):
    _c, cfg_sha, _r, _b, out_dir, _m = _run_stub_extraction(tmp_path, monkeypatch)
    rows = [json.loads(l) for l in (out_dir / "rows.jsonl").read_text().splitlines()]
    for row in rows:
        assert row["extraction_config_sha"] == cfg_sha
        assert len(row["prompt_hash"]) == 16
        assert row["layer_count"] == schema.expected_layer_count(2)


def test_run_extraction_is_resumable_idempotent(tmp_path, monkeypatch):
    """A second run over the same out_dir appends NOTHING (all keys done)."""
    config, cfg_sha, slice_rows, backend, out_dir, _m = _run_stub_extraction(
        tmp_path, monkeypatch)
    first = (out_dir / "rows.jsonl").read_text()
    # Re-run with a fresh backend instance (deterministic stub).
    backend2 = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    hsp.run_extraction(config, cfg_sha, backend2, slice_rows, out_dir)
    second = (out_dir / "rows.jsonl").read_text()
    assert second == first  # idempotent: no duplicate rows


def test_stub_h_base_differs_from_h_lora_structurally(tmp_path, monkeypatch):
    """The stub seeds h_base != h_lora by arm_state, so delta is non-trivial.

    This is the GPU-FREE structural analogue of the GPU-only numerical
    h_base!=h_lora assertion; it proves the harness wires distinct arm states
    into distinct vectors (the seam works), NOT that real LoRA moves activations.
    """
    backend = hsp.StubExtractionBackend(num_hidden_layers=2, hidden_dim=8)
    rendered = backend.render("Who wrote Paradise Lost?")
    h_base = backend.forward_hidden_states(rendered, schema.ADAPTER_STATE_DISABLED, None)
    h_lora = backend.forward_hidden_states(rendered, schema.ADAPTER_STATE_ACTIVE, "sft")
    assert h_base != h_lora
    delta = hsp._vector_delta(h_lora, h_base)
    assert any(any(abs(x) > 0 for x in vec) for vec in delta.values())


def test_run_extraction_marks_failed_on_backend_error(tmp_path, monkeypatch):
    """Crash-safe: a backend that raises mid-forward leaves status=failed on disk.

    Decision D-bis: the manifest is launched-before-invoke, so a crash during
    the forward must patch the on-disk manifest to `failed` (never silently
    leave it `launched` or, worse, `ok`).
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    out_dir = tmp_path / "out"

    class _ExplodingBackend:
        num_hidden_layers = 2
        hidden_dim = 8

        def render(self, question):
            return f"<|stub|>{question}"

        def forward_hidden_states(self, rendered, arm_state, adapter_name):
            raise RuntimeError("simulated GPU OOM mid-forward")

    with pytest.raises(RuntimeError, match="extraction failed after launch"):
        hsp.run_extraction(config, cfg_sha, _ExplodingBackend(), slice_rows, out_dir)

    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["status"] == schema.STATUS_FAILED
    assert manifest["verified"] is False  # never verified on a failed run


def test_run_extraction_validates_arm_tensor_shapes(tmp_path, monkeypatch):
    """A backend emitting a mis-shaped stack is caught and marks the run failed.

    Guards the harness's _validate_arm_tensors call: a backend whose
    forward returns the wrong layer count must fail the run (status=failed),
    not silently persist a malformed extraction.
    """
    monkeypatch.setattr(hsp, "PROBE_DIR", PROBE_DIR)
    config = _stub_config()
    cfg_sha = schema.config_sha(config)
    slice_rows = hsp.select_matched_slice(config)
    out_dir = tmp_path / "out"

    class _WrongShapeBackend:
        num_hidden_layers = 2  # harness expects 3 layers (N+1)
        hidden_dim = 8

        def render(self, question):
            return f"<|stub|>{question}"

        def forward_hidden_states(self, rendered, arm_state, adapter_name):
            # Emit only 2 layers (should be expected_layer_count(2) == 3).
            return {0: [0.0] * 8, 1: [0.0] * 8}

    with pytest.raises(RuntimeError, match="extraction failed after launch"):
        hsp.run_extraction(config, cfg_sha, _WrongShapeBackend(), slice_rows, out_dir)
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["status"] == schema.STATUS_FAILED
