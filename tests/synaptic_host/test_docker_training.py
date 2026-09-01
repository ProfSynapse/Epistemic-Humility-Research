from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from synaptic_host import cli
from synaptic_host.cli import (
    TrainingRunCommandCodeV2,
    TrainingRunCommandStatusV2,
    TrainingRunIngressV1,
    prepare_training_run_ingress_v1,
)
from synaptic_host.docker_provider import DockerProviderProfileV1


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"
CONFIG_REF = "project://training/smokes/modal-sft.json"
PROVENANCE_KEYS = (
    "training_input_digest",
    "training_contract_identity_digest",
    "training_source_sha256",
    "training_ingress_digest",
    "provider_policy_digest",
)
INPUT_KINDS = (
    "training-config",
    "training-dataset",
)
INPUT_FIELDS = (
    "kind", "ref", "path", "git_object_id", "size_bytes", "sha256",
)


@pytest.fixture(scope="module", autouse=True)
def _isolated_engine_import_state():
    host_package = sys.modules["synaptic_host"]
    original = {
        name: value for name, value in sys.modules.items()
        if (
            name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
            or name == "tuner" or name.startswith("tuner.")
            or name == "synaptic_host.docker_staging"
            or name == "synaptic_host.docker_training"
        )
    }
    for name in original:
        sys.modules.pop(name, None)
    for attribute in ("docker_staging", "docker_training"):
        if hasattr(host_package, attribute):
            delattr(host_package, attribute)
    cli._ENGINE_CONTRACT_CACHE = None
    try:
        yield
    finally:
        for name in tuple(sys.modules):
            if (
                name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
                or name == "tuner" or name.startswith("tuner.")
                or name == "synaptic_host.docker_staging"
                or name == "synaptic_host.docker_training"
            ):
                sys.modules.pop(name, None)
        sys.modules.update(original)
        for attribute in ("docker_staging", "docker_training"):
            module = original.get(f"synaptic_host.{attribute}")
            if module is not None:
                setattr(host_package, attribute, module)
            elif hasattr(host_package, attribute):
                delattr(host_package, attribute)
        cli._ENGINE_CONTRACT_CACHE = None


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments), check=True,
        capture_output=True, timeout=30,
    ).stdout


def _commit(repository: Path, message: str) -> str:
    _git(repository, "add", "-A")
    _git(repository, "commit", "-m", message)
    return _git(repository, "rev-parse", "HEAD").decode("ascii").strip()


