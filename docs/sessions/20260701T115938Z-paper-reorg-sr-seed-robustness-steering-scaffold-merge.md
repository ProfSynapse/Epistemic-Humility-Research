---
schema_version: research-session/v1
session_id: 20260701T115938Z-paper-reorg-sr-seed-robustness-steering-scaffold-merge
title: Paper reorg + SR seed-robustness + steering-scaffold merge
status: active
created_at: '2026-07-01T11:59:38Z'
updated_at: '2026-07-01T17:01:25Z'
phase: phase1
question: Are the training-free two-signal readout headline magnitudes (Z cross-family
  dial+veto) seed-robust under sampled decoding, and consolidate the paper numbering
  + merge the Paper-4 steering scaffold?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-infrastructure
  at: '2026-07-01T12:00:08Z'
  kind: infrastructure
  title: "Steering scaffold (Paper 4) reviewed + merged; Paper 5\u21924 relabel"
  summary: "Reviewed the confidence-steering scaffold from the paper5 worktree: purely\
    \ additive (10 files under archive/experiment/phase1/probe/steering/), training-free by\
    \ construction (Arm A forward-hook activation steering h\u2190h+alpha*d; Arm B\
    \ CoT text injection; zero weight updates), 88/88 CPU tests green. Merged via\
    \ PR #137, then relabeled Paper 5\u2192Paper 4 (canonical map) via PR #138. Design\
    \ doc docs/plans/confidence-steering-experiment.md already existed on main and\
    \ was already correctly numbered (the '#137 missing plan doc' flag was a wrong-branch\
    \ false alarm). Worktrees + branches cleaned up."
  evidence:
  - archive/experiment/phase1/probe/steering/README.md
  run_ids: []
  commands: []
  decisions:
  - Merge scaffolding to main now (user asked); training-free constraint baked in
    as a hard design rule for Paper 4; full pre-reg (gates/falsifiers) deferred until
    the steering amendment is minted.
  next_steps: []
  signals: {}
- id: 002-launch
  at: '2026-07-01T12:00:08Z'
  kind: launch
  title: Amendment SR (sampled-decode seed-robustness) pre-registered + launched
  summary: Hardens the Z headline dial+veto magnitudes against the single-greedy-decode
    confound. Identical training-free readout under SAMPLED decoding (temp 0.7/top_p
    0.9) x 3 seeds (20260701/02/03) on the 4 confirmatory families ONLY (Qwen3-4B/W
    excluded so the seed pass stays inside the confirmatory set). Scope dial+veto
    (gate is pre-gen-anchor decode-INVARIANT, emitted as invariance check). Extractor
    gained backward-compatible --do-sample/--temperature/--top-p (default greedy =
    X/Z reproduce). SUCCESS = dial 4/4 seed-stable + veto >=3/4 seed-stable + per-seed
    veto majority >=3/4 every seed. Launched 10:11 UTC local Docker unsloth-z:latest,
    single GPU sequential, 12 cells.
  evidence:
  - experiments/sampled-decode-seed-robustness/AMENDMENT.md
  run_ids: []
  commands:
  - bash archive/experiment/phase1/probe/amendments/amendment_sr_queue.sh
  decisions: []
  next_steps: []
  signals: {}
- id: 003-result
  at: '2026-07-01T12:00:08Z'
  kind: result
  title: "SR 3/12: Llama-3.2-3B veto flips greedy-FAIL \u2192 seed-stable PASS (3/3)"
  summary: "Llama-3.2-3B family complete (3 seeds). veto 0.801/0.684/0.732 = seed-stable\
    \ PASS 3/3 (mean ~0.739); dial 0.827/0.853/0.865 all PASS; gate ~0.997 all (decode-invariance\
    \ confirmed). Llama's veto was the CLEAN GREEDY FAIL (0.633) in Z \u2014 under\
    \ sampled decoding it passes on every seed, so the Z single-decode veto miss looks\
    \ like a greedy-decode artifact. n=1 family so far; not read into the locked verdict.\
    \ Ministral/Qwen3.5/Gemma-4 pending (~30 min/seed, ETA ~16:00-17:00 UTC)."
  evidence:
  - experiment/phase1/probe/sr_logs/PROGRESS.log
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - "Let the queue finish; fill AMENDMENT-SR \xA77 per-seed tables + seed-stability\
    \ roll-up + per-seed veto majority + locked verdict; refresh experiment note;\
    \ open the SR PR."
  signals: {}
