# Margin theory of epistemic state: a framework for the next experiment series

Status: working framework, drafted 2026-07-16 after the resolution of
`experiments/gate-contribution-factorial/` (gate axis falsified, both
families). This is a research-direction document, not a governed claims
surface. Every experimental fact below cites the governed doc and section it
was read from; nothing here supersedes any signed Outcome. Registered claims
come only from amendments; this document exists to generate them.

## 1. The three anchor results

The framework is built to explain three registered or governed results that
initially look contradictory:

1. **At Qwen3-4B / L34 / dose 200, the write is non-selective and the gate is
   essential.** Ungated dose-matched dosing damages 60.1% of held-out
   known-correct rows versus 3.1% gated (57.0pp, McNemar p = 4.2e-43), while
   the gate costs only 4.3pp of confab conversion
   (`experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`, Outcome,
   one-sentence verdict and H4-G1/H4-G2; resolved 2026-07-13).
2. **At Qwen3.5-4B / hs20 / dose_abs 12.608, the write is content-selective
   in-sample and the gate is a deployment limiter.** In the permuted-gate
   control, randomly selected dosed confabs refuse at 0.669 vs the gated
   arm's 0.684, while directly dosed knowns refuse at only 0.056; the gate's
   operational role is limiting how many knowns get dosed (13 vs 197 at
   hs20), not creating the refusal selectivity
   (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md`, Outcome note 3;
   in-sample FIT characterization by that doc's own scope note 2).
3. **At the mid-band operating points of BOTH families, held out and
   pre-registered, the gate's selectivity increment is real but sub-floor.**
   Gap_Sel(c_hat) 0.148 qwen (CI [0.119, 0.177]) and 0.129 mistral (CI
   [0.103, 0.156]) against a registered 0.20 floor; cost protection 0.008 /
   0.034 against a 0.10 floor; permuted-gate confab abstention 0.550 / 0.600
   vs baselines 0.083 / 0.282; S1 direction-specificity passes qwen (ratio
   7.27, sign-opposed) and fails mistral (ratio 2.03)
   (`experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome;
   resolved 2026-07-16, status falsified).

Result 1's own Binding scope statement 2 already states the reconciliation:
"the write's content-selectivity is operating-point-dependent"
(`ungated-vs-gated-dose-matched/AMENDMENT.md`, Outcome). The framework's job
is to give that dependence a mechanism and make it quantitatively
predictive.

## 2. The framework

### Claim 1: knowledge is encoded as distance to an abstention boundary

For each (model, question) pair there is an internal abstention boundary,
and the row's epistemic status is expressed in its **commitment margin**:
the minimum perturbation dose that flips the row's behavior to abstention.
Confabulation-prone rows have short margins; well-supported known rows have
long ones. The factorial's central observation, identical dose with opposite
outcomes by row type, is the signature of this encoding.

### Claim 2: dose regime determines who supplies selectivity

Selectivity-without-gating exists exactly when the dose lands in the gap
between the confab margin distribution and the known margin distribution.

- **Mid-band regime** (dose above typical confab margins, below typical
  known margins): the write self-sorts; the gate contributes only a modest
  increment plus cost concentration. Anchor results 2 and 3.
- **Overdrive regime** (dose above typical known margins): everything
  crosses, or degrades; the gate becomes the sole source of selectivity.
  Anchor result 1 (dose 200 damaged 60.1% of knowns, decomposed in that
  Outcome as 55.8pp false refusal, 3.9pp answered-wrong, 0.4pp degenerate).

This makes the apparent contradiction between anchors 1 and 3 a predicted
consequence of one geometry measured at two doses. The quantitative test:
margin distributions measured per row should retrodict all three anchors
from their operating points alone.

### Claim 3: epistemic information exists in two channels that can dissociate

- **Readout channel**: what a linear probe or gate extracts (the c_hat
  projection).
- **Susceptibility channel**: the margin, revealed only by intervention.

The factorial showed the susceptibility channel carries most of the
behaviorally usable selectivity at mid-band. Open question: are the two
channels redundant views of one latent variable, or does the margin carry
information the readout misses (or vice versa)? This is directly testable
(experiment M2 below).

### Claim 4: boundary anisotropy is substrate-dependent

On qwen, short confab margins are direction-specific: random directions at
matched magnitude produce about 0 refusal until they destroy well-formedness
(`qwen35-4b-midband-doubt-snap/AMENDMENT.md`, Outcome note 4), and the
factorial's S1 passes at ratio 7.27. On mistral, generic pushes recruit
abstention (S1 fails at 2.03). Substrates therefore differ in how
directionally organized their epistemic geometry is. This is a measurable
family-level property (experiment M3), not a nuisance.

## 3. Vocabulary: what we rename and why

The factorial showed our names were carrying argumentative weight the
evidence had not earned. "The doubt gate supplies selectivity" felt plausible
partly because we called the readout "doubt"; the permuted-gate control would
have felt urgent much earlier under a neutral name. Names are hypotheses,
and these were partially falsified.

| Old name | New name | Commitment |
|----------|----------|------------|
| doubt direction | known-unknown direction (symbol c_hat unchanged) | how it was fit; no mental-state attribution |
| doubt gate | KU readout gate | a classifier threshold used for deployment targeting |
| caution write | boundary push (dosed write) | a displacement toward an existing boundary, not an installed disposition |
| confab propensity | split: baseline confab rate vs commitment margin | behavior without intervention vs fragility under it |
| (unnamed) | boundary anisotropy | whether short margins are direction-specific (qwen) or generic (mistral) |

