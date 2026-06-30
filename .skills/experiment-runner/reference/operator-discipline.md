# Operator Discipline

These are non-negotiables, inherited in spirit from the tuner's fine-tuning
skill:

- **Never** launch a cost-incurring cloud run, cancel a job, or delete artifacts
  unless the user has explicitly approved that exact action in the current
  conversation. Treat launch/cancel/delete as irreversible operator actions; do
  not infer permission from a broader goal.
- **Branch-per-amendment lifecycle (one amendment = one branch = one PR, landed
  before the next).** Cut a dedicated branch from an up-to-date `main` for each
  Amendment or standalone experiment. Do the FULL arc on it (recipes, run
  records, scored results, doc verdict, skill notes), open a PR into `main`, and
  MERGE it before cutting the branch for the next amendment. Do not stack a
  second amendment on an unmerged branch, and do not let a branch accumulate a
  long-lived divergence (Amendment R reached 14 commits off `main` before
  landing — that is the anti-pattern this rule exists to prevent). Serializing
  amendments through `main` keeps it the single source of truth and makes each
  amendment a reviewable, revertable unit. `main` is protected: open a PR, never
  push or commit to it directly. Exception: lab-notebook smokes / diagnostics /
  re-runs that belong to the IN-FLIGHT amendment ride its branch; only a
  genuinely new amendment must start clean off `main`.
- **No-pollution rule (SACROSANCT).** The runner communicates with the tuner
  ONLY through (1) the materialized recipe YAML and (2) the tuner's public CLI
  verbs. It imports NO tuner internals, adds NO committed file under
  `synaptic-tuner/`, and registers NO experiment-specific method/config there.
  The only tuner-tree write is ephemeral per-cell data staged under the tuner's
  ALREADY gitignored `scratch/eh_staging/<run_id>/` — scratch, never source. If
  the runner needs a tuner behavior the CLI does not expose, the correct move is
  to FLAG it (it indicates a missing GENERAL tuner capability), never to reach
  into tuner internals from this repo.
- **Do not guess tuner CLI flags.** Check `synaptic-tuner/tuner/cli/parser.py`
  or `python tuner.py --help` before relying on a flag.
- **Prefer the checked-in `run_matrix.py`** over ad hoc per-cell loops.
- **Never loosen the count assertions** to absorb a `matrix.yaml` edit. The
  counts are pre-registered; a change needs a NEW signed PROTOCOL revision first.
- **Never silently expand the v0.3 matrix for Amendment A.** Mixed-stage
  `SFT -> DPO` / `SFT -> KTO` cells are signed Amendment A / v0.4 prospective
  extension cells, not v0.3 matrix cells. Materialize them only through a
  deliberate implementation path with separate run records and labels.
- **BOTH lanes are safety-gated by a LIVE capability probe.** A cell is only safe
  once the tuner forwards per-cell `seed` / `beta` on the lane it runs; otherwise
  cells silently train at defaults. The gap spans both lanes (cloud command
  builder + local run handler + trainer flags); `check_prereqs` PROBES the actual
  tuner source surface for that lane — not a flag or SHA — and SKIPs cells until
  the probe passes. The local probe currently fails on missing beta forwarding.
  Do not work around this in the runner; the capability is a general tuner change
  (Task #32, coder-cloud owns the reconciliation). See [lanes.md](reference/lanes.md).
