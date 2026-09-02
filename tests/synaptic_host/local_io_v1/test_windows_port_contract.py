"""Location: tests/synaptic_host/local_io_v1/test_windows_port_contract.py

Linux-runnable contract tests for the native-Windows retained-handle closure.

These tests cover the parts of the closure that do NOT need a Windows host:
the gate widening and capability report in
``synaptic_host/local_io_v1/filesystem.py``, the structural shape of
``synaptic_host/local_io_v1/windows.py``, the shared invariants in
``synaptic_host/local_io_v1/model.py`` that a non-POSIX backend must be able
to satisfy, and the platform factory in
``synaptic_host/publication_composition.py``.

They drive ``LocalFilesystemV1`` with the deterministic in-memory port from
``tests/synaptic_host/local_io_v1/conftest.py`` (``FakePosixFilesystemPortV1``)
and a synthetic ``native_platform`` string, so no Windows interpreter, no NTFS
volume, and no host filesystem effect is involved. The tests that require a
real Windows host (end-to-end publication, restart safety, admission
exclusion, non-NTFS refusal) belong to ``test_publication_local_windows.py``
and are NOT in this file.

Design authority: docs/architecture/native-windows-publication-closure.md,
section 9.2 tests 0-7.
"""

from __future__ import annotations

import hashlib
import inspect
import os
import sys
from pathlib import Path
from typing import Generic, Protocol

import pytest

from synaptic_host.local_io_v1.filesystem import (
    LocalFilesystemV1,
    PosixFilesystemPortV1,
)
from synaptic_host.local_io_v1.model import (
    CapabilityStatusV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RecoveryStatusV1,
    RootAccessV1,
    SingleRootPurposeV1,
    digest_v1,
)

from .conftest import FakePosixFilesystemPortV1

# Platform strings under test. "win32" is the only Windows value that
# _SUPPORTED_PLATFORMS admits; the BSDs are POSIX-family but hold no
# crash-released directory admission and must stay excluded.
WINDOWS_PLATFORM = "win32"
LINUX_PLATFORM = "linux"
NON_ADMISSION_POSIX_PLATFORMS = ("darwin", "freebsd", "openbsd", "netbsd")
UNSUPPORTED_PLATFORMS = ("sunos5", "aix", "cygwin")

# The three features every available platform reports, and the two
# platform-neutral admission properties Windows earns on top of them.
BASE_FEATURES = ("descriptor_relative", "exclusive_create", "retained_dirfd")
WINDOWS_ADMISSION_FEATURES = ("crash-released-admission", "directory-inode-admission")
# POSIX-named mechanisms Windows must never claim: it has neither flock nor exec.
POSIX_ONLY_FEATURES = ("exec-closed-admission", "nonblocking-directory-flock")


class _Authenticator:
    """Minimal permit authenticator: admits only permits handed to allow()."""

    def __init__(self) -> None:
        self.permits: dict[int, LocalRootPermitV1] = {}

    def allow(self, permit: LocalRootPermitV1) -> None:
        self.permits[id(permit)] = permit

    def authenticate(self, permit: LocalRootPermitV1):
        return permit if self.permits.get(id(permit)) is permit else None


def _binding(path: Path, ref: str, authenticator: _Authenticator) -> LocalRootBindingV1:
    absolute = path.absolute()
    permit_ref = "permit-" + ref
    canonical = {
        "access": RootAccessV1.READ_CREATE.value,
        "absolute_root": str(absolute),
        "authority_ref": "authority-test",
        "key_ref": "key-test",
        "permit_ref": permit_ref,
        "root_ref": ref,
    }
    permit = LocalRootPermitV1(
        permit_ref, ref, absolute, RootAccessV1.READ_CREATE, "authority-test",
        "key-test", digest_v1(canonical), "0" * 64,
    )
    authenticator.allow(permit)
    return LocalRootBindingV1(
        ref, f"project://{ref}", absolute, RootAccessV1.READ_CREATE, permit_ref, permit
    )


def _filesystem(platform: str, port=None) -> LocalFilesystemV1:
    """A coordinator on a synthetic platform, with or without a port."""
    return LocalFilesystemV1(port, _Authenticator(), native_platform=platform)


