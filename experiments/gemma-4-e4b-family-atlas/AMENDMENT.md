# gemma-4-e4b-family-atlas

Status: draft (not signed; do not launch as confirmatory evidence). Lead
signs; this document is prepared for lead review, not self-signed.

Keep this document the prose home for the experiment. The machine state lives
in `experiment.yaml` and is never duplicated here.

## Motivation and posture

Google/gemma-4-E4B-it is a new family entering the program (a
MatFormer/per-layer-embedding "elastic" architecture, distinct from every
prior atlased family). Per `.skills/family-atlas/SKILL.md`, no per-family
actuation cell should be designed against a ported layer from another
family; this atlas is the prerequisite read-only mapping instrument. This is
a READ-ONLY mapping experiment: no steering, no interventions, no behavioral
outcomes. Posture: exploratory instrument-building evidence, never pooled
with a confirmatory headline matrix.

This is the third registered family-atlas cell (after `jspace-family-atlas`'s
llama32_3b_instruct and mistral7b_instruct_v03). It has one structural
difference from both: **no reusable committed split manifest exists for this
substrate.**

## Design

Substrate: `google/gemma-4-E4B-it` at pinned revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`, 42 hidden layers (text backbone;
`Gemma4ForConditionalGeneration` is a multimodal wrapper with additional
vision/audio towers this atlas does not touch), hidden size 2560, vocab
262144, tied embeddings. n_hidden_states for full-depth capture = 43.

**Pin provenance**: `experiments/doubt-snap-cross-family-confirmatory/model_matrix.yaml:68-74`
(`cell_id: gemma4_e4b_it`, `gated_access: false`, `panel_role:
direct_Z_panel_match`). Independently corroborated by
`papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_z_gemma-4-e4b_result.json`,
which used the same `base_model: "google/gemma-4-E4B-it"` for the two-signal
readout paper's cross-size panel (that artifact does not itself carry a
revision hash, so it corroborates the repo identity, not the exact pin).
Correction to the task brief that named this pin: the lead's message
attributed this substrate to "the rr-cross-family-raw-refusal records";
`rr-cross-family-raw-refusal` (`experiments/rr-cross-family-raw-refusal/`) is
llama + mistral only and never touched Gemma. The correct prior source for
this pin is `doubt-snap-cross-family-confirmatory`'s model matrix, not
`rr-cross-family-raw-refusal`.

**Row pool (the load-bearing design decision for this cell)**: no existing
experiment has a committed split manifest for `google/gemma-4-E4B-it` under
the family-atlas role/split taxonomy (`confab` / `known_correct_answered` /
`unknown_refused`, split labels `fit` / `held_out` / `fit_only`).
`doubt-snap-cross-family-confirmatory/model_matrix.yaml` DOES define a
`gemma4_e4b_it` cell at this exact pin, but its own `AMENDMENT.md` (lines
283-284) states plainly: "`gemma4_e4b` (small tier) and the remaining
mid-tier cells were never launched (fleet abandoned pre-launch)." Two other
artifact families reference `google/gemma-4-E4B-it`
(`experiments/sampled-decode-seed-robustness/` and the archive
"Amendment Z" lineage under `papers/paper-4-two-signal-readout/`), but both
use a DIFFERENT row-role taxonomy (`correct` / `wrong` / `hallucination` /
`known_answered`, from the archive `cross_size_training_free_two_signal`
dial-calibration lineage), which the skill's own guidance says needs a
mapping layer before this instrument can read it -- not a straight reuse.

Per `SKILL.md` step 2's fallback clause ("Only mine a fresh pool if none
exists ... mine it per the program's standard roles"), this cell MINES a
fresh pool rather than inventing a new taxonomy or a mapping layer, and does
so by resuming the fleet's own already-defined, never-launched
`gemma4_e4b_it` cell through its own generic prep script:

```
python experiments/doubt-snap-cross-family-confirmatory/prep_tuner_cell.py \
    prepare --cell-id gemma4_e4b_it --batch-size <TBD from smoke>
