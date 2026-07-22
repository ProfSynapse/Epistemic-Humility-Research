from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save_file

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "surface_control", HERE / "reanalyze_surface_diversity.py"
)
assert SPEC is not None and SPEC.loader is not None
control = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = control
SPEC.loader.exec_module(control)


def config() -> dict:
    return control.load_yaml(HERE / "cell.yaml")


def test_surface_features_exclude_role_and_behavior() -> None:
    rows = []
    for i in range(40):
        rows.append(
            {
                "row_key": f"ahx::kuq_ku_unknown_x::{i:06d}",
                "role": "confab" if i % 2 else "unknown_refused",
                "question": f"Question {i}: WHO is item {i % 7}?",
                "rendered_prompt_token_count": 20 + i % 5,
                "render_template_id": "synthetic",
                "category_canon": f"c{i % 3}",
                "answer_text": "must not enter Z",
                "baseline_behavior": i,
            }
        )
    features = control.build_surface_features(rows, config())
    assert features.combined.shape[0] == len(rows)
    assert features.scalar_names == control.SCALAR_COLUMNS
    flipped = [dict(r, role="known_correct_answered", answer_text="changed") for r in rows]
    flipped_features = control.build_surface_features(flipped, config())
    np.testing.assert_allclose(features.combined, flipped_features.combined)


def test_nested_crossfit_removes_surface_signal() -> None:
    rng = np.random.default_rng(7)
    n, p, d = 120, 7, 16
    z = rng.normal(size=(n, p))
    h = z @ rng.normal(size=(p, d)) + rng.normal(scale=0.1, size=(n, d))
    strata = np.asarray([f"s{i % 4}" for i in range(n)])
    residual, predicted, alphas = control.crossfit_ridge(
        h, z, strata, [0.01, 0.1, 1.0, 10.0], 5, 3, 11
    )
    assert len(alphas) == 5
    assert np.mean(residual**2) < 0.05 * np.mean(h**2)
    assert predicted.shape == h.shape


