from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

import pytest

import synaptic_host
import synaptic_host.publication_composition as composition
from synaptic_host.artifact_destinations import (
    DestinationAdapterInstallationV1,
    DestinationAdapterRegistrationV1,
)
from synaptic_host.artifact_spool import LocalArtifactSpoolCleanupStatusV1
from synaptic_host.publication_composition import (
    HostPublicationFacadeV1,
    PublicationConfigurationDocumentsV1,
    compose_host_publication_v1,
)
from synaptic_host.publication_store import SqlitePublicationStoreV1
from synaptic_tuner.api.v1 import (
    ArtifactDestination,
    DestinationPage,
    ProjectContext,
    PublicationPage,
    PublicationRef,
    PublicationRequest,
    PublicationResult,
    PublicationState,
    PublicationVerification,
    RunsAPI,
    TrainingRunRef,
)
from synaptic_tuner.api.v1.publication import PublicationOperationsV1


class _RunsOperations:
    pass


def _registration() -> DestinationAdapterRegistrationV1:
    def factory(configuration_bytes):
        return object()

    return DestinationAdapterRegistrationV1(
        "host.local/v1",
        "synaptic-local-artifact-destination/v1",
        object,
        factory,
    )


def _installation(
    registration=None, trace=None, label="adapter", failed=False,
    on_cleanup=None,
) -> DestinationAdapterInstallationV1:
    selected_trace = trace if trace is not None else []

    def cleanup():
        selected_trace.append(f"cleanup-{label}")
        if on_cleanup is not None:
            on_cleanup()
        if failed:
            raise OSError("private adapter detail")
        return True

    return DestinationAdapterInstallationV1(
        registration or _registration(), cleanup
    )


class _Spool:
    def __init__(self, trace=None, failed=False, on_cleanup=None):
        self.trace = trace if trace is not None else []
        self.failed = failed
        self.on_cleanup = on_cleanup

    def cleanup_owned(self):
        self.trace.append("cleanup-spool")
        if self.on_cleanup is not None:
            self.on_cleanup()
        status = (
            LocalArtifactSpoolCleanupStatusV1.CLEANED_WITH_FAILURES
            if self.failed else LocalArtifactSpoolCleanupStatusV1.CLEANED
        )
        return SimpleNamespace(status=status)


def _context(tmp_path: Path) -> ProjectContext:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    return ProjectContext.host(engine_root=engine, project_root=project)


@pytest.fixture(autouse=True)
def _installation_contract(monkeypatch):
    monkeypatch.setattr(composition, "_spool_type", lambda: _Spool)


def _operations() -> PublicationOperationsV1:
    return PublicationOperationsV1(
        store=object(), destinations=object(), sources=object(), spool=object(),
        authority=object(), clock=lambda: "2026-08-31T00:00:00Z",
    )


def _facade(tmp_path: Path, installations=(), spool=None) -> HostPublicationFacadeV1:
    store = SqlitePublicationStoreV1(tmp_path / "state" / "training.sqlite3")
    return HostPublicationFacadeV1(
        _operations(), store, tuple(installations), spool or _Spool()
    )


def _results():
    run = TrainingRunRef("run-1", "project-1")
    ref = PublicationRef("publication-1", "destination-1")
    request = PublicationRequest(run, "destination-1")
    result = PublicationResult(
        "synaptic-publication-result/v1", ref, run,
        PublicationState.VERIFIED,
    )
    return run, ref, request, result


def test_five_methods_delegate_directly_with_exact_results(tmp_path, monkeypatch):
    _run, ref, request, result = _results()
    destinations = DestinationPage((ArtifactDestination("destination-1", "Local"),))
    publications = PublicationPage((result,))
    verification = PublicationVerification(ref, True, "2026-08-31T00:00:00Z")
    calls = []

    monkeypatch.setattr(
        PublicationOperationsV1, "destinations",
        lambda self: calls.append(("destinations",)) or destinations,
    )
    monkeypatch.setattr(
        PublicationOperationsV1, "publications",
        lambda self, value: calls.append(("publications", value)) or publications,
    )
    monkeypatch.setattr(
        PublicationOperationsV1, "publish",
        lambda self, value: calls.append(("publish", value)) or result,
    )
    monkeypatch.setattr(
        PublicationOperationsV1, "verify",
        lambda self, value: calls.append(("verify", value)) or verification,
    )
    facade = _facade(tmp_path)

    assert facade.destinations() is destinations
    assert facade.publications("destination-1") is publications
    assert facade.publish(request) is result
    assert facade.verify(ref) is verification
    assert calls == [
        ("destinations",),
        ("publications", "destination-1"),
        ("publish", request),
        ("verify", ref),
    ]
    facade.close()
    for callback in (
        facade.destinations,
        lambda: facade.publications("destination-1"),
        lambda: facade.publish(request),
        lambda: facade.verify(ref),
    ):
        with pytest.raises(RuntimeError, match="facade is closed"):
            callback()


