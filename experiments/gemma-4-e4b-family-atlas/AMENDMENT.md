# gemma-4-e4b-family-atlas

Status: signed 2026-07-20 (machine state in `experiment.yaml`); signed
revision 1 recorded 2026-07-20 (AG0a mining instrument re-specification,
see that section). This header was stale boilerplate reading "draft" until
2026-07-20; corrected to match the machine state, which was already
`signed`.

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

## Signed revision 1 (2026-07-20): AG0a mining instrument re-specification

Recorded after AG0a v1 failed and before any atlas capture stage ran. User
approval: the PI selected "Revise + re-mine" (2026-07-20) from the three
options presented (revise and re-mine; re-mine with the gate unchanged; halt
the cell).

What happened. Pool mining (fleet `prep_tuner_cell.py prepare --cell-id
gemma4_e4b_it`, external pin unchanged) completed generation (4000 rows) and
anchor capture (2819 rows across two runs; run 1 died at 576/2819 on a
transient CUDA "unknown error" with the GPU healthy afterward, run 2 resumed
from tuner checkpoints and completed), then exited 3. Its
`g0_prep_summary.json`: held_out_power true (confab held-out 1265 >= 150,
known_correct 253 >= 250), gate_auc_on_fit 0.9507 (pass),
directions_byte_identical true, generation_terminates_rate 0.8020 (FAIL vs
0.90), batched_parity_smoke FAIL (2 of 8 smoke rows). AG0a v1
`mining_completed` therefore FAILED; `role_pool_adequacy` PASSED.

Diagnosis. Both failing checks are instrument-model fit, not pool defects.
(1) The 200-token generation cap is hardcoded in the fleet script and was
calibrated on Qwen-family cells; Gemma-4-E4B-it is more verbose, so 572 of
4000 generations (14.3%) hit the cap. Among naturally terminated rows the
length p99 is roughly 250 tokens, so a 400-token cap is expected to clear
the unchanged 0.90 threshold honestly. (2) The parity smoke compares the
parsed answer field by exact string equality plus finish_reason equality.
On paragraph-length free-text answers this is brittle under
batched-vs-sequential numeric divergence: both mismatched rows agree on
answer prefix and content and diverge mid-generation (one also flips eos to
length at the 200 cap). The atlas consumes role labels, not generation
strings, so role-relevant grade agreement is the integrity property that
matters here.

Change. The mining module becomes a local pinned copy,
`prep_tuner_cell_gemma.py`, derived from the fleet script at its pinned sha
with exactly four documented hunks: (a) ROOT re-pointed to the fleet
experiment directory so data paths, imports, the model registry, and the
analysis output location resolve unchanged; (b) baseline generation cap
200 to 400; (c) parity-smoke sequential re-decode cap 200 to 400; (d) the
parity comparator replaced by role-relevant grade agreement: for all 8
smoke rows the sequential re-decode must receive the same role-determining
grades (semantic verdict, clean flag under its own finish reason, refusal
classification) as the batched baseline. `gates.yaml` AG0a is revised to
v2 naming this module and comparator. Unchanged: the 0.90 termination
threshold, the role floors, AG0/AG1/AG2, and the prediction/falsifier.
All cap-200 mining artifacts (generation, grading, capture, split manifest)
are archived under the cell's private analysis directory and none are used
for the atlas; mining reruns from scratch at the 400-token cap, and the
anchor capture reruns against the new split manifest.

## Signed revision 2 (2026-07-21): AG0a termination limb re-specified to answer-capture

Recorded after AG0a v2 failed on its termination limb alone and before any
atlas capture stage ran. User approval: the PI selected "Revision 2:
answer-capture check" (2026-07-20 EDT) from three options (re-specify with
red-team review first; re-mine at an 800-token cap; stop the cell). An
adversarial red-team review ran BEFORE this signing and returned
SIGN-WITH-CONSTRAINTS; all five of its constraints are incorporated below,
including two corrections to the lead's original proposal rationale.

What happened. Run 3 (400-token cap, pinned copy per signed revision 1)
passed four of five limbs: held_out_power (known-correct held-out 251 vs
floor 250, confab 1263), gate AUC 0.9472, directions byte-identical, and
the parity smoke PASSED under the role-relevant-grade comparator. The
termination limb failed again: EOS-emission 0.8849 on split rows vs 0.90
(0.802 at the 200 cap). Row-level diagnosis: 337/4000 generations
truncated, 96.7% concentrated in kuq_unknowns_all, 1.8% loop-like; 136/337
(40.4%) contain a complete well-formed first-JSON answer, the truncation
landing only in post-answer prose Gemma appends without emitting EOS.

