# Amendment AH — Divergent-Pool Own-Readout Attribution (probe ≠ gold)

**Status: DRAFT** (queued 2026-07-03, session 0036; not signed, not launched).
**Tier:** A (new evidence cell; gates pre-stated before launch; Stage-0
recalibration window declared in §6).
**Branch:** `amendment-ah-divergent-pool`.
**Depends on:** AF (PASS, channel-authority), AG (PASS, asymmetric compliance),
session-0035 MI pliability result (boundary-distance law).

---

## 1. Motivation and strategic position

AF established that a second-person system-prompt doubt prime moves refusal
behavior selectively (+18.0pt over permuted). AG established that the same
channel is obeyed even when the prime is wrong (induced refusal on
known-correct +34.0pt) and that the belief axis never moves — compliance
travels through the caution/policy axis. Neither experiment can answer the
question that now matters most, because on the AF/AG pool the probe label and
the gold label agree on 600/600 rows: a prime aligned with the model's OWN
internal readout is byte-identical to a prime aligned with ground truth. The
two hypotheses — "the model consults its own readout when deciding whether to
take up the prime" vs "the model obeys instruction content, full stop" — make
identical predictions on a concordant pool.

This amendment builds the pool where they diverge: rows on which the frozen
internal readout disagrees with gold answerability. On such rows a
readout-aligned prime and a gold-aligned prime are OPPOSITE sentences, and the
two hypotheses finally separate.

**Strategic stakes (user directive, 2026-07-03, recorded verbatim):** "i would
prefer not to go the prosthetic path it's too fragile and easy to game." The
prosthetic path (external probe-read + gate + veto scaffolding at inference)
is rejected as a program goal; the goal is NATIVE epistemic humility — a model
whose emitted behavior consults its own internal knowledge state. AH is the
gatekeeper experiment for the native path via the text channel:

- If uptake is gated by congruence with the model's own readout (H-resonance),
  a native hook exists in the strongest known channel, and Paper 5 pivots to
  amplifying it.
- If uptake is pure instruction compliance (H-compliance), the text channel is
  confirmed belief-blind even when belief and instruction conflict, and the
  native path requires engineered dependency at training time — probe-as-reward
  RL (backlog item 4) becomes the mainline candidate.

Either verdict moves the program; the failure mode this design eliminates is
the current unfalsifiable ambiguity.

## 2. Hypotheses and pre-stated prediction

- **H-compliance:** prime uptake on divergent rows is fully explained by prime
  direction (muzzle vs release; AG showed these are asymmetric) plus baseline
  distance from the refusal boundary (session-0035 pliability law). Congruence
  between prime content and the model's own readout contributes nothing.
- **H-resonance:** primes congruent with the model's own readout get
  systematically more uptake than incongruent primes, beyond what direction
  and boundary distance explain.

**Orchestrator prediction (pre-stated):** H-compliance. AG showed the model
obeys a gold-anti-aligned prime against its own demonstrable knowledge while
the doubt readout stays anti-semantic; nothing yet observed suggests the
policy consults the readout. Recording this so a resonance result counts as a
genuine surprise. User prediction to be recorded at signing.

## 3. Design

### 3.1 The divergent pool

Two divergent cells, defined against the FROZEN AF doubt probe (L24 logistic,
pre-generation anchor, operating threshold frozen from the AF calibration
artifacts — no refitting to manufacture divergence):

- **D-over** — probe says HIGH certainty; gold says unanswerable. The readout
  overestimates. Gold-unanswerable is definitional (e.g. SelfAware
  unanswerable subset), so no behavioral verification is needed.
- **D-under** — probe says LOW certainty; gold answerable AND the model
  demonstrably knows: greedy correct answer under the forced-best-guess
  rendering (AG census methodology). Behavioral verification is required
  because "gold answerable but model doesn't know" is not a probe error.

