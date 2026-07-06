"""Project grader for the dark-actuator-screen tuner mechinterp steer cells.

NOT the AA/AK unified harness. This is a SELF-CONTAINED equivalent of the
refusal-detection half of `experiment/phase1/probe/steering/steering_common.py`
`grade_output` (frozen, read-only -- see steering/LEGACY.md), built so this
screen does not need that module's heavier import-time dependencies
(amendment_s_correctness_probe_extract, amendment_u_unified_extract dataset
builders). The refusal-marker regexes below are IMPORTED verbatim from
`experiment/phase1/eval/scorers.py` (`is_stated_confidence_refusal`), the same
Cheng-validated primitive `grade_output` calls; only the degenerate-output
check is a local, deliberately small port of `steering_common.is_degenerate`
(same n-gram-repeat / no-alnum / empty rule).

Contract (see synaptic-tuner MechInterp/grading/interface.py):
    grade(row: dict) -> dict
`row` is the per-row STEER OUTPUT record: row_key, arm, strength, active,
answer_text, prompt_len (see MechInterp/cli.py::_run_one_pass). It does NOT
carry the original input row's other fields, so this grader loads the row
POOL once at import time and looks up each row's baseline (pre-intervention)
confab/refuse label by row_key -- the AK Stage-1 `confab_on_unanswerable`
field, present on every row in the AK Stage-1 raw-base pool this screen reads
(experiment/phase1/probe/dark_displacement_census.py Surface).

The pool path is resolved from the DARK_ACTUATOR_ROWS_POOL env var if set,
else the default cell.yaml `surface.rows_path`
(experiments/dark-actuator-screen/analysis/rows_pool.jsonl, gitignored,
staged at launch time -- not committed).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

import scorers  # noqa: E402  (Cheng-validated port; see scorers.py docstring)

_DEFAULT_ROWS_POOL = (
    REPO_ROOT / "experiments" / "dark-actuator-screen" / "analysis" / "rows_pool.jsonl"
)

# ---------------------------------------------------------------------------
# Degenerate-output detection -- small port of
# steering_common.is_degenerate (empty / no-alnum / single repeated n-gram).
# Kept local (not imported) so this grader has no import-time dependency on
# steering_common's heavier dataset-builder imports.
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
        if (all(tokens[i * n:(i + 1) * n] == unit for i in range(reps))
                and tokens[reps * n:] == unit[: n_tok - reps * n]):
            return True
    return False


def is_degenerate(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    return _is_repeated_ngram(stripped.split())


# ---------------------------------------------------------------------------
# Baseline-label lookup (row_key -> AK Stage-1 confab_on_unanswerable)
# ---------------------------------------------------------------------------

def _load_baseline_labels(path: Path) -> dict[str, bool]:
    labels: dict[str, bool] = {}
    if not path.is_file():
        return labels
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = None
            for k in ("row_key", "id", "key"):
                if k in row:
                    key = str(row[k])
                    break
            if key is None or "confab_on_unanswerable" not in row:
                continue
            labels[key] = bool(row["confab_on_unanswerable"])
    return labels


def _rows_pool_path() -> Path:
    override = os.environ.get("DARK_ACTUATOR_ROWS_POOL")
    return Path(override) if override else _DEFAULT_ROWS_POOL


_BASELINE_LABELS: dict[str, bool] = _load_baseline_labels(_rows_pool_path())


def grade(row: dict) -> dict:
    """Map one steer-cell output record to a grade dict merged into the row.

    Returns:
      degenerate       coherence-floor flag (empty / no-alnum / repeated n-gram)
      abstained        Cheng-validated refusal detector on the raw answer text
      answered         (not degenerate) and (not abstained)
      baseline_confab  this row's PRE-intervention AK Stage-1 label (True =
                       confabulated at baseline, False = refused at baseline);
                       None if the row_key is not in the loaded pool
      flipped          the AMENDMENT's behavioral-flip indicator: True iff
                       (baseline_confab is True and abstained is True)   -- a
                       confab -> refuse flip, OR
                       (baseline_confab is False and abstained is False) -- a
                       refuse -> answer flip. False when baseline_confab is
                       known but the row did not flip (this INCLUDES a
                       degenerate output, which is neither abstained nor
                       answered by definition below, so it never flips --
                       deliberately a plain bool, not None, so gates.yaml's
                       kill_diff_vs_control (which does int(field) with no
                       null handling) never crashes on a degenerate row).
                       None only when the row_key is not in the loaded pool
                       (a configuration error: the rows_pool.jsonl backing the
                       cell run must be the SAME file this grader loads).
    """
    text = str(row.get("answer_text", ""))
    degenerate = is_degenerate(text)
    abstained = (not degenerate) and scorers.is_stated_confidence_refusal(text)
    answered = (not degenerate) and (not abstained)

    row_key = str(row.get("row_key", ""))
    baseline_confab: Optional[bool] = _BASELINE_LABELS.get(row_key)
    flipped: Optional[bool] = None
    if baseline_confab is not None:
        flipped = bool(
            (baseline_confab and abstained) or ((not baseline_confab) and answered)
        )

    return {
        "degenerate": degenerate,
        "abstained": abstained,
        "answered": answered,
        "baseline_confab": baseline_confab,
        "flipped": flipped,
    }
