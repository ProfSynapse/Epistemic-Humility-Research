"""Cold, provider-neutral training-run command ingress."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import unicodedata
import weakref
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


_INGRESS_SCHEMA = "synaptic-training-run-ingress/v1"
_RESULT_SCHEMA = "synaptic-training-run-command-result/v2"
_DESTINATION = "provider-staging"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_DESTINATION_REF = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_COMPONENT = re.compile(r"^[^\\/?#%\x00-\x1f\x7f]+$")
_GIT_OBJECT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_MAX_GIT_BLOB_BYTES = 64 * 1024 * 1024
_ENGINE_CONTRACT_CACHE: tuple[Path, object, dict[str, object], object] | None = None


class TrainingRunCommandStatusV2(str, Enum):
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    SUBMITTED = "submitted"
    RECONCILE_REQUIRED = "reconcile_required"


class TrainingRunCommandCodeV2(str, Enum):
    COMMAND_INVALID = "COMMAND_INVALID"
    PROVIDER_INVALID = "PROVIDER_INVALID"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    CONFIG_REF_INVALID = "CONFIG_REF_INVALID"
    CONFIG_UNAVAILABLE = "CONFIG_UNAVAILABLE"
    INPUT_INVALID = "INPUT_INVALID"
    DESTINATION_INVALID = "DESTINATION_INVALID"
    CAPABILITY_UNSUPPORTED = "CAPABILITY_UNSUPPORTED"
    BOOTSTRAP_UNAVAILABLE = "BOOTSTRAP_UNAVAILABLE"
    CREDENTIALS_UNAVAILABLE = "CREDENTIALS_UNAVAILABLE"
    COMPOSITION_UNAVAILABLE = "COMPOSITION_UNAVAILABLE"
    RESOLUTION_UNAVAILABLE = "RESOLUTION_UNAVAILABLE"
    PREFLIGHT_REJECTED = "PREFLIGHT_REJECTED"
    AUTHORIZATION_UNAVAILABLE = "AUTHORIZATION_UNAVAILABLE"
    START_UNAVAILABLE = "START_UNAVAILABLE"
    SUBMITTED = "SUBMITTED"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


@dataclass(frozen=True, slots=True, init=False, weakref_slot=True)
class TrainingRunIngressV1:
    provider_ref: str
    config_ref: str
    destination_ref: str
    training_input: object
    input_digest: str
    source_sha256: str
    contract_identity_digest: str
    envelope_digest: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("training run ingress is factory-issued")

    def __post_init__(self) -> None:
        if type(self.provider_ref) is not str or type(self.config_ref) is not str:
            raise TypeError("ingress references are invalid")
        if type(self.destination_ref) is not str:
            raise TypeError("ingress destination is invalid")
        if (
            type(self.input_digest) is not str
            or type(self.source_sha256) is not str
            or type(self.contract_identity_digest) is not str
        ):
            raise TypeError("ingress digests are invalid")
        if type(self.envelope_digest) is not str:
            raise TypeError("ingress envelope digest is invalid")
        if self.provider_ref not in {"modal", "docker"}:
            raise ValueError("ingress provider is invalid")
        if (
            self.provider_ref == "modal" and self.destination_ref != _DESTINATION
        ) or (
            self.provider_ref == "docker"
            and (
                self.destination_ref == _DESTINATION
                or _DESTINATION_REF.fullmatch(self.destination_ref) is None
            )
        ):
            raise ValueError("ingress destination is invalid")
        if _DIGEST.fullmatch(self.input_digest) is None:
            raise ValueError("ingress input digest is invalid")
        if _DIGEST.fullmatch(self.source_sha256) is None:
            raise ValueError("ingress source digest is invalid")
        if _DIGEST.fullmatch(self.contract_identity_digest) is None:
            raise ValueError("ingress contract identity digest is invalid")
        if self.envelope_digest != self.recomputed_envelope_digest():
            raise ValueError("ingress envelope digest is invalid")

    def envelope_body(self) -> dict[str, object]:
        return {
            "schema_version": _INGRESS_SCHEMA,
            "provider_ref": self.provider_ref,
            "config_ref": self.config_ref,
            "destination_ref": self.destination_ref,
            "input_digest": self.input_digest,
            "source_sha256": self.source_sha256,
            "contract_identity_digest": self.contract_identity_digest,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.envelope_body(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")

    def recomputed_envelope_digest(self) -> str:
        return hashlib.sha256(
            _INGRESS_SCHEMA.encode("ascii") + b"\0" + self.canonical_bytes()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class _CommittedGitBlobV1:
    source_commit: str
    path: str
    git_object_id: str
    content: bytes
    sha256: str

    def __post_init__(self) -> None:
        if type(self.source_commit) is not str or _GIT_OBJECT.fullmatch(self.source_commit) is None:
            raise ValueError("committed blob source commit is invalid")
        if (
            type(self.path) is not str
            or self.path.startswith(("/", "\\"))
            or "\\" in self.path
            or any(part in {"", ".", ".."} for part in self.path.split("/"))
        ):
            raise ValueError("committed blob path is invalid")
        if type(self.git_object_id) is not str or _GIT_OBJECT.fullmatch(self.git_object_id) is None:
            raise ValueError("committed blob object identity is invalid")
        if type(self.content) is not bytes or not self.content:
            raise ValueError("committed blob content is invalid")
        if (
            type(self.sha256) is not str
            or _DIGEST.fullmatch(self.sha256) is None
            or hashlib.sha256(self.content).hexdigest() != self.sha256
        ):
            raise ValueError("committed blob digest is invalid")

    @property
    def size_bytes(self) -> int:
        return len(self.content)


@dataclass(frozen=True, slots=True)
class TrainingRunCommandResultV2:
    schema_version: str
    status: TrainingRunCommandStatusV2
    code: TrainingRunCommandCodeV2
    provider_ref: str | None
    config_ref: str | None
    destination_ref: str | None
    input_digest: str | None
    project_ref: str | None
    run_id: str | None
    plan_fingerprint: str | None
    effect_id: str | None
    provider_job_ref: str | None
    submitted_at: str | None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not str or self.schema_version != _RESULT_SCHEMA:
            raise ValueError("command result schema is invalid")
        if type(self.status) is not TrainingRunCommandStatusV2:
            raise TypeError("command result status is invalid")
        if type(self.code) is not TrainingRunCommandCodeV2:
            raise TypeError("command result code is invalid")
        rejected = {
            TrainingRunCommandCodeV2.COMMAND_INVALID,
            TrainingRunCommandCodeV2.PROVIDER_INVALID,
            TrainingRunCommandCodeV2.CONFIG_REF_INVALID,
            TrainingRunCommandCodeV2.INPUT_INVALID,
            TrainingRunCommandCodeV2.DESTINATION_INVALID,
            TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED,
            TrainingRunCommandCodeV2.PREFLIGHT_REJECTED,
        }
        unavailable = {
            TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE,
            TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE,
            TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
            TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE,
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
            TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE,
            TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE,
            TrainingRunCommandCodeV2.START_UNAVAILABLE,
            TrainingRunCommandCodeV2.INTERNAL_FAILURE,
        }
        expected_status = (
            TrainingRunCommandStatusV2.REJECTED if self.code in rejected
            else TrainingRunCommandStatusV2.UNAVAILABLE if self.code in unavailable
            else TrainingRunCommandStatusV2.SUBMITTED
            if self.code is TrainingRunCommandCodeV2.SUBMITTED
            else TrainingRunCommandStatusV2.RECONCILE_REQUIRED
        )
        if self.status is not expected_status:
            raise ValueError("command result status and code disagree")
        identities = (
            self.provider_ref, self.config_ref, self.destination_ref,
            self.project_ref, self.run_id, self.effect_id,
            self.provider_job_ref, self.submitted_at,
        )
        try:
            invalid_identity = any(
                value is not None and (
                    type(value) is not str or not value
                    or len(value.encode("utf-8")) > 512
                    or any(
                        unicodedata.category(character).startswith("C")
                        for character in value
                    )
                )
                for value in identities
            )
        except (TypeError, UnicodeError):
            invalid_identity = True
        if invalid_identity:
            raise ValueError("command result references are invalid") from None
        if self.provider_ref is None and any(
            value is not None for value in (self.config_ref, self.destination_ref, self.input_digest)
        ):
            raise ValueError("command result validation adjacency is invalid")
        if self.destination_ref is None and any(
            value is not None for value in (self.config_ref, self.input_digest)
        ):
            raise ValueError("command result validation adjacency is invalid")
        if self.config_ref is None and self.input_digest is not None:
            raise ValueError("command result validation adjacency is invalid")
        if self.input_digest is not None and (
            type(self.input_digest) is not str
            or _DIGEST.fullmatch(self.input_digest) is None
        ):
            raise ValueError("command result input digest is invalid")
        prefix = tuple(
            value is not None for value in (
                self.provider_ref, self.config_ref,
                self.destination_ref, self.input_digest,
            )
        )
        full = ((True, True, True, True),)
        allowed_prefixes = {
            TrainingRunCommandCodeV2.COMMAND_INVALID: ((False, False, False, False),),
            TrainingRunCommandCodeV2.PROVIDER_INVALID: ((False, False, False, False),),
            TrainingRunCommandCodeV2.DESTINATION_INVALID: ((True, False, False, False),),
            TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED: full,
            TrainingRunCommandCodeV2.CONFIG_REF_INVALID: ((True, False, True, False),),
            TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE: ((True, True, True, False),),
            TrainingRunCommandCodeV2.INPUT_INVALID: ((True, True, True, False),),
            TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE: (
                (True, True, True, False), (True, True, True, True),
            ),
            TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.PREFLIGHT_REJECTED: full,
            TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.START_UNAVAILABLE: full,
            TrainingRunCommandCodeV2.SUBMITTED: full,
            TrainingRunCommandCodeV2.RECONCILE_REQUIRED: full,
            TrainingRunCommandCodeV2.INTERNAL_FAILURE: ((False, False, False, False),),
        }
        if prefix not in allowed_prefixes[self.code]:
            raise ValueError("command result fields and code disagree")
        if self.plan_fingerprint is not None and (
            type(self.plan_fingerprint) is not str
            or _DIGEST.fullmatch(self.plan_fingerprint) is None
        ):
            raise ValueError("command result plan fingerprint is invalid")
        operation = tuple(
            value is not None for value in (
                self.project_ref, self.run_id, self.plan_fingerprint,
                self.effect_id, self.provider_job_ref, self.submitted_at,
            )
        )
        if self.code is TrainingRunCommandCodeV2.SUBMITTED:
            allowed_operation = {(True, True, True, True, True, True)}
        elif self.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED:
            allowed_operation = {
                (True, True, True, True, False, False),
                (True, True, True, True, True, False),
            }
        else:
            allowed_operation = {(False, False, False, False, False, False)}
        if operation not in allowed_operation:
            raise ValueError("command result operation fields and code disagree")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "code": self.code.value,
            "provider_ref": self.provider_ref,
            "config_ref": self.config_ref,
            "destination_ref": self.destination_ref,
            "input_digest": self.input_digest,
            "project_ref": self.project_ref,
            "run_id": self.run_id,
            "plan_fingerprint": self.plan_fingerprint,
            "effect_id": self.effect_id,
            "provider_job_ref": self.provider_job_ref,
            "submitted_at": self.submitted_at,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )


def _failure(
    code: TrainingRunCommandCodeV2, *, provider_ref: str | None = None,
    config_ref: str | None = None, destination_ref: str | None = None,
    input_digest: str | None = None,
) -> TrainingRunCommandResultV2:
    unavailable = code in {
        TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE,
        TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE,
        TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
        TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE,
        TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
        TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE,
        TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE,
        TrainingRunCommandCodeV2.START_UNAVAILABLE,
        TrainingRunCommandCodeV2.INTERNAL_FAILURE,
    }
    return TrainingRunCommandResultV2(
        _RESULT_SCHEMA,
        TrainingRunCommandStatusV2.UNAVAILABLE if unavailable
        else TrainingRunCommandStatusV2.REJECTED,
        code, provider_ref, config_ref, destination_ref, input_digest,
        None, None, None, None, None, None,
    )


def _install_ingress_provenance_v1():
    lock = threading.RLock()
    registry: dict[int, tuple[object, ...]] = {}

    def issue(
        provider_ref: str, config_ref: str, destination_ref: str,
        training_input: object, input_digest: str, source_sha256: str,
        contract_identity_digest: str, envelope_digest: str, bundle: object,
        project_root: Path | None = None, engine_root: Path | None = None,
        config_blob: _CommittedGitBlobV1 | None = None,
    ) -> TrainingRunIngressV1:
        value = object.__new__(TrainingRunIngressV1)
        assigned = (
            ("provider_ref", provider_ref), ("config_ref", config_ref),
            ("destination_ref", destination_ref), ("training_input", training_input),
            ("input_digest", input_digest), ("source_sha256", source_sha256),
            ("contract_identity_digest", contract_identity_digest),
            ("envelope_digest", envelope_digest),
        )
        for name, field_value in assigned:
            object.__setattr__(value, name, field_value)
        TrainingRunIngressV1.__post_init__(value)
        input_type = object.__getattribute__(bundle, "input_type")
        identity = object.__getattribute__(bundle, "identity")
        identity_digest = object.__getattribute__(identity, "identity_digest")
        if (
            type(training_input) is not input_type
            or identity_digest != contract_identity_digest
        ):
            raise ValueError("training run ingress authority is invalid")
        # C1 (section 29.5(f)).  This bound the committed source on the docker
        # arm only.  Both arms now read the committed blob, so both are held
        # to it: an ingress may not carry a source the released checkout does
        # not contain, whichever provider is about to execute it.
        if (
            not isinstance(project_root, Path)
            or not isinstance(engine_root, Path)
            or not project_root.is_absolute()
            or not engine_root.is_absolute()
            or type(config_blob) is not _CommittedGitBlobV1
            or config_blob.sha256 != source_sha256
        ):
            raise ValueError("ingress source binding is invalid")
        baseline = tuple(
            field_value for name, field_value in assigned if name != "training_input"
        )
        anchor = object()
        object_id = id(value)

        def remove(reference: weakref.ReferenceType[TrainingRunIngressV1]) -> None:
            with lock:
                current = registry.get(object_id)
                if (
                    current is not None
                    and current[0] is reference
                    and current[1] is anchor
                ):
                    del registry[object_id]

        reference = weakref.ref(value, remove)
        record = (
            reference, anchor, baseline, training_input, bundle, input_type,
            identity_digest, project_root, engine_root, config_blob,
        )
        with lock:
            registry[object_id] = record
        return value

    def authenticate(value: object) -> tuple[object, ...] | None:
        if type(value) is not TrainingRunIngressV1:
            return None
        object_id = id(value)
        with lock:
            record = registry.get(object_id)
            if record is None or record[0]() is not value:
                return None
        try:
            (
                reference, anchor, baseline, training_input, bundle, input_type,
                identity_digest, project_root, engine_root, config_blob,
            ) = record
            current = (
                value.provider_ref, value.config_ref, value.destination_ref,
                value.input_digest, value.source_sha256,
                value.contract_identity_digest, value.envelope_digest,
            )
            if (
                current != baseline
                or value.training_input is not training_input
                or type(training_input) is not input_type
                or value.contract_identity_digest != identity_digest
                or _ENGINE_CONTRACT_CACHE is None
                or _ENGINE_CONTRACT_CACHE[3] is not bundle
            ):
                return None
            TrainingRunIngressV1.__post_init__(value)
            observed_digest = training_input.input_digest()
            if type(observed_digest) is not str or observed_digest != value.input_digest:
                return None
        except BaseException:
            return None
        with lock:
            current_record = registry.get(object_id)
            if not (
                current_record is record
                and current_record[0] is reference
                and current_record[1] is anchor
                and reference() is value
            ):
                return None
            current = (
                value.provider_ref, value.config_ref, value.destination_ref,
                value.input_digest, value.source_sha256,
                value.contract_identity_digest, value.envelope_digest,
            )
            if current != baseline or value.training_input is not training_input:
                return None
            return baseline + (project_root, engine_root, config_blob)

    return issue, authenticate


_issue_training_run_ingress_v1, _authenticate_training_run_ingress_v1 = (
    _install_ingress_provenance_v1()
)


def bootstrap_unavailable_result_v2(
    ingress: TrainingRunIngressV1,
) -> TrainingRunCommandResultV2:
    authenticated = _authenticate_training_run_ingress_v1(ingress)
    if authenticated is None:
        return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
    provider_ref, config_ref, destination_ref, input_digest, *_unused = authenticated
    return _failure(
        TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
        provider_ref=provider_ref, config_ref=config_ref,
        destination_ref=destination_ref, input_digest=input_digest,
    )


def _parse(argv: list[str]) -> tuple[str, str, str] | None:
    if type(argv) is not list or any(type(item) is not str for item in argv):
        return None
    if len(argv) != 8 or argv[:2] != ["training", "run"]:
        return None
    options: dict[str, str] = {}
    for index in range(2, 8, 2):
        name, value = argv[index:index + 2]
        if name not in {"--provider", "--config", "--destination"}:
            return None
        if name in options or not value or value.startswith("--"):
            return None
        options[name] = value
    if frozenset(options) != {"--provider", "--config", "--destination"}:
        return None
    return options["--provider"], options["--config"], options["--destination"]


def _config_components(config_ref: str) -> tuple[str, ...] | None:
    if type(config_ref) is not str:
        return None
    try:
        encoded = config_ref.encode("utf-8")
    except UnicodeEncodeError:
        return None
    prefix = "project://training/"
    if not 1 <= len(encoded) <= 512 or not config_ref.startswith(prefix):
        return None
    components = tuple(config_ref[len(prefix):].split("/"))
    if not 1 <= len(components) <= 64:
        return None
    for component in components:
        try:
            size = len(component.encode("utf-8"))
        except UnicodeEncodeError:
            return None
        if (
            not 1 <= size <= 255 or component in {".", "..", "~"}
            or _COMPONENT.fullmatch(component) is None
            or re.match(r"^[A-Za-z]:", component) is not None
            or any(unicodedata.category(character) == "Cc" for character in component)
        ):
            return None
    return components


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def _read_config(
    project_root: Path, components: tuple[str, ...]
) -> tuple[bytes, str] | None:
    try:
        project = project_root.resolve(strict=True)
        declared_training = project / "training"
        declared_stat = declared_training.lstat()
        if stat.S_ISLNK(declared_stat.st_mode) or not stat.S_ISDIR(declared_stat.st_mode):
            return None
        training = declared_training.resolve(strict=True)
        training.relative_to(project)
        if training.is_symlink() or not training.is_dir():
            return None
        current = training
        for component in components[:-1]:
            current = current / component
            observed = current.lstat()
            if stat.S_ISLNK(observed.st_mode) or not stat.S_ISDIR(observed.st_mode):
                return None
            current.resolve(strict=True).relative_to(training)
        candidate = current / components[-1]
        candidate.resolve(strict=True).relative_to(training)
        before_path = candidate.lstat()
        if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
            return None
        if before_path.st_size > 65536:
            return None
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(candidate, flags)
        try:
            before_fd = os.fstat(descriptor)
            chunks = []
            size = 0
            while size < 65537:
                chunk = os.read(descriptor, 65537 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            payload = b"".join(chunks)
            after_fd = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after_path = candidate.lstat()
        identities = (
            _stat_identity(before_path), _stat_identity(before_fd),
            _stat_identity(after_fd), _stat_identity(after_path),
        )
        if any(identity != identities[0] for identity in identities[1:]):
            return None
        if len(payload) > 65536 or len(payload) != before_fd.st_size:
            return None
        return payload, hashlib.sha256(payload).hexdigest()
    except (OSError, RuntimeError, ValueError):
        return None


def _read_committed_git_blob_v1(
    project_root: Path, project_relative_path: str, *, maximum_bytes: int,
    expected_commit: str | None = None,
) -> _CommittedGitBlobV1:
    """Read one exact regular blob from the project's locked HEAD tree."""

    if (
        type(project_relative_path) is not str
        or project_relative_path.startswith(("/", "\\"))
        or "\\" in project_relative_path
        or any(part in {"", ".", ".."} for part in project_relative_path.split("/"))
        or type(maximum_bytes) is not int
        or not 1 <= maximum_bytes <= _MAX_GIT_BLOB_BYTES
        or (
            expected_commit is not None
            and (type(expected_commit) is not str or _GIT_OBJECT.fullmatch(expected_commit) is None)
        )
    ):
        raise ValueError("committed blob request is invalid")
    project = Path(project_root).resolve(strict=True)
    environment = {
        key: os.environ[key]
        for key in ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
        if key in os.environ
    }
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "Never", "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C", "LANG": "C",
    })

    def run(maximum_output_bytes: int, *arguments: str) -> bytes:
        process = None
        try:
            process = subprocess.Popen(
                ("git", "-C", str(project), *arguments),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=environment,
            )
            if process.stdout is None:
                raise ValueError
            chunks: list[bytes] = []
            state: dict[str, object] = {"size": 0, "failed": False}

            def drain() -> None:
                try:
                    while state["size"] <= maximum_output_bytes:
                        size = state["size"]
                        chunk = process.stdout.read(
                            min(65536, maximum_output_bytes + 1 - size)
                        )
                        if not chunk:
                            break
                        chunks.append(chunk)
                        state["size"] = size + len(chunk)
                        if state["size"] > maximum_output_bytes:
                            process.kill()
                            break
                except BaseException:
                    state["failed"] = True

            reader = threading.Thread(target=drain, daemon=True)
            reader.start()
            try:
                status = process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                reader.join(timeout=5)
                raise ValueError("committed blob process exceeded its time bound")
            reader.join(timeout=5)
            process.stdout.close()
            if reader.is_alive() or state["failed"] or status != 0:
                raise ValueError
            if state["size"] > maximum_output_bytes:
                raise ValueError("committed blob output exceeded its bound")
            return b"".join(chunks)
        except (OSError, subprocess.SubprocessError, ValueError):
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            raise ValueError("committed blob is unavailable") from None

    head = run(128, "rev-parse", "HEAD").decode("ascii", errors="strict").strip().lower()
    if _GIT_OBJECT.fullmatch(head) is None or (
        expected_commit is not None and head != expected_commit.lower()
    ):
        raise ValueError("project HEAD differs from the locked source commit")
    tree = run(4096, "ls-tree", "-z", head, "--", project_relative_path)
    records = tuple(record for record in tree.split(b"\0") if record)
    if len(records) != 1:
        raise ValueError("committed blob is not uniquely present")
    try:
        metadata, raw_path = records[0].split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        observed_path = raw_path.decode("utf-8")
    except (ValueError, UnicodeError):
        raise ValueError("committed blob tree entry is malformed") from None
    if (
        mode not in {"100644", "100755"}
        or kind != "blob"
        or observed_path != project_relative_path
        or _GIT_OBJECT.fullmatch(object_id) is None
    ):
        raise ValueError("committed tree entry is not an exact regular blob")
    content = run(maximum_bytes, "cat-file", "blob", object_id)
    if not content or len(content) > maximum_bytes:
        raise ValueError("committed blob size is invalid")
    return _CommittedGitBlobV1(
        head, project_relative_path, object_id, content,
        hashlib.sha256(content).hexdigest(),
    )


