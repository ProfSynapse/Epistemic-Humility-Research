from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerSourceSealV1,
    DockerEffectIdentityV1,
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
from synaptic_host.bundle_io_v1.ports import (
    BundleMountVerifyAccessV1,
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
    effect_identity: DockerEffectIdentityV1
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
            if (
                type(self.effect_identity) is not DockerEffectIdentityV1
                or self.effect_identity.effect_kind != "stage"
                or self.effect_identity.effect_id != self.stage_effect_id
                or self.effect_identity.command_digest != self.stage_command_digest
                or self.effect_identity.digest != self.effect_identity_digest
            ):
                raise ValueError
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
        cls, *, effect_identity,
        source_seal_request_digest, source_ref,
        source_digest, authenticated_declaration,
        bundle_command_digest, authenticated_binding, source_seal,
    ):
        if type(effect_identity) is not DockerEffectIdentityV1:
            _fail(DockerHostSourceCodeV1.STORE_CONFLICT)
        stage_effect_id = effect_identity.effect_id
        stage_command_digest = effect_identity.command_digest
        effect_identity_digest = effect_identity.digest
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
            effect_identity,
            stage_effect_id, stage_command_digest, effect_identity_digest,
            source_seal_request_digest, source_ref, source_digest,
            authenticated_declaration, declaration_digest,
            bundle_command_digest,
            binding_digest, stage_ref, authenticated_binding, source_seal,
            seal_digest, digest_v1(body),
        )


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerStageBundleBindingV1:
    content: DockerStageBundleBindingV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self) -> None:
        try:
            if type(self.content) is not DockerStageBundleBindingV1:
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
            "effect_identity_digest": self.content.effect_identity_digest,
            "key_ref": self.key_ref,
            "record_digest": self.content.record_digest,
            "schema_version": "synaptic-host-authenticated-docker-stage-bundle/v1",
            "stage_command_digest": self.content.stage_command_digest,
            "stage_effect_id": self.content.stage_effect_id,
            "tag": self.tag,
        })


class DockerMountCodeV1(str, Enum):
    COMMAND_INVALID = "DOCKER_HOST_MOUNT_COMMAND_INVALID"
    AUTHENTICATION_FAILED = "DOCKER_HOST_MOUNT_AUTHENTICATION_FAILED"
    STAGE_CONFLICT = "DOCKER_HOST_MOUNT_STAGE_CONFLICT"
    STAGE_INDETERMINATE = "DOCKER_HOST_MOUNT_STAGE_INDETERMINATE"
    MAPPING_CONFLICT = "DOCKER_HOST_MOUNT_MAPPING_CONFLICT"
    MAPPING_INDETERMINATE = "DOCKER_HOST_MOUNT_MAPPING_INDETERMINATE"
    VERIFICATION_CONFLICT = "DOCKER_HOST_MOUNT_VERIFICATION_CONFLICT"
    VERIFICATION_INDETERMINATE = "DOCKER_HOST_MOUNT_VERIFICATION_INDETERMINATE"
    BOUND_EXCEEDED = "DOCKER_HOST_MOUNT_BOUND_EXCEEDED"


class DockerMountErrorV1(RuntimeError):
    def __init__(self, code: DockerMountCodeV1) -> None:
        if type(code) is not DockerMountCodeV1:
            raise TypeError("exact Docker mount code required")
        self.code = code
        super().__init__(code.value)


class DockerStoragePurposeV1(str, Enum):
    SOURCE_BUNDLE = "source_bundle"
    ARTIFACT_OUTPUT = "artifact_output"


def _wsl_root_v1(value: object) -> str:
    if type(value) is not str or not 1 <= len(value.encode("utf-8")) <= 4096:
        raise DockerMountErrorV1(DockerMountCodeV1.BOUND_EXCEEDED)
    if value != unicodedata.normalize("NFC", value) or not value.startswith("/"):
        raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT)
    components = value.split("/")[1:]
    if (
        not components
        or any(
            not component
            or component in {".", ".."}
            or len(component.encode("utf-8")) > 240
            or any(unicodedata.category(character)[0] == "C" for character in component)
            for component in components
        )
    ):
        raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT)
    return value


