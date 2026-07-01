# Amendment AA — Causal confidence steering: writing the trust axis (Paper 5)

**Status:** DRAFT PRE-REGISTRATION (2026-07-01) — awaiting user signature. NOT
signed, NOT authorized to run. No GPU cell may launch until (a) this amendment is
signed and (b) the user gives explicit launch approval naming the exact cells and
lane.

Tier-2 amendment (per `amendment-vs-lab-notebook.md`: a new exploratory evidence
line, reported separately from the locked PROTOCOL v0.3 headline surface). One
branch (`amendment-aa-confidence-steering`, off `main` @ 0046a8fd), one PR.
Design source: `docs/plans/confidence-steering-experiment.md` (design capture,
2026-06-30). Code scaffold: `experiment/phase1/probe/steering/` (merged to main;
88 CPU unit tests green on 2026-07-01). This is the first experiment of the
Paper 5 line (reading vs. writing the trust axis).

## Why this experiment (the through-line)

- **O** showed the internal trust signal is latent and drives a near-perfect
  policy via an *external* readout — only the channel to the output is missing.
- **R** tried to open that channel by *training* (joint aux-head co-train) and
  was FALSIFIED: the emitted scalar collapsed onto the answer/abstain action.
- **S/T** showed the correctness signal peaks mid-network and reads best *after*
  the answer; **W/X/Z/SR** showed the two-signal readout (gate + dial) is
  training-free, size-robust, family-general, and seed-stable.

Everything so far is **observational**: probes show where the signal is
*legible*, not where it is *causally used*. This amendment turns the probe
around — write the signal back in (activation steering; CoT injection) and test
whether behavior moves, and whether it moves **position-specifically** in the
same pattern the probes decode. Probing measures *presence*; steering measures
*use*. A position-locked causal effect would be the first causal evidence for
the anchor-vs-end account; a position-indiscriminate effect would falsify that
account's causal reading (a real, publishable negative).

## Design: 2 arms × 2 signals × 2 positions, staged

| | write at ANCHOR / early | write at END / late (revision pass) |
|---|---|---|
| **gate** (answerability) | predicted: moves answer/abstain | predicted: muted |
| **dial** (correctness) | predicted: muted | predicted: moves revision/trust |

- **Arm A — activation steering:** `h ← h + α·d` at the probe's best layer via
  forward hook (`confidence_steer.py`), α proportional to measured uncertainty.
- **Arm B — CoT injection:** compute the probe score for the item, render it as
  a short note (e.g. `[internal: answerability 0.3 — likely unknown]`), inject
  into the reasoning trace (`cot_inject.py`). **Placebo control:** identical note
  structure with a shuffled score from the same distribution — isolates the
  specific signal from generic "be cautious" priming.

