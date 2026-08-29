from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import synaptic_host.cli as cli
from synaptic_host.cli import (
    TrainingRunCommandCodeV1,
    TrainingRunCommandResultV1,
    TrainingRunCommandStatusV1,
    TrainingRunIngressV1,
    dispatch_validated_training_run_v1,
    emit_training_run_result_v1,
    prepare_training_run_ingress_v1,
)


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"


@pytest.fixture(autouse=True)
def _isolated_engine_import_state():
    original = {
        name: value for name, value in sys.modules.items()
        if name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
    }
    for name in original:
        sys.modules.pop(name, None)
    cli._ENGINE_CONTRACT_CACHE = None
    try:
        yield
    finally:
        for name in tuple(sys.modules):
            if name == "synaptic_tuner" or name.startswith("synaptic_tuner."):
                sys.modules.pop(name, None)
        sys.modules.update(original)
        cli._ENGINE_CONTRACT_CACHE = None


def _document() -> dict[str, object]:
    return {
        "schema_version": "synaptic-training-input/v1",
        "method": "sft",
        "model": {
            "ref": "organization/model", "revision": "revision-1",
            "tokenizer_revision": "tokenizer-1",
        },
        "dataset": {"ref": "dataset://organization/corpus"},
        "hyperparameters": {
            "schema_version": "synaptic-sft-hyperparameters/v1",
            "batch_size": 2, "gradient_accumulation_steps": 4,
            "learning_rate": 0.0002,
            "duration": {"max_steps": 100, "num_epochs": None},
            "max_seq_length": 2048, "seed": 42, "save_steps": 25,
            "save_total_limit": 2, "lora_rank": 16, "lora_alpha": 32,
            "lora_dropout": 0.05,
            "lora_target_modules": ["k_proj", "q_proj", "v_proj"],
            "use_dora": False, "use_rslora": True,
            "init_lora_weights": True, "split_dataset": False,
        },
        "artifacts": {
            "required_kinds": ["final_model", "training_lineage"],
            "retain_checkpoints": True,
        },
    }


def _project(tmp_path: Path, content: bytes | None = None) -> Path:
    training = tmp_path / "training"
    training.mkdir(parents=True)
    payload = (
        json.dumps(_document(), sort_keys=True, separators=(",", ":")).encode()
        if content is None else content
    )
    (training / "input.json").write_bytes(payload)
    return tmp_path


def _argv(provider: str = "modal", config: str = "project://training/input.json",
          destination: str = "provider-staging") -> list[str]:
    return [
        "training", "run", "--provider", provider, "--config", config,
        "--destination", destination,
    ]


def _ingress(tmp_path: Path, provider: str = "modal") -> TrainingRunIngressV1:
    value = prepare_training_run_ingress_v1(
        _argv(provider), project_root=_project(tmp_path), engine_root=ENGINE
    )
    assert type(value) is TrainingRunIngressV1
    return value


def test_valid_ingress_binds_exact_source_input_and_envelope(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path)
    source = (tmp_path / "training/input.json").read_bytes()
    assert ingress.source_sha256 == hashlib.sha256(source).hexdigest()
    assert ingress.input_digest == ingress.training_input.input_digest()
    assert cli._ENGINE_CONTRACT_CACHE is not None
    assert ingress.contract_identity_digest == cli._ENGINE_CONTRACT_CACHE[3].identity.identity_digest
    assert ingress.envelope_digest == ingress.recomputed_envelope_digest()
    assert ingress.envelope_body() == {
        "schema_version": "synaptic-training-run-ingress/v1",
        "provider_ref": "modal", "config_ref": "project://training/input.json",
        "destination_ref": "provider-staging",
        "input_digest": ingress.input_digest, "source_sha256": ingress.source_sha256,
        "contract_identity_digest": ingress.contract_identity_digest,
    }
    with pytest.raises(dataclasses.FrozenInstanceError):
        ingress.provider_ref = "docker"  # type: ignore[misc]


@pytest.mark.parametrize(
    "argv",
    [
        [], ["provider", "deploy"], ["training", "start"], ["training", "run"],
        _argv() + ["extra"], _argv() + ["--provider", "modal"],
        ["training", "run", "--provider", "modal", "--provider", "modal",
         "--destination", "provider-staging"],
        ["training", "run", "--provider", "--config", "x", "--destination", "y"],
    ],
)
def test_only_exact_training_run_grammar_is_accepted(argv: list[str]) -> None:
    result = prepare_training_run_ingress_v1(
        argv, project_root=ROOT, engine_root=ENGINE
    )
    assert type(result) is TrainingRunCommandResultV1
    assert result.error_code is TrainingRunCommandCodeV1.COMMAND_INVALID
    assert result.provider_ref is result.config_ref is result.destination_ref is None


