"""Concrete retained-handle Windows adapter for host local I/O v1.

Location: ``synaptic_host/local_io_v1/windows.py``.

This module is the native-Windows sibling of ``local_io_v1/posix.py``. It
supplies ``WindowsRetainedHandlePortV1``, a structural implementation of the
``PosixFilesystemPortV1`` protocol declared in ``local_io_v1/filesystem.py``,
plus ``detect_windows_capability_v1``. ``LocalFilesystemV1`` drives the port and
owns every shared invariant; the port owns only the platform primitives.

How it is used with the rest of the tree:

* ``publication_composition.py`` selects this port over the POSIX one through a
  two-branch factory keyed on ``os.name == "nt"``. The import is branch-local so
  a POSIX process never binds ``ctypes.WinDLL`` and a Windows process never
  imports ``fcntl``.
* ``local_io_v1/filesystem.py`` calls the 21 protocol methods and enforces the
  create-commit protocol, including the hardlink-count 1 -> 2 -> 1 proof.
* ``local_io_v1/model.py`` owns ``LocalFileIdentityV1`` and the closed error
  taxonomy. This module satisfies those invariants on NTFS; it never relaxes
  them and ``model.py`` is not modified by this closure.

Design rules this module must not break:

1. Every mutation is handle-relative. ``retain_directory`` is the only entry
   point that accepts a full path, and it re-proves identity at every component.
2. ``fsync_directory`` issues a real ``FlushFileBuffers`` barrier and raises on
   failure. It must never degrade to a silent no-op: a no-op would satisfy every
   ``nlink`` and ``changed_ns`` assertion in the shared create-commit sequence
   while destroying the crash-safety property, and the loss would be invisible
   until a real power failure.
3. The synthesised POSIX ``mode`` is a fixed named constant. It is hashed into
   ``registry_digest`` through ``identity.canonical()``, so it must never be
   derived from an ACL or a umask.
4. The commit primitive is ``NtSetInformationFile`` with
   ``FileLinkInformationEx``, which is handle-relative. ``CreateHardLinkW`` is
   deliberately not used: it resolves a full path and would reopen the redirect
   window that the retained-handle design exists to close.
5. Errors stay closed. Only the stable ``LocalIOCodeV1`` is observable; no Win32
   error number, NT status, path, or handle value may reach a message.

This module is import-clean on non-Windows hosts: the ``ctypes.WinDLL`` binding
is lazy and the ``ctypes.Structure`` definitions use platform-neutral C types.
"""

from __future__ import annotations

import os
import re
import secrets
import stat
import struct
import sys
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import ctypes

from .filesystem import MAX_DIRECTORY_ENTRIES, OpenFileV1
from .model import (
    LocalAdmissionRootNodeV1,
    CapabilityStatusV1,
    CreateJournalRecordV1,
    JournalPublishResultV1,
    JournalPublishStatusV1,
    JournalSnapshotStatusV1,
    JournalSnapshotV1,
    LocalFileIdentityV1,
    LocalFilesystemCapabilityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    RetainedDirectoryAdmissionV1,
    RetainedDirectoryV1,
    canonical_relative_components_v1,
    canonical_posix_root_component_v1,
    checked_sha256,
    digest_v1,
    journal_record_bytes_v1,
    parse_journal_record_v1,
)


# --------------------------------------------------------------------------
# Evidence contract constants.
#
# Windows has no POSIX mode. These two values are synthesised for the model
# only; real access control on Windows stays the SDDL DACL applied and
# ACE-validated in security.py. Every shared consumer inspects only the file
# type nibble (mode & 0o170000) and never the permission bits, but the value IS
# hashed into registry_digest through LocalFileIdentityV1.canonical(), so it
# must remain a fixed constant. Deriving it from an ACL or a umask would make
# the publication digest vary with directory permissions.
# --------------------------------------------------------------------------
WINDOWS_SYNTHETIC_FILE_MODE_V1 = stat.S_IFREG | 0o600
WINDOWS_SYNTHETIC_DIRECTORY_MODE_V1 = stat.S_IFDIR | 0o700

# FILETIME is 100 ns ticks since 1601-01-01 UTC. This is the tick count of the
# Unix epoch, used to convert into the non-negative nanoseconds the model wants.
_FILETIME_UNIX_EPOCH_TICKS = 116_444_736_000_000_000

_MAX_CHUNK_BYTES = 1_048_576
_MAX_JOURNAL_RECORD_BYTES = 16_384

# NTFS carries at most 255 UTF-16 code units in one path component.
_MAX_COMPONENT_UTF16_UNITS = 255

# Win32 device names. Reserved with or without an extension and in any case,
# so "con", "CON.txt" and "com1.log" are all refused along with "CON".
_RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{digit}" for digit in range(1, 10)}
    | {f"LPT{digit}" for digit in range(1, 10)}
)

_FEATURES = tuple(sorted((
    "crash-released-admission",
    # M-11: one neutral vocabulary across both ports. posix.py:56 and the
    # gate at filesystem.py:578,591 already spell it this way, so the old
    # "directory-id-admission" was a string the gate did not recognise.
    "directory-inode-admission",
    "exclusive-create",
    "flush-file-buffers",
    "handle-relative-open",
    "handle-relative-stat",
    "hardlink-at",
    "nofollow",
    "retained-handles",
    "share-mode-directory-admission",
)))

# Win32 / NT constants. Values mirror docker_staging.py, which already drives
# these same primitives in this repository.
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_READ_DATA = 0x00000001
_FILE_LIST_DIRECTORY = 0x00000001
_FILE_WRITE_DATA = 0x00000002
_FILE_ADD_FILE = 0x00000002
_FILE_ADD_SUBDIRECTORY = 0x00000004
_FILE_TRAVERSE = 0x00000020
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_WRITE_ATTRIBUTES = 0x00000100
_DELETE = 0x00010000
_SYNCHRONIZE = 0x00100000

_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_FILE_SHARE_READ_WRITE = _FILE_SHARE_READ | _FILE_SHARE_WRITE
_FILE_SHARE_ALL = _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE

_OPEN_EXISTING = 3
_FILE_OPEN = 1
_FILE_CREATE = 2

_FILE_DIRECTORY_FILE = 0x00000001
_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
_FILE_NON_DIRECTORY_FILE = 0x00000040
_FILE_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_OBJ_DONT_REPARSE = 0x00001000

_FILE_BASIC_INFO_CLASS = 0
_FILE_STANDARD_INFO_CLASS = 1
_FILE_ID_INFO_CLASS = 18
_FILE_ID_EXTD_DIRECTORY_INFO_CLASS = 19
_FILE_ID_EXTD_DIRECTORY_RESTART_INFO_CLASS = 20
_FILE_DISPOSITION_INFO_EX_CLASS = 21
_FILE_DISPOSITION_DELETE = 0x00000001

# NT information class used by NtSetInformationFile for the handle-relative
# hardlink. This is the analogue of os.link(..., dst_dir_fd=) on POSIX.
_FILE_LINK_INFORMATION_EX_CLASS = 72

_STATUS_OBJECT_NAME_COLLISION = 0xC0000035
_STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
_STATUS_OBJECT_PATH_NOT_FOUND = 0xC000003A
_STATUS_FILE_IS_A_DIRECTORY = 0xC00000BA
_STATUS_NOT_A_DIRECTORY = 0xC0000103
_STATUS_SHARING_VIOLATION = 0xC0000043

# The ONLY statuses that mean "the name does not resolve to an object of the
# requested type". They are the closed definition of PATH_INVALID out of
# _nt_open_relative, and stat_at's two-pass probe treats exactly this set as
# "keep probing". Every other failing status is a real error and maps to
# IO_FAILED: a default of PATH_INVALID made ACCESS_DENIED, DELETE_PENDING and
# resource exhaustion indistinguishable from absence, which stat_at then
# reported as None and filesystem.py turned into DEFINITELY_ABSENT. Adding a
# status here therefore widens what the port is willing to call "absent", so
# add one only when it genuinely means the name did not resolve.
_PATH_INVALID_STATUSES = frozenset({
    _STATUS_OBJECT_NAME_NOT_FOUND,
    _STATUS_OBJECT_PATH_NOT_FOUND,
    _STATUS_FILE_IS_A_DIRECTORY,
    _STATUS_NOT_A_DIRECTORY,
})

