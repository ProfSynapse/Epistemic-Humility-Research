# Archived Legacy Mechinterp Local Gotchas

Read for archived legacy mechinterp causal-pilot and logit-diagnostic execution caveats.

- For archived legacy mechinterp causal-pilot GPU smokes in `unsloth/unsloth:latest`, override the
  default image entrypoint with `--entrypoint python` before invoking
  `experiments/common/mechinterp/causal_pilot_runner.py`. Without the override,
  the image can run studio setup, try to chmod the mounted repository, fail on
  Windows-mounted repo permissions, and never invoke the runner. This applies to
  the logit diagnostic path as well as generation smokes; use
  `--mode logit_diagnostic --allow-logit-diagnostic` for the bounded logit check
  through the existing archived legacy activation hook/model/candidate path.

- Archived legacy mechinterp causal-pilot live runs must not blindly reuse readiness-plan control
  labels as executable intervention labels. The dry-run config can list future
  controls such as random direction, shuffled labels, wrong-layer neighbors, and
  sign flips before the live runner implements them. A live runner should fail
  closed on unsupported controls and use explicit labels such as
  `activation_addition` and `activation_subtraction`; otherwise an artifact can
  be mechanically valid but scientifically mislabeled. First live smoke on
  2026-06-18 caught this: `control=sign_flip` with a positive coefficient was
  a valid hook/scoring smoke, but the label was misleading for interpretation.

- Archived legacy mechinterp causal-pilot logit diagnostics are gated separately from generation:
  use `--mode logit_diagnostic --allow-logit-diagnostic` when the question is
  whether activation addition/subtraction changes next-token logits before
  scaling generated rows. A moved logit distribution with unchanged greedy
  top-1 means the hook is mechanically active but not yet behaviorally strong
  under that direction/layer/coefficient; prefer richer logit probability
  slices, an alternate direction, a layer/position sweep, or a final-norm
  intervention before treating the null generation result as decisive.