@pytest.fixture(scope="module")
def clean_project(tmp_path_factory):
    base = tmp_path_factory.mktemp("docker-admission")
    project = base / "project"
    engine = project / "synaptic-tuner"
    engine_bare = base / "engine-remote.git"
    project_bare = base / "project-remote.git"
    engine_url = "https://git.example/synaptic-tuner.git"
    project_url = "https://git.example/product.git"

    project.mkdir()
    engine_commit = _git(
        ROOT, "rev-parse", "HEAD:synaptic-tuner"
    ).decode("ascii").strip()
    subprocess.run(
        (
            "git", "clone", "--shared", "--no-checkout",
            str(ENGINE), str(engine),
        ),
        check=True, capture_output=True, timeout=60,
    )
    _git(engine, "checkout", "--detach", engine_commit)
    subprocess.run(
        ("git", "init", "--bare", str(engine_bare)),
        check=True, capture_output=True, timeout=30,
    )
    _git(engine, "push", str(engine_bare), "HEAD:refs/heads/main")
    _git(engine, "config", "remote.origin.url", engine_url)
    _git(engine, "config", "branch.main.remote", "origin")
    _git(engine, "config", "branch.main.merge", "refs/heads/main")

    _git(project, "init", "-b", "main")
    _git(project, "config", "user.email", "docker-admission@example.invalid")
    _git(project, "config", "user.name", "Docker Admission Test")
    copies = (
        "training/smokes/modal-sft.json",
        "training/fixtures/modal-smoke.jsonl",
        "training/providers/docker.json",
        "training/artifacts.json",
        "training/storage.json",
        "synaptic.yaml",
    )
    for relative in copies:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (project / ".gitmodules").write_text(
        '[submodule "synaptic-tuner"]\n'
        "\tpath = synaptic-tuner\n"
        f"\turl = {engine_url}\n"
        "\tbranch = main\n",
        encoding="utf-8",
    )
    initial_commit = _commit(project, "clean Docker admission fixture")
    subprocess.run(
        ("git", "init", "--bare", str(project_bare)),
        check=True, capture_output=True, timeout=30,
    )
    _git(project, "push", str(project_bare), "HEAD:refs/heads/main")
    _git(project, "remote", "add", "origin", project_url)
    _git(project, "config", "branch.main.remote", "origin")
    _git(project, "config", "branch.main.merge", "refs/heads/main")

    ingresses = tuple(_ingress(project, engine) for _ in range(3))
    invalid_project = base / "invalid-project"
    subprocess.run(
        ("git", "clone", "--no-hardlinks", str(project), str(invalid_project)),
        check=True, capture_output=True, timeout=30,
    )
    _git(invalid_project, "config", "user.email", "docker-admission@example.invalid")
    _git(invalid_project, "config", "user.name", "Docker Admission Test")
    (invalid_project / "training/providers/docker.json").write_bytes(b"{}\n")
    _commit(invalid_project, "invalid Docker profile")
    invalid_ingress = _ingress(invalid_project, engine)
    assert _git(engine, "status", "--porcelain", "--untracked-files=normal") == b""
    assert _git(project, "status", "--porcelain", "--untracked-files=normal") == b""

    mapping = {project_url: project_bare, engine_url: engine_bare}
    calls: list[tuple[str, ...]] = []

    def transport(argv) -> bytes:
        arguments = tuple(argv)
        calls.append(arguments)
        assert arguments[:3] == ("git", "ls-remote", "--refs")
        remote = mapping[arguments[3]]
        return subprocess.run(
            ("git", "ls-remote", "--refs", str(remote), arguments[4]),
            check=True, capture_output=True, timeout=30,
        ).stdout

    return {
        "project": project, "engine": engine,
        "project_bare": project_bare, "initial_commit": initial_commit,
        "transport": transport, "calls": calls, "ingresses": ingresses,
        "invalid_project": invalid_project, "invalid_ingress": invalid_ingress,
    }


def _ingress(project: Path, engine: Path) -> TrainingRunIngressV1:
    value = prepare_training_run_ingress_v1(
        [
            "training", "run", "--provider", "docker",
            "--config", CONFIG_REF, "--destination", "local-default",
        ],
        project_root=project,
        engine_root=engine,
    )
    assert type(value) is TrainingRunIngressV1, getattr(value, "code", None)
    return value


def test_checked_in_profile_is_closed_and_declares_no_sft_backend() -> None:
    profile = DockerProviderProfileV1.load(project_root=ROOT)
    assert profile.supported_methods == ()
    assert profile.supports("sft") is False
    assert profile.workload_transport == "sealed_file"
    assert profile.source_mode == "dual_clone_read_only"
    assert profile.network_mode == "none"
    assert profile.cpu_count == 1


def test_outer_main_runs_actual_clean_superproject_path(
    monkeypatch, capsys, clean_project,
) -> None:
    from synaptic_host import __main__ as entry
    from synaptic_host.security import ScopedGitRemoteReader

    project = clean_project["project"]
    monkeypatch.setattr(entry, "__file__", str(project / "synaptic_host/__main__.py"))
    monkeypatch.setattr(
        ScopedGitRemoteReader, "_run",
        staticmethod(clean_project["transport"]),
    )
    code = entry.main([
        "training", "run", "--provider", "docker",
        "--config", CONFIG_REF, "--destination", "local-default",
    ])
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["code"] == "CAPABILITY_UNSUPPORTED"
    assert result["status"] == "rejected"
    assert not (project / ".synaptic").exists()


