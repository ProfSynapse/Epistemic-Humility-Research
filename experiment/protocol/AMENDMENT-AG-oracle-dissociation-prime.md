# Amendment AG — Oracle Dissociation of the Second-Person Doubt Prime

Status: DRAFT 2026-07-03 (queued by user, in-conversation: "might as well add
that experiment to the queue then so we can really put the oracle to the test").
NOT SIGNED. Gates below are a design sketch, not locked; they are finalized and
locked at signing, which is gated on (a) the AF red-team audit adjudication and
(b) the AF results arc merging to `main`. Tier-2 exploratory local mechanism
evidence under `PHASE3-control-system-protocol.md` (RQ4, base-model substrate).
Not headline evidence; never pooled with the locked Phase 1 matrix.

Run lane: LOCAL 3090 only. No cloud spend. ONE new generation arm (~600 rows,
same cost as one AF arm); everything else reuses frozen AF artifacts.

## 1. Motivation: the question AF cannot answer about itself

AF passed AF-G1 (true beats permuted on the selectivity gap by +18.0pt, CI
[+11.8, +24.7]) and its pre-registered MANDATORY-ORACLE-AUDIT fired (true gap
22.9pt > 20pt). The audit surfaced the structural limit: the base sensor is
near-ceiling (held-out AUROC 0.9945 @ L24), so the median-threshold certainty
label coincides EXACTLY with gold known/unknown on this pool (300/300 per
side). AF's "true" arm is therefore operationally a GOLD-answerability prime.
The permuted control proves the effect requires an ITEM-ALIGNED label, but on
this pool "item-aligned" and "gold-correct" are the same thing, so AF cannot
distinguish:

- **H-compliance:** the model follows any credible per-item instruction; the
  prime works because the label is CORRECT, regardless of the model's internal
  state. (AF is then an instruction-following demo with a well-aimed oracle.)
- **H-resonance:** uptake of the prime is gated by congruence with the model's
  OWN internal read-out; the text lands because it matches what the model
  already represents.

AF's own permuted arm already hints compliance is substantial: anti-aligned
LOW primes induced 22.4% refusal on `known_correct_answered`, and the ~half-HIGH
shuffled primes released +3.9pt on `unknown_refused`. AG makes this the
registered question rather than a post-hoc reading.

## 2. Design: maximal anti-alignment (the inverted prime)

Substrate, pool, prompt, decoding, and sensor are FROZEN from AF (raw
`unsloth/Qwen3-4B-bnb-4bit`, no adapter; AE pool 600 rows POOL_SEED 20260701;
AC/AE abstention-affording JSON system prompt; greedy, `max_new_tokens` 96,
`enable_thinking` false; per-item labels from `af_labels.json`, L24 probe,
median threshold). No refit, no re-extraction: the AF sensor gate (AUROC
0.9945 ≥ 0.90) carries over by construction.

ONE new arm:

| arm | system prime |
|-----|--------------|
| inverted | per-item certainty sentence with the label INVERTED (HIGH↔LOW) relative to the AF probe label; sentences, placement, and everything else byte-identical to AF |

Comparison arms are AF's existing `baseline` and `true` generations (frozen on
disk; re-used, not re-run). Under inversion every known gets the LOW/"say you
don't know" sentence and every unknown gets the HIGH/"answer directly"
sentence — the maximal anti-aligned prime the design space allows.

Predictions per hypothesis (pre-stated at draft time):
- **H-compliance:** inverted ≈ mirror of true. Knowns get muzzled (induced
  refusal on `known_correct_answered` large, cf. permuted's 22.4% from ~half
  the dose), unknowns get released into confabulation; the selectivity gap is
  large and NEGATIVE, magnitude comparable to true's +22.9pt.
- **H-resonance:** anti-aligned primes are resisted; |inverted gap| is a small
  fraction of |true gap| and the release pattern is asymmetric (the model
  declines to confabulate on unknowns it internally doubts even when told its
  knowledge is reliable).

## 3. Stage 0 (CPU, free, before the GPU arm): conditional compliance in AF's permuted arm

