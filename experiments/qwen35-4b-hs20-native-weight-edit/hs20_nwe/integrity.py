"""Measured source/runtime/data binding and verifiable kill/resume receipts."""

import os
from pathlib import Path

import yaml

from . import commitments
from .config import Layout
from .util import HarnessError, canonical_sha256, read_json, read_jsonl, sha256_file

BINDING_NAME = "run_binding.json"


def _stamp(cell, document):
    return all(document.get(k) == value for k, value in cell.stamp().items())


def snapshot(cell, layout, *, full_model=True):
    from engine_host.engine_identity import inspect_engine
    import engine_host

    layout = Layout(layout.project_root, layout.slug)
    engine = inspect_engine(layout.project_root)
    if engine["wheel_sha256"] != cell.cell["engine"]["wheel_sha256"]:
        raise HarnessError("ENGINE_DRIFT", "cell and installed engine wheel pins differ")
    expected_image = yaml.safe_load((cell.directory / "experiment.yaml").read_text())["instrument"]["runtime_image_digest"]
    attestation = read_json(layout.local("runtime_attestation.json", shared=True))
    if (os.environ.get("EHR_RUNTIME_IMAGE_DIGEST") != expected_image
            or attestation.get("derived_image") != expected_image or attestation.get("base_layers_verified") is not True):
        raise HarnessError("RUNTIME_DRIFT", "launch image does not match its reviewed host attestation")
    manifest_path = layout.local("materialize/manifest.json", shared=True)
    manifest = read_json(manifest_path)
    payload = {k: v for k, v in manifest.items() if k != "manifest_sha256_payload"}
    if not _stamp(cell, manifest) or canonical_sha256(payload) != manifest.get("manifest_sha256_payload"):
        raise HarnessError("MATERIALIZE_DRIFT", "materialization stamp or checksum changed")
    for name, digest in manifest["row_file_sha256"].items():
        if sha256_file(layout.local(f"materialize/{name}.jsonl", shared=True)) != digest:
            raise HarnessError("MATERIALIZE_DRIFT", "a frozen materialized population changed")
    for name, digest in manifest["input_sha256"].items():
        if sha256_file(layout.local(f"inputs/{name}", shared=True)) != digest:
            raise HarnessError("INPUT_DRIFT", "a staged source pool changed")
    shards = cell.cell["model"]["files_sha256"]
    if full_model:
        for name, digest in shards.items():
            if sha256_file(layout.local(f"base_model/{name}", shared=True)) != digest:
                raise HarnessError("MODEL_DRIFT", "a base model shard changed")
    direction_root = layout.project_local(cell.cell["writer"]["direction_root"])
    directions = {p.name: sha256_file(p) for p in sorted(direction_root.glob("*.json"))}
    from .stages import doctor
    from .stages import Ctx
    doctor(Ctx(layout.project_root, cell, layout))
    source = {path.relative_to(cell.directory).as_posix(): sha256_file(path)
              for path in sorted((cell.directory / "hs20_nwe").glob("*"))
              if path.is_file() and path.suffix in (".py", ".json", ".yaml")}
    host = {path.name: sha256_file(path) for path in sorted(Path(engine_host.__file__).parent.glob("*.py"))}
    return {"schema_version": "hs20-nwe-run-binding/v1", **cell.stamp(),
            "engine_identity": engine, "host_module_sha256": host,
            "runtime_attestation": attestation, "source_module_sha256": source,
            "project_manifest_sha256": sha256_file(layout.project_root / "synaptic.yaml"),
            "materialize_manifest_sha256": sha256_file(manifest_path), "model_files_sha256": shards,
            "direction_files_sha256": directions}


def bind(cell, layout):
    document = snapshot(cell, layout, full_model=True)
    path = commitments.public_path(layout, BINDING_NAME)
    if path.exists() and read_json(path) != document:
        raise HarnessError("BINDING_CHANGED", "use a fresh execution namespace for changed source/runtime/data")
    commitments.export(layout, BINDING_NAME, document)
    return {"public_manifest": str(path), "git_commit_required": True}


def verify(cell, layout, *, full_model=False):
    expected = read_json(commitments.public_path(layout, BINDING_NAME))
    actual = snapshot(cell, layout, full_model=full_model)
    if actual != expected:
        raise HarnessError("BINDING_DRIFT", "source, thresholds, runtime or frozen populations changed")
    commit = commitments.require_git(layout, BINDING_NAME, expected)
    for path in layout.local("stages").glob("*.done.json"):
        stage = read_json(path)
        if not _stamp(cell, stage):
            raise HarnessError("STAGE_DRIFT", "a completed stage used different registered constants")
        for job in stage.get("jobs", []) if isinstance(stage.get("jobs"), list) else []:
            if isinstance(job, dict) and "grades_sha256" in job:
                if sha256_file(layout.local(f"grades/{job['job']}.jsonl")) != job["grades_sha256"]:
                    raise HarnessError("GRADE_DRIFT", "detector grades changed after their completed stage")
    return {"passed": True, "binding_commit": commit, "full_model_hashes_checked": full_model}


def report(cell, layout):
    try:
        return verify(cell, layout, full_model=True)
    except (HarnessError, OSError, KeyError, ValueError) as exc:
        return {"passed": False, "reason": str(exc)}


def binding_digest(layout):
    return sha256_file(commitments.public_path(layout, BINDING_NAME))


def evidence_stamp(cell, layout):
    return {**cell.stamp(), "run_binding_sha256": binding_digest(layout)}


def verify_drill(cell, layout, evidence):
    """Require actual before/after journals, signal evidence, and exact resume."""
    if not evidence or evidence.get("schema_version") != "hs20-nwe-kill-resume/v1" or not _stamp(cell, evidence):
        return False
    if evidence.get("run_binding_sha256") != binding_digest(layout):
        return False
    drills = evidence.get("drills", [])
    if {d.get("module") for d in drills} != {"extract", "generation", "localize"} or len(drills) != 3:
        return False
    try:
        for drill in drills:
            before_path = layout.to_local(drill["before_journal"])
            after_path = layout.to_local(drill["after_journal"])
            if sha256_file(before_path) != drill["before_sha256"] or sha256_file(after_path) != drill["after_sha256"]:
                return False
            before, after = read_jsonl(before_path), read_jsonl(after_path)
            keys = [r.get("row_key", r.get("key")) for r in after]
            if (drill["signal"] != 9 or drill["killed_pid"] <= 0 or drill["resume_exit_code"] != 0
                    or drill.get("run_binding_sha256") != binding_digest(layout)
                    or drill["expected_rows"] != cell.cell["qualification"]["rows"]
                    or len(before) < 4 or len(after) != drill["expected_rows"]
                    or len(after) <= len(before) or len(set(keys)) != len(after) or None in keys
                    or after[:len(before)] != before):
                return False
        return True
    except (HarnessError, OSError, ValueError, KeyError, TypeError):
        return False
