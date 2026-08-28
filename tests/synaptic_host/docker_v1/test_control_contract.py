from dataclasses import replace
from enum import Enum
from hashlib import sha256
import pickle
import copy
from concurrent.futures import ThreadPoolExecutor
import traceback

import pytest

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    DockerAbsenceContentV1,
    DockerLookupPurposeV1,
    DockerImageV1, DockerLabelsV1, DockerRuntimeV1, DockerWorkloadV1,
)

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerAdmissionDispositionV1,
    DockerAdmissionResultV1,
    DockerCASDispositionV1,
    DockerCASResultV1,
    DockerControlContractErrorV1,
    DockerControlContractCodeV1,
    DockerControlIntentV1,
    DockerControlOperationV1,
    DockerCreatePathBindingV1,
    DockerCreateSpecificationV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
    docker_operation_id_v1,
    authenticate_absence_v1,
    authenticate_control_intent_v1,
    authenticate_create_path_binding_v1,
    authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
)
from synaptic_host.docker_v1.control_private import (
    DockerPrivateCreateInvocationFactoryV1,
    DockerPrivateCreateInvocationV1,
    DockerPrivateStartInvocationV1,
    DockerPrivateWorkloadEnvironmentResolutionV1,
)
from synaptic_host.docker_v1.model import (
    DockerCLICommandV1, DockerCLIVerbV1, DockerCLIResultV1,
    DockerCLIOutcomeV1,
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
    DockerWindowsPathV1,
)
from synaptic_host.docker_v1.control_model import (
    OWNED_LABEL_NAMES_V1, OWNED_LABEL_PREFIX_V1,
    DockerCreateExecutionProjectionV1, DockerCreateExecutionResultV1,
    DockerStartExecutionResultV1,
    docker_create_execution_request_digest_v1,
    docker_start_execution_request_digest_v1,
)


SHA = "a" * 64


def _request(ref, purpose, path):
    return DockerWSLPathRequestV1.build(
        mapping_ref=ref, expected_mapping_digest=SHA,
        expected_distro="Ubuntu-22.04", purpose=purpose, posix_path=path,
    )


def _path_binding():
    return DockerCreatePathBindingV1.build(
        labels_digest=SHA, source_ref="source", artifact_ref="artifact",
        mount_resolution_digest=SHA,
        source_storage_mapping_proof_digest=SHA,
        artifact_storage_mapping_proof_digest=SHA,
        source_mapping_pair_proof_digest="b" * 64,
        artifact_mapping_pair_proof_digest="c" * 64,
        source_request=_request("source-map", DockerWSLPathPurposeV1.SOURCE_READ, "/source"),
        artifact_request=_request("artifact-map", DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/artifacts"),
        source_read_only=True,
    )


def test_path_binding_exact_purposes_distinct_refs_and_recursive_mutation():
    binding = _path_binding()
    assert binding.source_request.purpose is DockerWSLPathPurposeV1.SOURCE_READ
    assert binding.canonical_without_digest()["source_mapping_pair_proof_digest"] == "b" * 64
    assert binding.canonical_without_digest()["artifact_mapping_pair_proof_digest"] == "c" * 64
    with pytest.raises(DockerControlContractErrorV1):
        replace(binding, source_mapping_pair_proof_digest="d" * 64)
    values = {
        name: getattr(binding, name)
        for name in binding.__dataclass_fields__
        if name not in {
            "binding_digest", "source_mapping_pair_proof_digest",
            "artifact_mapping_pair_proof_digest",
        }
    }
    with pytest.raises(KeyError):
        DockerCreatePathBindingV1.build(**values)
    with pytest.raises(DockerControlContractErrorV1):
        replace(binding, source_ref="artifact")
    object.__setattr__(binding.source_request, "purpose", DockerWSLPathPurposeV1.ARTIFACT_WRITE)
    with pytest.raises(DockerControlContractErrorV1):
        replace(binding)


def test_environment_exact_set_sorting_empty_and_redaction():
    entries = (DockerWorkloadEnvironmentEntryV1.build("A", "secret-a"),
               DockerWorkloadEnvironmentEntryV1.build("B", ""))
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("A", "B"), entries)
    assert "secret-a" not in repr(binding)
    assert DockerWorkloadEnvironmentBindingV1.build(SHA, (), ()).requested_keys == ()
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("A",), entries)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("B", "A"), entries)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("A", "A"), (entries[0], entries[0]))


class EnvAuthority:
    authority_ref = "authority"
    key_ref = "key"
    def authenticate(self, value):
        return AuthenticatedDockerWorkloadEnvironmentBindingV1(
            DockerWorkloadEnvironmentBindingV1(
                value.content.workload_digest, tuple(value.content.requested_keys),
                tuple(DockerWorkloadEnvironmentEntryV1(
                    item.key, item.key_digest, item.value_digest, item.entry_digest
                ) for item in value.content.supplied_entries),
                value.content.binding_digest,
            ), value.authority_ref, value.key_ref, value.tag,
        )


