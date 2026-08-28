from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest

from synaptic_host.docker_v1.capability_assembly import (
    DockerCapabilityAssemblyBuilderV1,
    DockerCapabilityAssemblyCodeV1,
    DockerCapabilityAssemblyErrorV1,
    DockerCapabilityCleanupObservationCodeV1,
    DockerCapabilityCleanupObservationV1,
    DockerCapabilityCleanupStatusV1,
    DockerCapabilitySlotV1,
    DockerLiveCapabilityBuildV1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
)

from bundle_io_v1.conftest import Authenticator
from local_io_v1.conftest import FakePosixFilesystemPortV1


class _TracingFilesystem:
    def __init__(self, inner):
        self.inner = inner
        self.release_order = []
        self.reenter = None
        self.fail_after_release = {}

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def _after(self, value):
        callback = self.reenter
        self.reenter = None
        if callback is not None:
            callback()
        failure = self.fail_after_release.get(id(value))
        if failure is not None:
            raise failure

    def release_borrow(self, value, *, purpose):
        self.release_order.append((purpose.value, value))
        self.inner.release_borrow(value, purpose=purpose)
        self._after(value)

    def release_root_authority(self, value):
        self.release_order.append(("root", value))
        self.inner.release_root_authority(value)
        self._after(value)


def _builder_environment():
    port = FakePosixFilesystemPortV1()
    authenticator = Authenticator()
    base = Path.cwd() / ".fake-metadata" / "capability-assembly-r1"
    labels = (
        "source-data", "source-control", "stage-data", "stage-control",
        "artifact-data", "artifact-control",
    )
    paths = {label: base / label for label in labels}
    for label, path in paths.items():
        port.add_root(path, label)
    bindings = {
        label: authenticator.binding(paths[label], label) for label in labels
    }
    real = LocalFilesystemV1(port, authenticator, native_platform="linux")
    filesystem = _TracingFilesystem(real)
    builder = _make_builder(filesystem, bindings)
    return builder, filesystem, port, bindings


def _make_builder(filesystem, bindings, *, source_ref="dataset-source"):
    return DockerCapabilityAssemblyBuilderV1(
        filesystem=filesystem,
        source_data_binding=bindings["source-data"],
        source_control_binding=bindings["source-control"],
        source_ref=source_ref,
        source_component="dataset-source",
        stage_data_binding=bindings["stage-data"],
        stage_control_binding=bindings["stage-control"],
        stage_destination_ref="stage-destination",
        artifact_data_binding=bindings["artifact-data"],
        artifact_control_binding=bindings["artifact-control"],
    )


def _closed(call, code):
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        call()
    assert caught.value.code is code
    assert caught.value.cleanup_result is None


def test_live_build_keeps_fallible_gap_owned_until_abort_or_explicit_transfer():
    builder, _filesystem, port, bindings = _builder_environment()
    live = builder.build()
    assert type(live) is DockerLiveCapabilityBuildV1
    assembly = live.assembly
    assert assembly.source.borrow is assembly.source_read_borrow
    assert assembly.stage_access.verify_root is assembly.stage_verify_root
    assert assembly.artifact_access_digest == bindings["artifact-data"].binding_digest

    with pytest.raises(RuntimeError):
        raise RuntimeError("b5 fallible gap")
    aborted = live.abort()
    assert aborted.status is DockerCapabilityCleanupStatusV1.CLEANED
    assert (aborted.attempted_count, aborted.released_count) == (6, 6)
    assert aborted.provisional_attempted_count == 0
    assert port.live_directories == {}
    assert live.abort() is aborted
    _closed(lambda: live.assembly, DockerCapabilityAssemblyCodeV1.BUILD_CLOSED)
    _closed(live.transfer, DockerCapabilityAssemblyCodeV1.BUILD_CLOSED)
    _closed(builder.build, DockerCapabilityAssemblyCodeV1.BUILD_CLOSED)

    second_builder, _second_fs, second_port, _ = _builder_environment()
    second_live = second_builder.build()
    ownership = second_live.transfer()
    _closed(second_live.transfer, DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED)
    _closed(second_live.abort, DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED)
    _closed(lambda: second_live.assembly, DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED)
    cleaned = ownership.cleanup()
    assert cleaned.attempted_count == cleaned.released_count == 6
    assert ownership.cleanup() is cleaned
    assert second_port.live_directories == {}


def test_abort_is_reverse_order_reentrant_safe_and_concurrently_cached():
    builder, filesystem, port, _bindings = _builder_environment()
    live = builder.build()
    assembly = live.assembly
    observed = []
    filesystem.reenter = lambda: observed.append(live.abort())
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _index: live.abort(), range(24)))
    assert type(observed[0]) is DockerCapabilityCleanupObservationV1
    assert observed[0].code is DockerCapabilityCleanupObservationCodeV1.REENTRANT_CLEANUP_IN_PROGRESS
    assert all(value is results[0] for value in results)
    assert results[0].status is DockerCapabilityCleanupStatusV1.CLEANED
    assert filesystem.release_order == [
        ("root", assembly.artifact_root_authority),
        (BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value, assembly.stage_verify_borrow),
        (BorrowPurposeV1.BUNDLE_DESTINATION_CREATE.value, assembly.stage_create_borrow),
        ("root", assembly.stage_root_authority),
        (BorrowPurposeV1.BUNDLE_SOURCE_READ.value, assembly.source_read_borrow),
        ("root", assembly.source_root_authority),
    ]
    assert port.live_directories == {}