def test_real_clean_superproject_compiles_canonical_plan_and_rejects_without_effects(
    monkeypatch, clean_project,
) -> None:
    project = clean_project["project"]
    engine = clean_project["engine"]
    ingress = clean_project["ingresses"][0]
    swapped = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=None,
        project_root=clean_project["invalid_project"], engine_root=engine,
    )
    assert swapped.code is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE

    from synaptic_host import docker_training
    from synaptic_host.docker_v1 import composition as docker_composition
    from synaptic_host.local_artifact_destination import LocalArtifactDestinationV1
    from synaptic_host.security import ScopedGitRemoteReader
    from synaptic_host.sqlite_repository import SqliteTrainingRepository
    from synaptic_tuner.api.v1 import (
        CanonicalDocument, SourceLock, TrainingPlan, TrainingRequest,
    )

    observed: dict[str, object] = {}
    original_post_init = SourceLock.__post_init__
    original_compiler = docker_training.compile_training_plan_v1
    original_validator = docker_training.validate_source_lock_provenance_v1

    def record_lock(self):
        original_post_init(self)
        if tuple(self.configuration) == PROVENANCE_KEYS:
            observed["source_lock"] = self

    def record_compile(*, training_input, context, resolver):
        try:
            plan = original_compiler(
                training_input=training_input, context=context, resolver=resolver,
            )
        except BaseException as error:
            observed["compiler_error"] = repr(error)
            raise
        observed["plan"] = plan
        observed["session"] = resolver.session
        observed["session_key"] = bytes(resolver.session._key)
        observed["evidence_payload"] = resolver.session._verified.source_evidence.authenticated_payload
        observed["evidence_tag"] = resolver.session._verified.source_evidence.tag
        assert resolver.session._closed is False
        with pytest.raises(ValueError, match="already consumed"):
            resolver.resolve(
                TrainingRequest(CanonicalDocument.from_mapping(training_input.to_dict())),
                context=context,
            )
        return plan

    def record_validation(source, source_lock, expected):
        observed["validated"] = (source, source_lock, dict(expected))
        return original_validator(source, source_lock, expected)

    forbidden = lambda *_args, **_kwargs: pytest.fail(
        "admission crossed a durable or provider effect boundary"
    )
    monkeypatch.setattr(SourceLock, "__post_init__", record_lock)
    monkeypatch.setattr(docker_training, "compile_training_plan_v1", record_compile)
    monkeypatch.setattr(
        docker_training, "validate_source_lock_provenance_v1", record_validation,
    )
    monkeypatch.setattr(docker_composition, "compose_docker_host_v1", forbidden)
    monkeypatch.setattr(SqliteTrainingRepository, "from_context", forbidden)
    monkeypatch.setattr(LocalArtifactDestinationV1, "publish_once", forbidden)

    result = docker_training.execute_docker_training_admission_v1(
        ingress, project_root=project, engine_root=engine,
        remote_reader=ScopedGitRemoteReader(runner=clean_project["transport"]),
    )

    assert result.code is TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED, observed
    assert result.status is TrainingRunCommandStatusV2.REJECTED
    assert result.input_digest == ingress.input_digest
    assert type(observed["plan"]) is TrainingPlan
    assert type(observed["plan"]).__module__ == "synaptic_tuner.api.v1.training"
    assert observed["plan"].workload.to_dict()["method"] == "sft"
    lock = observed["source_lock"]
    assert type(lock) is SourceLock
    assert tuple(lock.configuration) == PROVENANCE_KEYS
    assert tuple(item["kind"] for item in lock.inputs) == INPUT_KINDS
    assert all(tuple(item) == INPUT_FIELDS for item in lock.inputs)
    assert tuple(item["path"] for item in lock.inputs) == (
        "training/smokes/modal-sft.json",
        "training/fixtures/modal-smoke.jsonl",
    )
    assert tuple(item["ref"] for item in lock.inputs) == (
        CONFIG_REF,
        "project://training/fixtures/modal-smoke.jsonl",
    )
    assert lock.configuration["training_input_digest"] == ingress.input_digest
    assert lock.configuration["training_contract_identity_digest"] == ingress.contract_identity_digest
    assert lock.configuration["training_source_sha256"] == lock.inputs[0]["sha256"]
    assert lock.configuration["training_ingress_digest"] == ingress.envelope_digest
    assert all(len(lock.configuration[key]) == 64 for key in PROVENANCE_KEYS)
    assert tuple(
        _git(project, "rev-parse", f"{lock.project_source.commit}:{item['path']}")
        .decode("ascii").strip()
        for item in lock.inputs
    ) == tuple(item["git_object_id"] for item in lock.inputs)
    manifest = lock.project["manifest"]
    provider = lock.runtime["provider_profile"]
    storage = lock.runtime["storage_configuration"]
    registry = lock.outputs["destination_registry"]
    assert tuple(manifest) == tuple(provider) == tuple(storage) == tuple(registry) == INPUT_FIELDS
    assert (manifest["kind"], provider["kind"], storage["kind"], registry["kind"]) == (
        "project-manifest", "docker-provider-profile",
        "host-storage-configuration",
        "artifact-destination-registry",
    )
    assert lock.runtime["provider_policy_digest"] == lock.configuration["provider_policy_digest"]
    assert lock.outputs["destination_ref"] == "local-default"
    assert len(lock.outputs["destination_declaration_digest"]) == 64
    assert lock.runtime["storage_configuration_digest"] == storage["sha256"]
    for item in (manifest, provider, storage, registry):
        assert (
            _git(project, "rev-parse", f"{lock.project_source.commit}:{item['path']}")
            .decode("ascii").strip()
            == item["git_object_id"]
        )
    assert lock.project_source.dirty is False and lock.project_source.pushed is True
    assert lock.engine_source.dirty is False and lock.engine_source.pushed is True
    assert observed["plan"].execution_source.source_evidence.binds(lock)
    assert observed["plan"].execution_source.roots == {
        "engine": "/source/engine",
        "project": "/source/project",
        "artifacts": "/artifacts/artifacts",
        "state": "/artifacts/state",
        "tracking": "/artifacts/tracking",
        "cache": "/artifacts/cache",
        "tmp": "/artifacts/tmp",
    }
    assert observed["plan"].execution_source.writable_capability_root == "/artifacts"
    assert observed["validated"][1] is lock
    assert observed["validated"][2] == dict(lock.configuration)
    assert observed["session"]._closed is True
    assert observed["session"]._key == b""
    assert observed["session"]._payload == b""
    assert observed["session"]._tag == b""
    expected_tag = hmac.digest(
        observed["session_key"],
        b"source-lock-evidence/v1\0" + observed["evidence_payload"],
        hashlib.sha256,
    )
    assert hmac.compare_digest(expected_tag, observed["evidence_tag"])
    assert len(clean_project["calls"]) >= 4
    assert not (project / ".synaptic").exists()


