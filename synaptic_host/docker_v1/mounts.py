from __future__ import annotations

from dataclasses import replace

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.coordinator_v1.model import ProviderExecutionBindingV1
from tuner.execution.foundation_v2.commands import SubmitCommandV2, parse_exact_command
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerCommandBindingV1,
    AuthenticatedDockerSourceSealV1,
    DockerCommandBindingV1,
    DockerEffectIdentityV1,
    DockerImageV1,
    DockerLabelsV1,
    DockerRuntimeV1,
    DockerSourceSealContentV1,
    DockerWorkloadV1,
    PreparedDockerPlanV1,
    labels_for,
    validated_profile_snapshot,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleMemberCommandV1,
    BundleMemberEvidenceV1,
    BundleMountVerificationV1,
    BundleSealCommandV1,
    digest_v1,
)
from synaptic_host.bundle_io_v1.ports import (
    BundleMountVerifyAccessV1,
)

from .model import (
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStageBundleBindingV1,
    AuthenticatedDockerStorageMappingV1,
    DockerMountCodeV1,
    DockerMountErrorV1,
    DockerSourceDeclarationV1,
    DockerStageBundleBindingV1,
    DockerStorageMappingV1,
    DockerStoragePurposeV1,
    ResolvedDockerMountsV1,
)


def _error(code: DockerMountCodeV1) -> DockerMountErrorV1:
    return DockerMountErrorV1(code)


def _execution_binding(profile) -> ProviderExecutionBindingV1:
    return ProviderExecutionBindingV1(
        profile.provider, profile.descriptor.descriptor_digest,
        profile.profile_digest, profile.scope, profile.executor_descriptor,
        profile.adapter_descriptor.digest, profile.resource_digest,
        profile.quote_digest, profile.secret_requirements_digest,
    )


