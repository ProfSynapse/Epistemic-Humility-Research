#!/usr/bin/env python3
"""CPU-only integration test for score_gates.py (declarative gate composition).

Builds a tiny synthetic cell + graded arm rows + gates.yaml on disk and runs the
scorer end to end, asserting each gate's verdict. No torch, no model, no network.
Runs under pytest OR standalone.
"""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

STEER_DIR = Path(__file__).resolve().parent.parent
if str(STEER_DIR) not in sys.path:
    sys.path.insert(0, str(STEER_DIR))

import score_gates as sg  # noqa: E402


def _jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _build(tmp: Path):
    out = tmp / "out"
    (out / "primary" / "gen").mkdir(parents=True)
    (out / "control" / "gen").mkdir(parents=True)

    # 10 rows: 6 baseline confabs (c0..c5), 4 baseline correct (k0..k3).
    baseline = []
    for i in range(6):
        baseline.append({"row_key": f"c{i}", "confab_on_unanswerable": True,
                         "correct": None, "answered": True})
    for i in range(4):
        baseline.append({"row_key": f"k{i}", "confab_on_unanswerable": False,
                         "correct": True, "answered": True})
    base_file = tmp / "baseline.jsonl"
    _jsonl(base_file, baseline)

    # primary: flags all confabs + all correct; kills c0..c4 (5 confabs), and
    # flips k0 to refusal (1 collateral <= 2).
    primary = []
    for i in range(6):
        killed = i < 5
        primary.append({"row_key": f"c{i}", "flagged": True,
                        "confab_on_unanswerable": not killed, "refused": killed})
    for i in range(4):
        refused = i == 0
        primary.append({"row_key": f"k{i}", "flagged": True,
                        "confab_on_unanswerable": False, "refused": refused,
                        "correct": None if refused else True})
    _jsonl(out / "primary" / "gen" / "rows.jsonl", primary)

    # control: flags a count-matched set but kills only c0 (1 confab).
    control = []
    for i in range(6):
        killed = i == 0
        control.append({"row_key": f"c{i}", "flagged": True,
                        "confab_on_unanswerable": not killed, "refused": killed})
    for i in range(4):
        control.append({"row_key": f"k{i}", "flagged": True,
                        "confab_on_unanswerable": False, "refused": False,
                        "correct": True})
    _jsonl(out / "control" / "gen" / "rows.jsonl", control)

    # a minimal cell.yaml whose out_dir points at `out`
    cell_yaml = tmp / "cell.yaml"
    cell_yaml.write_text(f"""
name: gates_fixture
surface:
  rows_file: {base_file.name}
  generation:
    model: stub/tiny
arms:
  - tag: primary
outputs:
  dir: {out.as_posix()}
""")

    gates_yaml = tmp / "gates.yaml"
    gates_yaml.write_text(f"""
seed: 20260705
arms:
  primary: primary/gen/rows.jsonl
  control: control/gen/rows.jsonl
baseline:
  rows_file: {base_file.as_posix()}
  key: row_key
predicates:
  baseline_confab: "base.get('confab_on_unanswerable') is True"
  baseline_correct: "base.get('correct') is True and base.get('answered') is True"
  steered_not_confab: "not arm.get('confab_on_unanswerable', False)"
  steered_refused: "arm.get('refused') is True"
gates:
  G1_collateral:
    kind: count_flips
    arm: primary
    before: baseline_correct
    after: steered_refused
    universe: flagged
    assert: "at_most(result.flips, 2)"
  G2_reach:
    kind: count_flips
    arm: primary
    before: baseline_confab
    after: steered_not_confab
    universe: flagged
    assert: "at_least(result.flips, 5)"
  G3_specificity:
    kind: kill_diff_vs_control
    treatment: primary
    control: control
    before: baseline_confab
    after: steered_not_confab
    assert: "at_least(result.diff, 5)"
""")
    return cell_yaml, gates_yaml, out


class TestScoreGates:
    def test_end_to_end_all_pass(self):
        with tempfile.TemporaryDirectory() as d:
            cell_yaml, gates_yaml, out = _build(Path(d))
            rc = sg.main(["--config", str(cell_yaml), "--gates", str(gates_yaml)])
            report = json.loads((out / "gates_report.json").read_text())
            g = report["gates"]
            assert g["G1_collateral"]["flips"] == 1
            assert g["G1_collateral"]["pass"] is True
            assert g["G2_reach"]["flips"] == 5
            assert g["G2_reach"]["pass"] is True
            # primary kills 5 confabs, control kills 1 -> diff 4 -> fails >= 5
            assert g["G3_specificity"]["diff"] == 4
            assert g["G3_specificity"]["pass"] is False
            assert report["overall_pass"] is False
            assert rc == 5  # nonzero because a gate failed

    def test_determinism(self):
        with tempfile.TemporaryDirectory() as d:
            cell_yaml, gates_yaml, out = _build(Path(d))
            sg.main(["--config", str(cell_yaml), "--gates", str(gates_yaml)])
            r1 = (out / "gates_report.json").read_text()
            sg.main(["--config", str(cell_yaml), "--gates", str(gates_yaml)])
            r2 = (out / "gates_report.json").read_text()
            assert r1 == r2


def _run_without_pytest() -> int:
    inst = TestScoreGates()
    failures = 0
    total = 0
    for name in dir(inst):
        if not name.startswith("test_"):
            continue
        total += 1
        try:
            getattr(inst, name)()
            print(f"PASS TestScoreGates.{name}")
        except Exception:  # noqa: BLE001
            failures += 1
            print(f"FAIL TestScoreGates.{name}")
            traceback.print_exc()
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_without_pytest())