- id: 004-result
  at: '2026-07-01T17:01:25Z'
  kind: result
  title: 'SR queue complete: 9/12 scored, 3 families PASS, Gemma re-run pending (9P
    infra fault)'
  summary: 'Amendment SR sampled-decode queue completed 16:54 UTC. Llama/Ministral/Qwen3.5
    = 3/3 seeds each (9 eligible cells): dial 9/9 PASS (0.799-0.865), gate decode-invariant
    (0.9964-0.9986), veto seed-stable PASS on all three (Llama 3/3, Ministral 2/3,
    Qwen3.5 3/3). Llama''s Z greedy veto FAIL (0.633) and Qwen3.5''s Z greedy marginal
    (0.666) both PASS under sampled decoding -> single-greedy-decode veto softness
    was a decode artifact. Gemma-4-E4B DID NOT RUN: compat smoke crashed on a transient
    9P PermissionError at mkdir before model load (other 12 in-container dirs created
    fine). Retryable infra fault, NOT scientific INELIGIBLE (Gemma passed same greedy
    smoke in Z, identical image).'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - "Record Gemma as RE-RUN PENDING, not INELIGIBLE (mkdir error is not a pre-reg\
    \ blocker). DEFER the SR verdict: strict per-seed clause (c) at seed 701 hinges\
    \ on Gemma-701 (2/4 without it; seeds 702/703 already 3/4). \xA77 + experiment\
    \ note updated and committed (f7cc4ad6)."
  next_steps:
  - Get explicit user GPU launch approval to re-run gemma-4-e4b seeds 20260701/02/03
    on local Docker GPU lane (lab-notebook re-run of a pre-registered cell, no goalpost
    change), then finalize verdict + open SR PR + update memory.
  signals: {}
legacy_session:
  id: '0031'
  path: docs/sessions/0031 - paper-reorg-sr-seed-robustness-steering-scaffold-merge.md
---
# Paper reorg + SR seed-robustness + steering-scaffold merge

## Question

Are the training-free two-signal readout headline magnitudes (Z cross-family dial+veto) seed-robust under sampled decoding, and consolidate the paper numbering + merge the Paper-4 steering scaffold?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-infrastructure - Steering scaffold (Paper 4) reviewed + merged; Paper 5→4 relabel

- at: `2026-07-01T12:00:08Z`
- kind: `infrastructure`
- summary: Reviewed the confidence-steering scaffold from the paper5 worktree: purely additive (10 files under archive/experiment/phase1/probe/steering/), training-free by construction (Arm A forward-hook activation steering h←h+alpha*d; Arm B CoT text injection; zero weight updates), 88/88 CPU tests green. Merged via PR #137, then relabeled Paper 5→Paper 4 (canonical map) via PR #138. Design doc docs/plans/confidence-steering-experiment.md already existed on main and was already correctly numbered (the '#137 missing plan doc' flag was a wrong-branch false alarm). Worktrees + branches cleaned up.
- evidence:
  - `archive/experiment/phase1/probe/steering/README.md`
- decisions:
  - Merge scaffolding to main now (user asked); training-free constraint baked in as a hard design rule for Paper 4; full pre-reg (gates/falsifiers) deferred until the steering amendment is minted.
### 002-launch - Amendment SR (sampled-decode seed-robustness) pre-registered + launched

- at: `2026-07-01T12:00:08Z`
- kind: `launch`
- summary: Hardens the Z headline dial+veto magnitudes against the single-greedy-decode confound. Identical training-free readout under SAMPLED decoding (temp 0.7/top_p 0.9) x 3 seeds (20260701/02/03) on the 4 confirmatory families ONLY (Qwen3-4B/W excluded so the seed pass stays inside the confirmatory set). Scope dial+veto (gate is pre-gen-anchor decode-INVARIANT, emitted as invariance check). Extractor gained backward-compatible --do-sample/--temperature/--top-p (default greedy = X/Z reproduce). SUCCESS = dial 4/4 seed-stable + veto >=3/4 seed-stable + per-seed veto majority >=3/4 every seed. Launched 10:11 UTC local Docker unsloth-z:latest, single GPU sequential, 12 cells.
- evidence:
  - `experiments/sampled-decode-seed-robustness/AMENDMENT.md`
- commands:
  - `bash archive/experiment/phase1/probe/amendments/amendment_sr_queue.sh`
### 003-result - SR 3/12: Llama-3.2-3B veto flips greedy-FAIL → seed-stable PASS (3/3)

