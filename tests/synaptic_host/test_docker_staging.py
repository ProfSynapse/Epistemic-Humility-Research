from __future__ import annotations

import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import tarfile
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
    _extract_link_free,
    _git_archive,
    _load_locked_closure,
    _release_windows_stage,
    _source_manifest,
    _stage_locked_closure,
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


def test_git_archive_reads_the_exact_commit_not_worktree_bytes(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.email", "staging@example.invalid")
    _git(repository, "config", "user.name", "Staging Test")
    source = repository / "source.txt"
    source.write_text("committed\n", encoding="utf-8")
    _git(repository, "add", "source.txt")
    _git(repository, "commit", "-m", "fixture")
    commit = _git(repository, "rev-parse", "HEAD")
    source.write_text("uncommitted\n", encoding="utf-8")

    destination = tmp_path / "destination"
    _extract_link_free(_git_archive(repository, commit), destination)

    assert (destination / "source.txt").read_text(encoding="utf-8") == "committed\n"


def test_link_free_extraction_rejects_symlinks(tmp_path: Path) -> None:
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w") as archive:
        member = tarfile.TarInfo("redirect")
        member.type = tarfile.SYMTYPE
        member.linkname = "outside"
        archive.addfile(member)

    with pytest.raises(ValueError, match="link or special"):
        _extract_link_free(payload.getvalue(), tmp_path / "destination")


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