Change. The termination limb becomes ANSWER-CAPTURE: a split row is
captured iff finish_reason != "length", OR its clean grading shows a
complete well-formed first-JSON answer and the row is not degenerate.
Threshold unchanged at 0.90, computed on split rows. The gate number for
run 3 under this definition, independently computed by the red-team on the
exact split-row population, is 0.9286 (2614/2815); the all-rows figure
(0.9497) is not the gate number. The raw EOS-emission rate remains in
g0_prep_summary.json as a committed descriptive field. Implemented as a
fifth documented hunk in prep_tuner_cell_gemma.py; evaluation is offline
from run-3 artifacts (tuner checkpoints make every GPU stage a resume
no-op); no new GPU work.

Corrections adopted from the red-team (both were defects in the lead's
proposal rationale, disclosed here rather than repaired silently):
1. It is NOT true that grading consumes only the first JSON object. The
   role grader (grade_one) reads the whole completion text, so trailing
   prose can reach role labels: 3 of the 123 captured-via-well-formed split
   rows take their refusal label from trailing prose, and 22/2815 split
   rows (0.78%) disagree between whole-text and first-JSON refusal reads.
   The re-specification is therefore justified on grading-relevant
   COMPLETENESS (the answer object is fully present), not on prose
   isolation. This behavior is identical under the old and new limb; the
   limb never gates row admission.
2. The 201 mid-answer-truncated rows are NOT excluded by grading. They are
   graded confab from incomplete text and 124 sit in the held-out confab
   set. This is accepted as a known pool property: non-termination
   correlates with the confab role (captured-via-EOS kuq rows grade 86%
   confab / 14% refused; captured-via-well-formed 97.5% / 2.5%; uncaptured
   100% confab), intrinsic to the pool and unchanged by this revision. The
   anchor is captured at the final prompt token, so hidden states never
   depend on completion text; only role labels do. Held-out floors carry
   the attrition risk: removing every truncated held-out confab row would
   still leave 1069 vs the 150 floor, and the known-correct held-out margin
   (251 vs 250) contains zero truncated rows.

Scope and stopping rule (red-team constraint 5). AG0a is an
instrument-adequacy go/no-go; its verdict is never reported as a finding.
A THIRD re-specification of the termination limb is not permitted: if the
limb fails again in any future run of this cell, the cell resolves as "the
fleet mining instrument cannot cleanly mine this family" rather than
redefining the check again.

Unchanged: the 0.90 threshold, all other AG0a limbs, AG0/AG1/AG2, the role
floors, and the prediction/falsifier.

## Outcome

Resolved 2026-07-20 (lead adjudication; all numbers re-derived by the lead
directly from `analysis-committed/gemma4_e4b_it/atlas_summary.json`, not
relayed from the harness report).

**Verdict (one line, mirrored in `experiment.yaml verdict:`)**: falsifier
fired on the profile limb: eff_dim_frac peaks early-exterior at hs_index 4
(0.0189, 0.095 depth), no interior workspace band declared; read panel
healthy with a contiguous all-three-axes >= 0.80 band at hs_index 13-42.
Gemma-4-E4B-it is the third family (after llama and mistral,
`experiments/jspace-family-atlas`) showing an early-exterior profile peak
decoupled from a healthy mid-band read panel.

### Gate results

- **AG0a (pool-mining integrity, v3 per signed revisions 1-2)**: PASS on
  all five limbs (answer-capture 0.9285968 on split rows vs 0.90; AUC
  0.9472; directions byte-identical; parity smoke passed; held-out floors
  known-correct 251 vs 250, confab 1263 vs 150). Instrument-adequacy
  go/no-go only; per signed revision 2 this is not a finding and is not
  reported as one.
- **AG0 (integrity)**: PASS 3/3. capture_coverage 1.0 (2815/2815 rows, no
  attrition at any layer) vs 0.95 floor; direction refits byte-identical
  (np.array_equal exact, 9/9 layer-axis combinations at hs 4/13/40);
  held-out power survives attrition trivially (zero attrition; confab 1263
  vs 150, known-correct 251 vs 250).
- **AG1 (profile)**: PASS 2/2. eff_dim_frac computed at all 43 hs indices
  (0-42); 20% fit-row subsample reproduces the peak exactly (hs 4 vs hs 4,
  delta 0 vs +/-1 tolerance).
- **AG2 (read panel)**: reported per gate design (no numeric threshold;
  bootstrap CIs, 2000 resamples). Numbers below.

### Profile

