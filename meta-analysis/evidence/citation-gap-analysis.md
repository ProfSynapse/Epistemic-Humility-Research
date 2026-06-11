# Citation-graph gap analysis (references-of-references crawl)

Date: 2026-06-11. Method: for each of the 69 arXiv papers in draft-v0's reference
list, the full reference list was pulled from the Semantic Scholar Graph API
(`/paper/arXiv:<id>/references`, 69/69 resolved, including all 2603-2606 IDs).
Referenced papers were aggregated by arXiv ID / title and ranked by how many of
our 69 cited sources cite them; everything already in our bibliography was
excluded. The full ranked list (143 candidates cited by >= 3 of our sources) is
in `citation-gap-candidates.csv`. Raw per-paper reference dumps and the crawl
script are in `/tmp/citegraph/` (not committed; rerunnable).

This complements, and does not duplicate, the 4 post-freeze v1 candidates
already logged in `prisma-flow.md` (2312.17249, 2506.14387, 2603.09117,
2605.25850) — none of those four surfaced independently in this crawl's >= 3x
band, and none of the findings below overlaps them.

## Tier 1 — named or quoted in the draft text but absent from the references

These read as oversights rather than scope decisions: each is the source of a
specific claim or number that appears in the prose.

| arXiv | Paper | Where used in draft | Co-cited by |
|---|---|---|---|
| 2509.25760 | TruthRL: Incentivizing Truthful LLMs via RL | §6.3 gap 3: ternary GRPO reward, CRAG 43.5% → 19.4% hallucination, 5.3% → 37.2% truthfulness — quoted with numbers, no ID anywhere in the draft (every other report-06 GRPO paper in that sentence carries its ID) | 1 (2507.16806) |
| 2505.13787 | Preference Learning with Lie Detectors can Induce Honesty or Evasion | §6.3 gap 3 closing caution: ">85% detector-evading deception once detector TPR falls below ~75%, while off-policy DPO stays under 25%" | 0 |
| 2304.13734 | Azaria & Mitchell, The Internal State of an LLM Knows When It's Lying | §6.3 gap 4: "Azaria-Mitchell internal-state probes at 71-83% accuracy" | 8 |
| 2306.03341 | Li et al., Inference-Time Intervention (ITI) | §6.3 gap 4: "ITI raising TruthfulQA true*informative from 32.5% to 65.1%" | 5 |
| 2212.03827 | Burns et al., Discovering Latent Knowledge (CCS) | §6.3 gap 4: "contrast-consistent search (CCS)" | 4 |
| 2310.01405 | Zou et al., Representation Engineering | §6.3 gap 4: "representation-engineering contrast vectors" | 3 |
| 2310.06824 | Marks & Tegmark, The Geometry of Truth | §6.3 gap 4: "mass-mean truth probes with causal validation" | 1 |
| 2406.15927 | Kossen et al., Semantic Entropy Probes | §6.3 gap 4: "semantic-entropy probes at AUROC ~0.7-0.95, including from pre-generation hidden states" | 1 |
| 2503.03750 | Ren et al., The MASK Benchmark | §5.4: "improved MASK statement-belief consistency" (the acronym pass deliberately left MASK as a proper name, but the benchmark itself is citable) | 0 |

