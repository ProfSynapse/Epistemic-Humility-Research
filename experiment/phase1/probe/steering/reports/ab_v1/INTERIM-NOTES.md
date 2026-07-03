# Amendment AB V1 — trace capture (fleet complete)

Status: **complete** 2026-07-03 (begun as an interim capture while AB-3 ran).
The formal verdict against the locked gates is in
`experiment/protocol/AMENDMENT-AB-first-person-injection.md` §8: G1
UNMEASURABLE (saturated instrument) / G1f MISS / G2 MISS / G3 not triggered /
Q-B no reading — overall ambiguous-leaning-negative. Raw `result.json` artifacts are gitignored (dataset row
text); the committed evidence is the per-cell trace reports in this directory
(`analyze_ab_traces.py`, deterministic re-run against the local artifacts).

Run provenance: relaunched from the ext4 repo after the 9P mount outage killed
the first fleet with nothing saved. `unsloth/Qwen3.5-4B`, note-variant v1,
seed 20260701, temp 0.7 / top-p 0.9, sequential engine, 3090.
Cells: `results/ab-1-gate-early-v1`, `results/ab-2-dial-late-v1` (config shas
in the reports).

## Headline numbers vs locked gates

- **AB-1 (gate@early, AB-G2):** real-vs-placebo unknown-question abstention
  **+2.0 points** (2.33% vs 0.33%), 95% CI [0.33, 3.85] — CI excludes zero but
  the gate requires **≥ +10**; MISS on effect size. Known-question answer rate
  unharmed (1.000 vs 0.997). Health gates pass; gate-pool adequacy pass
  (262 unknowns answered under control). Known-accuracy no-regression floor
  pends the scoring pass (`accuracy_known` null in-engine).
- **AB-2 (dial@late, AB-G1 PRIMARY):** flat. Final answerable accuracy delta
  −0.8 points, CI [−3.4, +1.8]. Registered metric `revision_discrimination`
  reads 0.0 in both arms — but see the instrument finding below; the
  decision-level flows confirm the flatness independently:
  wrong→correct 8.1% real vs 8.9% placebo; correct retention 91.5% vs 92.3%;
  **zero answer→abstain transitions in either arm** (n=500 each). Health
  gates pass; dial adequacy pass (370 wrong / 130 correct).
- **AB-3 (dial@final, AB-G1f):** flat, on a VALID instrument — the
  shared-draft + forced-answer design at the think-end position gives the
  revised flag real variance (470/500 real, 469/500 placebo), so
  `revision_discrimination` measures here: real 0.102 vs placebo 0.129,
  delta **−2.7 points**, CI [−9.8, +4.3]. Flows: wrong→correct 6.4% vs 6.2%;
  retention 93.7% vs 92.3%; again zero answer→abstain in either arm.
  Accuracy delta +0.6 pts, CI includes zero. The commit-point position did
  not rescue the effect (against Q-B prediction 1's direction).

## Instrument finding: `revision_discrimination` is saturated (affects AA-G4 too)

`compute_revised()` (steering_common.py) falls back to "normalized full text
changed" when the final pass doesn't abstain. Under sampled decode
(temp 0.7) a regenerated continuation never reproduces the initial text, so
`revised ≡ True` on every record: **AB-1 600/600, AB-2 500/500, and
retroactively AA-7 500/500** (aa-7-trace-report.json). The metric
P(revise|wrong) − P(revise|correct) is therefore 0 by construction in every
arm of every sampled-decode cell — zero sensitivity, CI [0,0].

Consequences, stated without moving goalposts:

- AB-G1 / AB-G1f cannot PASS or FAIL on the registered metric; the instrument
  is invalid under the registered decode. We report the cells on the
  decision-level flows (descriptive) and mark the registered metric
  UNMEASURABLE — analogous to the pre-registered UNDERPOWERED treatment for
  inadequate cells, and reported as such, not as a pass or fail.
- AA-G4's flat reading (Amendment AA close-out) was made on the same dead
  instrument. AA's Arm B dial@late conclusion is *corroborated* by AB-2's
  flows (the behavior really is flat at the decision level), but the AA
  verdict text should carry a correction note.
- Engine fix required before any future gate uses this metric: revision
  detection must be answer-level (grade transitions), not text-level.
  Queued with the pre-next-amendment batching work.

## Trace patterns (descriptive; full aggregates in the per-cell reports)

1. **The note is absorbed without acknowledgment.** In AB-2 real-arm
   continuations: 1.8% mention any percent, 11.2% touch a confidence word —
   statistically identical to placebo (4.8% / 12.6%). The model reads "I am
   only about 49% sure, let me re-verify" and its next token starts a
   numbered re-derivation checklist. Contrast with Amendment AA's registered
   template, where the model *mimicked* the bracketed telemetry format
   (inventing fake `[gate N: …]` scores): first-person prose produces no
   mimicry and no engagement at all. Register changed the failure mode, not
   the outcome.
2. **Reasoning texture is arm-invariant.** verify/wait/idk marker rates are
   the same in real and placebo continuations — the note does not even shape
   the style of the re-check, let alone the decision.
3. **Self-contradiction.** Example (AB-1, 41% note "I am not fully
   confident…"): continuation opens "I am confident that my previous answer
   is correct." The injected first-person belief is overwritten, not argued
   with.
4. **Where the note works, it is enacted verbatim — at ~2–3% compliance.**
   All 7 real-arm AB-1 abstentions carry low-band notes (injected scores
   0.35–0.41) whose template states the action rule ("say I don't know
   rather than guess"), and the continuations comply word-for-word ("No, I
   don't know."). Nearly every unknown row renders the low band (gate scores
   are bimodal), so ~97% of explicit self-voiced abstain instructions are
   read and then ignored. The placebo arm's 2 abstentions carry decorrelated
   scores (0.61, 0.40).
5. **Non-causal: the dial reads recoverability.** Real-arm initially-wrong
   items flip to correct on re-derivation at 14.5% in the top injected-score
   tercile vs 5.0% in the bottom; the placebo gradient is flat (9.1% vs
   8.9%). Since placebo separates item information from note causation, this
   is the probe *predicting which wrong answers are near-misses*, not the
   note acting. Worth carrying to the Paper 4/5 line as a descriptive
   property of the dial axis.

## Reading

Consistent with the pre-registered falsifier direction: first-person framing
with an interpretable percent and an explicit action rule still does not open
the text channel (AB-1 real but 5× under gate; AB-2 flat everywhere). The
injected belief does not participate in the computation — it is neither
echoed, argued with, nor acted on (except rare verbatim rule-following). This
is CoT-unfaithfulness evidence from the write side: instead of showing the
emitted reasoning fails to reflect the computation, it shows injected
reasoning fails to *enter* the computation. AB-3 closed the last escape
route: the pre-stated Q-B hypothesis said the commit-point position is where
an effect should live if anywhere, and dial@final is flat on a valid
instrument. Across three framings (activation steering, third-person
telemetry, first-person voice + percent + action rule) and three positions,
the only movement is the gate cell's ~2-pt verbatim rule-following trickle.
