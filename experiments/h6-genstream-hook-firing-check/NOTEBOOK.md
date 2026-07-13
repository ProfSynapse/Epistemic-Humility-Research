# Commitment-Point gen_stream Hook-Firing Check notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (SIGNED, pre-launch): Signed after lead review of the built
  harness (commit 93bda177; CPU smoke re-run by the lead under pytest, 7/7
  both paths; note the smoke is pytest-style and a bare python3 invocation
  exits 0 silently without running anything, so always run it via
  python3 -m pytest). gates.yaml was transcribed from AMENDMENT.md
  thresholds verbatim pre-sign (was a placeholder). Builder adjudications
  reviewed and accepted, recorded here so the Outcome inherits them:
  (1) PATH-BESPOKE's GenerationHookController is source-extracted from the
  archived steering_common.py because that module's import chain broke in
  the paper-reorg migration; the extraction is the exact class source with
  no runtime dependency on the broken imports, and SteeringHook imports
  unmodified. (2) PATH-TUNER's NOOP condition uses force_active=True at
  strength 0.0 so the real clone/add code path is exercised, not the
  inactive-row early-exit. (3) PATH-BESPOKE's NOOP is a structural identity
  with ABSENT by construction (its controller short-circuits at alpha==0
  before touching the hidden state), so add-zero perturbation is untestable
  on that path as written; its G3 pass is legitimate but weaker, and the
  Outcome must say so. (4) H6-G1's decode-call count reads HF cached
  generate() semantics: N new tokens = 1 prefill + N-1 decode-only calls,
  and both controllers' gen_stream mode skips the prefill, so the exact
  expectation is N-1 steered calls. Launch: local RTX 3090 after the H4 run
  frees the card; GPU minutes for both paths.

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
