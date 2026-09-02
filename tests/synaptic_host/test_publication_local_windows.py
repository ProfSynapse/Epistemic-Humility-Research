"""Native-Windows counterpart of ``test_publication_local_posix.py``.

Design tests 10-13 from ``docs/architecture/native-windows-publication-closure.md``
section 9.2. Every test is guarded on ``os.name == "nt"`` because each one drives
the real ``WindowsRetainedHandlePortV1`` against a real NTFS volume; none of them
uses a fake port.

What these tests do and do not prove:

* Test 10/11 prove the publication protocol's shared invariants hold end to end
  on NTFS through the real port, including restart safety.
* Test 12 is the instrument for residual R-4. It asserts BOTH directions of the
  share-mode pair and BOTH orders, because a test that asserted only the denial
  would pass for a port that excluded everything, its own opens included, and
  such a port cannot function at all. It uses TWO SEPARATE PORT INSTANCES on
  purpose: each instance owns a private ``_admission_leases`` dictionary, so a
  ``ROOT_IN_USE`` raised against the second instance cannot have come from the
  in-process bookkeeping guard and must have come from the kernel sharing
  violation, which is the property R-4 actually names.
* Test 13 is the two-half capability test. Construction must succeed regardless
  of volume, because the port is built with no path; the refusal must land at
  the first ``retain_directory`` against a bad volume, before any mutation.
* NONE of these tests asserts crash durability. Residual R-1 says the Windows
  directory barrier is NTFS-log-backed and is not independently proven by this
  closure. These tests assert the barrier is CALLED and SUCCEEDS, which is what
  the design controls; elevating R-1 needs a power-loss rig and is out of scope.

WHERE THIS SUITE RUNS CHANGES WHAT IT PROVES (M-6):

  This suite is diagnostic for host defect 2 -- the ancestor access mask -- ONLY
  when pytest's basetemp sits on the SYSTEM volume. Defect 2 was that every
  ancestor on the way down to a retained root was opened with the leaf's
  write-flavoured _DIRECTORY_ACCESS, which a non-elevated process cannot obtain
  on the C: drive root. Under a basetemp on a secondary volume such as the
  F: drive, where the user does hold write access to the volume root, the
  buggy mask is granted and every test here passes, so a green run on that
  arm says nothing about defect 2.

  Consequently a single green arm is not a verification of the ancestor-mask
  fix. Run this suite on BOTH a system-volume basetemp (the pytest default,
  under the per-user AppData Local Temp directory) and any secondary-volume
  basetemp, and treat only the system-volume arm as evidence for defect 2. The
  Linux-runnable constant and call-site pins in
  tests/synaptic_host/local_io_v1/test_windows_port_contract.py cover the mask
  itself; this note is about what the HOST arms can and cannot witness.

  One-line form for the design ledger section 9: "The Windows publication suite
  is diagnostic for defect 2 only under a system-volume basetemp; a green run
  on a secondary volume grants the buggy mask and proves nothing about it."
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import string
from pathlib import Path
from types import SimpleNamespace

import pytest

from synaptic_host.local_artifact_destination import (
    build_local_artifact_destination_registration_v1,
)
from synaptic_host.local_io_v1.model import LocalIOCodeV1, LocalIOErrorV1
from synaptic_host.publication_composition import (
    PublicationConfigurationDocumentsV1,
    compose_host_publication_v1,
)
from synaptic_tuner.api.v1 import (
    ProjectContext,
    PublicationRequest,
    RunArtifactRequest,
    RunOutcome,
    RunsAPI,
    RunVerification,
    TrainingRunRef,
    TrainingRunState,
    VerifiedArtifact,
)

windows_only = pytest.mark.skipif(
    os.name != "nt", reason="real Windows retained-handle publication"
)


def _windows_port():
    """Import the port lazily so this module still imports on POSIX."""
    from synaptic_host.local_io_v1.windows import WindowsRetainedHandlePortV1

    return WindowsRetainedHandlePortV1


class _ArtifactStream:
    def __init__(self, run, artifact, maximum_bytes, payload):
        self.run = run
        self.artifact = artifact
        self.maximum_bytes = maximum_bytes
        self._payload = payload

    def iter_bytes(self):
        midpoint = max(1, len(self._payload) // 2)
        yield self._payload[:midpoint]
        if midpoint < len(self._payload):
            yield self._payload[midpoint:]


class _RunsOperations:
    def __init__(self, run: TrainingRunRef, payload: bytes) -> None:
        self.run = run
        self.payload = payload
        self.artifact = VerifiedArtifact(
            "model", hashlib.sha256(payload).hexdigest(), len(payload)
        )

    def show(self, run):
        assert run == self.run
        return RunOutcome(
            "synaptic-run-outcome/v1",
            run,
            TrainingRunState.SUCCEEDED,
            (self.artifact,),
        )

    def reverify(self, run):
        assert run == self.run
        return RunVerification(run, True, "2026-08-31T12:00:00Z")

    def artifacts(self, request: RunArtifactRequest):
        assert request.run == self.run
        assert request.role == self.artifact.role
        assert request.maximum_bytes >= self.artifact.size_bytes
        return _ArtifactStream(
            request.run, self.artifact, request.maximum_bytes, self.payload
        )


def _write_json(path: Path, value: object) -> Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return path.resolve()


def _environment(tmp_path: Path):
    """Mirror of ``test_publication_local_posix.py::_environment``.

    Deliberately duplicated rather than imported: these two files must be able
    to drift independently if a platform ever needs a different fixture shape,
    and a cross-import between two skipif-guarded suites collects on both
    platforms even when every test in one of them is skipped.
    """
    project = tmp_path / "host-project"
    engine = project / "synaptic-tuner"
    data_root = project / ".synaptic" / "artifacts"
    control_root = project / ".synaptic" / "publication-control"
    spool_root = project / ".synaptic" / "publication-spool"
    state_root = project / ".synaptic" / "state"
    for path in (engine, data_root, control_root, spool_root, state_root):
        path.mkdir(parents=True)

    context = ProjectContext.host(
        engine_root=engine,
        project_root=project,
        state_root=state_root,
    )
    storage_path = _write_json(project / "storage.json", {
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {
                "access": "read_create",
                "location": "project://.synaptic/artifacts",
                "permit_ref": "permit-artifact-data",
                "root_ref": "artifact-data",
            },
            {
                "access": "read_create",
                "location": "project://.synaptic/publication-control",
                "permit_ref": "permit-artifact-control",
                "root_ref": "artifact-control",
            },
            {
                "access": "read_create",
                "location": "project://.synaptic/publication-spool",
                "permit_ref": "permit-artifact-spool",
                "root_ref": "artifact-spool",
            },
        ],
    })
    destination_path = _write_json(project / "artifacts.json", {
        "schema_version": "synaptic-host-artifact-destinations/v1",
        "destinations": [{
            "adapter_ref": "host.local/v1",
            "configuration": {
                "control_root_ref": "artifact-control",
                "data_root_ref": "artifact-data",
                "schema_version": "synaptic-local-artifact-destination/v1",
            },
            "destination_ref": "local-proof",
            "display_name": "Local proof",
            "policy": {
                "maximum_artifact_bytes": 1_048_576,
                "maximum_total_bytes": 1_048_576,
            },
            "schema_version": "synaptic-host-artifact-destination/v1",
        }],
    })
    run = TrainingRunRef("run-windows-proof", "project-windows-proof")
    payload = b"submodule-first-publication-proof"
    runs = RunsAPI(_RunsOperations(run, payload))

    def compose():
        return compose_host_publication_v1(
            context=context,
            runs=runs,
            configuration=PublicationConfigurationDocumentsV1.from_paths(
                destination_path=destination_path, storage_path=storage_path
            ),
            spool_root_ref="artifact-spool",
            clock=lambda: "2026-08-31T12:00:00Z",
            registration_builders=(
                build_local_artifact_destination_registration_v1,
            ),
        )

    return SimpleNamespace(
        compose=compose,
        context=context,
        control_root=control_root,
        data_root=data_root,
        destination_path=destination_path,
        payload=payload,
        run=run,
        spool_root=spool_root,
        state_root=state_root,
        storage_path=storage_path,
    )


# --------------------------------------------------------------------------
# Test 10 -- end-to-end publication on NTFS through the real Windows port.
# --------------------------------------------------------------------------
@windows_only
def test_real_windows_publication_is_project_owned_and_publishes(tmp_path: Path):
    environment = _environment(tmp_path)
    facade = environment.compose()

    page = facade.destinations()
    assert tuple(item.destination_ref for item in page.destinations) == ("local-proof",)

    result = facade.publish(PublicationRequest(environment.run, "local-proof"))
    assert result.state.value == "verified"
    assert result.artifacts == (
        _RunsOperations(environment.run, environment.payload).artifact,
    )
    assert facade.verify(result.publication).verified is True
    assert facade.publications("local-proof").publications == (result,)
    facade.close()

    assert (environment.state_root / "training.sqlite3").is_file()
    members = tuple(environment.data_root.iterdir())
    assert len(members) == 1
    assert members[0].is_file()
    assert members[0].read_bytes() == environment.payload
    # Ruling (b): the admission creates no namespace entry, so the spool root
    # is empty and artifact_spool.py's startup reclaim sees nothing unexpected.
    assert tuple(environment.spool_root.iterdir()) == ()


# --------------------------------------------------------------------------
# Test 11 -- restart safety: recomposing and republishing yields no duplicate.
# --------------------------------------------------------------------------
@windows_only
def test_real_windows_publication_is_restart_safe(tmp_path: Path):
    environment = _environment(tmp_path)

    facade = environment.compose()
    result = facade.publish(PublicationRequest(environment.run, "local-proof"))
    assert result.state.value == "verified"
    members = tuple(environment.data_root.iterdir())
    assert len(members) == 1
    facade.close()
    assert tuple(environment.spool_root.iterdir()) == ()

    reopened = environment.compose()
    replay = reopened.publish(PublicationRequest(environment.run, "local-proof"))
    assert replay == result
    assert reopened.verify(result.publication).verified is True
    # No duplicate artifact and no duplicate publication record.
    assert tuple(environment.data_root.iterdir()) == members
    assert reopened.publications("local-proof").publications == (result,)
    reopened.close()
    assert tuple(environment.spool_root.iterdir()) == ()


# --------------------------------------------------------------------------
# Test 12 -- residual R-4. The share-mode pair, both directions, both orders.
# --------------------------------------------------------------------------
@windows_only
def test_second_port_admission_is_denied_with_root_in_use_in_both_orders(
    tmp_path: Path,
):
    """Direction 1 of R-4: a second admission open is denied.

    Both orders are exercised. In order A the rival port retains its directory
    handle AFTER the admission is held; in order B it retains BEFORE. The
    denial must not depend on which handle was opened first.

    Two port instances are used so the denial cannot come from the per-instance
    ``_admission_leases`` bookkeeping guard, which only ever sees one lease.
    """
    port_class = _windows_port()
    spool = tmp_path / "spool"
    spool.mkdir()

    # ---- order A: admission first, rival's directory handle second ----
    holder = port_class()
    rival = port_class()
    held = holder.retain_directory(spool)
    lease = holder.acquire_directory_admission(held)
    try:
        rival_directory = rival.retain_directory(spool)
        with pytest.raises(LocalIOErrorV1) as denied_a:
            rival.acquire_directory_admission(rival_directory)
        assert denied_a.value.code is LocalIOCodeV1.ROOT_IN_USE
        rival.close_directory(rival_directory)
    finally:
        holder.release_directory_admission(held, lease)
        holder.close_directory(held)

    # ---- order B: rival's directory handle first, admission second ----
    holder_b = port_class()
    rival_b = port_class()
    rival_directory_b = rival_b.retain_directory(spool)
    held_b = holder_b.retain_directory(spool)
    lease_b = holder_b.acquire_directory_admission(held_b)
    try:
        with pytest.raises(LocalIOErrorV1) as denied_b:
            rival_b.acquire_directory_admission(rival_directory_b)
        assert denied_b.value.code is LocalIOCodeV1.ROOT_IN_USE
    finally:
        holder_b.release_directory_admission(held_b, lease_b)
        holder_b.close_directory(held_b)

    # ---- the exclusion is released, not permanent ----
    # Without this the whole test would pass for a port that denied every
    # admission forever, which is a port that cannot publish anything.
    regained = rival_b.acquire_directory_admission(rival_directory_b)
    rival_b.release_directory_admission(rival_directory_b, regained)
    rival_b.close_directory(rival_directory_b)


@windows_only
def test_ordinary_directory_opens_succeed_while_the_admission_is_held(
    tmp_path: Path,
):
    """Direction 2 of R-4: the port's own directory opens keep working.

    This is the half a denial-only test cannot see. If the admission handle's
    ShareAccess were too strict, every ordinary open would fail and the port
    would be unusable while still passing an exclusion test.

    Both orders are exercised: handles opened AFTER the admission is taken, and
    a handle opened BEFORE it that must remain usable afterwards.
    """
    port_class = _windows_port()
    spool = tmp_path / "spool"
    spool.mkdir()
    (spool / "child").mkdir()

    port = port_class()
    other = port_class()

    # Order B setup: an ordinary handle opened BEFORE the admission exists.
    opened_before = other.retain_directory(spool)
    assert other.list_names_at(opened_before, 16) == ("child",)

    held = port.retain_directory(spool)
    lease = port.acquire_directory_admission(held)
    try:
        # Order A: ordinary opens taken AFTER the admission is held.
        opened_after = other.retain_directory(spool)
        assert other.list_names_at(opened_after, 16) == ("child",)
        child_after = other.open_directory_at(opened_after, "child")
        other.close_directory(child_after)
        other.close_directory(opened_after)

        # Order B: the pre-existing handle still works while admission is held.
        assert other.list_names_at(opened_before, 16) == ("child",)
        child_before = other.open_directory_at(opened_before, "child")
        other.close_directory(child_before)

        # The admission holder's own handle-relative opens must work too --
        # this is the port doing its actual job while holding its own lease.
        assert port.list_names_at(held, 16) == ("child",)
        own_child = port.open_directory_at(held, "child")
        port.close_directory(own_child)
    finally:
        port.release_directory_admission(held, lease)
        port.close_directory(held)
        other.close_directory(opened_before)


# --------------------------------------------------------------------------
# Test 13 -- two halves: construction is volume-blind, retention is not.
# --------------------------------------------------------------------------
def _fixed_volume_roots() -> dict[str, str]:
    """Map ``X:\\`` -> filesystem name for every FIXED local volume."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    found: dict[str, str] = {}
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if kernel32.GetDriveTypeW(root) != 3:  # DRIVE_FIXED only
            continue
        filesystem = ctypes.create_unicode_buffer(64)
        if not kernel32.GetVolumeInformationW(
            root, None, 0, None, None, None, filesystem, 64
        ):
            continue
        found[root] = filesystem.value.upper()
    return found


