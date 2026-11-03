"""Weights-inspect configs, patch proposals/payloads, receipts and norm-matched controls.

Edits are analytic only (no fitting): for block b, columns J (ranked) and scale l,
``DeltaW[:, J] = l * c_hat * (c_hat^T W[:, J])``.  It is expressed as the
engine's generic ``add_rank_one`` op with ``u = c_hat``, ``v = c_hat^T W[:, J]``
(taken from the engine's own float64 ``weights-inspect`` dots, so this module
never reads the base tensor) and ``scale = l``.  Realized norms and budgets are
decided by the engine's ``weights-patch --validate`` receipts, never by
numpy here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from .config import Cell, Layout
from .util import HarnessError, sha256_file, write_yaml

INSPECT_SCHEMA = "mechinterp-weights-inspect/v1"
PATCH_SCHEMA = "mechinterp-weight-patch/v1"


def unwrap(doc: dict) -> dict:
    """CLI --json output is ``{success, data|error}``; accept a bare report too."""
    if isinstance(doc, dict) and "success" in doc:
        if not doc["success"]:
            err = doc.get("error", {})
            raise HarnessError(str(err.get("code", "ENGINE_ERROR")), str(err.get("message", "engine refused")))
        return doc["data"]
    return doc


def tensor_pattern(block: int) -> str:
    return f"*layers.{block}.mlp.down_proj.weight"


# ---------------------------------------------------------------------------
# weights-inspect requests (bounded numeric reads)
# ---------------------------------------------------------------------------

def list_request(cell: Cell, layout: Layout) -> dict:
    return {
        "schema_version": INSPECT_SCHEMA,
        "checkpoint": layout.ref("base_model", shared=True),
        "hash_files": True,
        "hash_tensors": True,
        "tensors": [tensor_pattern(b) for b in cell.cell["candidates"]["blocks"]],
        "max_listed_tensors": 16,
        "projections": [],
    }


def resolve_targets(cell: Cell, listing: dict) -> dict[int, dict]:
    """Exactly one hash-pinned down_proj weight per block, of the registered shape."""
    hidden, inter = cell.cell["model"]["hidden_dim"], cell.cell["model"]["intermediate_dim"]
    by_block: dict[int, dict] = {}
    for block in cell.cell["candidates"]["blocks"]:
        import fnmatch

        hits = [t for t in listing["tensors"] if fnmatch.fnmatchcase(t["name"], tensor_pattern(block))]
        if len(hits) != 1:
            raise HarnessError("TENSOR_RESOLUTION", f"block {block}: expected one down_proj weight, found {len(hits)}")
        t = hits[0]
        if t["dtype"] != cell.cell["model"]["dtype"] or list(t["shape"]) != [hidden, inter] or not t.get("sha256"):
            raise HarnessError("TENSOR_RESOLUTION", f"block {block}: {t['name']} has unexpected dtype/shape/hash")
        by_block[block] = t
    if listing.get("listing_truncated"):
        raise HarnessError("TENSOR_RESOLUTION", "tensor listing was truncated")
    return by_block


def listing_binding(listing: dict) -> dict:
    files = {f["name"]: f.get("sha256") for f in listing["files"]}
    index_sha = listing.get("index_sha256")
    if index_sha is None and len(files) == 1:
        # The engine's index-or-file binding uses the sole shard hash for
        # unindexed checkpoints. Production Qwen uses its explicit index hash.
        index_sha = next(iter(files.values()))
    if not files or not index_sha or any(not v for v in files.values()):
        raise HarnessError("BINDING", "listing lacks index/file hashes (hash_files must be true)")
    return {"index_sha256": index_sha, "files_sha256": files}


def dots_request(cell: Cell, layout: Layout, target: dict, block: int, c_hat_ref: str, c_hat_sha: str) -> dict:
    """Dot(c_hat, W[:, j]) for every column j of one block: 9216 numbers, bounded."""
    cols = int(target["shape"][1])
    return {
        "schema_version": INSPECT_SCHEMA,
        "checkpoint": layout.ref("base_model", shared=True),
        "max_listed_tensors": 4,
        "max_output_values": cols,
        "max_tensor_bytes": int(target["nbytes"]) + 1,
        "projections": [{
            "id": f"col_dots_b{block}", "tensor": target["name"], "axis": "cols", "kind": "dot",
            "include_norms": False,
            "vector": {"direction_json": {"path": c_hat_ref, "sha256": c_hat_sha}},
        }],
    }


def read_dots(report: dict, block: int, target: dict) -> np.ndarray:
    proj = next((p for p in report.get("projections", []) if p["id"] == f"col_dots_b{block}"), None)
    if proj is None:
        raise HarnessError("DOTS", f"missing col_dots_b{block}")
    if proj["tensor_sha256"] != target["sha256"] or proj["tensor"] != target["name"]:
        raise HarnessError("DOTS", "dots were read from a tensor that differs from the pinned listing")
    if proj["indices"] != "all":
        raise HarnessError("DOTS", "dots must cover every column")
    values = np.asarray(proj["values"], dtype=np.float64)
    if values.shape != (int(target["shape"][1]),) or not np.isfinite(values).all():
        raise HarnessError("DOTS", "dots have the wrong shape or are non-finite")
    return values


# ---------------------------------------------------------------------------
# proposals
# ---------------------------------------------------------------------------

@dataclass
class Proposal:
    cand_id: str
    block: int
    scale: float
    tensor: str
    columns: list[int]
    spec_path: Path | None = None
    payload_path: Path | None = None
    spec_sha256: str | None = None
    payload_sha256: str | None = None
    spec: dict = field(default_factory=dict)


def candidate_id(block: int, scale: float) -> str:
    return f"b{block}_s{scale:g}"


def plan_proposals(cell: Cell, rankings: dict[int, dict]) -> list[tuple[int, float, list[int]]]:
    """Blocks ascending x scales ascending; blocks with <32 positives supply none."""
    cand = cell.cell["candidates"]
    plan = []
    for block in sorted(cand["blocks"]):
        rk = rankings[block]
        if not rk["eligible"]:
            continue
        if len(rk["columns"]) != cand["columns"]:
            raise HarnessError("RANKING", f"block {block} ranking has {len(rk['columns'])} columns")
        for scale in sorted(cand["scales"]):
            plan.append((block, float(scale), list(rk["columns"])))
    if len(plan) > cand["max_candidates"]:
        raise HarnessError("PROPOSAL_CAP", f"{len(plan)} proposals exceed the registered cap {cand['max_candidates']}")
    return plan


def make_spec(cell: Cell, layout: Layout, *, dir_rel: str, tensor: dict, binding: dict, scale: float,
              columns: list[int], payload_sha: str, description: str) -> dict:
    b = cell.cell["candidates"]["budget"]
    return {
        "schema_version": PATCH_SCHEMA,
        "description": description,
        "base": {
            "model_id": cell.cell["model"]["repo"], "revision": cell.revision,
            "checkpoint": layout.ref("base_model", shared=True),
            "index_sha256": binding["index_sha256"], "files_sha256": binding["files_sha256"],
            "allow_symlinked_files": False,
            "runtime_prefix_rules": cell.cell["model"].get("runtime_prefix_rules", []),
            "tensors": {tensor["name"]: {"dtype": tensor["dtype"], "shape": list(tensor["shape"]),
                                         "sha256": tensor["sha256"]}},
        },
        "budget": {
            "allowed_tensors": [tensor["name"]],
            "max_modified_tensors": int(b["max_modified_tensors"]),
            "max_modified_entries": int(b["max_modified_entries"]),
            "max_relative_frobenius": float(b["max_relative_frobenius"]),
        },
        "payload": {"path": layout.ref(f"{dir_rel}/payload.safetensors", shared=True), "sha256": payload_sha},
        "operations": [{"id": "amplify", "tensor": tensor["name"], "op": "add_rank_one",
                        "scale": float(scale), "cols": [int(c) for c in columns],
                        "arrays": {"u": "u", "v": "v"}}],
    }


def write_payload(path: Path, u: np.ndarray, v: np.ndarray) -> str:
    from safetensors.numpy import save_file

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    save_file({"u": np.ascontiguousarray(u, dtype=np.float64), "v": np.ascontiguousarray(v, dtype=np.float64)}, str(tmp))
    tmp.replace(path)
    return sha256_file(path)


def build_proposal_files(cell: Cell, layout: Layout, *, c_hat: np.ndarray, targets: dict[int, dict],
                         binding: dict, dots: dict[int, np.ndarray], rankings: dict[int, dict]) -> list[Proposal]:
    out = []
    for block, scale, columns in plan_proposals(cell, rankings):
        cid = candidate_id(block, scale)
        rel = f"patches/{cid}"
        v = dots[block][columns]
        payload_path = layout.local(f"{rel}/payload.safetensors", shared=True)
        payload_sha = write_payload(payload_path, c_hat, v)
        spec = make_spec(cell, layout, dir_rel=rel, tensor=targets[block], binding=binding, scale=scale,
                         columns=columns, payload_sha=payload_sha,
                         description=f"native column amplification candidate {cid}")
        spec_path = layout.local(f"{rel}/spec.yaml", shared=True)
        spec_sha = write_yaml(spec_path, spec)
        out.append(Proposal(cid, block, scale, targets[block]["name"], columns, spec_path, payload_path,
                            spec_sha, payload_sha, spec))
    return out


# ---------------------------------------------------------------------------
# validation receipts
# ---------------------------------------------------------------------------

@dataclass
class Validation:
    valid: bool
    code: str | None = None
    message: str | None = None
    patch_digest: str | None = None
    entries_changed: int | None = None
    delta_frobenius: float | None = None
    relative_frobenius: float | None = None
    receipt: dict | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def parse_validation(cell: Cell, doc: dict) -> Validation:
    """Interpret a ``weights-patch --validate --json`` document; refusals become invalid."""
    if isinstance(doc, dict) and doc.get("success") is False:
        err = doc.get("error", {})
        code = str(err.get("code", "UNKNOWN"))
        normalized = code.lower().removeprefix("weights_")
        if normalized != "budget":
            raise HarnessError("INSTRUMENT_REFUSAL", f"engine refused the instrument: {code}")
        return Validation(False, code=code, message=str(err.get("message", "")))
    data = unwrap(doc)
    receipt = data.get("receipt")
    if not receipt or receipt.get("schema_version") != "mechinterp-weight-patch-receipt/v1":
        raise HarnessError("RECEIPT", "validation output carries no weight-patch receipt")
    tensors = receipt["tensors"]
    b = cell.cell["candidates"]["budget"]
    if len(tensors) != 1:
        raise HarnessError("RECEIPT", "receipt does not hold exactly one targeted tensor")
    t = tensors[0]
    ok = (t["entries_changed"] <= b["max_modified_entries"] and t["relative_frobenius"] <= b["max_relative_frobenius"]
          and not receipt.get("noop") and 1 <= b["max_modified_tensors"])
    return Validation(bool(ok), None if ok else "BUDGET_LOCAL", None if ok else "receipt violates the registered budget",
                      receipt["patch_digest"], int(t["entries_changed"]), float(t["delta_frobenius"]),
                      float(t["relative_frobenius"]), receipt)


# ---------------------------------------------------------------------------
# norm-matched random controls
# ---------------------------------------------------------------------------

def orthogonal_unit(seed: int, c_hat: np.ndarray, u_d: np.ndarray) -> np.ndarray:
    """Seeded unit vector orthogonal to both c_hat and u_d (two projection passes)."""
    rng = np.random.default_rng(int(seed))
    g = rng.standard_normal(c_hat.shape[0])
    basis, _ = np.linalg.qr(np.stack([c_hat, u_d], axis=1))
    for _ in range(2):
        g = g - basis @ (basis.T @ g)
    norm = float(np.linalg.norm(g))
    if norm == 0.0:
        raise HarnessError("CONTROL", "degenerate random direction")
    r = g / norm
    if abs(float(r @ c_hat)) > 1e-9 or abs(float(r @ u_d)) > 1e-9:
        raise HarnessError("CONTROL", "random direction is not orthogonal to c_hat and u_d")
    return r


def build_control(cell: Cell, layout: Layout, *, seed: int, native: Proposal, native_delta: float,
                  c_hat: np.ndarray, u_d: np.ndarray, v: np.ndarray, tensor: dict, binding: dict,
                  validate: Callable[[Path], Validation]) -> dict:
    """Same block/columns/coefficients as native; seeded orthogonal output vector.

    The scale starts at the native lambda and is corrected from validation
    receipts only (<= max_norm_adjustments corrections).  Any failure is
    returned as a recorded refusal; K is never reduced.
    """
    ctl = cell.cell["controls"]
    tol, max_adj = float(ctl["relative_delta_norm_tolerance"]), int(ctl["max_norm_adjustments"])
    rel = f"controls/seed{seed}"
    payload_path = layout.local(f"{rel}/payload.safetensors", shared=True)
    payload_sha = write_payload(payload_path, orthogonal_unit(seed, c_hat, u_d), v)
    scale, history = float(native.scale), []
    for attempt in range(max_adj + 1):
        spec = make_spec(cell, layout, dir_rel=rel, tensor=tensor, binding=binding, scale=scale,
                         columns=native.columns, payload_sha=payload_sha,
                         description=f"norm-matched random control seed {seed} attempt {attempt}")
        spec_path = layout.local(f"{rel}/spec.yaml", shared=True)
        spec_sha = write_yaml(spec_path, spec)
        result = validate(spec_path)
        step = {"attempt": attempt, "scale": scale, "spec_sha256": spec_sha, "valid": result.valid,
                "code": result.code, "delta_frobenius": result.delta_frobenius}
        history.append(step)
        if not result.valid:
            return {"seed": seed, "status": "refused", "reason": result.code or "invalid", "history": history,
                    "target_delta_frobenius": native_delta}
        err = abs(result.delta_frobenius - native_delta) / native_delta
        step["relative_error"] = err
        if err <= tol:
            return {"seed": seed, "status": "matched", "scale": scale, "spec_path": str(spec_path),
                    "spec_sha256": spec_sha, "payload_sha256": payload_sha, "history": history,
                    "patch_digest": result.patch_digest, "delta_frobenius": result.delta_frobenius,
                    "target_delta_frobenius": native_delta, "relative_error": err}
        if result.delta_frobenius <= 0.0 or attempt == max_adj:
            break
        scale = scale * native_delta / result.delta_frobenius
    return {"seed": seed, "status": "failed_to_match", "history": history,
            "target_delta_frobenius": native_delta, "max_adjustments": max_adj}


def zero_noop_spec(cell: Cell, layout: Layout, *, native: Proposal, tensor: dict, binding: dict,
                   dir_rel: str = "parity/zero_patch") -> Path:
    """A scale-0 copy of the native patch: the engine must report ``noop`` and change no byte."""
    v = np.ones(len(native.columns), dtype=np.float64)
    u = np.zeros(cell.cell["model"]["hidden_dim"], dtype=np.float64)
    sha = write_payload(layout.local(f"{dir_rel}/payload.safetensors", shared=True), u, v)
    spec = make_spec(cell, layout, dir_rel=dir_rel, tensor=tensor, binding=binding, scale=0.0,
                     columns=native.columns, payload_sha=sha, description="zero (no-op) patch")
    path = layout.local(f"{dir_rel}/spec.yaml", shared=True)
    write_yaml(path, spec)
    return path