@dataclass(frozen=True, slots=True)
class DockerStorageMappingV1:
    mapping_ref: str
    declared_ref: str
    purpose: DockerStoragePurposeV1
    wsl_root: str
    root_authority_digest: str
    destination_ref: str
    access_digest: str
    verify_access: BundleMountVerifyAccessV1 | None
    mapping_digest: str

    def __post_init__(self) -> None:
        try:
            for value in (self.mapping_ref, self.declared_ref, self.destination_ref):
                checked_ref_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(
                self.root_authority_digest, BundleIOCodeV1.COMMAND_INVALID
            )
            checked_sha_v1(self.access_digest, BundleIOCodeV1.COMMAND_INVALID)
            _wsl_root_v1(self.wsl_root)
            if type(self.purpose) is not DockerStoragePurposeV1:
                raise ValueError
            source = self.purpose is DockerStoragePurposeV1.SOURCE_BUNDLE
            if source != (type(self.verify_access) is BundleMountVerifyAccessV1):
                raise ValueError
            if source and (
                self.verify_access.destination_ref != self.destination_ref
                or self.verify_access.root_authority_digest
                != self.root_authority_digest
                or self.verify_access.access_digest != self.access_digest
            ):
                raise ValueError
            if self.mapping_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise DockerMountErrorV1(
                DockerMountCodeV1.MAPPING_CONFLICT
            ) from None

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "access_digest": self.access_digest,
            "declared_ref": self.declared_ref,
            "destination_ref": self.destination_ref,
            "mapping_ref": self.mapping_ref,
            "purpose": self.purpose.value,
            "root_authority_digest": self.root_authority_digest,
            "schema_version": "synaptic-host-docker-storage-mapping/v1",
            "verify_access_digest": (
                None if self.verify_access is None
                else self.verify_access.access_digest
            ),
            "wsl_root": self.wsl_root,
        }

    @classmethod
    def build(
        cls, *, mapping_ref, declared_ref, purpose, wsl_root,
        root_authority_digest, destination_ref, access_digest,
        verify_access=None,
    ):
        body = {
            "access_digest": access_digest,
            "declared_ref": declared_ref,
            "destination_ref": destination_ref,
            "mapping_ref": mapping_ref,
            "purpose": purpose.value,
            "root_authority_digest": root_authority_digest,
            "schema_version": "synaptic-host-docker-storage-mapping/v1",
            "verify_access_digest": (
                None if verify_access is None else verify_access.access_digest
            ),
            "wsl_root": wsl_root,
        }
        return cls(
            mapping_ref, declared_ref, purpose, wsl_root,
            root_authority_digest, destination_ref, access_digest,
            verify_access, digest_v1(body),
        )


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerStorageMappingV1:
    content: DockerStorageMappingV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self) -> None:
        try:
            if type(self.content) is not DockerStorageMappingV1:
                raise ValueError
            checked_ref_v1(self.authority_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.key_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(self.tag, BundleIOCodeV1.COMMAND_INVALID)
        except BaseException:
            raise DockerMountErrorV1(
                DockerMountCodeV1.AUTHENTICATION_FAILED
            ) from None

    @property
    def proof_digest(self) -> str:
        return digest_v1({
            "authority_ref": self.authority_ref,
            "key_ref": self.key_ref,
            "mapping_digest": self.content.mapping_digest,
            "schema_version": "synaptic-host-authenticated-docker-storage-mapping/v1",
            "tag": self.tag,
        })


@dataclass(frozen=True, slots=True)
class ResolvedDockerMountsV1:
    source_wsl_private_path: str
    artifact_wsl_root: str
    command_binding_digest: str
    labels_digest: str
    stage_record_digest: str
    source_mapping_digest: str
    artifact_mapping_digest: str
    bundle_binding_digest: str
    mount_verification_digest: str
    source_read_only: bool
    resolution_digest: str

    def __post_init__(self) -> None:
        try:
            _wsl_root_v1(self.source_wsl_private_path)
            _wsl_root_v1(self.artifact_wsl_root)
            for value in (
                self.command_binding_digest, self.labels_digest,
                self.stage_record_digest, self.source_mapping_digest,
                self.artifact_mapping_digest, self.bundle_binding_digest,
                self.mount_verification_digest, self.resolution_digest,
            ):
                checked_sha_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            if (
                self.source_read_only is not True
                or self.resolution_digest
                != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise DockerMountErrorV1(DockerMountCodeV1.STAGE_CONFLICT) from None

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "artifact_mapping_digest": self.artifact_mapping_digest,
            "artifact_wsl_root": self.artifact_wsl_root,
            "bundle_binding_digest": self.bundle_binding_digest,
            "command_binding_digest": self.command_binding_digest,
            "labels_digest": self.labels_digest,
            "mount_verification_digest": self.mount_verification_digest,
            "schema_version": "synaptic-host-resolved-docker-mounts/v1",
            "source_mapping_digest": self.source_mapping_digest,
            "source_read_only": self.source_read_only,
            "source_wsl_private_path": self.source_wsl_private_path,
            "stage_record_digest": self.stage_record_digest,
        }


MAX_WSL_PATH_BYTES_V1 = 4096
MAX_WSL_COMPONENT_BYTES_V1 = 240
MAX_DOCKER_ARG_BYTES_V1 = 4096
MAX_DOCKER_ARGS_V1 = 256
MAX_DOCKER_STREAM_BYTES_V1 = 1_048_576
MAX_DOCKER_COMBINED_BYTES_V1 = 2_097_152
MAX_WINDOWS_PATH_BYTES_V1 = 4096


class DockerPlatformCodeV1(str, Enum):
    PATH_INVALID = "DOCKER_PLATFORM_PATH_INVALID"
    ROOT_UNREGISTERED = "DOCKER_PLATFORM_ROOT_UNREGISTERED"
    AUTHENTICATION_FAILED = "DOCKER_PLATFORM_AUTHENTICATION_FAILED"
    POLICY_INVALID = "DOCKER_PLATFORM_POLICY_INVALID"
    COMMAND_INVALID = "DOCKER_PLATFORM_COMMAND_INVALID"
    SPAWN_INDETERMINATE = "DOCKER_PLATFORM_SPAWN_INDETERMINATE"
    IO_INDETERMINATE = "DOCKER_PLATFORM_IO_INDETERMINATE"
    TIMEOUT = "DOCKER_PLATFORM_TIMEOUT"
    OUTPUT_BOUND_EXCEEDED = "DOCKER_PLATFORM_OUTPUT_BOUND_EXCEEDED"
    TERMINATION_INDETERMINATE = "DOCKER_PLATFORM_TERMINATION_INDETERMINATE"
    OUTPUT_INVALID = "DOCKER_PLATFORM_OUTPUT_INVALID"


class DockerPlatformErrorV1(RuntimeError):
    def __init__(self, code: DockerPlatformCodeV1) -> None:
        if type(code) is not DockerPlatformCodeV1:
            raise TypeError("exact Docker platform code required")
        self.code = code
        super().__init__(code.value)


def _platform_fail(code: DockerPlatformCodeV1) -> None:
    raise DockerPlatformErrorV1(code) from None


class DockerWSLPathPurposeV1(str, Enum):
    SOURCE_READ = "SOURCE_READ"
    ARTIFACT_WRITE = "ARTIFACT_WRITE"


def canonical_wsl_path_v1(value: str) -> str:
    try:
        if (
            type(value) is not str
            or not value.startswith("/")
            or value == "/"
            or value.endswith("/")
            or "//" in value
            or "\\" in value
            or unicodedata.normalize("NFC", value) != value
            or len(value.encode("utf-8")) > MAX_WSL_PATH_BYTES_V1
        ):
            raise ValueError
        parts = value[1:].split("/")
        if not parts or len(parts) > 128:
            raise ValueError
        for part in parts:
            if (
                part in ("", ".", "..")
                or len(part.encode("utf-8")) > MAX_WSL_COMPONENT_BYTES_V1
                or any(ord(char) < 32 or ord(char) == 127 for char in part)
            ):
                raise ValueError
        return value
    except BaseException:
        _platform_fail(DockerPlatformCodeV1.PATH_INVALID)


def _distro_v1(value: str) -> str:
    try:
        if (
            type(value) is not str
            or not 1 <= len(value) <= 64
            or not value[0].isalnum()
            or any(not (char.isascii() and (char.isalnum() or char in "._-")) for char in value)
        ):
            raise ValueError
        return value
    except BaseException:
        _platform_fail(DockerPlatformCodeV1.PATH_INVALID)


@dataclass(frozen=True, slots=True)
class DockerWSLRootMappingV1:
    mapping_ref: str
    distro: str
    purpose: DockerWSLPathPurposeV1
    posix_root: str
    mapping_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.mapping_ref, BundleIOCodeV1.COMMAND_INVALID)
            _distro_v1(self.distro)
            if type(self.purpose) is not DockerWSLPathPurposeV1:
                raise ValueError
            canonical_wsl_path_v1(self.posix_root)
            checked_sha_v1(self.mapping_digest, BundleIOCodeV1.COMMAND_INVALID)
            if self.mapping_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.PATH_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "distro": self.distro,
            "mapping_ref": self.mapping_ref,
            "posix_root": self.posix_root,
            "purpose": self.purpose.value,
            "schema_version": "synaptic-host-docker-wsl-root-mapping/v1",
        }

    @classmethod
    def build(cls, mapping_ref, distro, purpose, posix_root):
        try:
            if type(purpose) is not DockerWSLPathPurposeV1:
                raise ValueError
            body = {
                "distro": distro, "mapping_ref": mapping_ref,
                "posix_root": posix_root, "purpose": purpose.value,
                "schema_version": "synaptic-host-docker-wsl-root-mapping/v1",
            }
            return cls(mapping_ref, distro, purpose, posix_root, digest_v1(body))
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.PATH_INVALID)


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerWSLRootMappingV1:
    content: DockerWSLRootMappingV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self) -> None:
        try:
            if type(self.content) is not DockerWSLRootMappingV1:
                raise ValueError
            checked_ref_v1(self.authority_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.key_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(self.tag, BundleIOCodeV1.COMMAND_INVALID)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.AUTHENTICATION_FAILED)

    @property
    def proof_digest(self) -> str:
        return digest_v1({
            "authority_ref": self.authority_ref,
            "key_ref": self.key_ref,
            "mapping_digest": self.content.mapping_digest,
            "schema_version": "synaptic-host-authenticated-docker-wsl-root-mapping/v1",
            "tag": self.tag,
        })


