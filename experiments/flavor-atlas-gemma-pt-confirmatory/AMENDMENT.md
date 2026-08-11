# Second-substrate confirmatory: overt-unanswerability flavor separation on pretrain-only Gemma

Status: signed (machine state in `experiment.yaml`); not yet resolved --
the "Outcome" section below is correctly still a placeholder pending the
run. This header was stale boilerplate reading "draft (not signed); Lead
signs" until 2026-08-11; corrected to match the machine state, which was
already `signed`. GPU launch is separately gated and requires PI approval
AND the Qwen-side surface control
(`flavor-atlas-surface-control-confirmatory`) to have resolved first.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

- Slug: `flavor-atlas-gemma-pt-confirmatory`
- Type: probe-fit
- Tier: 3 (exploratory-confirmatory; nothing here pools with any headline
  matrix)
- Substrate: `google/gemma-4-E4B` pretrain-only base, no adapter, bf16,
  revision `411aa17b749aa952df1359d2dcea73917a544d9a` (resolved and pinned at
  signing prerequisite time via `HfApi().model_info`, no weight download; see
  NOTEBOOK.md).
- Companion cell: `flavor-atlas-surface-control-confirmatory` (the Qwen-side
  surface control). This cell and that one together are the promotion path.

## Motivation and posture

`flavor-atlas-rawbase` resolved as a mixed atlas on `unsloth/Qwen3-4B` raw
base: all six KUQ flavors separate from the KUQ known pool at held-out
out-of-fold AUROC 0.9800 to 0.9994 at their best layers, SelfAware reads
0.9937, every pair among those seven transfers at 0.8331 or better, and
AmbigQA is unreadable at all 37 layers (best 0.6590) with every probe into
it near chance. Its registered descriptive reading was that the pretrained
base carries a broad unanswerability code across overt flavors, and that the
operative boundary is overt versus covert unanswerability rather than flavor
versus flavor.

That reading is a one-substrate discovery. The program's promotion rule
requires a confirmatory replication registered before running, on fresh
seeds, a larger model, or held-out material. The Qwen-side surface control
removes one named alternative (linear prompt style) but adds no fresh
substrate. This cell supplies the fresh-substrate leg on a second family,
and carries the same surface-residualization readout as a built-in secondary
so that promotion does not need a third cell.

Posture: exploratory-confirmatory. It gates promotion of exactly two
clauses, which are adjudicated separately and can pass or fail
independently:

- Clause A, the broad-overt-code clause: a pretrained base carries a
  separable, freely transferring activation signature for all six overt KUQ
  flavors and for SelfAware.
- Clause B, the boundary clause: the operative boundary is overt versus
  covert unanswerability, evidenced by AmbigQA being unreadable at every
  depth while overt flavors read near ceiling.

Either clause may replicate without the other. Nothing here promotes a
claim about layer locations, which are family-relative by the program's own
standing finding and are never ported.

## Substrate choice and base form

The substrate is `google/gemma-4-E4B` in its PRETRAIN-ONLY (pt) form, not
the instruction-tuned `google/gemma-4-E4B-it` sibling that
`experiments/gemma-4-e4b-family-atlas` used. The family atlas chose the
instruct sibling because its question was where an instruction-tuned model's
read band sits; our clause is about what PRETRAINING leaves behind, so an
instruction-tuned checkpoint is the wrong base form. Base form parity with
the Qwen cell, which used a raw pretrained base with no adapter, is the
property that makes this a replication rather than a new question.

The program already has the pt sibling on record.
`experiments/pretrain-only-base-readout/AMENDMENT.md` (Amendment Y) names
`google/gemma-4-E4B` (pt) as one of its four Arm A pretrain-only bases and
reports a resolved result for it: `checkpoint: "raw google/gemma-4-E4B (no
adapter)"`.

Architecture, confirmed at signing prerequisite time by fetching
`config.json` only (no weight download; see NOTEBOOK.md): `model_type`
`gemma4`, `architectures` `["Gemma4ForConditionalGeneration"]`, nested
`text_config` with `num_hidden_layers: 42`, `hidden_size: 2560`, so 43 hidden
states for full-depth capture. `text_config.num_kv_shared_layers: 18`
independently corroborates the KV-seam hazard below (blocks 24 through 41,
18 blocks, share K/V with blocks 22/23). This matches the family atlas's
resolved read of the instruct sibling and Amendment Y's 43-entry surface for
the pt form (its `X_G1_gate.auroc_surface` is keyed `"0"` through `"42"`).

