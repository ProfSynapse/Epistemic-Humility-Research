#!/usr/bin/env python3
"""Shared deterministic I/O, provenance, and containment helpers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent
ANALYSIS = ROOT / "analysis"
COMMITTED = ROOT / "analysis-committed"
PROHIBITED_COMMITTED_KEYS = {
    "question", "answer", "answers", "answer_text", "aliases", "alias_text",
    "generation", "generation_text", "token_ids", "normalized_text_hash",
    "full_grader_dict", "parsed_answer", "answer_value",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_fingerprint(root: Path, files: Iterable[str]) -> dict[str, Any]:
    """Hash an explicit source import surface without relying on Git metadata."""
    records = []
    for relative in sorted(set(files)):
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"invalid source fingerprint path: {relative!r}")
        absolute = root / path
        if not absolute.is_file():
            raise ValueError(f"source fingerprint file is missing: {relative}")
        records.append({
            "path": path.as_posix(), "sha256": sha256_file(absolute),
            "size_bytes": absolute.stat().st_size,
        })
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return {"sha256": sha256_bytes(payload), "files": records}


def require_synaptic_tuner_source(cfg: dict[str, Any]) -> dict[str, Any]:
    """Verify the signed tuner byte surface without invoking Git in-container."""
    spec = cfg["generation"]["vllm"]["synaptic_tuner_source"]
    if spec.get("algorithm") != "sha256_canonical_path_digest_size_v1":
        raise RuntimeError("unsupported Synaptic Tuner source fingerprint algorithm")
    tuner_root = ROOT.parents[1] / spec["root"]
    observed = source_fingerprint(tuner_root, spec["files"])
    if observed["sha256"] != spec["sha256"]:
        raise RuntimeError("Synaptic Tuner runtime source fingerprint mismatch")
    return observed


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def append_jsonl_fsync(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def require_pinned_container(expected_digest: str) -> None:
    """Fail closed unless the launcher attests the exact pinned image."""
    if not expected_digest.startswith("sha256:") or len(expected_digest) != 71:
        raise RuntimeError("cell.yaml does not contain a valid pinned image digest")
    actual = os.environ.get("EHR_MECHINTERP_IMAGE_DIGEST")
    if not Path("/.dockerenv").exists() or actual != expected_digest:
        raise RuntimeError(
            "GPU entrypoint requires the pinned mechinterp-runner container and "
            f"EHR_MECHINTERP_IMAGE_DIGEST={expected_digest}"
        )


def instrument_fingerprint() -> str:
    manifest = load_yaml(ROOT / "experiment.yaml")
    instrument = manifest["instrument"]
    names = list(instrument["configs"]) + list(instrument["modules"])
    pins = instrument.get("pins", {})
    missing = [name for name in names if name not in pins]
    if missing:
        raise RuntimeError(f"signed instrument pins are missing for {missing}")
    mismatched = [name for name in names if sha256_file(ROOT / name) != pins[name]]
    if mismatched:
        raise RuntimeError(f"current instrument files differ from signed pins: {mismatched}")
    payload = [{"path": name, "sha256": pins[name]} for name in names]
    return sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def containment_lint(
    committed_root: Path = COMMITTED,
    *,
    private_texts: Iterable[str] = (),
) -> dict[str, Any]:
    """Scan committed structured artifacts for private keys and known text."""
    errors: list[str] = []
    needles = sorted({s for s in private_texts if isinstance(s, str) and len(s) >= 8})
    for path in sorted(committed_root.rglob("*")) if committed_root.exists() else []:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix in {".json", ".jsonl"}:
            values = [json.loads(line) for line in raw.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(raw)]
            for value in values:
                bad = sorted({k for k in _walk_keys(value) if k.casefold() in PROHIBITED_COMMITTED_KEYS})
                if bad:
                    errors.append(f"{path.name}: prohibited keys {bad}")
        for needle in needles:
            if needle in raw:
                errors.append(f"{path.name}: contains private text sha256={sha256_bytes(needle.encode())}")
    return {"status": "pass" if not errors else "fail", "errors": errors}


def terminal_containment_scan(*, private_texts: Iterable[str] = ()) -> dict[str, Any]:
    """Deterministic final allowlist and containment gate for packaging."""
    allowed_top = {
        "aggregate_results.json", "containment_report.json",
        "presign_matcher_reachability.json",
    }
    allowed_cell = {
        "split_manifest.jsonl", "g0_g2_summary.json", "capture_manifest.json",
        "aggregate_results.json",
        "presign_smoke_manifest.jsonl", "presign_smoke_summary.json",
    }
    errors: list[str] = []
    for path in sorted(COMMITTED.rglob("*")) if COMMITTED.exists() else []:
        if not path.is_file():
            continue
        rel = path.relative_to(COMMITTED)
        allowed = (len(rel.parts) == 1 and rel.name in allowed_top) or (
            len(rel.parts) == 2
            and rel.parts[0] in {"gemma4_e4b_it", "qwen3_4b_raw_base"}
            and rel.name in allowed_cell
        )
        if not allowed:
            errors.append(f"unexpected committed artifact: {rel.as_posix()}")
    lint = containment_lint(COMMITTED, private_texts=private_texts)
    errors.extend(lint["errors"])
    return {
        "status": "pass" if not errors else "fail",
        "allowlist_version": 1,
        "errors": sorted(set(errors)),
    }


def gate(status: str, checks: dict[str, Any], reasons: list[str] | None = None) -> dict[str, Any]:
    if status not in {"pass", "fail", "not_run"}:
        raise ValueError(f"invalid gate status {status!r}")
    return {"status": status, "checks": checks, "reasons": reasons or []}
