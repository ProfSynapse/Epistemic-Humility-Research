from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    AuthenticatedDockerCommandBindingV1,
    AuthenticatedDockerSourceSealV1,
    DockerSourceSealContentV1,
    DockerSourceSealRequestV1,
    DockerAbsenceContentV1,
    DockerImageV1,
    DockerLabelsV1,
    DockerRuntimeV1,
    DockerWorkloadV1,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleLookupResultV1,
    BundleSealCommandV1,
    BundleMountVerificationV1,
)
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleMountVerifyAccessV1,
)

from .model import (
    AuthenticatedDockerWSLRootMappingV1,
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStorageMappingV1,
    AuthenticatedDockerStageBundleBindingV1,
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerStageBundleBindingV1,
    DockerWindowsPathV1,
    DockerWSLPathRequestV1,
)
from .control_model import (
    DockerContainerInspectResultV1,
    DockerCreateExecutionResultV1,
    DockerExactNameInventoryResultV1,
    DockerImageInspectResultV1,
)
from .control_contract import (
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerMutationRecordV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    DockerAdmissionResultV1,
    DockerCASResultV1,
    DockerControlIntentV1,
    DockerCreatePathBindingV1,
    DockerMutationLookupResultV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerExpectedCreateBindingV1,
)
from .model import ResolvedDockerMountsV1


@dataclass(frozen=True, slots=True)
class DockerSourceResolutionV1:
    declaration: AuthenticatedDockerSourceDeclarationV1
    bundle_access: BundleBorrowAccessV1

    def __post_init__(self) -> None:
        try:
            if (
                type(self.declaration) is not AuthenticatedDockerSourceDeclarationV1
                or type(self.bundle_access) is not BundleBorrowAccessV1
                or self.declaration.content.destination_ref
                != self.bundle_access.destination_ref
                or self.declaration.content.root_authority_digest
                != self.bundle_access.root_authority_digest
                or self.declaration.content.bundle_access_digest
                != self.bundle_access.access_digest
            ):
                raise ValueError
        except BaseException:
            raise DockerHostSourceErrorV1(
                DockerHostSourceCodeV1.DECLARATION_CONFLICT
            ) from None


class DockerSourceDeclarationRegistryPortV1(Protocol):
    def resolve(self, request: DockerSourceSealRequestV1) -> DockerSourceResolutionV1: ...


class DockerSourceDeclarationAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def authenticate(
        self, value: AuthenticatedDockerSourceDeclarationV1
    ) -> AuthenticatedDockerSourceDeclarationV1 | None: ...


class DockerStageBundleStorePortV1(Protocol):
    def put_if_absent(
        self, value: AuthenticatedDockerStageBundleBindingV1
    ) -> AuthenticatedDockerStageBundleBindingV1: ...

    def get_by_stage_effect_id(
        self, stage_effect_id: str
    ) -> AuthenticatedDockerStageBundleBindingV1 | None: ...


class DockerStageBundleRecordAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def issue(
        self, value: DockerStageBundleBindingV1
    ) -> AuthenticatedDockerStageBundleBindingV1: ...

    def authenticate(
        self, value: AuthenticatedDockerStageBundleBindingV1
    ) -> AuthenticatedDockerStageBundleBindingV1 | None: ...


class DockerCommandBindingCatalogPortV1(Protocol):
    def resolve(
        self, command_digest: str
    ) -> AuthenticatedDockerCommandBindingV1: ...


class DockerCommandBindingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def authenticate(
        self, value: AuthenticatedDockerCommandBindingV1
    ) -> AuthenticatedDockerCommandBindingV1 | None: ...


class DockerStorageMappingRegistryPortV1(Protocol):
    def resolve_source(
        self, source_ref: str
    ) -> AuthenticatedDockerStorageMappingV1: ...

    def resolve_artifact(
        self, artifact_ref: str
    ) -> AuthenticatedDockerStorageMappingV1: ...


class DockerStorageMappingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def authenticate(
        self, value: AuthenticatedDockerStorageMappingV1
    ) -> AuthenticatedDockerStorageMappingV1 | None: ...


class BundleMountVerifierPortV1(Protocol):
    def verify_mount(
        self, command: BundleSealCommandV1,
        access: BundleMountVerifyAccessV1,
        expected_authenticated_binding: AuthenticatedBundleBindingV1,
    ) -> BundleMountVerificationV1: ...


class ImmutableSourceBundlePortV1(Protocol):
    def seal(
        self, command: BundleSealCommandV1, access: BundleBorrowAccessV1
    ) -> BundleLookupResultV1: ...


class BundleBindingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def issue(self, value: BundleBindingV1) -> AuthenticatedBundleBindingV1: ...

    def authenticate(
        self, value: AuthenticatedBundleBindingV1
    ) -> AuthenticatedBundleBindingV1 | None: ...


class DockerSourceSealAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def issue(
        self, value: DockerSourceSealContentV1
    ) -> AuthenticatedDockerSourceSealV1: ...

    def authenticate(
        self, value: AuthenticatedDockerSourceSealV1
    ) -> AuthenticatedDockerSourceSealV1 | None: ...


class DockerWSLRootMappingRegistryPortV1(Protocol):
    def resolve(
        self, mapping_ref: str, expected_mapping_digest: str
    ) -> AuthenticatedDockerWSLRootMappingV1 | None: ...


class DockerWSLRootMappingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str

    def authenticate(
        self, value: AuthenticatedDockerWSLRootMappingV1
    ) -> AuthenticatedDockerWSLRootMappingV1 | None: ...


class DockerWSLPathTranslatorPortV1(Protocol):
    def translate(self, request: DockerWSLPathRequestV1) -> DockerWindowsPathV1: ...


class DockerBinaryStreamPortV1(Protocol):
    def read(self, size: int) -> bytes: ...


class DockerProcessPortV1(Protocol):
    stdout: DockerBinaryStreamPortV1
    stderr: DockerBinaryStreamPortV1

    def poll(self) -> int | None: ...
    def wait(self, timeout: float | None = None) -> int: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...


class DockerPopenFactoryPortV1(Protocol):
    def __call__(self, argv: tuple[str, ...], **kwargs) -> DockerProcessPortV1: ...


class DockerTypedCLIRunnerPortV1(Protocol):
    def create_container(
        self, command, expected_container_name: str,
    ) -> DockerCreateExecutionResultV1: ...
    def inventory_exact_name(self, container_name: str) -> DockerExactNameInventoryResultV1: ...
    def inspect_image(self, image_digest: str) -> DockerImageInspectResultV1: ...
    def inspect_container(self, container_ref: str) -> DockerContainerInspectResultV1: ...


class DockerCreateMountResolverPortV1(Protocol):
    def resolve_create_mounts(
        self, *, labels: DockerLabelsV1, image: DockerImageV1,
        runtime: DockerRuntimeV1, workload: DockerWorkloadV1,
        source_ref: str, artifact_ref: str,
    ) -> ResolvedDockerMountsV1: ...


class DockerCreatePathBinderPortV1(Protocol):
    def bind(
        self, resolved: ResolvedDockerMountsV1,
        source_ref: str, artifact_ref: str,
    ) -> AuthenticatedDockerCreatePathBindingV1: ...


class DockerCreatePathBindingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerCreatePathBindingV1) -> AuthenticatedDockerCreatePathBindingV1: ...
    def authenticate(self, value: AuthenticatedDockerCreatePathBindingV1) -> AuthenticatedDockerCreatePathBindingV1 | None: ...


class DockerWorkloadEnvironmentBindingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerWorkloadEnvironmentBindingV1) -> AuthenticatedDockerWorkloadEnvironmentBindingV1: ...
    def authenticate(self, value: AuthenticatedDockerWorkloadEnvironmentBindingV1) -> AuthenticatedDockerWorkloadEnvironmentBindingV1 | None: ...


class DockerControlIntentAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerControlIntentV1) -> AuthenticatedDockerControlIntentV1: ...
    def authenticate(self, value: AuthenticatedDockerControlIntentV1) -> AuthenticatedDockerControlIntentV1 | None: ...


class DockerMutationRecordAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerMutationRecordV1) -> AuthenticatedDockerMutationRecordV1: ...
    def authenticate(self, value: AuthenticatedDockerMutationRecordV1) -> AuthenticatedDockerMutationRecordV1 | None: ...


class DockerMutationRepositoryPortV1(Protocol):
    def admit(self, request: DockerMutationAdmissionRequestV1) -> DockerAdmissionResultV1: ...
    def compare_and_swap(self, request: DockerMutationCASRequestV1) -> DockerCASResultV1: ...
    def lookup(self, operation_id: str) -> DockerMutationLookupResultV1: ...


class DockerAbsenceAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerAbsenceContentV1) -> AuthenticatedDockerAbsenceV1: ...
    def authenticate(self, value: AuthenticatedDockerAbsenceV1) -> AuthenticatedDockerAbsenceV1 | None: ...


class DockerExpectedCreateBindingAuthorityPortV1(Protocol):
    authority_ref: str
    key_ref: str
    def issue(self, value: DockerExpectedCreateBindingV1) -> AuthenticatedDockerExpectedCreateBindingV1: ...
    def authenticate(self, value: AuthenticatedDockerExpectedCreateBindingV1) -> AuthenticatedDockerExpectedCreateBindingV1 | None: ...


class DockerExpectedCreateBindingCatalogPortV1(Protocol):
    def resolve(
        self, engine_command_digest: str, labels_digest: str,
    ) -> AuthenticatedDockerExpectedCreateBindingV1 | None: ...


__all__: tuple[str, ...] = ()
