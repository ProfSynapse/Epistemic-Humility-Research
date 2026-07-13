# Archived Probe-Root Amendment Scripts

This directory holds frozen legacy scripts formerly stored directly under
`experiment/phase1/probe/` with names like `amendment_<letter>_*.py`.

The directory is intentionally flat because those scripts were authored as one
flat Python import namespace. Preserve that shape when archiving additional
probe-root amendment scripts unless a later migration also rewrites their import
graph.

Do not add new experiment machinery here. New activation-reading, probe-fit,
steering, or gate-scoring cells belong under `experiments/<slug>/` and should use
the tuner-backed `mechinterp` path described by the `mechinterp-cells` skill.
