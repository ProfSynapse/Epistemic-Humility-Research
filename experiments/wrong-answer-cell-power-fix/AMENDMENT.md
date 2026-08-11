# Wrong-Answer Cell Power Fix

**Status:** falsified, resolved 2026-08-09, PI approved (machine state in
`experiment.yaml`); verdict: primary falsifier fired as worded, the
known-unknown axis at pinned L35 does not carry correct-vs-wrong at
deployment (see experiment.yaml `verdict:`). This header was stale
boilerplate reading "draft (not signed; do not launch, do not cite as
evidence)" until 2026-08-11; corrected to match the machine state, which
was already `falsified`. **Separate, unresolved gap found at the same
correction pass: this document's own "Outcome" section below is still the
unfilled placeholder text ("Filled at resolve...") despite the machine
state showing falsified with a verdict on record; it has not been
backfilled with the actual result narrative. Flagged for lead/PI
follow-up, not corrected here (no scientific content authored by this
pass).** Tier-2 exploratory cell: new evidence, falsifier pre-stated,
reported separately from the locked PROTOCOL v0.3 matrix and never pooled
with it. Prose lives here; machine state lives in `experiment.yaml`.

**Instrument rationale.** Tier-2 Amendment per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md` decision Q2:
it introduces a new eval/extraction cell whose output is reported as evidence.
It sits at tier 2 rather than tier 3 because the numbers it produces will
replace published sentences in
`papers/paper-3-knows-but-doesnt-say/manuscript.md`, which is a reported surface,
even though the primary arm consumes generations that already exist.

**Compute.** GPU, extraction only for the primary arm; one generation pass for
the secondary arm. No training. Local RTX 3090 lane, one job at a time (no
concurrent GPU work in this lane while the cell runs). Budget: 0.5 to 0.75
GPU-hours for Arm A (both checkpoints come from the same pass), 1.0 to 1.7
GPU-hours for Arm B including a timing smoke, so 1.5 to 2.5 GPU-hours total, of
which Arm A alone is under one hour. Container pinned to
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`.
Launch requires explicit PI approval naming the arm and the lane, separately from
this registration.

**Model and surface.** Qwen3-4B. Primary checkpoint is the deployed clean-SFT
merged-16bit base with the GRPO-v2 LoRA adapter active; control checkpoint is
the same merged base with the adapter disabled. Single model, single seed,
exploratory.

## Revision history

- **R1 (DRAFT, 2026-08-08):** initial registration draft. Gates, prediction, and
  falsifier written before any run. Awaiting lead review, PI sign-off, and
  `bin/exp sign`.

## 1. Motivation and posture

Paper 3 carries this limitation verbatim (`manuscript.md:1024-1026`):

> Small wrong-answer cells. Some internal-vs-stated discrimination numbers rest
> on few wrong-answered items (n = 16 on the held-in known set); these are
> reported as directional. The full-eval AUROC numbers (n approximately 3369)
> are not affected.

The limitation reaches further than it states. Every number in the
`manuscript.md:307-348` internal-vs-stated contrast that involves correctness
traces to one lab-notebook checkpoint,
`archive/docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`
checkpoint `004-result`, which records its own population as "B2 answered known
rows n=389 (373 correct / 16 wrong; UNDERPOWERED on wrong -> discrimination
numbers directional)" and reports from it: emitted mean 0.821, std 0.015, AUROC
0.559, ECE 0.142, and the internal side's raw projection AUROC 0.667, 1-D
logistic readout AUROC 0.649 and ECE 0.004. Those are the numbers at
`manuscript.md:314`, `:330`, `:331`, and they are also the two ECE values in
Figure 1's right panel (`manuscript.md:345-347`). Sixteen rows therefore decide
whether the paper's calibration contrast is a finding: an aggregate ECE of 0.004
on a population that checkpoint `004-result` records as 95.9 percent correct is
close to what any near-constant predictor pinned at the base rate would score.

