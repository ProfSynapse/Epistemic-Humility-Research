#!/usr/bin/env python3
"""G2: the submit container satisfies 29.10, and its PATH is under 4096 bytes.

Gate G2 of docs/architecture/prepared-path-alpine-diagnostic.md 29.12. This
script runs INSIDE the submit container and decides the gate from what it can
observe there. It makes no Modal call, reads no credential, and needs no
network.

What the six checks establish
-----------------------------
C1  modal is importable and its version is exactly 1.5.4.
    29.10 pins the SDK by equality, not by a floor. The container installs it
    from the hash-locked `modal-launcher-v1.lock` with --require-hashes
    --only-binary :all: --no-deps, so a satisfied C1 also says the resolver
    never ran.

C2  NO engine or project source is baked into the image.
    29.10 forbids carrying either as a layer. The check runs BEFORE the engine
    root joins sys.path: if `tuner` already resolves, a layer carries it and the
    container is not the ruled one. This is the only check whose value depends
    on running first, so it is ordered first among the sys.path checks.

C3  After the submit process puts the engine root on sys.path in code, `tuner`
    resolves INSIDE that root.
    Containment is measured with importlib.util.find_spec, never by reading
    `module.__file__`: a namespace package has `__file__ = None`, so the
    attribute read raises on exactly the shape the check exists to catch. Both
    package shapes are handled: `spec.origin` for a regular package, and
    `spec.submodule_search_locations` for a namespace package. Every location
    found must lie under the engine root, and at least one must exist.

C4  The engine root holds the COMMIT the Host is pinned to.
    Containment (C3) proves which TREE was imported. It cannot prove which
    COMMIT that tree is at: a dirty or differently checked-out submodule passes
    C3 unchanged. The gitlink is therefore measured separately, on the host
    side where git lives, and passed in. Neither check implies the other and
    the gate needs both.

C5  The container PATH is under the 4096-byte bound.
    launcher.py:104-113 rejects any allowlisted child environment value longer
    than 4096 bytes, so ensure_and_reexec fails under a long PATH. The operator
    PATH was measured at 5248 bytes in a WSL shell and 3903 on Windows, so the
    bound is not theoretical: the submit container must carry a short PATH of
    its own rather than inherit the operator's. The operator measurement is
    recorded alongside (follow-up #432 asks G2 to record it), and a violating
    operator PATH is reported as a WARN rather than a gate failure, because the
    container's own PATH is what the gate governs.

C6  No credential-class name is present in the container environment.
    29.10 requires credentials to be passed in-process at submit time and never
    to enter a layer. The check counts matching names and reports the COUNT
    ONLY. It never emits a name, a value, or a length.

Usage
-----
    python3 g2_submit_container.py \
        --engine-root /engine \
        --gitlink-expected <sha> --gitlink-observed <sha> \
        --operator-path-bytes 5248

Exit 0 when every check passes, 1 when any fails, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

REQUIRED_SDK_VERSION = "1.5.4"
ENGINE_PACKAGE = "tuner"
CHILD_ENVIRONMENT_VALUE_LIMIT = 4096

# Names whose presence in a container layer would mean a credential was baked
# in. Held as data so that no report line ever has to contain one of them.
CREDENTIAL_NAMES = (
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "SYNAPTIC_EVIDENCE_MAC_KEY",
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
)


def emit(line: str) -> None:
    print(line)


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def check(self, tag: str, ok: bool, detail: str) -> bool:
        emit(f"{'PASS' if ok else 'FAIL'} {tag}  {detail}")
        if not ok:
            self.failures.append(tag)
        return ok

    def warn(self, tag: str, detail: str) -> None:
        emit(f"WARN {tag}  {detail}")
        self.warnings.append(tag)


def spec_locations(spec: importlib.machinery.ModuleSpec) -> list[Path]:
    """Every filesystem location a spec resolves to, for both package shapes.

    A regular package carries its __init__.py in `origin`. A namespace package
    carries `origin` None (or the literal "namespace") and one or more portions
    in `submodule_search_locations`. Reading `module.__file__` instead would
    raise on the namespace shape, which is the shape a stray sys.path entry
    most often produces.
    """
    locations: list[Path] = []
    origin = spec.origin
    if origin and origin != "namespace":
        locations.append(Path(origin).resolve())
    search = spec.submodule_search_locations
    if search:
        locations.extend(Path(entry).resolve() for entry in search)
    return locations


def is_contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--engine-root",
        type=Path,
        required=True,
        help="engine tree as mounted inside the container (read-only)",
    )
    parser.add_argument(
        "--gitlink-expected",
        required=True,
        help="engine commit the Host superproject records (measured on the host)",
    )
    parser.add_argument(
        "--gitlink-observed",
        required=True,
        help="engine commit the mounted tree is at (measured on the host)",
    )
    parser.add_argument(
        "--operator-path-bytes",
        type=int,
        default=None,
        help="byte length of the operator PATH, measured on the host (#432)",
    )
    args = parser.parse_args(argv)

    report = Report()
    engine_root = args.engine_root.resolve()

    emit("G2 submit-container gate (29.10, 29.12)")
    emit(f"interpreter    : {sys.version.split()[0]} at {sys.executable}")
    emit(f"engine root    : {engine_root}  (exists={engine_root.is_dir()})")
    emit("")

    # ---- C2 first: the image must not already carry the engine ----------
    pre_spec = importlib.util.find_spec(ENGINE_PACKAGE)
    report.check(
        "C2 no-engine-layer",
        pre_spec is None,
        f"{ENGINE_PACKAGE!r} resolvable before sys.path establishment: "
        f"{pre_spec is not None} (must be False)",
    )

    # ---- C1 the SDK pin -------------------------------------------------
    try:
        import modal  # noqa: PLC0415 - imported here so C2 can run first

        observed_version = getattr(modal, "__version__", None)
    except Exception as error:  # pragma: no cover - reported, not raised
        observed_version = None
        emit(f"     modal import raised {type(error).__name__}: {error}")
    report.check(
        "C1 sdk-pin",
        observed_version == REQUIRED_SDK_VERSION,
        f"modal.__version__={observed_version!r} required={REQUIRED_SDK_VERSION!r}",
    )

    # ---- C3 containment after in-code sys.path establishment ------------
    if not engine_root.is_dir():
        report.check("C3 engine-containment", False, "engine root is not a directory")
    else:
        sys.path.insert(0, str(engine_root))
        importlib.invalidate_caches()
        post_spec = importlib.util.find_spec(ENGINE_PACKAGE)
        if post_spec is None:
            report.check(
                "C3 engine-containment",
                False,
                f"{ENGINE_PACKAGE!r} still does not resolve with the engine root on sys.path",
            )
        else:
            locations = spec_locations(post_spec)
            contained = bool(locations) and all(
                is_contained(location, engine_root) for location in locations
            )
            shape = "regular" if post_spec.origin not in (None, "namespace") else "namespace"
            report.check(
                "C3 engine-containment",
                contained,
                f"shape={shape} locations={len(locations)} all under {engine_root}: {contained}",
            )
            if not contained:
                for location in locations:
                    emit(f"     resolved outside the engine root: {location}")

    # ---- C4 the pin, measured separately from containment ---------------
    report.check(
        "C4 gitlink-pin",
        args.gitlink_expected == args.gitlink_observed
        and len(args.gitlink_expected) >= 40,
        f"expected={args.gitlink_expected} observed={args.gitlink_observed}",
    )

    # ---- C5 the 4096-byte child environment bound -----------------------
    container_path_bytes = len(os.environb.get(b"PATH", b""))
    report.check(
        "C5 container-path-bound",
        0 < container_path_bytes < CHILD_ENVIRONMENT_VALUE_LIMIT,
        f"container PATH is {container_path_bytes} bytes, bound {CHILD_ENVIRONMENT_VALUE_LIMIT}",
    )
    if args.operator_path_bytes is None:
        report.warn(
            "C5 operator-path-record",
            "operator PATH length not supplied; #432 asks G2 to record it",
        )
    else:
        measured = args.operator_path_bytes
        emit(
            f"INFO C5 operator-path-record  operator PATH is {measured} bytes,"
            f" bound {CHILD_ENVIRONMENT_VALUE_LIMIT}"
        )
        if measured >= CHILD_ENVIRONMENT_VALUE_LIMIT:
            report.warn(
                "C5 operator-path-record",
                "the operator PATH exceeds the bound; the submit container carries"
                " its own short PATH, so the gate is unaffected, but the operator"
                " shell cannot host ensure_and_reexec directly",
            )

    # ---- C6 no credential-class name in the container environment -------
    present = sum(1 for name in CREDENTIAL_NAMES if name in os.environ)
    report.check(
        "C6 no-baked-credentials",
        present == 0,
        f"credential-class names present in the container environment: {present}"
        f" of {len(CREDENTIAL_NAMES)} checked (names and values are never emitted)",
    )

    emit("")
    if report.failures:
        emit(f"G2 FAIL  failing checks: {report.failures}")
        return 1
    if report.warnings:
        emit(f"G2 PASS with warnings: {report.warnings}")
        return 0
    emit("G2 PASS  all six checks satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