def _load_training_input(
    source: bytes, engine_root: Path
) -> tuple[object, str, str] | TrainingRunCommandCodeV2:
    global _ENGINE_CONTRACT_CACHE
    try:
        document = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return TrainingRunCommandCodeV2.INPUT_INVALID
    try:
        engine = engine_root.resolve(strict=True)
        expected_loader = engine / "synaptic_tuner/api/v1/training_input_loader.py"
        expected_input = engine / "synaptic_tuner/api/v1/training_input.py"
        source_identities: dict[Path, tuple[int, int, int, int]] = {}
        for expected in (expected_loader, expected_input):
            observed = expected.lstat()
            if stat.S_ISLNK(observed.st_mode) or not stat.S_ISREG(observed.st_mode):
                raise RuntimeError
            expected.resolve(strict=True).relative_to(engine)
            source_identities[expected] = _stat_identity(observed)
        if _ENGINE_CONTRACT_CACHE is None:
            if any(
                name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
                for name in sys.modules
            ):
                raise RuntimeError
            sys.path.insert(0, str(engine))
            try:
                loader_module = importlib.import_module(
                    "synaptic_tuner.api.v1.training_input_loader"
                )
            finally:
                if sys.path and sys.path[0] == str(engine):
                    del sys.path[0]
        else:
            cached_engine, loader_module, cached_modules, _bundle = (
                _ENGINE_CONTRACT_CACHE
            )
            if cached_engine != engine:
                raise RuntimeError
            current_modules = {
                name: value for name, value in sys.modules.items()
                if name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
            }
            if any(
                current_modules.get(name) is not value
                for name, value in cached_modules.items()
            ):
                raise RuntimeError
        input_module = sys.modules.get("synaptic_tuner.api.v1.training_input")
        if input_module is None:
            raise RuntimeError
        loader_spec = getattr(loader_module, "__spec__", None)
        input_spec = getattr(input_module, "__spec__", None)
        loader_origin = getattr(loader_spec, "origin", None)
        input_origin = getattr(input_spec, "origin", None)
        if type(loader_origin) is not str or type(input_origin) is not str:
            raise RuntimeError
        for origin, expected in (
            (loader_origin, expected_loader), (input_origin, expected_input)
        ):
            origin_path = Path(origin)
            observed = origin_path.lstat()
            if (
                origin_path.absolute() != expected.absolute()
                or origin_path.resolve(strict=True) != expected.resolve(strict=True)
                or stat.S_ISLNK(observed.st_mode)
                or not stat.S_ISREG(observed.st_mode)
                or _stat_identity(observed) != source_identities[expected]
            ):
                raise RuntimeError
        bundle_type = loader_module.LoadedTrainingInputContractV1
        identity_type = loader_module.TrainingInputContractIdentityV1
        load = loader_module.load_training_input_contract_v1
        bundle = load()
        if type(bundle) is not bundle_type or load() is not bundle:
            raise RuntimeError
        identity = bundle.identity
        if type(identity) is not identity_type:
            raise RuntimeError
        if (
            identity.schema_version != "synaptic-training-input-contract-identity/v1"
            or identity.contract_schema != "synaptic-training-input/v1"
            or identity.module_name != "synaptic_tuner.api.v1.training_input"
            or identity.type_name != "TrainingInputV1"
            or identity.parser_name != "from_json"
            or _DIGEST.fullmatch(identity.implementation_digest) is None
            or _DIGEST.fullmatch(identity.identity_digest) is None
            or bundle.input_type is not input_module.TrainingInputV1
        ):
            raise RuntimeError
        if _ENGINE_CONTRACT_CACHE is None:
            _ENGINE_CONTRACT_CACHE = (
                engine,
                loader_module,
                {
                    name: value for name, value in sys.modules.items()
                    if name == "synaptic_tuner" or name.startswith("synaptic_tuner.")
                },
                bundle,
            )
        elif _ENGINE_CONTRACT_CACHE[3] is not bundle:
            raise RuntimeError
    except BaseException:
        return TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
    try:
        training_input = bundle.parse_json(document)
        if type(training_input) is not bundle.input_type:
            return TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
        input_digest = training_input.input_digest()
        if type(input_digest) is not str or _DIGEST.fullmatch(input_digest) is None:
            return TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
        return training_input, input_digest, identity.identity_digest
    except BaseException as error:
        if (
            type(error) is loader_module.TrainingInputContractErrorV1
            and object.__getattribute__(error, "code")
            is loader_module.TrainingInputContractCodeV1.INPUT_INVALID
        ):
            return TrainingRunCommandCodeV2.INPUT_INVALID
        return TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE


def _prepare_training_run_ingress_v1(
    argv: list[str], *, project_root: Path, engine_root: Path,
) -> TrainingRunIngressV1 | TrainingRunCommandResultV2:
    parsed = _parse(argv)
    if parsed is None:
        return _failure(TrainingRunCommandCodeV2.COMMAND_INVALID)
    provider, config_ref, destination = parsed
    if provider not in {"modal", "docker"}:
        return _failure(TrainingRunCommandCodeV2.PROVIDER_INVALID)
    destination_invalid = (
        provider == "modal" and destination != _DESTINATION
    ) or (
        provider == "docker"
        and (
            destination == _DESTINATION
            or _DESTINATION_REF.fullmatch(destination) is None
        )
    )
    if destination_invalid:
        return _failure(TrainingRunCommandCodeV2.DESTINATION_INVALID, provider_ref=provider)
    components = _config_components(config_ref)
    if components is None:
        return _failure(
            TrainingRunCommandCodeV2.CONFIG_REF_INVALID,
            provider_ref=provider, destination_ref=destination,
        )
    try:
        project = Path(project_root).resolve(strict=True)
        engine = Path(engine_root).resolve(strict=True)
    except (OSError, RuntimeError):
        return _failure(
            TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
            provider_ref=provider, config_ref=config_ref, destination_ref=destination,
        )
    # C1 (section 29.5(f)).  Both arms read the COMMITTED blob.  The modal arm
    # used to fall through to a plain worktree read, which let a cloud job run
    # from whatever the operator had on disk -- a silent violation of the
    # standing ruling that execution uses only a released checkout, and the one
    # item on the 29.5 list whose failure is silent.  `provider` is already
    # constrained to the two providers above, so this is now unconditional.
    config_blob = None
    try:
        config_blob = _read_committed_git_blob_v1(
            project, "training/" + "/".join(components), maximum_bytes=65536,
        )
        loaded = (config_blob.content, config_blob.sha256)
    except ValueError:
        loaded = None
    if loaded is None:
        return _failure(
            TrainingRunCommandCodeV2.CONFIG_UNAVAILABLE,
            provider_ref=provider, config_ref=config_ref, destination_ref=destination,
        )
    source, source_sha256 = loaded
    parsed_input = _load_training_input(source, engine)
    if type(parsed_input) is TrainingRunCommandCodeV2:
        return _failure(
            parsed_input, provider_ref=provider,
            config_ref=config_ref, destination_ref=destination,
        )
    training_input, input_digest, contract_identity_digest = parsed_input
    body = {
        "schema_version": _INGRESS_SCHEMA, "provider_ref": provider,
        "config_ref": config_ref, "destination_ref": destination,
        "input_digest": input_digest, "source_sha256": source_sha256,
        "contract_identity_digest": contract_identity_digest,
    }
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    envelope_digest = hashlib.sha256(
        _INGRESS_SCHEMA.encode("ascii") + b"\0" + canonical
    ).hexdigest()
    if _ENGINE_CONTRACT_CACHE is None:
        return _failure(
            TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
            provider_ref=provider, config_ref=config_ref,
            destination_ref=destination, input_digest=input_digest,
        )
    return _issue_training_run_ingress_v1(
        provider, config_ref, destination, training_input, input_digest,
        source_sha256, contract_identity_digest, envelope_digest,
        _ENGINE_CONTRACT_CACHE[3], project, engine, config_blob,
    )