def test_options_may_reorder_but_each_occurs_once(tmp_path: Path) -> None:
    argv = [
        "training", "run", "--destination", "provider-staging",
        "--provider", "modal", "--config", "project://training/input.json",
    ]
    result = prepare_training_run_ingress_v1(
        argv, project_root=_project(tmp_path), engine_root=ENGINE
    )
    assert type(result) is TrainingRunIngressV1


def test_destination_rejects_before_config_or_engine_effects(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_read_config", lambda *_args: pytest.fail("read"))
    result = prepare_training_run_ingress_v1(
        _argv(destination="hf://bucket"), project_root=ROOT, engine_root=Path("missing")
    )
    assert result.error_code is TrainingRunCommandCodeV1.DESTINATION_INVALID
    assert result.provider_ref == "modal"
    assert result.destination_ref is result.config_ref is result.input_digest is None


def test_unknown_provider_is_closed() -> None:
    result = prepare_training_run_ingress_v1(
        _argv(provider="huggingface"), project_root=ROOT, engine_root=ENGINE
    )
    assert result.error_code is TrainingRunCommandCodeV1.PROVIDER_INVALID
    assert result.provider_ref is None


@pytest.mark.parametrize(
    "reference",
    [
        "training/input.json", "project://training/", "project://training/../x",
        "project://training/./x", "project://training/~/x",
        "project://training/a\\b", "project://training/a%2fb",
        "project://training/a?x", "project://training/a#x",
        "project://training/C:file", "project://training//x",
    ],
)
def test_config_reference_is_exact_and_closed(reference: str) -> None:
    result = prepare_training_run_ingress_v1(
        _argv(config=reference), project_root=ROOT, engine_root=ENGINE
    )
    assert result.error_code is TrainingRunCommandCodeV1.CONFIG_REF_INVALID
    assert result.provider_ref == "modal"
    assert result.destination_ref == "provider-staging"
    assert result.config_ref is None


def test_config_missing_oversize_and_invalid_utf8_are_totalized(tmp_path: Path) -> None:
    project = tmp_path / "missing"
    project.mkdir()
    (project / "training").mkdir()
    missing = prepare_training_run_ingress_v1(
        _argv(), project_root=project, engine_root=ENGINE
    )
    assert missing.error_code is TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE
    oversize = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path / "large", b"x" * 65537), engine_root=ENGINE
    )
    assert oversize.error_code is TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE
    invalid = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path / "utf8", b"\xff"), engine_root=ENGINE
    )
    assert invalid.error_code is TrainingRunCommandCodeV1.INPUT_INVALID


def test_config_file_must_be_stable(monkeypatch, tmp_path: Path) -> None:
    project = _project(tmp_path)
    original = cli._stat_identity
    calls = 0

    def changed(value):
        nonlocal calls
        calls += 1
        identity = original(value)
        return identity if calls < 4 else (*identity[:-1], identity[-1] + 1)

    monkeypatch.setattr(cli, "_stat_identity", changed)
    result = prepare_training_run_ingress_v1(
        _argv(), project_root=project, engine_root=ENGINE
    )
    assert result.error_code is TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE


def test_invalid_training_document_is_closed_and_adjacent(tmp_path: Path) -> None:
    result = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path, b'{"secret":"not echoed"}'),
        engine_root=ENGINE,
    )
    assert result.error_code is TrainingRunCommandCodeV1.INPUT_INVALID
    assert result.provider_ref == "modal"
    assert result.config_ref == "project://training/input.json"
    assert result.destination_ref == "provider-staging"
    assert result.input_digest is None
    assert "secret" not in result.canonical_json()


def test_engine_module_outside_pinned_root_is_bootstrap_unavailable(
    monkeypatch, tmp_path: Path,
) -> None:
    class ForeignModule:
        __file__ = str(tmp_path / "foreign" / "training_input.py")

    monkeypatch.setitem(
        cli.sys.modules, "synaptic_tuner.api.v1.training_input", ForeignModule()
    )
    result = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path / "project"), engine_root=ENGINE
    )
    assert result.error_code is TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE
    assert result.provider_ref == "modal"
    assert result.config_ref == "project://training/input.json"
    assert result.destination_ref == "provider-staging"
    assert result.input_digest is None


