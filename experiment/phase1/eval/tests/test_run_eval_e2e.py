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
