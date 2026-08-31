"""Authenticated publication source backed only by the public Runs API."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from threading import RLock
from weakref import WeakKeyDictionary

from synaptic_tuner.api.v1 import (
    RunArtifactRequest,
    RunOutcome,
    RunsAPI,
    TrainingRunRef,
    TrainingRunState,
    VerifiedArtifact,
)
from synaptic_tuner.api.v1.publication import AuthenticatedVerifiedSourceV1

from .publication_authority import (
    PublicationEvidenceVerifierV1,
    VerifiedSourceEvidenceIssuerV1,
)


_ZERO = "0" * 64


@dataclass(frozen=True, slots=True)
class _SourcePinsV1:
    runs: RunsAPI
    operations: object
    issuer: VerifiedSourceEvidenceIssuerV1
    verifier: PublicationEvidenceVerifierV1
    show: object
    reverify: object
    artifacts: object
    issue: object
    verify: object


def _source_pin_accessors():
    pins = WeakKeyDictionary()
    lock = RLock()

    def register(owner: object, value: _SourcePinsV1) -> None:
        with lock:
            pins[owner] = value

    def get(owner: object) -> object | None:
        with lock:
            return pins.get(owner)

    return register, get


_register_source_pin, _get_source_pin = _source_pin_accessors()


def _run(value: object) -> TrainingRunRef:
    if type(value) is not TrainingRunRef:
        raise TypeError("exact training run reference is required")
    return TrainingRunRef.from_dict(value.to_dict())


def _request(value: object) -> RunArtifactRequest:
    if type(value) is not RunArtifactRequest:
        raise TypeError("exact artifact request is required")
    return RunArtifactRequest(_run(value.run), value.role, value.maximum_bytes)


def _inventory(outcome: object, run: TrainingRunRef) -> tuple[VerifiedArtifact, ...]:
    if type(outcome) is not RunOutcome:
        raise ValueError("run outcome is invalid")
    rebuilt = RunOutcome.from_dict(outcome.to_dict())
    if (
        rebuilt.run != run
        or rebuilt.state is not TrainingRunState.SUCCEEDED
        or not rebuilt.artifacts
    ):
        raise ValueError("run does not expose verified artifacts")
    artifacts = tuple(VerifiedArtifact.from_dict(item.to_dict()) for item in rebuilt.artifacts)
    roles = tuple(item.role for item in artifacts)
    if roles != tuple(sorted(roles)) or len(roles) != len(set(roles)):
        raise ValueError("verified artifact inventory is invalid")
    return artifacts


def _verification_digest(
    run: TrainingRunRef, artifacts: tuple[VerifiedArtifact, ...]
) -> str:
    payload = json.dumps(
        {
            "schema_version": "synaptic-host-verified-artifact-source/v1",
            "run": run.to_dict(),
            "artifacts": [item.to_dict() for item in artifacts],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class AuthenticatedVerifiedArtifactSourceV1:
    __slots__ = (
        "_runs", "_issuer", "_verifier", "_show", "_reverify", "_artifacts",
        "_issue", "_verify", "__weakref__",
    )

    def __init__(
        self,
        *,
        runs: RunsAPI,
        issuer: VerifiedSourceEvidenceIssuerV1,
        verifier: PublicationEvidenceVerifierV1,
    ) -> None:
        if type(runs) is not RunsAPI:
            raise TypeError("exact RunsAPI is required")
        if type(issuer) is not VerifiedSourceEvidenceIssuerV1 or type(verifier) is not PublicationEvidenceVerifierV1:
            raise TypeError("exact publication evidence boundaries are required")
        if (issuer.authority_ref, issuer.key_ref) != (verifier.authority_ref, verifier.key_ref):
            raise ValueError("publication evidence boundaries do not match")
        self._runs = runs
        self._issuer = issuer
        self._verifier = verifier
        self._show = runs.show
        self._reverify = runs.reverify
        self._artifacts = runs.artifacts
        self._issue = issuer.issue
        self._verify = verifier.verify
        self._register_pins(_SourcePinsV1(
            runs,
            runs._operations,
            issuer,
            verifier,
            self._show,
            self._reverify,
            self._artifacts,
            self._issue,
            self._verify,
        ))

    def _register_pins(
        self, pins: _SourcePinsV1, _register=_register_source_pin
    ) -> None:
        _register(self, pins)

    def _intact(self, _get=_get_source_pin) -> bool:
        try:
            pins = _get(self)
            return (
                type(pins) is _SourcePinsV1
                and self._runs is pins.runs
                and type(self._runs) is RunsAPI
                and self._runs._operations is pins.operations
                and self._issuer is pins.issuer
                and self._verifier is pins.verifier
                and type(self._issuer) is VerifiedSourceEvidenceIssuerV1
                and type(self._verifier) is PublicationEvidenceVerifierV1
                and self._show == pins.show
                and self._reverify == pins.reverify
                and self._artifacts == pins.artifacts
                and self._issue == pins.issue
                and self._verify == pins.verify
                and self._runs.show == pins.show
                and self._runs.reverify == pins.reverify
                and self._runs.artifacts == pins.artifacts
                and self._issuer.issue == pins.issue
                and self._verifier.verify == pins.verify
            )
        except BaseException:
            return False

    @staticmethod
    def _closed() -> None:
        raise ValueError("verified artifact source is invalid") from None

    def describe(self, run: TrainingRunRef) -> AuthenticatedVerifiedSourceV1:
        baseline = _run(run)
        try:
            if not self._intact():
                self._closed()
            first = self._runs.show(TrainingRunRef.from_dict(baseline.to_dict()))
            first_inventory = _inventory(first, baseline)
            if not self._intact() or _run(run) != baseline:
                self._closed()
            verification = self._runs.reverify(TrainingRunRef.from_dict(baseline.to_dict()))
            if (
                verification.run != baseline
                or verification.verified is not True
                or not self._intact()
                or _run(run) != baseline
            ):
                self._closed()
            second = self._runs.show(TrainingRunRef.from_dict(baseline.to_dict()))
            second_inventory = _inventory(second, baseline)
            if first_inventory != second_inventory or not self._intact() or _run(run) != baseline:
                self._closed()
            unsigned = AuthenticatedVerifiedSourceV1(
                "synaptic-publication-verified-source/v1",
                TrainingRunRef.from_dict(baseline.to_dict()),
                second_inventory,
                _verification_digest(baseline, second_inventory),
                self._issuer.authority_ref,
                self._issuer.key_ref,
                _ZERO,
            )
            issued = self._issuer.issue(unsigned)
            rebuilt = replace(issued)
            if (
                not self._verifier.verify(
                    "publication-verified-source/v1", rebuilt.payload,
                    rebuilt.tag, rebuilt.key_ref,
                )
                or not self._intact()
                or _run(run) != baseline
            ):
                self._closed()
            return rebuilt
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        self._closed()

    def open(self, request: RunArtifactRequest):
        baseline = _request(request)
        try:
            if not self._intact():
                self._closed()
            outcome = self._runs.show(TrainingRunRef.from_dict(baseline.run.to_dict()))
            inventory = _inventory(outcome, baseline.run)
            matches = tuple(item for item in inventory if item.role == baseline.role)
            if (
                len(matches) != 1
                or matches[0].size_bytes > baseline.maximum_bytes
                or not self._intact()
                or _request(request) != baseline
            ):
                self._closed()
            stream = self._runs.artifacts(_request(baseline))
            artifact = VerifiedArtifact.from_dict(stream.artifact.to_dict())
            if (
                _run(stream.run) != baseline.run
                or artifact != matches[0]
                or stream.maximum_bytes != baseline.maximum_bytes
                or not callable(stream.iter_bytes)
                or not self._intact()
                or _request(request) != baseline
            ):
                self._closed()
            return stream
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        self._closed()


__all__ = ["AuthenticatedVerifiedArtifactSourceV1"]