Divergence must be CONFIDENT, not threshold noise: a row qualifies only if the
probe score sits beyond a margin band on the wrong side of the frozen
threshold (margin in z-units of the probe-score distribution; exact value
calibrated in Stage 0 inside the declared window). Rationale: near-threshold
rows have ambiguous internal states and make congruence ill-defined.

**Consensus-divergence requirement (hydra insurance):** a divergent row must
disagree with gold under ≥3 independent readouts of the same construct
(e.g. probes at L20/L24/L28, or a cross-validation fold ensemble at L24 —
fixed in Stage 0). Session 0035 showed the caution/doubt machinery is
redundantly encoded; a row where only ONE readout diverges is plausibly probe
noise (readout misreads state, state actually matches gold), which would
dilute a real resonance effect toward null and corrupt an H-compliance
verdict. Consensus divergence raises confidence that the internal state
itself, not one linear shadow of it, disagrees with gold.

**Gold-label audit:** a manual audit of 20 rows per divergent cell for
gold-label correctness (ambiguous questions, dataset label noise). Gold-noise
rows are excluded and replaced; probe-vs-wrong-gold is not probe-vs-gold.

**Concordant filler:** the run pool also carries concordant rows (probe ≡
gold) sampled from the same sources, both to keep the prompt distribution
natural and as a within-run positive control (§5, AH-G1).

### 3.2 Arms

Batch-1, greedy, byte-frozen AF harness (`amendment_af_generate.py` lineage:
sequential, max_new_tokens 96, enable_thinking False, prime + " " +
baseline_system). Prime sentences are PRIME_HIGH / PRIME_LOW verbatim from
the frozen AF constants; the arm only selects WHICH sentence a row gets.

- **A0 — baseline:** no prime.
- **A1 — readout-aligned:** prime content matches the row's probe label.
- **A2 — gold-aligned:** prime content matches the row's gold label.

On divergent rows A1 and A2 are opposite sentences. On concordant filler rows
A1 ≡ A2 (identical bytes) — generated once, reused for both arms' bookkeeping.

### 3.3 Identification: how congruence decouples from direction

On any single divergent row, arm (A1 vs A2) determines both prime direction
and congruence simultaneously — confounded. The two cells cross them:

| Cell | A1 (readout-aligned) | A2 (gold-aligned) |
|------|----------------------|--------------------|
| D-over (probe HIGH, gold unknown) | pro-answer prime, **congruent** | muzzle prime, incongruent |
| D-under (probe LOW, verified known) | muzzle prime, **congruent** | pro-answer prime, incongruent |

Across the 2×2 (cell × arm), each prime direction appears once congruent and
once incongruent, so a direction main effect (AG's asymmetry: muzzles obeyed,
releases resisted) is estimable separately from a congruence effect. This is
the design's core; a single divergent cell could not have separated them.

### 3.4 Primary analysis

Per-row uptake = behavioral flip relative to A0 baseline on the same row
(refusal→answer or answer→refusal in the prime's direction; AG grading
lineage, degeneracy tracked). Pooled logistic over divergent rows × prime
arms:

```
flip ~ prime_direction + baseline_boundary_distance_z + congruence
```

with `baseline_boundary_distance_z` the row's A0 signed distance from the
refused/answered boundary on the L24 caution axis (session-0035 pliability
covariate — it alone reads compliance at AUROC ~0.75–0.84, so omitting it
would leave congruence to soak up pliability variance). Congruence = 1 iff
the arm's prime matches the row's probe label. Cluster-robust or
row-paired inference since each row contributes both arms; bootstrap CI over
rows, consistent with the AF/AG convention.

Secondary/descriptive: per-cell 2×2 uptake table; congruent-minus-incongruent
uptake differential per direction; interaction congruence × direction.

## 4. Stage 0 — pool mining and feasibility (pre-registered STOP)

GPU work; requires separate explicit launch approval (§7).

