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

import ast
import hashlib
import inspect
import json
import os
import stat
import sys
import textwrap
import threading
import types
from pathlib import Path
from typing import Generic, Protocol

import pytest

from synaptic_host.local_io_v1.filesystem import (
    LocalFilesystemV1,
    PosixFilesystemPortV1,
)
from synaptic_host.local_io_v1.model import (
    CapabilityStatusV1,
    JournalSnapshotStatusV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RecoveryStatusV1,
    RetainedDirectoryV1,
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

    # M-5: the admission path no longer routes through the named-component
    # opener. Checked over the PARSED source rather than as a substring. The
    # old assertion was `'"."' not in source`, which only ever saw the
    # double-quoted spelling: a revert written as _open_relative(handle, '.')
    # would have passed it unchanged. An ast.Constant has a value, not a
    # quoting style, so the walk below is blind to how the literal is written.
    source = inspect.getsource(
        windows.WindowsRetainedHandlePortV1.acquire_directory_admission
    )
    assert "_reopen_by_handle" in source

    # Walk the WHOLE admission re-open path, not just its entry point. The
    # name a re-open supplies is chosen in _reopen_by_handle, so a revert to
    # the literal would land THERE and leave acquire_directory_admission
    # unchanged -- a one-function slice would stay green through exactly the
    # regression this test exists to catch. _windows_name is deliberately NOT
    # in the list: it is the validator, and its "." and ".." literals are the
    # rejection set, not a name being passed to an open.
    for label, function in (
        ("acquire_directory_admission",
         windows.WindowsRetainedHandlePortV1.acquire_directory_admission),
        ("_reopen_by_handle", windows._reopen_by_handle),
        ("_open_relative", windows._open_relative),
    ):
        dotted = [
            node
            for node in ast.walk(
                ast.parse(textwrap.dedent(inspect.getsource(function)))
            )
            if isinstance(node, ast.Constant) and node.value in (".", "..")
        ]
        assert not dotted, (
            f"{label} carries the literal(s) {[node.value for node in dotted]} "
            f"at line offset(s) {[node.lineno for node in dotted]}; the "
            "admission re-open must supply no name at all"
        )

    # Measured, and the second reason the substring form had to go: both
    # helpers DISCUSS the literal "." in their docstrings, so `'"."' not in
    # source` is False for them on correct code. The old assertion could not
    # have been widened to cover the two functions where a revert would
    # actually land; it would have failed on the shipped tree. An ast.Constant
    # comparison ignores prose, which is what makes the wider walk possible.
    for function in (windows._reopen_by_handle, windows._open_relative):
        assert '"."' in inspect.getsource(function)

    # Counter-check that the walk discriminates rather than passing for any
    # source at all: it catches every spelling of the literal, including the
    # single-quoted one the substring assertion let through.
    for spelling in ('"."', "'.'", '""".."""'):
        probe = ast.parse(f"def f(handle):\n    return _open(handle, {spelling})\n")
        assert any(
            isinstance(node, ast.Constant) and node.value in (".", "..")
            for node in ast.walk(probe)
        ), spelling


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
    clean_sibling = ("Documents and Settings", True, 0x11)

    def entries(pairs):
        # monkeypatch restores the real enumeration at teardown, so this never
        # leaks into the native-Windows tests that share a session.
        monkeypatch.setattr(
            windows, "_directory_entries", lambda handle, maximum: tuple(pairs)
        )

    # A reparse SIBLING is tolerated: the match itself is clean. The matched
    # entry's file id comes back with the component so the descent can bind the
    # handle it opens to the entry vetted here.
    entries([clean_sibling, ("Users", False, 0x22)])
    assert root_component(None, 0, "Users") == ("Users", 0x22)

    # The MATCHED entry being a reparse point is still refused.
    entries([clean_sibling, ("Users", True, 0x22)])
    with pytest.raises(LocalIOErrorV1) as reparse_match:
        root_component(None, 0, "Users")
    assert reparse_match.value.code is LocalIOCodeV1.ROOT_CHANGED

    # Exact-case agreement is unchanged.
    entries([("users", False, 0x22)])
    with pytest.raises(LocalIOErrorV1) as wrong_case:
        root_component(None, 0, "Users")
    assert wrong_case.value.code is LocalIOCodeV1.ROOT_CHANGED

    # M-7 (architect overturned #26): list_names_at NO LONGER vetoes the whole
    # listing on a reparse-point sibling. A junction the caller never opens
    # cannot redirect a name the caller does open, and the veto made every
    # directory holding one unlistable. The sibling is now simply listed.
    entries([clean_sibling, ("Users", False, 0x22)])
    assert windows._directory_names(0, 4096) == ("Documents and Settings", "Users")
    entries([("Users", False, 0x22)])
    assert windows._directory_names(0, 4096) == ("Users",)


# --- Cycle-1 remediation: B-1, M-1, M-2, M-3, M-10, F-1, F-2, F-3 -----------
#
# These drive the NT decision logic on Linux by replacing the ONE lazy binder
# ``windows._windows_native`` with a stub kernel32/ntdll pair whose
# NtCreateFile returns a chosen NTSTATUS. That single seam is enough:
# ``_nt_open_relative`` builds its OBJECT_ATTRIBUTES from plain ctypes
# structures that construct fine on POSIX, and it never dereferences the
# handle it returns. No Win32 symbol is resolved and no filesystem effect
# occurs, so these run in the ordinary Linux lane alongside the rest of this
# file. The real-host counterparts live in test_publication_local_windows.py.

_NTSTATUS_SUCCESS = 0x00000000

# Every status the widened table NAMES, with the code it must produce.
NAMED_STATUS_CODES = {
    0xC0000034: LocalIOCodeV1.PATH_INVALID,        # OBJECT_NAME_NOT_FOUND
    0xC000003A: LocalIOCodeV1.PATH_INVALID,        # OBJECT_PATH_NOT_FOUND
    0xC00000BA: LocalIOCodeV1.PATH_INVALID,        # FILE_IS_A_DIRECTORY
    0xC0000103: LocalIOCodeV1.PATH_INVALID,        # NOT_A_DIRECTORY
    0xC0000035: LocalIOCodeV1.DESTINATION_EXISTS,  # OBJECT_NAME_COLLISION
    0xC0000043: LocalIOCodeV1.ROOT_IN_USE,         # SHARING_VIOLATION
}

# Failures the table does NOT name. B-1: before the fix the default arm mapped
# every one of these to PATH_INVALID, which stat_at reads as "the name is
# absent" and _open_journal_dir read as "there is no journal". Each must now
# be IO_FAILED, so a real fault can never be mistaken for an absence.
UNNAMED_FAILURE_STATUSES = {
    "ACCESS_DENIED": 0xC0000022,
    "DELETE_PENDING": 0xC0000056,
    "REPARSE_POINT_ENCOUNTERED": 0xC000050B,
    "INSUFFICIENT_RESOURCES": 0xC000009A,
    "DISK_CORRUPT_ERROR": 0xC0000032,
    "OBJECT_NAME_INVALID": 0xC0000033,
    "MEDIA_WRITE_PROTECTED": 0xC00000A2,
    "DEVICE_NOT_READY": 0xC00000A3,
    "IO_DEVICE_ERROR": 0xC0000185,
}


def _as_ntstatus(raw: int) -> int:
    """NtCreateFile's restype is c_long, so a failure arrives NEGATIVE."""
    return raw - 0x100000000 if raw >= 0x80000000 else raw


class _KernelStub:
    """kernel32 stand-in: every call the tested paths make, all succeeding."""

    def __init__(self, anchor: int = 0x100) -> None:
        self.anchor = anchor
        self.closed: list[int] = []
        self.dispositions = 0

    def CreateFileW(self, path, access, share, security, disposition, flags, template):
        return self.anchor

    def CloseHandle(self, handle) -> int:
        self.closed.append(handle.value)
        return 1

    def FlushFileBuffers(self, handle) -> int:
        return 1

    def SetFileInformationByHandle(self, handle, klass, buffer, size) -> int:
        self.dispositions += 1
        return 1


class _NtCreateFileStub:
    """ntdll stand-in whose NtCreateFile plays a scripted status sequence.

    The last status repeats once the script runs out, so a single-status stub
    answers every call the same way.
    """

    def __init__(self, *statuses: int, handle: int = 0x1234) -> None:
        self.statuses = list(statuses) or [_NTSTATUS_SUCCESS]
        self.handle = handle
        self.calls = 0

    def NtCreateFile(
        self, out, access, attributes, status_block, allocation,
        file_attributes, share, disposition, options, ea, ea_length,
    ) -> int:
        self.calls += 1
        raw = self.statuses[min(self.calls - 1, len(self.statuses) - 1)]
        status = _as_ntstatus(raw)
        if status >= 0:
            # byref() keeps the original object reachable through _obj, which
            # is how an NT out-parameter is written without a real DLL.
            out._obj.value = self.handle
        return status


def _bind_native(monkeypatch, *statuses: int, handle: int = 0x1234, anchor: int = 0x100):
    """Replace the lazy Win32 binder for the duration of one test."""
    from synaptic_host.local_io_v1 import windows

    kernel = _KernelStub(anchor)
    ntdll = _NtCreateFileStub(*statuses, handle=handle)
    monkeypatch.setattr(windows, "_windows_native", lambda: (kernel, ntdll))
    return kernel, ntdll


def _dir_identity(inode: int = 0x5100) -> LocalFileIdentityV1:
    return LocalFileIdentityV1(
        device=1, inode=inode, mode=stat.S_IFDIR | 0o700, nlink=1,
        changed_ns=0, modified_ns=0, size=0,
    )


def _unbound_port():
    """A port instance built without __init__, which fails closed off Windows.

    Only the fields the methods under test read are populated. If one of them
    ever starts reading another field this raises AttributeError loudly rather
    than degrading into a test that silently checks nothing.
    """
    from synaptic_host.local_io_v1 import windows

    port = object.__new__(windows.WindowsRetainedHandlePortV1)
    port._directories = {}
    port._files = {}
    port._journal_lock = threading.Lock()
    port._admission_process_id = os.getpid()
    port._admission_process_ref = "process-contract-test"
    port._admission_leases = {}
    port._admission_lock = threading.Lock()
    return port


def _retained(port, handle: int, identity: LocalFileIdentityV1) -> RetainedDirectoryV1:
    retained = RetainedDirectoryV1("dir-contract-test", identity)
    port._directories["dir-contract-test"] = (handle, retained)
    return retained


def _raise_code(code: LocalIOCodeV1):
    def raiser(*args, **kwargs):
        raise LocalIOErrorV1(code)
    return raiser


# --- B-1: the NT status table ----------------------------------------------


def test_nt_open_maps_the_named_statuses_and_fails_closed_on_every_other(monkeypatch) -> None:
    """B-1: PATH_INVALID is reserved for the four not-found/wrong-type statuses.

    PATH_INVALID is not a plain error here, it is a CONTROL SIGNAL: stat_at
    and _open_journal_dir both read it as "absent". A default arm that mapped
    unnamed failures to it therefore reported ACCESS_DENIED as absence.
    """
    from synaptic_host.local_io_v1 import windows

    def open_with(raw: int) -> int:
        _bind_native(monkeypatch, raw)
        return windows._nt_open_relative(
            7, "child", directory=False, create=False,
            access=windows._FILE_READ_ATTRIBUTES, share=windows._FILE_SHARE_ALL,
        )

    for raw, expected in NAMED_STATUS_CODES.items():
        with pytest.raises(LocalIOErrorV1) as caught:
            open_with(raw)
        assert caught.value.code is expected, f"status {raw:#010x}"

    for name, raw in UNNAMED_FAILURE_STATUSES.items():
        with pytest.raises(LocalIOErrorV1) as caught:
            open_with(raw)
        assert caught.value.code is LocalIOCodeV1.IO_FAILED, name

    # The absence set is EXACTLY the four, so a later edit cannot widen it
    # without this assertion failing.
    assert windows._PATH_INVALID_STATUSES == frozenset(
        raw for raw, code in NAMED_STATUS_CODES.items()
        if code is LocalIOCodeV1.PATH_INVALID
    )

    # Counter-check: success still returns the handle the driver wrote, so the
    # test above discriminates rather than passing for any status at all.
    assert open_with(_NTSTATUS_SUCCESS) == 0x1234


def test_nt_open_treats_success_without_a_handle_as_io_failed(monkeypatch) -> None:
    """A driver that reports STATUS_SUCCESS with no handle is broken, not empty."""
    from synaptic_host.local_io_v1 import windows

    for handle in (0, windows._INVALID_HANDLE_VALUE):
        _bind_native(monkeypatch, _NTSTATUS_SUCCESS, handle=handle)
        with pytest.raises(LocalIOErrorV1) as caught:
            windows._nt_open_relative(
                7, "child", directory=False, create=False,
                access=windows._FILE_READ_ATTRIBUTES, share=windows._FILE_SHARE_ALL,
            )
        assert caught.value.code is LocalIOCodeV1.IO_FAILED, hex(handle or 0)


def test_stat_at_reports_absent_only_when_both_passes_say_the_name_is_gone(monkeypatch) -> None:
    """B-1 at the consumer: None means ABSENT and must mean nothing else."""
    from synaptic_host.local_io_v1 import windows

    identity = _dir_identity()
    port = _unbound_port()
    retained = _retained(port, 7, identity)
    monkeypatch.setattr(windows, "_query_identity", lambda handle: identity)

    # Both passes not-found: the only shape that may yield None.
    _, ntdll = _bind_native(monkeypatch, 0xC0000034, 0xC0000034)
    assert port.stat_at(retained, "child") is None
    assert ntdll.calls == 2

    # Every unnamed failure raises instead, and stops on the FIRST pass: a
    # real fault must not be retried as if it were a probe.
    for name, raw in UNNAMED_FAILURE_STATUSES.items():
        _, ntdll = _bind_native(monkeypatch, raw)
        with pytest.raises(LocalIOErrorV1) as caught:
            port.stat_at(retained, "child")
        assert caught.value.code is LocalIOCodeV1.IO_FAILED, name
        assert ntdll.calls == 1, name

    # A sharing violation keeps its own code rather than becoming an absence.
    _bind_native(monkeypatch, 0xC0000043)
    with pytest.raises(LocalIOErrorV1) as sharing:
        port.stat_at(retained, "child")
    assert sharing.value.code is LocalIOCodeV1.ROOT_IN_USE


def test_stat_at_continues_past_a_wrong_type_verdict_and_returns_the_identity(monkeypatch) -> None:
    """The file pass answering FILE_IS_A_DIRECTORY must not end the probe."""
    from synaptic_host.local_io_v1 import windows

    parent_identity = _dir_identity(0x5100)
    child_identity = _dir_identity(0x6200)
    port = _unbound_port()
    retained = _retained(port, 7, parent_identity)
    monkeypatch.setattr(
        windows, "_query_identity",
        lambda handle: child_identity if handle == 0x99 else parent_identity,
    )

    _, ntdll = _bind_native(monkeypatch, 0xC00000BA, _NTSTATUS_SUCCESS, handle=0x99)
    assert port.stat_at(retained, "child") == child_identity
    assert ntdll.calls == 2

    # Mirror case: the FILE pass succeeds, so the directory pass never runs.
    _, ntdll = _bind_native(monkeypatch, _NTSTATUS_SUCCESS, handle=0x99)
    assert port.stat_at(retained, "child") == child_identity
    assert ntdll.calls == 1


def test_open_journal_dir_never_reports_an_unreadable_journal_as_absent(monkeypatch) -> None:
    """B-1 second instance: only PATH_INVALID may become "no journal here"."""
    from synaptic_host.local_io_v1 import windows

    identity = _dir_identity()
    port = _unbound_port()
    control = _retained(port, 7, identity)
    monkeypatch.setattr(windows, "_query_identity", lambda handle: identity)
    mutation_id = "b" * 64

    _bind_native(monkeypatch, 0xC0000034)
    assert port._open_journal_dir(control, mutation_id, create=False) is None

    _bind_native(monkeypatch, 0xC0000103)  # NOT_A_DIRECTORY is still an absence
    assert port._open_journal_dir(control, mutation_id, create=False) is None

    for name, raw in UNNAMED_FAILURE_STATUSES.items():
        _bind_native(monkeypatch, raw)
        with pytest.raises(LocalIOErrorV1) as caught:
            port._open_journal_dir(control, mutation_id, create=False)
        assert caught.value.code is LocalIOCodeV1.IO_FAILED, name

    # A sharing violation is journal-shaped, not an I/O fault, and is neither
    # swallowed as absence nor relabelled IO_FAILED.
    _bind_native(monkeypatch, 0xC0000043)
    with pytest.raises(LocalIOErrorV1) as sharing:
        port._open_journal_dir(control, mutation_id, create=False)
    assert sharing.value.code is LocalIOCodeV1.JOURNAL_INVALID

    _bind_native(monkeypatch, _NTSTATUS_SUCCESS, handle=0x77)
    assert port._open_journal_dir(control, mutation_id, create=False) == 0x77


# --- F-3: journal snapshot status ------------------------------------------


def test_snapshot_journal_reraises_io_failed_and_never_answers_absent_with_a_handle() -> None:
    """F-3: an unreadable journal is not a conflicting one, and not an absent one."""
    from synaptic_host.local_io_v1 import windows

    port = _unbound_port()
    control = _retained(port, 7, _dir_identity())
    mutation_id = "c" * 64
    port._open_journal_dir = lambda control_arg, mid, create: 0x77
    port._close_calls: list[int] = []

    def snapshot():
        return port.snapshot_journal(control, mutation_id, 4)

    port._read_journal_handle = _raise_code(LocalIOCodeV1.IO_FAILED)
    with pytest.raises(LocalIOErrorV1) as caught:
        snapshot()
    assert caught.value.code is LocalIOCodeV1.IO_FAILED

    # A journal-shaped disagreement is the only thing that becomes CONFLICT.
    port._read_journal_handle = _raise_code(LocalIOCodeV1.JOURNAL_INVALID)
    assert snapshot().status is JournalSnapshotStatusV1.CONFLICT

    # An EMPTY read is INDETERMINATE, never ABSENT: the directory was opened,
    # so the journal exists and the question is only what it says. This is the
    # arm the unreachable ABSENT used to terminate.
    port._read_journal_handle = lambda handle, maximum: ((), False)
    assert snapshot().status is JournalSnapshotStatusV1.INDETERMINATE

    port._read_journal_handle = lambda handle, maximum: ((), True)
    assert snapshot().status is JournalSnapshotStatusV1.INDETERMINATE

    # ABSENT is reachable from exactly one place: the None-handle arm above
    # the try block. If a second mention appears, one of them is unreachable.
    source = inspect.getsource(windows.WindowsRetainedHandlePortV1.snapshot_journal)
    assert source.count("JournalSnapshotStatusV1.ABSENT") == 1

    # Counter-check: with no journal directory at all, ABSENT is still what
    # comes back, so the assertion above is not simply forbidding the status.
    port._open_journal_dir = lambda control_arg, mid, create: None
    assert snapshot().status is JournalSnapshotStatusV1.ABSENT


# --- F-2: names NTFS cannot carry ------------------------------------------


def test_windows_name_refuses_reserved_devices_and_over_long_components() -> None:
    """F-2: a tree Win32 cannot reopen afterwards is not a usable published tree."""
    from synaptic_host.local_io_v1 import windows

    # Reserved with or without an extension, in any case, for every COM/LPT
    # digit. The Win32 device mapping ignores the extension entirely.
    reserved = ("CON", "con", "Con", "CON.txt", "nul", "NUL.log", "aux",
                "PRN.a.b", "COM1", "com9.dat", "LPT1", "lpt9.txt", "AUX")
    for name in reserved:
        with pytest.raises(LocalIOErrorV1) as caught:
            windows._windows_name(name)
        assert caught.value.code is LocalIOCodeV1.PATH_INVALID, name

    # Counter-check: names that merely CONTAIN or extend a device name are
    # legal, so the guard is not just refusing anything that looks similar.
    for name in ("CONSOLE", "console.txt", "COM10", "COM0", "LPT0", "NULL",
                 "my-con", "conf.json", "auxiliary"):
        assert windows._windows_name(name) == name, name

    # NTFS caps one component at 255 UTF-16 code units.
    assert windows._windows_name("a" * 255) == "a" * 255
    with pytest.raises(LocalIOErrorV1) as over:
        windows._windows_name("a" * 256)
    assert over.value.code is LocalIOCodeV1.PATH_INVALID

    # A non-BMP character is a SURROGATE PAIR, so it spends two of the 255.
    pair = "\U0001F600"
    assert windows._windows_name(pair * 127 + "a") == pair * 127 + "a"
    with pytest.raises(LocalIOErrorV1) as surrogates:
        windows._windows_name(pair * 128)
    assert surrogates.value.code is LocalIOCodeV1.PATH_INVALID

    assert windows._MAX_COMPONENT_UTF16_UNITS == 255


# --- M-1: bind the opened handle to the enumerated entry --------------------


def test_descent_binds_the_opened_handle_to_the_enumerated_file_id(monkeypatch) -> None:
    """M-1: _root_component proves SPELLING; the open resolves the name again.

    Without comparing the opened object's file id to the enumerated entry's,
    a rebind between enumeration and open goes unnoticed. POSIX closes the
    same window with its before/opened/after stat triple.

    PLATFORM SPLIT, and it is about the FIXTURE, not the behaviour. The root
    is drive-qualified on NT because a driveless rooted path is not absolute
    there: Path("/anchor/middle/leaf").is_absolute() is False on Windows and
    True on Linux, so on a real host the old fixture died at the ROOT_INVALID
    guard in retain_directory before reaching any of the M-1 logic. Both
    spellings yield the same shape -- a single anchor part followed by the
    three components below -- so the assertions are identical on both
    platforms and the test runs, rather than skips, on the host.
    """
    from synaptic_host.local_io_v1 import windows

    descent_root = Path(
        "C:/anchor/middle/leaf" if os.name == "nt" else "/anchor/middle/leaf"
    )
    assert descent_root.is_absolute()
    assert descent_root.parts[1:] == ("anchor", "middle", "leaf")

    enumerated_id = 0xAAAA
    opens: list[tuple[str, int]] = []

    def fake_open(parent, name, *, directory, create=False, access, share):
        opens.append((name, access))
        return 0x200 + len(opens)

    monkeypatch.setattr(windows, "_require_ntfs", lambda path: None)
    monkeypatch.setattr(windows, "_flush_handle", lambda handle: None)
    monkeypatch.setattr(windows, "_open_relative", fake_open)
    monkeypatch.setattr(
        windows.WindowsRetainedHandlePortV1, "_root_component",
        lambda self, parent, value: (value, enumerated_id),
    )

    def run(opened_inode: int):
        port = _unbound_port()
        _bind_native(monkeypatch)
        monkeypatch.setattr(
            windows, "_query_identity", lambda handle: _dir_identity(opened_inode)
        )
        return port, port.retain_directory(descent_root)

    # Agreement: the descent completes and retains the leaf.
    opens.clear()
    port, retained = run(enumerated_id)
    assert type(retained) is RetainedDirectoryV1
    assert retained.identity.inode == enumerated_id

    # Three descents below the volume anchor, and only the LAST one takes the
    # write flavours. This is the ancestor-mask fix re-checked at its call
    # site rather than only against the constants.
    assert [name for name, _ in opens] == ["anchor", "middle", "leaf"]
    assert [access for _, access in opens[:-1]] == [
        windows._ANCESTOR_DIRECTORY_ACCESS
    ] * 2
    assert opens[-1][1] == windows._DIRECTORY_ACCESS

    # Disagreement: the name resolved to a DIFFERENT object than the one
    # enumerated and vetted, so the descent refuses rather than retaining it.
    opens.clear()
    with pytest.raises(LocalIOErrorV1) as caught:
        run(0xBBBB)
    assert caught.value.code is LocalIOCodeV1.ROOT_CHANGED


# --- M-2: no disposition through an admission handle ------------------------


def test_unlink_refuses_a_parent_handle_that_is_under_admission(monkeypatch) -> None:
    """M-2: the admission handle holds DELETE only as a share-mode token.

    Issuing a disposition through it would delete the ADMITTED DIRECTORY
    itself rather than the named child.
    """
    from synaptic_host.local_io_v1 import windows

    identity = _dir_identity()
    port = _unbound_port()
    retained = _retained(port, 7, identity)
    monkeypatch.setattr(windows, "_query_identity", lambda handle: identity)

    # _unlink_raw reads only .handle off each live lease, so a stand-in with
    # that one field exercises the same branch the real record would.
    port._admission_leases["lease-self"] = types.SimpleNamespace(handle=7)
    kernel, _ = _bind_native(monkeypatch, _NTSTATUS_SUCCESS)
    with pytest.raises(LocalIOErrorV1) as caught:
        port.unlink_at(retained, "victim")
    assert caught.value.code is LocalIOCodeV1.ADMISSION_INVALID
    # It refused BEFORE opening anything, so no disposition was issued.
    assert kernel.dispositions == 0

    # Counter-check: a lease on a DIFFERENT handle does not block the delete,
    # so the guard discriminates rather than refusing every unlink.
    port._admission_leases["lease-self"] = types.SimpleNamespace(handle=8)
    kernel, _ = _bind_native(monkeypatch, _NTSTATUS_SUCCESS)
    port.unlink_at(retained, "victim")
    assert kernel.dispositions == 1


# --- M-3 and M-10: cleanup paths ------------------------------------------


def test_retain_file_handle_preserves_the_identity_code_and_closes_the_handle(monkeypatch) -> None:
    """M-3: collapsing to IO_FAILED lost the ROOT_CHANGED a reparse point raises.

    The directory sibling re-raises; the file one used to swallow the code, so
    the same physical condition reported differently by handle kind.
    """
    from synaptic_host.local_io_v1 import windows

    port = _unbound_port()
    closed: list[int] = []
    monkeypatch.setattr(windows, "_close_handle_quietly", closed.append)

    for code in (LocalIOCodeV1.ROOT_CHANGED, LocalIOCodeV1.IO_FAILED,
                 LocalIOCodeV1.CAPABILITY_UNAVAILABLE):
        closed.clear()
        monkeypatch.setattr(windows, "_query_identity", _raise_code(code))
        with pytest.raises(LocalIOErrorV1) as caught:
            port._retain_file_handle(0x321)
        assert caught.value.code is code
        assert closed == [0x321], code
        assert port._files == {}


def test_close_handle_quietly_swallows_what_close_handle_raises() -> None:
    """M-10: it runs in finally arms, where a raise would mask the real error.

    PLATFORM SPLIT on the counter-check only. The swallow itself is the same
    claim everywhere, but WHY the inner call fails is not: off Windows the
    lazy binder refuses to bind at all and the failure is
    CAPABILITY_UNAVAILABLE, while on a real host the binder succeeds and the
    real CloseHandle rejects the bogus handle, which maps to IO_FAILED. The
    test previously asserted the off-Windows code unconditionally and so
    failed on the host. What the swallow needs is only that the loud form
    RAISES on this input, and both codes are that.
    """
    from synaptic_host.local_io_v1 import windows

    # The swallow: identical claim on both platforms.
    assert windows._close_handle_quietly(0x1) is None

    # Counter-check: the loud form DOES raise on the same input, so the line
    # above is measuring the swallow and not an operation that cannot fail.
    expected = (
        LocalIOCodeV1.IO_FAILED if os.name == "nt"
        else LocalIOCodeV1.CAPABILITY_UNAVAILABLE
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        windows._close_handle(0x1)
    assert caught.value.code is expected

    # It must not swallow an interpreter-level exit.
    source = inspect.getsource(windows._close_handle_quietly)
    assert "except Exception:" in source
    assert "except BaseException:" not in source


# --- F-1: storage roots must be local and inside the project ----------------
#
# These belong beside the rest of the registry tests in test_config.py; they
# live here because task #44 confines this cycle's test edits to this file.


def test_storage_config_refuses_unc_roots_and_roots_outside_the_project(tmp_path: Path) -> None:
    """F-1: a non-project root must name a local path inside the project.

    A UNC share has no ancestor chain the retained-handle descent can walk
    from a project anchor, and no containment relation to the project at all.
    """
    from synaptic_host.local_io_v1.config import StorageRegistryV1

    def load(location: str) -> StorageRegistryV1:
        config_path = tmp_path / "storage.json"
        config_path.write_text(json.dumps({
            "schema_version": "synaptic-host-storage/v1",
            "roots": [{
                "root_ref": "opaque", "location": location,
                "access": "read_create", "permit_ref": "permit-opaque",
            }],
        }), encoding="utf-8")
        return StorageRegistryV1.load(config_path, project_root=tmp_path)

    # Unchanged: a contained absolute root and a project:// root both load.
    assert load(str(tmp_path / "inside")) is not None
    assert load(str(tmp_path / "inside" / "deeper")) is not None
    assert load(str(tmp_path)) is not None
    assert load("project://spool") is not None

    refused = {
        # These six are UNC or Win32-namespace spellings. On POSIX they are
        # already refused one line earlier, because Path() does not read them
        # as absolute -- so this loop does NOT discriminate the UNC clause
        # here. test_storage_config_refuses_the_unc_forms_before_it_asks_pathlib
        # below carries that weight; a behavioural check needs a Windows host.
        "unc share": "\\\\server\\share",
        "unc forward slashes": "//server/share",
        "unc device form": "\\\\?\\UNC\\server\\share",
        "extended length prefix": "\\\\?\\C:\\host",
        "device namespace": "\\\\.\\PhysicalDrive0",
        "mixed separators": "\\/server/share",
        # Absolute, but not under the project anchor.
        "sibling of the project": str(tmp_path.parent / "outside"),
        "unrelated absolute": "/etc",
        # Lexically prefixed but a DIFFERENT directory: the containment test
        # compares path COMPONENTS, never a string prefix.
        "prefix twin": str(tmp_path) + "-twin",
        # Prefix-matches the anchor yet escapes it, which is why ".." is
        # refused outright instead of being normalised away.
        "dot dot escape": str(tmp_path / ".." / "escape"),
    }
    for label, location in refused.items():
        with pytest.raises(LocalIOErrorV1) as caught:
            load(location)
        assert caught.value.code is LocalIOCodeV1.CONFIG_INVALID, label

    # A single leading separator is an ordinary POSIX absolute path and is
    # still judged by containment alone, not by the UNC rule.
    assert load(str(tmp_path / "single-separator-ok")) is not None


def test_storage_config_refuses_the_unc_forms_before_it_asks_pathlib() -> None:
    """F-1: the two-separator refusal must not depend on the running platform.

    ``Path`` is platform-flavoured: on POSIX "\\\\server\\share" is a relative
    name and the existing is_absolute() check already refuses it, while on
    Windows it is absolute and reaches further. The guard therefore has to sit
    ABOVE the Path construction so both platforms reach the same verdict, and
    that ordering is what this test pins. The behavioural half needs a
    Windows host and belongs to the native-host suite.
    """
    from synaptic_host.local_io_v1 import config

    body = inspect.getsource(config.StorageRegistryV1.from_bytes).splitlines()
    guard = [
        index for index, line in enumerate(body)
        if 'location[0] in "\\\\/"' in line and 'location[1] in "\\\\/"' in line
    ]
    assert len(guard) == 1, "the two-separator refusal is missing or duplicated"

    construction = [index for index, line in enumerate(body) if "Path(location)" in line]
    assert len(construction) == 1
    assert guard[0] < construction[0], "the UNC refusal must precede Path(location)"

    # Counter-check on the corpus itself: every spelling this guard is meant
    # to catch really does open on two separators, and the local absolute
    # forms it must NOT catch do not.
    for name in ("\\\\server\\share", "//server/share", "\\\\?\\UNC\\server\\share",
                 "\\\\?\\C:\\host", "\\\\.\\PhysicalDrive0", "\\/server/share"):
        assert name[0] in "\\/" and name[1] in "\\/", name
    for name in ("C:\\host\\root", "/srv/project/root", "/a"):
        assert not (len(name) >= 2 and name[0] in "\\/" and name[1] in "\\/"), name


# --- Amendment items: M-7, M-11, and the _reject_collision code flattening ---


def test_list_names_no_longer_vetoes_a_listing_that_holds_a_junction(monkeypatch) -> None:
    """M-7: the redirect boundary is at OPEN time, not at enumeration time.

    Everything else _directory_entries enforces must survive the narrowing,
    so this pins what list_names_at still refuses as well as what it stopped
    refusing.
    """
    from synaptic_host.local_io_v1 import windows

    def entries(rows):
        monkeypatch.setattr(
            windows, "_directory_entries", lambda handle, maximum: tuple(rows)
        )

    # Narrowed: reparse siblings are listed, in enumeration order, and the
    # reparse flag never reaches the caller.
    entries([("junction", True, 0x11), ("real", False, 0x22), ("also", True, 0x33)])
    assert windows._directory_names(0, 4096) == ("junction", "real", "also")

    # Unchanged: whatever the enumeration itself refuses still propagates
    # with its own code rather than being swallowed by the names wrapper.
    for code in (LocalIOCodeV1.ROOT_CHANGED,       # casefold collision
                 LocalIOCodeV1.LIMIT_EXCEEDED,     # entry cap
                 LocalIOCodeV1.IO_FAILED):         # undecodable record
        monkeypatch.setattr(windows, "_directory_entries", _raise_code(code))
        with pytest.raises(LocalIOErrorV1) as caught:
            windows._directory_names(0, 4096)
        assert caught.value.code is code

    # The veto is gone from the source, not merely unreachable.
    source = inspect.getsource(windows._directory_names)
    assert "is_reparse" not in source

    # Counter-check that the boundary really did move rather than vanish:
    # _root_component still refuses a reparse point on the MATCHED entry.
    entries([("junction", True, 0x11)])
    with pytest.raises(LocalIOErrorV1) as matched:
        windows.WindowsRetainedHandlePortV1._root_component(None, 0, "junction")
    assert matched.value.code is LocalIOCodeV1.ROOT_CHANGED


def test_windows_reports_the_same_admission_feature_string_as_posix() -> None:
    """M-11: the detector must emit a name the gate and the POSIX port share.

    "directory-id-admission" was a string nothing else in the codebase spelled,
    so the gate that keys on the admission features could not match it.
    """
    from synaptic_host.local_io_v1 import posix, windows

    assert "directory-inode-admission" in windows._FEATURES
    assert "directory-id-admission" not in windows._FEATURES
    # One vocabulary: the POSIX port publishes the identical string.
    assert "directory-inode-admission" in set(posix._FEATURES)
    # And the gate this file already pins accepts it under that name.
    assert set(WINDOWS_ADMISSION_FEATURES) <= set(windows._FEATURES)


def test_reject_collision_keeps_the_port_code_instead_of_flattening_it(monkeypatch) -> None:
    """A directory that is too large is not a disk failure.

    _reject_collision wrapped list_names_at in a bare BaseException arm that
    rewrote every port verdict to IO_FAILED, so LIMIT_EXCEEDED and
    ROOT_CHANGED both reached the caller as "the disk failed".
    """
    port = FakePosixFilesystemPortV1()
    base = Path.cwd() / ".fake-metadata" / "reject-collision"
    port.add_root(base, "data")
    authenticator = _Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform=LINUX_PLATFORM)
    binding = _binding(base, "data", authenticator)
    directory = object()

    for code in (LocalIOCodeV1.LIMIT_EXCEEDED, LocalIOCodeV1.ROOT_CHANGED):
        monkeypatch.setattr(port, "list_names_at", _raise_code(code))
        with pytest.raises(LocalIOErrorV1) as caught:
            filesystem._reject_collision(directory, "child", may_be_missing=True)
        assert caught.value.code is code, code

    # Counter-check: a failure the port did NOT classify is still IO_FAILED,
    # so the new arm narrows the rewrite rather than removing it.
    def explode(*args, **kwargs):
        raise ValueError("not a closed error")

    monkeypatch.setattr(port, "list_names_at", explode)
    with pytest.raises(LocalIOErrorV1) as unclassified:
        filesystem._reject_collision(directory, "child", may_be_missing=True)
    assert unclassified.value.code is LocalIOCodeV1.IO_FAILED

    assert binding.root_ref == "data"


# --- M-4 and F-4: behaviour of the two guards, with ONLY the native call
# --- stubbed. Everything below drives the real windows.py function bodies.
#
# EVIDENCE CLASS for every test in this section: STUBBED-NATIVE, Linux-runnable.
# The kernel32 entry point is replaced; the guard arithmetic, the branch and
# the error mapping under test are the production ones. A green here is NOT
# evidence that a real NT enumeration or a real NTFS reparse point behaves this
# way -- that claim belongs to the host-only twins in
# tests/synaptic_host/test_publication_local_windows.py, which are named
# "..._on_a_real_nt_..." so the two can never be confused.


class _InformationKernel:
    """kernel32 stand-in for the three GetFileInformationByHandleEx classes.

    Writes through the byref() out-parameter exactly as the real call does,
    so _query_identity runs its own struct reads rather than a fake identity.
    """

    def __init__(self, attributes: int) -> None:
        self.attributes = attributes
        self.classes: list[int] = []

    def GetFileInformationByHandleEx(self, handle, info_class, ref, size) -> int:
        from synaptic_host.local_io_v1 import windows

        self.classes.append(info_class)
        target = ref._obj
        if info_class == windows._FILE_BASIC_INFO_CLASS:
            target.FileAttributes = self.attributes
            target.ChangeTime = windows._FILETIME_UNIX_EPOCH_TICKS
            target.LastWriteTime = windows._FILETIME_UNIX_EPOCH_TICKS
        elif info_class == windows._FILE_STANDARD_INFO_CLASS:
            target.NumberOfLinks = 1
            target.Directory = 1
            target.EndOfFile = 0
        elif info_class == windows._FILE_ID_INFO_CLASS:
            target.VolumeSerialNumber = 0x99
            target.FileId[0] = 0x42
        return 1


def test_query_identity_refuses_a_reparse_point_after_the_open(monkeypatch) -> None:
    """M-4: the post-open re-check is a BEHAVIOUR, not just a source line.

    The descent vets a name before it opens it, but the object behind that
    name can be swapped for a junction between the vet and the open. The only
    thing that closes that window is re-reading FileAttributes off the handle
    that was actually opened and refusing a reparse point there. Until now the
    re-check was pinned only by reading the source, which cannot tell whether
    the branch is reachable or which code it raises.

    Both directions are driven, so the test discriminates: clearing the single
    reparse bit turns the refusal into a normal identity.

    EVIDENCE CLASS: stubbed-native. See the section header.
    """
    from synaptic_host.local_io_v1 import windows

    directory_attribute = 0x10
    reparse = windows._FILE_ATTRIBUTE_REPARSE_POINT

    # Direction 1: an ordinary directory yields an identity.
    plain = _InformationKernel(directory_attribute)
    monkeypatch.setattr(windows, "_windows_native", lambda: (plain, None))
    identity = windows._query_identity(0x1234)
    assert isinstance(identity, LocalFileIdentityV1)
    assert stat.S_ISDIR(identity.mode)
    assert identity.inode == 0x42

    # Direction 2: the SAME call with only the reparse bit added is refused,
    # and refused as ROOT_CHANGED rather than as a generic IO failure -- the
    # descent reads that code as "the tree moved under me".
    redirected = _InformationKernel(directory_attribute | reparse)
    monkeypatch.setattr(windows, "_windows_native", lambda: (redirected, None))
    with pytest.raises(LocalIOErrorV1) as caught:
        windows._query_identity(0x1234)
    assert caught.value.code is LocalIOCodeV1.ROOT_CHANGED

    # The check happens AFTER the handle has been interrogated, not as a
    # pre-filter: all three information classes were read before the refusal.
    assert redirected.classes == [
        windows._FILE_BASIC_INFO_CLASS,
        windows._FILE_STANDARD_INFO_CLASS,
        windows._FILE_ID_INFO_CLASS,
    ]


class _EnumerationKernel:
    """kernel32 stand-in that replays a roster of FILE_ID_EXTD_DIR_INFO rows.

    Packs real records into the caller's real buffer, so _directory_entries
    runs its own struct.unpack_from, its own bounds arithmetic and its own
    casefold-collision set. Only the syscall is synthetic.

    NOTE: it refuses to run past the roster instead of reporting
    ERROR_NO_MORE_FILES. ctypes.get_last_error() exists only on Windows, so
    the natural end-of-enumeration exit in _directory_entries CANNOT execute
    off Windows -- an enumeration driven to exhaustion here would die with
    AttributeError inside ctypes, not with a clean stop. Every arm below
    therefore leaves the loop through a guard, which is the thing under test
    anyway.
    """

    def __init__(self, total: int, per_batch: int = 500) -> None:
        self.names = [f"entry{index:06d}" for index in range(total)]
        self.per_batch = per_batch
        self.cursor = 0
        self.batches = 0

    @staticmethod
    def _record(next_offset: int, name: str) -> bytes:
        from synaptic_host.local_io_v1 import windows

        encoded = name.encode("utf-16-le")
        body = windows._DIRECTORY_RECORD.pack(
            next_offset, 0, 0, 0, 0, 0, 0, 0,
            0, len(encoded), 0, 0, b"\0" * 16,
        ) + encoded
        return body + b"\0" * (next_offset - len(body) if next_offset else 0)

    def _batch(self, names) -> bytes:
        from synaptic_host.local_io_v1 import windows

        payload = b""
        for index, name in enumerate(names):
            size = windows._DIRECTORY_RECORD.size + len(name.encode("utf-16-le"))
            last = index == len(names) - 1
            payload += self._record(0 if last else ((size + 7) // 8) * 8, name)
        return payload

    def GetFileInformationByHandleEx(self, handle, info_class, buffer, size) -> int:
        import ctypes

        self.batches += 1
        chunk = self.names[self.cursor:self.cursor + self.per_batch]
        self.cursor += len(chunk)
        if not chunk:
            raise AssertionError(
                "the enumeration ran past its roster; off Windows the "
                "ERROR_NO_MORE_FILES exit cannot be reached, so an arm that "
                "gets here is not testing what it claims to test"
            )
        payload = self._batch(chunk)
        assert len(payload) <= size, (len(payload), size)
        ctypes.memmove(buffer, payload, len(payload))
        return 1


def test_directory_entries_cap_trips_with_a_stubbed_enumeration(monkeypatch) -> None:
    """F-4 / R-7: the ancestor enumeration cap, driven at windows.py itself.

    The cap was previously covered only by stubbing _directory_entries to
    raise LIMIT_EXCEEDED and watching _directory_names propagate it, which
    tests the wrapper and asserts the cap into existence rather than measuring
    it. This drives the real loop and its real bound.

    Three arms, and the middle one is what makes the pair discriminating:
    a `>=` instead of a `>` in the guard would redden the exactly-at-the-cap
    arm while leaving the over-by-one arm green.

    EVIDENCE CLASS: stubbed-native. See the section header. The twin that
    proves a real NT enumeration trips the same bound is
    test_directory_entries_cap_trips_on_a_real_nt_enumeration in
    tests/synaptic_host/test_publication_local_windows.py.
    """
    from synaptic_host.local_io_v1 import windows
    from synaptic_host.local_io_v1.filesystem import MAX_DIRECTORY_ENTRIES

    def enumerate_over(total: int, maximum: int):
        kernel = _EnumerationKernel(total)
        monkeypatch.setattr(windows, "_windows_native", lambda: (kernel, None))
        return windows._directory_entries(0x1234, maximum)

    # One entry past the cap is refused, and refused as LIMIT_EXCEEDED: a
    # directory that is too large is a bound being hit, not a disk failure.
    with pytest.raises(LocalIOErrorV1) as caught:
        enumerate_over(MAX_DIRECTORY_ENTRIES + 1, MAX_DIRECTORY_ENTRIES)
    assert caught.value.code is LocalIOCodeV1.LIMIT_EXCEEDED

    # Exactly at the cap is allowed through, entries intact. The guard is
    # strictly greater-than; this arm is what kills the off-by-one mutant.
    entries = enumerate_over(MAX_DIRECTORY_ENTRIES, MAX_DIRECTORY_ENTRIES - 1)
    assert len(entries) == MAX_DIRECTORY_ENTRIES
    assert entries[0][0] == "entry000000"
    assert all(is_reparse is False for _, is_reparse, _ in entries)

    # M-9 CHARACTERIZATION TEST. This arm pins CURRENT behaviour, not desired
    # behaviour: the fix is deferred to remediation cycle 2 by user decision,
    # and when M-9 lands this assertion FLIPS rather than being deleted.
    # Measured, and recorded because it is NOT what the signature suggests:
    # the `maximum` parameter does not bound the returned tuple. LIMIT_EXCEEDED
    # is keyed to the module constant MAX_DIRECTORY_ENTRIES, while `maximum`
    # only ends the loop at the next BATCH boundary, so the caller can be
    # handed a whole batch more than it asked for. This is inert today because
    # every live call site passes MAX_DIRECTORY_ENTRIES itself; the assertion
    # exists so that stops being true silently.
    loose = enumerate_over(2000, 10)
    assert len(loose) > 10
