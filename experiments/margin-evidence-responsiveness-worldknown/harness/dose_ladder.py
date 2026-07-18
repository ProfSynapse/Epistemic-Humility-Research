"""Per-rung dose construction for margin-evidence-responsiveness-worldknown
(M4-WK).

Ported (logic, byte-identical mechanics) from `margin-mapping/harness/
dose_ladder.py` (read in full before writing this) -- same erase-write
sigma/gain contract (setpoint = gain * sigma; InterventionHook's own
contract). M1 keyed everything by FAMILY (two families, one reference dose
and sigma_c each); M4-WK keys by DIRECTION instead (transfer/native, each
with its own reference_dose_abs and sigma_c), since this cell is qwen-only
but runs two directions. `sigma` and `gain` stay two named return values,
never conflated, mirroring M1's regression guard against the 2026-07-16
factorial defect (gain passed as both the sigma argument and the generation
strength, realizing gain**2 instead of gain*sigma).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402


def reference_dose_abs(direction: str) -> float:
    if direction == "transfer":
        return config.TRANSFER_REFERENCE_DOSE_ABS
    if direction == "native":
        return _native_reference_dose_abs()
    raise ValueError(f"unknown direction {direction!r}")


def sigma_c(direction: str) -> float:
    if direction == "transfer":
        return config.TRANSFER_SIGMA_C
    if direction == "native":
        return _native_sigma_c()
    raise ValueError(f"unknown direction {direction!r}")


def _native_direction_record() -> dict:
    import common

    if not config.NATIVE_C_HAT_PATH.is_file():
        raise SystemExit(
            f"dose_ladder FAIL: native direction not fit yet; no "
            f"{config.NATIVE_C_HAT_PATH}. Run fit_native.py first."
        )
    return common.load_json(config.NATIVE_C_HAT_PATH)


def _native_sigma_c() -> float:
    return float(_native_direction_record()["sigma"])


def _native_reference_dose_abs() -> float:
    """fork 1: native reference_dose_abs = 8x the native fit's own sigma_c
    (the SAME 8x multiplier that set the KUQ/transfer reference dose,
    12.608187917799976 = 8 x 1.576023489724997)."""
    return config.NATIVE_REFERENCE_DOSE_MULTIPLIER * _native_sigma_c()


def rung_dose_abs(direction: str, multiplier: float) -> float:
    """The ladder rung's target setpoint dose_abs (cell.yaml
    `channel2_margin.ladder_rebuild`: multiplier x reference_dose_abs[direction])."""
    return multiplier * reference_dose_abs(direction)


def c_hat_write_params(direction: str, setpoint: float) -> tuple[float, float]:
    """c_hat erase-write: sigma = sigma_c[direction] (the c_hat direction is
    calibrated so gain=1.0 corresponds to one sigma_c of realized
    projection), gain = setpoint / sigma_c."""
    sigma = sigma_c(direction)
    gain = float(setpoint / sigma)
    return sigma, gain


def rung_tag(multiplier: float) -> str:
    """Filesystem/RunLog-safe tag for a ladder multiplier (no '.' in the
    tag; RunLog paths and preflight report keys use this)."""
    s = f"{multiplier:g}"
    return s.replace(".", "p").replace("-", "neg")
