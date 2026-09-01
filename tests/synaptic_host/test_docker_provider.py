import json
from pathlib import Path

import pytest

from synaptic_host.docker_provider import DockerProviderProfileV1


ROOT = Path(__file__).resolve().parents[2]


def test_checked_in_docker_profile_binds_windows_host_and_inventory_policy():
    profile = DockerProviderProfileV1.load(project_root=ROOT)
    assert profile.docker_policy_ref == "docker-desktop-windows-v1"
    assert profile.wsl_distro == "docker-desktop"
    assert profile.inventory_root_ref
    assert profile.cache_admission is True
    assert profile.to_dict()["docker_host"] == {
        "policy_ref": profile.docker_policy_ref,
        "wsl_distro": profile.wsl_distro,
    }


def test_old_docker_policy_shape_fails_closed():
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    host = document.pop("docker_host")
    document["docker_policy_ref"] = host["policy_ref"]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)


@pytest.mark.parametrize("field", ("policy_ref", "wsl_distro"))
def test_docker_host_policy_fields_are_required(field):
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    del document["docker_host"][field]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)


def test_model_inventory_root_is_required():
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    del document["model"]["inventory_root_ref"]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)
