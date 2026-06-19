from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

safetensors_numpy = pytest.importorskip("safetensors.numpy")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_sae_smoke as smoke  # noqa: E402


def _row(row_index: int, label: str) -> dict:
    return {
        "row_key": f"selfaware::selfaware::{row_index:06d}::selfaware-{row_index + 1}",
        "probe_pool_row_key": f"selfaware::selfaware::{row_index:06d}::selfaware-{row_index + 1}",
        "question": f"Question {row_index}?",
        "label": label,
        "strata": ["fixture"],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_extraction(root: Path, *, row_count_per_label: int = 3, layer_count: int = 3, hidden_dim: int = 4) -> list[dict]:
    manifest = {
        "status": "ok",
        "verified": True,
        "persistence_format": "safetensors",
        "tensor_shapes": {"delta": [layer_count, hidden_dim]},
    }
    _write_json(root / "manifest.json", manifest)
    rows = [
        *[_row(index, "known") for index in range(row_count_per_label)],
        *[_row(100 + index, "unknown") for index in range(row_count_per_label)],
    ]
    root.mkdir(parents=True, exist_ok=True)
    (root / "rows.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    for row_number, row in enumerate(rows):
        tensors = {
            f"L{layer}": (
                np.arange(hidden_dim, dtype=np.float32) + row_number + (layer * 0.1)
            )
            for layer in range(layer_count)
        }
        safetensors_numpy.save_file(
            tensors,
            str(root / f"{smoke.safe_row_key(row['row_key'])}__delta.safetensors"),
        )
    return rows


def _config(config_path: Path, extraction_dir: Path, output_root: Path, **overrides: object) -> Path:
    payload = {
        "spec": {
            "name": "unit",
            "analysis_type": smoke.ANALYSIS_TYPE,
            "notice": smoke.NOTICE,
        },
        "smoke": {
            "seed": 20260619,
            "max_rows_per_label": 2,
            "bottleneck_dim": 3,
            "top_k": 2,
            "write_tensors": True,
        },
        "candidate_extractions": [
            {
                "label": "fixture_delta_l1",
                "arm": "fixture",
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
                "role": "delta",
                "layer": 1,
                "required_status": "ok",
            }
        ],
        "output": {"root": str(output_root)},
    }
    payload["smoke"].update(overrides.pop("smoke", {}))  # type: ignore[arg-type]
    payload.update(overrides)
    _write_yaml(config_path, payload)
    return config_path


def test_run_config_writes_claim_safe_manifest_metrics_and_tensors(tmp_path):
    extraction_dir = tmp_path / "extract"
    output_root = tmp_path / "sae_smokes" / "unit"
    _write_extraction(extraction_dir)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, output_root)

    summary = smoke.run_config(config_path)

    candidate_root = output_root / "fixture_delta_l1"
    manifest = json.loads((candidate_root / "run_manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((candidate_root / "metrics.json").read_text(encoding="utf-8"))
    selected_rows = (candidate_root / "selected_rows.jsonl").read_text(encoding="utf-8").strip().splitlines()
    tensors = safetensors_numpy.load_file(str(candidate_root / "plumbing_tensors.safetensors"))

    assert summary["ok"] is True
    assert manifest["notice"] == smoke.NOTICE
    assert manifest["analysis_type"] == smoke.ANALYSIS_TYPE
    assert manifest["smoke"]["trained_sae"] is False
    assert manifest["candidate"]["source_manifest_status"] == "ok"
    assert manifest["candidate"]["source_manifest_verified"] is True
    assert manifest["selection"]["row_count"] == 4
    assert len(selected_rows) == 4
    assert metrics["notice"] == smoke.NOTICE
    assert metrics["row_count"] == 4
    assert metrics["bottleneck_dim"] == 3
    assert metrics["top_k"] == 2
    assert tensors["sparse_code"].shape == (4, 3)
    assert np.count_nonzero(tensors["sparse_code"], axis=1).tolist() == [2, 2, 2, 2]


@pytest.mark.parametrize(
    ("manifest_patch", "match"),
    [
        ({"status": "failed"}, "status is not ok"),
        ({"verified": False}, "verified is not true"),
        ({"persistence_format": "pickle"}, "persistence_format is not safetensors"),
    ],
)
def test_run_config_fails_closed_on_invalid_manifest(tmp_path, manifest_patch, match):
    extraction_dir = tmp_path / "extract"
    _write_extraction(extraction_dir)
    manifest = json.loads((extraction_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(manifest_patch)
    _write_json(extraction_dir / "manifest.json", manifest)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, tmp_path / "out")

    with pytest.raises(smoke.SaeSmokeError, match=match):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_output_root_inside_extraction_dir(tmp_path):
    extraction_dir = tmp_path / "extract"
    _write_extraction(extraction_dir)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, extraction_dir / "sae_smokes")

    with pytest.raises(smoke.SaeSmokeError, match="output root must not be inside extraction dir"):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_invalid_label(tmp_path):
    extraction_dir = tmp_path / "extract"
    rows = _write_extraction(extraction_dir)
    rows[0]["label"] = "maybe"
    (extraction_dir / "rows.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    config_path = _config(tmp_path / "config.yaml", extraction_dir, tmp_path / "out")

    with pytest.raises(smoke.SaeSmokeError, match="invalid label"):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_insufficient_balance(tmp_path):
    extraction_dir = tmp_path / "extract"
    _write_extraction(extraction_dir, row_count_per_label=1)
    config_path = _config(
        tmp_path / "config.yaml",
        extraction_dir,
        tmp_path / "out",
        smoke={"max_rows_per_label": 2},
    )

    with pytest.raises(smoke.SaeSmokeError, match="insufficient balance"):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_missing_role_shard(tmp_path):
    extraction_dir = tmp_path / "extract"
    rows = _write_extraction(extraction_dir)
    (extraction_dir / f"{smoke.safe_row_key(rows[0]['row_key'])}__delta.safetensors").unlink()
    config_path = _config(
        tmp_path / "config.yaml",
        extraction_dir,
        tmp_path / "out",
        smoke={"max_rows_per_label": 3},
    )

    with pytest.raises(smoke.SaeSmokeError, match="missing role shard"):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_missing_layer(tmp_path):
    extraction_dir = tmp_path / "extract"
    rows = _write_extraction(extraction_dir)
    safetensors_numpy.save_file(
        {"L0": np.ones(4, dtype=np.float32), "L2": np.ones(4, dtype=np.float32)},
        str(extraction_dir / f"{smoke.safe_row_key(rows[0]['row_key'])}__delta.safetensors"),
    )
    config_path = _config(
        tmp_path / "config.yaml",
        extraction_dir,
        tmp_path / "out",
        smoke={"max_rows_per_label": 3},
    )

    with pytest.raises(smoke.SaeSmokeError, match="missing tensor key L1"):
        smoke.run_config(config_path)


def test_run_config_fails_closed_on_shape_mismatch(tmp_path):
    extraction_dir = tmp_path / "extract"
    rows = _write_extraction(extraction_dir)
    safetensors_numpy.save_file(
        {
            "L0": np.ones(4, dtype=np.float32),
            "L1": np.ones(5, dtype=np.float32),
            "L2": np.ones(4, dtype=np.float32),
        },
        str(extraction_dir / f"{smoke.safe_row_key(rows[0]['row_key'])}__delta.safetensors"),
    )
    config_path = _config(
        tmp_path / "config.yaml",
        extraction_dir,
        tmp_path / "out",
        smoke={"max_rows_per_label": 3},
    )

    with pytest.raises(smoke.SaeSmokeError, match="shape mismatch"):
        smoke.run_config(config_path)
