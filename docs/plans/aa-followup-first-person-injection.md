# Proposed follow-up: first-person confidence injection (AA phrasing diagnostic)

**Status:** DESIGN / PROPOSAL (2026-07-02). NOT launched. Runnable only after
the Amendment AA Stage-1 queue (cells AA-1..8) completes and its verdict is
recorded on the registered template — this diagnostic must not contaminate or
reinterpret AA's pre-registered cells.

**Instrument ruling (per `experiment-runner/reference/amendment-vs-lab-notebook.md`):**
**Tier-2 Amendment required before running.** AMENDMENT-AA lists only the α grid
and eval-subset sizes as authorized tier-3 knobs; the injection note template is
NOT among them, and this proposal carries a distinct mechanistic rationale from
AA (framing artifact vs. channel absence) and adds new evidence cells reported
as evidence. It therefore does not qualify as tier-3 tuning under AA. This
document is the design capture that becomes that amendment's draft (same path
`docs/plans/confidence-steering-experiment.md` took before AMENDMENT-AA was
signed). If a phrasing variant *moves* behavior, promoting that to a claim still
requires a fresh confirmatory replication registered before running it.

## Motivation

AA-5 (Arm B, gate signal, early position, real+placebo CoT injection) came back
FLAT: abstention delta +0.0033, CI [0.0, 0.010] includes zero; answer rate on
known items 1.000 in both conditions. Combined with the four flat Arm A
activation cells, the running interpretation is "presence ≠ use": the model
carries near-perfect answerability information (direction AUROC 0.998 @ L14)
but does not condition its answer/abstain action on it.

Before accepting that reading for the *text* channel, there is a named confound:
the registered injection note is out-of-distribution telemetry, not reasoning.

```
[internal: gate 0.87 — confident — known]
```

Three specific mismatches with how a model actually conditions on its own think
block:

1. **Voice** — reasoning traces are first-person prose; a bracketed
   third-person annotation may be treated as metadata noise rather than a held
   belief.
2. **No use-instruction** — the note supplies the information and hopes for
   use; it never states an intention to act on it. The presence-vs-use gap the
   experiment probes is arguably *reproduced inside the prompt design*.
3. **Interpretability** — "gate 0.87" presumes the model knows what a "gate"
   is; a plain-language self-assessment does not.

User-proposed framing (2026-07-02, verbatim intent): *"I am [X]% sure I have
the knowledge required to answer this question appropriately. I will
incorporate that into my thinking and response to the user."*

## Design

Same harness as AA Arm B (`run_arm_b.py` + `cot_inject.py`), same model
(Qwen/Qwen3.5-4B), same frozen pools, same probe directions, same
sampled-decode settings, same within-batch score-permutation placebo. The ONLY
manipulated factor is `note_template` (plus a percent rendering of the score).

### Variants (each run real+placebo)

| Variant | Template | Isolates |
|---|---|---|
| V0 (anchor) | `[internal: {signal} {score:.2f} — {interp}]` | registered AA template — reuse AA-5/AA-6 results, do not re-run |
| V1 (full reframe) | `I am {pct}% sure I have the knowledge required to answer this question appropriately. I will incorporate that into my thinking and response to the user.` | voice + interpretability + commitment together (max-effect probe) |
| V2 (commitment only) | `[internal: {signal} {score:.2f} — {interp}] I will incorporate this into my thinking and response.` | commitment clause alone, telemetry voice held fixed |
| V3 (voice only) | `I am {pct}% sure I have the knowledge required to answer this question appropriately.` | first-person voice + percent alone, no commitment |

V1 vs V0 answers "is there any phrasing under which the text channel works?";
V2/V3 decompose *which* ingredient did it, and are only worth running if V1
moves. Suggested order: V1 first (go/no-go), then V2+V3 only on a V1 hit.

### Cells per variant

Mirror the informative AA Arm B surface:

- **gate @ early** on the gate pool (abstention_unknown, answer_rate_known) —
  n=600 items, real+placebo.
- **dial @ late** on the dial pool (revision_discrimination, accuracy deltas) —
  the higher-headroom readout: AA-5 showed abstention is near-floor in both
  conditions on the gate pool, so the dial/revision surface is where a phrasing
  effect is most detectable. Match whichever AA-7/8 configuration is adequate.

Cost estimate: each variant-cell ≈ one AA Arm B cell (~2400 generations,
~2–3 h local dGPU). V1 alone = 2 cells ≈ one AA-5-sized day.

### Placebo note

The placebo stays the within-batch score permutation *inside the identical
sentence*. This is exactly the right control here: a first-person confident/
unsure sentence may prime generic caution regardless of the score value; the
permuted-score placebo subtracts that priming, so any surviving delta is
attributable to the *true* probe value flowing through the new phrasing.

## Prediction, falsifier, gates (pre-stated)

- **Prediction:** if AA's text-channel flatness is a framing artifact, V1 shows
  real-vs-placebo separation the registered template did not: on the dial/late
  cell, revision_discrimination delta > 0 with 95% CI excluding zero; on the
  gate/early cell, abstention_unknown delta CI excluding zero.
- **Falsifier for the framing hypothesis:** V1 flat on BOTH cells (all
  real-vs-placebo CIs include zero) with health checks passing (degenerate rate
  ≤ AA levels, coherence floor OK). That result *strengthens* AA's
  "information present but not wired to action" conclusion — the flatness
  survives the strongest natural-language framing.
- **Health gates (per cell):** degenerate_rate ≤ 0.02; coherence_floor_ok;
  adequacy same as AA (gate: ≥100 unknown-answered controls; dial: ≥40/40
  initial correct/wrong).
- **No goalpost moves:** AA's own verdict is computed on the registered
  template only. This diagnostic is reported separately, labeled exploratory.

## Preconditions

1. AA-6..8 complete and AA close-out recorded (`amendment_aa_verdict.py` output
   + amendment §7 with the anchor-vs-end confound named).
2. A signed Tier-2 amendment (this doc promoted to
   `experiments/<slug>/AMENDMENT.md` with the prediction,
   falsifier, and gates above locked) — user sign-off required.
3. Explicit user launch approval for the GPU run(s), naming variant + cells.
4. Branch discipline: this diagnostic depends on AA's registered-template
   verdict, so it cannot start until the AA PR merges. Once unblocked, it runs
   in its own dedicated worktree on its own branch off up-to-date `main`,
   never stacked mid-flight on the AA branch or worktree.

## Relation to the other queued follow-ups

Independent of follow-up #1 (trained-checkpoint steering) and #2
(probe-as-reward RL); complementary to #3 (think-end position): if V1 moves
behavior, position (#3) and phrasing (this) can be crossed in one small grid
later. If AA-6 (gate @ late) turns out non-flat, re-scope this diagnostic to
the position that showed life.