def _storage_mapping_snapshot_v1(
    value: AuthenticatedDockerStorageMappingV1,
) -> AuthenticatedDockerStorageMappingV1:
    try:
        if type(value) is not AuthenticatedDockerStorageMappingV1:
            raise ValueError
        content = value.content
        if type(content) is not DockerStorageMappingV1:
            raise ValueError
        access = content.verify_access
        if access is not None:
            if type(access) is not BundleMountVerifyAccessV1:
                raise ValueError
            access = BundleMountVerifyAccessV1(
                access.destination_ref,
                access.root_authority_digest,
                access.verify_borrow,
                access.verify_root,
                access.access_digest,
            )
        rebuilt_content = DockerStorageMappingV1(
            content.mapping_ref,
            content.declared_ref,
            content.purpose,
            content.wsl_root,
            content.root_authority_digest,
            content.destination_ref,
            content.access_digest,
            access,
            content.mapping_digest,
        )
        rebuilt = AuthenticatedDockerStorageMappingV1(
            rebuilt_content, value.authority_ref, value.key_ref, value.tag
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT) from None


def _wsl_mapping_snapshot_v1(
    value: AuthenticatedDockerWSLRootMappingV1,
) -> AuthenticatedDockerWSLRootMappingV1:
    try:
        if type(value) is not AuthenticatedDockerWSLRootMappingV1:
            raise ValueError
        content = value.content
        rebuilt_content = DockerWSLRootMappingV1(
            content.mapping_ref,
            content.distro,
            content.purpose,
            content.posix_root,
            content.mapping_digest,
        )
        rebuilt = AuthenticatedDockerWSLRootMappingV1(
            rebuilt_content, value.authority_ref, value.key_ref, value.tag
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT) from None


