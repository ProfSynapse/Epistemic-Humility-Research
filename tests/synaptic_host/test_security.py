from __future__ import annotations

from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import AuthorizationRequirement, ProjectContext
from synaptic_host.security import (
    BoundedGrantProvider,
    FileHmacAuthenticator,
    ScopedGitRemoteReader,
)

NOW = "2026-08-26T12:00:00Z"


def context(tmp_path: Path) -> ProjectContext:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    return ProjectContext.host(engine_root=engine, project_root=project)


def test_host_hmac_key_is_private_stable_and_remote_compatible(tmp_path: Path) -> None:
    value = FileHmacAuthenticator.from_context(context(tmp_path))
    value.initialize()
    first = value.encoded_key
    value.initialize()
    assert value.encoded_key == first
    tag = value.sign("purpose/v1", b"payload", "modal-evidence-v1")
    assert value.verify("purpose/v1", b"payload", tag, "modal-evidence-v1")
    assert not value.verify("purpose/v1", b"other", tag, "modal-evidence-v1")


def test_grant_provider_rejects_cost_or_currency_expansion() -> None:
    value = BoundedGrantProvider(
        maximum_cost_minor_units=100, currency="USD", clock=lambda: NOW
    )
    allowed = (AuthorizationRequirement("training.start", True, 100, "USD"),)
    assert value.authorize(allowed).grant_ref.startswith("grant-")
    with pytest.raises(ValueError, match="exceeds"):
        value.authorize(
            (AuthorizationRequirement("training.start", True, 101, "USD"),)
        )
    with pytest.raises(ValueError, match="exceeds"):
        value.authorize(
            (AuthorizationRequirement("training.start", True, 100, "EUR"),)
        )


def test_scoped_git_reader_builds_only_the_closed_read_command() -> None:
    seen = []

    def runner(argv):
        seen.append(tuple(argv))
        return b"a" * 40 + b"\trefs/heads/main\n"

    value = ScopedGitRemoteReader(runner)
    assert value.read_ref(
        canonical_url="https://github.com/example/project.git",
        exact_ref="refs/heads/main",
    ).endswith(b"\n")
    assert seen == [
        (
            "git", "ls-remote", "--refs",
            "https://github.com/example/project.git", "refs/heads/main",
        )
    ]
    with pytest.raises(ValueError, match="exact branch"):
        value.read_ref(
            canonical_url="https://github.com/example/project.git",
            exact_ref="HEAD",
        )
