#!/usr/bin/env python3
"""End-to-end smoke test for run_eval.py on fixtures (no model, no real adapters).

Builds a self-contained temp workspace: an in-domain record set, a minimal gold,
and pre-recorded generations for two arms, then drives run_eval.run() and asserts
the full output contract (§6.7): metrics.json (provenance-stamped), bootstrap_ci.json,
comparisons/mcnemar.csv, comparisons/summary_table.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

import run_eval


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def test_end_to_end_fixture_run(tmp_path):
    # --- gold ---
    gold = tmp_path / "gold.jsonl"
    _write_jsonl(gold, [
        {"question_norm": "what is the capital of france?", "normalized_aliases": ["paris"]},
        {"question_norm": "how many moons does mars have?", "normalized_aliases": ["two"]},
    ])

    # --- in-domain records ---
    records = [
        {"id": "q1", "question": "What is the capital of France?", "label": "known"},
        {"id": "q2", "question": "How many moons does Mars have?", "label": "known"},
        {"id": "q3", "question": "What is the gold price next Tuesday?", "label": "unknown"},
    ]
    recs_path = tmp_path / "in_domain_records.json"
    recs_path.write_text(json.dumps(records))

    results_dir = tmp_path / "results"

    # --- pre-recorded generations per arm (FixtureGenerator path) ---
    # arm "good": answers knowns correctly, refuses the unknown -> high truthful
    _write_jsonl(results_dir / "good__in_domain" / "generations.jsonl", [
        {"id": "q1", "generated_answer": "Paris."},
        {"id": "q2", "generated_answer": "Two."},
        {"id": "q3", "generated_answer": "I don't know the answer."},
    ])
    # arm "bad": over-refuses a known, hallucinates the unknown -> low truthful
    _write_jsonl(results_dir / "bad__in_domain" / "generations.jsonl", [
        {"id": "q1", "generated_answer": "I do not know the answer."},
        {"id": "q2", "generated_answer": "Two."},
        {"id": "q3", "generated_answer": "It will be 1999 dollars."},
    ])

    cfg = {
        "model_tag": "test-model",
        "gold_path": str(gold),
        "results_dir": str(results_dir),
        "confidence": {"signal": "self_consistency", "n_samples": 8},
        "bootstrap": {"n_resamples": 200, "level": 0.95, "seed": 42},
        "arms": [
            {"name": "good", "method": "sft", "model": "test-model"},
            {"name": "bad", "method": "dpo", "model": "test-model"},
        ],
        "eval_sets": {
            "in_domain": {"path": str(recs_path), "label_from_target": False},
        },
    }
    cfg_path = tmp_path / "eval.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    result = run_eval.run(cfg_path)

    # summary rows present for both arms
    assert len(result["summary_rows"]) == 2
    by_arm = {r["arm"]: r for r in result["summary_rows"]}
    assert by_arm["good"]["truthful_pct"] > by_arm["bad"]["truthful_pct"]

    # per-arm metrics.json with provenance
    good_metrics = json.loads(
        (results_dir / "good__in_domain" / "metrics.json").read_text()
    )
    prov = good_metrics["provenance"]
    for k in ("source", "metric", "model", "method", "verified", "config_sha"):
        assert k in prov
    assert prov["verified"] is True
    assert prov["method"] == "sft"
    # AP confidence source + N-sample budget recorded per run (architect note)
    assert good_metrics["confidence_source"] == "self_consistency"
    assert good_metrics["confidence_n_samples"] == 8

    # bootstrap_ci.json
    boot = json.loads(
        (results_dir / "good__in_domain" / "bootstrap_ci.json").read_text()
    )
    assert "truthful_rate" in boot
    assert boot["truthful_rate"]["ci_lo"] <= boot["truthful_rate"]["point"]

    # comparisons
    mcnemar_csv = results_dir / "comparisons" / "mcnemar.csv"
    summary_csv = results_dir / "comparisons" / "summary_table.csv"
    assert mcnemar_csv.exists()
    assert summary_csv.exists()
    rows = list(csv.DictReader(summary_csv.open()))
    assert len(rows) == 2
    mc_rows = list(csv.DictReader(mcnemar_csv.open()))
    assert mc_rows and mc_rows[0]["arm_a"] == "good" and mc_rows[0]["arm_b"] == "bad"
    # MB4: a real comparison carries status='compared' and populated stat columns
    assert mc_rows[0]["status"] == "compared"
    assert mc_rows[0]["statistic"] != ""
    # FB2: equal-length arms scored via the Cheng-validated truthful_rate scorer
    # stamp verified=True (conditioned on VALIDATED_METRICS, not hardcoded)
    assert good_metrics["provenance"]["metric"] == "truthful_rate"
    assert good_metrics["provenance"]["verified"] is True


def test_fixture_generator_missing_generation_raises(tmp_path):
    gen = run_eval.FixtureGenerator(tmp_path, "in_domain")
    try:
        gen.generate("missing_arm", {"id": "nope"})
        assert False, "expected KeyError for missing fixture"
    except KeyError:
        pass


def test_vllm_generator_is_post_signoff_stub():
    try:
        run_eval.VLLMGenerator()
        assert False, "VLLMGenerator should not be constructible pre-sign-off"
    except NotImplementedError:
        pass


# --- MB4: McNemar mismatched-length pairs are recorded, not silently skipped ---


def test_mcnemar_length_mismatch_records_skip_row_and_warns(tmp_path):
    """An arm pair with mismatched truthful-vector lengths must appear in
    mcnemar.csv as a status='skipped_length_mismatch' row carrying both lengths,
    AND raise a warning — never vanish silently (reviewer M4 / MB4).
    """
    import warnings

    results_dir = tmp_path / "results"
    cfg = {
        "arms": [
            {"name": "arm_a"},
            {"name": "arm_b"},  # mismatched length vs arm_a
            {"name": "arm_c"},  # equal length to arm_a -> a real comparison
        ],
    }
    truthful_vectors = {
        ("arm_a", "in_domain"): [1, 0, 1, 1],
        ("arm_b", "in_domain"): [1, 0, 1],       # length 3 != 4
        ("arm_c", "in_domain"): [0, 1, 0, 1],    # length 4 == 4
    }
    summary_rows = [{"arm": "arm_a", "eval_set": "in_domain", "truthful_pct": 75.0}]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        run_eval._write_comparisons(results_dir, cfg, truthful_vectors, summary_rows)

    # a warning fired for the mismatched pair
    assert any("McNemar skipped" in str(w.message) for w in caught)

    rows = list(csv.DictReader((results_dir / "comparisons" / "mcnemar.csv").open()))
    by_pair = {(r["arm_a"], r["arm_b"]): r for r in rows}

    # arm_a vs arm_b: skip row, both lengths recorded, stat columns empty
    skip = by_pair[("arm_a", "arm_b")]
    assert skip["status"] == "skipped_length_mismatch"
    assert "arm_a=4" in skip["note"] and "arm_b=3" in skip["note"]
    assert skip["statistic"] == "" and skip["p_value"] == ""

    # arm_a vs arm_c: real comparison still produced alongside the skip
    compared = by_pair[("arm_a", "arm_c")]
    assert compared["status"] == "compared"
    assert compared["statistic"] != ""


def test_mcnemar_missing_vector_records_skip_row(tmp_path):
    """A pair where one arm's vector is absent (e.g. arm not scored on that set)
    is also recorded as a skip with note='missing', not dropped.
    """
    results_dir = tmp_path / "results"
    cfg = {"arms": [{"name": "arm_a"}, {"name": "arm_b"}]}
    truthful_vectors = {
        ("arm_a", "in_domain"): [1, 0, 1],
        # arm_b absent on in_domain
    }
    run_eval._write_comparisons(results_dir, cfg, truthful_vectors, [])
    rows = list(csv.DictReader((results_dir / "comparisons" / "mcnemar.csv").open()))
    assert len(rows) == 1
    assert rows[0]["status"] == "skipped_length_mismatch"
    assert "missing" in rows[0]["note"]


# --- FB2: verified flag is conditioned on the scorer path, not hardcoded ------


def test_validated_metric_registry_drives_verified():
    """truthful_rate is a Cheng-regression-validated scorer path -> True;
    a synthetic non-validated metric -> False. Conditioning, not a literal.
    """
    assert run_eval.is_validated_metric("truthful_rate") is True
    assert run_eval.is_validated_metric("some_future_unvalidated_metric") is False


def test_provenance_non_validated_metric_stamps_verified_false():
    """A Provenance for a metric outside VALIDATED_METRICS must carry
    verified=False, preserving the HANDOFF §5 contract that the flag means
    'produced by a regression-validated scorer path'.
    """
    metric = "experimental_unvalidated_score"
    prov = run_eval.Provenance(
        source="in_domain",
        metric=metric,
        model="test-model",
        method="sft",
        verified=run_eval.is_validated_metric(metric),
        config_sha="deadbeef",
    )
    assert prov.verified is False
    assert prov.as_dict()["verified"] is False