@dataclass(frozen=True, slots=True)
class DockerStoragePathMappingPairV1:
    """Structurally adjacent storage and WSL mappings.

    Construction validates shape and live capability identity only. It does not
    authenticate either nested envelope; that belongs to the pair authority.
    """

    storage_mapping: AuthenticatedDockerStorageMappingV1
    wsl_mapping: AuthenticatedDockerWSLRootMappingV1
    pair_digest: str

    def __post_init__(self) -> None:
        try:
            storage = _storage_mapping_snapshot_v1(self.storage_mapping)
            wsl = _wsl_mapping_snapshot_v1(self.wsl_mapping)
            storage_content = storage.content
            wsl_content = wsl.content
            source = (
                storage_content.purpose is DockerStoragePurposeV1.SOURCE_BUNDLE
            )
            if (
                storage_content.mapping_ref != wsl_content.mapping_ref
                or storage_content.wsl_root != wsl_content.posix_root
                or source
                != (wsl_content.purpose is DockerWSLPathPurposeV1.SOURCE_READ)
                or (not source)
                != (wsl_content.purpose is DockerWSLPathPurposeV1.ARTIFACT_WRITE)
                or source
                != (type(storage_content.verify_access) is BundleMountVerifyAccessV1)
                or self.pair_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
            if source:
                original_access = self.storage_mapping.content.verify_access
                rebuilt_access = storage_content.verify_access
                if (
                    rebuilt_access.verify_borrow is not original_access.verify_borrow
                    or rebuilt_access.verify_root is not original_access.verify_root
                ):
                    raise ValueError
            object.__setattr__(self, "storage_mapping", storage)
            object.__setattr__(self, "wsl_mapping", wsl)
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT) from None

    def canonical_without_digest(self) -> dict[str, object]:
        storage = self.storage_mapping.content
        wsl = self.wsl_mapping.content
        return {
            "declared_ref": storage.declared_ref,
            "distro": wsl.distro,
            "mapping_ref": storage.mapping_ref,
            "root": storage.wsl_root,
            "schema_version": "synaptic-host-docker-storage-path-mapping-pair/v1",
            "storage_mapping_digest": storage.mapping_digest,
            "storage_mapping_proof_digest": self.storage_mapping.proof_digest,
            "storage_purpose": storage.purpose.value,
            "verify_access_digest": (
                None if storage.verify_access is None
                else storage.verify_access.access_digest
            ),
            "wsl_mapping_digest": wsl.mapping_digest,
            "wsl_mapping_proof_digest": self.wsl_mapping.proof_digest,
            "wsl_purpose": wsl.purpose.value,
        }

    @classmethod
    def build(cls, storage_mapping, wsl_mapping):
        try:
            temporary = cls.__new__(cls)
            object.__setattr__(temporary, "storage_mapping", storage_mapping)
            object.__setattr__(temporary, "wsl_mapping", wsl_mapping)
            object.__setattr__(temporary, "pair_digest", "0" * 64)
            body = temporary.canonical_without_digest()
            return cls(storage_mapping, wsl_mapping, digest_v1(body))
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise DockerMountErrorV1(DockerMountCodeV1.MAPPING_CONFLICT) from None


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerStoragePathMappingPairV1:
    content: DockerStoragePathMappingPairV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self) -> None:
        try:
            if type(self.content) is not DockerStoragePathMappingPairV1:
                raise ValueError
            rebuilt = DockerStoragePathMappingPairV1(
                self.content.storage_mapping,
                self.content.wsl_mapping,
                self.content.pair_digest,
            )
            if rebuilt != self.content:
                raise ValueError
            checked_ref_v1(self.authority_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(self.key_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(self.tag, BundleIOCodeV1.COMMAND_INVALID)
            object.__setattr__(self, "content", rebuilt)
        except DockerMountErrorV1:
            raise
        except BaseException:
            raise DockerMountErrorV1(
                DockerMountCodeV1.AUTHENTICATION_FAILED
            ) from None

    @property
    def proof_digest(self) -> str:
        return digest_v1({
            "authority_ref": self.authority_ref,
            "key_ref": self.key_ref,
            "pair_digest": self.content.pair_digest,
            "schema_version": (
                "synaptic-host-authenticated-docker-storage-path-mapping-pair/v1"
            ),
            "tag": self.tag,
        })


@dataclass(frozen=True, slots=True)
class DockerWSLPathRequestV1:
    mapping_ref: str
    expected_mapping_digest: str
    expected_distro: str
    purpose: DockerWSLPathPurposeV1
    posix_path: str
    request_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.mapping_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(
                self.expected_mapping_digest, BundleIOCodeV1.COMMAND_INVALID
            )
            _distro_v1(self.expected_distro)
            if type(self.purpose) is not DockerWSLPathPurposeV1:
                raise ValueError
            canonical_wsl_path_v1(self.posix_path)
            if self.request_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.PATH_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "expected_distro": self.expected_distro,
            "expected_mapping_digest": self.expected_mapping_digest,
            "mapping_ref": self.mapping_ref,
            "posix_path": self.posix_path,
            "purpose": self.purpose.value,
            "schema_version": "synaptic-host-docker-wsl-path-request/v1",
        }

    @classmethod
    def build(
        cls, *, mapping_ref, expected_mapping_digest, expected_distro,
        purpose, posix_path,
    ):
        try:
            if type(purpose) is not DockerWSLPathPurposeV1:
                raise ValueError
            body = {
                "expected_distro": expected_distro,
                "expected_mapping_digest": expected_mapping_digest,
                "mapping_ref": mapping_ref,
                "posix_path": posix_path,
                "purpose": purpose.value,
                "schema_version": "synaptic-host-docker-wsl-path-request/v1",
            }
            return cls(
                mapping_ref, expected_mapping_digest, expected_distro,
                purpose, posix_path, digest_v1(body),
            )
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.PATH_INVALID)


