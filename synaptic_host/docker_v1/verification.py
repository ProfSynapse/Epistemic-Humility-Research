from hashlib import sha256

from .control_contract import (
    DockerControlContractErrorV1,
    docker_owned_label_projections_v1,
    docker_owned_labels_projection_digest_v1,
)
from .model import DockerPlatformErrorV1


def docker_create_projection_matches_v1(
    labels, expected, environment, projection, container_ref, evidence,
):
    try:
        specification = expected.content.create_specification
        if (
            evidence.policy_digest
            != expected.content.intent.content.cli_policy_digest
            or projection.container_ref != container_ref
            or projection.container_name != labels.container_name
            or projection.image_digest != specification.image_digest
            or projection.owned_labels != docker_owned_label_projections_v1(labels)
            or docker_owned_labels_projection_digest_v1(labels)
            != specification.owned_labels_projection_digest
            or projection.network_mode != "none"
            or projection.nano_cpus != specification.nano_cpus
            or projection.memory_bytes != specification.memory_bytes
            or projection.device_requests_digest
            != specification.device_requests_digest
            or projection.argument_count != specification.argument_count
            or projection.arguments_digest != specification.arguments_digest
            or projection.working_directory_digest
            != specification.working_directory_digest
        ):
            return False
        observed_env = {
            (item.key_digest, item.value_digest)
            for item in projection.environment.entries
        }
        expected_env = {
            (item.key_digest, item.value_digest)
            for item in environment.content.supplied_entries
        }
        if not expected_env.issubset(observed_env) or len(projection.mounts) != 2:
            return False
        mounts = {item.destination_digest: item for item in projection.mounts}
        source_destination = sha256(b"/source").hexdigest()
        artifact_destination = sha256(b"/artifacts").hexdigest()
        if set(mounts) != {source_destination, artifact_destination}:
            return False
        source = mounts[source_destination]
        artifact = mounts[artifact_destination]
        return (
            source.mount_type == "bind"
            and source.source_digest == specification.source_unc_digest
            and source.read_write is False
            and artifact.mount_type == "bind"
            and artifact.source_digest == specification.artifact_unc_digest
            and artifact.read_write is True
        )
    except (
        DockerControlContractErrorV1, DockerPlatformErrorV1,
        AttributeError, TypeError, ValueError,
    ):
        return False


__all__: tuple[str, ...] = ()
