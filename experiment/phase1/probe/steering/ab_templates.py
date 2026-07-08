#!/usr/bin/env python3
"""Amendment AB — note-variant templates (V0..V3) with banded rendering.

SPEC: experiments/first-person-injection/AMENDMENT.md (SIGNED
2026-07-02 + Revision 1). Wording below is FINAL per the signed doc: V1 is
grounded in the idiom-mining pass (aa_think_trace_idiom_mining.md); band cuts
are LOCKED at signing (low < 0.40, mid 0.40-0.70, high > 0.70). No em dashes
in injected text.

V4 (decision rule in telemetry register) runs only on a V1 hit (AB-G3); its
per-band rule sentence finalizes then, so it is deliberately absent here.

The placebo contract is preserved by construction: a placebo (permuted) score
flows through the SAME banded machinery, so it carries its band and its
decision-rule clause with it — the only difference between real and placebo
is the score value driving band + percent.

String-construction only (CPU, no model calls).
"""

from __future__ import annotations

from cot_inject import InjectionConfig

VARIANTS = ("v0", "v1", "v2", "v3")

# Band cuts LOCKED at signing (AMENDMENT-AB, V1 templates section).
BAND_LOW_LT = 0.40
BAND_HIGH_GT = 0.70


def band(score: float) -> str:
    """Map a probe score to its locked band: low < 0.40, mid 0.40-0.70,
    high > 0.70 (boundary values fall in 'mid')."""
    if score < BAND_LOW_LT:
        return "low"
    if score > BAND_HIGH_GT:
        return "high"
    return "mid"


def _pct(score: float) -> int:
    return int(round(score * 100))


# V1 (go/no-go): first-person recall-experience prose + percent +
# score-conditional decision rule. Keyed (signal, band). Verbatim from the
# signed amendment doc.
_V1_TEMPLATES = {
    ("gate", "high"): (
        "Let me first check whether I actually know this. I am confident I "
        "have the knowledge needed to answer this correctly, about {pct}% "
        "sure. That is solid ground: I should commit to my best answer "
        "rather than hedge."),
    ("gate", "mid"): (
        "Let me first check whether I actually know this. I am not fully "
        "confident, only about {pct}% sure I have the knowledge needed. I "
        "need to verify what I actually know and answer only if it checks "
        "out; otherwise I should say I don't know."),
    ("gate", "low"): (
        "Let me first check whether I actually know this. I am not confident "
        "I have the knowledge needed to answer this correctly, only about "
        "{pct}% sure. When I am this unsure the right move is to say I "
        "don't know rather than guess."),
    ("dial", "high"): (
        "I am confident in my previous answer: my internal sense that it is "
        "right is about {pct}%. That is strong enough to trust. I should "
        "keep this answer and state it plainly."),
    ("dial", "mid"): (
        "I am not fully confident in my previous answer: my internal sense "
        "that it is right is only about {pct}%. Let me think through the "
        "key step again and keep the answer only if it actually checks out."),
    ("dial", "low"): (
        "I am not confident in my previous answer: my internal sense that it "
        "is right is only about {pct}%. An answer I trust less than a coin "
        "flip should not stand. The right move is to revise it or say I "
        "don't know."),
}

# V2 (intention only): the user's verbatim framing — drops the action rule.
_V2_TEMPLATE = (
    "I am {pct}% sure I have the knowledge required to answer this question "
    "appropriately. I will incorporate that into my thinking and response "
    "to the user.")

# V3 (voice only): drops even the intention.
_V3_TEMPLATE = (
    "I am {pct}% sure I have the knowledge required to answer this question "
    "appropriately.")


def render_note(variant: str, signal: str, score: float, position: str) -> str:
    """Render the injection note for a variant.

    v0 delegates to the registered AA telemetry template (byte-identical to
    cot_inject.InjectionConfig.render_note — never change it). v1-v3 render
    first-person prose; v1 selects by (signal, band(score)).
    """
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}, got {variant!r}")
    if not 0.0 <= float(score) <= 1.0:
        raise ValueError(f"score must be in [0, 1], got {score}")
    if variant == "v0":
        return InjectionConfig(signal=signal, score=float(score),
                               position=position).render_note()
    if signal not in ("gate", "dial"):
        raise ValueError(f"signal must be 'gate' or 'dial', got {signal!r}")
    if variant == "v1":
        return _V1_TEMPLATES[(signal, band(float(score)))].format(
            pct=_pct(float(score)))
    if variant == "v2":
        return _V2_TEMPLATE.format(pct=_pct(float(score)))
    return _V3_TEMPLATE.format(pct=_pct(float(score)))
