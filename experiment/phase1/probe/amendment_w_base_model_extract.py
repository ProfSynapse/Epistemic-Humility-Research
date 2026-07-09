"""Compatibility wrapper for the promoted shared readout implementation."""

from importlib import import_module
import runpy
import sys

_IMPL = "experiments.common.readouts.amendment_w_base_model_extract"
_impl = import_module(_IMPL)
globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})
if __name__ != "__main__":
    sys.modules[__name__] = _impl

if __name__ == "__main__":
    runpy.run_module(_IMPL, run_name="__main__")
