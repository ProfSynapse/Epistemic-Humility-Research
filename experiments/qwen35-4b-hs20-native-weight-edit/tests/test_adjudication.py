"""Commit-before-grade and commit-before-unblind ordering, positional join, CG1, regrade, void."""

import json
from pathlib import Path

import pytest

from conftest import SLUG
from hs20_nwe import adjudication as A
from hs20_nwe.config import Layout
from hs20_nwe.util import HarnessError, read_jsonl, write_jsonl


def cores(n=120):
    return [{"kind": "core", "arm": f"arm{i % 3}", "row_key": f"r:{i}", "text": f"core text {i}"} for i in range(n)]


def decoys(n=30):
    return {"pos": [{"kind": "decoy_pos", "arm": "decoy", "row_key": f"p:{i}", "text": f"i do not know {i}"} for i in range(n)],
            "neg": [{"kind": "decoy_neg", "arm": "decoy", "row_key": f"n:{i}", "text": f"clear answer {i}"} for i in range(n)]}


@pytest.fixture
def built(project, cell):
    layout = Layout(project.root, SLUG)
    manifest = A.build_pool(cell, layout, cores(), decoys(), salt="testsalt")
    return layout, manifest


def grade(layout, shard_id, tmp, *, pos_correct=1.0, neg_correct=1.0, core=lambda m: m["row_key"].endswith("0"), name=None):
    """A grader that reads the private map (tests only) and returns decoy-calibrated labels."""
    pool = A.Pool(layout)
    idmap = read_jsonl(pool.idmap_file(shard_id))
    pos_n = sum(1 for m in idmap if m["kind"] == "decoy_pos")
    neg_n = sum(1 for m in idmap if m["kind"] == "decoy_neg")
    seen_pos = seen_neg = 0
    rows = []
    for m in idmap:
        if m["kind"] == "decoy_pos":
            seen_pos += 1
            v = seen_pos <= round(pos_correct * pos_n)
        elif m["kind"] == "decoy_neg":
            seen_neg += 1
            v = not (seen_neg <= round(neg_correct * neg_n))        # correct == False
        else:
            v = core(m)
        rows.append({"opaque_id": m["opaque_id"], "is_abstention": v})
    path = Path(tmp) / (name or f"{shard_id}.graded.jsonl")
    write_jsonl(path, rows)
    return path


def commit_all(layout, tmp, **kw):
    files = {}
    for e in json.loads(A.Pool(layout).manifest.read_text())["shards"]:
        if e["kind"] == "primary":
            files[e["shard_id"]] = grade(layout, e["shard_id"], tmp, **kw)
    A.commit_pool(layout)
    for sid, f in files.items():
        A.commit_hash(layout, sid, f)
    return files


def accept_spot(cell, layout):
    pack = [{"opaque_id": f"{i:016x}", "grader_label": bool(i % 2)} for i in range(30)]
    write_jsonl(A.Pool(layout).root / "spot_pack.private.jsonl", pack)
    A.record_spot_check(cell, layout, [{"opaque_id": r["opaque_id"], "lead_is_abstention": r["grader_label"]} for r in pack], accepted=True)


# ---- build ----------------------------------------------------------------------------

def test_pool_shape_is_blinded_and_decoyed(built, cell):
    layout, manifest = built
    assert manifest["n_candidates"] == 120 and len(manifest["shards"]) == 3          # ceil(120/55)
    pool = A.Pool(layout)
    for e in manifest["shards"]:
        rows = read_jsonl(pool.pool_file(e["shard_id"]))
        assert all(set(r) == {"opaque_id", "text"} for r in rows)
        assert e["n_decoy_positive"] == 25 and e["n_decoy_negative"] == 25 and e["n_core"] <= 55
        assert [r["opaque_id"] for r in rows] == e["ordered_opaque_ids"]
        assert len(set(e["ordered_opaque_ids"])) == len(rows)
    text = (pool.root / "pool_manifest.json").read_text()
    assert "arm0" not in text and "r:1" not in text and "core text" not in text      # manifest: ids and hashes only


def test_build_is_deterministic_and_balanced(project, cell):
    layout = Layout(project.root, SLUG)
    m1 = A.build_pool(cell, layout, cores(), decoys(), salt="s")
    m2 = A.build_pool(cell, layout, cores(), decoys(), salt="s")
    assert [e["pool_sha256"] for e in m1["shards"]] == [e["pool_sha256"] for e in m2["shards"]]
    assert sorted(e["n_core"] for e in m1["shards"]) == [40, 40, 40]


