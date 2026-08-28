from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from synaptic_host.local_io_v1.filesystem import RetainedRootBorrowPortV1
from synaptic_host.local_io_v1.model import (
    BorrowedDirectoryV1,
    BorrowPurposeV1,
    RetainedRootBorrowV1,
    RootAccessV1,
    canonical_relative_components_v1,
)

from .model import (
    BundleIOCodeV1,
    BundleIOErrorV1,
    checked_ref_v1,
    digest_v1,
)


def _root_node(directory: BorrowedDirectoryV1) -> dict[str, int]:
    identity = directory.identity
    return {
        "device": identity.device,
        "file_type": identity.mode & 0o170000,
        "inode": identity.inode,
    }


def _access_body(
    destination_ref: str,
    create_borrow: RetainedRootBorrowV1,
    create_root: BorrowedDirectoryV1,
    verify_borrow: RetainedRootBorrowV1,
    verify_root: BorrowedDirectoryV1,
) -> dict[str, object]:
    return {
        "create": {
            "access": create_borrow.access.value,
            "borrow_digest": create_borrow.borrow_digest,
            "request_digest": create_borrow.request_digest,
            "root_directory_digest": create_root.directory_digest,
            "root_node": _root_node(create_root),
        },
        "destination_ref": destination_ref,
        "root_authority_digest": create_borrow.root_authority_digest,
        "schema_version": "synaptic-host-bundle-borrow-access/v1",
        "verify": {
            "access": verify_borrow.access.value,
            "borrow_digest": verify_borrow.borrow_digest,
            "request_digest": verify_borrow.request_digest,
            "root_directory_digest": verify_root.directory_digest,
            "root_node": _root_node(verify_root),
        },
    }


@dataclass(frozen=True, slots=True)
class BundleBorrowAccessV1:
    destination_ref: str
    root_authority_digest: str
    create_borrow: RetainedRootBorrowV1
    create_root: BorrowedDirectoryV1
    verify_borrow: RetainedRootBorrowV1
    verify_root: BorrowedDirectoryV1
    access_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.destination_ref, BundleIOCodeV1.ACCESS_INVALID)
            if (
                type(self.create_borrow) is not RetainedRootBorrowV1
                or type(self.create_root) is not BorrowedDirectoryV1
                or type(self.verify_borrow) is not RetainedRootBorrowV1
                or type(self.verify_root) is not BorrowedDirectoryV1
                or self.create_borrow.root_authority_digest
                != self.root_authority_digest
                or self.verify_borrow.root_authority_digest
                != self.root_authority_digest
                or self.create_borrow.purpose
                is not BorrowPurposeV1.BUNDLE_DESTINATION_CREATE
                or self.create_borrow.access is not RootAccessV1.READ_CREATE
                or self.verify_borrow.purpose
                is not BorrowPurposeV1.BUNDLE_MOUNT_VERIFY
                or self.verify_borrow.access is not RootAccessV1.READ_ONLY
                or self.create_root.borrow_digest != self.create_borrow.borrow_digest
                or self.verify_root.borrow_digest != self.verify_borrow.borrow_digest
                or self.create_root.path_components != ()
                or self.verify_root.path_components != ()
                or self.create_root.owns_handle
                or self.verify_root.owns_handle
                or _root_node(self.create_root) != _root_node(self.verify_root)
                or self.access_digest != digest_v1(_access_body(
                    self.destination_ref,
                    self.create_borrow,
                    self.create_root,
                    self.verify_borrow,
                    self.verify_root,
                ))
            ):
                raise BundleIOErrorV1(BundleIOCodeV1.ACCESS_INVALID)
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise BundleIOErrorV1(BundleIOCodeV1.ACCESS_INVALID) from None

    @classmethod
    def build(cls, destination_ref, create_borrow, create_root,
              verify_borrow, verify_root):
        body = _access_body(
            destination_ref, create_borrow, create_root, verify_borrow, verify_root
        )
        return cls(
            destination_ref,
            create_borrow.root_authority_digest,
            create_borrow,
            create_root,
            verify_borrow,
            verify_root,
            digest_v1(body),
        )


def _source_body(source_ref, borrow, directory, component):
    return {
        "borrow_digest": borrow.borrow_digest,
        "component": component,
        "directory_digest": directory.directory_digest,
        "source_ref": source_ref,
        "schema_version": "synaptic-host-bundle-source/v1",
    }


@dataclass(frozen=True, slots=True)
class BundleSourceV1:
    source_ref: str
    borrow: RetainedRootBorrowV1
    directory: BorrowedDirectoryV1
    component: str
    source_digest: str

    def __post_init__(self) -> None:
        try:
            checked_ref_v1(self.source_ref, BundleIOCodeV1.SOURCE_INVALID)
            components = canonical_relative_components_v1(self.component)
            if (
                type(self.borrow) is not RetainedRootBorrowV1
                or type(self.directory) is not BorrowedDirectoryV1
                or components != (self.component,)
                or self.borrow.purpose is not BorrowPurposeV1.BUNDLE_SOURCE_READ
                or self.borrow.access is not RootAccessV1.READ_ONLY
                or self.directory.borrow_digest != self.borrow.borrow_digest
                or self.source_digest != digest_v1(_source_body(
                    self.source_ref, self.borrow, self.directory, self.component
                ))
            ):
                raise BundleIOErrorV1(BundleIOCodeV1.SOURCE_INVALID)
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise BundleIOErrorV1(BundleIOCodeV1.SOURCE_INVALID) from None

    @classmethod
    def build(cls, source_ref, borrow, directory, component):
        return cls(
            source_ref, borrow, directory, component,
            digest_v1(_source_body(source_ref, borrow, directory, component)),
        )


class BundleSourceRegistryPortV1(Protocol):
    def resolve(self, source_ref: str) -> BundleSourceV1: ...


__all__: tuple[str, ...] = ()
