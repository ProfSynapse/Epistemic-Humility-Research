# Proposed experiment: causal confidence steering — "turn the probe around"

**Status:** DESIGN / PROPOSAL (2026-06-30). NOT registered, NOT launched. This is
the design capture for a NEW experiment line that emerged during the Amendment Z
session. It becomes runnable only after (a) a signed Tier-2 Amendment with locked
gates on its OWN branch off up-to-date `main`, and (b) explicit user launch
approval naming cells/lane. Nothing here is authorized to run yet.

**Instrument ruling (per `experiment-runner/reference/amendment-vs-lab-notebook.md`):**
this is a **new experiment / new paper line** (causal *steering*, Architecture A),
distinct from the observational two-signal *readout* paper (Paper 3). It does NOT
touch the locked PROTOCOL v0.3 headline surface, so it is not a Tier-1 protocol
revision. Its first concrete run is governed as a **Tier-2 Amendment** (falsifier
pre-stated), exactly as S/T/U/W/X/Z were for the readout paper. Working title:
**Paper 4 — reading vs. writing the trust axis.**

## One-line thesis

The linear probe we built to *listen* to the model's internal trust signal can be
turned around to *whisper* it back in — as a calibrated internal nudge (activation
steering) or as a note in the reasoning trace (CoT injection) — to influence the
model's thinking and its output from the inside, without retraining it.

## Why now (the intellectual through-line)

- **O** proved the trust signal is latent and drives a perfect policy via an
  external readout — "only the channel is missing."
- **R** tried to open that channel by *training* (joint aux-head co-train so the
  internal signal flows to the emitted token) and was **FALSIFIED**: the emitted
  scalar just collapsed onto the answer/abstain action.
- **S** found the correctness signal peaks *mid-network* and reads best *after*
  the answer — i.e. the knowledge exists but is not on the path to the output.

Steering/injection is the response to R's failure: instead of *teaching* the model
to route mid-network knowledge forward, **mechanically force the channel open at
inference** by writing the probe direction (or a textual proxy) back into the
computation. The directions already exist — every readout amendment (O/P/S/W/X/Z)
produced per-layer probe vectors. The hard part (finding the direction) is done.

## The centerpiece: a causal test of the anchor-vs-end "why"

Our current anchor-vs-end account is **observational** — probes *decode*
answerability best at the pre-answer anchor and correctness best at the post-answer
end token (S). That shows where the signal is *legible*, NOT where it is *causally
used*. Steering and injection are causal writes, so they test the stronger claim.

Two intervention modalities, each done individually and separately:

- **Arm A — internal steering** (sub-symbolic): add `α · direction` into the
  residual stream during generation.
- **Arm B — CoT injection** (symbolic): write the computed signal as text into the
  thinking trace of a thinking-enabled model.

Cross them with **position** to get a 2×2 that interrogates the theory:

| write at → | ANCHOR / early (pre-answer) | END / late (post-answer) |
|---|---|---|
| **answerability signal** | predicted: changes answer/abstain decision | predicted: little effect (already committed) |
| **correctness signal** | predicted: little effect (no answer yet to judge) | predicted: changes post-hoc trust / triggers revision |

- **Strengthens the theory** if the causal effect is position-locked in the SAME
  pattern the probes decode, AND both modalities (vector + text) agree. Convergent
  validity across two independent write channels is hard to explain away.
- **Weakens the theory** if intervention works equally at either position (the
  info is distributed/used everywhere), meaning the readout asymmetry was "easiest
  to decode here," not "used here." That is a real, publishable negative that
  sharpens the "why."

This is the presence-vs-use distinction made experimental: probing measures
*presence*; steering/injection measure *use*.

## Arm A — internal activation steering

Mechanics: at inference, at the probe's best layer, `h ← h + α · d`, where `d` is
the (unit-normed) probe direction and `α` scales with the *measured* uncertainty
(calibrated, not binary — proportional steering avoids inducing hedging on
confident-correct answers). Sweep `α` to find the coherence-preserving sweet spot.
Position variants: steer at the anchor position vs. the post-answer stream (for
end-position, the causal target is a self-revision / surfaced-confidence pass, not
the already-emitted token).

## Arm B — chain-of-thought injection

Mechanics: compute the probe score, render it as a short note, and insert it into
the reasoning trace, e.g. `[internal: answerability 0.3 — likely unknown]`. The
model reads it via normal attention and may reconsider ("let me double-check")
in its own voice. Position variants: inject early (before it reasons to an answer)
vs. late (after it has drafted one inside the think block). Adjacent to Amendment Y
(which tests whether the CoT verbalizes the signal unprompted); here we *force* it.

## Draft pre-registration (to be finalized + signed before any run)

- **Prediction (each arm):** writing the *answerability* signal at the
  anchor/early position raises appropriate abstention/hedging on unknown questions
  WITHOUT lowering accuracy on known ones; writing the *correctness* signal at the
  end/late position shifts post-hoc trust / induces self-revision. Effects are
  muted when the signal is written at the "wrong" position.
- **Falsifier(s):** (1) neither write shifts behavior at any position/strength
  before coherence breaks → steering/injection is inert (the R-style channel stays
  shut even by force); (2) writes shift behavior indiscriminately (position and
  signal-type do not matter) → the anchor-vs-end "why" is not causally load-bearing;
  (3) the only way to move behavior is to over-steer into incoherent text → no
  usable operating point.
- **Gates (to be set with numbers before running):** an appropriate-abstention /
  calibration-improvement metric with a CI-backed threshold; a correct-answer
  accuracy floor (no regression); a text-coherence floor; and a position-asymmetry
  contrast (effect at correct position minus effect at wrong position) with CI.
- **No goalposts move after the result.**

## Hard limits / caveats (honest scope)

- **Cannot inject knowledge it lacks** (read-vs-compute wall): steering amplifies
  a signal the model already computed; it can surface latent uncertainty, not
  create missing facts. The realistic win is *surfacing*, not *knowing*.
- **Must be calibrated/proportional**, or it degrades a confident-correct model
  into a timid one (over-hedging).
- **Coherence breaks under strong steering** — there is a sweet-spot `α`; find it
  empirically and report the whole curve, not just the best point.
- **Circularity check for Arm B:** injected text could change behavior via generic
  "be cautious" priming rather than the specific signal; include a shuffled/placebo
  score control (inject a random confidence value) to isolate the real signal.

## Dependencies & sequencing

- Reuses the per-model probe **directions** produced by the readout amendments;
  Amendment Z is generating cross-family direction vectors right now, so this can
  run per-family later.
- Arm B needs thinking-enabled models (Amendment Y territory).
- Sequencing: land/merge Z first (one-experiment-one-branch discipline), then mint
  the signed steering amendment on its own branch off up-to-date `main`.

## What was captured today (design only)

- This design doc.
- Cross-link + "next axis" entry in `experiment/notes/two-signal-readout.md`.
- Session 0030 checkpoint (design decision + instrument ruling).
- Cross-session memory `confidence-steering-experiment-proposed`.