## What is already committed about this substrate, and what is not

This matters because every band below must be justified from committed
quantities and none may be invented after a Gemma flavor number exists.

Amendment Y ran a KU-style answerability readout on this exact pt
checkpoint and committed a full-depth AUROC surface over hidden states 0 to
42:

- hs0 0.4979, hs1 0.9524, hs2 0.9777, hs3 0.9845, hs4 0.9897, hs5 0.9927,
  then a flat plateau in the 0.991 to 0.9975 range from hs6 through hs42,
  best hs24 0.9975 with 95% CI [0.9956, 0.9989], hs42 0.9969.
- Pool: the frozen SelfAware gate rows,
  `experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl`,
  1233 rows. Class counts n_known 518, n_unknown 627.

Three things about that surface are load-bearing here and one thing is not.

Load-bearing. First, hs0 reads 0.4979, which is chance, the same signature
the Qwen atlas records at its own hidden state 0 (exactly 0.5000, where the
anchor embeddings are byte-identical across rows). Second, the readout is
already at 0.9524 by hs1, matching the Qwen atlas's shallow onset
(0.9201 to 0.9888 across flavors at its hidden state 1). Third, the plateau
is flat from roughly hs6 to hs42, which means this substrate does not have a
narrow readable window that a replication could miss by picking the wrong
layer.

NOT load-bearing, and it must not be quoted as if it were the same
measurement. Y's readout is `known_answered` versus `hallucination`, that is
behavior-derived roles assigned after generation, on a 1233-row SelfAware
subset, scored by the Amendment X cross-model scorer. The flavor atlas's
readout is dataset-label unknown versus known, no behavior involved, scored
by the item-26 out-of-fold protocol. They are different labels and different
estimators on overlapping material. Y's surface is used here for exactly two
purposes: to fix an anchor layer independently of any KUQ flavor data, and
to establish that this substrate reads SOMETHING answerability-shaped at
near ceiling so that a null here would be surprising rather than expected.
It is never used as a baseline value that a flavor number is compared
against.

Revision pin resolved at signing prerequisite time (was NOT committed
anywhere in the program before this cell):
`411aa17b749aa952df1359d2dcea73917a544d9a`, resolved via `HfApi().model_info`
on `google/gemma-4-E4B`, no weight download. The repo is public and ungated
(`gated: False`, `private: False`). The instruct sibling's pin
(`fee6332c1abaafb77f6f9624236c63aa2f1d0187`) is a different checkpoint and is
not reused.

## Can existing captures be reused

No, and the reasons are worth stating because they are the difference
between a CPU-only cell and a GPU cell.

The 1.2 GB of full-depth anchor activations under
`experiments/gemma-4-e4b-family-atlas/analysis/gemma4_e4b_it/atlas_capture/`
cannot serve this cell. They are the instruct sibling, not the pretrain-only
base, which alone disqualifies them for a pretraining clause. Beyond base
form they also differ on every other instrument axis: 2815 rows mined by the
fleet prep script from TriviaQA, PopQA, and KUQ candidates rather than the
flavor atlas's screened pools; roles assigned by post-generation behavior
rather than dataset label; a known pool drawn from TriviaQA and PopQA
correct answers rather than KUQ knowns; and a different render module. Four
simultaneous instrument changes is not a replication.

Amendment Y's cloud cells uploaded only small result JSON plus manifests, so
no pt activations exist on disk to re-read. The pt weights are also not in
the local Hugging Face cache (only the it sibling is present), so a
first-time weight download is a prerequisite for the GPU capture step (not
performed by this scaffolding pass).

Conclusion: this cell requires new extraction on GPU. The style-control
secondary that rides on top of it is CPU-only once the extraction exists.

## Instrument hazard that governs the whole design