def prepare_training_run_ingress_v1(
    argv: list[str], *, project_root: Path, engine_root: Path,
) -> TrainingRunIngressV1 | TrainingRunCommandResultV2:
    try:
        return _prepare_training_run_ingress_v1(
            argv, project_root=project_root, engine_root=engine_root
        )
    except BaseException:
        return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)


def _establish_engine_import_root(engine_root: Path) -> None:
    """Put the bound engine root on `sys.path` once, appended, for good.

    B-15 (architecture section 24.3).  The contract loader at `:743-750`
    inserts this root and deletes it again, and provider `docker` then
    re-imports the engine at `docker_training.py:18` with nothing left to
    resolve it.  Runs 1 to 8 hid that because the operator's wrapper exported
    `PYTHONPATH`; the documented invocation does not, and run 9 died at cut 1
    on the top-level name `tuner`.

    APPENDED, never inserted at position 0, and that is not a style choice.
    The release root and the engine root both carry `docs/`, `scripts/` and
    `tests/`, and the engine's `Tools/` is the project's `tools/` on a
    case-insensitive Windows filesystem.  Appending makes the project win
    every collision, and nothing the engine needs is ambiguous.

    Adding a path entry imports nothing, so the `:738-742` refusal that no
    `synaptic_tuner` may be resident yet still holds, and if `:743` later
    inserts this same string at position 0 its `finally` deletes that
    position-0 copy while this appended entry survives.  `:743-750` needs no
    edit.
    """

    entry = str(engine_root)
    if entry not in sys.path:
        sys.path.append(entry)


