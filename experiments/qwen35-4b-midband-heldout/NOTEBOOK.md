# Qwen3.5-4B mid-band doubt-snap held-out confirmation (hs20 frozen operating point) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (draft): scaffolded and drafted the held-out confirmation stage
  reserved by qwen35-4b-midband-doubt-snap scope statement 2. Frozen operating
  point (hs20 direction set, tau_frozen, mu/sigma, sigma_c, dose 8 x sigma_c)
  is consumed verbatim from the ladder's committed artifacts; nothing is refit.
  Population is the untouched 1,332 confab + 360 known held-out pool. Four arms
  (baseline / gated / random_direction / permuted_gate), one dose. Gates:
  G0 instrument-validity stop, G1 primary (refused >= 0.60 AND well-formed
  >= 0.80, cost <= 0.10 over full 360 knowns), G3(i)/G3(ii) placebo. Prediction
  and falsifier enumerate outcome shapes A through E so nothing lands between
  them (fleet wording-gap lesson). NOT signed; harness not written (separate
  assignment). See AMENDMENT.md.

## 2026-07-13 - Sign preparation: provenance pins filled, tolerance adjudication recorded (lead)

Frozen operating-point hashes filled from the resolved
qwen35-4b-midband-doubt-snap ladder's committed artifacts (build_manifest
f0a8ea7a..., hs20 u_d 18e78f25..., c_hat 937d1bff..., random_direction
db8b930d...; full values in frozen_operating_point_hashes.json).
verify_frozen_operating_point_hashes() now has real targets and pipeline.py
refuses to run on any mismatch. All 12 instrument files (9 modules + cell.yaml
+ gates.yaml + the frozen-hash file) hand-pinned in experiment.yaml.

Tolerance adjudication (binding, recorded at sign as required by the G0
hardening acceptance): gates.yaml's "readback within tolerance" is read as the
shared synaptic-tuner MechInterp SmokeConfig contract via
evaluate_smoke_readback (write_rel_tol 0.05, write_abs_floor 0.5,
offtarget_tol 1e-3), applied in smoke mode to the gated and random arms. This
defers to the one shared readback-tolerance definition in the codebase rather
than minting a local variant; any future change to SmokeConfig would surface
as a pin-visible diff in the shared module, not silently here.

Full suite green post-rebase. Scoreboard: orchestrator call recorded in
AMENDMENT.md; awaiting the PI call, then bin/exp sign and the GPU sequence
(materialize -> capture_anchors ~18-19 min -> pipeline smoke -> full run).
