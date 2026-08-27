from __future__ import annotations

import json
from pathlib import Path

import pytest

from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.model import (
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootPermitV1,
    RootAccessV1,
    digest_v1,
)


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _project_spec(ref: str = "opaque-a") -> dict[str, object]:
    return {
        "root_ref": ref,
        "location": "project://data/a",
        "access": "read_only",
        "permit_ref": "permit-" + ref,
    }


def _load(tmp_path: Path, value: object, *, issue: bool = True) -> StorageRegistryV1:
    registry = StorageRegistryV1.load(_write(tmp_path / "storage.json", value), project_root=tmp_path)
    if issue and isinstance(value, dict) and isinstance(value.get("roots"), list):
        for spec in value["roots"]:
            if isinstance(spec, dict) and isinstance(spec.get("root_ref"), str):
                registry.issue_root_permit(
                    spec["root_ref"], authority_ref="test-authority", key_ref="test-key",
                    proof_digest="0" * 64,
                )
    return registry


def test_two_opaque_project_profiles_are_metadata_only_and_sorted(tmp_path: Path) -> None:
    value = {
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {
                "root_ref": "opaque-z",
                "location": "project://missing/z",
                "access": "create_only",
                "permit_ref": "permit-opaque-z",
            },
            _project_spec("opaque-a"),
        ],
    }
    registry = _load(tmp_path, value)
    assert [item.root_ref for item in registry.list_roots()] == ["opaque-a", "opaque-z"]
    assert registry.resolve("opaque-z").absolute_root == tmp_path / "missing" / "z"
    assert not (tmp_path / "missing").exists()


def test_absolute_root_requires_exact_explicit_authorization(tmp_path: Path) -> None:
    external = (tmp_path / "external").absolute()
    value = {
        "schema_version": "synaptic-host-storage/v1",
        "roots": [{
            "root_ref": "opaque-external",
            "location": str(external),
            "access": "read_create",
            "permit_ref": "allow-a",
        }],
    }
    registry = _load(tmp_path, value, issue=False)
    with pytest.raises(LocalIOErrorV1) as caught:
        registry.resolve("opaque-external")
    assert caught.value.code is LocalIOCodeV1.ROOT_UNAUTHORIZED
    permit = registry.issue_root_permit(
        "opaque-external", authority_ref="authority-a", key_ref="key-a", proof_digest="0" * 64
    )
    assert registry.resolve("opaque-external").authorization_ref == "allow-a"
    assert registry.resolve("opaque-external").root_permit is permit
    assert registry.authenticate(permit) is permit
    copied = LocalRootPermitV1(
        permit.permit_ref, permit.root_ref, permit.absolute_root, permit.access,
        permit.authority_ref, permit.key_ref, permit.permit_digest, permit.proof_digest,
    )
    assert registry.authenticate(copied) is None
    with pytest.raises(LocalIOErrorV1) as caught:
        registry.issue_root_permit(
            "opaque-external", authority_ref="different", key_ref="key-a", proof_digest="0" * 64
        )
    assert caught.value.code is LocalIOCodeV1.ROOT_UNAUTHORIZED


def test_registry_authenticator_canonicalizes_reconstructed_equal_permit(tmp_path: Path) -> None:
    value = {"schema_version": "synaptic-host-storage/v1", "roots": [_project_spec()]}
    first = _load(tmp_path, value, issue=False)
    first_permit = first.issue_root_permit(
        "opaque-a", authority_ref="authority", key_ref="key", proof_digest="0" * 64
    )
    second = _load(tmp_path, value, issue=False)
    second_permit = second.issue_root_permit(
        "opaque-a", authority_ref="authority", key_ref="key", proof_digest="0" * 64
    )
    assert first_permit == second_permit and first_permit is not second_permit
    assert first.resolve("opaque-a").binding_digest == second.resolve("opaque-a").binding_digest
    assert first.authenticate(second_permit) is None

@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(extra=True),
        lambda value: value["roots"][0].update(token="secret"),
        lambda value: value["roots"][0].update(location="relative/path"),
        lambda value: value["roots"][0].update(location="project://a/../b"),
        lambda value: value["roots"][0].update(location="project://a\\b"),
        lambda value: value["roots"].append(dict(value["roots"][0])),
    ],
)
def test_invalid_or_credential_bearing_config_fails_closed(tmp_path: Path, mutate) -> None:
    value = {"schema_version": "synaptic-host-storage/v1", "roots": [_project_spec()]}
    mutate(value)
    with pytest.raises(LocalIOErrorV1) as caught:
        _load(tmp_path, value)
    assert caught.value.code in {LocalIOCodeV1.CONFIG_INVALID, LocalIOCodeV1.ROOT_UNAUTHORIZED}
    assert str(tmp_path) not in str(caught.value)


def test_duplicate_json_keys_and_unknown_root_are_closed(tmp_path: Path) -> None:
    path = tmp_path / "storage.json"
    path.write_text(
        '{"schema_version":"synaptic-host-storage/v1","schema_version":"x","roots":[]}',
        encoding="utf-8",
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        StorageRegistryV1.load(path, project_root=tmp_path)
    assert caught.value.code is LocalIOCodeV1.CONFIG_INVALID

    registry = _load(
        tmp_path,
        {"schema_version": "synaptic-host-storage/v1", "roots": [_project_spec()]},
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        registry.resolve("not-present")
    assert caught.value.code is LocalIOCodeV1.ROOT_UNKNOWN


def test_missing_and_oversized_config_errors_do_not_echo_paths(tmp_path: Path) -> None:
    missing = tmp_path / "SENTINEL-secret-config.json"
    with pytest.raises(LocalIOErrorV1) as caught:
        StorageRegistryV1.load(missing, project_root=tmp_path)
    assert caught.value.code is LocalIOCodeV1.CONFIG_IO_FAILED
    assert "SENTINEL" not in str(caught.value)
    large = tmp_path / "large.json"
    large.write_bytes(b"x" * 65_537)
    with pytest.raises(LocalIOErrorV1) as caught:
        StorageRegistryV1.load(large, project_root=tmp_path)
    assert caught.value.code is LocalIOCodeV1.CONFIG_INVALID
