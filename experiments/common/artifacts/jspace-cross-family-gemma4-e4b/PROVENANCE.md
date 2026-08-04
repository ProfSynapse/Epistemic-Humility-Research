# J-Space Cross-Family — gemma4-e4b Pool, Split, and Frozen Directions

This directory promotes `google/gemma-4-E4B-it`'s committed-class artifacts from
`experiments/j-space-cross-family-layer-contrast/analysis-committed/gemma4-e4b/`
for reuse by downstream experiments.

Promoted for:

- `experiments/gemma4-e4b-kv-seam-quarantine` (second consumer; the promotion
  rule's trigger — see that experiment's `AMENDMENT.md` "Open questions at
  sign" #1, resolved by the lead 2026-07-25 in favour of promotion)

## Why this directory exists at all

These files were produced by the parent but were **never committed with it**.
PR #336 merged `j-space-cross-family-layer-contrast` carrying
`analysis-committed/` for `llama-3.2-3b`, `mistral-7b-v03`, and `qwen35-4b`
only; the `gemma4-e4b` directory remained untracked in a single working
directory. Promotion here is therefore also the first time gemma's artifacts
enter version control at all.

## Contents

Row manifests (ID-only):

- `split_manifest.json` — 730 rows: `row_key`, `role`, `category_canon`,
  `split`. FIT_FRAC = 0.40.
- `eval_pool_manifest.json` — 806 rows: `row_key`, `role`, `source`,
  `category_canon`.

Fitted readout/write artifacts (mid-band candidates hs34/hs38/hs42):

- `build_manifest_layers.json` — per-layer standardization
  (`mu_d`/`sigma_d`/`mu_c`/`sigma_c`) and fit counts.
- `gate_fit_layers.json` — per-layer `tau_frozen`, FIT AUC, Youden stats.
- `dose_calibration_summary.json` — the R2 normalized-ratio dose ladder result.
- `layer_profile.json` — J-lens profile used for band selection.
- `layers/hs{34,38,42}/` — `u_d_*.json` (KU readout direction), `c_hat_*.json`
  (boundary-push write vector), and the `source_directions/` pos/neg controls
  they were orthogonalized against.

## Containment

Verified before promotion, not assumed:

- No question text, aliases, answers, generations, or any row-level eval text is
  stored here. Both row manifests carry identifiers and categorical labels only.
- The only free-text string in any file is a methodological note authored by the
  drafter in `dose_calibration_summary.json`
  (`late_reference_selected_dose.note`).
- Runtime materialization must join these IDs against private/local sources and
  keep the resulting row text under gitignored `analysis/`.
- The 341.7 MB `anchor_extract.safetensors` and `pool_generations.jsonl` are
  **not** promoted. They remain private under the producing experiment's
  gitignored `analysis/` and are consumed by symlink.

## A caution specific to these files

`build_manifest_layers.json`, `gate_fit_layers.json`, and
`dose_calibration_summary.json` use the same filenames a consuming experiment
writes its own roll-ups to. Consume them by **explicit path into this
directory** — do not symlink them into a consumer's `analysis-committed/<family>/`,
where a later run could write through the symlink and corrupt the shared copy.
The ID-only manifests and `layers/` are read-only in every consumer and are safe
to link.

## Origin

- Source experiment: `j-space-cross-family-layer-contrast`
- Source path:
  `experiments/j-space-cross-family-layer-contrast/analysis-committed/gemma4-e4b/`
- Origin amendment verdict: gemma4-e4b stopped at the registered G0
  dose-viability rule (NOT-RUN, excluded from the cross-family denominator).
- **Read the origin caveat before using the write-side artifacts.** The parent
  records at `AMENDMENT.md:637` that gemma's write arm was fit on activations
  corrupted by `use_cache=False`, which starves blocks 24–41 of their donor K/V.
  hs00–hs24 are bit-identical to a correct run; hs25 onward decay (cos 0.732 at
  hs25 to 0.075 at hs42). Every artifact here at hs34/hs38/hs42 is therefore
  **corrupt-derived and uninterpretable, not negative**. The ID-only row
  manifests are unaffected — the split is over row identity, not activations.

## sha256 (full digests via `sha256sum`; first 16 hex shown)

```
2f9d4352c0ef14d1  build_manifest_layers.json
06f9298c931e365b  dose_calibration_summary.json
35eb9ac02e7f7d63  eval_pool_manifest.json
dd10168c6fcf8b60  gate_fit_layers.json
7e1944c345a53729  layer_profile.json
3e7f265f9953e0bd  layers/hs34/c_hat_hs34.json
59b2567951ad24a7  layers/hs34/source_directions/neg_ctrl_hs34.json
2aae282bc5125c6c  layers/hs34/source_directions/pos_ctrl_hs34.json
c152e12f74727c5a  layers/hs34/u_d_hs34.json
ea02272275ee41a5  layers/hs38/c_hat_hs38.json
44c46f9f2a126053  layers/hs38/source_directions/neg_ctrl_hs38.json
d0523323d2102b8e  layers/hs38/source_directions/pos_ctrl_hs38.json
8f59c4ee920d8b9e  layers/hs38/u_d_hs38.json
13b2729fae433bd1  layers/hs42/c_hat_hs42.json
a4ba7d0a9e96d0aa  layers/hs42/source_directions/neg_ctrl_hs42.json
a91b4be1a2367e09  layers/hs42/source_directions/pos_ctrl_hs42.json
26de72598dfbe25f  layers/hs42/u_d_hs42.json
8d2281179ab865be  split_manifest.json
```

## Added 2026-07-29: arch_literature_memo.md

Promoted from the parent's private
`analysis/gemma4-e4b/arch_literature_memo.md` (lead, user-approved, alongside
the `gemma4-e4b-kv-seam-quarantine` inputs uncommenting). It is a registered
input of that experiment. Content class: architecture literature memo only
(published-source claims about the gemma-4 KV-sharing layout, each tagged with
its source); no row data, no question text, no aliases, no generations.
sha256-verified byte-identical to the parent worktree original at promotion:

```
5048ef02227fdda7  arch_literature_memo.md
```
