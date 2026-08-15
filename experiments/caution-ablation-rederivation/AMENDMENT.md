# Re-deriving the archived caution-ablation over-refusal collapse

Status: DRAFT (2026-08-15). Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 3's Section 6 cited an ablation result (known-item over-refusal 0.994
to 0.030 on the clean_sft_grpo_v2_seed1 checkpoint) whose evidence chain was
found un-re-derivable: the `write-direction-naming-battery` amendment
documents that the figure's only sources are paper-3 prose and archived
phase-1 intervention configs whose declared output paths no longer exist.
The governed `doubt-regulated-caution` cell supports the same qualitative
claim at 0.994 to 0.524 (in-frame replication 0.536, specificity intact),
and per the PI ruling of 2026-08-15 paper 3 now carries those governed
numbers. The PI then asked for the archived pipeline to be RE-RUN so the
0.030 figure either regains a governed source or is formally retired.

Posture: provenance repair, exploratory tier-2. Whatever this cell finds,
it does NOT by itself re-promote 0.030 into any paper; promotion would
require a further registered confirmatory step. The interesting secondary
question is why the archived figure (0.030) and the governed in-frame
result (0.524/0.536) differ so strongly; the registrant's working
hypothesis is instrument-frame difference (different intervention variant,
detector frame, and layer targeting), not error in either.

## Design

Reproduce the archived intervention pipeline exactly, on the frozen legacy
mech-interp machinery (no modernization; the point is byte-faithful
re-derivation of an archived instrument):

- Checkpoint: `clean_sft_grpo_v2_seed1`
  (`scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`,
  the published `eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` weights).
- Direction vectors, archived, pinned by sha256:
  - `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_direction/caution_direction_L35.json`
    `9eb2a8c91dd950e669065f7a80b1424a0c3c24c389ed2a9ea1f98f13072d8785`
  - `.../caution_perp_direction_L35.json`
    `41e13f41100756fd10a974af8a7724940348ab869f2045be62ad4e86a079ee64`
- Intervention configs, archived, re-run verbatim (both, since the archived
  record does not unambiguously identify which variant produced 0.030):
  - `archive/experiment/phase1/probe/config/grpo-v2-residual-repair/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`
  - `archive/experiment/phase1/probe/config/grpo-v2-residual-repair/phase3_current_clean_grpo_v2_caution_perp_residual_intervention.yaml`
  - `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`
- Step 0 (pre-run, no GPU): reconstruct from the archived configs, the KG
  mechanism note, and session doc
  `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md` which
  variant the 0.030 claim most plausibly came from; record the attribution
  in NOTEBOOK.md BEFORE results exist.
- Each config's baseline (no-intervention) arm re-runs alongside its
  ablation arm; outputs land under this cell's gitignored results dir with
  aggregate metrics copied to `analysis-committed/`.

Engine exception (generation-bearing, sign-gate):
`instrument.engine_exception: {kind: parity-locked}` — the archived legacy
probe/steering stack is the instrument under test; switching its generation
engine would defeat the re-derivation.

## Prediction

Under the archived instrument, at least one archived intervention variant
reproduces the collapse: post-ablation known-item over-refusal at or below
0.10 (registrant's modal expectation: the caution_perp variant), with the
no-intervention baseline reproducing ~0.994 within 0.02.

## Falsifier

No archived variant brings post-ablation known-item over-refusal below
0.30 under the archived instrument: the 0.030 figure is declared not
recoverable and formally retired; paper 3 keeps the governed
doubt-regulated-caution numbers either way (pre-stated: this cell cannot
move paper text on its own).

## Gates

- CA-G0 (integrity, pre-outcome stop): direction-file shas match the pins
  above; archived config bytes unmodified (any incompatibility is a stop
  and report, never a patch-and-run); full coverage of each config's
  declared row set; baseline arm reproduces 0.994 within +/-0.02 (baseline
  drift = instrument-not-reproduced stop, results not interpretable).
- CA-G1 (reproduction call, fixed here): per variant, post-ablation
  known-item over-refusal <= 0.10 = reproduced; in (0.10, 0.30) = partial,
  reported as such with no promotion; >= 0.30 = not recoverable. Thresholds
  fixed before the run, never retuned.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | caution_perp variant reproduces <= 0.10; frame difference (variant/detector/layer), not error, explains the 0.524 divergence |
| user | requested the re-run 2026-08-15; no directional call recorded |

## Budget

One checkpoint, two-to-three intervention configs with baselines on the
known-item row set; ~1-2 GPU-hours on the local 3090. QUEUED BEHIND
`prompt-crossing-completion` (currently running). Launch authorized by the
PI 2026-08-15 ("can we re run the experiment where we got the .030").

## Outcome

Filled at resolve.
