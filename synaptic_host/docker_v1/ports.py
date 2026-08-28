from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerCommandBindingV1,
    AuthenticatedDockerSourceSealV1,
    DockerSourceSealContentV1,
    DockerSourceSealRequestV1,
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
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStorageMappingV1,
    AuthenticatedDockerStageBundleBindingV1,
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerStageBundleBindingV1,
)


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


__all__: tuple[str, ...] = ()
