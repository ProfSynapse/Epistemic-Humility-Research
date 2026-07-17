"""SC1 (dose readback) checks for margin-separation-fine-ladder (M1b)
(gates.yaml `SC1_dose_and_preflight`).

Ported (logic, byte-identical) from `margin-mapping/sc1_checks.py` (read in
full before writing this): the ONE check that applies to every M1b dosed
rung, |readback_measured - target| / target <= 0.005 OR
|readback_measured - target| <= 0.005 x family reference_dose_abs (M1's
PI-approved amended OR-rule, carried verbatim -- gates.yaml SC1 line 18),
target = the ladder rung's setpoint (multiplier * family reference_dose_abs).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

READBACK_TOLERANCE_REL = config.READBACK_TOLERANCE_REL
READBACK_TOLERANCE_ABS_FRAC_OF_REF = config.READBACK_TOLERANCE_ABS_FRAC_OF_REF


def check_readback(row_key: str, family: str, readback_measured: float | None, target: float) -> dict[str, Any]:
    # gates.yaml SC1 (M1's PI-approved OR-rule, carried verbatim): pass on
    # rel <= 0.005 OR abs <= 0.005 x family reference_dose_abs.
    if readback_measured is None:
        return {"row_key": row_key, "family": family, "readback_measured": None, "target": target, "passed": False, "reason": "no_readback_recorded"}
    delta = abs(readback_measured - target)
    rel_delta = delta / abs(target)
    tolerance_abs = READBACK_TOLERANCE_ABS_FRAC_OF_REF * config.REFERENCE_DOSE_ABS[family]
    return {
        "row_key": row_key, "family": family, "readback_measured": readback_measured, "target": target,
        "abs_delta": delta, "rel_delta": rel_delta, "tolerance_rel": READBACK_TOLERANCE_REL,
        "tolerance_abs": tolerance_abs,
        "passed": (rel_delta <= READBACK_TOLERANCE_REL) or (delta <= tolerance_abs),
    }
