"""Column ranking, six-proposal cap, sparse column formula/order, receipts and matched controls."""

import numpy as np
import pytest
import yaml
from safetensors.numpy import load_file

from bf16 import realized_delta, to_bf16
from conftest import DIM, INTER, SLUG
from hs20_nwe import localize, weights
from hs20_nwe.config import Layout
from hs20_nwe.util import HarnessError


# ---- ranking ----------------------------------------------------------------

def test_rank_formula_order_and_positivity():
    m_conf = np.array([3.0, 1.0, 2.0, 5.0, 0.0, 4.0])
    m_known = np.array([1.0, 2.0, 2.0, 1.0, 1.0, 1.0])
    dots = np.array([1.0, 1.0, 1.0, -1.0, 2.0, 3.0])
    # scores = (c-k)*d = [2, -1, 0, -4, -2, 9]; strictly positive: columns 0 and 5
    r = localize.rank_columns(m_conf, m_known, dots, 2)
    assert r["eligible"] and r["columns"] == [5, 0] and r["scores"] == [9.0, 2.0] and r["n_positive"] == 2


def test_rank_ties_break_by_column_index_ascending():
    m_conf, m_known = np.array([2.0, 2.0, 2.0, 2.0]), np.zeros(4)
    dots = np.array([1.0, 1.0, 1.0, 1.0])
    assert localize.rank_columns(m_conf, m_known, dots, 3)["columns"] == [0, 1, 2]


def test_zero_scores_are_not_positive_and_short_blocks_supply_nothing():
    m_conf, m_known, dots = np.ones(5), np.ones(5), np.ones(5)           # all scores 0
    r = localize.rank_columns(m_conf, m_known, dots, 2)
    assert not r["eligible"] and r["columns"] == [] and r["n_positive"] == 0
    r = localize.rank_columns(np.array([2.0, 1.0]), np.zeros(2), np.array([1.0, 1.0]), 3)
    assert not r["eligible"]


def test_unknown_refused_mean_never_enters_the_ranking_signature():
    import inspect

    assert list(inspect.signature(localize.rank_columns).parameters) == ["mean_confab", "mean_known", "dots", "k"]


# ---- proposals ----------------------------------------------------------------

def _targets(cell):
    return {b: {"name": f"model.language_model.layers.{b}.mlp.down_proj.weight", "dtype": "bfloat16",
                "shape": [DIM, INTER], "sha256": f"{b:064x}", "nbytes": DIM * INTER * 2} for b in cell.cell["candidates"]["blocks"]}


def _rankings(cell, eligible=(20, 21, 22)):
    k = cell.cell["candidates"]["columns"]
    return {b: {"eligible": b in eligible, "columns": list(range(100, 100 + k)) if b in eligible else [], "n_positive": 40,
                "scores": []} for b in cell.cell["candidates"]["blocks"]}


BINDING = {"index_sha256": "a" * 64, "files_sha256": {"s1.safetensors": "b" * 64, "s2.safetensors": "c" * 64}}


def test_exactly_six_proposals_in_order(project, cell):
    layout = Layout(project.root, SLUG)
    c_hat = project.c_hat
    dots = {b: np.random.default_rng(b).standard_normal(INTER) for b in (20, 21, 22)}
    props = weights.build_proposal_files(cell, layout, c_hat=c_hat, targets=_targets(cell), binding=BINDING, dots=dots,
                                         rankings=_rankings(cell))
    assert [p.cand_id for p in props] == ["b20_s4", "b20_s16", "b21_s4", "b21_s16", "b22_s4", "b22_s16"]


def test_ineligible_block_supplies_no_candidates_and_cap_is_enforced(project, cell):
    plan = weights.plan_proposals(cell, _rankings(cell, eligible=(20, 22)))
    assert [(b, s) for b, s, _ in plan] == [(20, 4.0), (20, 16.0), (22, 4.0), (22, 16.0)]
    assert weights.plan_proposals(cell, _rankings(cell, eligible=())) == []
    from dataclasses import replace

    bad = {**cell.cell, "candidates": {**cell.cell["candidates"], "max_candidates": 5}}
    with pytest.raises(HarnessError) as e:
        weights.plan_proposals(replace(cell, cell=bad), _rankings(cell))
    assert e.value.code == "PROPOSAL_CAP"