```

`prep_tuner_cell.py:prepare()` (`cell_by_id`, `build_candidate_pool`,
`run_baseline`, `stratified_split`, `assign_roles`) is written generically
per `cell_id`; it already reads `gemma4_e4b_it` correctly out of the fleet's
`model_matrix.yaml`, and `model_shape()` already resolves the nested
`text_config` a multimodal `AutoConfig` returns, so no code change is needed
to point it at this substrate. Running it will additionally emit a
single-layer (hs_index 40, the fleet's ported 0.94-depth layer) capture +
gate-fit as a side effect of that script's own G0 prep pipeline; this atlas
does not consume that side-effect output, only the mined
`split_rows_private.jsonl` / `split_manifest.json`.

**This mining run is real GPU generation** (baseline decode, up to
`DEFAULT_MAX_ANSWERABLE=1600` + `DEFAULT_MAX_UNANSWERABLE=2400` = 4000
candidate rows, 200 max_new_tokens, greedy, batched) -- it is NOT the
capture-only, "under $2" cost profile SKILL.md's Gotchas section describes
for cells that already have a pool. It is scoped and gated separately below
(AG0a) from the atlas's own full-depth capture (AG0/AG1/AG2), and both stages
require explicit launch approval before running on GPU.

Signal, per cell, once the pool exists (identical procedure to
`jspace-family-atlas`):

1. Full-depth anchor capture: hidden states at every decoder layer (0
   through 42) at the final-prompt-token anchor, for every row in the
   mined split manifest. FIT/held-out labels carried through unchanged.
2. Workspace profile: per-layer effective-dimension fraction (eff_dim_frac),
   the participation-ratio formula applied to the FIT-row anchor
   hidden-state matrix at each layer. Representation-variance PR, not
   comparable to a JVP-based profile from a different instrument;
   comparable across this atlas's own cells only.
3. Per-layer read panel with bootstrap CIs, for doubt / caution /
   raw_refusal, plus the standard random-direction control. `unknown_refused`
   is expected to be `fit_only` (no held-out partition) exactly as in both
   jspace-family-atlas cells; the deterministic `refused_fit`/`refused_eval`
   subdivision (seed 20260707, `profile_and_read_family_atlas_panel.py`'s
   `split_refused_pool()`) applies unchanged.
4. Committed outputs (aggregates and fitted metadata only, never row text):
   per-layer profile table, per-layer read AUROCs with CIs, the
   random-direction control, direction-fit manifests with seeds and sha256s,
   and the atlas summary JSON.

Execution: local RTX 3090 (pre-approved lane; no cloud/Modal without fresh
approval). Two GPU stages, each gated and launch-approved separately:
(a) pool mining via the fleet's `prep_tuner_cell.py prepare`, (b) this
atlas's own full-depth capture + CPU-only profile/read-panel scoring.
Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`render_gemma_atlas.py` (this experiment's own capture render module, ported
from `doubt-snap-cross-family-confirmatory/render.py`), and local,
byte-identical copies of the shared `capture_family_atlas_cell.py` and
`profile_and_read_family_atlas_panel.py` (sha256-verified against their
`.skills/family-atlas/scripts/` canonical originals). Copied rather than
referenced in place: both scripts compute `ROOT = Path(__file__).resolve().parent`
and derive `REPO_ROOT` / `private_dir()` / `committed_dir()` assuming the
copy-into-`experiments/<slug>/` placement their own docstrings state; run in
place from three levels below the repo root, `REPO_ROOT` resolves to
`.skills/` instead of the repo root and both scripts' private/committed
output dirs land inside `.skills/family-atlas/` instead of under this
experiment. Verified directly (`Path.parents` resolution test) before
copying; no prior atlas cell exercised this shared-script path (all four
prior/pending cells used bespoke per-experiment copies), so this is a
previously-latent gap in the shared skill infrastructure, not a design
choice for this cell. Flagged to the lead as a possible `.skills/family-atlas/`
documentation/implementation fix; not corrected upstream here.

## Cost and sizing (pre-sign probe evidence)

Pre-sign timed generation probe (lead-authorized, notebook-tier, sizing
evidence only -- not evidence rows, nothing from it is consumed downstream),
run inside the pinned `mechinterp-runner:local` image
(`sha256:d445632098cd2c70c115fe84d5343ff98286ac3f510a2d4c9cb488b550a3d23c`) on
the local RTX 3090, using synthetic placeholder questions (never real
KUQ/TriviaQA/PopQA text), the fleet's own baseline system prompt, and the
same `AutoModelForCausalLM` + explicit `.to("cuda:0")` loading pattern
`synaptic-tuner/tuner/batch/engines/hf_batched.py` actually uses (no
`device_map=`; the pinned image lacks `accelerate`, confirmed by a first
attempt that raised `ValueError: ... requires accelerate` -- the real mining
pipeline never hits this since it already avoids `device_map=`).

| | load | batch 8 (128 rows, 200 max_new_tokens, greedy) | batch 16 (128 rows) |
|---|---|---|---|
| wall-clock | 285.5s | 58.80s | 39.36s |
| tokens/s | -- | 70.75 | 105.76 |
| rows/s | -- | 2.177 | 3.252 |
| peak VRAM allocated | -- | 15.02 GB | 15.22 GB |

VRAM headroom at batch 8 on the 3090's 24 GB: ~8.98 GB, above the lead's
~6 GB threshold for also timing batch 16 -- batch 16 was in fact run (see
process note below) and its own peak VRAM (15.22 GB) confirms ~8.78 GB of
headroom remains even there. **Batch-size recommendation: 16** (46% higher
rows/s than batch 8 for +0.2 GB peak VRAM, comfortable margin under the
3090's 24 GB either way).

Process note (transparency): this probe ran both batch sizes unconditionally
in one script pass rather than gating the batch-16 timing on a first
foreground check of the batch-8 headroom, as the lead's instruction literally
sequenced it ("if VRAM headroom exceeds ~6GB at batch 8, also time batch
16"). The retroactive headroom check above confirms batch 16 was justified,
but the gate was checked after the fact, not before launching it. Flagged
here rather than silently presented as if the literal sequencing were
followed.

Projected full pool-mining wall-clock (stage (a), `prep_tuner_cell.py
prepare`, generation over up to `DEFAULT_MAX_ANSWERABLE=1600` +
`DEFAULT_MAX_UNANSWERABLE=2400` = 4000 candidate rows at batch 16): load
285.5s (one-time) + 4000 rows / 3.252 rows/s ~= 1230s generation ~= **~25.3
minutes total**. This exceeds the 15-minute short-run ceiling, confirming
the `incremental` persistence classification declared in `experiment.yaml`
(satisfied at the tuner layer by `batch-generate --resume`'s checkpoint.json,
not by this script itself). Stage (b)'s own capture (single forward pass per
row at the anchor position, ~3500 rows, no autoregressive generation) is
proportionally far cheaper per row than this generation-heavy mining stage
but was not separately timed by this probe; also declared `incremental`
regardless (satisfied the same way by `batch-capture --resume`).

## Prediction

Gemma-4-E4B-it shows an interior workspace band: a contiguous set of layers
strictly inside (20%, 85%) depth where eff_dim_frac peaks AND all three read
axes (doubt, caution, raw refusal) hold held-out AUROC >= 0.80, with the
band's peak layer differing from the fleet's ported 0.94-depth layer
(hs_index 40, i.e. block 39).

## Falsifier

No interior eff_dim_frac peak exists (the profile is monotone to the last
layer, OR the profile peaks in the outer 20% of depth on either end --
early-exterior, as `jspace-family-atlas` found for BOTH llama and mistral, or
late-exterior), OR no layer inside (20%, 85%) depth reaches held-out AUROC
>= 0.80 on all three axes simultaneously.

## Gates

See `gates.yaml`: AG0a (pool-mining integrity, this cell only), AG0
(capture/direction integrity), AG1 (profile), AG2 (read panel). Transcribed
verbatim; do not retune without a signed revision.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Falsifier fires on the profile limb: eff_dim_frac peaks early-exterior (outer 20% of depth), matching what jspace-family-atlas found for both llama and mistral, so no interior workspace band is declared. Read panel still healthy: at least one mid-depth layer holds held-out AUROC >= 0.80 on all three axes, but not coinciding with an interior eff_dim_frac peak. Ported 0.94-depth layer (hs_index 40) reads well on raw_refusal, weaker on doubt. (recorded pre-run, before any capture) |
| user | Approved the atlas arc 2026-07-20 ("get gemma going"); no separate quantitative call recorded. |

## Outcome

Filled at resolve. Record the verdict, the gate results (AG0a/AG0/AG1/AG2),
and the one-sentence summary that also goes into `verdict:` in the manifest.
Append this cell's row to `docs/atlas/family-layer-map.md` once resolved --
never add a registry row before this doc is signed and resolved.
