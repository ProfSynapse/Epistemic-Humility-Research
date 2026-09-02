"""Strict, metadata-only local storage registry loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .model import (
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RootAccessV1,
    canonical_posix_root_components_v1,
    checked_ref,
    checked_sha256,
    digest_v1,
)


_SCHEMA = "synaptic-host-storage/v1"
_MAX_CONFIG_BYTES = 65_536
_MAX_ROOTS = 128
_TOP_FIELDS = {"schema_version", "roots"}
_ROOT_FIELDS = {"root_ref", "location", "access", "permit_ref"}


def _closed(code: LocalIOCodeV1) -> LocalIOErrorV1:
    return LocalIOErrorV1(code)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _closed(LocalIOCodeV1.CONFIG_INVALID)
        result[key] = value
    return result


def _canonical_project_relative(value: object) -> tuple[str, ...]:
    if type(value) is not str or not value.startswith("project://"):
        raise _closed(LocalIOCodeV1.CONFIG_INVALID)
    suffix = value[len("project://") :]
    try:
        return canonical_posix_root_components_v1(suffix)
    except (LocalIOErrorV1, UnicodeError):
        raise _closed(LocalIOCodeV1.CONFIG_INVALID) from None


@dataclass(frozen=True, slots=True)
class _RootSpecV1:
    root_ref: str
    location_ref: str
    absolute_root: Path
    access: RootAccessV1
    permit_ref: str


@dataclass(slots=True)
class StorageRegistryV1:
    _specs: Mapping[str, _RootSpecV1]
    _roots: dict[str, LocalRootBindingV1]
    _permits: dict[str, LocalRootPermitV1]

    @classmethod
    def load(
        cls,
        config_path: Path,
        *,
        project_root: Path,
    ) -> "StorageRegistryV1":
        try:
            raw = config_path.read_bytes()
            if len(raw) > _MAX_CONFIG_BYTES:
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
        except LocalIOErrorV1:
            raise
        except (OSError, UnicodeError):
            raise _closed(LocalIOCodeV1.CONFIG_IO_FAILED) from None
        return cls.from_bytes(raw, project_root=project_root)

    @classmethod
    def from_bytes(
        cls,
        raw: bytes,
        *,
        project_root: Path,
    ) -> "StorageRegistryV1":
        try:
            if (
                type(raw) is not bytes
                or not project_root.is_absolute()
                or len(raw) > _MAX_CONFIG_BYTES
            ):
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        except LocalIOErrorV1:
            raise
        except (UnicodeError, TypeError, ValueError, json.JSONDecodeError):
            raise _closed(LocalIOCodeV1.CONFIG_INVALID) from None

        if type(value) is not dict or set(value) != _TOP_FIELDS:
            raise _closed(LocalIOCodeV1.CONFIG_INVALID)
        if value.get("schema_version") != _SCHEMA:
            raise _closed(LocalIOCodeV1.CONFIG_INVALID)
        specs = value.get("roots")
        if type(specs) is not list or not specs or len(specs) > _MAX_ROOTS:
            raise _closed(LocalIOCodeV1.CONFIG_INVALID)

        parsed: dict[str, _RootSpecV1] = {}
        for spec in specs:
            if type(spec) is not dict:
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
            location = spec.get("location")
            is_project = type(location) is str and location.startswith("project://")
            if set(spec) != _ROOT_FIELDS:
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
            root_ref = checked_ref(spec.get("root_ref"))
            if root_ref in parsed:
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
            try:
                access = RootAccessV1(spec.get("access"))
            except (TypeError, ValueError):
                raise _closed(LocalIOCodeV1.CONFIG_INVALID) from None

            permit_ref = checked_ref(spec.get("permit_ref"))
            if is_project:
                parts = _canonical_project_relative(location)
                absolute = project_root.absolute().joinpath(*parts)
            else:
                if type(location) is not str:
                    raise _closed(LocalIOCodeV1.CONFIG_INVALID)
                # Refuse every Win32 name that opens on two separators.  Windows
                # accepts "\" and "/" interchangeably, so all four pairings name
                # the same family: the UNC share ("\\server\share"), the UNC
                # device form ("\\?\UNC\server\share"), the extended-length
                # prefix ("\\?\C:\...") and the device namespace ("\\.\...").
                # None of them is a local volume path the retained-handle
                # descent can walk from a project anchor, and a remote share
                # cannot be contained by the project at all.  A SINGLE leading
                # separator is an ordinary POSIX absolute path and stays legal.
                if len(location) >= 2 and location[0] in "\\/" and location[1] in "\\/":
                    raise _closed(LocalIOCodeV1.CONFIG_INVALID)
                candidate = Path(location)
                if not candidate.is_absolute():
                    raise _closed(LocalIOCodeV1.CONFIG_INVALID)
                absolute = candidate.absolute()
                # Containment.  A ".." component would make the component-wise
                # prefix test below unsound -- "<project>/../etc" passes a parts
                # compare while naming a path outside the project -- so refuse
                # it outright.  Normalising it away instead would need
                # resolve(), and resolve() reads the filesystem and follows
                # symlinks, neither of which config parsing may do.
                if ".." in absolute.parts:
                    raise _closed(LocalIOCodeV1.CONFIG_INVALID)
                anchor = project_root.absolute().parts
                # Component-wise, never str.startswith: "/proj-other" must not
                # count as contained by "/proj".
                if absolute.parts[: len(anchor)] != anchor:
                    raise _closed(LocalIOCodeV1.CONFIG_INVALID)

            parsed[root_ref] = _RootSpecV1(
                root_ref, location, absolute, access, permit_ref
            )
        return cls(MappingProxyType(parsed), {}, {})

    def issue_root_permit(
        self,
        root_ref: str,
        *,
        authority_ref: str,
        key_ref: str,
        proof_digest: str,
    ) -> LocalRootPermitV1:
        checked = checked_ref(root_ref)
        checked_ref(authority_ref, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        checked_ref(key_ref, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        checked_sha256(proof_digest, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        try:
            spec = self._specs[checked]
        except KeyError:
            raise _closed(LocalIOCodeV1.ROOT_UNKNOWN) from None
        canonical = {
            "access": spec.access.value,
            "absolute_root": str(spec.absolute_root),
            "authority_ref": authority_ref,
            "key_ref": key_ref,
            "permit_ref": spec.permit_ref,
            "root_ref": spec.root_ref,
        }
        candidate = LocalRootPermitV1(
            spec.permit_ref, spec.root_ref, spec.absolute_root, spec.access,
            authority_ref, key_ref, digest_v1(canonical), proof_digest,
        )
        existing = self._permits.get(spec.permit_ref)
        if existing is not None:
            if existing != candidate:
                raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED)
            return existing
        binding = LocalRootBindingV1(
            spec.root_ref, spec.location_ref, spec.absolute_root, spec.access,
            spec.permit_ref, candidate,
        )
        self._permits[spec.permit_ref] = candidate
        self._roots[spec.root_ref] = binding
        return candidate

    def authenticate(self, permit: LocalRootPermitV1) -> LocalRootPermitV1 | None:
        if type(permit) is not LocalRootPermitV1:
            return None
        issued = self._permits.get(permit.permit_ref)
        return issued if issued is permit else None

    def resolve(self, root_ref: str) -> LocalRootBindingV1:
        checked = checked_ref(root_ref)
        if checked not in self._specs:
            raise _closed(LocalIOCodeV1.ROOT_UNKNOWN)
        try:
            return self._roots[checked]
        except KeyError:
            raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED) from None

    def list_roots(self) -> tuple[LocalRootBindingV1, ...]:
        if len(self._roots) != len(self._specs):
            raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED)
        return tuple(self._roots[key] for key in sorted(self._roots))