@windows_only
def test_port_construction_succeeds_regardless_of_volume(tmp_path: Path):
    """Half one of test 13.

    The factory builds the port with no path, so construction cannot know the
    target volume and must not fail on account of one. A test asserting a
    construction failure would pass for the wrong reason.
    """
    port_class = _windows_port()
    port = port_class()
    assert port is not None

    from synaptic_host.local_io_v1.windows import detect_windows_capability_v1

    capability = detect_windows_capability_v1()
    assert capability.platform_family == "windows"
    assert capability.status.value == "available"

    # Positive control: the same freshly constructed port retains an NTFS root
    # happily. Without this, half two below could pass for a port that refused
    # every volume.
    retained = port.retain_directory(tmp_path)
    port.close_directory(retained)


@windows_only
def test_first_retain_directory_on_a_non_ntfs_volume_is_capability_unavailable(
    tmp_path: Path,
):
    """Half two of test 13.

    The refusal lands at the first ``retain_directory``, before any mutation
    reaches the root. Skips when the host has no non-NTFS fixed volume, because
    faking one would test the fake and not the port.

    The positive control deliberately uses ``tmp_path`` rather than a volume
    root: a volume root is not writable by a non-elevated process, so using one
    would conflate the volume question this test asks with the ancestor-access
    question, which is a separate matter.
    """
    volumes = _fixed_volume_roots()
    non_ntfs = sorted(root for root, name in volumes.items() if name != "NTFS")
    if not non_ntfs:
        pytest.skip(f"host has no non-NTFS fixed volume; saw {volumes}")

    port_class = _windows_port()
    port = port_class()

    with pytest.raises(LocalIOErrorV1) as refused:
        port.retain_directory(Path(non_ntfs[0]))
    assert refused.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE

    # Positive control on the SAME port instance: an ordinary NTFS directory
    # still retains, so the refusal above is attributable to the volume and not
    # to the port having been poisoned by the failed attempt.
    retained = port.retain_directory(tmp_path)
    port.close_directory(retained)