Verify against raw report 06 before adding: the two probing caveats in gap 4
("probes may read knowledge-recall rather than truth-tracking"; "cross-dataset
probe transfer fails on negation-style shifts unless probes are trained on
diverse data") also rest on specific papers — the negation/generalization
result is most likely Levinstein & Herrmann (arXiv:2307.00175), but report 06
should say which sources those sentences came from.

## Tier 2 — high co-citation, topically central; recommended adds

| arXiv | Paper | Why | Co-cited by |
|---|---|---|---|
| 2305.18290 | Rafailov et al., Direct Preference Optimization | DPO is the central treatment of C2/C3 and the headline reanalysis; the method-defining paper is uncited (KTO's is cited) | 22 |
| 2203.02155 | Ouyang et al., InstructGPT | RLHF's defining paper; also InstructGPT is named as a model in the §5.3 FActScore reanalysis | 22 |
| 1706.04599 | Guo et al., On Calibration of Modern Neural Networks | Canonical ECE + temperature-scaling reference; §1 defines ECE and C1's repair argument is temperature scaling | 14 |
| 2302.09664 | Kuhn et al., Semantic Uncertainty | Founding semantic-entropy paper; the draft cites the SE fine-tuning paper (2410.17234) and SE probes but not the method's origin | 14 |
| — | Farquhar et al., Detecting hallucinations using semantic entropy (Nature 2024) | The scaled-up companion; standard pairing with Kuhn et al. | 6 |
| 2311.14648 | Kalai & Vempala, Calibrated Language Models Must Hallucinate | Theoretical companion (overlapping authors) to the cited Why Language Models Hallucinate (2509.04664); speaks directly to the §6.1 calibration-vs-abstention tension | 4 |
| 1705.03551 | Joshi et al., TriviaQA | The reanalysis redistributes TriviaQA-derived gold aliases (`datasets/triviaqa-rc-nocontext/`); dataset papers are customarily cited when their data is redistributed | 18 |
| 2012.14983 | Mielke et al., Linguistic Calibration (Reducing Conversational Agents' Overconfidence) | A *training* intervention on a calibration metric — possibly corpus-eligible under criterion (i), not just citable (pre-LLM BlenderBot setting; would need an eligibility call) | 5 |
| 2405.20974 | SaySelf: Teaching LLMs to Express Confidence | SFT+RL training for calibrated verbalized confidence — also looks corpus-eligible under criterion (i); arrived before the June 2026 freeze (2024) so worth an explicit include/exclude log entry in prisma-flow.md either way | 5 |
| 2204.05862 | Bai et al., HH-RLHF (Training a Helpful and Harmless Assistant) | RLHF-treatment provenance; reports its own calibration measurements | 20 |

## Tier 3 — optional context (cite only if a natural slot exists)

- 2012.00955 — Jiang et al., How Can We Know When Language Models Know? (5x): LM-QA calibration precursor for C1 background.
- Naeini et al. 2015, Bayesian Binning (no arXiv, 5x): the original ECE definition, if the §1 ECE definition wants its primary source.
- 2003.07892 — Desai & Durrett, Calibration of Pre-trained Transformers (4x) and 2106.07998 — Minderer et al., Revisiting Calibration (3x): pre-LLM calibration background.
- 2006.09462 — Kamath et al., Selective QA under Domain Shift (3x): the abstention/selective-prediction lineage ancestor.
- 2110.06674 — Evans et al., Truthful AI (3x): conceptual honesty framing for §2.
- 2401.06730 — Relying on the Unreliable (3x): human-reliance stakes of uncertainty reluctance; fits §1's stakes paragraph.
- 2503.14477 — Calibrating Verbal Uncertainty as a Linear Feature (3x): directly relevant prior art for the gap-4 probe-transfer experiment design.
- 2505.23646 — Are Reasoning Models More Prone to Hallucination? (3x): the reasoning/coherence thread (§3, C4).
- 2311.05232 or 2202.03629 — a hallucination survey (3x each), if §6.4's survey positioning wants the hallucination strand covered alongside abstention and honesty surveys.
- 2112.00861 — Askell et al., A General Language Assistant as a Laboratory for Alignment (11x): the HHH-honesty framing origin.
- 2009.03300 — MMLU (28x): named in §1 prose ("a subset of MMLU"); benchmark citation customary but the GPT-4 report citation arguably covers it.
- Tversky & Kahneman 1992, Advances in Prospect Theory (3x): if gap 1's "prospect-theoretic asymmetric loss aversion" gloss wants its primary source (the KTO paper citation arguably covers it).

## Deliberately not recommended

Generic infrastructure that tops the raw ranking but is out of scope for a
synthesis bibliography unless discussed: GPT-3 (21x), PPO (19x), Llama 2 (18x),
chain-of-thought (14x), self-consistency (13x), LLaMA (12x), LoRA (8x),
Constitutional AI (8x), RAG (7x), SQuAD/HotpotQA/NQ, scaling laws, etc. The
full list is in the CSV.

## Outcomes (2026-06-11, same day)

All Tier-1 oversights fixed in draft-v0.md; Tier-2 adds cited at inline
anchors (DPO, InstructGPT, PPO, Guo ECE, MMLU, TriviaQA, Kuhn semantic
uncertainty + Farquhar Nature 2024, Kalai-Vempala 2311.14648). Six candidates
were PDF-screened against §4.2 (plus user-flagged Machine Bullshit
arXiv:2507.07484, which the crawl's >=3x band had missed because it is too
recent to be widely cited by our corpus): 4 admitted as effect studies
(2203.02155, 2405.20974, 2505.23646, 2507.07484; +8 rows, corpus then 75 rows /
39 studies; C5 11/0 p=0.001; variance-aware rows 3→6), 2 screened-and-held
(2012.14983 pre-LLM regime; 2505.13787 synthetic deception-reward setting).
Full disposition table in prisma-flow.md ("Backward-citation pass" section);
remaining optional Tier-3 cites tracked in paper/TODO.md.

UPDATE 2026-06-11 (factuality review pass): the counts in the paragraph above
are the post-backward-pass state and are superseded. The mis-attributed row
2505.19056 was removed from the corpus and the IPO arm of 2404.14723 was
extracted, so the corpus is now 75 rows / 38 studies (73 verified); C5 is
10/0 p=0.002 after the multi-LLM prompting row left the family. Current
numbers regenerate from analysis/synthesize.py; decisions logged in
paper/TODO.md and docs/review/draft-v0-factuality-review-board-2026-06-11.md.
