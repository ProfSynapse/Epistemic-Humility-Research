from dataclasses import replace

import pytest

from synaptic_host.docker_v1.model import (
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerSourceDeclarationV1,
)


def test_declaration_is_canonical_and_every_binding_changes_digest(source_env):
    _, declaration, _ = source_env
    rebuilt = DockerSourceDeclarationV1.build(
        source_ref=declaration.source_ref,
        source_digest=declaration.source_digest,
        effect_identity_digest=declaration.effect_identity_digest,
        prepared_plan_digest=declaration.prepared_plan_digest,
        profile_ref=declaration.profile_ref,
        purpose_ref=declaration.purpose_ref,
        destination_ref=declaration.destination_ref,
        root_authority_digest=declaration.root_authority_digest,
        bundle_access_digest=declaration.bundle_access_digest,
        members=declaration.members,
    )
    assert rebuilt == declaration
    for field, value in (
        ("source_ref", "other-source"),
        ("source_digest", "a" * 64),
        ("effect_identity_digest", "b" * 64),
        ("prepared_plan_digest", "c" * 64),
        ("profile_ref", "opaque/other"),
        ("purpose_ref", "other-purpose"),
        ("destination_ref", "other-destination"),
        ("root_authority_digest", "d" * 64),
        ("bundle_access_digest", "e" * 64),
    ):
        values = declaration.__dict__ if hasattr(declaration, "__dict__") else {
            name: getattr(declaration, name) for name in declaration.__slots__
        }
        values = dict(values)
        values[field] = value
        with pytest.raises(DockerHostSourceErrorV1) as caught:
            DockerSourceDeclarationV1(**values)
        assert caught.value.code is DockerHostSourceCodeV1.DECLARATION_CONFLICT


def test_declaration_rejects_mutated_digest(source_env):
    _, declaration, _ = source_env
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        replace(declaration, declaration_digest="f" * 64)
    assert caught.value.code is DockerHostSourceCodeV1.DECLARATION_CONFLICT
