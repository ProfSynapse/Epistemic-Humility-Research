from __future__ import annotations

import json
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_host.modal_provider import ExplicitModalHostSession, ModalHostConfigV1


class StubAuthenticator:
    key_ref = "modal-evidence-v1"
    encoded_key = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    def initialize(self) -> None:
        pass


def config() -> ModalHostConfigV1:
    return ModalHostConfigV1.from_mapping({
        "schema_version": "synaptic-modal-host/v1",
        "environment_name": "main", "profile": "modal-a10-v1",
        "deployment": {"timeout_seconds": 3600},
        "volumes": {"control_name": "control-v1", "artifact_name": "artifact-v1"},
        "runtime_secret": {"name": "runtime-v1", "required_keys": ["HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"]},
        "runtime_environment": {"PATH": "/opt/conda/bin:/usr/bin", "LANG": "C.UTF-8"},
        "budget": {"maximum_cost_minor_units": 100, "currency": "USD"},
    })


class FakeNotFound(Exception):
    pass


class FakeObject:
    def __init__(self, object_id, name=None):
        self.object_id = object_id
        self.name = name
        self.is_hydrated = True

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
        if name not in cls.registry:
            raise FakeNotFound
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
        if name not in cls.registry:
            raise FakeNotFound
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

    def add_local_python_source(self, *modules, **kwargs):
        assert modules == ("tuner", "synaptic_tuner")
        assert kwargs == {"copy": False, "ignore": []}
        return self


class FakeFunction(FakeObject):
    current = None

    @classmethod
    def from_name(cls, app_name, function_name, **kwargs):
        assert "version" not in kwargs
        if cls.current is None or cls.current.name != function_name:
            raise FakeNotFound
        return cls.current


class FakeApp:
    deployed = False
    fail_once = False
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
        if type(self).fail_once:
            type(self).fail_once = False
            raise RuntimeError("simulated deploy interruption")
        type(self).deployed = True
        return self

    @classmethod
    def lookup(cls, name, **kwargs):
        assert name == "synaptic-training-v1"
        if not cls.deployed:
            raise FakeNotFound
        return cls(name, image=FakeImage("im-existing"))


class FakeSdk:
    exception = type("FakeException", (), {"NotFoundError": FakeNotFound})
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
    FakeApp.deployed = False
    FakeApp.fail_once = False


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
    changed = config().digest
    assert changed == value.digest


def test_explicit_session_deploys_once_and_writes_only_host_state(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(), token_id="token-id", token_secret="token-secret"
    )
    authenticator = StubAuthenticator()
    state = session.deploy(context=context, authenticator=authenticator, hf_token="hf-value")
    assert state.selection.deployment_ref.startswith("modal-deployment-")
    assert state.selection.function_name.endswith(state.selection.deployment_ref[-32:])
    assert state.control_volume_id.startswith("modal-volume-")
    assert (context.state_root / "modal" / "provider-state.json").is_file()
    assert (context.state_root / "modal" / "deployment-journal.json").is_file()
    assert not (context.engine_root / ".synaptic").exists()
    assert session.facade(state).bound_scope() == (
        session.binding.account_ref, "workspace", "main", session.binding.client_ref
    )
    with pytest.raises(FileExistsError, match="already deployed"):
        session.deploy(context=context, authenticator=authenticator, hf_token="hf-value")


def test_deploy_resumes_exact_journal_after_interruption(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(),
        token_id="token-id", token_secret="token-secret",
    )
    authenticator = StubAuthenticator()
    FakeApp.fail_once = True
    with pytest.raises(RuntimeError, match="interruption"):
        session.deploy(
            context=context, authenticator=authenticator, hf_token="hf-value"
        )
    journal = context.state_root / "modal" / "deployment-journal.json"
    assert journal.is_file()
    state = session.deploy(
        context=context, authenticator=authenticator, hf_token="hf-value"
    )
    assert state.selection.deployment_ref in journal.read_text(encoding="utf-8")
    assert (context.state_root / "modal" / "provider-state.json").is_file()


def test_adopt_empty_reuses_exact_resources_without_overwriting_secret(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    FakeVolume.registry.update({
        "control-v1": FakeVolume("vo-control-v1", "control-v1"),
        "artifact-v1": FakeVolume("vo-artifact-v1", "artifact-v1"),
    })
    existing_secret = {
        "HF_TOKEN": "existing-token",
        "SYNAPTIC_EVIDENCE_MAC_KEY": "existing-key",
    }
    FakeSecret.registry["runtime-v1"] = dict(existing_secret)
    FakeApp.deployed = True
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(),
        token_id="token-id", token_secret="token-secret",
    )
    state = session.deploy(
        context=context,
        authenticator=StubAuthenticator(),
        hf_token="unused-during-adoption",
        adopt_empty=True,
    )
    assert state.selection.deployment_ref.startswith("modal-deployment-")
    assert FakeSecret.registry["runtime-v1"] == existing_secret


def test_upgrade_rotates_deployment_and_preserves_durable_resources(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(),
        token_id="token-id", token_secret="token-secret",
    )
    authenticator = StubAuthenticator()
    prior = session.deploy(
        context=context, authenticator=authenticator, hf_token="hf-value"
    )
    control = FakeVolume.registry["control-v1"]
    artifact = FakeVolume.registry["artifact-v1"]
    secret = dict(FakeSecret.registry["runtime-v1"])

    current = session.upgrade(context=context, authenticator=authenticator)

    assert current.selection.deployment_ref != prior.selection.deployment_ref
    assert FakeVolume.registry["control-v1"] is control
    assert FakeVolume.registry["artifact-v1"] is artifact
    assert FakeSecret.registry["runtime-v1"] == secret
    modal_root = context.state_root / "modal"
    history = modal_root / "history"
    assert (history / prior.selection.deployment_ref / "provider-state.json").is_file()
    assert (history / prior.selection.deployment_ref / "deployment-journal.json").is_file()
    assert (history / current.selection.deployment_ref / "upgrade-journal.json").is_file()
    assert not (modal_root / "upgrade-journal.json").exists()


def test_upgrade_resumes_exact_journal_after_interruption(tmp_path: Path) -> None:
    context = project_context(tmp_path)
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(),
        token_id="token-id", token_secret="token-secret",
    )
    authenticator = StubAuthenticator()
    prior = session.deploy(
        context=context, authenticator=authenticator, hf_token="hf-value"
    )
    FakeApp.fail_once = True
    with pytest.raises(RuntimeError, match="interruption"):
        session.upgrade(context=context, authenticator=authenticator)
    pending_path = context.state_root / "modal" / "upgrade-journal.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    replacement_ref = pending["replacement"]["deployment_ref"]

    current = session.upgrade(context=context, authenticator=authenticator)

    assert current.selection.deployment_ref == replacement_ref
    assert current.selection.deployment_ref != prior.selection.deployment_ref
    assert not pending_path.exists()


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