def test_transfer_abort_race_has_one_winner_and_no_double_release():
    builder, _filesystem, port, _bindings = _builder_environment()
    live = builder.build()
    start = Event()

    def transfer():
        start.wait()
        try:
            return "transfer", live.transfer()
        except DockerCapabilityAssemblyErrorV1 as error:
            return "transfer-error", error.code

    def abort():
        start.wait()
        try:
            return "abort", live.abort()
        except DockerCapabilityAssemblyErrorV1 as error:
            return "abort-error", error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = (pool.submit(transfer), pool.submit(abort))
        start.set()
        outcomes = [value.result() for value in pending]
    successes = [value for label, value in outcomes if label in {"transfer", "abort"}]
    assert len(successes) == 1
    winner = successes[0]
    if hasattr(winner, "cleanup"):
        assert ("abort-error", DockerCapabilityAssemblyCodeV1.OWNERSHIP_TRANSFERRED) in outcomes
        result = winner.cleanup()
    else:
        assert ("transfer-error", DockerCapabilityAssemblyCodeV1.BUILD_CLOSED) in outcomes
        result = winner
    assert result.attempted_count == result.released_count == 6
    assert port.live_directories == {}


class _ScriptedFilesystem:
    def __init__(self, assembly, *, roots=None, borrows=None):
        self.assembly = assembly
        self.roots = list(roots or (
            assembly.source_root_authority,
            assembly.stage_root_authority,
            assembly.artifact_root_authority,
        ))
        self.borrows = list(borrows or (
            assembly.source_read_borrow,
            assembly.stage_create_borrow,
            assembly.stage_verify_borrow,
        ))
        self.released = []
        self.fail_release_ids = {}

    def retain_root_authority(self, data, control):
        return self.roots.pop(0)

    def borrow_root(self, authority, request):
        return self.borrows.pop(0)

    def root_directory(self, borrow, *, purpose):
        roots = {
            id(self.assembly.source_read_borrow): self.assembly.source_read_root,
            id(self.assembly.stage_create_borrow): self.assembly.stage_create_root,
            id(self.assembly.stage_verify_borrow): self.assembly.stage_verify_root,
        }
        return roots[id(borrow)]

    def _release(self, kind, value):
        self.released.append((kind, value))
        error = self.fail_release_ids.get(id(value))
        if error is not None:
            raise error

    def release_borrow(self, value, *, purpose):
        self._release("borrow", value)

    def release_root_authority(self, value):
        self._release("root", value)


def _seed_and_script():
    seed_builder, _seed_fs, _port, bindings = _builder_environment()
    seed_live = seed_builder.build()
    return seed_live, seed_live.assembly, bindings


@pytest.mark.parametrize("collision", ("stage-root", "stage-create", "stage-verify", "artifact-root"))
def test_exact_collision_has_zero_provisional_attempts_and_one_ledger_release(collision):
    seed_live, assembly, bindings = _seed_and_script()
    roots = [assembly.source_root_authority, assembly.stage_root_authority, assembly.artifact_root_authority]
    borrows = [assembly.source_read_borrow, assembly.stage_create_borrow, assembly.stage_verify_borrow]
    if collision == "stage-root":
        roots[1] = roots[0]
        collided = roots[0]
    elif collision == "stage-create":
        borrows[1] = borrows[0]
        collided = borrows[0]
    elif collision == "stage-verify":
        borrows[2] = borrows[1]
        collided = borrows[1]
    else:
        roots[2] = roots[1]
        collided = roots[1]
    scripted = _ScriptedFilesystem(assembly, roots=roots, borrows=borrows)
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        _make_builder(scripted, bindings).build()
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED
    result = caught.value.cleanup_result
    assert result.provisional_attempted_count == 0
    assert sum(value is collided for _kind, value in scripted.released) == 1
    seed_live.abort()


def test_stable_root_key_rejects_distinct_handle_projection_and_direct_cleans_once():
    seed_live, assembly, bindings = _seed_and_script()
    directory = replace(
        assembly.source_root_authority.data_directory,
        handle_ref="different-live-handle",
    )
    distinct = replace(
        assembly.source_root_authority,
        data_directory=directory,
    )
    assert distinct is not assembly.source_root_authority
    assert distinct.authority_ref == assembly.source_root_authority.authority_ref
    assert distinct.authority_digest == assembly.source_root_authority.authority_digest
    scripted = _ScriptedFilesystem(
        assembly,
        roots=(assembly.source_root_authority, distinct),
    )
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        _make_builder(scripted, bindings).build()
    result = caught.value.cleanup_result
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED
    assert result.provisional_attempted_count == 1
    assert sum(value is distinct for _kind, value in scripted.released) == 1
    assert sum(value is assembly.source_root_authority for _kind, value in scripted.released) == 1
    seed_live.abort()


