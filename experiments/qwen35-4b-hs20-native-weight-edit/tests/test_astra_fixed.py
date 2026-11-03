"""Synthetic math / provenance / refusal tests for the fixed Astra construction.

Synthetic arrays only: no checkpoint, model, private row or GPU is touched. Passing here shows the
arithmetic and the refusals behave as specified; it signs and qualifies nothing about the real model.
Independent oracles below restate the proposal's formulas in plain loops rather than calling the module.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml
from bf16 import to_bf16
from capturefix import write_capture
from hs20_nwe import astra_fixed as af
from hs20_nwe.util import HarnessError, sha256_bytes, sha256_file
from safetensors.numpy import load as st_load

EXPERIMENT = Path(__file__).resolve().parents[1]
REAL_YAML = EXPERIMENT / "astra_r1.yaml"
SIGMA = 1.576023489724997


def real_raw() -> dict:
    return yaml.safe_load(REAL_YAML.read_text(encoding="utf-8"))


def small_proposal(rows=12, cols=40, columns=4, counts=8, **patch) -> af.Proposal:
    raw = copy.deepcopy(real_raw())
    raw["patch"].update(shape=[rows, cols], columns=columns, maximum_modified_entries=rows * columns, **patch)
    raw["development"]["counts"] = {"confab": counts, "known_correct_answered": counts}
    return af.Proposal(raw, sha256_bytes(json.dumps(raw, sort_keys=True).encode()))


def unit(rng, n):
    c = rng.standard_normal(n)
    return c / np.linalg.norm(c)


def groups(rng, n=8, m=40, shift_cols=(3, 7, 11, 19, 25), shift=6.0, k_noise=1.0):
    u = rng.standard_normal((n, m))
    k = rng.standard_normal((n, m)) * k_noise
    for j in shift_cols:
        u[:, j] += shift * (1 + 0.1 * j)
    return u, k


def keys(prefix, n):
    return [f"{prefix}{i}" for i in range(n)]


def oracle_support(U, K, columns, eta_mult):
    eta = eta_mult * np.mean(np.concatenate([U, K]) ** 2)
    rows = []
    for j in range(U.shape[1]):
        mu, mk = U[:, j].mean(), K[:, j].mean()
        vu = ((U[:, j] - mu) ** 2).mean()
        vk = ((K[:, j] - mk) ** 2).mean()
        rows.append((-(mu - mk) ** 2 / (0.5 * (vu + vk) + eta), j))
    return sorted(j for _, j in sorted(rows)[:columns])


def oracle_scores(U, K, js, eta_mult):
    eta = eta_mult * np.mean(np.concatenate([U, K]) ** 2)
    return [(U[:, j].mean() - K[:, j].mean()) ** 2 / (0.5 * (U[:, j].var() + K[:, j].var()) + eta) for j in js]   # ddof=0


def oracle_caps(U, K, W, S, c, prop):
    u, k = U.mean(0)[S], K.mean(0)[S]
    q = u if k @ k == 0 else u - k * (k @ u) / (k @ k)
    v = q / (q @ u)
    r_k = math.sqrt(np.mean((K[:, S] @ v) ** 2))
    nv = np.linalg.norm(v)
    caps = {"nominal": 2 * SIGMA, "full_norm": 0.009 * np.linalg.norm(W) / nv,
            "column_norm": 0.09 * np.linalg.norm(W[:, S]) / nv,
            "known_rms": None if r_k == 0 else 0.5 * SIGMA / r_k}
    return v, caps


def realize(W, S, c, v, scale):
    """Engine arithmetic: float32 add of scale*outer(u, v) on the support, cast to bf16."""
    out = W.copy()
    new = to_bf16(W[:, S].astype(np.float32) + np.float32(scale) * np.outer(c.astype(np.float32), v.astype(np.float32)))
    out[:, S] = new
    return out


def bf16_weight(rng, shape, scale=0.05):
    return to_bf16(rng.standard_normal(shape) * scale).astype(np.float32)


# ---------------------------------------------------------------------------
# proposal file
# ---------------------------------------------------------------------------

def test_real_proposal_loads_and_refuses_when_edited(tmp_path):
    prop = af.load_proposal(REAL_YAML)
    assert prop.shape == (2560, 9216) and prop.columns == 32 and prop.sigma == SIGMA
    assert prop.tensor == "model.language_model.layers.19.mlp.down_proj.weight"
    for field, value in (("launch_authority", True), ("schema_version", "other")):
        raw = real_raw()
        raw[field] = value
        path = tmp_path / f"{field}.yaml"
        path.write_text(yaml.safe_dump(raw))
        with pytest.raises(HarnessError) as e:
            af.load_proposal(path)
        assert e.value.code in {"PROPOSAL_AUTHORITY", "PROPOSAL_SCHEMA"}
    raw = real_raw()
    raw["patch"]["maximum_modified_entries"] = 81921
    path = tmp_path / "entries.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(HarnessError) as e:
        af.load_proposal(path)
    assert e.value.code == "PROPOSAL_FIELDS"


# ---------------------------------------------------------------------------
# roster
# ---------------------------------------------------------------------------

def oracle_roster(rows, surfaces, seed, counts):
    import unicodedata

    norm = lambda s: " ".join(unicodedata.normalize("NFKC", s).casefold().split())
    banned = {norm(q) for qs in surfaces.values() for q in qs}
    out = {}
    for role, n in counts.items():
        best = {}
        for r in rows:
            if r["role"] != role or norm(r["question"]) in banned:
                continue
            nq = norm(r["question"])
            if nq not in best or r["row_key"].encode() < best[nq].encode():
                best[nq] = r["row_key"]
        ordered = sorted(best.values(), key=lambda s: s.encode())
        perm = np.random.default_rng(seed).permutation(len(ordered))
        out[role] = [ordered[i] for i in perm[:n]]
    return out


def fit_rows(n_each=30):
    rows = []
    for role, tag in (("confab", "c"), ("known_correct_answered", "k")):
        for i in range(n_each):
            rows.append({"row_key": f"{tag}{i:02d}", "role": role, "question": f"Question {tag} number {i}?"})
    rows.append({"row_key": "u00", "role": "unknown_refused", "question": "Ignored unknown row?"})
    return rows


def test_roster_matches_oracle_with_exclusions_and_duplicates():
    rows = fit_rows()
    rows += [{"row_key": "c00-dup", "role": "confab", "question": "  QUESTION c   number 0? "},   # same normalized question, larger key
             {"row_key": "a-first", "role": "confab", "question": "ｑuestion c number 1?"}]       # NFKC variant; smaller key wins
    surfaces = {"selfaware": ["question  K number 3?", "unrelated"], "ambigqa": ["QUESTION c number 5?"]}
    counts = {"confab": 6, "known_correct_answered": 6}
    got = af.select_roster(rows, surfaces, seed=20261103, counts=counts)
    assert got["keys"] == oracle_roster(rows, surfaces, 20261103, counts)
    sel = set(got["keys"]["confab"]) | set(got["keys"]["known_correct_answered"])
    assert not sel & {"k03", "c05", "unknown", "u00", "c00-dup", "c01"}      # eval matches, other role, losing duplicate
    assert af.select_roster(list(reversed(rows)), surfaces, seed=20261103, counts=counts)["keys"] == got["keys"]
    assert af.select_roster(rows, surfaces, seed=1, counts=counts)["keys"] != got["keys"]
    stats = got["stats"]["confab"]
    assert stats["excluded_by_surface"] == {"selfaware": 0, "ambigqa": 1} and stats["duplicates_removed"] == 2
    assert "uestion" not in json.dumps(got["stats"])                            # counts only, no text


@pytest.mark.parametrize("mutate,code", [
    (lambda r: r.append({"row_key": "x1", "role": "known_correct_answered", "question": "question c number 2?"}), "ROSTER_CROSS_ROLE"),
    (lambda r: r.append({"row_key": "c00", "role": "confab", "question": "different"}), "ROSTER_DUP_KEY"),
    (lambda r: r.append({"row_key": "c99", "role": "confab"}), "ROSTER_ROW"),
    (lambda r: r.__delitem__(slice(20, 30)), "ROSTER_SHORT"),
])
def test_roster_refusals(mutate, code):
    rows = fit_rows()
    mutate(rows)
    with pytest.raises(HarnessError) as e:
        af.select_roster(rows, {"selfaware": [], "ambigqa": []}, seed=1, counts={"confab": 25, "known_correct_answered": 25})
    assert e.value.code == code


def test_roster_short_after_exclusion_does_not_shrink():
    rows = fit_rows(10)
    surfaces = {"selfaware": [r["question"] for r in rows if r["row_key"] < "c05" and r["role"] == "confab"], "ambigqa": []}
    with pytest.raises(HarnessError) as e:
        af.select_roster(rows, surfaces, seed=1, counts={"confab": 8, "known_correct_answered": 8})
    assert e.value.code == "ROSTER_SHORT"


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return sha256_file(path)


def test_prepare_roster_hash_pins_and_create_only(tmp_path):
    prop = small_proposal(counts=6)
    fit, sa, am = tmp_path / "fit.jsonl", tmp_path / "sa.jsonl", tmp_path / "am.jsonl"
    prop.raw["development"]["fit_sha256"] = write_jsonl(fit, fit_rows())
    surf = prop.raw["evaluation"]["surfaces"]
    surf["selfaware"].update(sha256=write_jsonl(sa, [{"question": "Question c number 2?"}]), rows=1)
    surf["ambigqa"].update(sha256=write_jsonl(am, [{"question": "elsewhere"}]), rows=1)
    out = tmp_path / "roster.json"
    summary = af.prepare_roster(prop, fit, {"selfaware": sa, "ambigqa": am}, out)
    doc = json.loads(out.read_text())
    assert doc["roster_sha256"] == summary["roster_sha256"] and "Question" not in out.read_text()
    assert "c02" not in doc["keys"]["confab"] and len(doc["keys"]["confab"]) == 6
    with pytest.raises(HarnessError) as e:                       # create-only
        af.prepare_roster(prop, fit, {"selfaware": sa, "ambigqa": am}, out)
    assert e.value.code == "OUTPUT_EXISTS"
    fit.write_text(fit.read_text() + "\n")                       # patched FIT no longer matches the registered sha
    with pytest.raises(HarnessError) as e:
        af.prepare_roster(prop, fit, {"selfaware": sa, "ambigqa": am}, tmp_path / "roster2.json")
    assert e.value.code == "INPUT_HASH"
    assert not (tmp_path / "roster2.json").exists()


# ---------------------------------------------------------------------------
# constructor
# ---------------------------------------------------------------------------

def build(prop, rng=None, **kw):
    rng = rng or np.random.default_rng(0)
    R, M = prop.shape
    n = prop.group_size["confab"]
    U, K = groups(rng, n=n, m=M, **kw)
    c = unit(rng, R)
    W = rng.standard_normal((R, M)) * 0.05
    return U, K, c, W, keys("u", n), keys("k", n)


def test_support_ties_ascending_and_sorted():
    small_proposal(columns=4)
    rng = np.random.default_rng(3)
    n, m = 8, 40
    U, K = rng.standard_normal((n, m)), rng.standard_normal((n, m))
    pattern = rng.standard_normal(n)
    tied = [30, 9, 21, 14, 5, 33]                                  # identical score columns
    for j in tied:
        U[:, j] = pattern + 50.0
        K[:, j] = -pattern
    U[:, 2], K[:, 2] = 0.01 * pattern + 5000.0, -0.01 * pattern  # one clearly higher score
    sup, scores, eta = af.select_support(U, K, columns=4, eta_multiplier=1e-6)
    assert sup == sorted(sup) == oracle_support(U, K, 4, 1e-6)
    assert 2 in sup
    assert [j for j in sup if j in tied] == [5, 9, 14]             # ties resolved to the lowest indices
    assert scores[sup.index(5)] == scores[sup.index(9)] == scores[sup.index(14)]
    assert eta > 0 and eta == pytest.approx(1e-6 * np.mean(np.concatenate([U, K]) ** 2), rel=1e-12)
    assert scores == pytest.approx(oracle_scores(U, K, sup, 1e-6), rel=1e-12)     # population variances


@pytest.mark.parametrize("target", ["nominal", "full_norm", "column_norm", "known_rms"])
def test_each_active_scale_cap_and_mean_constraints(target):
    prop = small_proposal()
    rng = np.random.default_rng(7)
    k_noise = {"nominal": 0.01, "full_norm": 1.0, "column_norm": 1.0, "known_rms": 2000.0}[target]
    U, K, c, W, uk, kk = build(prop, rng, shift=60.0, k_noise=k_noise)
    S = af.select_support(U, K, columns=4, eta_multiplier=1e-6)[0]
    if target in ("nominal", "known_rms"):
        W = W * 1000
    if target == "column_norm":
        W[:, S] *= 1e-3
    con = af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)
    v, caps = oracle_caps(U, K, W, S, c, prop)
    assert con.columns == S and np.allclose(con.v, v, rtol=1e-12, atol=0)
    assert con.limiting == target
    assert con.alpha == pytest.approx(min(x for x in caps.values() if x is not None), rel=1e-12)
    assert all(x is None or x > con.alpha for t, x in caps.items() if t != target)   # unique binding term
    mu_u, mu_k = U.mean(0)[S], K.mean(0)[S]
    assert v @ mu_u == pytest.approx(1.0, abs=1e-12) and abs(v @ mu_k) < 1e-12
    assert con.ideal["mean_U_write_along_c"] == pytest.approx(con.alpha, rel=1e-12) and con.alpha > 0
    assert abs(con.ideal["mean_K_write_along_c"]) < 1e-9 * con.alpha
    assert con.ideal["rms_K_write_along_c"] <= 0.5 * SIGMA * (1 + 1e-12)


def test_zero_known_mean_uses_u_and_zero_known_rms_omits_term():
    prop = small_proposal()
    rng = np.random.default_rng(11)
    U, K, c, W, uk, kk = build(prop, rng, shift=20.0)
    K[:] = 0.0
    con = af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)
    u = U.mean(0)[con.columns]
    assert np.allclose(con.v, u / (u @ u)) and con.caps["known_rms"] is None and con.limiting != "known_rms"


@pytest.mark.parametrize("what", ["nan_U", "inf_W", "c_rows", "ragged_K", "overlap", "dup_u", "key_count", "c_norm",
                                  "zero_W", "few_cols", "all_zero", "collinear", "group_size", "shape"])
def test_construct_refuses_degenerate_or_malformed(what):
    prop = small_proposal()
    rng = np.random.default_rng(5)
    U, K, c, W, uk, kk = build(prop, rng, shift=15.0)
    kw = {}
    if what == "nan_U":
        U[2, 3] = np.nan
    elif what == "inf_W":
        W[0, 0] = np.inf
    elif what == "c_rows":
        c = c[:-1]
    elif what == "ragged_K":
        K = K[:, :-1]
    elif what == "overlap":
        kk[0] = uk[0]
    elif what == "dup_u":
        uk[1] = uk[0]
    elif what == "key_count":
        uk = uk[:-1]
    elif what == "c_norm":
        c = c * 1.01
    elif what == "zero_W":
        W[:] = 0.0
    elif what == "few_cols":
        U, K, W = U[:, :3], K[:, :3], W[:, :3]
    elif what == "all_zero":
        U[:], K[:] = 0.0, 0.0
    elif what == "collinear":
        U, K = np.tile(np.arange(1.0, 41.0), (8, 1)) * 2.0, np.tile(np.arange(1.0, 41.0), (8, 1))
        U[:4] += 1e-9
        K[:4] -= 1e-9
    elif what == "group_size":
        kw["expected_group_size"] = {"confab": 64, "known_correct_answered": 64}
    elif what == "shape":
        kw["expected_shape"] = (2560, 9216)
    with pytest.raises(HarnessError) as e:
        af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk, **kw)
    assert e.value.code in {"INPUT_NONFINITE", "INPUT_SHAPE", "GROUPS", "DEGENERATE"}
    assert e.value.code == {"nan_U": "INPUT_NONFINITE", "inf_W": "INPUT_NONFINITE", "overlap": "GROUPS", "dup_u": "GROUPS",
                            "group_size": "GROUPS", "all_zero": "DEGENERATE", "collinear": "DEGENERATE",
                            "zero_W": "DEGENERATE", "c_norm": "DEGENERATE"}.get(what, "INPUT_SHAPE")


def test_production_constants_full_shape_construction():
    prop = af.load_proposal(REAL_YAML)
    rng = np.random.default_rng(1)
    U, K = groups(rng, n=64, m=9216, shift_cols=(5, 700, 9000), shift=4.0)
    W = bf16_weight(rng, (2560, 9216), 0.02)
    c = unit(rng, 2560)
    con = af.construct(U, K, c, W, prop, u_keys=keys("u", 64), k_keys=keys("k", 64), expected_shape=(2560, 9216),
                       expected_group_size=prop.group_size)
    assert len(con.columns) == 32 and con.columns == sorted(con.columns) and {5, 700, 9000} <= set(con.columns)
    assert con.alpha > 0 and con.limiting in af.TERMS and con.shape == (2560, 9216)


# ---------------------------------------------------------------------------
# spec / payload
# ---------------------------------------------------------------------------

def listing_for(prop, W, name=None, **override):
    name = name or prop.tensor
    tensor = {"name": name, "dtype": "bfloat16", "shape": list(W.shape), "nbytes": W.size * 2,
              "sha256": af.bf16_raw_sha256(W), "file": next(iter(prop.raw["model"]["files_sha256"]))}
    tensor.update(override)
    return {"index_sha256": "c" * 64, "files": [{"name": n, "sha256": s} for n, s in prop.raw["model"]["files_sha256"].items()],
            "tensors": [tensor], "listing_truncated": False}


def setup_construction(prop=None, seed=2):
    prop = prop or small_proposal()
    rng = np.random.default_rng(seed)
    U, K, c, _, uk, kk = build(prop, rng, shift=40.0)
    W = bf16_weight(rng, prop.shape)
    return prop, U, K, c, W, uk, kk, af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)


def test_bf16_hash_matches_raw_byte_convention():
    w = np.array([[1.0, -2.0], [0.5, 0.0]], dtype=np.float32)
    assert af.bf16_raw_sha256(w) == hashlib.sha256(bytes([0x80, 0x3F, 0x00, 0xC0, 0x00, 0x3F, 0x00, 0x00])).hexdigest()
    with pytest.raises(HarnessError) as e:
        af.bf16_raw_sha256(np.array([1.0000001], dtype=np.float32))
    assert e.value.code == "NOT_BF16"


def test_emit_binds_base_tensor_support_scale_and_is_create_only(tmp_path):
    prop, _U, _K, c, W, _uk, _kk, con = setup_construction()
    tensor, binding = af.resolve_target(prop, listing_for(prop, W))
    out = af.emit_patch(prop, con, tensor, binding, out_dir=tmp_path, checkpoint_ref="artifact://x/base", payload_ref="artifact://x/payload.safetensors")
    spec = yaml.safe_load(Path(out["spec_path"]).read_text())
    op = spec["operations"][0]
    assert (op["op"], op["tensor"], op["cols"], op["scale"], op["arrays"]) == ("add_rank_one", prop.tensor, con.columns, con.alpha, {"u": "u", "v": "v"})
    assert spec["base"]["tensors"] == {prop.tensor: {"dtype": "bfloat16", "shape": list(prop.shape), "sha256": af.bf16_raw_sha256(W)}}
    assert spec["base"]["files_sha256"] == prop.raw["model"]["files_sha256"] and spec["base"]["revision"] == prop.raw["model"]["revision"]
    assert spec["base"]["index_sha256"] == "c" * 64 and spec["base"]["allow_symlinked_files"] is False
    assert spec["budget"]["allowed_tensors"] == [prop.tensor] and spec["budget"]["max_modified_tensors"] == 1
    assert spec["budget"]["max_modified_entries"] == prop.shape[0] * 4 and spec["budget"]["max_relative_frobenius"] == 0.01
    raw = Path(out["payload_path"]).read_bytes()
    assert spec["payload"]["sha256"] == sha256_bytes(raw) == out["payload_sha256"]
    arrays = st_load(raw)
    assert arrays["u"].dtype == arrays["v"].dtype == np.float32
    assert np.array_equal(arrays["u"], c.astype(np.float32)) and np.array_equal(arrays["v"], con.v.astype(np.float32))
    before = (Path(out["spec_path"]).read_bytes(), raw)
    with pytest.raises(HarnessError) as e:
        af.emit_patch(prop, con, tensor, binding, out_dir=tmp_path, checkpoint_ref="artifact://x/base", payload_ref="artifact://x/p")
    assert e.value.code == "OUTPUT_EXISTS" and (Path(out["spec_path"]).read_bytes(), Path(out["payload_path"]).read_bytes()) == before


@pytest.mark.parametrize("what", ["other_layer", "dtype", "shape", "short_sha", "truncated", "shard_hash", "no_hash",
                                  "unbound_file", "duplicate"])
def test_target_resolution_refuses_without_fallback(what):
    prop, *_, W, _, _, _con = setup_construction()
    lst = listing_for(prop, W)
    t = lst["tensors"][0]
    if what == "other_layer":
        t["name"] = prop.tensor.replace("layers.19", "layers.18")    # a different layer is never an acceptable stand-in
    elif what == "dtype":
        t["dtype"] = "float32"
    elif what == "shape":
        t["shape"] = [prop.shape[0], prop.shape[1] + 1]
    elif what == "short_sha":
        t["sha256"] = "ab"
    elif what == "truncated":
        lst["listing_truncated"] = True
    elif what == "shard_hash":
        lst["files"][0]["sha256"] = "0" * 64
    elif what == "no_hash":
        lst["files"][0]["sha256"] = None
    elif what == "unbound_file":
        t["file"] = "stray.safetensors"
    elif what == "duplicate":
        lst["tensors"].append(dict(t))
    with pytest.raises(HarnessError) as e:
        af.resolve_target(prop, lst)
    assert e.value.code in {"TENSOR_RESOLUTION", "BINDING"}


def test_spec_refuses_non_artifact_refs(tmp_path):
    prop, *_, W, _, _, con = setup_construction()
    tensor, binding = af.resolve_target(prop, listing_for(prop, W))
    with pytest.raises(HarnessError) as e:
        af.emit_patch(prop, con, tensor, binding, out_dir=tmp_path, checkpoint_ref="/abs/base", payload_ref="artifact://p")
    assert e.value.code == "SPEC_REF" and not list(tmp_path.iterdir())


# ---------------------------------------------------------------------------
# realized audit
# ---------------------------------------------------------------------------

def audit_args(seed=2):
    prop, U, K, c, W, _uk, _kk, con = setup_construction(seed=seed)
    return prop, con, U, K, W, c


def test_realized_audit_reports_actual_readback_not_ideal():
    prop, con, U, K, W, c = audit_args()
    edited = realize(W, con.columns, c, con.v, con.alpha)
    rep = af.audit_realized(con, prop, U, K, W, edited)
    assert rep["passed"], rep["failures"]
    D = (edited - W).astype(np.float64)
    assert rep["entries_changed"] == int((D != 0).sum()) and rep["changed_off_support"] == 0
    # independent: apply the realized delta to each item's down-proj input and project on c
    pu = np.array([c @ (D @ a) for a in U])
    pk = np.array([c @ (D @ a) for a in K])
    assert rep["write_along_c"]["U_mean"] == pytest.approx(pu.mean(), rel=1e-9) and rep["write_along_c"]["U_mean"] > 0
    assert rep["write_along_c"]["K_rms"] == pytest.approx(math.sqrt((pk ** 2).mean()), rel=1e-9)
    off_u = np.array([np.linalg.norm(D @ a - c * (c @ (D @ a))) for a in U])
    off_k = np.array([np.linalg.norm(D @ a - c * (c @ (D @ a))) for a in K])
    assert rep["off_c"]["residual_frobenius"] > 0 and rep["off_c"]["U_rms"] > 0     # bf16 rounding leaves an off-c residue
    assert rep["off_c"]["U_rms"] == pytest.approx(math.sqrt((off_u ** 2).mean()), rel=1e-9)
    assert rep["off_c"]["K_rms"] == pytest.approx(math.sqrt((off_k ** 2).mean()), rel=1e-9)
    assert rep["relative_frobenius_full"] == pytest.approx(np.linalg.norm(D) / np.linalg.norm(W.astype(np.float64)), rel=1e-12)
    assert rep["limiting_construction_term"] == con.limiting and rep["alpha"] == con.alpha
    assert rep["write_along_c"]["U_mean"] != con.ideal["mean_U_write_along_c"]     # realized, not the ideal number


def test_noop_after_rounding_is_refused_not_rescaled():
    prop, con, U, K, W, c = audit_args()
    edited = realize(W, con.columns, c, con.v, con.alpha * 1e-9)       # below bf16 resolution everywhere
    assert np.array_equal(edited, W)
    rep = af.audit_realized(con, prop, U, K, W, edited)
    assert not rep["passed"] and next(f["code"] for f in rep["failures"]) == "NOOP" and rep["entries_changed"] == 0


@pytest.mark.parametrize("what,codes", [
    ("inflate3", {"NORM_FULL"}),
    ("negative", {"U_MEAN_NOT_POSITIVE"}),
    ("off_support", {"OFF_SUPPORT"}),
])
def test_realized_guard_refusals(what, codes):
    prop, con, U, K, W, c = audit_args()
    if what == "inflate3":
        edited = realize(W, con.columns, c, con.v, 3 * con.alpha)
    elif what == "negative":
        edited = realize(W, con.columns, c, con.v, -con.alpha)
    else:
        edited = realize(W, con.columns, c, con.v, con.alpha)
        free = next(j for j in range(prop.shape[1]) if j not in con.columns)
        edited[0, free] = to_bf16(np.array([edited[0, free] + 0.25], dtype=np.float32))[0]
    rep = af.audit_realized(con, prop, U, K, W, edited)
    assert not rep["passed"] and codes <= {f["code"] for f in rep["failures"]}


def test_known_anchor_rms_guard_refuses_inflated_realized_write():
    prop = small_proposal()
    rng = np.random.default_rng(7)
    U, K, c, W, uk, kk = build(prop, rng, shift=60.0, k_noise=2000.0)
    probe = af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)
    # scale W so the norm caps sit well above the known-RMS cap, keeping the edit above bf16 resolution
    W = to_bf16(W * (3 * probe.caps["known_rms"] / min(probe.caps["full_norm"], probe.caps["column_norm"]))).astype(np.float32)
    con = af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)
    assert con.limiting == "known_rms"
    assert af.audit_realized(con, prop, U, K, W, realize(W, con.columns, c, con.v, con.alpha))["entries_changed"] > 0
    bad = af.audit_realized(con, prop, U, K, W, realize(W, con.columns, c, con.v, 3 * con.alpha))
    assert "K_RMS" in {f["code"] for f in bad["failures"]} and bad["write_along_c"]["K_rms"] > 0.5 * SIGMA


def test_column_norm_and_entry_guards():
    prop = small_proposal()
    rng = np.random.default_rng(9)
    U, K, c, W, uk, kk = build(prop, rng, shift=40.0)
    W = to_bf16(W).astype(np.float32)
    S = af.select_support(U, K, columns=4, eta_multiplier=1e-6)[0]
    W[:, S] *= 1e-2
    W = to_bf16(W).astype(np.float32)
    con = af.construct(U, K, c, W, prop, u_keys=uk, k_keys=kk)
    assert con.limiting == "column_norm"
    ok = af.audit_realized(con, prop, U, K, W, realize(W, S, c, con.v, con.alpha))
    assert ok["relative_frobenius_columns"] <= 0.1 + 5e-3 and ok["limiting_realized_guard"] in ok["limits"]
    bad = af.audit_realized(con, prop, U, K, W, realize(W, S, c, con.v, 2 * con.alpha))
    assert "NORM_COLUMNS" in {f["code"] for f in bad["failures"]}
    tight_raw = copy.deepcopy(prop.raw)
    tight_raw["patch"]["maximum_modified_entries"] = 2
    tight = af.Proposal(tight_raw, "x" * 64)
    rep = af.audit_realized(con, tight, U, K, W, realize(W, S, c, con.v, con.alpha))
    assert "ENTRY_COUNT" in {f["code"] for f in rep["failures"]}


def test_receipt_cross_check_and_malformed_readback():
    prop, con, U, K, W, c = audit_args()
    edited = realize(W, con.columns, c, con.v, con.alpha)
    D = edited.astype(np.float64) - W
    receipt = {"name": prop.tensor, "entries_changed": int((D != 0).sum()), "delta_frobenius": float(np.linalg.norm(D))}
    assert af.audit_realized(con, prop, U, K, W, edited, receipt_tensor=receipt)["receipt_checked"]
    wrong = dict(receipt, entries_changed=receipt["entries_changed"] + 1)
    assert "RECEIPT_MISMATCH" in {f["code"] for f in af.audit_realized(con, prop, U, K, W, edited, receipt_tensor=wrong)["failures"]}
    with pytest.raises(HarnessError) as e:                       # readback not exactly in the stored dtype
        af.audit_realized(con, prop, U, K, W, edited + np.float32(1e-7))
    assert e.value.code == "NOT_BF16"
    with pytest.raises(HarnessError) as e:                       # audit of a different base than the one constructed from
        af.audit_realized(con, prop, U, K, to_bf16(W * 1.5).astype(np.float32), edited)
    assert e.value.code == "BASE_MISMATCH"
    edited[0, 0] = np.nan
    with pytest.raises(HarnessError) as e:
        af.audit_realized(con, prop, U, K, W, edited)
    assert e.value.code == "INPUT_NONFINITE"


# ---------------------------------------------------------------------------
# capture provenance + CLI round trip
# ---------------------------------------------------------------------------

def write_synthetic_capture(directory, u_keys, k_keys, U, K, *, block=19, W=None, proposal=None, **kw):
    table = {k: U[i] for i, k in enumerate(u_keys)} | {k: K[i] for i, k in enumerate(k_keys)}
    manifest = write_capture(directory, [{"row_key": k} for k in table], lambda r: np.ones(W.shape[0] if W is not None else 6),
                             lambda r, b: table[r["row_key"]], hidden_state=20, blocks=(block,), **kw)
    if W is not None:
        from hs20_nwe import astra_capture, astra_render
        from safetensors.numpy import load_file, save_file
        for rec in manifest["rows"]:
            info = rec["site_captures"]["anchor"]
            path = directory / info["file"]
            tensors = load_file(str(path))
            tensors[f"L{block}.mlp.down_proj.output"] = (W.astype(np.float64) @ table[rec["row_key"]]).astype(np.float32)[None, :]
            save_file(tensors, str(path))
            info["sha256"] = sha256_file(path)
        (directory / "manifest.json").write_text(json.dumps(manifest))
        source = proposal.raw["model"]
        spec = proposal.raw["development"]["capture"]
        identity = {"schema_version": "mechinterp-capture-journal/v1",
                    "run": {"model": {"path": "synthetic-base", "files": source["files_sha256"]},
                            "revision": source["revision"], "adapter": None, "content_end": None,
                            "render": {"callable": "hs20_nwe.astra_render:render_pstruct",
                                       "source_sha256": sha256_file(astra_render.__file__)}},
                    "inputs": [{"row_key": k, "prompt_sha256": sha256_bytes(k.encode())} for k in list(u_keys) + list(k_keys)],
                    "families": ["anchor"], "layers": [20], "every_k": spec["every_k"],
                    "max_new_tokens": spec["max_new_tokens"], "use_cache": spec["use_cache"],
                    "forward_only": True, "save_tensors": True, "manifest_extra": None,
                    "sites": [{"layer": block, "module": "mlp.down_proj", "tensor": t} for t in ["input", "output"]]}
        request = {"schema_version": astra_capture.SCHEMA, "proposal_sha256": proposal.sha256,
                   "identity": identity, "fingerprint": astra_capture.fingerprint(identity)}
        (directory.parent / "capture_request.json").write_text(json.dumps(request))
        (directory / "capture.runlog.jsonl.meta.json").write_text(json.dumps({"complete": True, "fingerprint": request["fingerprint"]}))
        (directory / "capture.runlog.jsonl").write_text(''.join(json.dumps(r) + '\n' for r in manifest["rows"]))
    return manifest


def test_capture_reader_returns_ordered_groups_and_refuses_stale_captures(tmp_path):
    small_proposal()
    rng = np.random.default_rng(4)
    U, K = groups(rng)
    uk, kk = keys("u", 8), keys("k", 8)
    d = tmp_path / "cap"
    write_synthetic_capture(d, uk, kk, U, K)
    got = af.load_group_activations(d, uk, kk, block=19, hidden_state=20)
    assert np.allclose(got["U"], U.astype(np.float32)) and np.allclose(got["K"], K.astype(np.float32))
    assert got["manifest_sha256"] == sha256_file(d / "manifest.json")
    with pytest.raises(HarnessError) as e:                       # a different roster than the captured rows
        af.load_group_activations(d, uk[:-1] + ["u-new"], kk, block=19, hidden_state=20)
    assert e.value.code == "CAPTURE_ROWS"
    for name, setup, code in (
        ("patched", lambda p: (p / "u0__anchor.sites.safetensors").write_bytes(b"x" + (p / "u0__anchor.sites.safetensors").read_bytes()), "CAPTURE_HASH"),
        ("missing", lambda p: (p / "k3__anchor.safetensors").unlink(), "CAPTURE_MISSING"),
        ("incomplete", lambda p: (p / "manifest.json").write_text(json.dumps({**json.loads((p / "manifest.json").read_text()), "complete": False})), "CAPTURE_INCOMPLETE"),
        ("not_forward", lambda p: (p / "manifest.json").write_text(json.dumps({**json.loads((p / "manifest.json").read_text()), "forward_only": False})), "CAPTURE_MODE"),
        ("no_manifest", lambda p: (p / "manifest.json").unlink(), "CAPTURE_INCOMPLETE"),
    ):
        dd = tmp_path / name
        write_synthetic_capture(dd, uk, kk, U, K)
        setup(dd)
        with pytest.raises(HarnessError) as e:
            af.load_group_activations(dd, uk, kk, block=19, hidden_state=20)
        assert e.value.code == code, name


def test_cli_prepare_and_audit_round_trip_on_synthetic_inputs(tmp_path, capsys):
    prop = small_proposal(rows=16, cols=64, columns=8, counts=8)
    rng = np.random.default_rng(21)
    raw = prop.raw
    c = unit(rng, 16)
    chat = tmp_path / "c_hat.json"
    chat.write_text(json.dumps({"vector": c.tolist(), "layer": 19, "sigma": SIGMA}))
    raw["patch"]["direction_sha256"] = sha256_file(chat)
    fit = tmp_path / "fit.jsonl"
    rows = fit_rows(12)
    raw["development"]["fit_sha256"] = write_jsonl(fit, rows)
    sa, am = tmp_path / "sa.jsonl", tmp_path / "am.jsonl"
    raw["evaluation"]["surfaces"]["selfaware"].update(sha256=write_jsonl(sa, [{"question": "Question c number 0?"}]), rows=1)
    raw["evaluation"]["surfaces"]["ambigqa"].update(sha256=write_jsonl(am, [{"question": "other"}]), rows=1)
    proposal_path = tmp_path / "astra.yaml"
    proposal_path.write_text(yaml.safe_dump(raw))
    base = ["--proposal", str(proposal_path)]

    assert af.main(base + ["roster", "--fit", str(fit), "--selfaware", str(sa), "--ambigqa", str(am), "--out", str(tmp_path / "roster.json")]) == 0
    roster = json.loads((tmp_path / "roster.json").read_text())
    assert "c00" not in roster["keys"]["confab"] and "Question" not in capsys.readouterr().out

    uk, kk = roster["keys"]["confab"], roster["keys"]["known_correct_answered"]
    U, K = groups(rng, n=8, m=64, shift_cols=(2, 9, 17, 30, 31, 40, 50, 60, 63), shift=30.0)
    W = bf16_weight(rng, (16, 64))
    loaded_proposal = af.load_proposal(proposal_path)
    write_synthetic_capture(tmp_path / "cap", uk, kk, U.astype(np.float32).astype(np.float64),
                            K.astype(np.float32).astype(np.float64), W=W, proposal=loaded_proposal)
    np.save(tmp_path / "base.npy", W)
    lst = listing_for(prop, W)
    (tmp_path / "listing.json").write_text(json.dumps({"success": True, "data": lst}))
    out = tmp_path / "patch"
    prep = base + ["prepare", "--roster", str(tmp_path / "roster.json"), "--capture-dir", str(tmp_path / "cap"), "--c-hat", str(chat),
                   "--capture-binding", str(tmp_path / "capture_request.json"),
                   "--inspect-listing", str(tmp_path / "listing.json"), "--base-tensor-npy", str(tmp_path / "base.npy"),
                   "--checkpoint-ref", "artifact://t/base", "--payload-ref", "artifact://t/patch/payload.safetensors",
                   "--export-ref", "artifact://t/export", "--out-dir", str(out)]
    assert af.main(prep) == 0
    assert af.main(prep) == 2 and capsys.readouterr().err.count("OUTPUT_EXISTS") >= 1       # create-only
    report = json.loads((out / "prepare_report.json").read_text())
    spec = yaml.safe_load((out / "spec.yaml").read_text())
    assert spec['export'] == {'output_dir': 'artifact://t/export'}
    assert report["launch_authority"] is False and spec["operations"][0]["scale"] == report["construction"]["alpha"]
    assert report["spec_sha256"] == sha256_file(out / "spec.yaml") and report["payload_sha256"] == spec["payload"]["sha256"]
    assert report["roster_sha256"] == roster["roster_sha256"] and report["tensor"]["sha256"] == af.bf16_raw_sha256(W)

    con = report["construction"]
    edited = realize(W, con["columns"], c, np.array(con["v"]), con["alpha"])
    np.save(tmp_path / "edited.npy", edited)
    audit = base + ["audit", "--prepare-report", str(out / "prepare_report.json"), "--spec", str(out / "spec.yaml"),
                    "--capture-binding", str(tmp_path / "capture_request.json"),
                    "--payload", str(out / "payload.safetensors"), "--roster", str(tmp_path / "roster.json"),
                    "--capture-dir", str(tmp_path / "cap"), "--c-hat", str(chat), "--base-tensor-npy", str(tmp_path / "base.npy"),
                    "--edited-tensor-npy", str(tmp_path / "edited.npy"), "--out", str(tmp_path / "audit.json")]
    assert af.main(audit) == 0
    assert json.loads((tmp_path / "audit.json").read_text())["passed"] is True
    np.save(tmp_path / "edited.npy", realize(W, con["columns"], c, np.array(con["v"]), 4 * con["alpha"]))
    assert af.main(audit[:-2] + ["--out", str(tmp_path / "audit2.json")]) == 3                  # guard failure is final
    # stale: spec bytes changed after prepare
    (out / "spec.yaml").write_text((out / "spec.yaml").read_text() + "\n# tampered\n")
    capsys.readouterr()
    assert af.main(audit[:-2] + ["--out", str(tmp_path / "audit3.json")]) == 2 and "REPORT_STALE" in capsys.readouterr().err
    # wrong base bytes are refused before any file is written
    np.save(tmp_path / "base_bad.npy", to_bf16(W * 2).astype(np.float32))
    prep_bad = [a if a != str(tmp_path / "base.npy") else str(tmp_path / "base_bad.npy") for a in prep]
    prep_bad[prep_bad.index("--out-dir") + 1] = str(tmp_path / "patch2")
    assert af.main(prep_bad) == 2 and "BASE_HASH" in capsys.readouterr().err and not (tmp_path / "patch2").exists()


def test_native_selfaware_container_and_exfat_create_only(tmp_path, monkeypatch):
    source = tmp_path / 'SelfAware.json'
    source.write_text(json.dumps({'dataset_name': 'synthetic', 'example': [{'question': 'Synthetic question?'}]}))
    assert af._read_question_rows(source) == [{'question': 'Synthetic question?'}]
    def no_hardlinks(*args, **kwargs):
        raise OSError('hard links unavailable on exFAT')
    monkeypatch.setattr(af.os, 'link', no_hardlinks)
    target = tmp_path / 'record.json'
    assert af._create_only(target, b'{}\n') == sha256_bytes(b'{}\n')
    with pytest.raises(HarnessError) as exc:
        af._create_only(target, b'changed')
    assert exc.value.code == 'OUTPUT_EXISTS' and target.read_bytes() == b'{}\n'