def test_private_environment_is_opaque_unpickleable_and_rehashes():
    entry = DockerWorkloadEnvironmentEntryV1.build("TOKEN", "raw-secret")
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("TOKEN",), (entry,))
    authenticated = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        binding, "authority", "key", SHA
    )
    private = DockerPrivateWorkloadEnvironmentResolutionV1(
        authenticated, (("TOKEN", "raw-secret"),)
    )
    assert "raw-secret" not in repr(private) and "raw-secret" not in str(private)
    assert private.materialize_for_cli(EnvAuthority()) == (("TOKEN", "raw-secret"),)
    with pytest.raises(DockerControlContractErrorV1):
        pickle.dumps(private)
    object.__setattr__(entry, "value_digest", "b" * 64)
    with pytest.raises(DockerControlContractErrorV1) as caught:
        private.materialize_for_cli(EnvAuthority())
    assert "raw-secret" not in "".join(traceback.format_exception(caught.value))


class CreateRunnerSpy:
    def __init__(self, error=False):
        self.calls = []
        self.error = error

    def create_container(self, command, name):
        self.calls.append((command.command_digest, name))
        if self.error:
            raise RuntimeError("raw-secret-runner")
        return _sanitized_create_result(command, name)


def _sanitized_create_result(command, name, ref="1" * 64):
    stdout = ref.encode()
    empty = sha256(b"").hexdigest()
    body = {
        "command_digest": command.command_digest, "exit_code": 0,
        "outcome": "SUCCESS", "policy_digest": SHA,
        "schema_version": "synaptic-host-docker-cli-result/v1",
        "stderr_digest": empty, "stderr_size": 0,
        "stdout_digest": sha256(stdout).hexdigest(), "stdout_size": 64,
    }
    evidence = DockerCLIResultV1(
        command.command_digest, SHA, DockerCLIOutcomeV1.SUCCESS, 0,
        64, sha256(stdout).hexdigest(), 0, empty, digest_v1(body),
    )
    request = docker_create_execution_request_digest_v1(
        name, command.command_digest
    )
    projection = DockerCreateExecutionProjectionV1.build(
        ref, request, command.command_digest
    )
    return DockerCreateExecutionResultV1.build(
        name, request, command.command_digest, evidence, projection
    )


def _private_invocation():
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.CREATE,
        ("--name", "synaptic-job", "--env", "TOKEN=raw-secret"),
    )
    return DockerPrivateCreateInvocationV1(command, "synaptic-job")


def test_private_create_invocation_is_redacted_uncopyable_and_one_shot():
    invocation = _private_invocation()
    assert "raw-secret" not in repr(invocation)
    assert "raw-secret" not in str(invocation)
    for operation in (
        lambda: pickle.dumps(invocation), lambda: copy.copy(invocation),
        lambda: copy.deepcopy(invocation),
    ):
        with pytest.raises(DockerControlContractErrorV1):
            operation()
    runner = CreateRunnerSpy()
    assert invocation.execute_once(runner).target == "synaptic-job"
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert len(runner.calls) == 1


@pytest.mark.parametrize("error", (False, True))
def test_private_create_invocation_concurrently_enters_runner_at_most_once(error):
    invocation = _private_invocation()
    runner = CreateRunnerSpy(error=error)
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(
            lambda _index: _capture_invocation(invocation, runner), range(8)
        ))
    assert len(runner.calls) == 1
    assert sum(type(outcome) is DockerCreateExecutionResultV1 for outcome in outcomes) <= 1
    assert "raw-secret" not in repr(outcomes)


def _capture_invocation(invocation, runner):
    try:
        return invocation.execute_once(runner)
    except DockerControlContractErrorV1 as error:
        return error.code.value


@pytest.mark.parametrize("returned", (object(), {"result": "forged"}))
def test_private_create_invocation_rejects_untyped_return_and_stays_consumed(returned):
    class ReturningRunner:
        def __init__(self):
            self.calls = 0
        def create_container(self, _command, _name):
            self.calls += 1
            return returned

    invocation = _private_invocation()
    runner = ReturningRunner()
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert runner.calls == 1