_ERROR_NO_MORE_FILES = 18
_ERROR_SHARING_VIOLATION = 32
_ERROR_FILE_NOT_FOUND = 2
_ERROR_PATH_NOT_FOUND = 3

_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# FILE_ID_EXTD_DIR_INFO fixed header, matching docker_staging.py:212.
_DIRECTORY_RECORD = struct.Struct("<IIqqqqqqIIII16s")

# Directory handles carry read and write flavours plus SYNCHRONIZE. They
# deliberately do NOT request DELETE: the admission handle distinguishes itself
# by requesting DELETE, which is the only sharing axis on Windows that can
# express single-writer exclusion (see acquire_directory_admission).
_DIRECTORY_ACCESS = (
    _FILE_LIST_DIRECTORY
    | _FILE_TRAVERSE
    | _FILE_READ_ATTRIBUTES
    | _FILE_WRITE_ATTRIBUTES
    | _FILE_ADD_FILE
    | _FILE_ADD_SUBDIRECTORY
    | _SYNCHRONIZE
)
_ADMISSION_ACCESS = _DIRECTORY_ACCESS | _DELETE

# Ancestors on the way DOWN to a retained root are only traversed, listed and
# stat-ed; nothing is ever created, linked, unlinked or stamped in them. They
# therefore take no write flavour. This matters because a non-elevated process
# cannot obtain write access to C:\, so asking for _DIRECTORY_ACCESS on every
# ancestor made every root on the system volume unreachable -- including the
# default pytest basetemp under C:\Users\<user>\AppData\Local\Temp.
# FILE_LIST_DIRECTORY is required because _root_component enumerates the
# PARENT to prove exact-case spelling; FILE_READ_ATTRIBUTES is required
# because the descent calls _query_identity on each opened directory;
# FILE_TRAVERSE is required to open a child relative to it; and SYNCHRONIZE is
# required by _FILE_SYNCHRONOUS_IO_NONALERT. The retained LEAF keeps the full
# _DIRECTORY_ACCESS the design requires.
_ANCESTOR_DIRECTORY_ACCESS = (
    _FILE_LIST_DIRECTORY
    | _FILE_TRAVERSE
    | _FILE_READ_ATTRIBUTES
    | _SYNCHRONIZE
)


@dataclass(slots=True)
class _LiveDirectoryAdmissionV1:
    """Mirror of the POSIX port's live admission record."""

    lease: RetainedDirectoryAdmissionV1
    directory: RetainedDirectoryV1
    handle: int
    root_key: tuple[int, int, int, str]
    state: str = "ACTIVE"


_WINDOWS_NATIVE: tuple[object, object] | None = None


def _windows_native() -> tuple[object, object]:
    """Bind kernel32 and ntdll lazily so this module imports on POSIX."""
    global _WINDOWS_NATIVE
    if os.name != "nt":
        raise LocalIOErrorV1(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
    if _WINDOWS_NATIVE is None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        kernel32.CreateFileW.argtypes = (
            ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
            ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
        )
        kernel32.CreateFileW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
        kernel32.CloseHandle.restype = ctypes.c_int
        kernel32.FlushFileBuffers.argtypes = (ctypes.c_void_p,)
        kernel32.FlushFileBuffers.restype = ctypes.c_int
        kernel32.GetFileInformationByHandleEx.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong,
        )
        kernel32.GetFileInformationByHandleEx.restype = ctypes.c_int
        kernel32.SetFileInformationByHandle.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong,
        )
        kernel32.SetFileInformationByHandle.restype = ctypes.c_int
        kernel32.GetFinalPathNameByHandleW.argtypes = (
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
        )
        kernel32.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        kernel32.GetVolumePathNameW.argtypes = (
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong,
        )
        kernel32.GetVolumePathNameW.restype = ctypes.c_int
        kernel32.GetVolumeInformationW.argtypes = (
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_wchar_p, ctypes.c_ulong,
        )
        kernel32.GetVolumeInformationW.restype = ctypes.c_int
        kernel32.ReadFile.argtypes = (
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p,
        )
        kernel32.ReadFile.restype = ctypes.c_int
        kernel32.WriteFile.argtypes = (
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p,
        )
        kernel32.WriteFile.restype = ctypes.c_int
        ntdll.NtCreateFile.argtypes = (
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong,
            ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatusBlock),
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
        )
        ntdll.NtCreateFile.restype = ctypes.c_long
        ntdll.NtSetInformationFile.argtypes = (
            ctypes.c_void_p, ctypes.POINTER(_IoStatusBlock), ctypes.c_void_p,
            ctypes.c_ulong, ctypes.c_int,
        )
        ntdll.NtSetInformationFile.restype = ctypes.c_long
        _WINDOWS_NATIVE = kernel32, ntdll
    return _WINDOWS_NATIVE


class _UnicodeString(ctypes.Structure):
    _fields_ = (
        ("Length", ctypes.c_ushort),
        ("MaximumLength", ctypes.c_ushort),
        ("Buffer", ctypes.c_wchar_p),
    )


class _ObjectAttributes(ctypes.Structure):
    _fields_ = (
        ("Length", ctypes.c_ulong),
        ("RootDirectory", ctypes.c_void_p),
        ("ObjectName", ctypes.POINTER(_UnicodeString)),
        ("Attributes", ctypes.c_ulong),
        ("SecurityDescriptor", ctypes.c_void_p),
        ("SecurityQualityOfService", ctypes.c_void_p),
    )


class _IoStatusValue(ctypes.Union):
    _fields_ = (("Status", ctypes.c_long), ("Pointer", ctypes.c_void_p))


