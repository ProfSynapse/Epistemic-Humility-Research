# jspace-family-atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-12 (lead adjudication of the two build ambiguities, pre-sign): (1)
  eff_dim_frac is the Stage A participation-ratio FORMULA applied to
  anchor hidden-state variance, not Stage A's JVP-push input; the
  cross-program comparability claim is dropped from the design and the
  profile is comparable across atlas cells only. (2) The read panel gains a
  deterministic 50/50 subdivision of the fit_only refused pool
  (refused_fit for direction fitting, refused_eval for scoring, seed
  20260707) so all reported AUROCs are two-sided held-out rather than
  half-in-sample; no behavioral row changes split. Both changes are in the
  draft AMENDMENT before signing; profile_and_read_panel.py needs the
  refused-split implementation before sign.

- 2026-07-12: Instrument built (draft, unsigned, not launched). Delivered
  `cell.yaml`, `gates.yaml` (AG0/AG1/AG2 transcribed verbatim from
  AMENDMENT.md), `render_jspace_atlas.py` (ported from the fleet's
  `render.py`), `capture_atlas_cell.py` (GPU: full-depth anchor capture,
  `--layers all`, manual-tokenize `len(token_ids)-1` anchor position mirrored
  from `doubt-snap-cross-family-confirmatory/prep_tuner_cell.py:402-419` for
  audit-parity), `profile_and_read_panel.py` (CPU: eff_dim_frac via the
  participation-ratio estimator ported byte-for-byte from
  `experiments/qwen35-4b-midband-doubt-snap/jlens_qwen35.py:183-193`/`:224`,
  plus a per-layer read panel with 2000-resample bootstrap AUROC CIs for
  doubt/caution/raw_refusal), `cloud/modal_jspace_atlas.py` (capture-only
  Modal wrapper, A10G default, mounts the fleet's `eh-doubt-snap-cross-family`
  volume read-only for input plus this experiment's own
  `eh-jspace-family-atlas` volume for output), and
  `smoke_profile_and_read_panel.py` (local CPU smoke against synthetic
  captures; passed).
  Row counts verified directly against each fleet cell's committed
  `split_manifest.json` (pulled read-only via `modal volume get`, aggregate
  fields only): llama32_3b_instruct 2,956 rows (confab 1453, known_correct
  556, unknown_refused 947); mistral7b_instruct_v03 3,037 rows (confab 2186,
  known_correct 637, unknown_refused 214).
  Cost estimate (capture-only, one forward pass per row, no generation, no
  in-repo empirical benchmark for this exact workload so treat as rough):
  5,993 total rows x roughly 150 prompt tokens each is approximately 900K
  tokens; at an assumed 1,000-3,000 tok/s A10G prefill throughput that is
  roughly 5-15 GPU-busy minutes total, plus cold-start/model-download and
  safetensors I/O overhead (~2.5 GiB float32 anchor tensors across both
  cells), for a rough total wall time of 30-45 minutes across both cells at
  the repo's own stated A10G rate (~$1.10-1.50/hr, per
  `experiments/j-space-localization-qwen3-4b/NOTEBOOK.md:166`) => under $2
  total. This should be confirmed against the wrapper's own logs on first
  launch rather than trusted as precise.
  Two ambiguities resolved and flagged for lead review (full detail in
  `cell.yaml`/`profile_and_read_panel.py` comments): (1) "the same estimator
  as Stage A" is read as the identical `_participation_ratio` formula
  applied to captured hidden states rather than Stage A's JVP-push vectors,
  since this atlas is capture-only with no gradients; (2) all three read-panel
  axes' held-out AUROC is only half held-out, because `unknown_refused` is
  `fit_only` in both fleet cells (0 held-out rows by the fleet's own
  stratified_split design) -- every axis's held-out AUROC scores the
  genuinely-held-out class against the same fit_only refused pool used to
  fit the direction, not a fully held-out contrast on both sides.
  Not signed, not launched. `bin/exp validate` passes (63 experiments, no
  manifest errors introduced).