def test_close_waits_for_active_call_and_cleans_exactly_once(tmp_path, monkeypatch):
    entered = Event()
    release = Event()
    trace = []

    def blocking(_self):
        entered.set()
        assert release.wait(5)
        return DestinationPage(())

    monkeypatch.setattr(PublicationOperationsV1, "destinations", blocking)
    first = _installation(trace=trace, label="first")
    second = _installation(trace=trace, label="second")
    facade = _facade(tmp_path, (first, second), _Spool(trace))
    call = Thread(target=facade.destinations)
    close = Thread(target=facade.close)
    call.start()
    assert entered.wait(5)
    close.start()
    assert trace == []
    release.set()
    call.join(5)
    close.join(5)
    assert not call.is_alive() and not close.is_alive()
    assert trace == ["cleanup-second", "cleanup-first", "cleanup-spool"]
    facade.close()
    assert trace == ["cleanup-second", "cleanup-first", "cleanup-spool"]


def test_same_thread_close_defers_cleanup_until_outer_lease_exit(
    tmp_path, monkeypatch,
):
    trace = []
    facade = _facade(
        tmp_path, (_installation(trace=trace),), _Spool(trace)
    )

    def reentrant(_self):
        trace.append("callback-before-close")
        facade.close()
        trace.append("callback-after-close")
        return DestinationPage(())

    monkeypatch.setattr(PublicationOperationsV1, "destinations", reentrant)
    assert facade.destinations() == DestinationPage(())
    assert trace == [
        "callback-before-close",
        "callback-after-close",
        "cleanup-adapter",
        "cleanup-spool",
    ]
    facade.close()
    assert trace.count("cleanup-adapter") == 1
    assert trace.count("cleanup-spool") == 1


def test_nested_same_thread_close_cleans_only_after_outermost_exit(
    tmp_path, monkeypatch,
):
    trace = []
    facade = _facade(
        tmp_path, (_installation(trace=trace),), _Spool(trace)
    )

    def nested(_self, destination_ref):
        trace.append("nested-before-close")
        facade.close()
        trace.append("nested-after-close")
        return PublicationPage(())

    def outer(_self):
        trace.append("outer-before-nested")
        assert facade.publications("destination-1") == PublicationPage(())
        trace.append("outer-after-nested")
        with pytest.raises(RuntimeError, match="facade is closed"):
            facade.destinations()
        return DestinationPage(())

    monkeypatch.setattr(PublicationOperationsV1, "publications", nested)
    monkeypatch.setattr(PublicationOperationsV1, "destinations", outer)
    assert facade.destinations() == DestinationPage(())
    assert trace == [
        "outer-before-nested",
        "nested-before-close",
        "nested-after-close",
        "outer-after-nested",
        "cleanup-adapter",
        "cleanup-spool",
    ]


def test_external_close_converges_with_reentrant_close_request(
    tmp_path, monkeypatch,
):
    entered = Event()
    release = Event()
    trace = []
    facade = _facade(
        tmp_path, (_installation(trace=trace),), _Spool(trace)
    )

    def reentrant(_self):
        facade.close()
        entered.set()
        assert release.wait(5)
        return DestinationPage(())

    monkeypatch.setattr(PublicationOperationsV1, "destinations", reentrant)
    call = Thread(target=facade.destinations)
    external = Thread(target=facade.close)
    call.start()
    assert entered.wait(5)
    external.start()
    assert trace == []
    release.set()
    call.join(5)
    external.join(5)
    assert not call.is_alive() and not external.is_alive()
    assert trace == ["cleanup-adapter", "cleanup-spool"]


