from hashlib import sha256

import pytest

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    DockerAbsenceContentV1,
    DockerImageV1,
    DockerLabelsV1,
    DockerLookupDispositionV1,
    DockerLookupPurposeV1,
    DockerLookupRequestV1,
)
from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.control import (
    DockerHostControlErrorV1,
    DockerHostControlV1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlIntentV1,
    DockerControlOperationV1,
    DockerCreateSpecificationV1,
    DockerExpectedCreateBindingV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
    docker_accelerator_device_requests_digest_v1,
    docker_device_requests_projection_digest_v1,
    docker_operation_id_v1,
    docker_owned_label_projections_v1,
    docker_owned_labels_projection_digest_v1,
)
from synaptic_host.docker_v1.control_model import (
    DockerExactNameInventoryResultV1,
    DockerExactNameInventoryV1,
    DockerImageInspectProjectionV1,
    DockerImageInspectResultV1,
    DockerTypedResultKindV1,
    DockerContainerInspectProjectionV1,
    DockerContainerInspectResultV1,
    DockerContainerStateV1,
    DockerContainerStatusV1,
    DockerEnvironmentEntryProjectionV1,
    DockerEnvironmentProjectionV1,
    DockerMountProjectionV1,
    docker_typed_request_digest_v1,
)
from synaptic_host.docker_v1.verification import (
    docker_create_projection_matches_v1,
)
from synaptic_host.docker_v1.model import (
    DockerCLICommandV1,
    DockerCLIOutcomeV1,
    DockerCLIResultV1,
    DockerCLIVerbV1,
)


SHA = "a" * 64
IMAGE = "sha256:" + "b" * 64


def _labels(effect_kind="submit"):
    return DockerLabelsV1(
        SHA, "docker", "profile", "account", "namespace", "project",
        "run", SHA, SHA, "effect", effect_kind, SHA, SHA,
    )


def _evidence(command, outcome=DockerCLIOutcomeV1.SUCCESS, policy_digest=SHA):
    exit_code = 0 if outcome is DockerCLIOutcomeV1.SUCCESS else 1
    empty = sha256(b"").hexdigest()
    body = {
        "command_digest": command.command_digest, "exit_code": exit_code,
        "outcome": outcome.value, "policy_digest": policy_digest,
        "schema_version": "synaptic-host-docker-cli-result/v1",
        "stderr_digest": empty, "stderr_size": 0,
        "stdout_digest": empty, "stdout_size": 0,
    }
    return DockerCLIResultV1(
        command.command_digest, policy_digest, outcome, exit_code,
        0, empty, 0, empty,
        digest_v1(body),
    )


def _image_result(
    outcome=DockerCLIOutcomeV1.SUCCESS, image_digest=IMAGE,
    policy_digest=SHA,
):
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT, ("--type", "image", image_digest)
    )
    request_digest = docker_typed_request_digest_v1(
        DockerTypedResultKindV1.IMAGE_INSPECT, image_digest, command.command_digest
    )
    projection = (
        DockerImageInspectProjectionV1.build(
            image_digest, request_digest, command.command_digest
        ) if outcome is DockerCLIOutcomeV1.SUCCESS else None
    )
    return DockerImageInspectResultV1.build(
        image_digest, request_digest, command,
        _evidence(command, outcome, policy_digest), projection
    )


def _inventory_result(labels, refs=()):
    name = labels.container_name
    query = f"name=^/{name}$"
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.PS,
        ("--all", "--quiet", "--no-trunc", "--filter", query),
    )
    request_digest = docker_typed_request_digest_v1(
        DockerTypedResultKindV1.EXACT_NAME_INVENTORY,
        name, command.command_digest,
    )
    projection = DockerExactNameInventoryV1.build(
        name, query, request_digest, command.command_digest, tuple(refs)
    )
    return DockerExactNameInventoryResultV1.build(
        name, request_digest, command, _evidence(command), projection
    )


