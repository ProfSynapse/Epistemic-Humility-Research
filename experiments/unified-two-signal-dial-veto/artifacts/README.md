# Unified Two-Signal Diagnostic Artifacts

These checked-in artifacts are the Stage 1 and Stage 1.5 CPU lab-notebook
diagnostics that de-risked Amendment U. They are historical provenance for the
unified two-signal mechanism, not active runtime inputs.

- `two_signal_stage1_diagnostic.json`: separate gate and dial component
  diagnostic from existing tensors.
- `two_signal_stage1p5_integration.json`: same-item CPU integration diagnostic
  on the Amendment T answerable stream plus SelfAware unknown gate scores.

The producer scripts remain in `experiment/phase1/probe/` for now because they
reuse Phase 1 extraction helpers. Their default `--out` paths point here so a
rerun does not repopulate the legacy probe root.
