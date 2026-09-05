from __future__ import annotations

import hashlib
import json
import os
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
from synaptic_host.artifact_spool import (
    LocalArtifactSpoolCleanupStatusV1,
    LocalArtifactSpoolV1,
)
from synaptic_host.local_artifact_destination import (
    build_local_artifact_destination_registration_v1,
)
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
        def list_declared_roots(self):
            # Declares nothing, so `_ensure_declared_private_roots` finds no
            # creatable root under `.synaptic` and never touches the filesystem.
            return ()

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
    monkeypatch.setattr(composition, "_local_filesystem_port_v1", lambda: object())
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
        def list_declared_roots(self):
            # See the note on the sibling double: an empty declaration keeps
            # `_ensure_declared_private_roots` inert for this test.
            return ()

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
    monkeypatch.setattr(composition, "_local_filesystem_port_v1", lambda: object())
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


# ---------------------------------------------------------------------------
# B-18 (architecture section 27) -- R1-R4, the declared-root ensure.
#
# The storage and destination documents below are the bytes run 13 actually
# staged, copied in from the read-only reference stage rather than referenced
# from it, so no test reaches into a release clone.  The seven roots matter as
# a set: three are `read_create` under `.synaptic` and are what 27.3 creates;
# `opaque-training-output` (`create_only`) and `opaque-local-io-control`
# (`read_create`) are creatable but live in the operator's working tree, and
# `docker-model-inventory-source` is under `.synaptic` but is `read_only`.  A
# helper that used either half of the predicate alone would act on the wrong
# set, which is what R4 pins.
# ---------------------------------------------------------------------------

_DECLARED_ROOTS = (
    ("opaque-training-input", "project://training/input", "read_only"),
    ("opaque-training-output", "project://training/output", "create_only"),
    ("opaque-local-io-control", "project://training/.local-io-control", "read_create"),
    ("artifact-local-default", "project://.synaptic/artifacts", "read_create"),
    (
        "artifact-publication-control",
        "project://.synaptic/publication-control",
        "read_create",
    ),
    (
        "artifact-publication-spool",
        "project://.synaptic/publication-spool",
        "read_create",
    ),
    ("docker-model-inventory-source", "project://.synaptic/model-inventory", "read_only"),
)

_ENSURED_ROOTS = (
    ".synaptic/artifacts",
    ".synaptic/publication-control",
    ".synaptic/publication-spool",
)


def _write_declared_configs(tmp_path: Path, roots=_DECLARED_ROOTS) -> tuple[Path, Path]:
    destination = tmp_path / "declared-artifacts.json"
    storage = tmp_path / "declared-storage.json"
    destination.write_text(
        json.dumps({
            "schema_version": "synaptic-host-artifact-destinations/v1",
            "destinations": [{
                "schema_version": "synaptic-host-artifact-destination/v1",
                "destination_ref": "local-default",
                "display_name": "Local artifacts",
                "adapter_ref": "host.local/v1",
                "configuration": {
                    "schema_version": "synaptic-local-artifact-destination/v1",
                    "control_root_ref": "artifact-publication-control",
                    "data_root_ref": "artifact-local-default",
                },
                "policy": {
                    "maximum_artifact_bytes": 2147483648,
                    "maximum_total_bytes": 4294967296,
                },
            }],
        }),
        encoding="utf-8",
    )
    storage.write_text(
        json.dumps({
            "schema_version": "synaptic-host-storage/v1",
            "roots": [
                {
                    "root_ref": root_ref,
                    "location": location,
                    "access": access,
                    "permit_ref": f"permit-{root_ref}",
                }
                for root_ref, location, access in roots
            ],
        }),
        encoding="utf-8",
    )
    return destination.resolve(), storage.resolve()


def _compose_declared(tmp_path: Path, monkeypatch, roots=_DECLARED_ROOTS):
    # The module-level autouse `_installation_contract` fixture points
    # `_spool_type` at the `_Spool` double so the lifecycle tests can drive
    # cleanup without a real root.  R1-R4 compose the REAL spool, so the
    # production predicate at `publication_composition.py:252` has to be back
    # in place or the facade rejects its own spool.
    monkeypatch.setattr(composition, "_spool_type", lambda: LocalArtifactSpoolV1)
    context = _context(tmp_path)
    destination_path, storage_path = _write_declared_configs(tmp_path, roots)
    return compose_host_publication_v1(
        context=context,
        runs=RunsAPI(_RunsOperations()),
        configuration=PublicationConfigurationDocumentsV1.from_paths(
            destination_path=destination_path, storage_path=storage_path,
        ),
        spool_root_ref="artifact-publication-spool",
        clock=lambda: "2026-09-05T00:00:00Z",
        registration_builders=(
            build_local_artifact_destination_registration_v1,
        ),
    ), context


