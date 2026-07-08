# J-Space Mid-Band Dose Calibration Provenance

This experiment follows the pre-outcome G0 stop in
`j-space-midband-write-sweep-qwen3-4b`.

Public committed inputs:

- `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/build_manifest_layers.json`
- `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/gate_fit_layers.json`
- `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/`
- `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/smoke_summary.json`

Local private inputs:

- `experiments/j-space-midband-write-sweep-qwen3-4b/analysis/rows_with_text.jsonl`
  for FIT row text and aliases.
- The source experiment's gitignored activation scratch, if gate decisions need
  to be recomputed from frozen readouts.

Containment:

- The calibration script writes only aggregate public summaries under
  `analysis-committed/`.
- Row text, aliases, raw generations, and logs remain under gitignored
  `analysis/`.

Committed output:

- `dose_calibration_summary.json`: aggregate FIT-only dose calibration summary
  with selected setpoints hs23=25, hs26=75, hs29=125, hs34=175. It contains no
  row text, aliases, or raw generations.