# --------------------------------------------------------------------------
# F-4 / R-7 -- the ancestor enumeration cap against a REAL NT enumeration.
#
# EVIDENCE CLASS: real-host. This is the twin of
# test_directory_entries_cap_trips_with_a_stubbed_enumeration in
# tests/synaptic_host/local_io_v1/test_windows_port_contract.py. That one
# replaces kernel32 and proves the cap arithmetic and the error mapping; it
# cannot say anything about a real directory. This one builds real entries on
# a real NTFS volume and drives the public port surface, so it is the only one
# of the pair whose green means "NT enumeration trips this bound".
# --------------------------------------------------------------------------
@windows_only
def test_directory_entries_cap_trips_on_a_real_nt_enumeration(tmp_path: Path):
    """R-7: a directory one entry past the cap is refused, and refused as a bound.

    Both sides of the boundary are built, because a test that only asserted
    the refusal would pass for a port that refused every directory. Exactly at
    the cap must come back intact.

    LIMIT_EXCEEDED rather than IO_FAILED is the load-bearing half: a directory
    that is too large is a bound being hit, not a disk failure, and
    _reject_collision keys on that distinction.
    """
    from synaptic_host.local_io_v1.filesystem import MAX_DIRECTORY_ENTRIES

    port = _windows_port()()

    def enumerate_directory(count: int):
        directory = tmp_path / f"entries{count}"
        directory.mkdir()
        for index in range(count):
            (directory / f"e{index:06d}").touch()
        assert len(os.listdir(directory)) == count
        retained = port.retain_directory(directory)
        try:
            return port.list_names_at(retained, MAX_DIRECTORY_ENTRIES)
        finally:
            port.close_directory(retained)

    # Exactly at the cap: listed in full.
    names = enumerate_directory(MAX_DIRECTORY_ENTRIES)
    assert len(names) == MAX_DIRECTORY_ENTRIES
    assert len(set(names)) == MAX_DIRECTORY_ENTRIES

    # One past it: refused, with the bound's own code.
    with pytest.raises(LocalIOErrorV1) as refused:
        enumerate_directory(MAX_DIRECTORY_ENTRIES + 1)
    assert refused.value.code is LocalIOCodeV1.LIMIT_EXCEEDED