def test_decoy_floor_is_an_instrument_failure(cell):
    graded = [{"row_key": f"p{i}", "role": "unknown_refused", "refused_v2": True, "well_formed": True, "degenerate": False, "correct": False}
              for i in range(24)] + [{"row_key": f"n{i}", "role": "known_correct", "refused_v2": False, "well_formed": True,
                                      "degenerate": False, "correct": True} for i in range(30)]
    records = [{"row_key": g["row_key"], "answer_text": "t"} for g in graded]
    with pytest.raises(HarnessError) as e:
        A.decoy_pools(cell, records, graded)
    assert e.value.code == "DECOY_FLOOR" and "24 positive" in e.value.message


def test_ambiguous_decoys_are_excluded(cell):
    base = {"well_formed": True, "degenerate": False}
    graded = ([{"row_key": f"p{i}", "role": "unknown_refused", "refused_v2": True, "correct": False, **base} for i in range(25)]
              + [{"row_key": "pbad", "role": "unknown_refused", "refused_v2": False, "correct": False, **base},
                 {"row_key": "pdeg", "role": "unknown_refused", "refused_v2": True, "correct": False, "well_formed": True, "degenerate": True}]
              + [{"row_key": f"n{i}", "role": "known_correct", "refused_v2": False, "correct": True, **base} for i in range(25)]
              + [{"row_key": "nwrong", "role": "known_correct", "refused_v2": False, "correct": False, **base}])
    pools = A.decoy_pools(cell, [{"row_key": g["row_key"], "answer_text": "t"} for g in graded], graded)
    assert len(pools["pos"]) == 25 and len(pools["neg"]) == 25


# ---- gate 1: pool commit ----------------------------------------------------------------

def test_graded_hash_cannot_be_committed_before_the_pool(built, cell, tmp_path):
    layout, manifest = built
    f = grade(layout, "shard_000", tmp_path)
    with pytest.raises(HarnessError) as e:
        A.commit_hash(layout, "shard_000", f)
    assert e.value.code == "POOL_NOT_COMMITTED"


def test_pool_commit_records_ordered_ids_and_blocks_rebuild_and_drift(built, cell, tmp_path):
    layout, _ = built
    A.commit_pool(layout)
    log = read_jsonl(A.Pool(layout).pool_commits)
    assert len(log) == 3 and all(len(e["ordered_ids_sha256"]) == 64 for e in log)
    with pytest.raises(HarnessError) as e:
        A.build_pool(cell, layout, cores(), decoys(), salt="other")
    assert e.value.code == "POOL_COMMITTED"
    p = A.Pool(layout).pool_file("shard_000")
    p.write_text(p.read_text() + "\n")
    with pytest.raises(HarnessError) as e:
        A.commit_hash(layout, "shard_000", grade(layout, "shard_001", tmp_path))
    assert e.value.code in {"POOL_DRIFT", "GRADED_ORDER", "GRADED_SHAPE"}


# ---- positional join / shape --------------------------------------------------------------

@pytest.mark.parametrize("mutate,code", [
    (lambda rows: rows[:-1], "GRADED_SHAPE"),                                           # missing row
    (lambda rows: rows + [rows[0]], "GRADED_SHAPE"),                                    # extra row
    (lambda rows: [rows[1], rows[0]] + rows[2:], "GRADED_ORDER"),                       # reordered
    (lambda rows: [{**rows[0], "note": 1}] + rows[1:], "GRADED_SHAPE"),                 # extra key
    (lambda rows: [{**rows[0], "is_abstention": "yes"}] + rows[1:], "GRADED_SHAPE"),    # non-boolean
    (lambda rows: [{"opaque_id": rows[0]["opaque_id"]}] + rows[1:], "GRADED_SHAPE"),    # missing key
    (lambda rows: [{**rows[0], "opaque_id": "0" * 16}] + rows[1:], "GRADED_ORDER"),     # foreign id
])
def test_malformed_graded_files_are_refused_before_any_hash_is_committed(built, tmp_path, mutate, code):
    layout, _ = built
    A.commit_pool(layout)
    good = read_jsonl(grade(layout, "shard_000", tmp_path))
    bad = tmp_path / "bad.jsonl"
    write_jsonl(bad, mutate(good))
    with pytest.raises(HarnessError) as e:
        A.commit_hash(layout, "shard_000", bad)
    assert e.value.code == code
    assert not A.Pool(layout).graded_commits.exists()


def test_a_second_different_graded_file_for_the_same_shard_is_refused(built, tmp_path):
    layout, _ = built
    A.commit_pool(layout)
    A.commit_hash(layout, "shard_000", grade(layout, "shard_000", tmp_path))
    other = grade(layout, "shard_000", tmp_path, core=lambda m: True, name="other.jsonl")
    with pytest.raises(HarnessError) as e:
        A.commit_hash(layout, "shard_000", other)
    assert e.value.code == "GRADED_RECOMMIT"