def test_reentrant_cleanup_failure_preserves_result_and_is_cached(
    tmp_path, monkeypatch,
):
    trace = []
    facade = _facade(
        tmp_path,
        (_installation(trace=trace, failed=True),),
        _Spool(trace),
    )

    def reentrant(_self):
        facade.close()
        return DestinationPage(())

    monkeypatch.setattr(PublicationOperationsV1, "destinations", reentrant)
    assert facade.destinations() == DestinationPage(())
    assert trace == ["cleanup-adapter", "cleanup-spool"]
    for _ in range(2):
        with pytest.raises(RuntimeError, match="^host publication cleanup failed$"):
            facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]


def test_installation_cleanup_can_reenter_close_without_deadlock(tmp_path):
    trace = []
    holder = {}
    installation = _installation(
        trace=trace,
        on_cleanup=lambda: holder["facade"].close(),
    )
    facade = _facade(tmp_path, (installation,), _Spool(trace))
    holder["facade"] = facade
    facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]
    facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]


def test_spool_cleanup_can_reenter_close_without_deadlock(tmp_path):
    trace = []
    holder = {}
    spool = _Spool(
        trace,
        on_cleanup=lambda: holder["facade"].close(),
    )
    facade = _facade(tmp_path, (_installation(trace=trace),), spool)
    holder["facade"] = facade
    facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]
    facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]


@pytest.mark.parametrize("cleanup_failed", (False, True))
def test_cleanup_owner_reentry_and_multiple_external_waiters_converge(
    tmp_path, cleanup_failed,
):
    trace = []
    holder = {}
    cleanup_entered = Event()
    cleanup_release = Event()
    errors = []

    def reenter_and_block():
        holder["facade"].close()
        cleanup_entered.set()
        assert cleanup_release.wait(5)

    installation = _installation(
        trace=trace,
        failed=cleanup_failed,
        on_cleanup=reenter_and_block,
    )
    facade = _facade(tmp_path, (installation,), _Spool(trace))
    holder["facade"] = facade

    def close_from_waiter():
        try:
            facade.close()
        except RuntimeError as error:
            errors.append(str(error))

    waiters = [Thread(target=close_from_waiter) for _ in range(8)]
    for waiter in waiters:
        waiter.start()
    assert cleanup_entered.wait(5)
    assert any(waiter.is_alive() for waiter in waiters)
    cleanup_release.set()
    for waiter in waiters:
        waiter.join(5)
    assert all(not waiter.is_alive() for waiter in waiters)
    assert trace == ["cleanup-adapter", "cleanup-spool"]
    assert errors == (
        ["host publication cleanup failed"] * 8 if cleanup_failed else []
    )
    if cleanup_failed:
        with pytest.raises(RuntimeError, match="^host publication cleanup failed$"):
            facade.close()
    else:
        facade.close()
    assert trace == ["cleanup-adapter", "cleanup-spool"]


def test_cleanup_failure_is_sanitized_cached_and_continues(tmp_path):
    trace = []
    facade = _facade(
        tmp_path,
        (
            _installation(trace=trace, label="failed", failed=True),
            _installation(trace=trace, label="later"),
        ),
        _Spool(trace, failed=True),
    )
    for _ in range(2):
        with pytest.raises(RuntimeError, match="^host publication cleanup failed$"):
            facade.close()
    assert trace == ["cleanup-later", "cleanup-failed", "cleanup-spool"]


def _write_configs(tmp_path: Path) -> tuple[Path, Path]:
    destination = tmp_path / "artifacts.json"
    storage = tmp_path / "storage.json"
    destination.write_text(
        json.dumps({
            "schema_version": "synaptic-host-artifact-destinations/v1",
            "destinations": [{
                "schema_version": "synaptic-host-artifact-destination/v1",
                "destination_ref": "local-default",
                "display_name": "Local",
                "adapter_ref": "host.local/v1",
                "configuration": {
                    "schema_version": "synaptic-local-artifact-destination/v1",
                    "control_root_ref": "control",
                    "data_root_ref": "data",
                },
                "policy": {
                    "maximum_artifact_bytes": 1024,
                    "maximum_total_bytes": 2048,
                },
            }],
        }),
        encoding="utf-8",
    )
    storage.write_text(
        json.dumps({
            "schema_version": "synaptic-host-storage/v1",
            "roots": [{
                "root_ref": "spool",
                "location": "project://spool",
                "access": "read_create",
                "permit_ref": "permit-spool",
            }],
        }),
        encoding="utf-8",
    )
    return destination.resolve(), storage.resolve()


