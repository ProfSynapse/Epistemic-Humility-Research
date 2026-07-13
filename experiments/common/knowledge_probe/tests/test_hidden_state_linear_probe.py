from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import hidden_state_linear_probe as hslp  # noqa: E402


def _write_fixture_extraction(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        ("000000000000|known_a", "known", -2.0),
        ("000000000001|known_b", "known", -1.0),
        ("000000000002|unknown_a", "unknown", 1.0),
        ("000000000003|unknown_b", "unknown", 2.0),
        ("000000000004|discard", "discard", 0.0),
    ]
    with (root / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row_key, label, _signal in rows:
            fh.write(json.dumps({
                "probe_pool_row_key": row_key,
                "question": row_key,
                "label": label,
                "layer_count": 2,
                "hidden_dim": 3,
            }) + "\n")

    for row_key, label, signal in rows:
        if label == "discard":
            continue
        safe_key = row_key.replace("|", "_")
        base = {
            "L0": np.asarray([signal, signal * 0.5, 1.0], dtype=np.float32),
            "L1": np.asarray([0.0, signal, 1.0], dtype=np.float32),
        }
        lora = {
            "L0": np.asarray([signal * 2.0, signal, 1.0], dtype=np.float32),
            "L1": np.asarray([0.0, signal * 2.0, 1.0], dtype=np.float32),
        }
        delta = {key: lora[key] - base[key] for key in base}
        save_file(base, str(root / f"{safe_key}__h_base.safetensors"))
        save_file(lora, str(root / f"{safe_key}__h_lora.safetensors"))
        save_file(delta, str(root / f"{safe_key}__delta.safetensors"))
    return root


def _write_kfold_fixture_extraction(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        ("000000000000|known_a", "known", -3.0),
        ("000000000001|known_b", "known", -2.0),
        ("000000000002|known_c", "known", -1.0),
        ("000000000003|unknown_a", "unknown", 1.0),
        ("000000000004|unknown_b", "unknown", 2.0),
        ("000000000005|unknown_c", "unknown", 3.0),
    ]
    with (root / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row_key, label, _signal in rows:
            fh.write(json.dumps({"probe_pool_row_key": row_key, "label": label}) + "\n")

    for row_key, _label, signal in rows:
        safe_key = row_key.replace("|", "_")
        save_file(
            {"L0": np.asarray([signal, signal * 0.25, 1.0], dtype=np.float32)},
            str(root / f"{safe_key}__h_base.safetensors"),
        )
    return root


def test_evaluate_writes_diagnostic_results_for_each_role_and_layer(tmp_path):
    extraction = _write_fixture_extraction(tmp_path)

    rows, metadata = hslp.evaluate(extraction, hslp.DEFAULT_ROLES, ridge=1.0)

    assert metadata["analysis_type"] == "hidden_state_linear_probe_diagnostic_smoke"
    assert "not pre-registered headline evidence" in metadata["diagnostic_notice"]
    assert metadata["cv_strategy"] == "loo"
    assert metadata["cv_folds"] == 4
    assert metadata["label_counts"] == {"known": 2, "unknown": 2}
    assert metadata["skipped_input_labels"] == {"discard": 1}
    assert {(row["role"], row["layer"]) for row in rows} == {
        ("h_base", 0), ("h_base", 1),
        ("h_lora", 0), ("h_lora", 1),
        ("delta", 0), ("delta", 1),
    }
    assert all(row["status"] == "ok" for row in rows)
    assert all(row["cv_strategy"] == "loo" for row in rows)
    assert all(row["cv_folds"] == 4 for row in rows)
    assert all(row["accuracy"] == 1.0 for row in rows)
    assert all("DIAGNOSTIC_SMOKE_ONLY" in row["diagnostic_notice"] for row in rows)


def test_main_writes_csv_and_json_to_output_dir(tmp_path):
    extraction = _write_fixture_extraction(tmp_path / "extraction")
    out_dir = tmp_path / "analysis"
    out_dir.mkdir()

    hslp.main([str(extraction), "--output-dir", str(out_dir), "--prefix", "probe"])

    csv_path = out_dir / "probe.csv"
    json_path = out_dir / "probe.json"
    assert csv_path.exists()
    assert json_path.exists()
    with csv_path.open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    assert csv_rows
    assert csv_rows[0]["diagnostic_notice"].startswith("DIAGNOSTIC_SMOKE_ONLY")
    assert csv_rows[0]["cv_strategy"] == "loo"
    assert csv_rows[0]["cv_folds"] == "4"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["strategy"].startswith("leave_one_out_ridge")
    assert payload["cv_strategy"] == "loo"
    assert payload["cv_folds"] == 4


def test_evaluate_supports_deterministic_stratified_kfold(tmp_path):
    extraction = _write_kfold_fixture_extraction(tmp_path)

    rows, metadata = hslp.evaluate(
        extraction,
        ("h_base",),
        ridge=1.0,
        cv="stratified_kfold",
        cv_folds=3,
    )

    assert metadata["strategy"].startswith("stratified_kfold_ridge")
    assert metadata["cv_strategy"] == "stratified_kfold"
    assert metadata["cv_folds"] == 3
    assert rows == [{
        "status": "ok",
        "n": 6,
        "n_known": 3,
        "n_unknown": 3,
        "correct": 6,
        "accuracy": 1.0,
        "known_accuracy": 1.0,
        "unknown_accuracy": 1.0,
        "balanced_accuracy": 1.0,
        "mean_score": rows[0]["mean_score"],
        "cv_strategy": "stratified_kfold",
        "cv_folds": 3,
        "role": "h_base",
        "layer": 0,
        "ridge": 1.0,
        "diagnostic_notice": hslp.DIAGNOSTIC_NOTICE,
    }]

    y = np.asarray([0, 0, 0, 1, 1, 1], dtype=np.int64)
    folds, _cv_info = hslp.make_cv_folds(y, "stratified_kfold", 3)
    assert [fold.tolist() for fold in folds] == [[0, 3], [1, 4], [2, 5]]


def test_evaluate_skips_when_class_counts_are_too_small(tmp_path):
    extraction = tmp_path
    with (extraction / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row_key, label, signal in [
            ("0|known_a", "known", -1.0),
            ("1|known_b", "known", -0.5),
            ("2|unknown_a", "unknown", 1.0),
        ]:
            fh.write(json.dumps({"probe_pool_row_key": row_key, "label": label}) + "\n")
            safe_key = row_key.replace("|", "_")
            save_file(
                {"L0": np.asarray([signal, 1.0], dtype=np.float32)},
                str(extraction / f"{safe_key}__h_base.safetensors"),
            )

    rows, _metadata = hslp.evaluate(extraction, ("h_base",), ridge=1.0)

    assert rows == [{
        "status": "skipped_insufficient_balanced_examples",
        "reason": "leave-one-out requires at least two examples per class",
        "n": 3,
        "n_known": 2,
        "n_unknown": 1,
        "cv_strategy": "loo",
        "cv_folds": 3,
        "role": "h_base",
        "layer": 0,
        "ridge": 1.0,
        "diagnostic_notice": hslp.DIAGNOSTIC_NOTICE,
    }]
