"""Host-owned Modal SDK session, deployment, and exact provider-state lock."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_tuner.api.v1.modal import (
    EXACT_MODAL_SDK_VERSION,
    EnvironmentHmacAuthenticator,
    ExplicitModal154ReadFacade,
    GitDualCloneMaterializer,
    ModalClientBinding,
    ModalDeploymentSelectionV1,
    ModalDeploymentSpecV1,
    ModalProviderProfileV1,
    ModalRuntimeLockV1,
    ModalSecretProfileV1,
    MountedCompletionProducerV1,
    MountedModalWorkerV1,
    SubprocessSftRunner,
    build_modal_deployment,
    modal_function_name,
)

from .modal_resolver import ModalProviderStateV1, _closed, _read_json, _text
from .security import FileHmacAuthenticator


@dataclass(frozen=True, slots=True)
class ModalHostConfigV1:
    environment_name: str
    profile: str
    control_volume_name: str
    artifact_volume_name: str
    runtime_secret_name: str
    runtime_secret_keys: tuple[str, ...]
    runtime_environment: Mapping[str, str]
    timeout_seconds: int
    maximum_cost_minor_units: int
    currency: str

    def __post_init__(self) -> None:
        for name in (
            "environment_name", "profile",
            "control_volume_name", "artifact_volume_name",
            "runtime_secret_name", "currency",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.control_volume_name == self.artifact_volume_name:
            raise ValueError("Modal volumes must differ")
        keys = tuple(self.runtime_secret_keys)
        if keys != ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"):
            raise ValueError("Modal v1 runtime secret keys are fixed")
        object.__setattr__(self, "runtime_secret_keys", keys)
        environment = dict(self.runtime_environment)
        if not environment or any(
            not isinstance(key, str) or not key or not isinstance(value, str)
            for key, value in environment.items()
        ):
            raise ValueError("runtime environment must be a nonempty string map")
        object.__setattr__(self, "runtime_environment", MappingProxyType(environment))
        if type(self.timeout_seconds) is not int or not 1 <= self.timeout_seconds <= 86400:
            raise ValueError("timeout must be a bounded integer")
        if type(self.maximum_cost_minor_units) is not int or self.maximum_cost_minor_units < 0:
            raise ValueError("maximum cost must be a non-negative integer")
        currency = self.currency.upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ModalHostConfigV1":
        root = _closed(
            value,
            {
                "schema_version", "environment_name", "profile", "deployment",
                "volumes", "runtime_secret", "runtime_environment", "budget",
            },
            "Modal host config",
        )
        if root["schema_version"] != "synaptic-modal-host/v1":
            raise ValueError("unsupported Modal host config schema")
        deployment = _closed(root["deployment"], {"timeout_seconds"}, "deployment")
        volumes = _closed(root["volumes"], {"control_name", "artifact_name"}, "volumes")
        secret = _closed(root["runtime_secret"], {"name", "required_keys"}, "runtime secret")
        budget = _closed(root["budget"], {"maximum_cost_minor_units", "currency"}, "budget")
        if not isinstance(secret["required_keys"], list) or not isinstance(root["runtime_environment"], Mapping):
            raise ValueError("Modal secret keys and runtime environment are malformed")
        return cls(
            environment_name=root["environment_name"], profile=root["profile"],
            control_volume_name=volumes["control_name"],
            artifact_volume_name=volumes["artifact_name"],
            runtime_secret_name=secret["name"],
            runtime_secret_keys=tuple(secret["required_keys"]),
            runtime_environment=dict(root["runtime_environment"]),
            timeout_seconds=deployment["timeout_seconds"],
            maximum_cost_minor_units=budget["maximum_cost_minor_units"],
            currency=budget["currency"],
        )

    @classmethod
    def load(cls, context: ProjectContext, path: Path | None = None) -> "ModalHostConfigV1":
        selected = path or context.config_root / "providers" / "modal.json"
        selected = selected.resolve()
        if not selected.is_relative_to(context.config_root.resolve()):
            raise ValueError("Modal host config must live below the host config root")
        return cls.from_mapping(_read_json(selected))

    @property
    def digest(self) -> str:
        value = {
            "environment_name": self.environment_name,
            "profile": self.profile,
            "control_volume_name": self.control_volume_name,
            "artifact_volume_name": self.artifact_volume_name,
            "runtime_secret_name": self.runtime_secret_name,
            "runtime_secret_keys": list(self.runtime_secret_keys),
            "runtime_environment": dict(self.runtime_environment),
            "timeout_seconds": self.timeout_seconds,
            "maximum_cost_minor_units": self.maximum_cost_minor_units,
            "currency": self.currency,
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ModalDeploymentJournalV1:
    """Host authority for exactly one resumable provider deployment."""

    config_digest: str
    deployment_ref: str
    function_name: str
    resource_policy: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.config_digest, str)
            or len(self.config_digest) != 64
            or any(character not in "0123456789abcdef" for character in self.config_digest)
        ):
            raise ValueError("deployment journal config digest is invalid")
        expected = modal_function_name(self.deployment_ref)
        if self.function_name != expected:
            raise ValueError("deployment journal function identity changed")
        if self.resource_policy not in {"create", "adopt-empty"}:
            raise ValueError("deployment journal resource policy is invalid")

    @classmethod
    def create(
        cls, config: ModalHostConfigV1, *, adopt_empty: bool
    ) -> "ModalDeploymentJournalV1":
        if type(config) is not ModalHostConfigV1:
            raise TypeError("exact Modal host config is required")
        deployment_ref = "modal-deployment-" + secrets.token_hex(16)
        return cls(
            config.digest, deployment_ref, modal_function_name(deployment_ref),
            "adopt-empty" if adopt_empty else "create",
        )

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> "ModalDeploymentJournalV1":
        root = _closed(
            value,
            {
                "schema_version", "config_digest", "deployment_ref",
                "function_name", "resource_policy",
            },
            "Modal deployment journal",
        )
        if root["schema_version"] != "synaptic-modal-deployment-journal/v1":
            raise ValueError("unsupported Modal deployment journal schema")
        return cls(
            root["config_digest"], root["deployment_ref"],
            root["function_name"], root["resource_policy"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-modal-deployment-journal/v1",
            "config_digest": self.config_digest,
            "deployment_ref": self.deployment_ref,
            "function_name": self.function_name,
            "resource_policy": self.resource_policy,
        }


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError("durable host record already exists")
    temporary = path.parent / ("." + path.name + "." + secrets.token_hex(8) + ".tmp")
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), indent=2) + "\n"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, payload.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

def _opaque_ref(kind: str, *values: str) -> str:
    payload = "\0".join(_text(value, f"{kind} identity component") for value in values)
    return f"modal-{kind}-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]



class ExplicitModalHostSession:
    """One explicit Modal 1.5.4 client bound to host state and environment."""

    def __init__(self, *, sdk: object, client: object, config: ModalHostConfigV1, binding: ModalClientBinding):
        if getattr(sdk, "__version__", None) != EXACT_MODAL_SDK_VERSION:
            raise ValueError("Modal SDK must be exactly 1.5.4")
        self.sdk = sdk
        self.client = client
        self.config = config
        self.binding = binding

    @classmethod
    def from_credentials(
        cls, *, sdk: object, config: ModalHostConfigV1,
        token_id: str, token_secret: str,
    ) -> "ExplicitModalHostSession":
        if not token_id or not token_secret:
            raise ValueError("explicit Modal credentials are required")
        client = sdk.Client.from_credentials(token_id, token_secret)
        return cls.from_client(sdk=sdk, config=config, client=client)

    @classmethod
    def from_client(
        cls, *, sdk: object, config: ModalHostConfigV1, client: object
    ) -> "ExplicitModalHostSession":
        """Bind an explicit client, including one loaded from Modal host config."""
        if getattr(sdk, "__version__", None) != EXACT_MODAL_SDK_VERSION:
            raise ValueError("Modal SDK must be exactly 1.5.4")
        if client is None:
            raise ValueError("explicit authenticated Modal client is required")
        workspace = sdk.Workspace.from_context(client=client)
        workspace.hydrate()
        environment = sdk.Environment.from_name(config.environment_name, client=client)
        environment.hydrate()
        workspace_name = _text(workspace.name, "workspace name")
        environment_name = _text(environment.name, "environment name")
        if environment_name != config.environment_name:
            raise ValueError("Modal environment identity changed")
        workspace_ref = _opaque_ref("workspace", workspace_name)
        client_ref = _opaque_ref(
            "client", workspace_name, environment_name, EXACT_MODAL_SDK_VERSION
        )
        binding = ModalClientBinding(
            workspace_ref, workspace_name, environment_name,
            client_ref, EXACT_MODAL_SDK_VERSION,
        )
        return cls(sdk=sdk, client=client, config=config, binding=binding)

    def observe_scope(self, client: object) -> tuple[str, str, str, str]:
        if client is not self.client:
            raise ValueError("Modal client identity changed")
        workspace = self.sdk.Workspace.from_context(client=client)
        workspace.hydrate()
        environment = self.sdk.Environment.from_name(
            self.config.environment_name, client=client
        )
        environment.hydrate()
        workspace_name = _text(workspace.name, "workspace name")
        environment_name = _text(environment.name, "environment name")
        if workspace_name != self.binding.workspace_ref:
            raise ValueError("Modal workspace identity changed")
        if environment_name != self.config.environment_name:
            raise ValueError("Modal environment identity changed")
        return (
            self.binding.account_ref, workspace_name, environment_name, self.binding.client_ref,
        )

    def _optional_volume(self, name: str):
        try:
            value = self.sdk.Volume.from_name(
                name, version=1, create_if_missing=False,
                environment_name=self.config.environment_name,
                client=self.client,
            )
            value.hydrate(self.client)
            if value.is_hydrated is not True:
                raise ValueError
            return value
        except self.sdk.exception.NotFoundError:
            return None
        except Exception:
            raise ValueError("Modal volume observation failed") from None

    def _optional_secret(self):
        try:
            value = self.sdk.Secret.from_name(
                self.config.runtime_secret_name,
                environment_name=self.config.environment_name,
                required_keys=list(self.config.runtime_secret_keys),
                client=self.client,
            )
            value.hydrate(self.client)
            if value.is_hydrated is not True:
                raise ValueError
            return value
        except self.sdk.exception.NotFoundError:
            return None
        except Exception:
            raise ValueError("Modal secret observation failed") from None

    def _app_exists(self) -> bool:
        try:
            self.sdk.App.lookup(
                "synaptic-training-v1",
                environment_name=self.config.environment_name,
                create_if_missing=False,
                client=self.client,
            )
            return True
        except self.sdk.exception.NotFoundError:
            return False
        except Exception:
            raise ValueError("Modal application observation failed") from None

    @staticmethod
    def _volume_is_empty(volume: object) -> bool:
        try:
            return next(volume.iterdir("/", recursive=True), None) is None
        except Exception:
            raise ValueError("Modal volume inventory failed") from None

    def facade(self, state: ModalProviderStateV1) -> ExplicitModal154ReadFacade:
        if state.binding != self.binding:
            raise ValueError("authenticated Modal session differs from provider state")

        def deployment_observer(**arguments):
            if set(arguments) != {
                "client", "app_name", "function_name", "environment_name",
            }:
                raise ValueError("Modal deployment observation is malformed")
            if (
                arguments["client"] is not self.client
                or arguments["app_name"] != state.selection.app_name
                or arguments["function_name"] != state.selection.function_name
                or arguments["environment_name"]
                != state.selection.environment_ref
            ):
                raise ValueError("Modal deployment observation changed")
            return state.selection

        return ExplicitModal154ReadFacade(
            self.binding, sdk=self.sdk, client=self.client,
            scope_observer=self.observe_scope,
            deployment_observer=deployment_observer,
            volume_names={
                state.control_volume_id: state.profile.control_volume_ref,
                state.artifact_volume_id: state.profile.artifact_volume_ref,
            },
        )

    def deploy(
        self,
        *,
        context: ProjectContext,
        authenticator: FileHmacAuthenticator,
        hf_token: str,
        adopt_empty: bool = False,
    ) -> ModalProviderStateV1:
        if type(adopt_empty) is not bool:
            raise TypeError("adopt_empty must be an exact boolean")
        state_path = context.state_root / "modal" / "provider-state.json"
        journal_path = context.state_root / "modal" / "deployment-journal.json"
        if state_path.exists() or state_path.is_symlink():
            raise FileExistsError("Modal provider is already deployed for this host")
        if not hf_token:
            raise ValueError("HF_TOKEN is required to bind the named Modal Secret")

        control = self._optional_volume(self.config.control_volume_name)
        artifact = self._optional_volume(self.config.artifact_volume_name)
        runtime_secret = self._optional_secret()
        app_exists = self._app_exists()
        if journal_path.exists() or journal_path.is_symlink():
            journal = ModalDeploymentJournalV1.from_mapping(
                _read_json(journal_path)
            )
            if journal.config_digest != self.config.digest:
                raise ValueError("deployment journal differs from host config")
            if adopt_empty and journal.resource_policy != "adopt-empty":
                raise ValueError("deployment journal resource policy changed")
        else:
            if adopt_empty:
                if control is None or artifact is None or runtime_secret is None:
                    raise ValueError("adopt-empty requires every named resource")
                if (
                    not self._volume_is_empty(control)
                    or not self._volume_is_empty(artifact)
                ):
                    raise ValueError("adopt-empty requires empty Modal volumes")
            elif any(
                value is not None
                for value in (control, artifact, runtime_secret)
            ) or app_exists:
                raise ValueError("Modal deployment resource collision")
            journal = ModalDeploymentJournalV1.create(
                self.config, adopt_empty=adopt_empty
            )
            _atomic_json(journal_path, journal.to_dict())

        authenticator.initialize()
        runtime_lock = ModalRuntimeLockV1.packaged()
        if journal.resource_policy == "adopt-empty":
            if control is None or artifact is None or runtime_secret is None:
                raise ValueError("adopted Modal resource disappeared")
            if (
                not self._volume_is_empty(control)
                or not self._volume_is_empty(artifact)
            ):
                raise ValueError("adopted Modal volume is no longer empty")
        else:
            if control is None:
                control = self.sdk.Volume.objects.create(
                    self.config.control_volume_name, version=1,
                    allow_existing=False,
                    environment_name=self.config.environment_name,
                    client=self.client,
                )
            if artifact is None:
                artifact = self.sdk.Volume.objects.create(
                    self.config.artifact_volume_name, version=1,
                    allow_existing=False,
                    environment_name=self.config.environment_name,
                    client=self.client,
                )
            if runtime_secret is None:
                runtime_secret = self.sdk.Secret.objects.create(
                    self.config.runtime_secret_name,
                    {
                        "HF_TOKEN": hf_token,
                        "SYNAPTIC_EVIDENCE_MAC_KEY": authenticator.encoded_key,
                    },
                    allow_existing=False,
                    environment_name=self.config.environment_name,
                    client=self.client,
                )
        remote_auth = EnvironmentHmacAuthenticator(
            environment_key="SYNAPTIC_EVIDENCE_MAC_KEY",
            key_ref=authenticator.key_ref,
        )
        completion = MountedCompletionProducerV1(remote_auth)
        worker = MountedModalWorkerV1(
            verifier=remote_auth,
            sources=GitDualCloneMaterializer(),
            processes=SubprocessSftRunner(
                secret_keys=self.config.runtime_secret_keys,
                timeout_seconds=self.config.timeout_seconds,
            ),
            completion=completion,
        )
        objects = build_modal_deployment(
            sdk=self.sdk, client=self.client,
            environment_name=self.config.environment_name,
            spec=ModalDeploymentSpecV1(
                deployment_ref=journal.deployment_ref,
                function_name=journal.function_name,
                registry_reference=runtime_lock.registry_reference,
                control_volume_name=self.config.control_volume_name,
                artifact_volume_name=self.config.artifact_volume_name,
                runtime_secret_name=self.config.runtime_secret_name,
                runtime_secret_keys=self.config.runtime_secret_keys,
                environment=self.config.runtime_environment,
                timeout_seconds=self.config.timeout_seconds,
            ),
            worker=worker,
        )
        objects.app.deploy(
            name="synaptic-training-v1",
            environment_name=self.config.environment_name,
            client=self.client,
            strategy="recreate",
        )
        exact_function = self.sdk.Function.from_name(
            "synaptic-training-v1", journal.function_name,
            environment_name=self.config.environment_name,
            client=self.client,
        )
        exact_function.hydrate(self.client)
        if exact_function.is_hydrated is not True:
            raise ValueError("deployed function did not hydrate by exact name")
        for volume_name in (
            self.config.control_volume_name, self.config.artifact_volume_name,
        ):
            if self._optional_volume(volume_name) is None:
                raise ValueError("deployed Modal volume disappeared")
        profile = ModalProviderProfileV1(
            self.config.profile,
            "synaptic-training-v1",
            journal.function_name,
            journal.deployment_ref,
            "engine://tuner/execution/providers/modal/modal-runtime-v1.lock.json",
            self.config.control_volume_name,
            self.config.artifact_volume_name,
            (ModalSecretProfileV1(
                self.config.runtime_secret_name, self.config.runtime_secret_keys
            ),),
        )
        selection = ModalDeploymentSelectionV1.from_profile(
            profile, binding=self.binding,
            runtime_environment=self.config.runtime_environment,
            timeout_seconds=self.config.timeout_seconds,
        )
        control_ref = _opaque_ref(
            "volume", self.binding.account_ref, self.config.control_volume_name
        )
        artifact_ref = _opaque_ref(
            "volume", self.binding.account_ref, self.config.artifact_volume_name
        )
        state = ModalProviderStateV1(
            profile, self.binding, selection, control_ref, artifact_ref,
        )
        _atomic_json(state_path, state.to_dict())
        return state
