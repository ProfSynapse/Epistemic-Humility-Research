"""Compatibility wrapper for the Probe-as-Reward experiment script."""

from _experiment_script_wrapper import load_experiment_script, run_experiment_script

_SLUG = "probe-as-reward"
_MODULE = "par_sensor_refit_union_inloop"
_impl = load_experiment_script(_SLUG, _MODULE)
globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})

if __name__ == "__main__":
    run_experiment_script(_SLUG, _MODULE)
