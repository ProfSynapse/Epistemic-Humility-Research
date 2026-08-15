# Prompt-vs-training disentanglement panel: base counterfactuals and instruction-free abstention

Status: DRAFT (2026-08-14). Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The cold-GRPO red-team audit (2026-08-14, recorded in
`experiments/grpo-cold-start-induction/NOTEBOOK.md`) established three facts:

1. Both of the program's eval contracts contain an abstention instruction in
   the system prompt. The response-confidence contract (training data of all
   four objectives; eval of every GRPO-touching arm) explicitly instructs:
   say "I don't know the answer" rather than guessing. The plain-answer
   contract (the cold-start confirmatory block's eval default,
   `archive/experiment/phase1/eval/run_eval.py:50`) instructs: "if you do
   not [know], say so plainly."
2. No raw-base (untrained, no-adapter) SelfAware eval exists anywhere in the
   program, under any contract. The base counterfactual for every
   "training X induces/fails-to-induce abstention" claim is unmeasured.
3. The prompt provably does heavy lifting: in the cold-GRPO run's step-1
   rollouts (untrained base under the RC contract, T=1.35), 59.3% of
   unknown-labeled rollouts already refused.

Prompt and training are therefore two crossed factors, and the program has
only measured one margin of the table. Every trained checkpoint already
exists, so every missing cell is an eval-only run. This panel fills the
missing cells. It is measurement, not hypothesis test: it carries an
integrity gate (PV-G0) and pre-stated interpretation bands (R1-R4) that fix
how paper-2 prose responds to the numbers, but no headline gate, because the
design's purpose is to word existing claims honestly, not to win a bet.

Exploratory tier (tier-2), never pooled with the confirmatory headline
matrix. Its numbers feed: the cold-GRPO cell's Outcome wording, paper 2's
claim scoping (the "induces" verb program-wide), and the base-row anchor for
paper-2 operating-point tables.

## Design

Instrument: `archive/experiment/phase1/eval/run_eval.py` verbatim (vLLM,
greedy, temperature 0.0, full SelfAware set n=3,369, standard scorer and
refusal detection). No engine exception: this is a plain generation-bearing
eval and runs under the program's forced vLLM default. Only the
`prompt.system` block and the `arms` list vary across the three pinned
configs. Refusal detection operates on answer text and is prompt-independent,
so unprompted abstention is still counted.

Three prompt levels:

- **P-rc**: the response-confidence contract, verbatim from the GRPO-layer
  evals (pinned in `configs/eval_panel_prc_local_4b.yaml`).
- **P-plain**: the plain-answer harness default, verbatim
  (`configs/eval_panel_pplain_local_4b.yaml` pins it explicitly rather than
  relying on the in-code default, so the measurement surface is committed).
- **P-struct**: minimal structure-only prompt, frozen at signing. Two configs
  with byte-identical prompt text, because `run_eval.py` loads one base model
  per config: `configs/eval_panel_pstruct_cold_local_4b.yaml` (raw bnb-4bit
  base: arms 3-7) and `configs/eval_panel_pstruct_warmed_local_4b.yaml`
  (merged clean-SFT seed-1 base, the warmed cell-of-record pairing: arms
  8-9). Wording:

  > Answer the user's question. Return only a JSON object with exactly two
  > keys: "answer" and "response_confidence". The "answer" value is your
  > answer. The "response_confidence" value is your probability from 0 to 1
  > that your response is appropriate. Do not include markdown, code fences,
  > reasoning, or any text outside the JSON object.

  Design constraints honored: no abstention affordance anywhere (the RC
  contract's "or abstention text" clauses removed from both key
  descriptions); JSON schema retained so the structured-output machinery and
  scorer run unchanged.

Eleven arms, run in registered priority order (1-2 unblock the cold-GRPO
resolve first):

| # | Checkpoint | Prompt | Question it answers |
|---|-----------|--------|---------------------|
| 1 | raw base (no adapter) | P-rc | counterfactual for cold GRPO |
| 2 | raw base | P-plain | counterfactual for "only SFT induces abstention" |
| 3 | raw base | P-struct | spontaneous-abstention floor |
| 4 | cold SFT seed 1 | P-struct | internalization test for the arm that "worked" |
| 5 | cold DPO seed 1 | P-struct | internalization test for an arm read as "failed" |
| 6 | cold KTO seed 1 | P-struct | same |
| 7 | cold GRPO seed 1 | P-struct | did GRPO internalize or just comply? |
| 8 | clean-SFT (merged) | P-struct | warmed-layer anchor without instruction |
| 9 | clean_sft_grpo_v2 seed 1 | P-struct | warmed GRPO without instruction |
| 10 | cold DPO seed 1 | P-rc | same-contract cold comparison (closes the cross-contract seam) |
| 11 | cold KTO seed 1 | P-rc | same |

Checkpoint identities are pinned in the three configs; cell-of-record
provenance for each adapter is recorded in NOTEBOOK at scaffold time with the
doc line that establishes it. Budget: ~11 full SelfAware evals at ~25 min
each on the local 3090, ~4-5 GPU-hours total, no training, no cloud spend.

## Prediction

Disclosure (no blind guess is possible): the registrants have seen the
cold-GRPO step-1 rollout diagnostics and every trained arm's instructed-eval
numbers before this registration. Informed predictions, stated anyway
(refusal recall on unknown-labeled rows, n=1,032):

