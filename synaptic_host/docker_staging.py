"""Run-owned selective staging for the offline Docker SFT worker."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path, PurePosixPath

from synaptic_tuner.api.v1 import ProjectContext, SourceLock, TrainingPlan
from tuner.cloud.runtime_layout import CloudRuntimeLayout, RuntimeMount
from tuner.runtime import (
    CanonicalWorkloadFileLocationV1,
    WorkerBundleMaterializationV1,
    WorkerControlLocationV1,
    build_worker_invocation,
    materialize_worker_bundle,
)

from .docker_execution_state import DockerStageProjectionV1


_CLOSURE_MANIFEST_SOURCE_PATH = "tuner/runtime/manifests/offline-sft-worker-v1.json"
_CLOSURE_SCHEMA = "synaptic-offline-sft-worker-closure/v1"
_MANIFEST_FIELDS = frozenset({
    "schema_version", "closure_ref", "entrypoint", "trainer_entrypoint",
    "owned_module_prefixes", "optional_features", "member_count",
    "payload_bytes", "members", "closure_digest",
})
_MEMBER_FIELDS = frozenset({"path", "git_mode", "size_bytes", "sha256"})
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_ID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_SEMANTIC_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}$")
_MODULE_PREFIX = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,127}$")
_MAX_PROJECT_ARCHIVE_BYTES = 256 * 1024 * 1024
_MAX_PROJECT_EXPANDED_BYTES = 512 * 1024 * 1024
_MAX_PROJECT_ENTRIES = 20_000
_MAX_INVENTORY_FILES = 20_000
_ARTIFACT_DIRECTORY_NAMES = ("artifacts", "cache", "state", "tmp", "tracking")
_EMPTY_ARTIFACT_DIRECTORY_NAMES = ("artifacts", "state", "tmp", "tracking")
# B-10-R2 (review section 3.3): the content-addressed model inventory occupies
# one subtree of `cache`, and the value is already written down twice. The
# engine reads `--model-cache-dir {cache}/model` at
# `synaptic-tuner/tuner/runtime/verification.py:675`, and this Host builds every
# entry under the same prefix at `docker_model_inventory.py:259-262`. Construct
# it here rather than discovering it by scanning the staged tree at runtime:
# that is the B-13 precedent, and a discovered prefix would follow whatever the
# container wrote instead of what preparation projected.
_MODEL_INVENTORY_PREFIX = "model"
_FORBIDDEN_DISPATCH_ENVIRONMENT = frozenset({
    "PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "HF_TOKEN",
})


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(value)).hexdigest()


def _safe_relative(value: str, label: str) -> PurePosixPath:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError(f"{label} is invalid")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{label} is invalid")
    return path


def _unique_pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if type(key) is not str or key in result:
            raise ValueError("duplicate or invalid JSON field")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is prohibited: {value}")


def _is_reparse(info: os.stat_result) -> bool:
    return bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _walk_tree(root: Path, label: str) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    try:
        root_info = root.lstat()
    except OSError:
        raise ValueError(f"{label} is unavailable") from None
    if root.is_symlink() or _is_reparse(root_info) or not stat.S_ISDIR(root_info.st_mode):
        raise ValueError(f"{label} root is redirected or invalid")
    pending = [root]
    directories: list[Path] = []
    files: list[Path] = []
    while pending:
        directory = pending.pop()
        try:
            entries = tuple(os.scandir(directory))
        except OSError:
            raise ValueError(f"{label} is unavailable") from None
        for entry in entries:
            path = Path(entry.path)
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                raise ValueError(f"{label} is unavailable") from None
            if entry.is_symlink() or _is_reparse(info):
                raise ValueError(f"{label} contains a redirect")
            if stat.S_ISDIR(info.st_mode):
                directories.append(path)
                pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                files.append(path)
            else:
                raise ValueError(f"{label} contains a special file")
    order = lambda path: path.relative_to(root).as_posix()
    return tuple(sorted(directories, key=order)), tuple(sorted(files, key=order))


def _walk_regular_files(root: Path, label: str) -> tuple[Path, ...]:
    return _walk_tree(root, label)[1]


def _ensure_direct_parent(root: Path, relative: PurePosixPath) -> Path:
    current = root
    try:
        root_info = current.lstat()
    except OSError:
        raise ValueError("staging destination root is unavailable") from None
    if current.is_symlink() or _is_reparse(root_info) or not stat.S_ISDIR(
        root_info.st_mode
    ):
        raise ValueError("staging destination contains a redirect or special entry")
    for part in relative.parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        info = current.lstat()
        if current.is_symlink() or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise ValueError("staging destination contains a redirect or special entry")
    return current


def _apply_file_mode(path: Path, *, executable: bool, read_only: bool = False) -> None:
    if read_only:
        path.chmod(stat.S_IREAD if os.name == "nt" else 0o444)
    else:
        path.chmod(0o755 if executable else 0o644)


def _verify_file_mode(
    info: os.stat_result, *, executable: bool, read_only: bool = False
) -> bool:
    if os.name == "nt":
        return True
    expected = 0o444 if read_only else 0o755 if executable else 0o644
    return stat.S_IMODE(info.st_mode) == expected


def _identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns,
    )


_FILE_ATTRIBUTE_READONLY = 0x00000001
_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_LIST_DIRECTORY = 0x00000001
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_WRITE_ATTRIBUTES = 0x00000100
_DELETE = 0x00010000
_SYNCHRONIZE = 0x00100000
_FILE_SHARE_ALL = 0x00000007
_FILE_SHARE_READ_WRITE = 0x00000003
_OPEN_EXISTING = 3
_FILE_OPEN = 1
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
_ERROR_NO_MORE_FILES = 18
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_DIRECTORY_RECORD = struct.Struct("<IIqqqqqqIIII16s")


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


class _FileTime(ctypes.Structure):
    _fields_ = (("Low", ctypes.c_ulong), ("High", ctypes.c_ulong))


class _ByHandleFileInformation(ctypes.Structure):
    _fields_ = (
        ("FileAttributes", ctypes.c_ulong),
        ("CreationTime", _FileTime),
        ("LastAccessTime", _FileTime),
        ("LastWriteTime", _FileTime),
        ("VolumeSerialNumber", ctypes.c_ulong),
        ("FileSizeHigh", ctypes.c_ulong),
        ("FileSizeLow", ctypes.c_ulong),
        ("NumberOfLinks", ctypes.c_ulong),
        ("FileIndexHigh", ctypes.c_ulong),
        ("FileIndexLow", ctypes.c_ulong),
    )


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


@dataclass(frozen=True, slots=True)
class _WindowsHandleMetadataV1:
    identity: tuple[int, bytes]
    is_directory: bool
    attributes: int
    size: int
    link_count: int


@dataclass(frozen=True, slots=True)
class _WindowsCleanupEntryV1:
    handle: int
    depth: int
    location: str
    metadata: _WindowsHandleMetadataV1


@dataclass(slots=True)
class _WindowsStageCleanupV1:
    parent_handle: int
    temporary_handle: int
    parent_identity: tuple[int, bytes]
    temporary_identity: tuple[int, bytes]
    parent_location: str
    temporary_location: str
    temporary_name: str
    child_handles: dict[int, int] = field(default_factory=dict, repr=False)
    cleanup_active: bool = False
    released: bool = False


_WINDOWS_NATIVE: tuple[object, object] | None = None


def _windows_native() -> tuple[object, object]:
    global _WINDOWS_NATIVE
    if os.name != "nt":
        raise ValueError("Windows staging cleanup is unavailable")
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
        kernel32.GetFileInformationByHandle.argtypes = (
            ctypes.c_void_p, ctypes.POINTER(_ByHandleFileInformation),
        )
        kernel32.GetFileInformationByHandle.restype = ctypes.c_int
        kernel32.GetFileInformationByHandleEx.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong,
        )
        kernel32.GetFileInformationByHandleEx.restype = ctypes.c_int
        kernel32.GetFinalPathNameByHandleW.argtypes = (
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
        )
        kernel32.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        kernel32.SetFileInformationByHandle.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong,
        )
        kernel32.SetFileInformationByHandle.restype = ctypes.c_int
        ntdll.NtCreateFile.argtypes = (
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong,
            ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatusBlock),
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
        )
        ntdll.NtCreateFile.restype = ctypes.c_long
        _WINDOWS_NATIVE = kernel32, ntdll
    return _WINDOWS_NATIVE


def _windows_component(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or value[-1] in {" ", "."}
        or any(character in value for character in "\\/:\0")
        or any(ord(character) < 32 for character in value)
    ):
        raise ValueError("Windows staging entry name is not canonical")
    try:
        encoded = value.encode("utf-16-le")
    except UnicodeError:
        raise ValueError("Windows staging entry name is not canonical") from None
    if not encoded or len(encoded) > 65_534:
        raise ValueError("Windows staging entry name is not canonical")
    return value


def _windows_close_raw(handle: int) -> None:
    kernel32, _ = _windows_native()
    if not kernel32.CloseHandle(ctypes.c_void_p(handle)):
        raise ValueError("Windows staging handle release failed")


def _windows_query_metadata(handle: int) -> _WindowsHandleMetadataV1:
    kernel32, _ = _windows_native()
    information = _ByHandleFileInformation()
    file_id = _FileIdInfo()
    standard = _FileStandardInfo()
    if not kernel32.GetFileInformationByHandle(
        ctypes.c_void_p(handle), ctypes.byref(information)
    ) or not kernel32.GetFileInformationByHandleEx(
        ctypes.c_void_p(handle), _FILE_ID_INFO_CLASS,
        ctypes.byref(file_id), ctypes.sizeof(file_id),
    ) or not kernel32.GetFileInformationByHandleEx(
        ctypes.c_void_p(handle), _FILE_STANDARD_INFO_CLASS,
        ctypes.byref(standard), ctypes.sizeof(standard),
    ):
        raise ValueError("Windows staging handle metadata is unavailable")
    attributes = int(information.FileAttributes)
    if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("Windows staging handle is a reparse point")
    return _WindowsHandleMetadataV1(
        identity=(int(file_id.VolumeSerialNumber), bytes(file_id.FileId)),
        is_directory=bool(standard.Directory),
        attributes=attributes,
        size=int(standard.EndOfFile),
        link_count=int(standard.NumberOfLinks),
    )


def _windows_handle_location(handle: int) -> str:
    kernel32, _ = _windows_native()
    buffer = ctypes.create_unicode_buffer(32_768)
    length = kernel32.GetFinalPathNameByHandleW(
        ctypes.c_void_p(handle), buffer, len(buffer), 0
    )
    if length == 0 or length >= len(buffer):
        raise ValueError("Windows staging handle location is unavailable")
    location = buffer.value
    if not location.startswith("\\\\?\\") or location.endswith("\\"):
        raise ValueError("Windows staging handle location is not canonical")
    return location


def _windows_open_parent(
    path: Path | str, *, cleanup: bool = False,
) -> int:
    kernel32, _ = _windows_native()
    desired_access = _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE
    if cleanup:
        desired_access |= _FILE_WRITE_ATTRIBUTES | _DELETE
    handle = kernel32.CreateFileW(
        str(path),
        desired_access,
        _FILE_SHARE_READ_WRITE if cleanup else _FILE_SHARE_ALL,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle in {None, _INVALID_HANDLE_VALUE}:
        raise ValueError("Windows staging parent handle is unavailable")
    return int(handle)


def _windows_open_relative(
    parent_handle: int,
    name: str,
    is_directory: bool,
    *,
    cleanup: bool = False,
) -> int:
    _, ntdll = _windows_native()
    component = _windows_component(name)
    encoded = component.encode("utf-16-le")
    buffer = ctypes.create_unicode_buffer(component)
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
    desired_access = _FILE_READ_ATTRIBUTES | _SYNCHRONIZE
    if cleanup:
        desired_access |= _FILE_WRITE_ATTRIBUTES | _DELETE
    if is_directory:
        desired_access |= _FILE_LIST_DIRECTORY
    options = (
        (_FILE_DIRECTORY_FILE if is_directory else _FILE_NON_DIRECTORY_FILE)
        | _FILE_OPEN_REPARSE_POINT
        | _FILE_SYNCHRONOUS_IO_NONALERT
    )
    status = ntdll.NtCreateFile(
        ctypes.byref(output),
        desired_access,
        ctypes.byref(attributes),
        ctypes.byref(status_block),
        None,
        0,
        _FILE_SHARE_READ_WRITE if cleanup else _FILE_SHARE_ALL,
        _FILE_OPEN,
        options,
        None,
        0,
    )
    if status < 0 or output.value in {None, _INVALID_HANDLE_VALUE}:
        raise ValueError("Windows staging child handle is unavailable")
    return int(output.value)


def _capture_windows_stage_cleanup(
    parent: Path, temporary: Path,
) -> _WindowsStageCleanupV1:
    parent = Path(parent)
    temporary = Path(temporary)
    if (
        not parent.is_absolute()
        or not temporary.is_absolute()
        or temporary.parent != parent
        or not temporary.name.startswith("stage-")
        or len(temporary.name) == len("stage-")
    ):
        raise ValueError("Windows staging temporary is not a direct stage child")
    parent_handle = _windows_open_parent(parent)
    temporary_handle = 0
    try:
        parent_metadata = _windows_query_metadata(parent_handle)
        if not parent_metadata.is_directory:
            raise ValueError("Windows staging parent is not a directory")
        temporary_handle = _windows_open_relative(
            parent_handle, temporary.name, True
        )
        temporary_metadata = _windows_query_metadata(temporary_handle)
        if not temporary_metadata.is_directory:
            raise ValueError("Windows staging temporary is not a directory")
        parent_location = _windows_handle_location(parent_handle)
        temporary_location = _windows_handle_location(temporary_handle)
        if temporary_location != parent_location + "\\" + temporary.name:
            raise ValueError("Windows staging temporary location is invalid")
        return _WindowsStageCleanupV1(
            parent_handle=parent_handle,
            temporary_handle=temporary_handle,
            parent_identity=parent_metadata.identity,
            temporary_identity=temporary_metadata.identity,
            parent_location=parent_location,
            temporary_location=temporary_location,
            temporary_name=temporary.name,
        )
    except BaseException:
        if temporary_handle:
            _windows_close_raw(temporary_handle)
        _windows_close_raw(parent_handle)
        raise


def _windows_directory_records(handle: int) -> tuple[tuple[str, int, int, bytes], ...]:
    kernel32, _ = _windows_native()
    records: list[tuple[str, int, int, bytes]] = []
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
            raise ValueError("Windows staging directory enumeration failed")
        offset = 0
        while True:
            if offset + _DIRECTORY_RECORD.size > len(buffer):
                raise ValueError("Windows staging directory record is malformed")
            unpacked = _DIRECTORY_RECORD.unpack_from(buffer, offset)
            next_offset = unpacked[0]
            end_of_file = unpacked[6]
            attributes = unpacked[8]
            name_length = unpacked[9]
            reparse_tag = unpacked[11]
            file_id = unpacked[12]
            name_start = offset + _DIRECTORY_RECORD.size
            name_end = name_start + name_length
            if name_length % 2 or name_end > len(buffer):
                raise ValueError("Windows staging directory record is malformed")
            try:
                name = ctypes.string_at(
                    ctypes.addressof(buffer) + name_start, name_length
                ).decode("utf-16-le")
            except UnicodeError:
                raise ValueError(
                    "Windows staging directory record name is malformed"
                ) from None
            if name not in {".", ".."}:
                canonical = _windows_component(name)
                folded = canonical.casefold()
                if folded in seen:
                    raise ValueError("Windows staging directory is ambiguous")
                seen.add(folded)
                if (
                    attributes & _FILE_ATTRIBUTE_REPARSE_POINT
                    or reparse_tag != 0
                ):
                    raise ValueError(
                        "Windows staging temporary contains a reparse point"
                    )
                records.append(
                    (canonical, int(attributes), int(end_of_file), bytes(file_id))
                )
            if next_offset == 0:
                break
            if (
                next_offset < _DIRECTORY_RECORD.size
                or next_offset % 8
                or offset + next_offset >= len(buffer)
            ):
                raise ValueError("Windows staging directory record is malformed")
            offset += next_offset
    return tuple(records)


def _windows_acquire_cleanup_authority(cleanup: _WindowsStageCleanupV1) -> None:
    if cleanup.released or cleanup.cleanup_active:
        raise ValueError("Windows staging cleanup transition is invalid")
    cleanup_parent = _windows_open_parent(cleanup.parent_location, cleanup=True)
    cleanup_temporary = 0
    try:
        cleanup_temporary = _windows_open_relative(
            cleanup_parent, cleanup.temporary_name, True, cleanup=True
        )
        parent_metadata = _windows_query_metadata(cleanup_parent)
        temporary_metadata = _windows_query_metadata(cleanup_temporary)
        if (
            parent_metadata.identity != cleanup.parent_identity
            or not parent_metadata.is_directory
            or temporary_metadata.identity != cleanup.temporary_identity
            or not temporary_metadata.is_directory
            or _windows_handle_location(cleanup_parent) != cleanup.parent_location
            or _windows_handle_location(cleanup_temporary)
            != cleanup.temporary_location
        ):
            raise ValueError("Windows staging cleanup transition changed authority")
    except BaseException:
        if cleanup_temporary:
            _windows_close_raw(cleanup_temporary)
        _windows_close_raw(cleanup_parent)
        raise
    promotion_temporary = cleanup.temporary_handle
    promotion_parent = cleanup.parent_handle
    cleanup.parent_handle = cleanup_parent
    cleanup.temporary_handle = cleanup_temporary
    cleanup.cleanup_active = True
    failure: ValueError | None = None
    for handle in (promotion_temporary, promotion_parent):
        try:
            _windows_close_raw(handle)
        except ValueError as error:
            failure = failure or error
    if failure is not None:
        raise failure


def _windows_cleanup_inventory(
    cleanup: _WindowsStageCleanupV1,
) -> tuple[_WindowsCleanupEntryV1, ...]:
    if cleanup.released:
        raise ValueError("Windows staging cleanup authority was released")
    if not cleanup.cleanup_active:
        _windows_acquire_cleanup_authority(cleanup)
    parent_metadata = _windows_query_metadata(cleanup.parent_handle)
    temporary_metadata = _windows_query_metadata(cleanup.temporary_handle)
    if (
        parent_metadata.identity != cleanup.parent_identity
        or not parent_metadata.is_directory
        or temporary_metadata.identity != cleanup.temporary_identity
        or not temporary_metadata.is_directory
    ):
        raise ValueError("Windows staging cleanup authority changed")
    entries = [_WindowsCleanupEntryV1(
        cleanup.temporary_handle,
        0,
        cleanup.temporary_location,
        temporary_metadata,
    )]
    pending = [(cleanup.temporary_handle, 0, cleanup.temporary_location)]
    while pending:
        directory_handle, depth, directory_location = pending.pop()
        for name, attributes, size, file_id in _windows_directory_records(
            directory_handle
        ):
            is_directory = bool(attributes & _FILE_ATTRIBUTE_DIRECTORY)
            handle = _windows_open_relative(
                directory_handle, name, is_directory, cleanup=True
            )
            try:
                metadata = _windows_query_metadata(handle)
                location = directory_location + "\\" + name
                if metadata.identity[1] != file_id:
                    raise ValueError("Windows staging entry identity changed")
                if metadata.is_directory != is_directory:
                    raise ValueError("Windows staging entry type changed")
                if metadata.attributes != attributes:
                    raise ValueError("Windows staging entry attributes changed")
                if not is_directory and metadata.size != size:
                    raise ValueError("Windows staging file size changed")
                if _windows_handle_location(handle) != location:
                    raise ValueError("Windows staging entry location changed")
                cleanup.child_handles[handle] = depth + 1
            except BaseException:
                _windows_close_raw(handle)
                raise
            entry = _WindowsCleanupEntryV1(
                handle, depth + 1, location, metadata
            )
            entries.append(entry)
            if is_directory:
                pending.append((handle, depth + 1, location))
    entries.sort(key=lambda entry: entry.depth, reverse=True)
    return tuple(entries)


def _windows_basic_info(handle: int) -> _FileBasicInfo:
    kernel32, _ = _windows_native()
    information = _FileBasicInfo()
    if not kernel32.GetFileInformationByHandleEx(
        ctypes.c_void_p(handle), _FILE_BASIC_INFO_CLASS,
        ctypes.byref(information), ctypes.sizeof(information),
    ):
        raise ValueError("Windows staging basic metadata is unavailable")
    return information


def _windows_clear_readonly(
    entry: _WindowsCleanupEntryV1,
) -> _WindowsHandleMetadataV1:
    kernel32, _ = _windows_native()
    current = entry.metadata
    if current.is_directory or not current.attributes & _FILE_ATTRIBUTE_READONLY:
        return current
    basic = _windows_basic_info(entry.handle)
    if int(basic.FileAttributes) != current.attributes:
        raise ValueError("Windows staging file attributes changed before cleanup")
    attributes = current.attributes & ~_FILE_ATTRIBUTE_READONLY
    if attributes == 0 or attributes == _FILE_ATTRIBUTE_NORMAL:
        raise ValueError("Windows staging readonly attributes are unsupported")
    updated = _FileBasicInfo(
        CreationTime=basic.CreationTime,
        LastAccessTime=basic.LastAccessTime,
        LastWriteTime=basic.LastWriteTime,
        ChangeTime=basic.ChangeTime,
        FileAttributes=attributes,
    )
    if not kernel32.SetFileInformationByHandle(
        ctypes.c_void_p(entry.handle), _FILE_BASIC_INFO_CLASS,
        ctypes.byref(updated), ctypes.sizeof(updated),
    ):
        raise ValueError("Windows staging readonly attribute clear failed")
    observed = _windows_query_metadata(entry.handle)
    expected = _WindowsHandleMetadataV1(
        identity=current.identity,
        is_directory=False,
        attributes=attributes,
        size=current.size,
        link_count=current.link_count,
    )
    if observed != expected:
        raise ValueError("Windows staging file changed during readonly clear")
    return expected


def _windows_close_owned(
    cleanup: _WindowsStageCleanupV1, handle: int,
) -> None:
    _windows_close_raw(handle)
    cleanup.child_handles.pop(handle, None)
    if cleanup.temporary_handle == handle:
        cleanup.temporary_handle = 0


def _windows_prove_entry(
    entry: _WindowsCleanupEntryV1,
    metadata: _WindowsHandleMetadataV1 | None = None,
) -> None:
    if (
        _windows_query_metadata(entry.handle) != (metadata or entry.metadata)
        or _windows_handle_location(entry.handle) != entry.location
    ):
        raise ValueError("Windows staging handle location or identity changed")


def _windows_validate_inventory(
    entries: tuple[_WindowsCleanupEntryV1, ...],
) -> None:
    for entry in entries:
        _windows_prove_entry(entry)


def _windows_delete_inventory(
    cleanup: _WindowsStageCleanupV1,
    entries: tuple[_WindowsCleanupEntryV1, ...],
) -> None:
    kernel32, _ = _windows_native()
    _windows_validate_inventory(entries)
    for entry in entries:
        _windows_prove_entry(entry)
        admitted = _windows_clear_readonly(entry)
        _windows_prove_entry(entry, admitted)
        disposition = _FileDispositionInfoEx(Flags=_FILE_DISPOSITION_DELETE)
        if not kernel32.SetFileInformationByHandle(
            ctypes.c_void_p(entry.handle),
            _FILE_DISPOSITION_INFO_EX_CLASS,
            ctypes.byref(disposition),
            ctypes.sizeof(disposition),
        ):
            raise ValueError("Windows staging handle disposition failed")
        _windows_close_owned(cleanup, entry.handle)


def _release_windows_stage(cleanup: _WindowsStageCleanupV1) -> None:
    if cleanup.released:
        return
    failure: ValueError | None = None
    handles = tuple(
        handle for handle, _depth in sorted(
            cleanup.child_handles.items(), key=lambda item: item[1], reverse=True
        )
    )
    if cleanup.temporary_handle:
        handles += (cleanup.temporary_handle,)
    if cleanup.parent_handle:
        handles += (cleanup.parent_handle,)
    cleanup.child_handles.clear()
    cleanup.temporary_handle = 0
    cleanup.parent_handle = 0
    cleanup.released = True
    for handle in handles:
        try:
            _windows_close_raw(handle)
        except ValueError as error:
            failure = failure or error
    if failure is not None:
        raise failure


def _cleanup_windows_stage(cleanup: _WindowsStageCleanupV1) -> None:
    try:
        entries = _windows_cleanup_inventory(cleanup)
        _windows_delete_inventory(cleanup, entries)
    finally:
        _release_windows_stage(cleanup)


def _cleanup_unpromoted_stage(
    temporary: Path, windows_cleanup: _WindowsStageCleanupV1 | None,
) -> None:
    if windows_cleanup is None:
        shutil.rmtree(temporary)
        return
    _cleanup_windows_stage(windows_cleanup)


def _read_direct_regular(path: Path, label: str) -> tuple[bytes, os.stat_result]:
    try:
        before = path.lstat()
        if path.is_symlink() or _is_reparse(before) or not stat.S_ISREG(
            before.st_mode
        ):
            raise ValueError
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        after = path.lstat()
    except (OSError, ValueError):
        raise ValueError(f"{label} is redirected, special, or unavailable") from None
    if (
        not stat.S_ISREG(opened.st_mode)
        or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        or _identity(before) != _identity(after)
    ):
        raise ValueError(f"{label} changed during its exact read")
    payload = b"".join(chunks)
    if len(payload) != opened.st_size:
        raise ValueError(f"{label} changed during its exact read")
    return payload, after


def _write_new_regular(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            view = memoryview(payload)
            written = 0
            while written < len(view):
                count = os.write(descriptor, view[written:])
                if count <= 0:
                    raise OSError
                written += count
        finally:
            os.close(descriptor)
    except OSError:
        raise ValueError("staging destination changed during materialization") from None
    _apply_file_mode(path, executable=False)


def _mode_projection(info: os.stat_result) -> str:
    if os.name == "nt":
        return "windows-regular"
    return f"posix-{stat.S_IMODE(info.st_mode):04o}"


@dataclass(frozen=True, slots=True)
class _ClosureMemberV1:
    path: str
    git_mode: str
    size_bytes: int
    sha256: str
    payload: bytes = field(repr=False, compare=False)

    def projection(self) -> dict[str, object]:
        return {
            "git_mode": self.git_mode,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class _LockedClosureV1:
    manifest_bytes: bytes
    manifest_sha256: str
    closure_digest: str
    members: tuple[_ClosureMemberV1, ...]
    payload_bytes: int
    closure_ref: str
    entrypoint: str
    trainer_entrypoint: str
    owned_module_prefixes: tuple[str, ...]
    optional_features: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DockerModelInventoryEntryV1:
    relative_path: str
    source_path: Path
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        _safe_relative(self.relative_path, "model inventory relative_path")
        source = Path(self.source_path)
        try:
            info = source.lstat()
            resolved = source.resolve(strict=True)
        except OSError:
            raise ValueError("model inventory source is unavailable") from None
        if (
            source.is_symlink()
            or bool(
                getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )
            or not stat.S_ISREG(info.st_mode)
            or resolved != source.absolute()
        ):
            raise ValueError("model inventory source must be a direct regular file")
        if type(self.byte_count) is not int or self.byte_count < 0:
            raise ValueError("model inventory byte_count is invalid")
        if type(self.sha256) is not str or _DIGEST.fullmatch(self.sha256) is None:
            raise ValueError("model inventory sha256 is invalid")

    def projection(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class DockerStagingResultV1:
    projection: DockerStageProjectionV1
    source_root: Path
    artifact_root: Path
    worker_bundle: WorkerBundleMaterializationV1

    def __post_init__(self) -> None:
        if (
            type(self.projection) is not DockerStageProjectionV1
            or type(self.worker_bundle) is not WorkerBundleMaterializationV1
        ):
            raise TypeError("staging result contains a noncanonical value")
        if any(
            not Path(value).is_absolute()
            for value in (self.source_root, self.artifact_root)
        ):
            raise ValueError("staging roots must be absolute")


def _git_environment() -> dict[str, str]:
    environment = {
        key: os.environ[key]
        for key in (
            "PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP",
            "TMP", "LANG", "LC_ALL",
        )
        if key in os.environ
    }
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return environment


def _commit(value: str) -> str:
    if type(value) is not str or _OBJECT_ID.fullmatch(value) is None:
        raise ValueError("source commit is invalid")
    return value


def _git(repository: Path, arguments: tuple[str, ...], *, timeout: int = 60) -> bytes:
    try:
        completed = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True, capture_output=True, timeout=timeout,
            env=_git_environment(),
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("exact locked Git object is unavailable") from None
    return completed.stdout


def _git_blob_metadata(
    repository: Path, commit: str, path: str,
) -> tuple[str, str, int]:
    relative = _safe_relative(path, "locked Git path").as_posix()
    raw = _git(
        repository,
        ("ls-tree", "-z", "--full-tree", _commit(commit), "--", relative),
    )
    records = tuple(item for item in raw.split(b"\0") if item)
    if len(records) != 1 or b"\t" not in records[0]:
        raise ValueError("locked Git path does not name one exact blob")
    metadata, encoded_path = records[0].split(b"\t", 1)
    try:
        mode, object_type, object_id = metadata.decode("ascii").split(" ")
        observed_path = encoded_path.decode("utf-8")
    except (UnicodeError, ValueError):
        raise ValueError("locked Git blob metadata is invalid") from None
    if (
        observed_path != relative
        or object_type != "blob"
        or mode not in {"100644", "100755"}
        or _OBJECT_ID.fullmatch(object_id) is None
    ):
        raise ValueError("locked Git path is not an admitted regular blob")
    raw_size = _git(repository, ("cat-file", "-s", object_id))
    try:
        size = int(raw_size.decode("ascii").strip())
    except (UnicodeError, ValueError):
        raise ValueError("locked Git blob size is invalid") from None
    if size < 0 or str(size).encode("ascii") != raw_size.strip():
        raise ValueError("locked Git blob size is invalid")
    return mode, object_id, size


def _git_blob(
    repository: Path, object_id: str, *, expected_size: int,
) -> bytes:
    payload = _git(repository, ("cat-file", "blob", object_id))
    if len(payload) != expected_size:
        raise ValueError("locked Git blob differs from its exact size")
    return payload


def _git_selected_blobs(
    repository: Path,
    commit: str,
    paths: tuple[str, ...],
) -> dict[str, tuple[str, bytes]]:
    raw = _git(
        repository,
        ("archive", "--format=tar", _commit(commit), "--", *paths),
        timeout=120,
    )
    try:
        archive = tarfile.open(fileobj=BytesIO(raw), mode="r:")
    except tarfile.TarError:
        raise ValueError("locked worker source closure is unavailable") from None
    selected: dict[str, tuple[str, bytes]] = {}
    with archive:
        for member in archive:
            relative = _safe_relative(
                member.name.rstrip("/"), "locked worker archive member"
            ).as_posix()
            if member.isdir():
                continue
            if not member.isreg() or relative in selected:
                raise ValueError("locked worker archive contains an invalid member")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError("locked worker archive member is unavailable")
            payload = handle.read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError("locked worker archive member is truncated")
            mode = "100755" if member.mode & 0o111 else "100644"
            selected[relative] = (mode, payload)
    if set(selected) != set(paths):
        raise ValueError("locked worker archive contains missing or extra files")
    return selected


def _load_locked_closure(repository: Path, commit: str) -> _LockedClosureV1:
    manifest_mode, manifest_object, manifest_size = _git_blob_metadata(
        repository, commit, _CLOSURE_MANIFEST_SOURCE_PATH
    )
    if manifest_mode != "100644" or manifest_size <= 0:
        raise ValueError("worker closure manifest metadata is invalid")
    manifest_bytes = _git_blob(
        repository, manifest_object, expected_size=manifest_size
    )
    try:
        document = json.loads(
            manifest_bytes.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError):
        raise ValueError("worker closure manifest is not strict JSON") from None
    if type(document) is not dict or manifest_bytes != _canonical(document) + b"\n":
        raise ValueError("worker closure manifest is not canonical JSON")
    if frozenset(document) != _MANIFEST_FIELDS:
        raise ValueError("worker closure manifest fields are malformed")
    closure_ref = document["closure_ref"]
    entrypoint = _safe_relative(
        document["entrypoint"], "worker closure entrypoint"
    ).as_posix()
    trainer_entrypoint = _safe_relative(
        document["trainer_entrypoint"], "worker trainer entrypoint"
    ).as_posix()
    raw_prefixes = document["owned_module_prefixes"]
    raw_features = document["optional_features"]
    if (
        document["schema_version"] != _CLOSURE_SCHEMA
        or type(closure_ref) is not str
        or _SEMANTIC_REF.fullmatch(closure_ref) is None
        or type(raw_prefixes) is not list
        or not raw_prefixes
        or any(
            type(value) is not str
            or _MODULE_PREFIX.fullmatch(value) is None
            for value in raw_prefixes
        )
        or len(set(raw_prefixes)) != len(raw_prefixes)
        or type(raw_features) is not list
        or any(
            type(value) is not str
            or _SEMANTIC_REF.fullmatch(value) is None
            for value in raw_features
        )
        or len(set(raw_features)) != len(raw_features)
    ):
        raise ValueError("worker closure semantic fields are malformed")
    recorded_digest = document["closure_digest"]
    digest_document = dict(document)
    digest_document.pop("closure_digest")
    if (
        type(recorded_digest) is not str
        or _DIGEST.fullmatch(recorded_digest) is None
        or hashlib.sha256(_canonical(digest_document)).hexdigest() != recorded_digest
    ):
        raise ValueError("worker closure digest is invalid")
    raw_members = document["members"]
    if type(raw_members) is not list or not raw_members:
        raise ValueError("worker closure member count is invalid")
    declared: list[_ClosureMemberV1] = []
    for raw in raw_members:
        if type(raw) is not dict or frozenset(raw) != _MEMBER_FIELDS:
            raise ValueError("worker closure member is malformed")
        path = _safe_relative(raw["path"], "worker closure member").as_posix()
        mode = raw["git_mode"]
        size = raw["size_bytes"]
        sha256 = raw["sha256"]
        if (
            mode not in {"100644", "100755"}
            or type(size) is not int
            or size < 0
            or type(sha256) is not str
            or _DIGEST.fullmatch(sha256) is None
        ):
            raise ValueError("worker closure member metadata is invalid")
        declared.append(_ClosureMemberV1(path, mode, size, sha256, b""))
    paths = tuple(member.path for member in declared)
    if (
        paths != tuple(sorted(paths))
        or len(paths) != len(set(paths))
        or not {entrypoint, trainer_entrypoint}.issubset(set(paths))
        or type(document["member_count"]) is not int
        or document["member_count"] != len(declared)
        or type(document["payload_bytes"]) is not int
        or document["payload_bytes"] != sum(item.size_bytes for item in declared)
        or document["payload_bytes"] <= 0
    ):
        raise ValueError("worker closure totals or ordering are invalid")
    payloads = _git_selected_blobs(repository, commit, paths)
    observed: list[_ClosureMemberV1] = []
    for member in declared:
        mode, payload = payloads[member.path]
        size = len(payload)
        sha256 = hashlib.sha256(payload).hexdigest()
        if (
            mode != member.git_mode
            or size != member.size_bytes
            or sha256 != member.sha256
        ):
            raise ValueError("locked worker member differs from its declaration")
        observed.append(_ClosureMemberV1(member.path, mode, size, sha256, payload))
    recomputed = dict(document)
    recomputed["members"] = [item.projection() for item in observed]
    recomputed["member_count"] = len(observed)
    recomputed["payload_bytes"] = sum(item.size_bytes for item in observed)
    recomputed_digest_document = dict(recomputed)
    recomputed_digest_document.pop("closure_digest")
    recomputed_digest = hashlib.sha256(
        _canonical(recomputed_digest_document)
    ).hexdigest()
    if recomputed_digest != recorded_digest:
        raise ValueError("locked worker source closure digest is invalid")
    return _LockedClosureV1(
        manifest_bytes,
        hashlib.sha256(manifest_bytes).hexdigest(),
        recomputed_digest,
        tuple(observed),
        sum(item.size_bytes for item in observed),
        closure_ref,
        entrypoint,
        trainer_entrypoint,
        tuple(raw_prefixes),
        tuple(raw_features),
    )


def _stage_locked_closure(
    closure: _LockedClosureV1,
    destination: Path,
) -> None:
    try:
        destination.mkdir()
    except OSError:
        raise ValueError("worker staging destination is not fresh") from None
    for member in closure.members:
        relative = PurePosixPath(member.path)
        parent = _ensure_direct_parent(destination, relative.parent)
        target = parent / relative.name
        if not target.absolute().is_relative_to(destination.absolute()):
            raise ValueError("staged worker member escapes its destination")
        _write_new_regular(target, member.payload)
        _apply_file_mode(target, executable=member.git_mode == "100755")
    _verify_staged_closure(destination, closure)


def _verify_staged_closure(root: Path, closure: _LockedClosureV1) -> None:
    staged = _walk_regular_files(root, "staged worker closure")
    files = [path.relative_to(root).as_posix() for path in staged]
    if set(files) != {member.path for member in closure.members}:
        raise ValueError("staged worker closure contains missing or extra files")
    for member in closure.members:
        target = root.joinpath(*PurePosixPath(member.path).parts)
        payload, info = _read_direct_regular(target, "staged worker member")
        if (
            len(payload) != member.size_bytes
            or hashlib.sha256(payload).hexdigest() != member.sha256
            or not _verify_file_mode(
                info, executable=member.git_mode == "100755"
            )
        ):
            raise ValueError("staged worker closure differs from its manifest")


def _locked_project_descriptors(
    source_lock: SourceLock,
) -> tuple[dict[str, object], ...]:
    """The project descriptors this path stages, derived from the lock alone.

    B-17 (architecture section 26.3).  B-12 staged `source_lock.inputs` and
    nothing else, but the Host's own publication phase is a second consumer of
    the staged source root: `_configuration_for_request`
    (`docker_publication.py:342`) reads `project/training/artifacts.json` from
    it at `:347-349`.  The lock records that file at
    `outputs.destination_registry` (`docker_training.py:304-308`), in the same
    `_descriptor` shape as an input and digested by the same admission, so the
    union below adds nothing the lock does not already carry and already
    digest.  Section 21.4's trust argument is preserved: the scope stays
    derived from the lock, exact, and verifiable from the lock alone.

    Sited outside `_stage_locked_project_inputs` deliberately.  That function
    keeps one reason to change -- how a recorded descriptor becomes a staged
    file -- and this one carries the other -- which recorded descriptors this
    path stages.  Every property B-12 gave the inputs therefore covers the
    registry with no new code: the pre-write size and digest equality, the
    read from the commit, and the set-equality re-verification of the staged
    tree.

    Refusing an absent or malformed registry rather than skipping it is the
    ruling, not caution.  The publish cut reads that file unconditionally, so
    skipping would reproduce B-17 several cuts later from a frame that knows
    nothing about the lock.  Admission writes the descriptor on the
    unconditional bind path, so the refusal is unreachable today; it is a
    contract pin, in the same spirit as the Y-B belt retained below, and for
    the same reason -- the proof of unreachability rests on another
    function's behaviour, which nothing enforces.
    """

    inputs = tuple(source_lock.inputs)
    outputs = source_lock.outputs
    registry = outputs.get("destination_registry") if type(outputs) is dict else None
    if (
        type(registry) is not dict
        or type(registry.get("path")) is not str
        or not registry["path"]
        or type(registry.get("size_bytes")) is not int
        or type(registry.get("sha256")) is not str
    ):
        raise ValueError(
            "locked project outputs do not record the destination registry"
        )
    for descriptor in inputs:
        if descriptor.get("path") != registry["path"]:
            continue
        # The registry is already among the inputs.  Append nothing: a blind
        # append would turn this coincidence into the duplicate-path refusal
        # below.  A differing digest or size means the lock disagrees with
        # itself, and staging must not pick a winner between two of its own
        # records.
        if (
            descriptor.get("size_bytes") == registry["size_bytes"]
            and descriptor.get("sha256") == registry["sha256"]
        ):
            return inputs
        raise ValueError(
            "locked project inputs disagree with the destination registry"
        )
    return inputs + (registry,)


def _stage_locked_project_inputs(
    repository: Path,
    commit: str,
    descriptors: tuple[dict[str, object], ...],
    destination: Path,
) -> None:
    """Stage exactly the project inputs the source lock records.

    B-12 (architecture section 21.12 items 1-4).  The prepared path used to
    archive the whole superproject at the locked commit, so a project large
    enough to hold research data could not be staged at all.  The staged scope
    is now the lock's `inputs` descriptors plus the destination registry the
    lock records at `outputs.destination_registry`: the container reads one of
    those files and the Host's own publication phase reads another (section
    26.2 carries the consumer census; section 21.3 was scoped to the container
    alone and is the frame error 26.1 diagnosed).  Every descriptor was written
    and digested by admission (section 21.10), so nothing new is trusted and no
    schema moves.

    Each member is read from the commit with `_git_selected_blobs`, never from
    the checkout, and its length and digest are compared to the recorded
    descriptor BEFORE it is written.  `_git_selected_blobs` also refuses a
    member that is not a regular blob at that commit (a symlink, a device, a
    duplicate), which is the property the retired link-free extraction carried.

    The bounds of section 21.7 are unchanged in value and now measure the
    staged input set rather than the operator's repository.
    """

    if type(descriptors) is not tuple or not descriptors:
        raise ValueError("staged project inputs contain missing or extra files")
    paths: list[str] = []
    total = 0
    for descriptor in descriptors:
        path = descriptor["path"]
        size = descriptor["size_bytes"]
        digest = descriptor["sha256"]
        if type(path) is not str or type(digest) is not str:
            raise ValueError("staged project inputs contain missing or extra files")
        if type(size) is not int or size < 0:
            raise ValueError("exact project input differs from its locked size")
        paths.append(path)
        total += size
    if len(set(paths)) != len(paths):
        raise ValueError("staged project inputs contain missing or extra files")
    if len(paths) > _MAX_PROJECT_ENTRIES or total > _MAX_PROJECT_ARCHIVE_BYTES:
        raise ValueError("exact project inputs exceed their bound")

    selected = _git_selected_blobs(repository, commit, tuple(paths))
    for descriptor in descriptors:
        _, payload = selected[descriptor["path"]]
        if not payload:
            raise ValueError("exact project input is empty")
        if len(payload) != descriptor["size_bytes"]:
            raise ValueError("exact project input differs from its locked size")
        if hashlib.sha256(payload).hexdigest() != descriptor["sha256"]:
            raise ValueError("exact project input differs from its locked digest")

    try:
        destination.mkdir()
    except OSError:
        raise ValueError("project staging destination is not fresh") from None
    for descriptor in descriptors:
        mode, payload = selected[descriptor["path"]]
        relative = _safe_relative(descriptor["path"], "locked project input")
        parent = _ensure_direct_parent(destination, relative.parent)
        target = parent / relative.name
        if not target.absolute().is_relative_to(destination.absolute()):
            raise ValueError("staged project input escapes its destination")
        _write_new_regular(target, payload)
        _apply_file_mode(target, executable=mode == "100755")
    _verify_staged_project_inputs(destination, descriptors)


def _verify_staged_project_inputs(
    root: Path, descriptors: tuple[dict[str, object], ...],
) -> None:
    """Re-verify the staged project root against the lock's descriptors.

    B-12 (architecture section 21.12 item 3), in the shape of
    `_verify_staged_closure`.  The set equality is the assertion that makes
    the scope a scope: a stage that wrote anything the lock does not record
    fails here.  Re-reading is not redundant with the pre-write check; it is
    what makes the staged tree, rather than the payload that was in memory,
    the thing that was verified.
    """

    staged = _walk_regular_files(root, "staged project inputs")
    files = [path.relative_to(root).as_posix() for path in staged]
    recorded = {descriptor["path"] for descriptor in descriptors}
    if set(files) != recorded or len(files) != len(recorded):
        raise ValueError("staged project inputs contain missing or extra files")
    total = 0
    for descriptor in descriptors:
        target = root.joinpath(*PurePosixPath(descriptor["path"]).parts)
        payload, _info = _read_direct_regular(target, "staged project input")
        if not payload:
            raise ValueError("exact project input is empty")
        if len(payload) != descriptor["size_bytes"]:
            raise ValueError("exact project input differs from its locked size")
        if hashlib.sha256(payload).hexdigest() != descriptor["sha256"]:
            raise ValueError("exact project input differs from its locked digest")
        total += len(payload)
        # Y-B (architecture section 22.15).  UNREACHABLE as the code
        # stands.  `_stage_locked_project_inputs` already sums the same
        # descriptors' `size_bytes` and bounds that sum by
        # _MAX_PROJECT_ARCHIVE_BYTES (256 MiB) before anything is written,
        # and the equality above pins each payload to its descriptor's
        # `size_bytes`, so this running total cannot exceed 256 MiB and can
        # never reach 512 MiB.  Retained as defence in depth rather than
        # deleted: the whole proof rests on that earlier bound running
        # FIRST, which nothing enforces, so a later change that moves or
        # drops it makes this belt load-bearing again silently.
        if total > _MAX_PROJECT_EXPANDED_BYTES:
            raise ValueError("exact project inputs exceed their bound")


def _copy_inventory(
    entries: tuple[DockerModelInventoryEntryV1, ...], destination: Path,
) -> str:
    if (
        type(entries) is not tuple
        or len(entries) > _MAX_INVENTORY_FILES
        or any(type(item) is not DockerModelInventoryEntryV1 for item in entries)
    ):
        raise TypeError("model inventory must be an exact bounded tuple")
    if tuple(sorted(entries, key=lambda item: item.relative_path)) != entries:
        raise ValueError("model inventory must be unique and sorted")
    if len({item.relative_path for item in entries}) != len(entries):
        raise ValueError("model inventory contains duplicate paths")
    for entry in entries:
        try:
            payload, source_info = _read_direct_regular(
                entry.source_path, "model inventory source"
            )
            source_after = entry.source_path.lstat()
        except (OSError, ValueError):
            raise ValueError("model inventory source is unavailable") from None
        if (
            entry.source_path.is_symlink()
            or _is_reparse(source_info)
            or not stat.S_ISREG(source_info.st_mode)
            or (
                source_info.st_dev, source_info.st_ino, source_info.st_mode,
                source_info.st_size, source_info.st_mtime_ns,
            ) != (
                source_after.st_dev, source_after.st_ino, source_after.st_mode,
                source_after.st_size, source_after.st_mtime_ns,
            )
            or len(payload) != entry.byte_count
            or hashlib.sha256(payload).hexdigest() != entry.sha256
        ):
            raise ValueError("model inventory source differs from its descriptor")
        relative = PurePosixPath(entry.relative_path)
        parent = _ensure_direct_parent(destination, relative.parent)
        target = parent / relative.name
        if not target.absolute().is_relative_to(destination.absolute()):
            raise ValueError("model inventory entry escapes its destination")
        _write_new_regular(target, payload)
        _apply_file_mode(target, executable=False, read_only=True)
    return _digest(
        b"synaptic-host-docker-model-inventory/v1",
        [item.projection() for item in entries],
    )


def _verify_inventory_at(
    entries: tuple[DockerModelInventoryEntryV1, ...], destination: Path,
) -> None:
    # B-10-R2 (review section 3.3): `destination` is the inventory's own
    # subtree, `cache/model`, NOT the cache root. Entry paths carry the
    # `model/` prefix, so they are stripped here to be compared against a walk
    # rooted at that subtree. The contract this narrows to is "the inventory's
    # subtree contains the inventory and nothing else"; siblings of the subtree
    # are not this function's business, because no engine resolution reads them.
    scoped_entries: list[tuple[str, DockerModelInventoryEntryV1]] = []
    expected_directories: set[str] = set()
    for entry in entries:
        relative = PurePosixPath(entry.relative_path)
        if len(relative.parts) < 2 or relative.parts[0] != _MODEL_INVENTORY_PREFIX:
            raise ValueError(
                "content-addressed model inventory entry is outside "
                f"{_MODEL_INVENTORY_PREFIX}/: {entry.relative_path}"
            )
        scoped = PurePosixPath(*relative.parts[1:])
        scoped_entries.append((scoped.as_posix(), entry))
        for depth in range(1, len(scoped.parts)):
            expected_directories.add(PurePosixPath(*scoped.parts[:depth]).as_posix())
    try:
        destination.lstat()
    except FileNotFoundError:
        # `_copy_inventory` creates the subtree lazily, one parent at a time,
        # so an inventory with no entries never brings `cache/model` into
        # existence. An absent subtree is an empty one; it is not a licence to
        # skip the comparison, which still fails below for a non-empty
        # inventory. Deliberately NOT `OSError`: a permission failure or any
        # other `lstat` error is not an absent subtree, and swallowing it here
        # would let the verify cut answer "empty" to a question it could not
        # actually ask.
        directories: tuple[Path, ...] = ()
        files: tuple[Path, ...] = ()
    except OSError:
        # Every other `lstat` failure keeps the contract it had before this
        # subtree scoping existed. This mirrors `_walk_tree` at :110-113, which
        # converts any `lstat` OSError into this same ValueError under the same
        # label, so an unreadable subtree still reaches the caller as a topology
        # cause rather than escaping as a raw OSError.
        raise ValueError(
            "content-addressed model inventory is unavailable"
        ) from None
    else:
        directories, files = _walk_tree(
            destination, "content-addressed model inventory"
        )
    observed = {
        path.relative_to(destination).as_posix(): path
        for path in files
    }
    if set(observed) != {scoped for scoped, _entry in scoped_entries}:
        raise ValueError("content-addressed model inventory has missing or extra files")
    if {
        path.relative_to(destination).as_posix() for path in directories
    } != expected_directories:
        raise ValueError("content-addressed model inventory has extra directories")
    for scoped, entry in scoped_entries:
        target = observed[scoped]
        try:
            payload, info = _read_direct_regular(
                target, "content-addressed model inventory"
            )
        except (OSError, ValueError):
            raise ValueError("content-addressed model inventory is incomplete") from None
        if (
            target.is_symlink()
            or _is_reparse(info)
            or not stat.S_ISREG(info.st_mode)
            or not _verify_file_mode(info, executable=False, read_only=True)
            or len(payload) != entry.byte_count
            or hashlib.sha256(payload).hexdigest() != entry.sha256
        ):
            raise ValueError("content-addressed model inventory differs from preparation")


def _create_artifact_topology(root: Path) -> None:
    for name in _ARTIFACT_DIRECTORY_NAMES:
        try:
            (root / name).mkdir()
        except OSError:
            raise ValueError("artifact preparation topology is not fresh") from None


def _verify_artifact_topology(
    root: Path,
    entries: tuple[DockerModelInventoryEntryV1, ...],
    *,
    expect_unused_artifacts: bool,
) -> None:
    # B-10 (architecture section 19.4): this function answers two different
    # questions in one scan. The checks below are IDENTITY -- is this the stage
    # we prepared -- and run unconditionally on every cut, because they cover
    # the tree that determines what executes. Only the final emptiness loop is
    # about USE, and only the caller knows whether the run has started yet.
    # `expect_unused_artifacts` is required and takes no default deliberately:
    # a default would let a future call site silently receive the permissive
    # branch, which is the one that admits an unverified stage.
    try:
        root_info = root.lstat()
        observed = tuple(os.scandir(root))
    except OSError:
        raise ValueError("artifact preparation topology is unavailable") from None
    if root.is_symlink() or _is_reparse(root_info) or not stat.S_ISDIR(
        root_info.st_mode
    ):
        raise ValueError("artifact preparation root is redirected or invalid")
    names: list[str] = []
    for entry in observed:
        try:
            info = entry.stat(follow_symlinks=False)
        except OSError:
            raise ValueError("artifact preparation topology is unavailable") from None
        if (
            entry.is_symlink()
            or _is_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise ValueError("artifact preparation topology contains an invalid entry")
        names.append(entry.name)
    if tuple(sorted(names)) != _ARTIFACT_DIRECTORY_NAMES:
        raise ValueError("artifact preparation topology is incomplete or extended")
    # B-10-R2 (review section 3.3): scoped to the inventory's own subtree, and
    # deliberately still OUTSIDE the guard below. `cache` is a writable mount
    # (`_layout`, read_only=False) and is excluded from
    # `_EMPTY_ARTIFACT_DIRECTORY_NAMES`, so the container may write siblings
    # such as `cache/huggingface` under the engine's HF cache pin. The domain
    # narrows; the schedule does not. Moving this call under the guard would
    # prove the inventory once, before the run, and never again on the tree
    # that determines what executes.
    _verify_inventory_at(entries, root / "cache" / _MODEL_INVENTORY_PREFIX)
    if expect_unused_artifacts:
        for name in _EMPTY_ARTIFACT_DIRECTORY_NAMES:
            try:
                if tuple(os.scandir(root / name)):
                    raise ValueError("artifact writable directory is not empty")
            except OSError:
                raise ValueError(
                    "artifact writable directory is unavailable"
                ) from None


def _source_manifest(root: Path) -> tuple[list[dict[str, object]], str]:
    entries: list[dict[str, object]] = []
    for path in _walk_regular_files(root, "staged source"):
        relative = path.relative_to(root).as_posix()
        if relative in {
            "control/source-manifest.json", "control/preparation-projection.json",
        }:
            continue
        payload, info = _read_direct_regular(path, "staged source file")
        entries.append({
            "relative_path": relative,
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "platform_mode": _mode_projection(info),
        })
    digest = _digest(b"synaptic-host-docker-source-manifest/v1", entries)
    return entries, digest


def _layout(source: Path, artifacts: Path) -> CloudRuntimeLayout:
    writable = tuple(
        RuntimeMount(
            name, artifacts / name, PurePosixPath("/artifacts") / name, False,
        )
        for name in ("artifacts", "state", "tracking", "cache", "tmp")
    )
    return CloudRuntimeLayout(
        engine=RuntimeMount(
            "engine", source / "engine", PurePosixPath("/source/engine"), True
        ),
        project=RuntimeMount(
            "project", source / "project", PurePosixPath("/source/project"), True
        ),
        writable=writable,
    )


def _control_manifest_relative(runtime_path: PurePosixPath) -> PurePosixPath:
    control_root = PurePosixPath("/source/control")
    if type(runtime_path) is not PurePosixPath:
        raise ValueError("worker manifest runtime path is not canonical")
    try:
        relative = runtime_path.relative_to(control_root)
    except ValueError:
        raise ValueError("worker manifest runtime path escapes control") from None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("worker manifest runtime path is not canonical")
    return relative


def _verify_worker_closure_binding(
    worker: object,
    bundle: object,
    closure: _LockedClosureV1,
) -> PurePosixPath:
    invalid_cause: BaseException | None = None
    try:
        transport = worker.transport
        if (
            type(transport.path) is not PurePosixPath
            or type(transport.control_root) is not PurePosixPath
            or not transport.path.is_absolute()
            or not transport.control_root.is_absolute()
            or any(
                part in {"", ".", ".."}
                for path in (transport.path, transport.control_root)
                for part in path.parts[1:]
            )
        ):
            raise ValueError
        expected_entrypoint = (
            worker.roots_map["engine"] / worker.entrypoint
        ).as_posix()
        expected_argv = (
            worker.interpreter,
            expected_entrypoint,
            "--canonical-workload-file",
            transport.path.as_posix(),
            "--canonical-workload-control-root",
            transport.control_root.as_posix(),
            "--canonical-workload-byte-count",
            str(bundle.workload_byte_count),
            "--canonical-workload-sha256",
            bundle.workload_sha256,
            "--canonical-workload-fingerprint",
            bundle.workload_fingerprint,
        )
        valid = (
            bundle.closure_manifest_bytes == closure.manifest_bytes
            and bundle.closure_manifest_byte_count == len(closure.manifest_bytes)
            and bundle.closure_manifest_sha256 == closure.manifest_sha256
            and bundle.closure_digest == closure.closure_digest
            and worker.entrypoint.as_posix() == closure.entrypoint
            and transport.byte_count == bundle.workload_byte_count
            and transport.sha256 == bundle.workload_sha256
            and transport.workload_fingerprint == bundle.workload_fingerprint
            and bundle.dispatch.argv == expected_argv
            and not (
                _FORBIDDEN_DISPATCH_ENVIRONMENT
                & set(bundle.dispatch.environment_map)
            )
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        # Section 27.4 shape.  The raise below runs outside this handler,
        # where the `as` binding is already gone, so bind a copy here: it is
        # what carries the rejection into `__cause__`.  It stays `None` on
        # the ordinary mismatch route, where `valid` is simply False and
        # there is no originating exception to name.
        invalid_cause = error
        valid = False
    if not valid:
        raise ValueError(
            "worker bundle differs from the locked source closure"
        ) from invalid_cause
    return _control_manifest_relative(bundle.closure_manifest_runtime_path)


def _verify_control_files(
    control: Path, manifest_relative: PurePosixPath
) -> None:
    directories, files = _walk_tree(control, "Docker control stage")
    expected_files = {
        "preparation-projection.json", "source-lock.json", "source-manifest.json",
        "storage.json", "workload.json", manifest_relative.as_posix(),
    }
    expected_directories = {
        PurePosixPath(*manifest_relative.parts[:depth]).as_posix()
        for depth in range(1, len(manifest_relative.parts))
    }
    if (
        {path.relative_to(control).as_posix() for path in files} != expected_files
        or {path.relative_to(control).as_posix() for path in directories}
        != expected_directories
    ):
        raise ValueError("Docker control stage contains missing or extra files")


def _verify_reuse(
    source: Path,
    projection: DockerStageProjectionV1,
    closure: _LockedClosureV1,
    manifest_runtime_path: PurePosixPath,
) -> None:
    manifest_path = source / "control" / "source-manifest.json"
    projection_path = source / "control" / "preparation-projection.json"
    manifest_relative = _control_manifest_relative(manifest_runtime_path)
    closure_path = source / "control" / Path(*manifest_relative.parts)
    try:
        manifest_bytes, _ = _read_direct_regular(
            manifest_path, "content-addressed source manifest"
        )
        projection_bytes, _ = _read_direct_regular(
            projection_path, "content-addressed preparation projection"
        )
        closure_bytes, _ = _read_direct_regular(
            closure_path, "content-addressed worker manifest"
        )
        manifest = json.loads(manifest_bytes)
        stored_projection = json.loads(projection_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("content-addressed Docker stage is incomplete") from None
    observed_entries, observed_digest = _source_manifest(source)
    if (
        _canonical(manifest) != manifest_bytes
        or _canonical(stored_projection) != projection_bytes
        or manifest.get("manifest_digest") != projection.source_manifest_digest
        or manifest.get("entries") != observed_entries
        or observed_digest != projection.source_manifest_digest
        or stored_projection != projection.to_dict()
        or closure_bytes != closure.manifest_bytes
    ):
        raise ValueError("content-addressed Docker stage differs from preparation")
    _verify_staged_closure(source / "engine", closure)
    _verify_control_files(source / "control", manifest_relative)


def stage_docker_worker_v1(
    *,
    plan: TrainingPlan,
    source_lock: SourceLock,
    context: ProjectContext,
    storage_configuration: bytes,
    model_inventory: tuple[DockerModelInventoryEntryV1, ...],
    expect_unused_artifacts: bool,
) -> DockerStagingResultV1:
    """Materialize one exact two-root worker stage without Docker or network I/O."""

    if type(plan) is not TrainingPlan or type(source_lock) is not SourceLock:
        raise TypeError("exact plan and source lock are required")
    if type(context) is not ProjectContext or context.mode != "host":
        raise TypeError("exact Host project context is required")
    if type(storage_configuration) is not bytes or not storage_configuration:
        raise ValueError("committed storage configuration is required")
    try:
        storage_document = json.loads(storage_configuration.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("committed storage configuration is invalid") from None
    if (
        type(storage_document) is not dict
        or storage_document.get("schema_version") != "synaptic-host-storage/v1"
        or plan.execution_source.project_source != source_lock.project_source
        or plan.execution_source.engine_source != source_lock.engine_source
        or plan.execution_source.environment.get("PYTHONPATH") != "/source/engine"
    ):
        raise ValueError("Docker staging provenance is invalid")
    locked_closure = _load_locked_closure(
        context.engine_root, source_lock.engine_source.commit
    )
    state_root = context.state_root.resolve(strict=False)
    mutable_root = (context.project_root / ".synaptic").resolve(strict=False)
    if not state_root.is_relative_to(mutable_root):
        raise ValueError("Docker staging must remain below Host state")
    stage_parent = state_root / "docker" / "stages"
    stage_parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="stage-", dir=stage_parent))
    windows_cleanup = (
        _capture_windows_stage_cleanup(stage_parent, temporary)
        if os.name == "nt"
        else None
    )
    promoted = False
    source = temporary / "source"
    artifacts = temporary / "artifacts"
    try:
        source.mkdir()
        artifacts.mkdir()
        _create_artifact_topology(artifacts)
        _stage_locked_project_inputs(
            context.project_root,
            source_lock.project_source.commit,
            _locked_project_descriptors(source_lock),
            source / "project",
        )
        _stage_locked_closure(
            locked_closure,
            source / "engine",
        )
        # The copier takes the cache ROOT and writes entry paths under it
        # verbatim, `model/` prefix included; the verifier takes the
        # `cache/model` SUBTREE and strips that prefix.  The two destinations
        # differ by one component on purpose -- see the B-10-R2 comment on
        # `_verify_inventory_at` (audit #297 YELLOW-2).
        inventory_digest = _copy_inventory(model_inventory, artifacts / "cache")
        control = source / "control"
        control.mkdir()
        _write_new_regular(
            control / "source-lock.json", source_lock.canonical_bytes
        )
        _write_new_regular(control / "storage.json", storage_configuration)
        layout = _layout(source, artifacts)
        control_location = WorkerControlLocationV1(PurePosixPath("/source/control"))
        worker = build_worker_invocation(
            plan,
            layout,
            control_location,
            CanonicalWorkloadFileLocationV1(PurePosixPath("/source/control")),
        )
        bundle = materialize_worker_bundle(worker)
        manifest_relative = _verify_worker_closure_binding(
            worker, bundle, locked_closure
        )
        _write_new_regular(
            control / "workload.json", bundle.canonical_workload_bytes
        )
        manifest_parent = _ensure_direct_parent(control, manifest_relative.parent)
        _write_new_regular(
            manifest_parent / manifest_relative.name, locked_closure.manifest_bytes
        )
        manifest_entries, manifest_digest = _source_manifest(source)
        _write_new_regular(
            control / "source-manifest.json",
            _canonical({
                "schema_version": "synaptic-host-docker-source-manifest/v1",
                "entries": manifest_entries,
                "manifest_digest": manifest_digest,
            }),
        )
        storage_digest = hashlib.sha256(storage_configuration).hexdigest()
        stage_key = _digest(b"synaptic-host-docker-stage/v1", {
            "source_lock_digest": source_lock.binding.source_lock_digest,
            "source_manifest_digest": manifest_digest,
            "worker_projection_digest": bundle.projection_sha256,
            "worker_closure_manifest_path": _CLOSURE_MANIFEST_SOURCE_PATH,
            "worker_closure_manifest_sha256": locked_closure.manifest_sha256,
            "worker_source_closure_digest": locked_closure.closure_digest,
            "model_inventory_digest": inventory_digest,
            "storage_configuration_digest": storage_digest,
        })
        final_source = stage_parent / stage_key / "source"
        final_artifacts = stage_parent / stage_key / "artifacts"
        projection = DockerStageProjectionV1(
            source_stage_ref=f"host-stage://{stage_key}/source",
            source_manifest_digest=manifest_digest,
            artifact_stage_ref=f"host-stage://{stage_key}/artifacts",
            worker_projection_digest=bundle.projection_sha256,
            workload_fingerprint=bundle.workload_fingerprint,
            workload_sha256=bundle.workload_sha256,
            worker_closure_manifest_path=_CLOSURE_MANIFEST_SOURCE_PATH,
            worker_closure_manifest_sha256=locked_closure.manifest_sha256,
            worker_source_closure_digest=locked_closure.closure_digest,
            staged_model_inventory_digest=inventory_digest,
            staged_storage_configuration_digest=storage_digest,
        )
        _write_new_regular(
            control / "preparation-projection.json",
            _canonical(projection.to_dict()),
        )
        _verify_control_files(control, manifest_relative)
        final_stage = final_source.parent
        if not final_stage.exists():
            final_stage.parent.mkdir(parents=True, exist_ok=True)
            try:
                temporary.rename(final_stage)
            except FileExistsError:
                pass
            else:
                promoted = True
                if windows_cleanup is not None:
                    _release_windows_stage(windows_cleanup)
        _verify_reuse(
            final_source,
            projection,
            locked_closure,
            bundle.closure_manifest_runtime_path,
        )
        _verify_artifact_topology(
            final_artifacts,
            model_inventory,
            expect_unused_artifacts=expect_unused_artifacts,
        )
        return DockerStagingResultV1(
            projection, final_source, final_artifacts, bundle
        )
    finally:
        if not promoted:
            _cleanup_unpromoted_stage(temporary, windows_cleanup)


__all__ = [
    "DockerModelInventoryEntryV1",
    "DockerStagingResultV1",
    "stage_docker_worker_v1",
]
