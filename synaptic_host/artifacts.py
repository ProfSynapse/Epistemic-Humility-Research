"""Host-owned final artifact destinations and publication durability."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from synaptic_tuner.api.v1 import (
    ArtifactPublicationReceipt,
    ProjectContext,
    PublishedArtifact,
    RunRef,
    VerifiedArtifactSource,
)


_SCHEMA = "synaptic-artifact-destinations/v1"
_RECEIPT_SCHEMA = "synaptic-artifact-publication/v1"
_FILENAMES = {
    "final_model": "final_model.tar",
    "tokenizer": "tokenizer.tar",
    "training_lineage": "training_lineage.json",
    "training_metrics": "training_metrics.json",
    "workload_record": "workload.json",
}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _ref(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) is None:
        raise ValueError(f"{name} is invalid")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


@dataclass(frozen=True, slots=True)
class LocalDestinationV1:
    root: str
    kind: str = "local"

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", _text(self.root, "local root"))


@dataclass(frozen=True, slots=True)
class HuggingFaceDestinationV1:
    repo_id: str
    repo_type: str
    revision: str
    path_prefix: str
    kind: str = "huggingface"

    def __post_init__(self) -> None:
        object.__setattr__(self, "repo_id", _text(self.repo_id, "repo_id"))
        if self.repo_type not in {"model", "dataset"}:
            raise ValueError("repo_type must be model or dataset")
        object.__setattr__(self, "revision", _ref(self.revision, "revision"))
        prefix = PurePosixPath(_text(self.path_prefix, "path_prefix"))
        if prefix.is_absolute() or any(part in {"", ".", ".."} for part in prefix.parts):
            raise ValueError("path_prefix must be a safe relative path")
        object.__setattr__(self, "path_prefix", prefix.as_posix())


DestinationV1 = LocalDestinationV1 | HuggingFaceDestinationV1


@dataclass(frozen=True, slots=True)
class ArtifactDestinationsV1:
    destinations: Mapping[str, DestinationV1]

    @classmethod
    def load(cls, context: ProjectContext) -> "ArtifactDestinationsV1":
        path = context.config_root / "artifacts.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {"schema_version", "destinations"} or value["schema_version"] != _SCHEMA:
            raise ValueError("artifact destination config is invalid")
        raw = value["destinations"]
        if not isinstance(raw, dict) or not raw:
            raise ValueError("at least one artifact destination is required")
        parsed: dict[str, DestinationV1] = {}
        for reference, spec in raw.items():
            reference = _ref(reference, "destination reference")
            if not isinstance(spec, dict) or "kind" not in spec:
                raise ValueError("artifact destination is invalid")
            if spec["kind"] == "local" and set(spec) == {"kind", "root"}:
                parsed[reference] = LocalDestinationV1(spec["root"])
            elif spec["kind"] == "huggingface" and set(spec) == {"kind", "repo_id", "repo_type", "revision", "path_prefix"}:
                parsed[reference] = HuggingFaceDestinationV1(
                    spec["repo_id"], spec["repo_type"], spec["revision"], spec["path_prefix"]
                )
            else:
                raise ValueError("artifact destination has unsupported fields")
        return cls(parsed)

    def resolve(self, reference: str) -> DestinationV1:
        try:
            return self.destinations[_ref(reference, "destination reference")]
        except KeyError:
            raise ValueError("artifact destination was not found") from None


def _receipt_bytes(receipt: ArtifactPublicationReceipt) -> bytes:
    return _canonical({
        "schema_version": _RECEIPT_SCHEMA,
        "project_ref": receipt.run.project_ref,
        "run_id": receipt.run.run_id,
        "plan_fingerprint": receipt.plan_fingerprint,
        "destination_ref": receipt.destination_ref,
        "artifacts": [
            {"kind": item.kind, "uri": item.uri, "sha256": item.sha256, "size": item.size}
            for item in receipt.artifacts
        ],
    })


def _parse_receipt(raw: bytes) -> ArtifactPublicationReceipt:
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {"schema_version", "project_ref", "run_id", "plan_fingerprint", "destination_ref", "artifacts"} or value["schema_version"] != _RECEIPT_SCHEMA:
        raise ValueError("artifact publication receipt is invalid")
    artifacts = value["artifacts"]
    if not isinstance(artifacts, list) or any(not isinstance(item, dict) or set(item) != {"kind", "uri", "sha256", "size"} for item in artifacts):
        raise ValueError("artifact publication receipt is invalid")
    return ArtifactPublicationReceipt(
        RunRef(value["run_id"], value["project_ref"]),
        value["plan_fingerprint"], value["destination_ref"],
        tuple(PublishedArtifact(item["kind"], item["uri"], item["sha256"], item["size"]) for item in artifacts),
    )


class HostArtifactPublisherV1:
    def __init__(
        self, *, context: ProjectContext, repository: object,
        destinations: ArtifactDestinationsV1,
        hf_token: Callable[[], str] | None = None,
        hf_api_factory: Callable[[str], object] | None = None,
        hf_operation_factory: Callable[[str, Path], object] | None = None,
    ) -> None:
        self.context = context
        self.repository = repository
        self.destinations = destinations
        self.hf_token = hf_token
        self.hf_api_factory = hf_api_factory
        self.hf_operation_factory = hf_operation_factory

    def publish(
        self, source: VerifiedArtifactSource, destination_ref: str
    ) -> ArtifactPublicationReceipt:
        if not isinstance(source, VerifiedArtifactSource):
            raise TypeError("verified artifact source is required")
        destination_ref = _ref(destination_ref, "destination reference")
        prior = self.repository.load_artifact_publication(
            source.run.project_ref, source.run.run_id, destination_ref
        )
        if prior is not None:
            receipt = _parse_receipt(prior)
            if receipt.plan_fingerprint != source.plan_fingerprint:
                raise ValueError("artifact publication plan collision")
            return receipt
        destination = self.destinations.resolve(destination_ref)
        if isinstance(destination, LocalDestinationV1):
            receipt = self._publish_local(source, destination_ref, destination)
        else:
            receipt = self._publish_huggingface(source, destination_ref, destination)
        raw = _receipt_bytes(receipt)
        stored = self.repository.commit_artifact_publication(
            source.run.project_ref, source.run.run_id, source.plan_fingerprint,
            destination_ref, raw
        )
        return _parse_receipt(stored)

    def _write_payloads(
        self, source: VerifiedArtifactSource, directory: Path
    ) -> dict[str, Path]:
        if {item.kind for item in source.artifacts} != set(_FILENAMES):
            raise ValueError("publication requires the exact verified artifact set")
        payloads: dict[str, Path] = {}
        for descriptor in source.artifacts:
            path = directory / _FILENAMES[descriptor.kind]
            digest = hashlib.sha256()
            size = 0
            with path.open("xb") as stream:
                for chunk in source.iter_bytes(
                    descriptor.kind, maximum=max(1, descriptor.size)
                ):
                    if not isinstance(chunk, bytes):
                        raise TypeError("artifact chunks must be bytes")
                    size += len(chunk)
                    if size > descriptor.size:
                        raise ValueError("verified artifact exceeds its descriptor")
                    digest.update(chunk)
                    stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            if size != descriptor.size or digest.hexdigest() != descriptor.sha256:
                raise ValueError("verified artifact changed during publication")
            payloads[descriptor.kind] = path
        return payloads

    def _local_root(self, value: str) -> Path:
        if value.startswith("project://"):
            relative = PurePosixPath(value.removeprefix("project://"))
            if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
                raise ValueError("project-local artifact root is invalid")
            return self.context.project_root.joinpath(*relative.parts).resolve(strict=False)
        path = Path(value)
        if not path.is_absolute():
            raise ValueError("external local artifact root must be absolute")
        return path.resolve(strict=False)

    def _publish_local(self, source, destination_ref, destination):
        root = self._local_root(destination.root)
        project = _ref(source.run.project_ref, "project_ref")
        run = _ref(source.run.run_id, "run_id")
        parent = root / project
        final = parent / run
        parent.mkdir(parents=True, exist_ok=True)
        artifacts = tuple(
            PublishedArtifact(
                descriptor.kind,
                "local://" + (final / _FILENAMES[descriptor.kind]).as_posix(),
                descriptor.sha256,
                descriptor.size,
            )
            for descriptor in source.artifacts
        )
        receipt = ArtifactPublicationReceipt(
            source.run, source.plan_fingerprint, destination_ref, artifacts
        )
        if final.exists():
            return self._verify_local(final, receipt)
        temporary = Path(tempfile.mkdtemp(prefix=f".{run}.", dir=parent))
        try:
            self._write_payloads(source, temporary)
            with (temporary / "publication.json").open("xb") as stream:
                stream.write(_receipt_bytes(receipt)); stream.flush(); os.fsync(stream.fileno())
            temporary.rename(final)
        except BaseException:
            if temporary.exists():
                shutil.rmtree(temporary)
            if final.exists():
                return self._verify_local(final, receipt)
            raise
        return self._verify_local(final, receipt)

    @staticmethod
    def _verify_local(final: Path, expected: ArtifactPublicationReceipt):
        if final.is_symlink() or not final.is_dir():
            raise ValueError("local artifact publication target changed")
        expected_names = {"publication.json", *(_FILENAMES[item.kind] for item in expected.artifacts)}
        if {item.name for item in final.iterdir()} != expected_names:
            raise ValueError("local artifact publication inventory changed")
        observed = _parse_receipt((final / "publication.json").read_bytes())
        if observed != expected:
            raise ValueError("local artifact publication receipt changed")
        for item in expected.artifacts:
            content = (final / _FILENAMES[item.kind]).read_bytes()
            if len(content) != item.size or hashlib.sha256(content).hexdigest() != item.sha256:
                raise ValueError("local artifact publication content changed")
        return observed

    def _publish_huggingface(self, source, destination_ref, destination):
        if self.hf_token is None:
            raise ValueError("Hugging Face token provider is unavailable")
        token = self.hf_token().strip()
        if not token:
            raise ValueError("Hugging Face token is unavailable")
        if self.hf_api_factory is None or self.hf_operation_factory is None:
            from huggingface_hub import CommitOperationAdd, HfApi
            api = HfApi(token=token)
            operation_factory = lambda path, local_path: CommitOperationAdd(
                path_in_repo=path, path_or_fileobj=local_path
            )
        else:
            api = self.hf_api_factory(token)
            operation_factory = self.hf_operation_factory
        base = PurePosixPath(destination.path_prefix) / source.run.project_ref / source.run.run_id
        paths = {kind: (base / filename).as_posix() for kind, filename in _FILENAMES.items()}
        spool_parent = self.context.project_root / ".synaptic" / "tmp"
        spool_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f"publish-{source.run.run_id}-", dir=spool_parent
        ) as temporary:
            payloads = self._write_payloads(source, Path(temporary))
            result = api.create_commit(
                repo_id=destination.repo_id,
                repo_type=destination.repo_type,
                revision=destination.revision,
                operations=[
                    operation_factory(paths[kind], payloads[kind])
                    for kind in sorted(payloads)
                ],
                commit_message=(
                    f"Publish verified training artifacts for {source.run.run_id}"
                ),
            )
        oid = _text(getattr(result, "oid", None), "Hugging Face commit oid")
        artifacts = tuple(
            PublishedArtifact(
                item.kind,
                f"hf://{destination.repo_type}/{destination.repo_id}@{oid}/{paths[item.kind]}",
                item.sha256, item.size,
            )
            for item in source.artifacts
        )
        return ArtifactPublicationReceipt(
            source.run, source.plan_fingerprint, destination_ref, artifacts
        )


__all__ = [
    "ArtifactDestinationsV1", "HostArtifactPublisherV1",
    "HuggingFaceDestinationV1", "LocalDestinationV1",
]
