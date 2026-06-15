# Amendment A Transition Analysis

Source artifacts: persisted local `metrics.json` and `comparisons/mcnemar.csv` files from the Amendment A SelfAware full and broader OOD eval directories.

Row-identity caveat: the live eval outputs in these result directories do not include `generations.jsonl` or another per-row prediction file. Exact row-level transitions cannot be reconstructed from the persisted artifacts. McNemar truthful flips are exact because the eval driver persisted paired truthful-vector discordance counts. The narrower refusal/correctness transitions below are tight feasible count ranges implied by the per-arm margins plus those exact McNemar counts.

## SelfAware Full

| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |
|---|---:|---:|---:|---:|---:|---:|
| `sft_merged->sft_dpo` | 424 | 146 | 348-424 | 1111-1437 | 0-146 | 0-76 |
| `sft_merged->sft_kto` | 124 | 71 | 71-124 | 308-816 | 0-71 | 0-53 |
| `sft_dpo->sft_kto` | 108 | 333 | 0-56 | 0-326 | 0-56 | 52-108 |

## KUQ Supporting Slice

| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |
|---|---:|---:|---:|---:|---:|---:|
| `sft_merged->sft_dpo` | 58 | 11 | 55-58 | 115-144 | 0-11 | 0-3 |
| `sft_merged->sft_kto` | 18 | 4 | 15-18 | 14-43 | 0-4 | 0-3 |
| `sft_dpo->sft_kto` | 11 | 44 | 0-4 | 0-39 | 0-4 | 7-11 |

Interpretation guardrail: CoCoNot, TruthfulQA, and PopQA in the broader directory remain useful for aggregate refusal/over-refusal pressure, but not for the SelfAware known/unknown transition questions. CoCoNot answer aliases are empty in the local contrast file, so correctness is intentionally not interpreted there.

## Interpretation

Sequential DPO is mixed, not a clean recovery. On full SelfAware it reduced known over-refusal sharply, but the persisted evidence implies at least 348 and at most 424 unknown rows where `sft_merged` correctly refused and `sft_dpo` answered instead. KUQ supports the same direction: at least 55 of the 58 exact `sft_merged`-truthful / `sft_dpo`-untruthful flips came from unknown rows where DPO answered after SFT refused.

The known-question recovery side is weaker than the aggregate over-refusal drop suggests. Full SelfAware has 1,111 fewer known refusals for `sft_dpo` than `sft_merged`, but only 70 additional known correct answers in the aggregate. The feasible row-level bounds allow 0-146 known rows where SFT refused and DPO answered correctly, so the current persisted artifacts cannot prove that most over-refusal reduction became useful correct recovery. It could include substantial incorrect answering.

Sequential KTO is closer to SFT than DPO. On full SelfAware it can account for 71-124 unknown SFT-refusal to KTO-answer losses, versus 348-424 for DPO, and its exact truthful loss against SFT is much smaller (124 vs 424). The cost is that KTO retains high known over-refusal: aggregate SelfAware over-refusal is 48.31 for KTO versus 13.95 for DPO and 61.49 for SFT.

## Recommendations

Use this as bounded local Amendment A evidence only. Do not fold it into v0.3 headline/protocol claims.

The next experimental direction is sensitivity around the sequential preference stage rather than a binary keep/drop decision. DPO deserves lower-intensity variants because it has the desired over-refusal pressure but overshoots into unknown-answering and lower known correctness. Reasonable axes are lower DPO beta, lower LR, fewer effective epochs/steps, and possibly smaller downstream LoRA rank/alpha if the goal is a gentler correction to SFT.

KTO deserves a separate sensitivity axis only if the priority is preserving abstention first. It retained more unknown refusal but did not reduce over-refusal enough in this local run, so KTO variants should target stronger known-question recovery without collapsing unknown refusal.

Future live eval runs should persist `generations.jsonl` or a compact per-row scored table (`id`, question/order key, label, refused, correct, truthful) for each arm. Without that, exact transition analysis is limited to McNemar truthful flips plus feasible bounds from aggregate margins.