def test_docker_is_unavailable_only_after_complete_ingress(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")
    result = dispatch_validated_training_run_v1(ingress)
    assert result.status is TrainingRunCommandStatusV1.UNAVAILABLE
    assert result.error_code is TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE
    assert result.input_digest == ingress.input_digest


def test_modal_production_is_unavailable_and_has_no_submission_boundary(
    tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    unavailable = dispatch_validated_training_run_v1(ingress)
    assert unavailable.error_code is TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE
    assert tuple(item.value for item in TrainingRunCommandStatusV1) == (
        "rejected", "unavailable",
    )
    with pytest.raises(TypeError):
        dispatch_validated_training_run_v1(ingress, modal_boundary=lambda _: None)  # type: ignore[call-arg]


def test_emit_is_one_canonical_line_with_exact_exit(capsys, tmp_path: Path) -> None:
    result = dispatch_validated_training_run_v1(_ingress(tmp_path, "docker"))
    assert emit_training_run_result_v1(result) == 4
    output = capsys.readouterr().out
    assert output == result.canonical_json() + "\n"
    assert json.loads(output) == result.to_dict()


def test_emitter_reconstructs_exact_result_before_output(capsys) -> None:
    result = cli._failure(TrainingRunCommandCodeV1.COMMAND_INVALID)
    object.__setattr__(result, "status", TrainingRunCommandStatusV1.UNAVAILABLE)
    assert emit_training_run_result_v1(result) == 4
    document = json.loads(capsys.readouterr().out)
    assert document["error_code"] == "INTERNAL_FAILURE"


_RESULT_SHAPES = {
    TrainingRunCommandCodeV1.COMMAND_INVALID: {(False, False, False, False)},
    TrainingRunCommandCodeV1.PROVIDER_INVALID: {(False, False, False, False)},
    TrainingRunCommandCodeV1.DESTINATION_INVALID: {(True, False, False, False)},
    TrainingRunCommandCodeV1.CONFIG_REF_INVALID: {(True, False, True, False)},
    TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE: {(True, True, True, False)},
    TrainingRunCommandCodeV1.INPUT_INVALID: {(True, True, True, False)},
    TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE: {
        (True, True, True, False), (True, True, True, True),
    },
    TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV1.INTERNAL_FAILURE: {(False, False, False, False)},
}


def _result_for_shape(
    code: TrainingRunCommandCodeV1, shape: tuple[bool, bool, bool, bool],
) -> TrainingRunCommandResultV1:
    unavailable = code in {
        TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE,
        TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE,
        TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE,
        TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE,
        TrainingRunCommandCodeV1.INTERNAL_FAILURE,
    }
    values = ("modal", "project://training/input.json", "provider-staging", "a" * 64)
    selected = tuple(value if present else None for value, present in zip(values, shape))
    return TrainingRunCommandResultV1(
        "synaptic-training-run-command-result/v1",
        TrainingRunCommandStatusV1.UNAVAILABLE if unavailable
        else TrainingRunCommandStatusV1.REJECTED,
        *selected,
        code,
    )


def test_result_code_field_matrix_is_exact_for_every_presence_pattern() -> None:
    all_shapes = tuple(itertools.product((False, True), repeat=4))
    for code, allowed in _RESULT_SHAPES.items():
        for shape in all_shapes:
            if shape in allowed:
                result = _result_for_shape(code, shape)
                assert result.error_code is code
                assert tuple(
                    value is not None for value in (
                        result.provider_ref, result.config_ref,
                        result.destination_ref, result.input_digest,
                    )
                ) == shape
            else:
                with pytest.raises(ValueError):
                    _result_for_shape(code, shape)


def test_ingress_constructor_is_unavailable_and_unenrolled_copies_fail_closed(
    tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    with pytest.raises(TypeError, match="factory-issued"):
        TrainingRunIngressV1(
            ingress.provider_ref, ingress.config_ref, ingress.destination_ref,
            ingress.training_input, ingress.input_digest, ingress.source_sha256,
            ingress.contract_identity_digest, ingress.envelope_digest,
        )
    copied = object.__new__(TrainingRunIngressV1)
    for field in dataclasses.fields(TrainingRunIngressV1):
        object.__setattr__(copied, field.name, getattr(ingress, field.name))
    assert copied == ingress
    rejected = dispatch_validated_training_run_v1(copied)
    assert rejected.error_code is TrainingRunCommandCodeV1.INTERNAL_FAILURE
    assert rejected.provider_ref is rejected.config_ref is None
    assert rejected.destination_ref is rejected.input_digest is None


def test_dispatch_rejects_forged_or_mutated_training_input(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path)
    forged = object.__new__(TrainingRunIngressV1)
    for field in dataclasses.fields(TrainingRunIngressV1):
        object.__setattr__(forged, field.name, getattr(ingress, field.name))
    object.__setattr__(forged, "training_input", object())
    assert forged.envelope_digest == forged.recomputed_envelope_digest()
    assert (
        dispatch_validated_training_run_v1(forged).error_code
        is TrainingRunCommandCodeV1.INTERNAL_FAILURE
    )
    object.__setattr__(ingress, "training_input", object())
    assert (
        dispatch_validated_training_run_v1(ingress).error_code
        is TrainingRunCommandCodeV1.INTERNAL_FAILURE
    )


def test_concurrent_dispatch_authentication_converges(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = tuple(
            pool.map(lambda _index: dispatch_validated_training_run_v1(ingress), range(128))
        )
    assert all(
        result.error_code is TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE
        and result.input_digest == ingress.input_digest
        for result in results
    )