`google/gemma-4-E4B` shares K/V across depth: blocks 24 through 41 read
donor K/V from blocks 22 and 23 THROUGH the cache object (independently
corroborated at signing by `text_config.num_kv_shared_layers: 18`, exactly
the 18 blocks 24-41). The consequence, documented at
`experiments/gemma4-e4b-kv-seam-quarantine/extract_anchor.py` and in
`experiments/j-space-cross-family-layer-contrast`, is that a forward pass
run with `use_cache=False` starves those blocks: hidden states hs00 through
hs24 stay bit-identical to a correct run, and hs25 through hs42 are garbage,
decaying from cosine 0.732 at hs25 to 0.075 at hs42 against the correct
values. The vendored extractor states the rule in its own comment: only a
`forward_use_cache == True`, complete, full-depth extraction is admissible
for a read profile.

This is not a hypothetical. `synaptic-tuner/MechInterp/extraction/capture.py`
line 161 passes `use_cache=False` unconditionally. That is the code path
behind the `mechinterp extract` verb and behind the three extraction recipes
`flavor-atlas-rawbase` used. Running this cell the way the Qwen cell was run
would silently corrupt 18 of 43 hidden states, including the entire upper
half of the depth range, and would corrupt them in a way that still produces
plausible-looking AUROCs. Llama, Mistral, and Qwen are unaffected, which is
exactly why the Qwen cell never had to think about it.

Registered consequence: the `mechinterp extract` verb is PROHIBITED for this
cell. Extraction runs through `extract_anchor_gemma.py`, a vendored, adapted
copy of `experiments/gemma4-e4b-kv-seam-quarantine/extract_anchor.py`, which
already passes `use_cache=True`, builds a fresh full-length cache per row so
no row's donor reads leak into the next, captures every hidden state at the
`prompt_len - 1` anchor, and records `forward_use_cache: true` in its
manifest as the provenance marker. The vendored copy is modified only to
consume this cell's panels and render, and to write per-row safetensors plus
a manifest in the layout `flavor_probe_sweep.py` already reads, so the probe
protocol itself is imported byte-identically.

Corroboration that the seam-safe path yields a healthy deep profile on this
substrate: Amendment Y's committed surface for the pt checkpoint shows no
collapse above hs24 (0.9975 at hs24, 0.9969 at hs42), which is what an
uncorrupted extraction looks like.

## Design

### Panels

Byte-identical to `flavor-atlas-rawbase`, reusing its already-built panel
files so the row sets, labels, and flavor assignments cannot drift between
substrates. Only the substrate and the render change. `build_flavor_panels.py`
in this cell does not rebuild or resample anything: it verifies the source
panel files at `experiments/flavor-atlas-rawbase/analysis/panels/*.jsonl`
against the pinned sha256 values below byte for byte, then copies them
unchanged into this cell's own `analysis/panels/`. A sha256 mismatch is a
hard stop, not a silent rebuild.

- KUQ panel, 5540 rows = 3071 known + 2469 unknown, flavor counts ambiguous
  411, controversial 490, counterfactual 403, false assumption 368, future
  unknown 490, unsolved problem 307. sha256
  `69433a777d40b76544b7f4575bc042bb2a9d4d159ca6e8a8bf20d133cf0a8eef`.
- AmbigQA panel, 2748 rows = 1245 known + 1503 unknown. sha256
  `ee60cbf9115eefc18a997a0a81600ce627789c6f710f9905fe959936ba33d7f2`.
- SelfAware panel, 3369 rows = 2337 answerable + 1032 unanswerable. sha256
  `378762ac7cd703743b7b4edc54bdbdd86fa47e1cd8657688f4dbf5d43aa186f0`.
- Panels manifest sha256
  `6a58e429c930723c9e6c29afa76821cacbdc9a92b053ec4975c8618f8a5225d0`.

Total 11657 rows. No resampling, no rebuilding, no filtering. (The upstream
source files these panels were built from are not present in every checkout
because `analysis/` is gitignored; `build_flavor_panels.py` operates on the
already-built flavor-atlas-rawbase panel jsonls, which is the level this
cell reuses at.)

### Render (PRIMARY/CONTROL SWAPPED from the original draft's default, per
lead adjudication: "Amendment Y base-mode k-shot render rule")

Two registered surfaces exist in the program and they point opposite ways.
The Qwen cell rendered its raw pretrained base through a chat template
belonging to a fine-tuned sibling of that base. Amendment Y's pre-stated
prompting-surface rule is that ALL pretrain-only base cells use a base-mode
k-shot surface with no chat template, uniformly, even where a base
checkpoint ships a template.

