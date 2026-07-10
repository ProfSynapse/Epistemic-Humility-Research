# Phase 1 (frozen historical record)

This tree is the historical record of the Phase 1 protocol era: the LOCKED
PROTOCOL v0.3 run matrix, its run records, the probe pipeline, and the bespoke
steering / mech-interp machinery. It is preserved for provenance and stays
byte-stable as the signed instrument of past and in-flight amendments. The frozen
steering machinery and its terms are catalogued in
`probe/steering/LEGACY.md`.

Nothing new lands here. New evidence-producing work lives at the top-level
`experiments/` tree (one self-contained directory per experiment); see
`experiments/README.md`. New activation reading/writing cells use the tuner
`mechinterp` verbs per the `mechinterp-cells` skill, never the frozen scripts
under `probe/steering/`.
