"""Inspect the installed distribution without importing ML or provider runtimes."""

from __future__ import annotations

from importlib import metadata
from importlib.util import find_spec
import base64
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from packaging.specifiers import SpecifierSet
from packaging.version import Version
import yaml


def inspect_engine(project_root: Path) -> dict:
    project_root = Path(project_root).resolve()
    manifest_path = project_root / "synaptic.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "synaptic-project/v1":
        raise ValueError("a synaptic-project/v1 manifest is required")
    engine = manifest.get("engine", {})
    if engine.get("api") != "v1" or not isinstance(engine.get("requires"), str):
        raise ValueError("engine.api v1 and engine.requires are required")
    distribution = metadata.distribution("synaptic-tuner")
    version = Version(distribution.version)
    requirement = SpecifierSet(engine["requires"])
    if not requirement.contains(version, prereleases=bool(requirement.prereleases)):
        raise ValueError("installed engine does not satisfy the project requirement")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    wheel_sha = direct.get("archive_info", {}).get("hashes", {}).get("sha256")
    archive_hash = direct.get("archive_info", {}).get("hash", "")
    if wheel_sha is None and archive_hash.startswith("sha256="):
        wheel_sha = archive_hash.split("=", 1)[1]
    # uv retains a reviewed direct-reference hash in the URL fragment rather
    # than archive_info. Both transports bind the installation to the wheel.
    if wheel_sha is None:
        wheel_sha = parse_qs(urlparse(direct.get("url", "")).fragment).get("sha256", [None])[0]
    expected_sha = engine.get("wheel_sha256")
    if expected_sha is not None:
        if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise ValueError("engine.wheel_sha256 must be a full lowercase SHA256")
        if wheel_sha != expected_sha or "dir_info" in direct:
            raise ValueError("installed engine does not match the reviewed wheel SHA256")
    # Verify installed bytes, rather than merely hashing the RECORD text. This
    # detects accidental edits; the trusted build ledger supplies the wheel pin.
    for file in distribution.files or ():
        if file.hash and file.hash.mode == "sha256":
            path = Path(distribution.locate_file(file))
            if not path.is_file():
                raise ValueError("installed engine file is missing")
            digest = base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest()).decode().rstrip("=")
            if digest != file.hash.value:
                raise ValueError("installed engine file differs from its installation RECORD")
    for name in ("synaptic_tuner", "tuner", "MechInterp", "shared", "Trainers", "Evaluator", "SynthChat", "schemas"):
        spec = find_spec(name)
        expected_root = Path(distribution.locate_file(name)).resolve()
        locations = list(spec.submodule_search_locations or ()) if spec else []
        if spec and spec.origin and spec.origin != "namespace":
            locations.append(spec.origin)
        if any(not Path(location).resolve().is_relative_to(expected_root) for location in locations):
            raise ValueError("a host module shadows an installed engine package")
    from synaptic_tuner.api.v1 import APIHost, DataAPI, EvaluationAPI, RunsAPI, TrainingAPI
    import synaptic_tuner

    package_path = Path(synaptic_tuner.__file__).resolve()
    installed_root = Path(distribution.locate_file("synaptic_tuner")).resolve()
    if not package_path.is_relative_to(installed_root):
        raise ValueError("imported engine does not belong to the installed distribution")
    historical = project_root / "synaptic-tuner"
    if package_path.is_relative_to(historical):
        raise ValueError("new work requires an installed engine, not the historical submodule")
    record = distribution.read_text("RECORD")
    return {
        "schema_version": "ehr-engine-identity/v1",
        "version": str(version),
        "cli_requires": engine.get("cli_requires"),
        "api": "v1",
        "package_path": str(package_path),
        "installation_record_sha256": hashlib.sha256(record.encode()).hexdigest() if record else None,
        "wheel_sha256": wheel_sha,
        "wheel_pin_verified": expected_sha is not None and wheel_sha == expected_sha,
        "declared_source_commit": engine.get("source_commit"),
        "source_commit_evidence": "reviewed-wheel-ledger" if expected_sha else "not-pinned",
        "direct_url": direct,
        "installed_files_verified": True,
        "project_id": manifest["project"]["id"],
        "manifest_path": str(manifest_path),
        "families": [c.__name__ for c in (APIHost, DataAPI, EvaluationAPI, RunsAPI, TrainingAPI)],
        "mechinterp_boundary": "version-pinned-cli",
        "backend_qualification": "not-established-by-import",
    }