- at: `2026-07-01T12:00:08Z`
- kind: `result`
- summary: Llama-3.2-3B family complete (3 seeds). veto 0.801/0.684/0.732 = seed-stable PASS 3/3 (mean ~0.739); dial 0.827/0.853/0.865 all PASS; gate ~0.997 all (decode-invariance confirmed). Llama's veto was the CLEAN GREEDY FAIL (0.633) in Z — under sampled decoding it passes on every seed, so the Z single-decode veto miss looks like a greedy-decode artifact. n=1 family so far; not read into the locked verdict. Ministral/Qwen3.5/Gemma-4 pending (~30 min/seed, ETA ~16:00-17:00 UTC).
- evidence:
  - `experiment/phase1/probe/sr_logs/PROGRESS.log`
- next steps:
  - Let the queue finish; fill AMENDMENT-SR §7 per-seed tables + seed-stability roll-up + per-seed veto majority + locked verdict; refresh experiment note; open the SR PR.
### 004-result - SR queue complete: 9/12 scored, 3 families PASS, Gemma re-run pending (9P infra fault)

- at: `2026-07-01T17:01:25Z`
- kind: `result`
- summary: Amendment SR sampled-decode queue completed 16:54 UTC. Llama/Ministral/Qwen3.5 = 3/3 seeds each (9 eligible cells): dial 9/9 PASS (0.799-0.865), gate decode-invariant (0.9964-0.9986), veto seed-stable PASS on all three (Llama 3/3, Ministral 2/3, Qwen3.5 3/3). Llama's Z greedy veto FAIL (0.633) and Qwen3.5's Z greedy marginal (0.666) both PASS under sampled decoding -> single-greedy-decode veto softness was a decode artifact. Gemma-4-E4B DID NOT RUN: compat smoke crashed on a transient 9P PermissionError at mkdir before model load (other 12 in-container dirs created fine). Retryable infra fault, NOT scientific INELIGIBLE (Gemma passed same greedy smoke in Z, identical image).
- decisions:
  - Record Gemma as RE-RUN PENDING, not INELIGIBLE (mkdir error is not a pre-reg blocker). DEFER the SR verdict: strict per-seed clause (c) at seed 701 hinges on Gemma-701 (2/4 without it; seeds 702/703 already 3/4). §7 + experiment note updated and committed (f7cc4ad6).
- next steps:
  - Get explicit user GPU launch approval to re-run gemma-4-e4b seeds 20260701/02/03 on local Docker GPU lane (lab-notebook re-run of a pre-registered cell, no goalpost change), then finalize verdict + open SR PR + update memory.
### 005-result - Gemma re-run GREEN (--user 0:0 fix): seeds 701+702 scored, both PASS; verdict clauses (b)+(c) now locked

- at: `2026-07-01T20:45:00Z`
- kind: `result`
- summary: Root cause of the Gemma "transient" fault found and fixed — probe/ ownership flipped to root:root on the 9P mount mid-day, so the image's uid 1001 could not mkdir; re-run container uses --user 0:0 (root) and cleared it. Seed 20260701 gate=0.998 dial=0.802 PASS veto=0.7618 PASS; seed 20260702 gate=0.998 dial=0.8385 PASS veto=0.7455 PASS (adequacy OK both). Verdict arithmetic: clause (c) per-seed veto majority now >=3/4 on EVERY seed (701 was the hinge — resolved YES); clause (b) veto seed-stable >=3/4 families now 4/4 (Gemma 2/2 secures >=2/3). Only clause (a) remains: Gemma dial 3/3 needs seed 20260703 dial >=0.65 (prior two: 0.802/0.839). Seed 703 extracting.
- evidence:
  - `experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_gemma-4-e4b_seed20260701_result.json`
  - `experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_gemma-4-e4b_seed20260702_result.json`
  - `experiment/phase1/probe/sr_logs/PROGRESS.log`
- next steps:
  - When seed 703 lands: fill Gemma rows in AMENDMENT-SR §7, compute the locked verdict, finalize paper3 §4.8 + §4.7/abstract, commit, open the SR PR, update the amendment-sr memory.
### 006-writeup - Paper 1 rewritten as unified review+regimen paper (draft-v2); meta-analysis archived as Part I source

