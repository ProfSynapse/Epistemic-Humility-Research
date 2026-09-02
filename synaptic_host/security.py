"""Host-owned authentication, execution grants, and scoped Git reads."""

from __future__ import annotations

import base64
import ctypes
import hashlib
import hmac
import os
import re
import secrets
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Sequence

if os.name == "nt":
    from ctypes import wintypes

from synaptic_tuner.api.v1 import (
    AuthorizationRequirement,
    ExecutionGrant,
    GrantBinding,
    ProjectContext,
)
from synaptic_tuner.api.v1.sources import RepositoryLocation

_HEAD_REF = re.compile(r"^refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_URL_USERINFO = re.compile(r"://[^/\s]*@")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _scrubbed_stderr(raw: bytes | None) -> str:
    """Bound and de-credential a child's stderr for an operator-facing error.

    Sliced to 512 bytes BEFORE decoding so a hostile remote cannot flood the
    log, decoded with errors="replace" because a truncated slice can cut a
    UTF-8 sequence in half, and any "scheme://userinfo@host" is dropped.  The
    reader already disables credential helpers and prompts, so a credential
    should never reach here at all; this is the second line, not the first.
    """
    text = (raw or b"")[:512].decode("utf-8", errors="replace")
    return " ".join(_URL_USERINFO.sub("://", text).split())


_PRIVATE_STORAGE_ERROR = "HMAC private storage validation failed"
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _private_storage_error() -> ValueError:
    return ValueError(_PRIVATE_STORAGE_ERROR)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _same_stat(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


if os.name == "nt":
    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ADVAPI32 = ctypes.WinDLL("advapi32", use_last_error=True)

    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _GENERIC_READ = 0x80000000
    _GENERIC_WRITE = 0x40000000
    _READ_CONTROL = 0x00020000
    _FILE_SHARE_READ = 0x00000001
    _CREATE_NEW = 1
    _OPEN_EXISTING = 3
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _FILE_ALL_ACCESS = 0x001F01FF
    _SE_FILE_OBJECT = 1
    _OWNER_SECURITY_INFORMATION = 0x00000001
    _DACL_SECURITY_INFORMATION = 0x00000004
    _SE_DACL_PROTECTED = 0x1000
    _ACL_SIZE_INFORMATION_CLASS = 2
    _ACCESS_ALLOWED_ACE_TYPE = 0
    _INHERITED_ACE = 0x10
    _TOKEN_QUERY = 0x0008
    _TOKEN_USER_CLASS = 1
    _SDDL_REVISION_1 = 1
    _ERROR_ALREADY_EXISTS = 183
    _ERROR_FILE_EXISTS = 80

    class _SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = (
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", wintypes.LPVOID),
            ("bInheritHandle", wintypes.BOOL),
        )

    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = (
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        )

    class _SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = (("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD))

    class _TOKEN_USER(ctypes.Structure):
        _fields_ = (("User", _SID_AND_ATTRIBUTES),)

    class _ACL_SIZE_INFORMATION(ctypes.Structure):
        _fields_ = (
            ("AceCount", wintypes.DWORD),
            ("AclBytesInUse", wintypes.DWORD),
            ("AclBytesFree", wintypes.DWORD),
        )

    class _ACE_HEADER(ctypes.Structure):
        _fields_ = (
            ("AceType", ctypes.c_ubyte),
            ("AceFlags", ctypes.c_ubyte),
            ("AceSize", wintypes.WORD),
        )

    class _ACCESS_ALLOWED_ACE(ctypes.Structure):
        _fields_ = (
            ("Header", _ACE_HEADER),
            ("Mask", wintypes.DWORD),
            ("SidStart", wintypes.DWORD),
        )

    _KERNEL32.GetCurrentProcess.restype = wintypes.HANDLE
    _KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _KERNEL32.CloseHandle.restype = wintypes.BOOL
    _KERNEL32.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(_SECURITY_ATTRIBUTES), wintypes.DWORD, wintypes.DWORD,
        wintypes.HANDLE,
    )
    _KERNEL32.CreateFileW.restype = wintypes.HANDLE
    _KERNEL32.CreateDirectoryW.argtypes = (
        wintypes.LPCWSTR, ctypes.POINTER(_SECURITY_ATTRIBUTES),
    )
    _KERNEL32.CreateDirectoryW.restype = wintypes.BOOL
    _KERNEL32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
    )
    _KERNEL32.GetFileInformationByHandle.restype = wintypes.BOOL
    _KERNEL32.GetVolumePathNameW.argtypes = (
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
    )
    _KERNEL32.GetVolumePathNameW.restype = wintypes.BOOL
    _KERNEL32.GetVolumeInformationW.argtypes = (
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
    )
    _KERNEL32.GetVolumeInformationW.restype = wintypes.BOOL
    _KERNEL32.ReadFile.argtypes = (
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    )
    _KERNEL32.ReadFile.restype = wintypes.BOOL
    _KERNEL32.WriteFile.argtypes = (
        wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    )
    _KERNEL32.WriteFile.restype = wintypes.BOOL
    _KERNEL32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    _KERNEL32.FlushFileBuffers.restype = wintypes.BOOL
    _KERNEL32.LocalFree.argtypes = (wintypes.HLOCAL,)
    _KERNEL32.LocalFree.restype = wintypes.HLOCAL
    _ADVAPI32.OpenProcessToken.argtypes = (
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE),
    )
    _ADVAPI32.OpenProcessToken.restype = wintypes.BOOL
    _ADVAPI32.GetTokenInformation.argtypes = (
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    _ADVAPI32.GetTokenInformation.restype = wintypes.BOOL
    _ADVAPI32.ConvertSidToStringSidW.argtypes = (
        wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR),
    )
    _ADVAPI32.ConvertSidToStringSidW.restype = wintypes.BOOL
    _ADVAPI32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    )
    _ADVAPI32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    _ADVAPI32.GetSecurityInfo.argtypes = (
        wintypes.HANDLE, ctypes.c_int, wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
    )
    _ADVAPI32.GetSecurityInfo.restype = wintypes.DWORD
    _ADVAPI32.GetSecurityDescriptorControl.argtypes = (
        wintypes.LPVOID, ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    _ADVAPI32.GetSecurityDescriptorControl.restype = wintypes.BOOL
    _ADVAPI32.GetAclInformation.argtypes = (
        wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, ctypes.c_int,
    )
    _ADVAPI32.GetAclInformation.restype = wintypes.BOOL
    _ADVAPI32.GetAce.argtypes = (
        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID),
    )
    _ADVAPI32.GetAce.restype = wintypes.BOOL


    def _win_close(handle: int) -> None:
        if handle not in (None, _INVALID_HANDLE_VALUE):
            _KERNEL32.CloseHandle(handle)


    def _win_sid_string(sid: int) -> str:
        rendered = wintypes.LPWSTR()
        if not _ADVAPI32.ConvertSidToStringSidW(sid, ctypes.byref(rendered)):
            raise _private_storage_error()
        try:
            return rendered.value
        finally:
            _KERNEL32.LocalFree(ctypes.cast(rendered, wintypes.HLOCAL))


    def _win_current_user_sid() -> str:
        token = wintypes.HANDLE()
        if not _ADVAPI32.OpenProcessToken(
            _KERNEL32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)
        ):
            raise _private_storage_error()
        try:
            required = wintypes.DWORD()
            _ADVAPI32.GetTokenInformation(
                token, _TOKEN_USER_CLASS, None, 0, ctypes.byref(required)
            )
            if required.value == 0:
                raise _private_storage_error()
            buffer = ctypes.create_string_buffer(required.value)
            if not _ADVAPI32.GetTokenInformation(
                token, _TOKEN_USER_CLASS, buffer, required.value,
                ctypes.byref(required),
            ):
                raise _private_storage_error()
            user = ctypes.cast(buffer, ctypes.POINTER(_TOKEN_USER)).contents
            return _win_sid_string(user.User.Sid)
        finally:
            _win_close(token.value)


    def _win_security_attributes() -> tuple[_SECURITY_ATTRIBUTES, int]:
        user_sid = _win_current_user_sid()
        descriptor = wintypes.LPVOID()
        sddl = f"O:{user_sid}G:{user_sid}D:P(A;;FA;;;SY)(A;;FA;;;{user_sid})"
        if not _ADVAPI32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, _SDDL_REVISION_1, ctypes.byref(descriptor), None
        ):
            raise _private_storage_error()
        attributes = _SECURITY_ATTRIBUTES(
            ctypes.sizeof(_SECURITY_ATTRIBUTES), descriptor, False
        )
        return attributes, descriptor.value


    def _win_create_private_directory(path: Path) -> None:
        _win_require_ntfs(path.parent)
        attributes, descriptor = _win_security_attributes()
        try:
            if not _KERNEL32.CreateDirectoryW(str(path), ctypes.byref(attributes)):
                error = ctypes.get_last_error()
                if error != _ERROR_ALREADY_EXISTS:
                    raise _private_storage_error()
        finally:
            _KERNEL32.LocalFree(descriptor)


    def _win_require_ntfs(path: Path) -> None:
        volume = ctypes.create_unicode_buffer(32768)
        filesystem = ctypes.create_unicode_buffer(64)
        if not _KERNEL32.GetVolumePathNameW(str(path), volume, len(volume)):
            raise _private_storage_error()
        if not _KERNEL32.GetVolumeInformationW(
            volume.value, None, 0, None, None, None,
            filesystem, len(filesystem),
        ) or filesystem.value.upper() != "NTFS":
            raise _private_storage_error()


    def _win_open_path(path: Path, *, directory: bool, write: bool = False,
                       create: bool = False) -> int:
        desired = _READ_CONTROL | _GENERIC_READ | (_GENERIC_WRITE if write else 0)
        flags = _FILE_FLAG_OPEN_REPARSE_POINT
        if directory:
            flags |= _FILE_FLAG_BACKUP_SEMANTICS
        attributes = None
        descriptor = None
        if create:
            attributes, descriptor = _win_security_attributes()
        try:
            handle = _KERNEL32.CreateFileW(
                str(path), desired, _FILE_SHARE_READ,
                ctypes.byref(attributes) if attributes is not None else None,
                _CREATE_NEW if create else _OPEN_EXISTING, flags, None,
            )
            if handle == _INVALID_HANDLE_VALUE:
                error = ctypes.get_last_error()
                if create and error in {_ERROR_ALREADY_EXISTS, _ERROR_FILE_EXISTS}:
                    raise FileExistsError
                raise _private_storage_error()
            return handle
        finally:
            if descriptor is not None:
                _KERNEL32.LocalFree(descriptor)


    def _win_file_info(handle: int) -> tuple[tuple[int, int], int, int, int]:
        info = _BY_HANDLE_FILE_INFORMATION()
        if not _KERNEL32.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise _private_storage_error()
        identity = (
            int(info.dwVolumeSerialNumber),
            (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow),
        )
        size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
        return identity, int(info.dwFileAttributes), int(info.nNumberOfLinks), size


    def _win_validate_acl(handle: int) -> None:
        owner = wintypes.LPVOID()
        dacl = wintypes.LPVOID()
        descriptor = wintypes.LPVOID()
        result = _ADVAPI32.GetSecurityInfo(
            handle, _SE_FILE_OBJECT,
            _OWNER_SECURITY_INFORMATION | _DACL_SECURITY_INFORMATION,
            ctypes.byref(owner), None, ctypes.byref(dacl), None,
            ctypes.byref(descriptor),
        )
        if result != 0 or not descriptor.value or not owner.value or not dacl.value:
            if descriptor.value:
                _KERNEL32.LocalFree(descriptor)
            raise _private_storage_error()
        try:
            control = wintypes.WORD()
            revision = wintypes.DWORD()
            if (
                not _ADVAPI32.GetSecurityDescriptorControl(
                    descriptor, ctypes.byref(control), ctypes.byref(revision)
                )
                or not (control.value & _SE_DACL_PROTECTED)
                or _win_sid_string(owner) != _win_current_user_sid()
            ):
                raise _private_storage_error()
            size = _ACL_SIZE_INFORMATION()
            if not _ADVAPI32.GetAclInformation(
                dacl, ctypes.byref(size), ctypes.sizeof(size),
                _ACL_SIZE_INFORMATION_CLASS,
            ):
                raise _private_storage_error()
            expected = {_win_current_user_sid(), "S-1-5-18"}
            observed: set[str] = set()
            if size.AceCount != len(expected):
                raise _private_storage_error()
            for index in range(size.AceCount):
                pointer = wintypes.LPVOID()
                if not _ADVAPI32.GetAce(dacl, index, ctypes.byref(pointer)):
                    raise _private_storage_error()
                ace = ctypes.cast(pointer, ctypes.POINTER(_ACCESS_ALLOWED_ACE)).contents
                if (
                    ace.Header.AceType != _ACCESS_ALLOWED_ACE_TYPE
                    or ace.Header.AceFlags & _INHERITED_ACE
                    or ace.Mask != _FILE_ALL_ACCESS
                ):
                    raise _private_storage_error()
                sid_pointer = ctypes.addressof(ace) + _ACCESS_ALLOWED_ACE.SidStart.offset
                sid = _win_sid_string(sid_pointer)
                if sid not in expected or sid in observed:
                    raise _private_storage_error()
                observed.add(sid)
            if observed != expected:
                raise _private_storage_error()
        finally:
            _KERNEL32.LocalFree(descriptor)


    def _win_validate_directory(path: Path) -> None:
        _win_require_ntfs(path)
        first = _win_open_path(path, directory=True)
        second = None
        try:
            identity, attributes, _links, _size = _win_file_info(first)
            if (
                not attributes & _FILE_ATTRIBUTE_DIRECTORY
                or attributes & _FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise _private_storage_error()
            _win_validate_acl(first)
            second = _win_open_path(path, directory=True)
            after_identity, after_attributes, _after_links, _after_size = _win_file_info(second)
            if identity != after_identity or attributes != after_attributes:
                raise _private_storage_error()
            _win_validate_acl(second)
        finally:
            _win_close(second)
            _win_close(first)


    def _win_read_private_key(path: Path) -> tuple[bytes, tuple[int, int]]:
        _win_require_ntfs(path)
        first = _win_open_path(path, directory=False)
        second = None
        try:
            identity, attributes, links, size = _win_file_info(first)
            if (
                attributes & (_FILE_ATTRIBUTE_DIRECTORY | _FILE_ATTRIBUTE_REPARSE_POINT)
                or links != 1
                or size != 32
            ):
                raise _private_storage_error()
            _win_validate_acl(first)
            buffer = ctypes.create_string_buffer(33)
            count = wintypes.DWORD()
            if not _KERNEL32.ReadFile(first, buffer, 33, ctypes.byref(count), None):
                raise _private_storage_error()
            if count.value != 32:
                raise _private_storage_error()
            second = _win_open_path(path, directory=False)
            after_identity, after_attributes, after_links, after_size = _win_file_info(second)
            if (
                identity != after_identity
                or attributes != after_attributes
                or after_links != 1
                or after_size != 32
            ):
                raise _private_storage_error()
            _win_validate_acl(second)
            return bytes(buffer.raw[:32]), identity
        finally:
            _win_close(second)
            _win_close(first)


    def _win_create_private_key(path: Path, value: bytes) -> None:
        _win_require_ntfs(path.parent)
        handle = _win_open_path(path, directory=False, write=True, create=True)
        try:
            identity, attributes, links, size = _win_file_info(handle)
            if (
                attributes & (_FILE_ATTRIBUTE_DIRECTORY | _FILE_ATTRIBUTE_REPARSE_POINT)
                or links != 1
                or size != 0
                or identity == (0, 0)
            ):
                raise _private_storage_error()
            _win_validate_acl(handle)
            source = ctypes.create_string_buffer(value)
            written = wintypes.DWORD()
            if (
                not _KERNEL32.WriteFile(
                    handle, source, len(value), ctypes.byref(written), None
                )
                or written.value != len(value)
                or not _KERNEL32.FlushFileBuffers(handle)
            ):
                raise _private_storage_error()
        finally:
            _win_close(handle)


class FileHmacAuthenticator:
    """HMAC boundary backed by one private host-state key file."""

    def __init__(self, key_path: Path, *, key_ref: str) -> None:
        path = Path(key_path)
        if not path.is_absolute() or not key_ref or key_ref != key_ref.strip():
            raise ValueError("absolute key path and canonical key reference are required")
        self.key_path = _lexical_absolute(path)
        self.key_ref = key_ref
        self._private_storage_root = self.key_path.parent
        self._bound_key_identity: tuple[int, int] | None = None

    @classmethod
    def from_context(
        cls, context: ProjectContext, *, key_ref: str = "modal-evidence-v1"
    ) -> "FileHmacAuthenticator":
        if not isinstance(context, ProjectContext) or context.mode != "host":
            raise ValueError("host project context is required")
        return cls(context.state_root / "modal" / "evidence-hmac.key", key_ref=key_ref)

    @classmethod
    def for_docker(
        cls, context: ProjectContext, *, durable_rows_exist: bool,
    ) -> "FileHmacAuthenticator":
        """Open or exclusively create the one stable Docker control key."""

        if (
            not isinstance(context, ProjectContext)
            or context.mode != "host"
            or type(durable_rows_exist) is not bool
        ):
            raise ValueError("host context and exact Docker durability state are required")
        state = _lexical_absolute(context.state_root)
        mutable = _lexical_absolute(context.project_root / ".synaptic")
        try:
            confined = os.path.commonpath((str(state), str(mutable))) == str(mutable)
        except ValueError:
            confined = False
        if not confined:
            raise ValueError("Docker key must remain below host state")
        directory = state / "docker"
        key_path = directory / "control-hmac.key"
        value = cls(key_path, key_ref="docker-control-v1")
        value._private_storage_root = mutable
        value._ensure_private_storage_directories()
        try:
            key_path.lstat()
        except FileNotFoundError:
            if durable_rows_exist:
                raise ValueError("Docker control key is missing for durable runs") from None
            value.initialize()
        else:
            value._key()
        return value

    @staticmethod
    def _create_private_directory(path: Path) -> None:
        if os.name == "nt":
            _win_create_private_directory(path)
            return
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass

    @staticmethod
    def _validate_private_directory(path: Path) -> None:
        try:
            if os.name == "nt":
                _win_validate_directory(path)
                return
            before = os.lstat(path)
            flags = (
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
            )
            descriptor = os.open(path, flags)
            try:
                opened = os.fstat(descriptor)
                after = os.lstat(path)
                if (
                    not stat.S_ISDIR(before.st_mode)
                    or stat.S_ISLNK(before.st_mode)
                    or not stat.S_ISDIR(opened.st_mode)
                    or not _same_stat(before, opened)
                    or not _same_stat(opened, after)
                    or opened.st_uid != os.geteuid()
                    or stat.S_IMODE(opened.st_mode) != 0o700
                ):
                    raise _private_storage_error()
            finally:
                os.close(descriptor)
        except (FileNotFoundError, OSError, ValueError):
            raise _private_storage_error() from None

    def _ensure_private_storage_directories(self) -> None:
        root = self._private_storage_root
        leaf = self.key_path.parent
        try:
            relative = leaf.relative_to(root)
        except ValueError:
            raise _private_storage_error() from None
        cursor = root
        chain = (root,) + tuple(root.joinpath(*relative.parts[:index]) for index in range(1, len(relative.parts) + 1))
        for directory in chain:
            if not directory.exists():
                parent = directory.parent
                if not parent.exists():
                    missing: list[Path] = []
                    probe = parent
                    while not probe.exists():
                        missing.append(probe)
                        probe = probe.parent
                    for ancestor in reversed(missing):
                        self._create_private_directory(ancestor)
                self._create_private_directory(directory)
            self._validate_private_directory(directory)

    def initialize(self) -> None:
        self._ensure_private_storage_directories()
        generated = secrets.token_bytes(32)
        if not isinstance(generated, bytes) or len(generated) != 32:
            raise ValueError("evidence key generation failed")
        if os.name == "nt":
            try:
                _win_create_private_key(self.key_path, generated)
            except FileExistsError:
                self._key()
                return
            try:
                persisted = self._key()
                if not hmac.compare_digest(persisted, generated):
                    raise ValueError("evidence key publication failed")
            except BaseException:
                raise
            return
        try:
            descriptor = os.open(
                self.key_path,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_BINARY", 0),
                0o600,
            )
        except FileExistsError:
            self._key()
            return

        created_metadata: os.stat_result | None = None
        try:
            created_metadata = os.fstat(descriptor)
            if not stat.S_ISREG(created_metadata.st_mode):
                raise ValueError("evidence key must be a regular file")

            value = memoryview(generated)
            written = 0
            while written < len(value):
                count = os.write(descriptor, value[written:])
                if (
                    type(count) is not int
                    or count <= 0
                    or count > len(value) - written
                ):
                    raise OSError("evidence key write made no progress")
                written += count
            os.fsync(descriptor)

            closing_descriptor = descriptor
            descriptor = None
            os.close(closing_descriptor)
            persisted = self._key()
            if not hmac.compare_digest(persisted, generated):
                raise ValueError("evidence key publication failed")
        except BaseException:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException:
                    pass
            if created_metadata is not None:
                self._remove_created_file(created_metadata)
            raise

    def _remove_created_file(self, created_metadata: os.stat_result) -> None:
        try:
            current_metadata = os.lstat(self.key_path)
            if (
                not stat.S_ISREG(current_metadata.st_mode)
                or stat.S_ISLNK(current_metadata.st_mode)
                or current_metadata.st_dev != created_metadata.st_dev
                or current_metadata.st_ino != created_metadata.st_ino
            ):
                return
            os.unlink(self.key_path)
        except BaseException:
            pass

    def _key(self, key_ref: str | None = None) -> bytes:
        if key_ref is not None and key_ref != self.key_ref:
            raise ValueError("evidence key reference mismatch")
        self._ensure_private_storage_directories()
        if os.name == "nt":
            try:
                value, identity = _win_read_private_key(self.key_path)
                if (
                    self._bound_key_identity is not None
                    and self._bound_key_identity != identity
                ):
                    raise _private_storage_error()
                self._bound_key_identity = identity
                return value
            except (FileNotFoundError, OSError, ValueError):
                raise _private_storage_error() from None
        descriptor = None
        try:
            before = os.lstat(self.key_path)
            descriptor = os.open(
                self.key_path,
                os.O_RDONLY | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            )
            opened = os.fstat(descriptor)
            after_open = os.lstat(self.key_path)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_ISLNK(before.st_mode)
                or not stat.S_ISREG(opened.st_mode)
                or not _same_stat(before, opened)
                or not _same_stat(opened, after_open)
                or opened.st_uid != os.geteuid()
                or stat.S_IMODE(opened.st_mode) != 0o600
                or opened.st_nlink != 1
                or opened.st_size != 32
            ):
                raise _private_storage_error()
            chunks: list[bytes] = []
            remaining = 33
            while remaining:
                chunk = os.read(descriptor, remaining)
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            value = b"".join(chunks)
            after_read = os.fstat(descriptor)
            after_path = os.lstat(self.key_path)
            if (
                len(value) != 32
                or not _same_stat(opened, after_read)
                or not _same_stat(after_read, after_path)
                or after_read.st_nlink != 1
                or after_read.st_size != 32
                or stat.S_IMODE(after_read.st_mode) != 0o600
            ):
                raise _private_storage_error()
            identity = (int(after_read.st_dev), int(after_read.st_ino))
            if (
                self._bound_key_identity is not None
                and self._bound_key_identity != identity
            ):
                raise _private_storage_error()
            self._bound_key_identity = identity
            return value
        except (FileNotFoundError, OSError, ValueError):
            raise _private_storage_error() from None
        finally:
            if descriptor is not None:
                os.close(descriptor)

    @property
    def private_storage_verified(self) -> bool:
        self._key()
        return True

    @property
    def encoded_key(self) -> str:
        return base64.b64encode(self._key()).decode("ascii")

    def sign(self, purpose: str, payload: bytes, key_ref: str) -> bytes:
        if not isinstance(purpose, str) or not purpose or not purpose.isascii():
            raise TypeError("evidence purpose must be nonblank ASCII")
        if not isinstance(payload, bytes):
            raise TypeError("evidence payload must be bytes")
        return hmac.new(
            self._key(key_ref), purpose.encode("ascii") + b"\0" + payload,
            hashlib.sha256,
        ).digest()

    def verify(self, purpose: str, payload: bytes, tag: bytes, key_ref: str) -> bool:
        expected = self.sign(purpose, payload, key_ref)
        return isinstance(tag, bytes) and hmac.compare_digest(expected, tag)


