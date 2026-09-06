"""tests/synaptic_host/test_modal_key_rotation.py

Acceptance for the two operator key-rotation procedures in
`synaptic_host/modal_key_rotation.py` (section 29.3 ruling (1)).

The gate here is RK1: the delete-first property.  `initialize()` creates with
`O_EXCL` and reads the existing key back on `FileExistsError`, so a rotation
that forgot to delete first would be a no-op that looks like a success.  RK1
runs both arms against the same fixture, so the pass is a measured difference
and not an unexercised assertion.

No key material is printed, logged, asserted by literal, or reported by
length anywhere in this file.  Where two key files must be told apart, they
are compared by a sha256 digest of the file bytes taken in-process.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import ProjectContext

from synaptic_host.modal_key_rotation import (
    retire_worker_channel,
    rotate_host_evidence_key,
)
from synaptic_host.modal_provider import (
    HOST_EVIDENCE_KEY_REF,
    WORKER_EVIDENCE_KEY_REF,
    build_worker_authenticator,
)
from synaptic_host.security import FileHmacAuthenticator


def _context(tmp_path: Path) -> ProjectContext:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    return ProjectContext.host(
        engine_root=engine,
        project_root=project,
        config_root=project / "training",
    )


def _digest(path: Path) -> str:
    """Identify a key file without ever surfacing its content."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


class _RecordingSecretObjects:
    """Records the Secret deletion without performing one."""

    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.calls: list[dict[str, object]] = []

    def delete(self, name, *, allow_missing, environment_name, client):
        self.order.append("secret")
        self.calls.append(
            {
                "name": name,
                "allow_missing": allow_missing,
                "environment_name": environment_name,
                "client": client,
            }
        )


class _FakeSession:
    """The narrow surface `retire_worker_channel` reads from a session."""

    def __init__(self, order: list[str]) -> None:
        self.objects = _RecordingSecretObjects(order)
        self.sdk = type("_Sdk", (), {"Secret": type("_Secret", (), {})})
        self.sdk.Secret.objects = self.objects
        self.config = type(
            "_Config",
            (),
            {"runtime_secret_name": "runtime-v1", "environment_name": "main"},
        )()
        self.client = object()


def test_rk1_rotation_replaces_the_host_key_and_initialize_alone_does_not(
    tmp_path: Path,
) -> None:
    """RK1 — the delete-first property, with its counter-arm.

    Arm A is the mutation: without the delete, `initialize()` reads the
    existing key back and the file is unchanged.  Arm B is the procedure.  If
    the delete were ever dropped from `rotate_host_evidence_key`, arm B would
    produce arm A's digest and this test would red.
    """

    context = _context(tmp_path)
    original = FileHmacAuthenticator.from_context(
        context, key_ref=HOST_EVIDENCE_KEY_REF
    )
    original.initialize()
    before = _digest(original.key_path)

    # Arm A: `initialize()` on its own is a read, not a rotation.
    FileHmacAuthenticator.from_context(
        context, key_ref=HOST_EVIDENCE_KEY_REF
    ).initialize()
    assert _digest(original.key_path) == before

    # Arm B: the procedure deletes first, so the material is new.
    rotated = rotate_host_evidence_key(context)
    assert rotated.key_path == original.key_path
    assert _digest(original.key_path) != before


def test_rk2_rotation_is_correct_when_the_host_has_never_held_the_key(
    tmp_path: Path,
) -> None:
    """RK2 — an absent key file is not an error; the procedure mints one."""

    context = _context(tmp_path)
    expected = context.state_root / "modal" / "evidence-hmac.key"
    assert not expected.exists()

    rotated = rotate_host_evidence_key(context)

    assert rotated.key_path == expected
    assert rotated.key_ref == HOST_EVIDENCE_KEY_REF
    assert expected.is_file()


def test_rk3_rotating_the_host_key_leaves_the_worker_key_alone(
    tmp_path: Path,
) -> None:
    """RK3 — the two keys are independent, so a host rotation is scoped.

    This is what makes the procedure correct whether or not the old host key
    is in the live Secret: the Secret's key is the WORKER key, and nothing
    here touches it.
    """

    context = _context(tmp_path)
    worker = build_worker_authenticator(context)
    worker.initialize()
    before = _digest(worker.key_path)

    rotate_host_evidence_key(context)

    assert worker.key_ref == WORKER_EVIDENCE_KEY_REF
    assert worker.key_path != (context.state_root / "modal" / "evidence-hmac.key")
    assert _digest(worker.key_path) == before


def test_rk4_closeout_deletes_the_secret_before_the_local_worker_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RK4 — both halves go, and the Secret goes first.

    The order is the safe half of the pair: a failure after the Secret
    deletion leaves an inert orphaned key file, while the reverse order would
    leave a live channel key the Host can no longer retire.
    """

    context = _context(tmp_path)
    worker = build_worker_authenticator(context)
    worker.initialize()
    assert worker.key_path.is_file()

    order: list[str] = []
    session = _FakeSession(order)
    original_unlink = Path.unlink

    def _observing_unlink(self, *args, **kwargs):
        if self == worker.key_path:
            order.append("local")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", _observing_unlink)
    retire_worker_channel(session, context=context)

    assert order == ["secret", "local"]
    assert not worker.key_path.exists()
    assert session.objects.calls == [
        {
            "name": session.config.runtime_secret_name,
            "allow_missing": True,
            "environment_name": session.config.environment_name,
            "client": session.client,
        }
    ]


def test_rk5_closeout_completes_a_partial_first_run(tmp_path: Path) -> None:
    """RK5 — idempotent on both halves, so a partial run can be finished.

    A first run that removed the Secret and then failed leaves the local key.
    A second run must delete that key and must not raise on the already
    absent Secret, which is what `allow_missing=True` buys.
    """

    context = _context(tmp_path)
    worker = build_worker_authenticator(context)
    worker.initialize()

    order: list[str] = []
    session = _FakeSession(order)

    retire_worker_channel(session, context=context)
    assert not worker.key_path.exists()

    # Second run over an already retired channel: no raise, no resurrection.
    retire_worker_channel(session, context=context)
    assert not worker.key_path.exists()
    assert len(session.objects.calls) == 2
    assert all(call["allow_missing"] is True for call in session.objects.calls)
