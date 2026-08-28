from __future__ import annotations

from .model import (
    AuthenticatedDockerWSLRootMappingV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
    DockerWindowsPathV1,
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
    DockerWSLRootMappingV1,
)
from .ports import (
    DockerWSLRootMappingAuthorityPortV1,
    DockerWSLRootMappingRegistryPortV1,
)
from synaptic_host.bundle_io_v1.model import digest_v1


def _error(code: DockerPlatformCodeV1) -> DockerPlatformErrorV1:
    return DockerPlatformErrorV1(code)


class DockerWSLPathTranslatorV1:
    def __init__(
        self, *, registry: DockerWSLRootMappingRegistryPortV1,
        authority: DockerWSLRootMappingAuthorityPortV1,
    ) -> None:
        self._registry = registry
        self._authority = authority
        try:
            self._pinned_refs = (authority.authority_ref, authority.key_ref)
            if any(type(value) is not str or not value for value in self._pinned_refs):
                raise ValueError
        except BaseException:
            raise _error(DockerPlatformCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot(value) -> AuthenticatedDockerWSLRootMappingV1:
        try:
            if type(value) is not AuthenticatedDockerWSLRootMappingV1:
                raise ValueError
            content = value.content
            rebuilt_content = DockerWSLRootMappingV1(
                content.mapping_ref, content.distro, content.purpose,
                content.posix_root, content.mapping_digest,
            )
            rebuilt = AuthenticatedDockerWSLRootMappingV1(
                rebuilt_content, value.authority_ref, value.key_ref, value.tag,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerPlatformErrorV1 as error:
            raise _error(error.code) from None
        except BaseException:
            raise _error(DockerPlatformCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_request(value) -> DockerWSLPathRequestV1:
        try:
            if type(value) is not DockerWSLPathRequestV1:
                raise ValueError
            rebuilt = DockerWSLPathRequestV1(
                value.mapping_ref, value.expected_mapping_digest,
                value.expected_distro, value.purpose, value.posix_path,
                value.request_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerPlatformCodeV1.PATH_INVALID) from None

    def translate(self, request: DockerWSLPathRequestV1) -> DockerWindowsPathV1:
        request = self._snapshot_request(request)
        mapping_ref = request.mapping_ref
        purpose = request.purpose
        path = request.posix_path
        try:
            raw = self._registry.resolve(
                mapping_ref, request.expected_mapping_digest
            )
        except BaseException:
            raise _error(DockerPlatformCodeV1.ROOT_UNREGISTERED) from None
        if raw is None:
            raise _error(DockerPlatformCodeV1.ROOT_UNREGISTERED)
        supplied = self._snapshot(raw)
        if (supplied.authority_ref, supplied.key_ref) != self._pinned_refs:
            raise _error(DockerPlatformCodeV1.AUTHENTICATION_FAILED)
        try:
            authenticated = self._authority.authenticate(supplied)
        except BaseException:
            raise _error(DockerPlatformCodeV1.AUTHENTICATION_FAILED) from None
        trusted = self._snapshot(authenticated)
        if trusted != supplied or (trusted.authority_ref, trusted.key_ref) != self._pinned_refs:
            raise _error(DockerPlatformCodeV1.AUTHENTICATION_FAILED)
        mapping = trusted.content
        if (
            mapping.mapping_ref != mapping_ref
            or mapping.mapping_digest != request.expected_mapping_digest
            or mapping.distro != request.expected_distro
            or mapping.purpose is not purpose
        ):
            raise _error(DockerPlatformCodeV1.PATH_INVALID)
        root_parts = mapping.posix_root[1:].split("/")
        path_parts = path[1:].split("/")
        if path_parts[:len(root_parts)] != root_parts:
            raise _error(DockerPlatformCodeV1.PATH_INVALID)
        unc = "\\\\wsl.localhost\\" + mapping.distro + path.replace("/", "\\")
        body = {
            "distro": mapping.distro,
            "mapping_digest": mapping.mapping_digest,
            "mapping_ref": mapping.mapping_ref,
            "posix_path": path,
            "purpose": purpose.value,
            "schema_version": "synaptic-host-docker-windows-path/v1",
            "unc_path": unc,
        }
        return DockerWindowsPathV1(
            mapping.mapping_ref, mapping.mapping_digest, purpose,
            mapping.distro, path, unc, digest_v1(body),
        )


__all__: tuple[str, ...] = ()