def _one_id_fixture(status=DockerContainerStatusV1.RUNNING, exit_code=0,
                    extra_environment=True, labels=None, accelerator=None,
                    observed_device_requests_digest=None):
    labels = labels or _labels()
    accelerator = accelerator or AcceleratorDeviceRequestV1("cpu", (), ())
    expected_device_requests_digest = (
        docker_accelerator_device_requests_digest_v1(accelerator)
    )
    if observed_device_requests_digest is None:
        observed_device_requests_digest = expected_device_requests_digest
    container_ref = "1" * 64
    env_entry = DockerWorkloadEnvironmentEntryV1.build("TOKEN", "expected")
    env_binding = DockerWorkloadEnvironmentBindingV1.build(
        SHA, ("TOKEN",), (env_entry,)
    )
    auth_env = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        env_binding, "authority", "key", SHA
    )
    owned_digest = docker_owned_labels_projection_digest_v1(labels)
    source_destination = sha256(b"/source").hexdigest()
    artifact_destination = sha256(b"/artifacts").hexdigest()
    specification = DockerCreateSpecificationV1.build(
        labels_digest=labels.digest,
        owned_labels_projection_digest=owned_digest,
        container_name=labels.container_name, image_digest=IMAGE,
        runtime_digest=SHA, workload_digest=SHA, argument_count=1,
        arguments_digest=SHA,
        environment_binding_proof_digest=auth_env.proof_digest,
        mount_resolution_digest=SHA, path_binding_proof_digest=SHA,
        source_windows_path_digest=SHA, source_unc_digest="c" * 64,
        source_destination_digest=source_destination, source_read_only=True,
        artifact_windows_path_digest=SHA, artifact_unc_digest="d" * 64,
        artifact_destination_digest=artifact_destination,
        artifact_read_write=True, network_mode="none",
        nano_cpus=1_000_000_000, memory_bytes=1024,
        device_requests_digest=expected_device_requests_digest,
        endpoint_descriptor_digest=SHA,
    )
    operation_id = docker_operation_id_v1(
        DockerControlOperationV1.CREATE, labels.effect_id
    )
    intent = DockerControlIntentV1.build(
        operation_id=operation_id, operation=DockerControlOperationV1.CREATE,
        effect_id=labels.effect_id, engine_command_digest=labels.command_digest,
        labels_digest=labels.digest, container_name=labels.container_name,
        create_specification_digest=specification.specification_digest,
        cli_command_digest=SHA, container_ref=None,
        cli_policy_digest=SHA,
        verified_create_record_digest=None,
    )
    auth_intent = AuthenticatedDockerControlIntentV1(
        intent, "authority", "key", SHA
    )
    expected = DockerExpectedCreateBindingV1.build(
        labels, specification, auth_intent, auth_env
    )
    auth_expected = AuthenticatedDockerExpectedCreateBindingV1(
        expected, "authority", "key", SHA
    )
    record = DockerMutationRecordV1.build(
        operation_id=operation_id, operation=DockerControlOperationV1.CREATE,
        effect_id=labels.effect_id,
        control_intent_proof_digest=auth_intent.proof_digest,
        phase=DockerMutationPhaseV1.ATTEMPTED, revision=2,
        attempt_count=1, previous_record_digest=SHA,
        container_ref=None, verification_result_digest=None,
    )
    auth_record = AuthenticatedDockerMutationRecordV1(
        record, "authority", "key", SHA
    )
    repository_result = DockerMutationLookupResultV1.build(
        operation_id, DockerMutationLookupDispositionV1.FOUND, auth_record
    )
    projected_env = [DockerEnvironmentEntryProjectionV1.build(
        env_entry.key_digest, env_entry.value_digest
    )]
    if extra_environment:
        projected_env.append(DockerEnvironmentEntryProjectionV1.build(
            sha256(b"IMAGE_DEFAULT").hexdigest(), sha256(b"default").hexdigest()
        ))
    started = status is not DockerContainerStatusV1.CREATED
    running = status in (
        DockerContainerStatusV1.RUNNING, DockerContainerStatusV1.PAUSED,
        DockerContainerStatusV1.RESTARTING,
    )
    state = DockerContainerStateV1.build(
        status, running, exit_code, started, 0
    )
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT, ("--type", "container", container_ref)
    )
    request_digest = docker_typed_request_digest_v1(
        DockerTypedResultKindV1.CONTAINER_INSPECT,
        container_ref, command.command_digest,
    )
    projection = DockerContainerInspectProjectionV1.build(
        container_ref=container_ref, container_name=labels.container_name,
        image_digest=IMAGE, request_digest=request_digest,
        command_digest=command.command_digest,
        owned_labels=docker_owned_label_projections_v1(labels),
        network_mode="none", nano_cpus=1_000_000_000,
        memory_bytes=1024,
        mounts=(
            DockerMountProjectionV1.build(
                "bind", "d" * 64, artifact_destination, True
            ),
            DockerMountProjectionV1.build(
                "bind", "c" * 64, source_destination, False
            ),
        ), state=state,
        environment=DockerEnvironmentProjectionV1.build(projected_env),
        argument_count=1, arguments_digest=SHA,
        device_requests_digest=observed_device_requests_digest,
    )
    container_result = DockerContainerInspectResultV1.build(
        container_ref, request_digest, command, _evidence(command), projection
    )
    return labels, container_ref, repository_result, auth_expected, container_result


