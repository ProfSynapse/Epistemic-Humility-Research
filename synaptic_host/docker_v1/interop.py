"""Closed argv0-only Docker CLI interoperability for WSL hosts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import stat
import subprocess
import unicodedata

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.model import (
    DockerCLIEnvironmentV1,
    MAX_WINDOWS_PATH_BYTES_V1,
)


_WINDOWS_EXECUTABLE = re.compile(r"([A-Z]):\\([^/]+(?:\\[^/]+)*)\Z")
_INTEROP_PATH = re.compile(r"/run/WSL/([1-9][0-9]*)_interop\Z")
_DOCKER_DESKTOP_WSL_EXECUTABLE = "/Docker/host/bin/docker.exe"


def _windows_components(value):
    try:
        match = _WINDOWS_EXECUTABLE.fullmatch(value)
        if (
            type(value) is not str
            or match is None
            or unicodedata.normalize("NFC", value) != value
            or len(value.encode("utf-8")) > MAX_WINDOWS_PATH_BYTES_V1
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ValueError
        drive, tail = match.groups()
        components = tuple(tail.split("\\"))
        reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
        reserved.update(f"COM{number}" for number in range(1, 10))
        reserved.update(f"LPT{number}" for number in range(1, 10))
        reserved.update(f"COM{number}" for number in "\u00b9\u00b2\u00b3")
        reserved.update(f"LPT{number}" for number in "\u00b9\u00b2\u00b3")
        for component in components:
            base = component.split(".", 1)[0].rstrip(" .").upper()
            if (
                not component
                or component in (".", "..")
                or component.endswith((" ", "."))
                or any(character in '<>:"|?*' for character in component)
                or base in reserved
            ):
                raise ValueError
        if not value.lower().endswith(".exe"):
            raise ValueError
        return drive, components
    except BaseException:
        _fail()


def _wsl_executable(value):
    try:
        if value == _DOCKER_DESKTOP_WSL_EXECUTABLE:
            return value, "/Docker/host/bin"
        drive, components = _windows_components(value)
        executable = "/mnt/" + drive.lower() + "/" + "/".join(components)
        return executable, executable.rsplit("/", 1)[0]
    except DockerWSLInteropErrorV1:
        raise
    except BaseException:
        _fail()


class DockerWSLInteropCodeV1(str, Enum):
    INVALID = "INVALID"
    CHANNEL_INVALID = "CHANNEL_INVALID"
    CHANNEL_CHANGED = "CHANNEL_CHANGED"
    SPAWN_INDETERMINATE = "SPAWN_INDETERMINATE"


class DockerWSLInteropErrorV1(Exception):
    __slots__ = ("code",)

    def __init__(self, code):
        self.code = code
        super().__init__("docker WSL interoperability failed")


def _fail(code=DockerWSLInteropCodeV1.INVALID):
    raise DockerWSLInteropErrorV1(code) from None


@dataclass(frozen=True, slots=True)
class DockerWSLExecutableBindingV1:
    policy_executable: str
    wsl_executable: str
    wsl_cwd: str

    def __post_init__(self):
        try:
            if type(self.policy_executable) is not str:
                raise ValueError
            expected, cwd = _wsl_executable(self.policy_executable)
            if self.wsl_executable != expected or self.wsl_cwd != cwd:
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, policy_executable):
        try:
            if type(policy_executable) is not str:
                raise ValueError
            wsl_executable, wsl_cwd = _wsl_executable(policy_executable)
            return cls(
                policy_executable,
                wsl_executable,
                wsl_cwd,
            )
        except DockerWSLInteropErrorV1:
            raise
        except BaseException:
            _fail()


class DockerPrivateWSLInteropChannelV1:
    __slots__ = (
        "_path", "_path_pin", "_path_baseline", "_identity",
        "_identity_pin", "_identity_baseline", "_identity_digest", "_lstat",
        "_lstat_pin",
    )

    def __init__(self, path, *, lstat):
        try:
            if (
                type(path) is not str
                or _INTEROP_PATH.fullmatch(path) is None
                or not callable(lstat)
            ):
                raise ValueError
            identity = self._read_identity(path, lstat)
            path_baseline = (path + "\x00")[:-1]
            identity_baseline = tuple(list(identity))
            if path_baseline is path or identity_baseline is identity:
                raise ValueError
            self._path = path
            self._path_pin = path
            self._path_baseline = path_baseline
            self._identity = identity
            self._identity_pin = identity
            self._identity_baseline = identity_baseline
            self._identity_digest = self._digest_identity(identity_baseline)
            self._lstat = lstat
            self._lstat_pin = lstat
        except DockerWSLInteropErrorV1:
            raise
        except BaseException:
            _fail(DockerWSLInteropCodeV1.CHANNEL_INVALID)

    @staticmethod
    def _digest_identity(identity):
        try:
            return digest_v1({
                "schema": "synaptic-host-wsl-interop-socket-identity/v1",
                "st_dev": identity[0],
                "st_gid": identity[4],
                "st_ino": identity[1],
                "st_mode": identity[2],
                "st_nlink": identity[5],
                "st_uid": identity[3],
            })
        except BaseException:
            _fail(DockerWSLInteropCodeV1.CHANNEL_INVALID)

    @staticmethod
    def _read_identity(path, lstat):
        try:
            value = lstat(path)
            identity = tuple(
                getattr(value, name)
                for name in (
                    "st_dev", "st_ino", "st_mode", "st_uid", "st_gid",
                    "st_nlink",
                )
            )
            if (
                any(type(item) is not int for item in identity)
                or not stat.S_ISSOCK(identity[2])
                or identity[5] <= 0
            ):
                raise ValueError
            return identity
        except BaseException:
            _fail(DockerWSLInteropCodeV1.CHANNEL_INVALID)

    @classmethod
    def acquire(cls, path, *, lstat):
        return cls(path, lstat=lstat)

    def _configuration_exact(self):
        try:
            if (
                type(self._path) is not str
                or self._path is not self._path_pin
                or self._path != self._path_baseline
                or _INTEROP_PATH.fullmatch(self._path_baseline) is None
                or type(self._identity) is not tuple
                or self._identity is not self._identity_pin
                or self._identity != self._identity_baseline
                or self._digest_identity(self._identity_baseline)
                != self._identity_digest
                or self._lstat is not self._lstat_pin
            ):
                raise ValueError
        except BaseException:
            _fail(DockerWSLInteropCodeV1.CHANNEL_CHANGED)

    def _validated_path(self):
        self._configuration_exact()
        local_path = (self._path_baseline + "\x00")[:-1]
        local_identity = tuple(list(self._identity_baseline))
        local_digest = self._identity_digest
        try:
            identity = self._read_identity(local_path, self._lstat_pin)
        except DockerWSLInteropErrorV1:
            _fail(DockerWSLInteropCodeV1.CHANNEL_CHANGED)
        self._configuration_exact()
        if (
            identity != local_identity
            or self._digest_identity(identity) != local_digest
        ):
            _fail(DockerWSLInteropCodeV1.CHANNEL_CHANGED)
        self._configuration_exact()
        return local_path

    def __repr__(self):
        return "DockerPrivateWSLInteropChannelV1(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        _fail(DockerWSLInteropCodeV1.CHANNEL_INVALID)

    __copy__ = __reduce__

    def __deepcopy__(self, _memo):
        return self.__reduce__()


class DockerWSLInteropPopenFactoryV1:
    """Validate the native runner boundary and delegate one WSL-native spawn."""

    __slots__ = (
        "_executable", "_executable_pin", "_executable_baseline",
        "_environment", "_environment_pin", "_environment_baseline",
        "_channel", "_channel_pin", "_popen", "_popen_pin",
    )

    def __init__(
        self, *, executable, environment, channel,
        popen_factory=subprocess.Popen,
    ):
        try:
            if (
                type(executable) is not DockerWSLExecutableBindingV1
                or type(environment) is not DockerCLIEnvironmentV1
                or type(channel) is not DockerPrivateWSLInteropChannelV1
                or not callable(popen_factory)
            ):
                raise ValueError
            executable_baseline = DockerWSLExecutableBindingV1(
                executable.policy_executable,
                executable.wsl_executable,
                executable.wsl_cwd,
            )
            environment_baseline = DockerCLIEnvironmentV1(
                tuple(environment.entries), environment.environment_digest
            )
            if executable_baseline != executable or environment_baseline != environment:
                raise ValueError
            self._executable = executable
            self._executable_pin = executable
            self._executable_baseline = executable_baseline
            self._environment = environment
            self._environment_pin = environment
            self._environment_baseline = environment_baseline
            self._channel = channel
            self._channel_pin = channel
            self._popen = popen_factory
            self._popen_pin = popen_factory
        except DockerWSLInteropErrorV1:
            raise
        except BaseException:
            _fail()

    def _configuration_exact(self):
        try:
            executable = self._executable
            environment = self._environment
            if (
                executable is not self._executable_pin
                or type(executable) is not DockerWSLExecutableBindingV1
                or DockerWSLExecutableBindingV1(
                    executable.policy_executable,
                    executable.wsl_executable,
                    executable.wsl_cwd,
                ) != self._executable_baseline
                or environment is not self._environment_pin
                or type(environment) is not DockerCLIEnvironmentV1
                or DockerCLIEnvironmentV1(
                    tuple(environment.entries), environment.environment_digest
                ) != self._environment_baseline
                or self._channel is not self._channel_pin
                or type(self._channel) is not DockerPrivateWSLInteropChannelV1
                or self._popen is not self._popen_pin
            ):
                raise ValueError
        except BaseException:
            _fail()

    def __call__(self, argv, **kwargs):
        self._configuration_exact()
        executable = self._executable
        environment = self._environment_baseline
        try:
            if (
                type(argv) is not tuple
                or not argv
                or argv[0] != executable.policy_executable
                or any(type(value) is not str for value in argv)
                or set(kwargs) != {
                    "shell", "stdin", "stdout", "stderr", "env", "text",
                    "close_fds",
                }
                or kwargs["shell"] is not False
                or kwargs["stdin"] != subprocess.DEVNULL
                or kwargs["stdout"] != subprocess.PIPE
                or kwargs["stderr"] != subprocess.PIPE
                or kwargs["text"] is not False
                or kwargs["close_fds"] is not True
                or type(kwargs["env"]) is not dict
                or tuple(kwargs["env"].items()) != environment.entries
            ):
                raise ValueError
            tail = argv[1:]
            delegated_argv = (executable.wsl_executable, *tail)
            if any(
                delegated_argv[index] is not argv[index]
                for index in range(1, len(argv))
            ):
                raise ValueError
            channel_path = self._channel._validated_path()
            delegated_environment = dict(environment.entries)
            delegated_environment["WSL_INTEROP"] = channel_path
            delegated_kwargs = {
                "shell": False,
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "env": delegated_environment,
                "text": False,
                "close_fds": True,
                "cwd": executable.wsl_cwd,
            }
            self._configuration_exact()
        except DockerWSLInteropErrorV1:
            raise
        except BaseException:
            _fail()
        try:
            return self._popen(delegated_argv, **delegated_kwargs)
        except BaseException:
            _fail(DockerWSLInteropCodeV1.SPAWN_INDETERMINATE)


__all__: tuple[str, ...] = ()
