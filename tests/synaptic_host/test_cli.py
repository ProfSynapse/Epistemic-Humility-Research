from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import synaptic_host.cli as cli
from synaptic_host.cli import (
    TrainingRunCommandCodeV2,
    TrainingRunCommandResultV2,
    TrainingRunCommandStatusV2,
    TrainingRunIngressV1,
    dispatch_validated_training_run_v1,
    emit_training_run_result_v2,
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
    assert type(result) is TrainingRunCommandResultV2
    assert result.code is TrainingRunCommandCodeV2.COMMAND_INVALID
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
    assert result.code is TrainingRunCommandCodeV2.DESTINATION_INVALID
    assert result.provider_ref == "modal"
    assert result.destination_ref is result.config_ref is result.input_digest is None


def test_unknown_provider_is_closed() -> None:
    result = prepare_training_run_ingress_v1(
        _argv(provider="huggingface"), project_root=ROOT, engine_root=ENGINE
    )
    assert result.code is TrainingRunCommandCodeV2.PROVIDER_INVALID
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
    assert result.code is TrainingRunCommandCodeV2.CONFIG_REF_INVALID
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
    assert missing.code is TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE
    oversize = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path / "large", b"x" * 65537), engine_root=ENGINE
    )
    assert oversize.code is TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE
    invalid = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path / "utf8", b"\xff"), engine_root=ENGINE
    )
    assert invalid.code is TrainingRunCommandCodeV2.INPUT_INVALID


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
    assert result.code is TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE


def test_invalid_training_document_is_closed_and_adjacent(tmp_path: Path) -> None:
    result = prepare_training_run_ingress_v1(
        _argv(), project_root=_project(tmp_path, b'{"secret":"not echoed"}'),
        engine_root=ENGINE,
    )
    assert result.code is TrainingRunCommandCodeV2.INPUT_INVALID
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
    assert result.code is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
    assert result.provider_ref == "modal"
    assert result.config_ref == "project://training/input.json"
    assert result.destination_ref == "provider-staging"
    assert result.input_digest is None


def test_docker_is_unavailable_only_after_complete_ingress(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")
    result = dispatch_validated_training_run_v1(ingress)
    assert result.status is TrainingRunCommandStatusV2.UNAVAILABLE
    assert result.code is TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE
    assert result.input_digest == ingress.input_digest


def test_modal_requires_credentials_before_composition(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    unavailable = dispatch_validated_training_run_v1(ingress)
    assert unavailable.code is TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE
    monkeypatch.setenv("MODAL_TOKEN_ID", "id-value")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "secret-value")
    unavailable = dispatch_validated_training_run_v1(ingress)
    assert unavailable.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
    assert tuple(item.value for item in TrainingRunCommandStatusV2) == (
        "rejected", "unavailable", "submitted", "reconcile_required",
    )
    with pytest.raises(TypeError):
        dispatch_validated_training_run_v1(ingress, modal_boundary=lambda _: None)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("token_id", "token_secret"),
    [
        (None, None), ("id", None), (None, "secret"), ("", "secret"),
        ("id", ""), ("id\n", "secret"), ("id", "secret\x7f"),
        ("id\u0085", "secret"),
        ("i" * 4097, "secret"), ("id", "s" * 4097),
    ],
)
def test_modal_credentials_are_exact_bounded_all_or_nothing(
    monkeypatch, tmp_path: Path, token_id: str | None, token_secret: str | None,
) -> None:
    ingress = _ingress(tmp_path)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    if token_id is not None:
        monkeypatch.setenv("MODAL_TOKEN_ID", token_id)
    if token_secret is not None:
        monkeypatch.setenv("MODAL_TOKEN_SECRET", token_secret)
    result = dispatch_validated_training_run_v1(ingress)
    assert result.code is TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE
    if token_id:
        assert token_id not in result.to_dict().values()
    if token_secret:
        assert token_secret not in result.to_dict().values()


