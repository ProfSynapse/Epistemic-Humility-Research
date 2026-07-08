# Legacy migration map

Read this when replacing frozen bespoke Phase 3 machinery with tuner-backed
configs, or when identifying a genericization gap.

The legacy tree is frozen for provenance. Do not edit it while authoring new
cells. New capability should become declarative tuner config or generic tuner
surface area, not another project-local runner.

## Frozen file to tuner replacement

| Legacy file or pattern | Tuner-backed replacement |
|------------------------|--------------------------|
| `confidence_steer.py` `SteeringHook` (`h += alpha*d`) | `mechinterp steer` with `law.kind: additive` or `erase_write`, plus explicit `law.position` and `law.generation_mode`. |
| `amendment_*_grade_and_gates.py` | `mechinterp score-gates` plus a project grader under `experiments/common/graders/` or the experiment's own helper area. |
| `gpu_equivalence_cell.py` CPU-vs-GPU hook check | Built-in `steer` smoke readback / equivalence self-check. |
| `*_extract.py`, `amendment_*_primed_extract.py` | `mechinterp extract` plus optional `content_end_fn` plug-in. |
| `persist_probe_direction.py` fit + persist direction | `mechinterp probe-fit` to frozen `mechinterp-direction/v1` JSON. |
| Bespoke erase-write dose sweeps | `mechinterp dose-calibrate` with `calibration.doses`, `dose_kind`, checkpoint JSONL, and summary JSON. |
| `run_arm_a.py` / `run_arm_b.py` orchestration | `arms` block in one `cell.yaml` using fixed, score-thresholded, flagged, or permuted-control selection. |

## Genericization gaps

Compound multi-write arms and J-lens/token-target direction builders are not
yet first-class tuner verbs. The reusable split is:

- tuner-owned: schema for one arm carrying multiple readout writes, each with
  its own readout, layer override, setpoint/strength, and optional readback;
- project-owned: prompt rendering, row splits, gates, graders, and token/J-lens
  bundles;
- tuner-owned: deterministic checkpoint/resume, recursive `redact_fields`, and
  smoke/readback validation;
- project-owned: restricted-field policy and amendment-specific aggregate gates.

Keep one-off versions project-side only long enough to settle the interface,
then promote the interface as a config-driven tuner surface instead of copying
another bespoke runner.

Do not promote experiment-local no-op record seeding until the runner can assert
the generation contract is deterministic (`do_sample: false`) and the arm is
provably off for that row. Under sampling, copied no-op rows are not a valid
resume optimization.