def test_composition_orders_permit_builders_and_project_store(
    tmp_path, monkeypatch,
):
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True)
    destination_path, storage_path = _write_configs(tmp_path)
    trace = []
    spool = _Spool(trace)
    def adapter_factory(configuration_bytes, declared_configuration_digest):
        return object()

    registration = DestinationAdapterRegistrationV1(
        "host.local/v1",
        "synaptic-local-artifact-destination/v1",
        object,
        adapter_factory,
    )
    installation = _installation(registration, trace)

    class Storage:
        def issue_root_permit(self, root_ref, **kwargs):
            trace.append(("permit", root_ref, kwargs))

        def resolve(self, root_ref):
            trace.append(("resolve", root_ref))
            return object()

    storage = Storage()
    evidence = SimpleNamespace(
        verifier=SimpleNamespace(authority_ref="publication-authority", key_ref="key-v1"),
        destinations=object(), verified_sources=object(),
    )
    monkeypatch.setattr(composition.StorageRegistryV1, "from_bytes", lambda *a, **k: storage)
    monkeypatch.setattr(composition, "create_publication_evidence_v1", lambda value: evidence)
    monkeypatch.setattr(composition, "PosixRetainedDirfdPortV1", lambda: object())
    monkeypatch.setattr(composition, "LocalFilesystemV1", lambda port, auth: object())
    monkeypatch.setattr(
        composition, "acquire_local_artifact_spool_v1",
        lambda filesystem, binding: trace.append("acquire-spool") or spool,
    )
    monkeypatch.setattr(
        composition, "ImmutableArtifactDestinationRegistryV1",
        lambda **kwargs: trace.append(("registry", kwargs["registrations"])) or object(),
    )
    monkeypatch.setattr(
        composition, "AuthenticatedVerifiedArtifactSourceV1", lambda **kwargs: object()
    )

    def builder(**kwargs):
        trace.append(("builder", kwargs))
        return installation

    facade = compose_host_publication_v1(
        context=context,
        runs=RunsAPI(_RunsOperations()),
        configuration=PublicationConfigurationDocumentsV1.from_paths(
            destination_path=destination_path, storage_path=storage_path
        ),
        spool_root_ref="spool",
        clock=lambda: "2026-08-31T00:00:00Z",
        registration_builders=(builder,),
    )
    assert facade.__class__ is HostPublicationFacadeV1
    assert (context.state_root / "training.sqlite3").is_file()
    permit = next(item for item in trace if type(item) is tuple and item[0] == "permit")
    assert permit[1] == "spool"
    assert permit[2]["authority_ref"] == "publication-authority"
    assert len(permit[2]["proof_digest"]) == 64
    builder_call = next(item for item in trace if type(item) is tuple and item[0] == "builder")
    assert builder_call[1]["storage"] is storage
    assert builder_call[1]["spool"] is spool
    assert builder_call[1]["evidence"] is evidence
    facade.close()
    assert trace[-2:] == ["cleanup-adapter", "cleanup-spool"]


def test_old_path_api_is_rejected_before_permit_or_spool(tmp_path, monkeypatch):
    context = _context(tmp_path)
    destination_path, storage_path = _write_configs(tmp_path)
    calls = []
    monkeypatch.setattr(
        composition, "create_publication_evidence_v1",
        lambda value: calls.append("evidence"),
    )

    def builder(**kwargs):
        raise AssertionError("builder must not run")

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        compose_host_publication_v1(
            context=context,
            runs=RunsAPI(_RunsOperations()),
            destination_config_path=destination_path,
            storage_config_path=storage_path,
            spool_root_ref="spool",
            clock=lambda: "2026-08-31T00:00:00Z",
            registration_builders=(builder,),
        )
    assert calls == []


@pytest.mark.parametrize(
    ("changed_call", "changed_field"),
    ((1, "st_ino"), (2, "st_ctime_ns")),
)
def test_configuration_reader_rejects_swap_restore_and_restored_mtime(
    tmp_path, monkeypatch, changed_call, changed_field,
):
    destination_path, storage_path = _write_configs(tmp_path)
    original_fstat = composition.os.fstat
    calls = 0

    def unstable(descriptor):
        nonlocal calls
        current = original_fstat(descriptor)
        calls += 1
        if calls != changed_call:
            return current
        values = {
            "st_mode": current.st_mode,
            "st_size": current.st_size,
            "st_dev": current.st_dev,
            "st_ino": current.st_ino,
            "st_mtime_ns": current.st_mtime_ns,
            "st_ctime_ns": current.st_ctime_ns,
            "st_file_attributes": getattr(current, "st_file_attributes", 0),
        }
        values[changed_field] += 1
        return SimpleNamespace(**values)

    monkeypatch.setattr(composition.os, "fstat", unstable)
    with pytest.raises(ValueError, match="document is invalid"):
        PublicationConfigurationDocumentsV1.from_paths(
            destination_path=destination_path, storage_path=storage_path
        )


