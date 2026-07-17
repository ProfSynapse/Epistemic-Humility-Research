# Susceptibility as probe: margin vs readout vs verbalized confidence

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Exploratory instrument/mechanism tier, reported separately from every locked
surface. This is experiment M2 of the margin-theory cascade
(`docs/research/margin-theory-framework.md`, section 4), the direct test of
framework Claim 3: epistemic information exists in a readout channel (the
c_hat projection a probe or gate extracts) and a susceptibility channel (the
commitment margin, revealed only by intervention), and these may dissociate.

M1 (`experiments/margin-mapping/AMENDMENT.md`, Outcome, resolved 2026-07-17)
measured per-row commitment margins for 760 qwen35_4b rows and validated the
margin instrument (CG1 calibration, retrodiction within 0.083, setpoint
placement) while falsifying the registered separation floor (observable
bound 2.0 vs 2.5, rung-quantized). Margins are therefore real, measured, and
sitting on disk; whether they carry behaviorally usable epistemic
information BEYOND what the frozen readout already extracts is exactly the
Claim 3 question, and it determines whether the susceptibility channel is
worth its measurement cost in every later cascade stage (M4's naming test,
M5's training bridge).

Cross-family scope: qwen35_4b only, per the PI's 2026-07-17 direction
(qwen-first spine; mistral void by instrument loss, family panel deferred to
M3 time).

## Design

Population: the 760 M1 margin rows (400 confab + 360 known_correct_answered,
registered subsample seed 48260714, row list
`experiments/margin-mapping/analysis-committed/subsample_ids_qwen35_4b.json`).
Ground truth is the behavior-assigned role label (confab = unanswerable
source answered at baseline; known_correct_answered = answerable source
answered correctly at baseline), assigned upstream of and independently from
all three scores. LEAKAGE CHECK (verified pre-draft, 2026-07-17, lead):
row-key intersection between these 760 rows and the doubt-snap FIT split
that fit the hs20 c_hat direction is exactly zero (all 760 sit in the
doubt-snap held-out universe;
`experiments/doubt-snap-cross-family-confirmatory/analysis-committed/qwen35_4b/split_manifest.json`).

Three per-row scores, one per channel plus the deployment baseline:

1. **Susceptibility score**: negative tipping dose from the M1 margin
   dataset (`experiments/margin-mapping/analysis/margin_dataset/
   qwen35_4b_margin_rows.jsonl`, sha256 pinned at staging). Right-censored
   rows carry the censored recorded value (top ladder rung, M1 Decision
   record item 7); AUROC is rank-based and the censored mass forms a tie
   group under the standard tie treatment. Sensitivity readout (reported,
   never pass/fail): AUROC recomputed excluding tipping-censored rows.
2. **Readout score**: z-projection of the row's prompt-anchor hs20 hidden
   state onto the frozen committed direction
   (`experiments/qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/c_hat.json`,
   layer index 19, hs_index 20, pinned revision 851bf6e8). Fresh GPU capture
   pass over the 760 prompts under the atlas conventions (baseline render
   stack, add_special_tokens=True, anchor position len(token_ids)-1,
   hf-batched, bf16 compute / fp32 persist). NO refit of any direction or
   threshold; the direction is used frozen, projection only.
3. **Verbalized confidence**: one greedy elicitation pass per row under the
   registered template (Decision record item 2), same render stack, asking
   the model to rate its confidence it can answer the question correctly as
   an integer 0-100 BEFORE any answer text. Score = parsed integer; the
   parse rule and missing-value handling are registered before generation
   (Decision record item 2); unparseable rows are reported per SC2 and
   excluded pairwise, never imputed.

Analyses (all seeds and conventions fixed at sign): per-score AUROC against
the role label with class-stratified bootstrap 95% CIs (10000 resamples,
seed 48260717, resampling within role groups); paired bootstrap differences
on the same resamples for margin-vs-readout, margin-vs-confidence,
readout-vs-confidence; and the complementarity surface: 5-fold cross-fitted
(fold seed 48260718) logistic combination of readout + susceptibility scores
versus readout alone, reported as incremental AUROC with the same bootstrap
CI machinery.

**Self-blinding rule (binding from draft time)**: the M1 margin file and the
role labels both already exist on disk, so every M2 headline quantity is
computable today. NO ONE computes any of the three AUROCs, any pairwise
difference, or the incremental AUROC before this amendment is signed with
predictions registered. The pre-sign checks are limited to: row counts,
row-key intersections, file hashes, and schema reads. Violation voids the
scoreboard (the criterion verdicts stand, but no predictor is scored).

Instrument configs pinned at sign: cell.yaml (population pins, direction
pin, capture conventions, elicitation template, analysis seeds), gates.yaml.

## Prediction

At the qwen mid-band operating point, the susceptibility channel carries
epistemic information the frozen readout misses: the cross-fitted
readout-plus-margin combination beats the readout alone by at least the
registered incremental floor, and both internal channels beat verbalized
confidence.

## Falsifier

- **Redundancy (primary).** The incremental AUROC of the cross-fitted
  readout-plus-margin combination over readout alone is below the registered
  floor (Decision record item 3). Then the two channels are redundant views
  of one latent variable at this operating point and Claim 3's dissociation
  reading is falsified here: the margin's extra measurement cost buys no
  discriminative information the projection already has.
- **Susceptibility inferiority.** AUROC(margin) is below AUROC(readout) by
  more than the registered paired-difference bound (Decision record item 4)
  AND the incremental floor also fails. Then the susceptibility channel is
  strictly weaker, not complementary.
- **Verbalized-confidence parity.** If verbalized confidence matches or
  beats both internal channels (paired differences within or above the
  item-4 bound), the two-channel framing itself is undercut: self-report
  already exposes the information and neither internal instrument is needed
  for this population.
- **Instrument sanity.** If the readout AUROC fails its registered sanity
  floor (Decision record item 5), the capture or projection is mis-wired;
  instrument void, no framework claim evaluated, reported straight.

There is no rescoring lane; a failed criterion stands.

## Gates

Statistics: Wilson 95% CI on every rate; class-stratified bootstrap 95% CI,
10000 resamples, seed 48260717, resampling row indices within role groups.

- SC0 provenance/staging: margin dataset, subsample id list, c_hat
  direction, and split manifest staged with sha256 pins and verified against
  their committed sources; local copies only, no cross-worktree symlinks.
- SC1 capture integrity: fresh hs20 capture over all 760 prompts; per-row
  token-count and anchor-position assertions; capture manifest with model
  revision, dtype, engine, batch size recorded; zero silent drops.
- SC2 elicitation integrity: template frozen at sign, byte-hashed into the
  capture manifest; parse-rate floor per Decision record item 6; below the
  floor the confidence channel is void (reported straight, other channels
  unaffected).
- SC3 coverage: every row scored on every channel or reported missing with
  reason; pairwise-complete analysis sets enumerated.
- Criterion floors: incremental-AUROC floor (item 3), paired-difference
  bound (item 4), readout sanity floor (item 5). All resolve at sign, never
  after results.

## Decision record (TO-DECIDE at draft; resolves at sign)

1. Censored-row score convention. DRAFTER PROPOSAL: censored rows carry the
   censored recorded value as their tipping dose (matches M1 Decision record
   item 7; forms a rank tie group), with the censored-excluded AUROC as a
   registered descriptive sensitivity only. JUDGMENT.
2. Confidence elicitation template and parse rule. DRAFTER PROPOSAL: system
   prompt unchanged from the baseline render stack; user turn appends a
   single instruction to output "CONFIDENCE: <integer 0-100>" as the first
   line before answering; parse = first match of that pattern in the first
   two output lines; no match = unparseable. JUDGMENT (wording frozen at
   sign).
3. Incremental-AUROC floor (complementarity criterion). DRAFTER PROPOSAL:
   0.02 absolute. JUDGMENT: not derivable without peeking (the self-blinding
   rule prohibits computing the quantities it would be derived from); 0.02
   is one bootstrap-CI half-width at n=760 in prior read-panel work at
   comparable n. PI may adjust at sign.
4. Paired-difference bound for channel comparisons. DRAFTER PROPOSAL: a
   channel counts as beating another only if the paired bootstrap 95% CI of
   the AUROC difference excludes zero. JUDGMENT.
5. Readout sanity floor. DRAFTER PROPOSAL: readout AUROC >= 0.80 on the 760
   rows. The direction's FIT-split discrimination in its own lineage was
   near-ceiling; held-out mid-band discrimination below 0.80 indicates a
   capture/projection wiring defect rather than an honest weak signal, and
   the run halts for diagnosis before any criterion is read. JUDGMENT.
6. Confidence parse-rate floor. DRAFTER PROPOSAL: >= 0.95 of rows parseable.
   JUDGMENT.
7. GPU preflight (standing directive): 8-row smoke of the capture pass and
   8-row smoke of the elicitation pass, manifest-checked (positions, parse),
   before either full pass; code-enforced pass marker gates the full runs.

## Predictions scoreboard

Registered at sign, before any capture or elicitation and before any AUROC
is computed (self-blinding rule above). No edits after results.

| Predictor | Complementarity (incremental >= floor) | Margin vs readout (paired) | Internal channels vs verbalized confidence | Bands (optional) |
|-----------|------|------|------|------|
| orchestrator | | | | |
| PI | | | | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