def test_private_create_return_owns_runner_result_snapshots():
    invocation = _private_invocation()
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.CREATE,
        ("--name", "synaptic-job", "--env", "TOKEN=raw-secret"),
    )
    runner_result = _sanitized_create_result(command, "synaptic-job")

    class ReturningRunner:
        def create_container(self, _command, _name):
            return runner_result

    returned = invocation.execute_once(ReturningRunner())
    assert returned is not runner_result
    assert returned.evidence is not runner_result.evidence
    assert returned.projection is not runner_result.projection
    evidence_digest = returned.evidence.result_digest
    projection_digest = returned.projection.projection_digest
    container_ref = returned.projection.container_ref
    object.__setattr__(runner_result.evidence, "result_digest", "4" * 64)
    object.__setattr__(runner_result.projection, "container_ref", "4" * 64)
    assert returned.evidence.result_digest == evidence_digest
    assert returned.projection.projection_digest == projection_digest
    assert returned.projection.container_ref == container_ref
    DockerCreateExecutionResultV1(
        returned.result_kind, returned.target, returned.request_digest,
        returned.command_digest, returned.evidence, returned.projection,
        returned.result_digest,
    )


def _private_start_invocation(ref="2" * 64):
    return DockerPrivateStartInvocationV1(
        DockerCLICommandV1.build(DockerCLIVerbV1.START, (ref,)), ref
    )


def _sanitized_start_result(command, ref):
    empty = sha256(b"").hexdigest()
    stdout = (ref + "\n").encode()
    body = {
        "command_digest": command.command_digest, "exit_code": 0,
        "outcome": "SUCCESS", "policy_digest": SHA,
        "schema_version": "synaptic-host-docker-cli-result/v1",
        "stderr_digest": empty, "stderr_size": 0,
        "stdout_digest": sha256(stdout).hexdigest(), "stdout_size": len(stdout),
    }
    evidence = DockerCLIResultV1(
        command.command_digest, SHA, DockerCLIOutcomeV1.SUCCESS, 0,
        len(stdout), sha256(stdout).hexdigest(), 0, empty, digest_v1(body),
    )
    request = docker_start_execution_request_digest_v1(
        ref, command.command_digest
    )
    return DockerStartExecutionResultV1.build(ref, request, command, evidence)


class StartRunnerSpy:
    def __init__(self, *, error=False, returned=None):
        self.calls = []
        self.error = error
        self.returned = returned

    def start_container(self, command, ref):
        self.calls.append((command.command_digest, ref))
        if self.error:
            raise RuntimeError("raw-secret-start-error")
        if self.returned is not None:
            return self.returned
        return _sanitized_start_result(command, ref)


def test_private_start_invocation_redacted_uncopyable_and_one_shot():
    invocation = _private_start_invocation()
    assert "2" * 64 not in repr(invocation)
    assert "2" * 64 not in str(invocation)
    for operation in (
        lambda: pickle.dumps(invocation), lambda: copy.copy(invocation),
        lambda: copy.deepcopy(invocation),
    ):
        with pytest.raises(DockerControlContractErrorV1):
            operation()
    runner = StartRunnerSpy()
    assert invocation.execute_once(runner).target == "2" * 64
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert len(runner.calls) == 1


@pytest.mark.parametrize("error", (False, True))
def test_private_start_invocation_concurrent_consumed_before_call(error):
    invocation = _private_start_invocation()
    runner = StartRunnerSpy(error=error)
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(
            lambda _index: _capture_invocation(invocation, runner), range(8)
        ))
    assert len(runner.calls) == 1
    assert sum(type(item) is DockerStartExecutionResultV1 for item in outcomes) <= 1
    assert "raw-secret-start-error" not in repr(outcomes)


@pytest.mark.parametrize("returned", (object(), {"forged": True}))
def test_private_start_invocation_rejects_untyped_return_and_stays_consumed(returned):
    invocation = _private_start_invocation()
    runner = StartRunnerSpy(returned=returned)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert len(runner.calls) == 1


def test_private_start_invocation_rejects_cross_target_return():
    invocation = _private_start_invocation("2" * 64)
    other_command = DockerCLICommandV1.build(
        DockerCLIVerbV1.START, ("3" * 64,)
    )
    runner = StartRunnerSpy(
        returned=_sanitized_start_result(other_command, "3" * 64)
    )
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert len(runner.calls) == 1


@pytest.mark.parametrize("ref", ("2" * 63, "2" * 65, "G" * 64))
def test_private_start_invocation_rejects_invalid_target(ref):
    command = DockerCLICommandV1.build(DockerCLIVerbV1.START, (ref,))
    with pytest.raises(DockerControlContractErrorV1):
        DockerPrivateStartInvocationV1(command, ref)


def test_private_start_invocation_rejects_nested_mutated_result_and_subclass():
    ref = "2" * 64
    command = DockerCLICommandV1.build(DockerCLIVerbV1.START, (ref,))
    result = _sanitized_start_result(command, ref)
    object.__setattr__(result.evidence, "stdout_size", 999)
    invocation = _private_start_invocation(ref)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(StartRunnerSpy(returned=result))

    class Forged(DockerStartExecutionResultV1):
        pass

    valid = _sanitized_start_result(command, ref)
    forged = Forged(
        valid.result_kind, valid.target, valid.request_digest, valid.command,
        valid.command_digest, valid.evidence, valid.result_digest,
    )
    invocation = _private_start_invocation(ref)
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(StartRunnerSpy(returned=forged))


