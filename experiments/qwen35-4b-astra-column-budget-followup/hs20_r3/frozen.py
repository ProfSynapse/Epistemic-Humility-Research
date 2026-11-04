"""Frozen function ports. See ORIGINS.json. No import of R1 or its globals."""
from __future__ import annotations
import hashlib, json, math, os, unicodedata
from pathlib import Path
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .astra_r2 import Proposal, Construction
from collections.abc import Iterable, Sequence
import numpy as np
from types import SimpleNamespace
HISTORICAL_ROLES = ("confab", "known_correct_answered")
weights = SimpleNamespace(PATCH_SCHEMA="mechinterp-weight-patch/v1")


class HarnessError(RuntimeError):
    """A refusal or stop condition. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: str | Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def canonical_sha256(obj: Any) -> str:
    return sha256_bytes(canonical_json(obj).encode("utf-8"))

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

def _finite_array(name: str, value: Any, ndim: int) -> np.ndarray:
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise HarnessError("INPUT_SHAPE", f"{name} is not numeric") from exc
    if arr.ndim != ndim:
        raise HarnessError("INPUT_SHAPE", f"{name} must be {ndim}-dimensional, got {arr.ndim}")
    if not np.isfinite(arr).all():
        raise HarnessError("INPUT_NONFINITE", f"{name} contains non-finite values")
    return arr

def normalize_question(text: str) -> str:
    """NFKC, casefold, collapse whitespace."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

def _bytes(key: str) -> bytes:
    return key.encode("utf-8")

def select_roster(fit_rows: Sequence[dict], eval_questions: dict[str, Iterable[str]], *, seed: int,
                  counts: dict[str, int]) -> dict:
    """Deterministic development roster. Returns row keys (IDs only) and count statistics.

    Per historical role: drop rows whose normalized question matches either
    evaluation surface; deduplicate by normalized question keeping the
    byte-smallest row key; byte-sort the keys; draw ``default_rng(seed)``
    permutation (a separate generator per role) and take the first ``counts[role]``.
    """
    surfaces = {name: {normalize_question(q) for q in qs} for name, qs in eval_questions.items()}
    seen_keys: set[str] = set()
    by_role: dict[str, list[tuple[str, str]]] = {role: [] for role in HISTORICAL_ROLES}
    for row in fit_rows:
        key, question, role = row.get("row_key"), row.get("question"), row.get("role")
        if not isinstance(key, str) or not key or not isinstance(question, str) or not question.strip():
            raise HarnessError("ROSTER_ROW", "a FIT row lacks a usable row_key or question")
        if key in seen_keys:
            raise HarnessError("ROSTER_DUP_KEY", "duplicate row_key in the FIT input")
        seen_keys.add(key)
        if role in by_role:
            by_role[role].append((key, normalize_question(question)))
    stats: dict[str, Any] = {}
    eligible_norms: dict[str, set[str]] = {}
    keys_by_role: dict[str, list[str]] = {}
    for role in HISTORICAL_ROLES:
        rows = by_role[role]
        excluded = {name: sum(1 for _, nq in rows if nq in qs) for name, qs in surfaces.items()}
        kept = [(k, nq) for k, nq in rows if not any(nq in qs for qs in surfaces.values())]
        best: dict[str, str] = {}
        for k, nq in kept:
            if nq not in best or _bytes(k) < _bytes(best[nq]):
                best[nq] = k
        eligible_norms[role] = set(best)
        ordered = sorted(best.values(), key=_bytes)
        stats[role] = {"fit_rows": len(rows), "excluded_by_surface": excluded,
                       "excluded_total": len(rows) - len(kept), "duplicates_removed": len(kept) - len(best),
                       "eligible_unique": len(ordered), "selected": int(counts[role])}
        keys_by_role[role] = ordered
    if eligible_norms[HISTORICAL_ROLES[0]] & eligible_norms[HISTORICAL_ROLES[1]]:
        raise HarnessError("ROSTER_CROSS_ROLE", "a normalized question appears in both historical roles")
    selected: dict[str, list[str]] = {}
    for role in HISTORICAL_ROLES:
        ordered, n = keys_by_role[role], int(counts[role])
        if len(ordered) < n:
            raise HarnessError("ROSTER_SHORT", f"{role} has {len(ordered)} eligible unique questions, need {n}")
        perm = np.random.default_rng(int(seed)).permutation(len(ordered))
        selected[role] = [ordered[int(i)] for i in perm[:n]]
    return {"keys": selected, "stats": stats}

