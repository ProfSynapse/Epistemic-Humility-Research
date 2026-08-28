"""Same-process Docker control reference store.

Coordination is guaranteed only for adapters sharing this exact store instance.
Restart durability and cross-process coordination are intentionally out of scope.
"""

from __future__ import annotations

import re
from threading import RLock

from .control_contract import (
    DockerAdmissionDispositionV1,
    DockerAdmissionResultV1,
    DockerCASDispositionV1,
    DockerCASResultV1,
    DockerExpectedCreatePublishDispositionV1,
    DockerExpectedCreatePublishRequestV1,
    DockerExpectedCreatePublishResultV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    _fail,
    _snapshot_authenticated,
)


_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _expected(value):
    return _snapshot_authenticated(value)


def _record(value):
    return _snapshot_authenticated(value)


def _publish_request(value):
    if type(value) is not DockerExpectedCreatePublishRequestV1:
        _fail()
    return DockerExpectedCreatePublishRequestV1(
        value.engine_command_digest, value.labels_digest,
        _expected(value.candidate), value.request_digest,
    )


def _admission_request(value):
    if type(value) is not DockerMutationAdmissionRequestV1:
        _fail()
    return DockerMutationAdmissionRequestV1(
        value.operation_id, _record(value.candidate), value.request_digest
    )


def _cas_request(value):
    if type(value) is not DockerMutationCASRequestV1:
        _fail()
    return DockerMutationCASRequestV1(
        value.operation_id, _record(value.expected),
        _record(value.replacement), value.request_digest,
    )


class InMemoryDockerControlStoreV1:
    def __init__(self):
        self._lock = RLock()
        self._catalog = {}
        self._mutations = {}

    def __repr__(self):
        with self._lock:
            return (
                "InMemoryDockerControlStoreV1("
                f"catalog_entries={len(self._catalog)}, "
                f"mutation_entries={len(self._mutations)})"
            )

    def publish_once(self, request):
        request = _publish_request(request)
        key = (request.engine_command_digest, request.labels_digest)
        with self._lock:
            current = self._catalog.get(key)
            if current is None:
                stored = _expected(request.candidate)
                self._catalog[key] = stored
                disposition = DockerExpectedCreatePublishDispositionV1.PUBLISHED
                returned = _expected(stored)
            elif current == request.candidate:
                disposition = DockerExpectedCreatePublishDispositionV1.EXISTING
                returned = _expected(current)
            else:
                disposition = DockerExpectedCreatePublishDispositionV1.CONFLICT
                returned = _expected(current)
        return DockerExpectedCreatePublishResultV1.build(
            _publish_request(request), disposition, returned
        )

    def resolve(self, engine_command_digest, labels_digest):
        if (
            type(engine_command_digest) is not str
            or type(labels_digest) is not str
            or _SHA.fullmatch(engine_command_digest) is None
            or _SHA.fullmatch(labels_digest) is None
        ):
            _fail()
        with self._lock:
            current = self._catalog.get((engine_command_digest, labels_digest))
            return None if current is None else _expected(current)

    def admit(self, request):
        request = _admission_request(request)
        with self._lock:
            current = self._mutations.get(request.operation_id)
            if current is None:
                stored = _record(request.candidate)
                self._mutations[request.operation_id] = stored
                disposition = DockerAdmissionDispositionV1.ADMITTED
                returned = _record(stored)
            elif (
                current.content.control_intent_proof_digest
                == request.candidate.content.control_intent_proof_digest
            ):
                disposition = DockerAdmissionDispositionV1.EXISTING
                returned = _record(current)
            else:
                disposition = DockerAdmissionDispositionV1.CONFLICT
                returned = _record(current)
        return DockerAdmissionResultV1.build(
            _admission_request(request), disposition, returned
        )

    def compare_and_swap(self, request):
        request = _cas_request(request)
        with self._lock:
            current = self._mutations.get(request.operation_id)
            if current is None:
                disposition = DockerCASDispositionV1.INDETERMINATE
                returned = None
            elif current == request.expected:
                stored = _record(request.replacement)
                self._mutations[request.operation_id] = stored
                disposition = DockerCASDispositionV1.APPLIED
                returned = _record(stored)
            else:
                disposition = DockerCASDispositionV1.CURRENT
                returned = _record(current)
        return DockerCASResultV1.build(
            _cas_request(request), disposition, returned
        )

    def lookup(self, operation_id):
        if type(operation_id) is not str or _SHA.fullmatch(operation_id) is None:
            _fail()
        with self._lock:
            current = self._mutations.get(operation_id)
            disposition = (
                DockerMutationLookupDispositionV1.ABSENT
                if current is None else DockerMutationLookupDispositionV1.FOUND
            )
            returned = None if current is None else _record(current)
        return DockerMutationLookupResultV1.build(
            operation_id, disposition, returned
        )


__all__: tuple[str, ...] = ()
