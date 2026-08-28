from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from threading import Lock

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerSourceSealV1,
    DockerEffectIdentityV1,
    DockerLookupDispositionV1,
    DockerSourceSealContentV1,
    DockerSourceSealLookupRequestV1,
    DockerSourceSealLookupResultV1,
    DockerSourceSealRequestV1,
    PreparedDockerPlanV1,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleIOErrorV1,
    BundleLookupResultV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleMemberEvidenceV1,
    BundleSealCommandV1,
)
from synaptic_host.bundle_io_v1.ports import BundleBorrowAccessV1

from .model import (
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStageBundleBindingV1,
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerSourceDeclarationV1,
    DockerStageBundleBindingV1,
)
from .ports import DockerSourceResolutionV1


def _error(code: DockerHostSourceCodeV1) -> DockerHostSourceErrorV1:
    return DockerHostSourceErrorV1(code)


class DockerBundleSourceSealAdapterV1:
    """Exact STAGE source sealing with retained lookup-only recovery."""

    def __init__(
        self, *, declarations, declaration_authority, bundle,
        binding_authority, source_seal_authority, stage_record_authority, store,
    ) -> None:
        self._declarations = declarations
        self._declaration_authority = declaration_authority
        self._bundle = bundle
        self._binding_authority = binding_authority
        self._source_seal_authority = source_seal_authority
        self._stage_record_authority = stage_record_authority
        self._store = store
        try:
            refs = (
                declaration_authority.authority_ref,
                declaration_authority.key_ref,
                binding_authority.authority_ref,
                binding_authority.key_ref,
                source_seal_authority.authority_ref,
                source_seal_authority.key_ref,
                stage_record_authority.authority_ref,
                stage_record_authority.key_ref,
            )
            if any(type(value) is not str or not value for value in refs):
                raise ValueError
            (
                self._declaration_authority_ref, self._declaration_key_ref,
                self._binding_authority_ref, self._binding_key_ref,
                self._seal_authority_ref, self._seal_key_ref,
                self._stage_authority_ref, self._stage_key_ref,
            ) = refs
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None
        self._guard_lock = Lock()
        self._stage_guards: dict[str, list[object]] = {}

    @contextmanager
    def _stage_guard(self, effect_id: str):
        with self._guard_lock:
            entry = self._stage_guards.get(effect_id)
            if entry is None:
                entry = [Lock(), 0]
                self._stage_guards[effect_id] = entry
            entry[1] += 1
        guard = entry[0]
        acquired = False
        release_failed = False
        try:
            try:
                acquired = guard.acquire()
                if acquired is not True:
                    raise RuntimeError
                yield
            except DockerHostSourceErrorV1:
                raise
            except BaseException:
                raise _error(
                    DockerHostSourceCodeV1.STORE_INDETERMINATE
                ) from None
        finally:
            if acquired:
                try:
                    guard.release()
                except BaseException:
                    release_failed = True
            with self._guard_lock:
                current = self._stage_guards.get(effect_id)
                if current is entry:
                    entry[1] -= 1
                    if entry[1] == 0:
                        del self._stage_guards[effect_id]
            if release_failed:
                raise _error(
                    DockerHostSourceCodeV1.STORE_INDETERMINATE
                ) from None

    @staticmethod
    def _snapshot_identity(value) -> DockerEffectIdentityV1:
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
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT) from None

    @staticmethod
    def _snapshot_request(value) -> DockerSourceSealRequestV1:
        if type(value) is not DockerSourceSealRequestV1:
            raise _error(DockerHostSourceCodeV1.REQUEST_INVALID)
        try:
            identity = value.identity
            plan = PreparedDockerPlanV1(
                identity.plan.profile, identity.plan.project_ref,
                identity.plan.run_id, identity.plan.plan_fingerprint,
                identity.plan.source_digest, identity.plan.preparation_digest,
            )
            rebuilt_identity = DockerEffectIdentityV1(
                identity.command_digest, identity.effect_id,
                identity.effect_kind, plan,
            )
            rebuilt = DockerSourceSealRequestV1(
                rebuilt_identity, value.source_ref, value.source_digest
            )
            if (
                rebuilt != value
                or rebuilt.digest != value.digest
                or rebuilt.source_ref
                != rebuilt.identity.plan.profile.roots.source_ref
                or rebuilt.source_digest != rebuilt.identity.plan.source_digest
            ):
                raise ValueError
            return rebuilt
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.REQUEST_INVALID) from None

    @classmethod
    def _snapshot_lookup(cls, value):
        if type(value) is not DockerSourceSealLookupRequestV1:
            raise _error(DockerHostSourceCodeV1.REQUEST_INVALID)
        try:
            source_request = cls._snapshot_request(value.source_request)
            rebuilt = DockerSourceSealLookupRequestV1(
                source_request, value.generation
            )
            if rebuilt != value or rebuilt.digest != value.digest:
                raise ValueError
            return rebuilt
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.REQUEST_INVALID) from None

    @staticmethod
    def _snapshot_binding(value) -> BundleBindingV1:
        if type(value) is not BundleBindingV1:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
        try:
            members = tuple(
                BundleMemberEvidenceV1(
                    member.logical_name, member.physical_name, member.size,
                    member.sha256, replace(member.identity),
                )
                for member in value.members
            )
            rebuilt = BundleBindingV1(
                value.command_digest, value.destination_ref,
                value.root_authority_digest, value.private_name,
                value.marker_name, value.companion_name,
                value.manifest_digest, value.inventory_digest, members,
                replace(value.manifest_identity), replace(value.marker_identity),
                value.binding_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    @classmethod
    def _snapshot_authenticated_binding(cls, value):
        if type(value) is not AuthenticatedBundleBindingV1:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
        try:
            rebuilt = AuthenticatedBundleBindingV1(
                cls._snapshot_binding(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_seal(value):
        if type(value) is not AuthenticatedDockerSourceSealV1:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
        try:
            content = value.content
            rebuilt_content = DockerSourceSealContentV1(
                content.request_digest, content.effect_identity_digest,
                content.source_ref, content.source_digest, content.read_only,
                content.stage_ref, content.evidence_digest,
            )
            rebuilt = AuthenticatedDockerSourceSealV1(
                rebuilt_content, value.authority_ref, value.key_ref, value.tag
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_declaration(value):
        if type(value) is not AuthenticatedDockerSourceDeclarationV1:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
        try:
            content = value.content
            members = tuple(
                BundleMemberCommandV1(
                    member.logical_name, member.source_ref,
                    member.size, member.sha256,
                )
                for member in content.members
            )
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
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    @staticmethod
    def _snapshot_access(value):
        if type(value) is not BundleBorrowAccessV1:
            raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT)
        try:
            rebuilt = BundleBorrowAccessV1(
                value.destination_ref, value.root_authority_digest,
                value.create_borrow, value.create_root,
                value.verify_borrow, value.verify_root, value.access_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT) from None

    @classmethod
    def _snapshot_resolution(cls, value):
        if type(value) is not DockerSourceResolutionV1:
            raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT)
        try:
            declaration = cls._snapshot_declaration(value.declaration)
            access = cls._snapshot_access(value.bundle_access)
            rebuilt = DockerSourceResolutionV1(declaration, access)
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT) from None

    @classmethod
    def _snapshot_record(cls, value):
        if type(value) is not DockerStageBundleBindingV1:
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT)
        try:
            rebuilt = DockerStageBundleBindingV1(
                cls._snapshot_identity(value.effect_identity),
                value.stage_effect_id, value.stage_command_digest,
                value.effect_identity_digest, value.source_seal_request_digest,
                value.source_ref, value.source_digest,
                cls._snapshot_declaration(value.authenticated_declaration),
                value.authenticated_declaration_digest,
                value.bundle_command_digest, value.authenticated_binding_digest,
                value.stage_ref,
                cls._snapshot_authenticated_binding(value.authenticated_binding),
                cls._snapshot_seal(value.source_seal),
                value.source_seal_digest, value.record_digest,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerHostSourceErrorV1 as error:
            if error.code is DockerHostSourceCodeV1.AUTHENTICATION_FAILED:
                raise _error(DockerHostSourceCodeV1.STORE_CONFLICT) from None
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT) from None

    @classmethod
    def _snapshot_stage_envelope(cls, value):
        if type(value) is not AuthenticatedDockerStageBundleBindingV1:
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT)
        try:
            rebuilt = AuthenticatedDockerStageBundleBindingV1(
                cls._snapshot_record(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerHostSourceErrorV1:
            raise
        except BaseException:
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT) from None

    def _authenticate_binding(self, value):
        presented = self._snapshot_authenticated_binding(value)
        try:
            if (
                presented.authority_ref != self._binding_authority_ref
                or presented.key_ref != self._binding_key_ref
            ):
                raise ValueError
            trusted = self._snapshot_authenticated_binding(
                self._binding_authority.authenticate(presented)
            )
            if trusted != presented:
                raise ValueError
            return trusted
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    def _authenticate_seal(self, value):
        presented = self._snapshot_seal(value)
        try:
            if (
                presented.authority_ref != self._seal_authority_ref
                or presented.key_ref != self._seal_key_ref
            ):
                raise ValueError
            trusted = self._snapshot_seal(
                self._source_seal_authority.authenticate(presented)
            )
            if trusted != presented:
                raise ValueError
            return trusted
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    def _authenticate_declaration(self, value):
        presented = self._snapshot_declaration(value)
        try:
            if (
                presented.authority_ref != self._declaration_authority_ref
                or presented.key_ref != self._declaration_key_ref
            ):
                raise ValueError
            trusted = self._snapshot_declaration(
                self._declaration_authority.authenticate(presented)
            )
            if trusted != presented:
                raise ValueError
            return trusted
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    def _authenticate_stage(self, value):
        presented = self._snapshot_stage_envelope(value)
        try:
            if (
                presented.authority_ref != self._stage_authority_ref
                or presented.key_ref != self._stage_key_ref
            ):
                raise ValueError
            trusted = self._snapshot_stage_envelope(
                self._stage_record_authority.authenticate(presented)
            )
            if trusted != presented:
                raise ValueError
            return trusted
        except BaseException:
            raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None

    def _validated_record(self, value, request):
        record = self._snapshot_record(value)
        declaration = self._authenticate_declaration(
            record.authenticated_declaration
        )
        binding = self._authenticate_binding(record.authenticated_binding)
        seal = self._authenticate_seal(record.source_seal)
        if (
            record.effect_identity != request.identity
            or declaration != record.authenticated_declaration
            or binding != record.authenticated_binding
            or seal != record.source_seal
            or record.stage_effect_id != request.identity.effect_id
            or record.stage_command_digest != request.identity.command_digest
            or record.effect_identity_digest != request.identity.digest
            or record.source_seal_request_digest != request.digest
            or record.source_ref != request.source_ref
            or record.source_digest != request.source_digest
            or declaration.content.source_ref != request.source_ref
            or declaration.content.source_digest != request.source_digest
            or declaration.content.effect_identity_digest != request.identity.digest
            or declaration.content.prepared_plan_digest != request.identity.plan.digest
            or declaration.content.profile_ref
            != request.identity.plan.profile.provider.profile_ref
            or declaration.content.bundle_command_digest
            != binding.content.command_digest
            or declaration.content.destination_ref
            != binding.content.destination_ref
            or declaration.content.root_authority_digest
            != binding.content.root_authority_digest
        ):
            raise _error(DockerHostSourceCodeV1.STORE_CONFLICT)
        return record

    def _get(self, request):
        try:
            value = self._store.get_by_stage_effect_id(
                request.identity.effect_id
            )
        except BaseException:
            raise _error(DockerHostSourceCodeV1.STORE_INDETERMINATE) from None
        if value is None:
            return None
        envelope = self._authenticate_stage(value)
        self._validated_record(envelope.content, request)
        return envelope

    def seal_read_only(self, request):
        request = self._snapshot_request(request)
        with self._stage_guard(request.identity.effect_id):
            retained = self._get(request)
            if retained is not None:
                return retained.content.source_seal
            try:
                resolution = self._snapshot_resolution(
                    self._declarations.resolve(request)
                )
            except DockerHostSourceErrorV1:
                raise
            except BaseException:
                raise _error(
                    DockerHostSourceCodeV1.DECLARATION_CONFLICT
                ) from None
            declaration = self._authenticate_declaration(
                resolution.declaration
            )
            content = declaration.content
            profile = request.identity.plan.profile
            if (
                content.source_ref != request.source_ref
                or content.source_digest != request.source_digest
                or content.effect_identity_digest != request.identity.digest
                or content.prepared_plan_digest != request.identity.plan.digest
                or content.profile_ref != profile.provider.profile_ref
                or content.destination_ref != resolution.bundle_access.destination_ref
                or content.root_authority_digest
                != resolution.bundle_access.root_authority_digest
                or content.bundle_access_digest
                != resolution.bundle_access.access_digest
            ):
                raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT)
            command = BundleSealCommandV1.build(
                content.profile_ref, content.purpose_ref,
                content.destination_ref, content.members,
            )
            if command.command_digest != content.bundle_command_digest:
                raise _error(DockerHostSourceCodeV1.DECLARATION_CONFLICT)
            try:
                result = self._bundle.seal(command, resolution.bundle_access)
            except BaseException:
                raise _error(DockerHostSourceCodeV1.BUNDLE_INDETERMINATE) from None
            if type(result) is not BundleLookupResultV1:
                raise _error(DockerHostSourceCodeV1.BUNDLE_INDETERMINATE)
            if result.status is BundleLookupStatusV1.CONFLICT:
                raise _error(DockerHostSourceCodeV1.BUNDLE_CONFLICT)
            if (
                result.status is not BundleLookupStatusV1.FOUND
                or type(result.binding) is not BundleBindingV1
                or result.command_digest != command.command_digest
            ):
                raise _error(DockerHostSourceCodeV1.BUNDLE_INDETERMINATE)
            binding_content = self._snapshot_binding(result.binding)
            expected_members = tuple(
                (
                    member.logical_name,
                    f"member-{index:04d}",
                    member.size,
                    member.sha256,
                )
                for index, member in enumerate(content.members)
            )
            observed_members = tuple(
                (
                    member.logical_name, member.physical_name,
                    member.size, member.sha256,
                )
                for member in binding_content.members
            )
            if (
                binding_content.command_digest != command.command_digest
                or binding_content.destination_ref != content.destination_ref
                or binding_content.destination_ref
                != resolution.bundle_access.destination_ref
                or binding_content.root_authority_digest
                != content.root_authority_digest
                or binding_content.root_authority_digest
                != resolution.bundle_access.root_authority_digest
                or observed_members != expected_members
            ):
                raise _error(DockerHostSourceCodeV1.BUNDLE_CONFLICT)
            try:
                issued_binding = self._binding_authority.issue(binding_content)
            except BaseException:
                raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None
            binding = self._authenticate_binding(issued_binding)
            stage_ref = "bundle-" + binding.proof_digest
            seal_content = DockerSourceSealContentV1(
                request.digest, request.identity.digest, request.source_ref,
                request.source_digest, True, stage_ref, binding.proof_digest,
            )
            try:
                issued_seal = self._source_seal_authority.issue(seal_content)
            except BaseException:
                raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None
            seal = self._authenticate_seal(issued_seal)
            if seal.content != seal_content:
                raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
            record = DockerStageBundleBindingV1.build(
                effect_identity=request.identity,
                source_seal_request_digest=request.digest,
                source_ref=request.source_ref,
                source_digest=request.source_digest,
                authenticated_declaration=declaration,
                bundle_command_digest=command.command_digest,
                authenticated_binding=binding,
                source_seal=seal,
            )
            try:
                issued_stage = self._stage_record_authority.issue(record)
            except BaseException:
                raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED) from None
            stage_envelope = self._authenticate_stage(issued_stage)
            if stage_envelope.content != record:
                raise _error(DockerHostSourceCodeV1.AUTHENTICATION_FAILED)
            try:
                self._store.put_if_absent(stage_envelope)
            except BaseException:
                pass
            retained = self._get(request)
            if retained is None:
                raise _error(DockerHostSourceCodeV1.STORE_INDETERMINATE)
            if retained != stage_envelope:
                raise _error(DockerHostSourceCodeV1.STORE_CONFLICT)
            return retained.content.source_seal

    def lookup(self, request):
        try:
            lookup = self._snapshot_lookup(request)
            source_request = lookup.source_request
            retained = self._get(source_request)
            if retained is None:
                return DockerSourceSealLookupResultV1(
                    DockerLookupDispositionV1.INDETERMINATE
                )
            return DockerSourceSealLookupResultV1(
                DockerLookupDispositionV1.FOUND,
                seal=retained.content.source_seal,
            )
        except DockerHostSourceErrorV1 as error:
            if error.code is DockerHostSourceCodeV1.REQUEST_INVALID:
                raise
            return DockerSourceSealLookupResultV1(
                DockerLookupDispositionV1.INDETERMINATE
            )
        except BaseException:
            return DockerSourceSealLookupResultV1(
                DockerLookupDispositionV1.INDETERMINATE
            )


__all__: tuple[str, ...] = ()
