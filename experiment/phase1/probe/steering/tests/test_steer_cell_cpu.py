#!/usr/bin/env python3
"""CPU-only tests for steer_cell.py config/selection paths (no torch, no model).

Covers the paths that must run without a GPU: config parse + sha, readout
projection/z-score math, the selection law (expression / permuted / flag-file /
all), the config-sha mismatch guard, and the plan command. GPU generation paths
are NOT exercised here (they need a model); the smoke-first discipline is a
runner-state contract tested at the config level.

Runs under pytest OR standalone.
"""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np

STEER_DIR = Path(__file__).resolve().parent.parent
if str(STEER_DIR) not in sys.path:
    sys.path.insert(0, str(STEER_DIR))

import steer_cell as sc  # noqa: E402


def _write(path: Path, obj) -> Path:
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def _fixture_cell(tmp: Path):
    """Build a minimal on-disk cell: rows file + one readout direction + config."""
    rows = tmp / "rows.jsonl"
    with rows.open("w") as fh:
        for i in range(6):
            fh.write(json.dumps({"row_key": f"r{i}",
                                 "question": f"q{i}"}) + "\n")
    # a 4-dim unit-ish direction with mu/sigma calibration
    direction = tmp / "dir.json"
    _write(direction, {"theta": [1.0, 0.0, 0.0, 0.0], "layer": 3,
                       "mu": 0.0, "sigma": 2.0})
    cfg_text = f"""
name: fixture_cell
surface:
  rows_file: {rows.name}
  generation:
    model: stub/tiny
    enable_thinking: false
    max_new_tokens: 8
    seed: 123
readouts:
  - name: prop
    path: {direction.name}
    layer: 3
law:
  actuation: setpoint
  actuation_readout: prop
  gain: 2.0
  position: anchor_only
arms:
  - tag: primary
    law:
      selection:
        expression: "prop_z >= 1.0"
    row_subset: flagged_only
  - tag: control
    law:
      selection:
        permuted:
          match_count: 2
  - tag: unsteered
    law:
      actuation: none
      selection:
        all: true
smoke:
  n: 4
  readback_tolerance: 0.5
outputs:
  dir: {tmp.as_posix()}/out
"""
    cfg = tmp / "cell.yaml"
    cfg.write_text(cfg_text, encoding="utf-8")
    return cfg


