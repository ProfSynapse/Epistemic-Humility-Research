from __future__ import annotations

import os
import stat
import subprocess
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
POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor path")
WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="Windows NTFS path")


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


def test_docker_hmac_key_is_fixed_stable_and_refuses_rotation(tmp_path: Path) -> None:
    project_context = context(tmp_path)
    first = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=False,
    )
    original = first.encoded_key
    assert first.key_path == (
        project_context.state_root / "docker" / "control-hmac.key"
    ).resolve(strict=False)
    assert first.key_ref == "docker-control-v1"
    second = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=True,
    )
    assert second.encoded_key == original

    first.key_path.unlink()
    with pytest.raises(ValueError, match="missing for durable runs"):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=True,
        )


def test_docker_hmac_key_rejects_linked_directory(
    tmp_path: Path,
) -> None:
    project_context = context(tmp_path)
    target = tmp_path / "foreign"
    target.mkdir()
    docker_directory = project_context.state_root / "docker"
    docker_directory.parent.mkdir(parents=True)
    try:
        docker_directory.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    with pytest.raises(ValueError):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=False,
        )


@POSIX_ONLY
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
    creates = tuple(entry for entry in seen if entry[0] & os.O_CREAT)
    assert len(creates) == 1
    flags, mode = creates[0]
    assert flags & binary_flag
    assert flags & os.O_WRONLY
    assert flags & os.O_CREAT
    assert flags & os.O_EXCL
    assert mode == 0o600


@POSIX_ONLY
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
@POSIX_ONLY
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
@POSIX_ONLY
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
            metadata = os.fstat(descriptor)
            real_operation(descriptor)
            if not failed and stat.S_ISREG(metadata.st_mode):
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