def test_source_proof_precedes_invalid_profile_and_dirty_source(
    monkeypatch, clean_project,
) -> None:
    project = clean_project["project"]
    engine = clean_project["engine"]

    from synaptic_host import docker_training
    from synaptic_host.security import ScopedGitRemoteReader
    original_reader = cli._read_committed_git_blob_v1
    reads = []

    def record_read(*args, **kwargs):
        reads.append((args, kwargs))
        return original_reader(*args, **kwargs)

    monkeypatch.setattr(cli, "_read_committed_git_blob_v1", record_read)
    invalid = docker_training.execute_docker_training_admission_v1(
        clean_project["invalid_ingress"],
        project_root=clean_project["invalid_project"], engine_root=engine,
        remote_reader=ScopedGitRemoteReader(runner=clean_project["transport"]),
    )
    assert invalid.code is TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE
    assert reads == []

    dirty_marker = project / "untracked-source.txt"
    dirty_marker.write_text("dirty\n", encoding="utf-8")
    try:
        dirty = docker_training.execute_docker_training_admission_v1(
            clean_project["ingresses"][2], project_root=project, engine_root=engine,
            remote_reader=ScopedGitRemoteReader(runner=clean_project["transport"]),
        )
    finally:
        dirty_marker.unlink()
    assert dirty.code is TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE
    assert reads == []
    assert dirty.status is TrainingRunCommandStatusV2.UNAVAILABLE
    assert not (project / ".synaptic").exists()


