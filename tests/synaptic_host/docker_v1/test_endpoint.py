import json

import pytest

from synaptic_host.docker_v1.cli import DockerBoundedProcessRunnerV1
from synaptic_host.docker_v1.endpoint import DockerLocalEndpointResolverV1
from synaptic_host.docker_v1.model import (
    DockerLocalEndpointDescriptorV1, DockerPlatformErrorV1,
)


class Stream:
    def __init__(self, chunks): self.chunks = list(chunks)
    def read(self, _size): return self.chunks.pop(0) if self.chunks else b""
    def close(self): pass


class Process:
    def __init__(self, stdout, exit_code=0):
        self.stdout, self.stderr = Stream((stdout,)), Stream(())
        self.exit_code = exit_code
    def wait(self, timeout=None): return self.exit_code
    def terminate(self): pass
    def kill(self): pass


class Factory:
    def __init__(self, process): self.process, self.calls = process, []
    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs)); return self.process


def _runner(factory):
    return DockerBoundedProcessRunnerV1(
        timeout_ms=10_000, terminate_grace_ms=1_000,
        stdout_limit=65_536, stderr_limit=65_536, combined_limit=131_072,
        popen_factory=factory,
    )


def _document(**changes):
    value = {
        "Name": "desktop-linux",
        "Endpoints": {"docker": {
            "Host": "npipe:////./pipe/dockerDesktopLinuxEngine",
            "SkipTLSVerify": False,
        }},
        "TLSMaterial": {}, "Metadata": {"ignored": "secret"},
        "Storage": {"MetadataPath": "C:\\ignored", "TLSPath": "C:\\ignored"},
    }
    value.update(changes)
    return json.dumps(value).encode()


def test_resolver_uses_fixed_context_inspect_and_discards_metadata():
    factory = Factory(Process(_document()))
    value = DockerLocalEndpointResolverV1(_runner(factory)).resolve(
        "C:\\Program Files\\Docker\\docker.exe", "desktop-linux",
        {"PATH": "C:\\trusted", "USERPROFILE": "C:\\User"},
    )
    assert value == DockerLocalEndpointDescriptorV1.build(
        "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False
    )
    argv, kwargs = factory.calls[0]
    assert argv == (
        "C:\\Program Files\\Docker\\docker.exe", "context", "inspect",
        "--format", "{{json .}}", "desktop-linux",
    )
    assert kwargs["shell"] is False
    assert kwargs["env"] == {"PATH": "C:\\trusted", "USERPROFILE": "C:\\User"}
    assert "ignored" not in repr(value)


@pytest.mark.parametrize("document", (
    b"{}", b"{} {}", b"not-json",
    _document(Name="other"), _document(TLSMaterial={"key": "x"}),
    _document(Endpoints={"docker": {"Host": "npipe:other", "SkipTLSVerify": False}}),
    _document(Endpoints={"docker": {"Host": "npipe:////./pipe/dockerDesktopLinuxEngine", "SkipTLSVerify": True}}),
))
def test_resolver_rejects_malformed_or_security_drift(document):
    with pytest.raises(DockerPlatformErrorV1):
        DockerLocalEndpointResolverV1(_runner(Factory(Process(document)))).resolve(
            "C:\\Docker\\docker.exe", "desktop-linux", {},
        )


def test_descriptor_digest_is_computed_and_exact():
    value = DockerLocalEndpointDescriptorV1.build(
        "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False
    )
    assert len(value.descriptor_digest) == 64
    assert "descriptor_digest" not in value.__dataclass_fields__
    with pytest.raises(DockerPlatformErrorV1):
        DockerLocalEndpointDescriptorV1.build("desktop-linux", value.host, True)