class DockerSubmitMountResolverV1:
    def __init__(
        self, *, command_catalog, command_authority, stage_store,
        stage_record_authority, declaration_authority,
        binding_authority, source_seal_authority,
        mapping_registry, mapping_authority, bundle_verifier,
    ) -> None:
        self._command_catalog = command_catalog
        self._command_authority = command_authority
        self._stage_store = stage_store
        self._stage_record_authority = stage_record_authority
        self._declaration_authority = declaration_authority
        self._binding_authority = binding_authority
        self._source_seal_authority = source_seal_authority
        self._mapping_registry = mapping_registry
        self._mapping_authority = mapping_authority
        self._bundle_verifier = bundle_verifier
        try:
            refs = (
                command_authority.authority_ref, command_authority.key_ref,
                stage_record_authority.authority_ref,
                stage_record_authority.key_ref,
                declaration_authority.authority_ref, declaration_authority.key_ref,
                binding_authority.authority_ref, binding_authority.key_ref,
                source_seal_authority.authority_ref, source_seal_authority.key_ref,
                mapping_authority.authority_ref, mapping_authority.key_ref,
            )
            if any(type(value) is not str or not value for value in refs):
                raise ValueError
            self._pinned_refs = tuple(refs)
        except BaseException:
            raise _error(DockerMountCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_identity(value):
        try:
            if type(value) is not DockerEffectIdentityV1:
                raise ValueError
            plan = PreparedDockerPlanV1(
                value.plan.profile, value.plan.project_ref, value.plan.run_id,
                value.plan.plan_fingerprint, value.plan.source_digest,
                value.plan.preparation_digest,
            )
            rebuilt = DockerEffectIdentityV1(
                value.command_digest, value.effect_id, value.effect_kind, plan
            )
            if rebuilt != value or rebuilt.digest != value.digest:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @staticmethod
    def _snapshot_labels(value) -> DockerLabelsV1:
        try:
            if type(value) is not DockerLabelsV1:
                raise ValueError
            rebuilt = DockerLabelsV1(**value.to_dict())
            if rebuilt != value or rebuilt.digest != value.digest:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.COMMAND_INVALID) from None

    @staticmethod
    def _snapshot_inputs(image, runtime, workload):
        try:
            if (
                type(image) is not DockerImageV1
                or type(runtime) is not DockerRuntimeV1
                or type(workload) is not DockerWorkloadV1
            ):
                raise ValueError
            return (
                DockerImageV1(image.image_ref, image.image_digest, image.presence_policy),
                DockerRuntimeV1(
                    runtime.cpu_count, runtime.memory_bytes,
                    runtime.timeout_seconds,
                    AcceleratorDeviceRequestV1(
                        runtime.accelerator_devices.kind,
                        tuple(runtime.accelerator_devices.device_indices),
                        tuple(runtime.accelerator_devices.capabilities),
                    ),
                    runtime.network_mode,
                ),
                DockerWorkloadV1(
                    workload.arguments, workload.environment_keys,
                    workload.workload_digest,
                ),
            )
        except BaseException:
            raise _error(DockerMountCodeV1.COMMAND_INVALID) from None

    @staticmethod
    def _snapshot_command_binding(value):
        try:
            if type(value) is not AuthenticatedDockerCommandBindingV1:
                raise ValueError
            content = value.content
            if type(content) is not DockerCommandBindingV1:
                raise ValueError
            profile = validated_profile_snapshot(content.plan.profile)
            plan = PreparedDockerPlanV1(
                profile, content.plan.project_ref, content.plan.run_id,
                content.plan.plan_fingerprint, content.plan.source_digest,
                content.plan.preparation_digest,
            )
            identity = DockerEffectIdentityV1(
                content.identity.command_digest, content.identity.effect_id,
                content.identity.effect_kind, plan,
            )
            rebuilt_content = DockerCommandBindingV1(
                identity, bytes(content.command_bytes),
                content.original_submit_command_bytes,
                content.cancel_container_ref, content.cancel_reason_digest,
                content.cancel_submit_labels,
                content.cancel_authorization_digest,
            )
            rebuilt = AuthenticatedDockerCommandBindingV1(
                rebuilt_content, value.binding_digest, value.authority_ref,
                value.key_ref, value.tag,
            )
            if rebuilt != value or rebuilt_content.binding_digest != value.binding_digest:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_declaration(value):
        try:
            if type(value) is not AuthenticatedDockerSourceDeclarationV1:
                raise ValueError
            content = value.content
            members = tuple(replace(member) for member in content.members)
            rebuilt_content = DockerSourceDeclarationV1(
                content.source_ref, content.source_digest,
                content.effect_identity_digest, content.prepared_plan_digest,
                content.profile_ref, content.purpose_ref,
                content.destination_ref, content.root_authority_digest,
                content.bundle_access_digest, members,
                content.bundle_command_digest, content.declaration_digest,
            )
            rebuilt = AuthenticatedDockerSourceDeclarationV1(
                rebuilt_content, value.authority_ref, value.key_ref, value.tag
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @staticmethod
    def _snapshot_binding(value):
        try:
            if type(value) is not AuthenticatedBundleBindingV1:
                raise ValueError
            content = value.content
            members = tuple(
                BundleMemberEvidenceV1(
                    member.logical_name, member.physical_name, member.size,
                    member.sha256, replace(member.identity),
                )
                for member in content.members
            )
            rebuilt_content = BundleBindingV1(
                content.command_digest, content.destination_ref,
                content.root_authority_digest, content.private_name,
                content.marker_name, content.companion_name,
                content.manifest_digest, content.inventory_digest, members,
                replace(content.manifest_identity), replace(content.marker_identity),
                content.binding_digest,
            )
            rebuilt = AuthenticatedBundleBindingV1(
                rebuilt_content, value.authority_ref, value.key_ref, value.tag
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @staticmethod
    def _snapshot_seal(value):
        try:
            if type(value) is not AuthenticatedDockerSourceSealV1:
                raise ValueError
            content = value.content
            rebuilt = AuthenticatedDockerSourceSealV1(
                DockerSourceSealContentV1(
                    content.request_digest, content.effect_identity_digest,
                    content.source_ref, content.source_digest,
                    content.read_only, content.stage_ref,
                    content.evidence_digest,
                ),
                value.authority_ref, value.key_ref, value.tag,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @classmethod
    def _snapshot_stage(cls, value):
        try:
            if type(value) is not DockerStageBundleBindingV1:
                raise ValueError
            rebuilt = DockerStageBundleBindingV1(
                cls._snapshot_identity(value.effect_identity),
                value.stage_effect_id, value.stage_command_digest,
                value.effect_identity_digest, value.source_seal_request_digest,
                value.source_ref, value.source_digest,
                cls._snapshot_declaration(value.authenticated_declaration),
                value.authenticated_declaration_digest,
                value.bundle_command_digest, value.authenticated_binding_digest,
                value.stage_ref, cls._snapshot_binding(value.authenticated_binding),
                cls._snapshot_seal(value.source_seal),
                value.source_seal_digest, value.record_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @classmethod
    def _snapshot_stage_envelope(cls, value):
        try:
            if type(value) is not AuthenticatedDockerStageBundleBindingV1:
                raise ValueError
            rebuilt = AuthenticatedDockerStageBundleBindingV1(
                cls._snapshot_stage(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_CONFLICT) from None

    @staticmethod
    def _snapshot_mount_access(value):
        try:
            if type(value) is not BundleMountVerifyAccessV1:
                raise ValueError
            rebuilt = BundleMountVerifyAccessV1(
                value.destination_ref, value.root_authority_digest,
                value.verify_borrow, value.verify_root, value.access_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerMountCodeV1.MAPPING_CONFLICT) from None

    @staticmethod
    def _snapshot_mapping(value):
        try:
            if type(value) is not AuthenticatedDockerStorageMappingV1:
                raise ValueError
            content = value.content
            owned_access = (
                None if content.verify_access is None
                else DockerSubmitMountResolverV1._snapshot_mount_access(
                    content.verify_access
                )
            )
            rebuilt_content = DockerStorageMappingV1(
                content.mapping_ref, content.declared_ref, content.purpose,
                content.wsl_root, content.root_authority_digest,
                content.destination_ref, content.access_digest,
                owned_access, content.mapping_digest,
            )
            rebuilt = AuthenticatedDockerStorageMappingV1(
                rebuilt_content, value.authority_ref, value.key_ref, value.tag
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise _error(DockerMountCodeV1.MAPPING_CONFLICT) from None

    def _authenticate(self, value, authority, pair, snapshot, code):
        presented = snapshot(value)
        try:
            if (
                presented.authority_ref != pair[0]
                or presented.key_ref != pair[1]
            ):
                raise ValueError
            trusted = snapshot(authority.authenticate(presented))
            if trusted != presented:
                raise ValueError
            return trusted
        except BaseException:
            raise _error(code) from None

    def _resolve_command(self, labels):
        try:
            owned = self._command_catalog.resolve(labels.command_digest)
        except BaseException:
            raise _error(DockerMountCodeV1.AUTHENTICATION_FAILED) from None
        authenticated = self._authenticate(
            owned, self._command_authority, self._pinned_refs[0:2],
            self._snapshot_command_binding,
            DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        binding = authenticated.content
        try:
            command = parse_exact_command(binding.command_bytes)
            if type(command) is not SubmitCommandV2:
                raise ValueError
            profile = binding.plan.profile
            preparation = command.preparation
            if (
                command.digest != binding.command_digest
                or binding.effect_kind != "submit"
                or command.operation.effect.effect_id != binding.effect_id
                or command.operation.effect.kind.value != "submit"
                or preparation.preparation_digest
                != binding.plan.preparation_digest
                or preparation.provider != profile.provider
                or preparation.scope != profile.scope
                or preparation.project_ref != binding.plan.project_ref
                or preparation.run_id != binding.plan.run_id
                or preparation.plan_fingerprint
                != binding.plan.plan_fingerprint
                or preparation.source_digest != binding.plan.source_digest
                or preparation.workload_digest
                != profile.workload.workload_digest
                or preparation.runtime_digest != profile.runtime.digest
                or preparation.resource_digest != profile.resource_digest
                or preparation.artifact_contract_digest != profile.artifacts.digest
                or preparation.quote_digest != profile.quote_digest
                or preparation.secret_requirements_digest
                != profile.secret_requirements_digest
                or preparation.execution_binding_digest
                != _execution_binding(profile).binding_digest
                or command.payload.provider_id != profile.provider.provider_id
                or command.payload.payload_kind != "submit-payload/v2"
                or command.payload.input_digest != profile.workload.workload_digest
                or command.executor != profile.executor_descriptor
            ):
                raise ValueError
            return authenticated, command
        except BaseException:
            raise _error(DockerMountCodeV1.COMMAND_INVALID) from None

    def _resolve_stage(self, predecessor, binding):
        profile = binding.plan.profile
        if (
            predecessor.provider_id != profile.provider.provider_id
            or predecessor.profile_ref != profile.provider.profile_ref
            or predecessor.account_ref != profile.scope.account_ref
            or predecessor.namespace_ref != profile.scope.namespace_ref
            or predecessor.project_ref != binding.plan.project_ref
            or predecessor.run_id != binding.plan.run_id
            or predecessor.plan_fingerprint != binding.plan.plan_fingerprint
            or predecessor.preparation_digest != binding.plan.preparation_digest
            or predecessor.workload_digest != profile.workload.workload_digest
        ):
            raise _error(DockerMountCodeV1.STAGE_CONFLICT)
        try:
            raw = self._stage_store.get_by_stage_effect_id(
                predecessor.stage_effect_id
            )
        except BaseException:
            raise _error(DockerMountCodeV1.STAGE_INDETERMINATE) from None
        if raw is None:
            raise _error(DockerMountCodeV1.STAGE_INDETERMINATE)
        stage_envelope = self._authenticate(
            raw, self._stage_record_authority,
            self._pinned_refs[2:4], self._snapshot_stage_envelope,
            DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        stage = stage_envelope.content
        declaration = self._authenticate(
            stage.authenticated_declaration, self._declaration_authority,
            self._pinned_refs[4:6], self._snapshot_declaration,
            DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        bundle = self._authenticate(
            stage.authenticated_binding, self._binding_authority,
            self._pinned_refs[6:8], self._snapshot_binding,
            DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        seal = self._authenticate(
            stage.source_seal, self._source_seal_authority,
            self._pinned_refs[8:10], self._snapshot_seal,
            DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        content = declaration.content
        evidence = bundle.content
        if (
            stage.effect_identity.effect_kind != "stage"
            or stage.effect_identity.effect_id != predecessor.stage_effect_id
            or stage.effect_identity.command_digest
            != stage.stage_command_digest
            or stage.effect_identity.plan != binding.plan
            or stage.effect_identity.digest != stage.effect_identity_digest
            or stage.stage_effect_id != predecessor.stage_effect_id
            or content.prepared_plan_digest != binding.plan.digest
            or content.profile_ref != profile.provider.profile_ref
            or content.source_ref != profile.roots.source_ref
            or content.source_digest != binding.plan.source_digest
            or stage.source_ref != content.source_ref
            or stage.source_digest != content.source_digest
            or stage.effect_identity_digest != content.effect_identity_digest
            or stage.bundle_command_digest != content.bundle_command_digest
            or evidence.command_digest != content.bundle_command_digest
            or evidence.destination_ref != content.destination_ref
            or evidence.root_authority_digest != content.root_authority_digest
            or seal.content.effect_identity_digest != content.effect_identity_digest
            or seal.content.source_ref != content.source_ref
            or seal.content.source_digest != content.source_digest
            or seal.content.stage_ref != stage.stage_ref
            or seal.content.evidence_digest != bundle.proof_digest
            or stage.authenticated_binding_digest != bundle.proof_digest
        ):
            raise _error(DockerMountCodeV1.STAGE_CONFLICT)
        return stage, declaration, bundle

    def _resolve_mapping(self, *, source, declared_ref):
        try:
            raw = (
                self._mapping_registry.resolve_source(declared_ref)
                if source else self._mapping_registry.resolve_artifact(declared_ref)
            )
        except BaseException:
            raise _error(DockerMountCodeV1.MAPPING_INDETERMINATE) from None
        mapping = self._authenticate(
            raw, self._mapping_authority, self._pinned_refs[10:12],
            self._snapshot_mapping, DockerMountCodeV1.AUTHENTICATION_FAILED,
        )
        expected = (
            DockerStoragePurposeV1.SOURCE_BUNDLE
            if source else DockerStoragePurposeV1.ARTIFACT_OUTPUT
        )
        if mapping.content.purpose is not expected or mapping.content.declared_ref != declared_ref:
            raise _error(DockerMountCodeV1.MAPPING_CONFLICT)
        return mapping

    def resolve_create_mounts(
        self, *, labels, image, runtime, workload, source_ref, artifact_ref,
    ) -> ResolvedDockerMountsV1:
        labels = self._snapshot_labels(labels)
        image, runtime, workload = self._snapshot_inputs(image, runtime, workload)
        if type(source_ref) is not str or type(artifact_ref) is not str:
            raise _error(DockerMountCodeV1.COMMAND_INVALID)
        authenticated_command, command = self._resolve_command(labels)
        binding = authenticated_command.content
        profile = binding.plan.profile
        if (
            labels != labels_for(binding.identity)
            or image != profile.image
            or runtime != profile.runtime
            or workload != profile.workload
            or source_ref != profile.roots.source_ref
            or artifact_ref != profile.roots.artifact_ref
        ):
            raise _error(DockerMountCodeV1.COMMAND_INVALID)
        stage, declaration, bundle = self._resolve_stage(
            command.stage_predecessor, binding
        )
        source_mapping = self._resolve_mapping(source=True, declared_ref=source_ref)
        artifact_mapping = self._resolve_mapping(
            source=False, declared_ref=artifact_ref
        )
        source = source_mapping.content
        artifact = artifact_mapping.content
        verify_access = self._snapshot_mount_access(source.verify_access)
        if (
            source.destination_ref != declaration.content.destination_ref
            or source.root_authority_digest
            != declaration.content.root_authority_digest
            or source.access_digest
            != verify_access.access_digest
            or source.destination_ref != verify_access.destination_ref
            or source.root_authority_digest
            != verify_access.root_authority_digest
            or source.destination_ref != bundle.content.destination_ref
            or source.root_authority_digest
            != bundle.content.root_authority_digest
            or artifact.verify_access is not None
        ):
            raise _error(DockerMountCodeV1.MAPPING_CONFLICT)
        bundle_command = BundleSealCommandV1.build(
            declaration.content.profile_ref,
            declaration.content.purpose_ref,
            declaration.content.destination_ref,
            declaration.content.members,
        )
        try:
            verification = self._bundle_verifier.verify_mount(
                bundle_command, verify_access, bundle
            )
        except BundleIOErrorV1 as error:
            if error.code is BundleIOCodeV1.BOUND_EXCEEDED:
                raise _error(DockerMountCodeV1.BOUND_EXCEEDED) from None
            if error.code is BundleIOCodeV1.CONFLICT:
                raise _error(DockerMountCodeV1.VERIFICATION_CONFLICT) from None
            raise _error(DockerMountCodeV1.VERIFICATION_INDETERMINATE) from None
        except BaseException:
            raise _error(DockerMountCodeV1.VERIFICATION_INDETERMINATE) from None
        try:
            if type(verification) is not BundleMountVerificationV1:
                raise ValueError
            verification = replace(verification)
            expected_entries = tuple(
                (
                    member.logical_name, member.physical_name,
                    member.size, member.sha256,
                )
                for member in bundle.content.members
            )
            if (
                verification.command_digest != bundle_command.command_digest
                or verification.destination_ref != source.destination_ref
                or verification.root_authority_digest
                != source.root_authority_digest
                or verification.access_digest != source.access_digest
                or verification.binding_digest != bundle.content.binding_digest
                or verification.private_name != bundle.content.private_name
                or verification.manifest_digest != bundle.content.manifest_digest
                or verification.inventory_digest != bundle.content.inventory_digest
                or verification.logical_entries != expected_entries
                or verification.read_only is not True
            ):
                raise ValueError
        except BaseException:
            raise _error(DockerMountCodeV1.VERIFICATION_CONFLICT) from None
        body = {
            "artifact_mapping_digest": artifact_mapping.proof_digest,
            "artifact_wsl_root": artifact.wsl_root,
            "bundle_binding_digest": bundle.proof_digest,
            "command_binding_digest": authenticated_command.proof_digest,
            "labels_digest": labels.digest,
            "mount_verification_digest": verification.verification_digest,
            "schema_version": "synaptic-host-resolved-docker-mounts/v1",
            "source_mapping_digest": source_mapping.proof_digest,
            "source_read_only": True,
            "source_wsl_private_path": (
                source.wsl_root + "/" + bundle.content.private_name
            ),
            "stage_record_digest": stage.record_digest,
        }
        return ResolvedDockerMountsV1(
            body["source_wsl_private_path"], artifact.wsl_root,
            authenticated_command.proof_digest, labels.digest,
            stage.record_digest, source_mapping.proof_digest,
            artifact_mapping.proof_digest, bundle.proof_digest,
            verification.verification_digest, True, digest_v1(body),
        )


__all__: tuple[str, ...] = ()