**Lead adjudication (this signing pass): Amendment Y's rule governs.** The
base-mode k-shot surface is PRIMARY; the chat-template surface is the
descriptive dual-render CONTROL. This is the reverse of the draft's
original default (which proposed chat-template primary / k-shot control)
and follows the draft's own stated fallback: "If the lead prefers Y's rule,
swap the primary and the control; the arithmetic is unchanged." All G1-G5
primary readouts below are computed on the full-panel k-shot captures; G6 is
the chat-template control on the 1800-row subsample.

**Primary: base-mode k-shot, vendored byte-identical from Amendment Y's own
implementation.** `render_gemma.py::render_primary_kshot` reproduces
`experiments/common/readouts/amendment_x_cross_model_extract.py`'s
`build_base_mode_prompt` / `_BASE_MODE_FEWSHOT` byte-for-byte: a fixed,
hand-written 5-shot trivia QA block (`"Q: {q}\nA: {a}\n\n"` per exemplar,
none of the five drawn from PopQA/TriviaQA/SelfAware/KUQ, the program's
leakage rule), followed by `"Q: {question}\nA:"` for the target question, no
chat template, no system prompt. The anchor position is the last token of
this string (`prompt_len - 1`), matching the extractor's own convention.
This is the render-invariant, gate-like surface Y's own dual-render evidence
supports (0.998 both ways on `Qwen3.5-4B-Base`) and is instrument parity
with Y's registered rule for pretrain-only bases, at the cost of prompt
parity with the Qwen atlas's chat-template render.

**Control (descriptive, G6): chat-template surface, for cross-reference to
the Qwen atlas's own render.** `render_gemma.py::render_control_chat`
applies the `google/gemma-4-E4B-it` chat template to the pt base, with the
same verbatim system prompt the Qwen render carries
(`ood_breadth_response_confidence_render.SYSTEM_PROMPT`), since post-training
does not retrain tokenization and the pt and it siblings share a tokenizer.
The it tokenizer is already in the local cache. The control is descriptive
and cannot pass, falsify, or rescue anything; if it shows the k-shot and
chat-template surfaces reading materially differently, a primary null is
reported as render-confounded rather than as a failed replication.

Dual-render subsample recipe, fixed now: 200 unknown rows per KUQ flavor
(the smallest flavor has 307, so 200 is reachable for all six) plus 600 KUQ
known rows, all drawn by a fixed seed with deterministic ordering from the
pinned KUQ panel. 1800 rows, all 43 hidden states, rendered with the
chat-template control surface.

### Capture

One forward-only, no-generation anchor capture per panel on the pt base, all
43 hidden states in a single pass, anchor position `prompt_len - 1`, batch 1
with a fresh full-length cache per row, `use_cache=True`, bf16, no adapter,
rendered with the PRIMARY k-shot surface. Plus the dual-render CONTROL
capture on the 1800-row subsample, rendered with the chat-template surface.
Four capture verbs total, sequential, one GPU job at a time, all through
`extract_anchor_gemma.py` (never `mechinterp extract`).

### Probe protocol

Byte-identical to the Qwen cell: `internal_panel_probe_gate._cv_auroc_with_oof`
imported unchanged (StandardScaler plus L2 LogisticRegression C=0.5,
StratifiedKFold 5, seed 0, held-out out-of-fold AUROC), pinned at sha256
`ee3f22eed5f8b4fe8f260c5b3335c565156eadfcf083473bb445921d29885b08`, driven
by `flavor_probe_sweep.py` (this cell's vendored copy, adapted for 43 layers
and the two-leg decision surface), with no change to any estimator.

### Readouts

G1, flavor-by-layer map. For each KUQ flavor, that flavor's unknowns against
the full 3071-row KUQ known pool, at every one of the 43 hidden states, plus
a pooled all-unknowns row. Same construction as the Qwen atlas M1. Computed
on the PRIMARY (k-shot) capture.

G2, AmbigQA layer sweep, unknown versus known at every hidden state. This is
the boundary clause's decision surface, and it is a whole-curve statement,
not a single cell. PRIMARY capture.

