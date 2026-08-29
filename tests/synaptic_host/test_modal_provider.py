from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from synaptic_tuner.api.v1 import ProjectContext
import synaptic_host.modal_provider as modal_provider
from synaptic_host.modal_provider import (
    ExplicitModalHostSession,
    ModalDeploymentJournalV1,
    ModalHostConfigV1,
    ModalProviderAuthorityV1,
    ModalTrainingPolicyV1,
)


ROOT = Path(__file__).resolve().parents[2]


class StubAuthenticator:
    key_ref = "modal-evidence-v1"
    encoded_key = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    def initialize(self) -> None:
        pass


def config_mapping() -> dict[str, object]:
    return {
        "schema_version": "synaptic-modal-host/v1",
        "environment_name": "main", "profile": "modal-a10-v1",
        "training": {
            "schema_version": "synaptic-modal-training-policy/v1",
            "provider_ref": "modal", "profile_ref": "modal-a10-v1",
            "model": {"load_in_4bit": False},
        },
        "deployment": {"timeout_seconds": 3600},
        "volumes": {"control_name": "control-v1", "artifact_name": "artifact-v1"},
        "runtime_secret": {"name": "runtime-v1", "required_keys": ["HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"]},
        "runtime_environment": {"PATH": "/opt/conda/bin:/usr/bin", "LANG": "C.UTF-8"},
        "budget": {"maximum_cost_minor_units": 100, "currency": "USD"},
    }


def config() -> ModalHostConfigV1:
    return ModalHostConfigV1.from_mapping(config_mapping())


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


