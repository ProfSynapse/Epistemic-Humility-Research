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