@dataclass(frozen=True, slots=True)
class DockerWindowsPathV1:
    mapping_ref: str
    mapping_digest: str
    purpose: DockerWSLPathPurposeV1
    distro: str
    posix_path: str
    unc_path: str
    path_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.mapping_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(self.mapping_digest, BundleIOCodeV1.COMMAND_INVALID)
            if type(self.purpose) is not DockerWSLPathPurposeV1:
                raise ValueError
            _distro_v1(self.distro)
            canonical_wsl_path_v1(self.posix_path)
            expected = "\\\\wsl.localhost\\" + self.distro + self.posix_path.replace("/", "\\")
            if self.unc_path != expected or self.path_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.PATH_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "distro": self.distro, "mapping_digest": self.mapping_digest,
            "mapping_ref": self.mapping_ref, "posix_path": self.posix_path,
            "purpose": self.purpose.value,
            "schema_version": "synaptic-host-docker-windows-path/v1",
            "unc_path": self.unc_path,
        }


class DockerCLIVerbV1(str, Enum):
    VERSION = "version"
    CREATE = "create"
    START = "start"
    STOP = "stop"
    INSPECT = "inspect"
    PS = "ps"
    LOGS = "logs"


def _argv_token_v1(value: str) -> str:
    try:
        if (
            type(value) is not str or not value
            or unicodedata.normalize("NFC", value) != value
            or len(value.encode("utf-8")) > MAX_DOCKER_ARG_BYTES_V1
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError
        return value
    except BaseException:
        _platform_fail(DockerPlatformCodeV1.COMMAND_INVALID)


def _windows_drive_path_v1(value: str) -> str:
    """Validate the exact uppercase-drive Windows path used for process policy."""
    try:
        if (
            type(value) is not str
            or len(value) < 3
            or not (
                value[0].isascii()
                and value[0].isalpha()
                and value[0].isupper()
            )
            or value[1:3] != ":\\"
            or "/" in value
            or unicodedata.normalize("NFC", value) != value
            or len(value.encode("utf-8")) > MAX_WINDOWS_PATH_BYTES_V1
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError
        components = value[3:].split("\\") if len(value) > 3 else []
        reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
        reserved.update({f"COM{number}" for number in range(1, 10)})
        reserved.update({f"LPT{number}" for number in range(1, 10)})
        reserved.update({f"COM{number}" for number in "\u00b9\u00b2\u00b3"})
        reserved.update({f"LPT{number}" for number in "\u00b9\u00b2\u00b3"})
        for component in components:
            base_name = component.split(".", 1)[0].rstrip(" .").upper()
            if (
                component in ("", ".", "..")
                or component.endswith((" ", "."))
                or any(char in '<>:"|?*' for char in component)
                or base_name in reserved
            ):
                raise ValueError
        return value
    except BaseException:
        _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)


def _docker_desktop_wsl_executable_v1(value: str) -> str:
    """Accept Docker Desktop's exact WSL-integrated Windows CLI proxy."""

    try:
        if value == "/Docker/host/bin/docker.exe":
            return value
        checked = _windows_drive_path_v1(value)
        if not checked.lower().endswith(".exe"):
            raise ValueError
        return checked
    except DockerPlatformErrorV1:
        raise
    except BaseException:
        _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)


