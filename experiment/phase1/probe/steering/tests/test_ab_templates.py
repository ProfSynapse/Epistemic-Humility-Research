"""Unit tests for ab_templates.py (Amendment AB note variants V0-V3).

CPU-only string-construction tests: locked band cuts, verbatim template
selection, percent rendering, v0 byte-compatibility with the AA note, and
the placebo band-carrying contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

steering_dir = Path(__file__).resolve().parent.parent
if str(steering_dir) not in sys.path:
    sys.path.insert(0, str(steering_dir))

from ab_templates import BAND_HIGH_GT, BAND_LOW_LT, band, render_note
from cot_inject import InjectionConfig


class TestBand:
    def test_locked_cuts(self):
        assert (BAND_LOW_LT, BAND_HIGH_GT) == (0.40, 0.70)

    @pytest.mark.parametrize("score,expected", [
        (0.0, "low"), (0.39, "low"),
        (0.40, "mid"), (0.55, "mid"), (0.70, "mid"),
        (0.71, "high"), (1.0, "high"),
    ])
    def test_banding(self, score, expected):
        assert band(score) == expected


class TestRenderNote:
    def test_v0_byte_identical_to_aa_note(self):
        for signal, score, position in (("gate", 0.23, "early"),
                                        ("dial", 0.78, "late"),
                                        ("dial", 0.31, "final")):
            aa = InjectionConfig(signal=signal, score=score,
                                 position=position).render_note()
            assert render_note("v0", signal, score, position) == aa

    def test_v1_selects_by_signal_and_band(self):
        low = render_note("v1", "dial", 0.31, "final")
        assert "coin flip" in low and "31%" in low
        high = render_note("v1", "gate", 0.88, "early")
        assert "solid ground" in high and "88%" in high
        mid = render_note("v1", "dial", 0.55, "late")
        assert "key step" in mid and "55%" in mid

    def test_v1_no_em_dash(self):
        for signal in ("gate", "dial"):
            for score in (0.1, 0.5, 0.9):
                assert "—" not in render_note("v1", signal, score, "late")

    def test_v2_verbatim_user_framing(self):
        note = render_note("v2", "gate", 0.42, "early")
        assert note == ("I am 42% sure I have the knowledge required to "
                        "answer this question appropriately. I will "
                        "incorporate that into my thinking and response "
                        "to the user.")

    def test_v3_drops_intention(self):
        note = render_note("v3", "gate", 0.42, "early")
        assert note.endswith("appropriately.")
        assert "incorporate" not in note

    def test_placebo_score_carries_its_band(self):
        # The band (and its decision-rule clause) must travel with the score:
        # a permuted low score renders the low-band rule even on a high item.
        real = render_note("v1", "dial", 0.9, "late")
        placebo = render_note("v1", "dial", 0.1, "late")
        assert "keep this answer" in real
        assert "revise it or say I don't know" in placebo

    def test_invalid_variant_raises(self):
        with pytest.raises(ValueError, match="variant"):
            render_note("v9", "gate", 0.5, "early")

    def test_invalid_score_raises(self):
        with pytest.raises(ValueError, match="score"):
            render_note("v1", "gate", 1.5, "early")