def test_stable_borrow_key_rejects_distinct_object_without_dataclass_equality():
    seed_live, assembly, bindings = _seed_and_script()
    distinct = replace(assembly.source_read_borrow)
    scripted = _ScriptedFilesystem(
        assembly,
        borrows=(assembly.source_read_borrow, distinct),
    )
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        _make_builder(scripted, bindings).build()
    result = caught.value.cleanup_result
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.ASSEMBLY_FAILED
    assert result.provisional_attempted_count == 1
    assert sum(value is distinct for _kind, value in scripted.released) == 1
    seed_live.abort()


def test_provisional_cleanup_failure_is_terminal_sanitized_and_not_discarded():
    seed_live, assembly, bindings = _seed_and_script()
    distinct = replace(
        assembly.source_root_authority,
        data_directory=replace(
            assembly.source_root_authority.data_directory,
            handle_ref="failed-provisional-handle",
        ),
    )
    scripted = _ScriptedFilesystem(
        assembly,
        roots=(assembly.source_root_authority, distinct),
    )
    scripted.fail_release_ids[id(distinct)] = LocalIOErrorV1(LocalIOCodeV1.IO_FAILED)
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        _make_builder(scripted, bindings).build()
    result = caught.value.cleanup_result
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.CLEANUP_FAILED
    assert result.status is DockerCapabilityCleanupStatusV1.CLEANUP_FAILED
    assert result.provisional_attempted_count == 1
    assert result.attempted_count == 3 and result.released_count == 2
    failure = result.failures[0]
    assert failure.slot is DockerCapabilitySlotV1.STAGE_ROOT_AUTHORITY
    assert failure.local_io_code is LocalIOCodeV1.IO_FAILED
    assert "failed-provisional-handle" not in repr(caught.value)
    seed_live.abort()


def test_ledger_failure_attempts_child_then_parent_and_caches_terminal_digest():
    builder, filesystem, port, _bindings = _builder_environment()
    live = builder.build()
    assembly = live.assembly
    filesystem.fail_after_release[id(assembly.stage_verify_borrow)] = RuntimeError("child secret")
    filesystem.fail_after_release[id(assembly.stage_root_authority)] = LocalIOErrorV1(LocalIOCodeV1.IO_FAILED)
    result = live.abort()
    assert result.status is DockerCapabilityCleanupStatusV1.CLEANUP_FAILED
    assert (result.attempted_count, result.released_count) == (6, 4)
    assert result.provisional_attempted_count == 0
    assert tuple(value.slot for value in result.failures) == (
        DockerCapabilitySlotV1.STAGE_VERIFY_BORROW,
        DockerCapabilitySlotV1.STAGE_ROOT_AUTHORITY,
    )
    verify_index = next(index for index, item in enumerate(filesystem.release_order) if item[1] is assembly.stage_verify_borrow)
    parent_index = next(index for index, item in enumerate(filesystem.release_order) if item[1] is assembly.stage_root_authority)
    assert verify_index < parent_index
    assert live.abort() is result
    assert port.live_directories == {}
    assert "secret" not in repr(result)
    with pytest.raises((AttributeError, TypeError)):
        result.released_count = 6


def test_construction_assembly_failure_reports_complete_ledger_cleanup_failure():
    seed_live, assembly, bindings = _seed_and_script()
    scripted = _ScriptedFilesystem(assembly)
    scripted.fail_release_ids[id(assembly.stage_verify_borrow)] = RuntimeError(
        "unobservable cleanup detail"
    )
    builder = _make_builder(scripted, bindings)
    builder._source_ref = "invalid source ref"
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        builder.build()
    result = caught.value.cleanup_result
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.CLEANUP_FAILED
    assert result.attempted_count == 6 and result.released_count == 5
    assert result.failures[0].slot is DockerCapabilitySlotV1.STAGE_VERIFY_BORROW
    assert sum(value is assembly.stage_root_authority for _kind, value in scripted.released) == 1
    assert "unobservable" not in repr(caught.value)
    seed_live.abort()


def test_acquisition_failure_is_closed_and_returns_zero_attempt_cleanup_result():
    builder, filesystem, _port, _bindings = _builder_environment()
    filesystem.inner.retain_root_authority = lambda *args: (_ for _ in ()).throw(
        RuntimeError("SENTINEL authority handle")
    )
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        builder.build()
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.ACQUISITION_FAILED
    assert caught.value.cleanup_result.attempted_count == 0
    assert "SENTINEL" not in repr(caught.value)


def test_invalid_constructor_input_rejects_before_acquisition():
    _builder, filesystem, _port, bindings = _builder_environment()
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        _make_builder(filesystem, bindings, source_ref="invalid source ref")
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.INPUT_INVALID
    assert caught.value.cleanup_result is None
    assert filesystem.release_order == []