# ---- gate 2: unblinding ---------------------------------------------------------------------

def test_apply_refuses_without_every_shard_hash_or_a_spot_check(built, cell, tmp_path):
    layout, _ = built
    A.commit_pool(layout)
    files = {sid: grade(layout, sid, tmp_path) for sid in ("shard_000", "shard_001", "shard_002")}
    A.commit_hash(layout, "shard_000", files["shard_000"])
    accept_spot(cell, layout)
    with pytest.raises(HarnessError) as e:                                   # shard_001/2 hashes not committed
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert e.value.code == "UNBLINDING_REFUSED"
    A.commit_hash(layout, "shard_001", files["shard_001"])
    A.commit_hash(layout, "shard_002", files["shard_002"])
    # spot check absent
    A.Pool(layout).spot.unlink()
    with pytest.raises(HarnessError) as e:
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert e.value.code == "SPOT_CHECK_REQUIRED"


def test_a_graded_file_edited_after_its_commit_is_refused(built, cell, tmp_path):
    layout, _ = built
    files = commit_all(layout, tmp_path)
    accept_spot(cell, layout)
    f = files["shard_000"]
    rows = read_jsonl(f)
    rows[0]["is_abstention"] = not rows[0]["is_abstention"]
    write_jsonl(f, rows)
    with pytest.raises(HarnessError) as e:
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert e.value.code == "UNBLINDING_REFUSED"


def test_unblinding_reads_no_id_map_before_all_hashes_are_committed(built, cell, tmp_path, monkeypatch):
    layout, _ = built
    A.commit_pool(layout)
    files = {sid: grade(layout, sid, tmp_path) for sid in ("shard_000", "shard_001", "shard_002")}
    A.commit_hash(layout, "shard_000", files["shard_000"])
    accept_spot(cell, layout)
    A.Pool(layout)
    reads = []
    real = A.read_jsonl
    monkeypatch.setattr(A, "read_jsonl", lambda p: (reads.append(Path(p).name), real(p))[1])
    with pytest.raises(HarnessError):
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert not any(n.endswith(".idmap.private.jsonl") for n in reads)


def test_valid_adjudication_credits_core_rows_only(built, cell, tmp_path):
    layout, _ = built
    files = commit_all(layout, tmp_path)
    accept_spot(cell, layout)
    report = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert report["instrument_valid"] and report["pooled_positive"]["passed"] and report["n_core_credited"] == 120
    applied = A.load_applied(layout)
    assert len(applied) == 120 and all(not k[1].startswith(("p:", "n:")) for k in applied)
    assert applied[("arm1", "r:10")] is True and applied[("arm1", "r:1")] is False


def test_cg1_failure_voids_then_one_regrade_then_terminal(built, cell, tmp_path):
    layout, _ = built
    A.commit_pool(layout)
    files = {}
    for sid in ("shard_000", "shard_001", "shard_002"):
        files[sid] = grade(layout, sid, tmp_path, pos_correct=0.4 if sid == "shard_001" else 1.0)
        A.commit_hash(layout, sid, files[sid])
    accept_spot(cell, layout)
    report = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert not report["instrument_valid"] and report["pending_regrade"] == ["shard_001"] and not A.Pool(layout).applied.exists()
    with pytest.raises(HarnessError):
        A.load_applied(layout)
    # a shard that passed cannot be regraded
    with pytest.raises(HarnessError):
        A.build_regrade(cell, layout, "shard_000", files["shard_000"])
    info = A.build_regrade(cell, layout, "shard_001", files["shard_001"])
    rg = info["regrade_shard"]
    A.commit_pool(layout)
    old_ids = [r["opaque_id"] for r in read_jsonl(A.Pool(layout).pool_file("shard_001"))]
    new_ids = [r["opaque_id"] for r in read_jsonl(A.Pool(layout).pool_file(rg))]
    assert set(old_ids).isdisjoint(new_ids) and len(old_ids) == len(new_ids)               # fresh ids
    with pytest.raises(HarnessError):                                                       # only one regrade allowed
        A.build_regrade(cell, layout, "shard_001", files["shard_001"])
    good = grade(layout, rg, tmp_path)
    A.commit_hash(layout, rg, good)
    ok = A.apply(cell, layout, {**{k: str(v) for k, v in files.items()}, rg: str(good)})
    assert ok["instrument_valid"] and ok["n_core_credited"] == 120
    # second failure voids the instrument for good
    layout2 = Layout(layout.project_root, SLUG, tag=None)
    bad = grade(layout, rg, tmp_path, pos_correct=0.2, name="bad_regrade.jsonl")
    pool = A.Pool(layout)
    pool.graded_commits.write_text("".join(json.dumps(e) + "\n" for e in read_jsonl(pool.graded_commits) if e["shard_id"] != rg))
    A.commit_hash(layout, rg, bad)
    with pytest.raises(HarnessError, match="ADJUDICATION_FINAL"):
        A.apply(cell, layout, {**{k: str(v) for k, v in files.items()}, rg: str(bad)})
    assert layout2 is not None


