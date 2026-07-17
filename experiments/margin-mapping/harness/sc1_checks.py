"""SC1 (dose readback) checks for margin-mapping (M1) (gates.yaml
`SC1_dose_and_preflight`).

Trimmed from `gate-contribution-factorial/sc1_checks.py` (read in full
before writing this): M1 has NO random-direction arms and no randomness-bar
seed ledger (every rung is a c_hat erase-write; cell.yaml `ladder`: "No gate
anywhere: every row in the population is dosed at every ladder step" -- the
factorial's `check_randomness_bar`/`resolve_seed_ledger` machinery is for
its K=5 random-direction arms, which M1 does not have). Only `check_readback`
is ported (logic, byte-identical) -- the ONE check that applies to every
M1 dosed rung: |readback_measured - target| / target <= 0.005 (gates.yaml
line 16), target = the ladder rung's setpoint (multiplier * family
reference_dose_abs), not a fixed single setpoint.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

READBACK_TOLERANCE_REL = config.READBACK_TOLERANCE_REL


def check_readback(row_key: str, family: str, readback_measured: float | None, target: float) -> dict[str, Any]:
    if readback_measured is None:
        return {"row_key": row_key, "family": family, "readback_measured": None, "target": target, "passed": False, "reason": "no_readback_recorded"}
    delta = abs(readback_measured - target)
    rel_delta = delta / abs(target)
    return {
        "row_key": row_key, "family": family, "readback_measured": readback_measured, "target": target,
        "abs_delta": delta, "rel_delta": rel_delta, "tolerance_rel": READBACK_TOLERANCE_REL,
        "passed": rel_delta <= READBACK_TOLERANCE_REL,
    }
