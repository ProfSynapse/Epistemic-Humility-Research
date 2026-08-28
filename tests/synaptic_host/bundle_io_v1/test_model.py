from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, replace

import pytest

from synaptic_host.bundle_io_v1.model import (
    MAX_BUNDLE_MEMBER_BYTES,
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleMemberCommandV1,
    BundleSealCommandV1,
    BundleMountVerificationV1,
)
from synaptic_host.bundle_io_v1.ports import BundleMountVerifyAccessV1


def member(name="a", source="source", payload=b"x"):
    return BundleMemberCommandV1(
        name, source, len(payload), hashlib.sha256(payload).hexdigest()
    )


def test_command_is_canonical_immutable_and_every_field_bound() -> None:
    command = BundleSealCommandV1.build("profile", "purpose", "destination", (member(),))
    assert replace(command) == command
    with pytest.raises(FrozenInstanceError):
        command.destination_ref = "other"
    for field, value in (
        ("profile_ref", "other"), ("purpose_ref", "other"),
        ("destination_ref", "other"), ("members", (member("b", "other"),)),
    ):
        with pytest.raises(BundleIOErrorV1) as caught:
            replace(command, **{field: value})
        assert caught.value.code is BundleIOCodeV1.COMMAND_INVALID


def test_command_rejects_order_duplicates_and_bounds() -> None:
    with pytest.raises(BundleIOErrorV1):
        BundleSealCommandV1.build(
            "profile", "purpose", "destination",
            (member("b", "b"), member("a", "a")),
        )
    with pytest.raises(BundleIOErrorV1):
        BundleSealCommandV1.build(
            "profile", "purpose", "destination",
            (member("a", "a"), member("a", "b")),
        )
    with pytest.raises(BundleIOErrorV1) as caught:
        BundleMemberCommandV1("a", "source", MAX_BUNDLE_MEMBER_BYTES + 1, "0" * 64)
    assert caught.value.code is BundleIOCodeV1.BOUND_EXCEEDED


def test_one_source_may_back_multiple_distinct_logical_entries() -> None:
    command = BundleSealCommandV1.build(
        "profile", "purpose", "destination",
        (member("a", "shared"), member("b", "shared")),
    )
    assert tuple(value.source_ref for value in command.members) == ("shared", "shared")


@pytest.mark.parametrize("name", ["../x", "/x", "x\\y", "x/./y", "x:ads"])
def test_logical_names_use_portable_canonical_validation(name) -> None:
    with pytest.raises(BundleIOErrorV1):
        member(name)


def test_mount_verification_is_canonical_immutable_and_every_field_bound(
    bundle_env,
) -> None:
    _, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    authenticated = service._binding_authority.issue(found.binding)
    verify_access = BundleMountVerifyAccessV1.build(
        command.destination_ref, access.verify_borrow, access.verify_root
    )
    verification = service.verify_mount(
        command, verify_access, authenticated
    )
    assert type(verification) is BundleMountVerificationV1
    assert replace(verification) == verification
    for field, value in (
        ("private_name", ".synaptic-bundle-" + "0" * 32),
        ("logical_entries", tuple(reversed(verification.logical_entries))),
        ("read_only", False),
        ("verification_digest", "0" * 64),
    ):
        with pytest.raises(BundleIOErrorV1) as caught:
            replace(verification, **{field: value})
        assert caught.value.code is BundleIOCodeV1.CONFLICT