def test_payload_and_spec_encode_the_column_amplification_formula(project, cell):
    """DeltaW[:, J] = l * c_hat * (c_hat^T W[:, J]) as the engine's add_rank_one(u=c_hat, v=dots[J], scale=l)."""
    layout = Layout(project.root, SLUG)
    rng = np.random.default_rng(5)
    W = to_bf16(rng.standard_normal((DIM, 64)).astype(np.float32) * 0.05).astype(np.float64)   # a column slice
    dots_all = project.c_hat @ W                                                                  # c_hat^T W[:, j]
    cols = [7, 3, 40]                                                                           # ranked order, not sorted
    rank = {"eligible": True, "columns": cols, "n_positive": 3, "scores": []}
    plan_cols = {20: rank, 21: {"eligible": False, "columns": []}, 22: {"eligible": False, "columns": []}}
    full_dots = {20: np.concatenate([dots_all, np.zeros(INTER - 64)])}
    cell32 = cell
    from dataclasses import replace

    c = {**cell.cell, "candidates": {**cell.cell["candidates"], "columns": 3}}
    props = weights.build_proposal_files(replace(cell32, cell=c), layout, c_hat=project.c_hat, targets=_targets(cell),
                                         binding=BINDING, dots=full_dots, rankings=plan_cols)
    p = props[1]                                       # lambda = 16
    spec = yaml.safe_load(p.spec_path.read_text())
    op = spec["operations"][0]
    assert op["op"] == "add_rank_one" and op["cols"] == cols and op["scale"] == 16.0 and op["tensor"] == p.tensor
    arrays = load_file(str(p.payload_path))
    assert set(arrays) == {"u", "v"}
    assert np.array_equal(arrays["u"], project.c_hat) and np.allclose(arrays["v"], dots_all[cols])
    ref = 16.0 * np.outer(project.c_hat, project.c_hat @ W[:, cols])
    got = op["scale"] * np.outer(arrays["u"], arrays["v"])
    assert np.allclose(got, ref)                                  # the analytic formula, column for column
    assert spec["payload"]["sha256"] == p.payload_sha256 and spec["base"]["revision"] == cell.revision
    assert spec["base"]["checkpoint"].startswith("artifact://") and spec["payload"]["path"].startswith("artifact://")
    b = spec["budget"]
    assert (b["max_modified_tensors"], b["max_modified_entries"], b["max_relative_frobenius"]) == (1, 81920, 0.05)
    assert b["allowed_tensors"] == [p.tensor] and list(spec["base"]["tensors"]) == [p.tensor]


def test_budget_numbers_come_from_cell_yaml(cell):
    assert cell.cell["candidates"]["budget"] == {"max_modified_tensors": 1, "max_modified_entries": 81920,
                                                 "max_relative_frobenius": 0.05}
    assert cell.cell["candidates"]["columns"] * cell.cell["model"]["hidden_dim"] == 81920


# ---- inspect parsing --------------------------------------------------------------

def test_dots_must_come_from_the_pinned_tensor_and_cover_every_column(cell):
    target = {"name": "t", "sha256": "x" * 64, "shape": [DIM, 4]}
    good = {"projections": [{"id": "col_dots_b20", "tensor": "t", "tensor_sha256": "x" * 64, "indices": "all",
                             "values": [1.0, 2.0, 3.0, 4.0]}]}
    assert weights.read_dots(good, 20, target).tolist() == [1.0, 2.0, 3.0, 4.0]
    for field, bad in (("tensor_sha256", "y" * 64), ("indices", [0, 1, 2, 3])):
        doc = {"projections": [{**good["projections"][0], field: bad}]}
        with pytest.raises(HarnessError):
            weights.read_dots(doc, 20, target)


def test_resolve_targets_requires_exactly_one_pinned_tensor_per_block(cell):
    def listing(names):
        return {"tensors": [{"name": n, "dtype": "bfloat16", "shape": [DIM, INTER], "sha256": "d" * 64} for n in names],
                "listing_truncated": False}
    names = [f"model.language_model.layers.{b}.mlp.down_proj.weight" for b in (20, 21, 22)]
    assert set(weights.resolve_targets(cell, listing(names))) == {20, 21, 22}
    with pytest.raises(HarnessError):
        weights.resolve_targets(cell, listing(names[:2]))
    with pytest.raises(HarnessError):
        weights.resolve_targets(cell, listing(names + ["x.layers.20.mlp.down_proj.weight"]))


# ---- validation receipts + controls --------------------------------------------------

def _receipt(delta, entries=81000, rel=0.01, noop=False):
    return {"success": True, "data": {"receipt": {"schema_version": "mechinterp-weight-patch-receipt/v1", "patch_digest": "p" * 64,
                                                  "noop": noop, "tensors": [{"entries_changed": entries, "delta_frobenius": delta,
                                                                              "relative_frobenius": rel}]}}}


def test_validation_receipt_classification(cell):
    assert weights.parse_validation(cell, _receipt(1.0)).valid
    assert not weights.parse_validation(cell, _receipt(1.0, entries=81921)).valid
    assert not weights.parse_validation(cell, _receipt(1.0, rel=0.0501)).valid
    assert not weights.parse_validation(cell, _receipt(0.0, noop=True)).valid
    refusal = weights.parse_validation(cell, {"success": False, "error": {"code": "WEIGHTS_BUDGET", "message": "x"}})
    assert not refusal.valid and refusal.code == "WEIGHTS_BUDGET"


