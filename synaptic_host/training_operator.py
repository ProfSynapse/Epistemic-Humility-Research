"""Supported, bounded operator reads for an existing Modal training run."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import modal_sdk


_SCHEMA = "synaptic-training-operator-result/v1"
_REQUEST_SCHEMA = "synaptic-training-operator-request/v1"
_CONTRACT_DIGEST = hashlib.sha256(
    b"synaptic-training-operator-contract/v1\0status,reconcile,retrieve"
).hexdigest()
_RUN_ID = re.compile(r"^run-[0-9a-f]{32}$")


@dataclass(frozen=True, slots=True)
class _DurableEffectView:
    identity: object
    provider_job_ref: str | None


class _ReadOnlyModalRunRepository:
    """Narrow repository that rechecks one validated ledger pair on every read."""

    __slots__ = (
        "_context", "_project_ref", "_run_id", "_effect_id",
        "_record_bytes", "_preparation_bytes",
    )

    def __init__(self, context, project_ref: str, run_id: str, record, preparation):
        self._context = context
        self._project_ref = project_ref
        self._run_id = run_id
        self._effect_id = preparation.operation.effect.effect_id
        self._record_bytes = bytes(record.canonical_bytes)
        self._preparation_bytes = bytes(preparation.canonical_bytes)

    def _pair(self):
        pair = _read_existing_pair(self._context, self._project_ref, self._run_id)
        if pair is None:
            raise ValueError("durable Modal run is unavailable")
        record, preparation, _effect = pair
        if (
            record.canonical_bytes != self._record_bytes
            or preparation.canonical_bytes != self._preparation_bytes
        ):
            raise ValueError("durable Modal run changed during retrieval")
        return record, preparation

    def load(self, project_ref: str, run_id: str):
        if (project_ref, run_id) != (self._project_ref, self._run_id):
            raise ValueError("durable Modal run was misrouted")
        return self._pair()[0]

    def load_modal_preparation(self, project_ref: str, run_id: str):
        if (project_ref, run_id) != (self._project_ref, self._run_id):
            raise ValueError("durable Modal preparation was misrouted")
        return self._pair()[1]

    def load_modal_preparation_by_effect(self, effect_id: str):
        if effect_id != self._effect_id:
            raise ValueError("durable Modal effect was misrouted")
        return self._pair()[1]


def _result(code: str, *, run_id: str | None = None, **fields: object) -> dict[str, object]:
    return {"schema_version": _SCHEMA, "code": code, "run_id": run_id, **fields}


def _emit(value: dict[str, object]) -> int:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if value["code"] == "OK" else 2 if value["code"] in {
        "COMMAND_INVALID", "RUN_INVALID", "RUN_MISSING",
    } else 4


def _parse(argv: list[str]) -> tuple[str, str] | None:
    if (
        type(argv) is not list or len(argv) != 4
        or argv[0] != "training" or argv[1] not in {"status", "reconcile", "retrieve"}
        or argv[2] != "--run-id" or type(argv[3]) is not str
        or _RUN_ID.fullmatch(argv[3]) is None
    ):
        return None
    return argv[1], argv[3]


def _request_digest(verb: str, run_id: str) -> str:
    body = json.dumps(
        {"schema_version": _REQUEST_SCHEMA, "verb": verb, "run_id": run_id},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(_REQUEST_SCHEMA.encode("ascii") + b"\0" + body).hexdigest()


def _project_context(project_root: Path, engine_root: Path):
    manifest_module = importlib.import_module("tuner.project.manifest")
    manifest = manifest_module.load_project_manifest(project_root / "synaptic.yaml")
    if manifest.path.parent.resolve(strict=True) != project_root:
        raise ValueError("project manifest escaped the released root")
    return manifest, manifest.create_context(
        engine_root=engine_root, invocation_cwd=project_root
    )


def _database_path(context) -> Path:
    mutable = Path(os.path.abspath(context.project_root / ".synaptic"))
    state = Path(os.path.abspath(context.state_root))
    try:
        confined = os.path.commonpath((str(mutable), str(state))) == str(mutable)
    except ValueError:
        confined = False
    if not confined:
        raise ValueError("training state root escaped the private host root")
    return state / "training.sqlite3"


def _private_database_descriptor(
    context,
) -> tuple[Path, int, tuple[int, ...], tuple[tuple[Path, tuple[int, ...]], ...]]:
    from .security import FileHmacAuthenticator

    database = _database_path(context)
    private_root = Path(os.path.abspath(context.project_root / ".synaptic"))
    relative = database.parent.relative_to(private_root)
    directories = [private_root]
    directory = private_root
    for component in relative.parts:
        directory /= component
        directories.append(directory)
    directory_identities = []
    for directory in directories:
        observed_directory = directory.lstat()
        FileHmacAuthenticator._validate_private_directory(directory)
        directory_identities.append((directory, (
            observed_directory.st_dev, observed_directory.st_ino,
            observed_directory.st_mode, observed_directory.st_uid,
        )))
    if any(_path_exists(Path(str(database) + suffix)) for suffix in ("-wal", "-shm")):
        raise ValueError("training ledger has active sidecar state")
    flags = (
        os.O_RDONLY | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(database, flags)
    observed = os.fstat(descriptor)
    if (
        not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1
        or observed.st_uid != os.geteuid() or stat.S_IMODE(observed.st_mode) & 0o022
    ):
        os.close(descriptor)
        raise ValueError("training ledger is not a private regular file")
    identity = (
        observed.st_dev, observed.st_ino, observed.st_mode, observed.st_nlink,
        observed.st_uid, observed.st_size, observed.st_mtime_ns,
    )
    return database, descriptor, identity, tuple(directory_identities)


def _path_exists(path: Path) -> bool:
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def _read_existing_pair(context, project_ref: str, run_id: str):
    """Read without invoking the repository initializer or migrating state."""
    from .sqlite_repository import read_validated_operator_snapshot

    database, descriptor, identity, directory_identities = (
        _private_database_descriptor(context)
    )
    connection = None
    try:
        connection = read_validated_operator_snapshot(
            descriptor, expected_identity=identity
        )
        lifecycle = connection.execute(
            "SELECT record_json FROM lifecycle_records WHERE project_ref=? AND run_id=? LIMIT 2",
            (project_ref, run_id),
        ).fetchall()
        preparation = connection.execute(
            "SELECT preparation_json FROM modal_preparations WHERE project_ref=? AND run_id=? LIMIT 2",
            (project_ref, run_id),
        ).fetchall()
    finally:
        if connection is not None:
            connection.close()
        after = os.fstat(descriptor)
        os.close(descriptor)
    after_identity = (
        after.st_dev, after.st_ino, after.st_mode, after.st_nlink,
        after.st_uid, after.st_size, after.st_mtime_ns,
    )
    try:
        path = database.lstat()
    except FileNotFoundError:
        raise ValueError("training ledger identity changed") from None
    path_identity = (
        path.st_dev, path.st_ino, path.st_mode, path.st_nlink,
        path.st_uid, path.st_size, path.st_mtime_ns,
    )
    if identity != after_identity or identity != path_identity:
        raise ValueError("training ledger identity changed")
    if any(_path_exists(Path(str(database) + suffix)) for suffix in ("-wal", "-shm")):
        raise ValueError("training ledger sidecar state changed")
    for directory, expected in directory_identities:
        observed = directory.lstat()
        if (
            observed.st_dev, observed.st_ino, observed.st_mode, observed.st_uid
        ) != expected:
            raise ValueError("training ledger ancestor identity changed")
    if not lifecycle and not preparation:
        return None
    if len(lifecycle) != 1 or len(preparation) != 1:
        raise ValueError("durable run and Modal preparation disagree")
    return _decode_existing_pair(
        lifecycle[0][0], preparation[0][0], project_ref, run_id
    )


def _decode_existing_pair(
    lifecycle_raw: object, preparation_raw: object,
    project_ref: str, run_id: str,
):
    api = importlib.import_module("synaptic_tuner.api.v1")
    modal_api = importlib.import_module("synaptic_tuner.api.v1.modal")
    record = api.LifecycleRecord.from_canonical_bytes(bytes(lifecycle_raw))
    prepared = modal_api.ModalDurablePreparationV1.from_canonical_bytes(
        bytes(preparation_raw)
    )
    events = tuple(record.events[:4])
    if len(events) != 4:
        raise ValueError("durable Modal preparation is incomplete")
    prefix = api.LifecycleRecord(
        record.run_id, record.project_ref, 4, api.LifecyclePhase.READY,
        api.VerificationStatus.NOT_READY, events[-1].occurred_at,
        api.MessageCode.READY, events, (), events[1].grant_binding,
    )
    modal_api.ModalPreparedRunV1(prefix, prepared)
    effect_id = prepared.operation.effect.effect_id
    if (
        record.project_ref != project_ref or record.run_id != run_id
        or prepared.operation.project_ref != project_ref
        or prepared.operation.run_id != run_id
        or prepared.public_plan_fingerprint != prepared.operation.plan_fingerprint
    ):
        raise ValueError("durable Modal run binding is invalid")
    effects = tuple(item for item in record.effects if item.identity.effect_id == effect_id)
    if len(effects) > 1 or (
        effects and effects[0].identity != prepared.operation.effect
    ):
        raise ValueError("durable Modal effect binding is invalid")
    return record, prepared, (
        _DurableEffectView(prepared.operation.effect, None)
        if not effects else effects[0]
    )


def _local_status(context, project_ref: str, run_id: str) -> dict[str, object]:
    try:
        pair = _read_existing_pair(context, project_ref, run_id)
    except FileNotFoundError:
        pair = None
    if pair is None:
        return _result("RUN_MISSING", run_id=run_id)
    record, prepared, effect = pair
    return _result(
        "OK", run_id=run_id, project_ref=project_ref,
        observation="local_ledger", provider_refreshed=False,
        phase=record.phase.value, revision=record.revision,
        updated_at=record.updated_at,
        plan_fingerprint=prepared.public_plan_fingerprint,
        effect_id=effect.identity.effect_id,
        provider_job_ref=effect.provider_job_ref,
    )


def _submission(record, prepared):
    api = importlib.import_module("synaptic_tuner.api.v1")
    effect_id = prepared.operation.effect.effect_id
    submitted_at = record.updated_at
    for event in record.events:
        if event.effect is not None and event.effect.identity.effect_id == effect_id:
            submitted_at = event.occurred_at
            break
    return api.TrainingSubmission(
        api.RunRef(record.run_id, record.project_ref),
        prepared.public_plan_fingerprint, submitted_at,
    )


def _validate_released_source(context, prepared) -> None:
    api = importlib.import_module("synaptic_tuner.api.v1")
    locked = prepared.detached_execution_source()
    inspected = api.GitCliLocalSourceInspector().inspect(context=context)

    def identity(source) -> tuple[object, ...]:
        return (
            source.location.canonical_url, source.commit.lower(),
            source.submodule_path,
            None if source.gitlink_commit is None else source.gitlink_commit.lower(),
        )

    if (
        locked.run_id != prepared.operation.run_id
        or inspected.mode != "superproject"
        or inspected.project_source.dirty or inspected.engine_source.dirty
        or identity(locked.project_source) != identity(inspected.project_source)
        or identity(locked.engine_source) != identity(inspected.engine_source)
    ):
        raise ValueError("released source differs from the durable Modal run")


def _authorized_run(
    context, project_ref: str, run_id: str, authority_token: object, *, verb: str, token_id: str,
    token_secret: str, sdk_loader: Callable[[], object], clock: Callable[[], str],
):
    from . import launcher

    if verb not in {"reconcile", "retrieve"}:
        return _result("COMMAND_INVALID", run_id=run_id)
    consumed = launcher._consume_isolated_child_authority_v1(
        authority_token, ingress_digest=_request_digest(verb, run_id),
        contract_identity_digest=_CONTRACT_DIGEST,
    )
    if consumed is None:
        return _result("AUTHORITY_INVALID", run_id=run_id)
    project_root, engine_root, bound_id, bound_secret = consumed
    if project_root != context.project_root or engine_root != context.engine_root:
        return _result("AUTHORITY_INVALID", run_id=run_id)
    if (token_id, token_secret) != (bound_id, bound_secret) or not token_id or not token_secret:
        return _result("CREDENTIALS_UNAVAILABLE", run_id=run_id)
    try:
        pair = _read_existing_pair(context, project_ref, run_id)
    except FileNotFoundError:
        pair = None
    if pair is None:
        return _result("RUN_MISSING", run_id=run_id)
    record, prepared, _effect = pair
    _validate_released_source(context, prepared)
    if verb == "retrieve":
        api = importlib.import_module("synaptic_tuner.api.v1")
        if (
            record.phase is not api.LifecyclePhase.SUCCEEDED
            or record.verification is not api.VerificationStatus.VERIFIED
        ):
            return _result("RUN_NOT_VERIFIED", run_id=run_id)
    from .modal_provider import (
        ExplicitModalHostSession, ModalProviderAuthorityV1, build_worker_authenticator,
    )
    from .modal_training import (
        EvidenceKeyRouterV1, _RejectingSecretProvider, _RejectingTrainingResolver,
    )
    from .security import (
        HOST_EVIDENCE_KEY_REF, BoundedGrantProvider, FileHmacAuthenticator,
        ScopedGitRemoteReader,
    )
    from .sqlite_repository import SqliteTrainingRepository

    authority = ModalProviderAuthorityV1.load(context)
    host_auth = FileHmacAuthenticator.from_context(
        context, key_ref=HOST_EVIDENCE_KEY_REF
    )
    worker_auth = build_worker_authenticator(context)
    if (
        host_auth.private_storage_verified is not True
        or worker_auth.private_storage_verified is not True
    ):
        raise ValueError("existing run evidence keys are unavailable")
    session = ExplicitModalHostSession.from_credentials(
        sdk=sdk_loader(), config=authority.config,
        token_id=token_id, token_secret=token_secret,
    )
    authenticator = EvidenceKeyRouterV1(host=host_auth, worker=worker_auth)
    facade = session.facade(authority.state)
    if verb == "retrieve":
        return (
            record, prepared, authority,
            _ReadOnlyModalRunRepository(
                context, project_ref, run_id, record, prepared
            ),
            authenticator, facade,
        )
    repository = SqliteTrainingRepository.from_context(context, clock=clock)
    ports = importlib.import_module("synaptic_tuner.api.v1").HostPorts(
        lifecycle=repository, runs=repository,
        grants=BoundedGrantProvider(
            maximum_cost_minor_units=authority.config.maximum_cost_minor_units,
            currency=authority.config.currency, clock=clock,
        ),
        secrets=_RejectingSecretProvider(), evidence_replay=repository,
        authenticator=authenticator,
        clock=clock, git_remote=ScopedGitRemoteReader(),
        modal_reads=facade,
        training_resolver=_RejectingTrainingResolver(),
    )
    return record, prepared, authority, ports


def _reconcile(
    context, project_ref: str, run_id: str, authority_token: object, *, token_id: str,
    token_secret: str, sdk_loader: Callable[[], object], clock: Callable[[], str],
) -> dict[str, object]:
    admitted = _authorized_run(
        context, project_ref, run_id, authority_token, verb="reconcile",
        token_id=token_id, token_secret=token_secret, sdk_loader=sdk_loader, clock=clock,
    )
    if type(admitted) is dict:
        return admitted
    record, prepared, authority, ports = admitted
    modal_api = importlib.import_module("synaptic_tuner.api.v1.modal")
    operations = modal_api.compose_modal_training_operations(
        context=context, host_ports=ports, provider_config=authority.state.profile,
    )
    outcome = importlib.import_module("synaptic_tuner.api.v1").TrainingAPI(
        operations
    ).outcome(_submission(record, prepared))
    return _result(
        "OK", run_id=run_id, project_ref=project_ref,
        observation="public_training_outcome",
        state=outcome.status.state.value, updated_at=outcome.status.updated_at,
        plan_fingerprint=prepared.public_plan_fingerprint,
        artifacts=tuple(item.artifact_id for item in outcome.artifacts),
    )


def _retrieve(
    context, project_ref: str, run_id: str, authority_token: object, *, token_id: str,
    token_secret: str, sdk_loader: Callable[[], object], clock: Callable[[], str],
) -> dict[str, object]:
    admitted = _authorized_run(
        context, project_ref, run_id, authority_token, verb="retrieve",
        token_id=token_id, token_secret=token_secret, sdk_loader=sdk_loader, clock=clock,
    )
    if type(admitted) is dict:
        return admitted
    _record, prepared, authority, repository, authenticator, facade = admitted
    api = importlib.import_module("synaptic_tuner.api.v1")
    modal_api = importlib.import_module("synaptic_tuner.api.v1.modal")
    from .modal_artifact_retrieval import retrieve_verified_artifacts

    reads = modal_api.compose_modal_verified_run_reads(
        context=context, repository=repository, authenticator=authenticator,
        modal_reads=facade, clock=clock,
    )
    receipt = retrieve_verified_artifacts(
        project_root=context.project_root,
        runs=api.RunsAPI(reads), run=api.TrainingRunRef(run_id, project_ref),
        plan_fingerprint=prepared.public_plan_fingerprint,
    )
    return _result(
        "OK", run_id=run_id, project_ref=project_ref,
        observation="verified_artifact_retrieval", **receipt,
    )


def main(
    argv: list[str], *, project_root: Path, engine_root: Path,
    sdk_loader: Callable[[], object] = modal_sdk.load_modal_sdk,
    clock: Callable[[], str] | None = None,
) -> int:
    parsed = _parse(argv)
    if parsed is None:
        return _emit(_result("COMMAND_INVALID"))
    verb, run_id = parsed
    try:
        project = Path(project_root).resolve(strict=True)
        engine = Path(engine_root).resolve(strict=True)
        from .cli import _establish_engine_import_root
        _establish_engine_import_root(engine)
        manifest, context = _project_context(project, engine)
        project_ref = manifest.project_id
        if verb == "status":
            return _emit(_local_status(context, project_ref, run_id))
        from . import launcher
        request_digest = _request_digest(verb, run_id)
        child = launcher.ensure_and_reexec(
            project_root=project, engine_root=engine, argv=argv,
            ingress_digest=request_digest,
            contract_identity_digest=_CONTRACT_DIGEST,
        )
        if type(child) is int:
            return child
        selected_clock = clock
        if selected_clock is None:
            from .security import utc_now
            selected_clock = utc_now
        credentials = tuple(os.environ.get(name, "") for name in (
            "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"
        ))
        operation = _reconcile if verb == "reconcile" else _retrieve
        return _emit(operation(
            context, project_ref, run_id, child, token_id=credentials[0],
            token_secret=credentials[1], sdk_loader=sdk_loader, clock=selected_clock,
        ))
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        return _emit(_result("OPERATION_UNAVAILABLE", run_id=run_id))


__all__ = ["main"]
