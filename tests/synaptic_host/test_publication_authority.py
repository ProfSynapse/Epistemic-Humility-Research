from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

import synaptic_host.publication_authority as authority_module
from synaptic_host.publication_authority import (
    PublicationEvidenceAuthorityV1,
    PublicationReceiptEvidenceIssuerV1,
    create_publication_evidence_v1,
)
from synaptic_host.security import FileHmacAuthenticator
from synaptic_tuner.api.v1 import ProjectContext, TrainingRunRef, VerifiedArtifact
from synaptic_tuner.api.v1.publication import (
    AuthenticatedDestinationInventoryV1,
    AuthenticatedDestinationV1,
    AuthenticatedLookupV1,
    AuthenticatedPublicationReceiptV1,
    AuthenticatedPublicationTombstoneV1,
    AuthenticatedVerifiedSourceV1,
    DestinationArtifactV1,
    DestinationInventoryV1,
    LookupOutcomeV1,
)


ZERO = "0" * 64
ROOT = Path(__file__).resolve().parents[2]


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


def _unsigned_terminal_evidence(authority_ref: str, key_ref: str):
    inventory = AuthenticatedDestinationInventoryV1(
        DestinationInventoryV1((DestinationArtifactV1("adapter", "adapter", "1" * 64, 7),)),
        "2" * 64, "3" * 64, "4" * 64, "5" * 64,
        "2026-08-31T12:00:00Z", authority_ref, key_ref, ZERO,
    )
    receipt = AuthenticatedPublicationReceiptV1(
        "synaptic-publication-receipt/v1", "2" * 64, "3" * 64,
        TrainingRunRef("run-1", "project-1"), "6" * 64, "local-default",
        "7" * 64, "4" * 64, "8" * 64, "5" * 64, inventory,
        "2026-08-31T12:00:01Z", authority_ref, key_ref, ZERO,
    )
    tombstone = AuthenticatedPublicationTombstoneV1(
        "synaptic-publication-tombstone/v1", "2" * 64, "4" * 64,
        "3" * 64, "8" * 64, "local-default", "7" * 64, "9" * 64,
        "a" * 64, authority_ref, key_ref, "5" * 64, "b" * 64,
        "c" * 64, "2026-08-31T12:00:02Z", "d" * 64,
        authority_ref, key_ref, ZERO,
    )
    lookup = AuthenticatedLookupV1(
        "synaptic-publication-lookup/v1", LookupOutcomeV1.INDETERMINATE,
        "2" * 64, "3" * 64, "7" * 64, "4" * 64, "5" * 64,
        "b" * 64, "c" * 64, "2026-08-31T12:00:03Z", None, None,
        authority_ref, key_ref, ZERO,
    )
    return inventory, receipt, lookup, tombstone