def test_exact_gpu_create_projection_matches_bound_specification():
    gpu = AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",))
    labels, ref, _record, expected, inspected = _one_id_fixture(
        accelerator=gpu
    )
    assert docker_create_projection_matches_v1(
        labels, expected, expected.content.environment_binding,
        inspected.projection, ref, inspected.evidence,
    )


@pytest.mark.parametrize("observed", (
    (),
    (("nvidia", 1, ("0",), (("gpu",),), ()),),
    (("amd", 0, ("0",), (("gpu",),), ()),),
    (("nvidia", 0, ("all",), (("gpu",),), ()),),
    (("nvidia", 0, ("1",), (("gpu",),), ()),),
    (("nvidia", 0, ("0", "1"), (("gpu",),), ()),),
    (("nvidia", 0, ("0",), (("compute",),), ()),),
    (("nvidia", 0, ("0",), (("gpu", "utility"),), ()),),
    (("nvidia", 0, ("0",), (("gpu",),), (("mode", "exclusive"),)),),
    (
        ("nvidia", 0, ("0",), (("gpu",),), ()),
        ("nvidia", 0, ("0",), (("gpu",),), ()),
    ),
))
def test_gpu_create_projection_rejects_every_well_formed_device_drift(observed):
    gpu = AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",))
    labels, ref, _record, expected, inspected = _one_id_fixture(
        accelerator=gpu,
        observed_device_requests_digest=(
            docker_device_requests_projection_digest_v1(observed)
        ),
    )
    assert not docker_create_projection_matches_v1(
        labels, expected, expected.content.environment_binding,
        inspected.projection, ref, inspected.evidence,
    )


class Authority:
    authority_ref = "authority"
    key_ref = "key"
    def authenticate(self, value): return value


class AbsenceAuthority(Authority):
    def issue(self, content):
        return AuthenticatedDockerAbsenceV1(content, self.authority_ref, self.key_ref, SHA)


class MutableAuthority(Authority):
    def __init__(self, *, mutate_on_auth=False, mutate_on_issue=False):
        self.authority_ref = "authority"
        self.key_ref = "key"
        self.mutate_on_auth = mutate_on_auth
        self.mutate_on_issue = mutate_on_issue

    def authenticate(self, value):
        if self.mutate_on_auth:
            self.key_ref = "changed"
        return value

    def issue(self, content):
        value = AuthenticatedDockerAbsenceV1(
            content, self.authority_ref, self.key_ref, SHA
        )
        if self.mutate_on_issue:
            self.key_ref = "changed"
        return value


class SubstitutingAbsenceAuthority(Authority):
    def __init__(self, field, *, mutate_in_place):
        self.field = field
        self.mutate_in_place = mutate_in_place

    def issue(self, content):
        replacements = {
            "request_digest": "e" * 64,
            "labels_digest": "e" * 64,
            "purpose": DockerLookupPurposeV1.RECONCILE_SUBMIT,
            "generation": content.generation + 1,
            "evidence_digest": "e" * 64,
        }
        if self.mutate_in_place:
            object.__setattr__(content, self.field, replacements[self.field])
            changed = content
        else:
            values = {
                name: getattr(content, name)
                for name in content.__dataclass_fields__
            }
            values[self.field] = replacements[self.field]
            changed = DockerAbsenceContentV1(**values)
        return AuthenticatedDockerAbsenceV1(
            changed, self.authority_ref, self.key_ref, SHA
        )

