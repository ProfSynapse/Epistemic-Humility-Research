# Paper 1 Citation Sources

Status: KG-backed citation spine for `paper1-training-regimen-draft-v1.md`

This file records the local knowledge-graph notes used to ground the first real
Paper 1 draft. It is not a bibliography replacement; it is a provenance map from
manuscript claims to local notes.

## KG Queries Used

- `DPO KTO calibration abstention refusal IDK TruthfulQA SelfAware KUQ`
- `direct preference optimization DPO Kahneman Tversky optimization KTO preference optimization`
- `Qwen3 TriviaQA SelfAware KUQ CoCoNot TruthfulQA PopQA abstention benchmark`
- ACL Anthology lookup for `2024.emnlp-main.1205` / UaIT after local KG search
  showed the paper was missing.

## Core Sources

| Manuscript role | Local KG source | External identifier |
|---|---|---|
| IDK data construction and SFT over-refusal tradeoff | `library/notes/2401.13275--can-ai-assistants-know-what-they-dont-know.md` | arXiv:2401.13275 |
| DPO method framing | `library/notes/2305.18290--direct-preference-optimization.md` | arXiv:2305.18290 |
| KTO method framing | `library/notes/2402.01306--kto-prospect-theoretic.md` | arXiv:2402.01306 |
| SelfAware benchmark | `library/notes/2305.18153--selfaware-know-what-they-dont-know.md` | arXiv:2305.18153 |
| KUQ benchmark | `library/notes/2305.13712--kuq-knowledge-of-knowledge.md` | arXiv:2305.13712 |
| UaIT stated-uncertainty training | `library/notes/2024.emnlp-main.1205--llms-learn-uncertainty-uait.md` | ACL Anthology 2024.emnlp-main.1205 / DOI:10.18653/v1/2024.emnlp-main.1205 |
| Verbalized uncertainty in words | `library/notes/2205.14334--teaching-models-uncertainty-in-words.md` | arXiv:2205.14334 |
| Stated/verbalized confidence framing | `library/notes/2305.14975--just-ask-for-calibration.md` | arXiv:2305.14975 |
| TriviaQA dataset description | `library/concepts/datasets/triviaqa.md` | Joshi et al. 2017 / arXiv:1705.03551 |

## Local Result Sources

The manuscript's numeric tables come from generated files under
`experiment/paper/analysis/`, produced by:

```powershell
python experiment\paper\scripts\build_paper1_figures.py
```

The script reads local eval artifacts under `experiment/phase1/eval/results_*`,
including `summary_table.csv`, `metrics.json`, and `scored_rows.jsonl` where
available.