def test_hmac_session_rejects_post_compiler_evidence_mutation(
    monkeypatch, clean_project,
) -> None:
    from synaptic_host import docker_training
    from synaptic_host.security import ScopedGitRemoteReader

    original = docker_training.compile_training_plan_v1
    observed = {}

    def mutate(*, training_input, context, resolver):
        plan = original(
            training_input=training_input, context=context, resolver=resolver,
        )
        observed["session"] = resolver.session
        object.__setattr__(
            plan.execution_source.source_evidence,
            "tag_base64", base64.b64encode(b"changed-tag").decode("ascii"),
        )
        return plan

    monkeypatch.setattr(docker_training, "compile_training_plan_v1", mutate)
    result = docker_training.execute_docker_training_admission_v1(
        clean_project["ingresses"][1],
        project_root=clean_project["project"], engine_root=clean_project["engine"],
        remote_reader=ScopedGitRemoteReader(runner=clean_project["transport"]),
    )
    assert result.code is TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE
    assert observed["session"]._closed is True
    assert observed["session"]._key == b""


def test_clean_admission_stage_materializes_exact_two_runtime_roots(
    monkeypatch, clean_project,
) -> None:
    docker_training = importlib.import_module("synaptic_host.docker_training")
    docker_staging = importlib.import_module("synaptic_host.docker_staging")
    from synaptic_host.security import ScopedGitRemoteReader
    from tuner.project.manifest import load_project_manifest

    observed = {}
    replay_checks = []
    artifact_checks = []
    original = docker_training.compile_training_plan_v1
    original_replay = docker_staging._verify_reuse
    original_artifacts = docker_staging._verify_artifact_topology

    def capture(*, training_input, context, resolver):
        plan = original(
            training_input=training_input, context=context, resolver=resolver,
        )
        observed["plan"] = plan
        observed["source_lock"] = resolver.session._verified.source_lock
        return plan

    def verify_replay(source, projection, closure, manifest_runtime_path):
        replay_checks.append(source)
        return original_replay(
            source, projection, closure, manifest_runtime_path
        )

    def verify_artifacts(root, inventory):
        artifact_checks.append(root)
        return original_artifacts(root, inventory)

    monkeypatch.setattr(docker_training, "compile_training_plan_v1", capture)
    monkeypatch.setattr(docker_staging, "_verify_reuse", verify_replay)
    monkeypatch.setattr(
        docker_staging, "_verify_artifact_topology", verify_artifacts
    )
    project = clean_project["project"]
    result = docker_training.execute_docker_training_admission_v1(
        clean_project["ingresses"][0],
        project_root=project,
        engine_root=clean_project["engine"],
        remote_reader=ScopedGitRemoteReader(runner=clean_project["transport"]),
    )
    assert result.code is TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED
    manifest = load_project_manifest(project / "synaptic.yaml")
    context = manifest.create_context(
        engine_root=clean_project["engine"], invocation_cwd=project,
    )
    staged = docker_staging.stage_docker_worker_v1(
        plan=observed["plan"],
        source_lock=observed["source_lock"],
        context=context,
        storage_configuration=(project / "training/storage.json").read_bytes(),
        model_inventory=(),
    )
    assert staged.source_root.joinpath("control/workload.json").read_bytes() == (
        staged.worker_bundle.canonical_workload_bytes
    )
    assert staged.source_root.joinpath("control/source-lock.json").read_bytes() == (
        observed["source_lock"].canonical_bytes
    )
    locked_manifest = subprocess.run(
        (
            "git", "-C", str(clean_project["engine"]), "show",
            observed["source_lock"].engine_source.commit
            + ":tuner/runtime/manifests/offline-sft-worker-v1.json",
        ),
        check=True,
        capture_output=True,
    ).stdout
    runtime_manifest = staged.worker_bundle.closure_manifest_runtime_path
    runtime_relative = runtime_manifest.relative_to("/source/control")
    assert staged.source_root.joinpath(
        "control", *runtime_relative.parts
    ).read_bytes() == locked_manifest
    closure_manifest = json.loads(locked_manifest)
    engine_files = tuple(
        path for path in staged.source_root.joinpath("engine").rglob("*")
        if path.is_file()
    )
    assert len(engine_files) == closure_manifest["member_count"]
    assert sum(path.stat().st_size for path in engine_files) == (
        closure_manifest["payload_bytes"]
    )
    assert staged.projection.worker_closure_manifest_path == (
        "tuner/runtime/manifests/offline-sft-worker-v1.json"
    )
    assert staged.projection.worker_closure_manifest_sha256 == hashlib.sha256(
        locked_manifest
    ).hexdigest()
    assert staged.projection.worker_source_closure_digest == (
        closure_manifest["closure_digest"]
    )
    assert observed["plan"].execution_source.environment["PYTHONPATH"] == (
        "/source/engine"
    )
    assert not {
        "PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "HF_TOKEN",
    } & set(staged.worker_bundle.dispatch.environment_map)
    assert staged.artifact_root.name == "artifacts"
    assert tuple(
        path.name for path in sorted(staged.artifact_root.iterdir())
    ) == ("artifacts", "cache", "state", "tmp", "tracking")
    assert replay_checks == [staged.source_root]
    assert artifact_checks == [staged.artifact_root]
    replay = docker_staging.stage_docker_worker_v1(
        plan=observed["plan"],
        source_lock=observed["source_lock"],
        context=context,
        storage_configuration=(project / "training/storage.json").read_bytes(),
        model_inventory=(),
    )
    assert replay.projection == staged.projection
    assert replay.source_root == staged.source_root
    assert replay.artifact_root == staged.artifact_root
    assert replay_checks == [staged.source_root, replay.source_root]
    assert artifact_checks == [staged.artifact_root, replay.artifact_root]