@POSIX_ONLY
def test_initialize_preserves_replacement_when_close_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    replacement = tmp_path / "replacement.key"
    replacement_bytes = b"r" * 32
    real_close = os.close

    def replace_then_fail(descriptor):
        metadata = os.fstat(descriptor)
        real_close(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            return
        replacement.write_bytes(replacement_bytes)
        os.replace(replacement, value.key_path)
        raise OSError("synthetic close failure")

    monkeypatch.setattr(security.os, "close", replace_then_fail)

    with pytest.raises(OSError, match="synthetic close failure"):
        value.initialize()

    assert value.key_path.read_bytes() == replacement_bytes


@POSIX_ONLY
def test_initialize_rejects_different_valid_replacement_without_deleting_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    generated = b"g" * 32
    replacement_bytes = b"r" * 32
    replacement = tmp_path / "replacement.key"
    real_close = os.close
    replaced = False

    def replace_after_close(descriptor):
        nonlocal replaced
        metadata = os.fstat(descriptor)
        real_close(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or replaced:
            return
        replaced = True
        replacement.write_bytes(replacement_bytes)
        os.replace(replacement, value.key_path)

    monkeypatch.setattr(security.secrets, "token_bytes", lambda size: generated)
    monkeypatch.setattr(security.os, "close", replace_after_close)

    with pytest.raises(ValueError, match="private storage") as caught:
        value.initialize()

    assert generated.hex() not in str(caught.value)
    assert repr(generated) not in str(caught.value)
    assert value.key_path.read_bytes() == replacement_bytes


@POSIX_ONLY
def test_initialize_preserves_primary_error_when_close_and_cleanup_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = authenticator(tmp_path)
    real_close = os.close

    def fail_write(descriptor, remaining):
        raise OSError("primary write failure")

    def close_then_fail(descriptor):
        metadata = os.fstat(descriptor)
        real_close(descriptor)
        if stat.S_ISREG(metadata.st_mode):
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
@POSIX_ONLY
def test_initialize_never_removes_a_preexisting_path(
    tmp_path: Path, existing: str
) -> None:
    value = authenticator(tmp_path)
    value.key_path.parent.mkdir(parents=True)
    os.chmod(value.key_path.parent, 0o700)
    if existing == "directory":
        value.key_path.mkdir()
    else:
        value.key_path.write_bytes(b"v" * 32 if existing == "valid" else b"bad")
        os.chmod(value.key_path, 0o600)

    if existing == "valid":
        value.initialize()
        assert value.key_path.read_bytes() == b"v" * 32
    else:
        with pytest.raises((OSError, ValueError)):
            value.initialize()
        assert value.key_path.exists()


@POSIX_ONLY
def test_initialize_never_removes_a_preexisting_symlink(tmp_path: Path) -> None:
    value = authenticator(tmp_path)
    value.key_path.parent.mkdir(parents=True)
    os.chmod(value.key_path.parent, 0o700)
    target = tmp_path / "target.key"
    target.write_bytes(b"t" * 32)
    try:
        value.key_path.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="private storage"):
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


def test_private_storage_property_and_every_key_operation_fail_closed_after_drift(
    tmp_path: Path,
) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    assert value.private_storage_verified is True
    tag = value.sign("purpose/v1", b"payload", "test-evidence-v1")
    value.key_path.write_bytes(b"short")

    with pytest.raises(ValueError, match="private storage"):
        _ = value.encoded_key
    with pytest.raises(ValueError, match="private storage"):
        value.sign("purpose/v1", b"payload", "test-evidence-v1")
    with pytest.raises(ValueError, match="private storage"):
        value.verify("purpose/v1", b"payload", tag, "test-evidence-v1")
    with pytest.raises(ValueError, match="private storage"):
        value.verify("purpose/v1", b"payload", object(), "test-evidence-v1")


def test_private_storage_rejects_permissive_parent_without_repair(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "permissive"
    parent.mkdir()
    key = parent / "control.key"
    key.write_bytes(b"k" * 32)
    value = FileHmacAuthenticator(key.resolve(), key_ref="test-evidence-v1")

    with pytest.raises(ValueError, match="private storage"):
        _ = value.private_storage_verified
    assert key.read_bytes() == b"k" * 32


def test_private_storage_rejects_hardlink_after_initial_acceptance(
    tmp_path: Path,
) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    assert value.private_storage_verified is True
    linked = value.key_path.with_name("linked.key")
    os.link(value.key_path, linked)

    with pytest.raises(ValueError, match="private storage"):
        _ = value.encoded_key


def test_private_storage_rejects_valid_key_replacement_for_bound_authenticator(
    tmp_path: Path,
) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    assert value.private_storage_verified is True
    replacement = FileHmacAuthenticator(
        value.key_path.with_name("replacement.key"), key_ref="replacement-v1"
    )
    replacement.initialize()
    os.replace(replacement.key_path, value.key_path)

    with pytest.raises(ValueError, match="private storage"):
        _ = value.private_storage_verified
    reopened = FileHmacAuthenticator(value.key_path, key_ref="test-evidence-v1")
    assert reopened.private_storage_verified is True


def test_private_storage_rejects_key_symlink_or_reparse_point(tmp_path: Path) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    target = value.key_path.with_name("target.key")
    target.write_bytes(b"t" * 32)
    value.key_path.unlink()
    try:
        value.key_path.symlink_to(target)
    except OSError as error:
        pytest.skip(f"file symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="private storage"):
        _ = value.private_storage_verified


@POSIX_ONLY
def test_posix_private_storage_rejects_mode_and_open_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    os.chmod(value.key_path, 0o644)
    with pytest.raises(ValueError, match="private storage"):
        _ = value.private_storage_verified
    os.chmod(value.key_path, 0o600)
    assert value.private_storage_verified is True

    replacement = value.key_path.with_name("replacement.key")
    replacement.write_bytes(b"r" * 32)
    os.chmod(replacement, 0o600)
    real_open = os.open
    replaced = False

    def replace_after_open(path, flags, mode=0o777):
        nonlocal replaced
        descriptor = real_open(path, flags, mode)
        if Path(path) == value.key_path and not replaced:
            replaced = True
            os.replace(replacement, value.key_path)
        return descriptor

    monkeypatch.setattr(security.os, "open", replace_after_open)
    with pytest.raises(ValueError, match="private storage"):
        _ = value.private_storage_verified


@WINDOWS_ONLY
def test_windows_private_storage_creation_reopen_and_default_acl_rejection(
    tmp_path: Path,
) -> None:
    value = authenticator(tmp_path)
    value.initialize()
    assert value.private_storage_verified is True
    reopened = FileHmacAuthenticator(value.key_path, key_ref="test-evidence-v1")
    assert reopened.private_storage_verified is True

    permissive_key = value.key_path.with_name("default-acl.key")
    permissive_key.write_bytes(b"p" * 32)
    permissive = FileHmacAuthenticator(permissive_key, key_ref="permissive-v1")
    with pytest.raises(ValueError, match="private storage"):
        _ = permissive.private_storage_verified


@WINDOWS_ONLY
def test_windows_docker_storage_rejects_directory_junction(tmp_path: Path) -> None:
    project_context = context(tmp_path)
    target = tmp_path / "junction-target"
    target.mkdir()
    junction = project_context.project_root / ".synaptic"
    completed = subprocess.run(
        ("cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)),
        capture_output=True, check=False,
    )
    if completed.returncode != 0:
        pytest.skip("directory junction creation unavailable")

    with pytest.raises(ValueError, match="private storage"):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=False,
        )


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


_SCRUBBED_KEYS = {
    "PATH", "GIT_TERMINAL_PROMPT", "GCM_INTERACTIVE", "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_OPTIONAL_LOCKS",
    "LC_ALL", "LANG",
}


def _captured_env(monkeypatch, *, os_name: str, environ: dict) -> dict:
    """Run the scrubbed reader against a fake child and return the env it built."""
    seen: dict = {}

    class _Completed:
        stdout = b""

    def fake_run(argv, **kwargs):
        seen.update(kwargs["env"])
        return _Completed()

    monkeypatch.setattr(security.os, "name", os_name)
    monkeypatch.setattr(security.os, "environ", environ)
    monkeypatch.setattr(security.subprocess, "run", fake_run)
    security.ScopedGitRemoteReader._run(("git", "ls-remote"))
    return seen


def test_scoped_git_reader_scrub_carries_system_root_only_on_windows(monkeypatch) -> None:
    # B-7.  Winsock cannot initialise without SystemRoot, so every remote read
    # died at DNS on Windows.  Exactly one key earns its way in.
    posix = _captured_env(
        monkeypatch, os_name="posix",
        environ={"PATH": "/usr/bin", "SystemRoot": "C:\\Windows"},
    )
    assert set(posix) == _SCRUBBED_KEYS, "the POSIX allowlist must not change"

    windows = _captured_env(
        monkeypatch, os_name="nt",
        environ={"PATH": "C:\\bin", "SystemRoot": "C:\\Windows"},
    )
    assert set(windows) == _SCRUBBED_KEYS | {"SystemRoot"}
    assert windows["SystemRoot"] == "C:\\Windows"

    # The four keys measured unnecessary stay out even when the host defines
    # them, so the scrub cannot quietly widen into a passthrough.
    defined = _captured_env(
        monkeypatch, os_name="nt",
        environ={
            "PATH": "C:\\bin", "SystemRoot": "C:\\Windows", "SystemDrive": "C:",
            "windir": "C:\\Windows", "COMSPEC": "C:\\Windows\\system32\\cmd.exe",
            "PATHEXT": ".COM;.EXE", "USERPROFILE": "C:\\Users\\x",
        },
    )
    assert set(defined) == _SCRUBBED_KEYS | {"SystemRoot"}

    # A Windows host that defines no SystemRoot must not gain a synthesised one.
    bare = _captured_env(monkeypatch, os_name="nt", environ={"PATH": "C:\\bin"})
    assert set(bare) == _SCRUBBED_KEYS


def test_scoped_git_reader_surfaces_bounded_scrubbed_stderr_on_failure(monkeypatch) -> None:
    noise = b"Z" * 4096

    def fake_run(argv, **kwargs):
        raise subprocess.CalledProcessError(
            128, argv,
            stderr=(
                b"fatal: unable to access "
                b"'https://operator:s3cret@example.com/project.git': "
                b"getaddrinfo() thread failed to start\n" + noise
            ),
        )

    monkeypatch.setattr(security.subprocess, "run", fake_run)
    with pytest.raises(ValueError) as caught:
        security.ScopedGitRemoteReader._run(("git", "ls-remote"))

    message = str(caught.value)
    assert "exit 128" in message
    # The child's own diagnosis reaches the operator instead of a bare exit code.
    assert "getaddrinfo() thread failed to start" in message
    # Bounded: a hostile remote cannot flood the log through this path.
    assert message.count("Z") < len(noise)
    assert len(message) < 700
    # Userinfo is dropped even though the reader disables helpers and prompts,
    # so a credential should never have reached this slice in the first place.
    assert "s3cret" not in message and "operator:" not in message
    assert "https://example.com/project.git" in message


# B-11 (architecture section 20.14).  W1 to W5 are Windows-only and carry the
# existing WINDOWS_ONLY skip, so under WSL they SKIP rather than pass: every
# assertion below sits unconditionally in the test body, so none of them can
# go green by vacuity on a platform that cannot execute the primitive.
OBJECT_INHERIT_ACE = 0x01
CONTAINER_INHERIT_ACE = 0x02


def windows_acl(path: Path) -> dict:
    """Read one object's owner, protection bit and entries, by handle.

    The tests read the access list themselves rather than asking
    `private_storage_verified`, because B-11-M1 measured the validator
    ACCEPTING a root whose whole subtree the path-based editor had just
    emptied.  The validator is scoped to the directory, so it can never be the
    acceptance test for a repair that must not touch the children.
    """
    import ctypes
    from ctypes import wintypes

    handle = security._win_open_path(path, directory=path.is_dir())
    try:
        owner = wintypes.LPVOID()
        dacl = wintypes.LPVOID()
        descriptor = wintypes.LPVOID()
        result = security._ADVAPI32.GetSecurityInfo(
            handle, security._SE_FILE_OBJECT,
            security._OWNER_SECURITY_INFORMATION
            | security._DACL_SECURITY_INFORMATION,
            ctypes.byref(owner), None, ctypes.byref(dacl), None,
            ctypes.byref(descriptor),
        )
        assert result == 0 and descriptor.value and owner.value and dacl.value
        try:
            control = wintypes.WORD()
            revision = wintypes.DWORD()
            assert security._ADVAPI32.GetSecurityDescriptorControl(
                descriptor, ctypes.byref(control), ctypes.byref(revision)
            )
            size = security._ACL_SIZE_INFORMATION()
            assert security._ADVAPI32.GetAclInformation(
                dacl, ctypes.byref(size), ctypes.sizeof(size),
                security._ACL_SIZE_INFORMATION_CLASS,
            )
            entries = []
            for index in range(size.AceCount):
                pointer = wintypes.LPVOID()
                assert security._ADVAPI32.GetAce(
                    dacl, index, ctypes.byref(pointer)
                )
                ace = ctypes.cast(
                    pointer, ctypes.POINTER(security._ACCESS_ALLOWED_ACE)
                ).contents
                sid_pointer = (
                    ctypes.addressof(ace)
                    + security._ACCESS_ALLOWED_ACE.SidStart.offset
                )
                entries.append({
                    "sid": security._win_sid_string(sid_pointer),
                    "type": int(ace.Header.AceType),
                    "flags": int(ace.Header.AceFlags),
                    "mask": int(ace.Mask),
                    "inherited": bool(
                        ace.Header.AceFlags & security._INHERITED_ACE
                    ),
                })
            return {
                "protected": bool(control.value & security._SE_DACL_PROTECTED),
                "owner": security._win_sid_string(owner),
                "entries": entries,
            }
        finally:
            security._KERNEL32.LocalFree(descriptor)
    finally:
        security._win_close(handle)


@WINDOWS_ONLY
def test_windows_repairs_a_chain_root_the_operator_created_first(
    tmp_path: Path,
) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()

    # Prove the FIXTURE is the state under test before repairing it.  Without
    # this the test would still pass if tmp_path happened to sit somewhere
    # that produces a different list, and it would pass for the wrong reason.
    before = windows_acl(root)
    assert before["protected"] is False
    assert before["entries"], "fixture is not the inherited-list state"
    assert all(entry["inherited"] for entry in before["entries"])
    assert before["owner"] == security._win_current_user_sid()

    value = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=False,
    )
    assert value.private_storage_verified is True

    after = windows_acl(root)
    assert after["protected"] is True
    assert after["owner"] == security._win_current_user_sid()
    assert len(after["entries"]) == 2
    assert {entry["sid"] for entry in after["entries"]} == {
        security._win_current_user_sid(), "S-1-5-18",
    }
    for entry in after["entries"]:
        assert entry["inherited"] is False
        assert entry["mask"] == security._FILE_ALL_ACCESS
        # Half of section 20.8's combination, and the half a copy-paste of the
        # CREATION descriptor would silently lose.  Without these flags the
        # children carry entries marked inherited from a parent that publishes
        # nothing, so any later propagation empties them.
        assert entry["flags"] & OBJECT_INHERIT_ACE
        assert entry["flags"] & CONTAINER_INHERIT_ACE


@WINDOWS_ONLY
def test_windows_repair_is_idempotent(tmp_path: Path) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()

    FileHmacAuthenticator.for_docker(project_context, durable_rows_exist=False)
    first = windows_acl(root)

    again = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=True,
    )
    assert again.private_storage_verified is True
    assert windows_acl(root) == first


@WINDOWS_ONLY
def test_windows_refuses_a_chain_directory_carrying_an_explicit_entry(
    tmp_path: Path,
) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()
    completed = subprocess.run(
        ("icacls", str(root), "/grant", "*S-1-5-32-545:(RX)"),
        capture_output=True, check=False,
    )
    if completed.returncode != 0:
        pytest.skip("explicit access entry could not be written")

    before = windows_acl(root)
    explicit = [
        entry for entry in before["entries"] if not entry["inherited"]
    ]
    assert explicit, "fixture did not produce a non-inherited entry"

    with pytest.raises(ValueError, match="private storage"):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=False,
        )

    # Somebody made a decision on this object.  The entry is still there,
    # which is what proves the repair did not act rather than acted and failed.
    after = windows_acl(root)
    assert after["protected"] is False
    assert [
        entry for entry in after["entries"] if not entry["inherited"]
    ] == explicit