class _IoStatusBlock(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = (("value", _IoStatusValue), ("Information", ctypes.c_size_t))


class _FileIdInfo(ctypes.Structure):
    _fields_ = (
        ("VolumeSerialNumber", ctypes.c_ulonglong),
        ("FileId", ctypes.c_ubyte * 16),
    )


class _FileStandardInfo(ctypes.Structure):
    _fields_ = (
        ("AllocationSize", ctypes.c_longlong),
        ("EndOfFile", ctypes.c_longlong),
        ("NumberOfLinks", ctypes.c_ulong),
        ("DeletePending", ctypes.c_ubyte),
        ("Directory", ctypes.c_ubyte),
    )


class _FileBasicInfo(ctypes.Structure):
    _fields_ = (
        ("CreationTime", ctypes.c_longlong),
        ("LastAccessTime", ctypes.c_longlong),
        ("LastWriteTime", ctypes.c_longlong),
        ("ChangeTime", ctypes.c_longlong),
        ("FileAttributes", ctypes.c_ulong),
    )


class _FileDispositionInfoEx(ctypes.Structure):
    _fields_ = (("Flags", ctypes.c_ulong),)


def _closed(code: LocalIOCodeV1 = LocalIOCodeV1.IO_FAILED) -> LocalIOErrorV1:
    """Build a closed error. Only the stable code is ever observable."""
    return LocalIOErrorV1(code)


def _filetime_to_unix_ns(value: int) -> int:
    """Convert a FILETIME tick count into non-negative Unix nanoseconds.

    The model rejects negative integers, so pre-1970 timestamps clamp to zero.
    The shared monotonicity assertions use a strict ``<``, so two operations
    inside one 100 ns tick compare equal and pass.
    """
    ticks = int(value) - _FILETIME_UNIX_EPOCH_TICKS
    if ticks < 0:
        return 0
    return ticks * 100


def _identity_from_information(
    basic: _FileBasicInfo, standard: _FileStandardInfo, file_id: _FileIdInfo
) -> LocalFileIdentityV1:
    """Map the three Windows information classes onto the shared identity.

    ``nlink`` carries ``NumberOfLinks`` exactly: it is the commit proof the
    shared create-commit sequence asserts as 1 -> 2 -> 1. ``inode`` carries the
    full 128-bit ``FileId`` as a Python int with no reduction, which the model
    accepts because it bounds integer fields only by non-negative int, and which
    reaches ``registry_digest`` losslessly because the canonical serialiser
    renders Python big integers in full decimal.
    """
    is_directory = bool(standard.Directory)
    return LocalFileIdentityV1(
        device=int(file_id.VolumeSerialNumber),
        inode=int.from_bytes(bytes(file_id.FileId), "little", signed=False),
        mode=(
            WINDOWS_SYNTHETIC_DIRECTORY_MODE_V1 if is_directory
            else WINDOWS_SYNTHETIC_FILE_MODE_V1
        ),
        nlink=max(1, int(standard.NumberOfLinks)),
        changed_ns=_filetime_to_unix_ns(int(basic.ChangeTime)),
        modified_ns=_filetime_to_unix_ns(int(basic.LastWriteTime)),
        size=max(0, int(standard.EndOfFile)),
    )


def _query_identity(handle: int) -> LocalFileIdentityV1:
    """Read the three information classes off a live handle."""
    kernel32, _ = _windows_native()
    basic = _FileBasicInfo()
    standard = _FileStandardInfo()
    file_id = _FileIdInfo()
    if (
        not kernel32.GetFileInformationByHandleEx(
            ctypes.c_void_p(handle), _FILE_BASIC_INFO_CLASS,
            ctypes.byref(basic), ctypes.sizeof(basic),
        )
        or not kernel32.GetFileInformationByHandleEx(
            ctypes.c_void_p(handle), _FILE_STANDARD_INFO_CLASS,
            ctypes.byref(standard), ctypes.sizeof(standard),
        )
        or not kernel32.GetFileInformationByHandleEx(
            ctypes.c_void_p(handle), _FILE_ID_INFO_CLASS,
            ctypes.byref(file_id), ctypes.sizeof(file_id),
        )
    ):
        raise _closed()
    if int(basic.FileAttributes) & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise _closed(LocalIOCodeV1.ROOT_CHANGED)
    return _identity_from_information(basic, standard, file_id)


def _close_handle(handle: int) -> None:
    kernel32, _ = _windows_native()
    if not kernel32.CloseHandle(ctypes.c_void_p(handle)):
        raise _closed()


def _close_handle_quietly(handle: int) -> None:
    """Best-effort close for cleanup paths.

    Catches Exception, not BaseException: a cleanup helper must not swallow
    KeyboardInterrupt or SystemExit and turn an interpreter shutdown into a
    silent continue.
    """
    try:
        _close_handle(handle)
    except Exception:
        pass


def _flush_handle(handle: int) -> None:
    """Issue the durability barrier. Never silently succeeds without one."""
    kernel32, _ = _windows_native()
    if not kernel32.FlushFileBuffers(ctypes.c_void_p(handle)):
        raise _closed()


def _windows_name(value: str) -> str:
    """Reject names NTFS cannot carry as one literal component.

    Handle-relative NT opens would accept a reserved device name and a
    component longer than NTFS allows, because the device mapping and the
    component-length rule both live in the Win32 layer this port bypasses.
    They are refused here anyway: a published artifact tree that any ordinary
    Win32 consumer cannot open afterwards is not a usable tree.
    """
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or value[-1] in {" ", "."}
        or any(character in value for character in "\\/:\0")
        or any(ord(character) < 32 for character in value)
        or value.split(".", 1)[0].upper() in _RESERVED_DEVICE_NAMES
    ):
        raise _closed(LocalIOCodeV1.PATH_INVALID)
    try:
        encoded = value.encode("utf-16-le")
    except UnicodeError:
        raise _closed(LocalIOCodeV1.PATH_INVALID) from None
    # NTFS caps one component at 255 UTF-16 code units, which is len(encoded)
    # halved because every code unit is two bytes. Surrogate pairs count as
    # the two units NTFS counts them as.
    if not encoded or len(encoded) > _MAX_COMPONENT_UTF16_UNITS * 2:
        raise _closed(LocalIOCodeV1.PATH_INVALID)
    return value


def _nt_open_relative(
    parent_handle: int,
    component: str,
    *,
    directory: bool,
    create: bool,
    access: int,
    share: int,
) -> int:
    """Issue one NtCreateFile relative to a live parent handle.

    The single NT opening chokepoint, so every relative open shares one
    status mapping. ``component`` is already validated by the caller; an
    EMPTY string is the canonical NT re-open-by-handle form, which names the
    ``RootDirectory`` object itself rather than a child of it.
    """
    _, ntdll = _windows_native()
    encoded = component.encode("utf-16-le")
    # An empty ObjectName still needs a non-NULL Buffer with a zero Length;
    # this is the exact form measured returning STATUS_SUCCESS on the host.
    buffer = (
        ctypes.create_unicode_buffer(component) if component
        else ctypes.create_unicode_buffer(1)
    )
    unicode_name = _UnicodeString(
        Length=len(encoded),
        MaximumLength=len(encoded) + 2,
        Buffer=ctypes.cast(buffer, ctypes.c_wchar_p),
    )
    attributes = _ObjectAttributes(
        Length=ctypes.sizeof(_ObjectAttributes),
        RootDirectory=ctypes.c_void_p(parent_handle),
        ObjectName=ctypes.pointer(unicode_name),
        Attributes=_OBJ_DONT_REPARSE,
        SecurityDescriptor=None,
        SecurityQualityOfService=None,
    )
    status_block = _IoStatusBlock()
    output = ctypes.c_void_p()
    options = (
        (_FILE_DIRECTORY_FILE if directory else _FILE_NON_DIRECTORY_FILE)
        | _FILE_OPEN_REPARSE_POINT
        | _FILE_SYNCHRONOUS_IO_NONALERT
    )
    status = ntdll.NtCreateFile(
        ctypes.byref(output),
        access,
        ctypes.byref(attributes),
        ctypes.byref(status_block),
        None,
        0,
        share,
        _FILE_CREATE if create else _FILE_OPEN,
        options,
        None,
        0,
    )
    raw = status & 0xFFFFFFFF
    if status < 0:
        if raw == _STATUS_OBJECT_NAME_COLLISION:
            raise _closed(LocalIOCodeV1.DESTINATION_EXISTS)
        if raw in _PATH_INVALID_STATUSES:
            raise _closed(LocalIOCodeV1.PATH_INVALID)
        if raw == _STATUS_SHARING_VIOLATION:
            raise _closed(LocalIOCodeV1.ROOT_IN_USE)
        # Fail closed. Anything not named above -- ACCESS_DENIED,
        # DELETE_PENDING, REPARSE_POINT_ENCOUNTERED, INSUFFICIENT_RESOURCES --
        # is a real failure, never an absence.
        raise _closed(LocalIOCodeV1.IO_FAILED)
    if output.value in {None, _INVALID_HANDLE_VALUE}:
        # STATUS_SUCCESS with no handle is a broken driver contract, not a
        # missing name, so it must not reach stat_at as "absent" either.
        raise _closed(LocalIOCodeV1.IO_FAILED)
    return int(output.value)


def _open_relative(
    parent_handle: int,
    name: str,
    *,
    directory: bool,
    create: bool = False,
    access: int,
    share: int,
) -> int:
    """Open one NAMED component relative to a live parent handle.

    This is the single opening primitive for everything below the anchor.
    ``OBJ_DONT_REPARSE`` plus ``FILE_OPEN_REPARSE_POINT`` mean a redirect is
    never traversed, and ``RootDirectory`` makes the operation relative to the
    retained handle rather than to a re-resolved path. The name is validated
    first, so "." and ".." are refused here exactly as before.
    """
    return _nt_open_relative(
        parent_handle, _windows_name(name),
        directory=directory, create=create, access=access, share=share,
    )


def _reopen_by_handle(parent_handle: int, *, access: int, share: int) -> int:
    """Re-open the directory a handle already names, with a new access pair.

    The canonical NT form is an EMPTY ObjectName with ``RootDirectory`` set.
    Asking for the literal name "." instead is rejected twice over: by
    ``_windows_name``, and by NtCreateFile itself with
    STATUS_OBJECT_NAME_INVALID. ``_windows_name`` keeps refusing "." and ".."
    for ordinary component names; this path simply never supplies a name.

    Used by ``acquire_directory_admission`` to take a second handle on the
    same directory object with the DELETE access that carries the share-mode
    exclusion.
    """
    return _nt_open_relative(
        parent_handle, "", directory=True, create=False,
        access=access, share=share,
    )