1. **Mine:** score a candidate set of a few thousand items (on-disk pools:
   KUQ, SelfAware splits, and answerable sets with gold labels; exact
   inventory from the session-0036 scout, appended at signing) with one
   pre-generation extraction pass on the raw base + the frozen probes;
   baseline generation + forced-best-guess verification for D-under
   candidates.
2. **Assemble:** apply margin band + consensus rule + gold audit.
3. **Adequacy floor (AE precedent, pre-stated):** ≥50 audited rows in EACH
   divergent cell. If the full candidate set cannot reach the floor, STOP and
   record infeasibility — itself an informative result (the readout's natural
   error rate on minable distributions is too low to test resonance without
   going out-of-domain; a harder-domain or perturbation-based pool would be a
   separate signed amendment, not a quiet extension of this one).

Calibration window: margin band value, consensus rule instantiation, and the
final gate thresholds in §5 may be adjusted from Stage-0 data ONLY before
signing; after signing nothing moves (AG discipline).

## 5. Gates (sketch — locked at signing after Stage 0)

- **AH-G0 (feasibility):** ≥50 audited rows per divergent cell. Fail → STOP.
- **AH-G1 (positive control):** on concordant filler, muzzle-direction prime
  reproduces the AF/AG effect (induced refusal ≥ +20pt vs baseline). Fail →
  run invalid, no reading on G2.
- **AH-G2 (congruence):** in the §3.4 model, the congruence term's 95% CI
  excludes 0 AND the pooled congruent-minus-incongruent uptake differential is
  ≥ +10pt. PASS → H-resonance. Sketch values; locked post-Stage-0.
- **Falsifier (for H-resonance; the predicted outcome):** AH-G1 passes while
  the congruence CI includes 0 (or differential < +10pt) → H-compliance
  verdict: the text channel does not consult the model's own readout even
  when readout and instruction conflict. Native path via prompting is closed;
  probe-as-reward dependency engineering becomes the mainline.

Ambiguity guard: if the two cells give opposite-signed congruence effects
(interaction dominates), the verdict is AMBIGUOUS, not a pass — pre-stated to
prevent post-hoc cell-picking.

## 6. Instrumentation (§8-style, gate-free)

Primed pre-generation extraction passes on the divergent pool (A1/A2), read
on the frozen doubt and caution axes: does an incongruent prime move either
readout differently than a congruent one? AG found doubt anti-semantic and
caution carrying compliance on the concordant pool; the divergent pool tests
whether that picture holds when instruction fights belief. Descriptive only.

## 7. Preconditions and approvals

1. This DRAFT merged to main (PR; queue convention).
2. Stage-0 scout inventory appended (session-0036 scout, CPU, running).
3. Stage-0 GPU mining pass: **separate explicit user launch approval.**
4. Post-Stage-0: gates locked, margin/consensus instantiated, user prediction
   recorded, user sign-off.
5. Main run (3 arms × pool on the 3090): **separate explicit launch approval.**
   Signing ≠ launch.

## 8. Interpretive caveats (pre-stated)

- **Readout vs state:** a divergent row is either (a) the probe misreading a
  state that actually matches gold, or (b) a state that genuinely diverges
  from gold. Per-row we cannot distinguish them; the consensus rule (§3.1)
  shifts mass toward (b) but does not eliminate (a). Residual (a)
  contamination biases a true resonance effect toward null, so an
  H-compliance verdict carries this qualification; an H-resonance PASS is
  conservative with respect to it.
- **Confabulation induction:** A1 on D-over and A2 on D-under press the model
  to answer unanswerable questions; induced-confabulation counts are reported
  (AG-G2 lineage) as a cost-of-compliance descriptive.
- **Population validity:** divergent rows are, by construction, rows where the
  readout errs or the state is unusual; effects estimated there may not
  transfer to the concordant bulk. The claim is about the MECHANISM (does the
  policy consult the readout at all), for which the unusual rows are exactly
  the informative ones.

## 9. Result

_(empty until run)_