def test_training_policy_is_exact_canonical_and_domain_separated() -> None:
    policy = config().training
    expected = {
        "schema_version": "synaptic-modal-training-policy/v1",
        "provider_ref": "modal",
        "profile_ref": "modal-a10-v1",
        "model": {"load_in_4bit": False},
    }
    canonical = json.dumps(
        expected, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    assert policy.to_dict() == expected
    assert policy.canonical_bytes() == canonical
    assert policy.digest == hashlib.sha256(
        b"synaptic-modal-training-policy/v1\0" + canonical
    ).hexdigest()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.profile_ref = "other"  # type: ignore[misc]


def test_training_policy_rejects_closed_field_type_and_profile_attacks() -> None:
    valid = config_mapping()["training"]
    assert type(valid) is dict
    attacks = []
    for missing in tuple(valid):
        candidate = copy.deepcopy(valid)
        del candidate[missing]
        attacks.append(candidate)
    extra = copy.deepcopy(valid)
    extra["provider"] = "modal"
    attacks.append(extra)
    for field, value in (
        ("schema_version", "synaptic-modal-training-policy/v2"),
        ("provider_ref", "docker"),
        ("profile_ref", " modal-a10-v1"),
    ):
        candidate = copy.deepcopy(valid)
        candidate[field] = value
        attacks.append(candidate)
    for value in (1, 0, "true", None):
        candidate = copy.deepcopy(valid)
        candidate["model"]["load_in_4bit"] = value
        attacks.append(candidate)
    missing_model = copy.deepcopy(valid)
    missing_model["model"] = {}
    attacks.append(missing_model)
    extra_model = copy.deepcopy(valid)
    extra_model["model"]["quantization"] = "4bit"
    attacks.append(extra_model)
    for candidate in attacks:
        with pytest.raises((TypeError, ValueError)):
            ModalTrainingPolicyV1.from_mapping(candidate)
    with pytest.raises(ValueError, match="exact object"):
        ModalTrainingPolicyV1.from_mapping(MappingProxyType(valid))
    proxy_model = copy.deepcopy(valid)
    proxy_model["model"] = MappingProxyType(proxy_model["model"])
    with pytest.raises(ValueError, match="exact object"):
        ModalTrainingPolicyV1.from_mapping(proxy_model)
    class Text(str):
        pass

    for field in ("schema_version", "provider_ref", "profile_ref"):
        candidate = copy.deepcopy(valid)
        candidate[field] = Text(candidate[field])
        with pytest.raises((TypeError, ValueError)):
            ModalTrainingPolicyV1.from_mapping(candidate)


def test_host_config_requires_policy_and_binds_profile_and_digest() -> None:
    old = config_mapping()
    del old["training"]
    with pytest.raises(ValueError, match="missing or unknown"):
        ModalHostConfigV1.from_mapping(old)
    mismatch = config_mapping()
    mismatch["training"]["profile_ref"] = "modal-other-v1"
    with pytest.raises(ValueError, match="profile differs"):
        ModalHostConfigV1.from_mapping(mismatch)
    changed = config_mapping()
    changed["training"]["model"]["load_in_4bit"] = True
    changed_config = ModalHostConfigV1.from_mapping(changed)
    assert changed_config.training.digest != config().training.digest
    assert changed_config.digest != config().digest
    checked = ModalHostConfigV1.from_mapping(json.loads(
        (ROOT / "training/providers/modal.json").read_text(encoding="utf-8")
    ))
    assert checked.training.provider_ref == "modal"
    assert checked.training.profile_ref == checked.profile
    assert checked.training.load_in_4bit is False


def test_host_config_rejects_nonexact_root_nested_and_collection_types() -> None:
    callbacks = []

    class Dictionary(dict):
        def items(self):
            callbacks.append("items")
            return super().items()

    class Sequence(list):
        def __iter__(self):
            callbacks.append("iter")
            return super().__iter__()

    valid = config_mapping()
    for root in (MappingProxyType(valid), Dictionary(valid), object()):
        callbacks.clear()
        with pytest.raises(ValueError, match="exact object"):
            ModalHostConfigV1.from_mapping(root)
        assert callbacks == []
    for name in (
        "deployment", "volumes", "runtime_secret", "runtime_environment",
        "budget", "training",
    ):
        for wrapper in (MappingProxyType, Dictionary):
            candidate = copy.deepcopy(valid)
            candidate[name] = wrapper(candidate[name])
            callbacks.clear()
            with pytest.raises(ValueError, match="exact object"):
                ModalHostConfigV1.from_mapping(candidate)
            assert callbacks == []
    candidate = copy.deepcopy(valid)
    candidate["training"]["model"] = MappingProxyType(
        candidate["training"]["model"]
    )
    with pytest.raises(ValueError, match="exact object"):
        ModalHostConfigV1.from_mapping(candidate)
    candidate = copy.deepcopy(valid)
    candidate["runtime_secret"]["required_keys"] = Sequence(
        candidate["runtime_secret"]["required_keys"]
    )
    callbacks.clear()
    with pytest.raises(ValueError, match="malformed"):
        ModalHostConfigV1.from_mapping(candidate)
    assert callbacks == []


def test_host_config_rejects_string_subclasses_without_invoking_callbacks() -> None:
    calls = []

    class HostileText(str):
        def __eq__(self, other):
            calls.append("eq")
            return super().__eq__(other)

        def __hash__(self):
            calls.append("hash")
            return super().__hash__()

        def strip(self, *args, **kwargs):
            calls.append("strip")
            return super().strip(*args, **kwargs)

        def upper(self):
            calls.append("upper")
            return super().upper()

    attacks = []
    for path in (
        ("schema_version",), ("environment_name",), ("profile",),
        ("volumes", "control_name"), ("volumes", "artifact_name"),
        ("runtime_secret", "name"), ("budget", "currency"),
        ("training", "schema_version"), ("training", "provider_ref"),
        ("training", "profile_ref"),
    ):
        candidate = copy.deepcopy(config_mapping())
        target = candidate
        for component in path[:-1]:
            target = target[component]
        target[path[-1]] = HostileText(target[path[-1]])
        attacks.append(candidate)
    candidate = copy.deepcopy(config_mapping())
    candidate["runtime_secret"]["required_keys"][0] = HostileText("HF_TOKEN")
    attacks.append(candidate)
    candidate = copy.deepcopy(config_mapping())
    candidate["runtime_environment"]["LANG"] = HostileText("C.UTF-8")
    attacks.append(candidate)
    for candidate in attacks:
        calls.clear()
        with pytest.raises((TypeError, ValueError)):
            ModalHostConfigV1.from_mapping(candidate)
        assert calls == []
    hostile_key = copy.deepcopy(config_mapping())
    profile = hostile_key.pop("profile")
    hostile_key[HostileText("profile")] = profile
    calls.clear()
    with pytest.raises(ValueError, match="keys must be exact strings"):
        ModalHostConfigV1.from_mapping(hostile_key)
    assert calls == []


def test_host_config_direct_construction_rejects_nonexact_retained_values() -> None:
    class Text(str):
        pass

    policy = config().training
    arguments = dict(
        environment_name="main", profile="modal-a10-v1", training=policy,
        control_volume_name="control-v1", artifact_volume_name="artifact-v1",
        runtime_secret_name="runtime-v1",
        runtime_secret_keys=("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        runtime_environment={"LANG": "C.UTF-8"}, timeout_seconds=3600,
        maximum_cost_minor_units=100, currency="USD",
    )
    for name in (
        "environment_name", "profile", "control_volume_name",
        "artifact_volume_name", "runtime_secret_name", "currency",
    ):
        candidate = dict(arguments)
        candidate[name] = Text(candidate[name])
        with pytest.raises(TypeError, match="exact text"):
            ModalHostConfigV1(**candidate)
    for environment in (
        MappingProxyType({"LANG": "C.UTF-8"}),
        {"LANG": Text("C.UTF-8")},
    ):
        with pytest.raises(ValueError, match="exact"):
            ModalHostConfigV1(**{**arguments, "runtime_environment": environment})
    with pytest.raises(TypeError, match="exact string tuple"):
        ModalHostConfigV1(**{
            **arguments,
            "runtime_secret_keys": ["HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"],
        })
    with pytest.raises(TypeError, match="exact string tuple"):
        ModalHostConfigV1(**{
            **arguments,
            "runtime_secret_keys": (Text("HF_TOKEN"), "SYNAPTIC_EVIDENCE_MAC_KEY"),
        })


def authority_inputs(
    tmp_path: Path,
) -> tuple[
    ProjectContext, ModalHostConfigV1, object, ModalDeploymentJournalV1,
]:
    context = project_context(tmp_path)
    selected = context.config_root / "providers" / "modal.json"
    selected.parent.mkdir(parents=True)
    selected.write_text(
        json.dumps(config().to_dict(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    session = ExplicitModalHostSession.from_credentials(
        sdk=FakeSdk, config=config(), token_id="token-id", token_secret="token-secret"
    )
    state = session.deploy(
        context=context, authenticator=StubAuthenticator(), hf_token="hf-value"
    )
    journal = ModalDeploymentJournalV1.from_mapping(json.loads(
        (context.state_root / "modal/deployment-journal.json").read_text(
            encoding="utf-8"
        )
    ))
    return context, config(), state, journal


def test_provider_authority_loads_exact_deployed_lock_without_sdk_effects(
    monkeypatch, tmp_path: Path,
) -> None:
    context, expected_config, state, journal = authority_inputs(tmp_path)
    deployment_state = (
        dict(FakeVolume.registry), dict(FakeSecret.registry),
        FakeFunction.current, FakeApp.deployed,
    )
    monkeypatch.setattr(
        FakeClient, "from_credentials",
        classmethod(lambda *_args, **_kwargs: pytest.fail("SDK client call")),
    )
    monkeypatch.setattr(
        FakeApp, "lookup",
        classmethod(lambda *_args, **_kwargs: pytest.fail("SDK app call")),
    )
    authority = ModalProviderAuthorityV1.load(context)
    assert authority.config == expected_config
    assert authority.training is authority.config.training
    assert authority.state == state
    assert authority.journal == journal
    assert deployment_state == (
        dict(FakeVolume.registry), dict(FakeSecret.registry),
        FakeFunction.current, FakeApp.deployed,
    )


def test_provider_authority_rejects_policy_state_journal_and_volume_confusion(
    tmp_path: Path,
) -> None:
    context, host_config, state, journal = authority_inputs(tmp_path)
    replacement_policy = ModalTrainingPolicyV1.from_mapping(
        host_config.training.to_dict()
    )
    with pytest.raises(ValueError, match="policy identity"):
        ModalProviderAuthorityV1(host_config, replacement_policy, state, journal)

    changed_config_value = host_config.to_dict()
    changed_config_value["profile"] = "modal-other-v1"
    changed_config_value["training"]["profile_ref"] = "modal-other-v1"
    changed_config = ModalHostConfigV1.from_mapping(changed_config_value)
    changed_journal = ModalDeploymentJournalV1(
        changed_config.digest, journal.deployment_ref,
        journal.function_name, journal.resource_policy,
    )
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1(
            changed_config, changed_config.training, state, changed_journal
        )

    other_journal = ModalDeploymentJournalV1.create(host_config, adopt_empty=False)
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1(
            host_config, host_config.training, state, other_journal
        )

    original_control = state.control_volume_id
    object.__setattr__(state, "control_volume_id", "modal-volume-" + "f" * 32)
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1(
            host_config, host_config.training, state, journal
        )
    object.__setattr__(state, "control_volume_id", original_control)

    journal_path = context.state_root / "modal/deployment-journal.json"
    stale = journal.to_dict()
    stale["config_digest"] = "0" * 64
    journal_path.write_text(json.dumps(stale), encoding="utf-8")
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1.load(context)


def test_provider_authority_rejects_coordinated_cross_environment_state_and_journal(
    tmp_path: Path,
) -> None:
    context, host_config, state, journal = authority_inputs(tmp_path)
    state_value = state.to_dict()
    state_value["binding"]["environment_ref"] = "other"
    state_value["selection"]["environment_ref"] = "other"
    state_value["volumes"] = {
        "control_volume_id": modal_provider._opaque_ref(
            "volume", state.binding.account_ref, "other",
            host_config.control_volume_name,
        ),
        "artifact_volume_id": modal_provider._opaque_ref(
            "volume", state.binding.account_ref, "other",
            host_config.artifact_volume_name,
        ),
    }
    assert state_value["volumes"]["control_volume_id"] != state.control_volume_id
    cross_environment_state = type(state).from_mapping(state_value)
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1(
            host_config, host_config.training, cross_environment_state, journal
        )
    state_path = context.state_root / "modal/provider-state.json"
    state_path.write_text(json.dumps(state_value), encoding="utf-8")
    with pytest.raises(ValueError, match="identities disagree"):
        ModalProviderAuthorityV1.load(context)


@pytest.mark.parametrize(
    "attack",
    [
        "profile", "deployment", "function", "runtime", "control-volume",
        "artifact-volume", "sdk-binding", "sdk-selection",
    ],
)
def test_provider_authority_rejects_every_pinned_state_identity(
    tmp_path: Path, attack: str,
) -> None:
    _context, host_config, state, journal = authority_inputs(tmp_path)
    if attack == "profile":
        object.__setattr__(state.profile, "profile", "modal-other-v1")
    elif attack == "deployment":
        object.__setattr__(
            state.profile, "deployment_ref", "modal-deployment-" + "d" * 32
        )
    elif attack == "function":
        object.__setattr__(state.profile, "function_name", "synaptic-other")
    elif attack == "runtime":
        object.__setattr__(state.selection, "image_digest", "f" * 64)
    elif attack == "control-volume":
        object.__setattr__(state.profile, "control_volume_ref", "control-other")
    elif attack == "artifact-volume":
        object.__setattr__(state.profile, "artifact_volume_ref", "artifact-other")
    elif attack == "sdk-binding":
        object.__setattr__(state.binding, "sdk_version", "1.5.5")
    else:
        object.__setattr__(state.selection, "sdk_version", "1.5.5")
    with pytest.raises((TypeError, ValueError)):
        ModalProviderAuthorityV1(
            host_config, host_config.training, state, journal
        )


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