def dispatch_validated_training_run_v1(
    ingress: TrainingRunIngressV1,
    *,
    isolated_child_authority: object | None,
    project_root: Path | None = None,
    engine_root: Path | None = None,
) -> TrainingRunCommandResultV2:
    authenticated = _authenticate_training_run_ingress_v1(ingress)
    if authenticated is None:
        return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
    try:
        (
            provider_ref, config_ref, destination_ref, input_digest,
            _source_sha256, _contract_digest, _ingress_digest,
            bound_project_root, bound_engine_root, _config_blob,
        ) = authenticated
        if provider_ref == "docker":
            if project_root is None or engine_root is None:
                return _failure(
                    TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                    provider_ref=provider_ref, config_ref=config_ref,
                    destination_ref=destination_ref, input_digest=input_digest,
                )
            try:
                supplied_project = Path(project_root).resolve(strict=True)
                supplied_engine = Path(engine_root).resolve(strict=True)
            except (OSError, RuntimeError):
                return _failure(
                    TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                    provider_ref=provider_ref, config_ref=config_ref,
                    destination_ref=destination_ref, input_digest=input_digest,
                )
            if supplied_project != bound_project_root or supplied_engine != bound_engine_root:
                return _failure(
                    TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                    provider_ref=provider_ref, config_ref=config_ref,
                    destination_ref=destination_ref, input_digest=input_digest,
                )
            _establish_engine_import_root(supplied_engine)
            docker_training = importlib.import_module("synaptic_host.docker_training")
            result = docker_training.execute_docker_training_admission_v1(
                ingress, project_root=supplied_project, engine_root=supplied_engine,
            )
            if (
                _authenticate_training_run_ingress_v1(ingress) != authenticated
                or type(result) is not TrainingRunCommandResultV2
            ):
                return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
            return result
        if isolated_child_authority is None:
            return _failure(
                TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                provider_ref=provider_ref, config_ref=config_ref,
                destination_ref=destination_ref, input_digest=input_digest,
            )
        launcher = importlib.import_module("synaptic_host.launcher")
        if _authenticate_training_run_ingress_v1(ingress) != authenticated:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        authenticate_authority = launcher._authenticate_isolated_child_authority_v1
        consume_authority = launcher._consume_isolated_child_authority_v1
        authority_authentication_failed = False
        try:
            authority_is_current = authenticate_authority(
                isolated_child_authority
            )
        except BaseException:
            authority_authentication_failed = True
            authority_is_current = False
        if _authenticate_training_run_ingress_v1(ingress) != authenticated:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if authority_authentication_failed:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if not authority_is_current:
            return _failure(
                TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                provider_ref=provider_ref, config_ref=config_ref,
                destination_ref=destination_ref, input_digest=input_digest,
            )
        consumption_failed = False
        try:
            isolated = consume_authority(
                isolated_child_authority,
                ingress_digest=ingress.envelope_digest,
                contract_identity_digest=ingress.contract_identity_digest,
            )
        except BaseException:
            consumption_failed = True
            isolated = None
        if _authenticate_training_run_ingress_v1(ingress) != authenticated:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if consumption_failed:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if isolated is None:
            return _failure(
                TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
                provider_ref=provider_ref, config_ref=config_ref,
                destination_ref=destination_ref, input_digest=input_digest,
            )
        if type(isolated) is not tuple or len(isolated) != 4:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        project_root, engine_root, token_id, token_secret = isolated
        if type(token_id) is not str or type(token_secret) is not str:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if not token_id or not token_secret:
            return _failure(
                TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE,
                provider_ref=provider_ref, config_ref=config_ref,
                destination_ref=destination_ref, input_digest=input_digest,
            )
        _establish_engine_import_root(engine_root)
        modal_training = importlib.import_module("synaptic_host.modal_training")
        executor = modal_training.execute_modal_training_run_v2
        if _authenticate_training_run_ingress_v1(ingress) != authenticated:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        result = executor(
            ingress, project_root=project_root, engine_root=engine_root,
            token_id=token_id, token_secret=token_secret,
        )
        if _authenticate_training_run_ingress_v1(ingress) != authenticated:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        if type(result) is not TrainingRunCommandResultV2:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        rebuilt = TrainingRunCommandResultV2(
            result.schema_version, result.status, result.code,
            result.provider_ref, result.config_ref, result.destination_ref,
            result.input_digest, result.project_ref, result.run_id,
            result.plan_fingerprint, result.effect_id,
            result.provider_job_ref, result.submitted_at,
        )
        if rebuilt != result:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        return rebuilt
    except BaseException as error:
        # B-15 (section 24.4).  This catch used to swallow the cause whole:
        # run 9 reported INTERNAL_FAILURE exit 4 with an all-null envelope and
        # an EMPTY stderr, so the operator learned that a run failed and
        # nothing about where.  The envelope does NOT widen -- it is the
        # contract the driver parses, it is rebuilt and equality-checked, and
        # six of the seven bare failure sites have no exception to name -- so
        # the cause goes to stderr on the mechanism 20.11 already ruled.
        #
        # Imported here rather than at module scope: this module deliberately
        # takes no relative import while it is cold.  Guarded because a
        # diagnostic that can fail the path it diagnoses is worse than none.
        try:
            from .cause_line import report_cause_line_v1

            report_cause_line_v1(
                error, TrainingRunCommandCodeV2.INTERNAL_FAILURE,
            )
        except BaseException:
            pass
        return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)


