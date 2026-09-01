from __future__ import annotations

from hashlib import sha256

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCreateDispositionV1, DockerCreateResultV1, DockerImageV1,
    DockerLabelsV1, DockerRuntimeV1, DockerWorkloadV1,
)

from .control import _snapshot_typed
from .control_contract import (
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    DockerAdmissionDispositionV1, DockerAdmissionResultV1,
    DockerCASDispositionV1, DockerCASResultV1,
    DockerControlIntentV1, DockerControlOperationV1,
    DockerCreateAdmissionV1,
    DockerCreateSpecificationV1, DockerCreateVerificationV1,
    DockerExpectedCreateBindingV1,
    DockerExpectedCreatePublishDispositionV1,
    DockerExpectedCreatePublishRequestV1,
    DockerExpectedCreatePublishResultV1,
    DockerMutationAdmissionRequestV1, DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1, DockerMutationLookupResultV1,
    DockerMutationPhaseV1, DockerMutationRecordV1,
    authenticate_control_intent_v1, authenticate_create_path_binding_v1,
    authenticate_expected_create_binding_v1, authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
    docker_accelerator_device_requests_digest_v1,
    docker_arguments_projection_digest_v1, docker_operation_id_v1,
    docker_owned_labels_projection_digest_v1, snapshot_docker_labels_v1,
    _snapshot_authenticated, _snapshot_contract_content,
)
from .control_model import (
    DockerContainerInspectResultV1, DockerExactNameInventoryResultV1,
)
from .control_private import DockerPrivateCreateInvocationFactoryV1
from .model import (
    DockerCLIOutcomeV1, DockerWindowsPathV1, ResolvedDockerMountsV1,
)
from .verification import docker_create_projection_matches_v1


def _indeterminate():
    return DockerCreateResultV1(DockerCreateDispositionV1.INDETERMINATE)


def _collision():
    return DockerCreateResultV1(DockerCreateDispositionV1.COLLISION)


def _publish_request_snapshot(value):
    return DockerExpectedCreatePublishRequestV1(
        value.engine_command_digest, value.labels_digest,
        _snapshot_authenticated(value.candidate), value.request_digest,
    )


def _admission_request_snapshot(value):
    return DockerMutationAdmissionRequestV1(
        value.operation_id, _snapshot_authenticated(value.candidate),
        value.request_digest,
    )


def _cas_request_snapshot(value):
    return DockerMutationCASRequestV1(
        value.operation_id, _snapshot_authenticated(value.expected),
        _snapshot_authenticated(value.replacement), value.request_digest,
    )


