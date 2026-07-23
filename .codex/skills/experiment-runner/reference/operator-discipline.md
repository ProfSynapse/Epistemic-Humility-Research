# Operator Discipline

These are non-negotiables, inherited in spirit from the tuner's fine-tuning
skill:

- **Never** launch a cost-incurring cloud run, cancel a job, or delete artifacts
  unless the user has explicitly approved that exact action in the current
  conversation. Treat launch/cancel/delete as irreversible operator actions; do
  not infer permission from a broader goal.
- **Worktree-per-amendment lifecycle (one amendment = one branch in its OWN
  worktree = one PR).** Cut a dedicated branch from an up-to-date `origin/main`
  for each Amendment or standalone experiment, and materialize it as a git
  WORKTREE (`git worktree add .worktrees/<branch> -b <branch> origin/main`)
  instead of checking it out in the primary working tree. Never swap branches
  in the primary tree: long-running GPU queues, docker mounts, and monitors
  execute scripts from that tree in place, and an in-place checkout changes
  files under a live run (user directive, 2026-07-02). Do the FULL arc for the
  amendment inside its worktree: scaffold with `bin/exp new` so the
  `AMENDMENT.md` and `experiment.yaml` manifest live under `experiments/<slug>/`,
  then recipes, run records, scored results, `bin/exp sign` at sign-off and
  `bin/exp resolve` at the verdict, plus skill notes. Open a PR into `main`, and
  remove the worktree after merge (`git worktree remove`). The pre-commit hook
  validates every manifest and regenerates `experiments/REGISTRY.md`, so run
  `bin/exp regen` and stage it whenever a manifest changes. Amendments proceed
  in PARALLEL, each in its own dedicated worktree: never stack a second
  amendment on another amendment's branch or worktree, and never push amendment
  evidence directly to `main`. Do not let any branch accumulate long-lived
  divergence (Amendment R reached 14 commits off `main` before landing, the
  anti-pattern this rule exists to prevent). `main` is protected: open a PR,
  never push or commit to it directly. Exception: lab-notebook smokes /
  diagnostics / re-runs that belong to the IN-FLIGHT amendment ride its branch;
  only a genuinely new amendment must start clean off `origin/main` (in its own
  worktree, not the in-flight amendment's). Cross-worktree gotcha: a file edited
  but not yet committed in one worktree is invisible to the others, commit (or
  copy) before referencing it from another tree.
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
