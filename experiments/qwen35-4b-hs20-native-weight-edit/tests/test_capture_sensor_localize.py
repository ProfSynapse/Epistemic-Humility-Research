"""Manifest-only hash-checked capture reading, fresh sensor rule, resumable per-row localization."""

import json

import numpy as np
import pytest

from capturefix import write_capture
from hs20_nwe import capture, localize, sensor
from hs20_nwe.util import HarnessError


def rows(n, role="confab", prefix="r"):
    return [{"row_key": f"{prefix}:{i}", "role": role} for i in range(n)]


def test_reads_only_manifest_files_and_ignores_stray_files(tmp_path):
    rs = rows(3)
    write_capture(tmp_path, rs, lambda r: np.ones(2560))
    (tmp_path / "stray__anchor.safetensors").write_bytes(b"not a tensor")
    m = capture.load_manifest(tmp_path)
    capture.check_rows_covered(m, [r["row_key"] for r in rs])
    out = capture.read_row(tmp_path, m["rows"][0], hidden_state=20, sites=[])
    assert out["residual"].shape == (2560,)


def test_hash_mismatch_missing_file_and_symlink_are_refused(tmp_path):
    rs = rows(2)
    m = write_capture(tmp_path, rs, lambda r: np.ones(2560))
    f = tmp_path / m["rows"][0]["capture_files"]["anchor"]["file"]
    f.write_bytes(f.read_bytes() + b"\0")
    with pytest.raises(HarnessError) as e:
        capture.read_row(tmp_path, m["rows"][0], hidden_state=20, sites=[])
    assert e.value.code == "CAPTURE_HASH"
    g = tmp_path / m["rows"][1]["capture_files"]["anchor"]["file"]
    g.rename(tmp_path / "moved")
    with pytest.raises(HarnessError) as e:
        capture.read_row(tmp_path, m["rows"][1], hidden_state=20, sites=[])
    assert e.value.code == "CAPTURE_MISSING"
    g.symlink_to(tmp_path / "moved")
    with pytest.raises(HarnessError):
        capture.read_row(tmp_path, m["rows"][1], hidden_state=20, sites=[])


def test_incomplete_or_foreign_manifest_and_unsafe_names(tmp_path):
    write_capture(tmp_path, rows(1), lambda r: np.ones(2560), complete=False)
    with pytest.raises(HarnessError) as e:
        capture.load_manifest(tmp_path)
    assert e.value.code == "CAPTURE_INCOMPLETE"
    with pytest.raises(HarnessError):
        capture.load_manifest(tmp_path / "nowhere")
    bad = {"file": "../x", "sha256": "0" * 64}
    with pytest.raises(HarnessError) as e:
        capture.verified_path(tmp_path, bad)
    assert e.value.code == "CAPTURE_UNSAFE"


def test_row_set_must_match_registered_population(tmp_path):
    rs = rows(3)
    m = write_capture(tmp_path, rs, lambda r: np.ones(2560))
    with pytest.raises(HarnessError):
        capture.check_rows_covered(m, [r["row_key"] for r in rs[:2]])


def test_unsafe_row_keys_use_manifest_filenames(tmp_path):
    rs = [{"row_key": "popqa:1046216", "role": "confab"}]               # ':' is hash-encoded by the engine
    m = write_capture(tmp_path, rs, lambda r: np.ones(2560))
    assert m["rows"][0]["capture_files"]["anchor"]["file"].startswith("row-")
    assert capture.read_row(tmp_path, m["rows"][0], hidden_state=20, sites=[])["residual"].shape == (2560,)


def test_fire_rule_matches_frozen_convention(cell):
    s = cell.cell["sensor"]
    # proj far below mu -> z clipped to -2 -> score 2 -> fire; proj far above -> score -2 -> no fire
    assert cell.fire(s["mu_d"] - 10 * s["sigma_d"])["fire"] is True
    assert cell.fire(s["mu_d"] + 10 * s["sigma_d"])["fire"] is False
    edge = cell.fire(s["mu_d"] - s["tau"] * s["sigma_d"] * -1)       # z = -tau -> score == ... boundary check below
    d = cell.fire(s["mu_d"])                                          # z = 0, score 0 >= tau(-0.59) -> fire
    assert d["fire"] is True and d["score_neg_z_d"] == 0.0 and edge["tau"] == s["tau"]
    just_above = cell.fire(s["mu_d"] - s["tau"] * s["sigma_d"] + 1e-9)    # score slightly below tau -> no fire
    assert just_above["fire"] is False