def emit_training_run_result_v2(result: TrainingRunCommandResultV2) -> int:
    if type(result) is not TrainingRunCommandResultV2:
        result = _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
    try:
        rebuilt = TrainingRunCommandResultV2(
            result.schema_version, result.status, result.code,
            result.provider_ref, result.config_ref, result.destination_ref,
            result.input_digest, result.project_ref, result.run_id,
            result.plan_fingerprint, result.effect_id,
            result.provider_job_ref, result.submitted_at,
        )
        if rebuilt != result:
            raise ValueError
        line = rebuilt.canonical_json()
    except BaseException:
        result = _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        line = result.canonical_json()
    sys.stdout.write(line + "\n")
    if result.status is TrainingRunCommandStatusV2.SUBMITTED:
        return 0
    if result.status is TrainingRunCommandStatusV2.REJECTED:
        return 2
    if result.status is TrainingRunCommandStatusV2.UNAVAILABLE:
        return 4
    return 8


__all__ = [
    "TrainingRunCommandCodeV2", "TrainingRunCommandResultV2",
    "TrainingRunCommandStatusV2", "TrainingRunIngressV1",
    "dispatch_validated_training_run_v1", "emit_training_run_result_v2",
    "prepare_training_run_ingress_v1",
    "bootstrap_unavailable_result_v2",
]
