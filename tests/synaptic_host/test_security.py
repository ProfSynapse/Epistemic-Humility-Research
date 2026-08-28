from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import synaptic_host.security as security
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


def authenticator(tmp_path: Path) -> FileHmacAuthenticator:
    return FileHmacAuthenticator(
        (tmp_path / "state" / "evidence-hmac.key").resolve(),
        key_ref="test-evidence-v1",
    )


def test_host_hmac_key_is_private_stable_and_remote_compatible(tmp_path: Path) -> None:
    value = FileHmacAuthenticator.from_context(context(tmp_path))
    value.initialize()
    first = value.encoded_key
    value.initialize()
    assert value.encoded_key == first
    tag = value.sign("purpose/v1", b"payload", "modal-evidence-v1")
    assert value.verify("purpose/v1", b"payload", tag, "modal-evidence-v1")
    assert not value.verify("purpose/v1", b"other", tag, "modal-evidence-v1")


def test_initialize_uses_binary_exclusive_create_and_preserves_lf_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    generated = b"A\nB" + b"x" * 29
    platform_binary_flag = getattr(os, "O_BINARY", 0)
    binary_flag = platform_binary_flag or 0x8000
    real_open = os.open
    seen: list[tuple[int, int]] = []

    monkeypatch.setattr(security.os, "O_BINARY", binary_flag, raising=False)

    def recording_open(path, flags, mode=0o777):
        seen.append((flags, mode))
        return real_open(
            path,
            (flags & ~binary_flag) | platform_binary_flag,
            mode,
        )

    monkeypatch.setattr(security.os, "open", recording_open)
    monkeypatch.setattr(security.secrets, "token_bytes", lambda size: generated)

    value.initialize()

    assert value.key_path.read_bytes() == generated
    assert len(seen) == 1
    flags, mode = seen[0]
    assert flags & binary_flag
    assert flags & os.O_WRONLY
    assert flags & os.O_CREAT
    assert flags & os.O_EXCL
    assert mode == 0o600


def test_initialize_completes_short_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    generated = bytes(range(32))
    real_write = os.write
    writes: list[int] = []

    def short_write(descriptor, remaining):
        count = min(3, len(remaining))
        writes.append(count)
        return real_write(descriptor, remaining[:count])

    monkeypatch.setattr(security.secrets, "token_bytes", lambda size: generated)
    monkeypatch.setattr(security.os, "write", short_write)

    value.initialize()

    assert value.key_path.read_bytes() == generated
    assert len(writes) > 1


@pytest.mark.parametrize("failure", ["zero", "raised"])
def test_initialize_cleans_up_write_failure_and_can_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    value = authenticator(tmp_path)
    real_write = os.write
    first = True

    def failing_write(descriptor, remaining):
        nonlocal first
        if first:
            first = False
            if failure == "zero":
                return 0
            raise OSError("synthetic write failure")
        return real_write(descriptor, remaining)

    monkeypatch.setattr(security.os, "write", failing_write)

    with pytest.raises(OSError):
        value.initialize()

    assert not value.key_path.exists()
    value.initialize()
    assert len(value.key_path.read_bytes()) == 32


@pytest.mark.parametrize("failure", ["generation", "fsync", "close", "validation"])
def test_initialize_cleans_up_post_create_failure_and_can_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    value = authenticator(tmp_path)
    failed = False

    if failure == "generation":
        real_operation = security.secrets.token_bytes

        def fail_once(size):
            nonlocal failed
            if not failed:
                failed = True
                raise RuntimeError("synthetic generation failure")
            return real_operation(size)

        monkeypatch.setattr(security.secrets, "token_bytes", fail_once)
    elif failure == "fsync":
        real_operation = os.fsync

        def fail_once(descriptor):
            nonlocal failed
            if not failed:
                failed = True
                raise OSError("synthetic fsync failure")
            return real_operation(descriptor)

        monkeypatch.setattr(security.os, "fsync", fail_once)
    elif failure == "close":
        real_operation = os.close

        def fail_once(descriptor):
            nonlocal failed
            real_operation(descriptor)
            if not failed:
                failed = True
                raise OSError("synthetic close failure")

        monkeypatch.setattr(security.os, "close", fail_once)
    else:
        real_operation = FileHmacAuthenticator._key

        def fail_once(instance, key_ref=None):
            nonlocal failed
            if not failed:
                failed = True
                raise ValueError("synthetic validation failure")
            return real_operation(instance, key_ref)

        monkeypatch.setattr(FileHmacAuthenticator, "_key", fail_once)

    with pytest.raises((OSError, RuntimeError, ValueError), match=failure):
        value.initialize()

    assert not value.key_path.exists()
    value.initialize()
    assert len(value.key_path.read_bytes()) == 32