def _directory_entries(handle: int, maximum: int) -> tuple[tuple[str, bool, int], ...]:
    """Enumerate one directory by handle as (name, is_reparse_point, file_id).

    The scan itself, with every structural bound and the case-fold collision
    check, but WITHOUT a verdict on redirects: it reports which entries are
    reparse points and lets the caller decide. ``_directory_names`` keeps the
    strict whole-directory rejection; ``_root_component`` needs a decision
    about ONE named entry instead.

    ``file_id`` is the entry's 128-bit FILE_ID_128 decoded the same way
    ``_identity_from_information`` decodes FILE_ID_INFO, so it is directly
    comparable to ``LocalFileIdentityV1.inode``. Carrying it is what lets the
    descent bind the object it OPENED to the object it ENUMERATED and vetted,
    rather than trusting that the name still refers to the same object.
    """
    kernel32, _ = _windows_native()
    entries: list[tuple[str, bool, int]] = []
    seen: set[str] = set()
    first = True
    while True:
        buffer = ctypes.create_string_buffer(64 * 1024)
        info_class = (
            _FILE_ID_EXTD_DIRECTORY_RESTART_INFO_CLASS
            if first else _FILE_ID_EXTD_DIRECTORY_INFO_CLASS
        )
        first = False
        if not kernel32.GetFileInformationByHandleEx(
            ctypes.c_void_p(handle), info_class, buffer, len(buffer)
        ):
            if ctypes.get_last_error() == _ERROR_NO_MORE_FILES:
                break
            raise _closed()
        offset = 0
        while True:
            if offset + _DIRECTORY_RECORD.size > len(buffer):
                raise _closed()
            unpacked = _DIRECTORY_RECORD.unpack_from(buffer, offset)
            next_offset = unpacked[0]
            attributes = unpacked[8]
            name_length = unpacked[9]
            reparse_tag = unpacked[11]
            file_id = unpacked[12]
            name_start = offset + _DIRECTORY_RECORD.size
            name_end = name_start + name_length
            if name_length % 2 or name_end > len(buffer):
                raise _closed()
            try:
                name = ctypes.string_at(
                    ctypes.addressof(buffer) + name_start, name_length
                ).decode("utf-16-le")
            except UnicodeError:
                raise _closed() from None
            if name not in {".", ".."}:
                folded = unicodedata.normalize("NFC", name).casefold()
                if folded in seen:
                    raise _closed(LocalIOCodeV1.ROOT_CHANGED)
                seen.add(folded)
                is_reparse = bool(
                    attributes & _FILE_ATTRIBUTE_REPARSE_POINT or reparse_tag != 0
                )
                entries.append((
                    name, is_reparse,
                    int.from_bytes(file_id, "little", signed=False),
                ))
                if len(entries) > MAX_DIRECTORY_ENTRIES:
                    raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
            if next_offset == 0:
                break
            if (
                next_offset < _DIRECTORY_RECORD.size
                or next_offset % 8
                or offset + next_offset >= len(buffer)
            ):
                raise _closed()
            offset += next_offset
        if len(entries) > maximum:
            break
    return tuple(entries)


def _directory_names(handle: int, maximum: int) -> tuple[str, ...]:
    """Enumerate one directory by handle, rejecting collisions and overflow.

    M-7: the whole-listing reparse veto is GONE. A reparse-point SIBLING
    cannot redirect a name the caller never opens, and vetoing the listing on
    one made every directory containing a junction unlistable -- the C: drive
    root carries the legacy "Documents and Settings" junction, so this
    disabled listing on the most common root on the system.

    ``_directory_entries`` still enforces everything that survives: a
    casefold collision is ROOT_CHANGED, the entry cap is LIMIT_EXCEEDED, and
    an undecodable or malformed record is IO_FAILED.

    The redirect boundary stays at OPEN time, where it belongs and where it
    is three-deep: ``_root_component`` refuses a reparse point on the MATCHED
    entry, every open carries ``OBJ_DONT_REPARSE`` with
    ``FILE_OPEN_REPARSE_POINT``, and ``_query_identity`` refuses one again on
    the handle it opened.
    """
    return tuple(name for name, _, _ in _directory_entries(handle, maximum))


def _require_ntfs(path: Path) -> None:
    """Reject any volume that cannot carry FILE_ID_INFO or a hardlink.

    Mirrors the ``_win_require_ntfs`` pattern in ``security.py``. FAT and exFAT
    support neither the 128-bit file id nor ``FileLinkInformationEx``, so the
    commit proof would be unreproducible there.
    """
    kernel32, _ = _windows_native()
    volume = ctypes.create_unicode_buffer(32_768)
    filesystem = ctypes.create_unicode_buffer(64)
    if not kernel32.GetVolumePathNameW(str(path), volume, len(volume)):
        raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
    if not kernel32.GetVolumeInformationW(
        volume.value, None, 0, None, None, None, filesystem, len(filesystem),
    ) or filesystem.value.upper() != "NTFS":
        raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)


def detect_windows_capability_v1(
    *, platform_name: str | None = None, os_name: str | None = None
) -> LocalFilesystemCapabilityV1:
    """Report whether the Windows retained-handle port can be constructed.

    Signature mirrors ``detect_posix_capability_v1``. This reports AVAILABLE
    only when the process is native Windows, the pointer width is 64-bit, and
    every kernel32 and ntdll entry point the port needs resolves.

    The NTFS check and the ``fsync_directory`` barrier probe are NOT performed
    here, because at construction no path is known: ``publication_composition``
    builds the port with no arguments and only later hands it a root. Both are
    performed per root inside ``retain_directory``, which is the first point at
    which the real target volume exists, and both fail closed with
    ``CAPABILITY_UNAVAILABLE`` there. That is strictly stronger than probing a
    scratch volume at construction, and it preserves the rule that
    ``fsync_directory`` is never a silent no-op.
    """
    platform_value = sys.platform if platform_name is None else platform_name
    os_value = os.name if os_name is None else os_name
    family = "windows" if platform_value.startswith("win") or os_value == "nt" else (
        "posix" if os_value == "posix" else "other"
    )
    available = False
    if family == "windows" and os_value == "nt" and platform_value.startswith("win"):
        available = ctypes.sizeof(ctypes.c_void_p) == 8
        if available:
            try:
                kernel32, ntdll = _windows_native()
            except BaseException:
                available = False
            else:
                available = all(
                    callable(getattr(kernel32, name, None)) for name in (
                        "CloseHandle", "CreateFileW", "FlushFileBuffers",
                        "GetFileInformationByHandleEx", "GetFinalPathNameByHandleW",
                        "GetVolumeInformationW", "GetVolumePathNameW",
                        "ReadFile", "SetFileInformationByHandle", "WriteFile",
                    )
                ) and all(
                    callable(getattr(ntdll, name, None))
                    for name in ("NtCreateFile", "NtSetInformationFile")
                )
    status = CapabilityStatusV1.AVAILABLE if available else CapabilityStatusV1.UNAVAILABLE
    features = _FEATURES if available else ()
    canonical = {"features": list(features), "platform_family": family, "status": status.value}
    return LocalFilesystemCapabilityV1(family, status, features, digest_v1(canonical))