def test_private_start_return_owns_runner_result_snapshots():
    ref = "2" * 64
    command = DockerCLICommandV1.build(DockerCLIVerbV1.START, (ref,))
    runner_result = _sanitized_start_result(command, ref)
    invocation = _private_start_invocation(ref)
    returned = invocation.execute_once(StartRunnerSpy(returned=runner_result))
    assert returned is not runner_result
    assert returned.command is not runner_result.command
    assert returned.evidence is not runner_result.evidence
    command_digest = returned.command.command_digest
    evidence_digest = returned.evidence.result_digest
    object.__setattr__(runner_result.command, "command_digest", "3" * 64)
    object.__setattr__(runner_result.evidence, "result_digest", "3" * 64)
    assert returned.command.command_digest == command_digest
    assert returned.evidence.result_digest == evidence_digest
    DockerStartExecutionResultV1(
        returned.result_kind, returned.target, returned.request_digest,
        returned.command, returned.command_digest, returned.evidence,
        returned.result_digest,
    )


class HostileContractError(DockerControlContractErrorV1):
    pass


@pytest.mark.parametrize("invocation_kind", ("create", "start"))
@pytest.mark.parametrize("error_type", (DockerControlContractErrorV1, HostileContractError))
def test_private_invocations_normalize_hostile_contract_errors_outside_catch(
    invocation_kind, error_type,
):
    secret = "raw-dependency-contract-secret"

    class HostileRunner:
        def __init__(self):
            self.calls = 0

        def _raise(self):
            self.calls += 1
            error = error_type(DockerControlContractCodeV1.INVALID)
            error.args = (secret,)
            raise error from RuntimeError(secret)

        def create_container(self, _command, _name):
            return self._raise()

        def start_container(self, _command, _ref):
            return self._raise()

    invocation = (
        _private_invocation() if invocation_kind == "create"
        else _private_start_invocation()
    )
    runner = HostileRunner()
    with pytest.raises(DockerControlContractErrorV1) as caught:
        invocation.execute_once(runner)
    assert type(caught.value) is DockerControlContractErrorV1
    assert caught.value.code is DockerControlContractCodeV1.INVALID
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in "".join(traceback.format_exception(caught.value))
    with pytest.raises(DockerControlContractErrorV1):
        invocation.execute_once(runner)
    assert runner.calls == 1


def _factory_labels():
    return DockerLabelsV1(
        SHA, "docker", "profile", "account", "namespace", "project", "run",
        SHA, SHA, "effect", "submit", SHA, SHA,
    )


def _windows_path(purpose, posix):
    distro = "Ubuntu-22.04"
    unc = "\\\\wsl.localhost\\" + distro + posix.replace("/", "\\")
    body = {
        "distro": distro, "mapping_digest": SHA, "mapping_ref": "mapping",
        "posix_path": posix, "purpose": purpose.value,
        "schema_version": "synaptic-host-docker-windows-path/v1",
        "unc_path": unc,
    }
    return DockerWindowsPathV1(
        "mapping", SHA, purpose, distro, posix, unc, digest_v1(body)
    )


def _private_environment(pairs, workload_digest=SHA):
    pairs = tuple(pairs)
    entries = tuple(
        DockerWorkloadEnvironmentEntryV1.build(key, value)
        for key, value in pairs
    )
    binding = DockerWorkloadEnvironmentBindingV1.build(
        workload_digest, tuple(key for key, _ in pairs), entries
    )
    authenticated = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        binding, "authority", "key", SHA
    )
    return DockerPrivateWorkloadEnvironmentResolutionV1(authenticated, pairs)


class CaptureCreateRunner:
    def __init__(self):
        self.command = None

    def create_container(self, command, _name):
        self.command = command
        return _sanitized_create_result(command, _name)


def _factory_invocation(*, pairs=(("TOKEN", "raw-secret"),), arguments=("python", "train.py"),
                        source=None, artifact=None, workload_digest=SHA):
    keys = tuple(key for key, _ in pairs)
    workload = DockerWorkloadV1(tuple(arguments), keys, workload_digest)
    return DockerPrivateCreateInvocationFactoryV1().build(
        labels=_factory_labels(),
        image=DockerImageV1("ignored-ref", "sha256:" + "b" * 64),
        runtime=DockerRuntimeV1(2, 4096, 60), workload=workload,
        source_path=source or _windows_path(
            DockerWSLPathPurposeV1.SOURCE_READ, "/source"
        ),
        artifact_path=artifact or _windows_path(
            DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/artifacts"
        ),
        environment=_private_environment(pairs, workload_digest),
        environment_authority=EnvAuthority(),
    )


