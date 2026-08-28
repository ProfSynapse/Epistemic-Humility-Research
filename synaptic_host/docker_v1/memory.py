"""Same-process Docker control reference store.

Coordination is guaranteed only for adapters sharing this exact store instance.
Restart durability and cross-process coordination are intentionally out of scope.
"""

from __future__ import annotations

import re
from copy import deepcopy
from threading import RLock

from synaptic_host.bundle_io_v1.model import BundleIOCodeV1, checked_ref_v1

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
from .model import (
    AuthenticatedDockerStageBundleBindingV1,
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
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


def _stage_fail() -> None:
    raise DockerHostSourceErrorV1(
        DockerHostSourceCodeV1.STORE_CONFLICT
    )


def _stage_effect_id(value):
    try:
        return checked_ref_v1(value, BundleIOCodeV1.COMMAND_INVALID)
    except BaseException:
        _stage_fail()


class InMemoryDockerStageBundleStoreV1:
    """Same-process authenticated, convergent stage-record store."""

    def __init__(self, *, authority):
        try:
            if not callable(getattr(authority, "authenticate", None)):
                raise ValueError
            checked_ref_v1(
                authority.authority_ref, BundleIOCodeV1.AUTHENTICATION_FAILED
            )
            checked_ref_v1(
                authority.key_ref, BundleIOCodeV1.AUTHENTICATION_FAILED
            )
            self._authority = authority
            self._authority_ref = authority.authority_ref
            self._key_ref = authority.key_ref
            self._lock = RLock()
            self._records = {}
        except BaseException:
            _stage_fail()

    def __repr__(self):
        with self._lock:
            return (
                "InMemoryDockerStageBundleStoreV1("
                f"record_entries={len(self._records)})"
            )

    def _authenticated(self, value):
        try:
            if (
                type(value) is not AuthenticatedDockerStageBundleBindingV1
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
                or value.authority_ref != self._authority_ref
                or value.key_ref != self._key_ref
            ):
                raise ValueError
            baseline = deepcopy(value)
            if (
                type(baseline) is not AuthenticatedDockerStageBundleBindingV1
                or baseline != value
            ):
                raise ValueError
            presented = deepcopy(baseline)
            returned = self._authority.authenticate(presented)
            retained = deepcopy(returned)
            if (
                type(retained) is not AuthenticatedDockerStageBundleBindingV1
                or retained != baseline
                or self._authority.authority_ref != self._authority_ref
                or self._authority.key_ref != self._key_ref
            ):
                raise ValueError
            return deepcopy(baseline)
        except BaseException:
            _stage_fail()

    def put_if_absent(self, value):
        candidate = self._authenticated(value)
        key = _stage_effect_id(candidate.content.stage_effect_id)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                self._records[key] = candidate
                current = candidate
            elif current != candidate:
                _stage_fail()
        return self._authenticated(current)

    def get_by_stage_effect_id(self, stage_effect_id):
        key = _stage_effect_id(stage_effect_id)
        with self._lock:
            current = self._records.get(key)
        return None if current is None else self._authenticated(current)


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