def test_initialize_preserves_replacement_when_close_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    replacement = tmp_path / "replacement.key"
    replacement_bytes = b"r" * 32
    real_close = os.close

    def replace_then_fail(descriptor):
        real_close(descriptor)
        replacement.write_bytes(replacement_bytes)
        os.replace(replacement, value.key_path)
        raise OSError("synthetic close failure")

    monkeypatch.setattr(security.os, "close", replace_then_fail)

    with pytest.raises(OSError, match="synthetic close failure"):
        value.initialize()

    assert value.key_path.read_bytes() == replacement_bytes


def test_initialize_rejects_different_valid_replacement_without_deleting_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    generated = b"g" * 32
    replacement_bytes = b"r" * 32
    replacement = tmp_path / "replacement.key"
    real_close = os.close

    def replace_after_close(descriptor):
        real_close(descriptor)
        replacement.write_bytes(replacement_bytes)
        os.replace(replacement, value.key_path)

    monkeypatch.setattr(security.secrets, "token_bytes", lambda size: generated)
    monkeypatch.setattr(security.os, "close", replace_after_close)

    with pytest.raises(ValueError, match="publication failed") as caught:
        value.initialize()

    assert generated.hex() not in str(caught.value)
    assert repr(generated) not in str(caught.value)
    assert value.key_path.read_bytes() == replacement_bytes


def test_initialize_preserves_primary_error_when_close_and_cleanup_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    real_close = os.close

    def fail_write(descriptor, remaining):
        raise OSError("primary write failure")

    def close_then_fail(descriptor):
        real_close(descriptor)
        raise OSError("secondary close failure")

    def fail_unlink(path):
        raise OSError("secondary cleanup failure")

    monkeypatch.setattr(security.os, "write", fail_write)
    monkeypatch.setattr(security.os, "close", close_then_fail)
    monkeypatch.setattr(security.os, "unlink", fail_unlink)

    with pytest.raises(OSError, match="primary write failure") as caught:
        value.initialize()

    assert "secondary" not in str(caught.value)
    assert value.key_path.exists()


@pytest.mark.parametrize("existing", ["valid", "malformed", "directory"])
def test_initialize_never_removes_a_preexisting_path(
    tmp_path: Path, existing: str
) -> None:
    value = authenticator(tmp_path)
    value.key_path.parent.mkdir(parents=True)
    if existing == "directory":
        value.key_path.mkdir()
    else:
        value.key_path.write_bytes(b"v" * 32 if existing == "valid" else b"bad")

    if existing == "valid":
        value.initialize()
        assert value.key_path.read_bytes() == b"v" * 32
    else:
        with pytest.raises((OSError, ValueError)):
            value.initialize()
        assert value.key_path.exists()


def test_initialize_never_removes_a_preexisting_symlink(tmp_path: Path) -> None:
    value = authenticator(tmp_path)
    value.key_path.parent.mkdir(parents=True)
    target = tmp_path / "target.key"
    target.write_bytes(b"t" * 32)
    try:
        value.key_path.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="regular file"):
        value.initialize()

    assert value.key_path.is_symlink()
    assert target.read_bytes() == b"t" * 32


def test_concurrent_initialization_never_corrupts_or_removes_published_key(
    tmp_path: Path,
) -> None:
    value = authenticator(tmp_path)

    def initialize() -> type[BaseException] | None:
        try:
            value.initialize()
        except BaseException as error:
            return type(error)
        return None

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes = tuple(pool.map(lambda _: initialize(), range(32)))

    assert None in outcomes
    assert all(
        outcome is None or issubclass(outcome, (OSError, ValueError))
        for outcome in outcomes
    )
    assert len(value.key_path.read_bytes()) == 32


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