def test_private_factory_builds_exact_full_create_argv_in_frozen_order():
    labels = _factory_labels()
    invocation = _factory_invocation()
    runner = CaptureCreateRunner()
    result = invocation.execute_once(runner)
    arguments = runner.command.arguments
    assert arguments[:10] == (
        "--name", labels.container_name, "--pull", "never", "--network",
        "none", "--cpus", "2", "--memory", "4096",
    )
    label_tokens = arguments[10:40]
    assert label_tokens[::2] == ("--label",) * 15
    assert tuple(
        token.split("=", 1)[0]
        for token in label_tokens[1::2]
    ) == tuple(OWNED_LABEL_PREFIX_V1 + name for name in OWNED_LABEL_NAMES_V1)
    assert arguments[40:44] == (
        "--mount",
        r"type=bind,source=\\wsl.localhost\Ubuntu-22.04\source,destination=/source,readonly",
        "--mount",
        r"type=bind,source=\\wsl.localhost\Ubuntu-22.04\artifacts,destination=/artifacts",
    )
    assert arguments[44:] == (
        "--env", "TOKEN=raw-secret", "sha256:" + "b" * 64,
        "python", "train.py",
    )
    assert result.command_digest == runner.command.command_digest
    assert "raw-secret" not in repr(invocation)


def test_private_factory_maximum_env_and_workload_shape_is_within_cli_limit():
    pairs = tuple((f"K{i:02d}", "v") for i in range(64))
    arguments = tuple(f"arg{i}" for i in range(64))
    invocation = _factory_invocation(pairs=pairs, arguments=arguments)
    runner = CaptureCreateRunner()
    invocation.execute_once(runner)
    assert len(runner.command.arguments) == 237


@pytest.mark.parametrize("bad", (",", '"', "\n", "\x01", "e\u0301"))
def test_private_factory_rejects_hostile_unc_without_raw_traceback(bad):
    source = _windows_path(DockerWSLPathPurposeV1.SOURCE_READ, "/source")
    object.__setattr__(source, "unc_path", source.unc_path + bad + "raw-secret")
    with pytest.raises(DockerControlContractErrorV1) as caught:
        _factory_invocation(source=source)
    assert "raw-secret" not in str(caught.value)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize("which", ("source", "artifact"))
