"""Compatibility wrapper for archived Amendment AH implementation."""

from _archived_amendment_wrapper import load_archived_module, run_archived_module

_MODULE = "amendment_ah_stage0_extract"
_impl = load_archived_module(_MODULE)
globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})

if __name__ == "__main__":
    run_archived_module(_MODULE)
