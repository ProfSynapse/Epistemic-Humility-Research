from copy import copy, deepcopy
from concurrent.futures import ThreadPoolExecutor
import pickle
from stat import S_IFSOCK
from types import SimpleNamespace

import pytest

from synaptic_host.docker_v1.cli import DockerCLIRunnerV1
from synaptic_host.docker_v1.interop import (
    DockerPrivateWSLInteropChannelV1,
    DockerWSLExecutableBindingV1,
    DockerWSLInteropCodeV1,
    DockerWSLInteropErrorV1,
    DockerWSLInteropPopenFactoryV1,
)
from synaptic_host.docker_v1.model import (
    DockerCLICommandV1,
    DockerCLIEnvironmentV1,
    DockerCLIPolicyV1,
    DockerCLIVerbV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
)


WINDOWS_DOCKER = "C:\\Program Files\\Docker\\docker.exe"
DOCKER_DESKTOP_WSL = "/Docker/host/bin/docker.exe"
INTEROP = "/run/WSL/42_interop"


def _environment():
    return DockerCLIEnvironmentV1.build((
        ("SystemRoot", "C:\\Windows"),
        ("TEMP", "C:\\Temp"),
        ("TMP", "C:\\Temp"),
        ("WINDIR", "C:\\Windows"),
    ))


def _socket(**changes):
    values = {
        "st_dev": 1, "st_ino": 2, "st_mode": S_IFSOCK | 0o600,
        "st_uid": 1000, "st_gid": 1000, "st_nlink": 1,
        "st_atime_ns": 10, "st_mtime_ns": 11, "st_ctime_ns": 12,
    }
    values.update(changes)
    return SimpleNamespace(**values)


class Lstat:
    def __init__(self, value=None):
        self.value = _socket() if value is None else value
        self.paths = []
        self.callback = None

    def __call__(self, path):
        self.paths.append(path)
        if self.callback is not None:
            self.callback()
        return self.value


class Popen:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self.result


def _factory(*, lstat=None, popen=None):
    lstat = Lstat() if lstat is None else lstat
    popen = Popen(object()) if popen is None else popen
    executable = DockerWSLExecutableBindingV1.build(WINDOWS_DOCKER)
    channel = DockerPrivateWSLInteropChannelV1.acquire(INTEROP, lstat=lstat)
    return (
        DockerWSLInteropPopenFactoryV1(
            executable=executable, environment=_environment(), channel=channel,
            popen_factory=popen,
        ), lstat, popen, executable, channel,
    )


def _runner(factory):
    policy = DockerCLIPolicyV1.build(
        WINDOWS_DOCKER, "desktop-linux", _environment(),
        timeout_ms=100, terminate_grace_ms=10, stdout_limit=100,
        stderr_limit=100, combined_limit=200,
    )
    return DockerCLIRunnerV1(policy, popen_factory=factory)


def test_executable_binding_is_exact_and_canonical():
    value = DockerWSLExecutableBindingV1.build(
        "D:\\Program Files\\Docker\\resources\\bin\\docker.exe"
    )
    assert value.wsl_executable == "/mnt/d/Program Files/Docker/resources/bin/docker.exe"
    assert value.wsl_cwd == "/mnt/d/Program Files/Docker/resources/bin"


def test_executable_binding_accepts_docker_desktop_wsl_proxy():
    value = DockerWSLExecutableBindingV1.build(DOCKER_DESKTOP_WSL)
    assert value.policy_executable == DOCKER_DESKTOP_WSL
    assert value.wsl_executable == DOCKER_DESKTOP_WSL
    assert value.wsl_cwd == "/Docker/host/bin"


@pytest.mark.parametrize("value", (
    "c:\\Docker\\docker.exe", "C:/Docker/docker.exe",
    "C:\\Docker\\not-an-executable", "C:\\Docker\\..\\docker.exe",
    "C:\\Docker\\", "C:\\docker.exe\\tail",
))
def test_executable_binding_rejects_noncanonical_paths(value):
    with pytest.raises(DockerWSLInteropErrorV1):
        DockerWSLExecutableBindingV1.build(value)


@pytest.mark.parametrize("name", ("docker.EXE", "Docker.Exe", "helper.exe"))
def test_executable_binding_matches_policy_valid_executable_suffix_casing(name):
    value = DockerWSLExecutableBindingV1.build(f"C:\\Docker\\{name}")
    assert value.policy_executable.endswith(name)


@pytest.mark.parametrize("reserved", ("COM1", "LPT9", "COM\u00b9", "LPT\u00b2", "LPT\u00b3"))
def test_executable_binding_matches_complete_policy_reserved_inventory(reserved):
    with pytest.raises(DockerWSLInteropErrorV1):
        DockerWSLExecutableBindingV1.build(
            f"C:\\Docker\\{reserved}\\docker.exe"
        )


