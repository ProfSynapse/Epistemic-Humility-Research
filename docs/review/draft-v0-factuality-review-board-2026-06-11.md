# Review board report: draft-v0.md factuality audit (2026-06-11)

**Decision: Major revision.** Not rejection: the computational infrastructure is unusually sound for this genre (every analysis script reproduces byte-identical, all 92 arXiv IDs resolve to the claimed papers, and nearly every external number checked against its primary source was confirmed). But the paper's own integrity rules are violated in three places that a hostile reviewer would treat as disqualifying if unfixed, the corpus self-description contains hand-tallied errors that contradict the committed CSV, and the vote-counting methodology has a structural cherry-picking exposure the paper does not disclose.

**Audit scope.** Six independent verification streams: (1) re-run of all seven analysis scripts against committed outputs; (2) row-by-row tracing of every quantitative claim in the draft to effects.csv, idk-method-reanalysis.csv, the raw reports, and the evidence docs; (3) independent recomputation of every statistic in sections 4-5 from raw data with fresh code; (4) resolution of all 92 arXiv references against the arXiv API; (5)-(6) fact-checks of ~47 headline claims against the primary PDFs/HTML, including refutation attempts on the section 6.3 gap claims.

---

## A. Violations of the paper's own integrity rules (must fix)

**A1. The C2 headline vote rests on an unverified row, contrary to the stated rule.** Section 4.4 promises "headline claims... rest only on verified rows" and section 4.5 says unverified rows are "excluded from headline claims." But C2's "Three studies support, none contradict (p = 0.25)" requires jmir-e76048, which is verified=false (no accessible PDF). Drop it and C2 is 2 studies, p = 0.50. The JMIR row is also quoted at line 141 ("DPO +8% over SFT with p = 0.003") with no inline unverified flag; the only flag is in section 7. Either restate C2 on verified rows alone or flag the JMIR dependency at every point of use and in the abstract.

**A2. The IPO contradiction was left unextracted, and the vote count depends on that.** 2404.14723's IPO result (a preference method losing to SFT by 5.4%) lives only in the notes field of row 56; no IPO row exists. Had it been extracted, the synthesis code would have counted 2404.14723 in both columns: C2 becomes 3 support / 1 contradict, two-sided p = 0.625. The prose discloses IPO as a "caution," but the quantitative claim "none contradict" survives only because the contradicting comparison from an already-extracted paper stayed in free text. Extract the IPO row and recompute, or give an explicit pre-stated extraction rule that excludes it and apply that rule symmetrically.

**A3. The Machine Bullshit BI model attribution violates the project's own open caveat.** The draft states "(Llama-3-8b)" flatly for the Bullshit Index 0.379 → 0.665. effects.csv row 72 records the model as "Llama-3-8b (probable; Fig.3 not explicit)" and TODO.md explicitly says to confirm with the authors before quoting the BI per-model. The deceptive-claims half (20.9% → 84.5%) is firm (the paper's Table 2 names Llama-3-8b). Hedge the BI attribution or resolve the TODO first.

## B. Corpus self-description errors (contradict the committed CSV)

**B1. Section 5.1 area breakdown is wrong.** Draft: calibration 17, abstention 25, hallucination/factuality 12, knowledge-boundary 2, sycophancy 15, methods 4. The CSV: calibration 17, abstention 26, hallucination 10, knowledge-boundary 2, sycophancy 15, methods 4, capability 1. The numbers were hand-tallied (no script emits them) and cannot be assembled from the CSV without silent relabeling. Generate these counts from the CSV in synthesize.py.

**B2. "Eight of them, our own computed reanalysis rows" (section 4.5) is wrong; the number is twelve** (4 Cheng + 8 AbstentionBench). prisma-flow.md repeats the same error. Note that section 7's "49 retrospectively checked rows" arithmetic only works with the 18-row artifact-anchored set, contradicting the "eight" in the same paper.

**B3. Data availability section says "all 67 effect rows"; everywhere else says 75.** Stale pre-backward-pass figure.

**B4. "Excluded outright" is overstated.** The mis-attributed row (2505.19056, row 59) is still in effects.csv, still counted in the 75 rows / 39 studies / 3 unverified rows. It is excluded from pooling only. Reword, or actually remove it and restate the corpus as 74 rows / 38 studies.