- at: `2026-07-01T21:10:00Z`
- kind: `writeup`
- summary: Per user direction ("archive our meta analysis and rewrite as our proposed paper 1"), wrote papers/paper-2-training-regimen/manuscript.md: Part I condenses the systematic synthesis (Depths of Ignorance, C1-C5, reanalyses, verified gaps 1-3 as motivation); Part II presents the full regimen experiment SFT/DPO/KTO/GRPO as ONE narrative — stage decomposition (SFT induces 87.9/64.8; DPO/KTO cold-start fail 0.03/0.00; warmed DPO repositions 61.6->14.0 over-refusal at -34pt recall; KTO conservative; GRPO amplifies to 93-98 recall / best truthful 41.1-41.6 with over-refusal back up; stacks marginal) + confidence-channel arc (v2 collapse std 0.013/AUROC 0.520; proper-scoring v3 does NOT fix std 0.027/0.522; contrastive SFT calibrates 0.684/0.183 at behavior cost 79.2 over-refusal; GRPO-on-contrastive retains calibration 0.646 but behavior worsens 90.8, beta-sweep-invariant) + probe coda (internal 0.972 vs emitted 0.637). No amendment labels in prose; full label->artifact map in Appendix A. All numbers re-verified against calibration_gap_*.json + selfaware_full_run_comparison_grouped.csv before writing. Archival banners added: meta-analysis/paper/draft-v0.md (status archived, provenance-source-of-record note) and paper1 draft-v1 (superseded).
- evidence:
  - `papers/paper-2-training-regimen/manuscript.md`
  - `meta-analysis/paper/draft-v0.md`
- decisions:
  - Working-tree only for now (on the SR branch with the Gemma GPU run reading the tree); commit on a dedicated docs branch after the SR PR closes out, per one-branch-one-PR discipline.
### 007-writeup - Paper 1 v2 figures generated (fig-p1-07..09) + figs 1-6 regenerated

- at: `2026-07-01T21:55:00Z`
- kind: `writeup`
- summary: New deterministic builder papers/paper-2-training-regimen/scripts/build_extended_figures.py renders fig-p1-07 (regimen operating points, 9 response-confidence arms from the grouped CSV), fig-p1-08 (confidence-channel seesaw: std/AUROC/over-refusal across GRPO-v2, GRPO-v3, contrastive, masked-contrastive, GRPO-on-contrastive; N triple transcribed from AMENDMENT-N §7 table with provenance comment since no calibration-gap JSON exists for that cell), fig-p1-09 (internal 0.972 vs emitted 0.637 AUROC from calibration_gap_clean_sft_grpo_v2_seed1.json B_internal_vs_emitted). Existing build_paper1_figures.py re-run to confirm figs 1-6 reproduce. All 8 figures embedded into paper1-training-regimen-draft-v2.md with captions (numbered Figures 1-8). Bonus datum surfaced while wiring fig-08: GRPO-v3 behavior is FINE (over_refusal 65.13, truthful 40.99) — the proper-scoring negative is confidence-channel-specific, matching §7.2's framing.
- evidence:
  - `papers/paper-2-training-regimen/scripts/build_extended_figures.py`
  - `papers/paper-2-training-regimen/figures/fig-p1-0{7,8,9}-*.png`
### 008-writeup - Paper 1 v2 citation + LaTeX pass (author-year, complete refs, math)

- at: `2026-07-01T23:20:00Z`
- kind: `writeup`
- summary: Per user question ("are we using latex for any math representations and is everything cited properly not just arxiv codes?"): the draft had zero LaTeX and ~45 in-text bare [arXiv:ID] citations with a References list covering only ~19 of ~40 cited works (plus a placeholder note deferring Part I citations to the meta-analysis bibliography). Fixed via deterministic script (scratchpad fix_paper1_citations.py): (1) every in-text arXiv bracket converted to author-year, metadata sourced from library/notes frontmatter; (2) References rebuilt — 46 entries, alphabetical, verified one-to-one with in-text citations in both directions (audit script: zero cited-but-missing, zero listed-but-uncited); previously-uncited entries (Kalai, Lin 2022, Tian 2023a, Bianchi, Liu, Amayuelas) woven in at textually apt sites; Lin TruthfulQA re-dated 2021 and Tian split 2023a/2023b to disambiguate; (3) LaTeX added: GRPO group-normalized advantage display equation (§5.3), Brier proper-scoring reward + uniqueness-of-optimum display equation (§7.2), inline math for p-values, n, Spearman rho, F_1, KL beta (0.10→0.05), ECE ≈. Frontmatter notes now declare the math/citation conventions.
- evidence:
  - `papers/paper-2-training-regimen/manuscript.md`
