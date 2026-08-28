from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest

from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.model import (
    BundleMemberCommandV1,
    BundleSealCommandV1,
)
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleSourceV1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RetainedRootBorrowRequestV1,
    RootAccessV1,
    digest_v1,
)

from local_io_v1.conftest import FakePosixFilesystemPortV1, _verified_ext4_root


@pytest.fixture
def bundle_ext4_root(request):
    try:
        configured = request.config.getoption("--b42-ext4-root")
    except ValueError:
        configured = None
    if configured is None:
        pytest.skip("pass --b42-ext4-root from the canonical WSL ext4 checkout")
    authorized = _verified_ext4_root(configured)
    created = Path(tempfile.mkdtemp(prefix="b42-bundle-", dir=authorized))
    try:
        yield created
    finally:
        shutil.rmtree(created)


class Authenticator:
    def __init__(self) -> None:
        self.permits = {}

    def binding(self, path: Path, ref: str) -> LocalRootBindingV1:
        absolute = path.absolute()
        permit_ref = "permit-" + ref
        canonical = {
            "access": RootAccessV1.READ_CREATE.value,
            "absolute_root": str(absolute),
            "authority_ref": "authority-bundle",
            "key_ref": "key-bundle",
            "permit_ref": permit_ref,
            "root_ref": ref,
        }
        permit = LocalRootPermitV1(
            permit_ref, ref, absolute, RootAccessV1.READ_CREATE,
            "authority-bundle", "key-bundle", digest_v1(canonical), "0" * 64,
        )
        self.permits[id(permit)] = permit
        return LocalRootBindingV1(
            ref, "project://" + ref, absolute, RootAccessV1.READ_CREATE,
            permit_ref, permit,
        )

    def authenticate(self, permit):
        return permit if self.permits.get(id(permit)) is permit else None


class SourceRegistry:
    def __init__(self) -> None:
        self.values = {}
        self.calls = []

    def resolve(self, source_ref: str):
        self.calls.append(source_ref)
        return self.values[source_ref]


def borrow(filesystem, authority, purpose, access):
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, purpose, access
    )
    capability = filesystem.borrow_root(authority, request)
    root = filesystem.root_directory(capability, purpose=purpose)
    return capability, root


@pytest.fixture
def bundle_env():
    payloads = {"source-a": b"alpha", "source-b": b"beta-data"}
    port = FakePosixFilesystemPortV1()
    base = Path.cwd() / ".fake-metadata" / "bundle-io"
    data_path = base / "data"
    control_path = base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    for name, payload in payloads.items():
        port.add_file("dir-data", name, payload)
    authenticator = Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(
        authenticator.binding(data_path, "bundle-data"),
        authenticator.binding(control_path, "bundle-control"),
    )
    create_borrow, create_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
        RootAccessV1.READ_CREATE,
    )
    verify_borrow, verify_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
        RootAccessV1.READ_ONLY,
    )
    source_borrow, source_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_SOURCE_READ,
        RootAccessV1.READ_ONLY,
    )
    registry = SourceRegistry()
    for source_ref in payloads:
        registry.values[source_ref] = BundleSourceV1.build(
            source_ref, source_borrow, source_root, source_ref
        )
    access = BundleBorrowAccessV1.build(
        "opaque-destination", create_borrow, create_root,
        verify_borrow, verify_root,
    )
    members = tuple(
        BundleMemberCommandV1(
            f"logical/{index}", source_ref, len(payload),
            hashlib.sha256(payload).hexdigest(),
        )
        for index, (source_ref, payload) in enumerate(payloads.items())
    )
    command = BundleSealCommandV1.build(
        "opaque-profile", "source-seal", "opaque-destination", members
    )
    service = ImmutableSourceBundleV1(filesystem, registry)
    return port, filesystem, service, registry, command, access, authority, authenticator
