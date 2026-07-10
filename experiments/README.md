# Experiments

This is the going-forward home for all new evidence-producing work. Every
experiment is one self-contained directory, `experiments/<slug>/`, holding
everything needed to run and adjudicate it:

- `AMENDMENT.md` - the signed protocol amendment (prediction, falsifier, gates).
- `experiment.yaml` - a thin, machine-readable manifest (indices are GENERATED
  from these manifests, never hand-edited).
- `cell.yaml` / `gates.yaml` - the tuner cell config and its declarative gates.
- `NOTEBOOK.md` - the running lab notebook for the experiment.
- `analysis/` - run outputs. UNTRACKED (gitignored).
- `directions/` - fitted direction data. UNTRACKED (gitignored); promoted to
  `experiments/common/directions/<checkpoint>/` the first time a second
  experiment consumes the same direction.

Shared, cross-experiment code lives under `experiments/common/`
(`cloud/`, `graders/`, `renders/`, and promoted `directions/`).

## Rules

- **Experiments-first.** New work lands here, not in `experiment/` (singular),
  which is the FROZEN historical Phase 1 protocol era. See
  `experiment/phase1/README.md`.
- **Indices are generated, never hand-edited.** The registry and any roll-up
  index are produced from each experiment's `experiment.yaml` manifest.
- **Lifecycle tooling is `bin/exp`.** Scaffolding, signing, index regeneration,
  and validation run through the `bin/exp` CLI and the `experiments` skill (PR in
  flight; see `.skills/experiments/` once merged).
- **Naming.** The directory slug matches the amendment letter (e.g.
  `amendment-an`) or the diagnostic slug for a lab-notebook diagnostic.

## example-cell/

`experiments/example-cell/` is a teaching artifact for the `mechinterp-cells`
skill, NOT a registered instrument: it parses against the real tuner schema and
runs end to end, but it is never signed and never launched as confirmatory.