def test_committed_blob_reader_enforces_call_and_global_bounds(
    monkeypatch, clean_project,
) -> None:
    project = clean_project["project"]
    monkeypatch.setattr(
        cli.subprocess, "run",
        lambda *_args, **_kwargs: pytest.fail("bounded reader used capture_output run"),
    )
    with pytest.raises(ValueError):
        cli._read_committed_git_blob_v1(
            project, "training/fixtures/modal-smoke.jsonl", maximum_bytes=1,
        )
    with pytest.raises(ValueError):
        cli._read_committed_git_blob_v1(
            project, "training/providers/docker.json",
            maximum_bytes=64 * 1024 * 1024 + 1,
        )
    profile = cli._read_committed_git_blob_v1(
        project, "training/providers/docker.json", maximum_bytes=64 * 1024,
    )
    assert profile.size_bytes == len(profile.content)


def test_docker_provider_staging_is_rejected_before_input_loading() -> None:
    result = prepare_training_run_ingress_v1(
        [
            "training", "run", "--provider", "docker",
            "--config", CONFIG_REF, "--destination", "provider-staging",
        ],
        project_root=ROOT,
        engine_root=ENGINE,
    )
    assert result.code is TrainingRunCommandCodeV2.DESTINATION_INVALID
    assert result.config_ref is None
    assert result.input_digest is None


def test_active_dirty_worktree_outer_command_is_resolution_unavailable() -> None:
    code = f"""
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.path.insert(0, {str(ENGINE)!r})
from synaptic_host.__main__ import main
raise SystemExit(main([
    'training', 'run', '--provider', 'docker',
    '--config', {CONFIG_REF!r}, '--destination', 'local-default',
]))
"""
    completed = subprocess.run(
        (sys.executable, "-I", "-c", code), cwd=ROOT,
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 4
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["code"] == "RESOLUTION_UNAVAILABLE"