- decisions:
  - Wang et al. (2025, arXiv:2505.20903) listed without author initials — library note carries surnames only; complete in the submission pass.
  - Liu et al. (2024) cited to EMNLP 2024 (no arXiv id in the vault note).
### 009-writeup - Paper 1 v2 polish: ref completions, plain-language captions, figure label fix; PR opened

- at: `2026-07-01T23:59:00Z`
- kind: `writeup`
- summary: (1) Completed the two deferred reference entries: Wang et al. 2505.20903 full author list fetched from the arXiv API (Ziming Wang, Zeyu Shi, Haoyi Zhou, Shiqi Gao, Qingyun Sun, Jianxin Li); Liu et al. 2024 completed from the vault note 2024.emnlp-main.1205 (7 authors, DOI, EMNLP proceedings — not on arXiv). (2) Per user request, every Figure 1-8 caption in draft-v2 now ends with an "In plain terms:" sentence explaining the chart without jargon. (3) Fixed the fig-p1-05/06 value-label inconsistency in build_paper1_figures.py (labels printed raw 0-1 values on 0-100 axes; now printed on the axis scale) and re-rendered; visually verified. (4) Paper-1 changes committed on a docs branch built in a separate git worktree off origin/main (Gemma seed-703 extraction still reading this working tree) and PR'd to main with user authorization to merge.
- evidence:
  - `papers/paper-2-training-regimen/manuscript.md`
  - `papers/paper-2-training-regimen/scripts/build_figures.py`
### 010-writeup - Paper 1 abstract tightened (~430 -> ~215 words); PR #140 merged

- at: `2026-07-02T00:20:00Z`
- kind: `writeup`
- summary: Per user review ("the abstract in this draft seems wayyy too long"), cut the draft-v2 abstract from ~430 words / two result-dense paragraphs to one ~215-word paragraph keeping the stage-decomposition claim, the confidence-channel negative, and the probe-vs-emitted gap; all dropped numbers remain in sections 6-8. Merged as PR #140 (follow-up to #139).
- evidence:
  - `papers/paper-2-training-regimen/manuscript.md`
### 011-design - NEW proposed line: pretrain-only readout (base-model era study)

