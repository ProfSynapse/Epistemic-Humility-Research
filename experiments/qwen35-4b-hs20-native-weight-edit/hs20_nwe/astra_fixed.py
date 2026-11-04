"""Astra's one frozen rank-one construction: roster, factors, base-bound spec, realized audit.

Implements, without redesign, the proposal frozen in ``astra_r1.yaml``:

1. ``select_roster`` / ``prepare_roster``: deterministic 64+64 development roster.
2. ``construct``: pure float64 support / key / scale arithmetic (no search, no rescale).
3. ``emit_patch``: one base-bound engine ``add_rank_one`` spec plus a float32
   safetensors payload (create-only, hash-pinned).
4. ``audit_realized``: guards evaluated on the REALIZED edited tensor read back by
   the host, never on the ideal float64 delta. A refusal is final: no reroll.

All constants come from the proposal file. This module launches nothing, runs no
model, reads no checkpoint itself (callers supply inspected metadata and the
actual base tensor as an array) and grants no launch authority. A pass over
synthetic arrays says nothing about real-model behavior.

CLI: ``python -m hs20_nwe.astra_fixed {roster,prepare,audit} ...``
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from . import capture, weights
from .astra_capture import linear_consistency, verify_request
from .util import HarnessError, canonical_sha256, sha256_bytes, sha256_file

PROPOSAL_SCHEMA = "ehr-astra-fixed-edit/v1"
ROSTER_SCHEMA = "ehr-astra-roster/v1"
REPORT_SCHEMA = "ehr-astra-prepare-report/v1"
AUDIT_SCHEMA = "ehr-astra-realized-audit/v1"
HISTORICAL_ROLES = ("confab", "known_correct_answered")  # U (confab) then K (known-correct)
SITE = ("mlp.down_proj", "input")
UNIT_NORM_TOL = 1e-6        # validation tolerance on |c_hat| = 1, not a scientific constant
FACTOR_CHECK_TOL = 1e-9     # sanity tolerance on v.mu_U = 1 and v.mu_K = 0 in float64
RECEIPT_RTOL = 1e-6         # receipt-vs-readback agreement on delta Frobenius
TERMS = ("nominal", "full_norm", "column_norm", "known_rms")


# ---------------------------------------------------------------------------
# proposal (frozen constants)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Proposal:
    raw: dict
    sha256: str

    @property
    def patch(self) -> dict:
        return self.raw["patch"]

    @property
    def tensor(self) -> str:
        return self.patch["tensor"]

    @property
    def shape(self) -> tuple[int, int]:
        return (int(self.patch["shape"][0]), int(self.patch["shape"][1]))

    @property
    def columns(self) -> int:
        return int(self.patch["columns"])

    @property
    def sigma(self) -> float:
        return float(self.patch["sigma_c"])

    @property
    def group_size(self) -> dict[str, int]:
        return {k: int(v) for k, v in self.raw["development"]["counts"].items()}


def load_proposal(path: str | Path) -> Proposal:
    data = Path(path).read_bytes()
    raw = yaml.safe_load(data)
    if not isinstance(raw, dict) or raw.get("schema_version") != PROPOSAL_SCHEMA:
        raise HarnessError("PROPOSAL_SCHEMA", f"proposal schema must be {PROPOSAL_SCHEMA}")
    if raw.get("launch_authority") is not False:
        raise HarnessError("PROPOSAL_AUTHORITY", "proposal must declare launch_authority: false")
    p = raw.get("patch") or {}
    try:
        rows, cols = int(p["shape"][0]), int(p["shape"][1])
        ok = (p["operation"] == "add_rank_one" and int(p["variance_ddof"]) == 0 and int(p["maximum_modified_tensors"]) == 1
              and int(p["maximum_modified_entries"]) == rows * int(p["columns"]) and cols > int(p["columns"]) > 0
              and raw["model"]["dtype"] == "bfloat16" and set(raw["development"]["counts"]) == set(HISTORICAL_ROLES))
        for key in ("eta_multiplier", "q_relative_norm_min", "nominal_sigma", "full_norm_scale_margin",
                    "column_norm_scale_margin", "known_anchor_rms_sigma_max", "maximum_relative_frobenius",
                    "maximum_selected_columns_relative_frobenius", "sigma_c"):
            ok = ok and math.isfinite(float(p[key])) and float(p[key]) > 0
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise HarnessError("PROPOSAL_FIELDS", f"proposal lacks a required field: {exc!r}") from exc
    if not ok:
        raise HarnessError("PROPOSAL_FIELDS", "proposal fields are inconsistent with the frozen construction")
    return Proposal(raw, sha256_bytes(data))


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

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


def bf16_raw_sha256(weight: np.ndarray) -> str:
    """sha256 of the little-endian bf16 bytes of an array whose values are exactly bf16.

    This is the engine's tensor-hash convention (raw dtype bytes, row-major), so a
    caller-supplied float array can be tied to the pinned base tensor hash.
    """
    w = np.ascontiguousarray(weight, dtype=np.float32)
    bits = w.view(np.uint32)
    if (bits & np.uint32(0xFFFF)).any():
        raise HarnessError("NOT_BF16", "array holds values that are not exactly representable in bfloat16")
    return sha256_bytes((bits >> np.uint32(16)).astype("<u2").tobytes())


# ---------------------------------------------------------------------------
# 1. development roster
# ---------------------------------------------------------------------------

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


def roster_digest(keys: dict[str, list[str]]) -> str:
    return canonical_sha256({role: keys[role] for role in HISTORICAL_ROLES})


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


# ---------------------------------------------------------------------------
# capture reading (reuses the hash-checked, manifest-only reader)
# ---------------------------------------------------------------------------

def load_group_activations(directory: Path, u_keys: Sequence[str], k_keys: Sequence[str], *, block: int,
                           hidden_state: int, family: str = "anchor", require_output: bool = False) -> dict:
    """Down-proj inputs for the ordered U and K roster rows from a completed, hash-pinned capture."""
    directory = Path(directory)
    manifest = capture.load_manifest(directory)
    if manifest.get("forward_only") is not True:
        raise HarnessError("CAPTURE_MODE", "capture manifest is not forward-only")
    capture.check_rows_covered(manifest, list(u_keys) + list(k_keys))
    by_key = {r["row_key"]: r for r in manifest["rows"]}
    sites = [(block, SITE[0], SITE[1])]
    if require_output:
        sites.append((block, SITE[0], "output"))
    key = capture.site_key(block, SITE[0], SITE[1])
    files = []
    outputs = []

    def read(keys: Sequence[str]) -> np.ndarray:
        out = []
        for k in keys:
            rec = by_key[k]
            row = capture.read_row(directory, rec, hidden_state=hidden_state, sites=sites, family=family)
            out.append(row["sites"][key])
            if require_output:
                outputs.append(row["sites"][capture.site_key(block, SITE[0], "output")])
            files.append((k, rec["capture_files"][family]["sha256"], rec["site_captures"][family]["sha256"]))
        return np.stack(out)

    result = {"U": read(u_keys), "K": read(k_keys),
            "manifest_sha256": sha256_file(directory / "manifest.json"),
            "capture_files_digest": canonical_sha256(sorted(files))}
    if require_output:
        result["outputs"] = np.stack(outputs)
    return result


# ---------------------------------------------------------------------------
# 2. pure numerical constructor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Construction:
    columns: list[int]
    scores: list[float]
    eta: float
    c: np.ndarray            # float64 unit output direction
    v: np.ndarray            # float64 key on the support
    alpha: float
    limiting: str
    caps: dict[str, float | None]
    norms: dict[str, float]
    ideal: dict[str, float]
    sigma: float
    shape: tuple[int, int]

    def report(self) -> dict:
        return {"columns": self.columns, "support_scores": self.scores, "eta": self.eta, "alpha": self.alpha,
                "limiting_term": self.limiting, "caps": self.caps, "norms": self.norms, "sigma": self.sigma,
                "ideal_float64_not_evidence": self.ideal, "v": [float(x) for x in self.v], "shape": list(self.shape)}


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


def construct(U: np.ndarray, K: np.ndarray, c_hat: np.ndarray, W: np.ndarray, proposal: Proposal, *,
              u_keys: Sequence[str], k_keys: Sequence[str], expected_shape: tuple[int, int] | None = None,
              expected_group_size: dict[str, int] | None = None) -> Construction:
    """Astra's support / key / single scale. Float64 throughout; no search, no rescale, no fallback.

    ``expected_shape`` / ``expected_group_size`` default to None so factor math can be unit-tested on
    smaller declared shapes; production callers pass the registered values.
    """
    p = proposal.patch
    U, K = _finite_array("U", U, 2), _finite_array("K", K, 2)
    W, c = _finite_array("W", W, 2), _finite_array("c_hat", c_hat, 1)
    u_keys, k_keys = list(u_keys), list(k_keys)
    if len(u_keys) != U.shape[0] or len(k_keys) != K.shape[0] or U.shape[0] < 1 or K.shape[0] < 1:
        raise HarnessError("INPUT_SHAPE", "group keys must match the activation rows")
    if len(set(u_keys)) != len(u_keys) or len(set(k_keys)) != len(k_keys) or set(u_keys) & set(k_keys):
        raise HarnessError("GROUPS", "U and K must be duplicate-free and disjoint")
    if expected_group_size and (U.shape[0], K.shape[0]) != (expected_group_size["confab"], expected_group_size["known_correct_answered"]):
        raise HarnessError("GROUPS", "group sizes differ from the registered development counts")
    if U.shape[1] != K.shape[1] or U.shape[1] != W.shape[1] or c.shape[0] != W.shape[0]:
        raise HarnessError("INPUT_SHAPE", "U, K, c_hat and W shapes are inconsistent")
    if expected_shape is not None and tuple(W.shape) != tuple(expected_shape):
        raise HarnessError("INPUT_SHAPE", f"W shape {tuple(W.shape)} differs from the registered {tuple(expected_shape)}")
    c_norm = float(np.linalg.norm(c))
    if abs(c_norm - 1.0) > UNIT_NORM_TOL:
        raise HarnessError("DEGENERATE", f"c_hat is not unit norm ({c_norm!r})")

    support, scores, eta = select_support(U, K, columns=int(p["columns"]), eta_multiplier=float(p["eta_multiplier"]))
    mu_u, mu_k = U.mean(axis=0)[support], K.mean(axis=0)[support]
    n_u = float(np.linalg.norm(mu_u))
    if n_u == 0.0:
        raise HarnessError("DEGENERATE", "norm(u) is zero")
    kk = float(mu_k @ mu_k)
    q = mu_u.copy() if kk == 0.0 else mu_u - mu_k * (float(mu_k @ mu_u) / kk)
    n_q, qu = float(np.linalg.norm(q)), float(q @ mu_u)
    if n_q <= float(p["q_relative_norm_min"]) * n_u:
        raise HarnessError("DEGENERATE", "q is numerically collinear with the known-mean direction")
    if not (math.isfinite(qu) and qu > 0.0):
        raise HarnessError("DEGENERATE", "dot(q, u) is not positive")
    v = q / qu
    if not np.isfinite(v).all():
        raise HarnessError("DEGENERATE", "key v is non-finite")
    if abs(float(v @ mu_u) - 1.0) > FACTOR_CHECK_TOL or abs(float(v @ mu_k)) > FACTOR_CHECK_TOL * max(1.0, float(np.linalg.norm(v) * np.linalg.norm(mu_k))):
        raise HarnessError("FACTOR_CHECK", "v does not satisfy v.mu_U = 1 and v.mu_K = 0")

    sigma, n_v = float(p["sigma_c"]), float(np.linalg.norm(v))
    f_full, f_cols = float(np.linalg.norm(W)), float(np.linalg.norm(W[:, support]))
    r_k = float(np.sqrt(np.mean((K[:, support] @ v) ** 2)))
    caps: dict[str, float | None] = {
        "nominal": float(p["nominal_sigma"]) * sigma,
        "full_norm": float(p["full_norm_scale_margin"]) * f_full / n_v,
        "column_norm": float(p["column_norm_scale_margin"]) * f_cols / n_v,
        "known_rms": None if r_k == 0.0 else float(p["known_anchor_rms_sigma_max"]) * sigma / r_k,
    }
    active = {t: x for t, x in caps.items() if x is not None}
    limiting = min((t for t in TERMS if t in active), key=lambda t: active[t])  # ties: first in TERMS order
    alpha = active[limiting]
    if not (math.isfinite(alpha) and alpha > 0.0):
        raise HarnessError("DEGENERATE", "scale is not a positive finite number")
    ideal = {"mean_U_write_along_c": alpha * float(np.mean(U[:, support] @ v)),
             "mean_K_write_along_c": alpha * float(np.mean(K[:, support] @ v)),
             "rms_K_write_along_c": alpha * r_k,
             "relative_frobenius_full": alpha * n_v / f_full,
             "relative_frobenius_columns": alpha * n_v / f_cols}
    norms = {"weight_frobenius": f_full, "weight_columns_frobenius": f_cols, "v_norm": n_v, "known_rms_of_v": r_k,
             "c_norm": c_norm}
    return Construction(support, scores, eta, c, v, alpha, limiting, caps, norms, ideal, sigma, tuple(W.shape))


# ---------------------------------------------------------------------------
# 3. base-bound spec and float32 payload
# ---------------------------------------------------------------------------

def resolve_target(proposal: Proposal, listing: dict) -> tuple[dict, dict]:
    """Exactly the registered tensor, dtype, shape and full hashes from an inspected listing (no patterns)."""
    if listing.get("listing_truncated"):
        raise HarnessError("TENSOR_RESOLUTION", "tensor listing was truncated")
    binding = weights.listing_binding(listing)
    if binding["files_sha256"] != proposal.raw["model"]["files_sha256"]:
        raise HarnessError("BINDING", "inspected shard hashes differ from the registered base files")
    hits = [t for t in listing.get("tensors", []) if t.get("name") == proposal.tensor]
    if len(hits) != 1:
        raise HarnessError("TENSOR_RESOLUTION", f"expected exactly one {proposal.tensor}, found {len(hits)}")
    t = hits[0]
    sha = t.get("sha256")
    if (t.get("dtype") != proposal.raw["model"]["dtype"] or tuple(t.get("shape", ())) != proposal.shape
            or not (isinstance(sha, str) and len(sha) == 64)):
        raise HarnessError("TENSOR_RESOLUTION", "target tensor has an unexpected dtype, shape or hash")
    if t.get("file") not in binding["files_sha256"]:
        raise HarnessError("BINDING", "target tensor is not in a bound shard file")
    return t, binding


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


def emit_patch(proposal: Proposal, construction: Construction, tensor: dict, binding: dict, *, out_dir: Path,
               checkpoint_ref: str, payload_ref: str, runtime_prefix_rules: Sequence = (), export_ref: str | None = None) -> dict:
    """Create-only ``payload.safetensors`` and ``spec.yaml`` in ``out_dir``. Nothing is overwritten."""
    out_dir = Path(out_dir)
    payload_path, spec_path = out_dir / "payload.safetensors", out_dir / "spec.yaml"
    if payload_path.exists() or spec_path.exists():
        raise HarnessError("OUTPUT_EXISTS", "refusing to overwrite an existing spec or payload")
    data = payload_bytes(construction)
    spec = build_spec(proposal, construction, tensor, binding, checkpoint_ref=checkpoint_ref, payload_ref=payload_ref,
                      payload_sha=sha256_bytes(data), runtime_prefix_rules=runtime_prefix_rules, export_ref=export_ref)
    payload_sha = _create_only(payload_path, data)
    spec_sha = _create_only(spec_path, yaml.safe_dump(spec, sort_keys=False, default_flow_style=False).encode("utf-8"))
    return {"spec_path": str(spec_path), "spec_sha256": spec_sha, "payload_path": str(payload_path),
            "payload_sha256": payload_sha, "spec": spec}


# ---------------------------------------------------------------------------
# c_hat and the end-to-end prepare step
# ---------------------------------------------------------------------------

def load_c_hat(proposal: Proposal, path: Path) -> tuple[np.ndarray, str]:
    p = proposal.patch
    sha = sha256_file(path)
    if sha != p["direction_sha256"]:
        raise HarnessError("INPUT_HASH", "c_hat file sha256 differs from the registered direction")
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    c = np.asarray(doc.get("vector"), dtype=np.float64)
    if c.shape != (proposal.shape[0],) or int(doc.get("layer", -1)) != int(p["decoder_block"]):
        raise HarnessError("DIRECTION", "c_hat has the wrong length or layer")
    if not math.isclose(float(doc.get("sigma", math.nan)), proposal.sigma, rel_tol=1e-12):
        raise HarnessError("DIRECTION", "c_hat sigma differs from the registered sigma_c")
    return c, sha


def prepare(proposal: Proposal, *, roster: dict, capture_dir: Path, c_hat_path: Path, listing: dict,
            base_weight: np.ndarray, out_dir: Path, checkpoint_ref: str, payload_ref: str,
            capture_binding: Path, runtime_prefix_rules: Sequence = (), export_ref: str | None = None) -> dict:
    """Validate everything, construct, then emit spec, payload and report (create-only). Never rescales."""
    out_dir = Path(out_dir)
    report_path = out_dir / "prepare_report.json"
    if any(x.exists() for x in (report_path, out_dir / "spec.yaml", out_dir / "payload.safetensors")):
        raise HarnessError("OUTPUT_EXISTS", "refusing to overwrite an existing prepare output")
    tensor, binding = resolve_target(proposal, listing)
    c, c_sha = load_c_hat(proposal, c_hat_path)
    if tuple(np.shape(base_weight)) != proposal.shape:
        raise HarnessError("INPUT_SHAPE", "base tensor shape differs from the registered target")
    if bf16_raw_sha256(base_weight) != tensor["sha256"]:
        raise HarnessError("BASE_HASH", "supplied base tensor bytes differ from the pinned tensor sha256")
    u_keys, k_keys = roster["keys"]["confab"], roster["keys"]["known_correct_answered"]
    provenance = verify_request(proposal, capture_dir, capture_binding, list(u_keys) + list(k_keys))
    cap = load_group_activations(capture_dir, u_keys, k_keys, block=int(proposal.patch["decoder_block"]),
                                 hidden_state=int(proposal.raw["development"]["capture"]["hidden_state"]),
                                 require_output=True)
    consistency = linear_consistency(cap["U"], cap["K"], cap["outputs"], base_weight, proposal)
    con = construct(cap["U"], cap["K"], c, base_weight, proposal, u_keys=u_keys, k_keys=k_keys,
                    expected_shape=proposal.shape, expected_group_size=proposal.group_size)
    emitted = emit_patch(proposal, con, tensor, binding, out_dir=out_dir, checkpoint_ref=checkpoint_ref,
                         payload_ref=payload_ref, runtime_prefix_rules=runtime_prefix_rules, export_ref=export_ref)
    report = {"schema_version": REPORT_SCHEMA, "launch_authority": False, "proposal_sha256": proposal.sha256,
              "roster_sha256": roster["roster_sha256"], "capture_manifest_sha256": cap["manifest_sha256"],
              "capture_files_digest": cap["capture_files_digest"], "c_hat_sha256": c_sha,
              "capture_provenance": provenance, "linear_consistency": consistency,
              "tensor": {k: tensor[k] for k in ("name", "dtype", "shape", "sha256", "file")},
              "binding": binding, "spec_sha256": emitted["spec_sha256"], "payload_sha256": emitted["payload_sha256"],
              "construction": con.report(),
              "note": "Ideal float64 numbers are not evidence. Run the realized audit on the engine readback."}
    _create_only(report_path, _json_bytes(report))
    return report


# ---------------------------------------------------------------------------
# 4. realized-delta audit
# ---------------------------------------------------------------------------

def audit_realized(construction: Construction, proposal: Proposal, U: np.ndarray, K: np.ndarray, base_weight: np.ndarray,
                   edited_weight: np.ndarray, *, receipt_tensor: dict | None = None) -> dict:
    """Guards on the actual edited tensor read back by the host. Returns a report; failures are final.

    ``edited_weight`` must be the engine/host readback of the edited target tensor (exact bf16 values).
    Malformed input raises; a guard violation yields ``passed: False`` with failure codes and no retry.
    """
    p = proposal.patch
    U, K = _finite_array("U", U, 2), _finite_array("K", K, 2)
    W0, W1 = _finite_array("base_weight", base_weight, 2), _finite_array("edited_weight", edited_weight, 2)
    if W0.shape != W1.shape or tuple(W0.shape) != tuple(construction.shape):
        raise HarnessError("INPUT_SHAPE", "base, edited and construction tensor shapes must agree")
    if U.shape[1] != W0.shape[1] or K.shape[1] != W0.shape[1]:
        raise HarnessError("INPUT_SHAPE", "activations do not match the tensor input width")
    for arr in (W0, W1):
        bf16_raw_sha256(arr)  # raises NOT_BF16 for values that are not stored-dtype exact
    if not math.isclose(float(np.linalg.norm(W0)), construction.norms["weight_frobenius"], rel_tol=1e-12):
        raise HarnessError("BASE_MISMATCH", "base tensor differs from the one the construction used")
    S, c = list(construction.columns), construction.c
    D = W1 - W0
    changed = D != 0.0
    entries = int(changed.sum())
    off = changed.copy()
    off[:, S] = False
    f_full, f_cols = float(np.linalg.norm(W0)), float(np.linalg.norm(W0[:, S]))
    d_norm = float(np.linalg.norm(D))
    DS = D[:, S]
    wc = c @ DS                                   # (|S|,) c-projected row of the realized delta
    p_u, p_k = U[:, S] @ wc, K[:, S] @ wc          # c-projected writes per item
    off_u, off_k = DS @ U[:, S].T, DS @ K[:, S].T
    off_u = off_u - np.outer(c, c @ off_u)
    off_k = off_k - np.outer(c, c @ off_k)
    off_resid = float(np.linalg.norm(DS - np.outer(c, wc)))
    rel_full, rel_cols = d_norm / f_full, d_norm / f_cols
    rms_k = float(np.sqrt(np.mean(p_k ** 2)))
    limits = {"relative_frobenius_full": float(p["maximum_relative_frobenius"]),
              "relative_frobenius_columns": float(p["maximum_selected_columns_relative_frobenius"]),
              "known_rms_write": float(p["known_anchor_rms_sigma_max"]) * construction.sigma}
    used = {"relative_frobenius_full": rel_full, "relative_frobenius_columns": rel_cols, "known_rms_write": rms_k}
    failures: list[dict] = []

    def fail(code: str, **detail: Any) -> None:
        failures.append({"code": code, **detail})

    if entries == 0:
        fail("NOOP", entries_changed=0)
    if int(off.sum()):
        fail("OFF_SUPPORT", changed_off_support=int(off.sum()))
    if entries > int(p["maximum_modified_entries"]):
        fail("ENTRY_COUNT", entries_changed=entries, max=int(p["maximum_modified_entries"]))
    if rel_full > limits["relative_frobenius_full"]:
        fail("NORM_FULL", value=rel_full, max=limits["relative_frobenius_full"])
    if rel_cols > limits["relative_frobenius_columns"]:
        fail("NORM_COLUMNS", value=rel_cols, max=limits["relative_frobenius_columns"])
    if not float(np.mean(p_u)) > 0.0:
        fail("U_MEAN_NOT_POSITIVE", value=float(np.mean(p_u)))
    if rms_k > limits["known_rms_write"]:
        fail("K_RMS", value=rms_k, max=limits["known_rms_write"])
    if receipt_tensor is not None:
        ok = (receipt_tensor.get("name") == proposal.tensor and int(receipt_tensor.get("entries_changed", -1)) == entries
              and math.isclose(float(receipt_tensor.get("delta_frobenius", math.nan)), d_norm, rel_tol=RECEIPT_RTOL, abs_tol=0.0))
        if not ok:
            fail("RECEIPT_MISMATCH", receipt_entries=receipt_tensor.get("entries_changed"), readback_entries=entries)
    limiting_realized = max(limits, key=lambda k: used[k] / limits[k])
    return {
        "schema_version": AUDIT_SCHEMA, "launch_authority": False, "passed": not failures, "failures": failures,
        "entries_changed": entries, "changed_off_support": int(off.sum()), "delta_frobenius": d_norm,
        "relative_frobenius_full": rel_full, "relative_frobenius_columns": rel_cols,
        "write_along_c": {"U_mean": float(np.mean(p_u)), "U_rms": float(np.sqrt(np.mean(p_u ** 2))),
                          "K_mean": float(np.mean(p_k)), "K_rms": rms_k},
        "off_c": {"residual_frobenius": off_resid, "residual_relative_to_delta": off_resid / d_norm if d_norm else None,
                  "U_rms": float(np.sqrt(np.mean(np.sum(off_u ** 2, axis=0)))),
                  "K_rms": float(np.sqrt(np.mean(np.sum(off_k ** 2, axis=0))))},
        "limits": limits, "headroom": {k: 1.0 - used[k] / limits[k] for k in limits},
        "limiting_realized_guard": limiting_realized,
        "limiting_construction_term": construction.limiting, "alpha": construction.alpha,
        "receipt_checked": receipt_tensor is not None,
        "note": "Realized guards on host readback. A failure is final: no rescale, support change or reroll.",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_npy(path: str | Path) -> np.ndarray:
    return np.load(str(path), allow_pickle=False)


def _say(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def _cmd_audit(args: argparse.Namespace, proposal: Proposal) -> dict:
    report = json.loads(Path(args.prepare_report).read_text(encoding="utf-8"))
    if report.get("schema_version") != REPORT_SCHEMA or report.get("proposal_sha256") != proposal.sha256:
        raise HarnessError("REPORT_STALE", "prepare report is not for this proposal")
    spec_path = Path(args.spec)
    if sha256_file(spec_path) != report["spec_sha256"] or sha256_file(Path(args.payload)) != report["payload_sha256"]:
        raise HarnessError("REPORT_STALE", "spec or payload bytes differ from the prepare report")
    roster = load_roster(proposal, Path(args.roster))
    if roster["roster_sha256"] != report["roster_sha256"]:
        raise HarnessError("REPORT_STALE", "roster differs from the prepare report")
    u_keys, k_keys = roster["keys"]["confab"], roster["keys"]["known_correct_answered"]
    provenance = verify_request(proposal, Path(args.capture_dir), args.capture_binding, list(u_keys) + list(k_keys))
    if provenance != report["capture_provenance"]:
        raise HarnessError("REPORT_STALE", "capture request or journal differs from preparation")
    cap = load_group_activations(Path(args.capture_dir), u_keys, k_keys, block=int(proposal.patch["decoder_block"]),
                                 hidden_state=int(proposal.raw["development"]["capture"]["hidden_state"]),
                                 require_output=True)
    if cap["manifest_sha256"] != report["capture_manifest_sha256"] or cap["capture_files_digest"] != report["capture_files_digest"]:
        raise HarnessError("REPORT_STALE", "capture differs from the one the prepare report used")
    c, c_sha = load_c_hat(proposal, Path(args.c_hat))
    base = _load_npy(args.base_tensor_npy)
    if bf16_raw_sha256(base) != report["tensor"]["sha256"]:
        raise HarnessError("BASE_HASH", "supplied base tensor bytes differ from the pinned tensor sha256")
    if linear_consistency(cap["U"], cap["K"], cap["outputs"], base, proposal) != report["linear_consistency"]:
        raise HarnessError("REPORT_STALE", "capture linear consistency differs from preparation")
    con = construct(cap["U"], cap["K"], c, base, proposal, u_keys=u_keys, k_keys=k_keys, expected_shape=proposal.shape,
                    expected_group_size=proposal.group_size)
    if con.report() != report["construction"]:
        raise HarnessError("REPORT_STALE", "re-derived construction differs from the prepare report")
    receipt = None
    if args.receipt:
        data = weights.unwrap(json.loads(Path(args.receipt).read_text(encoding="utf-8")))
        tensors = (data.get("receipt") or data).get("tensors") or []
        if len(tensors) != 1:
            raise HarnessError("RECEIPT", "receipt does not hold exactly one targeted tensor")
        receipt = tensors[0]
    result = audit_realized(con, proposal, cap["U"], cap["K"], base, _load_npy(args.edited_tensor_npy), receipt_tensor=receipt)
    result.update({"proposal_sha256": proposal.sha256, "prepare_report_sha256": sha256_file(Path(args.prepare_report)),
                   "spec_sha256": report["spec_sha256"], "payload_sha256": report["payload_sha256"],
                   "capture_manifest_sha256": cap["manifest_sha256"], "c_hat_sha256": c_sha})
    if args.out:
        _create_only(args.out, _json_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hs20_nwe.astra_fixed", description=__doc__.split("\n\n")[0])
    parser.add_argument("--proposal", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("roster")
    r.add_argument("--fit", type=Path, required=True)
    r.add_argument("--selfaware", type=Path, required=True)
    r.add_argument("--ambigqa", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    pr = sub.add_parser("prepare")
    pr.add_argument("--roster", type=Path, required=True)
    pr.add_argument("--capture-dir", type=Path, required=True)
    pr.add_argument("--capture-binding", type=Path, required=True, help="expected capture request recorded before extraction")
    pr.add_argument("--c-hat", type=Path, required=True)
    pr.add_argument("--inspect-listing", type=Path, required=True, help="weights-inspect JSON (hash_files, hash_tensors)")
    pr.add_argument("--base-tensor-npy", type=Path, required=True, help="float32 .npy of the target tensor (exact bf16 values)")
    pr.add_argument("--checkpoint-ref", required=True)
    pr.add_argument("--payload-ref", required=True)
    pr.add_argument("--export-ref", default=None, help="export destination embedded before the spec is hash-frozen")
    pr.add_argument("--runtime-prefix-rules", type=Path, default=None, help="JSON list; default none")
    pr.add_argument("--out-dir", type=Path, required=True)
    a = sub.add_parser("audit")
    a.add_argument("--prepare-report", type=Path, required=True)
    a.add_argument("--spec", type=Path, required=True)
    a.add_argument("--payload", type=Path, required=True)
    a.add_argument("--roster", type=Path, required=True)
    a.add_argument("--capture-dir", type=Path, required=True)
    a.add_argument("--capture-binding", type=Path, required=True)
    a.add_argument("--c-hat", type=Path, required=True)
    a.add_argument("--base-tensor-npy", type=Path, required=True)
    a.add_argument("--edited-tensor-npy", type=Path, required=True, help="host readback of the edited target tensor")
    a.add_argument("--receipt", type=Path, default=None, help="weights-patch --validate JSON (optional cross-check)")
    a.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        proposal = load_proposal(args.proposal)
        if args.command == "roster":
            _say(prepare_roster(proposal, args.fit, {"selfaware": args.selfaware, "ambigqa": args.ambigqa}, args.out))
        elif args.command == "prepare":
            listing = weights.unwrap(json.loads(args.inspect_listing.read_text(encoding="utf-8")))
            rules = json.loads(args.runtime_prefix_rules.read_text(encoding="utf-8")) if args.runtime_prefix_rules else []
            rep = prepare(proposal, roster=load_roster(proposal, args.roster), capture_dir=args.capture_dir,
                          c_hat_path=args.c_hat, listing=listing, base_weight=_load_npy(args.base_tensor_npy),
                          out_dir=args.out_dir, checkpoint_ref=args.checkpoint_ref, payload_ref=args.payload_ref,
                          capture_binding=args.capture_binding,
                          runtime_prefix_rules=rules, export_ref=args.export_ref)
            _say({"spec_sha256": rep["spec_sha256"], "payload_sha256": rep["payload_sha256"],
                  "alpha": rep["construction"]["alpha"], "limiting_term": rep["construction"]["limiting_term"],
                  "columns": rep["construction"]["columns"]})
        else:
            result = _cmd_audit(args, proposal)
            _say(result)
            return 0 if result["passed"] else 3
    except HarnessError as exc:
        print(json.dumps({"error": exc.code, "message": exc.message}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
