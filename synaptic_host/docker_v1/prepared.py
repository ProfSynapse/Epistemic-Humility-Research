"""Prepared-only Docker mount binding for an immutable Host stage."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from tuner.execution.providers.docker_provider_v1.model import (
    DockerCommandBindingV1, DockerImageV1, DockerLabelsV1, DockerRuntimeV1,
    DockerWorkloadV1, labels_for,
)
from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_execution import DockerPreparedRunRequestV1
from synaptic_host.docker_staging import DockerStagingResultV1
from .control_contract import (
    DockerCreatePathBindingV1, authenticate_create_path_binding_v1,
)
from .model import (
    DockerWindowsPathV1, DockerWSLPathPurposeV1, DockerWSLPathRequestV1,
    ResolvedDockerMountsV1,
)

_STAGE_REF = re.compile(r"host-stage://([0-9a-f]{64})/(source|artifacts)\Z")
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _identity(path: Path, lstat) -> tuple[int, int, int, int]:
    metadata = lstat(path)
    attributes = getattr(metadata, "st_file_attributes", 0)
    if (
        not path.is_absolute() or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode) or attributes & _REPARSE
        or type(metadata.st_dev) is not int or type(metadata.st_ino) is not int
    ):
        raise ValueError("prepared Docker stage contains an untrusted directory")
    return (
        metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode),
        attributes & _REPARSE,
    )


def _wsl_path(path: Path, root: str) -> str:
    if (
        type(root) is not str or not root.startswith("/") or root.endswith("/")
        or "\\" in root
        or any(part in {"", ".", ".."} for part in root[1:].split("/"))
    ):
        raise ValueError("prepared Docker drive mount root is invalid")
    value, drive = path.as_posix(), path.drive
    if len(drive) != 2 or drive[1] != ":" or not value.startswith(drive + "/"):
        raise ValueError("prepared Docker stage requires a Windows drive path")
    relative = value[3:]
    if not relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise ValueError("prepared Docker stage path is invalid")
    return f"{root}/{drive[0].lower()}/{relative}"


class DockerPreparedMountAdapterV1:
    """Derive and authenticate mounts from one retained staging result."""

    def __init__(
        self, *, request: DockerPreparedRunRequestV1,
        binding: DockerCommandBindingV1, labels: DockerLabelsV1,
        distro: str, drive_mount_root: str, path_authority: object,
        lstat=os.lstat,
    ) -> None:
        if (
            type(request) is not DockerPreparedRunRequestV1
            or type(binding) is not DockerCommandBindingV1
            or type(labels) is not DockerLabelsV1
            or labels != labels_for(binding.identity)
            or binding.plan != request.prepared_plan
            or binding.command_bytes != request.preparation.submit_command_bytes
            or type(distro) is not str or not distro or distro.startswith("/")
            or type(drive_mount_root) is not str
            or not drive_mount_root.startswith("/")
            or drive_mount_root.endswith("/")
            or not callable(lstat)
            or not callable(getattr(path_authority, "issue", None))
            or not callable(getattr(path_authority, "authenticate", None))
        ):
            raise ValueError("prepared Docker mount adapter is invalid")
        staging = request.staging
        if type(staging) is not DockerStagingResultV1:
            raise TypeError("exact Docker staging result is required")
        source_match = _STAGE_REF.fullmatch(staging.projection.source_stage_ref)
        artifact_match = _STAGE_REF.fullmatch(staging.projection.artifact_stage_ref)
        source, artifacts = Path(staging.source_root), Path(staging.artifact_root)
        stage = source.parent
        if (
            source_match is None or artifact_match is None
            or source_match.group(1) != artifact_match.group(1)
            or source_match.group(2) != "source"
            or artifact_match.group(2) != "artifacts"
            or source.name != "source" or artifacts.name != "artifacts"
            or source.parent != artifacts.parent or stage.name != source_match.group(1)
            or stage.parent.name != "stages" or stage.parent.parent.name != "docker"
        ):
            raise ValueError("prepared Docker stage topology is invalid")
        chain = (stage.parent.parent, stage.parent, stage, source, artifacts)
        tokens = tuple((path, _identity(path, lstat)) for path in chain)
        if source.resolve(strict=True) != source or artifacts.resolve(strict=True) != artifacts:
            raise ValueError("prepared Docker stage roots are redirected")
        if tuple((path, _identity(path, lstat)) for path in chain) != tokens:
            raise ValueError("prepared Docker stage changed during derivation")
        self._request, self._binding, self._labels = request, binding, labels
        self._distro, self._path_authority = distro, path_authority
        self._drive_mount_root = drive_mount_root
        self._lstat, self._tokens = lstat, tokens
        self._source_wsl_path = _wsl_path(source, drive_mount_root)
        self._artifact_wsl_path = _wsl_path(artifacts, drive_mount_root)
        self._source_mapping_digest = self._mapping_digest(
            staging.projection.source_stage_ref, "prepared-source",
            self._source_wsl_path, tokens[-2][1],
            DockerWSLPathPurposeV1.SOURCE_READ,
        )
        self._artifact_mapping_digest = self._mapping_digest(
            staging.projection.artifact_stage_ref, "prepared-artifacts",
            self._artifact_wsl_path, tokens[-1][1],
            DockerWSLPathPurposeV1.ARTIFACT_WRITE,
        )

    def _mapping_digest(self, reference, mapping_ref, path, identity, purpose):
        return digest_v1({
            "declared_ref": reference, "distro": self._distro,
            "identity": list(identity), "mapping_ref": mapping_ref, "path": path,
            "purpose": purpose.value,
            "schema_version": "synaptic-host-prepared-stage-mapping/v1",
        })

    def _unchanged(self) -> None:
        if tuple(
            (path, _identity(path, self._lstat)) for path, _token in self._tokens
        ) != self._tokens:
            raise ValueError("prepared Docker stage identity changed")

    def resolve_create_mounts(
        self, *, labels, image, runtime, workload, source_ref, artifact_ref,
    ) -> ResolvedDockerMountsV1:
        self._unchanged()
        profile = self._request.prepared_plan.profile
        if (
            labels != self._labels
            or type(image) is not DockerImageV1 or image != profile.image
            or type(runtime) is not DockerRuntimeV1 or runtime != profile.runtime
            or type(workload) is not DockerWorkloadV1 or workload != profile.workload
            or source_ref != profile.roots.source_ref
            or artifact_ref != profile.roots.artifact_ref
            or source_ref != self._request.staging.projection.source_stage_ref
            or artifact_ref != self._request.staging.projection.artifact_stage_ref
        ):
            raise ValueError("prepared Docker mount inputs changed")
        projection = self._request.staging.projection
        body = {
            "artifact_mapping_digest": self._artifact_mapping_digest,
            "artifact_wsl_root": self._artifact_wsl_path,
            "bundle_binding_digest": projection.worker_projection_digest,
            "command_binding_digest": self._binding.binding_digest,
            "labels_digest": self._labels.digest,
            "mount_verification_digest": projection.source_manifest_digest,
            "schema_version": "synaptic-host-resolved-docker-mounts/v1",
            "source_mapping_digest": self._source_mapping_digest,
            "source_read_only": True,
            "source_wsl_private_path": self._source_wsl_path,
            "stage_record_digest": self._request.preparation.preparation_digest,
        }
        result = ResolvedDockerMountsV1(
            self._source_wsl_path, self._artifact_wsl_path,
            self._binding.binding_digest, self._labels.digest,
            self._request.preparation.preparation_digest,
            self._source_mapping_digest, self._artifact_mapping_digest,
            projection.worker_projection_digest, projection.source_manifest_digest,
            True, digest_v1(body),
        )
        self._unchanged()
        return result

    def bind(self, resolved, source_ref, artifact_ref):
        self._unchanged()
        if type(resolved) is not ResolvedDockerMountsV1:
            raise TypeError("exact resolved Docker mounts are required")
        source_request = DockerWSLPathRequestV1.build(
            mapping_ref="prepared-source",
            expected_mapping_digest=self._source_mapping_digest,
            expected_distro=self._distro,
            purpose=DockerWSLPathPurposeV1.SOURCE_READ,
            posix_path=self._source_wsl_path,
        )
        artifact_request = DockerWSLPathRequestV1.build(
            mapping_ref="prepared-artifacts",
            expected_mapping_digest=self._artifact_mapping_digest,
            expected_distro=self._distro,
            purpose=DockerWSLPathPurposeV1.ARTIFACT_WRITE,
            posix_path=self._artifact_wsl_path,
        )
        content = DockerCreatePathBindingV1.build(
            labels_digest=resolved.labels_digest, source_ref=source_ref,
            artifact_ref=artifact_ref,
            mount_resolution_digest=resolved.resolution_digest,
            source_storage_mapping_proof_digest=self._source_mapping_digest,
            artifact_storage_mapping_proof_digest=self._artifact_mapping_digest,
            source_mapping_pair_proof_digest=self._source_mapping_digest,
            artifact_mapping_pair_proof_digest=self._artifact_mapping_digest,
            source_request=source_request, artifact_request=artifact_request,
            source_read_only=True,
        )
        self._unchanged()
        result = authenticate_create_path_binding_v1(
            self._path_authority, self._path_authority.issue(content)
        )
        self._unchanged()
        return result

    def translate(self, request: DockerWSLPathRequestV1) -> DockerWindowsPathV1:
        self._unchanged()
        if type(request) is not DockerWSLPathRequestV1:
            raise TypeError("exact Docker WSL path request is required")
        expected = {
            "prepared-source": (
                self._source_mapping_digest, DockerWSLPathPurposeV1.SOURCE_READ,
                self._source_wsl_path,
            ),
            "prepared-artifacts": (
                self._artifact_mapping_digest,
                DockerWSLPathPurposeV1.ARTIFACT_WRITE,
                self._artifact_wsl_path,
            ),
        }.get(request.mapping_ref)
        if expected != (
            request.expected_mapping_digest, request.purpose, request.posix_path
        ) or request.expected_distro != self._distro:
            raise ValueError("prepared Docker path request changed")
        unc = "\\\\wsl.localhost\\" + self._distro + request.posix_path.replace("/", "\\")
        body = {
            "distro": self._distro, "mapping_digest": request.expected_mapping_digest,
            "mapping_ref": request.mapping_ref, "posix_path": request.posix_path,
            "purpose": request.purpose.value,
            "schema_version": "synaptic-host-docker-windows-path/v1",
            "unc_path": unc,
        }
        result = DockerWindowsPathV1(
            request.mapping_ref, request.expected_mapping_digest, request.purpose,
            self._distro, request.posix_path, unc, digest_v1(body),
        )
        self._unchanged()
        return result


__all__ = ["DockerPreparedMountAdapterV1"]