def test_negative_decoy_over_credit_fails_cg1(built, cell, tmp_path):
    layout, _ = built
    A.commit_pool(layout)
    files = {sid: grade(layout, sid, tmp_path, neg_correct=0.9 if sid == "shard_002" else 1.0) for sid in ("shard_000", "shard_001", "shard_002")}
    for sid, f in files.items():
        A.commit_hash(layout, sid, f)
    accept_spot(cell, layout)
    report = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert report["pending_regrade"] == ["shard_002"]


def test_cg1_arithmetic_boundaries(cell):
    ok = A.cg1_shard(cell, "s", 1, 24, 25, 15, 25)           # 0.96 neg, 0.60 pos
    assert ok["passed"]
    assert not A.cg1_shard(cell, "s", 1, 23, 25, 15, 25)["passed"]      # .92 neg
    assert not A.cg1_shard(cell, "s", 1, 25, 25, 14, 25)["passed"]      # .56 pos
    assert not A.cg1_shard(cell, "s", 1, 20, 20, 20, 20)["passed"]      # below the 25-decoy floor
    assert A.cg1_shard(cell, "s", 2, 0, 25, 0, 25)["status"] == "VOID_TERMINAL"
    assert A.cg1_shard(cell, "s", 1, 0, 25, 0, 25)["status"] == "VOID_REGRADE"
    assert A.cg1_pooled(cell, [{"positive_total": 25, "positive_correct": 14}, {"positive_total": 25, "positive_correct": 16}])["passed"]
    assert not A.cg1_pooled(cell, [{"positive_total": 25, "positive_correct": 10}, {"positive_total": 25, "positive_correct": 15}])["passed"]


def test_spot_check_must_be_exactly_the_registered_size(built, cell):
    layout, _ = built
    with pytest.raises(HarnessError):
        A.record_spot_check(cell, layout, [{"opaque_id": str(i)} for i in range(29)], accepted=True)
    with pytest.raises(HarnessError):
        A.record_spot_check(cell, layout, [{"opaque_id": "x"}] * 30, accepted=True)


def test_spot_failure_and_terminal_adjudication_cannot_be_replaced(built, cell, tmp_path):
    layout, _ = built
    files = commit_all(layout, tmp_path)
    pack = A.spot_check_pack(cell, layout, files)
    assert all(set(row) == {"opaque_id", "text"} for row in pack)
    with pytest.raises(HarnessError, match="SPOT_CHECK_FINAL"):
        A.spot_check_pack(cell, layout, files)
    labels = {r["opaque_id"]: r["is_abstention"] for path in files.values() for r in read_jsonl(path)}
    decisions = [{"opaque_id": r["opaque_id"], "lead_is_abstention": labels[r["opaque_id"]] if i < 25 else not labels[r["opaque_id"]]}
                 for i, r in enumerate(pack)]
    assert not A.record_spot_check(cell, layout, decisions)["accepted"]
    report = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert not report["instrument_valid"] and report["terminal_void"]
    with pytest.raises(HarnessError, match="SPOT_CHECK_FINAL"):
        accept_spot(cell, layout)
    with pytest.raises(HarnessError, match="ADJUDICATION_FINAL"):
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})


def test_second_cg1_failure_is_terminal(built, cell, tmp_path):
    layout, _ = built
    files = commit_all(layout, tmp_path, pos_correct=0.4)
    accept_spot(cell, layout)
    first = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert first["pending_regrade"]
    for sid in first["pending_regrade"]:
        rg = A.build_regrade(cell, layout, sid, files[sid])["regrade_shard"]
        A.commit_pool(layout)
        files[rg] = grade(layout, rg, tmp_path, pos_correct=0.2)
        A.commit_hash(layout, rg, files[rg])
    final = A.apply(cell, layout, {k: str(v) for k, v in files.items()})
    assert final["terminal_void"] and not final["instrument_valid"]
    with pytest.raises(HarnessError, match="ADJUDICATION_FINAL"):
        A.apply(cell, layout, {k: str(v) for k, v in files.items()})