@WINDOWS_ONLY
def test_windows_refuses_a_chain_directory_already_protected_wrongly(
    tmp_path: Path,
) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()
    completed = subprocess.run(
        ("icacls", str(root), "/inheritance:r",
         "/grant", "*S-1-5-32-545:(F)"),
        capture_output=True, check=False,
    )
    if completed.returncode != 0:
        pytest.skip("protected access list could not be written")

    before = windows_acl(root)
    assert before["protected"] is True

    # Protection is only ever set deliberately, so this is the tampered state
    # and it stays refused with today's error.
    with pytest.raises(ValueError, match="private storage"):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=False,
        )
    assert windows_acl(root) == before


@WINDOWS_ONLY
def test_windows_populated_chain_survives_the_repair(tmp_path: Path) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()
    inventory = root / "model-inventory"
    inventory.mkdir()
    child = inventory / "probe.txt"
    child.write_bytes(b"inventory")

    before_child = windows_acl(child)
    before_inventory = windows_acl(inventory)

    FileHmacAuthenticator.for_docker(project_context, durable_rows_exist=False)

    # The regression guard for the propagation hazard.  This reads the CHILD,
    # not the validator: the path-based editor left the root acceptable to the
    # validator while emptying every list below it, so asking the validator
    # here would report success on a destroyed tree.
    #
    # Section 20.14 W5 pins the FILE, and the file is untouched: same content,
    # byte-identical list, still inherited and still unprotected.
    assert child.read_bytes() == b"inventory"
    assert windows_acl(child) == before_child

    # The intermediate DIRECTORY is a measured exception the ruling did not
    # anticipate.  Setting a protected list on the chain root by handle also
    # freezes the immediate child directories: their entries keep every
    # security identifier and every access mask, but the inherited flag is
    # cleared and their own list becomes protected.  No grant is removed and
    # nothing is emptied, which is what separates this from the path-based
    # editor's outcome, so the property pinned here is the preservation of the
    # grants rather than the preservation of the flags.
    after_inventory = windows_acl(inventory)
    assert [
        (entry["sid"], entry["mask"]) for entry in after_inventory["entries"]
    ] == [
        (entry["sid"], entry["mask"]) for entry in before_inventory["entries"]
    ]
    assert after_inventory["entries"] != []
    assert sorted(item.name for item in inventory.iterdir()) == ["probe.txt"]

    assert windows_acl(root)["protected"] is True