**B5. Flow-accounting loose ends.** "Plus five non-arXiv items" (section 4.1) vs. prisma-flow's 8 admitted non-arXiv records; the library count "97 papers were admitted" vs. a 109-entry manifest after the backward pass, never reconciled in the same paragraph that describes that pass. "Models span 125M-540B" cannot be audited from the size_b column (min 3.0; the 125M lives in a notes field).

## C. Claims contradicted or overstated vs. primary sources

**C1. PPO-M "ECE improves on all six evaluated benchmarks in both prompt settings" is false.** Table 1 of arXiv:2410.09724: Llama3-8B Professional Knowledge CoT worsens (0.4309 → 0.4329). Accurate phrasing: 11 of 12 Llama3-8B cells, all 12 for Mistral-7B. (The draft's irreproducibility parenthetical about the abstract's −6.44/+2.73 is confirmed and can stay.)

**C2. The 17.5% parenthetical misdescribes its origin.** The draft says a secondary report's 17.5% figure for KTO-vs-SFT "is not supported by the paper's appendix tables." The figure originates in the paper's own main text (Table 3, instruction-tuned-base setting, a points-vs-percent conflation by the authors). Rephrase as a setting mix-up, not an invented number. Also +21.2% is the more precise relative figure (9.25/43.73).

**C3. Sharma et al. "outranks truthfulness as a predictor of human preference" is stronger than the source.** The paper says matching user beliefs is among the most predictive features and that the exact ranking is condition-dependent. Soften to "among the most predictive features, comparable to or exceeding truthfulness features."

**C4. GPT-4 ECE 0.007/0.074 are figure annotations, not stated text.** The strings exist only inside Figure 8's plots; the caption says "a subset of the MMLU dataset." Given section 4.6's own disclosure standard about figure-derived values, mark these as read from the figure. "Rises tenfold" is the draft's arithmetic (10.6×).

**C5. The Cheng "excessive conservatism" quote exists only in arXiv v2.** v1 words it differently. Pin the citation to v2.

**C6. Smaller attribution fixes.** RLCR's "~90%" is from the project page, not the abstract. SycEval's term is "sycophantic behavior," not "capitulation." TruthfulQA's "60× smaller" belongs to the generation comparison; the MC comparison is 6B vs 125M (~48×). AbstentionBench's own paper headline is 20 models / 20 datasets; keep "23 × 31" strictly attached to the released CSV (line 121's unqualified "30 benchmark subsets" vs line 175's "31" needs one sentence of reconciliation: 31 is the grid, 30 the paired-cell count). OpenAI postmortem quote: actual wording is "our primary reward signal," not "the."

## D. Statistical methodology (required disclosures and one recompute)

**D1. Sidedness is never stated.** All five family p-values and the reanalysis binomials are two-sided exact binomial tests (verified consistent). Say so in section 4.4.

**D2. Tie handling is undisclosed and one stated n is wrong as read.** The 8B DPO recall test is binomtest(24, 29) after dropping 1 tie; the paper's "24 of 30 cells positive, p = 5.5e-04" invites binomtest(24,30) = 1.4e-03. The precision wash is 13 up / 12 down / 5 ties; the paper leaves 5 of 30 cells unexplained. Add "(ties dropped)" with counts. Conclusions survive either convention for the quoted tests, but at 70B-PPO precision the tie convention flips significance, so the disclosure is not cosmetic.

**D3. Unit-of-analysis inconsistency.** Votes are deduplicated to study level (good, conservative), but magnitude medians are computed over rows, so multi-row studies are double-weighted in medians (Cheng contributes 5 of C2's 7 median inputs; SelfAware 2 of C4's 4). C1's prose counts rows while C2/C4/C5 count studies. Pick one unit or report both.

**D4. Medians silently drop delta-only rows.** Medians use rel_change_pct only: C4's 41.5% median is over 4 of the family's 7 rows, and the three dropped values are all smaller, so the headline magnitude is inflated by the missingness pattern (with deltas included the median is ~19.8). C5 drops 4 of 18 rows. Disclose the denominator per family.

**D5. C5's family contains a non-training row.** Row 42 (multi-LLM abstention) is method=prompting inside "targeted training interventions" (dropping it: 10/0, p = 0.002, conclusion survives). A capability/accuracy row (GSM8K, row 7) also enters the C5 median for a family about humility metrics.