def test_private_factory_rejects_wrong_path_purpose(which):
    source = _windows_path(DockerWSLPathPurposeV1.SOURCE_READ, "/source")
    artifact = _windows_path(DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/artifacts")
    target = source if which == "source" else artifact
    object.__setattr__(target, "purpose", (
        DockerWSLPathPurposeV1.ARTIFACT_WRITE
        if which == "source" else DockerWSLPathPurposeV1.SOURCE_READ
    ))
    with pytest.raises(DockerControlContractErrorV1):
        _factory_invocation(source=source, artifact=artifact)


@pytest.mark.parametrize(
    "pairs",
    (
        (("B", "two"), ("A", "one")),
        (("A", "one"), ("A", "two")),
    ),
)
def test_private_factory_rejects_noncanonical_environment_sets(pairs):
    with pytest.raises((DockerControlContractErrorV1, ValueError)):
        _factory_invocation(pairs=pairs)


def test_private_binding_accessor_is_reconstructed_and_rejects_mutation():
    private = _private_environment((("TOKEN", "raw-secret"),))
    snapshot = private.authenticated_binding_snapshot(EnvAuthority())
    assert snapshot.content.requested_keys == ("TOKEN",)
    assert "raw-secret" not in repr(snapshot)
    object.__setattr__(snapshot.content.supplied_entries[0], "value_digest", "b" * 64)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1(
            snapshot.content.workload_digest, snapshot.content.requested_keys,
            snapshot.content.supplied_entries, snapshot.content.binding_digest,
        )


def _spec(**changes):
    values = dict(
        labels_digest=SHA, owned_labels_projection_digest=SHA,
        container_name="synaptic-job", image_digest="sha256:" + "b" * 64,
        runtime_digest=SHA, workload_digest=SHA, argument_count=1,
        arguments_digest=SHA, environment_binding_proof_digest=SHA,
        mount_resolution_digest=SHA, path_binding_proof_digest=SHA,
        source_windows_path_digest=SHA, source_unc_digest=SHA,
        source_destination_digest=sha256(b"/source").hexdigest(),
        source_read_only=True, artifact_windows_path_digest=SHA,
        artifact_unc_digest=SHA,
        artifact_destination_digest=sha256(b"/artifacts").hexdigest(),
        artifact_read_write=True, network_mode="none",
        nano_cpus=1_000_000_000, memory_bytes=1,
    )
    values.update(changes)
    return DockerCreateSpecificationV1.build(**values)


@pytest.mark.parametrize("changes", (
    {"argument_count": 0}, {"argument_count": 65},
    {"nano_cpus": 999_999_999}, {"nano_cpus": 1_000_000_001},
    {"nano_cpus": 257_000_000_000}, {"memory_bytes": 0},
    {"memory_bytes": 2**50 + 1}, {"network_mode": "bridge"},
))
def test_create_spec_engine_bounds_and_fixed_destinations(changes):
    with pytest.raises(DockerControlContractErrorV1):
        _spec(**changes)
    valid = _spec(argument_count=64, nano_cpus=256_000_000_000, memory_bytes=2**50)
    assert valid.source_destination_digest == sha256(b"/source").hexdigest()


def _intent(operation=DockerControlOperationV1.CREATE, **changes):
    effect = "effect"
    values = dict(
        operation_id=docker_operation_id_v1(operation, effect), operation=operation,
        effect_id=effect, engine_command_digest=SHA, labels_digest=SHA,
        container_name="synaptic-job", create_specification_digest=SHA,
        cli_command_digest=SHA, container_ref=None,
        verified_create_record_digest=None,
    )
    if operation is DockerControlOperationV1.START:
        values.update(container_ref="c" * 64, verified_create_record_digest=SHA)
    values.update(changes)
    return DockerControlIntentV1.build(**values)


def _auth_record(phase=DockerMutationPhaseV1.ADMITTED, previous=SHA):
    intent = _intent()
    values = dict(
        operation_id=intent.operation_id, operation=intent.operation,
        effect_id=intent.effect_id,
        control_intent_proof_digest=SHA, phase=phase,
        revision=1, attempt_count=0, previous_record_digest=None,
        container_ref=None, verification_result_digest=None,
    )
    if phase is DockerMutationPhaseV1.ATTEMPTED:
        values.update(revision=2, attempt_count=1, previous_record_digest=previous)
    if phase is DockerMutationPhaseV1.VERIFIED:
        values.update(revision=3, attempt_count=1, previous_record_digest=previous,
                      container_ref="c" * 64, verification_result_digest=SHA)
    record = DockerMutationRecordV1.build(**values)
    return AuthenticatedDockerMutationRecordV1(record, "authority", "key", SHA)


def test_intent_create_start_matrix_and_substitution():
    assert _intent().container_ref is None
    assert _intent(DockerControlOperationV1.START).container_ref is not None
    with pytest.raises(DockerControlContractErrorV1):
        _intent(container_ref="c" * 64)
    with pytest.raises(DockerControlContractErrorV1):
        _intent(DockerControlOperationV1.START, verified_create_record_digest=None)


def test_mutation_phase_matrix_and_downgrade():
    for phase in DockerMutationPhaseV1:
        assert _auth_record(phase).content.phase is phase
    verified = _auth_record(DockerMutationPhaseV1.VERIFIED).content
    with pytest.raises(DockerControlContractErrorV1):
        replace(verified, phase=DockerMutationPhaseV1.ADMITTED)


@pytest.mark.parametrize("disposition", tuple(DockerAdmissionDispositionV1))
def test_admission_result_matrix(disposition):
    candidate = _auth_record()
    request = DockerMutationAdmissionRequestV1.build(
        candidate.content.operation_id, candidate
    )
    required = disposition is not DockerAdmissionDispositionV1.INDETERMINATE
    if disposition is DockerAdmissionDispositionV1.CONFLICT:
        content = candidate.content
        conflicting = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest="b" * 64,
            phase=content.phase, revision=content.revision,
            attempt_count=content.attempt_count,
            previous_record_digest=content.previous_record_digest,
            container_ref=content.container_ref,
            verification_result_digest=content.verification_result_digest,
        )
        record = AuthenticatedDockerMutationRecordV1(
            conflicting, "authority", "key", SHA
        )
    else:
        record = candidate if required else None
    result = DockerAdmissionResultV1.build(request, disposition, record)
    assert (result.record is not None) is required
    with pytest.raises(DockerControlContractErrorV1):
        DockerAdmissionResultV1.build(
            request, disposition, None if required else candidate
        )


def test_cas_and_lookup_matrices_and_exact_operation():
    record = _auth_record()
    replacement = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, record.content.record_digest
    )
    request = DockerMutationCASRequestV1.build(
        record.content.operation_id, record, replacement
    )
    for disposition in (DockerCASDispositionV1.APPLIED, DockerCASDispositionV1.CURRENT):
        returned = replacement if disposition is DockerCASDispositionV1.APPLIED else record
        assert DockerCASResultV1.build(request, disposition, returned).record is returned
    assert DockerCASResultV1.build(request, DockerCASDispositionV1.INDETERMINATE, None).record is None
    found = DockerMutationLookupResultV1.build(
        record.content.operation_id, DockerMutationLookupDispositionV1.FOUND, record
    )
    assert found.record is record
    for disposition in (DockerMutationLookupDispositionV1.ABSENT,
                        DockerMutationLookupDispositionV1.INDETERMINATE):
        assert DockerMutationLookupResultV1.build(SHA, disposition, None).record is None
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationLookupResultV1.build(SHA, DockerMutationLookupDispositionV1.FOUND, record)