@WINDOWS_ONLY
def test_windows_repairs_a_whole_chain_the_operator_created_first(
    tmp_path: Path,
) -> None:
    """B-11-R1 (architecture section 20.21.7, test W6).

    The acceptance gate of the ruling.  W1 pre-creates the chain ROOT only, so
    the shipped root-first loop never had a member two to walk into, and the
    suite passed on the very volume where activation wedges.  This fixture
    pre-creates EVERY member, which is the shape the operator recipe and the
    driver probe actually leave behind.

    The fixture must stay on `tmp_path`, because the effect is a property of
    the volume.  Where the inherited set propagates, setting the protected
    list on `.synaptic` converts its immediate children to explicit and
    protected, so a root-first repair meets member two in a state section 20.6
    clauses 3 and 4 refuse, and the chain wedges for good.  Relocating this
    fixture off the temporary volume is exactly how it would go green without
    ever reaching the state it exists to test, so the drive is asserted rather
    than assumed.
    """
    import tempfile

    fixture_drive = os.path.splitdrive(str(tmp_path))[0]
    assert fixture_drive.lower() == os.path.splitdrive(
        tempfile.gettempdir()
    )[0].lower(), (
        "W6 must run on the temporary volume, where the inherited set "
        f"propagates; the fixture resolved to {fixture_drive}"
    )

    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    state = root / "state"
    docker = state / "docker"
    docker.mkdir(parents=True)
    stages = docker / "stages"
    stages.mkdir()
    sidecar = root / "recipe.txt"
    sidecar.write_bytes(b"operator")

    # Prove the FIXTURE is the state under test before repairing it, member by
    # member.  Without this the test would still pass if the whole chain
    # happened to arrive already protected, and it would pass for the wrong
    # reason.
    chain = (root, state, docker)
    for member in chain:
        before = windows_acl(member)
        assert before["protected"] is False, member.name
        assert before["entries"], "fixture is not the inherited-list state"
        assert all(entry["inherited"] for entry in before["entries"])
        assert before["owner"] == security._win_current_user_sid()
    before_stages = windows_acl(stages)
    before_sidecar = windows_acl(sidecar)

    value = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=False,
    )
    assert value.private_storage_verified is True

    for member in chain:
        after = windows_acl(member)
        assert after["protected"] is True, member.name
        assert after["owner"] == security._win_current_user_sid()
        assert len(after["entries"]) == 2, member.name
        assert {entry["sid"] for entry in after["entries"]} == {
            security._win_current_user_sid(), "S-1-5-18",
        }
        for entry in after["entries"]:
            assert entry["inherited"] is False
            assert entry["mask"] == security._FILE_ALL_ACCESS
            assert entry["flags"] == (
                OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE
            ), member.name

    # The non-chain nodes carry the tamper-mask guard.  Section 20.14 W5
    # measured that a repair freezes an immediate child in place: every
    # security identifier and every access mask survives, and only the
    # inherited flag is cleared.  What must never happen is the path-based
    # editor's outcome, an emptied list, so the property pinned here is the
    # preservation of the grants rather than the preservation of the flags.
    for node, was in ((stages, before_stages), (sidecar, before_sidecar)):
        now = windows_acl(node)
        assert [
            (entry["sid"], entry["mask"]) for entry in now["entries"]
        ] == [
            (entry["sid"], entry["mask"]) for entry in was["entries"]
        ], node.name
        assert now["entries"] != [], node.name
    assert sidecar.read_bytes() == b"operator"
    assert sorted(item.name for item in docker.iterdir()) == [
        "control-hmac.key", "stages",
    ]