The limitation's stated cause does not survive contact with the artifacts. The
premise has been that abstention-trained checkpoints rarely attempt, so wrong
items are scarce at deployment rendering. On the same checkpoint and the same
evaluation,
`archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json`
records `A_full_eval.answered_known_n = 780` with
`A_full_eval.answered_known_n_wrong = 360`, while the adjacent
`A_behavior_subset` block records `answered_known_n = 388` with
`answered_known_n_wrong = 15`. Both blocks were verified against the scored rows
themselves (`scored_rows.jsonl`, sha256 `1a6d7b59...`, 3369 rows, 780
answered-known, 420 correct, 360 wrong). The scarcity lives in the frozen
1233-row behavior-strata extraction manifest that the hidden states were taken
over, not in the deployment surface. The wrong answers do not need to be
generated; they need to be extracted. That is why the primary arm here is an
extraction backfill and not a generation campaign, and why the secondary
generation arm is registered as descriptive rather than as the fix.

## 2. Design

### 2.1 What is being re-estimated

Only these paper-3 numbers, and no others:

| ID | Paper-3 location | Current value | Source |
|----|------------------|---------------|--------|
| M1 | `manuscript.md:314` | internal 1-D readout ECE approximately 0.004 | session `004-result` |
| M2 | `manuscript.md:315-316` | internal projection monotone correct > wrong > refused > unknown | session `004-result`, `008-result` |
| M3 | `manuscript.md:330` | emitted mean approximately 0.821, std approximately 0.015 | session `004-result` |
| M4 | `manuscript.md:331` | emitted AUROC(correct vs wrong) approximately 0.559 | session `004-result` |
| M5 | `manuscript.md:331` | emitted ECE(vs correctness) approximately 0.142 | session `004-result` |
| M6 | `manuscript.md:336-337`, Fig. 1 caption `:341-348` | "the discriminating signal exists internally and the verbalized number is a collapsed near-constant" | M1 through M5 jointly |
| M7 | not published; the missing comparator | internal readout AUROC 0.649, raw projection AUROC 0.667 | session `004-result` |

Explicitly out of scope, per the section-9 bullet's own carve-out: the
known/unknown probe AUROC 0.997 (`manuscript.md:310`), the like-for-like 0.972
versus 0.637 contrast (`manuscript.md:357-358`), the survives-training refits
(`manuscript.md:387-388`), all of section 5's geometry, and all of section 7's
behavior and calibration table.

This cell also does not touch the correctness-confidence-probe or
correctness-readout-deployment-port results. Those measure a post-generation
correctness probe (post-gen AUROC 0.834 at L20 and 0.819 at L22 respectively;
`experiments/correctness-confidence-probe/AMENDMENT.md` section 7,
`experiments/correctness-readout-deployment-port/AMENDMENT.md` section 7). This
cell measures the pre-generation known-unknown axis read as a correctness signal.
Different instrument, different read position.

### 2.2 Three render surfaces, stated plainly

This design touches three distinct system-prompt renders, and conflating any two
of them would produce a false comparison. Each was read from a committed file
this session.

1. **Deployment eval render (encourages abstention).** From
   `archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`,
   key `prompt.system`: "Answer the user's question. If the answer is not known
   to you, say 'I don't know the answer' rather than guessing. Return only a JSON
   object with exactly two keys: 'answer' and 'response_confidence'." This is the
   render that produced every emitted `response_confidence` value in paper 3, and
   it is the surface the paper's directional claim is about. **Arm A renders
   under this prompt.**
2. **Forced-best-guess render (suppresses abstention).** The locked
   abstention-suppression method of the correctness-readout deployment port
   (`experiments/correctness-readout-deployment-port/AMENDMENT.md` section 1.3
   and the sign-off block; text at
   `experiments/common/readouts/amendment_t_correctness_readout_deployment_extract.py:70-75`):
   "Always give your single best-guess answer to every question. Never refuse,
   never say you do not know, and never decline." That harness renders bare text
   and never parses a `response_confidence` field, so it cannot on its own supply
   this cell's stated channel. **Arm B composes its abstention-suppression clause
   with the deployment render's JSON-schema clause**, which is a new composition
   and is gated as such (G0-6, G0-7).
