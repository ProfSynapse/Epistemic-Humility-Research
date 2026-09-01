# j-space-calibrated-layer-contrast-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-08T12:05:00Z - Full held-out contrast completed locally on the RTX
  3090. Smoke G0 passed first, then full mode ran with
  `--i-know-this-is-the-held-out-run` and wrote public aggregate
  `analysis-committed/full_summary.json`. Result: exploratory pass. Best
  mid-band layer was hs23: clean_tighten 165/185 = 89.2% vs hs34 123/185 =
  66.5%, delta +22.7pp; known-correct cost 9/258 = 3.5% vs hs34 7/258 = 2.7%,
  delta +0.78pp. G1/G2/G3 all passed. Operational limitation: this bespoke
  contrast runner writes only an end-of-run aggregate and is not row-resumable;
  future cells should prefer the generic tuner checkpoint/resume path where
  feasible.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 3 files / ~6 KB, built at repo commit e38646f6.
- HF repo: `professorsynapse/eh-j-space-calibrated-layer-contrast-qwen3-4b` (dataset)
- HF revision: `49b01c09cb6371d236c98151f8f55f6c9a4e3fff`
