"""R2 constructor bridge, with frozen R1 roster I/O only. No R1 scale selection."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any
import yaml
from .util import HarnessError, canonical_sha256, sha256_file, sha256_bytes
from .constructor import Proposal, load_proposal, bf16_raw_sha256, select_roster, normalize_question, roster_digest, HISTORICAL_ROLES
ROSTER_SCHEMA="ehr-astra-roster/v1"

def _create_only(path: str | Path, data: bytes) -> str:
    """Create once and fsync, including on T7 exFAT (which has no hard links).

    Consumers require the completed report and verify every artifact hash. A
    killed short preparation can leave an incomplete file; it is never resumed
    by overwriting it. Repeat the same construction in a fresh output directory.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise HarnessError("OUTPUT_EXISTS", f"refusing to overwrite {path.name}") from exc
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256_bytes(data)


def _json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_question_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(doc, list):
            rows = doc
        elif isinstance(doc, dict) and isinstance(doc.get("example"), list):
            rows = doc["example"]  # native SelfAware release container, preserved byte-for-byte
        elif isinstance(doc, dict) and isinstance(doc.get("question"), str):
            rows = [doc]
        else:
            raise HarnessError("SURFACE_ROWS", "unsupported question dataset container")
    return rows


def _questions(rows: list[dict], what: str) -> list[str]:
    out = []
    for row in rows:
        q = row.get("question") if isinstance(row, dict) else None
        if not isinstance(q, str) or not q.strip():
            raise HarnessError("SURFACE_ROW", f"{what} has a row without a question field")
        out.append(q)
    return out


def prepare_roster(proposal: Proposal, fit_path: Path, surface_paths: dict[str, Path], out_path: Path) -> dict:
    """Hash-check inputs, select the roster, write an ID-only create-only roster. Returns a text-free summary."""
    dev, surf = proposal.raw["development"], proposal.raw["evaluation"]["surfaces"]
    if set(surface_paths) != set(surf):
        raise HarnessError("SURFACES", f"need exactly the registered surfaces {sorted(surf)}")
    if sha256_file(fit_path) != dev["fit_sha256"]:
        raise HarnessError("INPUT_HASH", "FIT input sha256 differs from the registered hash")
    questions = {}
    for name, path in surface_paths.items():
        if sha256_file(path) != surf[name]["sha256"]:
            raise HarnessError("INPUT_HASH", f"{name} surface sha256 differs from the registered hash")
        rows = _read_question_rows(Path(path))
        if len(rows) != int(surf[name]["rows"]):
            raise HarnessError("SURFACE_ROWS", f"{name} row count differs from the registered count")
        questions[name] = _questions(rows, name)
    result = select_roster(_read_question_rows(Path(fit_path)), questions, seed=dev["seed"], counts=proposal.group_size)
    doc = {"schema_version": ROSTER_SCHEMA, "launch_authority": False, "proposal_sha256": proposal.sha256,
           "seed": int(dev["seed"]), "counts": proposal.group_size, "fit_sha256": dev["fit_sha256"],
           "surface_sha256": {n: surf[n]["sha256"] for n in sorted(surf)}, "keys": result["keys"],
           "roster_sha256": roster_digest(result["keys"]), "stats": result["stats"],
           "note": "IDs only; contains no question or answer text."}
    _create_only(out_path, _json_bytes(doc))
    return {"roster_sha256": doc["roster_sha256"], "stats": doc["stats"]}


def load_roster(proposal: Proposal, path: Path) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema_version") != ROSTER_SCHEMA or doc.get("proposal_sha256") != proposal.sha256:
        raise HarnessError("ROSTER_STALE", "roster is not for this proposal")
    keys = doc.get("keys") or {}
    if set(keys) != set(HISTORICAL_ROLES) or roster_digest(keys) != doc.get("roster_sha256"):
        raise HarnessError("ROSTER_STALE", "roster content does not match its recorded digest")
    for role, n in proposal.group_size.items():
        if len(keys[role]) != n or len(set(keys[role])) != n:
            raise HarnessError("ROSTER_STALE", f"roster {role} size is not {n}")
    if set(keys[HISTORICAL_ROLES[0]]) & set(keys[HISTORICAL_ROLES[1]]):
        raise HarnessError("ROSTER_STALE", "roster groups overlap")
    return doc

