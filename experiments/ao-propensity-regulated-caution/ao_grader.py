"""Grader for the AO propensity-regulated-caution cell.

Ported (logic, not import) from the FROZEN steering harness
``archive/experiment/phase1/probe/steering/steering_common.py`` (726 lines, read in
full; not modified): ``is_degenerate`` is copied verbatim (the repeated
n-gram / empty-output coherence-floor check), and the refusal/correctness
structure mirrors its ``grade_output`` (degenerate -> abstained/refused ->
answered -> correct-if-graded) exactly. steering_common.py itself is not
imported directly because its module-level imports pull in unrelated
dataset-builder machinery (``amendment_s_correctness_probe_extract``,
``amendment_u_unified_extract``, ``confidence_steer``); this module stays
self-contained per the task's instruction, importing only the lightweight,
dependency-free ``experiment/phase1/eval/scorers.py`` (the same import
steering_common.py itself makes for ``is_stated_confidence_refusal`` /
``is_correct``).

Refusal/correctness on RAW ``answer_text`` (no JSON-schema unwrap): this
checkpoint's baseline system prompt constrains output to
``{"answer": ..., "response_confidence": ...}`` (see the AI-TRUE extraction
manifest), but the ACTUAL byte-pinned grader for this exact surface
(``archive/experiment/phase1/probe/amendment_ai_verdict_extract_gen.py`` at
generation time, and ``amendment_al_prep_grade_a0_generations.py`` at
grading time -- together "the AL A0 cell" grader the AMENDMENT names) calls
``scorers.is_stated_confidence_refusal`` / ``scorers.is_correct`` directly on
the RAW decoded text, never on a JSON-unwrapped ``"answer"`` field. This
module matches that convention exactly (a gold alias or refusal phrase
embedded inside ``{"answer": "...", ...}`` is still matched as a substring of
the raw text).

Fields returned, merged into the row by the tuner's ``run_steer`` (see
synaptic-tuner ``MechInterp/cli.py:360``, ``rec.update(grader(rec))``):
  refused           bool
  correct           bool | None  (None where correctness is not meaningful,
                    e.g. an unanswered/refused row, or a row with no aliases)
  degenerate        bool  (coherence-floor flag, descriptive)
  baseline_refused  bool  (this row_key's `refused` value under the baseline
                    arm -- see "Cross-arm join" below)
  baseline_correct  bool | None  (same, for `correct`)

gates.yaml (G1, G2a, G2b) reads exactly these fields plus `cell` and
`row_key`, both carried through unchanged from the rows pool
(`prop_z_gain_map_rows.jsonl`) into every arm's generation record by the
tuner's row-plumbing (not this module's concern).

Cross-arm join (baseline_refused / baseline_correct)
-----------------------------------------------------
``MechInterp/cli.py:run_steer`` calls ``grade(row)`` once per (row, arm),
synchronously, arm-by-arm in ``cell.yaml``'s declared order (baseline first),
within one process -- it never hands the grader more than one row's record.
There is therefore no single call at which "the baseline value for this
row_key" is available except by remembering it. This module keeps a
module-level cache keyed by row_key, populated the moment a baseline-arm row
is graded, and consulted for every later arm's row. On a RESUMED run in a
fresh process, the cache is lazily re-primed by reading any baseline rows
already present on disk the first time ``grade()`` is called. This
reproduces, within the tuner's one-row-at-a-time contract, the same "rows
already carry their own baseline join, no separate post-pass" property the
AL/AN scripts get for free by operating over a full rows.jsonl at once
(``amendment_al_grade_and_gates.py``, ``amendment_an_grade_and_gates.py``).

Priming path (config-driven, not hardcoded): ``grader(row)`` receives only the
per-row record (``MechInterp/cli.py:360``, ``rec.update(grader(rec))``) --
there is no channel from the tuner for a grader to read the calling cell's own
``execution.output_path``. Three cells share this grader module (Stage-2's
``cell.yaml`` -> ``analysis/rows_out.jsonl``, and the two Stage-1 cells ->
``analysis/rows_out_stage1_caution_perp.jsonl`` /
``analysis/rows_out_stage1_fallback_mass_mean.jsonl``), so priming from one
hardcoded path silently fails to re-prime a DIFFERENT cell's resumed run
(KeyError on the first non-baseline row graded after a restart, even though
that cell's own baseline rows are sitting on disk under its own path). Fixed
by reading the path from the ``AO_GRADER_OUTPUT_PATH`` environment variable,
set by the invoker to match whichever cell.yaml's ``execution.output_path``
is actually being run; see ``_resolve_output_path`` below. Falls back to
Stage-2's own default path if unset, so an invocation that forgets to set it
still behaves exactly as before (a loud KeyError on a crash-and-resume in a
fresh process, never a silent wrong-file read).

FLAG FOR REVIEW: the AMENDMENT does not spell out this join mechanism; it is
a Stage-0 CPU judgment call, not itself pinned by the amendment text. If a
future revision wants a real post-pass instead (mirroring the AL/AN scripts
literally), swap this cache for a script run between the GPU generation and
`score-gates`, over the full written `rows_out.jsonl`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

EVAL_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/eval")
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
import scorers  # noqa: E402  (eval/scorers.py -- Cheng-validated port, dependency-free)

# Stage-2's own output path (cell.yaml's execution.output_path), used as the
# fallback default when AO_GRADER_OUTPUT_PATH is unset -- see
# _resolve_output_path below and the "Priming path" section of this module's
# docstring for why a single hardcoded path cannot serve all three cells that
# share this grader.
_DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent / "analysis" / "rows_out.jsonl"
)


def _resolve_output_path() -> Path:
    """The CURRENT cell's own output_path, read from the environment.

    Set AO_GRADER_OUTPUT_PATH to the exact value of the cell.yaml being run's
    execution.output_path before invoking `mechinterp steer` (or `score-gates`
    tooling that re-primes this module), so a resumed run in a fresh process
    re-primes the baseline cache from THIS cell's own rows, not Stage-2's.
    """
    raw = os.environ.get("AO_GRADER_OUTPUT_PATH")
    return Path(raw) if raw else _DEFAULT_OUTPUT_PATH


# ---------------------------------------------------------------------------
# is_degenerate -- verbatim port from steering_common.py (_MAX_NGRAM=5,
# _MIN_REPEATS=3: empty, no alphanumeric content, or a single repeated n-gram
# covering the whole output).
# ---------------------------------------------------------------------------

_MAX_NGRAM = 5
_MIN_REPEATS = 3


def _is_repeated_ngram(tokens: list[str]) -> bool:
    n_tok = len(tokens)
    for n in range(1, _MAX_NGRAM + 1):
        if n_tok < n * _MIN_REPEATS:
            continue
        unit = tokens[:n]
        reps = n_tok // n
        if reps < _MIN_REPEATS:
            continue
        if all(tokens[i * n:(i + 1) * n] == unit for i in range(reps)) and \
                tokens[reps * n:] == unit[: n_tok - reps * n]:
            return True
    return False


def is_degenerate(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    tokens = stripped.split()
    return _is_repeated_ngram(tokens)


# ---------------------------------------------------------------------------
# Per-row grade (steering_common.py's grade_output shape, on raw answer_text,
# matching amendment_ai_verdict_extract_gen.py / amendment_al_prep_grade_a0_
# generations.py's byte-pinned convention for this exact surface).
# ---------------------------------------------------------------------------

def _normalize_aliases(row: dict) -> list[str]:
    raw = row.get("aliases") or row.get("aliases_norm") or []
    return [scorers.normalize(str(a)) for a in raw if str(a).strip()]


def grade_one(answer_text: str, aliases_norm: list[str]) -> dict:
    """steering_common.grade_output, applied to RAW (not JSON-unwrapped) text."""
    degenerate = is_degenerate(answer_text)
    refused = (not degenerate) and bool(scorers.is_stated_confidence_refusal(answer_text))
    answered = (not degenerate) and (not refused)
    correct: Optional[bool] = None
    if answered and aliases_norm:
        correct = bool(scorers.is_correct(answer_text, aliases_norm))
    return {"degenerate": degenerate, "refused": refused, "answered": answered, "correct": correct}


_baseline_cache: dict[str, dict] = {}
_cache_primed = False


def _prime_cache_from_disk() -> None:
    global _cache_primed
    _cache_primed = True
    output_path = _resolve_output_path()
    if not output_path.is_file():
        return
    with output_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") == "baseline" and "refused" in rec and "row_key" in rec:
                _baseline_cache[rec["row_key"]] = {
                    "refused": bool(rec["refused"]),
                    "correct": rec.get("correct"),
                }


def grade(row: dict) -> dict:
    """Contract: one per-row output dict -> a grade dict merged back into it.

    See synaptic-tuner/docs/MECH_INTERP_CELLS.md "Plug-in points" and
    experiments/common/graders/example_grader.py for the generic contract this
    implements.
    """
    if not _cache_primed:
        _prime_cache_from_disk()

    row_key = row.get("row_key")
    answer_text = str(row.get("answer_text", ""))
    aliases_norm = _normalize_aliases(row)

    g = grade_one(answer_text, aliases_norm)

    if row.get("arm") == "baseline" and row_key is not None:
        _baseline_cache[row_key] = {"refused": g["refused"], "correct": g["correct"]}
        baseline_refused, baseline_correct = g["refused"], g["correct"]
    else:
        cached = _baseline_cache.get(row_key)
        if cached is None:
            raise KeyError(
                f"ao_grader: no baseline-arm grade cached for row_key={row_key!r}; "
                "the baseline arm must be graded before (or already present on "
                "disk for) any other arm's rows -- check cell.yaml's arms order "
                "and execution.resume state."
            )
        baseline_refused, baseline_correct = cached["refused"], cached["correct"]

    return {
        "refused": g["refused"],
        "correct": g["correct"],
        "degenerate": g["degenerate"],
        "baseline_refused": baseline_refused,
        "baseline_correct": baseline_correct,
    }
