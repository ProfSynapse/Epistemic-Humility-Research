from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

import synaptic_host.publication_authority as authority_module
from synaptic_host.publication_authority import create_publication_evidence_v1
from synaptic_host.security import FileHmacAuthenticator
from synaptic_tuner.api.v1 import ProjectContext, TrainingRunRef, VerifiedArtifact
from synaptic_tuner.api.v1.publication import (
    AuthenticatedDestinationV1,
    AuthenticatedVerifiedSourceV1,
)


ZERO = "0" * 64


def _context(tmp_path: Path) -> ProjectContext:
    project = tmp_path.resolve()
    return ProjectContext.host(
        engine_root=project / "engine",
        project_root=project,
        state_root=project / ".synaptic" / "state",
    )


def _destination(authority_ref: str, key_ref: str) -> AuthenticatedDestinationV1:
    return AuthenticatedDestinationV1(
        "synaptic-publication-destination/v1",
        "local-default",
        "Local artifacts",
        hashlib.sha256(b"config").hexdigest(),
        hashlib.sha256(b"policy").hexdigest(),
        1024,
        4096,
        authority_ref,
        key_ref,
        ZERO,
    )


def _source(authority_ref: str, key_ref: str) -> AuthenticatedVerifiedSourceV1:
    artifact = VerifiedArtifact("adapter", hashlib.sha256(b"x").hexdigest(), 1)
    return AuthenticatedVerifiedSourceV1(
        "synaptic-publication-verified-source/v1",
        TrainingRunRef("run-1", "project-1"),
        (artifact,),
        hashlib.sha256(b"verified").hexdigest(),
        authority_ref,
        key_ref,
        ZERO,
    )


def test_factory_creates_domain_separated_typed_publication_evidence(tmp_path: Path) -> None:
    verifier, destinations, sources = create_publication_evidence_v1(_context(tmp_path))
    assert verifier.authority_ref == destinations.authority_ref == sources.authority_ref
    assert verifier.key_ref == destinations.key_ref == sources.key_ref
    assert (tmp_path / ".synaptic/state/publication/evidence-hmac.key").is_file()

    destination = destinations.issue(_destination(destinations.authority_ref, destinations.key_ref))
    source = sources.issue(_source(sources.authority_ref, sources.key_ref))
    assert verifier.verify(
        "publication-destination/v1", destination.payload,
        destination.tag, destination.key_ref,
    )
    assert verifier.verify(
        "publication-verified-source/v1", source.payload,
        source.tag, source.key_ref,
    )
    assert not verifier.verify(
        "publication-verified-source/v1", destination.payload,
        destination.tag, destination.key_ref,
    )
    assert not verifier.verify(
        "publication-destination/v1", source.payload, source.tag, source.key_ref,
    )


@pytest.mark.parametrize("tag", ["", "A" * 64, "g" * 64, "0" * 63, "0" * 65])
def test_verifier_rejects_malformed_or_forged_tags(tmp_path: Path, tag: str) -> None:
    verifier, issuer, _ = create_publication_evidence_v1(_context(tmp_path))
    value = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    assert not verifier.verify(
        "publication-destination/v1", value.payload, tag, value.key_ref
    )


def test_issuers_reject_wrong_envelope_or_authority_binding(tmp_path: Path) -> None:
    _, destinations, sources = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises(TypeError):
        destinations.issue(object())
    with pytest.raises(TypeError):
        sources.issue(object())
    with pytest.raises(ValueError):
        destinations.issue(_destination("other-authority", destinations.key_ref))
    with pytest.raises(ValueError):
        sources.issue(_source(sources.authority_ref, "other-key"))


def test_repeated_factory_reuses_key_and_stable_evidence(tmp_path: Path) -> None:
    first = create_publication_evidence_v1(_context(tmp_path))
    first_value = first[1].issue(_destination(first[1].authority_ref, first[1].key_ref))
    second = create_publication_evidence_v1(_context(tmp_path))
    second_value = second[1].issue(_destination(second[1].authority_ref, second[1].key_ref))
    assert first_value == second_value
    assert second[0].verify(
        "publication-destination/v1", first_value.payload,
        first_value.tag, first_value.key_ref,
    )


def test_factory_rejects_non_project_owned_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    context = ProjectContext.host(
        engine_root=project / "engine",
        project_root=project,
        state_root=tmp_path / "external-state",
    )
    with pytest.raises(ValueError, match="project-owned"):
        create_publication_evidence_v1(context)


def test_public_verifier_has_no_generic_sign_surface(tmp_path: Path) -> None:
    verifier, _, _ = create_publication_evidence_v1(_context(tmp_path))
    assert not hasattr(verifier, "sign")
    assert not hasattr(verifier, "issue")


def test_destination_mutation_changes_tag_and_identity(tmp_path: Path) -> None:
    verifier, issuer, _ = create_publication_evidence_v1(_context(tmp_path))
    original = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    changed_unsigned = replace(original, display_name="Changed", tag=ZERO)
    changed = issuer.issue(changed_unsigned)
    assert changed.identity_digest != original.identity_digest
    assert changed.tag != original.tag
    assert not verifier.verify(
        "publication-destination/v1", changed.payload,
        original.tag, changed.key_ref,
    )


def test_key_path_or_key_content_substitution_invalidates_authority(tmp_path: Path) -> None:
    verifier, issuer, _ = create_publication_evidence_v1(_context(tmp_path))
    original = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    replacement = FileHmacAuthenticator(
        (tmp_path / "replacement.key").resolve(), key_ref=issuer.key_ref
    )
    replacement.initialize()
    issuer._kernel._authenticator.key_path = replacement.key_path
    assert not verifier.verify(
        "publication-destination/v1", original.payload,
        original.tag, original.key_ref,
    )
    with pytest.raises(ValueError, match="publication evidence request is invalid"):
        issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))


def test_coordinated_kernel_slots_or_view_kernel_substitution_remain_fenced(
    tmp_path: Path, monkeypatch,
) -> None:
    verifier, issuer, _ = create_publication_evidence_v1(_context(tmp_path / "first"))
    original = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    other_verifier, other_issuer, _ = create_publication_evidence_v1(_context(tmp_path / "other"))
    other_kernel = other_issuer._kernel
    kernel = issuer._kernel
    object.__setattr__(kernel, "_authenticator", other_kernel._authenticator)
    object.__setattr__(kernel, "_key_path", other_kernel._key_path)
    object.__setattr__(kernel, "_continuity_payload", other_kernel._continuity_payload)
    object.__setattr__(kernel, "_continuity_tag", other_kernel._continuity_tag)
    object.__setattr__(kernel, "_sign_identity", other_kernel._sign_identity)
    object.__setattr__(kernel, "_verify_identity", other_kernel._verify_identity)
    monkeypatch.setattr(authority_module, "_get_kernel_pin", lambda owner: None)
    assert not verifier.verify(
        "publication-destination/v1", original.payload,
        original.tag, original.key_ref,
    )

    object.__setattr__(issuer, "_kernel", other_kernel)
    with pytest.raises(ValueError, match="authority binding is invalid"):
        issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    assert other_verifier is not verifier