@dataclass(frozen=True, slots=True)
class DockerCLICommandV1:
    verb: DockerCLIVerbV1
    arguments: tuple[str, ...]
    command_digest: str

    def __post_init__(self) -> None:
        try:
            if type(self.verb) is not DockerCLIVerbV1 or type(self.arguments) is not tuple:
                raise ValueError
            if len(self.arguments) > MAX_DOCKER_ARGS_V1:
                raise ValueError
            for value in self.arguments:
                _argv_token_v1(value)
            checked_sha_v1(self.command_digest, BundleIOCodeV1.COMMAND_INVALID)
            if self.command_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.COMMAND_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "arguments": list(self.arguments),
            "schema_version": "synaptic-host-docker-cli-command/v1",
            "verb": self.verb.value,
        }

    @classmethod
    def build(cls, verb, arguments=()):
        try:
            if type(verb) is not DockerCLIVerbV1 or type(arguments) is not tuple:
                raise ValueError
            body = {
                "arguments": list(arguments),
                "schema_version": "synaptic-host-docker-cli-command/v1",
                "verb": verb.value,
            }
            return cls(verb, arguments, digest_v1(body))
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.COMMAND_INVALID)


@dataclass(frozen=True, slots=True)
class DockerCLIEnvironmentV1:
    entries: tuple[tuple[str, str], ...]
    environment_digest: str

    def __post_init__(self) -> None:
        try:
            if type(self.entries) is not tuple:
                raise ValueError
            expected_keys = ("SystemRoot", "TEMP", "TMP", "WINDIR")
            if (
                any(type(entry) is not tuple or len(entry) != 2 for entry in self.entries)
                or tuple(key for key, _ in self.entries) != expected_keys
            ):
                raise ValueError
            for key, value in self.entries:
                if (
                    type(key) is not str
                ):
                    raise ValueError
                _windows_drive_path_v1(value)
                upper = key.upper()
                if (
                    upper.startswith("DOCKER_") or "TOKEN" in upper or "AUTH" in upper
                    or "PROXY" in upper
                ):
                    raise ValueError
            checked_sha_v1(self.environment_digest, BundleIOCodeV1.COMMAND_INVALID)
            if self.environment_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "entries": [[key, value] for key, value in self.entries],
            "schema_version": "synaptic-host-docker-cli-environment/v1",
        }

    @classmethod
    def build(cls, entries):
        try:
            entries = tuple(entries)
            body = {"entries": [[key, value] for key, value in entries],
                    "schema_version": "synaptic-host-docker-cli-environment/v1"}
            return cls(entries, digest_v1(body))
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)


