"""Per-rung dose construction for margin-mapping (M1) (cell.yaml `ladder`).

`c_hat_write_params` is ported (logic, byte-identical) from
`gate-contribution-factorial/run_factorial.py::c_hat_write_params` (read in
full before writing this) -- SAME erase-write sigma/gain contract (setpoint =
gain * sigma; InterventionHook's own contract), generalized here across the
ladder's 10 rungs instead of the factorial's single fixed setpoint. The
factorial's own defect history is directly relevant: a 2026-07-16 fix there
corrected BOTH call sites that had passed the gain as the sigma argument to
`steer_lib.build_hook_and_controller` AND as the generation strength,
realizing gain**2 instead of gain*sigma at every dosed write. This module
keeps `sigma` and `gain` as two named return values (never conflated) for
exactly the same reason; the smoke suite pins `sigma != gain` per family per
rung as a regression guard.
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
