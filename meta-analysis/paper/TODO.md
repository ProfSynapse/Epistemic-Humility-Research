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
- [ ] **Backward-citation follow-ups:** (a) re-check 2505.23646 Table 6
      probe-accuracy duplication against a later arXiv revision before
      citing its probe numbers anywhere; (b) Machine Bullshit Fig. 3 BI row
      model attribution is "Llama-3-8b (probable)" — paper never states it;
      confirm with authors/v2 if the BI number is ever quoted per-model;
      (c) DONE 2026-06-11: library/manifest.yaml updated (12 new entries,
      97→109; 4 admitted studies status: verified with notes + PDFs;
      2 screened-held status: fetched; 8 context refs as candidates;
      note stubs created and Summary/Extracted sections filled for all 6
      screened papers; PDFs copied into library/pdfs/); (d) consider Tier-3
      optional cites from citation-gap-analysis.md (Naeini 2015 for ECE
      origin; 2503.14477 for gap-4 prior art) at style-pass time.
