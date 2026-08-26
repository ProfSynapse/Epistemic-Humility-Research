from __future__ import annotations

from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_host.modal_provider import ExplicitModalHostSession, ModalHostConfigV1
from synaptic_host.security import FileHmacAuthenticator


def config() -> ModalHostConfigV1:
    return ModalHostConfigV1.from_mapping({
        "schema_version": "synaptic-modal-host/v1",
        "environment_name": "main", "profile": "modal-a10-v1",
        "deployment": {"function_version": "1", "timeout_seconds": 3600},
        "volumes": {"control_name": "control-v1", "artifact_name": "artifact-v1"},
        "runtime_secret": {"name": "runtime-v1", "required_keys": ["HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"]},
        "runtime_environment": {"PATH": "/opt/conda/bin:/usr/bin", "LANG": "C.UTF-8"},
        "budget": {"maximum_cost_minor_units": 100, "currency": "USD"},
    })


class FakeObject:
    def __init__(self, object_id, name=None):
        self.object_id = object_id
        self.name = name

    def hydrate(self, client=None):
        return self


class FakeClient:
    @classmethod
    def from_credentials(cls, token_id, token_secret):
        assert token_id == "token-id" and token_secret == "token-secret"
        return cls()


class FakeWorkspace:
    @staticmethod
    def from_context(*, client):
        return FakeObject("ac-workspace", "workspace")


class FakeEnvironment:
    @staticmethod
    def from_name(name, *, client):
        return FakeObject("en-main", name)


class FakeVolume(FakeObject):
    registry = {}

    class objects:
        @staticmethod
        def create(name, **kwargs):
            if name in FakeVolume.registry and not kwargs["allow_existing"]:
                raise RuntimeError("exists")
            value = FakeVolume.registry.setdefault(name, FakeVolume("vo-" + name, name))
            return value

    @classmethod
    def from_name(cls, name, **kwargs):
        return cls.registry[name]

    def read_file(self, path):
        return iter(())

    def iterdir(self, path, recursive):
        return iter(())


class FakeSecret:
    registry = {}

    class objects:
        @staticmethod
        def create(name, values, **kwargs):
            if name in FakeSecret.registry and not kwargs["allow_existing"]:
                raise RuntimeError("exists")
            FakeSecret.registry[name] = dict(values)
            return FakeObject("st-" + name, name)

    @classmethod
    def from_name(cls, name, **kwargs):
        assert set(FakeSecret.registry[name]) == {"HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"}
        return FakeObject("st-" + name, name)


class FakeImage(FakeObject):
    @classmethod
    def from_registry(cls, reference):
        value = cls("im-runtime-1")
        value.reference = reference
        return value

    def entrypoint(self, value):
        assert value == []
        return self

    def env(self, value):
        self.environment = dict(value)
        return self


class FakeFunction(FakeObject):
    current = None

    @classmethod
    def from_name(cls, app_name, function_name, **kwargs):
        assert kwargs["version"] == 1
        return cls.current


class FakeApp:
    def __init__(self, name, **kwargs):
        self.name = name
        self.image = kwargs["image"]

    def function(self, **kwargs):
        def decorator(function):
            value = FakeFunction("fu-runtime-1", kwargs["name"])
            FakeFunction.current = value
            return value
        return decorator

    def deploy(self, **kwargs):
        assert kwargs["name"] == "synaptic-training-v1"
        return self


class FakeSdk:
    __version__ = "1.5.4"
    Client = FakeClient
    Workspace = FakeWorkspace
    Environment = FakeEnvironment
    Volume = FakeVolume
    Secret = FakeSecret
    Image = FakeImage
    Function = FakeFunction
    App = FakeApp

    @staticmethod
    def current_function_call_id():
        return "fc-1"


@pytest.fixture(autouse=True)
def clear_fakes():
    FakeVolume.registry.clear()
    FakeSecret.registry.clear()
    FakeFunction.current = None


def project_context(tmp_path: Path) -> ProjectContext:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    return ProjectContext.host(
        engine_root=engine, project_root=project,
        config_root=project / "training",
    )


def test_host_config_is_closed_and_budget_bounded() -> None:
    value = config()
    assert value.currency == "USD"
    assert len(value.digest) == 64
    with pytest.raises(ValueError, match="initial function version"):
        ModalHostConfigV1(
            value.environment_name, value.profile, "2",
            value.control_volume_name, value.artifact_volume_name,
            value.runtime_secret_name, value.runtime_secret_keys,
            value.runtime_environment, value.timeout_seconds,
            value.maximum_cost_minor_units, value.currency,
        )


def test_explicit_session_deploys_once_and_writes_only_host_state(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(), token_id="token-id", token_secret="token-secret"
    )
    authenticator = FileHmacAuthenticator.from_context(context)
    state = session.deploy(context=context, authenticator=authenticator, hf_token="hf-value")
    assert state.selection.image_id == "im-runtime-1"
    assert state.selection.function_version == "1"
    assert state.control_volume_id == "vo-control-v1"
    assert (context.state_root / "modal" / "provider-state.json").is_file()
    assert not (context.engine_root / ".synaptic").exists()
    assert session.facade(state).bound_scope() == (
        "ac-workspace", "workspace", "main", session.binding.client_ref
    )
    with pytest.raises(FileExistsError, match="already deployed"):
        session.deploy(context=context, authenticator=authenticator, hf_token="hf-value")


def test_session_accepts_one_explicit_client_loaded_from_host_config() -> None:
    client = FakeClient()
    session = ExplicitModalHostSession.from_client(
        sdk=FakeSdk, config=config(), client=client
    )
    assert session.client is client


def test_session_rejects_any_sdk_version_drift() -> None:
    class WrongSdk(FakeSdk):
        __version__ = "1.5.5"

    with pytest.raises(ValueError, match="exactly 1.5.4"):
        ExplicitModalHostSession.from_credentials(
            sdk=WrongSdk, config=config(), token_id="token-id", token_secret="token-secret"
        )
