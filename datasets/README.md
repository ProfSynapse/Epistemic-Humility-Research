# Local dataset store — epistemic humility research

Everything here is committed to the repo (the execution container is ephemeral).
Each dataset folder carries a `dataset.md` with Obsidian-style frontmatter for
querying. Re-fetch provenance is recorded per dataset.

## Local now (fetched 2026-06-09, GitHub sources)

| Folder | Dataset | License | Role |
|---|---|---|---|
| `selfaware/` | SelfAware (3,369 Q) | CC-BY-SA-4.0 (data) | Abstention eval |
| `truthfulqa/` | TruthfulQA (817 Q) | Apache-2.0 | Truthfulness eval |
| `sycophancy-eval/` | Sharma et al. sycophancy-eval | MIT per HF mirror (no LICENSE in repo — verify) | Sycophancy eval |
| `anthropic-sycophancy/` | Perez et al. model-written sycophancy evals | CC-BY-4.0 | Sycophancy eval |
| `sayself/` | SaySelf stage-1 SFT (8,603 ex) + small eval sets | MIT | Reference train data |
| `say-i-dont-know-outputs/` | Cheng et al. per-method TriviaQA test outputs (SFT/DPO/PPO/BoN/HIR) | unstated | **Meta-analysis reanalysis** — lets us independently recompute truthful rates |

## Local now (fetched 2026-06-10, HF hub via `scripts/fetch_datasets.py`)

| Folder | Dataset | License | Role |
|---|---|---|---|
| `triviaqa-rc-nocontext/` | TriviaQA rc.nocontext validation (17,944 Q) | unknown on HF; research use per official release | Gold aliases for exact truthful-rate recomputation; known/unknown split substrate |
| `mmlu/` | MMLU all test+validation (14,042 + 1,531) | MIT | OOD eval + correctness splits |
| `popqa/` | PopQA test (14,267 Q) | untagged on HF; GitHub MIT | Long-tail "likely unknown" proxy eval |
| `kuq/` | KUQ knowns_unknowns + unknowns_all (6,884 + 6,363) | MIT | Known-unknown eval with categories |
| `coconot/` | CoCoNot original train/test + contrast test (11,477 + 1,001 + 379) | untagged on HF (AI2) | Noncompliance + over-refusal contrast sets |
| `abstentionbench-repo/` | AbstentionBench repo snapshot (loading script only — see its dataset.md) | CC-BY-NC-4.0 | Holistic abstention eval, needs materialization |

## Local now (fetched 2026-06-10, released research artifacts — second wave)

| Folder | Dataset | License | Role |
|---|---|---|---|
| `factscore-data/` | FActScore released data: 549 human-annotated generations (16,040 labeled atomic facts; InstructGPT/ChatGPT/PerplexityAI) + 12 LMs x 500 raw bio generations + 12 LMs auto-scored atomic-fact labels (5,476 responses) | MIT | **Meta-analysis reanalysis** — respond-rate vs. factual-precision operating points across RLHF ladder + SFT-only models |
| `abstentionbench-results/` | AbstentionBench aggregated results: 23 models x 31 subsets, abstention precision/recall/F1, incl. Tulu-3 Base→SFT→DPO→PPO ladder at 8B+70B (624 rows) | CC-BY-NC-4.0 | **Meta-analysis reanalysis** — over-refusal trade-offs + scale/post-training comparisons; raw per-question outputs were never released |
| `reward-calibration/` | PPO-M (Leng et al.) calibration preference mixture, stratified 2,400/25,524 sample + PPO prompt collection sample 1,020/20,480 | Apache-2.0 (repo); HF datasets untagged — verify | Reference train data — only released confidence-calibration preference pairs; KTO recipe template |
| `repos-staging/` | Shallow clones pending lead disposition (see its README.md) | per-repo | staging only — do not commit `.git` dirs |

Also: `sycophancy-eval/dataset.md` gained a 2026-06-10 verification note —
upstream repo confirmed to contain prompts only, NO released model outputs.

## Still pending

| Dataset | Source | Why we want it |
|---|---|---|
| Natural Questions | HF `google-research-datasets/natural_questions` | OOD eval substrate (large — subset before committing) |
| AbstentionBench materialized data | GitHub `facebookresearch/abstentionbench` pipeline | Repo snapshot has no data; some constituents (GPQA) gated |
| Idk train datasets | Google Drive via `OpenMOSS/Say-I-Dont-Know` | Model-specific Idk SFT + preference data (we will regenerate for Qwen anyway) |
| R-Tuning data | Google Drive via `shizhediao/R-Tuning` | Refusal-aware train sets |
| LACIE preference pairs | `esteng/pragmatic_calibration` `data.tar.gz` (60 MB, cloned to scratch but not committed) | DPO calibration pairs reference |

Note: for our experiment the known/unknown splits MUST be regenerated against our
own base models (Qwen2.5-3B/7B-Instruct) — published splits are model-specific
by construction. The blocked items above are for evaluation substrates and
cross-checks, not as-is training data.