class TypedCLI:
    def __init__(self, image_result=None, inventory_result=None, container_result=None):
        self.image_result = image_result
        self.inventory_result = inventory_result
        self.container_result = container_result
        self.calls = []
    def inspect_image(self, digest):
        self.calls.append(("image", digest)); return self.image_result
    def inventory_exact_name(self, name):
        self.calls.append(("inventory", name)); return self.inventory_result
    def inspect_container(self, ref):
        self.calls.append(("container", ref)); return self.container_result


class Repository:
    def __init__(self, result): self.result = result; self.calls = []
    def lookup(self, operation_id): self.calls.append(operation_id); return self.result
    def admit(self, _request): raise AssertionError("read-only control called admit")
    def compare_and_swap(self, _request): raise AssertionError("read-only control called CAS")


class Catalog:
    def __init__(self, value=None): self.calls = []; self.value = value
    def resolve(self, *args):
        self.calls.append(args)
        if self.value is None: raise AssertionError
        return self.value


def _control(cli, repository, catalog=None, absence_authority=None,
             record_authority=None, expected_authority=None,
             intent_authority=None, environment_authority=None):
    authority = Authority()
    return DockerHostControlV1(
        typed_cli=cli, mutation_repository=repository,
        mutation_record_authority=record_authority or authority,
        expected_catalog=catalog or Catalog(),
        expected_authority=expected_authority or authority,
        intent_authority=intent_authority or authority,
        environment_authority=environment_authority or authority,
        absence_authority=absence_authority or AbsenceAuthority(),
        cli_policy_digest=SHA,
    )


def test_require_present_true_false_and_closed_failure_are_one_shot():
    image = DockerImageV1("image", IMAGE)
    repo = Repository(None)
    cli = TypedCLI(image_result=_image_result())
    assert _control(cli, repo).require_present(image) is True
    assert cli.calls == [("image", IMAGE)]
    cli = TypedCLI(image_result=_image_result(DockerCLIOutcomeV1.NONZERO_EXIT))
    assert _control(cli, repo).require_present(image) is False
    with pytest.raises(DockerHostControlErrorV1):
        _control(TypedCLI(image_result=object()), repo).require_present(image)


def test_require_present_rejects_valid_cross_target_result_as_closed_error():
    other = "sha256:" + "f" * 64
    with pytest.raises(DockerHostControlErrorV1):
        _control(
            TypedCLI(image_result=_image_result(image_digest=other)),
            Repository(None),
        ).require_present(DockerImageV1("image", IMAGE))


def test_require_present_rejects_policy_digest_mismatch_without_bypass():
    with pytest.raises(DockerHostControlErrorV1):
        _control(
            TypedCLI(image_result=_image_result(policy_digest="f" * 64)),
            Repository(None),
        ).require_present(DockerImageV1("image", IMAGE))


def test_require_present_rejects_valid_cross_target_nonzero_as_closed_error():
    other = "sha256:" + "f" * 64
    with pytest.raises(DockerHostControlErrorV1):
        _control(
            TypedCLI(image_result=_image_result(
                DockerCLIOutcomeV1.NONZERO_EXIT, other
            )),
            Repository(None),
        ).require_present(DockerImageV1("image", IMAGE))


def test_lookup_unsupported_is_indeterminate_with_zero_calls():
    labels = _labels("stage")
    cli = TypedCLI()
    repo = Repository(None)
    result = _control(cli, repo).lookup(
        DockerLookupRequestV1(labels, DockerLookupPurposeV1.OBSERVE, 1)
    )
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE
    assert cli.calls == [] and repo.calls == []