@pytest.mark.parametrize(
    ("failure_phase", "expected_cleanup"),
    (
        ("builder", ["cleanup-adapter", "cleanup-spool"]),
        ("registry", ["cleanup-adapter", "cleanup-spool"]),
        ("store", ["cleanup-adapter", "cleanup-spool"]),
        ("operations", ["cleanup-store", "cleanup-adapter", "cleanup-spool"]),
    ),
)
def test_construction_rollback_cleans_every_acquired_owner_in_order(
    tmp_path, monkeypatch, failure_phase, expected_cleanup,
):
    context = _context(tmp_path)
    destination_path, storage_path = _write_configs(tmp_path)
    trace = []
    spool = _Spool(trace)

    def adapter_factory(configuration_bytes):
        return object()

    registration = DestinationAdapterRegistrationV1(
        "host.local/v1",
        "synaptic-local-artifact-destination/v1",
        object,
        adapter_factory,
    )
    installation = _installation(registration, trace)

    class Storage:
        def issue_root_permit(self, *args, **kwargs):
            return object()

        def resolve(self, root_ref):
            return object()

    evidence = SimpleNamespace(
        verifier=SimpleNamespace(authority_ref="publication-authority", key_ref="key-v1"),
        destinations=object(), verified_sources=object(),
    )
    monkeypatch.setattr(composition.StorageRegistryV1, "from_bytes", lambda *a, **k: Storage())
    monkeypatch.setattr(composition, "create_publication_evidence_v1", lambda value: evidence)
    monkeypatch.setattr(composition, "PosixRetainedDirfdPortV1", lambda: object())
    monkeypatch.setattr(composition, "LocalFilesystemV1", lambda port, auth: object())
    monkeypatch.setattr(composition, "acquire_local_artifact_spool_v1", lambda *a: spool)
    monkeypatch.setattr(
        composition, "AuthenticatedVerifiedArtifactSourceV1", lambda **kwargs: object()
    )

    def registry(**kwargs):
        if failure_phase == "registry":
            raise RuntimeError("private registry detail")
        return object()

    monkeypatch.setattr(composition, "ImmutableArtifactDestinationRegistryV1", registry)

    class Store:
        @classmethod
        def from_context(cls, selected):
            if failure_phase == "store":
                raise RuntimeError("private store detail")
            return cls()

        def close(self):
            trace.append("cleanup-store")

    monkeypatch.setattr(composition, "SqlitePublicationStoreV1", Store)
    if failure_phase == "operations":
        monkeypatch.setattr(
            composition, "PublicationOperationsV1",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("private operation detail")),
        )

    def first_builder(**kwargs):
        return installation

    def failing_builder(**kwargs):
        raise RuntimeError("private builder detail")

    builders = (
        (first_builder, failing_builder)
        if failure_phase == "builder" else (first_builder,)
    )
    with pytest.raises(RuntimeError, match="^host publication composition failed$"):
        compose_host_publication_v1(
            context=context,
            runs=RunsAPI(_RunsOperations()),
            configuration=PublicationConfigurationDocumentsV1.from_paths(
                destination_path=destination_path, storage_path=storage_path
            ),
            spool_root_ref="spool",
            clock=lambda: "2026-08-31T00:00:00Z",
            registration_builders=builders,
        )
    assert trace == expected_cleanup


def test_exports_are_narrow():
    assert synaptic_host.HostPublicationFacadeV1 is HostPublicationFacadeV1
    assert synaptic_host.compose_host_publication_v1 is compose_host_publication_v1
    assert (
        synaptic_host.DestinationAdapterInstallationV1
        is DestinationAdapterInstallationV1
    )
    assert "PublicationOperationsV1" not in synaptic_host.__all__
    assert "ArtifactsAPI" not in synaptic_host.__all__
    assert not hasattr(HostPublicationFacadeV1, "artifacts")