- at: `2026-07-02T00:50:00Z`
- kind: `design`
- summary: User raised that all "training-free" readout evidence sits on vendor-post-trained instruct checkpoints (Amendment W's "raw base" = Qwen3-4B Instruct, no adapter of ours; X/Z/SR likewise), so Paper 1 §8's pretraining-origin claim is untested. Captured a design-only proposal at docs/plans/base-model-era-readout.md: Arm A paired base-vs-instruct contrasts (Qwen3-4B, Llama-3.2-3B, Mistral-7B-v0.1 pairs; H_B1 base gate ≥0.90 with a stated falsifier, H_B2 base veto ≥0.65 on ≥2/3), Arm B descriptive era ladder (gpt2-xl → pythia-2.8b → Llama-2-7B base → OLMo-2). Infra prereq: backward-compatible base-mode (no-chat-template, k-shot) prompting path in the X extractor + SR-style adequacy gate. NOT registered, NOT launched; sequenced behind the SR PR.
- evidence:
  - `docs/plans/base-model-era-readout.md`
### 012-design - Amendment Y drafted (pretrain-only base readout), NOT SIGNED

- at: `2026-07-01T14:40:00Z`
- kind: `design`
- summary: Per user direction to set the new experiment up through the experiment-runner skill, the base-model era proposal (docs/plans/base-model-era-readout.md) was promoted to a formal amendment draft following reference/protocol-amendments.md + the template: experiments/pretrain-only-base-readout/AMENDMENT.md (letter Y is the first unused). Status DRAFT / NOT SIGNED. Gates frozen in the draft: H_B1 base gate >=0.90 with falsifier (base <0.75 while sibling >=0.95 -> post-training CREATES the signal), H_B2 base veto >=0.65 on >=2/3 Arm A bases, H_B3 report-only sharpening delta, SR-style adequacy floor (proposed 50/50 rows). Branch discipline honored: the draft file is deliberately left UNCOMMITTED (untracked) — it must NOT ride the SR branch; it gets its own branch off main after the SR PR merges, then user sign-off, then (separately) launch approval naming exact cells/lane.
- evidence:
  - `experiments/pretrain-only-base-readout/AMENDMENT.md`
### 013-result - Amendment SR VERDICT: SUCCESS (Gemma re-run complete, 12/12 cells)

- at: `2026-07-01T22:30:00Z`
- kind: `result`
- summary: Gemma-4-E4B re-run (user-approved relaunch with --user 0:0 after the 9P mkdir PermissionError; lab-notebook re-run of a pre-registered cell) completed 22:18 UTC — smoke OK, three sampled-decode seeds extracted and scored in-run: 20260701 dial 0.802 / veto 0.762, 20260702 dial 0.839 / veto 0.746, 20260703 dial 0.812 / veto 0.718; gate 0.998 all, adequacy OK all. LOCKED verdict computed: (a) dial seed-stable 4/4 PASS (12/12 cells), (b) veto seed-stable 4/4 PASS, (c) per-seed veto majority 3/4, 4/4, 4/4 PASS — seed 20260701 (the pre-identified pinch: Ministral 0.606) clears at exactly 3/4 via Gemma. Falsifier did NOT fire (only Ministral flips status; >=2 required). Z magnitudes promoted to seed-robust-under-sampled-decoding. AMENDMENT-SR sec 7 filled (tables, roll-up, verdict, provenance incl. sr_rr_* dirs); paper3 draft finalized (abstract point 3 + co-headline reworded to the decode-artifact finding, sec 4.7 closing, sec 4.8 Table 2 + verdict paragraph, sec 5 pipeline veto note, sec 6 discussion, sec 7 limitation 1). Both greedy Z-margin misses moved UP under sampling (Llama 0.633 FAIL -> 0.68-0.80 3/3 PASS; Qwen3.5 0.666 marginal -> 3/3 clean): greedy point estimates understated the veto.
- evidence:
  - `experiments/sampled-decode-seed-robustness/AMENDMENT.md`
  - `papers/paper-4-two-signal-readout/manuscript.md`
  - `experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_gemma-4-e4b_seed20260701_result.json`
  - `experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_gemma-4-e4b_seed20260702_result.json`
  - `experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_gemma-4-e4b_seed20260703_result.json`
### 014-refactor - FIVE-paper line executed (Paper 1 split back out; Paper 2 slimmed)

- at: `2026-07-02T00:45:00Z`
- kind: `refactor`
- summary: Executed the user's five-paper re-steer on branch paper-line-restructure (off main post-PR #141). Renames (git mv): paper1-training-regimen-draft-v{0,1,2} -> paper2-*, paper2-knows-but-doesnt-say -> paper3-*, paper3-two-signal-readout -> paper4-*. NEW Paper 1 written (papers/paper-1-taxonomy-framework/manuscript.md): standalone taxonomy + evidence synthesis + policy-vs-signal framework with three propositions (P1 locus / P2 policy-not-signal / P3 readout) and the program agenda; Meno/Daedalus tether image surfaced from the source-of-record so Paper 3's citation of it stays true. Paper 2 draft-v2 slimmed 1094 -> 677 lines: Part I replaced by a one-page Section 2 citing Paper 1; sections 7-8 (confidence-channel depth + probe coda) replaced by a short Section 5 bridge (confidence tracks the decision, not the truth + forward pointer to Paper 3); references pruned 46 -> 21 (verified one-to-one). Per user direction mid-turn, the mix-and-match stacks are compressed to a ONE-SENTENCE null (table rows dropped; Figure 6 keeps stack points as visual support) and the paper is explicitly the SFT-warm -> DPO/KTO/GRPO story. Seed-accounting check against run records: cold-start and SFT-warmed arms are 3-seed (KTO 2 plain-answer seeds); ALL GRPO cells single-seed exploratory - user's "3 seeds each" memory corrected in-session. meta-analysis/draft-v0 un-archived as Paper 1's source of record; cross-refs fixed in paper3/paper4 drafts, research-trajectory.md (Publication shape rewritten to the five-paper line; stale supersession note corrected), papers/paper-4-two-signal-readout/notes/framework.md, and the internal-paper3 KG note (slug accurate again). Figure/script prefixes (fig-p1-*/build_paper1_* etc.) deliberately NOT renamed - legacy mapping documented in research-trajectory.md. OWED FOLLOW-UP: Paper 3 must absorb the draft-v2 sections 7-8 depth (proper-scoring negative, contrastive/masked, RL-on-contrastive, Figs 7-8).
- evidence:
  - `papers/paper-1-taxonomy-framework/manuscript.md`
  - `papers/paper-2-training-regimen/manuscript.md`
  - `docs/research-trajectory.md`
