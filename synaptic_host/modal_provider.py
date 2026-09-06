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

from .cli import _read_committed_git_blob_v1
from .modal_resolver import ModalProviderStateV1, _closed, _read_json, _text
from .security import FileHmacAuthenticator, _lexical_absolute


# --- R1 (section 29.3 ruling (1)): two keys, three refs -------------------
#
# `modal-evidence-v1` is the HOST key.  It signs and verifies the source and
# deployment attestations.  It never leaves the Host and is never a Secret
# value.
#
# `modal-worker-v1` is the WORKER key.  It is the only key placed in the
# runtime Secret and the only ref carried by `stage_target.key_ref`, so the
# container channel is confined to it.
#
# Section 29.13 item 1: the algorithm is a symmetric HMAC, so the ability to
# verify is the ability to sign.  Separating the keys confines the scope of
# the container channel.  It does not make evidence produced inside a
# container unforgeable, and nothing here should be read as claiming that.
HOST_EVIDENCE_KEY_REF = "modal-evidence-v1"
WORKER_EVIDENCE_KEY_REF = "modal-worker-v1"


def build_worker_authenticator(
    context: ProjectContext,
) -> FileHmacAuthenticator:
    """Open the container-channel key at `state_root/modal/worker-hmac.key`.

    Section 29.3 ruling (1), key 2.  This is the ONLY key placed in the
    runtime Secret and the only ref carried by `stage_target.key_ref`.  It is
    a sibling of the host key inside the same private `state_root/modal`
    directory, so it inherits that directory's already-validated
    private-storage chain.  The caller owns `initialize()`; `initialize`
    creates with `O_EXCL` and never overwrites, so calling it against an
    existing key is a read.
    """

    return FileHmacAuthenticator(
        context.state_root / "modal" / "worker-hmac.key",
        key_ref=WORKER_EVIDENCE_KEY_REF,
    )


def _require_worker_authenticator(authenticator: object) -> None:
    """Refuse any authenticator not bound to the worker key reference.

    The check is POSITIVE: it admits exactly `WORKER_EVIDENCE_KEY_REF` and
    refuses everything else, including a missing attribute.  It runs at the
    ENTRY of `deploy` and `upgrade`, before any Modal resource is created,
    because both creates refuse an existing resource: a guard placed later
    would fire only after the wrong key had already been published under a
    Secret that cannot then be replaced.
    """

    key_ref = getattr(authenticator, "key_ref", None)
    if key_ref != WORKER_EVIDENCE_KEY_REF:
        raise ValueError(
            "Modal deployment requires the worker evidence key reference"
        )


def _exact_object(
    value: object, expected: set[str], label: str,
) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an exact object")
    try:
        items = tuple(dict.items(value))
    except BaseException:
        raise ValueError(f"{label} could not be snapshotted") from None
    if any(type(key) is not str for key, _member in items):
        raise ValueError(f"{label} keys must be exact strings")
    if {key for key, _member in items} != expected:
        raise ValueError(f"{label} contains missing or unknown fields")
    return {key: member for key, member in items}


def _exact_string_map(value: object, label: str) -> dict[str, str]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an exact object")
    try:
        items = tuple(dict.items(value))
    except BaseException:
        raise ValueError(f"{label} could not be snapshotted") from None
    if not items or any(
        type(key) is not str or not key
        or type(member) is not str
        for key, member in items
    ):
        raise ValueError(f"{label} must be a nonempty exact string map")
    return {key: member for key, member in items}


