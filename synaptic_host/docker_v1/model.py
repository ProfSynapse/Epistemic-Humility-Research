from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerSourceSealV1,
    DockerSourceSealContentV1,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleIOCodeV1,
    BundleMemberCommandV1,
    checked_ref_v1,
    checked_sha_v1,
    digest_v1,
)


class DockerHostSourceCodeV1(str, Enum):
    REQUEST_INVALID = "DOCKER_HOST_SOURCE_REQUEST_INVALID"
    AUTHENTICATION_FAILED = "DOCKER_HOST_SOURCE_AUTHENTICATION_FAILED"
    DECLARATION_CONFLICT = "DOCKER_HOST_SOURCE_DECLARATION_CONFLICT"
    BUNDLE_CONFLICT = "DOCKER_HOST_SOURCE_BUNDLE_CONFLICT"
    BUNDLE_INDETERMINATE = "DOCKER_HOST_SOURCE_BUNDLE_INDETERMINATE"
    STORE_CONFLICT = "DOCKER_HOST_SOURCE_STORE_CONFLICT"
    STORE_INDETERMINATE = "DOCKER_HOST_SOURCE_STORE_INDETERMINATE"


class DockerHostSourceErrorV1(RuntimeError):
    def __init__(self, code: DockerHostSourceCodeV1) -> None:
        if type(code) is not DockerHostSourceCodeV1:
            raise TypeError("exact Docker host source code required")
        self.code = code
        super().__init__(code.value)


def _fail(code: DockerHostSourceCodeV1) -> None:
    raise DockerHostSourceErrorV1(code)