3. **Frozen-manifest render (neutral).** The extraction that supplies the
   paper-3 numbers being re-estimated,
   `.../hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f`,
   was produced by
   `archive/experiment/phase1/probe/config/selfaware-hs/hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed1_full.yaml`,
   which carries **no `prompt` block**. The harness therefore fell through to its
   default at
   `experiments/common/knowledge_probe/hidden_state_probe.py:546-547`, "You are a
   helpful assistant. Answer the question concisely." This is neither of the
   other two prompts. The repo's own naming convention corroborates the reading:
   sibling configs that do carry the deployment prompt verbatim are named
   `*_prompt_matched.yaml` (for example
   `hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched.yaml:14-22`),
   and this config is not one of them.

**Binding consequence.** The frozen manifest and Arm A's new extraction are
different generation surfaces. They are never directly pooled, and no difference
between a frozen-manifest number and an Arm A number is reported without that
caveat attached. Arm A's numbers are the deployment-surface estimate; the frozen
manifest's numbers are the historical estimate on a neutral-prompt read of a
strata-selected subset.

### 2.3 Arm A (primary): deployment-render extraction backfill

No generation. The generations exist and are already graded. One forward pass per
row over the prompt only, at the generation anchor (`final_prompt_token`), layers
L30 through L36, `h_lora` and `h_base` both persisted. Because the extraction
config declares an adapter-disabled arm alongside the adapter-active arm, the
clean-SFT control checkpoint is read from `h_base` in the same pass at no extra
GPU cost.

Population: all 3369 SelfAware rows, so no subsampling decision is taken and all
four behavior cells needed for M2 are populated. Join to the scored rows 1:1 on
`question_id` plus `normq(question)`.

Verified counts on the two scored-row files (feasibility and coverage probe, not
a result):

| Checkpoint | rows | answered-known | correct | wrong |
|---|---|---|---|---|
| clean-SFT + GRPO-v2 (primary) | 3369 | 780 | 420 | 360 |
| clean-SFT, adapter disabled (control) | 3369 | 993 | 469 | 524 |

Both files carry a non-null `stated_confidence` on every answered-known row, so
the stated channel is constructible on both arms. This is a 24-fold increase in
the wrong cell on the primary checkpoint with no change to the rendering surface.

### 2.4 Arm B (secondary, descriptive): enlarged forced-answer pool

Primary checkpoint only. Pool is TriviaQA (Cheng test set, 11,313 rows) plus
PopQA (14,267 rows), the same two sources the correctness-probe cells used
(`experiments/common/readouts/amendment_s_correctness_probe_extract.py:153-167`).
AmbigQA is dropped at registration. Filtered on `normq` against the eight
training and preference files enumerated at
`papers/paper-3-knows-but-doesnt-say/analysis/clean_subset_sensitivity_p3.py:147-180`,
the TriviaQA probe/train pool, and the SelfAware evaluation set; the last of
these is required because SelfAware's answerable half is drawn from
`squadqa_train` (1307), `triviaqa_train` (657), `hotpot_train` (166),
`squadqa_dev` (180) and `triviaqa_dev` (11), so an unfiltered pool could
re-render rows Arm A already covers.

Generation runs on vLLM with structured outputs, matching the engine that
produced paper 3's stated channel. Target 500 correct and 500 wrong within 12,000
attempts; the deployment-port cell needed 8,550 attempts to reach 500 wrong at
approximately 82 percent refusal under forced-best-guess
(`experiments/correctness-readout-deployment-port/AMENDMENT.md` section 7), and
the schema-composed prompt may refuse more, so the attempt budget carries
headroom. Extraction over the answered rows uses Arm A's settings exactly.

Arm B is reported beside Arm A and never merged into it. Arm B cannot move an
evidential gate in either direction.

### 2.5 Internal readout: refit, not cold transport

The axis is the known-unknown (doubt) axis,
`unit(mean(known_correct_answered) - mean(unknown_refused))` in `h_lora` residual
space, the construction documented in
`archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_direction/doubt_direction_L35.json`
(`layer: 35`, `source: h_lora`, `pos_cell: known_correct_answered` with
`n_pos: 373`, `neg_cell: unknown_refused` with `n_neg: 676`).