Rules of use: governed docs keep their historical names; this table governs
new prose, new amendments, and the paper 5 revision, with an explicit
old-to-new mapping where both appear. KG node ids are never renamed; new
aliases and caveat prose are added instead.

**Earnability criterion for mentalistic names.** A name like "doubt" is
earned for an activation when it (a) tracks actual ignorance, (b) drives
abstention when amplified, (c) does so direction-specifically, and (d)
responds to evidence the way doubt should: supplying the true answer
in-context should collapse the projection on that row and lengthen its
margin. Qwen satisfies (a) through (c). Criterion (d) was tested by the M4
arc (2026-07-18) and is NOT earned on the world-known error class: the named
KUQ direction does not fire there at all (primary transfer void, out of
domain, with a genuine population reversal; it reads as unanswerability
recognition), the native refit shows only a weak evidence-specific,
sub-floor, behaviorally inert projection response, and the constructive
search for a specific evidence axis recovered covariance-generic
retrieval-family geometry instead. Sources:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` and
`experiments/evidence-response-direction-search/AMENDMENT.md` (Outcome
sections). The mentalistic name stays retired program-wide; the section 3
table's replacements are now backed by a completed (d) adjudication, not
only by prudence. Mistral fails (c), so mentalistic naming was retired for
mistral independent of (d).

## 4. The experiment cascade

Ordered cheap-first; each amendment gets its own branch, pre-stated
prediction, falsifier, and floors per the standing instrument rules. The
margin-mapping dataset (M1) feeds every later stage.

Scorecard as of 2026-07-18 (verdict sentences mirrored from each cell's
AMENDMENT.md, the sole source of truth): M1 resolved, Claim 1 falsified as
registered at the qwen mid-band operating point (observable separation bound
2.0 vs floor 2.5) though margins are mechanistically real and retrodiction
holds within 0.083; the M1b fine-ladder retest resolved the miss as
instrument-resolution-limited, so the falsification stands without a clean
mechanistic reading. M2 resolved, channels redundant as registered
(incremental AUROC 0.0154 vs floor 0.02, readout alone 0.982). M4 resolved
across two cells, criterion (d) not earned (section 3 above). M3, M5, M6
pending; the family memo precedes M3.

- **M1. Margin mapping (keystone).** Per-row dose staircase along c_hat at
  the mid-band operating points; deliverable is each row's tipping dose
  (commitment margin) for the existing confab and known pools, both
  families. Predictions to register: (i) margin distributions for confab vs
  known rows separate with a gap containing the current setpoints; (ii) the
  measured distributions retrodict the three anchor results from their doses
  alone, including the H4 overdrive result via the known-margin tail.
  Local 3090, reuses frozen directions, pools, and the wide instrument.
- **M2. Susceptibility as probe.** AUROC of inverse margin vs the trained
  probe score vs verbalized confidence, predicting ground-truth
  confabulation on held-out rows. Adjudicates whether the two channels of
  Claim 3 are redundant or complementary.
- **M3. Anisotropy panel.** Margins along K vetted random directions
  (census seed lineage) plus c_hat, per family; deliverable is an anisotropy
  index. Prediction: qwen high, mistral low. The llama retest (backlog task
  7) becomes the third family data point.
- **M4. Evidence-responsiveness (the naming test).** Supply the true answer
  in-context; measure the c_hat projection shift and the margin shift on
  the same rows. Adjudicates earnability criterion (d).
- **M5. Training bridge.** Apply the M1 margin instrument to the Phase 1
  abstention-trained checkpoints (SFT/DPO/KTO): does training shrink
  unknown-row margins, or move the boundary? Unifies the training and
  steering halves of the program under one geometric account.
- **M6. Scale.** Margin separation vs model size (backlog task 8 absorbs
  this framing).

## 5. Consequences for paper 5

The gated-dosing selectivity claims must be rewritten as
operating-point-dependent: gate-supplied in the overdrive regime (H4,
registered), write-supplied at mid-band (factorial, registered), with the
gate's mid-band role reduced to a modest increment plus cost governance
(the gate holds known false refusal at 0.042 / 0.005 vs the permuted 0.050 /
0.039, which matters against the registered 0.05 ceiling). The rewrite
adopts the section 3 vocabulary with an old-to-new mapping. No locked
verdict moves; the affected text is interpretation, not registered numbers.

## 6. Prerequisites and hygiene

- Governed docs read for this framework: the three anchor Outcomes cited in
  section 1 (read 2026-07-16). Any future claim about them re-reads the doc.
- The confirmatory-replication option named in the factorial Outcome (a
  design point where the gate axis could pass its floors) is deprioritized:
  two families with tight sub-floor CIs suggest the increment is genuinely
  modest, and M1 will measure the thing directly instead of re-testing the
  threshold.
- KG updates accompanying this note: commitment-margin and
  boundary-anisotropy term nodes, an operating-point-dependence synthesis
  mechanism linking the three anchors, and naming-caveat aliases on the
  existing doubt/caution atoms. Node ids are additive only.