def test_docker_dispatch_does_not_read_modal_credentials(monkeypatch, tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")

    class ForbiddenEnvironment(dict):
        def get(self, name, default=None):
            if name in {"MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"}:
                pytest.fail("Docker dispatch read ambient credentials")
            return super().get(name, default)

    monkeypatch.setattr(cli.os, "environ", ForbiddenEnvironment(cli.os.environ))
    assert (
        dispatch_validated_training_run_v1(ingress).code
        is TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE
    )


def test_modal_credential_string_subclasses_are_rejected(monkeypatch, tmp_path: Path) -> None:
    class String(str):
        pass

    ingress = _ingress(tmp_path)
    environment = dict(cli.os.environ)
    environment["MODAL_TOKEN_ID"] = String("subclass-id")
    environment["MODAL_TOKEN_SECRET"] = "secret"
    monkeypatch.setattr(cli.os, "environ", environment)
    assert (
        dispatch_validated_training_run_v1(ingress).code
        is TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE
    )


def test_emit_is_one_canonical_line_with_exact_exit(capsys, tmp_path: Path) -> None:
    result = dispatch_validated_training_run_v1(_ingress(tmp_path, "docker"))
    assert emit_training_run_result_v2(result) == 4
    output = capsys.readouterr().out
    assert output == result.canonical_json() + "\n"
    assert json.loads(output) == result.to_dict()


def test_emitter_has_exact_submitted_and_reconcile_exit_codes(capsys) -> None:
    submitted = _result_for_shape(
        TrainingRunCommandCodeV2.SUBMITTED, (True, True, True, True),
        (True, True, True, True, True, True),
    )
    assert emit_training_run_result_v2(submitted) == 0
    assert capsys.readouterr().out == submitted.canonical_json() + "\n"
    reconcile = _result_for_shape(
        TrainingRunCommandCodeV2.RECONCILE_REQUIRED,
        (True, True, True, True), (True, True, True, True, False, False),
    )
    assert emit_training_run_result_v2(reconcile) == 8
    assert capsys.readouterr().out == reconcile.canonical_json() + "\n"


def test_emitter_reconstructs_exact_result_before_output(capsys) -> None:
    result = cli._failure(TrainingRunCommandCodeV2.COMMAND_INVALID)
    object.__setattr__(result, "status", TrainingRunCommandStatusV2.UNAVAILABLE)
    assert emit_training_run_result_v2(result) == 4
    document = json.loads(capsys.readouterr().out)
    assert document["code"] == "INTERNAL_FAILURE"


_CATEGORY_C_VALUES = (
    "\u0085",  # Cc, assigned control
    "\u202e",  # Cf, assigned format control
    "\ud800",  # Cs, surrogate
    "\ue000",  # Co, private use
    "\u0378",  # Cn, deliberately unassigned
)


@pytest.mark.parametrize(
    "field_name",
    (
        "provider_ref", "config_ref", "destination_ref", "project_ref",
        "run_id", "effect_id", "provider_job_ref", "submitted_at",
    ),
)
@pytest.mark.parametrize("hostile", _CATEGORY_C_VALUES)
def test_result_rejects_every_unicode_category_c_reference(
    field_name: str, hostile: str,
) -> None:
    assert unicodedata.category(hostile).startswith("C")
    valid = _result_for_shape(
        TrainingRunCommandCodeV2.SUBMITTED, (True, True, True, True),
        (True, True, True, True, True, True),
    )
    with pytest.raises(ValueError, match="references"):
        dataclasses.replace(valid, **{field_name: "valid" + hostile})


@pytest.mark.parametrize("field_name", ("provider_ref", "submitted_at"))
@pytest.mark.parametrize("hostile", ("\u0085", "\u202e", "\ue000"))
def test_emitter_never_serializes_mutated_category_c_references(
    capsys, field_name: str, hostile: str,
) -> None:
    result = _result_for_shape(
        TrainingRunCommandCodeV2.SUBMITTED, (True, True, True, True),
        (True, True, True, True, True, True),
    )
    object.__setattr__(result, field_name, "secret" + hostile)
    assert emit_training_run_result_v2(result) == 4
    output = capsys.readouterr().out
    assert hostile not in output
    assert "secret" not in output
    assert json.loads(output)["code"] == "INTERNAL_FAILURE"


_RESULT_SHAPES = {
    TrainingRunCommandCodeV2.COMMAND_INVALID: {(False, False, False, False)},
    TrainingRunCommandCodeV2.PROVIDER_INVALID: {(False, False, False, False)},
    TrainingRunCommandCodeV2.DESTINATION_INVALID: {(True, False, False, False)},
    TrainingRunCommandCodeV2.CONFIG_REF_INVALID: {(True, False, True, False)},
    TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE: {(True, True, True, False)},
    TrainingRunCommandCodeV2.INPUT_INVALID: {(True, True, True, False)},
    TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE: {
        (True, True, True, False), (True, True, True, True),
    },
    TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.PREFLIGHT_REJECTED: {(True, True, True, True)},
    TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.START_UNAVAILABLE: {(True, True, True, True)},
    TrainingRunCommandCodeV2.SUBMITTED: {(True, True, True, True)},
    TrainingRunCommandCodeV2.RECONCILE_REQUIRED: {(True, True, True, True)},
    TrainingRunCommandCodeV2.INTERNAL_FAILURE: {(False, False, False, False)},
}

_RESULT_STATUS = {
    TrainingRunCommandCodeV2.COMMAND_INVALID: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.PROVIDER_INVALID: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.CONFIG_REF_INVALID: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.INPUT_INVALID: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.DESTINATION_INVALID: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.PREFLIGHT_REJECTED: TrainingRunCommandStatusV2.REJECTED,
    TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.START_UNAVAILABLE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.INTERNAL_FAILURE: TrainingRunCommandStatusV2.UNAVAILABLE,
    TrainingRunCommandCodeV2.SUBMITTED: TrainingRunCommandStatusV2.SUBMITTED,
    TrainingRunCommandCodeV2.RECONCILE_REQUIRED:
        TrainingRunCommandStatusV2.RECONCILE_REQUIRED,
}


def _result_for_shape(
    code: TrainingRunCommandCodeV2, shape: tuple[bool, bool, bool, bool],
    operation: tuple[bool, bool, bool, bool, bool, bool] | None = None,
) -> TrainingRunCommandResultV2:
    values = ("modal", "project://training/input.json", "provider-staging", "a" * 64)
    selected = tuple(value if present else None for value, present in zip(values, shape))
    operation = operation or (False, False, False, False, False, False)
    operation_values = (
        "project", "run", "b" * 64, "effect", "provider-job",
        "2026-08-29T00:00:00Z",
    )
    selected_operation = tuple(
        value if present else None
        for value, present in zip(operation_values, operation)
    )
    return TrainingRunCommandResultV2(
        "synaptic-training-run-command-result/v2",
        _RESULT_STATUS[code], code, *selected, *selected_operation,
    )


def test_result_code_field_matrix_is_exact_for_every_presence_pattern() -> None:
    all_shapes = tuple(itertools.product((False, True), repeat=4))
    for code, allowed in _RESULT_SHAPES.items():
        for shape in all_shapes:
            operation = (
                (True, True, True, True, True, True)
                if code is TrainingRunCommandCodeV2.SUBMITTED
                else (True, True, True, True, False, False)
                if code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
                else (False, False, False, False, False, False)
            )
            if shape in allowed:
                result = _result_for_shape(code, shape, operation)
                assert result.code is code
                assert tuple(
                    value is not None for value in (
                        result.provider_ref, result.config_ref,
                        result.destination_ref, result.input_digest,
                    )
                ) == shape
            else:
                with pytest.raises(ValueError):
                    _result_for_shape(code, shape, operation)


def test_result_operation_matrix_rejects_every_missing_or_extra_field() -> None:
    full_prefix = (True, True, True, True)
    empty = (False, False, False, False, False, False)
    submitted = (True, True, True, True, True, True)
    reconcile_without_job = (True, True, True, True, False, False)
    reconcile_with_job = (True, True, True, True, True, False)
    for code in TrainingRunCommandCodeV2:
        allowed = (
            {submitted} if code is TrainingRunCommandCodeV2.SUBMITTED
            else {reconcile_without_job, reconcile_with_job}
            if code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
            else {empty}
        )
        prefix = next(iter(_RESULT_SHAPES[code]))
        for operation in itertools.product((False, True), repeat=6):
            if operation in allowed:
                assert _result_for_shape(code, prefix, operation).code is code
            else:
                with pytest.raises(ValueError):
                    _result_for_shape(code, prefix, operation)


def test_v1_result_symbols_are_removed() -> None:
    assert not hasattr(cli, "TrainingRunCommandCodeV1")
    assert not hasattr(cli, "TrainingRunCommandStatusV1")
    assert not hasattr(cli, "TrainingRunCommandResultV1")
    assert not hasattr(cli, "emit_training_run_result_v1")
    assert not hasattr(cli, "bootstrap_unavailable_result_v1")
    assert cli.emit_training_run_result_v2 is emit_training_run_result_v2
    assert callable(cli.bootstrap_unavailable_result_v2)


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
    assert rejected.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
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
        dispatch_validated_training_run_v1(forged).code
        is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    )
    object.__setattr__(ingress, "training_input", object())
    assert (
        dispatch_validated_training_run_v1(ingress).code
        is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    )


def test_concurrent_dispatch_authentication_converges(tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = tuple(
            pool.map(lambda _index: dispatch_validated_training_run_v1(ingress), range(128))
        )
    assert all(
        result.code is TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE
        and result.input_digest == ingress.input_digest
        for result in results
    )