@dataclass(frozen=True, slots=True)
class ModalTrainingPolicyV1:
    schema_version: str
    provider_ref: str
    profile_ref: str
    load_in_4bit: bool

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not str
            or self.schema_version != "synaptic-modal-training-policy/v1"
        ):
            raise ValueError("unsupported Modal training policy schema")
        if type(self.provider_ref) is not str or self.provider_ref != "modal":
            raise ValueError("Modal training policy provider is invalid")
        if type(self.profile_ref) is not str:
            raise TypeError("training profile_ref must be exact text")
        object.__setattr__(
            self, "profile_ref", _text(self.profile_ref, "training profile_ref")
        )
        if type(self.load_in_4bit) is not bool:
            raise TypeError("model.load_in_4bit must be an exact boolean")

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> "ModalTrainingPolicyV1":
        if type(value) is not dict:
            raise ValueError("Modal training policy must be an exact object")
        root = _exact_object(
            value,
            {"schema_version", "provider_ref", "profile_ref", "model"},
            "Modal training policy",
        )
        if type(root["model"]) is not dict:
            raise ValueError("Modal training model policy must be an exact object")
        model = _exact_object(
            root["model"], {"load_in_4bit"}, "Modal training model policy"
        )
        return cls(
            root["schema_version"], root["provider_ref"], root["profile_ref"],
            model["load_in_4bit"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "provider_ref": self.provider_ref,
            "profile_ref": self.profile_ref,
            "model": {"load_in_4bit": self.load_in_4bit},
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            b"synaptic-modal-training-policy/v1\0" + self.canonical_bytes()
        ).hexdigest()


_MAX_MODAL_CONFIG_BYTES = 1024 * 1024


def _read_committed_configuration_v1(
    context: ProjectContext, selected: Path
) -> dict[str, object]:
    """Read one provider configuration from the project's committed HEAD tree.

    C1 (section 29.5(f)).  The docker arm has read the committed blob since
    `cli.py` was written; the modal arm read whatever happened to be on disk.
    That asymmetry is the one item on the 29.5 list whose failure is silent.
    The container materializes the project by cloning the committed commit
    from the committed origin (`GitDualCloneMaterializer`, wired into the
    worker below), so a worktree-only edit to this file changed which provider
    environment, which two volumes, which Secret and which cost ceiling the
    Host acted under while the cloud job executed released source.  Nothing
    raised.  Nothing in the run record disagreed with itself.

    The route is `cli._read_committed_git_blob_v1`, the same helper the docker
    arm reads its training input through, so the two arms cannot drift apart
    again without one diff touching both.  No worktree byte of this file is
    parsed here, which also removes the symlink and size questions the
    worktree read had to answer for itself.

    A configuration the released checkout does not contain is not readable at
    all: the helper refuses, and the run stops before any provider call.  That
    is the intended refusal, not a regression.
    """

    project = Path(context.project_root).resolve(strict=True)
    try:
        relative = selected.relative_to(project).as_posix()
    except ValueError:
        raise ValueError(
            "Modal host config must live below the project root"
        ) from None
    blob = _read_committed_git_blob_v1(
        project, relative, maximum_bytes=_MAX_MODAL_CONFIG_BYTES,
    )
    try:
        value = json.loads(blob.content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("configuration must contain valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("configuration must contain a JSON object")
    return value


@dataclass(frozen=True, slots=True)
class ModalHostConfigV1:
    environment_name: str
    profile: str
    training: ModalTrainingPolicyV1
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
            if type(getattr(self, name)) is not str:
                raise TypeError(f"{name} must be exact text")
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if type(self.training) is not ModalTrainingPolicyV1:
            raise TypeError("training must be an exact ModalTrainingPolicyV1")
        if self.training.profile_ref != self.profile:
            raise ValueError("Modal training policy profile differs from host config")
        if self.control_volume_name == self.artifact_volume_name:
            raise ValueError("Modal volumes must differ")
        if type(self.runtime_secret_keys) is not tuple or any(
            type(key) is not str for key in self.runtime_secret_keys
        ):
            raise TypeError("runtime secret keys must be an exact string tuple")
        keys = tuple(self.runtime_secret_keys)
        if keys != ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"):
            raise ValueError("Modal v1 runtime secret keys are fixed")
        object.__setattr__(self, "runtime_secret_keys", keys)
        environment = _exact_string_map(
            self.runtime_environment, "runtime environment"
        )
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
        root = _exact_object(
            value,
            {
                "schema_version", "environment_name", "profile", "deployment",
                "volumes", "runtime_secret", "runtime_environment", "budget",
                "training",
            },
            "Modal host config",
        )
        if (
            type(root["schema_version"]) is not str
            or root["schema_version"] != "synaptic-modal-host/v1"
        ):
            raise ValueError("unsupported Modal host config schema")
        deployment = _exact_object(
            root["deployment"], {"timeout_seconds"}, "deployment"
        )
        volumes = _exact_object(
            root["volumes"], {"control_name", "artifact_name"}, "volumes"
        )
        secret = _exact_object(
            root["runtime_secret"], {"name", "required_keys"}, "runtime secret"
        )
        budget = _exact_object(
            root["budget"], {"maximum_cost_minor_units", "currency"}, "budget"
        )
        if type(secret["required_keys"]) is not list:
            raise ValueError("Modal secret keys and runtime environment are malformed")
        try:
            secret_keys = tuple(list.__iter__(secret["required_keys"]))
        except BaseException:
            raise ValueError("Modal secret keys could not be snapshotted") from None
        if any(type(key) is not str for key in secret_keys):
            raise ValueError("Modal secret keys must be exact strings")
        environment = _exact_string_map(
            root["runtime_environment"], "runtime environment"
        )
        return cls(
            environment_name=root["environment_name"], profile=root["profile"],
            training=ModalTrainingPolicyV1.from_mapping(root["training"]),
            control_volume_name=volumes["control_name"],
            artifact_volume_name=volumes["artifact_name"],
            runtime_secret_name=secret["name"],
            runtime_secret_keys=secret_keys,
            runtime_environment=environment,
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
        # C1 (section 29.5(f)).  The committed blob, not the worktree file.
        return cls.from_mapping(_read_committed_configuration_v1(context, selected))

    @property
    def digest(self) -> str:
        value = {
            "environment_name": self.environment_name,
            "profile": self.profile,
            "training": self.training.to_dict(),
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

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-modal-host/v1",
            "environment_name": self.environment_name,
            "profile": self.profile,
            "training": self.training.to_dict(),
            "deployment": {"timeout_seconds": self.timeout_seconds},
            "volumes": {
                "control_name": self.control_volume_name,
                "artifact_name": self.artifact_volume_name,
            },
            "runtime_secret": {
                "name": self.runtime_secret_name,
                "required_keys": list(self.runtime_secret_keys),
            },
            "runtime_environment": dict(self.runtime_environment),
            "budget": {
                "maximum_cost_minor_units": self.maximum_cost_minor_units,
                "currency": self.currency,
            },
        }


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
        if self.resource_policy not in {"create", "adopt-empty", "reuse-existing"}:
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


@dataclass(frozen=True, slots=True)
class ModalUpgradeJournalV1:
    """Durable intent for one resumable provider-code upgrade."""

    config_digest: str
    prior_deployment_ref: str
    replacement: ModalDeploymentJournalV1

    def __post_init__(self) -> None:
        if self.config_digest != self.replacement.config_digest:
            raise ValueError("upgrade journal config digest changed")
        if self.replacement.resource_policy != "reuse-existing":
            raise ValueError("upgrade journal must reuse existing resources")
        modal_function_name(self.prior_deployment_ref)
        if self.prior_deployment_ref == self.replacement.deployment_ref:
            raise ValueError("upgrade deployment identity must change")

    @classmethod
    def create(
        cls, config: ModalHostConfigV1, *, prior_deployment_ref: str
    ) -> "ModalUpgradeJournalV1":
        deployment_ref = "modal-deployment-" + secrets.token_hex(16)
        replacement = ModalDeploymentJournalV1(
            config.digest, deployment_ref, modal_function_name(deployment_ref),
            "reuse-existing",
        )
        return cls(config.digest, prior_deployment_ref, replacement)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ModalUpgradeJournalV1":
        root = _closed(
            value,
            {
                "schema_version", "config_digest", "prior_deployment_ref",
                "replacement",
            },
            "Modal upgrade journal",
        )
        if root["schema_version"] != "synaptic-modal-upgrade-journal/v1":
            raise ValueError("unsupported Modal upgrade journal schema")
        return cls(
            root["config_digest"], root["prior_deployment_ref"],
            ModalDeploymentJournalV1.from_mapping(root["replacement"]),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-modal-upgrade-journal/v1",
            "config_digest": self.config_digest,
            "prior_deployment_ref": self.prior_deployment_ref,
            "replacement": self.replacement.to_dict(),
        }


# SEC-F2: the carrier authenticator in `_ensure_private_chain` needs a key
# path to derive its leaf from, and a key reference to satisfy the
# constructor.  Neither names anything real: the file is never created, read
# or written, and the reference never signs or verifies.  They are spelled
# distinctly so a grep for either evidence key ref cannot match them.
_SENTINEL_KEY_NAME = ".private-chain-anchor"
_SENTINEL_KEY_REF = "modal-private-chain-anchor-not-a-key"


def _private_storage_root(context: ProjectContext) -> Path:
    """The `.synaptic` root that confines everything this lane writes.

    SEC-F2 (section 29.5(c)).  The ruling's decision (2) scopes the fix to the
    whole `.synaptic` subtree this lane writes, not only `state/modal`, so the
    chain to repair and validate starts here and not at the leaf.  This is the
    same anchor `FileHmacAuthenticator.for_docker` uses for the Docker control
    key, read from the same field of the same context.
    """

    return _lexical_absolute(Path(context.project_root) / ".synaptic")


def _ensure_private_chain(private_root: Path, leaf: Path) -> None:
    """Create and validate every directory from `private_root` down to `leaf`.

    SEC-F2 (section 29.5(c)).  Before this, the durable-record writers below
    reached their parent directory with a bare
    `path.parent.mkdir(parents=True, exist_ok=True)`: none of the B-11
    private-chain construction, none of the B-11-R1 leaf-first repair, no
    validation.  The `0o600` on the record file was real, and the directory
    holding it inherited whatever the parent granted.  `.synaptic` is where
    this lane's evidence keys live, so an inherited list there is an ACL
    property of the key material, not of the record.

    *Reuse, and no new mechanism.*  The ruling requires exactly that, so this
    delegates to `FileHmacAuthenticator._ensure_private_storage_directories`
    rather than restating its walk.  That method derives its chain from
    `_private_storage_root` down to `key_path.parent` and runs the B-11-R1 two
    passes over it: pass A repairs leaf first, so a member is judged before a
    write higher up the chain can alter it, and pass B creates missing members
    root first and validates every member unconditionally and last.  Keeping
    one copy of that order matters more than the small awkwardness here: the
    ordering rule is the whole content of B-11-R1, and a second copy of it
    would be a second thing to keep correct.

    The authenticator constructed here is a carrier for those two fields and
    nothing else.  `_SENTINEL_KEY_NAME` names a file that is never created,
    never read, and never written; the method uses only its parent.  A test
    pins that the sentinel does not exist after this returns, so a future
    change that started touching `key_path` would be caught rather than
    silently minting a file under `.synaptic`.

    It carries no key material and mints none.
    """

    carrier = FileHmacAuthenticator(
        _lexical_absolute(Path(leaf)) / _SENTINEL_KEY_NAME,
        key_ref=_SENTINEL_KEY_REF,
    )
    carrier._private_storage_root = _lexical_absolute(Path(private_root))
    carrier._ensure_private_storage_directories(repair=True)


def _atomic_json(
    path: Path, value: Mapping[str, object], *, private_root: Path
) -> None:
    # SEC-F2: keyword-only and REQUIRED, with no default, in the same shape as
    # the B-11 `repair=` flag.  Every call site states the root it is confined
    # to, and a future one cannot inherit a bare mkdir by omission.
    _ensure_private_chain(private_root, path.parent)
    if path.exists() or path.is_symlink():
        # 29.6.  This is the write-once refusal a second attempt at the same
        # run meets.  The ruling is that a retry is a NEW RUN ID, never an
        # operator deletion of this record: the record is the deliverable of
        # the attempt that failed, on a lane whose whole point is evidence.
        # So the refusal names the record it is protecting instead of leaving
        # the operator to guess that deleting it would clear the way.  The
        # name is the record's file name, which carries no key material, no
        # credential and no path outside the private root.
        raise FileExistsError(
            "durable host record already exists and is retained as the "
            "evidence of the attempt that wrote it; retry under a new run "
            f"id rather than deleting {path.name}"
        )
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


def _replace_json(
    path: Path, value: Mapping[str, object], *, private_root: Path
) -> None:
    _ensure_private_chain(private_root, path.parent)
    temporary = path.parent / (
        "." + path.name + "." + secrets.token_hex(8) + ".tmp"
    )
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), indent=2
    ) + "\n"
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
    )
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


def _record_or_verify(
    path: Path, value: Mapping[str, object], *, private_root: Path
) -> None:
    if path.exists() or path.is_symlink():
        if _read_json(path) != dict(value):
            # 29.6, the same rule one step further in: a history record that
            # already disagrees is not re-written and not deleted.  Naming it
            # is what tells the operator which record to read.
            raise ValueError(f"durable Modal history changed at {path.name}")
        return
    _atomic_json(path, value, private_root=private_root)

def _opaque_ref(kind: str, *values: str) -> str:
    payload = "\0".join(_text(value, f"{kind} identity component") for value in values)
    return f"modal-{kind}-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class ModalProviderAuthorityV1:
    """Pure host authority over one already-deployed Modal provider."""

    config: ModalHostConfigV1
    training: ModalTrainingPolicyV1
    state: ModalProviderStateV1
    journal: ModalDeploymentJournalV1

    def __post_init__(self) -> None:
        if type(self.config) is not ModalHostConfigV1:
            raise TypeError("authority config must be an exact ModalHostConfigV1")
        if type(self.training) is not ModalTrainingPolicyV1:
            raise TypeError("authority training policy must be exact")
        if type(self.state) is not ModalProviderStateV1:
            raise TypeError("authority provider state must be exact")
        if type(self.journal) is not ModalDeploymentJournalV1:
            raise TypeError("authority deployment journal must be exact")
        if self.training is not self.config.training:
            raise ValueError("authority training policy identity changed")
        if ModalHostConfigV1.from_mapping(self.config.to_dict()) != self.config:
            raise ValueError("Modal host config is not canonical")
        if ModalTrainingPolicyV1.from_mapping(
            self.training.to_dict()
        ) != self.training:
            raise ValueError("Modal training policy is not canonical")
        if ModalProviderStateV1.from_mapping(
            self.state.to_dict()
        ) != self.state:
            raise ValueError("Modal provider state is not canonical")
        if ModalDeploymentJournalV1.from_mapping(
            self.journal.to_dict()
        ) != self.journal:
            raise ValueError("Modal deployment journal is not canonical")

        profile = self.state.profile
        binding = self.state.binding
        selection = self.state.selection
        runtime = ModalRuntimeLockV1.packaged()
        expected_secrets = (
            ModalSecretProfileV1(
                self.config.runtime_secret_name,
                self.config.runtime_secret_keys,
            ),
        )
        if (
            self.training.provider_ref != "modal"
            or self.training.profile_ref != self.config.profile
            or profile.profile != self.config.profile
            or self.journal.config_digest != self.config.digest
            or self.journal.deployment_ref != selection.deployment_ref
            or self.journal.function_name != selection.function_name
            or profile.app_name != "synaptic-training-v1"
            or profile.deployment_ref != selection.deployment_ref
            or profile.function_name != selection.function_name
            or profile.runtime_lock_ref
            != "engine://tuner/execution/providers/modal/modal-runtime-v1.lock.json"
            or profile.control_volume_ref != self.config.control_volume_name
            or profile.artifact_volume_ref != self.config.artifact_volume_name
            or profile.secrets != expected_secrets
            or binding.environment_ref != self.config.environment_name
            or selection.environment_ref != self.config.environment_name
            or binding.sdk_version != EXACT_MODAL_SDK_VERSION
            or selection.sdk_version != EXACT_MODAL_SDK_VERSION
            or selection.runtime_environment != self.config.runtime_environment
            or selection.timeout_seconds != self.config.timeout_seconds
            or self.state.control_volume_id != _opaque_ref(
                "volume", binding.account_ref, binding.environment_ref,
                self.config.control_volume_name,
            )
            or self.state.artifact_volume_id != _opaque_ref(
                "volume", binding.account_ref, binding.environment_ref,
                self.config.artifact_volume_name,
            )
        ):
            raise ValueError("Modal provider authority identities disagree")
        runtime.validate_selection(selection)

    @classmethod
    def load(
        cls, context: ProjectContext, config_path: Path | None = None,
    ) -> "ModalProviderAuthorityV1":
        config = ModalHostConfigV1.load(context, config_path)
        state = ModalProviderStateV1.load(context)
        journal = ModalDeploymentJournalV1.from_mapping(
            _read_json(context.state_root / "modal" / "deployment-journal.json")
        )
        return cls(config, config.training, state, journal)



class ExplicitModalHostSession:
    """One explicit Modal 1.5.4 client bound to host state and environment."""

    def __init__(self, *, sdk: object, client: object, config: ModalHostConfigV1, binding: ModalClientBinding):
        if getattr(sdk, "__version__", None) != EXACT_MODAL_SDK_VERSION:
            raise ValueError("Modal SDK must be exactly 1.5.4")
        self.sdk = sdk
        self.client = client
        self.config = config
        self.binding = binding
        function_call = getattr(sdk, "FunctionCall", None)
        from_id = getattr(function_call, "from_id", None)
        if function_call is None or not callable(from_id):
            raise ValueError("Modal FunctionCall restoration is unavailable")
        self._function_call_type = function_call
        self._function_call_from_id_owner = getattr(from_id, "__self__", None)
        self._function_call_from_id_function = getattr(from_id, "__func__", from_id)

    def _restore_callback_is_current(self) -> bool:
        try:
            function_call = getattr(self.sdk, "FunctionCall")
            callback = getattr(function_call, "from_id")
            return (
                function_call is self._function_call_type
                and getattr(callback, "__self__", None)
                is self._function_call_from_id_owner
                and getattr(callback, "__func__", callback)
                is self._function_call_from_id_function
            )
        except BaseException:
            return False

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

    def restore_function_call(self, provider_job_ref: str):
        """Restore an exact durable call reference without observing its result."""
        reference = _text(provider_job_ref, "provider job reference")
        sdk = self.sdk
        client = self.client
        function_call = self._function_call_type
        callback = getattr(function_call, "from_id")
        restored = None
        failed = False
        try:
            if not self._restore_callback_is_current():
                raise ValueError
            restored = callback(reference, client=client)
            if (
                self.sdk is not sdk
                or self.client is not client
                or not self._restore_callback_is_current()
                or object.__getattribute__(restored, "object_id") != reference
            ):
                raise ValueError
        except BaseException:
            failed = True
        if failed:
            raise ValueError("Modal function call could not be restored") from None
        return restored

    def _deploy_journal(
        self,
        *,
        journal: ModalDeploymentJournalV1,
        worker_authenticator: FileHmacAuthenticator,
    ) -> ModalProviderStateV1:
        # R1: the container channel is bound to the WORKER ref only.  The
        # guard is repeated here so the binding cannot drift if a future
        # caller reaches this method without passing the public entry point.
        _require_worker_authenticator(worker_authenticator)
        runtime_lock = ModalRuntimeLockV1.packaged()
        remote_auth = EnvironmentHmacAuthenticator(
            environment_key="SYNAPTIC_EVIDENCE_MAC_KEY",
            key_ref=worker_authenticator.key_ref,
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
            "volume", self.binding.account_ref, self.binding.environment_ref,
            self.config.control_volume_name,
        )
        artifact_ref = _opaque_ref(
            "volume", self.binding.account_ref, self.binding.environment_ref,
            self.config.artifact_volume_name,
        )
        return ModalProviderStateV1(
            profile, self.binding, selection, control_ref, artifact_ref,
        )

    def deploy(
        self,
        *,
        context: ProjectContext,
        authenticator: FileHmacAuthenticator,
        hf_token: str,
        adopt_empty: bool = False,
    ) -> ModalProviderStateV1:
        # R1: `authenticator` is the WORKER key.  Refused at the entry, before
        # any Modal resource exists, per section 29.3 ruling (1).
        _require_worker_authenticator(authenticator)
        if type(adopt_empty) is not bool:
            raise TypeError("adopt_empty must be an exact boolean")
        private_root = _private_storage_root(context)
        state_path = context.state_root / "modal" / "provider-state.json"
        journal_path = context.state_root / "modal" / "deployment-journal.json"
        if state_path.exists() or state_path.is_symlink():
            # 29.6, the outermost of the three write-once refusals and the one
            # an operator meets first.  The same rule: the record is kept and
            # the retry is a new run id.  A redeploy over a live state file is
            # not a retry at all, so this one names what to read instead of
            # what to delete.
            raise FileExistsError(
                "Modal provider is already deployed for this host; read "
                f"{state_path.name} rather than removing it"
            )
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
            _atomic_json(
                journal_path, journal.to_dict(), private_root=private_root
            )

        authenticator.initialize()
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
        state = self._deploy_journal(
            journal=journal, worker_authenticator=authenticator
        )
        _atomic_json(state_path, state.to_dict(), private_root=private_root)
        return state

    def _validate_upgrade_source(
        self,
        state_value: Mapping[str, object],
        journal_value: Mapping[str, object],
    ) -> ModalDeploymentSelectionV1:
        root = _closed(
            state_value,
            {"schema_version", "profile", "binding", "selection", "volumes"},
            "Modal provider state",
        )
        if root["schema_version"] != "synaptic-modal-provider-state/v1":
            raise ValueError("unsupported Modal provider state schema")
        profile = ModalProviderProfileV1.from_mapping(root["profile"])
        binding_value = _closed(
            root["binding"],
            {
                "account_ref", "workspace_ref", "environment_ref",
                "client_ref", "sdk_version",
            },
            "Modal binding",
        )
        binding = ModalClientBinding(**binding_value)
        selection = ModalDeploymentSelectionV1.from_dict(root["selection"])
        volumes = _closed(
            root["volumes"],
            {"control_volume_id", "artifact_volume_id"},
            "Modal volumes",
        )
        journal = ModalDeploymentJournalV1.from_mapping(journal_value)
        expected_secrets = (
            ModalSecretProfileV1(
                self.config.runtime_secret_name,
                self.config.runtime_secret_keys,
            ),
        )
        if (
            journal.config_digest != self.config.digest
            or journal.deployment_ref != selection.deployment_ref
            or journal.function_name != selection.function_name
            or binding != self.binding
            or profile.profile != self.config.profile
            or profile.app_name != "synaptic-training-v1"
            or profile.function_name != selection.function_name
            or profile.deployment_ref != selection.deployment_ref
            or profile.control_volume_ref != self.config.control_volume_name
            or profile.artifact_volume_ref != self.config.artifact_volume_name
            or profile.secrets != expected_secrets
            or selection.account_ref != binding.account_ref
            or selection.workspace_ref != binding.workspace_ref
            or selection.environment_ref != binding.environment_ref
            or selection.client_ref != binding.client_ref
            or selection.runtime_environment != self.config.runtime_environment
            or selection.timeout_seconds != self.config.timeout_seconds
            or selection.secret_requirements_digest
            != profile.secret_requirements_digest
            or volumes["control_volume_id"] != _opaque_ref(
                "volume", binding.account_ref, binding.environment_ref,
                self.config.control_volume_name,
            )
            or volumes["artifact_volume_id"] != _opaque_ref(
                "volume", binding.account_ref, binding.environment_ref,
                self.config.artifact_volume_name,
            )
        ):
            raise ValueError("prior Modal provider state differs from host authority")
        return selection

    def upgrade(
        self,
        *,
        context: ProjectContext,
        authenticator: FileHmacAuthenticator,
    ) -> ModalProviderStateV1:
        """Replace provider code while preserving named durable resources."""
        # R1: `authenticator` is the WORKER key.  Refused at the entry, before
        # any Modal resource is replaced, per section 29.3 ruling (1).
        _require_worker_authenticator(authenticator)
        private_root = _private_storage_root(context)
        modal_root = context.state_root / "modal"
        state_path = modal_root / "provider-state.json"
        journal_path = modal_root / "deployment-journal.json"
        upgrade_path = modal_root / "upgrade-journal.json"
        if not state_path.is_file() or state_path.is_symlink():
            raise ValueError("Modal provider state is unavailable for upgrade")
        if not journal_path.is_file() or journal_path.is_symlink():
            raise ValueError("Modal deployment journal is unavailable for upgrade")

        if upgrade_path.exists() or upgrade_path.is_symlink():
            upgrade = ModalUpgradeJournalV1.from_mapping(
                _read_json(upgrade_path)
            )
            history_root = modal_root / "history" / upgrade.prior_deployment_ref
            prior_state_value = _read_json(history_root / "provider-state.json")
            prior_journal_value = _read_json(
                history_root / "deployment-journal.json"
            )
            prior = self._validate_upgrade_source(
                prior_state_value, prior_journal_value
            )
        else:
            prior_state_value = _read_json(state_path)
            prior_journal_value = _read_json(journal_path)
            prior = self._validate_upgrade_source(
                prior_state_value, prior_journal_value
            )
            upgrade = ModalUpgradeJournalV1.create(
                self.config, prior_deployment_ref=prior.deployment_ref
            )
            _atomic_json(
                upgrade_path, upgrade.to_dict(), private_root=private_root
            )
            history_root = modal_root / "history" / prior.deployment_ref
            _record_or_verify(
                history_root / "provider-state.json", prior_state_value,
                private_root=private_root,
            )
            _record_or_verify(
                history_root / "deployment-journal.json", prior_journal_value,
                private_root=private_root,
            )

        if (
            upgrade.config_digest != self.config.digest
            or upgrade.prior_deployment_ref != prior.deployment_ref
        ):
            raise ValueError("Modal upgrade journal differs from host authority")
        current_value = _read_json(state_path)
        current_selection = ModalDeploymentSelectionV1.from_dict(
            _closed(
                current_value,
                {"schema_version", "profile", "binding", "selection", "volumes"},
                "Modal provider state",
            )["selection"]
        )
        replacement = upgrade.replacement
        if current_selection.deployment_ref == prior.deployment_ref:
            if current_value != prior_state_value:
                raise ValueError("prior Modal provider state changed during upgrade")
            control = self._optional_volume(self.config.control_volume_name)
            artifact = self._optional_volume(self.config.artifact_volume_name)
            runtime_secret = self._optional_secret()
            if control is None or artifact is None or runtime_secret is None:
                raise ValueError("Modal upgrade requires every named resource")
            authenticator.initialize()
            state = self._deploy_journal(
                journal=replacement, worker_authenticator=authenticator
            )
            _replace_json(
                journal_path, replacement.to_dict(), private_root=private_root
            )
            _replace_json(
                state_path, state.to_dict(), private_root=private_root
            )
        elif current_selection.deployment_ref == replacement.deployment_ref:
            state = ModalProviderStateV1.from_mapping(current_value)
            if _read_json(journal_path) != replacement.to_dict():
                raise ValueError("completed Modal upgrade journal changed")
        else:
            raise ValueError("Modal provider state is outside the upgrade journal")

        completed_path = (
            modal_root / "history" / replacement.deployment_ref
            / "upgrade-journal.json"
        )
        if completed_path.exists() or completed_path.is_symlink():
            _record_or_verify(
                completed_path, upgrade.to_dict(), private_root=private_root
            )
            upgrade_path.unlink()
        else:
            # SEC-F2: the fourth bare mkdir on this lane.  The rename writes
            # a durable record into the same subtree, so its parent chain is
            # built and validated the same way as the writers' above.
            _ensure_private_chain(private_root, completed_path.parent)
            os.replace(upgrade_path, completed_path)
        return state