def test_fire_decisions_read_fresh_capture_dot_u_d(tmp_path, cell, project):
    u = project.u_d
    s = cell.cell["sensor"]
    projs = {"a:0": s["mu_d"] - 3 * s["sigma_d"], "a:1": s["mu_d"] + 3 * s["sigma_d"]}
    rs = [{"row_key": k, "role": "confab"} for k in projs]
    write_capture(tmp_path, rs, lambda r: projs[r["row_key"]] * u)          # residual . u_d == projs
    out = {d["row_key"]: d for d in sensor.fire_decisions(cell, tmp_path, rs, u)}
    assert out["a:0"]["fire"] is True and out["a:1"]["fire"] is False
    assert out["a:0"]["proj_d"] == pytest.approx(projs["a:0"])


def test_direction_layer_report_is_decoder_block_convention(project):
    rep = sensor.direction_layer_report(project.dir / "c_hat.json")
    assert rep["json_layer"] == 19 and rep["convention"] == "decoder_block"


# ---- localization -------------------------------------------------------------------

def _site(row, b):
    base = np.random.default_rng(int(row["row_key"].split(":")[1]) + b).standard_normal(9216)
    return base + (3.0 if row["role"] == "confab" else 0.0)


@pytest.fixture
def fit_capture(tmp_path, cell):
    rs = rows(6, "confab", "c") + rows(4, "known_correct", "k") + rows(3, "unknown_refused", "u")
    write_capture(tmp_path / "cap", rs, lambda r: np.ones(2560), _site)
    return tmp_path, rs


def test_reduction_gives_exact_role_means(fit_capture, cell):
    tmp, rs = fit_capture
    red = localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    assert red["counts"] == {"confab": 6, "known_correct": 4, "unknown_refused": 3}
    for b in (20, 21, 22):
        want = np.mean([_site(r, b).astype(np.float32).astype(np.float64) for r in rs if r["role"] == "confab"], axis=0)
        assert np.allclose(red["means"][("confab", b)], want)


def test_reduction_resumes_per_row_and_survives_a_torn_journal(fit_capture, cell, monkeypatch):
    tmp, rs = fit_capture
    real = capture.read_row
    calls = {"n": 0}

    def dying(*a, **k):
        calls["n"] += 1
        if calls["n"] == 6:
            raise KeyboardInterrupt("simulated kill")
        return real(*a, **k)

    monkeypatch.setattr(localize, "read_row", dying)
    with pytest.raises(KeyboardInterrupt):
        localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    with (tmp / "work" / "localization.runlog.jsonl").open("ab") as f:
        f.write(b'{"torn":')
    monkeypatch.setattr(localize, "read_row", real)
    counted = {"n": 0}

    def counting(*a, **k):
        counted["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(localize, "read_row", counting)
    red = localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    assert counted["n"] == len(rs) - 5 and red["recomputed_this_pass"] == len(rs) - 5   # 5 rows were already durable
    full = localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work2", blocks=[20, 21, 22])
    for key in red["means"]:
        assert np.array_equal(red["means"][key], full["means"][key])


def test_corrupt_row_file_is_recomputed_on_resume(fit_capture, cell):
    tmp, rs = fit_capture
    localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    victim = localize._row_path(tmp / "work", rs[0]["row_key"])
    victim.write_bytes(victim.read_bytes()[:-8])
    red = localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    assert red["recomputed_this_pass"] == 1


def test_changed_capture_manifest_is_a_new_run(fit_capture, cell):
    from engine_host.runlog import RunLogError

    tmp, rs = fit_capture
    localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
    m = json.loads((tmp / "cap" / "manifest.json").read_text())
    m["n_answered"] += 0
    (tmp / "cap" / "manifest.json").write_text(json.dumps(m, indent=1))
    with pytest.raises(RunLogError):
        localize.reduce_rows(cell, tmp / "cap", rs, tmp / "work", blocks=[20, 21, 22])
