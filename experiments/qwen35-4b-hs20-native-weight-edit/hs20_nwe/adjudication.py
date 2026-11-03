"""Blinded adjudication lane (ported mechanics of the RR3 builder/apply, composed for this cell).

Two separate, code-enforced gates:

1. **Pool commit.**  ``build_pool`` writes bare ``{opaque_id, text}`` shards and a
   draft manifest (sha256 + ordered opaque ids).  ``commit_pool`` records those
   hashes in an append-only log.  ``commit_hash`` refuses any shard whose pool is
   not committed (or whose file changed since).
2. **Graded-hash commit.**  ``commit_hash`` validates the graded file against the
   *pool file* (line count, positional opaque_id equality, exactly two keys,
   boolean values) without unblinding, then appends its sha256.  ``apply`` refuses
   to read any opaque-id -> row mapping until every shard has a committed graded
   hash, and re-verifies each hash.

The join is positional.  A shard failing CG1 is regraded once through a fresh
regrade shard (fresh ids and shuffle); a second failure voids the instrument.
Degenerate or empty text never counts as an abstention.
"""

from __future__ import annotations

import hashlib
import math
import random
import secrets
import time
from pathlib import Path

from .config import Cell, Layout
from . import commitments
from .util import (HarnessError, append_jsonl, read_json, read_jsonl, sha256_file, write_json, write_jsonl)

# ----- CG1 arithmetic (thresholds come from cell.yaml `grading`) -----------------


def cg1_shard(cell: Cell, shard_id: str, attempt: int, neg_ok: int, neg_n: int, pos_ok: int, pos_n: int) -> dict:
    g = cell.cell["grading"]
    neg = neg_ok / neg_n if neg_n else 0.0
    pos = pos_ok / pos_n if pos_n else 0.0
    floor_met = pos_n >= int(g["positive_decoys_per_shard"]) and neg_n >= int(g["negative_decoys_per_shard"])
    passed = bool(floor_met and neg >= g["per_shard_negative_agreement"] and pos >= g["per_shard_positive_agreement"])
    status = "PASS" if passed else ("VOID_TERMINAL" if attempt >= 1 + int(g["max_regrades"]) else "VOID_REGRADE")
    return {"shard_id": shard_id, "attempt": attempt, "negative_agreement": neg, "positive_agreement": pos,
            "negative_total": neg_n, "positive_total": pos_n, "positive_correct": pos_ok,
            "decoy_floor_met": floor_met, "passed": passed, "status": status}


def cg1_pooled(cell: Cell, results: list[dict]) -> dict:
    total = sum(r["positive_total"] for r in results)
    correct = sum(r["positive_correct"] for r in results)
    rate = correct / total if total else 0.0
    floor = cell.cell["grading"]["pooled_positive_agreement"]
    return {"n_shards": len(results), "positive_total": total, "positive_correct": correct,
            "positive_agreement": rate, "floor": floor, "passed": bool(total and rate >= floor)}


# ----- paths -----------------------------------------------------------------------


class Pool:
    def __init__(self, layout: Layout):
        self.layout = layout
        self.root = layout.local("grading", shared=True)
        self.shards = self.root / "shards"
        self.manifest = self.root / "pool_manifest.json"
        self.salt = self.root / "pool_salt.private"
        self.pool_commits = self.root / "pool_commit.log.jsonl"
        self.graded_commits = self.root / "graded_commit.log.jsonl"
        self.spot = self.root / "spot_check.json"
        self.applied = self.root / "adjudication_applied.jsonl"
        self.report = self.root / "adjudication_report.json"

    def pool_file(self, shard_id: str) -> Path:
        return self.shards / f"{shard_id}.jsonl"

    def idmap_file(self, shard_id: str) -> Path:
        return self.shards / f"{shard_id}.idmap.private.jsonl"