@dataclass(frozen=True, slots=True)
class DockerLocalEndpointDescriptorV1:
    source_context_ref: str
    host: str
    tls: bool

    def __post_init__(self) -> None:
        try:
            if (
                self.source_context_ref != "desktop-linux"
                or self.host != "npipe:////./pipe/dockerDesktopLinuxEngine"
                or type(self.tls) is not bool
                or self.tls is not False
            ):
                raise ValueError
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)

    def canonical(self) -> dict[str, object]:
        return {
            "host": self.host,
            "schema_version": "synaptic-host-docker-local-endpoint/v1",
            "source_context_ref": self.source_context_ref,
            "tls": self.tls,
        }

    @property
    def descriptor_digest(self) -> str:
        return digest_v1(self.canonical())

    @classmethod
    def build(cls, source_context_ref, host, tls):
        return cls(source_context_ref, host, tls)


@dataclass(frozen=True, slots=True)
class DockerCLIPolicyV1:
    executable: str
    endpoint: DockerLocalEndpointDescriptorV1
    environment: DockerCLIEnvironmentV1
    timeout_ms: int
    terminate_grace_ms: int
    stdout_limit: int
    stderr_limit: int
    combined_limit: int
    policy_digest: str

    def __post_init__(self) -> None:
        try:
            _docker_desktop_wsl_executable_v1(self.executable)
            if (
                type(self.endpoint) is not DockerLocalEndpointDescriptorV1
                or type(self.environment) is not DockerCLIEnvironmentV1
            ):
                raise ValueError
            DockerLocalEndpointDescriptorV1.build(
                self.endpoint.source_context_ref, self.endpoint.host,
                self.endpoint.tls,
            )
            if (
                type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 3_600_000
                or type(self.terminate_grace_ms) is not int or not 1 <= self.terminate_grace_ms <= 60_000
                or type(self.stdout_limit) is not int or not 1 <= self.stdout_limit <= MAX_DOCKER_STREAM_BYTES_V1
                or type(self.stderr_limit) is not int or not 1 <= self.stderr_limit <= MAX_DOCKER_STREAM_BYTES_V1
                or type(self.combined_limit) is not int or not 1 <= self.combined_limit <= MAX_DOCKER_COMBINED_BYTES_V1
                or self.combined_limit < max(self.stdout_limit, self.stderr_limit)
            ):
                raise ValueError
            checked_sha_v1(self.policy_digest, BundleIOCodeV1.COMMAND_INVALID)
            if self.policy_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "combined_limit": self.combined_limit,
            "endpoint_descriptor_digest": self.endpoint.descriptor_digest,
            "environment_digest": self.environment.environment_digest,
            "executable": self.executable,
            "schema_version": "synaptic-host-docker-cli-policy/v1",
            "stderr_limit": self.stderr_limit, "stdout_limit": self.stdout_limit,
            "terminate_grace_ms": self.terminate_grace_ms,
            "timeout_ms": self.timeout_ms,
        }

    @classmethod
    def build(cls, executable, endpoint, environment, *, timeout_ms=30_000,
              terminate_grace_ms=1_000, stdout_limit=MAX_DOCKER_STREAM_BYTES_V1,
              stderr_limit=MAX_DOCKER_STREAM_BYTES_V1,
              combined_limit=MAX_DOCKER_COMBINED_BYTES_V1):
        try:
            if (
                type(endpoint) is not DockerLocalEndpointDescriptorV1
                or type(environment) is not DockerCLIEnvironmentV1
            ):
                raise ValueError
            endpoint = DockerLocalEndpointDescriptorV1.build(
                endpoint.source_context_ref, endpoint.host, endpoint.tls,
            )
            body = {
                "combined_limit": combined_limit,
                "endpoint_descriptor_digest": endpoint.descriptor_digest,
                "environment_digest": environment.environment_digest,
                "executable": executable,
                "schema_version": "synaptic-host-docker-cli-policy/v1",
                "stderr_limit": stderr_limit, "stdout_limit": stdout_limit,
                "terminate_grace_ms": terminate_grace_ms, "timeout_ms": timeout_ms,
            }
            return cls(executable, endpoint, environment, timeout_ms,
                       terminate_grace_ms, stdout_limit, stderr_limit,
                       combined_limit, digest_v1(body))
        except DockerPlatformErrorV1 as error:
            _platform_fail(error.code)
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.POLICY_INVALID)


