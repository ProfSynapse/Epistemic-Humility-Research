"""Fail-closed local sink for authenticated training artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import ctypes
import errno
from pathlib import Path

from synaptic_tuner.api.v1 import (
    RunArtifactRequest, RunsAPI, TrainingRunRef, TrainingRunState, VerifiedArtifact,
)


_ROLES = (
    "workload_record", "training_lineage", "training_metrics",
    "final_model", "tokenizer",
)
_FILENAMES = {
    "workload_record": "workload-record.json",
    "training_lineage": "training-lineage.json",
    "training_metrics": "training-metrics.json",
    "final_model": "final-model.bin",
    "tokenizer": "tokenizer.bin",
}
_RUN_ID = re.compile(r"^run-[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_FILE_LIMIT = 64 * 1024 * 1024
_TOTAL_LIMIT = 256 * 1024 * 1024
_CHUNK_LIMIT = 1024 * 1024


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")


def _directory(fd: int) -> tuple[int, int]:
    value = os.fstat(fd)
    if (
        not stat.S_ISDIR(value.st_mode) or value.st_uid != os.geteuid()
        or stat.S_IMODE(value.st_mode) != 0o700
    ):
        raise ValueError("retrieval storage is not private")
    return value.st_dev, value.st_ino


def _require_link(parent: int, name: str, child: int) -> None:
    try:
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
        opened = os.fstat(child)
    except OSError:
        raise ValueError("retrieval storage identity changed") from None
    if (
        not stat.S_ISDIR(linked.st_mode)
        or (linked.st_dev, linked.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        raise ValueError("retrieval storage identity changed")
    _directory(child)


def _require_root(path: Path, fd: int) -> None:
    try:
        linked = os.stat(path, follow_symlinks=False)
        opened = os.fstat(fd)
    except OSError:
        raise ValueError("project root identity changed") from None
    if (
        not stat.S_ISDIR(linked.st_mode) or linked.st_uid != os.geteuid()
        or (linked.st_dev, linked.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        raise ValueError("project root identity changed")


def _require_namespace(root: Path, root_fd: int, synaptic_fd: int,
                       retrievals_fd: int, run_name: str, run_fd: int) -> None:
    _require_root(root, root_fd)
    _require_link(root_fd, ".synaptic", synaptic_fd)
    _require_link(synaptic_fd, "retrievals", retrievals_fd)
    _require_link(retrievals_fd, run_name, run_fd)


def _open_child(parent: int, name: str, *, create: bool, exclusive: bool = False) -> int:
    if create:
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            if exclusive:
                raise ValueError("retrieval already exists") from None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, dir_fd=parent)
    except OSError:
        raise ValueError("retrieval storage is unavailable") from None
    try:
        _directory(fd)
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
        opened = os.fstat(fd)
        if (linked.st_dev, linked.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("retrieval storage identity changed")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _inventory(outcome: object, run: TrainingRunRef) -> tuple[VerifiedArtifact, ...]:
    if outcome.run != run or outcome.state is not TrainingRunState.SUCCEEDED:
        raise ValueError("run is not verified and successful")
    artifacts = outcome.artifacts
    if type(artifacts) is not tuple or tuple(item.role for item in artifacts) != _ROLES:
        # RunOutcome sorts roles, while the required role tuple is semantic.
        by_role = {item.role: item for item in artifacts}
        if set(by_role) != set(_ROLES) or len(by_role) != len(_ROLES):
            raise ValueError("verified artifact inventory is invalid")
        artifacts = tuple(by_role[role] for role in _ROLES)
    if any(
        type(item) is not VerifiedArtifact
        or _DIGEST.fullmatch(item.sha256) is None
        or type(item.size_bytes) is not int
        or not 0 < item.size_bytes <= _FILE_LIMIT
        for item in artifacts
    ) or sum(item.size_bytes for item in artifacts) > _TOTAL_LIMIT:
        raise ValueError("verified artifact inventory exceeds bounds")
    return artifacts


def _same_inventory(left: tuple[VerifiedArtifact, ...], right: tuple[VerifiedArtifact, ...]) -> bool:
    return tuple(item.to_dict() for item in left) == tuple(item.to_dict() for item in right)


def _write_artifact(run_fd: int, runs: RunsAPI, run: TrainingRunRef,
                    artifact: VerifiedArtifact) -> tuple[int, int]:
    name = _FILENAMES[artifact.role]
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(name, flags, 0o600, dir_fd=run_fd)
    digest = hashlib.sha256()
    size = 0
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError("retrieval artifact is not a private regular file")
        stream = runs.artifacts(RunArtifactRequest(run, artifact.role, _FILE_LIMIT))
        if stream.artifact != artifact:
            raise ValueError("artifact identity changed")
        chunks = stream.iter_bytes()
        if iter(chunks) is not chunks:
            raise ValueError("artifact stream must be an iterator")
        for chunk in chunks:
            if type(chunk) is not bytes or not chunk or len(chunk) > _CHUNK_LIMIT:
                raise ValueError("artifact stream chunk is invalid")
            size += len(chunk)
            if size > artifact.size_bytes or size > _FILE_LIMIT:
                raise ValueError("artifact stream exceeds verified size")
            digest.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(fd, view)
                if type(written) is not int or written <= 0:
                    raise OSError("artifact write made no progress")
                view = view[written:]
        if size != artifact.size_bytes or digest.hexdigest() != artifact.sha256:
            raise ValueError("artifact content does not match verified metadata")
        os.fsync(fd)
        after = os.fstat(fd)
        if (
            after.st_nlink != 1 or after.st_uid != os.geteuid()
            or stat.S_IMODE(after.st_mode) != 0o600
        ):
            raise ValueError("retrieval artifact identity changed")
        identity = (after.st_dev, after.st_ino)
    finally:
        os.close(fd)

    check = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=run_fd)
    try:
        meta = os.fstat(check)
        if (
            not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1
            or meta.st_uid != os.geteuid() or stat.S_IMODE(meta.st_mode) != 0o600
            or meta.st_size != size or (meta.st_dev, meta.st_ino) != identity
        ):
            raise ValueError("retrieval artifact identity changed")
        reread = hashlib.sha256()
        remaining = artifact.size_bytes
        while remaining:
            chunk = os.read(check, min(_CHUNK_LIMIT, remaining))
            if not chunk:
                raise ValueError("retrieval artifact reread failed")
            reread.update(chunk)
            remaining -= len(chunk)
        if os.read(check, 1):
            raise ValueError("retrieval artifact grew during reread")
        final = os.fstat(check)
        if (
            (final.st_dev, final.st_ino) != identity or final.st_nlink != 1
            or final.st_uid != os.geteuid() or stat.S_IMODE(final.st_mode) != 0o600
            or final.st_size != artifact.size_bytes
        ):
            raise ValueError("retrieval artifact identity changed")
        if reread.hexdigest() != artifact.sha256:
            raise ValueError("retrieval artifact reread failed")
    finally:
        os.close(check)
    return identity


def _validate_local_inventory(
    run_fd: int, artifacts: tuple[VerifiedArtifact, ...],
    identities: dict[str, tuple[int, int]],
) -> None:
    if set(os.listdir(run_fd)) != set(_FILENAMES.values()):
        raise ValueError("local retrieval inventory changed")
    for artifact in artifacts:
        name = _FILENAMES[artifact.role]
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=run_fd)
        try:
            before = os.fstat(fd)
            linked = os.stat(name, dir_fd=run_fd, follow_symlinks=False)
            expected = identities[artifact.role]
            if (
                not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_uid != os.geteuid() or stat.S_IMODE(before.st_mode) != 0o600
                or before.st_size != artifact.size_bytes
                or (before.st_dev, before.st_ino) != expected
                or (linked.st_dev, linked.st_ino) != expected
            ):
                raise ValueError("local retrieval artifact identity changed")
            digest = hashlib.sha256()
            remaining = artifact.size_bytes
            while remaining:
                chunk = os.read(fd, min(_CHUNK_LIMIT, remaining))
                if not chunk:
                    raise ValueError("local retrieval artifact is truncated")
                digest.update(chunk)
                remaining -= len(chunk)
            if os.read(fd, 1):
                raise ValueError("local retrieval artifact exceeds verified size")
            after = os.fstat(fd)
            if (
                (after.st_dev, after.st_ino) != expected or after.st_nlink != 1
                or after.st_uid != os.geteuid() or stat.S_IMODE(after.st_mode) != 0o600
                or after.st_size != artifact.size_bytes
                or digest.hexdigest() != artifact.sha256
            ):
                raise ValueError("local retrieval artifact verification failed")
        finally:
            os.close(fd)


def _open_receipt_temp(run_fd: int) -> int:
    try:
        fd = os.open(
            ".", os.O_WRONLY | os.O_TMPFILE | os.O_CLOEXEC, 0o600, dir_fd=run_fd,
        )
    except OSError:
        raise ValueError("atomic receipt storage is unavailable") from None
    if os.fstat(fd).st_nlink != 0:
        os.close(fd)
        raise ValueError("atomic receipt storage is unavailable")
    return fd


def _write_receipt(run_fd: int, fd: int, receipt: dict[str, object]) -> bytes:
    payload = _canonical(receipt) + b"\n"
    view = memoryview(payload)
    while view:
        count = os.write(fd, view)
        if type(count) is not int or count <= 0:
            raise OSError("receipt write made no progress")
        view = view[count:]
    os.fsync(fd)
    if os.fstat(fd).st_nlink != 0:
        raise ValueError("receipt identity changed")
    libc = ctypes.CDLL(None, use_errno=True)
    linkat = libc.linkat
    linkat.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_int)
    linkat.restype = ctypes.c_int
    if linkat(fd, b"", run_fd, b"receipt.json", 0x1000) != 0:  # AT_EMPTY_PATH
        failure = ctypes.get_errno()
        if failure == errno.EEXIST:
            raise ValueError("receipt already exists")
        raise OSError(failure, "receipt publication failed")
    # A failure here can leave a complete receipt. The caller still raises and
    # therefore never reports success for an un-synced directory entry.
    os.fsync(run_fd)
    return payload


def _validate_published_receipt(run_fd: int, retained_fd: int, payload: bytes) -> None:
    expected_names = set(_FILENAMES.values()) | {"receipt.json"}
    if set(os.listdir(run_fd)) != expected_names:
        raise ValueError("completed retrieval inventory changed")
    try:
        fd = os.open(
            "receipt.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=run_fd,
        )
    except OSError:
        raise ValueError("receipt publication identity changed") from None
    try:
        retained = os.fstat(retained_fd)
        before = os.fstat(fd)
        linked = os.stat("receipt.json", dir_fd=run_fd, follow_symlinks=False)
        identity = (retained.st_dev, retained.st_ino)
        if (
            not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or before.st_uid != os.geteuid() or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size != len(payload)
            or (before.st_dev, before.st_ino) != identity
            or (linked.st_dev, linked.st_ino) != identity
        ):
            raise ValueError("receipt publication identity changed")
        remaining = len(payload)
        chunks: list[bytes] = []
        digest = hashlib.sha256()
        while remaining:
            chunk = os.read(fd, min(_CHUNK_LIMIT, remaining))
            if not chunk:
                raise ValueError("published receipt is truncated")
            chunks.append(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            raise ValueError("published receipt exceeds its canonical size")
        after = os.fstat(fd)
        relinked = os.stat("receipt.json", dir_fd=run_fd, follow_symlinks=False)
        if (
            b"".join(chunks) != payload
            or digest.hexdigest() != hashlib.sha256(payload).hexdigest()
            or (after.st_dev, after.st_ino) != identity or after.st_nlink != 1
            or after.st_uid != os.geteuid() or stat.S_IMODE(after.st_mode) != 0o600
            or after.st_size != len(payload)
            or (relinked.st_dev, relinked.st_ino) != identity
        ):
            raise ValueError("published receipt verification failed")
    finally:
        os.close(fd)


def retrieve_verified_artifacts(
    *, project_root: Path, runs: RunsAPI, run: TrainingRunRef,
    plan_fingerprint: str,
) -> dict[str, object]:
    """Retrieve exactly one verified five-file inventory into private Host state."""
    if os.name != "posix" or not isinstance(project_root, Path) or not project_root.is_absolute():
        raise ValueError("Linux absolute project root is required")
    if type(runs) is not RunsAPI or type(run) is not TrainingRunRef:
        raise TypeError("exact RunsAPI and TrainingRunRef are required")
    if _RUN_ID.fullmatch(run.run_id) is None or _DIGEST.fullmatch(plan_fingerprint) is None:
        raise ValueError("retrieval identity is invalid")
    root = project_root.resolve(strict=True)
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    synaptic_fd = retrievals_fd = run_fd = receipt_fd = None
    try:
        verification = runs.reverify(run)
        if verification.run != run or verification.verified is not True:
            raise ValueError("run verification failed")
        baseline = _inventory(runs.show(run), run)

        synaptic_fd = _open_child(root_fd, ".synaptic", create=True)
        retrievals_fd = _open_child(synaptic_fd, "retrievals", create=True)
        run_fd = _open_child(retrievals_fd, run.run_id, create=True, exclusive=True)
        receipt_fd = _open_receipt_temp(run_fd)
        identities: dict[str, tuple[int, int]] = {}
        for artifact in baseline:
            identities[artifact.role] = _write_artifact(run_fd, runs, run, artifact)
            _require_namespace(
                root, root_fd, synaptic_fd, retrievals_fd, run.run_id, run_fd,
            )

        verification = runs.reverify(run)
        final = _inventory(runs.show(run), run)
        if verification.run != run or verification.verified is not True or not _same_inventory(baseline, final):
            raise ValueError("verified artifact inventory changed")
        _require_namespace(
            root, root_fd, synaptic_fd, retrievals_fd, run.run_id, run_fd,
        )
        _validate_local_inventory(run_fd, baseline, identities)
        inventory_value = [item.to_dict() for item in baseline]
        inventory_digest = hashlib.sha256(_canonical(inventory_value)).hexdigest()
        summary: dict[str, object] = {
            "retrieval_root_ref": f"host-private://retrievals/{run.run_id}",
            "artifact_count": len(baseline),
            "inventory_digest": inventory_digest,
            "model_load_verified": False,
        }
        receipt = {
            "schema_version": "synaptic-modal-artifact-receipt/v1",
            "run": run.to_dict(), "plan_fingerprint": plan_fingerprint,
            "inventory": inventory_value, **summary,
        }
        _require_namespace(
            root, root_fd, synaptic_fd, retrievals_fd, run.run_id, run_fd,
        )
        receipt_payload = _write_receipt(run_fd, receipt_fd, receipt)
        _require_namespace(
            root, root_fd, synaptic_fd, retrievals_fd, run.run_id, run_fd,
        )
        os.fsync(run_fd); os.fsync(retrievals_fd); os.fsync(synaptic_fd)
        _require_namespace(
            root, root_fd, synaptic_fd, retrievals_fd, run.run_id, run_fd,
        )
        _validate_published_receipt(run_fd, receipt_fd, receipt_payload)
        return summary
    finally:
        for fd in (receipt_fd, run_fd, retrievals_fd, synaptic_fd, root_fd):
            if fd is not None:
                os.close(fd)


__all__ = ["retrieve_verified_artifacts"]
