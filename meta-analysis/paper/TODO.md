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
- [x] **Verify 2026 arXiv IDs** — DONE 2026-06-10 (batches A+B): all
      essay-cited 2603-2606 IDs resolve to the intended papers and their
      quoted values are PDF-verified.