@POSIX_ONLY
def test_posix_repairs_a_permissive_chain_directory(tmp_path: Path) -> None:
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    root.mkdir()
    os.chmod(root, 0o755)
    assert stat.S_IMODE(os.stat(root).st_mode) == 0o755

    value = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=False,
    )
    assert value.private_storage_verified is True
    assert stat.S_IMODE(os.stat(root).st_mode) == 0o700


@POSIX_ONLY
def test_posix_repairs_a_permissive_whole_chain(tmp_path: Path) -> None:
    """B-11-R1 (architecture section 20.21.7, test P4).

    The POSIX twin of W6, on the same whole-chain fixture.  Mode bits carry no
    propagation, so this lane cannot reproduce the wedge; what it pins is that
    the two-pass order did not change the outcome on the platform where the
    shipped root-first order was already correct, and that repairing a member
    still leaves the nodes outside the chain alone.
    """
    project_context = context(tmp_path)
    root = project_context.project_root / ".synaptic"
    state = root / "state"
    docker = state / "docker"
    docker.mkdir(parents=True)
    stages = docker / "stages"
    stages.mkdir()
    sidecar = root / "recipe.txt"
    sidecar.write_bytes(b"operator")

    chain = (root, state, docker)
    for member in chain:
        os.chmod(member, 0o755)
        assert stat.S_IMODE(os.stat(member).st_mode) == 0o755
    os.chmod(stages, 0o755)
    os.chmod(sidecar, 0o644)

    value = FileHmacAuthenticator.for_docker(
        project_context, durable_rows_exist=False,
    )
    assert value.private_storage_verified is True
    for member in chain:
        assert stat.S_IMODE(os.stat(member).st_mode) == 0o700, member.name
    assert stat.S_IMODE(os.stat(stages).st_mode) == 0o755
    assert stat.S_IMODE(os.stat(sidecar).st_mode) == 0o644
    assert sidecar.read_bytes() == b"operator"