@pytest.mark.parametrize("path", (
    "/run/WSL/0_interop", "/run/WSL/01_interop", "/run/wsl/1_interop",
    "/run/WSL/1_interop/extra", "/tmp/1_interop",
))
def test_channel_requires_exact_positive_pid_path(path):
    with pytest.raises(DockerWSLInteropErrorV1):
        DockerPrivateWSLInteropChannelV1.acquire(path, lstat=Lstat())


def test_channel_requires_a_socket_without_leaking_lstat_failure():
    with pytest.raises(DockerWSLInteropErrorV1) as caught:
        DockerPrivateWSLInteropChannelV1.acquire(
            INTEROP, lstat=Lstat(_socket(st_mode=0o100600))
        )
    assert caught.value.code is DockerWSLInteropCodeV1.CHANNEL_INVALID
    assert caught.value.__cause__ is None
    assert INTEROP not in str(caught.value)


def test_channel_is_redacted_noncopyable_and_unpickleable():
    _factory_value, _lstat, _popen, _binding, channel = _factory()
    assert repr(channel) == "DockerPrivateWSLInteropChannelV1(<redacted>)"
    for operation in (copy, deepcopy, pickle.dumps):
        with pytest.raises(DockerWSLInteropErrorV1):
            operation(channel)


def test_factory_revalidates_stable_identity_but_ignores_timestamps():
    factory, lstat, popen, executable, _channel = _factory()
    tail_value = "name;literal"
    argv = (WINDOWS_DOCKER, "--context", tail_value)
    environment = dict(_environment().entries)
    lstat.value = _socket(st_atime_ns=999, st_mtime_ns=998, st_ctime_ns=997)
    result = factory(
        argv, shell=False, stdin=-3, stdout=-1, stderr=-1,
        env=environment, text=False, close_fds=True,
    )
    assert result is popen.result
    assert len(popen.calls) == 1
    delegated_argv, kwargs = popen.calls[0]
    assert delegated_argv[0] == executable.wsl_executable
    assert all(delegated_argv[index] is argv[index] for index in range(1, len(argv)))
    assert tuple(kwargs["env"]) == (
        "SystemRoot", "TEMP", "TMP", "WINDIR", "WSL_INTEROP"
    )
    assert kwargs["env"]["WSL_INTEROP"] == INTEROP
    assert kwargs["cwd"] == executable.wsl_cwd
    assert kwargs["shell"] is False and kwargs["text"] is False
    assert kwargs["close_fds"] is True
    assert lstat.paths == [INTEROP, INTEROP]


@pytest.mark.parametrize(
    "attack", ("path", "equal-path", "identity", "path-and-identity")
)
def test_lstat_callback_cannot_replace_channel_working_state(attack):
    factory, lstat, popen, _executable, channel = _factory()

    def mutate():
        if attack in ("path", "path-and-identity"):
            object.__setattr__(channel, "_path", "/run/WSL/43_interop")
        elif attack == "equal-path":
            replacement = (channel._path + "\x00")[:-1]
            assert replacement == channel._path and replacement is not channel._path
            object.__setattr__(channel, "_path", replacement)
        if attack in ("identity", "path-and-identity"):
            replacement = tuple(list(channel._identity))
            assert replacement == channel._identity and replacement is not channel._identity
            object.__setattr__(channel, "_identity", replacement)

    lstat.callback = mutate
    with pytest.raises(DockerWSLInteropErrorV1) as caught:
        factory(
            (WINDOWS_DOCKER,), shell=False, stdin=-3, stdout=-1, stderr=-1,
            env=dict(_environment().entries), text=False, close_fds=True,
        )
    assert caught.value.code is DockerWSLInteropCodeV1.CHANNEL_CHANGED
    assert popen.calls == []


@pytest.mark.parametrize("field", (
    "st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink",
))
def test_factory_rejects_each_channel_identity_change_before_spawn(field):
    factory, lstat, popen, _executable, _channel = _factory()
    lstat.value = _socket(**{field: 999})
    with pytest.raises(DockerWSLInteropErrorV1) as caught:
        factory(
            (WINDOWS_DOCKER,), shell=False, stdin=-3, stdout=-1, stderr=-1,
            env=dict(_environment().entries), text=False, close_fds=True,
        )
    assert caught.value.code is DockerWSLInteropCodeV1.CHANNEL_CHANGED
    assert popen.calls == []


@pytest.mark.parametrize("change", (
    {"shell": True}, {"text": True}, {"close_fds": False},
    {"cwd": "/tmp"}, {"env": {"SystemRoot": "C:\\Windows"}},
))
def test_factory_rejects_runner_boundary_changes(change):
    factory, _lstat, popen, _executable, _channel = _factory()
    kwargs = {
        "shell": False, "stdin": -3, "stdout": -1, "stderr": -1,
        "env": dict(_environment().entries), "text": False,
        "close_fds": True,
    }
    kwargs.update(change)
    with pytest.raises(DockerWSLInteropErrorV1):
        factory((WINDOWS_DOCKER, "ps"), **kwargs)
    assert popen.calls == []