class EchoAuthority:
    def __init__(self, authority_ref="authority", key_ref="key"):
        self.authority_ref = authority_ref
        self.key_ref = key_ref
    def authenticate(self, value):
        return value


def test_alternate_signers_fail_for_every_authenticated_contract():
    path = AuthenticatedDockerCreatePathBindingV1(
        _path_binding(), "authority", "key", SHA
    )
    env_content = DockerWorkloadEnvironmentBindingV1.build(SHA, (), ())
    env = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        env_content, "authority", "key", SHA
    )
    intent = AuthenticatedDockerControlIntentV1(
        _intent(), "authority", "key", SHA
    )
    record = _auth_record()
    absence_content = DockerAbsenceContentV1(
        SHA, SHA, DockerLookupPurposeV1.OBSERVE, 1, SHA
    )
    absence = AuthenticatedDockerAbsenceV1(
        absence_content, "authority", "key", SHA
    )
    cases = (
        (authenticate_create_path_binding_v1, path),
        (authenticate_workload_environment_binding_v1, env),
        (authenticate_control_intent_v1, intent),
        (authenticate_mutation_record_v1, record),
        (authenticate_absence_v1, absence),
    )
    for authenticate, envelope in cases:
        assert authenticate(EchoAuthority(), envelope) == envelope
        with pytest.raises(DockerControlContractErrorV1):
            authenticate(EchoAuthority("alternate", "key"), envelope)


def test_private_alternate_signer_never_releases_raw_value():
    raw = "raw-secret-private-value"
    entry = DockerWorkloadEnvironmentEntryV1.build("TOKEN", raw)
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("TOKEN",), (entry,))
    envelope = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        binding, "authority", "key", SHA
    )
    private = DockerPrivateWorkloadEnvironmentResolutionV1(
        envelope, (("TOKEN", raw),)
    )
    with pytest.raises(DockerControlContractErrorV1) as caught:
        private.materialize_for_cli(EchoAuthority("alternate", "key"))
    assert raw not in "".join(traceback.format_exception(caught.value))


def test_environment_exact_64_and_utf8_token_boundaries():
    pairs = tuple(sorted((f"K{i}", "v") for i in range(64)))
    entries = tuple(DockerWorkloadEnvironmentEntryV1.build(*pair) for pair in pairs)
    binding = DockerWorkloadEnvironmentBindingV1.build(
        SHA, tuple(key for key, _ in pairs), entries
    )
    assert len(binding.supplied_entries) == 64
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(
            SHA, binding.requested_keys + ("Z",),
            entries + (DockerWorkloadEnvironmentEntryV1.build("Z", "v"),),
        )
    DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4094)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4095)
    DockerPrivateWorkloadEnvironmentResolutionV1(
        AuthenticatedDockerWorkloadEnvironmentBindingV1(
            DockerWorkloadEnvironmentBindingV1.build(
                SHA, ("K",),
                (DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4094),),
            ), "authority", "key", SHA,
        ), (("K", "v" * 4094),)
    )


def test_bool_counters_container_names_and_refs_fail_closed():
    with pytest.raises(DockerControlContractErrorV1):
        _auth_record().content.__class__.build(
            operation_id=_intent().operation_id,
            operation=DockerControlOperationV1.CREATE,
            effect_id="effect",
            control_intent_proof_digest=SHA,
            phase=DockerMutationPhaseV1.ADMITTED,
            revision=True, attempt_count=0, previous_record_digest=None,
            container_ref=None, verification_result_digest=None,
        )
    with pytest.raises(DockerControlContractErrorV1):
        _spec(container_name="bad/name")
    with pytest.raises(DockerControlContractErrorV1):
        _intent(DockerControlOperationV1.START, container_ref="C" * 64)


def test_foreign_disposition_enum_is_rejected():
    class Foreign(str, Enum):
        ABSENT = "ABSENT"
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationLookupResultV1.build(SHA, Foreign.ABSENT, None)


def _record_from(base, **changes):
    content = base.content
    values = dict(
        operation_id=content.operation_id,
        operation=content.operation,
        effect_id=content.effect_id,
        control_intent_proof_digest=content.control_intent_proof_digest,
        phase=content.phase,
        revision=content.revision,
        attempt_count=content.attempt_count,
        previous_record_digest=content.previous_record_digest,
        container_ref=content.container_ref,
        verification_result_digest=content.verification_result_digest,
    )
    values.update(changes)
    record = DockerMutationRecordV1.build(**values)
    return AuthenticatedDockerMutationRecordV1(
        record, changes.get("authority_ref", base.authority_ref),
        changes.get("key_ref", base.key_ref), SHA,
    )


