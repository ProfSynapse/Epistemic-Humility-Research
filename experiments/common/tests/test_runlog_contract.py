"""CPU unit tests for experiments/common/runlog_contract.py.

All stubs and payloads use short synthetic strings only -- this repo is
public and never carries real question/prompt/generation text in tests.
Every test injects a stub RunLog class via ``run_log_cls`` so none of this
requires a synaptic-tuner checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
COMMON_DIR = HERE.parent
sys.path.insert(0, str(COMMON_DIR))

import runlog_contract as rc  # noqa: E402


class _StubRunLogLegacy:
    """Shape of a RunLog class that predates the required_fields parameter:
    no such keyword accepted at all."""

    def __init__(self, path, run_config, **kwargs):
        assert "required_fields" not in kwargs
        self.path = path
        self.run_config = run_config
        self.records: list[tuple] = []

    def record(self, key, payload):
        self.records.append((key, dict(payload)))

    def close(self):
        pass


class _StubRunLogModern:
    """Shape of a RunLog class that already accepts required_fields and
    enforces it itself (mirrors the real tuner behavior after PR pairing)."""

    def __init__(self, path, run_config, *, required_fields=(), **kwargs):
        self.path = path
        self.run_config = run_config
        self.required_fields = tuple(required_fields)
        self.records: list[tuple] = []

    def record(self, key, payload):
        missing = [
            f for f in self.required_fields
            if not isinstance(payload.get(f), str) or not payload.get(f)
        ]
        if missing:
            raise rc.RunlogContractError(f"missing {missing}")
        self.records.append((key, dict(payload)))

    def close(self):
        pass


@pytest.mark.parametrize("stub_cls", [_StubRunLogLegacy, _StubRunLogModern])
def test_text_present_passes(stub_cls):
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=stub_cls
    )
    log.record("row-1", {"out_text": "synthetic output text"})
    assert log.records == [("row-1", {"out_text": "synthetic output text"})]


@pytest.mark.parametrize("stub_cls", [_StubRunLogLegacy, _StubRunLogModern])
def test_missing_text_raises(stub_cls):
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=stub_cls
    )
    with pytest.raises(Exception):
        log.record("row-1", {"score": 1})
    assert log.records == []


@pytest.mark.parametrize("stub_cls", [_StubRunLogLegacy, _StubRunLogModern])
def test_empty_string_text_raises(stub_cls):
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=stub_cls
    )
    with pytest.raises(Exception):
        log.record("row-1", {"out_text": ""})
    assert log.records == []


def test_custom_text_field_name_is_enforced():
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, text_field="foo", run_log_cls=_StubRunLogLegacy
    )
    with pytest.raises(rc.RunlogContractError, match="foo"):
        log.record("row-1", {"out_text": "synthetic output text"})
    log.record("row-1", {"foo": "synthetic output text"})
    assert log.records == [("row-1", {"foo": "synthetic output text"})]


@pytest.mark.parametrize("stub_cls", [_StubRunLogLegacy, _StubRunLogModern])
def test_textless_reason_permits_textfree_records_and_lands_in_run_config(stub_cls):
    log = rc.open_generation_runlog(
        "unused.jsonl",
        {"arm": "a"},
        textless_reason="analysis-only pass, no generation performed",
        run_log_cls=stub_cls,
    )
    # Durably recorded on the run_config that feeds the meta fingerprint.
    assert log.run_config["textless_reason"] == (
        "analysis-only pass, no generation performed"
    )
    # No text field required once the opt-out is active.
    log.record("row-1", {"score": 1})
    assert log.records == [("row-1", {"score": 1})]


def test_explicit_none_reason_behaves_as_default_and_enforces():
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, textless_reason=None, run_log_cls=_StubRunLogLegacy
    )
    with pytest.raises(rc.RunlogContractError):
        log.record("row-1", {"score": 1})


@pytest.mark.parametrize("bad_reason", ["", "   "])
def test_explicit_empty_or_whitespace_reason_raises(bad_reason):
    with pytest.raises(rc.RunlogContractError):
        rc.open_generation_runlog(
            "unused.jsonl", {"arm": "a"}, textless_reason=bad_reason,
            run_log_cls=_StubRunLogLegacy,
        )


def test_works_with_stub_lacking_required_fields():
    # _StubRunLogLegacy has no required_fields parameter at all; the
    # contract wrapper must still enforce the check client-side.
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=_StubRunLogLegacy
    )
    assert isinstance(log, rc._ClientSideRequiredFieldsRunLog)
    log.record("row-1", {"out_text": "synthetic output text"})
    assert log.records == [("row-1", {"out_text": "synthetic output text"})]


def test_modern_stub_is_passed_through_directly_not_wrapped():
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=_StubRunLogModern
    )
    assert isinstance(log, _StubRunLogModern)
    assert log.required_fields == ("out_text",)


def test_delegates_unknown_attributes_to_inner_runlog():
    log = rc.open_generation_runlog(
        "unused.jsonl", {"arm": "a"}, run_log_cls=_StubRunLogLegacy
    )
    log.record("row-1", {"out_text": "synthetic output text"})
    log.close()  # delegated to the inner stub; must not raise
