from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file, save_file

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import hidden_state_directions as hsd  # noqa: E402


def _write_fixture_extraction(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        ("000000000000|known_a", "known", np.asarray([1.0, 0.0], dtype=np.float32)),
        ("000000000001|known_b", "known", np.asarray([1.0, 2.0], dtype=np.float32)),
        ("000000000002|unknown_a", "unknown", np.asarray([3.0, 2.0], dtype=np.float32)),
        ("000000000003|unknown_b", "unknown", np.asarray([3.0, 4.0], dtype=np.float32)),
        ("000000000004|discard", "discard", np.asarray([9.0, 9.0], dtype=np.float32)),
    ]
    with (root / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row_key, label, _base_l0 in rows:
            fh.write(json.dumps({
                "probe_pool_row_key": row_key,
                "label": label,
                "layer_count": 2,
                "hidden_dim": 2,
            }) + "\n")
    (root / "manifest.json").write_text(
        json.dumps({"status": "ok", "verified": True}),
        encoding="utf-8",
    )

    for row_key, label, base_l0 in rows:
        if label == "discard":
            continue
        safe_key = row_key.replace("|", "_")
        base = {
            "L0": base_l0,
            "L1": base_l0 + np.asarray([0.0, 10.0], dtype=np.float32),
        }
        delta_shift = (
            np.asarray([0.0, 2.0], dtype=np.float32)
            if label == "known"
            else np.asarray([0.0, 4.0], dtype=np.float32)
        )
        delta = {key: delta_shift for key in base}
        lora = {key: base[key] + delta[key] for key in base}
        save_file(base, str(root / f"{safe_key}__h_base.safetensors"))
        save_file(lora, str(root / f"{safe_key}__h_lora.safetensors"))
        save_file(delta, str(root / f"{safe_key}__delta.safetensors"))
    return root


def _by_key(rows: list[dict]) -> dict[tuple[str, str, int], dict]:
    return {
        (row["method"], row["role"], row["layer"]): row
        for row in rows
        if row["status"] == "ok"
    }


def test_derive_directions_builds_known_unknown_and_delta_candidates(tmp_path):
    extraction = _write_fixture_extraction(tmp_path)

    rows, manifest = hsd.derive_directions(extraction)

    assert manifest["analysis_type"] == hsd.ANALYSIS_TYPE
    assert "not a steering run" in manifest["notice"]
    assert manifest["label_counts"] == {"known": 2, "unknown": 2}
    assert manifest["skipped_input_labels"] == {"discard": 1}
    assert manifest["source_hashes"]["rows_jsonl_sha256"]
    assert manifest["source_hashes"]["manifest_json_sha256"]

    ok_rows = [row for row in rows if row["status"] == "ok"]
    assert len(ok_rows) == 12
    assert {
        (row["method"], row["role"], row["layer"], row["contrast"])
        for row in ok_rows
    } >= {
        ("known_unknown_diff", "h_base", 0, "unknown_minus_known"),
        ("known_unknown_diff", "h_lora", 1, "unknown_minus_known"),
        ("known_unknown_diff", "delta", 0, "unknown_minus_known"),
        ("arm_delta_mean", "delta", 0, "all_mean_lora_minus_base"),
        ("arm_delta_mean", "delta", 1, "known_mean_lora_minus_base"),
        ("arm_delta_mean", "delta", 1, "unknown_mean_lora_minus_base"),
    }
    assert all(row["vector_file"].startswith("directions/") for row in ok_rows)
    assert all(np.isclose(row["unit_norm"], 1.0) for row in ok_rows)


def test_main_writes_csv_manifest_and_direction_tensors(tmp_path):
    extraction = _write_fixture_extraction(tmp_path / "extraction")
    out_dir = tmp_path / "directions_out"

    hsd.main([str(extraction), "--output-dir", str(out_dir), "--prefix", "candidates"])

    csv_path = out_dir / "candidates.csv"
    manifest_path = out_dir / "candidates.manifest.json"
    assert csv_path.exists()
    assert manifest_path.exists()

    with csv_path.open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    assert csv_rows
    first = csv_rows[0]
    assert first["notice"].startswith("EXPLORATORY_DIRECTION_CANDIDATES")
    assert first["vector_file"].startswith("directions/")
    tensor_path = out_dir / first["vector_file"]
    assert tensor_path.exists()
    tensor = load_file(str(tensor_path))["direction"]
    assert tensor.shape == (2,)
    assert np.isclose(np.linalg.norm(tensor.astype(np.float64)), 1.0)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["analysis_type"] == hsd.ANALYSIS_TYPE
    assert "_vector" not in payload["directions"][0]
    assert payload["directions"][0]["vector_file"] == first["vector_file"]


def test_known_unknown_direction_convention_is_unknown_minus_known(tmp_path):
    extraction = _write_fixture_extraction(tmp_path)

    rows, _manifest = hsd.derive_directions(
        extraction,
        roles=("h_base",),
        methods=("known_unknown_diff",),
    )
    row = _by_key(rows)[("known_unknown_diff", "h_base", 0)]
    vector = row.pop("_vector")

    expected = np.asarray([2.0, 2.0], dtype=np.float32)
    expected = expected / np.linalg.norm(expected)
    assert row["contrast"] == "unknown_minus_known"
    assert np.allclose(vector, expected)
    assert row["n_positive"] == 2
    assert row["n_negative"] == 2


def test_missing_role_is_recorded_as_skipped(tmp_path):
    extraction = _write_fixture_extraction(tmp_path)

    rows, _manifest = hsd.derive_directions(extraction, roles=("delta",))
    for shard in extraction.glob("*__delta.safetensors"):
        shard.unlink()
    skipped_rows, _skipped_manifest = hsd.derive_directions(extraction, roles=("delta",))

    assert rows
    assert skipped_rows == [hsd.skipped_direction(
        role="delta",
        layer="",
        method="load_role",
        reason="no 'delta' safetensors shards found",
    )]