def test_r1_fresh_project_root_composes_and_creates_the_declared_roots(tmp_path, monkeypatch):
    """R1 (section 27.7): run 13's cut 6, as a unit test.

    Red before the change: the three declared `read_create` roots under
    `.synaptic` are never created by anything, `retain_directory` opens
    `_OPEN_EXISTING`, and the composition fails.  This is the acceptance test
    for 27.3 and the arm half of B-18.
    """

    facade, context = _compose_declared(tmp_path, monkeypatch)
    try:
        assert type(facade) is HostPublicationFacadeV1
        for relative in _ENSURED_ROOTS:
            assert (context.project_root / relative).is_dir(), relative
    finally:
        facade.close()


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory mode")
def test_r2_ensured_roots_carry_the_private_creation_mode(tmp_path, monkeypatch):
    """R2: pins the creation primitive, not merely the outcome.

    `FileHmacAuthenticator._create_private_directory` is `os.mkdir(path,
    0o700)` on this branch, so a helper that created the directories with any
    other primitive (or with default permissions) reddens here even though R1
    would still pass.
    """

    facade, context = _compose_declared(tmp_path, monkeypatch)
    try:
        for relative in _ENSURED_ROOTS:
            mode = (context.project_root / relative).stat().st_mode & 0o777
            assert mode == 0o700, (relative, oct(mode))
    finally:
        facade.close()


def test_r3_pre_existing_root_is_not_repaired_or_modified(tmp_path, monkeypatch):
    """R3: "do not repair" -- an existing root is left exactly as found.

    The directory is created by the test with ordinary permissions before the
    composition runs.  27.3 forbids repair, validation and ACL narrowing, so
    the composition must succeed and must leave the mode untouched.  The
    helper therefore tests existence and skips rather than relying on the
    creation primitive being idempotent, whose Windows branch is not read here.
    """

    project = tmp_path / "project"
    (project / ".synaptic" / "publication-control").mkdir(parents=True)
    (project / ".synaptic" / "publication-control").chmod(0o755)
    before = (project / ".synaptic" / "publication-control").stat()

    facade, context = _compose_declared(tmp_path, monkeypatch)
    try:
        after = (context.project_root / ".synaptic" / "publication-control").stat()
        assert after.st_ino == before.st_ino
        if os.name == "posix":
            assert after.st_mode & 0o777 == 0o755
    finally:
        facade.close()


def test_r4_creatable_roots_outside_synaptic_are_not_created(tmp_path, monkeypatch):
    """R4: pins the `.synaptic` predicate.

    `opaque-local-io-control` and `opaque-training-output` are both creatable
    and both live in the operator's working tree.  #325 proved the first has
    no consumer anywhere in the clone, so a helper that created every
    creatable root would write two directories nothing retains into a tree the
    Host does not own.  Asserting their absence is what would have caught that.
    """

    facade, context = _compose_declared(tmp_path, monkeypatch)
    try:
        assert not (context.project_root / "training" / ".local-io-control").exists()
        assert not (context.project_root / "training" / "output").exists()
        assert not (context.project_root / "training").exists()
        assert not (context.project_root / ".synaptic" / "model-inventory").exists()
    finally:
        facade.close()


def test_c2_composition_failure_carries_the_original_as_its_cause(
    tmp_path: Path, monkeypatch,
) -> None:
    """C2 of section 27.7 (site 1).

    Run 13's cut 6 reported the swallowing site and nothing else, because the
    handler at the end of `compose_host_publication_v1` raised `from None`.  The
    forced failure here stands in for whatever fails inside the try block: what
    is pinned is that the original reaches the caller as `__cause__`, so the
    failure stays recoverable to a debugger, to a `traceback` printer and to any
    future chain-walking reader.  The 22.14 renderer is not one of them: it
    walks `__traceback__` alone, so restoring the chain changes nothing it
    prints (the 27.4 Correction).
    """
    failure = RuntimeError("forced inner failure")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(composition, "create_publication_evidence_v1", fail)
    context = _context(tmp_path)
    destination_path, storage_path = _write_declared_configs(tmp_path, _DECLARED_ROOTS)
    with pytest.raises(RuntimeError) as raised:
        compose_host_publication_v1(
            context=context,
            runs=RunsAPI(_RunsOperations()),
            configuration=PublicationConfigurationDocumentsV1.from_paths(
                destination_path=destination_path, storage_path=storage_path,
            ),
            spool_root_ref="artifact-publication-spool",
            clock=lambda: "2026-09-05T00:00:00Z",
            registration_builders=(build_local_artifact_destination_registration_v1,),
        )
    assert str(raised.value) == "host publication composition failed"
    assert raised.value.__cause__ is failure
