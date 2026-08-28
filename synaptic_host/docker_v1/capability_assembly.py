"""Linear same-process acquisition and cleanup for Docker capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Condition, Lock, get_ident

from synaptic_host.bundle_io_v1.ports import BundleBorrowAccessV1, BundleSourceV1
from synaptic_host.bundle_io_v1.model import BundleIOCodeV1, checked_ref_v1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    BorrowedDirectoryV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootAuthorityV1,
    LocalRootBindingV1,
    RetainedRootBorrowRequestV1,
    RetainedRootBorrowV1,
    RootAccessV1,
    canonical_relative_components_v1,
    digest_v1,
)


class DockerCapabilitySlotV1(str, Enum):
    SOURCE_ROOT_AUTHORITY = "source_root_authority"
    SOURCE_READ_BORROW = "source_read_borrow"
    STAGE_ROOT_AUTHORITY = "stage_root_authority"
    STAGE_CREATE_BORROW = "stage_create_borrow"
    STAGE_VERIFY_BORROW = "stage_verify_borrow"
    ARTIFACT_ROOT_AUTHORITY = "artifact_root_authority"


_ORDER = tuple(DockerCapabilitySlotV1)


class DockerCapabilityResourceKindV1(str, Enum):
    ROOT_AUTHORITY = "root_authority"
    ROOT_BORROW = "root_borrow"


class DockerCapabilityAssemblyCodeV1(str, Enum):
    INPUT_INVALID = "DOCKER_CAPABILITY_INPUT_INVALID"
    ACQUISITION_FAILED = "DOCKER_CAPABILITY_ACQUISITION_FAILED"
    ASSEMBLY_FAILED = "DOCKER_CAPABILITY_ASSEMBLY_FAILED"
    CLEANUP_FAILED = "DOCKER_CAPABILITY_CLEANUP_FAILED"
    BUILD_CLOSED = "DOCKER_CAPABILITY_BUILD_CLOSED"
    OWNERSHIP_TRANSFERRED = "DOCKER_CAPABILITY_OWNERSHIP_TRANSFERRED"


class DockerCapabilityCleanupStatusV1(str, Enum):
    CLEANED = "cleaned"
    CLEANUP_FAILED = "cleanup_failed"


class DockerCapabilityCleanupFailureClassV1(str, Enum):
    LOCAL_IO = "local_io"
    CLOSED = "closed"


class DockerCapabilityCleanupObservationCodeV1(str, Enum):
    REENTRANT_CLEANUP_IN_PROGRESS = "reentrant_cleanup_in_progress"


@dataclass(frozen=True, slots=True)
class DockerCapabilityCleanupFailureV1:
    slot: DockerCapabilitySlotV1
    resource_kind: DockerCapabilityResourceKindV1
    failure_class: DockerCapabilityCleanupFailureClassV1
    local_io_code: LocalIOCodeV1 | None

    def __post_init__(self):
        is_local = self.failure_class is DockerCapabilityCleanupFailureClassV1.LOCAL_IO
        if (
            type(self.slot) is not DockerCapabilitySlotV1
            or type(self.resource_kind) is not DockerCapabilityResourceKindV1
            or type(self.failure_class) is not DockerCapabilityCleanupFailureClassV1
            or (self.local_io_code is not None and type(self.local_io_code) is not LocalIOCodeV1)
            or is_local != (self.local_io_code is not None)
        ):
            raise ValueError("invalid Docker capability cleanup failure")

    def canonical(self):
        return {
            "failure_class": self.failure_class.value,
            "local_io_code": self.local_io_code.value if self.local_io_code is not None else None,
            "resource_kind": self.resource_kind.value,
            "slot": self.slot.value,
        }


@dataclass(frozen=True, slots=True)
class DockerCapabilityCleanupResultV1:
    status: DockerCapabilityCleanupStatusV1
    attempted_count: int
    released_count: int
    provisional_attempted_count: int
    failures: tuple[DockerCapabilityCleanupFailureV1, ...]
    result_digest: str

    def __post_init__(self):
        valid_counts = (
            type(self.attempted_count) is int
            and type(self.released_count) is int
            and type(self.provisional_attempted_count) is int
            and 0 <= self.released_count <= self.attempted_count
            and 0 <= self.provisional_attempted_count <= self.attempted_count
        )
        valid_failures = (
            type(self.failures) is tuple
            and all(type(value) is DockerCapabilityCleanupFailureV1 for value in self.failures)
            and len(self.failures) == self.attempted_count - self.released_count
        )
        valid_status = (
            type(self.status) is DockerCapabilityCleanupStatusV1
            and (self.status is DockerCapabilityCleanupStatusV1.CLEANED) == (not self.failures)
        )
        if not (valid_counts and valid_failures and valid_status):
            raise ValueError("invalid Docker capability cleanup result")
        if self.result_digest != digest_v1(self.canonical_without_digest()):
            raise ValueError("invalid Docker capability cleanup result")

    def canonical_without_digest(self):
        return {
            "attempted_count": self.attempted_count,
            "failures": [value.canonical() for value in self.failures],
            "provisional_attempted_count": self.provisional_attempted_count,
            "released_count": self.released_count,
            "schema": "synaptic-host-docker-capability-cleanup-result/v1",
            "status": self.status.value,
        }

    @classmethod
    def build(cls, attempted, released, provisional, failures):
        failures = tuple(failures)
        status = DockerCapabilityCleanupStatusV1.CLEANUP_FAILED if failures else DockerCapabilityCleanupStatusV1.CLEANED
        body = {
            "attempted_count": attempted,
            "failures": [value.canonical() for value in failures],
            "provisional_attempted_count": provisional,
            "released_count": released,
            "schema": "synaptic-host-docker-capability-cleanup-result/v1",
            "status": status.value,
        }
        return cls(status, attempted, released, provisional, failures, digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerCapabilityCleanupObservationV1:
    code: DockerCapabilityCleanupObservationCodeV1

    def __post_init__(self):
        if self.code is not DockerCapabilityCleanupObservationCodeV1.REENTRANT_CLEANUP_IN_PROGRESS:
            raise ValueError("invalid Docker capability cleanup observation")


class DockerCapabilityAssemblyErrorV1(RuntimeError):
    __slots__ = ("code", "cleanup_result")

    def __init__(self, code, cleanup_result=None):
        if type(code) is not DockerCapabilityAssemblyCodeV1:
            code = DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED
        if cleanup_result is not None and type(cleanup_result) is not DockerCapabilityCleanupResultV1:
            cleanup_result = None
        RuntimeError.__init__(self, code.value)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "cleanup_result", cleanup_result)

    def __setattr__(self, name, value):
        if name in {"code", "cleanup_result"}:
            raise AttributeError("immutable Docker capability assembly error")
        BaseException.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class DockerCapabilityAssemblyV1:
    source_root_authority: LocalRootAuthorityV1
    source_read_borrow: RetainedRootBorrowV1
    source_read_root: BorrowedDirectoryV1
    source: BundleSourceV1
    stage_root_authority: LocalRootAuthorityV1
    stage_create_borrow: RetainedRootBorrowV1
    stage_create_root: BorrowedDirectoryV1
    stage_verify_borrow: RetainedRootBorrowV1
    stage_verify_root: BorrowedDirectoryV1
    stage_access: BundleBorrowAccessV1
    artifact_root_authority: LocalRootAuthorityV1
    artifact_access_digest: str

    def __post_init__(self):
        exact = (
            type(self.source_root_authority) is LocalRootAuthorityV1,
            type(self.source_read_borrow) is RetainedRootBorrowV1,
            type(self.source_read_root) is BorrowedDirectoryV1,
            type(self.source) is BundleSourceV1,
            type(self.stage_root_authority) is LocalRootAuthorityV1,
            type(self.stage_create_borrow) is RetainedRootBorrowV1,
            type(self.stage_create_root) is BorrowedDirectoryV1,
            type(self.stage_verify_borrow) is RetainedRootBorrowV1,
            type(self.stage_verify_root) is BorrowedDirectoryV1,
            type(self.stage_access) is BundleBorrowAccessV1,
            type(self.artifact_root_authority) is LocalRootAuthorityV1,
            type(self.artifact_access_digest) is str,
        )
        if not all(exact) or (
            self.source.borrow is not self.source_read_borrow
            or self.source.directory is not self.source_read_root
            or self.stage_access.create_borrow is not self.stage_create_borrow
            or self.stage_access.create_root is not self.stage_create_root
            or self.stage_access.verify_borrow is not self.stage_verify_borrow
            or self.stage_access.verify_root is not self.stage_verify_root
            or self.artifact_access_digest != self.artifact_root_authority.data_binding.binding_digest
        ):
            raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)


@dataclass(frozen=True, slots=True)
class _NodeV1:
    slot: DockerCapabilitySlotV1
    resource_kind: DockerCapabilityResourceKindV1
    capability: object
    stable_key: tuple[str, str]
    parent_token: object | None
    token: object
    cleanup: object


def _failure(slot, kind, error):
    if type(error) is LocalIOErrorV1 and type(error.code) is LocalIOCodeV1:
        return DockerCapabilityCleanupFailureV1(slot, kind, DockerCapabilityCleanupFailureClassV1.LOCAL_IO, error.code)
    return DockerCapabilityCleanupFailureV1(slot, kind, DockerCapabilityCleanupFailureClassV1.CLOSED, None)


class _CleanupAccountingV1:
    __slots__ = ("attempted", "released", "provisional", "failures")

    def __init__(self):
        self.attempted = 0
        self.released = 0
        self.provisional = 0
        self.failures = []

    def attempt(self, slot, kind, cleanup, capability, *, provisional):
        self.attempted += 1
        if provisional:
            self.provisional += 1
        try:
            cleanup(capability)
        except BaseException as error:
            self.failures.append(_failure(slot, kind, error))
        else:
            self.released += 1

    def result(self):
        return DockerCapabilityCleanupResultV1.build(self.attempted, self.released, self.provisional, self.failures)


class _GuardStateV1(str, Enum):
    ARMED = "armed"
    DISARMED_ENROLLED = "disarmed_enrolled"
    DISARMED_ENROLLED_COLLISION = "disarmed_enrolled_collision"
    DIRECT_CLEANED = "direct_cleaned"


class _ProvisionalGuardV1:
    __slots__ = ("_accounting", "_slot", "_kind", "_cleanup", "_capability", "state")

    def __init__(self, accounting, slot, kind, cleanup):
        self._accounting = accounting
        self._slot = slot
        self._kind = kind
        self._cleanup = cleanup
        self._capability = None
        self.state = _GuardStateV1.ARMED

    def bind(self, capability):
        if self.state is not _GuardStateV1.ARMED:
            raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)
        self._capability = capability

    def enrolled(self):
        self.state = _GuardStateV1.DISARMED_ENROLLED

    def collision(self):
        self.state = _GuardStateV1.DISARMED_ENROLLED_COLLISION

    def direct_cleanup(self):
        if self.state is not _GuardStateV1.ARMED or self._capability is None:
            return
        self.state = _GuardStateV1.DIRECT_CLEANED
        self._accounting.attempt(
            self._slot, self._kind, self._cleanup, self._capability,
            provisional=True,
        )


class _LedgerV1:
    __slots__ = ("nodes", "by_slot", "accounting")

    def __init__(self):
        self.nodes = []
        self.by_slot = {}
        self.accounting = _CleanupAccountingV1()

    @staticmethod
    def stable_key(kind, capability):
        if kind is DockerCapabilityResourceKindV1.ROOT_AUTHORITY:
            return capability.authority_ref, capability.authority_digest
        return capability.borrow_ref, capability.borrow_digest

    def enroll(self, slot, kind, capability, parent_slot, parent_token, cleanup, guard):
        try:
            if any(node.capability is capability for node in self.nodes):
                guard.collision()
                raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)
            stable_key = self.stable_key(kind, capability)
            if slot in self.by_slot or any(
                node.resource_kind is kind and node.stable_key == stable_key
                for node in self.nodes
            ):
                raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)
            if parent_slot is None:
                parent_is_exact = parent_token is None
            else:
                parent = self.by_slot.get(parent_slot)
                parent_is_exact = parent is not None and parent.token is parent_token
            if not parent_is_exact:
                raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)
            token = object()
            node = _NodeV1(slot, kind, capability, stable_key, parent_token, token, cleanup)
            self.nodes.append(node)
            self.by_slot[slot] = node
            guard.enrolled()
            return token
        except BaseException:
            guard.direct_cleanup()
            raise

    def complete(self):
        if tuple(node.slot for node in self.nodes) != _ORDER:
            raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED)

    def detach(self):
        self.complete()
        nodes = tuple(self.nodes)
        self.nodes.clear()
        self.by_slot.clear()
        return nodes

    def abort(self):
        nodes = tuple(self.nodes)
        self.nodes.clear()
        self.by_slot.clear()
        return _cleanup_nodes(nodes, self.accounting)


def _cleanup_nodes(nodes, accounting=None):
    accounting = accounting or _CleanupAccountingV1()
    for node in reversed(nodes):
        accounting.attempt(
            node.slot, node.resource_kind, node.cleanup, node.capability,
            provisional=False,
        )
    return accounting.result()


_REENTRANT = DockerCapabilityCleanupObservationV1(
    DockerCapabilityCleanupObservationCodeV1.REENTRANT_CLEANUP_IN_PROGRESS
)


class DockerCapabilityOwnershipV1:
    __slots__ = ("_nodes", "_condition", "_state", "_owner", "_result")

    def __init__(self, nodes):
        self._nodes = nodes
        self._condition = Condition(Lock())
        self._state = "owning"
        self._owner = None
        self._result = None

    def cleanup(self):
        thread_id = get_ident()
        with self._condition:
            if self._state == "cleaned":
                return self._result
            if self._state == "cleaning":
                if self._owner == thread_id:
                    return _REENTRANT
                while self._state == "cleaning":
                    self._condition.wait()
                return self._result
            self._state = "cleaning"
            self._owner = thread_id
        result = _cleanup_nodes(self._nodes)
        with self._condition:
            self._nodes = ()
            self._result = result
            self._owner = None
            self._state = "cleaned"
            self._condition.notify_all()
            return result


class DockerLiveCapabilityBuildV1:
    """A completed assembly that still owns its acquisition ledger."""

    __slots__ = ("_assembly", "_ledger", "_condition", "_state", "_owner", "_result")

    def __init__(self, assembly, ledger):
        self._assembly = assembly
        self._ledger = ledger
        self._condition = Condition(Lock())
        self._state = "owning"
        self._owner = None
        self._result = None

    @property
    def assembly(self):
        with self._condition:
            if self._state == "owning":
                return self._assembly
            code = (
                DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED
                if self._state == "transferred"
                else DockerCapabilityAssemblyCodeV1.BUILD_CLOSED
            )
            raise DockerCapabilityAssemblyErrorV1(code)

    def transfer(self):
        with self._condition:
            if self._state != "owning":
                code = (
                    DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED
                    if self._state == "transferred"
                    else DockerCapabilityAssemblyCodeV1.BUILD_CLOSED
                )
                raise DockerCapabilityAssemblyErrorV1(code)
            self._ledger.complete()
            nodes = tuple(self._ledger.nodes)
            ownership = DockerCapabilityOwnershipV1(nodes)
            self._ledger.detach()
            self._ledger = None
            self._assembly = None
            self._state = "transferred"
            self._condition.notify_all()
            return ownership

    def abort(self):
        thread_id = get_ident()
        with self._condition:
            if self._state == "transferred":
                raise DockerCapabilityAssemblyErrorV1(DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED)
            if self._state == "aborted":
                return self._result
            if self._state == "aborting":
                if self._owner == thread_id:
                    return _REENTRANT
                while self._state == "aborting":
                    self._condition.wait()
                return self._result
            self._state = "aborting"
            self._owner = thread_id
            ledger = self._ledger
        result = ledger.abort()
        with self._condition:
            self._ledger = None
            self._assembly = None
            self._result = result
            self._owner = None
            self._state = "aborted"
            self._condition.notify_all()
            return result


class DockerCapabilityAssemblyBuilderV1:
    """One-use builder that returns a live, explicitly transferable build."""

    def __init__(
        self, *, filesystem,
        source_data_binding, source_control_binding, source_ref,
        source_component, stage_data_binding, stage_control_binding,
        stage_destination_ref, artifact_data_binding,
        artifact_control_binding,
    ):
        for binding in (
            source_data_binding, source_control_binding,
            stage_data_binding, stage_control_binding,
            artifact_data_binding, artifact_control_binding,
        ):
            if type(binding) is not LocalRootBindingV1:
                raise DockerCapabilityAssemblyErrorV1(
                    DockerCapabilityAssemblyCodeV1.INPUT_INVALID
                )
        try:
            checked_ref_v1(source_ref, BundleIOCodeV1.SOURCE_INVALID)
            checked_ref_v1(stage_destination_ref, BundleIOCodeV1.ACCESS_INVALID)
            if canonical_relative_components_v1(source_component) != (
                source_component,
            ):
                raise ValueError
        except BaseException:
            raise DockerCapabilityAssemblyErrorV1(
                DockerCapabilityAssemblyCodeV1.INPUT_INVALID
            ) from None
        self._filesystem = filesystem
        self._source_data = source_data_binding
        self._source_control = source_control_binding
        self._source_ref = source_ref
        self._source_component = source_component
        self._stage_data = stage_data_binding
        self._stage_control = stage_control_binding
        self._stage_destination_ref = stage_destination_ref
        self._artifact_data = artifact_data_binding
        self._artifact_control = artifact_control_binding
        self._used = False
        self._use_lock = Lock()

    def _retain(self, ledger, slot, data, control):
        kind = DockerCapabilityResourceKindV1.ROOT_AUTHORITY
        cleanup = self._filesystem.release_root_authority
        guard = _ProvisionalGuardV1(ledger.accounting, slot, kind, cleanup)
        capability = self._filesystem.retain_root_authority(data, control)
        guard.bind(capability)
        if type(capability) is not LocalRootAuthorityV1:
            guard.direct_cleanup()
            raise DockerCapabilityAssemblyErrorV1(
                DockerCapabilityAssemblyCodeV1.ACQUISITION_FAILED
            )
        token = ledger.enroll(
            slot, kind, capability, None, None, cleanup, guard
        )
        return capability, token

    def _borrow(
        self, ledger, slot, authority, parent_slot, parent_token, purpose, access
    ):
        kind = DockerCapabilityResourceKindV1.ROOT_BORROW
        cleanup = lambda value: self._filesystem.release_borrow(
            value, purpose=purpose
        )
        guard = _ProvisionalGuardV1(ledger.accounting, slot, kind, cleanup)
        request = RetainedRootBorrowRequestV1.build(
            authority.authority_digest, purpose, access
        )
        capability = self._filesystem.borrow_root(authority, request)
        guard.bind(capability)
        if type(capability) is not RetainedRootBorrowV1:
            guard.direct_cleanup()
            raise DockerCapabilityAssemblyErrorV1(
                DockerCapabilityAssemblyCodeV1.ACQUISITION_FAILED
            )
        ledger.enroll(
            slot, kind, capability, parent_slot, parent_token, cleanup, guard
        )
        root = self._filesystem.root_directory(capability, purpose=purpose)
        if type(root) is not BorrowedDirectoryV1:
            raise DockerCapabilityAssemblyErrorV1(
                DockerCapabilityAssemblyCodeV1.ACQUISITION_FAILED
            )
        return capability, root

    def build(self):
        with self._use_lock:
            if self._used:
                raise DockerCapabilityAssemblyErrorV1(
                    DockerCapabilityAssemblyCodeV1.BUILD_CLOSED
                )
            self._used = True
        ledger = _LedgerV1()
        failure_code = DockerCapabilityAssemblyCodeV1.ACQUISITION_FAILED
        try:
            source_root, source_token = self._retain(
                ledger, DockerCapabilitySlotV1.SOURCE_ROOT_AUTHORITY,
                self._source_data, self._source_control,
            )
            source_borrow, source_directory = self._borrow(
                ledger, DockerCapabilitySlotV1.SOURCE_READ_BORROW,
                source_root, DockerCapabilitySlotV1.SOURCE_ROOT_AUTHORITY,
                source_token,
                BorrowPurposeV1.BUNDLE_SOURCE_READ, RootAccessV1.READ_ONLY,
            )
            stage_root, stage_token = self._retain(
                ledger, DockerCapabilitySlotV1.STAGE_ROOT_AUTHORITY,
                self._stage_data, self._stage_control,
            )
            create_borrow, create_directory = self._borrow(
                ledger, DockerCapabilitySlotV1.STAGE_CREATE_BORROW,
                stage_root, DockerCapabilitySlotV1.STAGE_ROOT_AUTHORITY,
                stage_token,
                BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
                RootAccessV1.READ_CREATE,
            )
            verify_borrow, verify_directory = self._borrow(
                ledger, DockerCapabilitySlotV1.STAGE_VERIFY_BORROW,
                stage_root, DockerCapabilitySlotV1.STAGE_ROOT_AUTHORITY,
                stage_token,
                BorrowPurposeV1.BUNDLE_MOUNT_VERIFY, RootAccessV1.READ_ONLY,
            )
            artifact_root, _artifact_token = self._retain(
                ledger, DockerCapabilitySlotV1.ARTIFACT_ROOT_AUTHORITY,
                self._artifact_data, self._artifact_control,
            )
            ledger.complete()
            failure_code = DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED
            source = BundleSourceV1.build(
                self._source_ref, source_borrow,
                source_directory, self._source_component,
            )
            access = BundleBorrowAccessV1.build(
                self._stage_destination_ref,
                create_borrow, create_directory,
                verify_borrow, verify_directory,
            )
            assembly = DockerCapabilityAssemblyV1(
                source_root, source_borrow, source_directory, source,
                stage_root, create_borrow, create_directory,
                verify_borrow, verify_directory, access,
                artifact_root, self._artifact_data.binding_digest,
            )
            return DockerLiveCapabilityBuildV1(assembly, ledger)
        except BaseException as error:
            if type(error) is DockerCapabilityAssemblyErrorV1:
                failure_code = error.code
            result = ledger.abort()
            code = (
                DockerCapabilityAssemblyCodeV1.CLEANUP_FAILED
                if result.status is DockerCapabilityCleanupStatusV1.CLEANUP_FAILED
                else failure_code
            )
            raise DockerCapabilityAssemblyErrorV1(code, result) from None


__all__: tuple[str, ...] = ()