def docker_source_seal_digest_v1(value: AuthenticatedDockerSourceSealV1) -> str:
    if type(value) is not AuthenticatedDockerSourceSealV1:
        _fail(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
    try:
        return digest_v1({
            "authority_ref": value.authority_ref,
            "content_digest": value.content.content_digest,
            "key_ref": value.key_ref,
            "schema_version": "synaptic-host-docker-source-seal-envelope/v1",
            "tag": value.tag,
        })
    except BaseException:
        _fail(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)


@dataclass(frozen=True, slots=True)
class DockerSourceDeclarationV1:
    source_ref: str
    source_digest: str
    effect_identity_digest: str
    prepared_plan_digest: str
    profile_ref: str
    purpose_ref: str
    destination_ref: str
    root_authority_digest: str
    bundle_access_digest: str
    members: tuple[BundleMemberCommandV1, ...]
    bundle_command_digest: str
    declaration_digest: str

    def __post_init__(self) -> None:
        try:
            for value in (
                self.source_ref, self.profile_ref, self.purpose_ref,
                self.destination_ref,
            ):
                checked_ref_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            for value in (
                self.source_digest, self.effect_identity_digest,
                self.prepared_plan_digest, self.root_authority_digest,
                self.bundle_access_digest, self.bundle_command_digest,
                self.declaration_digest,
            ):
                checked_sha_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            if (
                type(self.members) is not tuple
                or not self.members
                or any(type(member) is not BundleMemberCommandV1 for member in self.members)
            ):
                raise ValueError
            names = tuple(member.logical_name for member in self.members)
            if names != tuple(sorted(names)) or len(names) != len(set(names)):
                raise ValueError
            from synaptic_host.bundle_io_v1.model import BundleSealCommandV1
            command = BundleSealCommandV1.build(
                self.profile_ref, self.purpose_ref, self.destination_ref,
                self.members,
            )
            if (
                command.command_digest != self.bundle_command_digest
                or self.declaration_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            _fail(DockerHostSourceCodeV1.DECLARATION_CONFLICT)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "bundle_access_digest": self.bundle_access_digest,
            "bundle_command_digest": self.bundle_command_digest,
            "destination_ref": self.destination_ref,
            "effect_identity_digest": self.effect_identity_digest,
            "members": [member.canonical() for member in self.members],
            "prepared_plan_digest": self.prepared_plan_digest,
            "profile_ref": self.profile_ref,
            "purpose_ref": self.purpose_ref,
            "root_authority_digest": self.root_authority_digest,
            "schema_version": "synaptic-host-docker-source-declaration/v1",
            "source_digest": self.source_digest,
            "source_ref": self.source_ref,
        }

    @classmethod
    def build(
        cls, *, source_ref, source_digest, effect_identity_digest,
        prepared_plan_digest, profile_ref, purpose_ref, destination_ref,
        root_authority_digest, bundle_access_digest, members,
    ):
        from synaptic_host.bundle_io_v1.model import BundleSealCommandV1
        command = BundleSealCommandV1.build(
            profile_ref, purpose_ref, destination_ref, members
        )
        body = {
            "bundle_access_digest": bundle_access_digest,
            "bundle_command_digest": command.command_digest,
            "destination_ref": destination_ref,
            "effect_identity_digest": effect_identity_digest,
            "members": [member.canonical() for member in members],
            "prepared_plan_digest": prepared_plan_digest,
            "profile_ref": profile_ref,
            "purpose_ref": purpose_ref,
            "root_authority_digest": root_authority_digest,
            "schema_version": "synaptic-host-docker-source-declaration/v1",
            "source_digest": source_digest,
            "source_ref": source_ref,
        }
        return cls(
            source_ref, source_digest, effect_identity_digest,
            prepared_plan_digest, profile_ref, purpose_ref, destination_ref,
            root_authority_digest, bundle_access_digest, members,
            command.command_digest, digest_v1(body),
        )


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerSourceDeclarationV1:
    content: DockerSourceDeclarationV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self) -> None:
        try:
            if type(self.content) is not DockerSourceDeclarationV1:
                raise ValueError
            checked_ref_v1(self.authority_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.key_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(self.tag, BundleIOCodeV1.COMMAND_INVALID)
        except BaseException:
            _fail(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)

    @property
    def proof_digest(self) -> str:
        return digest_v1({
            "authority_ref": self.authority_ref,
            "declaration_digest": self.content.declaration_digest,
            "key_ref": self.key_ref,
            "schema_version": "synaptic-host-authenticated-docker-source-declaration/v1",
            "tag": self.tag,
        })


@dataclass(frozen=True, slots=True)
class DockerStageBundleBindingV1:
    stage_effect_id: str
    stage_command_digest: str
    effect_identity_digest: str
    source_seal_request_digest: str
    source_ref: str
    source_digest: str
    authenticated_declaration: AuthenticatedDockerSourceDeclarationV1
    authenticated_declaration_digest: str
    bundle_command_digest: str
    authenticated_binding_digest: str
    stage_ref: str
    authenticated_binding: AuthenticatedBundleBindingV1
    source_seal: AuthenticatedDockerSourceSealV1
    source_seal_digest: str
    record_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.stage_effect_id, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.source_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.stage_ref, BundleIOCodeV1.COMMAND_INVALID)
            for value in (
                self.stage_command_digest, self.effect_identity_digest,
                self.source_seal_request_digest, self.source_digest,
                self.authenticated_declaration_digest,
                self.bundle_command_digest, self.authenticated_binding_digest,
                self.source_seal_digest, self.record_digest,
            ):
                checked_sha_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            if (
                type(self.authenticated_declaration)
                is not AuthenticatedDockerSourceDeclarationV1
                or self.authenticated_declaration.proof_digest
                != self.authenticated_declaration_digest
                or type(self.authenticated_binding) is not AuthenticatedBundleBindingV1
                or type(self.source_seal) is not AuthenticatedDockerSourceSealV1
                or type(self.source_seal.content) is not DockerSourceSealContentV1
                or self.authenticated_binding.proof_digest
                != self.authenticated_binding_digest
                or self.authenticated_binding.content.command_digest
                != self.bundle_command_digest
                or self.source_seal_digest
                != docker_source_seal_digest_v1(self.source_seal)
                or self.stage_ref != "bundle-" + self.authenticated_binding_digest
            ):
                raise ValueError
            content = self.source_seal.content
            if (
                content.request_digest != self.source_seal_request_digest
                or content.effect_identity_digest != self.effect_identity_digest
                or content.source_ref != self.source_ref
                or content.source_digest != self.source_digest
                or content.read_only is not True
                or content.stage_ref != self.stage_ref
                or content.evidence_digest != self.authenticated_binding_digest
                or self.record_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            _fail(DockerHostSourceCodeV1.STORE_CONFLICT)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "authenticated_binding_digest": self.authenticated_binding_digest,
            "authenticated_declaration_digest": self.authenticated_declaration_digest,
            "bundle_command_digest": self.bundle_command_digest,
            "effect_identity_digest": self.effect_identity_digest,
            "schema_version": "synaptic-host-docker-stage-bundle-binding/v1",
            "source_digest": self.source_digest,
            "source_ref": self.source_ref,
            "source_seal_digest": self.source_seal_digest,
            "source_seal_request_digest": self.source_seal_request_digest,
            "stage_command_digest": self.stage_command_digest,
            "stage_effect_id": self.stage_effect_id,
            "stage_ref": self.stage_ref,
        }

    @classmethod
    def build(
        cls, *, stage_effect_id, stage_command_digest,
        effect_identity_digest, source_seal_request_digest, source_ref,
        source_digest, authenticated_declaration,
        bundle_command_digest, authenticated_binding, source_seal,
    ):
        declaration_digest = authenticated_declaration.proof_digest
        binding_digest = authenticated_binding.proof_digest
        seal_digest = docker_source_seal_digest_v1(source_seal)
        stage_ref = "bundle-" + binding_digest
        body = {
            "authenticated_binding_digest": binding_digest,
            "authenticated_declaration_digest": declaration_digest,
            "bundle_command_digest": bundle_command_digest,
            "effect_identity_digest": effect_identity_digest,
            "schema_version": "synaptic-host-docker-stage-bundle-binding/v1",
            "source_digest": source_digest,
            "source_ref": source_ref,
            "source_seal_digest": seal_digest,
            "source_seal_request_digest": source_seal_request_digest,
            "stage_command_digest": stage_command_digest,
            "stage_effect_id": stage_effect_id,
            "stage_ref": stage_ref,
        }
        return cls(
            stage_effect_id, stage_command_digest, effect_identity_digest,
            source_seal_request_digest, source_ref, source_digest,
            authenticated_declaration, declaration_digest,
            bundle_command_digest,
            binding_digest, stage_ref, authenticated_binding, source_seal,
            seal_digest, digest_v1(body),
        )


__all__: tuple[str, ...] = ()