G3, SelfAware layer sweep, the reference curve at every hidden state.
PRIMARY capture.

G4, transfer matrix. For each source among the six KUQ flavors, SelfAware,
and AmbigQA, fit one full-data probe at that source's own best layer, then
evaluate the frozen probe on every other flavor's rows at that same layer,
target unknowns against the target's own known pool. Same construction as
the Qwen atlas M4. PRIMARY capture.

G5, style-residualization secondary, built in
(`surface_residualization.py`). One unsupervised prompt-surface basis fit on
the union of the three panels' question strings without labels,
cross-fitted ridge prediction of each panel-layer activation matrix from
that surface matrix out of fold with alpha selected by inner three-fold
activation MSE from `[0.01, 0.1, 1, 10, 100, 1000]`, then the same pinned
probe run unchanged on the residual. The prohibited-input rule: dataset
source, panel identity, KUQ category, flavor, and label may not enter the
surface matrix, because here the label is exactly pool membership and
flavor is exactly the KUQ category; also excluded: generated_text,
completion_length, answer_correctness, answer_text, aliases. The surface
matrix is built ONLY from the question string's own text-shape statistics
(character/word/punctuation counts) and hashed lexical n-gram features
reduced by truncated SVD, matching the family-atlas-surface-residualization-
control instrument's lexical-covariate design but with its `source` and
`category` one-hot columns removed (those are exactly the prohibited
dataset-source/flavor signal here). Its treatment-strength, permuted-surface
negative control, and planted-channel positive control carry over from
`family-atlas-surface-residualization-control` with the same constants
(alpha grid, 20 permutations, hs0 plant).

The planted-channel positive control transfers cleanly because this
substrate has the same provably null layer: Amendment Y measures hidden
state 0 at 0.4979 on the pt checkpoint, chance, which is the constant-anchor
signature the plant needs. The control plants a linear-in-surface direction
at hidden state 0, requires it to reach pooled AUROC at least 0.90, and
requires residualization to return it to at most 0.75.

G6, dual-render control, descriptive. The six flavors and the pooled row on
the 1800-row chat-template-rendered subsample, at every hidden state,
compared against the same rows' PRIMARY (k-shot) reading.

### Containment

Committed output is a counts-only JSON at
`analysis-committed/gemma_flavor_sweep.json`: AUROCs at 4dp, class counts,
best layers, full layer curves, the transfer matrix, residualized curves,
control summaries, gate records, input shas, and the extraction manifests'
`forward_use_cache` values. No question text, no row-level surface matrix,
no row-level prediction, and no activation enters the committed surface.
Activations, panels, surface matrices, and out-of-fold predictions stay
under a gitignored `analysis/`.

## Multiplicity discipline and the layer problem