The permuted arm is a natural ~50/50 mix of aligned and anti-aligned primes.
Before generating anything, compute per-cell release CONDITIONAL on whether
the shuffled label agreed with the probe label for that row:
release(aligned-subset) vs release(anti-aligned-subset). This is a
lab-notebook analysis of existing rows (no new evidence cell) and calibrates
the AG gate threshold before it is locked. If the anti-aligned subset already
shows near-full compliance, the signing decision should say so and set the
gate accordingly.

## 4. Gate sketch (to be LOCKED at signing — numbers may be recalibrated by Stage 0, never after launch)

Let G_true = AF's true selectivity gap (+22.9pt, frozen) and G_inv = the
inverted arm's selectivity gap (expected negative under compliance; use
|G_inv| throughout).

- **AG-G1 (primary, two-sided adjudication):**
  - **Compliance verdict** if |G_inv| ≥ 0.6 × |G_true| with row-level
    bootstrap 95% CI (10k resamples) on |G_inv| − 0.6·|G_true| excluding 0.
    Consequence: AF's own-read-out attribution is REJECTED; AF's surviving
    claim is channel-authority only (the system prompt actuates a selective
    policy shift; the label's alignment with internal state is not
    established as the mechanism).
  - **Resonance verdict** if |G_inv| ≤ 0.3 × |G_true| with the analogous CI
    excluding 0. Consequence: uptake is state-gated; the own-read-out
    attribution gains registered support.
  - The band between is an HONEST MIXED result: partial compliance, reported
    as such, no rescue analysis.
- **Degeneracy guard:** ungradeable-rate rise ≤ 5pt vs baseline (as AF).
- **AG-G2 (estimate, not a gate):** on `unknown_refused` rows released by the
  inverted HIGH prime, the confabulation rate (released-unknown answer rate);
  under compliance this is the cost of a wrong oracle, worth reporting next
  to AF-G2's 0.857 released-known correctness.

Pre-committed: NO rescue — no wording variants, no dose tuning, no pool swap,
no threshold search after launch. A follow-up needs a new signed amendment.

## 5. What each outcome buys the research line

- Compliance: the AF result reduces to "a correct per-item answerability
  instruction steers the base selectively." Still the first text-channel
  actuation in the family (AA/AB/AD nulls stand for within-generation text),
  but the two-signal story keeps the activation channel (AC) as the only
  demonstrated OWN-STATE actuator. P5 framing: authority moves policy; state
  does not travel through text.
- Resonance: text uptake is gated by internal state — a genuinely new
  mechanism claim (the model checks instructions against its own read-out).
  Would motivate a trained-checkpoint twin (AF §6's deferred cell) and a
  probe-vs-gold divergent-pool design as the confirmatory step.
- Mixed: quantifies the compliance/resonance split; informs whether the
  divergent-pool design (the only clean separator when the sensor is at
  ceiling) is worth a letter.

## 6. Relationship to the family

- AF (PASSED, audit pending): established the effect this amendment explains.
  AG consumes AF's frozen baseline/true arms and labels; it adds only the
  inverted arm.
- AD (SIGNED, not launched): inverted-injection on TRAINED checkpoints via
  the generation channel. AG is the system-prompt/base twin of AD's
  direction-flip logic; their results should be read side by side.
- AC (activation write, PASSED): unaffected either way; AG adjudicates only
  what AF's TEXT effect is made of.
- Compositional-caution hypothesis: compliance = the instruction channel
  re-weights the caution recipe from OUTSIDE (authority), resonance = the
  recipe is re-weighted only when the doubt element already agrees — direct
  evidence on how the compound takes instruction-level input.

## 7. Preconditions before signing (all must hold)

1. AF red-team audit adjudicated by the lead and its findings folded into §4's
   locked thresholds (Stage 0 may recalibrate the 0.6/0.3 band BEFORE signing
   only).
2. AF results arc (scripts, results, doc verdict) MERGED to `main`; one
   amendment arc at a time.
3. Stage 0 conditional-compliance analysis computed and recorded.
4. Explicit user sign-off on the locked gates, then separate explicit GPU
   launch approval for the single inverted arm (signing ≠ launch).