class TestConfigParse:
    def test_sha_stable_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = _fixture_cell(Path(d))
            _c1, sha1 = sc.load_config(cfg)
            _c2, sha2 = sc.load_config(cfg)
            assert sha1 == sha2
            cfg.write_text(cfg.read_text() + "\n# edit\n")
            _c3, sha3 = sc.load_config(cfg)
            assert sha3 != sha1

    def test_cell_structure(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = _fixture_cell(Path(d))
            cell = sc.Cell(*sc.load_config(cfg), cfg)
            assert cell.name == "fixture_cell"
            assert set(a.tag for a in cell.arms) == {"primary", "control", "unsteered"}
            assert cell.readouts["prop"].layer == 3
            assert cell.seed == 123

    def test_missing_block_raises(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "bad.yaml"
            cfg.write_text("name: x\narms: []\n")
            try:
                sc.Cell(*sc.load_config(cfg), cfg)
            except ValueError as e:
                assert "surface" in str(e)
                return
            raise AssertionError("expected ValueError on missing surface block")


class TestReadoutMath:
    def test_projection_and_zscore(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = _fixture_cell(Path(d))
            cell = sc.Cell(*sc.load_config(cfg), cfg)
            r = cell.readouts["prop"]
            # unit direction is [1,0,0,0]; projecting [4,9,9,9] gives raw=4
            raw = r.project(np.array([4.0, 9.0, 9.0, 9.0]))
            assert abs(raw - 4.0) < 1e-9
            # z = (raw - mu)/sigma = (4-0)/2 = 2.0
            assert abs(r.zscore(raw) - 2.0) < 1e-9

    def test_zscore_none_without_calibration(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            direction = _write(tmp / "d.json",
                               {"theta": [0.0, 1.0], "layer": 2})
            r = sc.Readout({"name": "x", "path": direction.name}, tmp)
            assert r.zscore(5.0) is None


class TestSelectionLaw:
    def _cell(self, tmp: Path):
        cfg = _fixture_cell(tmp)
        return sc.Cell(*sc.load_config(cfg), cfg)

    def _scores(self):
        # r0..r5 z-scores; r1,r3,r5 clear the 1.0 threshold
        zs = [0.2, 1.5, 0.9, 2.0, -0.3, 1.1]
        return {f"r{i}": {"prop_z": z, "prop_raw": z * 2.0}
                for i, z in enumerate(zs)}

    def test_expression_selection(self):
        with tempfile.TemporaryDirectory() as d:
            cell = self._cell(Path(d))
            order = [f"r{i}" for i in range(6)]
            keys = cell.arm("primary").law.select_keys(
                order, self._scores(), seed=cell.seed)
            assert keys == ["r1", "r3", "r5"]

    def test_permuted_is_count_matched_and_seeded(self):
        with tempfile.TemporaryDirectory() as d:
            cell = self._cell(Path(d))
            order = [f"r{i}" for i in range(6)]
            k1 = cell.arm("control").law.select_keys(order, {}, seed=7)
            k2 = cell.arm("control").law.select_keys(order, {}, seed=7)
            assert len(k1) == 2
            assert k1 == k2  # seeded determinism
            k3 = cell.arm("control").law.select_keys(order, {}, seed=99)
            # different seed generally differs (allow the rare coincidence off)
            assert len(k3) == 2

    def test_all_selection_returns_every_row(self):
        with tempfile.TemporaryDirectory() as d:
            cell = self._cell(Path(d))
            order = [f"r{i}" for i in range(6)]
            keys = cell.arm("unsteered").law.select_keys(order, {}, seed=1)
            assert keys == order

    def test_flag_file_selection(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg = _fixture_cell(tmp)
            flags = _write(tmp / "flags.json", {"flagged_keys": ["r2", "r4"]})
            cell = sc.Cell(*sc.load_config(cfg), cfg)
            law = sc.Law({"selection": {"flag_file": flags.name},
                          "actuation": "none"},
                         cell.readouts, cell.base_dir)
            order = [f"r{i}" for i in range(6)]
            assert law.select_keys(order, {}, seed=1) == ["r2", "r4"]

    def test_undefined_readout_in_expression_raises(self):
        with tempfile.TemporaryDirectory() as d:
            cell = self._cell(Path(d))
            law = sc.Law({"selection": {"expression": "nonexistent_z >= 1"},
                          "actuation": "none"},
                         cell.readouts, cell.base_dir)
            try:
                law.select_keys(["r0"], {"r0": {"prop_z": 1.0}}, seed=1)
            except ValueError:
                return
            raise AssertionError("expected ValueError on undefined readout")


class TestConfigShaGuard:
    def test_expected_sha_mismatch_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg = _fixture_cell(tmp)
            # inject an expected_config_sha that cannot match the file
            text = cfg.read_text().replace(
                "    seed: 123",
                "    seed: 123\n    expected_config_sha: deadbeef")
            cfg.write_text(text)
            rc = sc.main(["plan", "--config", str(cfg)])
            # plan warns (nonfatal) but the run path is fatal; plan returns 0
            assert rc == 0
            rc2 = sc.main(["run", "--config", str(cfg)])
            assert rc2 == 2  # fatal sha mismatch, before any model load


class TestPlanCommand:
    def test_plan_runs_without_torch(self, capsys=None):
        with tempfile.TemporaryDirectory() as d:
            cfg = _fixture_cell(Path(d))
            rc = sc.main(["plan", "--config", str(cfg)])
            assert rc == 0


def _run_without_pytest() -> int:
    classes = [TestConfigParse, TestReadoutMath, TestSelectionLaw,
               TestConfigShaGuard, TestPlanCommand]
    failures = 0
    total = 0
    for cls in classes:
        inst = cls()
        for name in dir(inst):
            if not name.startswith("test_"):
                continue
            total += 1
            try:
                getattr(inst, name)()
                print(f"PASS {cls.__name__}.{name}")
            except Exception:  # noqa: BLE001
                failures += 1
                print(f"FAIL {cls.__name__}.{name}")
                traceback.print_exc()
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_without_pytest())