**Unified protocol per item (all cells):** an *initial answer pass* followed by a
*revision pass* ("Double-check your answer above. If you are not confident it is
correct, say so or revise it."). Interventions at the ANCHOR/early position act
during the initial pass; interventions at the END/late position act during the
revision pass only. All outcomes are computed on the FINAL post-revision output,
so every cell shares the same two outcome metrics:

- **Gate metric (per cell):** final abstention rate on unknown questions
  (appropriate abstention), with final accuracy on answerable questions as the
  no-regression floor.
- **Dial metric (per cell):** appropriate-revision discrimination =
  P(revise | initial answer wrong) − P(revise | initial answer correct).

**Stage 1 (pilot, this launch): Qwen3.5-4B only** — the family with native
thinking support (required for Arm B's think-block injection) and PASS verdicts
on all Z gates. Stage 2 (cross-family: Llama-3.2-3B, Ministral-3-3B,
Gemma-4-E4B) runs only after Stage 1 finds a coherence-preserving operating
point, under a separate launch approval; the Stage-2 roll-up bar is pre-stated
below so it cannot drift.

## Inputs (already produced; CPU, no GPU used)

Unit-normed probe directions fitted 2026-07-01 from the Amendment-Z extraction
dirs by `persist_probe_direction.py` (Amendment S/X oof_probe recipe, seed
20260630; artifacts gitignored, reproducible by the commands in
`steering/README.md`):

| family | gate layer | gate AUROC | dial layer | dial AUROC |
|---|---|---|---|---|
| Qwen3.5-4B | 14 | 0.998 | 16 | 0.827 |
| Llama-3.2-3B | 14 | 0.997 | 25 | 0.861 |
| Ministral-3-3B | 24 | 0.997 | 18 | 0.818 |
| Gemma-4-E4B | 25 | 0.998 | 24 | 0.818 |

Eval pools reuse the Amendment-Z item sets (model-agnostic text): SelfAware
known/unknown rows (gate cells; the shared rows from
`extraction__55254a04aa1f/rows.jsonl`) and the PopQA+TriviaQA answerable pool
(dial cells). Decode: sampled (per Amendment SR: greedy understates effects),
seed 20260701, `max_new_tokens` 128 initial / 96 revision, chat template from
the model's own tokenizer.

## Stage 1 cells (Qwen3.5-4B; single local GPU, sequential)

| cell | arm | signal | position | contents |
|---|---|---|---|---|
| AA-1 | A | gate | anchor | α sweep {−4,−2,−1,0,+1,+2,+4} × (300 unknown + 300 known) |
| AA-2 | A | gate | end | α\* only × same items |
| AA-3 | A | dial | end | α sweep (same values) × 500 answerable |
| AA-4 | A | dial | anchor | α\* only × same items |
| AA-5 | B | gate | early | real + placebo × (300 unknown + 300 known) |
| AA-6 | B | gate | late | real + placebo × same items |
| AA-7 | B | dial | late | real + placebo × 500 answerable |
| AA-8 | B | dial | early | real + placebo × same items |

α\* = the smallest |α| in the sweep that meets the effect gate AND the coherence
floor on the predicted-position cell (chosen from AA-1 for gate, AA-3 for dial).
The off-position cells run at α\* so the position contrast compares like with
like. The α grid and eval-subset sizes are **authorized knobs** (tier-3 tuning
under this amendment if a sweep needs refinement); the gates, falsifiers, and
metric definitions are **not**.

**Coherence floor (all cells):** degenerate-output rate ≤ 5% — an output is
degenerate if empty, a single repeated n-gram, or unparseable by the same
answer/abstention grader used in Amendment Z. A cell whose only behavioral
effects occur at α values violating the floor counts toward Falsifier 3, not as
an effect.

## Prediction (pre-stated)

Writing the **gate** signal at the **anchor** raises appropriate abstention on
unknown questions without lowering answerable accuracy; writing the **dial**
signal at the **end** raises appropriate revision of wrong answers. Effects are
**muted at the wrong position**, and the pattern holds for **both** the
sub-symbolic write (Arm A) and the symbolic write (Arm B beyond placebo) —
convergent causal validity for the anchor-vs-end account.

## Locked gates (Stage 1, Qwen3.5-4B)

Bootstrap 95% CIs (2000 resamples) throughout; "vs control" means α=0 for Arm A
and the placebo arm for Arm B (never a no-injection baseline).

- **AA-G1 (Arm A, gate@anchor):** at some α on the sweep meeting the coherence
  floor: unknown-question final abstention ≥ **+15 points** vs α=0, CI excludes
  0, AND answerable final accuracy drop ≤ **5 points** at that same α.
- **AA-G2 (Arm B, gate@early):** real vs placebo: unknown-question final
  abstention ≥ **+10 points**, CI excludes 0, AND answerable accuracy drop
  ≤ **5 points** vs placebo.
- **AA-G3 (Arm A, dial@end):** at some α meeting the coherence floor:
  appropriate-revision discrimination ≥ **+10 points** vs α=0, CI excludes 0.
- **AA-G4 (Arm B, dial@late):** real vs placebo: appropriate-revision
  discrimination ≥ **+10 points**, CI excludes 0.
- **AA-G5 (position asymmetry, PRIMARY):** for each arm×signal combination that
  passes its effect gate (G1–G4), the same metric at the predicted position
  minus at the wrong position (both at α\*/real) is **> 0 with CI excluding 0**,
  in **≥ 3 of 4** combinations.

**Adequacy:** ≥ 40 wrong AND ≥ 40 correct initial answers in each dial cell;
≥ 100 unknown items answered under control in each gate cell — otherwise the
affected gate is UNDERPOWERED (reported, excluded from that gate's verdict), not
PASS/FAIL.

## Success / falsifiers (LOCKED before running)

- **STAGE-1 SUCCESS:** AA-G5 (PRIMARY) passes AND at least one gate from each
  arm (G1 or G2; G3 or G4) passes. Interpretation: the trust axis is causally
  usable and position-locked as the readout work predicted.
- **FALSIFIER 1 (channel stays shut):** neither arm moves either metric past its
  effect gate at ANY α / injection meeting the coherence floor → the R-style
  channel cannot be forced open even mechanically; the steering line for this
  model family dies here.
- **FALSIFIER 2 (position does not matter):** effect gates pass but AA-G5 fails
  in ≥ 2 of the passing combinations (wrong-position effects statistically
  indistinguishable from predicted-position effects) → the anchor-vs-end
  asymmetry is about decodability, not causal use; the causal reading of the
  anchor-vs-end account is falsified (publishable negative; Paper 5 pivots to
  reporting it).
- **FALSIFIER 3 (no operating point):** behavior moves only at α values that
  violate the coherence floor → no usable steering regime; report the full
  α-vs-coherence curve as the finding.
- **Stage-2 bar (pre-stated now, run later):** the Stage-1 passing pattern
  replicates (same gates) on **≥ 2 of 3** remaining families; Arm B cells run
  only on families whose chat template supports a think block, with any
  exclusion recorded as INELIGIBLE (excluded from the denominator), never
  silently substituted.
- **No goalposts move after the result.** An ambiguous result is reported as
  ambiguous.

## Honest-scope caveats (pre-stated)

- Steering can surface latent uncertainty; it cannot inject knowledge the model
  lacks. The realistic win is *surfacing*, not *knowing*.
- Proportional (uncertainty-scaled) α is the default precisely to avoid
  degrading confident-correct answers into hedging; the accuracy floor in
  G1/G2 checks this.
- Arm B effects beyond placebo are the claim; the placebo itself moving behavior
  (generic caution priming) is expected and is NOT evidence for the signal.
- Single family in Stage 1; nothing generalizes until Stage 2.

## Method / harness

`run_arm_a.py` and `run_arm_b.py` (to be added on this branch, CPU-unit-tested
in the scaffold's style) orchestrate: model load via the Amendment-X hardened
loader → direction load → per-item initial + revision passes with the
intervention at the cell's position → grading with the Amendment-Z grader →
per-cell JSON (all α points, all items, seeds, degenerate-output flags) under
`steering/results/` (gitignored; scored roll-up JSON tracked at probe root as
`amendment_aa_qwen3.5-4b_result.json`). Lane: local Docker GPU (docker.exe /
Docker Desktop, F:\ mount), LM Studio unloaded first, `--user 0:0` for 9P
mkdir. Single GPU — cells strictly sequential.

## §7 Results (filled per cell as runs complete)

*(empty — no run authorized yet)*