def _composition(profile: str, platform: str = WINDOWS_PLATFORM):
    """Two-root (data + control) composition on a synthetic platform."""
    port = FakePosixFilesystemPortV1()
    base = Path.cwd() / ".fake-metadata" / profile
    data_path = base / "data"
    control_path = base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = _Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform=platform)
    authority = filesystem.retain_root_authority(
        _binding(data_path, profile, authenticator),
        _binding(control_path, profile + "-control", authenticator),
    )
    return port, filesystem, authority


def _single_root_composition(profile: str, platform: str = WINDOWS_PLATFORM):
    """Single-root (spool) composition on a synthetic platform."""
    port = FakePosixFilesystemPortV1()
    root_path = Path.cwd() / ".fake-metadata" / profile / "spool"
    port.add_root(root_path, "spool")
    authenticator = _Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform=platform)
    authority = filesystem.retain_single_root_authority(
        _binding(root_path, profile, authenticator),
        purpose=SingleRootPurposeV1.PUBLICATION_SPOOL,
    )
    return port, filesystem, authority


def _destination(filesystem, authority, payload: bytes):
    return filesystem.bind_destination(
        authority,
        "artifact.bin",
        role="arbitrary-role",
        expected_size=len(payload),
        expected_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _staging_node(port):
    """The single in-flight staging entry under the fake data root."""
    entries = port.directories["dir-data"]
    staged = [node for name, node in entries.items() if name.startswith(".synaptic-")]
    assert len(staged) == 1
    return staged[0]


def _protocol_method_names(protocol: type) -> frozenset[str]:
    """Every public callable the Protocol declares, derived at runtime.

    Derived from the class rather than hand-copied so this check cannot drift
    away from the Protocol when a method is added or removed.
    """
    names: set[str] = set()
    for base in protocol.__mro__:
        if base in (object, Protocol, Generic):
            continue
        for name, value in vars(base).items():
            if not name.startswith("_") and callable(value):
                names.add(name)
    return frozenset(names)


# --- Test 0: structural conformance of the Windows port -------------------


def test_windows_port_exposes_every_protocol_method() -> None:
    """The Windows port satisfies the whole Protocol, mkdir_at included.

    This inspects the class; it never calls it, so it runs on any platform.
    """
    from synaptic_host.local_io_v1.windows import WindowsRetainedHandlePortV1

    required = _protocol_method_names(PosixFilesystemPortV1)
    # Counter-check the derivation itself: an empty or truncated set would make
    # the membership loop below vacuously pass.
    assert "mkdir_at" in required
    assert len(required) == 21

    missing = sorted(
        name for name in required if not callable(getattr(WindowsRetainedHandlePortV1, name, None))
    )
    assert missing == []


def test_windows_capability_detector_fails_closed_without_native_bindings() -> None:
    """detect_windows_capability_v1 reports UNAVAILABLE off a real Windows host.

    Like detect_posix_capability_v1, the detector names the family of the
    RUNNING host, so on this lane it reports "posix". Injecting the Windows
    platform strings drives the Windows branch on a host where kernel32 and
    ntdll cannot resolve: it must fail closed, not raise.
    """
    from synaptic_host.local_io_v1.posix import detect_posix_capability_v1
    from synaptic_host.local_io_v1.windows import detect_windows_capability_v1

    if os.name == "nt":  # pragma: no cover - not reachable on the Linux lane
        pytest.skip("running on a real Windows host")

    running = detect_windows_capability_v1()
    assert running.status is CapabilityStatusV1.UNAVAILABLE
    assert running.features == ()
    # Family is derived the same way as the POSIX detector derives it.
    assert running.platform_family == detect_posix_capability_v1().platform_family

    injected = detect_windows_capability_v1(platform_name="win32", os_name="nt")
    assert injected.platform_family == "windows"
    assert injected.status is CapabilityStatusV1.UNAVAILABLE
    assert injected.features == ()


# --- Test 1: _require_retained_port -----------------------------------------


def test_retained_port_gate_admits_win32_and_still_rejects_the_bsds() -> None:
    port = FakePosixFilesystemPortV1()
    _filesystem(WINDOWS_PLATFORM, port)._require_retained_port()
    _filesystem(LINUX_PLATFORM, port)._require_retained_port()

    # darwin and the BSDs stay POSIX-family, so this gate still admits them;
    # it is the admission gate that excludes them. Asserted in test 2.
    for platform in NON_ADMISSION_POSIX_PLATFORMS:
        _filesystem(platform, port)._require_retained_port()

    # Platforms with no retained-handle port at all stay refused.
    for platform in UNSUPPORTED_PLATFORMS:
        with pytest.raises(LocalIOErrorV1) as caught:
            _filesystem(platform, port)._require_retained_port()
        assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE

    # win32 without a port is still unavailable: the platform widening never
    # substitutes for a real port.
    with pytest.raises(LocalIOErrorV1) as no_port:
        _filesystem(WINDOWS_PLATFORM, None)._require_retained_port()
    assert no_port.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE


# --- Test 2: _require_directory_admission -----------------------------------


def test_directory_admission_gate_admits_linux_and_win32_only() -> None:
    port = FakePosixFilesystemPortV1()
    _filesystem(WINDOWS_PLATFORM, port)._require_directory_admission()
    _filesystem(LINUX_PLATFORM, port)._require_directory_admission()

    for platform in NON_ADMISSION_POSIX_PLATFORMS:
        with pytest.raises(LocalIOErrorV1) as caught:
            _filesystem(platform, port)._require_directory_admission()
        assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE


# --- Test 3: capability() ----------------------------------------------------


def test_capability_reports_five_windows_features_and_seven_on_linux() -> None:
    port = FakePosixFilesystemPortV1()

    windows = _filesystem(WINDOWS_PLATFORM, port).capability()
    assert windows.platform_family == "windows"
    assert windows.status is CapabilityStatusV1.AVAILABLE
    assert windows.features == tuple(sorted(BASE_FEATURES + WINDOWS_ADMISSION_FEATURES))
    # Named explicitly so a later widening of the gate cannot add a POSIX
    # mechanism to the Windows claim silently.
    for refused in POSIX_ONLY_FEATURES:
        assert refused not in windows.features

    linux = _filesystem(LINUX_PLATFORM, port).capability()
    assert linux.platform_family == "posix"
    assert linux.status is CapabilityStatusV1.AVAILABLE
    assert linux.features == tuple(
        sorted(BASE_FEATURES + WINDOWS_ADMISSION_FEATURES + POSIX_ONLY_FEATURES)
    )
    assert len(linux.features) == 7

    # A Windows platform with no port reports the family but claims nothing.
    portless = _filesystem(WINDOWS_PLATFORM, None).capability()
    assert portless.platform_family == "windows"
    assert portless.status is CapabilityStatusV1.UNAVAILABLE
    assert portless.features == ()


# --- Test 4: full create-commit sequence on a non-POSIX platform -------------


def test_win32_create_commit_observes_nlink_one_two_one() -> None:
    """A non-POSIX backend satisfies the shared nlink commit proof.

    The staging file is created with nlink 1, the commit link takes it to 2,
    and unlinking the staging name returns it to 1. This is what proves the
    invariants in model.py are satisfiable without editing model.py.
    """
    port, filesystem, authority = _composition("win32-create-commit")
    payload = b"payload"
    destination = _destination(filesystem, authority, payload)
    create = filesystem.authorize_create(authority, destination)

    observed: list[int] = []
    port.callbacks["create_exclusive_at"] = lambda: observed.append(_staging_node(port).nlink)
    port.callbacks["link_at"] = lambda: observed.append(_staging_node(port).nlink)

    result = filesystem.create_once(authority, create, destination, [payload])

    assert result.status is RecoveryStatusV1.FOUND
    assert observed == [1, 2]
    final = port.directories["dir-data"]["artifact.bin"]
    assert final.nlink == 1
    assert bytes(final.content) == payload
    # The staging name is gone: the commit proof and the unlink proof both ran.
    assert [name for name in port.directories["dir-data"] if name.startswith(".synaptic-")] == []


# --- Test 5: a failing directory barrier never succeeds silently ------------


def test_win32_failing_directory_barrier_never_reports_committed() -> None:
    """Ruling (a): a directory barrier that fails must not read as success.

    Paired with a same-fixture positive so an implementation that always
    reported INDETERMINATE could not pass this test.
    """
    port, filesystem, authority = _composition("win32-barrier-fails")
    payload = b"payload"
    destination = _destination(filesystem, authority, payload)
    create = filesystem.authorize_create(authority, destination)
    # Fail the first barrier over the data directory, which is the one that
    # follows the commit link.
    port.fail_before["fsync_directory:data"] = 1

    result = filesystem.create_once(authority, create, destination, [payload])

    assert result.status is RecoveryStatusV1.INDETERMINATE
    assert "SENTINEL" not in str(result)
    # The staging name survives, so the mutation stays resumable rather than
    # being reported as a completed create.
    assert [name for name in port.directories["dir-data"] if name.startswith(".synaptic-")] != []

    # Same fixture, no injected failure: the sequence does reach FOUND.
    clean_port, clean_filesystem, clean_authority = _composition("win32-barrier-holds")
    clean_destination = _destination(clean_filesystem, clean_authority, payload)
    clean_create = clean_filesystem.authorize_create(clean_authority, clean_destination)
    clean_result = clean_filesystem.create_once(
        clean_authority, clean_create, clean_destination, [payload]
    )
    assert clean_result.status is RecoveryStatusV1.FOUND
    assert "fsync_directory:data" in clean_port.trace


# --- Test 6: 128-bit file id is carried losslessly --------------------------


def test_local_file_identity_carries_a_128_bit_inode_losslessly() -> None:
    """A Windows 128-bit FileId survives as a Python int and digests stably."""
    low = 0xDEAD_BEEF_1234_5678
    inode = (1 << 127) | (0x0BAD_C0DE << 64) | low

    def build(value: int) -> LocalFileIdentityV1:
        return LocalFileIdentityV1(
            device=7, inode=value, mode=0o100600, nlink=1,
            changed_ns=1, modified_ns=2, size=3,
        )

    identity = build(inode)
    assert identity.inode == inode
    assert identity.canonical()["inode"] == inode

    # Stable: the same 128-bit value digests to the same string twice.
    assert digest_v1(identity.canonical()) == digest_v1(build(inode).canonical())

    # Lossless: two ids that share their low 64 bits must not collide, which
    # is exactly what a truncating reduction to 64 bits would break.
    assert inode != low
    assert inode & ((1 << 64) - 1) == low
    assert digest_v1(identity.canonical()) != digest_v1(build(low).canonical())


# --- Test 7: admission introduces no spool-root entry -----------------------


def test_win32_admission_adds_no_entry_to_the_spool_root() -> None:
    """Ruling (b): admission is share-mode exclusion, never a lock file.

    _startup_reclaim raises on any unexpected entry under the spool root, so a
    reintroduced lock file would break publication startup.
    """
    port, filesystem, authority = _single_root_composition("win32-spool-admission")
    assert port.directories["dir-spool"] == {}

    admission = filesystem.acquire_single_root_admission(authority)
    assert port.directories["dir-spool"] == {}

    filesystem.release_single_root_admission(authority, admission)
    assert port.directories["dir-spool"] == {}


# --- S5: the platform factory keeps the POSIX path unchanged ----------------


def test_local_filesystem_port_factory_selects_the_posix_port_off_windows() -> None:
    """publication_composition picks the port by os.name, POSIX path unchanged."""
    from synaptic_host.publication_composition import _local_filesystem_port_v1
    from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1

    if os.name == "nt":  # pragma: no cover - not reachable on the Linux lane
        pytest.skip("POSIX branch is not the live branch on Windows")
    assert type(_local_filesystem_port_v1()) is PosixRetainedDirfdPortV1


def test_windows_port_module_imports_cleanly_on_linux() -> None:
    """The Windows module binds Win32 lazily, so importing it never needs NT."""
    import importlib

    module = importlib.import_module("synaptic_host.local_io_v1.windows")
    assert module.__name__ == "synaptic_host.local_io_v1.windows"
    assert sys.platform != "win32" or module is not None


# --- Task #24 host-defect fixes ---------------------------------------------
#
# These three cover the fixes for the defects the test-engineer measured on a
# real Windows host. They are Linux-runnable: they inspect constants and drive
# the pure decision logic with a synthetic enumeration, so no Win32 binding is
# ever resolved.


def test_ancestor_access_carries_no_write_flavour_and_leaf_still_does() -> None:
    """Defect 2: ancestors are traversed and listed, never written.

    A non-elevated process cannot get write access to the C: drive root, so
    asking for a write flavour on every ancestor made every root on the system
    volume unreachable. The leaf keeps the write access the design requires.
    """
    from synaptic_host.local_io_v1 import windows

    write_flavours = {
        "FILE_ADD_FILE": windows._FILE_ADD_FILE,
        "FILE_ADD_SUBDIRECTORY": windows._FILE_ADD_SUBDIRECTORY,
        "FILE_WRITE_ATTRIBUTES": windows._FILE_WRITE_ATTRIBUTES,
    }
    ancestor = windows._ANCESTOR_DIRECTORY_ACCESS
    leaf = windows._DIRECTORY_ACCESS

    for name, bit in write_flavours.items():
        assert not ancestor & bit, f"ancestor mask must not carry {name}"
        # Counter-check: the leaf mask DOES carry it, so this test discriminates
        # rather than passing for any pair of masks.
        assert leaf & bit, f"leaf mask must still carry {name}"

    # Everything the descent actually does on an ancestor handle.
    for name, bit in (
        ("FILE_LIST_DIRECTORY", windows._FILE_LIST_DIRECTORY),   # _root_component
        ("FILE_READ_ATTRIBUTES", windows._FILE_READ_ATTRIBUTES),  # _query_identity
        ("FILE_TRAVERSE", windows._FILE_TRAVERSE),                # relative open
        ("SYNCHRONIZE", windows._SYNCHRONIZE),                    # SYNCHRONOUS_IO
    ):
        assert ancestor & bit, f"ancestor mask needs {name}"

    # The ancestor mask is a strict subset of the leaf mask.
    assert ancestor & leaf == ancestor
    assert ancestor != leaf


def test_admission_reopen_uses_an_empty_name_and_dot_is_still_refused() -> None:
    """Defect 1: re-open by handle, never by the literal name ".".

    _windows_name must keep refusing "." and ".." for ordinary components; the
    admission path does not supply a name at all.
    """
    from synaptic_host.local_io_v1 import windows

    assert callable(windows._reopen_by_handle)

    for refused in (".", ".."):
        with pytest.raises(LocalIOErrorV1) as caught:
            windows._windows_name(refused)
        assert caught.value.code is LocalIOCodeV1.PATH_INVALID

    # The admission path no longer routes through the named-component opener.
    source = inspect.getsource(windows.WindowsRetainedHandlePortV1.acquire_directory_admission)
    assert "_reopen_by_handle" in source
    assert '"."' not in source


def test_root_component_rejects_a_reparse_match_but_tolerates_a_sibling(monkeypatch) -> None:
    """Defect 3: a redirect elsewhere in the parent must not veto the path.

    The C: drive root carries the legacy "Documents and Settings" junction, so
    rejecting the whole listing on any reparse entry made every path beneath it
    unreachable. The component actually descended into is still refused.
    """
    from synaptic_host.local_io_v1 import windows

    # The port constructor fails closed off Windows, and _root_component uses
    # no instance state, so drive it unbound. If it ever grows instance state
    # this call fails loudly rather than silently skipping the check.
    root_component = windows.WindowsRetainedHandlePortV1._root_component
    clean_sibling = ("Documents and Settings", True)

    def entries(pairs):
        # monkeypatch restores the real enumeration at teardown, so this never
        # leaks into the native-Windows tests that share a session.
        monkeypatch.setattr(
            windows, "_directory_entries", lambda handle, maximum: tuple(pairs)
        )

    # A reparse SIBLING is tolerated: the match itself is clean.
    entries([clean_sibling, ("Users", False)])
    assert root_component(None, 0, "Users") == "Users"

    # The MATCHED entry being a reparse point is still refused.
    entries([clean_sibling, ("Users", True)])
    with pytest.raises(LocalIOErrorV1) as reparse_match:
        root_component(None, 0, "Users")
    assert reparse_match.value.code is LocalIOCodeV1.ROOT_CHANGED

    # Exact-case agreement is unchanged.
    entries([("users", False)])
    with pytest.raises(LocalIOErrorV1) as wrong_case:
        root_component(None, 0, "Users")
    assert wrong_case.value.code is LocalIOCodeV1.ROOT_CHANGED

    # list_names_at's published strictness is unchanged: ANY reparse rejects.
    entries([clean_sibling, ("Users", False)])
    with pytest.raises(LocalIOErrorV1) as strict:
        windows._directory_names(0, 4096)
    assert strict.value.code is LocalIOCodeV1.ROOT_CHANGED
    entries([("Users", False)])
    assert windows._directory_names(0, 4096) == ("Users",)