**D6. The family selectors structurally guarantee zero contradictions.** Every harm-showing comparison category in the corpus (reasoning_ft_effect −24% abstention, satisfaction_rlhf, instruction_tuning sycophancy, uncertainty_method_under_shift +49% MSE) sits outside every family's improvement test, and C2's metric regex matches no abstention metric despite the family being titled "abstention/truthfulness." Each exclusion is individually arguable; jointly they mean the sign tests test the labeling, not the world. Either pre-state the membership rules and apply them blind, or report a sensitivity row per family ("if the adjacent harm rows are admitted, the count becomes X/Y").

**D7. Degenerate tests presented as tests.** C1's p = 0.50 is the minimum attainable two-sided p at n = 2; C3's p = 1.0 at n = 1 is vacuous. The body is honest about this; the abstract is not (it asserts C1 as finding #1 with no caveat and quotes only C5's significant p = 0.001). The abstract must carry the same hedges as section 5.2, and "median relative change 567% (range...)" should not dress two numbers in distributional language, one of which is a 957% relative change off a 0.007 baseline.

**D8. No multiplicity control.** The AbstentionBench reanalysis runs 12 sign tests; the quoted p = 0.036 (70B) would not survive any correction. Either correct or label the panel exploratory.

**D9. "None of the twelve calibration studies reported error bars" outruns the record.** Raw report 01: 7 of 12 entries say "none reported," 5 say "unknown." Section 4.4's hedged "in any retrieved material" is supportable; the abstract's flat phrasing is not. Also, the corpus's 17 calibration rows come from 11 studies, a different set from report 01's 12 papers; add a clause so readers don't equate them.

## E. Reproducibility and traceability

**E1. Scripts: clean.** All seven re-run; synthesize.py, abstentionbench_reanalysis.py, factscore_reanalysis.py regenerate committed outputs byte-identical; the Cheng reanalysis matches all 15 table cells; the RewardCal numbers match exactly (the ~300 contradictions are exactly 326).

**E2. rewardcal_audit.py has a fragility to fix before release.** It depends on ~141 MB of uncommitted parquets in scratch/; without them it silently falls back to a 2,400-row sample and would emit different percentages with exit 0. Its REPO = HERE.parents[3] path resolves outside the repo at the current layout (legacy layout assumption), making the committed evidence doc byte-irreproducible in its provenance line. Pin the data (or add a hard failure when the full parquet is absent) and fix the path.

**E3. Locally untraceable numbers.** TruthRL's CRAG/Llama3.1-8B-Instruct/prompting-baseline attribution (line 223) exists in no local evidence file (raw report 06 records a 403 on the fetch); it was confirmed online against the paper's Table 1 in this audit, but the extraction record should be committed. Same for 2605.21127's "0% visible reasoning / +50-57% pass@1," which exists only in TODO.md. Several other prose numbers trace only to library/notes, which the frontmatter's traceability claim does not name as a location; widen the frontmatter wording or move those values into the declared stores.

**E4. Rounding edge cases.** "91.5-93.9%" (actual min 91.45) and "69.6-71.7" (actual min 69.55) hold only under round-half-up; state ranges at the script's two-decimal precision.

## F. Citations

All 92 arXiv IDs resolve to the claimed papers; zero misattributions; zero orphans in either direction. Five reference-list entries print an editorial descriptor where the real title should be (2603.24967, 2606.05145, 2606.06475, 2506.18183, 2511.07477); replace with actual titles at BibTeX conversion.

## G. Gap claims

Gaps 1 and 2 survived adversarial refutation attempts (independent searches plus the TACL abstention survey's silence on KTO). One defensive addition: FactAlign (arXiv:2410.01691) applies a KTO-derived objective to long-form factuality alignment and is the closest thing to a counterexample a reviewer will find; cite it in Gap 1's "nearest existing evidence" before someone else does.

## What held up (for the record)

Every effects-row-anchored number in the prose matches its row, including direction, units, and verified status. The five family vote counts and p-values reproduce exactly under the committed selectors. The Cheng, AbstentionBench, FActScore, and RewardCal reanalyses reproduce from raw artifacts, including the Spearman ρ = −0.05 (p = 0.82) with a justified 20-of-23 model set. The 6 variance-carrying rows, the 18 stronger-than-PDF rows (4+8+2+2+1+1), 72/75 and 36/39 verified tallies, and the 110-query arithmetic all check out. Of ~47 primary-source spot-checks, zero claims were outright fabricated; the contradictions found are the overstatements listed in section C.
