# Amendment A Transition Analysis

Source artifacts: persisted local `metrics.json`, `scored_rows.jsonl` when present, and `comparisons/mcnemar.csv` files from the Amendment A SelfAware full and broader OOD eval directories.

Row-identity note: every compared arm for these eval sets includes `scored_rows.jsonl`, so all transition counts below are exact. Rows are aligned by `eval_set` plus `row_index`; `id` is treated as metadata only.

## SelfAware Full

The row-level transition table below is from the original seed-1 Amendment A
SelfAware eval where `sft_merged`, `sft_dpo`, and `sft_kto` were evaluated in
the same run with persisted scored rows.

| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |
|---|---:|---:|---:|---:|---:|---:|
| `sft_merged->sft_dpo` | 429 | 145 | 377 | 1113 | 95 | 52 |
| `sft_merged->sft_kto` | 125 | 70 | 91 | 322 | 37 | 34 |
| `sft_dpo->sft_kto` | 106 | 335 | 22 | 1 | 1 | 84 |

## Sequential DPO SelfAware Seed Expansion

Full SelfAware DPO-only evals for `SFT -> DPO` seeds 2 and 3 completed on
2026-06-16 while `SFT -> KTO` seed 2 trained in parallel. The original seed-2
attempt is retained below only as an excluded provenance item because it used a
bad SFT merge. The clean seed-2 low-memory rerun is the seed-2 result to compare
against seeds 1 and 3.

| Arm | Results dir | Refusal recall | Answer on unknown | Over-refusal | Correct on known | Truthful |
|---|---|---:|---:|---:|---:|---:|
| `sft_dpo` seed 1 | `results_amendment_a_selfaware_full_local_4b` | 48.84 | 51.16 | 13.95 | 25.61 | 30.25 |
| `sft_dpo` seed 2, excluded bad-merge attempt | `results_amendment_a_selfaware_full_seed2_sft_dpo_local_4b` | 2.23 | 97.77 | 0.04 | 23.54 | 17.01 |
| `sft_dpo` seed 2, clean low-memory rerun | `results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b/sft_dpo_seed2_lowmem__selfaware/metrics.json` | 65.89 | 34.11 | 18.36 | 25.84 | 34.82 |
| `sft_dpo` seed 3 | `results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b` | 43.70 | 56.30 | 11.42 | 24.69 | 28.55 |
| clean seed mean from listed seed metrics | n/a | 52.81 | 47.19 | 14.58 | 25.38 | 31.21 |

The excluded seed-2 attempt is confounded and should not be counted as clean
sequential evidence. The DPO training log showed a DPO run from the earlier
merged SFT seed2 path, but a post-hoc sanity eval of that merged SFT seed2 base
alone on the same 192-row SelfAware slice gave refusal_recall 6.32,
over_refusal 4.12, and truthful 12.5. That is incompatible with the
adapter-on-base SFT seed2 full SelfAware result of refusal_recall 87.4. The
earlier nonzero/OSError seed2 merge should be treated as a semantic merge
failure despite structural file validation.

The clean seed-2 low-memory rerun used the behaviorally verified
`merged-16bit-lowmem-20260616` SFT seed2 base and wrote 3,369 SelfAware rows =
1,032 unknown / 2,337 known. Its contamination scan for `<think>`, `</think>`,
and `reasoning_content` found no matches. Plain read: clean seed 2 is plausible
but stronger than clean seeds 1 and 3, with higher refusal recall, higher
over-refusal, and higher truthful score. Across the three clean seeds,
sequential DPO is directionally different from cold-start DPO: it reduces SFT's
known-question over-refusal while retaining some unknown refusal, but it still
does not cleanly recover the SFT abstention pattern.

Arithmetic note: the handoff-supplied clean mean for refusal recall was 52.48,
but the listed per-seed values in this report average to 52.81. The other clean
means above match the supplied values. Reconcile the refusal-recall aggregate
before using it in a publication-grade table.

## KUQ Supporting Slice

| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |
|---|---:|---:|---:|---:|---:|---:|
| `sft_merged->sft_dpo` | 57 | 11 | 54 | 116 | 10 | 3 |
| `sft_merged->sft_kto` | 17 | 4 | 14 | 16 | 4 | 3 |
| `sft_dpo->sft_kto` | 11 | 44 | 2 | 0 | 0 | 9 |

Interpretation guardrail: CoCoNot, TruthfulQA, and PopQA in the broader directory remain useful for aggregate refusal/over-refusal pressure, but not for the SelfAware known/unknown transition questions. CoCoNot answer aliases are empty in the local contrast file, so correctness is intentionally not interpreted there.

## Interpretation

Sequential DPO is mixed, not a clean recovery. On seed-1 full SelfAware it reduced known over-refusal sharply, but the persisted evidence implies 377 unknown rows where `sft_merged` correctly refused and `sft_dpo` answered instead. KUQ supports the same direction: 54 of the 57 exact `sft_merged`-truthful / `sft_dpo`-untruthful flips came from unknown rows where DPO answered after SFT refused. The original seed-2 attempt was not clean evidence because its merged SFT base was behaviorally bad; the clean low-memory seed-2 rerun is now the valid seed-2 comparator and is plausible but stronger than seeds 1 and 3.

The known-question recovery side is weaker than the aggregate over-refusal drop suggests. Full SelfAware has 1,113 fewer known refusals for `sft_dpo` than `sft_merged`, but only 67 net additional known correct answers in the aggregate. The exact row-level counts show 95 known rows where SFT refused and DPO answered correctly. These exact row-level artifacts show how much of the over-refusal reduction became useful correct recovery versus incorrect answering.

Sequential KTO is closer to SFT than DPO. On full SelfAware it can account for 91 unknown SFT-refusal to KTO-answer losses, versus 377 for DPO, and its exact truthful loss against SFT is much smaller (125 vs 429). The cost is that KTO retains high known over-refusal: aggregate SelfAware over-refusal is 48.31 for KTO versus 13.95 for DPO and 61.49 for SFT.

## Recommendations

Use this as row-level local evidence only. Do not fold it into v0.3 headline/protocol claims.

The next experimental direction depends on the pending KTO seed expansion. If KTO is more seed-stable, prioritize KTO or KTO sensitivity. If KTO shows similar instability, use deliberately scoped sensitivity around the sequential preference stage rather than a binary keep/drop decision. DPO deserves lower-intensity variants because it has the desired over-refusal pressure but overshoots into unknown-answering and lower known correctness. Reasonable axes are lower DPO beta, lower LR, fewer effective epochs/steps, and possibly smaller downstream LoRA rank/alpha if the goal is a gentler correction to SFT.

KTO deserves a separate sensitivity axis only if the priority is preserving abstention first. It retained more unknown refusal but did not reduce over-refusal enough in this local run, so KTO variants should target stronger known-question recovery without collapsing unknown refusal.

Future live eval runs should continue to persist `generations.jsonl` or a compact per-row scored table (`id`, question/order key, label, refused, correct, truthful) for each arm. Without that, exact transition analysis is limited to McNemar truthful flips plus feasible bounds from aggregate margins.
