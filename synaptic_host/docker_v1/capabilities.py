"""Deterministic same-process Docker-v1 capability registries."""

from __future__ import annotations

from types import MappingProxyType

from synaptic_host.bundle_io_v1.model import (
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleMemberCommandV1,
    checked_ref_v1,
    checked_sha_v1,
)
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleSourceV1,
)
from tuner.execution.providers.docker_provider_v1.model import (
    DockerProfileV1,
    DockerSourceSealRequestV1,
    validated_profile_snapshot,
)

from .model import (
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStorageMappingV1,
    AuthenticatedDockerStoragePathMappingPairV1,
    AuthenticatedDockerWSLRootMappingV1,
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerMountCodeV1,
    DockerMountErrorV1,
    DockerSourceDeclarationV1,
    DockerStoragePathMappingPairV1,
    DockerStoragePurposeV1,
    DockerWSLPathPurposeV1,
    _storage_mapping_snapshot_v1,
    _wsl_mapping_snapshot_v1,
)
from .ports import DockerSourceResolutionV1


def _source_fail(code=DockerHostSourceCodeV1.DECLARATION_CONFLICT):
    raise DockerHostSourceErrorV1(code)


def _mount_fail(code):
    raise DockerMountErrorV1(code)


def _snapshot_source(value):
    try:
        if type(value) is not BundleSourceV1:
            raise ValueError
        rebuilt = BundleSourceV1(
            value.source_ref, value.borrow, value.directory,
            value.component, value.source_digest,
        )
        if (
            rebuilt != value
            or rebuilt.borrow is not value.borrow
            or rebuilt.directory is not value.directory
        ):
            raise ValueError
        return rebuilt
    except BaseException:
        raise BundleIOErrorV1(BundleIOCodeV1.SOURCE_INVALID) from None


def _snapshot_access(value):
    try:
        if type(value) is not BundleBorrowAccessV1:
            raise ValueError
        rebuilt = BundleBorrowAccessV1(
            value.destination_ref, value.root_authority_digest,
            value.create_borrow, value.create_root,
            value.verify_borrow, value.verify_root, value.access_digest,
        )
        if (
            rebuilt != value
            or rebuilt.create_borrow is not value.create_borrow
            or rebuilt.create_root is not value.create_root
            or rebuilt.verify_borrow is not value.verify_borrow
            or rebuilt.verify_root is not value.verify_root
        ):
            raise ValueError
        return rebuilt
    except BaseException:
        _source_fail()


def _snapshot_members(value):
    try:
        if (
            type(value) is not tuple
            or not value
            or any(type(item) is not BundleMemberCommandV1 for item in value)
        ):
            raise ValueError
        rebuilt = tuple(BundleMemberCommandV1(
            item.logical_name, item.source_ref, item.size, item.sha256
        ) for item in value)
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _source_fail()


