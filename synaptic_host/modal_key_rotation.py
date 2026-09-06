"""synaptic_host/modal_key_rotation.py

The two operator key-rotation procedures for the Modal evidence keys.

Section 29.3 ruling (1) states two rotation obligations and says the first is
not optional.  This module is the checked-in form of both, so the operator
runs a named procedure instead of a remembered sequence of file deletions.

Who calls this.  Nothing in the request path does.  `modal_training.py` and
`modal_provider.py` construct and use the two authenticators; this module only
retires them.  `rotate_host_evidence_key` runs in the operator step that
creates the isolated object set, before the smoke.  `retire_worker_channel`
runs at closeout, against a live `ExplicitModalHostSession` from
`modal_provider.py`.

Why a delete has to come first.  `FileHmacAuthenticator.initialize()` creates
with `O_EXCL` and, on `FileExistsError`, reads the existing key back and
returns it.  So `initialize()` alone is a read, never a rotation.  The key
file must be gone before `initialize()` can mint new material.  That ordering
is the whole content of `rotate_host_evidence_key`, and it is what its test
pins.

What this module never does.  It never reads key material, never derives
anything from it, and never reports its length.  A key file is removed by
path; a key file is created by the production primitive.  No byte of either
key passes through this module.
"""

from __future__ import annotations

from pathlib import Path

from synaptic_tuner.api.v1 import ProjectContext

from .modal_provider import build_worker_authenticator
from .security import HOST_EVIDENCE_KEY_REF, FileHmacAuthenticator


def _remove_key_file(path: Path) -> bool:
    """Unlink one key file by path, and report whether one was there.

    `Path.unlink` removes a symbolic link itself rather than its target, so a
    substituted link cannot redirect this deletion outside the private
    directory.  An absent file is not an error: both procedures below are
    required to be correct on a host that has never held the key.
    """

    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


def rotate_host_evidence_key(context: ProjectContext) -> FileHmacAuthenticator:
    """Retire `state_root/modal/evidence-hmac.key` and mint a fresh one.

    The first of the two obligations in 29.3, and the one that is not
    optional.  The Secret in the live provider environment was created on
    2026-08-26 by a code path that uploaded the host key, and its contents
    were deliberately left unmeasured, so the host key must be treated as
    already outside the Host.

    This procedure is correct whether or not the old host key is in the live
    Secret, because it does not consult the Secret at all.  After R1 the host
    key is never uploaded, so a rotated host key is out of the container's
    reach by construction; whatever the old Secret holds becomes material for
    a reference this Host no longer signs anything under.  The Secret's own
    disposal is the second procedure's business, not this one's.

    Returns the authenticator bound to the fresh key so a caller can read its
    `key_ref` and `key_path`.  It carries no key material.
    """

    authenticator = FileHmacAuthenticator.from_context(
        context, key_ref=HOST_EVIDENCE_KEY_REF
    )
    _remove_key_file(authenticator.key_path)
    authenticator.initialize()
    return authenticator


def retire_worker_channel(session, *, context: ProjectContext) -> None:
    """Delete the provider Secret and the local worker key, in that order.

    The second obligation in 29.3.  The ruling requires the two to go
    together: deleting one without the other leaves a live channel key with no
    local counterpart, or the reverse.

    The order is load-bearing and is the safe half of the pair.  The Secret is
    deleted FIRST, so a failure part-way through leaves an orphaned local key
    file with no live channel behind it, which is inert.  The reverse order
    would leave the live channel key with nothing on the Host to retire it
    with, which is the state the ruling names as the failure.

    `allow_missing=True` makes the Secret deletion idempotent, so a second run
    after a partial first run completes the pair instead of raising.  The
    local deletion is idempotent for the same reason.

    Takes the session rather than building one, because the session already
    owns the SDK handle, the environment name and the authenticated client,
    and this procedure must act on exactly the environment that was deployed.
    """

    session.sdk.Secret.objects.delete(
        session.config.runtime_secret_name,
        allow_missing=True,
        environment_name=session.config.environment_name,
        client=session.client,
    )
    _remove_key_file(build_worker_authenticator(context).key_path)
