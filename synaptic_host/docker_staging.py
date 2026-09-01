"""Run-owned selective staging for the offline Docker SFT worker."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
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


def _git_archive(repository: Path, commit: str) -> bytes:
    raw = _git(repository, ("archive", "--format=tar", _commit(commit)))
    if not raw or len(raw) > _MAX_PROJECT_ARCHIVE_BYTES:
        raise ValueError("exact project Git archive exceeds its bound")
    return raw


def _extract_link_free(raw: bytes, destination: Path) -> None:
    if type(raw) is not bytes or not raw or len(raw) > _MAX_PROJECT_ARCHIVE_BYTES:
        raise ValueError("exact project Git archive exceeds its bound")
    try:
        archive = tarfile.open(fileobj=BytesIO(raw), mode="r:")
    except tarfile.TarError:
        raise ValueError("exact project Git archive is invalid") from None
    try:
        destination.mkdir()
    except OSError:
        raise ValueError("project staging destination is not fresh") from None
    count = 0
    total = 0
    seen: set[str] = set()
    with archive:
        for member in archive:
            count += 1
            if count > _MAX_PROJECT_ENTRIES:
                raise ValueError("exact project Git archive has too many entries")
            relative = _safe_relative(member.name.rstrip("/"), "archive member")
            name = relative.as_posix()
            if name in seen:
                raise ValueError("exact project Git archive contains duplicate entries")
            seen.add(name)
            if member.isdir():
                _ensure_direct_parent(destination, relative)
                continue
            if not member.isreg():
                raise ValueError("exact project Git archive contains a link or special file")
            total += member.size
            if total > _MAX_PROJECT_EXPANDED_BYTES:
                raise ValueError("exact project Git archive exceeds its expanded bound")
            parent = _ensure_direct_parent(destination, relative.parent)
            target = parent / relative.name
            if not target.absolute().is_relative_to(destination.absolute()):
                raise ValueError("project archive member escapes its destination")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError("exact project Git archive member is unavailable")
            payload = handle.read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError("exact project Git archive member is truncated")
            _write_new_regular(target, payload)
            _apply_file_mode(target, executable=bool(member.mode & 0o111))


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
    directories, files = _walk_tree(
        destination, "content-addressed model inventory"
    )
    observed = {
        path.relative_to(destination).as_posix(): path
        for path in files
    }
    expected_directories: set[str] = set()
    for entry in entries:
        relative = PurePosixPath(entry.relative_path)
        for depth in range(1, len(relative.parts)):
            expected_directories.add(PurePosixPath(*relative.parts[:depth]).as_posix())
    if set(observed) != {entry.relative_path for entry in entries}:
        raise ValueError("content-addressed model inventory has missing or extra files")
    if {
        path.relative_to(destination).as_posix() for path in directories
    } != expected_directories:
        raise ValueError("content-addressed model inventory has extra directories")
    for entry in entries:
        target = observed[entry.relative_path]
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
) -> None:
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
    _verify_inventory_at(entries, root / "cache")
    for name in _EMPTY_ARTIFACT_DIRECTORY_NAMES:
        try:
            if tuple(os.scandir(root / name)):
                raise ValueError("artifact writable directory is not empty")
        except OSError:
            raise ValueError("artifact writable directory is unavailable") from None


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
    except (AttributeError, KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("worker bundle differs from the locked source closure")
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
    source = temporary / "source"
    artifacts = temporary / "artifacts"
    source.mkdir()
    artifacts.mkdir()
    _create_artifact_topology(artifacts)
    try:
        _extract_link_free(
            _git_archive(context.project_root, source_lock.project_source.commit),
            source / "project",
        )
        _stage_locked_closure(
            locked_closure,
            source / "engine",
        )
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
        _verify_reuse(
            final_source,
            projection,
            locked_closure,
            bundle.closure_manifest_runtime_path,
        )
        _verify_artifact_topology(final_artifacts, model_inventory)
        return DockerStagingResultV1(
            projection, final_source, final_artifacts, bundle
        )
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


__all__ = [
    "DockerModelInventoryEntryV1",
    "DockerStagingResultV1",
    "stage_docker_worker_v1",
]
