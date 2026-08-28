# j-space-token-targeted-refusal-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-08T17:05:00Z - Held-out run resolved. The full 443-row local 3090
  run completed and wrote `analysis-committed/full_summary.json`.
  `c_hat_plus_j_token_hs23` improved confab clean_tighten by only +0.54pp over
  `c_hat_only_hs23` (166/185 = 89.7% vs 165/185 = 89.2%), below the pre-stated
  +4pp G1 threshold. Known-correct cost stayed within guard (+0.39pp), random-J
  did not improve, format/language guards passed, and all write readbacks were
  100% within tolerance. `j_token_only_hs23` was non-inert at 88/185 = 47.6%,
  but the natural observed token-target direction is mostly redundant once the
  stronger `c_hat` snap is active. Resolved the amendment as exploratory
  falsified and kept row-level records private.

- 2026-07-08T16:40:00Z - Scalability hygiene pass while the held-out run
  continued. Synced the generated `mechinterp-cells` skill mirrors after the
  canonical skill documented `execution.redact_fields` and the current
  genericization boundary. Also updated TODO item 42 from draft/signing language
  to the actual signed + held-out-running state, and clarified item 44 as the
  next generic tuner interface: config-driven compound multi-readout writes plus
  token/J-lens direction construction, with project-owned token bundles and
  graders remaining outside the submodule.

- 2026-07-08T16:15:00Z - FIT calibration completed and selected J-token dose
  5.0. At dose 5, hs23 `c_hat_plus_j_token` reached 119/124 = 96.0% FIT confab
  clean_tighten versus 118/124 = 95.2% for `c_hat_only`, with the same
  known-correct cost (3/172) and no malformed / forced / non-target-language
  rows. Doses 25/40/60 were rejected by the fit-only selector because the
  token-target write collapsed into malformed output despite accurate readback.
  This freezes the held-out dose but weakens the prior: FIT does not support
  the strong >=4pp hybrid-improvement prediction.

- 2026-07-08T15:20:00Z - Genericization boundary recorded while FIT calibration
  continued. The privacy/resume piece is generic and has already been promoted
  into Synaptic Tuner via `execution.redact_fields` plus fsync checkpoint writes.
  The remaining scalable interface is compound multi-readout steering: one arm
  should be able to declare several writes (`c_hat`, token-target, random
  control, etc.) in a single generation pass with per-write readback. Token/J-lens
  bundles, private row splits, gates, renderers, and graders should remain
  project plug-ins. The local no-op seeding optimization is deliberately not yet
  generic because it is valid only for deterministic greedy generation and rows
  proven inactive under the gate.

- 2026-07-08T14:20:00Z - Future-run hygiene while FIT calibration was
  checkpointing. The first calibration process was interrupted after 614 row
  records so the optimized runner could take effect. Added a shared
  `fit_baseline_c_hat_only_hs23` baseline mode that seeds from legacy per-dose
  `c_hat_only_hs23` records on resume and stops re-generating the same baseline
  arm for every J-token dose. Also added checkpoint-boundary sanitization for
  prompt/question/alias/raw-output/decoded-answer fields and rewrote the local
  private smoke/FIT JSONL checkpoints to remove prior `answer_value` fields.
  Row counts and aggregate metrics are unchanged; public outputs remain
  aggregate-only. Scalable follow-through: patched the generic Synaptic Tuner
  `mechinterp steer` and `mechinterp dose-calibrate` configs with opt-in
  `execution.redact_fields` plus fsync-backed per-row writes, so future
  restricted-row cells do not need to reimplement this sanitizer.

- 2026-07-08T14:45:00Z - Added gate-inactive no-op reuse to the project runner.
  About 59% of FIT rows are `fire=false` at hs23; for those rows all arms/doses
  run in off mode under greedy decoding, so the generated outcome is
  deterministic and arm-independent. The runner now seeds missing same-layer
  `fire=false` records from any existing no-op record, rewrites only
  mode/arm/write metadata, clears readbacks, and never copies fired rows. This
  keeps calibration semantics unchanged while avoiding thousands of duplicate
  no-op generations.

- 2026-07-08T13:15:00Z - Token-bundle research pass. KG search anchored the
  design in the resolved J-space localization/layer-contrast docs and the
  Transformer Circuits workspace note. The key selection rule is now explicit:
  the held-out primary bundle targets concrete refusal surface pieces and
  suppresses answer/reply continuations. Per user direction, semantically dense
  abstract labels (` doubt`, ` caution`, ` uncertain`, ` unsure`) and
  multilingual compact-token variants are deferred to a separate experiment so
  this first causal run stays single-factor. Added `token_bundle.yaml` and
  `token_bundle_audit.py`; the audit checks Qwen tokenizer IDs and whether
  tokens appeared in the committed H1 top-15 readouts.

- 2026-07-08T13:35:00Z - Added `run_token_target.py`, a local project runner
  for the first natural-token option-2 test. It builds hs23/hs29 token-target
  directions from FIT-only prompt gradients, writes private row-level JSONL
  checkpoints with `fsync`, calibrates the J-token dose on FIT rows, and keeps
  held-out/full outputs aggregate-only under `analysis-committed/`.

- 2026-07-08T12:25:00Z - Drafted from the post-layer-contrast brainstorm.
  Scope is option 2 only: internal J-lens token-target hidden-state writing,
  not an external decode-time logit bias. The amendment is intentionally not
  signed because the runner must first be implemented with row-level
  checkpoint/resume semantics, frozen token bundles, and FIT-only dose
  calibration.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 8 files / ~356 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-j-space-token-targeted-refusal-qwen3-4b` (dataset)
- HF revision: `74bf85613649a5ec722eceade197287115323d0c`
