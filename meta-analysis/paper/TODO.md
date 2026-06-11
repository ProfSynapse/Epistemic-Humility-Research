# Pre-submission checklist (draft-v0 -> arXiv v1)

- [x] **PDF verification pass.** DONE 2026-06-10: 56/59 rows now
      `verified=true` (31 studies); daggers removed for verified claims;
      synthesize.py re-run (C2 median 5.0% range 1.6-21.1%; C5 median 30.1%).
      Corrections applied: R-Tuning metric = AP score; Wei -8.8 = Flan-PaLM-8B;
      2410.09724 re-anchored to Table 1 (abstract's 6.44/2.73 irreproducible);
      2312.07000 baseline = UNALIGNED 50.06; 2404.14723 KTO = +2.17 (SFT base)
      / +9.25 (pretrained), report's 17.5% unsupported; 2109.07958 17% =
      gen-task largest-vs-60x-smaller. Remaining 3 unverified: nostalgebraist
      blog (verify against blog), jmir-e76048 (no PDF), 2505.19056 (RESOLVED 2026-06-10:
      dose-response re-attributed to Bianchi 2309.07875 — safety-domain
      sweep with figure-based over-refusal evidence; row stays excluded
      from pooled stats; draft gap 5 cites 2309.07875 qualitatively). Dagger elimination COMPLETE 2026-06-10: two agent
      fan-outs (batches A+B, 32 papers) verified every remaining in-text
      value; 0 content daggers left, † convention retired in the draft's
      legends. Batch-B corrections folded in: 2401.12794 (conformal-set
      growth coincides with *impaired/mixed* accuracy, not improvement),
      2512.00218 (only adversarial optimization vs. the monitor degrades
      monitorability — now cited as a boundary condition), 2606.03962
      ("as well as", better only under noisy judge; true title "Using
      Reward Uncertainty to Induce Diverse Behaviour in RL", GX-Chen et
      al.), 2606.08571 refined to 99.46% JSON-valid certificates on 735
      held-out questions, 2605.21127 metadata confirmed ("Reasoning-Trace
      Collapse", Twist et al.; VR→0% while pass@1 +50-57%). 60/94 library
      notes now status: verified.
- [x] **PRISMA flow counts.** DONE 2026-06-10: retrospective reconstruction
      in `evidence/prisma-flow.md` (110 queries; 93 structured entries; 114
      unique IDs; 95 admitted; 21-ID exclusion log in 3 categories; 34
      studies/59 rows; 36 context-cited). Figure: `analysis/prisma_figure.py`
      -> `figures/prisma.png`. Draft §4.1 flow paragraph + §7 caveat added
      (snippet-level hit counts were never logged — stated honestly). NOTE:
      4 post-freeze papers (2312.17249 Androids-Dreaming, 2506.14387 SEAT,
      2603.09117 DCPO, 2605.25850 TIAR) logged as v1 citation candidates.
- [x] **Integrate raw-reports/06** — DONE (commit 4fd8dd7): folded into §3,
      §6.2, §6.3 gaps 3-4; 15 papers registered; §4.1 now counts its 28
      queries (110 total).
- [x] **Internal-consistency sweep.** DONE 2026-06-10: §4.3/§5.1/§7 updated
      from the stale 10-verified-rows state to 56/59; §4.1 follow-up search
      marked complete; §7 limitation 1 rewritten (retrospective-verification
      framing, ~14% correction rate reported as a finding); references
      sorted, 2 missing entries added (2511.12991, 2604.17073), 3 uncited
      entries resolved (2205.14334 + 2305.14251 now cited in C1/C2;
      2403.18349 RLKF cited in gap 3); 2606.03969 entry cleaned. §8 stubbed
      out pending the research-trajectory conversation (v0 text parked at
      `experiment/protocol/future-work-section-v0.md`).
- [ ] **Figure regeneration.** `forest.png` regenerated 2026-06-10 (67-row
      corpus). Still to add: (a) per-claim-family vote/sign-test figure — do
      this as a Cochrane ch. 12 effect-direction plot, the natively
      recommended visualization for direction-based synthesis (also closes
      SWiM item 7 fully); (b) Section 5.3 recall-vs-over-refusal
      operating-point scatter (abstentionbench_frontier.png may already
      serve); (c) L1-L4 coverage map (depth x rows; framework renamed Depths of Ignorance 2026-06-11). Verify figure
      numbers match regenerated synthesis-summary.md.
- [x] **Methods evidence-basing.** DONE 2026-06-10: §4.4 grounds the
      synthesis design in the methodology literature (SWiM names our exact
      methods; Cochrane ch. 12 sanctions direction-based vote counting +
      sign test and condemns the significance-based variant we avoid;
      Hedges & Olkin 1980 cited as the honest limitation; Kitchenham &
      Charters for CS norms). §7 grounds the ~14% correction rate in
      measured single-extraction (Buscemi 2006) and LLM-extraction
      (Khraisha 2024, ~80% accuracy) error rates. PRISMA 2020 deviation
      now cited explicitly (Page et al. 2021). GRADE certainty handled as
      a blanket low/very-low statement in §4.4 (SWiM item 6); full
      per-family GRADE deferred. 7 methodology references added.
- [x] **Related-surveys positioning paragraph.** DONE 2026-06-10: §6.4
      expanded from a one-liner plus deferral note into a full comparison,
      grounded in a subagent deep-read of both local PDFs (2407.18418 Wen
      et al. abstention survey, v3 Feb 2025; 2409.18786 Li et al. honesty
      survey, Sep 2024). Verified differences asserted: both narrative, no
      search protocol, no quantitative schema/verification/pooling, KTO
      absent from both, central tension only qualitative. No 2026 surveys
      surfaced during the PDF pass.
- [x] **Author/affiliation block.** DONE 2026-06-10: Joseph Rosenbaum
      (Synaptic Labs, connect2synapse@gmail.com) added to frontmatter +
      title block. Re-confirm email choice and exact affiliation string at
      BibTeX/LaTeX time. SUPERSEDED 2026-06-11: all companion-essay
      mentions and the Synaptic Labs (2026) reference REMOVED by author
      decision; the Formalization Stack is now presented as introduced by
      this paper (§1 contribution 3, §3). Do not re-add the attribution.
- [x] **Finish the interim columns** of `idk-method-reanalysis.csv` — DONE
      2026-06-10: exact gold-alias grading via
      `datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl` (Cheng test set
      = TriviaQA unfiltered.nocontext/validation, 100% question-text match).
      Draft 5.3 updated; truthful scalar still excluded from claims (label
      base differs from the paper's Ik-threshold pipeline).
- [x] **Acronym pass.** DONE 2026-06-10: 30 first-use expansions (SFT, DPO,
      KTO, RLHF, ECE, RL, IDK, PPO, BoN, AUROC, LLM, GRPO, ECE-t, RMS, MSE,
      MAD, AP, AED, CI, QA, AUC, HIR, IPO, NLP, OOD, ROC, RLVR, PAEC, RLKF,
      RLCR, TPR, CCS, ITI, P(IK), MMLU); FactTune/LACIE/FLAME nicknames now
      carry their arXiv IDs at the §6 mention; stale abstract counts fixed
      (five searches/82 queries -> six/110). MASK and CRAG left as proper
      benchmark names (descriptive gloss in surrounding prose).
- [ ] **Refresh provider-card snapshot before submission.** §5.4 is now
      date-scoped ("flagship documentation current at the June 2026 search:
      GPT-5, Claude Opus 4.8, Gemini 3 Pro"). Vendors have already moved
      (Gemini 3.5 Flash / 3.1 Pro are out; OpenAI will iterate too). Right
      before arXiv submission, re-pull the then-current flagship cards and
      either update the paragraph or confirm the date-scoped framing stands
      (in particular re-test the "Gemini card has zero quantified honesty
      evals" observation against the newest Gemini card).
- [ ] **Abstract trim** to ~200 words (currently ~250) and final word-count /
      style pass; convert references to BibTeX; arXiv formatting (LaTeX or
      arXiv-ready markdown pipeline).
- [x] **Verify 2026 arXiv IDs** — DONE 2026-06-10 (batches A+B): all
      essay-cited 2603-2606 IDs resolve to the intended papers and their
      quoted values are PDF-verified.
- [x] **Backward-citation pass (reference-list checking).** DONE 2026-06-11:
      Semantic Scholar reference lists of all 69 bibliography arXiv papers
      aggregated and ranked (`evidence/citation-gap-analysis.md`,
      `citation-gap-candidates.csv`). 11 named-but-uncited papers fixed
      (TruthRL 2509.25760, lie-detectors 2505.13787 with tightened
      paraphrase, gap-4 probing toolkit 2304.13734/2212.03827/2310.06824/
      2306.03341/2310.01405/2406.15927, gap-4 caveat sources 2510.09033/
      2407.08582, MASK 2503.03750). 12 context refs added (DPO 2305.18290,
      InstructGPT 2203.02155, PPO, Guo ECE 1706.04599, MMLU, TriviaQA,
      Kuhn SE 2302.09664 + Farquhar Nature 2024, Kalai-Vempala 2311.14648
      [phrasing verified vs abstract 2026-06-11], Mielke 2012.14983).
      6 candidates PDF-screened against §4.2 by agents: 4 ADMITTED
      (+8 rows, corpus 67→75 rows / 35→39 studies: InstructGPT counterpoint
      row; SaySelf → C5 now 11/0 p=0.001, new `confidence_sft_rl` label in
      synthesize.py; 2505.23646 recipe rows; Machine Bullshit 2507.07484
      satisfaction-RLHF rows, variance-aware rows 3→6); 2 held out with
      logged rationales (Mielke pre-LLM regime; 2505.13787 synthetic
      deception-reward). synthesize.py re-run; prisma figure + flow doc
      updated; draft counts propagated (abstract, §1, §4.1/4.3/4.4/4.5,
      §5.1/5.2/5.5, §6.1/6.3, §7).
- [x] **§8 Future work drafted.** DONE 2026-06-11: four-phase program
      (8.1 three-way SFT/DPO/KTO, Gaps 1+2; 8.2 IDK-fraction dose-response +
      composition + KTO balance ablation, Gap 5; 8.3 probe-transfer mechanism,
      Gap 4; 8.4 rolling cross-architecture generalization + sycophancy +
      reasoning-trace axes, Gap 6; 8.5 standard inherited), sourced from
      `experiment/protocol/research-trajectory.md`. Written forward-looking
      only (no mention of program status); v0 parked text marked superseded.
      Citation cross-check passes (all §8 IDs already in references).
- [ ] **Backward-citation follow-ups:** (a) re-check 2505.23646 Table 6
      probe-accuracy duplication against a later arXiv revision before
      citing its probe numbers anywhere; (b) Machine Bullshit Fig. 3 BI row
      model attribution is "Llama-3-8b (probable)" — paper never states it;
      confirm with authors/v2 if the BI number is ever quoted per-model
      (INTERIM 2026-06-11: §1 now hedges the BI model attribution inline,
      so the draft no longer depends on this; un-hedge only after
      confirmation);
      (c) DONE 2026-06-11: library/manifest.yaml updated (12 new entries,
      97→109; 4 admitted studies status: verified with notes + PDFs;
      2 screened-held status: fetched; 8 context refs as candidates;
      note stubs created and Summary/Extracted sections filled for all 6
      screened papers; PDFs copied into library/pdfs/); (d) consider Tier-3
      optional cites from citation-gap-analysis.md (Naeini 2015 for ECE
      origin; 2503.14477 for gap-4 prior art) at style-pass time.
- [x] **Factuality review board, mechanical fixes.** DONE 2026-06-11
      (full report: `docs/review/draft-v0-factuality-review-board-2026-06-11.md`).
      Applied: §5.1 area breakdown corrected to the CSV (abstention 26,
      hallucination 10, +capability 1; synthesize.py now emits the
      breakdown); §4.5 eight→twelve reanalysis rows (also prisma-flow);
      data-availability 67→75; "excluded outright"→"excluded from pooled
      statistics" (§4.1, §7); §4.4 stats conventions added (two-sided,
      tie-dropping, study-level votes vs row-level medians, per-family
      median denominators); AbstentionBench tie counts disclosed
      (24/29 at 8B, 28 cells at 70B, 5 precision ties) + 30-vs-31 subset
      reconciliation + 12-tests-uncorrected note; C1 567%-median language
      replaced with the two raw values + near-zero-baseline caveat + minimum-
      attainable-p note; PPO-M "all six benchmarks"→11-of-12 Llama3-8B
      cells (Table 1 verified); 2404.14723 rel 21.1→21.2 in effects.csv
      (propagated) and 17.5% parenthetical recast as the paper's own
      Table 3 points-vs-percent setting mix-up; JMIR flagged unverified
      inline at point of use; BI model attribution hedged; Sharma
      "outranks truthfulness" softened; GPT-4 ECE marked figure-derived;
      OpenAI postmortem quote corrected to verbatim ("our primary reward
      signal, which"); Cheng quote pinned to arXiv v2; SycEval term
      clarified; TruthfulQA MC comparison scoped to 6B-vs-125M; RLCR ~90%
      attributed to authors' reported results; exact ranges 91.45-93.85 /
      69.55-71.74; abstract error-bar phrasing tightened + sign-tests-
      descriptive clause; §4.1 five non-arXiv items enumerated + library
      109 reconciled; 5 reference descriptors replaced with real titles;
      FactAlign 2410.01691 added to gap 1 (title/authors API-verified);
      TruthRL Table-1 attribution and 2605.21127 0%-VR/50-57% quotes
      PDF-verified and recorded in library/notes; rewardcal_audit.py
      REPO path fixed (parents[3]→parents[1], output now byte-identical)
      + hard failure on sample fallback (REWARDCAL_ALLOW_SAMPLE=1 to
      override). All scripts re-run clean after edits.
- [x] **Factuality review board, JUDGMENT items 1-4 DECIDED + APPLIED**
      (2026-06-11, author choices via review session):
      (1) C2 strict: votes now verified-only in synthesize.py (drops JMIR
      from every vote); IPO arm extracted as its own row (sft_vs_ipo,
      Table 8, -5.4%); prompting→SFT row relabeled prompting_vs_sft.
      C2 = 2 support / 1 contradict, sign test uninformative; median
      |rel| 5.0% over 7 rows, range -5.4% to +21.2%; abstract and §5.2
      restated ("every extracted comparison but one").
      (2) C5: multi_llm_abstention removed from the family (prompting,
      not training; kept in prose as adjacent, would be 11/0 p=0.001);
      capability area excluded from the family. C5 = 10/0, p=0.002,
      median 40.1% over 12 rows; abstract updated.
      (3) Boundary sensitivity: synthesize.py now emits a "rows matched
      by no family" section; §5.2 preamble discloses the harm rows
      outside all families and the C5 sensitivity (admitting
      reasoning-RL + satisfaction-RLHF → 10/2, p=0.039).
      (4) Excluded row 2505.19056 REMOVED from effects.csv (full record
      preserved in prisma-flow.md "Excluded row" section). Corpus is now
      75 rows / 38 studies, 73 verified (36 studies), 2 unverified rows.
      prisma_figure.py constants updated and figure regenerated; all
      counts propagated through frontmatter, abstract, §4.1/4.3/4.4/4.5,
      §5.1, §7. Stale-context sweep done 2026-06-11: the only stale
      tracked reference (citation-gap-analysis.md) carries a dated
      UPDATE note; remaining 75/39 mentions are immutable history
      (commit message c77b57b) or historical log lines left as-is.
- [ ] **Factuality review board, judgment items 5-6 (smaller, still open):**
      (5) Magnitude medians: kept rel-only with per-family denominators
      disclosed; alternative (incorporate delta-only rows; C4 median
      41.5%→~19.8) not adopted, revisit at style pass.
      (6) C4 heterogeneity: 4 of 7 rows are gap-at-one-scale, not scale
      sweeps; decide whether to split or re-scope the family claim.