def roster_digest(keys: dict[str, list[str]]) -> str:
    return canonical_sha256({role: keys[role] for role in HISTORICAL_ROLES})

def select_support(U: np.ndarray, K: np.ndarray, *, columns: int, eta_multiplier: float) -> tuple[list[int], list[float], float]:
    """Top standardized squared group-mean contrast; ties by ascending column index; sorted ascending."""
    allv = np.concatenate([U, K], axis=0)
    eta = float(eta_multiplier) * float(np.mean(allv ** 2))
    if not math.isfinite(eta) or eta <= 0.0:
        raise HarnessError("DEGENERATE", "eta is zero or non-finite")
    mu_u, mu_k = U.mean(axis=0), K.mean(axis=0)
    score = (mu_u - mu_k) ** 2 / (0.5 * (U.var(axis=0, ddof=0) + K.var(axis=0, ddof=0)) + eta)
    if not np.isfinite(score).all():
        raise HarnessError("INPUT_NONFINITE", "support scores are non-finite")
    if columns > score.shape[0]:
        raise HarnessError("INPUT_SHAPE", f"fewer than {columns} columns available")
    order = np.lexsort((np.arange(score.shape[0]), -score))[:columns]
    support = sorted(int(i) for i in order)
    return support, [float(score[i]) for i in support], eta

def build_spec(proposal: Proposal, construction: Construction, tensor: dict, binding: dict, *, checkpoint_ref: str,
               payload_ref: str, payload_sha: str, runtime_prefix_rules: Sequence = (), export_ref: str | None = None) -> dict:
    p = proposal.patch
    for ref in (checkpoint_ref, payload_ref):
        if not str(ref).startswith("artifact://"):
            raise HarnessError("SPEC_REF", "checkpoint and payload must be artifact:// references")
    spec = {
        "schema_version": weights.PATCH_SCHEMA,
        "description": f"{proposal.raw['proposal_id']} fixed Astra rank-one edit",
        "base": {
            "model_id": proposal.raw["model"]["repo"], "revision": proposal.raw["model"]["revision"],
            "checkpoint": checkpoint_ref, "index_sha256": binding["index_sha256"],
            "files_sha256": binding["files_sha256"], "allow_symlinked_files": False,
            "runtime_prefix_rules": list(runtime_prefix_rules),
            "tensors": {tensor["name"]: {"dtype": tensor["dtype"], "shape": list(tensor["shape"]), "sha256": tensor["sha256"]}},
        },
        "budget": {"allowed_tensors": [tensor["name"]], "max_modified_tensors": int(p["maximum_modified_tensors"]),
                   "max_modified_entries": int(p["maximum_modified_entries"]),
                   "max_relative_frobenius": float(p["maximum_relative_frobenius"])},
        "payload": {"path": payload_ref, "sha256": payload_sha},
        "operations": [{"id": "astra_r1", "tensor": tensor["name"], "op": "add_rank_one",
                        "scale": float(construction.alpha), "cols": [int(x) for x in construction.columns],
                        "arrays": {"u": "u", "v": "v"}}],
    }
    if export_ref is not None:
        if not export_ref.startswith('artifact://'):
            raise HarnessError('SPEC_REF', 'export output must be an artifact:// reference')
        spec['export'] = {'output_dir': export_ref}
    return spec

def payload_bytes(construction: Construction) -> bytes:
    """float32 safetensors factors ``u`` (= c_hat) and ``v``; serialized by the safetensors library."""
    from safetensors.numpy import save

    u32, v32 = construction.c.astype(np.float32), construction.v.astype(np.float32)
    if not (np.isfinite(u32).all() and np.isfinite(v32).all() and v32.any()):
        raise HarnessError("DEGENERATE", "float32 factors are non-finite or zero")
    return save({"u": np.ascontiguousarray(u32), "v": np.ascontiguousarray(v32)})