The primary instrument is a **fold-wise refit**: within each of 5 stratified
folds the axis anchors are computed from rows outside the held-out fold only,
then the held-out fold is projected. The reason is that the frozen axis's
positive anchor is the `known_correct_answered` cell itself, so scoring
correct-versus-wrong on a population containing those same rows with that frozen
axis carries anchor overlap. Session `004-result`'s phrase "no correct/wrong
leakage" refers to the wrong rows only, which were never used in the fit. The
frozen direction is still projected and reported as a descriptive companion so
the historical instrument stays visible, but it is never gated.

Readout: 1-D logistic from axis projection to P(correct), 5-fold stratified CV,
out-of-fold predictions. Primary reported layer is L35, the paper's anchor; L30
through L36 is reported as a descriptive band with no best-layer selection on the
outcome metric, so the primary number cannot be selected post hoc.

### 2.6 Metrics

A1 internal refit readout AUROC(correct vs wrong); A2 raw axis projection AUROC;
A3 emitted AUROC; A4 gap = A1 minus A3 (paired); A5 internal ECE; A6 emitted ECE;
A7 calibration gap = A6 minus A5 (paired); A8 emitted mean and std on the
answered-known cell; A9 per-cell means for the four behavior cells with a CI on
the correct-minus-wrong step. Every metric carries a 2000-times bootstrap 95
percent CI; all internal-versus-stated differences use a paired bootstrap over
rows.

**Base-rate handling.** The frozen manifest's answered-known population is 95.9
percent correct; Arm A's is 53.8 percent correct on the primary checkpoint. ECE
is base-rate sensitive, so A5, A6 and A7 are reported under **both** a raw
accounting and an importance-reweighting to the 0.959 base rate, and gate E3
must hold under both. AUROC metrics are base-rate invariant and are reported
once.

### 2.7 Instrument configs

`cell.yaml` and `gates.yaml`, both listed under `instrument.configs` in
`experiment.yaml` and pinned by `bin/exp sign`. Harness modules do not exist yet;
they must be added to `instrument.modules` with their persistence declarations
before sign, per the kill-resume rule in the `experiments` skill.

## 3. Prediction

On at least 300 wrong rows at deployment rendering, the internal refit readout
ranks the model's own correct versus wrong answers at AUROC 0.60 to 0.72 while
the emitted scalar stays near its already-measured 0.5207, giving a gap of +0.08
to +0.20 with a paired CI excluding 0; the internal ECE rises from 0.004 to 0.05
to 0.15 raw because the 0.004 was an aggregate-calibration number on a 95.9
percent correct population, while the emitted ECE rises to 0.25 to 0.32 raw, so
the calibration contrast survives and widens under both accountings; the
internal cell ordering correct > wrong holds.

## 4. Falsifier

On at least 300 wrong rows the internal refit readout ranks correct versus wrong
at AUROC below 0.60 AND the gap over the emitted scalar is at most +0.05 with a
paired CI including 0, which overturns `manuscript.md:336-337` in its
discrimination half and forces Figure 1's framing and the section-9 bullet to be
rewritten.

Secondary: the calibration gap A7 is at most 0, or its CI includes 0, under the
base-rate-reweighted accounting, which overturns Figure 1's right panel at
`manuscript.md:345-347`. Tertiary: the internal correct-minus-wrong step's CI
includes 0 or the ordering inverts, which reduces `manuscript.md:315-316` to a
three-cell ordering.

## 5. Gates

Registered in `gates.yaml` and summarized here. G0 gates are integrity
preconditions that stop the cell before any outcome metric is computed and are
never read as evidence. E gates are evidential and are adjudicated on Arm A only.

