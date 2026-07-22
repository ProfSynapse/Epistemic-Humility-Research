"""Per-rung dose construction for margin-separation-fine-ladder (M1b).

Ported (logic, byte-identical) from `margin-mapping/dose_ladder.py` (read in
full before writing this), itself ported from `gate-contribution-factorial/
run_factorial.py::c_hat_write_params`. SAME erase-write sigma/gain contract
(setpoint = gain * sigma; InterventionHook's own contract), unchanged across
this experiment's 8-rung ladder. `sigma` and `gain` are kept as two named
return values (never conflated) for the same reason M1 keeps them separate:
a 2026-07-16 factorial defect realized gain**2 by conflating the two at a
call site.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402


def rung_dose_abs(family: str, multiplier: float) -> float:
    """The ladder rung's target setpoint dose_abs (cell.yaml `ladder.write.
    setpoint: multiplier x reference_dose_abs`)."""
    return multiplier * config.REFERENCE_DOSE_ABS[family]


def c_hat_write_params(family: str, setpoint: float) -> tuple[float, float]:
    """c_hat erase-write: sigma = SIGMA_C[family] (the c_hat direction is
    calibrated so gain=1.0 corresponds to one sigma_c of realized
    projection), gain = setpoint / sigma_c."""
    sigma = config.SIGMA_C[family]
    gain = float(setpoint / sigma)
    return sigma, gain


def rung_tag(multiplier: float) -> str:
    """Filesystem/RunLog-safe tag for a ladder multiplier (no '.' in the
    tag; RunLog paths and preflight report keys use this)."""
    s = f"{multiplier:g}"
    return s.replace(".", "p").replace("-", "neg")