def test_cas_request_rejects_invalid_transition_graph_and_substitutions():
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    DockerMutationCASRequestV1.build(
        admitted.content.operation_id, admitted, attempted
    )

    invalid = []
    invalid.append(_auth_record(DockerMutationPhaseV1.ATTEMPTED, SHA))
    invalid.append(_record_from(
        admitted, phase=DockerMutationPhaseV1.VERIFIED,
        revision=3, attempt_count=1,
        previous_record_digest=admitted.content.record_digest,
        container_ref="c" * 64, verification_result_digest=SHA,
    ))
    invalid.append(_record_from(
        attempted, phase=DockerMutationPhaseV1.ADMITTED,
        revision=1, attempt_count=0, previous_record_digest=None,
        container_ref=None, verification_result_digest=None,
    ))
    invalid.append(_record_from(
        attempted, previous_record_digest=attempted.content.record_digest,
    ))
    invalid.append(_record_from(
        attempted, control_intent_proof_digest="b" * 64,
    ))
    invalid.append(AuthenticatedDockerMutationRecordV1(
        attempted.content, "alternate", "key", SHA
    ))
    start_id = docker_operation_id_v1(DockerControlOperationV1.START, "effect")
    invalid.append(_record_from(
        attempted, operation=DockerControlOperationV1.START,
        operation_id=start_id,
    ))
    for replacement in invalid:
        with pytest.raises(DockerControlContractErrorV1):
            DockerMutationCASRequestV1.build(
                admitted.content.operation_id, admitted, replacement
            )

    attempted_again = _record_from(
        attempted, previous_record_digest=attempted.content.record_digest
    )
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            attempted.content.operation_id, attempted, attempted_again
        )
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            attempted.content.operation_id, attempted, admitted
        )


@pytest.mark.parametrize("which", ("expected", "replacement"))
def test_cas_request_recursively_rejects_mutated_records(which):
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    target = admitted if which == "expected" else attempted
    object.__setattr__(target.content, "attempt_count", 99)
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            admitted.content.operation_id, admitted, attempted
        )


def test_record_rejects_create_operation_id_relabelled_as_start():
    content = _auth_record().content
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationRecordV1.build(
            operation_id=content.operation_id,
            operation=DockerControlOperationV1.START,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=content.phase, revision=content.revision,
            attempt_count=content.attempt_count,
            previous_record_digest=None, container_ref=None,
            verification_result_digest=None,
        )


@pytest.mark.parametrize("key,value", (("BAD\ud800", "value"), ("KEY", "BAD\ud800")))
def test_environment_lone_surrogates_fail_causally_closed(key, value):
    with pytest.raises(DockerControlContractErrorV1) as caught:
        DockerWorkloadEnvironmentEntryV1.build(key, value)
    assert caught.value.code.value == "DOCKER_CONTROL_CONTRACT_INVALID"
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    assert "UnicodeEncodeError" not in "".join(traceback.format_exception(caught.value))


def test_attempted_to_verified_cas_happy_path_reconstructs_exactly():
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED,
        admitted.content.record_digest,
    )
    verified = _auth_record(
        DockerMutationPhaseV1.VERIFIED,
        attempted.content.record_digest,
    )
    request = DockerMutationCASRequestV1.build(
        attempted.content.operation_id,
        attempted,
        verified,
    )
    rebuilt_request = DockerMutationCASRequestV1(
        request.operation_id,
        request.expected,
        request.replacement,
        request.request_digest,
    )
    assert rebuilt_request == request
    result = DockerCASResultV1.build(
        request, DockerCASDispositionV1.APPLIED, verified
    )
    rebuilt_result = DockerCASResultV1(
        result.request,
        result.disposition,
        result.record,
        result.result_digest,
    )
    assert rebuilt_result == result


def test_effect_id_only_relabel_rejects_canonical_operation_id_binding():
    original = _auth_record().content
    with pytest.raises(DockerControlContractErrorV1) as caught:
        DockerMutationRecordV1.build(
            operation_id=original.operation_id,
            operation=original.operation,
            effect_id="different-effect",
            control_intent_proof_digest=original.control_intent_proof_digest,
            phase=original.phase,
            revision=original.revision,
            attempt_count=original.attempt_count,
            previous_record_digest=original.previous_record_digest,
            container_ref=original.container_ref,
            verification_result_digest=original.verification_result_digest,
        )
    assert caught.value.code.value == "DOCKER_CONTROL_CONTRACT_INVALID"
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