class BoundedGrantProvider:
    """Issues one-process grants only within the configured paid-effect ceiling."""

    def __init__(self, *, maximum_cost_minor_units: int, currency: str, clock=utc_now):
        if type(maximum_cost_minor_units) is not int or maximum_cost_minor_units < 0:
            raise ValueError("maximum cost must be a non-negative integer")
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        self.maximum_cost_minor_units = maximum_cost_minor_units
        self.currency = currency.upper()
        self.clock = clock
        self._authorized: set[str] = set()

    def authorize(
        self, requirements: tuple[AuthorizationRequirement, ...]
    ) -> ExecutionGrant:
        if len(requirements) != 1:
            raise ValueError("exactly one execution authorization is required")
        requirement = requirements[0]
        if (
            requirement.operation != "training.start"
            or requirement.paid_effect is not True
            or requirement.currency != self.currency
            or requirement.maximum_cost_minor_units is None
            or requirement.maximum_cost_minor_units > self.maximum_cost_minor_units
        ):
            raise ValueError("execution requirement exceeds host authorization")
        grant = ExecutionGrant("grant-" + secrets.token_hex(16))
        self._authorized.add(grant.grant_ref)
        return grant

    def bind(self, grant, *, operation, requirements):
        if not isinstance(grant, ExecutionGrant) or grant.grant_ref not in self._authorized:
            raise ValueError("execution grant was not authorized by this host")
        self._authorized.remove(grant.grant_ref)
        self.authorize_requirement(requirements)
        issued = _parse_utc(self.clock())
        expires = issued + timedelta(minutes=5)
        return GrantBinding.from_operation(
            operation,
            issued_at=issued.strftime("%Y-%m-%dT%H:%M:%SZ"),
            expires_at=expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def authorize_requirement(self, requirements) -> None:
        if len(requirements) != 1:
            raise ValueError("exactly one execution authorization is required")
        requirement = requirements[0]
        if (
            requirement.operation != "training.start"
            or requirement.paid_effect is not True
            or requirement.currency != self.currency
            or requirement.maximum_cost_minor_units is None
            or requirement.maximum_cost_minor_units > self.maximum_cost_minor_units
        ):
            raise ValueError("execution requirement exceeds host authorization")


class ScopedGitRemoteReader:
    """Read exactly one pushed branch ref with prompts and ambient config disabled."""

    def __init__(self, runner: Callable[[Sequence[str]], bytes] | None = None) -> None:
        self._runner = runner or self._run

    @staticmethod
    def _run(argv: Sequence[str]) -> bytes:
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
            "LC_ALL": "C",
            "LANG": "C",
        }
        if os.name == "nt" and "SystemRoot" in os.environ:
            # Winsock will not initialise without SystemRoot, so ls-remote dies
            # at DNS with "getaddrinfo() thread failed to start".  SystemDrive,
            # windir, COMSPEC and PATHEXT were each measured unnecessary and are
            # deliberately NOT carried: the scrub stays minimal.
            environment["SystemRoot"] = os.environ["SystemRoot"]
        try:
            completed = subprocess.run(
                tuple(argv), check=True, capture_output=True, timeout=20,
                env=environment, stdin=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as failure:
            # check=True is kept, but the child's own diagnosis is no longer
            # discarded: a bare "exit 128" costs the next operator a whole
            # bisect, while the one line Git already wrote names the cause.
            raise ValueError(
                f"remote Git read failed with exit {failure.returncode}: "
                + _scrubbed_stderr(failure.stderr)
            ) from failure
        if len(completed.stdout) > 4096:
            raise ValueError("remote Git proof exceeded its bound")
        return completed.stdout

    def read_ref(self, *, canonical_url: str, exact_ref: str) -> bytes:
        location = RepositoryLocation.parse(canonical_url)
        if location.canonical_url != canonical_url or _HEAD_REF.fullmatch(exact_ref) is None:
            raise ValueError("canonical repository URL and exact branch ref are required")
        return self._runner(("git", "ls-remote", "--refs", canonical_url, exact_ref))
