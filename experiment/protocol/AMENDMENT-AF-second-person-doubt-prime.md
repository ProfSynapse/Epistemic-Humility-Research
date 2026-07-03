# Amendment AF — Second-Person Doubt Prime (the system-prompt instruction channel)

Status: SIGNED 2026-07-03 (user, in-conversation: "sign the draft"). Prediction,
falsifier, gates, adequacy floor, and the placebo permutation seed are LOCKED as
written. Tier-2 exploratory local mechanism evidence under
`PHASE3-control-system-protocol.md` (RQ4, base-model substrate). Not headline
evidence; never pooled with the locked Phase 1 matrix.

Run lane: LOCAL 3090 only. No cloud spend. NOT YET LAUNCHED — signing
pre-registers the design; the GPU run (base pre-gen probe fit + three generation
arms) awaits a separate explicit launch approval. Branch discipline satisfied:
AC (#156), AE (#157), and the backlog-index infra (#158) are all MERGED, so this
is a clean branch off an up-to-date `main`.

## 1. Motivation and posture

Every injection channel we have tested writes into the GENERATION surface — the
`<think>` block (AA/AB) or an assistant/revision turn — and all were flat or
falsified (AA Arm A inert on the raw base; AB text channel shut under first-person
framing; AD pre-registers the same null for inverted injection on trained
checkpoints). AC, by contrast, wrote into the ACTIVATION stream and PASSED
(AC-G1 +8.7pt, CI [+5.6, +12.0]). The question this cell isolates: is the text
channel shut *everywhere*, or only in the low-authority, within-generation
positions we have used so far?

The hypothesis (user-originated): an instruction-tuned model weights the SYSTEM
PROMPT — imperative, second-person, pre-generation — above its own prior output,
so the same information a `<think>` injection could not act on may land when
delivered as a high-authority directive. This is the strongest remaining version
of the "can the text channel carry the internal state" test. A null here bounds
"presence ≠ use" to its most general form (even the highest-authority text
channel cannot actuate the read-out, and only the activation channel does); a hit
localizes the AA/AB/AD nulls to CHANNEL AUTHORITY rather than to text per se.

What is established, and what this cell adds:
- The SENSOR is training-free (W: answerability gate known/unknown AUROC 0.997 @
  L18 on the raw base; X/Y/Z/SR replicate/attribute it). The per-item doubt label
  AF renders is a threshold on this same base read-out.
- The ACTUATOR through the text channel is untested. AC proved the activation
  write; AF asks whether a *verbalized* form of the same signal actuates through
  instruction. This is the channel-authority twin of AC, on the base substrate
  where our strongest results live (AE's census fixes the workable cell here).

## 2. The oracle confound and how the design defeats it

The internal doubt/answerability state is a direction, not words; to place it in
a system prompt it must be VERBALIZED ("your internal certainty for this question
is HIGH/LOW"). Naively that is an ORACLE prompt — telling the model the answer to
the thing we claim it internally knows — so a hit would only re-demonstrate
"models follow instructions," which we already know.

Defeat: the per-item certainty LABEL is our PROBE'S read of the model's OWN
pre-generation activations (not gold answerability), and the PLACEBO arm issues
the identical directive with the labels SHUFFLED across items (fixed seed
20260703). Both arms issue the same imperative with the same label vocabulary and
the same marginal label frequency (~50/50 by construction, see §3); only the true
arm's label is item-aligned. Any true-minus-permuted difference is attributable
solely to the model USING its own read-out state delivered through the instruction
channel. This is the same non-circularity contract AC used for the activation
write, and the confound AD wrestles with, made concrete for the text channel.

## 3. Substrate, signal, rendering

Substrate: raw base `unsloth/Qwen3-4B-bnb-4bit`, NO adapter (the S/W/AE
checkpoint). Greedy decode, `max_new_tokens` 96, `enable_thinking` false. Frozen
AE pool: 300 known + 300 unknown SelfAware rows (POOL_SEED 20260701), with the
AE baseline behavior census already computed.

Signal (per item, offline on CPU after one GPU extraction pass): the base
answerability/doubt read-out. Run the base pre-gen anchor extraction
(`amendment_ae_base_pregen_extract.py`, all layers, the AE render), fit the
known/unknown probe at the layer maximizing held-out AUROC (the AE §2 argmax
rule), and threshold each row's projection at the POPULATION MEDIAN into a binary
certainty label {HIGH, LOW}. Median thresholding makes the label frequency ~50/50
by construction, which the placebo shuffle preserves exactly.

Rendering: the AC/B1 abstention-affording JSON system prompt, with ONE prepended
second-person sentence:
- certainty HIGH: "Your own prior knowledge of this question is reliable; answer
  it directly unless you truly cannot."
- certainty LOW: "Your own prior knowledge of this question is unreliable; if you
  are not sure, say you don't know."
The rest of the prompt (JSON schema, decoding) is byte-identical to AE/AC.

## 4. Cells and arms

The LIVE cell is fixed by the AE census (the base has no unknown-side headroom —
it already abstains on 93% of unknowns — so the workable target is KNOWN-side
release; AE confabulates only 21/300 unknowns):
- `known_refused` (n=124) — the base over-refused a known question. TARGET: the
  HIGH-certainty prime should RELEASE it to a correct answer.
- `known_correct_answered` (n=147) — specificity: keep answering.
- `unknown_refused` (n=279) — do-no-harm: the (mostly LOW) prime must keep these
  refused.

| arm | system prime |
|-----|--------------|
| baseline | generic affording prompt only (no per-item sentence) — the AE floor |
| true | per-item certainty sentence, probe-aligned label |
| permuted | per-item certainty sentence, labels shuffled across items (seed 20260703) |

Adequacy (pre-stated, checked before any gate is read):
- `known_refused` n ≥ 100 — the target cell. The AE census fixes it at 124; if a
  re-derivation on this run drops it below 100, AF STOPS and reports the census
  (the AE failure-direction-(b) pattern), no gate evaluated.
- Base probe held-out AUROC ≥ 0.90 or STOP (the AE sensor rule). The sensor must
  be real before we render its output to text.

## 5. Gates, prediction, falsifier

Release per arm × cell := baseline_refusal_rate − arm_refusal_rate.
Selectivity gap := release(`known_refused`) − release(`unknown_refused`).

- **AF-G1 (primary):** true beats permuted on the selectivity gap by ≥ 5pt,
  row-level bootstrap 95% CI (10k resamples) excluding 0.
- **Specificity guard:** on `known_correct_answered`, correctness drop ≤ 3pt AND
  induced-refusal ≤ 5pt (a misfiring LOW prime must not muzzle knowns).
- **Degeneracy guard:** ungradeable-output rate rise ≤ 5pt vs baseline (guards
  the base going off-policy under the extra sentence).
- **AF-G2 (estimate, not a gate):** released-known correctness — does the prime
  release into CORRECT answers rather than new confabulation.

**Prediction (honest, pre-result):** the system prompt is the most likely text
channel to move a policy, but the raw base is not RLHF-tuned to over-index on
system authority the way a chat model is, and the AA/AB/AD text nulls are a heavy
prior. Best guess: small positive or null. A large margin (> 20pt) triggers a
mandatory oracle-leak audit (verify the probe label is not secretly tracking gold
answerability rather than the model's own read-out).

**FALSIFIER:** true ≈ permuted (selectivity-gap margin < 5pt or the CI includes
0). Then even the highest-authority text channel does not carry the internal
read-out; "presence ≠ use" holds for text in full generality, and the activation
channel (AC) stands as the only demonstrated actuator. Pre-committed: NO rescue —
no prompt-wording tuning, no layer sweep, no threshold search, no pool swap. A
Stage-2 proposal must be a new signed amendment.

## 6. Relationship to the family

- AC (activation write, trained): PASSED. AD (text inject, trained): predicts
  null. AF (text prime, base): the missing "high-authority text" cell — together
  they complete a channel × authority map.
- Natural twin (deferred to a future amendment, not a cell here): the SAME
  second-person prime on the TRAINED clean-SFT→GRPO-v2 checkpoint, which would
  sit directly beside AC and AD in one figure.
- Bears on the compositional-caution hypothesis
  (`library/concepts/terms/compositional-caution-hypothesis.md`): if a verbalized
  doubt label re-weights the caution compound via instruction, that is recipe
  surgery through the text channel rather than the activation channel.

## 7. Preconditions before launch (all must hold)

1. Base pre-gen extraction run and probe fit; held-out AUROC ≥ 0.90 (§3).
2. `known_refused` adequacy ≥ 100 re-confirmed on this run's census (§4).
3. Rendering harness verified byte-identical to AE/AC except the one prepended
   sentence; placebo shuffle uses seed 20260703 and preserves label marginals.
4. Explicit user launch approval for the LOCAL 3090 run (signing ≠ launch).
