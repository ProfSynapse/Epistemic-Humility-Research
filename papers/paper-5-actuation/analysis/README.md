# Paper 5 analysis directory

Paper 5's figures are built directly from each experiment's committed
`analysis-committed/` artifacts under the repo's experiments-first tree
(`experiments/<slug>/analysis-committed/...`). No paper-local snapshot of
those artifacts is made here.

This differs from Paper 4's `analysis/source-artifacts/` pattern: Paper 4's
source files predated the experiments-first layout and had to be migrated out
of a shared locked training-regimen probe tree so the paper could cite a
stable, paper-owned bundle. Paper 5's actuation cells were built directly
under `experiments/<slug>/` from the start, so there is nothing to migrate --
copying the same JSON into a second location here would just create a second
committed copy of the same numbers with no provenance benefit, and a risk of
the copy drifting from the source if the experiment is ever amended.

See `../scripts/build_figures.py` for the exact source paths and
`../figures/MANIFEST.md` for the file -> script -> artifact -> amendment
mapping for every published figure.