def test_factory_creates_domain_separated_typed_publication_evidence(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, destinations, sources = authority.verifier, authority.destinations, authority.verified_sources
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


def test_factory_issues_and_authenticates_all_closed_publication_evidence(
    tmp_path: Path,
) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    unsigned = _unsigned_terminal_evidence(
        authority.verifier.authority_ref, authority.verifier.key_ref
    )
    inventory = authority.destination_inventories.issue(unsigned[0])
    receipt = authority.receipts.issue(replace(unsigned[1], inventory=inventory))
    lookup = authority.lookups.issue(unsigned[2])
    tombstone = authority.tombstones.issue(unsigned[3])
    values = (
        ("publication-destination-inventory/v1", inventory),
        ("publication-receipt/v1", receipt),
        ("publication-lookup/v1", lookup),
        ("publication-tombstone/v1", tombstone),
    )
    for purpose, value in values:
        assert authority.verifier.verify(purpose, value.payload, value.tag, value.key_ref)
        assert value.tag != ZERO
    assert not hasattr(authority, "sign")
    assert not hasattr(authority.destination_inventories, "sign")
    assert not hasattr(authority.destination_inventories, "_issue")


def test_closed_issuers_reject_wrong_type_binding_and_substitution(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    inventory, receipt, lookup, tombstone = _unsigned_terminal_evidence(
        authority.verifier.authority_ref, authority.verifier.key_ref
    )
    with pytest.raises(TypeError, match="exact publication evidence"):
        authority.receipts.issue(inventory)
    with pytest.raises(ValueError, match="authority binding"):
        authority.tombstones.issue(replace(tombstone, authority_ref="other"))
    object.__setattr__(authority.lookups, "_kernel", object())
    with pytest.raises(ValueError, match="issuer integrity"):
        authority.lookups.issue(lookup)


def test_typed_issuer_leaves_reject_attribute_injection_and_cross_class_dispatch(
    tmp_path: Path,
) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    inventory, receipt, _, _ = _unsigned_terminal_evidence(
        authority.verifier.authority_ref, authority.verifier.key_ref
    )
    assert not hasattr(authority.receipts, "__dict__")
    for name, value in (
        ("issue", lambda envelope: envelope),
        ("_bound", lambda envelope: True),
        ("_finish", lambda *args: None),
        ("sign", lambda *args: ZERO),
    ):
        with pytest.raises((AttributeError, TypeError)):
            setattr(authority.receipts, name, value)
    with pytest.raises(ValueError, match="issuer integrity"):
        PublicationReceiptEvidenceIssuerV1.issue(
            authority.destination_inventories, receipt
        )
    with pytest.raises(TypeError, match="exact publication evidence"):
        PublicationReceiptEvidenceIssuerV1.issue(authority.receipts, inventory)


def test_fresh_process_seals_typed_issuer_base_before_leaf_pin_checks() -> None:
    code = r'''
from pathlib import Path
import tempfile
import synaptic_host.publication_authority as module
from synaptic_tuner.api.v1 import ProjectContext

base = module._TypedPublicationEvidenceIssuerV1
for name, value in (
    ("sign", lambda *args: "0" * 64),
    ("__getattribute__", lambda self, name: (lambda value: "SUBSTITUTED") if name == "issue" else object.__getattribute__(self, name)),
):
    try:
        setattr(base, name, value)
    except TypeError:
        pass
    else:
        raise SystemExit("base mutation was accepted")
with tempfile.TemporaryDirectory() as raw:
    root = Path(raw).resolve()
    authority = module.create_publication_evidence_v1(ProjectContext.host(
        engine_root=root / "engine", project_root=root,
        state_root=root / ".synaptic" / "state",
    ))
    if hasattr(authority.receipts, "sign"):
        raise SystemExit("injected sign surface is visible")
    try:
        authority.receipts.issue(None)
    except TypeError:
        pass
    else:
        raise SystemExit("substituted issue behavior executed")
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "synaptic-tuner")))
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_typed_issuer_rejects_hmac_valid_wrong_authority_envelope(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    _, receipt, _, _ = _unsigned_terminal_evidence(
        authority.verifier.authority_ref, authority.verifier.key_ref
    )
    wrong = replace(receipt, authority_ref="wrong-authority")
    wrong = replace(
        wrong,
        tag=authority.receipts._kernel.issue("publication-receipt/v1", wrong.payload),
    )
    assert authority.verifier.verify(
        "publication-receipt/v1", wrong.payload, wrong.tag, wrong.key_ref
    )
    with pytest.raises(ValueError, match="authority binding"):
        authority.receipts.issue(wrong)


def test_typed_issuer_uses_pinned_leaf_and_kernel_callables(
    tmp_path: Path, monkeypatch,
) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    _, receipt, _, _ = _unsigned_terminal_evidence(
        authority.verifier.authority_ref, authority.verifier.key_ref
    )
    with pytest.raises(TypeError, match="sealed publication evidence type"):
        setattr(PublicationReceiptEvidenceIssuerV1, "issue", lambda self, value: value)

    kernel_type = type(authority.receipts._kernel)
    monkeypatch.setattr(kernel_type, "issue", lambda self, purpose, payload: ZERO)
    with pytest.raises(ValueError, match="issuer integrity"):
        authority.receipts.issue(receipt)


def test_authority_aggregate_is_factory_only_and_rejects_member_substitution(
    tmp_path: Path,
) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises(TypeError, match="factory-created"):
        PublicationEvidenceAuthorityV1()
    with pytest.raises(TypeError, match="exact publication evidence authority members"):
        authority_module._create_publication_authority((object(),) * 7)
    assert not hasattr(authority, "_replace")
    assert not hasattr(authority, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        authority.receipts = authority.lookups
    with pytest.raises(TypeError, match="sealed publication evidence type"):
        setattr(PublicationEvidenceAuthorityV1, "receipts", property(lambda value: None))
    object.__setattr__(authority, "_seal", object())
    with pytest.raises(ValueError, match="authority integrity"):
        _ = authority.receipts


@pytest.mark.parametrize("tag", ["", "A" * 64, "g" * 64, "0" * 63, "0" * 65])
def test_verifier_rejects_malformed_or_forged_tags(tmp_path: Path, tag: str) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    value = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    assert not verifier.verify(
        "publication-destination/v1", value.payload, tag, value.key_ref
    )


def test_issuers_reject_wrong_envelope_or_authority_binding(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    destinations, sources = authority.destinations, authority.verified_sources
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
    first_value = first.destinations.issue(_destination(first.destinations.authority_ref, first.destinations.key_ref))
    second = create_publication_evidence_v1(_context(tmp_path))
    second_value = second.destinations.issue(_destination(second.destinations.authority_ref, second.destinations.key_ref))
    assert first_value == second_value
    assert second.verifier.verify(
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
    verifier = create_publication_evidence_v1(_context(tmp_path)).verifier
    assert not hasattr(verifier, "sign")
    assert not hasattr(verifier, "issue")


def test_destination_mutation_changes_tag_and_identity(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
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
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
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
    authority = create_publication_evidence_v1(_context(tmp_path / "first"))
    verifier, issuer = authority.verifier, authority.destinations
    original = issuer.issue(_destination(issuer.authority_ref, issuer.key_ref))
    other_authority = create_publication_evidence_v1(_context(tmp_path / "other"))
    other_verifier, other_issuer = other_authority.verifier, other_authority.destinations
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