@pytest.mark.parametrize(
    "repository_disposition,expected",
    (
        (DockerMutationLookupDispositionV1.ABSENT,
         DockerLookupDispositionV1.DEFINITELY_ABSENT),
        (DockerMutationLookupDispositionV1.INDETERMINATE,
         DockerLookupDispositionV1.INDETERMINATE),
    ),
)
def test_zero_inventory_absence_requires_repository_absent(
    repository_disposition, expected,
):
    labels = _labels()
    inventory = _inventory_result(labels)
    operation_id = digest_v1({
        "effect_id": labels.effect_id, "operation": "CREATE",
        "schema_version": "synaptic-host-docker-operation-id/v1",
    })
    repository_result = DockerMutationLookupResultV1.build(
        operation_id, repository_disposition, None
    )
    repo = Repository(repository_result)
    catalog = Catalog()
    result = _control(
        TypedCLI(inventory_result=inventory), repo, catalog
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is expected
    assert len(repo.calls) == 1 and catalog.calls == []


@pytest.mark.parametrize(
    "repository_disposition",
    (
        DockerMutationLookupDispositionV1.ABSENT,
        DockerMutationLookupDispositionV1.INDETERMINATE,
    ),
)
def test_zero_inventory_rejects_valid_cross_operation_repository_result(
    repository_disposition,
):
    labels = _labels()
    absence = AbsenceAuthority()
    result = _control(
        TypedCLI(inventory_result=_inventory_result(labels)),
        Repository(DockerMutationLookupResultV1.build(
            "f" * 64, repository_disposition, None
        )),
        absence_authority=absence,
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_zero_inventory_rejects_valid_cross_name_result_before_repository():
    labels = _labels()
    other = DockerLabelsV1(
        "f" * 64, labels.provider_id, labels.profile_ref, labels.account_ref,
        labels.namespace_ref, labels.project_ref, labels.run_id,
        labels.plan_fingerprint, labels.preparation_digest, labels.effect_id,
        labels.effect_kind, labels.effect_identity_digest,
        labels.adapter_descriptor_digest,
    )
    repo = Repository(None)
    result = _control(
        TypedCLI(inventory_result=_inventory_result(other)), repo
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE
    assert repo.calls == []


@pytest.mark.parametrize("mode", ("auth", "issue"))
def test_zero_inventory_rejects_absence_authority_pin_changes(mode):
    labels = _labels()
    operation_id = docker_operation_id_v1(
        DockerControlOperationV1.CREATE, labels.effect_id
    )
    authority = MutableAuthority(
        mutate_on_auth=mode == "auth", mutate_on_issue=mode == "issue"
    )
    result = _control(
        TypedCLI(inventory_result=_inventory_result(labels)),
        Repository(DockerMutationLookupResultV1.build(
            operation_id, DockerMutationLookupDispositionV1.ABSENT, None
        )),
        absence_authority=authority,
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


@pytest.mark.parametrize(
    "field",
    (
        "request_digest", "labels_digest", "purpose", "generation",
        "evidence_digest",
    ),
)
@pytest.mark.parametrize("mutate_in_place", (False, True))
def test_zero_inventory_rejects_same_signer_absence_content_substitution(
    field, mutate_in_place,
):
    labels = _labels()
    operation_id = docker_operation_id_v1(
        DockerControlOperationV1.CREATE, labels.effect_id
    )
    result = _control(
        TypedCLI(inventory_result=_inventory_result(labels)),
        Repository(DockerMutationLookupResultV1.build(
            operation_id, DockerMutationLookupDispositionV1.ABSENT, None
        )),
        absence_authority=SubstitutingAbsenceAuthority(
            field, mutate_in_place=mutate_in_place
        ),
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_multiple_inventory_stays_multiple_and_never_reads_repository():
    labels = _labels()
    cli = TypedCLI(inventory_result=_inventory_result(
        labels, ("1" * 64, "2" * 64)
    ))
    repo = Repository(None)
    result = _control(cli, repo).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.MULTIPLE
    assert repo.calls == []


@pytest.mark.parametrize(
    "status,exit_code,purpose,expected",
    (
        (DockerContainerStatusV1.CREATED, 0, DockerLookupPurposeV1.OBSERVE, "created"),
        (DockerContainerStatusV1.CREATED, 0, DockerLookupPurposeV1.RECONCILE_SUBMIT, None),
        (DockerContainerStatusV1.RUNNING, 0, DockerLookupPurposeV1.OBSERVE, "running"),
        (DockerContainerStatusV1.EXITED, 0, DockerLookupPurposeV1.OBSERVE, "succeeded"),
        (DockerContainerStatusV1.EXITED, 7, DockerLookupPurposeV1.OBSERVE, "failed"),
        (DockerContainerStatusV1.DEAD, 7, DockerLookupPurposeV1.OBSERVE, "failed"),
        (DockerContainerStatusV1.PAUSED, 0, DockerLookupPurposeV1.OBSERVE, None),
        (DockerContainerStatusV1.RESTARTING, 0, DockerLookupPurposeV1.OBSERVE, None),
    ),
)
def test_one_id_state_matrix_and_image_default_environment(
    status, exit_code, purpose, expected,
):
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture(status, exit_code)
    )
    cli = TypedCLI(
        inventory_result=_inventory_result(labels, (ref,)),
        container_result=container_result,
    )
    repo = Repository(repository_result)
    result = _control(cli, repo, Catalog(expected_binding)).lookup(
        DockerLookupRequestV1(labels, purpose, 1)
    )
    if expected is None:
        assert result.disposition is DockerLookupDispositionV1.INDETERMINATE
    else:
        assert result.disposition is DockerLookupDispositionV1.FOUND
        assert result.phase.value == expected
        assert result.container_ref == ref and result.labels == labels
    assert len(repo.calls) == 1
    assert not hasattr(repo, "admit_calls")


def test_one_id_accepts_stable_independent_expected_catalog_signer():
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    alternate = MutableAuthority()
    alternate.authority_ref = "catalog-authority"
    alternate.key_ref = "catalog-key"
    signed = AuthenticatedDockerExpectedCreateBindingV1(
        expected_binding.content, alternate.authority_ref,
        alternate.key_ref, SHA,
    )
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ),
        Repository(repository_result), Catalog(signed),
        expected_authority=alternate,
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.FOUND


def test_one_id_rejects_valid_same_signer_expected_binding_for_other_labels():
    labels, ref, repository_result, _expected_binding, container_result = (
        _one_id_fixture()
    )
    other_labels = DockerLabelsV1(
        "f" * 64, labels.provider_id, labels.profile_ref, labels.account_ref,
        labels.namespace_ref, labels.project_ref, labels.run_id,
        labels.plan_fingerprint, labels.preparation_digest, labels.effect_id,
        labels.effect_kind, labels.effect_identity_digest,
        labels.adapter_descriptor_digest,
    )
    _, _, _, other_expected, _ = _one_id_fixture(labels=other_labels)
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ),
        Repository(repository_result), Catalog(other_expected),
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_one_id_disappearing_after_inventory_is_indeterminate():
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    command = container_result.command
    container_result = DockerContainerInspectResultV1.build(
        ref, container_result.request_digest, command,
        _evidence(command, DockerCLIOutcomeV1.NONZERO_EXIT), None,
    )
    cli = TypedCLI(
        inventory_result=_inventory_result(labels, (ref,)),
        container_result=container_result,
    )
    result = _control(
        cli, Repository(repository_result), Catalog(expected_binding)
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def _retargeted_container_result(result, target):
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT, ("--type", "container", target)
    )
    request_digest = docker_typed_request_digest_v1(
        DockerTypedResultKindV1.CONTAINER_INSPECT,
        target, command.command_digest,
    )
    values = {
        name: getattr(result.projection, name)
        for name in result.projection.__dataclass_fields__
        if name != "projection_digest"
    }
    values.update(
        container_ref=target, request_digest=request_digest,
        command_digest=command.command_digest,
    )
    projection = DockerContainerInspectProjectionV1.build(**values)
    return DockerContainerInspectResultV1.build(
        target, request_digest, command, _evidence(command), projection
    )


def test_one_id_rejects_valid_cross_target_container_result():
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=_retargeted_container_result(
                container_result, "2" * 64
            ),
        ),
        Repository(repository_result), Catalog(expected_binding),
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


@pytest.mark.parametrize(
    "role",
    ("record", "expected", "intent", "environment"),
)
def test_one_id_rejects_authority_pin_change_during_authentication(role):
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    changed = MutableAuthority(mutate_on_auth=True)
    kwargs = {f"{role}_authority": changed}
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ),
        Repository(repository_result), Catalog(expected_binding), **kwargs,
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


