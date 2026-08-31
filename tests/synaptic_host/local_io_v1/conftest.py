from __future__ import annotations

import stat
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from synaptic_host.local_io_v1.filesystem import OpenFileV1
from synaptic_host.local_io_v1.model import (
    LocalAdmissionRootNodeV1,
    CreateJournalRecordV1,
    JournalPublishResultV1,
    JournalPublishStatusV1,
    JournalSnapshotStatusV1,
    JournalSnapshotV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    RetainedDirectoryAdmissionV1,
    RetainedDirectoryV1,
    digest_v1,
)


def pytest_addoption(parser) -> None:
    parser.getgroup("b42-local-io").addoption(
        "--b42-ext4-root",
        action="store",
        default=None,
        help="Explicit authorized ext4 root for B4.2a retained-dirfd tests",
    )


def _decode_mount_field(value: str) -> str:
    for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        value = value.replace(encoded, decoded)
    return value


def _verified_ext4_root(value: str) -> Path:
    if os.name != "posix" or type(value) is not str or not value:
        pytest.skip("explicit POSIX ext4 root is required")
    try:
        root = Path(value)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            pytest.fail("B4.2 ext4 root is not an authorized regular directory")
        root = root.resolve(strict=True)
        with Path("/proc/self/mountinfo").open("rb") as stream:
            raw = stream.read(1_048_577)
        if len(raw) > 1_048_576:
            pytest.fail("mountinfo exceeds the B4.2 verification bound")
        lines = raw.decode("utf-8").splitlines()
        if len(lines) > 4096:
            pytest.fail("mountinfo exceeds the B4.2 line bound")
        candidates: list[tuple[int, int, str]] = []
        for line_index, line in enumerate(lines):
            if len(line) > 8192 or " - " not in line:
                continue
            left, right = line.split(" - ", 1)
            fields = left.split()
            post = right.split()
            if len(fields) < 5 or not post:
                continue
            mountpoint = Path(_decode_mount_field(fields[4]))
            try:
                root.relative_to(mountpoint)
            except ValueError:
                continue
            candidates.append((len(mountpoint.parts), line_index, post[0]))
        if not candidates or max(candidates)[2] != "ext4":
            pytest.fail("B4.2 real adapter root must be on an exact ext4 mount")
        return root
    except pytest.fail.Exception:
        raise
    except BaseException:
        pytest.fail("B4.2 ext4 root verification failed closed")


@pytest.fixture
def b42_ext4_root(request):
    configured = request.config.getoption("--b42-ext4-root")
    if configured is None:
        pytest.skip("pass --b42-ext4-root from the canonical WSL ext4 checkout")
    authorized = _verified_ext4_root(configured)
    created = Path(tempfile.mkdtemp(prefix="b42-local-io-", dir=authorized))
    try:
        yield created
    finally:
        shutil.rmtree(created)


@dataclass
class _Node:
    inode: int
    mode: int
    content: bytearray = field(default_factory=bytearray)
    nlink: int = 1
    changed_ns: int = 1
    modified_ns: int = 1
    directory_handle: str | None = None

    def identity(self) -> LocalFileIdentityV1:
        return LocalFileIdentityV1(
            device=1,
            inode=self.inode,
            mode=self.mode,
            nlink=self.nlink,
            changed_ns=self.changed_ns,
            modified_ns=self.modified_ns,
            size=len(self.content),
        )


