# Commitment-Point gen_stream Hook-Firing Check notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13: harness built (`h6_hook_check.py`) implementing the AMENDMENT's
  Design/Measurement/Gates against both real path classes (PATH-BESPOKE:
  `confidence_steer.SteeringHook` + `steering_common.GenerationHookController`
  extracted by source since that module's own import chain is broken against
  the current repo layout, see the harness module docstring; PATH-TUNER:
  synaptic-tuner `MechInterp.intervention.InterventionHook` +
  `GenerationInterventionController`, unmodified). `gates.yaml` filled in
  (was a placeholder) by transcribing AMENDMENT.md's H6-G1..G4 thresholds
  verbatim, no new numbers. CPU smoke (`test_h6_smoke.py`, 7 tests) run
  against a tiny from-scratch plain-HF GPT2 model (no download, no GPU):
  ALL PASS for both paths' harness code, plus the existing tuner regression
  suite `synaptic-tuner/tests/mech_interp/test_gen_stream_firing.py` (6
  tests, pre-existing, not modified) cross-checked green. No GPU load
  performed; PATH-BESPOKE's real confound (Unsloth `for_inference`) is
  untestable on CPU by construction and remains open pending the real-model
  run. See the build report for adjudications made during construction
  (off-by-one in decode-call counting, PATH-BESPOKE's structural NOOP
  short-circuit, prompt-rendering scope for the real-run CLI).