@POSIX_ONLY
def test_posix_symbolic_link_in_the_chain_is_never_repaired(
    tmp_path: Path,
) -> None:
    target = tmp_path / "elsewhere"
    target.mkdir()
    os.chmod(target, 0o755)
    project_context = context(tmp_path)
    link = project_context.project_root / ".synaptic"
    link.symlink_to(target, target_is_directory=True)

    # Shape is never repaired, only access, so this stays refused.
    with pytest.raises(ValueError, match="private storage"):
        FileHmacAuthenticator.for_docker(
            project_context, durable_rows_exist=False,
        )
    assert link.is_symlink()
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o755


def test_ensure_private_storage_requires_an_explicit_repair_intent() -> None:
    """The guard cannot be omitted, and verification never repairs.

    Two properties in one place.  The parameter is keyword-only and has NO
    default, so a future call site cannot inherit the permissive branch by
    accident; and `_key`, which is what `private_storage_verified` calls,
    passes False, which is what keeps verification a pure predicate.
    """
    import inspect

    signature = inspect.signature(
        FileHmacAuthenticator._ensure_private_storage_directories
    )
    parameter = signature.parameters["repair"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty

    source = inspect.getsource(FileHmacAuthenticator._key)
    assert "_ensure_private_storage_directories(repair=False)" in source
    assert "repair=True" not in source