class FakePosixFilesystemPortV1:
    """Deterministic retained-handle fake; no host filesystem effects."""

    def __init__(self) -> None:
        self.trace: list[str] = []
        self._next_inode = 10
        self._next_handle = 1
        self.roots: dict[str, str] = {}
        self.directories: dict[str, dict[str, _Node]] = {}
        self.directory_nodes: dict[str, _Node] = {}
        self.files: dict[str, tuple[_Node, int]] = {}
        self.live_directories: dict[str, RetainedDirectoryV1] = {}
        self.live_files: dict[str, OpenFileV1] = {}
        self.journals: dict[str, list[CreateJournalRecordV1]] = {}
        self.private_journals: set[str] = set()
        self.fail_before: dict[str, int] = {}
        self.lose_after: dict[str, int] = {}
        self.callbacks: dict[str, object] = {}
        self.calls: dict[str, int] = {}
        self.admission_leases: dict[str, tuple[RetainedDirectoryAdmissionV1, str]] = {}
        self.admission_process_ref = "fake-process-instance"

    def _event(self, name: str) -> None:
        self.trace.append(name)
        count = self.calls.get(name, 0) + 1
        self.calls[name] = count
        if self.fail_before.get(name) == count:
            raise RuntimeError("SENTINEL raw fake failure")

    def _after(self, name: str) -> None:
        callback = self.callbacks.pop(name, None)
        if callback is not None:
            callback()
        if self.lose_after.get(name) == self.calls[name]:
            raise RuntimeError("SENTINEL lost return")

    def _directory(self, directory: RetainedDirectoryV1) -> str:
        if type(directory) is not RetainedDirectoryV1 or self.live_directories.get(directory.handle_ref) is not directory:
            raise RuntimeError("SENTINEL forged directory")
        return directory.handle_ref

    def _file(self, file: OpenFileV1) -> str:
        if type(file) is not OpenFileV1 or self.live_files.get(file.handle_ref) is not file:
            raise RuntimeError("SENTINEL forged file")
        return file.handle_ref

    def _new_inode(self, mode: int, payload: bytes = b"") -> _Node:
        self._next_inode += 1
        return _Node(self._next_inode, mode, bytearray(payload))

    def _touch_directory(self, handle: str, *, link_delta: int = 0) -> None:
        node = self.directory_nodes[handle]
        node.nlink += link_delta
        node.changed_ns += 1
        node.modified_ns += 1
        node.content = bytearray(len(self.directories[handle]))

    def add_root(self, path: Path, label: str) -> None:
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("absolute fake root required")
        handle = f"dir-{label}"
        node = self._new_inode(stat.S_IFDIR | 0o700)
        node.directory_handle = handle
        self.roots[str(path)] = handle
        self.directories[handle] = {}
        self.directory_nodes[handle] = node

    def add_directory(self, directory: str, name: str) -> str:
        handle = f"dir-{self._next_inode + 1}"
        node = self._new_inode(stat.S_IFDIR | 0o700)
        node.directory_handle = handle
        self.directories[directory][name] = node
        self.directories[handle] = {}
        self.directory_nodes[handle] = node
        self._touch_directory(directory, link_delta=1)
        return handle

    def add_file(
        self,
        directory: str,
        name: str,
        payload: bytes,
        *,
        mode: int = stat.S_IFREG | 0o600,
        nlink: int = 1,
    ) -> _Node:
        node = self._new_inode(mode, payload)
        node.nlink = nlink
        self.directories[directory][name] = node
        self._touch_directory(directory)
        return node

    def retain_directory(self, absolute_path: Path) -> RetainedDirectoryV1:
        self._event("retain_directory")
        base = self.roots[str(absolute_path)]
        handle = base
        if handle in self.live_directories:
            handle = f"{base}-retained-{self._next_handle}"
            self._next_handle += 1
            self.directories[handle] = self.directories[base]
            self.directory_nodes[handle] = self.directory_nodes[base]
        result = RetainedDirectoryV1(handle, self.directory_nodes[handle].identity())
        self.live_directories[handle] = result
        self._after("retain_directory")
        return result

    def open_directory_at(self, directory, component):
        self._event("open_directory_at")
        node = self.directories[self._directory(directory)][component]
        result = RetainedDirectoryV1(node.directory_handle, node.identity())
        self.live_directories[result.handle_ref] = result
        self._after("open_directory_at")
        return result

    def close_directory(self, directory):
        self._event("close_directory")
        del self.live_directories[self._directory(directory)]
        self._after("close_directory")

    def list_names_at(self, directory, maximum):
        self._event("list_names_at")
        names: list[str] = []
        for name in self.directories[self._directory(directory)]:
            names.append(name)
            if len(names) > maximum:
                break
        result = tuple(names)
        self._after("list_names_at")
        return result

    def stat_at(self, directory, component):
        self._event(f"stat_at:{component}")
        node = self.directories[self._directory(directory)].get(component)
        result = None if node is None else node.identity()
        self._after(f"stat_at:{component}")
        return result

    def _opened(self, node: _Node) -> OpenFileV1:
        handle = f"file-{self._next_handle}"
        self._next_handle += 1
        self.files[handle] = (node, 0)
        result = OpenFileV1(handle, node.identity())
        self.live_files[handle] = result
        return result

    def open_read_at(self, directory, component):
        self._event("open_read_at")
        result = self._opened(self.directories[self._directory(directory)][component])
        self._after("open_read_at")
        return result

    def create_exclusive_at(self, directory, component):
        self._event("create_exclusive_at")
        entries = self.directories[self._directory(directory)]
        if component in entries:
            raise FileExistsError(component)
        node = self._new_inode(stat.S_IFREG | 0o600)
        entries[component] = node
        self._touch_directory(self._directory(directory))
        result = self._opened(node)
        self._after("create_exclusive_at")
        return result

    def read(self, file, maximum):
        self._event("read")
        handle = self._file(file)
        node, offset = self.files[handle]
        payload = bytes(node.content[offset : offset + maximum])
        self.files[handle] = (node, offset + len(payload))
        self._after("read")
        return payload

    def write(self, file, payload):
        self._event("write")
        handle = self._file(file)
        node, offset = self.files[handle]
        node.content[offset:offset] = payload
        node.changed_ns += 1
        node.modified_ns += 1
        self.files[handle] = (node, offset + len(payload))
        self._after("write")
        return len(payload)

    def mkdir_at(self, directory, component):
        self._event("mkdir_at")
        handle = self._directory(directory)
        if component in self.directories[handle]:
            result = False
        else:
            self.add_directory(handle, component)
            result = True
        self._after("mkdir_at")
        return result

    def stat_file(self, file):
        self._event("stat_file")
        result = self.files[self._file(file)][0].identity()
        self._after("stat_file")
        return result

    def close_file(self, file):
        self._event("close_file")
        del self.live_files[self._file(file)]
        self._after("close_file")

    def fsync_file(self, file):
        self._event("fsync_file")
        self._file(file)
        self._after("fsync_file")

    def fsync_directory(self, directory):
        self._directory(directory)
        label = "control" if directory.handle_ref.startswith("dir-control") else "data"
        self._event(f"fsync_directory:{label}")
        self._after(f"fsync_directory:{label}")

    def link_at(self, directory, source, destination):
        self._event("link_at")
        entries = self.directories[self._directory(directory)]
        if destination in entries:
            raise FileExistsError(destination)
        node = entries[source]
        node.nlink += 1
        node.changed_ns += 1
        entries[destination] = node
        self._touch_directory(self._directory(directory))
        self._after("link_at")

    def unlink_at(self, directory, component):
        self._event("unlink_at")
        node = self.directories[self._directory(directory)].pop(component)
        node.nlink -= 1
        node.changed_ns += 1
        self._touch_directory(self._directory(directory))
        self._after("unlink_at")

    def acquire_directory_admission(self, directory):
        handle = self._directory(directory)
        self._event("acquire_directory_admission")
        if self.admission_leases:
            raise LocalIOErrorV1(LocalIOCodeV1.ROOT_IN_USE)
        identity = self.directory_nodes[handle].identity()
        node_body = {"device": identity.device, "file_type": stat.S_IFDIR,
                     "inode": identity.inode,
                     "schema": "synaptic-host-admission-root-node/v1"}
        root_node = LocalAdmissionRootNodeV1(
            identity.device, identity.inode, stat.S_IFDIR, digest_v1(node_body)
        )
        lease_ref = f"fake-admission-{len(self.calls)}"
        body = {
            "lease_ref": lease_ref,
            "root_node_digest": root_node.node_digest,
            "process_id": os.getpid(),
            "process_instance_ref": self.admission_process_ref,
            "schema": "synaptic-host-retained-directory-admission/v1",
        }
        lease = RetainedDirectoryAdmissionV1(
            lease_ref, root_node, os.getpid(), self.admission_process_ref,
            digest_v1(body),
        )
        self.admission_leases[lease_ref] = (lease, handle)
        return lease

    def validate_directory_admission(self, directory, lease):
        handle = self._directory(directory)
        state = self.admission_leases.get(getattr(lease, "lease_ref", None))
        if state is None or state[0] is not lease or state[1] != handle or lease.process_id != os.getpid():
            raise LocalIOErrorV1(LocalIOCodeV1.ADMISSION_INVALID)
        return lease

    def release_directory_admission(self, directory, lease):
        self.validate_directory_admission(directory, lease)
        del self.admission_leases[lease.lease_ref]
        self._event("release_directory_admission")

    def publish_journal(self, control, mutation_id, expected_previous_digest, record):
        control_handle = self._directory(control)
        self._event(f"append_journal:{record.phase.value}")
        if mutation_id in self.private_journals:
            return JournalPublishResultV1(
                JournalPublishStatusV1.CONFLICT, mutation_id, record.record_digest, record
            )
        new_journal = mutation_id not in self.journals
        records = self.journals.setdefault(mutation_id, [])
        actual = None if not records else records[-1].record_digest
        if actual != expected_previous_digest or len(records) != record.sequence:
            status = (
                JournalPublishStatusV1.EXISTS_IDENTICAL
                if record.sequence < len(records) and records[record.sequence] == record
                else JournalPublishStatusV1.CONFLICT
            )
            self._after(f"append_journal:{record.phase.value}")
            return JournalPublishResultV1(status, mutation_id, record.record_digest, record)
        if new_journal:
            self._touch_directory(control_handle, link_delta=1)
            self._event("journal_control_fsync")
            self._after("journal_control_fsync")
        for event in ("journal_temp_create", "journal_temp_write", "journal_temp_fsync"):
            self._event(event)
            if event == "journal_temp_create":
                self.private_journals.add(mutation_id)
            self._after(event)
        self._event("journal_link")
        records.append(record)
        self._after("journal_link")
        for event in ("journal_directory_fsync", "journal_temp_unlink", "journal_directory_fsync", "journal_reopen"):
            self._event(event)
            if event == "journal_temp_unlink":
                self.private_journals.discard(mutation_id)
            self._after(event)
        self._after(f"append_journal:{record.phase.value}")
        return JournalPublishResultV1(
            JournalPublishStatusV1.PUBLISHED, mutation_id, record.record_digest, record
        )

    def snapshot_journal(self, control, mutation_id, maximum):
        self._directory(control)
        self._event("read_journal")
        records = tuple(self.journals.get(mutation_id, ()))
        self._after("read_journal")
        status = (
            JournalSnapshotStatusV1.INDETERMINATE
            if mutation_id in self.private_journals or (mutation_id in self.journals and not records)
            else (JournalSnapshotStatusV1.FOUND if records else JournalSnapshotStatusV1.ABSENT)
        )
        if status is JournalSnapshotStatusV1.INDETERMINATE:
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
