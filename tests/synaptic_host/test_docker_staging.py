from __future__ import annotations

import hashlib
import inspect
import json
import os
import stat
import subprocess
from pathlib import Path
from pathlib import PurePosixPath
from types import SimpleNamespace

import pytest

from synaptic_host.docker_staging import (
    DockerModelInventoryEntryV1,
    _CLOSURE_MANIFEST_SOURCE_PATH,
    _capture_windows_stage_cleanup,
    _cleanup_unpromoted_stage,
    _cleanup_windows_stage,
    _copy_inventory,
    _load_locked_closure,
    _release_windows_stage,
    _source_manifest,
    _stage_locked_closure,
    _stage_locked_project_inputs,
    _verify_artifact_topology,
    _verify_inventory_at,
    _verify_worker_closure_binding,
    _verify_staged_closure,
    stage_docker_worker_v1,
)


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"
ENGINE_COMMIT = subprocess.run(
    ("git", "-C", str(ROOT), "rev-parse", "HEAD:synaptic-tuner"),
    check=True,
    capture_output=True,
    text=True,
    timeout=30,
).stdout.strip()


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_replay_cleans_readonly_temporary_not_durable_stage(
    tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    durable = stage_parent / ("a" * 64)
    durable.mkdir()
    durable_file = durable / "source-lock.json"
    durable_file.write_bytes(b"durable")
    temporary = stage_parent / "stage-replay"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    nested = temporary / "source" / "control"
    nested.mkdir(parents=True)
    readonly = nested / "source-lock.json"
    readonly.write_bytes(b"temporary")
    readonly.chmod(stat.S_IREAD)

    _cleanup_unpromoted_stage(temporary, cleanup)

    assert not temporary.exists()
    assert durable_file.read_bytes() == b"durable"


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_cleanup_rejects_replaced_root_during_authority_transition(
    tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-owned"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    (temporary / "owned.txt").write_bytes(b"owned")
    original = stage_parent / "captured-original"
    temporary.rename(original)
    temporary.mkdir()
    replacement = temporary / "replacement.txt"
    replacement.write_bytes(b"replacement")

    with pytest.raises(ValueError, match="transition changed authority"):
        _cleanup_windows_stage(cleanup)

    assert replacement.read_bytes() == b"replacement"
    assert (original / "owned.txt").read_bytes() == b"owned"


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_cleanup_blocks_post_inventory_rename_out_and_abort_preserves_tree(
    monkeypatch, tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-redirect"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    nested = temporary / "nested"
    nested.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    owned = nested / "owned.txt"
    owned.write_bytes(b"owned")
    escaped = external / "escaped"
    module_globals = _cleanup_windows_stage.__globals__

    def abort_after_blocked_rename(_captured, _entries):
        with pytest.raises(PermissionError) as blocked:
            nested.rename(escaped)
        assert blocked.value.winerror == 32
        raise RuntimeError("abort after sharing violation")

    monkeypatch.setitem(
        module_globals, "_windows_delete_inventory", abort_after_blocked_rename
    )
    with pytest.raises(RuntimeError, match="sharing violation"):
        _cleanup_windows_stage(cleanup)

    assert owned.read_bytes() == b"owned"
    assert tuple(external.iterdir()) == ()


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_cleanup_blocks_post_inventory_rename_out_then_continues(
    monkeypatch, tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-continue"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    nested = temporary / "nested"
    nested.mkdir()
    (nested / "owned.txt").write_bytes(b"owned")
    external = tmp_path / "external"
    external.mkdir()
    escaped = external / "escaped"
    module_globals = _cleanup_windows_stage.__globals__
    original_delete = module_globals["_windows_delete_inventory"]

    def continue_after_blocked_rename(captured, entries):
        with pytest.raises(PermissionError) as blocked:
            nested.rename(escaped)
        assert blocked.value.winerror == 32
        return original_delete(captured, entries)

    monkeypatch.setitem(
        module_globals, "_windows_delete_inventory", continue_after_blocked_rename
    )
    _cleanup_windows_stage(cleanup)

    assert not temporary.exists()
    assert tuple(external.iterdir()) == ()


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_location_mismatch_fails_before_any_mutation(
    monkeypatch, tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-location"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    target = temporary / "readonly.txt"
    target.write_bytes(b"before")
    target.chmod(stat.S_IREAD)
    module_globals = _cleanup_windows_stage.__globals__
    original_delete = module_globals["_windows_delete_inventory"]
    original_location = module_globals["_windows_handle_location"]

    def mismatch_before_delete(captured, entries):
        monkeypatch.setitem(
            module_globals,
            "_windows_handle_location",
            lambda handle: original_location(handle) + "-mismatch"
        )
        return original_delete(captured, entries)

    monkeypatch.setitem(
        module_globals, "_windows_delete_inventory", mismatch_before_delete
    )
    with pytest.raises(ValueError, match="location or identity"):
        _cleanup_windows_stage(cleanup)

    assert target.read_bytes() == b"before"
    assert target.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_cleanup_never_touches_stage_sibling(tmp_path: Path) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-owned"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    (temporary / "owned.txt").write_bytes(b"owned")
    sibling = stage_parent / "stage-sibling"
    sibling.mkdir()
    sibling_file = sibling / "keep.txt"
    sibling_file.write_bytes(b"keep")

    _cleanup_windows_stage(cleanup)

    assert not temporary.exists()
    assert sibling_file.read_bytes() == b"keep"


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_cleanup_rejects_post_inventory_file_drift(
    monkeypatch, tmp_path: Path,
) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-drift"
    temporary.mkdir()
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)
    target = temporary / "file.txt"
    target.write_bytes(b"before")
    module_globals = _cleanup_windows_stage.__globals__
    original_delete = module_globals["_windows_delete_inventory"]

    def drift_after_inventory(captured, entries):
        file_entry = next(entry for entry in entries if not entry.metadata.is_directory)
        basic = module_globals["_windows_basic_info"](file_entry.handle)
        basic.FileAttributes |= 0x00000002
        kernel32, _ = module_globals["_windows_native"]()
        assert kernel32.SetFileInformationByHandle(
            module_globals["ctypes"].c_void_p(file_entry.handle),
            module_globals["_FILE_BASIC_INFO_CLASS"],
            module_globals["ctypes"].byref(basic),
            module_globals["ctypes"].sizeof(basic),
        )
        return original_delete(captured, entries)

    monkeypatch.setitem(
        module_globals, "_windows_delete_inventory", drift_after_inventory
    )
    with pytest.raises(ValueError, match="location or identity"):
        _cleanup_windows_stage(cleanup)

    assert target.read_bytes() == b"before"


@pytest.mark.skipif(os.name != "nt", reason="Windows cleanup policy")
def test_windows_promotion_releases_handles_without_deletion(tmp_path: Path) -> None:
    stage_parent = tmp_path / "stages"
    stage_parent.mkdir()
    temporary = stage_parent / "stage-promoted"
    temporary.mkdir()
    target = temporary / "keep.txt"
    target.write_bytes(b"keep")
    cleanup = _capture_windows_stage_cleanup(stage_parent, temporary)

    _release_windows_stage(cleanup)

    assert cleanup.released is True
    assert target.read_bytes() == b"keep"


def test_non_windows_cleanup_keeps_direct_rmtree_behavior(tmp_path: Path) -> None:
    temporary = tmp_path / "stage-posix-policy"
    temporary.mkdir()
    (temporary / "file.txt").write_bytes(b"content")

    _cleanup_unpromoted_stage(temporary, None)

    assert not temporary.exists()


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


# B-12 (architecture section 21.12).  `_git_archive` and `_extract_link_free`
# are gone with the whole-superproject stage they served.  The two tests that
# covered them are retired by the lead's ruling on task #187: S5 below
# re-expresses "staging reads the commit, never the worktree" on the path that
# now stages, and S7 re-expresses the link refusal, which is now
# `_git_selected_blobs` refusing a member that is not a regular blob at the
# locked commit rather than a tar extractor refusing a SYMTYPE entry.


def _descriptor(kind: str, path: str, payload: bytes) -> dict[str, object]:
    """One `source_lock.inputs` entry, in the shape `docker_training._descriptor`
    writes it (docker_training.py:104-116)."""

    return {
        "kind": kind,
        "ref": "project://" + path,
        "path": path,
        "git_object_id": "0" * 40,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


@pytest.fixture
def locked_inputs_repository(tmp_path: Path):
    """A repository holding the two project inputs a source lock records."""

    repository = tmp_path / "repository"
    (repository / "training/smokes").mkdir(parents=True)
    (repository / "training/fixtures").mkdir(parents=True)
    config = b'{"method": "sft"}\n'
    dataset = b'{"messages": []}\n'
    (repository / "training/smokes/docker-sft.json").write_bytes(config)
    (repository / "training/fixtures/modal-smoke.jsonl").write_bytes(dataset)
    # Bulk content the lock does not record.  Small here: S1 in
    # tests/synaptic_host/test_docker_training.py carries the real bound.
    (repository / "datasets").mkdir()
    (repository / "datasets/corpus.bin").write_bytes(b"unstaged" * 64)
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.email", "staging@example.invalid")
    _git(repository, "config", "user.name", "Staging Test")
    _git(repository, "add", "-A")
    _git(repository, "commit", "-m", "fixture")
    commit = _git(repository, "rev-parse", "HEAD")
    descriptors = (
        _descriptor(
            "training-config", "training/smokes/docker-sft.json", config,
        ),
        _descriptor(
            "training-dataset", "training/fixtures/modal-smoke.jsonl", dataset,
        ),
    )
    return SimpleNamespace(
        path=repository,
        commit=commit,
        descriptors=descriptors,
        config=config,
        dataset=dataset,
    )


def test_staged_project_inputs_are_exactly_the_locked_set(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14 test S2), at the helper rather than through a run."""

    destination = tmp_path / "project"
    _stage_locked_project_inputs(
        locked_inputs_repository.path,
        locked_inputs_repository.commit,
        locked_inputs_repository.descriptors,
        destination,
    )

    assert {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*") if path.is_file()
    } == {
        descriptor["path"]
        for descriptor in locked_inputs_repository.descriptors
    }
    assert not (destination / "datasets").exists()


def test_staged_project_input_digest_mismatch_is_refused_before_any_write(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14 test S3).

    The digest is compared to the blob at the commit before the destination
    exists, so a refusal leaves nothing staged.  Asserting the destination is
    absent is what distinguishes "checked before the write" from "checked
    after"; a check that ran afterwards would pass the message assertion.
    """

    config, dataset = locked_inputs_repository.descriptors
    tampered = dict(dataset)
    tampered["sha256"] = hashlib.sha256(b"other").hexdigest()
    destination = tmp_path / "project"

    with pytest.raises(ValueError, match="differs from its locked digest"):
        _stage_locked_project_inputs(
            locked_inputs_repository.path,
            locked_inputs_repository.commit,
            (config, tampered),
            destination,
        )

    assert not destination.exists()


def test_staged_project_input_size_and_empty_read_have_distinct_messages(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14 test S4), the section 21.8 split.

    Two predicates, two messages.  The empty case is a committed zero-byte
    input whose descriptor records the truth about it, so only the emptiness
    predicate can fire; recording a wrong size instead would have reported the
    size message and left the empty branch unmeasured.
    """

    config, dataset = locked_inputs_repository.descriptors
    resized = dict(dataset)
    resized["size_bytes"] = dataset["size_bytes"] + 1
    with pytest.raises(ValueError, match="differs from its locked size"):
        _stage_locked_project_inputs(
            locked_inputs_repository.path,
            locked_inputs_repository.commit,
            (config, resized),
            tmp_path / "resized",
        )

    empty_path = "training/fixtures/empty.jsonl"
    locked_inputs_repository.path.joinpath(empty_path).write_bytes(b"")
    _git(locked_inputs_repository.path, "add", "-A")
    _git(locked_inputs_repository.path, "commit", "-m", "empty input")
    commit = _git(locked_inputs_repository.path, "rev-parse", "HEAD")
    empty = _descriptor("training-dataset", empty_path, b"")
    assert empty["size_bytes"] == 0

    with pytest.raises(ValueError, match="is empty"):
        _stage_locked_project_inputs(
            locked_inputs_repository.path, commit, (config, empty),
            tmp_path / "empty",
        )


def test_staged_project_input_reads_the_commit_not_the_dirty_worktree(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14 test S5).

    Dirty the checkout at the dataset path first.  The staged bytes must equal
    the blob at the locked commit, which the recorded digest also asserts, so
    the equality is stated against `git show` rather than against the constant
    the fixture happens to hold.
    """

    dataset_path = "training/fixtures/modal-smoke.jsonl"
    locked_inputs_repository.path.joinpath(dataset_path).write_bytes(
        b'{"messages": ["uncommitted"]}\n'
    )
    destination = tmp_path / "project"

    _stage_locked_project_inputs(
        locked_inputs_repository.path,
        locked_inputs_repository.commit,
        locked_inputs_repository.descriptors,
        destination,
    )

    committed = subprocess.run(
        (
            "git", "-C", str(locked_inputs_repository.path), "show",
            f"{locked_inputs_repository.commit}:{dataset_path}",
        ),
        check=True, capture_output=True, timeout=30,
    ).stdout
    staged = destination.joinpath(*PurePosixPath(dataset_path).parts)
    assert staged.read_bytes() == committed
    assert staged.read_bytes() != locked_inputs_repository.path.joinpath(
        dataset_path
    ).read_bytes()


def test_staging_the_same_locked_inputs_twice_gives_one_manifest_digest(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14 test S6), the pin section 21.4 names.

    The risk the ruling engineers against is a scope that is not covered by a
    digest, which would let two runs at the same lock stage different trees and
    report success both times.  `_source_manifest` walks what was staged, so
    equality of its digest across two stages is what makes the scope itself
    part of the recorded identity.
    """

    digests = []
    for index in range(2):
        destination = tmp_path / f"project-{index}"
        _stage_locked_project_inputs(
            locked_inputs_repository.path,
            locked_inputs_repository.commit,
            locked_inputs_repository.descriptors,
            destination,
        )
        _entries, digest = _source_manifest(destination)
        digests.append(digest)

    assert digests[0] == digests[1]
    # Counter-test the equality: the digest is a function of what was staged,
    # not a constant. A tree with one more file must digest differently, or the
    # assertion above would hold for a manifest that measured nothing.
    other = tmp_path / "project-other"
    _stage_locked_project_inputs(
        locked_inputs_repository.path,
        locked_inputs_repository.commit,
        locked_inputs_repository.descriptors,
        other,
    )
    other.joinpath("extra.txt").write_bytes(b"extra\n")
    assert _source_manifest(other)[1] != digests[0]


def test_staged_project_input_that_is_a_symlink_at_the_commit_is_refused(
    tmp_path: Path, locked_inputs_repository,
) -> None:
    """B-12 (section 21.14, the link property ported from the retired
    `test_link_free_extraction_rejects_symlinks` by the lead's ruling on #187).

    A descriptor naming a path that is not a regular blob at the locked commit
    is refused by `_git_selected_blobs`, before anything is written.  Committed
    with `git update-index` so the property holds on a host whose filesystem
    will not create a symlink.
    """

    link_path = "training/fixtures/redirect.jsonl"
    blob = subprocess.run(
        (
            "git", "-C", str(locked_inputs_repository.path),
            "hash-object", "-w", "--stdin",
        ),
        input=b"../../../outside", check=True, capture_output=True, timeout=30,
    ).stdout.decode("ascii").strip()
    _git(
        locked_inputs_repository.path, "update-index", "--add",
        "--cacheinfo", f"120000,{blob},{link_path}",
    )
    _git(locked_inputs_repository.path, "commit", "-m", "symlink input")
    commit = _git(locked_inputs_repository.path, "rev-parse", "HEAD")
    assert _git(
        locked_inputs_repository.path, "ls-tree", commit, "--", link_path,
    ).split()[0] == "120000"
    descriptor = _descriptor("training-dataset", link_path, b"../../../outside")
    destination = tmp_path / "project"

    with pytest.raises(ValueError, match="invalid member"):
        _stage_locked_project_inputs(
            locked_inputs_repository.path, commit,
            (locked_inputs_repository.descriptors[0], descriptor),
            destination,
        )

    assert not destination.exists()


def test_model_inventory_is_explicit_sorted_and_content_authenticated(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    entries = tuple(
        DockerModelInventoryEntryV1(
            relative,
            source,
            len(source.read_bytes()),
            hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        for relative, source in (
            ("model/models--org--name/snapshots/" + "1" * 40 + "/a.bin", first),
            ("model/models--org--name/snapshots/" + "1" * 40 + "/b.bin", second),
        )
    )
    destination = tmp_path / "stage"
    destination.mkdir()
    digest = _copy_inventory(entries, destination)
    assert len(digest) == 64
    assert destination.joinpath(*entries[0].relative_path.split("/")).read_bytes() == b"first"
    _, before = _source_manifest(destination)
    staged = destination.joinpath(*entries[0].relative_path.split("/"))
    staged.chmod(0o644)
    staged.write_bytes(b"changed")
    _, after = _source_manifest(destination)
    assert before != after


def test_model_inventory_rejects_descriptor_drift(tmp_path: Path) -> None:
    source = tmp_path / "model.bin"
    source.write_bytes(b"model")
    entry = DockerModelInventoryEntryV1(
        "model/file.bin", source, 5, hashlib.sha256(b"model").hexdigest()
    )
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="differs from its descriptor"):
        _copy_inventory((entry,), tmp_path / "stage")


def test_locked_worker_closure_stages_only_declared_commit_blobs(
    tmp_path: Path,
) -> None:
    closure = _load_locked_closure(ENGINE, ENGINE_COMMIT)
    destination = tmp_path / "engine"

    _stage_locked_closure(closure, destination)

    observed = tuple(sorted(
        path.relative_to(destination).as_posix()
        for path in sorted(destination.rglob("*"))
        if path.is_file()
    ))
    manifest = json.loads(closure.manifest_bytes)
    assert observed == tuple(sorted(member.path for member in closure.members))
    assert len(observed) == manifest["member_count"]
    assert closure.payload_bytes == manifest["payload_bytes"]
    assert closure.closure_digest == manifest["closure_digest"]
    assert not destination.joinpath(_CLOSURE_MANIFEST_SOURCE_PATH).exists()
    assert not destination.joinpath(".gitignore").exists()


def test_locked_worker_closure_rejects_declared_member_metadata_drift(
    monkeypatch,
) -> None:
    module_globals = _load_locked_closure.__globals__
    original = module_globals["_git_selected_blobs"]

    def changed(repository: Path, commit: str, paths: tuple[str, ...]):
        selected = original(repository, commit, paths)
        mode, payload = selected["Trainers/sft/runtime_v1.py"]
        selected["Trainers/sft/runtime_v1.py"] = (mode, payload + b"changed")
        return selected

    monkeypatch.setitem(module_globals, "_git_selected_blobs", changed)
    with pytest.raises(ValueError, match="differs from its declaration"):
        _load_locked_closure(ENGINE, ENGINE_COMMIT)


def test_staged_worker_closure_rejects_extra_output(tmp_path: Path) -> None:
    closure = _load_locked_closure(ENGINE, ENGINE_COMMIT)
    destination = tmp_path / "engine"
    _stage_locked_closure(closure, destination)
    (destination / "extra.py").write_bytes(b"extra")

    with pytest.raises(ValueError, match="missing or extra"):
        _verify_staged_closure(destination, closure)


def test_inventory_verification_rejects_extra_cache_files(tmp_path: Path) -> None:
    source = tmp_path / "model.bin"
    source.write_bytes(b"model")
    entry = DockerModelInventoryEntryV1(
        "model/file.bin", source, 5, hashlib.sha256(b"model").hexdigest()
    )
    destination = tmp_path / "cache"
    destination.mkdir()
    _copy_inventory((entry,), destination)
    (destination / "extra.bin").write_bytes(b"extra")
    with pytest.raises(ValueError, match="missing or extra"):
        _verify_inventory_at((entry,), destination)


def test_inventory_copy_rejects_redirected_destination_parent(
    tmp_path: Path,
) -> None:
    source = tmp_path / "model.bin"
    source.write_bytes(b"model")
    entry = DockerModelInventoryEntryV1(
        "redirect/file.bin", source, 5, hashlib.sha256(b"model").hexdigest()
    )
    destination = tmp_path / "cache"
    destination.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (destination / "redirect").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")
    with pytest.raises(ValueError, match="redirect"):
        _copy_inventory((entry,), destination)
    assert not (outside / "file.bin").exists()


def test_inventory_copy_rejects_reparse_destination_parent(
    monkeypatch, tmp_path: Path,
) -> None:
    source = tmp_path / "model.bin"
    source.write_bytes(b"model")
    entry = DockerModelInventoryEntryV1(
        "nested/file.bin", source, 5, hashlib.sha256(b"model").hexdigest()
    )
    module_globals = _copy_inventory.__globals__
    original = module_globals["_is_reparse"]

    def mark_directories(info):
        return original(info) or bool(info.st_mode & 0o040000)

    monkeypatch.setitem(module_globals, "_is_reparse", mark_directories)
    (tmp_path / "cache").mkdir()
    with pytest.raises(ValueError, match="redirect"):
        _copy_inventory((entry,), tmp_path / "cache")


def test_staged_closure_applies_platform_mode_policy(tmp_path: Path) -> None:
    closure = _load_locked_closure(ENGINE, ENGINE_COMMIT)
    destination = tmp_path / "engine"
    _stage_locked_closure(closure, destination)
    if os.name != "nt":
        for member in closure.members:
            mode = destination.joinpath(*member.path.split("/")).stat().st_mode
            expected = 0o755 if member.git_mode == "100755" else 0o644
            assert mode & 0o777 == expected


def test_locked_loader_accepts_alternate_non_66_semantic_manifest(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "alternate"
    repository.mkdir()
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.email", "closure@example.invalid")
    _git(repository, "config", "user.name", "Closure Test")
    payloads = {
        "alternate/runner.py": b"print('runner')\n",
        "alternate/trainer.py": b"print('trainer')\n",
    }
    members = []
    for path, payload in sorted(payloads.items()):
        target = repository.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        members.append({
            "git_mode": "100644",
            "path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        })
    document = {
        "schema_version": "synaptic-offline-sft-worker-closure/v1",
        "closure_ref": "alternate/closure/v9",
        "entrypoint": "alternate/runner.py",
        "trainer_entrypoint": "alternate/trainer.py",
        "owned_module_prefixes": ["alternate"],
        "optional_features": ["feature-v2"],
        "member_count": len(members),
        "payload_bytes": sum(item["size_bytes"] for item in members),
        "members": members,
    }
    canonical = lambda value: json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    document["closure_digest"] = hashlib.sha256(canonical(document)).hexdigest()
    manifest = repository / _CLOSURE_MANIFEST_SOURCE_PATH
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(canonical(document) + b"\n")
    _git(repository, "add", "-A")
    _git(repository, "commit", "-m", "alternate closure")
    commit = _git(repository, "rev-parse", "HEAD")

    closure = _load_locked_closure(repository, commit)

    assert len(closure.members) == 2
    assert closure.closure_ref == "alternate/closure/v9"
    assert closure.entrypoint == "alternate/runner.py"
    assert closure.trainer_entrypoint == "alternate/trainer.py"
    assert closure.owned_module_prefixes == ("alternate",)
    assert closure.optional_features == ("feature-v2",)


def _empty_artifact_topology(root: Path) -> None:
    root.mkdir()
    for name in ("artifacts", "cache", "state", "tmp", "tracking"):
        (root / name).mkdir()


def test_artifact_topology_requires_exact_empty_writable_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    _verify_artifact_topology(root, (), expect_unused_artifacts=True)

    (root / "state" / "unexpected.json").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="not empty"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=True)


def test_artifact_topology_rejects_extra_root_and_cache_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "extra").mkdir()
    with pytest.raises(ValueError, match="incomplete or extended"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=True)
    (root / "extra").rmdir()
    (root / "cache" / "extra-empty").mkdir()
    with pytest.raises(ValueError, match="extra directories"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=True)


def test_artifact_topology_rejects_special_slot_and_reparse_root(
    monkeypatch, tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "tracking").rmdir()
    (root / "tracking").write_bytes(b"not-a-directory")
    with pytest.raises(ValueError, match="invalid entry"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=True)

    (root / "tracking").unlink()
    (root / "tracking").mkdir()
    module_globals = _verify_artifact_topology.__globals__
    monkeypatch.setitem(module_globals, "_is_reparse", lambda _info: True)
    with pytest.raises(ValueError, match="redirected or invalid"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=True)


def test_artifact_topology_admits_written_writable_roots_after_the_run_started(
    tmp_path: Path,
) -> None:
    # B-10 (architecture section 19.13 test 1): the post-run cut. Once the run
    # has started, content under the writable roots is expected, and the caller
    # says so by passing False.
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "state" / "trainer-state.json").write_bytes(b"{}")
    (root / "artifacts" / "adapter").mkdir()
    (root / "tmp" / "scratch").write_bytes(b"scratch")
    (root / "tracking" / "events.jsonl").write_bytes(b"{}\n")

    _verify_artifact_topology(root, (), expect_unused_artifacts=False)


def test_artifact_topology_keeps_identity_checks_when_emptiness_is_relaxed(
    monkeypatch, tmp_path: Path,
) -> None:
    # B-10 (architecture section 19.13 test 2): the load-bearing one. Relaxing
    # the emptiness precondition must not disable the identity half, so every
    # case below carries a legitimately non-empty `state` AND an identity
    # violation, and must still raise. A relaxation that skipped the whole
    # function would pass test 1 above and fail every assertion here.
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "state" / "trainer-state.json").write_bytes(b"{}")

    (root / "cache" / "extra-empty").mkdir()
    with pytest.raises(ValueError, match="extra directories"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=False)
    (root / "cache" / "extra-empty").rmdir()

    (root / "extra").mkdir()
    with pytest.raises(ValueError, match="incomplete or extended"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=False)
    (root / "extra").rmdir()

    (root / "tracking").rmdir()
    (root / "tracking").write_bytes(b"not-a-directory")
    with pytest.raises(ValueError, match="invalid entry"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=False)
    (root / "tracking").unlink()
    (root / "tracking").mkdir()

    module_globals = _verify_artifact_topology.__globals__
    monkeypatch.setitem(module_globals, "_is_reparse", lambda _info: True)
    with pytest.raises(ValueError, match="redirected or invalid"):
        _verify_artifact_topology(root, (), expect_unused_artifacts=False)


def test_artifact_topology_still_rejects_a_written_root_before_the_run_starts(
    tmp_path: Path,
) -> None:
    # B-10 (architecture section 19.6): the tamper signal survives. Nothing the
    # durable record admits before start can explain content here, so the
    # original message still fires for every one of the four writable roots.
    for name in ("artifacts", "state", "tmp", "tracking"):
        root = tmp_path / f"artifacts-root-{name}"
        _empty_artifact_topology(root)
        (root / name / "unexpected.json").write_bytes(b"unexpected")
        with pytest.raises(ValueError, match="not empty"):
            _verify_artifact_topology(root, (), expect_unused_artifacts=True)


def test_artifact_topology_guard_cannot_be_omitted_by_a_caller(
    tmp_path: Path,
) -> None:
    # B-10 (architecture section 19.4): required keyword-only, no default. A
    # default would let a future call site silently take the permissive branch.
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    with pytest.raises(TypeError):
        _verify_artifact_topology(root, ())
    parameter = inspect.signature(_verify_artifact_topology).parameters[
        "expect_unused_artifacts"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    staged = inspect.signature(stage_docker_worker_v1).parameters[
        "expect_unused_artifacts"
    ]
    assert staged.kind is inspect.Parameter.KEYWORD_ONLY
    assert staged.default is inspect.Parameter.empty
    # The caller's value must reach the verifier rather than being recomputed
    # or hard-coded inside staging. The end-to-end coupling is already covered:
    # the spy in test_docker_training.py now declares the keyword as required,
    # so a stage that failed to forward it would raise TypeError there.
    assert "expect_unused_artifacts=expect_unused_artifacts" in inspect.getsource(
        stage_docker_worker_v1
    )


def test_worker_binding_rejects_argv_drift_and_runtime_escape() -> None:
    closure = _load_locked_closure(ENGINE, ENGINE_COMMIT)
    workload_sha256 = "1" * 64
    workload_fingerprint = "2" * 64
    workload_byte_count = 17
    transport = SimpleNamespace(
        path=PurePosixPath("/source/control/workload.json"),
        control_root=PurePosixPath("/source/control"),
        byte_count=workload_byte_count,
        sha256=workload_sha256,
        workload_fingerprint=workload_fingerprint,
    )
    worker = SimpleNamespace(
        roots_map={"engine": PurePosixPath("/source/engine")},
        entrypoint=PurePosixPath(closure.entrypoint),
        interpreter="python",
        transport=transport,
    )
    exact_argv = (
        "python", "/source/engine/" + closure.entrypoint,
        "--canonical-workload-file", "/source/control/workload.json",
        "--canonical-workload-control-root", "/source/control",
        "--canonical-workload-byte-count", str(workload_byte_count),
        "--canonical-workload-sha256", workload_sha256,
        "--canonical-workload-fingerprint", workload_fingerprint,
    )

    def bundle(*, argv=exact_argv, runtime_path=None, **workload):
        return SimpleNamespace(
            closure_manifest_bytes=closure.manifest_bytes,
            closure_manifest_byte_count=len(closure.manifest_bytes),
            closure_manifest_sha256=closure.manifest_sha256,
            closure_digest=closure.closure_digest,
            closure_manifest_runtime_path=(
                PurePosixPath("/source/control/manifest.json")
                if runtime_path is None else runtime_path
            ),
            workload_byte_count=workload.get(
                "workload_byte_count", workload_byte_count
            ),
            workload_sha256=workload.get("workload_sha256", workload_sha256),
            workload_fingerprint=workload.get(
                "workload_fingerprint", workload_fingerprint
            ),
            dispatch=SimpleNamespace(
                argv=argv,
                environment_map={},
            ),
        )

    assert _verify_worker_closure_binding(
        worker, bundle(), closure
    ) == PurePosixPath("manifest.json")
    wrong_entrypoint = list(exact_argv)
    wrong_entrypoint[1] = "/source/engine/wrong.py"
    with pytest.raises(ValueError, match="locked source closure"):
        _verify_worker_closure_binding(
            worker, bundle(argv=tuple(wrong_entrypoint)), closure
        )
    rejected_argv = [
        exact_argv[:-1],
        exact_argv + ("--extra",),
    ]
    for index, replacement in (
        (3, "/source/control/other-workload.json"),
        (5, "/source/other-control"),
        (7, "18"),
        (9, "3" * 64),
        (11, "4" * 64),
    ):
        changed = list(exact_argv)
        changed[index] = replacement
        rejected_argv.append(tuple(changed))
    for argv in rejected_argv:
        with pytest.raises(ValueError, match="locked source closure"):
            _verify_worker_closure_binding(worker, bundle(argv=argv), closure)

    for drift in (
        {"workload_byte_count": 18},
        {"workload_sha256": "3" * 64},
        {"workload_fingerprint": "4" * 64},
    ):
        with pytest.raises(ValueError, match="locked source closure"):
            _verify_worker_closure_binding(worker, bundle(**drift), closure)
    with pytest.raises(ValueError, match="escapes control"):
        _verify_worker_closure_binding(
            worker,
            bundle(runtime_path=PurePosixPath("/artifacts/manifest.json")),
            closure,
        )
