import json
from pathlib import Path

import pytest

from synaptic_host.docker_provider import DockerProviderProfileV1
from synaptic_host.docker_v1.model import canonical_wsl_path_v1


ROOT = Path(__file__).resolve().parents[2]


def test_checked_in_docker_profile_binds_windows_host_and_inventory_policy():
    profile = DockerProviderProfileV1.load(project_root=ROOT)
    assert profile.docker_policy_ref == "docker-desktop-windows-v1"
    assert profile.wsl_distro == "docker-desktop"
    assert profile.drive_mount_root == "/mnt/host"
    assert profile.inventory_root_ref
    assert profile.cache_admission is True
    assert profile.to_dict()["docker_host"] == {
        "policy_ref": profile.docker_policy_ref,
        "wsl_distro": profile.wsl_distro,
        "drive_mount_root": profile.drive_mount_root,
    }


def test_old_docker_policy_shape_fails_closed():
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    host = document.pop("docker_host")
    document["docker_policy_ref"] = host["policy_ref"]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)


@pytest.mark.parametrize("field", ("policy_ref", "wsl_distro", "drive_mount_root"))
def test_docker_host_policy_fields_are_required(field):
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    del document["docker_host"][field]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)


def _profile_document_with_root(value):
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    document["docker_host"]["drive_mount_root"] = value
    return document


@pytest.mark.parametrize("value", ("/mnt/host", "/mnt"))
def test_drive_mount_root_admits_both_measured_candidates(value):
    profile = DockerProviderProfileV1.from_mapping(_profile_document_with_root(value))
    assert profile.drive_mount_root == value


# One corpus, three properties. The profile-layer rule is a restatement of
# `canonical_wsl_path_v1` for the root alone, so it must never be LOOSER: a root
# the path contract refuses has to fail while the profile loads, not late as
# PATH_INVALID once staging has already created a stage directory.
_ROOT_CORPUS = (
    # admitted: the two measured candidates and ordinary shapes
    "/mnt/host", "/mnt", "/mnt/host/deep/er", "/a",
    # refused: the eleven shape cases
    "/mnt/host/", "mnt/host", "/mnt//host", "/mnt/./host", "/mnt/../host",
    "\\mnt\\host", "/mnt\\host", "/", "", "/mnt/hóst", "/mnt/ho\x01st",
    # refused: further control and separator cases
    "//mnt/host", "/mnt/host/.", "/mnt/host/..", "/mnt/host\x00",
    "/mnt/host\n", "/mnt/host\x7f",
    # the two bounds, on each side
    "/" + "x" * 240,                      # 240-byte component, admitted
    "/" + "x" * 241,                      # 241-byte component, refused
    "/" + "/".join(["a"] * 128),          # 128 parts, admitted
    "/" + "/".join(["a"] * 129),          # 129 parts, refused
)


def _profile_admits(value):
    try:
        DockerProviderProfileV1.from_mapping(_profile_document_with_root(value))
    except ValueError:
        return False
    return True


def _contract_admits(value):
    try:
        canonical_wsl_path_v1(value)
    except BaseException:
        return False
    return True


@pytest.mark.parametrize("value", _ROOT_CORPUS, ids=repr)
def test_profile_root_rule_is_never_looser_than_the_path_contract(value):
    """The implication that matters: admitted here implies contract-canonical.

    Equivalently, every value the contract refuses is refused at the profile
    layer with a ValueError. The converse is allowed -- being stricter is safe.
    """
    if _profile_admits(value):
        assert _contract_admits(value), (
            "profile layer admitted a root the path contract refuses"
        )
    if not _contract_admits(value):
        with pytest.raises(ValueError):
            DockerProviderProfileV1.from_mapping(_profile_document_with_root(value))


def test_profile_root_rule_admits_exactly_the_expected_corpus_members():
    # Pins the direction of every row, so a rule that refused everything (which
    # would satisfy the implication above vacuously) fails here.
    admitted = tuple(value for value in _ROOT_CORPUS if _profile_admits(value))
    assert admitted == (
        "/mnt/host", "/mnt", "/mnt/host/deep/er", "/a", "/" + "x" * 240,
        "/" + "/".join(["a"] * 128),
    )


@pytest.mark.parametrize("value", ("/mnt/host", "/mnt", "/mnt/host/deep/er", "/a"))
def test_admitted_roots_stay_canonical_once_a_drive_and_leaf_extend_them(value):
    # The realistic roots survive composition. This is NOT guaranteed at the
    # part bound: a 128-part root is contract-canonical on its own, and the
    # composed path that appends a drive and a stage relative path is not.
    # See the handoff; the composed value is re-checked at
    # DockerWSLPathRequestV1 before any container exists.
    assert canonical_wsl_path_v1(value + "/f/x") == value + "/f/x"


def test_part_bound_root_is_admitted_but_does_not_survive_composition():
    boundary = "/" + "/".join(["a"] * 128)
    assert _profile_admits(boundary)
    assert _contract_admits(boundary)
    with pytest.raises(BaseException):
        canonical_wsl_path_v1(boundary + "/f/x")


@pytest.mark.parametrize(
    "value",
    (
        "/mnt/host/",     # trailing slash
        "mnt/host",       # not absolute
        "/mnt//host",     # empty component
        "/mnt/./host",    # dot component
        "/mnt/../host",   # parent component
        "\\mnt\\host",    # Windows separators
        "/mnt\\host",     # embedded backslash
        "/",              # bare root
        "",               # empty
        "/mnt/ho\u0301st",  # decomposed combining acute, not NFC normalized
        "/mnt/ho\x01st",  # control character
    ),
)
def test_drive_mount_root_refuses_non_canonical_values(value):
    with pytest.raises(ValueError):
        DockerProviderProfileV1.from_mapping(_profile_document_with_root(value))


def test_drive_mount_root_refuses_a_distro_name_swapped_into_its_slot():
    # The field sits beside wsl_distro and carries the same type, so a swap of
    # the two values must not pass: only the mount root may be absolute.
    document = _profile_document_with_root("docker-desktop")
    document["docker_host"]["wsl_distro"] = "/mnt/host"
    with pytest.raises(ValueError):
        DockerProviderProfileV1.from_mapping(document)


def test_model_inventory_root_is_required():
    document = json.loads(
        (ROOT / "training/providers/docker.json").read_text(encoding="utf-8")
    )
    del document["model"]["inventory_root_ref"]
    with pytest.raises(ValueError, match="missing or unknown"):
        DockerProviderProfileV1.from_mapping(document)
