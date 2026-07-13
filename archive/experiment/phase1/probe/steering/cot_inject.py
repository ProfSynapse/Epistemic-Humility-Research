#!/usr/bin/env python3
"""Arm B — chain-of-thought injection harness (Paper 5 / confidence-steering experiment).

DESIGN REFERENCE: docs/plans/confidence-steering-experiment.md

NOT authorized for GPU runs. A signed Tier-2 Amendment with locked gates and
explicit user launch approval is required before any real inference run.

Mechanics
---------
Compute a probe score for the input question, render it as a short annotation
note, and inject it into the model's reasoning trace at a configurable position:

  EARLY injection  — note inserted BEFORE the model reasons to an answer
                     (target: changes answer/abstain decision)
  LATE  injection  — note inserted AFTER the model has drafted an answer inside
                     the think block (target: triggers self-revision / surfaced
                     confidence)
  FINAL injection  — note appended after the draft as the model's LAST thought
                     and the think block is CLOSED, so the very next tokens are
                     the committed answer (Amendment AB Revision 1; target:
                     decision-only use at the commit point, zero trajectory
                     confound)

The note format is:
  [internal: <signal_name> <score:.2f> — <interpretation>]

Placebo control (Amendment Y / Paper 5 circularity check):
  Replace the real score with a SHUFFLED/RANDOM value from the score distribution
  to isolate the real signal from generic "be cautious" priming.  The only
  difference between placebo and real is the score value; the note structure and
  format are identical.

This module is STRING-CONSTRUCTION-ONLY (CPU, no model calls). The actual model
inference is the responsibility of the caller / run harness.

Example usage
-------------
>>> from cot_inject import InjectionConfig, build_think_prompt, build_placebo_prompt
>>> cfg = InjectionConfig(signal="gate", score=0.23, position="early",
...                       interpretation="likely unknown")
>>> prompt = build_think_prompt(base_prompt="What is dark matter?", config=cfg)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Interpretation helpers
# ---------------------------------------------------------------------------

_GATE_INTERPRETATIONS = {
    (0.0, 0.3): "likely unknown — consider abstaining",
    (0.3, 0.6): "uncertain — verify before answering",
    (0.6, 0.8): "probably known",
    (0.8, 1.0): "confident — known",
}

_DIAL_INTERPRETATIONS = {
    (0.0, 0.3): "likely incorrect — consider revising",
    (0.3, 0.6): "uncertain correctness",
    (0.6, 0.8): "probably correct",
    (0.8, 1.0): "confident — correct",
}


def _score_to_interpretation(score: float, signal: str) -> str:
    """Map a probe score to a human-readable interpretation string."""
    table = _GATE_INTERPRETATIONS if signal == "gate" else _DIAL_INTERPRETATIONS
    for (lo, hi), interp in table.items():
        if lo <= score < hi:
            return interp
    # score == 1.0 edge case
    return list(table.values())[-1]


# ---------------------------------------------------------------------------
# Injection config
# ---------------------------------------------------------------------------

@dataclass
class InjectionConfig:
    """Configuration for a single CoT injection.

    Parameters
    ----------
    signal         : 'gate' (answerability) or 'dial' (correctness)
    score          : float in [0, 1], the probe P(positive) for this input
    position       : 'early' (pre-answer in think block), 'late' (post-draft,
                     model continues), or 'final' (post-draft, think block
                     closed — the note is the last thought before the answer)
    interpretation : human-readable string; if None, auto-derived from score+signal
    note_template  : f-string template for the note; {signal}, {score}, {interp}
                     are available as format keys
    """
    signal: str
    score: float
    position: str = "early"
    interpretation: Optional[str] = None
    note_template: str = "[internal: {signal} {score:.2f} — {interp}]"

    def __post_init__(self):
        if self.signal not in ("gate", "dial"):
            raise ValueError(f"signal must be 'gate' or 'dial', got {self.signal!r}")
        if self.position not in ("early", "late", "final"):
            raise ValueError(
                f"position must be 'early', 'late', or 'final', got {self.position!r}")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be in [0, 1], got {self.score}")

    @property
    def resolved_interpretation(self) -> str:
        if self.interpretation is not None:
            return self.interpretation
        return _score_to_interpretation(self.score, self.signal)

    def render_note(self) -> str:
        """Render the injection note string."""
        return self.note_template.format(
            signal=self.signal,
            score=self.score,
            interp=self.resolved_interpretation,
        )


# ---------------------------------------------------------------------------
# Think-block prompt builders
# ---------------------------------------------------------------------------

# The think-block delimiters used by thinking-enabled models (Qwen3 extended-think,
# Gemma thinking, etc.). These are the same delimiters used in Amendment Y.
_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"

# Separator placed between the note and surrounding content within the think block.
_NOTE_SEPARATOR = "\n\n"


def build_think_prompt(
    base_prompt: str,
    config: InjectionConfig,
    existing_draft: Optional[str] = None,
) -> str:
    """Build a prompt with the injection note embedded in the think block.

    Parameters
    ----------
    base_prompt    : the question/instruction for the model
    config         : InjectionConfig specifying signal, score, position
    existing_draft : for 'late' injection — the partial think-block content
                     that the model has already generated (as a string, without
                     the <think> delimiters). If None and position='late', an
                     empty draft is used (note goes at the start of the block).

    Returns
    -------
    Full prompt string with the think block already partially written, so the
    model continues reasoning from the injection point.

    Examples
    --------
    Early injection (position='early'):
        <user>: What is dark matter?
        <assistant>: <think>
        [internal: gate 0.23 — likely unknown — consider abstaining]

        (model continues here)

    Late injection (position='late', existing_draft="Dark matter is..."):
        <user>: What is dark matter?
        <assistant>: <think>
        Dark matter is...

        [internal: dial 0.78 — probably correct]

        (model continues here)

    Final injection (position='final', existing_draft="Dark matter is..."):
        <user>: What is dark matter?
        <assistant>: <think>
        Dark matter is...

        [internal: dial 0.78 — probably correct]
        </think>
        (model answers here — no further thinking possible)
    """
    note = config.render_note()

    if config.position == "early":
        # Note is the FIRST thing in the think block
        think_content = note + _NOTE_SEPARATOR
    elif config.position == "late":
        draft = existing_draft or ""
        think_content = draft + _NOTE_SEPARATOR + note + _NOTE_SEPARATOR
    else:  # "final"
        # Note is the LAST thought: append after the draft and CLOSE the
        # think block so the model must answer immediately.
        draft = existing_draft or ""
        think_content = (draft + _NOTE_SEPARATOR + note + "\n"
                         + _THINK_CLOSE + "\n")

    # We open the think block and populate it up to the injection point.
    # For 'early'/'late' we do NOT close </think> (the model must do that
    # itself); for 'final' the block is already closed above.
    injected_prompt = (
        f"{base_prompt}\n"
        f"{_THINK_OPEN}\n"
        f"{think_content}"
    )
    return injected_prompt


def extract_think_content(generated_text: str) -> str:
    """Extract the think-block content from a model generation.

    Used by the 'final' position (Amendment AB Revision 1): a shared plain
    thinking-enabled pass produces the reasoning draft; its think content is
    re-used verbatim as the `existing_draft` for the note-then-close prompt.

    Handles the generation starting with or without the '<think>' opener and
    a draft truncated before '</think>' (the whole text is the draft then).
    """
    text = generated_text
    if _THINK_CLOSE in text:
        text = text.split(_THINK_CLOSE, 1)[0]
    if _THINK_OPEN in text:
        text = text.split(_THINK_OPEN, 1)[1]
    return text.strip()


def build_placebo_prompt(
    base_prompt: str,
    config: InjectionConfig,
    score_distribution: list[float],
    rng: Optional[random.Random] = None,
    existing_draft: Optional[str] = None,
) -> tuple[str, float]:
    """Build a placebo prompt with a shuffled score instead of the real score.

    The placebo note is IDENTICAL in structure to the real note; only the score
    value is replaced with a random sample from the provided score distribution.
    This isolates the real probe signal from generic "be cautious" priming.

    Parameters
    ----------
    base_prompt        : same question/instruction
    config             : InjectionConfig (signal, position); score is REPLACED
    score_distribution : list of float scores to sample from (empirical distribution
                         from the model's own P(positive) on the same dataset, or
                         a shuffled permutation of the real scores)
    rng                : random.Random for reproducibility; default creates fresh
    existing_draft     : same as build_think_prompt

    Returns
    -------
    (prompt_str, placebo_score_used)
    """
    if rng is None:
        rng = random.Random()
    if not score_distribution:
        raise ValueError("score_distribution must be non-empty for placebo construction")

    placebo_score = rng.choice(score_distribution)
    placebo_config = InjectionConfig(
        signal=config.signal,
        score=placebo_score,
        position=config.position,
        interpretation=config.interpretation,  # keep same interpretation template
        note_template=config.note_template,
    )
    prompt = build_think_prompt(base_prompt, placebo_config, existing_draft)
    return prompt, placebo_score


# ---------------------------------------------------------------------------
# Batch construction helpers
# ---------------------------------------------------------------------------

def build_injection_batch(
    items: list[dict],
    signal: str,
    position: str,
    score_key: str = "probe_score",
    question_key: str = "question",
    draft_key: str = "think_draft",
) -> list[dict]:
    """Build a batch of injection prompts from a list of scored items.

    Each item should have at minimum:
      - question_key : str (the question text)
      - score_key    : float (probe P(positive) for this question)
      - draft_key    : str (optional; think block draft for late injection)

    Returns a list of dicts with:
      - all original item fields
      - "injected_prompt" : str
      - "injection_note"  : str
      - "injection_config": dict (InjectionConfig fields)
    """
    results = []
    for item in items:
        cfg = InjectionConfig(
            signal=signal,
            score=float(item[score_key]),
            position=position,
        )
        draft = item.get(draft_key)
        prompt = build_think_prompt(item[question_key], cfg, draft)
        results.append({
            **item,
            "injected_prompt": prompt,
            "injection_note": cfg.render_note(),
            "injection_config": {
                "signal": cfg.signal,
                "score": cfg.score,
                "position": cfg.position,
                "interpretation": cfg.resolved_interpretation,
            },
        })
    return results


def build_placebo_batch(
    items: list[dict],
    signal: str,
    position: str,
    score_key: str = "probe_score",
    question_key: str = "question",
    draft_key: str = "think_draft",
    seed: int = 20260630,
) -> list[dict]:
    """Build a placebo batch: same structure as build_injection_batch but with
    shuffled scores.  The real score distribution is derived from the items
    themselves (so the marginal distribution is preserved, only per-item labels
    are shuffled — a within-batch permutation control).
    """
    rng = random.Random(seed)
    real_scores = [float(item[score_key]) for item in items]
    # Shuffle a copy to get placebo scores
    placebo_scores = real_scores[:]
    rng.shuffle(placebo_scores)

    results = []
    for item, placebo_score in zip(items, placebo_scores):
        cfg = InjectionConfig(
            signal=signal,
            score=placebo_score,
            position=position,
        )
        draft = item.get(draft_key)
        prompt = build_think_prompt(item[question_key], cfg, draft)
        results.append({
            **item,
            "injected_prompt": prompt,
            "injection_note": cfg.render_note(),
            "real_score": float(item[score_key]),
            "placebo_score": placebo_score,
            "injection_config": {
                "signal": cfg.signal,
                "score": placebo_score,
                "position": cfg.position,
                "interpretation": cfg.resolved_interpretation,
                "is_placebo": True,
            },
        })
    return results


# ---------------------------------------------------------------------------
# CLI (dry-run / inspection only)
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    # demo command: render a note + prompt
    demo = sub.add_parser("demo", help="Render an example injection prompt")
    demo.add_argument("--signal", choices=["gate", "dial"], default="gate")
    demo.add_argument("--score", type=float, default=0.23)
    demo.add_argument("--position", choices=["early", "late", "final"], default="early")
    demo.add_argument("--question", default="What is dark matter?")
    demo.add_argument("--draft", default=None, help="Existing think-block draft (for late)")
    demo.add_argument("--placebo", action="store_true", help="Show placebo version too")

    # batch command: read a scored jsonl, output injected prompts
    batch = sub.add_parser("batch", help="Inject from a scored .jsonl")
    batch.add_argument("--input", required=True, type=str,
                       help="Path to scored .jsonl (one JSON per line)")
    batch.add_argument("--output", required=True, type=str)
    batch.add_argument("--signal", choices=["gate", "dial"], required=True)
    batch.add_argument("--position", choices=["early", "late", "final"], required=True)
    batch.add_argument("--placebo", action="store_true")
    batch.add_argument("--seed", type=int, default=20260630)

    a = ap.parse_args(argv)

    if a.cmd == "demo":
        cfg = InjectionConfig(signal=a.signal, score=a.score, position=a.position)
        prompt = build_think_prompt(a.question, cfg, a.draft)
        print("=== REAL INJECTION PROMPT ===")
        print(prompt)
        if a.placebo:
            distribution = [0.1, 0.3, 0.5, 0.7, 0.9]  # example distribution
            rng = random.Random(42)
            p_prompt, p_score = build_placebo_prompt(
                a.question, cfg, distribution, rng, a.draft
            )
            print("\n=== PLACEBO INJECTION PROMPT ===")
            print(f"(placebo_score={p_score:.2f})")
            print(p_prompt)
        return 0

    elif a.cmd == "batch":
        from pathlib import Path
        items = [json.loads(ln) for ln in Path(a.input).open(encoding="utf-8") if ln.strip()]
        if a.placebo:
            results = build_placebo_batch(
                items, a.signal, a.position, seed=a.seed
            )
        else:
            results = build_injection_batch(items, a.signal, a.position)
        out_path = Path(a.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            for r in results:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[cot_inject] wrote {len(results)} rows to {a.output}", flush=True)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