# --------------------------------------------------------------------------
# M-12 -- the admission exclusion against a FOREIGN handle.
#
# EVIDENCE CLASS: real-host, measured. Test 12 above proves the exclusion
# between two PORT instances. This proves it against a handle the port never
# created and knows nothing about, which is the only form that rules out the
# in-process bookkeeping entirely: there is no lease, no port and no
# RetainedDirectoryV1 on the other side, just a kernel share mode.
# --------------------------------------------------------------------------
@windows_only
def test_a_foreign_handle_without_share_delete_blocks_only_the_admission(
    tmp_path: Path,
):
    """M-12, as measured rather than as predicted.

    The probe was specified as "hold a directory handle whose dwShareMode
    omits FILE_SHARE_DELETE, attempt retain_directory, assert ROOT_IN_USE".
    Measured on the host, retain_directory SUCCEEDS and the refusal lands one
    call later, at acquire_directory_admission. That is correct and is the
    sharper result: a Windows sharing violation is raised by the ACCESS the
    new open asks for, and retain_directory deliberately asks for no DELETE
    (see _DIRECTORY_ACCESS) while acquire_directory_admission is defined by
    asking for it (_ADMISSION_ACCESS). So the foreign share mode partitions
    the two calls exactly along the axis the design says carries the
    exclusion, and the assertion is written against that rather than against
    the prediction.

    The second arm is the control that makes the first mean something: the
    SAME foreign handle opened WITH FILE_SHARE_DELETE lets the admission
    through, so the refusal is attributable to the share mode and not to the
    mere existence of another handle on the directory.
    """
    spool = tmp_path / "spool"
    spool.mkdir()

    generic_read = 0x80000000
    share_read, share_write, share_delete = 0x1, 0x2, 0x4
    open_existing = 3
    backup_semantics = 0x02000000
    invalid_handle = ctypes.c_void_p(-1).value

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = ctypes.c_void_p

    def foreign_handle(share: int) -> int:
        handle = kernel32.CreateFileW(
            str(spool), generic_read, share, None, open_existing,
            backup_semantics, None,
        )
        assert handle not in (invalid_handle, None), ctypes.get_last_error()
        return handle

    port_class = _windows_port()

    # Arm 1: the foreign handle refuses to share DELETE.
    handle = foreign_handle(share_read | share_write)
    try:
        port = port_class()
        # retain_directory asks for no DELETE, so it is NOT in conflict.
        retained = port.retain_directory(spool)
        try:
            with pytest.raises(LocalIOErrorV1) as denied:
                port.acquire_directory_admission(retained)
            assert denied.value.code is LocalIOCodeV1.ROOT_IN_USE
        finally:
            port.close_directory(retained)
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))

    # Arm 2, the control: the same foreign handle sharing DELETE lets the
    # admission through. Without this the test would pass for a port that
    # refused every admission whenever any other handle existed.
    handle = foreign_handle(share_read | share_write | share_delete)
    try:
        port = port_class()
        retained = port.retain_directory(spool)
        try:
            lease = port.acquire_directory_admission(retained)
            port.release_directory_admission(retained, lease)
        finally:
            port.close_directory(retained)
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
