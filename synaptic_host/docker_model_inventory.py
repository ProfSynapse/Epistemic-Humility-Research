"""Resolve an exact, offline Hugging Face model snapshot for Docker staging."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import unicodedata
from pathlib import Path, PurePosixPath

from synaptic_tuner.api.v1 import TrainingInputV1

from .docker_provider import DockerProviderProfileV1
from .docker_staging import DockerModelInventoryEntryV1
from .local_io_v1.config import StorageRegistryV1
from .local_io_v1.model import RootAccessV1


_ROOT_REF = "docker-model-inventory-source"
_LOCATION_REF = "project://.synaptic/model-inventory"
_PERMIT_REF = "permit-docker-model-inventory-source"
_AUTHORITY_REF = "docker-model-inventory-authority"
_KEY_REF = "docker-model-inventory-storage-configuration"
_REVISION = re.compile(r"[0-9a-f]{40}")
_REPOSITORY_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}")
_MAX_INVENTORY_FILES = 20_000


def _is_reparse(info: os.stat_result) -> bool:
    return bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _identity(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _opened_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    # Windows fstat can project creation-time nanoseconds differently from
    # path-based stat, so bind the handle with stable node/type/size fields and
    # compare the complete path identity before and after the read.
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
    )


def _direct_directory(path: Path, label: str) -> os.stat_result:
    try:
        info = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError:
        raise ValueError(f"{label} is unavailable") from None
    if (
        path.is_symlink()
        or _is_reparse(info)
        or not stat.S_ISDIR(info.st_mode)
        or resolved != path.absolute()
    ):
        raise ValueError(f"{label} is redirected or invalid")
    return info


def _repository_components(model_ref: str) -> tuple[str, str]:
    if type(model_ref) is not str:
        raise TypeError("model.ref must be exact text")
    parts = tuple(model_ref.split("/"))
    if (
        len(parts) != 2
        or any(_REPOSITORY_COMPONENT.fullmatch(item) is None for item in parts)
        or any(item.endswith((".", "-")) or ".." in item or "--" in item for item in parts)
    ):
        raise ValueError("model.ref must be an exact Hugging Face repository id")
    return parts[0], parts[1]


def _hash_direct_regular(path: Path) -> tuple[int, str, tuple[int, ...]]:
    descriptor = -1
    try:
        before = path.lstat()
        if path.is_symlink() or _is_reparse(before) or not stat.S_ISREG(before.st_mode):
            raise OSError
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            byte_count += len(chunk)
            digest.update(chunk)
        after = path.lstat()
    except OSError:
        raise ValueError("model inventory file is redirected, special, or unavailable") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    identity = _identity(before)
    if (
        not stat.S_ISREG(opened.st_mode)
        or _is_reparse(after)
        or _opened_identity(before) != _opened_identity(opened)
        or identity != _identity(after)
        or byte_count != opened.st_size
    ):
        raise ValueError("model inventory file changed during its exact read")
    return byte_count, digest.hexdigest(), identity


def _inventory_snapshot(snapshot: Path, staged_prefix: PurePosixPath) -> tuple[DockerModelInventoryEntryV1, ...]:
    directory_identities: dict[Path, tuple[int, ...]] = {
        snapshot: _identity(_direct_directory(snapshot, "model snapshot"))
    }
    pending = [snapshot]
    files: list[tuple[str, Path]] = []
    folded_nodes: dict[str, str] = {}
    while pending:
        directory = pending.pop()
        try:
            entries = tuple(os.scandir(directory))
        except OSError:
            raise ValueError("model snapshot is unavailable") from None
        for entry in entries:
            path = Path(entry.path)
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                raise ValueError("model snapshot is unavailable") from None
            if entry.is_symlink() or _is_reparse(info):
                raise ValueError("model snapshot contains a redirect")
            relative = path.relative_to(snapshot).as_posix()
            if unicodedata.normalize("NFC", relative) != relative or "\\" in relative:
                raise ValueError("model snapshot contains a noncanonical path")
            folded = relative.casefold()
            previous = folded_nodes.setdefault(folded, relative)
            if previous != relative:
                raise ValueError("model snapshot contains a case-colliding path")
            if stat.S_ISDIR(info.st_mode):
                directory_identities[path] = _identity(
                    _direct_directory(path, "model snapshot directory")
                )
                pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                files.append((relative, path))
            else:
                raise ValueError("model snapshot contains a special file")
            if len(files) > _MAX_INVENTORY_FILES:
                raise ValueError("model snapshot exceeds the inventory file limit")
    if not files:
        raise ValueError("model snapshot is empty")

    results: list[DockerModelInventoryEntryV1] = []
    file_identities: dict[Path, tuple[int, ...]] = {}
    for relative, source in sorted(files, key=lambda item: item[0]):
        byte_count, sha256, identity = _hash_direct_regular(source)
        file_identities[source] = identity
        results.append(
            DockerModelInventoryEntryV1(
                relative_path=(staged_prefix / PurePosixPath(relative)).as_posix(),
                source_path=source.absolute(),
                byte_count=byte_count,
                sha256=sha256,
            )
        )

    try:
        for path, expected in directory_identities.items():
            if _identity(_direct_directory(path, "model snapshot directory")) != expected:
                raise ValueError("model snapshot changed during inventory")
        for path, expected in file_identities.items():
            current = path.lstat()
            if path.is_symlink() or _is_reparse(current) or _identity(current) != expected:
                raise ValueError("model snapshot changed during inventory")
    except OSError:
        raise ValueError("model snapshot changed during inventory") from None
    return tuple(results)


def resolve_docker_model_inventory_v1(
    *,
    training_input: TrainingInputV1,
    profile: DockerProviderProfileV1,
    storage_configuration: bytes,
    project_root: Path,
) -> tuple[DockerModelInventoryEntryV1, ...]:
    """Return deterministic descriptors for one already-present offline snapshot."""

    if type(training_input) is not TrainingInputV1:
        raise TypeError("exact TrainingInputV1 is required")
    if type(profile) is not DockerProviderProfileV1:
        raise TypeError("exact DockerProviderProfileV1 is required")
    if type(storage_configuration) is not bytes:
        raise TypeError("storage_configuration must be exact bytes")
    root = Path(project_root)
    if not root.is_absolute():
        raise ValueError("project_root must be absolute")
    if getattr(profile, "cache_admission", None) is not True:
        raise ValueError("Docker model cache admission is disabled")
    if getattr(profile, "network_mode", None) != "none":
        raise ValueError("Docker model inventory requires an offline profile")
    inventory_root_ref = getattr(profile, "inventory_root_ref", None)
    if inventory_root_ref != _ROOT_REF:
        raise ValueError("Docker model inventory root reference is invalid")
    if training_input.model.revision != training_input.model.tokenizer_revision:
        raise ValueError("model and tokenizer revisions must be identical")
    revision = training_input.model.revision
    if type(revision) is not str or _REVISION.fullmatch(revision) is None:
        raise ValueError("model revision must be an exact commit")
    namespace, repository = _repository_components(training_input.model.ref)

    storage = StorageRegistryV1.from_bytes(storage_configuration, project_root=root)
    proof = hashlib.sha256(
        b"synaptic-host-docker-model-inventory-storage/v1\0" + storage_configuration
    ).hexdigest()
    storage.issue_root_permit(
        inventory_root_ref,
        authority_ref=_AUTHORITY_REF,
        key_ref=_KEY_REF,
        proof_digest=proof,
    )
    binding = storage.resolve(inventory_root_ref)
    if (
        binding.root_ref != _ROOT_REF
        or binding.location_ref != _LOCATION_REF
        or binding.access is not RootAccessV1.READ_ONLY
        or binding.authorization_ref != _PERMIT_REF
        or binding.root_permit.permit_ref != _PERMIT_REF
        or binding.root_permit.access is not RootAccessV1.READ_ONLY
    ):
        raise ValueError("Docker model inventory storage binding is invalid")

    inventory_root = binding.absolute_root
    model_directory = inventory_root / f"models--{namespace}--{repository}"
    snapshots_directory = model_directory / "snapshots"
    snapshot = snapshots_directory / revision
    for path, label in (
        (inventory_root, "model inventory root"),
        (model_directory, "model repository cache"),
        (snapshots_directory, "model snapshots directory"),
        (snapshot, "model snapshot"),
    ):
        _direct_directory(path, label)
    staged_prefix = PurePosixPath(
        "model", f"models--{namespace}--{repository}", "snapshots", revision
    )
    return _inventory_snapshot(snapshot, staged_prefix)


__all__ = ["resolve_docker_model_inventory_v1"]
