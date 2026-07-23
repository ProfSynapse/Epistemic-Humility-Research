"""SC1 (dose readback) checks for margin-evidence-responsiveness-worldknown
(M4-WK) (gates.yaml `SC1_dose_and_preflight`).

Ported (logic, byte-identical) from `margin-mapping/harness/sc1_checks.py`
(read in full before writing this): |readback_measured - target| / target
<= 0.005, OR abs_delta <= 0.005 x reference_dose_abs (M1's amended OR-abs
rule, carried verbatim). M1 keyed the abs-tolerance by FAMILY; M4-WK takes
`reference_dose_abs` directly as an argument (per-DIRECTION reference dose,
not per-family -- this cell is qwen-only but runs two directions)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

READBACK_TOLERANCE_REL = config.READBACK_TOLERANCE_REL
READBACK_TOLERANCE_ABS_FRAC_OF_REF = config.READBACK_TOLERANCE_ABS_FRAC_OF_REF


def check_readback(row_key: str, direction: str, readback_measured: float | None, target: float, reference_dose_abs: float) -> dict[str, Any]:
    if readback_measured is None:
        return {"row_key": row_key, "direction": direction, "readback_measured": None, "target": target, "passed": False, "reason": "no_readback_recorded"}
    delta = abs(readback_measured - target)
    rel_delta = delta / abs(target) if target != 0 else float("inf")
    tolerance_abs = READBACK_TOLERANCE_ABS_FRAC_OF_REF * reference_dose_abs
    return {
        "row_key": row_key, "direction": direction, "readback_measured": readback_measured, "target": target,
        "abs_delta": delta, "rel_delta": rel_delta, "tolerance_rel": READBACK_TOLERANCE_REL,
        "tolerance_abs": tolerance_abs,
        "passed": (rel_delta <= READBACK_TOLERANCE_REL) or (delta <= tolerance_abs),
    }