def _snapshot_declaration(value):
    try:
        if type(value) is not AuthenticatedDockerSourceDeclarationV1:
            raise ValueError
        content = value.content
        rebuilt_content = DockerSourceDeclarationV1(
            content.source_ref, content.source_digest,
            content.effect_identity_digest, content.prepared_plan_digest,
            content.profile_ref, content.purpose_ref,
            content.destination_ref, content.root_authority_digest,
            content.bundle_access_digest, _snapshot_members(content.members),
            content.bundle_command_digest, content.declaration_digest,
        )
        rebuilt = AuthenticatedDockerSourceDeclarationV1(
            rebuilt_content, value.authority_ref, value.key_ref, value.tag
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except DockerHostSourceErrorV1:
        raise
    except BaseException:
        _source_fail(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)


def _snapshot_declaration_content(value):
    try:
        if type(value) is not DockerSourceDeclarationV1:
            raise ValueError
        rebuilt = DockerSourceDeclarationV1(
            value.source_ref, value.source_digest,
            value.effect_identity_digest, value.prepared_plan_digest,
            value.profile_ref, value.purpose_ref, value.destination_ref,
            value.root_authority_digest, value.bundle_access_digest,
            _snapshot_members(value.members), value.bundle_command_digest,
            value.declaration_digest,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except DockerHostSourceErrorV1:
        raise
    except BaseException:
        _source_fail()


class DockerSingleLaunchSourceDeclarationResolverV1:
    """Deterministically derives one launch's declaration from its request."""

    def __init__(
        self, *, profile, source, source_digest, purpose_ref,
        destination_ref, members,
        bundle_access, declaration_authority,
    ):
        try:
            if type(profile) is not DockerProfileV1:
                raise ValueError
            profile = validated_profile_snapshot(profile)
            source = _snapshot_source(source)
            access = _snapshot_access(bundle_access)
            members = _snapshot_members(members)
            checked_sha_v1(source_digest, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(purpose_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_ref_v1(destination_ref, BundleIOCodeV1.COMMAND_INVALID)
            if (
                destination_ref != access.destination_ref
                or any(item.source_ref != source.source_ref for item in members)
                or not callable(getattr(declaration_authority, "issue", None))
                or not callable(
                    getattr(declaration_authority, "authenticate", None)
                )
            ):
                raise ValueError
            checked_ref_v1(
                declaration_authority.authority_ref,
                BundleIOCodeV1.AUTHENTICATION_FAILED,
            )
            checked_ref_v1(
                declaration_authority.key_ref,
                BundleIOCodeV1.AUTHENTICATION_FAILED,
            )
            self._profile = profile
            self._source = source
            self._source_digest = source_digest
            self._purpose_ref = purpose_ref
            self._destination_ref = destination_ref
            self._members = members
            self._access = access
            self._authority = declaration_authority
            self._authority_ref = declaration_authority.authority_ref
            self._key_ref = declaration_authority.key_ref
        except BundleIOErrorV1:
            _source_fail()
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            _source_fail()

    def resolve(self, request):
        try:
            if type(request) is not DockerSourceSealRequestV1:
                raise ValueError
            identity = request.identity
            plan = identity.plan
            if (
                validated_profile_snapshot(plan.profile) != self._profile
                or plan.profile.provider.profile_ref
                != self._profile.provider.profile_ref
                or request.source_ref != self._source.source_ref
                or request.source_digest != self._source_digest
                or plan.source_digest != self._source_digest
                or self._access.destination_ref != self._destination_ref
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
            ):
                raise ValueError
            declaration = DockerSourceDeclarationV1.build(
                source_ref=request.source_ref,
                source_digest=request.source_digest,
                effect_identity_digest=identity.digest,
                prepared_plan_digest=plan.digest,
                profile_ref=self._profile.provider.profile_ref,
                purpose_ref=self._purpose_ref,
                destination_ref=self._destination_ref,
                root_authority_digest=self._access.root_authority_digest,
                bundle_access_digest=self._access.access_digest,
                members=_snapshot_members(self._members),
            )
            baseline = _snapshot_declaration_content(declaration)
            issued = _snapshot_declaration(self._authority.issue(
                _snapshot_declaration_content(baseline)
            ))
            if (
                issued.content != baseline
                or issued.authority_ref != self._authority_ref
                or issued.key_ref != self._key_ref
            ):
                raise ValueError
            expected = _snapshot_declaration(
                AuthenticatedDockerSourceDeclarationV1(
                    _snapshot_declaration_content(baseline),
                    self._authority_ref, self._key_ref, issued.tag,
                )
            )
            if issued != expected:
                raise ValueError
            trusted = _snapshot_declaration(
                self._authority.authenticate(_snapshot_declaration(expected))
            )
            if (
                trusted != expected
                or trusted.content != baseline
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
            ):
                raise ValueError
            return DockerSourceResolutionV1(
                _snapshot_declaration(expected),
                _snapshot_access(self._access),
            )
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            _source_fail()


class DockerImmutableBundleSourceRegistryV1:
    """Non-owning immutable registry of exact live source capabilities."""

    def __init__(self, sources):
        try:
            if type(sources) is not tuple or not sources:
                raise ValueError
            retained = tuple(_snapshot_source(value) for value in sources)
            refs = tuple(value.source_ref for value in retained)
            if len(refs) != len(set(refs)):
                raise ValueError
            self._sources = MappingProxyType({
                value.source_ref: value for value in retained
            })
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise BundleIOErrorV1(BundleIOCodeV1.SOURCE_INVALID) from None

    def resolve(self, source_ref):
        try:
            checked_ref_v1(source_ref, BundleIOCodeV1.SOURCE_INVALID)
            value = self._sources.get(source_ref)
            if value is None:
                raise ValueError
            return _snapshot_source(value)
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise BundleIOErrorV1(BundleIOCodeV1.SOURCE_INVALID) from None


class ImmutableDockerStoragePathMappingPairRegistryV1:
    """Single immutable source for authenticated pair and mapping projections."""

    def __init__(self, *, source_pair, artifact_pair, authority):
        try:
            if not callable(getattr(authority, "authenticate", None)):
                raise ValueError
            checked_ref_v1(
                authority.authority_ref, BundleIOCodeV1.AUTHENTICATION_FAILED
            )
            checked_ref_v1(
                authority.key_ref, BundleIOCodeV1.AUTHENTICATION_FAILED
            )
            self._authority = authority
            self._authority_ref = authority.authority_ref
            self._key_ref = authority.key_ref
            source = self._authenticate(source_pair)
            artifact = self._authenticate(artifact_pair)
            self._validate_role(source, source=True)
            self._validate_role(artifact, source=False)
            source_storage = source.content.storage_mapping.content
            artifact_storage = artifact.content.storage_mapping.content
            if (
                source.content.pair_digest == artifact.content.pair_digest
                or source_storage.mapping_ref == artifact_storage.mapping_ref
                or source_storage.declared_ref == artifact_storage.declared_ref
            ):
                raise ValueError
            self._source_pair = source
            self._artifact_pair = artifact
            self._source_ref = source_storage.declared_ref
            self._artifact_ref = artifact_storage.declared_ref
            self._source_mapping_ref = source_storage.mapping_ref
            self._artifact_mapping_ref = artifact_storage.mapping_ref
        except DockerMountErrorV1:
            raise
        except BaseException:
            _mount_fail(DockerMountCodeV1.MAPPING_CONFLICT)

    def _authenticate(self, value):
        try:
            if (
                type(value)
                is not AuthenticatedDockerStoragePathMappingPairV1
                or value.authority_ref != self._authority_ref
                or value.key_ref != self._key_ref
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
            ):
                raise ValueError
            baseline = self._snapshot_pair(value)
            presented = self._snapshot_pair(baseline)
            returned = self._snapshot_pair(
                self._authority.authenticate(presented)
            )
            if (
                returned != baseline
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
            ):
                raise ValueError
            return self._snapshot_pair(baseline)
        except BaseException:
            _mount_fail(DockerMountCodeV1.AUTHENTICATION_FAILED)

    @staticmethod
    def _snapshot_pair(value):
        if type(value) is not AuthenticatedDockerStoragePathMappingPairV1:
            raise ValueError
        original_access = value.content.storage_mapping.content.verify_access
        rebuilt = AuthenticatedDockerStoragePathMappingPairV1(
            DockerStoragePathMappingPairV1(
                value.content.storage_mapping,
                value.content.wsl_mapping,
                value.content.pair_digest,
            ),
            value.authority_ref, value.key_ref, value.tag,
        )
        if rebuilt != value:
            raise ValueError
        rebuilt_access = rebuilt.content.storage_mapping.content.verify_access
        if original_access is None:
            if rebuilt_access is not None:
                raise ValueError
        elif (
            rebuilt_access.verify_borrow is not original_access.verify_borrow
            or rebuilt_access.verify_root is not original_access.verify_root
        ):
            raise ValueError
        return rebuilt

    @staticmethod
    def _validate_role(value, *, source):
        storage = value.content.storage_mapping.content
        wsl = value.content.wsl_mapping.content
        if source:
            valid = (
                storage.purpose is DockerStoragePurposeV1.SOURCE_BUNDLE
                and wsl.purpose is DockerWSLPathPurposeV1.SOURCE_READ
                and storage.verify_access is not None
            )
        else:
            valid = (
                storage.purpose is DockerStoragePurposeV1.ARTIFACT_OUTPUT
                and wsl.purpose is DockerWSLPathPurposeV1.ARTIFACT_WRITE
                and storage.verify_access is None
            )
        if not valid:
            _mount_fail(DockerMountCodeV1.MAPPING_CONFLICT)

    def _required_pair(self, value, expected_ref, supplied_ref, *, source):
        try:
            checked_ref_v1(supplied_ref, BundleIOCodeV1.COMMAND_INVALID)
            if supplied_ref != expected_ref:
                _mount_fail(DockerMountCodeV1.MAPPING_INDETERMINATE)
            trusted = self._authenticate(value)
            self._validate_role(trusted, source=source)
            if trusted.content.storage_mapping.content.declared_ref != supplied_ref:
                raise ValueError
            return trusted
        except DockerMountErrorV1:
            raise
        except BaseException:
            _mount_fail(DockerMountCodeV1.MAPPING_INDETERMINATE)

    def resolve_source_pair(self, source_ref):
        return self._required_pair(
            self._source_pair, self._source_ref, source_ref, source=True
        )

    def resolve_artifact_pair(self, artifact_ref):
        return self._required_pair(
            self._artifact_pair, self._artifact_ref,
            artifact_ref, source=False,
        )

    def resolve_source(self, source_ref):
        pair = self.resolve_source_pair(source_ref)
        returned = _storage_mapping_snapshot_v1(pair.content.storage_mapping)
        access = returned.content.verify_access
        original = pair.content.storage_mapping.content.verify_access
        if (
            returned.content.purpose is not DockerStoragePurposeV1.SOURCE_BUNDLE
            or returned.content.declared_ref != source_ref
            or access.verify_borrow is not original.verify_borrow
            or access.verify_root is not original.verify_root
        ):
            _mount_fail(DockerMountCodeV1.MAPPING_CONFLICT)
        return returned

    def resolve_artifact(self, artifact_ref):
        pair = self.resolve_artifact_pair(artifact_ref)
        returned = _storage_mapping_snapshot_v1(pair.content.storage_mapping)
        if (
            returned.content.purpose
            is not DockerStoragePurposeV1.ARTIFACT_OUTPUT
            or returned.content.declared_ref != artifact_ref
            or returned.content.verify_access is not None
        ):
            _mount_fail(DockerMountCodeV1.MAPPING_CONFLICT)
        return returned

    def resolve(self, mapping_ref, expected_mapping_digest):
        try:
            checked_ref_v1(mapping_ref, BundleIOCodeV1.COMMAND_INVALID)
            checked_sha_v1(
                expected_mapping_digest, BundleIOCodeV1.COMMAND_INVALID
            )
        except BaseException:
            return None
        if mapping_ref == self._source_mapping_ref:
            pair = self._authenticate(self._source_pair)
            self._validate_role(pair, source=True)
        elif mapping_ref == self._artifact_mapping_ref:
            pair = self._authenticate(self._artifact_pair)
            self._validate_role(pair, source=False)
        else:
            return None
        returned = _wsl_mapping_snapshot_v1(pair.content.wsl_mapping)
        if (
            returned.content.mapping_ref != mapping_ref
            or returned.content.mapping_digest != expected_mapping_digest
        ):
            return None
        return returned


__all__: tuple[str, ...] = ()
