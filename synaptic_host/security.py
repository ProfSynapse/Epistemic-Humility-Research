"""Host-owned authentication, execution grants, and scoped Git reads."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Sequence

from synaptic_tuner.api.v1 import (
    AuthorizationRequirement,
    ExecutionGrant,
    GrantBinding,
    ProjectContext,
)
from synaptic_tuner.api.v1.sources import RepositoryLocation

_HEAD_REF = re.compile(r"^refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


class FileHmacAuthenticator:
    """HMAC boundary backed by one private host-state key file."""

    def __init__(self, key_path: Path, *, key_ref: str) -> None:
        path = Path(key_path)
        if not path.is_absolute() or not key_ref or key_ref != key_ref.strip():
            raise ValueError("absolute key path and canonical key reference are required")
        self.key_path = path.resolve(strict=False)
        self.key_ref = key_ref

    @classmethod
    def from_context(
        cls, context: ProjectContext, *, key_ref: str = "modal-evidence-v1"
    ) -> "FileHmacAuthenticator":
        if not isinstance(context, ProjectContext) or context.mode != "host":
            raise ValueError("host project context is required")
        return cls(context.state_root / "modal" / "evidence-hmac.key", key_ref=key_ref)

    def initialize(self) -> None:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                self.key_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            self._key()
            return
        try:
            value = memoryview(secrets.token_bytes(32))
            written = 0
            while written < len(value):
                count = os.write(descriptor, value[written:])
                if count <= 0:
                    raise OSError("evidence key write made no progress")
                written += count
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            pass

    def _key(self, key_ref: str | None = None) -> bytes:
        if key_ref is not None and key_ref != self.key_ref:
            raise ValueError("evidence key reference mismatch")
        metadata = self.key_path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or self.key_path.is_symlink():
            raise ValueError("evidence key must be a regular file")
        value = self.key_path.read_bytes()
        if len(value) != 32:
            raise ValueError("evidence key is invalid")
        return value

    @property
    def encoded_key(self) -> str:
        return base64.b64encode(self._key()).decode("ascii")

    def sign(self, purpose: str, payload: bytes, key_ref: str) -> bytes:
        if not isinstance(purpose, str) or not purpose or not purpose.isascii():
            raise TypeError("evidence purpose must be nonblank ASCII")
        if not isinstance(payload, bytes):
            raise TypeError("evidence payload must be bytes")
        return hmac.new(
            self._key(key_ref), purpose.encode("ascii") + b"\0" + payload,
            hashlib.sha256,
        ).digest()

    def verify(self, purpose: str, payload: bytes, tag: bytes, key_ref: str) -> bool:
        return isinstance(tag, bytes) and hmac.compare_digest(
            self.sign(purpose, payload, key_ref), tag
        )


class BoundedGrantProvider:
    """Issues one-process grants only within the configured paid-effect ceiling."""

    def __init__(self, *, maximum_cost_minor_units: int, currency: str, clock=utc_now):
        if type(maximum_cost_minor_units) is not int or maximum_cost_minor_units < 0:
            raise ValueError("maximum cost must be a non-negative integer")
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        self.maximum_cost_minor_units = maximum_cost_minor_units
        self.currency = currency.upper()
        self.clock = clock
        self._authorized: set[str] = set()

    def authorize(
        self, requirements: tuple[AuthorizationRequirement, ...]
    ) -> ExecutionGrant:
        if len(requirements) != 1:
            raise ValueError("exactly one execution authorization is required")
        requirement = requirements[0]
        if (
            requirement.operation != "training.start"
            or requirement.paid_effect is not True
            or requirement.currency != self.currency
            or requirement.maximum_cost_minor_units is None
            or requirement.maximum_cost_minor_units > self.maximum_cost_minor_units
        ):
            raise ValueError("execution requirement exceeds host authorization")
        grant = ExecutionGrant("grant-" + secrets.token_hex(16))
        self._authorized.add(grant.grant_ref)
        return grant

    def bind(self, grant, *, operation, requirements):
        if not isinstance(grant, ExecutionGrant) or grant.grant_ref not in self._authorized:
            raise ValueError("execution grant was not authorized by this host")
        self._authorized.remove(grant.grant_ref)
        self.authorize_requirement(requirements)
        issued = _parse_utc(self.clock())
        expires = issued + timedelta(minutes=5)
        return GrantBinding.from_operation(
            operation,
            issued_at=issued.strftime("%Y-%m-%dT%H:%M:%SZ"),
            expires_at=expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def authorize_requirement(self, requirements) -> None:
        if len(requirements) != 1:
            raise ValueError("exactly one execution authorization is required")
        requirement = requirements[0]
        if (
            requirement.operation != "training.start"
            or requirement.paid_effect is not True
            or requirement.currency != self.currency
            or requirement.maximum_cost_minor_units is None
            or requirement.maximum_cost_minor_units > self.maximum_cost_minor_units
        ):
            raise ValueError("execution requirement exceeds host authorization")


class ScopedGitRemoteReader:
    """Read exactly one pushed branch ref with prompts and ambient config disabled."""

    def __init__(self, runner: Callable[[Sequence[str]], bytes] | None = None) -> None:
        self._runner = runner or self._run

    @staticmethod
    def _run(argv: Sequence[str]) -> bytes:
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
            "LC_ALL": "C",
            "LANG": "C",
        }
        completed = subprocess.run(
            tuple(argv), check=True, capture_output=True, timeout=20,
            env=environment, stdin=subprocess.DEVNULL,
        )
        if len(completed.stdout) > 4096:
            raise ValueError("remote Git proof exceeded its bound")
        return completed.stdout

    def read_ref(self, *, canonical_url: str, exact_ref: str) -> bytes:
        location = RepositoryLocation.parse(canonical_url)
        if location.canonical_url != canonical_url or _HEAD_REF.fullmatch(exact_ref) is None:
            raise ValueError("canonical repository URL and exact branch ref are required")
        return self._runner(("git", "ls-remote", "--refs", canonical_url, exact_ref))
