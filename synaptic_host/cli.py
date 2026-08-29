"""Cold, provider-neutral training-run command ingress."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import stat
import sys
import threading
import unicodedata
import weakref
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


_INGRESS_SCHEMA = "synaptic-training-run-ingress/v1"
_RESULT_SCHEMA = "synaptic-training-run-command-result/v1"
_DESTINATION = "provider-staging"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_COMPONENT = re.compile(r"^[^\\/?#%\x00-\x1f\x7f]+$")
_ENGINE_CONTRACT_CACHE: tuple[Path, object, dict[str, object], object] | None = None


class TrainingRunCommandStatusV1(str, Enum):
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class TrainingRunCommandCodeV1(str, Enum):
    COMMAND_INVALID = "COMMAND_INVALID"
    PROVIDER_INVALID = "PROVIDER_INVALID"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    CONFIG_REF_INVALID = "CONFIG_REF_INVALID"
    CONFIG_UNAVAILABLE = "CONFIG_UNAVAILABLE"
    INPUT_INVALID = "INPUT_INVALID"
    DESTINATION_INVALID = "DESTINATION_INVALID"
    BOOTSTRAP_UNAVAILABLE = "BOOTSTRAP_UNAVAILABLE"
    SUBMISSION_UNAVAILABLE = "SUBMISSION_UNAVAILABLE"
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
        if self.destination_ref != _DESTINATION:
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
class TrainingRunCommandResultV1:
    schema_version: str
    status: TrainingRunCommandStatusV1
    provider_ref: str | None
    config_ref: str | None
    destination_ref: str | None
    input_digest: str | None
    error_code: TrainingRunCommandCodeV1

    def __post_init__(self) -> None:
        if self.schema_version != _RESULT_SCHEMA:
            raise ValueError("command result schema is invalid")
        if type(self.status) is not TrainingRunCommandStatusV1:
            raise TypeError("command result status is invalid")
        if type(self.error_code) is not TrainingRunCommandCodeV1:
            raise TypeError("command result error code is invalid")
        unavailable = self.error_code in {
            TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE,
            TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE,
            TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE,
            TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE,
            TrainingRunCommandCodeV1.INTERNAL_FAILURE,
        }
        expected_status = (
            TrainingRunCommandStatusV1.UNAVAILABLE if unavailable
            else TrainingRunCommandStatusV1.REJECTED
        )
        if self.status is not expected_status:
            raise ValueError("command result status and code disagree")
        identities = (self.provider_ref, self.config_ref, self.destination_ref)
        if any(
            value is not None and (
                type(value) is not str or not value or len(value.encode("utf-8")) > 512
            )
            for value in identities
        ):
            raise ValueError("command result references are invalid")
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
        if self.input_digest is not None and _DIGEST.fullmatch(self.input_digest) is None:
            raise ValueError("command result input digest is invalid")
        present = (
            self.provider_ref is not None,
            self.config_ref is not None,
            self.destination_ref is not None,
            self.input_digest is not None,
        )
        allowed = {
            TrainingRunCommandCodeV1.COMMAND_INVALID: ((False, False, False, False),),
            TrainingRunCommandCodeV1.PROVIDER_INVALID: ((False, False, False, False),),
            TrainingRunCommandCodeV1.DESTINATION_INVALID: ((True, False, False, False),),
            TrainingRunCommandCodeV1.CONFIG_REF_INVALID: ((True, False, True, False),),
            TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE: ((True, True, True, False),),
            TrainingRunCommandCodeV1.INPUT_INVALID: ((True, True, True, False),),
            TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE: (
                (True, True, True, False),
                (True, True, True, True),
            ),
            TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE: ((True, True, True, True),),
            TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE: ((True, True, True, True),),
            TrainingRunCommandCodeV1.INTERNAL_FAILURE: ((False, False, False, False),),
        }
        if present not in allowed[self.error_code]:
            raise ValueError("command result fields and code disagree")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "provider_ref": self.provider_ref,
            "config_ref": self.config_ref,
            "destination_ref": self.destination_ref,
            "input_digest": self.input_digest,
            "error_code": self.error_code.value,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )


def _failure(
    code: TrainingRunCommandCodeV1, *, provider_ref: str | None = None,
    config_ref: str | None = None, destination_ref: str | None = None,
    input_digest: str | None = None,
) -> TrainingRunCommandResultV1:
    unavailable = code in {
        TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE,
        TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE,
        TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE,
        TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE,
        TrainingRunCommandCodeV1.INTERNAL_FAILURE,
    }
    return TrainingRunCommandResultV1(
        _RESULT_SCHEMA,
        TrainingRunCommandStatusV1.UNAVAILABLE if unavailable
        else TrainingRunCommandStatusV1.REJECTED,
        provider_ref, config_ref, destination_ref, input_digest, code,
    )


def _install_ingress_provenance_v1():
    lock = threading.RLock()
    registry: dict[int, tuple[object, ...]] = {}

    def issue(
        provider_ref: str, config_ref: str, destination_ref: str,
        training_input: object, input_digest: str, source_sha256: str,
        contract_identity_digest: str, envelope_digest: str, bundle: object,
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
            identity_digest,
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
            reference, anchor, baseline, training_input, bundle, input_type, identity_digest = record
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
            return baseline

    return issue, authenticate


_issue_training_run_ingress_v1, _authenticate_training_run_ingress_v1 = (
    _install_ingress_provenance_v1()
)


def bootstrap_unavailable_result_v1(
    ingress: TrainingRunIngressV1,
) -> TrainingRunCommandResultV1:
    authenticated = _authenticate_training_run_ingress_v1(ingress)
    if authenticated is None:
        return _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)
    provider_ref, config_ref, destination_ref, input_digest, *_unused = authenticated
    return _failure(
        TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE,
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


def _load_training_input(
    source: bytes, engine_root: Path
) -> tuple[object, str, str] | TrainingRunCommandCodeV1:
    global _ENGINE_CONTRACT_CACHE
    try:
        document = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return TrainingRunCommandCodeV1.INPUT_INVALID
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
            if current_modules.keys() != cached_modules.keys() or any(
                current_modules[name] is not value
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
        return TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE
    try:
        training_input = bundle.parse_json(document)
        if type(training_input) is not bundle.input_type:
            return TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE
        input_digest = training_input.input_digest()
        if type(input_digest) is not str or _DIGEST.fullmatch(input_digest) is None:
            return TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE
        return training_input, input_digest, identity.identity_digest
    except BaseException as error:
        if (
            type(error) is loader_module.TrainingInputContractErrorV1
            and object.__getattribute__(error, "code")
            is loader_module.TrainingInputContractCodeV1.INPUT_INVALID
        ):
            return TrainingRunCommandCodeV1.INPUT_INVALID
        return TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE


def _prepare_training_run_ingress_v1(
    argv: list[str], *, project_root: Path, engine_root: Path,
) -> TrainingRunIngressV1 | TrainingRunCommandResultV1:
    parsed = _parse(argv)
    if parsed is None:
        return _failure(TrainingRunCommandCodeV1.COMMAND_INVALID)
    provider, config_ref, destination = parsed
    if provider not in {"modal", "docker"}:
        return _failure(TrainingRunCommandCodeV1.PROVIDER_INVALID)
    if destination != _DESTINATION:
        return _failure(TrainingRunCommandCodeV1.DESTINATION_INVALID, provider_ref=provider)
    components = _config_components(config_ref)
    if components is None:
        return _failure(
            TrainingRunCommandCodeV1.CONFIG_REF_INVALID,
            provider_ref=provider, destination_ref=destination,
        )
    loaded = _read_config(project_root, components)
    if loaded is None:
        return _failure(
            TrainingRunCommandCodeV1.CONFIG_UNAVAILABLE,
            provider_ref=provider, config_ref=config_ref, destination_ref=destination,
        )
    source, source_sha256 = loaded
    parsed_input = _load_training_input(source, engine_root)
    if type(parsed_input) is TrainingRunCommandCodeV1:
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
            TrainingRunCommandCodeV1.BOOTSTRAP_UNAVAILABLE,
            provider_ref=provider, config_ref=config_ref,
            destination_ref=destination, input_digest=input_digest,
        )
    return _issue_training_run_ingress_v1(
        provider, config_ref, destination, training_input, input_digest,
        source_sha256, contract_identity_digest, envelope_digest,
        _ENGINE_CONTRACT_CACHE[3],
    )


def prepare_training_run_ingress_v1(
    argv: list[str], *, project_root: Path, engine_root: Path,
) -> TrainingRunIngressV1 | TrainingRunCommandResultV1:
    try:
        return _prepare_training_run_ingress_v1(
            argv, project_root=project_root, engine_root=engine_root
        )
    except BaseException:
        return _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)


def dispatch_validated_training_run_v1(
    ingress: TrainingRunIngressV1,
) -> TrainingRunCommandResultV1:
    authenticated = _authenticate_training_run_ingress_v1(ingress)
    if authenticated is None:
        return _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)
    try:
        provider_ref, config_ref, destination_ref, input_digest, *_unused = authenticated
        code = (
            TrainingRunCommandCodeV1.PROVIDER_UNAVAILABLE
            if provider_ref == "docker"
            else TrainingRunCommandCodeV1.SUBMISSION_UNAVAILABLE
        )
        return _failure(
            code, provider_ref=provider_ref, config_ref=config_ref,
            destination_ref=destination_ref, input_digest=input_digest,
        )
    except BaseException:
        return _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)


def emit_training_run_result_v1(result: TrainingRunCommandResultV1) -> int:
    if type(result) is not TrainingRunCommandResultV1:
        result = _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)
    try:
        rebuilt = TrainingRunCommandResultV1(
            result.schema_version, result.status, result.provider_ref,
            result.config_ref, result.destination_ref, result.input_digest,
            result.error_code,
        )
        if rebuilt != result:
            raise ValueError
        line = rebuilt.canonical_json()
    except BaseException:
        result = _failure(TrainingRunCommandCodeV1.INTERNAL_FAILURE)
        line = result.canonical_json()
    sys.stdout.write(line + "\n")
    if result.status is TrainingRunCommandStatusV1.REJECTED:
        return 2
    return 4


__all__ = [
    "TrainingRunCommandCodeV1", "TrainingRunCommandResultV1",
    "TrainingRunCommandStatusV1", "TrainingRunIngressV1",
    "dispatch_validated_training_run_v1", "emit_training_run_result_v1",
    "prepare_training_run_ingress_v1",
]