@pytest.mark.parametrize(
    ("name", "value"),
    (("stdin", 0), ("stdout", 1), ("stderr", 2)),
)
def test_factory_rejects_wrong_stdio_sentinel(name, value):
    factory, _lstat, popen, _executable, _channel = _factory()
    kwargs = {
        "shell": False, "stdin": -3, "stdout": -1, "stderr": -1,
        "env": dict(_environment().entries), "text": False,
        "close_fds": True,
    }
    kwargs[name] = value
    with pytest.raises(DockerWSLInteropErrorV1):
        factory((WINDOWS_DOCKER,), **kwargs)
    assert popen.calls == []


@pytest.mark.parametrize("attack", ("value", "order", "extra", "missing"))
def test_factory_rejects_environment_value_order_and_key_changes(attack):
    factory, _lstat, popen, _executable, _channel = _factory()
    items = list(_environment().entries)
    if attack == "value":
        items[0] = (items[0][0], "C:\\Different")
    elif attack == "order":
        items[0], items[1] = items[1], items[0]
    elif attack == "extra":
        items.append(("EXTRA", "C:\\Extra"))
    else:
        items.pop()
    supplied = dict(items)
    snapshot = tuple(supplied.items())
    with pytest.raises(DockerWSLInteropErrorV1):
        factory(
            (WINDOWS_DOCKER,), shell=False, stdin=-3, stdout=-1, stderr=-1,
            env=supplied, text=False, close_fds=True,
        )
    assert tuple(supplied.items()) == snapshot
    assert popen.calls == []


@pytest.mark.parametrize(
    "attribute", ("_executable", "_environment", "_channel", "_popen")
)
def test_factory_rejects_pinned_collaborator_substitution(attribute):
    factory, _lstat, popen, _executable, _channel = _factory()
    object.__setattr__(factory, attribute, object())
    with pytest.raises(DockerWSLInteropErrorV1):
        factory(
            (WINDOWS_DOCKER,), shell=False, stdin=-3, stdout=-1, stderr=-1,
            env=dict(_environment().entries), text=False, close_fds=True,
        )
    assert popen.calls == []


def test_spawn_failure_is_redacted_and_runner_totalizes_it():
    class FailingPopen:
        def __call__(self, _argv, **_kwargs):
            raise RuntimeError("raw secret spawn failure")

    factory, _lstat, _popen, _executable, _channel = _factory(
        popen=FailingPopen()
    )
    supplied = dict(_environment().entries)
    supplied_snapshot = tuple(supplied.items())
    with pytest.raises(DockerWSLInteropErrorV1) as direct:
        factory(
            (WINDOWS_DOCKER,), shell=False, stdin=-3, stdout=-1, stderr=-1,
            env=supplied, text=False, close_fds=True,
        )
    assert direct.value.code is DockerWSLInteropCodeV1.SPAWN_INDETERMINATE
    assert direct.value.__cause__ is None
    assert "raw secret" not in str(direct.value)
    assert tuple(supplied.items()) == supplied_snapshot
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _runner(factory).run(DockerCLICommandV1.build(DockerCLIVerbV1.PS))
    assert caught.value.code is DockerPlatformCodeV1.SPAWN_INDETERMINATE
    assert caught.value.__cause__ is None
    assert "raw secret" not in str(caught.value)


def test_successful_delegate_returns_exact_object_without_post_return_access():
    class OneShot:
        def __init__(self):
            self.calls = 0
            self.result = object()

        def __call__(self, _argv, **_kwargs):
            self.calls += 1
            return self.result

    popen = OneShot()
    factory, _lstat, _unused, _executable, _channel = _factory(popen=popen)
    returned = factory(
        (WINDOWS_DOCKER, "ps"), shell=False, stdin=-3, stdout=-1, stderr=-1,
        env=dict(_environment().entries), text=False, close_fds=True,
    )
    assert returned is popen.result
    assert popen.calls == 1


def test_concurrent_spawns_isolate_fresh_environment_and_preserve_inputs():
    factory, _lstat, popen, _executable, _channel = _factory()
    supplied = [dict(_environment().entries) for _ in range(32)]
    snapshots = [tuple(value.items()) for value in supplied]

    def spawn(index):
        return factory(
            (WINDOWS_DOCKER, f"value-{index}"), shell=False, stdin=-3,
            stdout=-1, stderr=-1, env=supplied[index], text=False,
            close_fds=True,
        )

    with ThreadPoolExecutor(max_workers=12) as pool:
        returned = list(pool.map(spawn, range(32)))
    assert all(value is popen.result for value in returned)
    assert [tuple(value.items()) for value in supplied] == snapshots
    delegated_environments = [kwargs["env"] for _argv, kwargs in popen.calls]
    assert len({id(value) for value in delegated_environments}) == 32
    assert all(
        tuple(value) == ("SystemRoot", "TEMP", "TMP", "WINDIR", "WSL_INTEROP")
        for value in delegated_environments
    )