Single maximum at hs_index 4: eff_dim_frac 0.018947, depth 4/42 = 0.095,
inside the outer-20% early-exterior region named by the falsifier. Steep
rise from hs 0 (0.00077), fall through hs 5-9, then a low flat 0.003-0.013
band through hs 42 with minor secondary bumps at hs 12 (0.0124) and hs 16
(0.0091), neither close to the peak. No interior peak exists; falsifier
limb 1 fires. Limb 2 does NOT fire: interior layers clear 0.80 on all
three axes (below).

### Read panel (held-out AUROC, 95% bootstrap CI)

- hs 4 (peak): doubt 0.9885 [0.9809, 0.9941]; caution 0.8347 [0.7981,
  0.8711]; raw_refusal 0.8005 [0.7648, 0.8358].
- hs 13 (band opener): doubt 0.9978 [0.9950, 0.9997]; caution 0.8816
  [0.8490, 0.9125]; raw_refusal 0.8049 [0.7708, 0.8353].
- hs 40 (fleet's ported 0.94-depth layer): doubt 0.9949 [0.9896, 0.9986];
  caution 0.9223 [0.8942, 0.9468]; raw_refusal 0.9272 [0.9012, 0.9496].

Band structure (lead re-derivation; corrects one sentence in the harness
report, which stated hs 13 is the first layer clearing 0.80 on all three
axes): hs 4-6 also clear it marginally (raw_refusal 0.8005/0.8087/0.8015),
then raw_refusal dips below 0.80 across hs 7-12 (0.759-0.787), and the
CONTIGUOUS band runs hs 13-42. hs 13 (0.31 depth) through hs 35 (0.83
depth) of that band sit strictly inside the (20%, 85%) interior region.
raw_refusal is the binding axis everywhere; doubt is the strongest axis at
every reported layer.

Random-direction control (lead re-derivation over all 43 layers, not just
the two layers the harness quoted): near chance at hs 0-8 (max 0.62), hs
14-18 (0.57-0.63), hs 36-40 (0.59-0.64), but ELEVATED and spiky across much
of the mid-band -- max-over-contrasts 0.83-0.87 at hs 10-12, 0.97 at hs 24,
0.85-0.94 at hs 28-34, 0.89 at hs 42. This is the same norm/position
confound family jspace-family-atlas documented for llama/mistral doubt,
here layer-patchy rather than doubt-specific. Consequence: the naive
best-per-axis layers (doubt 1.00 at hs 21, caution 0.9305 at hs 25,
raw_refusal 0.9345 at hs 26) all sit where the random baseline is 0.80-0.97
and are NOT clean reads. The cleanest strong-reading layers are the ones
where the control is near chance AND all three axes clear 0.80: hs 14-18
(axes ~0.998 / 0.88-0.89 / 0.81-0.84 vs control <= 0.63) and hs 36-40 (at
hs 40: 0.9949 / 0.9223 / 0.9272 vs control 0.592). At hs 4 and hs 40
specifically the control is 0.556 and 0.592, so the headline read-panel
numbers quoted above stand against a near-chance baseline. The gate verdict
is unaffected (neither falsifier limb references the control), but any
downstream per-family actuation work should pick its layer from the
clean-control set, not the raw best-AUROC set.

### Prediction scoreboard adjudication

Orchestrator's recorded call: headline CORRECT on both clauses (falsifier
fires early-exterior on the profile limb, matching llama/mistral; read
panel healthy at mid-depth without an interior eff_dim_frac peak). The
descriptive sub-clause on hs 40 ("reads well on raw_refusal, weaker on
doubt") is WRONG: doubt is the strongest axis at hs 40 (0.9949 vs
raw_refusal 0.9272). User recorded design approval only, no quantitative
call. Proposed score, subject to PI confirmation at PR review: orchestrator
WIN (headline exactly right, sub-clause miss disclosed), no user-side score,
tally moves to user 3 - orchestrator 5 - ties 2.

### Notes

- Gate-evidence aggregates (`ag0_direction_refit_determinism.json`,
  `ag1_subsample_reproducibility.json`) are committed under
  `gate-evidence/` at this experiment's root rather than
  `analysis-committed/`, because the container wrote `analysis-committed/`
  root-owned and neither the harness nor the lead can write inside it
  without privilege escalation. Contents are aggregates only (booleans and
  per-layer floats), containment-unchanged.
- Exhaust staged at `/home/profsynapse/code/ehr-exhaust/gemma-4-e4b-family-atlas/`
  (1.2G), `atlas_summary.json` sha256-verified against source
  (3374521c60cfc898485ed1839507f925e517a67ff8313cf04d78db4c45764560).
  Packaging waits for the data-exhaust gate; nothing uploaded.
- Registry row appended to `docs/atlas/family-layer-map.md` in this same
  branch, per the rule that a row lands only at resolve.
