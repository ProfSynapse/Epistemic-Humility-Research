# Pre-submission checklist (draft-v0 -> arXiv v1)

- [x] **PDF verification pass.** DONE 2026-06-10: 56/59 rows now
      `verified=true` (31 studies); daggers removed for verified claims;
      synthesize.py re-run (C2 median 5.0% range 1.6-21.1%; C5 median 30.1%).
      Corrections applied: R-Tuning metric = AP score; Wei -8.8 = Flan-PaLM-8B;
      2410.09724 re-anchored to Table 1 (abstract's 6.44/2.73 irreproducible);
      2312.07000 baseline = UNALIGNED 50.06; 2404.14723 KTO = +2.17 (SFT base)
      / +9.25 (pretrained), report's 17.5% unsupported; 2109.07958 17% =
      gen-task largest-vs-60x-smaller. Remaining 3 unverified: nostalgebraist
      blog (verify against blog), jmir-e76048 (no PDF), 2505.19056 (DISPUTED —
      dose-response claim not in paper; re-source, candidate Bianchi
      2309.07875). Remaining daggers (47) are raw-report-06 / essay-cited
      claims (TruthRL, Abstain-R1, probing numbers, 2604-2606 cluster) +
      Kadavath 2207.05221 quote + 2505.01997 preference-collapse quote.
- [ ] **PRISMA flow counts.** Reconstruct records-identified / screened /
      excluded / included numbers from the five search agents' logs (82
      queries) + the follow-up search; add a PRISMA-style flow figure and an
      explicit exclusion log. Currently only inclusion criteria are stated.
- [ ] **Integrate raw-reports/06** (mech-interp/probing follow-up search,
      running) into Sections 3, 6.2, 6.3 gap 4, and 8; add any new effects rows.
- [ ] **Figure regeneration.** Regenerate `analysis/figures/forest.png` from
      final effects.csv; add (a) per-claim-family vote/sign-test figure,
      (b) Section 5.3 recall-vs-over-refusal operating-point scatter,
      (c) L1-L4 coverage map (stack level x rows). Verify figure numbers match
      regenerated synthesis-summary.md.
- [ ] **Related-surveys positioning paragraph.** Expand Section 6.4 into a
      proper comparison with 2407.18418 (abstention survey) and 2409.18786
      (honesty survey), plus any 2026 surveys found during the PDF pass.
- [ ] **Author/affiliation block.** Add author name(s), affiliation, contact,
      and the companion-essay citation in final form; decide author-name form
      for the essay attribution (Section 3) and References.
- [x] **Finish the interim columns** of `idk-method-reanalysis.csv` — DONE
      2026-06-10: exact gold-alias grading via
      `datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl` (Cheng test set
      = TriviaQA unfiltered.nocontext/validation, 100% question-text match).
      Draft 5.3 updated; truthful scalar still excluded from claims (label
      base differs from the paper's Ik-threshold pipeline).
- [ ] **Abstract trim** to ~200 words (currently ~250) and final word-count /
      style pass; convert references to BibTeX; arXiv formatting (LaTeX or
      arXiv-ready markdown pipeline).
- [ ] **Verify 2026 arXiv IDs** flagged in library manifest (2603.xxxxx-
      2606.xxxxx cluster cited via the essay) resolve to the intended papers.
