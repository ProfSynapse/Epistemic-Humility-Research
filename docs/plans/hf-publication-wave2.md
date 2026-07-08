# HF Publication — Wave 2 plan (data, weights, and doc pointers)

**Status:** PROPOSAL (2026-07-02). Captured from a user request during the
Amendment Y cloud launch session ("what data/weights should we be tossing up
there so other people can access/analyze it, and how do we update our
reference docs/readme to point people toward the actual datasets").
Nothing here is uploaded until the per-artifact gates in
`docs/public-artifacts.md` and
`.skills/experiment-runner/reference/hf-publication.md` pass. That manifest
stays the SSOT; this plan feeds it.

## Already public (baseline)

| Repo | Contents |
|---|---|
| `professorsynapse/epistemic-humility-phase1` | Qwen3-4B train/dev JSONLs, build manifest, frozen questions |
| `professorsynapse/epistemic-humility-phase1-evals` | compact eval analysis layer |
| `professorsynapse/epistemic-humility-phase1-labels` | frozen split + probe manifest + sensitivity grid |
| `professorsynapse/epistemic-humility-cloud-results` | NEW (2026-07-02): per-cell result JSONs + manifests from the cloud lane (Y cells landing now). **Needs a README card** — it is live and bare. |

## Hard excludes (never publish — restated so wave 2 inherits them)

- `experiment/phase1/data/bridge_llama2_7b_chat/` (DO-NOT-REDISTRIBUTE).
- OpenMOSS / Cheng IDK raw rows (authorized for our use, not redistribution).
- `library/fulltext/`, `library/pdfs/` (copyright).
- Any base-model weights themselves (gated/vendor licenses); we publish
  LoRA deltas and derived artifacts only.

## Wave 2 candidates, ordered by value-per-effort

### 2a. README card for the cloud-results repo (do first; no gate needed)

Schema of a cell folder (result.json + manifest.json), provenance convention
(pinned repo commit inside each manifest), pointer back to the amendment doc
per run-tag prefix (y-*, smoke-*). Effort: one card.

### 2b. Probe directions (tiny, high leverage for steering/replication work)

The unit-normed gate/dial directions per family (Amendment AA fits, seed
20260630) + fit metadata (layer, AUROC, config sha). Currently gitignored by
design. One small dataset repo: `professorsynapse/eh-probe-directions`.
Lets anyone replicate the two-signal readout or steering without any
extraction pass. License: derived weights-of-a-linear-probe over our own
activations — no upstream restriction.

### 2c. Extraction row surfaces (the "fit your own probe" layer)

`rows.jsonl` per extraction (question, label, model answer, grade, config
sha — NO hidden states): ~5 MB each across S/T/U/W/X/Z/SR + Y cells.
One dataset repo `professorsynapse/eh-readout-rows` with one folder per
extraction, mirroring the local gitignored dirs. License pass per source:
PopQA (MIT) and TriviaQA (Apache-2.0) questions redistributable; SelfAware
already tracked publicly in-repo; model outputs fine for Qwen/Apache and
covered for Llama/Gemma under their output terms. EXCLUDE any Cheng-derived
rows. Value: reviewers can audit grading; others can study answer behavior
without GPUs.

### 2d. Hidden-state tensors (the full no-GPU reproducibility layer)

The `__pre/__post` safetensors per row (~2 GB per model). Start with the
four Amendment-Z families + the Qwen3-4B S/T/U/W set; one dataset repo per
family (`professorsynapse/eh-hidden-states-<family>`). This is the artifact
that lets anyone train probes/readouts from scratch on our exact surfaces.
Note: the in-flight Y cloud cells DISCARD extraction dirs by design
(upload-only-results); if Y hidden states should be public, that is a knob
to flip in `hf_jobs_cell.sh` for FUTURE cells (upload the extraction dir to
a bucket/dataset), not a re-run of this batch.

### 2e. Trained LoRA adapters (the gated wave — publication gate applies)

Per `docs/public-artifacts.md` policy: LoRA-only, one repo per evaluated
adapter, lowercase queryable names, `training_lineage.json`, exact eval
result recorded. Priority order by reuse value:

1. `eh-qwen3-4b-clean-sft-seed1-lora` (the clean-SFT anchor used by probes)
2. `eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` (the deployed two-signal
   checkpoint behind Amendments T/U and the AA follow-up plan)
3. The 9 headline cells (3 arms x 3 seeds) — the paper's confirmatory grid
4. GRPO-v3 / aux-head arms as diagnostic releases (clearly labeled)

Qwen3-4B base is Apache-2.0, so LoRA redistribution is clean. Llama-2
bridge adapters stay held (gated base license) unless separately cleared.
Gate work per adapter: run-record freshness + eval-on-exact-artifact
reconciliation against `archive/papers/retired/results-provenance-inventory.md`.

### 2f. HF Collection + doc pointers (after 2a–2c exist)

- Create one HF **Collection** ("Epistemic Humility Research") grouping all
  repos so a single link serves papers/README.
- README.md: add an **Artifacts & Data** section — table of HF repos with
  one-line contents, the collection link, and a pointer to
  `docs/public-artifacts.md` for provenance discipline.
- Each paper draft's reproducibility frontmatter: add the HF collection and
  per-claim repo pointers once revision SHAs are recorded.
- `docs/public-artifacts.md`: move each shipped item from Pending to
  Published with its revision SHA (existing convention).
- Dataset cards: every repo README carries schema, provenance (repo commit,
  run record / amendment doc path), license notes, citation stub.

## Suggested sequencing

1. **Now (free, no gate):** 2a cloud-results card; draft 2f README section.
2. **Next session:** 2b directions + 2c rows after the per-source license
   pass; record revisions in the manifest.
3. **Overnight upload:** 2d hidden-state repos (Z families first).
4. **Behind provenance reconciliation:** 2e adapter wave, in priority order.
5. **Close:** 2f collection + README/paper pointers, manifest updated.

Uploads use the tuner `upload-deployment` workflow for model artifacts and
plain `huggingface_hub` uploads for dataset repos; every upload records its
HF revision SHA in `docs/public-artifacts.md` (existing rule).