@pytest.mark.parametrize("role", ("record", "expected", "intent", "environment"))
def test_one_id_rejects_same_pin_alternate_authority_object(role):
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    control = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ),
        Repository(repository_result), Catalog(expected_binding),
    )
    setattr(control, "_" + role + "_authority", Authority())
    result = control.lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_zero_inventory_rejects_same_pin_alternate_absence_authority_object():
    labels = _labels()
    operation_id = docker_operation_id_v1(
        DockerControlOperationV1.CREATE, labels.effect_id
    )
    control = _control(
        TypedCLI(inventory_result=_inventory_result(labels)),
        Repository(DockerMutationLookupResultV1.build(
            operation_id, DockerMutationLookupDispositionV1.ABSENT, None
        )),
    )
    control._absence_authority = AbsenceAuthority()
    result = control.lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_zero_inventory_rejects_mid_issue_absence_object_swap():
    labels = _labels()
    operation_id = docker_operation_id_v1(
        DockerControlOperationV1.CREATE, labels.effect_id
    )

    class SwappingAbsence(AbsenceAuthority):
        control = None
        def issue(self, content):
            value = super().issue(content)
            self.control._absence_authority = AbsenceAuthority()
            return value

    authority = SwappingAbsence()
    control = _control(
        TypedCLI(inventory_result=_inventory_result(labels)),
        Repository(DockerMutationLookupResultV1.build(
            operation_id, DockerMutationLookupDispositionV1.ABSENT, None
        )), absence_authority=authority,
    )
    authority.control = control
    result = control.lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