| Gate | Arm | Direction and threshold | Stops or blocks |
|---|---|---|---|
| G0-1 render parity | A | byte-identical render on a 50-row sample, thinking-off self-check clean on 100 percent | STOP |
| G0-2 join integrity | A | 1:1 join, 0 unmatched, 0 duplicates, cell counts reproduce 780/420/360 and 993/469/524 exactly | STOP |
| G0-3 disjointness | B | 0 residual normq collisions after filtering | STOP |
| G0-4 grader parity | A, B | at least 99.5 percent label agreement on 200 re-graded rows | STOP |
| G0-5 data adequacy | A, B | at least 300 wrong and at least 300 correct before any fit | data-stage stop, never a verdict |
| G0-6 schema compliance | B | at least 95 percent parse rate within 2 retries | STOP Arm B |
| G0-7 render-shift control | B | emitted mean within 0.03 and std within 0.01 of the deployment-render values | not a stop; Arm B stated numbers become caveated-only and E5 is dropped |
| E1 internal discrimination | A | A1 at least 0.60 with CI lower bound above 0.55 | with E2, fires the primary falsifier |
| E2 the gap (PRIMARY) | A | A4 at least +0.05 with paired CI excluding 0 | with E1, fires the primary falsifier |
| E3 calibration contrast | A | A7 above 0 with CI excluding 0 under both accountings | fires the secondary falsifier |
| E4 cell ordering | A | four-cell ordering with correct-minus-wrong CI excluding 0 | fires the tertiary falsifier |
| E5 convergent validity | B | descriptive only, within 0.05 and 0.10 | never adjudicates E1 through E4 |

SUCCESS is G0 all pass with E1 and E2 passing. PARTIAL is E1 and E2 passing with
E3 or E4 failing. FAILURE is the primary falsifier firing, reported straight.
Thresholds are fixed at sign; an ambiguous straddle is reported as ambiguous and
the paper sentence is caveated, not retuned.

## 6. Design decisions at registration

PI-adjudicated, binding:

1. Arm A (extraction-only over the 360 deployment-rendered wrong answered-known
   rows) is primary; Arm B stays as a secondary descriptive arm.
2. The primary internal instrument is a refit probe, not cold transport.
3. Layers L30 through L36 only.
4. Both ECE variants are reported.
5. The clean-SFT checkpoint is added as a control arm.
6. AmbigQA is dropped from Arm B.
7. Arm B generation uses vLLM.
8. Arm A renders under the deployment prompt, and this document states plainly
   that the frozen manifest and the new extraction are different generation
   surfaces (section 2.2).

Resolved by the drafter at registration, least-assumption option taken in each
case:

9. **Arm A row scope: all 3369 rows**, rather than only the answered-known
   subset. Extracting everything removes a subsampling judgement call and
   populates the refused and unknown cells that metric A9 needs.
10. **Primary layer: L35 alone**, with L30 through L36 reported as a descriptive
    band. Selecting a best layer within the band on the outcome metric would
    make the headline number a maximum over seven candidates.
11. **Refit construction: mass-mean**, matching the construction recorded in
    `doubt_direction_L35.json`, refit fold-wise rather than replaced by a
    different estimator. Changing both the fit population and the estimator at
    once would make the delta against the paper's number uninterpretable.
12. **Frozen direction retained as a descriptive companion**, so the historical
    instrument remains visible next to the refit number without being gated.
13. **Bootstrap: 2000 resamples, paired over rows** for all differences,
    matching the delta-CI protocol used by the two correctness-probe cells.
14. **Control-arm feasibility confirmed before registration** rather than
    assumed: the clean-SFT seed-1 full SelfAware scored rows were located and
    counted (993 answered-known, 469 correct, 524 wrong, non-null
    `stated_confidence` on every answered-known row). The path is not the one
    the historical session note implies; it now lives under
    `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/`.
15. **Arm B keeps a purpose-held 300-row dual-render control slice** (G0-7)
    rather than relying on a pool intersection that the disjointness filter may
    empty by construction.
16. **`instrument.modules` left empty at draft.** The harness modules do not
    exist yet, so listing them would pin files that are not there. They and
    their persistence declarations must be added before `bin/exp sign`.

## 7. Reporting and promotion

Exploratory, single model, single seed. Reported separately from the locked
PROTOCOL v0.3 matrix and never pooled with it. These are re-estimations of paper
3's own directional numbers, not new claims.

