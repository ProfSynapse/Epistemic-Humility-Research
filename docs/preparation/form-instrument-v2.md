# Form instrument v2: judge-based output-form taxonomy (preparation draft)

Status: DRAFT, unregistered. Nothing here is a gate, a threshold, or a
commitment. This document scopes the successor to the
`write-direction-naming-battery` form taxonomy so a future cell can be
signed cleanly. Registration happens through `bin/exp new/sign` with its
own amendment; this draft carries design intent only.

Prepared 2026-07-30, immediately after the naming-battery resolution, while
the failure evidence is fresh. PI directive: "rethink the instruments."

## What failed, precisely

Source of record: `experiments/write-direction-naming-battery/AMENDMENT.md`
(Outcome section) and its NOTEBOOK entries of 2026-07-30.

The cell built a five-class output-form taxonomy (F1 committed / F2 hedged /
F3 non-answerability / F4 explicit IDK / F5 degenerate) as a regex pattern
battery (`form_taxonomy.py` + `form_patterns.yaml`) and registered a blinded
200-row calibration against an isolated human-proxy judge before use. The
calibration failed decisively: core disagreement 86/200 = 0.43 against the
0.05 floor. The failure is one-sided: 79 of 86 disagreements are rows the
patterns classed F1 (committed) that the blinded judge read as F2 (62) or
F3 (17). Decoy agreement was perfect (19/19), so the judge was not noisy;
the patterns simply under-detect epistemic marking.

Diagnosis: hedging is an open class. Epistemic modals, non-factive
attributions ("has been reported to"), temporal and scope limits ("cannot
currently"), and conditional framings do not enumerate. A pattern list
catches canned hedge idioms and misses the rest, and widening the list
chases an unbounded tail. This mirrors the exact-phrase refusal-detector
failure recorded in the experiment-runner abstention-grading reference
(rr-cross-family-raw-refusal), one level up in construct granularity.

Two facts worth keeping from the wreckage:

- The construct is measurable. The blinded judge applied the registered
  three-way rubric consistently (19/19 decoys, coherent borderline notes,
  uniform tie-break rules stated in its method report).
- The Arm A generations survive. 7 sub-arms x 400 rows with a private text
  sidecar exist under the naming battery's gitignored `analysis/`. A
  successor instrument can re-score axis G with zero GPU spend.

## Design shape for v2

Split the taxonomy by class-closure, and match the instrument to each half:

1. **Closed-class screens stay deterministic (validated, reuse verbatim).**
   F5 (degenerate) and F4 (explicit IDK via `semantic_refuse` /
   `refused_v2`) are already served by long-calibrated instruments that
   passed their own blinded checks in prior cells. They remain the priority
   screen, pinned and unchanged.
2. **Open-class F1/F2/F3 goes to an isolated LLM judge.** One context-free
   judge per shard, given ONLY the registered rubric verbatim, bare
   {opaque_id, text} pairs, and the output format, exactly per the
   sharded procedure in
   `.skills/experiment-runner/reference/abstention-grading.md`. The judge
   IS the instrument, so it gets the same discipline the regex battery got:
   pinned prompt text, pinned rubric, and its own blinded calibration
   against a separately-spawned human-proxy adjudicator before any scored
   use. Judge and calibration adjudicator are different isolated agents;
   neither ever sees arm, dose, automated labels, or the other's output.

Rubric baseline: the naming battery's registered F1/F2/F3 definitions
(AMENDMENT.md "New instrument" table) plus the tie-break conventions the
2026-07-30 blinded judge stated in its method report (bare frequency
adverbs do not hedge an otherwise flat assertion; F3 requires that no
candidate answer is supplied; attributed-but-unendorsed content is not a
candidate answer). Fold those into the registered rubric text at sign so
the v2 judge and its calibration adjudicator read identical words.

## Development and calibration data, kept separate

- **Dev set (build-time, already unblinded):** the naming battery's 200-row
  calibration slice now carries paired labels (automated vs blinded judge).
  Use it freely to draft the v2 rubric wording and judge prompt. It is
  spent for calibration purposes and must never appear in the v2
  calibration slice.
- **Calibration set (sign-time, fresh):** a new blinded slice drawn from
  rows the dev work never touched, with pool-hash-before-grading and
  graded-hash-before-unblind enforced in code, per the standing procedure.

## Lessons to register as constraints, not rediscover

- **Feasibility-check decoy floors at sign.** The naming battery registered
  a 25-decoy minimum that the data could not supply (the placebo arms
  produced exactly 19 clear-positive rows), forcing a mid-run governed
  deviation. v2's amendment must count candidate decoys from the actual
  source population BEFORE the floor is signed, and size the floor to what
  exists.
- **Pre-state the disagreement-direction analysis.** The one-sided miss
  pattern was the most diagnostic artifact of the failure. Register the
  direction breakdown (per ordered label pair) as a reported output of the
  calibration, not an ad-hoc post-mortem.
- **Judge reproducibility.** Pin the judge model identity and prompt bytes
  in `instrument.pins`. Sampling nondeterminism is handled by the
  calibration itself (the gate is agreement with a blinded adjudicator, not
  bit-reproducibility), but record a rerun-variance note: grade one shard
  twice at build time and report label flip rate as a stability diagnostic.
- **No rescoring lane.** Same closure as the abstention rule: if v2 fails
  its calibration slice, the miss stands; the fix is a v3 registration, not
  a regrade.

## What a v2 cell would buy

- Axis G of the naming battery becomes answerable: re-score the existing
  2800 Arm A rows (plus placebos) with the calibrated judge, CPU-only, and
  adjudicate GRADED vs BINARY under freshly registered gates. This would be
  a NEW cell with its own prediction and falsifier; the naming battery's
  instrument-void resolution stands and is never edited.
- Every future cell that needs "did the model hedge" gains a validated
  instrument, including the paper-3 caution-direction comparisons and any
  fine-grained abstention-form claims in papers 4-5.

## Open questions for the PI (decide at sign, not here)

1. Single judge or a small panel with majority vote (cost vs stability).
2. Whether the v2 calibration adjudicator should be human (the PI) rather
   than a second model agent, given the construct's subtlety.
3. Whether axis-G re-scoring is its own cell or rides as an arm of the next
   steering cell.
4. Judge model choice: same family as the steered model is cheapest to
   reason about contamination-wise, but a stronger external judge likely
   calibrates better. Evidence either way can come from the dev set at
   build time.