def test_propensity_matching_reports_aggregate_diagnostics() -> None:
    rng = np.random.default_rng(9)
    n = 240
    z = rng.normal(size=(n, 8))
    scalars = z[:, :4]
    roles = np.asarray(["confab"] * (n // 2) + ["unknown_refused"] * (n // 2))
    result = control.match_on_propensity(
        z,
        scalars,
        roles,
        np.asarray(["kuq"] * n),
        "confab",
        "unknown_refused",
        folds=5,
        seed=13,
    )
    assert result.n_pairs == n // 2
    assert np.isfinite(result.max_abs_scalar_smd)
    assert 0.0 <= result.heldout_surface_role_auroc <= 1.0


def test_peak_boundary_is_inclusive() -> None:
    profile = np.zeros(11)
    profile[2] = 2.0
    profile[3] = 1.0
    report = control.peak_summary(profile, early_max_depth=0.20)
    assert report["peak_depth"] == pytest.approx(0.20)
    assert report["classification"] == "early-exterior"


def test_checkpoint_refuses_fingerprint_mismatch(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(control, "ANALYSIS_ROOT", tmp_path.resolve())
    path = tmp_path / "checkpoints" / "unit.json"
    control.write_checkpoint(path, "one", "layer-2", {"complete": True})
    assert control.read_checkpoint(path, "one", "layer-2") == {"complete": True}
    with pytest.raises(control.ControlError, match="fingerprint mismatch"):
        control.read_checkpoint(path, "two", "layer-2")


def test_output_containment_and_private_text_scan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(control, "ANALYSIS_ROOT", tmp_path.resolve())
    payload = {
        "schema_version": 1,
        "report_kind": "preflight",
        "experiment": "synthetic",
        "config_fingerprint": "x",
        "substrates": {
            "gemma": {
                "provenance": {
                    "model_revision_match": True,
                    "capture_coverage": 1.0,
                    "n_hidden_states": 5,
                    "hidden_size": 8,
                    "activation_content_sha256": "c",
                    "activation_file_count": 1,
                    "files": {
                        name: {"path_sha256": "a", "file_sha256": "b", "record_count": 1}
                        for name in (
                            "capture_manifest",
                            "split_manifest",
                            "atlas_summary",
                            "capture_index",
                            "capture_input",
                            "private_rows",
                            "estimator_module",
                        )
                    },
                    "counts": {
                        "split_rows": 1,
                        "capture_index": 1,
                        "capture_input": 1,
                        "private_rows": 1,
                        "joined_rows": 1,
                        "fit_rows": 1,
                    },
                    "fit_role_counts": {
                        "confab": 1,
                        "known_correct_answered": 0,
                        "unknown_refused": 0,
                    },
                    "required_field_coverage": {
                        "role": 1,
                        "split": 1,
                        "question": 1,
                        "source": 1,
                        "category": 1,
                        "render_template_id": 1,
                        "prompt_token_count": 1,
                    },
                    "missing_counts": {
                        "capture_index": 0,
                        "capture_input": 0,
                        "private_rows": 0,
                        "capture_files": 0,
                        "question": 0,
                        "token_count": 0,
                        "activation_rows": 0,
                    },
                }
            }
        },
        "gates": {key: "not_run" for key in ("G0", "G1", "G2", "G3", "G4", "G5")},
        "decision": {"status": "preflight", "reason": "safe"},
    }
    path = tmp_path / "aggregate_results.json"
    control.write_aggregate(path, payload, {"private question contents"})
    control.write_aggregate(path, payload, {"private question contents"}, {"gemma"})
    assert json.loads(path.read_text())["decision"]["status"] == "preflight"
    for alternate in ("prompt_text", "input_text", "reference_answer"):
        bad = json.loads(json.dumps(payload))
        bad["substrates"]["gemma"][alternate] = "not accepted"
        with pytest.raises(control.ControlError, match="positive schema"):
            control.write_aggregate(path, bad, set(), {"gemma"})
    nested = json.loads(json.dumps(payload))
    nested["gates"]["G0"] = {"prompt_text": "hidden"}
    with pytest.raises(control.ControlError, match="scalar strings or booleans"):
        control.write_aggregate(path, nested, set(), {"gemma"})
    short = json.loads(json.dumps(payload))
    short["decision"]["reason"] = "abc"
    with pytest.raises(control.ControlError, match="exact private text"):
        control.write_aggregate(path, short, {"abc"}, {"gemma"})
    with pytest.raises(control.ControlError, match="outside experiment analysis root"):
        control.write_aggregate(tmp_path.parent / "bad.json", payload, set(), {"gemma"})


def test_real_run_is_fail_closed_without_sources() -> None:
    rc = control.main(["run", "--substrates", "gemma4_e4b_it"])
    assert rc == 2


def test_synthetic_check_reaches_registered_control() -> None:
    report = control.synthetic_check(config())
    assert report["ridge_reachability"] is True
    assert report["planted_removal_reachability"] is True
    assert report["registered_hs2_unique_peak"] is True
    assert report["registered_hs2_relocated"] is True
    assert report["registered_profile_tolerance"] is True


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_source_adapter_joins_and_loads_safetensors(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "atlas"
    committed = root / "analysis-committed" / "cell"
    capture_dir = root / "analysis" / "cell" / "atlas_capture"
    committed.mkdir(parents=True)
    capture_dir.mkdir(parents=True)
    n_rows, n_layers, width = 12, 5, 8
    roles = ["confab"] * 4 + ["known_correct_answered"] * 4 + ["unknown_refused"] * 4
    splits = ["fit"] * 8 + ["fit_only"] * 4
    split_rows = []
    index_rows = []
    input_rows = []
    private_rows = []
    matrices = [np.empty((n_rows, width), dtype=np.float64) for _ in range(n_layers)]
    rng = np.random.default_rng(4)
    for i in range(n_rows):
        row_id = f"ahx::kuq_ku_unknown_x::{i:06d}"
        split_rows.append(
            {"row_key": row_id, "role": roles[i], "split": splits[i], "source": "kuq", "category_canon": "x"}
        )
        input_rows.append({"id": row_id, "token_ids": [1, 2, 3], "positions": {"anchor": 2}})
        private_rows.append(
            {"row_key": row_id, "question": f"Synthetic question {i}?", "source": "kuq", "category_canon": "x"}
        )
        tensors = {}
        for layer in range(n_layers):
            vector = rng.normal(size=width).astype(np.float32)
            matrices[layer][i] = vector
            tensors[f"anchor__L{layer}"] = vector
        filename = f"row_{i}.safetensors"
        save_file(tensors, capture_dir / filename)
        index_rows.append(
            {"id": row_id, "file": filename, "hidden_dim": width, "n_layers": n_layers, "positions": {"anchor": 2}}
        )
    (committed / "split_manifest.json").write_text(json.dumps({"rows": split_rows}))
    _write_jsonl(capture_dir / "capture.jsonl", index_rows)
    _write_jsonl(root / "analysis" / "cell" / "atlas_capture_rows.jsonl", input_rows)
    private_path = tmp_path / "private.jsonl"
    _write_jsonl(private_path, private_rows)
    estimator_path = root / "profile_and_read_family_atlas_panel.py"
    estimator_path.write_text(
        "import numpy as np\n"
        "def eff_dim_frac(mat):\n"
        " x=mat.astype(np.float64); x=x-x.mean(0,keepdims=True); g=x@x.T/max(len(x)-1,1); e=np.clip(np.linalg.eigvalsh(g),0,None); return float((e.sum()**2/max((e**2).sum(),1e-30))/len(x))\n"
    )
    spec_module = importlib.util.spec_from_file_location("fixture_est", estimator_path)
    fixture_est = importlib.util.module_from_spec(spec_module)
    assert spec_module is not None and spec_module.loader is not None
    spec_module.loader.exec_module(fixture_est)
    per_layer = {
        str(layer): {"profile": {"eff_dim_frac": fixture_est.eff_dim_frac(matrices[layer])}}
        for layer in range(n_layers)
    }
    (committed / "atlas_summary.json").write_text(json.dumps({"per_layer": per_layer}))
    (committed / "capture_manifest.json").write_text(
        json.dumps(
            {
                "model": "fixture/model",
                "revision": "rev",
                "n_rows_captured": n_rows,
                "n_hidden_states": n_layers,
                "hidden_size": width,
                "coverage_frac": 1.0,
            }
        )
    )
    monkeypatch.setenv("FIXTURE_ROOT", str(root))
    monkeypatch.setenv("FIXTURE_ROWS", str(private_path))
    spec = {
        "atlas_root_env": "FIXTURE_ROOT",
        "private_rows_env": "FIXTURE_ROWS",
        "committed_dir": "analysis-committed/cell",
        "capture_dir": "analysis/cell/atlas_capture",
        "capture_input": "analysis/cell/atlas_capture_rows.jsonl",
        "estimator_module": "profile_and_read_family_atlas_panel.py",
        "model": "fixture/model",
        "revision": "rev",
        "expected_rows": n_rows,
        "expected_fit_rows": n_rows,
        "n_hidden_states": n_layers,
        "hidden_size": width,
    }
    data = control.load_source_data("fixture", spec)
    assert data.provenance["counts"]["joined_rows"] == n_rows
    assert data.provenance["missing_counts"] == {key: 0 for key in data.provenance["missing_counts"]}
    np.testing.assert_allclose(control.load_activation_layer(data, 3), matrices[3])
    pinned_spec = dict(
        spec,
        expected_activation_content_sha256=data.provenance[
            "activation_content_sha256"
        ],
    )
    swapped = [dict(row) for row in index_rows]
    swapped[0]["file"], swapped[1]["file"] = swapped[1]["file"], swapped[0]["file"]
    _write_jsonl(capture_dir / "capture.jsonl", swapped)
    with pytest.raises(control.ControlError, match="activation-content digest mismatch"):
        control.load_source_data("fixture", pinned_spec)
    _write_jsonl(capture_dir / "capture.jsonl", index_rows)
    mutated = {
        f"anchor__L{layer}": np.full(width, layer + 0.5, dtype=np.float32)
        for layer in range(n_layers)
    }
    save_file(mutated, capture_dir / index_rows[0]["file"])
    with pytest.raises(control.ControlError, match="activation-content digest mismatch"):
        control.load_source_data("fixture", pinned_spec)
    result_payload = {
        "schema_version": 1,
        "report_kind": "result",
        "experiment": "synthetic",
        "config_fingerprint": "fixture",
        "substrates": {
            "fixture": control._empty_result(
                data, {key: False for key in ("G0", "G1", "G2", "G3", "G4", "G5")}
            )
        },
        "gates": {key: "fail" for key in ("G0", "G1", "G2", "G3", "G4", "G5")},
        "decision": {"status": "indeterminate", "reason": "fixture"},
    }
    control.validate_aggregate(result_payload, {"fixture"})


def test_gate_adjudication_distinguishes_falsification_from_indeterminate() -> None:
    passed = {key: True for key in ("G0", "G1", "G2", "G3", "G4", "G5")}
    gates, decision = control.adjudicate_results({"gemma": {"gates": passed}})
    assert gates["G5"] == "pass"
    assert decision["status"] == "pass"
    falsified = dict(passed, G5=False)
    _, decision = control.adjudicate_results({"gemma": {"gates": falsified}})
    assert decision["status"] == "falsified"
    indeterminate = dict(passed, G2=False, G5=False)
    _, decision = control.adjudicate_results({"gemma": {"gates": indeterminate}})
    assert decision["status"] == "indeterminate"


def test_incremental_crossfit_checkpoint_resumes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(control, "ANALYSIS_ROOT", tmp_path.resolve())
    rng = np.random.default_rng(12)
    z = rng.normal(size=(80, 5))
    h = z @ rng.normal(size=(5, 9)) + rng.normal(scale=0.2, size=(80, 9))
    strata = np.asarray([f"s{i % 4}" for i in range(80)])
    base = tmp_path / "checkpoints" / "combined" / "hs2"
    first = control.crossfit_ridge_incremental(
        h, z, strata, [0.1, 1.0], 5, 3, 99, base, "fingerprint", "unit"
    )
    # Simulate a kill after two outer folds by retaining only those predictions.
    labels = control._make_strata(strata, 5)
    folds = list(control.StratifiedKFold(n_splits=5, shuffle=True, random_state=99).split(z, labels))
    partial_yhat = np.full_like(first[1], np.nan)
    for _, test in folds[:2]:
        partial_yhat[test] = first[1][test]
    with base.with_suffix(".npz").open("wb") as fh:
        np.savez_compressed(fh, yhat=partial_yhat)
    control.write_checkpoint(
        base.with_suffix(".json"),
        "fingerprint",
        "unit",
        {"completed_folds": 2, "chosen_alphas": first[2][:2]},
    )
    second = control.crossfit_ridge_incremental(
        h, z, strata, [0.1, 1.0], 5, 3, 99, base, "fingerprint", "unit"
    )
    np.testing.assert_allclose(first[0], second[0])
    np.testing.assert_allclose(first[1], second[1])
    assert first[2] == second[2]
    meta = json.loads(base.with_suffix(".json").read_text())
    assert meta["payload"]["completed_folds"] == 5


def test_planted_hs2_uses_paired_registered_partitions_and_tolerance() -> None:
    cfg = config()
    hs2 = int(cfg["planted_signal"]["hs_index"])
    unplanted_seed = control.registered_layer_seed(cfg, hs2)
    planted_seed = control.registered_planted_seed(cfg)
    assert planted_seed == unplanted_seed
    strata = np.asarray([f"s{i % 4}" for i in range(80)])
    labels = control._make_strata(strata, 5)
    unplanted_folds = [
        test.tolist()
        for _, test in control.StratifiedKFold(
            n_splits=5, shuffle=True, random_state=unplanted_seed
        ).split(np.zeros((80, 1)), labels)
    ]
    planted_folds = [
        test.tolist()
        for _, test in control.StratifiedKFold(
            n_splits=5, shuffle=True, random_state=planted_seed
        ).split(np.zeros((80, 1)), labels)
    ]
    assert planted_folds == unplanted_folds
    unplanted_profile = [1.0, 2.0, 4.0]
    planted_profile = [1.0, 2.0, 4.1]
    assert control.paired_profile_deviation(unplanted_profile, planted_profile) == pytest.approx(0.025)
