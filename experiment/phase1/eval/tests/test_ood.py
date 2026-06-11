#!/usr/bin/env python3
"""Unit tests for ood.py loaders against the on-disk OOD corpora (skip if absent).

Each loader must produce the uniform eval-record contract:
  {id, question, label in {known,unknown,None}, aliases (normalized), source}.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ood

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "datasets"


def _require(p: Path):
    if not p.exists():
        pytest.skip(f"OOD corpus not on disk: {p}")
    return p


def _assert_contract(records, source):
    assert records, "loader returned no records"
    r = records[0]
    assert set(["id", "question", "label", "aliases", "source"]).issubset(r)
    assert r["source"] == source
    assert r["label"] in ("known", "unknown", None)
    assert isinstance(r["aliases"], list)


def test_load_kuq():
    recs = ood.load_kuq(_require(DATA / "kuq" / "knowns_unknowns.jsonl"))
    _assert_contract(recs, "kuq")
    # KUQ carries the unknown bool -> both labels should appear
    labels = {r["label"] for r in recs}
    assert "unknown" in labels


def test_load_coconot_all_known_contrast():
    recs = ood.load_coconot(_require(DATA / "coconot" / "contrast_test.jsonl"))
    _assert_contract(recs, "coconot")
    assert all(r["label"] == "known" for r in recs)


def test_load_popqa_aliases_parsed():
    recs = ood.load_popqa(_require(DATA / "popqa" / "test.jsonl"))
    _assert_contract(recs, "popqa")
    # possible_answers parses to a non-empty alias list for at least one record
    assert any(r["aliases"] for r in recs)


def test_load_selfaware_labels():
    recs = ood.load_selfaware(_require(DATA / "selfaware" / "SelfAware.json"))
    _assert_contract(recs, "selfaware")
    labels = {r["label"] for r in recs}
    assert {"known", "unknown"} & labels


def test_load_truthfulqa():
    recs = ood.load_truthfulqa(_require(DATA / "truthfulqa" / "TruthfulQA.csv"))
    _assert_contract(recs, "truthfulqa")
    assert any(r["aliases"] for r in recs)


def test_load_mmlu_mcq_fields():
    recs = ood.load_mmlu(_require(DATA / "mmlu" / "test.jsonl"))
    _assert_contract(recs, "mmlu")
    r = recs[0]
    assert "choices" in r and isinstance(r["choices"], list)
    assert "answer_index" in r and isinstance(r["answer_index"], int)


def test_dispatch_unknown_set_raises():
    with pytest.raises(KeyError):
        ood.load_ood_set("not_a_set", "/dev/null")