class ObjectSwappingAuthority(Authority):
    def __init__(self, role):
        self.role = role
        self.control = None

    def authenticate(self, value):
        setattr(self.control, "_" + self.role + "_authority", Authority())
        return value


@pytest.mark.parametrize("role", ("record", "expected", "intent", "environment"))
def test_one_id_rejects_mid_auth_role_object_swap(role):
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    authority = ObjectSwappingAuthority(role)
    kwargs = {f"{role}_authority": authority}
    control = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ), Repository(repository_result), Catalog(expected_binding), **kwargs,
    )
    authority.control = control
    result = control.lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE


def _rebuilt_container_result(result, attack):
    projection = result.projection
    values = {
        name: getattr(projection, name)
        for name in projection.__dataclass_fields__
        if name != "projection_digest"
    }
    if attack == "config":
        values["memory_bytes"] = 2048
    elif attack == "label":
        labels = list(values["owned_labels"])
        labels[0] = type(labels[0]).build(labels[0].name, "e" * 64)
        values["owned_labels"] = tuple(labels)
    elif attack == "environment":
        entries = list(values["environment"].entries)
        expected_key = sha256(b"TOKEN").hexdigest()
        index = next(
            index for index, item in enumerate(entries)
            if item.key_digest == expected_key
        )
        entries[index] = DockerEnvironmentEntryProjectionV1.build(
            entries[index].key_digest, "e" * 64
        )
        values["environment"] = DockerEnvironmentProjectionV1.build(entries)
    else:
        mounts = list(values["mounts"])
        item = mounts[0]
        mounts[0] = DockerMountProjectionV1.build(
            item.mount_type, "e" * 64, item.destination_digest,
            item.read_write,
        )
        values["mounts"] = tuple(mounts)
    changed = DockerContainerInspectProjectionV1.build(**values)
    return DockerContainerInspectResultV1.build(
        result.target, result.request_digest, result.command,
        result.evidence, changed,
    )


@pytest.mark.parametrize("attack", ("config", "label", "environment", "mount"))
def test_one_id_valid_config_label_env_and_mount_substitutions_are_closed(attack):
    labels, ref, repository_result, expected_binding, container_result = (
        _one_id_fixture()
    )
    container_result = _rebuilt_container_result(container_result, attack)
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=container_result,
        ),
        Repository(repository_result), Catalog(expected_binding),
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE
