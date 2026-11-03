"""Decoded equality cannot substitute for the registered token-ID parity."""

from hs20_nwe.parity import compare


def record(ids):
    return {"row_key": "synthetic", "answer_text": "identical decoded text",
            "n_new_tokens": len(ids), "terminated_naturally": True,
            "generated_token_ids": ids}


def test_different_token_ids_fail_even_when_text_and_counts_match():
    assert not compare([record([3, 7])], [record([4, 7])])["passed"]
    assert compare([record([3, 7])], [record([3, 7])])["passed"]


def test_legacy_outputs_missing_or_spoofing_ids_cannot_pass():
    missing = record([3, 7]); del missing["generated_token_ids"]
    assert not compare([missing], [missing])["passed"]
    malformed = record([3, 7]); malformed["generated_token_ids"] = [True, 7]
    assert not compare([malformed], [malformed])["passed"]
