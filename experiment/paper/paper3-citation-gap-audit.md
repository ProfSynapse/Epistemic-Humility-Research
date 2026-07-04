# Paper 3 citation-gap audit (KG sweep, 2026-07-04)

Two parallel sweeps over all 179 `library/notes/` entries against P3's five
claim pillars: (P1) internal-vs-stated gap, (P2) training-resistance,
(P3c) causal-but-asymmetric steering, (P4) signal predates post-training,
(P5) readout-not-training framing. P3 currently cites 9 arXiv ids inline
(all present in the KG). Everything below is IN the KG already; ids verified
against `library/notes/` on 2026-07-04. Feeds the bibliography-compilation
task on the paper3-final branch.

## Tier 0 — datasets/methods the paper USES (must cite; currently uncited)

| id | note | where in P3 |
|---|---|---|
| 1705.03551 | triviaqa-dataset | §3 setup: training/held-in cells built from TriviaQA-RC no-context |
| 2305.18153 | selfaware-know-what-they-dont-know | §3 setup: OOD eval surface (n=3369) used throughout |
| 2305.18290 | direct-preference-optimization | §7 DPO arms |
| 2402.01306 | kto-prospect-theoretic | §7 KTO arms |
| 2402.03300 | deepseekmath-grpo | §7 GRPO arms (v1/v2/v3) |

NOT P3 datasets (Paper 4's bibliography, not this one): KUQ (2305.13712),
PopQA (2212.10511), semantic uncertainty (2302.09664) — zero mentions in the
P3 draft.

## Tier 1 — direct prior/concurrent art (related-work §2 must position against)

| id | note | pillar | why |
|---|---|---|---|
| 2310.11877 | curious-case-hallucinatory-un-answerability | P1 | concurrent finding of the same phenomenon: linear probe reads answerability while the output hallucinates; P3 is replication + extension (small model, training-resistance depth) |
| 2410.02707 | llms-know-more-than-they-show | P1 | most direct parallel: internal truthfulness readout (AUROC ~0.97) exceeds what outputs show |
| 2511.12991 | finetuned-llms-know-they-dont-know | P4/P2 | fine-tuning suppresses rather than destroys the boundary structure; independent support for signal-survives-training |
| 2510.09033 | probes-read-recall-not-truth | P1 caveat | the recall-vs-truth-tracking caution P3 §8 already states in prose — this is the citable source |
| 2406.11717 | refusal-single-direction | P3c | one-dimensional causally-steerable refusal direction; the direct prior art for the caution-axis steering result |
| 2312.07000 | alignment-for-honesty | P2 | honesty-SFT failure modes (over-refusal, model-specific IDK labels); baseline for the training-arms story |
| 2401.13275 | can-ai-assistants-know-what-they-dont-know | P2 | IDK-dataset construction on TriviaQA; SFT over-refuses / DPO reduces — the pattern P3 probes deeper |

## Tier 2 — strengthen specific sections

| id | note | pillar | why |
|---|---|---|---|
| 2511.11500 | reinforced-hesitation | P2 §7 | GRPO with ternary abstention rewards fails to couple abstention to confidence — independent replication of P3's RL-arm nulls |
| 2506.09038 | abstentionbench | P2 | reasoning fine-tuning degrades abstention; scaling doesn't help — anchors training-moves-behavior-not-coupling |
| 2604.15574 | why-finetuning-encourages-hallucinations | P2/P4 | mechanistic account (representation interference) of why training moves policy without touching the signal |
| 2311.14648 | calibrated-lms-must-hallucinate | P2 | theoretical bound formalizing why output-channel calibration is structurally hard |
| 2311.13240 | calibration-of-llms-and-alignment | P2 | SFT/RLHF calibration-lifecycle expectations for the §7 arms |
| 2312.06681 | steering-llama-2-contrastive-activation-addition | P3c | CAA steering method + layer localization; methodological neighbor of §5–6 |
| 2308.10248 | steering-with-activation-engineering | P3c | ActAdd; residual-stream steering causality prior art |
| 2309.16042 | activation-patching-best-practices | P3c | methodological guardrails for the orthogonalization/erasure claims |
| 2403.03867 | origins-linear-representations | P1 | theory of why linear probes work at all — grounds the linear-readout premise |
| 2407.08582 | generalizable-truth-probes | P1 | cross-task truth hyperplane; supports axis-robustness framing |
| 2603.17504 | inducing-epistemological-humility-targeted-sft | P2 | training CAN move unknown-behavior (consistent with P3: behavioral abstention installable; coupling is what fails) |

## Tier 3 — borderline (cite if the paragraph already exists)

2202.05262 (ROME), 2104.08696 (knowledge neurons), 2305.01610 (sparse
probing), 2309.08600 (SAEs), 2303.08112 (tuned lens) — mechanistic-background
cluster; one sentence in §2 could take 2–3 of these.
2205.14334 (uncertainty in words), 2306.13063 (can-llms-express-uncertainty),
2405.20974 (SaySelf), 2405.21028 (LACIE), 2406.08391 (taught-to-know) —
verbalized-confidence training line; P3 §7 contrasts with these.
2203.02155 (InstructGPT), 1707.06347 (PPO) — training-lineage context.
2409.18786 (honesty survey), 2407.18418 (abstention survey) — positioning.
2602.02132 (more-to-refusal-than-single-direction) — caveat partner for
2406.11717 if the single-direction framing is used.

## Corrections made while merging the sweeps

- Sweep A listed 2310.06824 (geometry of truth) as missed — it is already
  cited; dropped.
- Sweep A marked 2305.18290 (DPO) as "already excluded" — it is NOT among the
  9 cited ids; promoted to Tier 0.
- Sweep B claimed GRPO's paper is "not in subset" — 2402.03300 is in the KG;
  promoted to Tier 0.
- Both sweeps recommended KUQ/PopQA/semantic-entropy as P3 datasets; the P3
  draft never mentions them (they are Paper 4 surfaces); moved out.