Layer coordinates are family-relative and are never ported. The Qwen cell's
primary layers (each flavor's committed best plus L35) have no meaning here,
and this cell must locate its own depths. It sweeps all 43 hidden states, as
the Qwen atlas swept all 37, and it fixes its decision surface before any
Gemma flavor number exists using two legs that between them remove the
post-hoc selection problem.

Leg A, pre-fixed anchor: hidden state 24. Justification, entirely from
committed material and fixed before this cell runs: hs24 is the best layer
of Amendment Y's committed answerability surface on this exact pretrain-only
checkpoint. It was selected on `known_answered` versus `hallucination` over
a 1233-row SelfAware subset, which is a different label set and a different
estimator from the six KUQ flavor probes this cell decides on, so with
respect to those twelve decisions hs24 is an externally fixed constant, not
a selection on the decision data. Its depth is 24/42 = 0.571, inside the Y
plateau and inside the instruct sibling's resolved readable band, and it
sits at the top of the seam-safe region (hs00 to hs24 are the states that
stay bit-identical under either cache setting), which makes it the layer
whose value is least sensitive to any residual doubt about the extraction
path.

Leg B, nested split-half selection: each flavor's decision layer is chosen
by maximum out-of-fold AUROC on a fixed 50% selection split, stratified by
label and flavor with a fixed seed, and the reported number is the
out-of-fold AUROC at that layer computed on the complementary 50% evaluation
split, which the selection never saw. This leg is immune to
max-over-43-layers inflation by construction and needs no external anchor.

Primary decision surface: 6 flavors by 2 legs = 12 cells. Decisions are per
flavor; there is no pooled single-number verdict for the six.

Reference rows, banded but not deciding: pooled all unknowns and SelfAware,
each at hs24 and under Leg B.

AmbigQA is adjudicated as a whole curve across all 43 hidden states, not at
a selected layer, because the boundary clause is the statement that it is
unreadable everywhere.

The transfer matrix is adjudicated as a set under one pre-stated rule, not
cell by cell.

Full 43-layer curves are reported for every row so no max-over-layer
selection is hidden. Maximum-over-layer values are printed next to their
full curves and are descriptive.

## Bands and where every number comes from

Two constants, both lifted verbatim from
`experiments/flavor-atlas-rawbase/gates.yaml`, where they were fixed before
any flavor number existed on any substrate:

- `0.90`, that cell's `p1_discovery_floor_heldout_auroc`. Headroom check
  against the closest committed comparators: the Qwen flavors all read
  0.9766 or above at both of their legs, and Y's committed answerability
  readout on this very pt checkpoint reads 0.9975 at hs24 and does not drop
  below 0.991 anywhere from hs6 to hs42. A 0.90 floor therefore leaves at
  least 0.076 of headroom against every relevant committed value.
- `0.75`, that cell's `p2_ambiguity_ceiling_all_layers`. It sits above the
  highest AmbigQA reading anywhere in the Qwen atlas (0.6590), which is the
  program's operational level for an unanswerability surface a base cannot
  read.

One constant from that file is deliberately REJECTED and the rejection is
recorded here so it cannot be quietly reinstated later. Its F1 universal-code
limb used `0.85` as the transfer-matrix off-diagonal bar. The Qwen cell's own
realized minimum off-diagonal among the seven overt sources was 0.8331,
below 0.85. Requiring 0.85 on Gemma would require the replication to beat
the thing it replicates, which is a goalpost move dressed as a constant.
The transfer bands below use 0.75 in both directions, which is below Qwen's
realized minimum of 0.8331 and above Qwen's realized maximum into AmbigQA
(0.5746) and out of AmbigQA (0.5853).

Committed Qwen values this cell is replicating, for reference only, never as
a threshold:

| Row | n unknown | best layer | AUROC at best | AUROC at L35 | AUROC at L1 |
|---|---:|---:|---:|---:|---:|
| ambiguous | 411 | 26 | 0.9800 | 0.9766 | 0.9201 |
| controversial | 490 | 20 | 0.9960 | 0.9949 | 0.9625 |
| counterfactual | 403 | 19 | 0.9963 | 0.9952 | 0.9773 |
| false assumption | 368 | 29 | 0.9918 | 0.9912 | 0.9432 |
| future unknown | 490 | 17 | 0.9994 | 0.9990 | 0.9888 |
| unsolved problem | 307 | 28 | 0.9937 | 0.9915 | 0.9295 |
| pooled all unknowns | 2469 | 27 | 0.9887 | 0.9874 | 0.9449 |
| SelfAware | 1032 | 25 | 0.9937 | 0.9925 | 0.9583 |
| AmbigQA | 1503 | 25 | 0.6590 | 0.6338 | 0.5935 |

Qwen transfer, committed: 0.8331 to 0.9996 among the six flavors and
SelfAware; every probe into AmbigQA 0.4878 to 0.5746; the AmbigQA-trained
probe reads 0.4332 to 0.5853 everywhere else.

## Prediction

- P1 (Clause A, primary): on `google/gemma-4-E4B` pretrain-only, all six KUQ
  flavors reach held-out out-of-fold AUROC at or above 0.90 at hidden state
  24 AND at or above 0.90 under the nested split-half selection leg, for all
  twelve primary cells.
- P2 (Clause B, primary): AmbigQA stays at or below 0.75 at every one of the
  43 hidden states.
- P3 (transfer, primary): every off-diagonal cell of the transfer matrix
  among the six KUQ flavors and SelfAware reads at or above 0.75, and every
  cell involving AmbigQA as source or as target reads at or below 0.75.
- P4 (style control, secondary, banded): after cross-fitted surface
  residualization, all six KUQ flavors retain AUROC at or above 0.90 at
  hidden state 24 and under the split-half leg.
- P5 (reference): SelfAware reaches at or above 0.90 at hidden state 24 and
  under the split-half leg.

## Falsifier

- F1 (Clause A does not replicate): with GG0 to GG4 passing, any one of the
  twelve primary cells reads below 0.90. Clause A is not promotable; the
  broad-overt-code finding is rescoped in writing to `unsloth/Qwen3-4B` raw
  base and is reported per flavor, with no pooled rescue and no band
  retuning.
- F2 (Clause B does not replicate): with GG0 to GG4 passing, AmbigQA reaches
  0.90 or above at any one of the 43 hidden states. The overt versus covert
  boundary is then a Qwen-specific property, not a property of pretrained
  bases, and the boundary clause is falsified as a cross-family statement.
- F3 (style artifact on the second substrate): with the residualization
  controls passing, all six KUQ flavors fall to 0.75 or below at both
  primary legs after residualization. Promotion is blocked regardless of
  what the Qwen-side surface control returned, and the finding is written up
  as surface-carried on this substrate.
- F4 (transfer does not replicate): any off-diagonal cell among the six
  flavors and SelfAware reads below 0.75. The "freely transferring" half of
  Clause A is not promotable; per-flavor separation may still stand and is
  reported separately.

F1 and F4 both bear on Clause A and are kept separate because Clause A has
two parts, separation and transfer, and they can fail independently.

## Ambiguous zone

- Any flavor reading strictly between 0.75 and 0.90 at either primary leg is
  partial replication. Reported at its measured value, per flavor, no
  promotion, no single-number verdict.
- AmbigQA reading strictly between 0.75 and 0.90 at one or more hidden
  states is partial boundary replication. Clause B is not promoted; the
  curve is reported in full and the maximum is stated with its layer.
- A split among the six, some clearing 0.90 and some at or below 0.75, is a
  mixed replication, reported per flavor exactly as the Qwen atlas reported
  its mixed result.

Two asymmetries are stated now, before any number exists, because they
govern how a null may be written up.

First, this is a cross-family comparison, so a Gemma null is confounded with
the render change and with the architecture. The dual-render control (G6)
is what lets a null be attributed, and if G6 shows the k-shot surface
reading materially differently from the chat-template surface, then a null
under the primary render is reported as render-confounded rather than as a
failed replication.

Second, the residualization asymmetry carried over from the companion cell:
residualization removes surface-predictable activation variance, not label
variance, so F3 licenses only "not promotable on these pools" and "the fresh
surface-matched pool is the next instrument". It never licenses "this base
has no unanswerability code".

## Gates

Fail-closed. Any GG failure voids the dependent G readings before they are
looked at. Full machine-readable form in `gates.yaml`.

- **GG0 substrate and input integrity.** The pt revision resolved at signing
  (`411aa17b749aa952df1359d2dcea73917a544d9a`) matches the manifest pin char
  for char; the loaded config exposes 42 text decoder blocks, hidden size
  2560, and 43 hidden states through the nested `text_config`; no adapter is
  loaded; every panel sha256 above matches byte for byte; panel row counts
  and the six locked KUQ flavor counts match `flavor-atlas-rawbase/gates.yaml`
  fg0 exactly; the probe module sha256 matches `ee3f22ee...`.
- **GG1 KV-seam admissibility.** THE decisive integrity gate for this
  substrate. Every extraction manifest records `forward_use_cache: true`.
  The `mechinterp extract` verb is not used anywhere in this cell, and no
  artifact produced by `synaptic-tuner/MechInterp/extraction/capture.py` is
  read. Before the production captures, a 32-row paired smoke extracts the
  same fixed rows under `use_cache=True` and `use_cache=False` and records
  the per-layer cosine between them; the documented signature (hs00 to hs24
  identical, divergence beginning at hs25) must either reproduce, confirming
  the hazard is live on this build and that the True path is the unstarved
  one, or the two paths must agree at every layer, confirming this
  transformers build does not exhibit the seam. Any third outcome, in
  particular divergence at or below hs24, halts the cell as indeterminate.
  The smoke is instrument verification and produces no G reading. A
  `--mode=synthetic` CPU-only harness (`kv_seam_paired_smoke.py`) exercises
  the classification logic itself against fabricated cosine profiles; it is
  not a substitute for the live GPU smoke, which still must run before
  production captures.
- **GG2 capture completeness.** For each of the four captures, rows
  extracted equals rows in the panel (5540, 2748, 3369, 1800), `complete` is
  true, 43 hidden states are present for every row, anchor position is
  `prompt_len - 1`, and hidden width is 2560.
- **GG3 runtime provenance.** Every GPU verb runs inside the pinned
  `mechinterp-runner` image with the digest verified char for char before
  the verb (confirmed at signing:
  `sha256:2471502c3110a96d4955b48eb58da41e96a90276d22c4d5f1eac2c99b60a2cf8`,
  matches char for char via `docker image inspect`), per the 2026-07-10
  standing directive, one GPU job at a time, with a provenance JSON line in
  each run log.
- **GG4 hidden-state-0 sanity.** Hidden state 0 must read at chance for
  every row of the atlas, consistent with a constant anchor embedding under
  a fixed template. Y's committed 0.4979 on this substrate and the Qwen
  atlas's exact 0.5000 are the precedent. A hidden state 0 that separates
  means the anchor is not what the design assumes and the cell is
  indeterminate.
- **GG5 residualization controls** (secondary readout only). Treatment
  strength: combined-block activation out-of-fold R2 at least 0.01 at each
  primary layer and at least 0.005 above the 95th percentile of 20
  permuted-surface nulls. Permutation negative control: at least 18 of 20
  permuted-surface runs leave all six flavors at or above 0.90 at both legs.
  Planted-channel positive control at hidden state 0: the plant reaches
  pooled AUROC at least 0.90 and residualization returns it to at most 0.75.
  All constants are the ones already registered in
  `family-atlas-surface-residualization-control` and carried by the
  companion cell. Failure makes P4 and F3 indeterminate and does not touch
  P1, P2, P3.
- **GG6 containment.** Committed JSON passes a positive schema check and a
  prohibited-text scan; no question text, row-level matrix, prediction, or
  activation appears in `analysis-committed/`; all other writes stay under
  gitignored `analysis/`.
- **GG7 decision.** Only after GG0 to GG4 pass (and GG5 for the secondary),
  adjudicate P1 through P5 and F1 through F4 against the bands above.
  Nothing else decides.

## Signing prerequisites - RESOLVED (this pass, all CPU-only)

1. **Revision pin.** `411aa17b749aa952df1359d2dcea73917a544d9a`, resolved via
   `HfApi().model_info("google/gemma-4-E4B")`, no weight download. See
   NOTEBOOK.md for the exact call.
2. **Hub access.** Public, `gated: False`, `private: False`. Metadata fetch
   succeeded with no auth token.
3. **Config shape.** Fetched `config.json` only (no weight download) at the
   pinned revision: `model_type: gemma4`,
   `architectures: ["Gemma4ForConditionalGeneration"]`, nested `text_config`
   with `num_hidden_layers: 42`, `hidden_size: 2560` -> 43 hidden states,
   matching the draft exactly. `num_kv_shared_layers: 18` independently
   confirms the KV-seam hazard footprint (blocks 24-41).
4. **Runtime image digest.** `docker image inspect mechinterp-runner:local`
   (read-only) returns `sha256:2471502c3110a96d4955b48eb58da41e96a90276d22c4d5f1eac2c99b60a2cf8`,
   matching the draft's pin char for char.
5. **Render module, vendored extractor, panel builder, probe sweep,
   residualization secondary, and gate adjudicator authored and CPU-smoked**
   over synthetic arrays; the GG1 paired-smoke harness's synthetic mode and a
   gate-math assertion (registered split-half Leg B selection-vs-evaluation
   split logic against a plausible-wrong circular formulation) are included.
   See NOTEBOOK.md for smoke results. No GPU verb, no docker run, no weight
   download was issued in this pass.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | (left for the lead, to be filled before any Gemma flavor number exists) |
| user | (left for the PI, to be filled before any Gemma flavor number exists) |

## Outcome

Filled at resolve. Record the twelve primary cells, the AmbigQA curve
maximum with its layer, the transfer matrix adjudication, the residualized
secondary, every gate result including the GG1 paired-smoke outcome, and the
one-sentence summary that also goes into `verdict:` in the manifest.