class WindowsRetainedHandlePortV1:
    """Real adapter whose effects remain relative to authenticated live handles.

    Structural counterpart of ``PosixRetainedDirfdPortV1``. The 21 public
    methods below are the ``PosixFilesystemPortV1`` protocol surface; the
    protocol keeps its POSIX name in this closure and renaming it is a recorded
    follow-up.
    """

    def __init__(self) -> None:
        self.capability = detect_windows_capability_v1()
        if self.capability.status is not CapabilityStatusV1.AVAILABLE:
            raise LocalIOErrorV1(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        self._directories: dict[str, tuple[int, RetainedDirectoryV1]] = {}
        self._files: dict[str, tuple[int, OpenFileV1]] = {}
        self._journal_lock = threading.Lock()
        self._admission_process_id = os.getpid()
        self._admission_process_ref = "process-" + secrets.token_hex(16)
        self._admission_leases: dict[str, _LiveDirectoryAdmissionV1] = {}
        self._admission_lock = threading.Lock()

    # -- shared guards ----------------------------------------------------

    def _require_construction_process(self) -> None:
        """Refuse to act from a process other than the constructing one."""
        try:
            current_pid = os.getpid()
        except BaseException:
            raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE) from None
        if current_pid != self._admission_process_id:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)

    @staticmethod
    def _component(value: str) -> str:
        try:
            parts = canonical_relative_components_v1(value)
        except LocalIOErrorV1:
            raise _closed(LocalIOCodeV1.PATH_INVALID) from None
        if len(parts) != 1:
            raise _closed(LocalIOCodeV1.PATH_INVALID)
        return _windows_name(parts[0])

    @staticmethod
    def _same_retained_node(
        left: LocalFileIdentityV1, right: LocalFileIdentityV1
    ) -> bool:
        return (left.device, left.inode, left.mode) == (right.device, right.inode, right.mode)

    def _directory(self, value: RetainedDirectoryV1) -> int:
        """Re-prove a retained directory handle before every use."""
        self._require_construction_process()
        if type(value) is not RetainedDirectoryV1:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        retained = self._directories.get(value.handle_ref)
        if retained is None or retained[1] is not value:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        current = _query_identity(retained[0])
        if not self._same_retained_node(value.identity, current) or not stat.S_ISDIR(current.mode):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        return retained[0]

    def _file(self, value: OpenFileV1) -> int:
        self._require_construction_process()
        if type(value) is not OpenFileV1:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        retained = self._files.get(value.handle_ref)
        if retained is None or retained[1] is not value:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        return retained[0]

    def _retain_directory_handle(self, handle: int) -> RetainedDirectoryV1:
        try:
            identity = _query_identity(handle)
            if not stat.S_ISDIR(identity.mode):
                raise _closed(LocalIOCodeV1.ROOT_INVALID)
            handle_ref = "dir-" + secrets.token_hex(16)
            result = RetainedDirectoryV1(handle_ref, identity)
            self._directories[handle_ref] = (handle, result)
            return result
        except BaseException:
            _close_handle_quietly(handle)
            raise

    def _retain_file_handle(self, handle: int) -> OpenFileV1:
        try:
            identity = _query_identity(handle)
            handle_ref = "file-" + secrets.token_hex(16)
            result = OpenFileV1(handle_ref, identity)
            self._files[handle_ref] = (handle, result)
            return result
        except BaseException:
            _close_handle_quietly(handle)
            # Re-raise as the directory sibling does. Collapsing to IO_FAILED
            # here lost the ROOT_CHANGED that _query_identity raises for a
            # reparse point, so the same physical condition reported two
            # different codes depending on which handle kind found it.
            raise

    def _root_component(self, parent_handle: int, value: str) -> tuple[str, int]:
        """Require the configured spelling to match the on-disk spelling.

        Returns the proven component AND the matched entry's 128-bit file id,
        so the caller can bind the handle it goes on to open to the entry that
        was actually vetted here. Without that binding the descent proves only
        SPELLING and TYPE, and the name could be rebound between this
        enumeration and the open.

        NTFS is case-insensitive, so at most one entry can fold to a given
        value. The check therefore reduces to exact-case agreement, which is
        stricter than the POSIX equivalent, not weaker.

        The redirect check is on the MATCHED entry, not on the directory as a
        whole. A reparse point somewhere else in the parent cannot redirect
        the component being descended into, and vetoing on a sibling made
        every path under the C: drive root unreachable, because that root
        carries the legacy "Documents and Settings" junction. The component
        actually traversed is still refused if it is a reparse point, here and
        again in ``_query_identity`` after it is opened.
        """
        component = canonical_posix_root_component_v1(value)
        entries = _directory_entries(parent_handle, MAX_DIRECTORY_ENTRIES)
        folded = unicodedata.normalize("NFC", component).casefold()
        matches = [
            (name, is_reparse, file_id) for name, is_reparse, file_id in entries
            if unicodedata.normalize("NFC", name).casefold() == folded
        ]
        if [name for name, _, _ in matches] != [component]:
            raise _closed(LocalIOCodeV1.ROOT_CHANGED)
        if matches[0][1]:
            raise _closed(LocalIOCodeV1.ROOT_CHANGED)
        return component, matches[0][2]

    # -- protocol surface -------------------------------------------------

    def retain_directory(self, absolute_path: Path) -> RetainedDirectoryV1:
        """Anchor by path once, then descend handle-relative to the root.

        This is the only method that accepts a full path. It also performs the
        three per-root fail-closed probes the detector cannot do at
        construction, because the factory builds the port with no path: the
        volume must be NTFS, the durability barrier must succeed on the
        retained handle, and FILE_ID_INFO must be retrievable from it. All
        three run on EVERY retained root, not once per process.
        """
        self._require_construction_process()
        kernel32, _ = _windows_native()
        if not isinstance(absolute_path, Path) or not absolute_path.is_absolute():
            raise _closed(LocalIOCodeV1.ROOT_INVALID)
        parts = absolute_path.parts
        if not parts:
            raise _closed(LocalIOCodeV1.ROOT_INVALID)
        _require_ntfs(absolute_path)
        current: int | None = None
        try:
            # Only the RETAINED LEAF takes the write flavours. Every ancestor
            # on the way down is traversed, listed and stat-ed but never
            # written, so it takes _ANCESTOR_DIRECTORY_ACCESS. When the root
            # IS a drive root (a single part), the anchor is itself the leaf
            # and keeps the full mask -- so a non-elevated C:\ as the retained
            # root still fails, which is correct rather than a defect.
            anchor_is_leaf = len(parts) == 1
            anchor = kernel32.CreateFileW(
                parts[0],
                _DIRECTORY_ACCESS if anchor_is_leaf else _ANCESTOR_DIRECTORY_ACCESS,
                _FILE_SHARE_ALL,
                None,
                _OPEN_EXISTING,
                _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
                None,
            )
            if anchor in {None, _INVALID_HANDLE_VALUE}:
                raise _closed(LocalIOCodeV1.ROOT_INVALID)
            current = int(anchor)
            final_index = len(parts) - 1
            for index, component in enumerate(parts[1:], start=1):
                checked, enumerated_id = self._root_component(current, component)
                child = _open_relative(
                    current, checked, directory=True,
                    access=_DIRECTORY_ACCESS if index == final_index
                    else _ANCESTOR_DIRECTORY_ACCESS,
                    share=_FILE_SHARE_ALL,
                )
                opened = _query_identity(child)
                # Bind the OPENED object to the ENUMERATED one. _root_component
                # proved spelling and refused a reparse point on the entry it
                # matched, but the open that follows resolves the NAME again,
                # so without this compare a rebind between the two steps goes
                # unnoticed and rule 1 above ("re-proves identity at every
                # component") would not hold. POSIX closes the same window with
                # its before/opened/after stat triple at posix.py:258-266.
                if not stat.S_ISDIR(opened.mode) or opened.inode != enumerated_id:
                    _close_handle_quietly(child)
                    raise _closed(LocalIOCodeV1.ROOT_CHANGED)
                _close_handle_quietly(current)
                current = child
            retained_handle = current
            current = None
            # Fail-closed durability probe on the real target volume. A port
            # whose barrier does not work must never be usable, because a
            # no-op barrier would leave every shared assertion passing while
            # the crash-safety property was gone.
            try:
                _flush_handle(retained_handle)
            except LocalIOErrorV1:
                _close_handle_quietly(retained_handle)
                raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE) from None
            # Fail-closed FILE_ID_INFO probe on the real target volume. Every
            # retained handle already goes through _query_identity, so this
            # call is the same one; making it explicit here classifies a volume
            # that cannot supply a 128-bit FileId as a capability refusal
            # rather than as a mid-life IO failure. A volume without file ids
            # can report no founded identity, so no mutation may run on it.
            try:
                _query_identity(retained_handle)
            except LocalIOErrorV1 as identity_failure:
                _close_handle_quietly(retained_handle)
                if identity_failure.code is LocalIOCodeV1.IO_FAILED:
                    raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE) from None
                raise
            return self._retain_directory_handle(retained_handle)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.ROOT_INVALID) from None
        finally:
            if current is not None:
                _close_handle_quietly(current)

    def open_directory_at(
        self, directory: RetainedDirectoryV1, component: str
    ) -> RetainedDirectoryV1:
        parent = self._directory(directory)
        name = self._component(component)
        child = _open_relative(
            parent, name, directory=True,
            access=_DIRECTORY_ACCESS, share=_FILE_SHARE_ALL,
        )
        return self._retain_directory_handle(child)

    def close_directory(self, directory: RetainedDirectoryV1) -> None:
        handle = self._directory(directory)
        del self._directories[directory.handle_ref]
        _close_handle(handle)

    def list_names_at(
        self, directory: RetainedDirectoryV1, maximum: int
    ) -> tuple[str, ...]:
        handle = self._directory(directory)
        if type(maximum) is not int or not 0 <= maximum <= MAX_DIRECTORY_ENTRIES + 1:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        return _directory_names(handle, maximum)

    def stat_at(
        self, directory: RetainedDirectoryV1, component: str
    ) -> LocalFileIdentityV1 | None:
        """Identify one named child, or report it absent.

        None means ABSENT and nothing else. Only PATH_INVALID continues the
        probe, and _PATH_INVALID_STATUSES defines that as exactly not-found or
        wrong-type; every other failure raises. This is the POSIX contract at
        posix.py:321-328, where only FileNotFoundError yields None.
        """
        parent = self._directory(directory)
        name = self._component(component)
        for as_directory in (False, True):
            try:
                child = _open_relative(
                    parent, name, directory=as_directory,
                    access=_FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                    share=_FILE_SHARE_ALL,
                )
            except LocalIOErrorV1 as error:
                if error.code is LocalIOCodeV1.PATH_INVALID:
                    continue
                raise
            try:
                return _query_identity(child)
            finally:
                _close_handle_quietly(child)
        # BOTH passes reported PATH_INVALID, and that can only mean absent: a
        # wrong-type verdict is impossible on both passes, because an existing
        # object answers the file pass with FILE_IS_A_DIRECTORY only when it IS
        # a directory (so the directory pass then opens it) and the directory
        # pass with NOT_A_DIRECTORY only when it is NOT (so the file pass
        # already opened it). Never both, so the object cannot exist.
        return None

    def open_read_at(
        self, directory: RetainedDirectoryV1, component: str
    ) -> OpenFileV1:
        parent = self._directory(directory)
        name = self._component(component)
        try:
            child = _open_relative(
                parent, name, directory=False,
                access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                share=_FILE_SHARE_READ_WRITE,
            )
        except LocalIOErrorV1:
            raise _closed(LocalIOCodeV1.SOURCE_INVALID) from None
        return self._retain_file_handle(child)

    def create_exclusive_at(
        self, directory: RetainedDirectoryV1, component: str
    ) -> OpenFileV1:
        parent = self._directory(directory)
        name = self._component(component)
        child = _open_relative(
            parent, name, directory=False, create=True,
            access=(
                _FILE_WRITE_DATA | _FILE_READ_DATA | _FILE_READ_ATTRIBUTES
                | _FILE_WRITE_ATTRIBUTES | _SYNCHRONIZE
            ),
            share=_FILE_SHARE_READ_WRITE,
        )
        return self._retain_file_handle(child)

    def mkdir_at(self, directory: RetainedDirectoryV1, component: str) -> bool:
        """Create one subdirectory. Returns False when it already exists."""
        parent = self._directory(directory)
        name = self._component(component)
        try:
            child = _open_relative(
                parent, name, directory=True, create=True,
                access=_DIRECTORY_ACCESS, share=_FILE_SHARE_ALL,
            )
        except LocalIOErrorV1 as error:
            if error.code is LocalIOCodeV1.DESTINATION_EXISTS:
                return False
            raise
        _close_handle_quietly(child)
        return True

    def read(self, file: OpenFileV1, maximum: int) -> bytes:
        kernel32, _ = _windows_native()
        handle = self._file(file)
        if type(maximum) is not int or not 0 < maximum <= _MAX_CHUNK_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        buffer = ctypes.create_string_buffer(maximum)
        read = ctypes.c_ulong(0)
        if not kernel32.ReadFile(
            ctypes.c_void_p(handle), buffer, maximum, ctypes.byref(read), None
        ):
            raise _closed()
        return bytes(buffer.raw[:int(read.value)])

    def write(self, file: OpenFileV1, payload: bytes) -> int:
        kernel32, _ = _windows_native()
        handle = self._file(file)
        if type(payload) is not bytes or not payload or len(payload) > _MAX_CHUNK_BYTES:
            raise _closed(LocalIOCodeV1.STREAM_INVALID)
        source = ctypes.create_string_buffer(payload, len(payload))
        written = ctypes.c_ulong(0)
        if not kernel32.WriteFile(
            ctypes.c_void_p(handle), source, len(payload),
            ctypes.byref(written), None,
        ):
            raise _closed()
        return int(written.value)

    def stat_file(self, file: OpenFileV1) -> LocalFileIdentityV1:
        return _query_identity(self._file(file))

    def close_file(self, file: OpenFileV1) -> None:
        handle = self._file(file)
        del self._files[file.handle_ref]
        _close_handle(handle)

    def fsync_file(self, file: OpenFileV1) -> None:
        _flush_handle(self._file(file))

    def fsync_directory(self, directory: RetainedDirectoryV1) -> None:
        """Make a namespace mutation durable.

        This issues a real barrier and raises when it fails. It must never
        become a no-op returning success: that would satisfy every shared
        assertion while removing the property the barrier exists to provide.
        """
        _flush_handle(self._directory(directory))

    def link_at(
        self, directory: RetainedDirectoryV1, source: str, destination: str
    ) -> None:
        """Create the second hardlink that IS the commit proof.

        Uses ``NtSetInformationFile`` with ``FileLinkInformationEx``, which
        takes a ``RootDirectory`` handle plus a single component. This is the
        handle-relative analogue of ``os.link(..., dst_dir_fd=)``.
        ``CreateHardLinkW`` is deliberately not used because it resolves a full
        path, which would make the one load-bearing step of the protocol the
        only redirect-vulnerable one.
        """
        _, ntdll = _windows_native()
        parent = self._directory(directory)
        source_name = self._component(source)
        destination_name = self._component(destination)
        opened = _open_relative(
            parent, source_name, directory=False,
            access=_FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            share=_FILE_SHARE_READ_WRITE,
        )
        try:
            encoded = destination_name.encode("utf-16-le")
            # FILE_LINK_INFORMATION_EX on 64-bit: ULONG Flags, 4 bytes of
            # padding, PVOID RootDirectory, ULONG FileNameLength, then the
            # name. Built by hand because ctypes would pad the trailing name
            # field to the structure alignment and shift the name offset.
            header = struct.pack("<IIQI", 0, 0, parent, len(encoded))
            payload = header + encoded
            buffer = ctypes.create_string_buffer(payload, len(payload))
            status_block = _IoStatusBlock()
            status = ntdll.NtSetInformationFile(
                ctypes.c_void_p(opened),
                ctypes.byref(status_block),
                buffer,
                len(payload),
                _FILE_LINK_INFORMATION_EX_CLASS,
            )
            if status < 0:
                if (status & 0xFFFFFFFF) == _STATUS_OBJECT_NAME_COLLISION:
                    raise _closed(LocalIOCodeV1.DESTINATION_EXISTS)
                raise _closed()
        finally:
            _close_handle_quietly(opened)

    def unlink_at(self, directory: RetainedDirectoryV1, component: str) -> None:
        self._unlink_raw(self._directory(directory), self._component(component))

    # -- directory admission ---------------------------------------------

    @staticmethod
    def _admission_node(identity: LocalFileIdentityV1) -> LocalAdmissionRootNodeV1:
        file_type = stat.S_IFMT(identity.mode)
        body = {"device": identity.device, "file_type": file_type,
                "inode": identity.inode,
                "schema": "synaptic-host-admission-root-node/v1"}
        return LocalAdmissionRootNodeV1(
            identity.device, identity.inode, file_type, digest_v1(body)
        )

    @staticmethod
    def _admission_root_key(
        node: LocalAdmissionRootNodeV1,
    ) -> tuple[int, int, int, str]:
        return node.device, node.inode, node.file_type, node.node_digest

    def acquire_directory_admission(
        self, directory: RetainedDirectoryV1
    ) -> RetainedDirectoryAdmissionV1:
        """Take single-writer admission by share-mode exclusion.

        The admission handle asks for DELETE access and shares only read and
        write. A second admission attempt therefore fails with a sharing
        violation, which maps to ROOT_IN_USE exactly as EAGAIN does on POSIX.
        Ordinary directory opens never request DELETE, so they keep working
        while the admission is held. No namespace entry is created, which is
        what keeps artifact_spool.py's startup reclaim off this change list: it
        raises on any spool entry that is not a recognised blob.

        Release on crash is provided by the kernel closing handles at process
        death, so it needs no cleanup code, exactly as flock does on POSIX.
        """
        self._require_construction_process()
        directory_handle = self._directory(directory)
        retained_node = self._admission_node(_query_identity(directory_handle))
        handle: int | None = None
        try:
            try:
                handle = _reopen_by_handle(
                    directory_handle,
                    access=_ADMISSION_ACCESS, share=_FILE_SHARE_READ_WRITE,
                )
            except LocalIOErrorV1 as error:
                if error.code is LocalIOCodeV1.ROOT_IN_USE:
                    raise
                raise _closed(LocalIOCodeV1.IO_FAILED) from None
            if self._admission_node(_query_identity(handle)) != retained_node:
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
            lease_ref = "directory-admission-" + secrets.token_hex(16)
            body = {"lease_ref": lease_ref, "root_node_digest": retained_node.node_digest,
                    "process_id": self._admission_process_id,
                    "process_instance_ref": self._admission_process_ref,
                    "schema": "synaptic-host-retained-directory-admission/v1"}
            lease = RetainedDirectoryAdmissionV1(
                lease_ref, retained_node, self._admission_process_id,
                self._admission_process_ref, digest_v1(body),
            )
            with self._admission_lock:
                if any(
                    value.root_key == self._admission_root_key(retained_node)
                    and value.state in {"ACTIVE", "RELEASING"}
                    for value in self._admission_leases.values()
                ):
                    raise _closed(LocalIOCodeV1.ROOT_IN_USE)
                self._admission_leases[lease_ref] = _LiveDirectoryAdmissionV1(
                    lease, directory, handle, self._admission_root_key(retained_node),
                )
            handle = None
            return lease
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if handle is not None:
                _close_handle_quietly(handle)

    def validate_directory_admission(
        self, directory: RetainedDirectoryV1, lease: RetainedDirectoryAdmissionV1
    ) -> RetainedDirectoryAdmissionV1:
        self._require_construction_process()
        if type(directory) is not RetainedDirectoryV1 or type(lease) is not RetainedDirectoryAdmissionV1:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        with self._admission_lock:
            live = self._admission_leases.get(lease.lease_ref)
            if (
                live is None
                or live.state != "ACTIVE"
                or live.lease is not lease
                or live.directory is not directory
            ):
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
            directory_handle = self._directory(directory)
            if (
                self._admission_node(_query_identity(directory_handle)) != lease.root_node
                or self._admission_node(_query_identity(live.handle)) != lease.root_node
            ):
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        return lease

    def release_directory_admission(
        self, directory: RetainedDirectoryV1, lease: RetainedDirectoryAdmissionV1
    ) -> None:
        self._require_construction_process()
        if type(directory) is not RetainedDirectoryV1 or type(lease) is not RetainedDirectoryAdmissionV1:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        with self._admission_lock:
            live = self._admission_leases.get(lease.lease_ref)
            if (
                live is None
                or live.state != "ACTIVE"
                or live.lease is not lease
                or live.directory is not directory
            ):
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
            self._directory(directory)
            live.state = "RELEASING"
        failed = False
        try:
            _close_handle(live.handle)
        except LocalIOErrorV1:
            failed = True
        finally:
            with self._admission_lock:
                current = self._admission_leases.get(lease.lease_ref)
                if current is live:
                    live.state = "RELEASED_WITH_FAILURE" if failed else "RELEASED"
                    del self._admission_leases[lease.lease_ref]
        if failed:
            raise _closed(LocalIOCodeV1.ADMISSION_RELEASE_FAILED)

    # -- journal ----------------------------------------------------------

    @staticmethod
    def _journal_name(mutation_id: str) -> str:
        checked_sha256(mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        return ".journal-" + mutation_id

    @staticmethod
    def _record_name(record: CreateJournalRecordV1) -> str:
        return f"{record.sequence}-{record.phase.value}.json"

    def _open_journal_dir(
        self, control: RetainedDirectoryV1, mutation_id: str, *, create: bool
    ) -> int | None:
        control_handle = self._directory(control)
        name = self._journal_name(mutation_id)
        if create:
            created = False
            try:
                child = _open_relative(
                    control_handle, name, directory=True, create=True,
                    access=_DIRECTORY_ACCESS, share=_FILE_SHARE_ALL,
                )
            except LocalIOErrorV1 as error:
                if error.code is not LocalIOCodeV1.DESTINATION_EXISTS:
                    raise
            else:
                created = True
                _close_handle_quietly(child)
            if created:
                _flush_handle(control_handle)
        try:
            return _open_relative(
                control_handle, name, directory=True,
                access=_DIRECTORY_ACCESS, share=_FILE_SHARE_ALL,
            )
        except LocalIOErrorV1 as error:
            # Same fail-open shape as stat_at, and closed the same way: None
            # here means the journal directory is ABSENT, and snapshot_journal
            # publishes that as JournalSnapshotStatusV1.ABSENT. Only
            # PATH_INVALID may say so. An unreadable directory raises
            # IO_FAILED and must keep that code rather than be relabelled a
            # journal-shaped problem, so a real I/O fault is never reported as
            # a missing journal.
            if error.code is LocalIOCodeV1.PATH_INVALID:
                return None
            if error.code is LocalIOCodeV1.IO_FAILED:
                raise
            raise _closed(LocalIOCodeV1.JOURNAL_INVALID) from None

    def _read_all(self, handle: int, limit: int) -> bytes:
        kernel32, _ = _windows_native()
        chunks: list[bytes] = []
        total = 0
        while True:
            size = min(4096, limit + 1 - total)
            if size <= 0:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            buffer = ctypes.create_string_buffer(size)
            read = ctypes.c_ulong(0)
            if not kernel32.ReadFile(
                ctypes.c_void_p(handle), buffer, size, ctypes.byref(read), None
            ):
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            count = int(read.value)
            if count == 0:
                break
            chunks.append(bytes(buffer.raw[:count]))
            total += count
            if total > limit:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
        return b"".join(chunks)

    def _read_record_at(self, directory_handle: int, name: str) -> CreateJournalRecordV1:
        """Read one journal record twice and require both reads to agree."""
        opened = _open_relative(
            directory_handle, name, directory=False,
            access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            share=_FILE_SHARE_READ_WRITE,
        )
        replay: int | None = None
        try:
            info = _query_identity(opened)
            if not stat.S_ISREG(info.mode) or info.nlink != 1 or info.size > _MAX_JOURNAL_RECORD_BYTES:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            payload = self._read_all(opened, _MAX_JOURNAL_RECORD_BYTES)
            if _query_identity(opened) != info:
                raise _closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            replay = _open_relative(
                directory_handle, name, directory=False,
                access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                share=_FILE_SHARE_READ_WRITE,
            )
            if _query_identity(replay) != info:
                raise _closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            if self._read_all(replay, _MAX_JOURNAL_RECORD_BYTES) != payload:
                raise _closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            return parse_journal_record_v1(payload)
        finally:
            if replay is not None:
                _close_handle_quietly(replay)
            _close_handle_quietly(opened)

    def _read_journal_handle(
        self, directory_handle: int, maximum: int
    ) -> tuple[tuple[CreateJournalRecordV1, ...], bool]:
        names = list(_directory_names(directory_handle, maximum + 4))
        if len(names) > maximum + 4:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        names.sort()
        private = [name for name in names if re.fullmatch(r"\.private-[0-9a-f]{32}", name)]
        canonical = [name for name in names if name not in private]
        if len(private) > 4 or len(canonical) > maximum or len(names) > maximum + 4:
            raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
        records = tuple(self._read_record_at(directory_handle, name) for name in canonical)
        if canonical != [self._record_name(record) for record in records]:
            raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
        return records, bool(private)

    @staticmethod
    def _publish_result(
        status: JournalPublishStatusV1, record: CreateJournalRecordV1
    ) -> JournalPublishResultV1:
        return JournalPublishResultV1(
            status, record.mutation_id, record.record_digest, record
        )

    def publish_journal(
        self,
        control: RetainedDirectoryV1,
        mutation_id: str,
        expected_previous_digest: str | None,
        record: CreateJournalRecordV1,
    ) -> JournalPublishResultV1:
        """Publish one journal record through the same commit shape as POSIX.

        Exclusive create, write, barrier the file, link, barrier the directory,
        unlink the private name, barrier the directory again, then read back
        and compare.
        """
        self._require_construction_process()
        if type(record) is not CreateJournalRecordV1 or record.mutation_id != mutation_id:
            raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
        with self._journal_lock:
            directory_handle = self._open_journal_dir(control, mutation_id, create=True)
            if directory_handle is None:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            opened: int | None = None
            temporary = ".private-" + secrets.token_hex(16)
            temporary_created = False
            try:
                records, has_private = self._read_journal_handle(directory_handle, 4)
                if has_private:
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                previous = None if not records else records[-1].record_digest
                if previous != expected_previous_digest or len(records) != record.sequence:
                    if record.sequence < len(records) and records[record.sequence] == record:
                        return self._publish_result(
                            JournalPublishStatusV1.EXISTS_IDENTICAL, record
                        )
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                opened = _open_relative(
                    directory_handle, temporary, directory=False, create=True,
                    access=(
                        _FILE_WRITE_DATA | _FILE_READ_DATA | _FILE_READ_ATTRIBUTES
                        | _FILE_WRITE_ATTRIBUTES | _SYNCHRONIZE
                    ),
                    share=_FILE_SHARE_READ_WRITE,
                )
                temporary_created = True
                payload = journal_record_bytes_v1(record)
                kernel32, _ = _windows_native()
                offset = 0
                while offset < len(payload):
                    chunk = payload[offset:]
                    source = ctypes.create_string_buffer(chunk, len(chunk))
                    written = ctypes.c_ulong(0)
                    if not kernel32.WriteFile(
                        ctypes.c_void_p(opened), source, len(chunk),
                        ctypes.byref(written), None,
                    ) or int(written.value) <= 0:
                        raise _closed()
                    offset += int(written.value)
                _flush_handle(opened)
                _close_handle(opened)
                opened = None
                published = True
                try:
                    self._link_raw(directory_handle, temporary, self._record_name(record))
                except LocalIOErrorV1 as error:
                    if error.code is not LocalIOCodeV1.DESTINATION_EXISTS:
                        raise
                    published = False
                _flush_handle(directory_handle)
                self._unlink_raw(directory_handle, temporary)
                temporary_created = False
                _flush_handle(directory_handle)
                canonical = self._read_record_at(directory_handle, self._record_name(record))
                if canonical != record:
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                return self._publish_result(
                    JournalPublishStatusV1.PUBLISHED if published
                    else JournalPublishStatusV1.EXISTS_IDENTICAL,
                    canonical,
                )
            except LocalIOErrorV1:
                raise
            except BaseException:
                raise _closed() from None
            finally:
                if opened is not None:
                    _close_handle_quietly(opened)
                if temporary_created:
                    try:
                        self._unlink_raw(directory_handle, temporary)
                        _flush_handle(directory_handle)
                    except BaseException:
                        pass
                _close_handle_quietly(directory_handle)

    def _link_raw(self, directory_handle: int, source: str, destination: str) -> None:
        """Handle-relative hardlink against a raw directory handle."""
        _, ntdll = _windows_native()
        opened = _open_relative(
            directory_handle, source, directory=False,
            access=_FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            share=_FILE_SHARE_READ_WRITE,
        )
        try:
            encoded = _windows_name(destination).encode("utf-16-le")
            header = struct.pack("<IIQI", 0, 0, directory_handle, len(encoded))
            payload = header + encoded
            buffer = ctypes.create_string_buffer(payload, len(payload))
            status_block = _IoStatusBlock()
            status = ntdll.NtSetInformationFile(
                ctypes.c_void_p(opened),
                ctypes.byref(status_block),
                buffer,
                len(payload),
                _FILE_LINK_INFORMATION_EX_CLASS,
            )
            if status < 0:
                if (status & 0xFFFFFFFF) == _STATUS_OBJECT_NAME_COLLISION:
                    raise _closed(LocalIOCodeV1.DESTINATION_EXISTS)
                raise _closed()
        finally:
            _close_handle_quietly(opened)

    def _unlink_raw(self, directory_handle: int, name: str) -> None:
        """The single disposition chokepoint: delete one name below a handle.

        Every delete this port performs goes through here, and the disposition
        is always issued on a FRESH handle opened for that name. It is never
        issued through an admission handle. The admission handle asks for
        DELETE only as a share-mode exclusion token, and a disposition through
        it would delete the admitted directory itself, so the parent handle is
        refused if it is one.
        """
        kernel32, _ = _windows_native()
        # Snapshot under the lock that guards the mapping. Iterating it live
        # races acquire/release and raises RuntimeError out of unlink_at, which
        # would escape the closed taxonomy rule 5 states. posix.py:376-380
        # keeps a lock-refreshed snapshot for the same reason.
        with self._admission_lock:
            admitted = frozenset(
                live.handle for live in self._admission_leases.values()
            )
        if directory_handle in admitted:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        opened = _open_relative(
            directory_handle, name, directory=False,
            access=_DELETE | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            share=_FILE_SHARE_ALL,
        )
        try:
            disposition = _FileDispositionInfoEx(Flags=_FILE_DISPOSITION_DELETE)
            if not kernel32.SetFileInformationByHandle(
                ctypes.c_void_p(opened),
                _FILE_DISPOSITION_INFO_EX_CLASS,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                raise _closed()
        finally:
            _close_handle_quietly(opened)

    def snapshot_journal(
        self, control: RetainedDirectoryV1, mutation_id: str, maximum: int
    ) -> JournalSnapshotV1:
        self._require_construction_process()
        if type(maximum) is not int or not 0 <= maximum <= 5:
            raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
        directory_handle = self._open_journal_dir(control, mutation_id, create=False)
        if directory_handle is None:
            status = JournalSnapshotStatusV1.ABSENT
            records: tuple[CreateJournalRecordV1, ...] = ()
            return JournalSnapshotV1(
                status,
                mutation_id,
                records,
                digest_v1({
                    "mutation_id": mutation_id, "record_digests": [],
                    "status": status.value,
                }),
            )
        try:
            try:
                records, has_private = self._read_journal_handle(directory_handle, maximum)
            except LocalIOErrorV1 as error:
                # Only a journal-shaped disagreement is a CONFLICT. A real I/O
                # fault keeps IO_FAILED: reporting an unreadable journal as a
                # conflicting one invites a caller to resolve a conflict that
                # was never observed. Absence is not reachable here at all --
                # a missing journal directory returned None above.
                if error.code is LocalIOCodeV1.IO_FAILED:
                    raise
                status = JournalSnapshotStatusV1.CONFLICT
                records = ()
            else:
                # records is non-empty in the else arm, so FOUND is the only
                # verdict it can carry; the ABSENT arm this expression used to
                # end with was unreachable.
                status = (
                    JournalSnapshotStatusV1.INDETERMINATE
                    if has_private or not records
                    else JournalSnapshotStatusV1.FOUND
                )
                if has_private or not records:
                    records = ()
            return JournalSnapshotV1(
                status,
                mutation_id,
                records,
                digest_v1({
                    "mutation_id": mutation_id,
                    "record_digests": [record.record_digest for record in records],
                    "status": status.value,
                }),
            )
        finally:
            _close_handle_quietly(directory_handle)
