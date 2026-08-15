# Completing the prompt-condition crossing

Status: DRAFT (2026-08-15). Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 2's Limitations section names three places where the prompt-condition
crossing is incomplete. The PI reviewed that paragraph on 2026-08-15 and
authorized running two of them (the third, instructed readings for cold
DPO/KTO seeds 2/3, was assessed as low-information and skipped):

- **Gap 3 (the open question):** the warmed preference arms, SFT followed by
  DPO and SFT followed by KTO (Amendment A, three seeds each), were never
  evaluated under the structure-only prompt. The study currently cannot say
  whether a preference stage applied to an internalized checkpoint preserves,
  erodes, or deepens what the supervised stage put in the weights. The paper
  itself calls this "the most obvious next measurement."
- **Gap 1 (contract symmetry for Section 4.5):** there is no
  response-confidence reading for the cold-start SFT arms and no plain-answer
  reading for the warmed arms (clean-SFT merged, SFT then GRPO v2), so the
  instructed-against-instruction-free pairs in Section 4.5 compare across
  contracts. These five evals convert that comparison to single-contract.

Eval-only: every checkpoint already exists; no training. Exploratory tier-2,
reported with the paper's prompt-crossing layer, never pooled with the
confirmatory headline matrix.

## Design

Instrument identical to the panel and seed-robustness cells: `run_eval.py`,
vLLM, greedy, full SelfAware (n=3,369 per arm), prompts byte-identical to the
pinned panel configs (P-struct, response-confidence contract) and the pinned
headline eval config (plain-answer contract). Three configs, eleven arms:

| Block | Arms | Base + adapter (cell of record) | Prompt |
|---|---|---|---|
| Gap 3 | seq_sft_dpo_seed{1,2,3}_pstruct | per-seed SFT merge + Amendment A sft_dpo adapter | P-struct |
| Gap 3 | seq_sft_kto_seed{1,2,3}_pstruct | per-seed SFT merge + Amendment A sft_kto adapter | P-struct |
| Gap 1a | cold_sft_seed{1,2,3}_rc | raw base + headline SFT adapter | response-confidence |
| Gap 1b | clean_sft_merged_pplain | clean-SFT merged 16-bit, no adapter | plain-answer |
| Gap 1b | sft_grpo_v2_seed1_pplain | clean-SFT merged + GRPO-v2 adapter | plain-answer |

The seq arms load each seed's adapter on the same 16-bit merge of that seed's
cold-start SFT adapter that Amendment A trained on (rebuilt if not on disk,
per the recipe in the run records; the rebuild is part of the instrument, not
a knob).

## Prediction

- Gap 3: all six seq preference arms stay at or above the 30% internalization
  floor under P-struct (expected band 40-80%); DPO arms at or below their own
  seed's cold-SFT parent value (repositioning toward answering), KTO arms
  near parent.
- Gap 1a: cold SFT seeds under the response-confidence contract read at or
  above their plain-answer instructed values (83.91/87.40/92.34); expected
  85-95%.
- Gap 1b: warmed arms under plain-answer land within about 10 points of their
  response-confidence readings.

## Falsifier

Any seq preference arm below 30% refusal recall under P-struct: a preference
stage applied after SFT erodes internalized abstention below the registered
floor, and paper 2's Section 4.3 repositioning story must add an erosion
finding. (Secondary, reported straight either way: any seq arm more than 10
points above its parent is read as deepening; gap-1 readings that break the
expected contract ordering are reported as-is. No registered claim rides on
gap 1; it exists to make Section 4.5 single-contract.)

## Gates

- PC-G0 (integrity precondition, per arm, verbatim from the panel's PV-G0):
  full coverage n=3,369; row-stamped config_sha matches pinned bytes; scorer
  parse path recorded. Any failure stops that arm, never retunes it.
- PC-G1 (classification rule for the six seq arms, fixed here before the
  run): each seq arm is compared to its own seed's cold-SFT P-struct parent
  value (69.57 / 76.94 / 79.36, from the panel and seed-robustness cells).
  Below 30% = erosion below the floor (falsifier). In [30%, parent - 10pp) =
  partial erosion, reported as such. Within +/-10pp of parent = preserved.
  Above parent + 10pp = deepened. The 30% floor is the panel's frozen R3
  value reused unchanged; the 10pp band is fixed here and never retuned.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | all six seq arms >= 30%, DPO at/below parent, KTO near parent; cold SFT RC 85-95%; warmed plain within ~10pp of RC |
| user | approved the run 2026-08-15; no directional call recorded |

## Budget

Eleven full SelfAware evals, ~4.5-5 GPU-hours on the local RTX 3090,
eval-only, GPU currently idle. Run authorized by the PI 2026-08-15
("run gap 3 and 1").

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
