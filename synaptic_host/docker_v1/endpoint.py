from __future__ import annotations

import json
from collections.abc import Mapping

from .cli import DockerBoundedProcessRunnerV1
from .model import (
    DockerLocalEndpointDescriptorV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
    _docker_desktop_wsl_executable_v1,
)


_CONTEXT = "desktop-linux"
_HOST = "npipe:////./pipe/dockerDesktopLinuxEngine"
_BOUNDS = (10_000, 1_000, 65_536, 65_536, 131_072)


def _fail(code=DockerPlatformCodeV1.OUTPUT_INVALID):
    raise DockerPlatformErrorV1(code) from None


class DockerLocalEndpointResolverV1:
    def __init__(self, runner: DockerBoundedProcessRunnerV1) -> None:
        try:
            if type(runner) is not DockerBoundedProcessRunnerV1:
                raise ValueError
            bounds = runner._policy
            if (
                bounds.timeout_ms, bounds.terminate_grace_ms,
                bounds.stdout_limit, bounds.stderr_limit,
                bounds.combined_limit,
            ) != _BOUNDS:
                raise ValueError
            self._runner = runner
        except BaseException:
            _fail(DockerPlatformCodeV1.POLICY_INVALID)

    @staticmethod
    def _environment(source: Mapping[str, str]) -> dict[str, str]:
        try:
            if not isinstance(source, Mapping) or len(source) > 256:
                raise ValueError
            result: dict[str, str] = {}
            total = 0
            for key, value in source.items():
                if type(key) is not str or type(value) is not str:
                    raise ValueError
                key_size = len(key.encode("utf-8"))
                value_size = len(value.encode("utf-8"))
                if not 1 <= key_size <= 256 or value_size > 32_768:
                    raise ValueError
                total += key_size + value_size
                if total > 1_048_576:
                    raise ValueError
                result[key] = value
            return result
        except BaseException:
            _fail(DockerPlatformCodeV1.POLICY_INVALID)

    def resolve(self, executable, source_context_ref, trusted_environment):
        try:
            _docker_desktop_wsl_executable_v1(executable)
            if source_context_ref != _CONTEXT:
                raise ValueError
            result = self._runner.execute(
                (executable, "context", "inspect", "--format", "{{json .}}", _CONTEXT),
                self._environment(trusted_environment), capture_stdout=True,
            )
            if result.exit_code != 0 or type(result.stdout) is not bytes:
                raise ValueError
            text = result.stdout.decode("utf-8")
            decoder = json.JSONDecoder()
            value, end = decoder.raw_decode(text.lstrip())
            if text.lstrip()[end:].strip() or type(value) is not dict:
                raise ValueError
            if value.get("Name") != _CONTEXT or type(value.get("TLSMaterial")) is not dict or value["TLSMaterial"]:
                raise ValueError
            endpoints = value.get("Endpoints")
            if type(endpoints) is not dict or set(endpoints) != {"docker"}:
                raise ValueError
            docker = endpoints["docker"]
            if (
                type(docker) is not dict
                or set(docker) != {"Host", "SkipTLSVerify"}
                or docker.get("Host") != _HOST
                or type(docker.get("SkipTLSVerify")) is not bool
                or docker["SkipTLSVerify"] is not False
            ):
                raise ValueError
            return DockerLocalEndpointDescriptorV1.build(
                value["Name"], docker["Host"], docker["SkipTLSVerify"]
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            _fail()


__all__: tuple[str, ...] = ()