class DockerHostCreateV1:
    def __init__(
        self, *, mount_resolver, path_binder, path_translator,
        environment_resolver, typed_runner, expected_publisher,
        mutation_repository, path_authority, environment_authority,
        intent_authority, expected_authority, record_authority,
        endpoint_descriptor_digest, cli_policy_digest,
    ):
        self._mount_resolver = mount_resolver
        self._path_binder = path_binder
        self._path_translator = path_translator
        self._environment_resolver = environment_resolver
        self._typed_runner = typed_runner
        self._publisher = expected_publisher
        self._repository = mutation_repository
        self._path_authority = path_authority
        self._environment_authority = environment_authority
        self._intent_authority = intent_authority
        self._expected_authority = expected_authority
        self._record_authority = record_authority
        self._endpoint_descriptor_digest = endpoint_descriptor_digest
        self._cli_policy_digest = cli_policy_digest
        self._pins = {
            "path": self._pin(path_authority),
            "environment": self._pin(environment_authority),
            "intent": self._pin(intent_authority),
            "expected": self._pin(expected_authority),
            "record": self._pin(record_authority),
        }
        self._authority_instances = {
            "path": path_authority,
            "environment": environment_authority,
            "intent": intent_authority,
            "expected": expected_authority,
            "record": record_authority,
        }
        self._authority_fields = {
            "path": "_path_authority",
            "environment": "_environment_authority",
            "intent": "_intent_authority",
            "expected": "_expected_authority",
            "record": "_record_authority",
        }

    @staticmethod
    def _pin(authority):
        return (authority.authority_ref, authority.key_ref)

    def _auth(self, role, authority, value, authenticate):
        pins = self._pins[role]
        pinned = self._authority_instances[role]
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != pins
        ):
            raise ValueError
        presented = _snapshot_authenticated(value)
        if (presented.authority_ref, presented.key_ref) != pins:
            raise ValueError
        returned = authenticate(authority, presented)
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != pins
        ):
            raise ValueError
        returned = _snapshot_authenticated(returned)
        if returned != presented or (returned.authority_ref, returned.key_ref) != pins:
            raise ValueError
        return returned

    def _issue(self, role, authority, content, authenticate):
        baseline = _snapshot_contract_content(content)
        pinned = self._authority_instances[role]
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != self._pins[role]
        ):
            raise ValueError
        issued = authority.issue(_snapshot_contract_content(baseline))
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != self._pins[role]
        ):
            raise ValueError
        issued = self._auth(role, authority, issued, authenticate)
        if issued.content != baseline:
            raise ValueError
        return issued

    def create_once(
        self, *, labels, image, runtime, workload, source_ref, artifact_ref,
        working_directory,
    ):
        try:
            labels = snapshot_docker_labels_v1(labels)
            image = DockerImageV1(image.image_ref, image.image_digest, image.presence_policy)
            runtime = DockerRuntimeV1(
                runtime.cpu_count, runtime.memory_bytes, runtime.timeout_seconds,
                AcceleratorDeviceRequestV1(
                    runtime.accelerator_devices.kind,
                    tuple(runtime.accelerator_devices.device_indices),
                    tuple(runtime.accelerator_devices.capabilities),
                ),
                runtime.network_mode,
            )
            workload = DockerWorkloadV1(
                tuple(workload.arguments), tuple(workload.environment_keys),
                workload.workload_digest,
            )
            if labels.effect_kind != "submit" or source_ref == artifact_ref:
                raise ValueError
            preflight = self._preflight(
                labels, image, runtime, workload, source_ref, artifact_ref,
                working_directory,
            )
            prepared_admission = self.prepare_admission(
                labels=labels, image=image, runtime=runtime, workload=workload,
                source_ref=source_ref, artifact_ref=artifact_ref,
                working_directory=working_directory,
            )
            if prepared_admission.expected_create != preflight["expected"]:
                raise ValueError
            publish_request = DockerExpectedCreatePublishRequestV1.build(
                labels.command_digest, labels.digest, preflight["expected"]
            )
            publish_baseline = _publish_request_snapshot(publish_request)
            raw_published = self._publisher.publish_once(
                _publish_request_snapshot(publish_baseline)
            )
            published = DockerExpectedCreatePublishResultV1(
                raw_published.request, raw_published.disposition,
                raw_published.binding, raw_published.result_digest,
            )
            if published.request != publish_baseline:
                return _indeterminate()
            if published.disposition is DockerExpectedCreatePublishDispositionV1.CONFLICT:
                return _collision()
            if (
                published.disposition not in (
                    DockerExpectedCreatePublishDispositionV1.PUBLISHED,
                    DockerExpectedCreatePublishDispositionV1.EXISTING,
                ) or published.binding != preflight["expected"]
            ):
                return _indeterminate()
            admitted = prepared_admission.create_mutation
            admission_request = DockerMutationAdmissionRequestV1.build(
                admitted.content.operation_id, admitted
            )
            admission_baseline = _admission_request_snapshot(admission_request)
            raw_admission = self._repository.admit(
                _admission_request_snapshot(admission_baseline)
            )
            admission = DockerAdmissionResultV1(
                raw_admission.request, raw_admission.disposition,
                raw_admission.record, raw_admission.result_digest,
            )
            if admission.request != admission_baseline:
                return _indeterminate()
            if admission.disposition is DockerAdmissionDispositionV1.CONFLICT:
                return _collision()
            if admission.disposition is DockerAdmissionDispositionV1.INDETERMINATE:
                return _indeterminate()
            current = self._auth(
                "record", self._record_authority, admission.record,
                authenticate_mutation_record_v1,
            )
            if (
                admission.disposition is DockerAdmissionDispositionV1.ADMITTED
                and current != admission_baseline.candidate
            ):
                return _indeterminate()
            if not self._record_matches(current, preflight):
                return _indeterminate()
            create_result = None
            attempted = None
            if current.content.phase is DockerMutationPhaseV1.ADMITTED:
                attempted = self._attempted(current)
                attempt_request = DockerMutationCASRequestV1.build(
                    current.content.operation_id, current, attempted
                )
                attempt_baseline = _cas_request_snapshot(attempt_request)
                try:
                    raw_cas = self._repository.compare_and_swap(
                        _cas_request_snapshot(attempt_baseline)
                    )
                except BaseException:
                    raw_cas = None
                if raw_cas is None:
                    return self._recover(
                        preflight, attempted, None, working_directory=working_directory
                    )
                cas = DockerCASResultV1(
                    raw_cas.request, raw_cas.disposition, raw_cas.record,
                    raw_cas.result_digest,
                )
                if cas.request != attempt_baseline:
                    return _indeterminate()
                if cas.disposition is DockerCASDispositionV1.APPLIED:
                    attempted = self._auth(
                        "record", self._record_authority, cas.record,
                        authenticate_mutation_record_v1,
                    )
                    if attempted != attempt_baseline.replacement:
                        return _indeterminate()
                    try:
                        create_result = preflight["invocation"].execute_once(
                            self._typed_runner
                        )
                    except BaseException:
                        create_result = None
                elif cas.disposition is DockerCASDispositionV1.CURRENT:
                    attempted = self._auth(
                        "record", self._record_authority, cas.record,
                        authenticate_mutation_record_v1,
                    )
                    if attempted.content.phase is DockerMutationPhaseV1.VERIFIED:
                        if not self._record_matches(attempted, preflight):
                            return _indeterminate()
                        return self._recover(
                            preflight, attempted, None,
                            working_directory=working_directory,
                            already_verified=True,
                        )
                else:
                    attempted = attempted
            elif current.content.phase is DockerMutationPhaseV1.ATTEMPTED:
                attempted = current
            elif current.content.phase is DockerMutationPhaseV1.VERIFIED:
                return self._recover(
                    preflight, current, None,
                    working_directory=working_directory,
                    already_verified=True,
                )
            else:
                return _indeterminate()
            if not self._record_matches(attempted, preflight):
                return _indeterminate()
            return self._recover(
                preflight, attempted, create_result,
                working_directory=working_directory,
            )
        except BaseException:
            return _indeterminate()

    def prepare_admission(
        self, *, labels, image, runtime, workload, source_ref, artifact_ref,
        working_directory,
    ) -> DockerCreateAdmissionV1:
        """Derive the exact initial admission without publishing or running Docker."""

        labels = snapshot_docker_labels_v1(labels)
        image = DockerImageV1(image.image_ref, image.image_digest, image.presence_policy)
        runtime = DockerRuntimeV1(
            runtime.cpu_count, runtime.memory_bytes, runtime.timeout_seconds,
            AcceleratorDeviceRequestV1(
                runtime.accelerator_devices.kind,
                tuple(runtime.accelerator_devices.device_indices),
                tuple(runtime.accelerator_devices.capabilities),
            ),
            runtime.network_mode,
        )
        workload = DockerWorkloadV1(
            tuple(workload.arguments), tuple(workload.environment_keys),
            workload.workload_digest,
        )
        if (
            labels.effect_kind != "submit"
            or source_ref == artifact_ref
            or type(working_directory) is not str
            or not working_directory.startswith("/artifacts/")
        ):
            raise ValueError("Docker create admission is invalid")
        preflight = self._preflight(
            labels, image, runtime, workload, source_ref, artifact_ref,
            working_directory,
        )
        return DockerCreateAdmissionV1.build(
            preflight["expected"], self._admitted(preflight)
        )

    def _preflight(
        self, labels, image, runtime, workload, source_ref, artifact_ref,
        working_directory,
    ):
        resolved = self._resolve(labels, image, runtime, workload, source_ref, artifact_ref)
        path_binding = self._path_binder.bind(resolved, source_ref, artifact_ref)
        path_binding = self._auth(
            "path", self._path_authority, path_binding,
            authenticate_create_path_binding_v1,
        )
        binding_content = path_binding.content
        if (
            binding_content.labels_digest != labels.digest
            or binding_content.source_ref != source_ref
            or binding_content.artifact_ref != artifact_ref
            or binding_content.mount_resolution_digest != resolved.resolution_digest
            or binding_content.source_request.posix_path
            != resolved.source_wsl_private_path
            or binding_content.artifact_request.posix_path
            != resolved.artifact_wsl_root
        ):
            raise ValueError
        source_path = self._translate(path_binding.content.source_request)
        artifact_path = self._translate(path_binding.content.artifact_request)
        if source_path.unc_path == artifact_path.unc_path:
            raise ValueError
        private_env = self._environment_resolver.resolve(workload)
        environment = private_env.authenticated_binding_snapshot(
            self._environment_authority
        )
        environment = self._auth(
            "environment", self._environment_authority, environment,
            authenticate_workload_environment_binding_v1,
        )
        invocation = DockerPrivateCreateInvocationFactoryV1().build(
            labels=labels, image=image, runtime=runtime, workload=workload,
            source_path=source_path, artifact_path=artifact_path,
            working_directory=working_directory,
            environment=private_env,
            environment_authority=self._environment_authority,
        )
        specification = DockerCreateSpecificationV1.build(
            labels_digest=labels.digest,
            owned_labels_projection_digest=docker_owned_labels_projection_digest_v1(labels),
            container_name=labels.container_name, image_digest=image.image_digest,
            runtime_digest=runtime.digest, workload_digest=workload.workload_digest,
            argument_count=len(workload.arguments),
            arguments_digest=docker_arguments_projection_digest_v1(workload.arguments),
            working_directory_digest=sha256(
                working_directory.encode("utf-8")
            ).hexdigest(),
            environment_binding_proof_digest=environment.proof_digest,
            mount_resolution_digest=resolved.resolution_digest,
            path_binding_proof_digest=path_binding.proof_digest,
            source_windows_path_digest=source_path.path_digest,
            source_unc_digest=sha256(source_path.unc_path.encode()).hexdigest(),
            source_destination_digest=sha256(b"/source").hexdigest(),
            source_read_only=True,
            artifact_windows_path_digest=artifact_path.path_digest,
            artifact_unc_digest=sha256(artifact_path.unc_path.encode()).hexdigest(),
            artifact_destination_digest=sha256(b"/artifacts").hexdigest(),
            artifact_read_write=True, network_mode="none",
            nano_cpus=runtime.cpu_count * 1_000_000_000,
            memory_bytes=runtime.memory_bytes,
            device_requests_digest=docker_accelerator_device_requests_digest_v1(
                runtime.accelerator_devices
            ),
            endpoint_descriptor_digest=self._endpoint_descriptor_digest,
        )
        operation_id = docker_operation_id_v1(
            DockerControlOperationV1.CREATE, labels.effect_id
        )
        intent = DockerControlIntentV1.build(
            operation_id=operation_id, operation=DockerControlOperationV1.CREATE,
            effect_id=labels.effect_id, engine_command_digest=labels.command_digest,
            labels_digest=labels.digest, container_name=labels.container_name,
            create_specification_digest=specification.specification_digest,
            cli_command_digest=invocation.command_digest, container_ref=None,
            cli_policy_digest=self._cli_policy_digest,
            verified_create_record_digest=None,
        )
        auth_intent = self._issue(
            "intent", self._intent_authority, intent,
            authenticate_control_intent_v1,
        )
        expected_content = DockerExpectedCreateBindingV1.build(
            labels, specification, auth_intent, environment
        )
        expected = self._issue(
            "expected", self._expected_authority, expected_content,
            authenticate_expected_create_binding_v1,
        )
        return locals()

    def _resolve(self, labels, image, runtime, workload, source_ref, artifact_ref):
        value = self._mount_resolver.resolve_create_mounts(
            labels=labels, image=image, runtime=runtime, workload=workload,
            source_ref=source_ref, artifact_ref=artifact_ref,
        )
        resolved = ResolvedDockerMountsV1(
            *(getattr(value, name) for name in value.__dataclass_fields__)
        )
        if resolved.labels_digest != labels.digest or resolved.source_read_only is not True:
            raise ValueError
        return resolved

    def _translate(self, request):
        value = self._path_translator.translate(request)
        rebuilt = DockerWindowsPathV1(
            *(getattr(value, name) for name in value.__dataclass_fields__)
        )
        if (
            rebuilt.mapping_ref != request.mapping_ref
            or rebuilt.mapping_digest != request.expected_mapping_digest
            or rebuilt.distro != request.expected_distro
            or rebuilt.posix_path != request.posix_path
            or rebuilt.purpose is not request.purpose
        ):
            raise ValueError
        return rebuilt

    def _admitted(self, preflight):
        intent = preflight["auth_intent"]
        labels = preflight["labels"]
        content = DockerMutationRecordV1.build(
            operation_id=intent.content.operation_id,
            operation=DockerControlOperationV1.CREATE,
            effect_id=labels.effect_id,
            control_intent_proof_digest=intent.proof_digest,
            phase=DockerMutationPhaseV1.ADMITTED, revision=1,
            attempt_count=0, previous_record_digest=None,
            container_ref=None, verification_result_digest=None,
        )
        return self._issue(
            "record", self._record_authority, content,
            authenticate_mutation_record_v1,
        )

    def _attempted(self, admitted):
        content = admitted.content
        replacement = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=DockerMutationPhaseV1.ATTEMPTED, revision=2,
            attempt_count=1, previous_record_digest=content.record_digest,
            container_ref=None, verification_result_digest=None,
        )
        return self._issue(
            "record", self._record_authority, replacement,
            authenticate_mutation_record_v1,
        )

    @staticmethod
    def _record_matches(record, preflight):
        content = record.content
        return (
            content.operation is DockerControlOperationV1.CREATE
            and content.effect_id == preflight["labels"].effect_id
            and content.operation_id == preflight["operation_id"]
            and content.control_intent_proof_digest
            == preflight["auth_intent"].proof_digest
        )

    def _recover(
        self, preflight, current, create_result, *, working_directory,
        already_verified=False,
    ):
        if (
            create_result is not None
            and create_result.evidence.policy_digest != self._cli_policy_digest
        ):
            return _indeterminate()
        labels = preflight["labels"]
        inventory = _snapshot_typed(
            self._typed_runner.inventory_exact_name(labels.container_name),
            DockerExactNameInventoryResultV1, labels.container_name,
            self._cli_policy_digest,
        )
        if inventory.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
            return _indeterminate()
        refs = inventory.projection.container_refs
        if len(refs) > 1:
            return _collision()
        if not refs:
            return _indeterminate()
        container_ref = refs[0]
        if (
            create_result is not None
            and create_result.evidence.outcome is DockerCLIOutcomeV1.NONZERO_EXIT
        ):
            return _collision()
        if create_result is not None and create_result.projection.container_ref != container_ref:
            return _collision()
        post = self._preflight(
            labels, preflight["image"], preflight["runtime"],
            preflight["workload"], preflight["source_ref"],
            preflight["artifact_ref"],
            working_directory,
        )
        if (
            post["resolved"] != preflight["resolved"]
            or post["path_binding"] != preflight["path_binding"]
            or post["source_path"] != preflight["source_path"]
            or post["artifact_path"] != preflight["artifact_path"]
            or post["expected"] != preflight["expected"]
        ):
            return _indeterminate()
        inspected = _snapshot_typed(
            self._typed_runner.inspect_container(container_ref),
            DockerContainerInspectResultV1, container_ref,
            self._cli_policy_digest,
        )
        if inspected.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
            return _indeterminate()
        if not docker_create_projection_matches_v1(
            labels, preflight["expected"], preflight["environment"],
            inspected.projection, container_ref, inspected.evidence,
        ):
            return _collision()
        if already_verified:
            if current.content.container_ref != container_ref:
                return _collision()
            return DockerCreateResultV1(
                DockerCreateDispositionV1.CREATED, labels, container_ref
            )
        verification = DockerCreateVerificationV1.build(
            operation_id=current.content.operation_id,
            attempted_record_digest=current.content.record_digest,
            expected_proof_digest=preflight["expected"].proof_digest,
            create_result_digest=(
                None if create_result is None else create_result.result_digest
            ),
            inventory_result_digest=inventory.result_digest,
            post_resolution_digest=post["resolved"].resolution_digest,
            post_path_binding_proof_digest=post["path_binding"].proof_digest,
            source_windows_path_digest=post["source_path"].path_digest,
            source_unc_digest=sha256(post["source_path"].unc_path.encode()).hexdigest(),
            artifact_windows_path_digest=post["artifact_path"].path_digest,
            artifact_unc_digest=sha256(post["artifact_path"].unc_path.encode()).hexdigest(),
            inspect_result_digest=inspected.result_digest,
            container_ref=container_ref,
        )
        content = current.content
        verified_content = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=DockerMutationPhaseV1.VERIFIED, revision=3,
            attempt_count=1, previous_record_digest=content.record_digest,
            container_ref=container_ref,
            verification_result_digest=verification.verification_digest,
        )
        verified = self._issue(
            "record", self._record_authority, verified_content,
            authenticate_mutation_record_v1,
        )
        final_request = DockerMutationCASRequestV1.build(
            content.operation_id, current, verified
        )
        final_baseline = _cas_request_snapshot(final_request)
        try:
            raw_result = self._repository.compare_and_swap(
                _cas_request_snapshot(final_baseline)
            )
        except BaseException:
            raw_result = None
        if raw_result is None:
            raw_lookup = self._repository.lookup(content.operation_id)
            lookup = DockerMutationLookupResultV1(
                raw_lookup.operation_id, raw_lookup.disposition,
                raw_lookup.record, raw_lookup.result_digest,
            )
            if lookup.disposition is not DockerMutationLookupDispositionV1.FOUND:
                return _indeterminate()
            durable = self._auth(
                "record", self._record_authority, lookup.record,
                authenticate_mutation_record_v1,
            )
            if (
                self._record_matches(durable, preflight)
                and durable.content.phase is DockerMutationPhaseV1.VERIFIED
                and durable.content.container_ref == container_ref
            ):
                return DockerCreateResultV1(
                    DockerCreateDispositionV1.CREATED, labels, container_ref
                )
            return _indeterminate()
        result = DockerCASResultV1(
            raw_result.request, raw_result.disposition, raw_result.record,
            raw_result.result_digest,
        )
        if result.request != final_baseline:
            return _indeterminate()
        if result.disposition is DockerCASDispositionV1.APPLIED:
            durable = self._auth(
                "record", self._record_authority, result.record,
                authenticate_mutation_record_v1,
            )
            if (
                durable != verified
                or result.request.expected != final_baseline.expected
                or result.request.replacement != final_baseline.replacement
            ):
                return _indeterminate()
            return DockerCreateResultV1(
                DockerCreateDispositionV1.CREATED, labels, container_ref
            )
        if result.disposition is DockerCASDispositionV1.CURRENT:
            durable = self._auth(
                "record", self._record_authority, result.record,
                authenticate_mutation_record_v1,
            )
        else:
            raw_lookup = self._repository.lookup(content.operation_id)
            lookup = DockerMutationLookupResultV1(
                raw_lookup.operation_id, raw_lookup.disposition,
                raw_lookup.record, raw_lookup.result_digest,
            )
            if lookup.disposition is not DockerMutationLookupDispositionV1.FOUND:
                return _indeterminate()
            durable = self._auth(
                "record", self._record_authority, lookup.record,
                authenticate_mutation_record_v1,
            )
        if (
            self._record_matches(durable, preflight)
            and durable.content.phase is DockerMutationPhaseV1.VERIFIED
            and durable.content.container_ref == container_ref
        ):
            return DockerCreateResultV1(
                DockerCreateDispositionV1.CREATED, labels, container_ref
            )
        return _indeterminate()


__all__: tuple[str, ...] = ()