- Lead: base+P-rc lands 55-80%; base+P-plain lands materially above zero
  (20-50%); base+P-struct < 10%; cold-SFT+P-struct retains > 50% of its
  instructed recall; cold-DPO/KTO+P-struct near zero; cold-GRPO+P-struct
  retains a smaller fraction than cold SFT retains (compliance-heavy
  hypothesis).
- PI: expects the prompt to carry much of the measured behavior (raised the
  concern that the design reads as a prompt intervention entangled with
  training).

## Falsifier

Instrument-level only (this is a measurement cell): PV-G0 fails — any arm
with incomplete row coverage, missing config-sha stamping, or a
refusal-detection sanity failure — and is reported straight as a stop, not
retried silently. There is no headline falsifier; the interpretation bands
below are frozen so the prose response to any outcome is fixed in advance.

## Gates and interpretation bands

- **PV-G0 (integrity precondition, per arm):** every attempted row receives a
  recorded disposition (n=3,369 per arm); `config_sha` stamped on every row
  matches the pinned config; the arm's scored rows parse under the standard
  scorer with the parse-failure path recorded. Any failure stops that arm's
  use, never retunes it.
- **Interpretation bands (frozen at signing; prose rules, not gates):**
  - R1. If base+P-plain recall >= 20%: the confirmatory block's "only SFT
    induces abstention" is reworded program-wide; cold DPO/KTO become
    "suppress instruction-elicited abstention"; the verb "induces" is
    retired for any instructed-prompt measurement.
  - R2. If base+P-rc recall >= 60%: the cold-GRPO Outcome verb becomes
    "preserves and sharpens instruction-elicited abstention" (its
    falsifier-zone call unchanged); if < 60%, "amplifies", with the
    step-1-vs-final delta quoted.
  - R3. If a trained arm's P-struct recall >= 30% while base+P-struct < 10%:
    that arm's training is described as internalizing abstention beyond
    instruction compliance.
  - R4. The 20/60/30/10 thresholds are fixed here and never retuned after
    the result. Outcomes between bands are reported descriptively without a
    mechanism verb.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | base+P-rc 55-80%; base+P-plain 20-50%; base+P-struct <10%; R3 fires for cold SFT; cold GRPO mostly compliance |
| user | prompt carries much of the measured abstention |

## Budget

~11 full SelfAware evals on the local 3090 (~25 min each, ~4-5 GPU-hours
total). Eval-only; no training. Launch requires explicit PI approval after
signing.

## Outcome

Run 2026-08-14, local RTX 3090, four config-level launches (two aborted
false starts before the first config — wrong container entrypoint, then an
arm-label validation failure fixed by pre-launch repin; both logged in
NOTEBOOK with zero run artifacts). All 11 arms completed.

**PV-G0 PASS on all 11 arms**: full coverage n=3,369 per arm; row-stamped
`config_sha` matches the pinned config bytes (lead-verified per config);
scorer parse path recorded.

Per-arm refusal recall / over-refusal (%, unknown-labeled n=1,032; full
metrics in `analysis-committed/`):

| Checkpoint | P-rc | P-plain | P-struct |
|---|---|---|---|
| raw base | 90.89 / 65.38 | 0.00 / 0.04 | 0.00 / 0.09 |
| cold DPO seed 1 | 94.48 / 73.34 | — | 0.00 / 0.09 |
| cold KTO seed 1 | 93.99 / 60.89 | — | 0.00 / 0.04 |
| cold SFT seed 1 | — | — | 69.57 / 47.63 |
| cold GRPO seed 1 | (85.66 / 60.89, its own cell) | — | 0.00 / 0.09 |
| clean-SFT merged (RC recipe) | — | — | 69.48 / 49.25 |
| SFT→GRPO v2 seed 1 | — | — | 77.42 / 58.71 |

**Bands:** R1 did NOT fire (base+P-plain 0.00 < 20): the confirmatory
block's "only SFT induces abstention" stands under its own contract. R2
FIRED (base+P-rc 90.89 >= 60): the cold-GRPO outcome verb is "preserves and
sharpens instruction-elicited abstention". R3 FIRED (cold SFT 69.57 >= 30
with base 0.00 < 10): SFT internalizes abstention beyond instruction
compliance. Additional descriptive findings: cold DPO/KTO track the base
under every prompt (0≈0 plain/struct; 94≈91 RC) — the 0-to-94 reversal of
the same checkpoint across contracts is the panel's sharpest single
exhibit; two independent SFT recipes internalize at near-identical levels
(69.57 vs 69.48); GRPO on an SFT base deepens internalization (77.42 vs its
base's 69.48) while cold GRPO internalizes nothing (0.00).

**Scorer-scope audit (descriptive, scorer not retuned):** a row-level audit
(gitignored `analysis/pstruct_refusal_audit/`, lead spot-checked) found the
four 0.00 P-struct readings undercount natural-language abstention
("not possible to determine...", mostly on insufficient-information math
items) that the pinned markers do not match; honest band ~4-6% recall for
base/DPO/KTO/GRPO under P-struct. All conclusions survive (the R3 base
ceiling is 10%); SFT-side refusals were audited in the opposite direction
with zero false positives in 60 sampled rows. Papers quote both numbers.

**One-sentence verdict:** crossing prompts with checkpoints shows the
response-confidence contract alone elicits near-ceiling abstention from the
untrained base (90.89% recall) while no prompt elicits any from it under
plain or structure-only conditions (0.00 scored, ~4-6 audited), and only
SFT-trained weights carry abstention without the instruction (69.6%,
deepened to 77.4 by GRPO on top) — so training-regimen abstention claims
are meaningful only relative to the prompt condition, and the program's
frame becomes scaffolded training with scaffold-removed measurement.