class DockerCLIOutcomeV1(str, Enum):
    SUCCESS = "SUCCESS"
    NONZERO_EXIT = "NONZERO_EXIT"


@dataclass(frozen=True, slots=True)
class DockerCLIResultV1:
    command_digest: str
    policy_digest: str
    outcome: DockerCLIOutcomeV1
    exit_code: int
    stdout_size: int
    stdout_digest: str
    stderr_size: int
    stderr_digest: str
    result_digest: str

    def __post_init__(self) -> None:
        try:
            for value in (self.command_digest, self.policy_digest,
                          self.stdout_digest, self.stderr_digest, self.result_digest):
                checked_sha_v1(value, BundleIOCodeV1.COMMAND_INVALID)
            if (
                type(self.outcome) is not DockerCLIOutcomeV1
                or type(self.exit_code) is not int
                or type(self.stdout_size) is not int or self.stdout_size < 0
                or type(self.stderr_size) is not int or self.stderr_size < 0
                or (self.outcome is DockerCLIOutcomeV1.SUCCESS) != (self.exit_code == 0)
                or self.result_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except BaseException:
            _platform_fail(DockerPlatformCodeV1.IO_INDETERMINATE)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "command_digest": self.command_digest, "exit_code": self.exit_code,
            "outcome": self.outcome.value, "policy_digest": self.policy_digest,
            "schema_version": "synaptic-host-docker-cli-result/v1",
            "stderr_digest": self.stderr_digest, "stderr_size": self.stderr_size,
            "stdout_digest": self.stdout_digest, "stdout_size": self.stdout_size,
        }


__all__: tuple[str, ...] = ()