def test_orthogonal_unit_is_seeded_unit_and_orthogonal(project):
    r1 = weights.orthogonal_unit(20261111, project.c_hat, project.u_d)
    r2 = weights.orthogonal_unit(20261111, project.c_hat, project.u_d)
    r3 = weights.orthogonal_unit(20261112, project.c_hat, project.u_d)
    assert np.array_equal(r1, r2) and not np.allclose(r1, r3)
    assert abs(np.linalg.norm(r1) - 1) < 1e-12 and abs(r1 @ project.c_hat) < 1e-9 and abs(r1 @ project.u_d) < 1e-9


class FakeValidator:
    """Fake ``weights-patch --validate`` using bf16 arithmetic on a synthetic weight slice."""

    def __init__(self, layout, W, native_u):
        self.layout, self.W, self.calls = layout, W, 0

    def __call__(self, spec_path):
        self.calls += 1
        spec = yaml.safe_load(spec_path.read_text())
        arrays = load_file(str(self.layout.to_local(spec["payload"]["path"])))
        op = spec["operations"][0]
        delta, entries = realized_delta(self.W[:, op["cols"]], arrays["u"], arrays["v"], op["scale"])
        doc = _receipt(delta, entries=entries)
        return weights.parse_validation(self.cell, doc)


def _control_setup(project, cell, n_cols=32, w_scale=0.05):
    from dataclasses import replace

    layout = Layout(project.root, SLUG)
    c = {**cell.cell, "candidates": {**cell.cell["candidates"], "columns": n_cols}}
    cell2 = replace(cell, cell=c)
    rng = np.random.default_rng(9)
    W = to_bf16(rng.standard_normal((DIM, n_cols)).astype(np.float32) * w_scale)
    cols = list(range(n_cols))
    v = project.c_hat @ W.astype(np.float64)
    native = weights.Proposal("b20_s16", 20, 16.0, "t", cols)
    ndelta, _ = realized_delta(W, project.c_hat, v, 16.0)
    fv = FakeValidator(layout, W, None)
    fv.cell = cell2
    return layout, cell2, native, ndelta, v, fv


def test_control_matches_norm_within_one_percent_with_at_most_three_adjustments(project, cell):
    layout, cell2, native, ndelta, v, fv = _control_setup(project, cell)
    res = weights.build_control(cell2, layout, seed=20261111, native=native, native_delta=ndelta, c_hat=project.c_hat,
                                u_d=project.u_d, v=v, tensor={"name": "t", "dtype": "bfloat16", "shape": [DIM, INTER], "sha256": "e" * 64},
                                binding=BINDING, validate=fv)
    assert res["status"] == "matched" and res["relative_error"] <= 0.01
    assert len(res["history"]) <= 4 and fv.calls == len(res["history"])      # first try + <=3 adjustments


def test_control_that_cannot_match_is_recorded_not_dropped(project, cell):
    layout, cell2, native, ndelta, v, fv = _control_setup(project, cell)
    res = weights.build_control(cell2, layout, seed=1, native=native, native_delta=ndelta * 1.37, c_hat=project.c_hat,
                                u_d=project.u_d, v=v, tensor={"name": "t", "dtype": "bfloat16", "shape": [DIM, INTER], "sha256": "e" * 64},
                                binding=BINDING, validate=lambda p: weights.Validation(True, patch_digest="p", entries_changed=10,
                                                                                         delta_frobenius=ndelta))   # delta never moves
    assert res["status"] == "failed_to_match" and len(res["history"]) == 4 and res["max_adjustments"] == 3


def test_control_refusal_is_recorded_without_adjustment(project, cell):
    layout, cell2, native, ndelta, v, fv = _control_setup(project, cell)
    res = weights.build_control(cell2, layout, seed=1, native=native, native_delta=ndelta, c_hat=project.c_hat, u_d=project.u_d, v=v,
                                tensor={"name": "t", "dtype": "bfloat16", "shape": [DIM, INTER], "sha256": "e" * 64},
                                binding=BINDING, validate=lambda p: weights.Validation(False, code="WEIGHTS_BUDGET"))
    assert res["status"] == "refused" and res["reason"] == "WEIGHTS_BUDGET" and len(res["history"]) == 1


def test_control_uses_same_support_and_coefficients_as_native(project, cell):
    layout, cell2, native, ndelta, v, fv = _control_setup(project, cell)
    weights.build_control(cell2, layout, seed=3, native=native, native_delta=ndelta, c_hat=project.c_hat, u_d=project.u_d, v=v,
                          tensor={"name": "t", "dtype": "bfloat16", "shape": [DIM, INTER], "sha256": "e" * 64}, binding=BINDING, validate=fv)
    spec = yaml.safe_load(layout.local("controls/seed3/spec.yaml", shared=True).read_text())
    arrays = load_file(str(layout.local("controls/seed3/payload.safetensors", shared=True)))
    assert spec["operations"][0]["cols"] == native.columns and np.allclose(arrays["v"], v)
    assert abs(arrays["u"] @ project.c_hat) < 1e-9 and abs(arrays["u"] @ project.u_d) < 1e-9