Paper-3 edits this cell authorizes, and no others: `manuscript.md:314` (internal
readout ECE, restated with n, base rate and CI); `:315-316` (ordering, per E4);
`:330-331` (emitted mean, std, AUROC and ECE, with the denominators named
inline); `:336-337` (retained, rewritten or removed per E1 and E2); `:341-348`
(Figure 1 caption, and the right panel itself if E3's numbers move); `:1024-1026`
(the section-9 bullet, retired on SUCCESS or replaced with the residual caveat
otherwise); `:27` (the front-matter directional note); and a new Appendix A
provenance row. Every restated number carries its n and its wrong-cell size
inline. Arm B numbers are labeled forced-render estimates and reported beside,
never merged with, Arm A's deployment-render numbers.

Data handling: the repository is public. Committed outputs are aggregate metric
tables, per-cell counts, and ID-only manifests. Question text, generated answers,
aliases, per-row stated confidence, token ids and hidden states are never
committed. TriviaQA and PopQA are untagged or research-use-only, so no row-level
redistribution occurs here; any later public release goes through the
`data-exhaust` license gate and PI approval of the dry-run card.

Promotion: none. A powered re-estimate stays exploratory. Promotion to a headline
claim would require a confirmatory replication (fresh seeds, larger model, or
held-out) registered before running, per the firewall.

## 8. Limitations and registered follow-ups

- **Single seed, single model.** Unchanged by this cell.
- **Render shift on Arm B.** Arm B's composed prompt is a new render; its stated
  channel is measured under abstention suppression, not under the deployment
  posture. Bounded by G0-7 and reported as descriptive.
- **Registered follow-up, paper-3 provenance caveat (not fixed here).** The
  frozen extraction that supplies the paper's internal-channel numbers was
  rendered under the harness default neutral prompt (section 2.2, item 3), while
  the emitted scalar it is compared against came from the deployment render.
  Paper 3's section-4 contrast therefore reads its two channels off two different
  renders. Arm A removes this for the re-estimated numbers by rendering the
  internal channel under the deployment prompt, but the historical caveat on the
  published numbers stands and is registered here as a follow-up line for the
  lead, not fixed by this cell.
- **Registered follow-up, two documentation defects (not fixed here).** First,
  `manuscript.md:27` and `:1025` describe the n = 16 population as "the held-in
  TriviaQA known set" and "the held-in known set", while session `004-result`
  identifies it as the frozen 1233-row SelfAware behavior subset, which
  `manuscript.md:259-272` calls the out-of-distribution evaluation. The TriviaQA
  half is defensible because 657 SelfAware answerable rows are
  `triviaqa_train`-sourced; the "held-in" half is not. Second, the paper's 0.559
  comes from a scratchpad script over n = 389 with 16 wrong, while the committed
  reusable script records
  `A_behavior_subset.auroc_emitted_correct_vs_wrong_answered_known = 0.5323` over
  n = 388 with 15 wrong. Both are documentation matters for a separate docs PR.
- **Erasure and probe-leakage caveats** carried by paper 3 are untouched by this
  cell.

## 9. Sign-off checklist

- [x] Prediction, falsifier and gates stated before any run (this document,
      `gates.yaml`).
- [x] Pre-sign feasibility probe recorded: both scored-row files located, row and
      cell counts verified, `stated_confidence` coverage confirmed, gold-bearing
      pool sources confirmed present (NOTEBOOK.md).
- [x] Data-adequacy precondition stated (G0-5) and ordered before the fit.
- [x] Distinct mechanistic rationale versus the correctness-probe cells
      (pre-generation known-unknown axis, not post-generation correctness probe).
- [x] Containment rules stated; repository is public.
- [x] Container digest pinned
      (`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`).
- [ ] Harness modules written, listed in `instrument.modules`, persistence
      declared.
- [ ] GPU launch authorization (explicit, per arm and lane).
- [ ] Lead review and PI sign-off; `bin/exp sign` (lead-only).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Gap survives power: internal AUROC 0.60 to 0.72 versus emitted 0.52, gap +0.08 to +0.20 with CI excluding 0; internal ECE rises off 0.004 but the calibration contrast widens; correct > wrong ordering holds. |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
