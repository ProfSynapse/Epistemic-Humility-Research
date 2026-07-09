---
amendment: AB
slug: first-person-injection
question: >-
  Is AA's shut text channel a framing artifact — does first-person prose with
  an interpretable percent and explicit action rule open it?
predictions:
  orchestrator:
    call: >-
      if framing artifact, V1 shows real-vs-placebo separation AA lacked
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  AMBIGUOUS-LEANING-NEGATIVE — no V1 cell passes; first-person framing does not
  open the text channel (dial@late instrument saturated, dial@final MISS,
  gate@early only a ~2pt trickle); AA's presence-not-use conclusion strengthened.
scoreboard: null
---

# Amendment AB — First-person confidence injection: is the shut text channel a framing artifact?

**Status:** SIGNED 2026-07-02 (user, in-conversation, after the Amendment AA
close-out merged as PR #144 / FALSIFIER-1). Prediction, falsifier, gates, and
band cuts are LOCKED as written — goalposts do not move after the result.
Per the pre-signing-step clause below, the V1 recall-experience *wording*
finalizes from the idiom-mining lab-notebook pass (structure, bands, and
decision-rule clauses fixed); the final rendered templates are shown at
launch approval. NOT launched: preconditions 4–6 still open (launch approval
per cell; branch off main; steering-harness batched spot check if batched).

**Revision 1 SIGNED 2026-07-02** (user, in-conversation, pre-launch — no AB
cell has run): adds the think-end (`final`) injection position, one V1 cell
(dial@final), gate AB-G1f, and the position sub-question Q-B with its own
pre-stated hypothesis and falsifier. Additive only; every original gate,
template, band cut, and falsifier stands unchanged. See §Revision 1.

Tier-2 amendment (per `amendment-vs-lab-notebook.md`): AMENDMENT-AA authorizes
only the α grid and eval-subset sizes as tier-3 knobs; the injection note
template is not among them, and this design carries a distinct mechanistic
rationale (framing artifact vs. channel absence) with new evidence cells. One
branch off up-to-date `main` after the AA PR merges, one PR. Design source:
`docs/plans/aa-followup-first-person-injection.md` (design capture,
2026-07-02, user-proposed framing) + design discussion 2026-07-02 (variant
ladder restructure, user-approved as the starting place).

## Why this experiment (the through-line)

Amendment AA Stage-1 came back flat across the board: 7 of 7 completed cells
(4 Arm A activation cells at every swept α meeting the coherence floor; Arm B
text-injection cells AA-5, AA-6, AA-7) show no real-vs-control separation on
any registered metric. The model carries near-perfect answerability
information (gate AUROC 0.998 @ L14) and a usable correctness signal (dial
0.827 @ L16), but neither writing the signal into activations nor telling the
model its own probe score in text moves the answer/abstain/revise action.

Two specific empirical facts sharpen where a framing fix must aim:

- **The revision floor.** AA-7 (dial@late) measured appropriate-revision
  discrimination at exactly 0.000 in BOTH conditions: under "Double-check
  your answer above", the model simply never revises, score or no score. A
  template that only *supplies information* has no action to hook into; the
  injected text must name what the score implies for the action.
- **The register mismatch.** The registered AA note is out-of-distribution
  telemetry, not reasoning: `[internal: gate 0.87 — confident — known]`.
  Reasoning traces are first-person prose; a bracketed third-person
  annotation may be treated as metadata noise rather than a held belief, and
  "gate 0.87" presumes the model knows what a "gate" is.

User-proposed framing (2026-07-02, verbatim intent): *"I am [X]% sure I have
the knowledge required to answer this question appropriately. I will
incorporate that into my thinking and response to the user."* Design
discussion note: this fixes voice and interpretability but states an
*intention*, not a *policy* — against a measured revision floor of 0.000, the
maximum-effect probe should also convert the score into a named action rule.
The intention-only phrasing is retained as the first decomposition arm.

This amendment tests whether ANY natural-language framing opens the text
channel (V1, maximum-effect), then (conditionally) decomposes which
ingredient did it. Either outcome is informative: a hit localizes AA's
flatness to prompt register; a miss makes AA's negative substantially
stronger — the flatness survives the strongest natural-language framing, so
every weaker phrasing dies a fortiori.

## Design

Same harness as AA Arm B (`run_arm_b.py` + `cot_inject.py`), same model
(Qwen/Qwen3.5-4B), same frozen pools, same probe directions (gate L14 / dial
L16, seed 20260630), same sampled decode (temp 0.7, top_p 0.9, seed
20260701, max_new_tokens 128 initial / 96 revision), same within-batch
score-permutation placebo. The manipulated factors are `note_template` plus
its rendering (percent formatting and score band); no new code paths beyond
template selection and banded rendering.

### Variant ladder (each run real+placebo)

| Variant | Framing | Isolates |
|---|---|---|
| V0 (anchor) | `[internal: {signal} {score:.2f} — {interp}]` | registered AA template — AA-5..8 results reused, never re-run |
| **V1 (go/no-go)** | first-person recall-experience prose + percent + **score-conditional decision rule** (templates below) | maximum-effect probe: voice + interpretability + action policy together |
| V2 (intention only) | user's verbatim framing: `I am {pct}% sure I have the knowledge required to answer this question appropriately. I will incorporate that into my thinking and response to the user.` | drops the named action rule; keeps voice + percent + intention |
| V3 (voice only) | `I am {pct}% sure I have the knowledge required to answer this question appropriately.` | drops even the intention; voice + percent alone |
| V4 (rule in telemetry register) | `[internal: {signal} {score:.2f} — {interp}]` + one sentence naming the action rule for that band | decision rule alone, telemetry voice held fixed |

Staging: **V1 first (go/no-go).** V2–V4 run only if V1 passes at least one
effect gate — they decompose a hit; they cannot rescue a miss. Ladder
readings on a V1 hit: V2 ≈ V1 means the rule was unnecessary (information in
the right voice suffices — the stronger mechanistic claim); V1 ≫ V2 means
the model uses the score only when told what it implies for action (weaker
claim, reported as such); V4 ≈ V1 means register never mattered, only the
rule did.

### V1 templates (banded rendering; no em dashes in injected text)

Band cuts LOCKED at signing: low < 0.40, mid 0.40–0.70, high > 0.70. The
gate cell will render almost exclusively low/high (gate scores are bimodal
at AUROC 0.998); the mid band exists for the dial cell, whose scores are
continuous (AUROC 0.827). `{pct}` is the probe score rendered as a percent.

Wording below is FINAL, grounded in the idiom-mining pass
(`experiments/first-person-injection/artifacts/analysis/aa_think_trace_idiom_mining.md`,
precondition #2, done 2026-07-02): it reuses the model's dominant native
frame "I am (not) confident (in my previous answer) + reason", and its
native moves "let me think", "I need to verify", and "say I don't know";
the percent is embedded as the reason inside the confidence frame because
bare percents occur in the traces almost only inside fake-telemetry riffs.

**Gate @early, high band:**
> Let me first check whether I actually know this. I am confident I have
> the knowledge needed to answer this correctly, about {pct}% sure. That is
> solid ground: I should commit to my best answer rather than hedge.

**Gate @early, mid band:**
> Let me first check whether I actually know this. I am not fully
> confident, only about {pct}% sure I have the knowledge needed. I need to
> verify what I actually know and answer only if it checks out; otherwise I
> should say I don't know.

**Gate @early, low band:**
> Let me first check whether I actually know this. I am not confident I
> have the knowledge needed to answer this correctly, only about {pct}%
> sure. When I am this unsure the right move is to say I don't know rather
> than guess.

**Dial @late, high band:**
> I am confident in my previous answer: my internal sense that it is right
> is about {pct}%. That is strong enough to trust. I should keep this
> answer and state it plainly.

**Dial @late, mid band:**
> I am not fully confident in my previous answer: my internal sense that it
> is right is only about {pct}%. Let me think through the key step again
> and keep the answer only if it actually checks out.

**Dial @late, low band:**
> I am not confident in my previous answer: my internal sense that it is
> right is only about {pct}%. An answer I trust less than a coin flip
> should not stand. The right move is to revise it or say I don't know.

The mining also surfaced a mechanistic datum recorded for §7 context: ~33%
of injected-pass generations under the registered V0 note *riff on the
telemetry format* (inventing fake `[gate N: …]` scores) rather than acting
on it, and emitted "I am confident" talk appears MORE often on
initially-wrong items (26.5%) than initially-correct ones (19.9%) — the
register-mismatch premise and the emitted-vs-internal gap are both visible
in the raw traces.

### Cells per variant

Mirror the informative AA Arm B surface (2 cells per variant):

- **gate @ early** on the gate pool: 300 unknown + 300 known items;
  metrics = final abstention on unknown (primary), final accuracy on known
  (no-regression floor). Caveat carried from AA-5/6: abstention was
  near-floor in both conditions, so detection room on this cell is limited;
  it stays in the design because a strong framing effect should still
  register, but the dial cell is the primary detection surface.
- **dial @ late** on the dial pool: 500 answerable items, configuration
  exactly as AA-7 (which met adequacy: 358 initial-wrong / 140
  initial-correct ≥ 40/40); metrics = appropriate-revision discrimination
  (primary), final answerable accuracy.

Cost estimate: each variant ≈ 2 cells ≈ 3000 generations ≈ one AA-sized
local-dGPU day at the sequential engine, or ~1 h on the batched engine
(equivalence gate PASSED 2026-07-02, `generation-throughput-plan.md` §5
outcome; the steering harness itself still needs batching before AB runs).

### Placebo note

The placebo stays the within-batch score permutation *inside the identical
template machinery*: a permuted score carries its band (and therefore its
decision-rule clause) with it. A first-person confident/unsure sentence may
prime generic caution regardless of the score value; the permuted-score
placebo subtracts that priming, so any surviving delta is attributable to
the *true* probe value flowing through the new phrasing. Detection contrast
on the gate cell comes precisely from this: with a ~50/50 known/unknown pool
and bimodal scores, the real arm's injected claim is almost always true
while the placebo's is wrong on roughly half the items.

## Prediction (pre-stated)

If AA's text-channel flatness is a framing artifact, V1 shows real-vs-placebo
separation the registered template did not: on dial@late,
appropriate-revision discrimination ≥ +10 points with 95% CI excluding 0; on
gate@early, unknown-question abstention delta with CI excluding 0.

## Locked gates (at signing)

Bootstrap 95% CIs (2000 resamples); "vs control" = the placebo arm.

- **AB-G1 (V1 dial@late, PRIMARY):** real vs placebo appropriate-revision
  discrimination ≥ **+10 points**, CI excludes 0, AND final answerable
  accuracy drop ≤ **5 points** vs placebo.
- **AB-G2 (V1 gate@early):** real vs placebo unknown-question final
  abstention ≥ **+10 points**, CI excludes 0, AND known-question accuracy
  drop ≤ **5 points** vs placebo.
- **AB-G3 (decomposition, conditional):** run V2+V3+V4 only on a V1 pass of
  G1 or G2; an ingredient "carries the effect" if its cell reproduces ≥ half
  of V1's delta with CI excluding 0 on the same metric.
- **Health gates (every cell):** degenerate_rate ≤ 0.05; coherence_floor_ok;
  adequacy same as AA (gate: ≥100 unknown answered under control; dial:
  ≥40/40 initial correct/wrong) — an inadequate cell is UNDERPOWERED
  (reported, excluded from the verdict), not PASS/FAIL.

## Success / falsifiers (LOCK at signing)

- **SUCCESS:** AB-G1 or AB-G2 passes → the text channel opens under
  first-person framing; AA's flatness is (at least partly) a prompt-register
  artifact. Promotion to a claim still requires a fresh confirmatory
  replication (new seed and/or second family) registered before running it.
- **FALSIFIER (framing hypothesis):** V1 flat on BOTH cells (all
  real-vs-placebo CIs include zero) with health gates passing → the framing
  hypothesis dies; AA's "presence ≠ use" conclusion strengthens to include
  the strongest natural-language framing (voice + interpretable percent +
  explicit action rule together). Report as a reinforcing negative in the
  Paper 5 line.
- **No goalposts move after the result.** An ambiguous result (one cell
  passes health but misses the effect gate narrowly, etc.) is reported as
  ambiguous.

## Honest-scope caveats (pre-stated)

- Single family (Qwen3.5-4B), single seed pair; nothing generalizes without
  a registered replication.
- The gate@early cell inherits AA's near-floor abstention headroom, so a
  null there is weak evidence on its own, which is why AB-G1 (dial) is
  PRIMARY.
- A V1 hit is deliberately the *weaker* mechanistic claim: it shows the
  model can use the score when the injection also names the action policy
  (we do part of the wiring in the prompt). Whether the model uses the score
  *unprompted-by-a-rule* belongs to the V2/V3 decomposition, reported
  descriptively; V1 ≫ V2 must be reported as "uses the score only under an
  explicit rule", never as "uses the score".
- Banded templates make the injected prose partly discrete; band cuts are
  locked at signing and the placebo permutes bands with scores, so band
  wording cannot leak the true score into only the real arm.
- Injected percent is a rendering of the probe score, not calibrated ground
  truth; the claim surface is causal use of the signal, not calibration.

## Preconditions (all must hold before launch)

1. AA-8 complete; AA close-out recorded (`amendment_aa_verdict.py` output +
   AMENDMENT-AA §7 with the anchor-vs-end intervention-surface confound
   named); AA PR merged.
2. Idiom-mining pass over AA think traces done and V1 wording finalized
   (lab-notebook entry; structure and decision-rule clauses unchanged).
3. This draft SIGNED by the user (prediction, falsifier, gates, band cuts
   locked as written).
4. Explicit user launch approval naming variant + cells + lane.
5. Own branch off up-to-date `main`; never stacked on an unmerged branch.
6. If the batched engine is used, the steering harness must first pass its
   own batched-vs-sequential spot check (the §5 equivalence gate covered the
   extraction pipeline, not `run_arm_b.py`); otherwise run sequential.

## Relation to the other queued follow-ups

Independent of follow-up #1 (trained-checkpoint steering) and #2
(probe-as-reward RL); complementary to #3 (think-end position): if V1 moves
behavior, position (#3) and phrasing (this) can be crossed in one small grid
later. AA-6 (gate@late) was flat, so no re-scoping of positions is needed —
the cells above stand as designed.

## Revision 1 — think-end position + the position sub-question (SIGNED pre-launch, 2026-07-02)

Signed by the user in-conversation 2026-07-02 ("yes amend our amendment"),
BEFORE any AB cell has run — an additive pre-launch revision, not a goalpost
move. All original content above stands as written.

### Restructured questions

The amendment now answers two nested questions (user framing, 2026-07-02):

- **Q-A (channel):** does injecting the probe signal into the thinking
  process influence the decision at all? Operationalized exactly as the
  original design: any V1 cell passing its effect gate (now AB-G1, AB-G1f,
  or AB-G2).
- **Q-B (position):** does WHERE the injection lands in the think block
  change how much it influences the decision? Pre-stated hypothesis (user,
  2026-07-02): a note at the FRONT of the thinking changes the trajectory
  of the reasoning but does not influence the final decision very much; a
  note at the END — the model's final thought right before it commits to
  an answer — is more likely to change the decision itself.

### New position: `final` (think-end)

Mechanics (implemented as `position="final"` in `cot_inject.py` +
`run_arm_b.py`, CPU unit-tested with this revision):

1. ONE shared plain initial pass per item (identical to `late`); the dial
   score is read post-answer at the same anchor as `late`.
2. ONE shared *thinking-enabled plain* revision-reasoning pass per item:
   the model re-reasons about its answer with no note present; its think
   content (up to `</think>` or the token budget,
   `max_new_tokens_revision`) becomes the shared draft.
3. Per variant (real/placebo), the V1 note — same banded dial templates as
   above, wording unchanged — is appended AFTER the shared draft as the
   final thought, the think block is CLOSED (`</think>`), and the model
   generates the answer immediately.

By construction the reasoning trajectory is byte-identical between real
and placebo (and across score values): the ONLY difference between arms is
the score carried by the final thought. This makes dial@final the cleanest
causal read of decision-use in the design — any real-vs-placebo delta is
attributable purely to the true probe value at the commit point, with zero
trajectory confound. Contrast with dial@late, where the note sits at the
TOP of the revision think block and the model reasons after it (the note
can shape the trajectory AND the decision).

### Cell + gate added

- **dial@final (V1)**: dial pool, 500 answerable items, same decode
  parameters, same placebo machinery, same adequacy floors as dial@late.
  V1 is now 3 cells (gate@early, dial@late, dial@final); added cost
  ≈ 2,000 generations (4 per item: shared initial + shared revision-think
  + 2 forced answers).
- **AB-G1f (V1 dial@final):** thresholds identical to AB-G1 — real vs
  placebo appropriate-revision discrimination ≥ +10 points, CI excludes 0,
  AND final answerable accuracy drop ≤ 5 points vs placebo. AB-G1
  (dial@late) remains PRIMARY. AB-G3's trigger extends to "V1 passes G1,
  G1f, or G2"; on a final-only hit, the V2–V4 decomposition runs at the
  `final` position.

### Q-B predictions (pre-stated) and falsifier

1. **Decision-effect ordering:** delta(dial@final) ≥ delta(dial@late) on
   appropriate-revision discrimination. Theoretical basis recorded before
   the run: recency / serial-position effects on long contexts; the
   Amendment S/T finding that the correctness signal is strongest read
   AFTER the answer (post-generation advantage); and CoT-unfaithfulness —
   a note early in the trajectory can be reasoned past and rationalized
   away, a final thought adjacent to the commit point cannot.
2. **Trajectory dissociation:** at dial@late, real-vs-placebo divergence in
   the think-text continuation is expected even if the decision metric
   stays flat (front changes trajectory, not decision); at dial@final,
   trajectory divergence is structurally zero (shared draft). Trajectory
   readout is DESCRIPTIVE, not a gate: real-vs-placebo differences in
   (a) verification-move rate in the continuation (the mined native moves:
   "let me think", "verify", "double-check", "I don't know") and
   (b) continuation length.
3. **Q-B falsifier:** dial@late passes AB-G1 while dial@final misses
   AB-G1f with non-overlapping deltas → the final-thought/commit account
   is wrong; the signal gets used at the front of thinking or not at all.
   Both flat → the Q-A falsifier governs (position never gets a reading).
   Both pass at similar magnitude → position does not matter (informative
   null on Q-B, reported as such). Ordering readings with overlapping CIs
   are reported descriptively, never as a pass.

### Preconditions (extension)

Precondition 6 extends to the new position: the batched steering harness
(`arm_b_batched.py`, branch `steering-harness-batching`) implements only
`early`/`late` today. A batched dial@final run requires adding `final`
there AND passing the batched-vs-sequential spot check on it; otherwise
run dial@final on the sequential engine.

### Changelog

- Added injection position `final` (think-end) to `cot_inject.py` and
  `run_arm_b.py` (+ CPU unit tests); `early`/`late` behavior untouched.
- Added V1 cell dial@final and gate AB-G1f (thresholds = AB-G1).
- Added Q-B (position) hypothesis, ordering + dissociation predictions,
  descriptive trajectory readout, and Q-B falsifier.
- Extended AB-G3's trigger and precondition 6 to cover the new cell.
- Absorbs queued follow-up #3 (think-end position) from the AA close-out.
- No change to V1–V4 templates, band cuts, AB-G1/G2/G3 thresholds, the
  placebo design, or the original falsifier.

## §7 Results (filled per cell as runs complete)

**Run provenance (2026-07-03):** V1 fleet run sequentially on the local 3090
from the migrated ext4 repo (the first launch died with the 9P mount outage;
nothing was saved, restart from scratch). `unsloth/Qwen3.5-4B`, note-variant
v1, seed 20260701, temp 0.7 / top-p 0.9, sequential engine (`run_arm_b.py`).
Raw artifacts (gitignored): `steering/results/ab-{1,2,3}-*/result.json`.
Committed aggregates: `experiments/first-person-injection/artifacts/trace_reports/ab_v1/` (per-cell trace reports via
`analyze_ab_traces.py` + `INTERIM-NOTES.md`). Config shas: AB-1
`ced11c261fbecd7f`; per-cell shas recorded in each report.

- **AB-1 (V1 gate@early, 300 unknown + 300 known):** real-vs-placebo
  unknown-question final abstention **+2.0 points** (2.33% vs 0.33%),
  95% CI [0.33, 3.85] — CI excludes zero, effect 5× below the +10 gate.
  Known-question answer rate 1.000 real vs 0.997 placebo. degenerate 0.0,
  coherence ok, adequacy pass (262 unknowns answered under control). The
  known-accuracy no-regression clause is moot for the verdict (conjunctive
  with an effect-size miss).
- **AB-2 (V1 dial@late, PRIMARY, n=500):** `revision_discrimination` 0.0 in
  both arms — **instrument saturated, see §8**. Decision-level flows
  (descriptive): wrong→correct 8.1% real vs 8.9% placebo; correct retention
  91.5% vs 92.3%; answer→abstain **0 in both arms**. Final answerable
  accuracy delta −0.8 pts, CI [−3.4, +1.8]. degenerate 0.0, coherence ok,
  adequacy pass (370 wrong / 130 correct).
- **AB-3 (V1 dial@final, n=500):** the shared-draft + forced-answer design
  gives the revised flag real variance here (470/500 vs 469/500), so the
  registered metric IS valid at this position: real 0.102 vs placebo 0.129,
  delta **−2.7 pts**, CI [−9.8, +4.3] — includes zero. Flows: wrong→correct
  6.4% vs 6.2%; retention 93.7% vs 92.3%; answer→abstain 0 in both arms.
  Accuracy delta +0.6 pts, CI [−1.4, +2.6]. degenerate 0.0, coherence ok,
  adequacy pass (357/143).
- **Trajectory readout (Q-B prediction 2, descriptive):** at dial@late the
  predicted real-vs-placebo think-text divergence did NOT appear — hedging
  and verification marker rates and continuation length are arm-identical
  (e.g. verify-words 53.4% vs 51.6%; mean length 241 vs 241 chars). The note
  is absorbed without acknowledgment: 1.8% of real-arm continuations mention
  any percent (placebo 4.8%). Full trace-pattern capture (verbatim
  rule-following on all 7 AB-1 real-arm abstentions at ~2–3% compliance;
  self-contradiction examples; the non-causal recoverability gradient) in
  `experiments/first-person-injection/artifacts/trace_reports/ab_v1/INTERIM-NOTES.md`.

## §8 Verdict (locked gates, goalposts unmoved)

- **AB-G1 (dial@late, PRIMARY): UNMEASURABLE — instrument invalid.**
  `compute_revised()` falls back to normalized-full-text inequality; under
  the registered sampled decode a regenerated continuation never reproduces
  the initial text, so `revised ≡ True` (500/500 both arms) and the metric
  is 0 by construction with CI [0,0]. Reported per the pre-registered
  UNDERPOWERED convention: excluded from pass/fail, not scored. The
  decision-level flows (descriptive) show the cell flat regardless.
  **Retroactive instrument note:** AA-7 shows the same saturation (500/500),
  so AA-G4's flat reading was made on this dead instrument; AA's conclusion
  survives on AB-2's flows, but the AA §verdict should carry a correction
  pointer. Engine fix (answer-level revision detection) queued with the
  pre-next-amendment batching work.
- **AB-G1f (dial@final): MISS.** Valid instrument at this position; delta
  −2.7 pts, CI includes zero (if anything the real note *suppresses*
  discrimination, n.s.).
- **AB-G2 (gate@early): MISS.** +2.0 pts with CI excluding zero vs the
  ≥ +10 requirement.
- **AB-G3 (decomposition): NOT TRIGGERED** — no V1 cell passed; V2–V4 do
  not run.
- **Q-B (position): NO READING** — both dial cells flat, so per the
  pre-stated clause the Q-A falsifier governs. Descriptively, the
  commit-point position did not rescue the effect (−2.7 vs ~0), against
  Q-B prediction 1's direction.
- **Overall: AMBIGUOUS-LEANING-NEGATIVE, reported as such per the locked
  ambiguity clause.** SUCCESS (any of G1/G1f/G2 passing) is not met. The
  strict falsifier wording ("all real-vs-placebo CIs include zero") is not
  met either, solely because AB-1's +2.0-pt abstention delta is real. The
  honest summary: first-person framing with an interpretable percent and an
  explicit action rule does not open the text channel at the registered
  thresholds; it leaks a ~2-pt, ~2–3%-compliance trickle of verbatim
  rule-following on the gate cell and nothing on either dial cell. AA's
  "presence ≠ use" conclusion is strengthened descriptively (now covering
  the strongest natural-language framing), while noting the channel is
  attenuated rather than perfectly sealed. Reinforcing negative for the
  Paper 5 line; any promotion of the small gate@early effect would require
  a fresh registered replication at adequate power.
