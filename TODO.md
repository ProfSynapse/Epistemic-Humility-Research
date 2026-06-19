# TODO

## Training / Eval Matrix

| Arm | Seed | Recipe | Training Run | Eval Run |
|---|---:|---|---|---|
| `sft_dpo_kto` = SFT -> DPO merge -> KTO | 1 | [ ] | [ ] | [ ] |
| `sft_dpo_kto` = SFT -> DPO merge -> KTO | 2 | [ ] | [ ] | [ ] |
| `sft_dpo_kto` = SFT -> DPO merge -> KTO | 3 | [ ] | [ ] | [ ] |
| `sft_kto_dpo` = SFT -> KTO merge -> DPO | 1 | [ ] | [ ] | [ ] |
| `sft_kto_dpo` = SFT -> KTO merge -> DPO | 2 | [ ] | [ ] | [ ] |
| `sft_kto_dpo` = SFT -> KTO merge -> DPO | 3 | [ ] | [ ] | [ ] |
| `grpo` = GRPO | 1 | [ ] | [ ] | [ ] |
| `grpo` = GRPO | 2 | [ ] | [ ] | [ ] |
| `grpo` = GRPO | 3 | [ ] | [ ] | [ ] |
| `sft_grpo` = SFT -> GRPO | 1 | [ ] | [ ] | [ ] |
| `sft_grpo` = SFT -> GRPO | 2 | [ ] | [ ] | [ ] |
| `sft_grpo` = SFT -> GRPO | 3 | [ ] | [ ] | [ ] |

## Later Mixes

- [ ] Add the remaining GRPO/DPO/KTO mix matrix and recipes later.

## Unknown-Question Category-Regimen Follow-Up

- [ ] Label always-unanswered unknown questions so category-regimen analysis covers the full unknown-question pool, not only questions answered by at least one arm.
- [ ] Run category-level statistical checks for SFT/DPO/KTO answer-on-unknown differences before treating the exploratory pattern as evidence.
- [ ] Review representative examples by semantic category and regimen, especially categories where DPO sharply increases answering.
- [ ] Validate v3 semantic labels before publication-grade claims; treat current broad labels and `answer_form` fields as exploratory until checked.