def _log(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


# ----- candidates and decoys ------------------------------------------------------


def core_items(records_by_job: dict[str, list[dict]], graded_by_job: dict[str, list[dict]]) -> list[dict]:
    """Every detector-v2-negative row of every scored arm, both populations."""
    items = []
    for job_id in sorted(records_by_job):
        text = {r["row_key"]: r.get("answer_text", "") for r in records_by_job[job_id]}
        for g in sorted(graded_by_job[job_id], key=lambda r: r["row_key"]):
            if not g["refused_v2"]:
                items.append({"kind": "core", "arm": job_id, "row_key": g["row_key"], "text": text[g["row_key"]]})
    return items


def decoy_pools(cell: Cell, decoy_records: list[dict], decoy_graded: list[dict]) -> dict[str, list[dict]]:
    """Unambiguous decoys from the reserved FIT-L baseline generations (never scored)."""
    text = {r["row_key"]: r.get("answer_text", "") for r in decoy_records}
    pos, neg = [], []
    for g in sorted(decoy_graded, key=lambda r: r["row_key"]):
        base = {"arm": "decoy", "row_key": g["row_key"], "text": text[g["row_key"]]}
        if g["role"] == "unknown_refused" and g["refused_v2"] and g["well_formed"] and not g["degenerate"]:
            pos.append({**base, "kind": "decoy_pos"})
        elif g["role"] == "known_correct" and g["correct"] and not g["refused_v2"] and g["well_formed"] and not g["degenerate"]:
            neg.append({**base, "kind": "decoy_neg"})
    need = max(int(cell.cell["grading"]["positive_decoys_per_shard"]), int(cell.cell["grading"]["negative_decoys_per_shard"]))
    if len(pos) < int(cell.cell["grading"]["positive_decoys_per_shard"]) or len(neg) < int(cell.cell["grading"]["negative_decoys_per_shard"]):
        raise HarnessError("DECOY_FLOOR", f"unambiguous decoys: {len(pos)} positive, {len(neg)} negative; "
                           f"need {need} of each before grading (instrument failure)")
    return {"pos": pos, "neg": neg}


def _slices(items: list, n: int) -> list[list]:
    base, extra = divmod(len(items), n)
    out, i = [], 0
    for k in range(n):
        take = base + (1 if k < extra else 0)
        out.append(items[i:i + take])
        i += take
    return out


def opaque_id(salt: str, shard_id: str, item: dict) -> str:
    payload = f"{salt}:{shard_id}:{item['kind']}:{item['arm']}:{item['row_key']}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _shard_rows(cell: Cell, shard_id: str, salt: str, items: list[dict], seed: int, salt_index: int) -> tuple[list, list]:
    shuffled = list(items)
    random.Random(f"{seed}:{salt_index}:{shard_id}").shuffle(shuffled)
    pool, idmap, seen = [], [], set()
    for it in shuffled:
        oid = opaque_id(salt, shard_id, it)
        if oid in seen:
            raise HarnessError("POOL_ID_COLLISION", f"opaque id collision in {shard_id}")
        seen.add(oid)
        pool.append({"opaque_id": oid, "text": it["text"]})
        idmap.append({"opaque_id": oid, "kind": it["kind"], "arm": it["arm"], "row_key": it["row_key"]})
    return pool, idmap


def build_pool(cell: Cell, layout: Layout, cores: list[dict], decoys: dict[str, list[dict]], *, salt: str | None = None) -> dict:
    pool = Pool(layout)
    if pool.pool_commits.exists():
        raise HarnessError("POOL_COMMITTED", "a pool is already committed; it cannot be rebuilt")
    g = cell.cell["grading"]
    if not cores:
        raise HarnessError("POOL_EMPTY", "no detector-negative rows to adjudicate")
    if salt is None:
        salt = pool.salt.read_text().strip() if pool.salt.exists() else secrets.token_hex(32)
    pool.root.mkdir(parents=True, exist_ok=True)
    pool.salt.write_text(salt + "\n", encoding="utf-8")
    n_shards = math.ceil(len(cores) / int(g["target_candidates_per_shard"]))
    ordered = sorted(cores, key=lambda r: (r["arm"], r["row_key"]))
    random.Random(f"{g['pool_seed']}:cores").shuffle(ordered)
    chunks = _slices(ordered, n_shards)
    entries = []
    for idx, chunk in enumerate(chunks):
        shard_id = f"shard_{idx:03d}"
        rng = random.Random(f"{g['pool_seed']}:decoys:{shard_id}")
        pos = rng.sample(decoys["pos"], int(g["positive_decoys_per_shard"]))
        neg = rng.sample(decoys["neg"], int(g["negative_decoys_per_shard"]))
        rows, idmap = _shard_rows(cell, shard_id, salt, chunk + pos + neg, int(g["pool_seed"]), idx)
        write_jsonl(pool.pool_file(shard_id), rows)
        write_jsonl(pool.idmap_file(shard_id), idmap)
        entries.append(_manifest_entry(pool, shard_id, "primary", None, 1, len(chunk), len(pos), len(neg)))
    manifest = {"schema_version": "hs20-nwe-pool-manifest/v1", **cell.stamp(), "pool_seed": g["pool_seed"],
                "salt_sha256": hashlib.sha256(salt.encode()).hexdigest(), "n_candidates": len(cores),
                "shards": entries}
    write_json(pool.manifest, manifest)
    return manifest


def _manifest_entry(pool: Pool, shard_id: str, kind: str, regrade_of: str | None, attempt: int,
                    n_core: int, n_pos: int, n_neg: int) -> dict:
    rows = read_jsonl(pool.pool_file(shard_id))
    ids = [r["opaque_id"] for r in rows]
    return {"shard_id": shard_id, "kind": kind, "regrade_of": regrade_of, "attempt": attempt,
            "pool_sha256": sha256_file(pool.pool_file(shard_id)), "row_count": len(rows),
            "ordered_opaque_ids": ids, "n_core": n_core, "n_decoy_positive": n_pos, "n_decoy_negative": n_neg}


# ----- gate 1: pool commit ---------------------------------------------------------


def commit_pool(layout: Layout) -> dict:
    pool = Pool(layout)
    manifest = read_json(pool.manifest)
    committed = {e["shard_id"] for e in _log(pool.pool_commits)}
    added = []
    for entry in manifest["shards"]:
        if entry["shard_id"] in committed:
            continue
        path = pool.pool_file(entry["shard_id"])
        if sha256_file(path) != entry["pool_sha256"]:
            raise HarnessError("POOL_DRIFT", f"{entry['shard_id']} pool file differs from the draft manifest")
        ids = [r["opaque_id"] for r in read_jsonl(path)]
        if ids != entry["ordered_opaque_ids"]:
            raise HarnessError("POOL_DRIFT", f"{entry['shard_id']} opaque id order differs from the manifest")
        append_jsonl(pool.pool_commits, {"shard_id": entry["shard_id"], "pool_sha256": entry["pool_sha256"],
                                         "ordered_ids_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
                                         "row_count": entry["row_count"], "ts": time.time()})
        added.append(entry["shard_id"])
    path = commitments.export(layout, "adjudication_pool_manifest.json", manifest)
    return {"committed_now": added, "committed_total": len(committed) + len(added),
            "public_manifest": str(path), "git_commit_required": True}


def _require_pool_committed(pool: Pool, shard_id: str) -> dict:
    entry = next((e for e in _log(pool.pool_commits) if e["shard_id"] == shard_id), None)
    if entry is None:
        raise HarnessError("POOL_NOT_COMMITTED", f"{shard_id}: pool hashes and ordered ids were not committed before grading")
    commitments.require_git(pool.layout, "adjudication_pool_manifest.json", read_json(pool.manifest))
    if sha256_file(pool.pool_file(shard_id)) != entry["pool_sha256"]:
        raise HarnessError("POOL_DRIFT", f"{shard_id}: pool file changed after its commit")
    return entry


# ----- gate 2: graded-hash commit ---------------------------------------------------


def check_graded_shape(pool_rows: list[dict], graded: list[dict]) -> None:
    if len(graded) != len(pool_rows):
        raise HarnessError("GRADED_SHAPE", f"graded file has {len(graded)} lines, pool has {len(pool_rows)}")
    for i, (g, p) in enumerate(zip(graded, pool_rows)):
        if set(g) != {"opaque_id", "is_abstention"}:
            raise HarnessError("GRADED_SHAPE", f"line {i}: exactly opaque_id and is_abstention are required")
        if not isinstance(g["is_abstention"], bool):
            raise HarnessError("GRADED_SHAPE", f"line {i}: is_abstention must be boolean")
        if g["opaque_id"] != p["opaque_id"]:
            raise HarnessError("GRADED_ORDER", f"line {i}: opaque_id differs from the pool (reordered/missing/extra)")


def commit_hash(layout: Layout, shard_id: str, graded_file: Path) -> dict:
    pool = Pool(layout)
    _require_pool_committed(pool, shard_id)
    graded_file = Path(graded_file)
    if not graded_file.is_file():
        raise HarnessError("GRADED_MISSING", f"graded file not found: {graded_file}")
    check_graded_shape(read_jsonl(pool.pool_file(shard_id)), read_jsonl(graded_file))
    digest = sha256_file(graded_file)
    log = _log(pool.graded_commits)
    if any(e["shard_id"] == shard_id and e["graded_sha256"] == digest for e in log):
        return {"shard_id": shard_id, "graded_sha256": digest, "already_committed": True}
    manifest = read_json(pool.manifest)
    attempt = next(e["attempt"] for e in manifest["shards"] if e["shard_id"] == shard_id)
    if any(e["shard_id"] == shard_id for e in log):
        raise HarnessError("GRADED_RECOMMIT", f"{shard_id} already has a different committed graded hash; regrade via a regrade shard")
    append_jsonl(pool.graded_commits, {"shard_id": shard_id, "graded_sha256": digest, "file_name": graded_file.name,
                                       "attempt": attempt, "ts": time.time()})
    commitments.export(layout, "adjudication_graded_manifest.json", _graded_public(pool))
    return {"shard_id": shard_id, "graded_sha256": digest, "already_committed": False}


def _graded_public(pool: Pool) -> dict:
    manifest = read_json(pool.manifest)
    pools = {entry["shard_id"]: entry["pool_sha256"] for entry in manifest["shards"]}
    return {"schema_version": "hs20-nwe-graded-commitment/v1",
            "cell_sha256": manifest["cell_sha256"], "gates_sha256": manifest["gates_sha256"],
            "shards": [{"shard_id": entry["shard_id"], "graded_sha256": entry["graded_sha256"],
                        "attempt": entry["attempt"], "pool_sha256": pools[entry["shard_id"]]}
                       for entry in _log(pool.graded_commits)]}


def _require_graded_committed(pool: Pool, shard_id: str, graded_file: Path) -> list[dict]:
    digest = sha256_file(graded_file)
    if not any(e["shard_id"] == shard_id and e["graded_sha256"] == digest for e in _log(pool.graded_commits)):
        raise HarnessError("UNBLINDING_REFUSED", f"{shard_id}: graded file hash was not committed before unblinding")
    commitments.require_git(pool.layout, "adjudication_graded_manifest.json", _graded_public(pool))
    return read_jsonl(graded_file)


# ----- unblinding, CG1, regrade -----------------------------------------------------


def _evaluate(cell: Cell, pool: Pool, shard_id: str, attempt: int, graded_file: Path) -> dict:
    _require_pool_committed(pool, shard_id)
    graded = _require_graded_committed(pool, shard_id, graded_file)
    pool_rows = read_jsonl(pool.pool_file(shard_id))
    check_graded_shape(pool_rows, graded)
    idmap = read_jsonl(pool.idmap_file(shard_id))
    if [m["opaque_id"] for m in idmap] != [p["opaque_id"] for p in pool_rows]:
        raise HarnessError("IDMAP_MISMATCH", f"{shard_id}: id map and pool disagree")
    pairs = [(m, g["is_abstention"]) for m, g in zip(idmap, graded)]
    neg = [v for m, v in pairs if m["kind"] == "decoy_neg"]
    pos = [v for m, v in pairs if m["kind"] == "decoy_pos"]
    result = cg1_shard(cell, shard_id, attempt, sum(1 for v in neg if v is False), len(neg),
                       sum(1 for v in pos if v is True), len(pos))
    return {"cg1": result, "pairs": pairs}


def build_regrade(cell: Cell, layout: Layout, shard_id: str, graded_file: Path) -> dict:
    """Fresh ids and shuffle for the same items of a CG1-failed shard (one regrade only)."""
    pool = Pool(layout)
    manifest = read_json(pool.manifest)
    primary = next((e for e in manifest["shards"] if e["shard_id"] == shard_id and e["kind"] == "primary"), None)
    if primary is None:
        raise HarnessError("REGRADE", f"{shard_id} is not a primary shard")
    if any(e["regrade_of"] == shard_id for e in manifest["shards"]):
        raise HarnessError("REGRADE", f"{shard_id} already has its one regrade")
    ev = _evaluate(cell, pool, shard_id, 1, graded_file)
    if ev["cg1"]["passed"]:
        raise HarnessError("REGRADE", f"{shard_id} passed CG1; no regrade is allowed")
    idmap = read_jsonl(pool.idmap_file(shard_id))
    text = {r["opaque_id"]: r["text"] for r in read_jsonl(pool.pool_file(shard_id))}
    items = [{"kind": m["kind"], "arm": m["arm"], "row_key": m["row_key"], "text": text[m["opaque_id"]]} for m in idmap]
    new_id = f"{shard_id}_regrade"
    salt = pool.salt.read_text().strip()
    rows, new_map = _shard_rows(cell, new_id, salt, items, int(cell.cell["grading"]["pool_seed"]), 9000)
    write_jsonl(pool.pool_file(new_id), rows)
    write_jsonl(pool.idmap_file(new_id), new_map)
    entry = _manifest_entry(pool, new_id, "regrade", shard_id, 2, primary["n_core"],
                            primary["n_decoy_positive"], primary["n_decoy_negative"])
    manifest["shards"].append(entry)
    write_json(pool.manifest, manifest)
    return {"regrade_shard": new_id, "first_attempt_cg1": ev["cg1"]}


def record_spot_check(cell: Cell, layout: Layout, decisions: list[dict], *, accepted: bool | None = None, note: str = "") -> dict:
    n = int(cell.cell["grading"]["lead_spot_check_n"])
    if len(decisions) != n or len({d["opaque_id"] for d in decisions}) != n:
        raise HarnessError("SPOT_CHECK", f"the lead spot-check must hold exactly {n} distinct opaque ids")
    pack = read_jsonl(Pool(layout).root / "spot_pack.private.jsonl")
    labels = {entry["opaque_id"]: entry["grader_label"] for entry in pack}
    if set(labels) != {d["opaque_id"] for d in decisions} or any(type(d.get("lead_is_abstention")) is not bool for d in decisions):
        raise HarnessError("SPOT_CHECK", "lead decisions must match the frozen blinded spot pack")
    agreement = sum(d["lead_is_abstention"] == labels[d["opaque_id"]] for d in decisions) / n
    passed = agreement >= float(cell.cell["grading"]["lead_spot_min_agreement"])
    if accepted is not None and accepted != passed:
        raise HarnessError("SPOT_CHECK", "an operator flag cannot override the registered agreement rule")
    record = {"n": n, "accepted": passed, "agreement": agreement, "note": note,
              "pack_sha256": sha256_file(Pool(layout).root / "spot_pack.private.jsonl"),
              "opaque_ids": sorted(d["opaque_id"] for d in decisions),
              "n_lead_abstention": sum(1 for d in decisions if d.get("lead_is_abstention") is True), "ts": time.time()}
    write_json(Pool(layout).spot, record)
    return record


def spot_check_pack(cell: Cell, layout: Layout, graded_files: dict[str, Path]) -> list[dict]:
    """30 blinded {opaque_id, text, grader_label} items for the lead; no arm/role/mapping."""
    pool = Pool(layout)
    n = int(cell.cell["grading"]["lead_spot_check_n"])
    rows = []
    for shard_id, path in sorted(graded_files.items()):
        graded = _require_graded_committed(pool, shard_id, path)
        for p, g in zip(read_jsonl(pool.pool_file(shard_id)), graded):
            rows.append({"shard_id": shard_id, "opaque_id": p["opaque_id"], "text": p["text"],
                         "grader_label": g["is_abstention"]})
    random.Random(f"{cell.cell['grading']['pool_seed']}:spot").shuffle(rows)
    picked = rows[:n]
    write_jsonl(pool.root / "spot_pack.private.jsonl", picked)
    return picked


def apply(cell: Cell, layout: Layout, grading: dict[str, str]) -> dict:
    """Unblind only after every shard's graded hash is committed. ``grading`` maps shard_id -> graded file."""
    pool = Pool(layout)
    manifest = read_json(pool.manifest)
    spot = read_json(pool.spot) if pool.spot.exists() else None
    if spot is None or spot.get("n") != int(cell.cell["grading"]["lead_spot_check_n"]):
        raise HarnessError("SPOT_CHECK_REQUIRED", "an accepted lead spot-check of the registered size must be recorded first")
    if spot.get("pack_sha256") != sha256_file(pool.root / "spot_pack.private.jsonl"):
        raise HarnessError("SPOT_CHECK", "the blinded spot pack changed after review")
    if not spot.get("accepted"):
        report = {"instrument_valid": False, "reason": "registered_spot_agreement_floor_failed", "spot": spot}
        write_json(pool.report, report)
        return report
    primaries = [e for e in manifest["shards"] if e["kind"] == "primary"]
    regrades = {e["regrade_of"]: e for e in manifest["shards"] if e["kind"] == "regrade"}
    # Every shard that will be read must already have a committed graded hash (checked before ANY id map is read).
    for sid in [e["shard_id"] for e in primaries]:
        if sid not in grading:
            raise HarnessError("UNBLINDING_REFUSED", f"no graded file supplied for {sid}")
        _require_graded_committed(pool, sid, Path(grading[sid]))
    for sid in [e["shard_id"] for e in regrades.values()]:
        if sid not in grading:
            raise HarnessError("UNBLINDING_REFUSED", f"no graded file supplied for regrade shard {sid}")
        _require_graded_committed(pool, sid, Path(grading[sid]))
    finals, core_pairs, trail = [], [], []
    voided = False
    for entry in primaries:
        sid = entry["shard_id"]
        first = _evaluate(cell, pool, sid, 1, Path(grading[sid]))
        trail.append(first["cg1"])
        final = first
        if not first["cg1"]["passed"]:
            rg = regrades.get(sid)
            if rg is None:
                trail[-1]["status"] = "VOID_REGRADE"
                finals.append(first["cg1"])
                voided = True
                continue
            final = _evaluate(cell, pool, rg["shard_id"], 2, Path(grading[rg["shard_id"]]))
            trail.append(final["cg1"])
        finals.append(final["cg1"])
        if final["cg1"]["passed"]:
            core_pairs.extend((m, v) for m, v in final["pairs"] if m["kind"] == "core")
        else:
            voided = True
    pooled = cg1_pooled(cell, [f for f in finals if f["passed"]])
    pending_regrade = [f["shard_id"] for f in finals if f["status"] == "VOID_REGRADE"]
    valid = bool(not voided and pooled["passed"] and not pending_regrade)
    report = {"schema_version": "hs20-nwe-adjudication-report/v1", **cell.stamp(), "instrument_valid": valid,
              "pending_regrade": pending_regrade, "terminal_void": bool(voided and not pending_regrade),
              "shards": trail, "pooled_positive": pooled, "n_core_credited": len(core_pairs) if valid else 0,
              "spot_check_sha256": sha256_file(pool.spot)}
    write_json(pool.report, report)
    if valid:
        write_jsonl(pool.applied, [{"arm": m["arm"], "row_key": m["row_key"], "adjudicated_abstention": bool(v)}
                                   for m, v in core_pairs])
    elif pool.applied.exists():
        pool.applied.unlink()
    return report


def load_applied(layout: Layout) -> dict[tuple[str, str], bool]:
    pool = Pool(layout)
    report = read_json(pool.report) if pool.report.exists() else None
    if not report or not report.get("instrument_valid"):
        raise HarnessError("INSTRUMENT_VOID", "adjudication is missing or the instrument is void")
    out: dict[tuple[str, str], bool] = {}
    for r in read_jsonl(pool.applied):
        key = (r["arm"], r["row_key"])
        if key in out:
            raise HarnessError("APPLIED_DUP", f"duplicate adjudicated item {key}")
        out[key] = bool(r["adjudicated_abstention"])
    return out
