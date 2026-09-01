from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path
from pathlib import PurePosixPath
from types import SimpleNamespace

import pytest

from synaptic_host.docker_staging import (
    DockerModelInventoryEntryV1,
    _CLOSURE_MANIFEST_SOURCE_PATH,
    _copy_inventory,
    _extract_link_free,
    _git_archive,
    _load_locked_closure,
    _source_manifest,
    _stage_locked_closure,
    _verify_artifact_topology,
    _verify_inventory_at,
    _verify_worker_closure_binding,
    _verify_staged_closure,
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
    _verify_artifact_topology(root, ())

    (root / "state" / "unexpected.json").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="not empty"):
        _verify_artifact_topology(root, ())


def test_artifact_topology_rejects_extra_root_and_cache_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "extra").mkdir()
    with pytest.raises(ValueError, match="incomplete or extended"):
        _verify_artifact_topology(root, ())
    (root / "extra").rmdir()
    (root / "cache" / "extra-empty").mkdir()
    with pytest.raises(ValueError, match="extra directories"):
        _verify_artifact_topology(root, ())


def test_artifact_topology_rejects_special_slot_and_reparse_root(
    monkeypatch, tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts-root"
    _empty_artifact_topology(root)
    (root / "tracking").rmdir()
    (root / "tracking").write_bytes(b"not-a-directory")
    with pytest.raises(ValueError, match="invalid entry"):
        _verify_artifact_topology(root, ())

    (root / "tracking").unlink()
    (root / "tracking").mkdir()
    module_globals = _verify_artifact_topology.__globals__
    monkeypatch.setitem(module_globals, "_is_reparse", lambda _info: True)
    with pytest.raises(ValueError, match="redirected or invalid"):
        _verify_artifact_topology(root, ())


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
