---
id: task-d342cb
title: Paper 5 submission prep (MATS / fellowship)
status: in-progress
assignee:
- claude
tier: P
priority: high
experiment: ''
component: ''
depends_on: []
files:
- papers/paper-5-actuation/manuscript.md
- papers/paper-5-actuation/scripts/build_coverage_table.py
- papers/paper-5-actuation/scripts/build_instruction_amplification_fig.py
- papers/paper-5-actuation/scripts/build_restructure_figures.py
- papers/paper-5-actuation/figures/MANIFEST.md
- papers/paper-5-actuation/figures/fig-p5-10-instruction-amplification.png
- papers/paper-5-actuation/figures/fig-p5-11-gemma-depth-ladder.png
- experiments/no-abstention-prompt-gated-replication/analysis-committed/two_stage_family_summary.json
- experiments/no-abstention-prompt-gated-replication/build_two_stage_summary.py
- experiments/no-abstention-prompt-gated-replication/NOTEBOOK.md
new_files: []
blocker: PI review
created_date: '2026-08-27'
updated_date: '2026-09-01'
---
## Description
Manuscript is through the figure restructure, voice passes, and the
external-reviewer-lens pass (PRs #563-#567 merged; #568 open for the
figure-key CSV). Remaining work is whatever the submission itself requires:
final PI read, formatting, application forms. Migrated from the TODO.md
audited backlog table (row P5S, audited 2026-08-27).

## Acceptance Criteria
- [ ] Final PI read completed
- [ ] Manuscript formatting matches the target venue's submission requirements
- [ ] Application forms (MATS / fellowship) submitted

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row P5S during the task-backlog harness build.
- 2026-08-30 @claude: added the paper-2 callback (prompt-vs-training panel, 90.89% vs 0% untrained-base actuation, Rosenbaum 2026b) to the 3.7 prompt frame and 6.4 bullet, PI-requested; numbers verified against the panel AMENDMENT Outcome.
- 2026-08-30 @claude: drafted the no-abstention-prompt disclosure edits on branch paper5-no-abstention-disclosure (methods prompt-frame paragraph in 3.7, scope note in Section 5, thermostat qualification in 6.1, exploratory-replication limits bullet in 6.4). Numbers pending final resolve of experiments/no-abstention-prompt-gated-replication; PR held for PI review, no merge before resolve.
- 2026-08-30 @claude: upgraded the 6.4 bullet to v2 two-stage numbers (qwen3.5 8.9->54.4, llama 4.1->13.4) and merged PR #584 into main on PI direction; manuscript remains a draft pending PI language pass.
- 2026-08-30 @claude: filled the pending mistral number in the 6.4 bullet from the resolved Outcome (11.5 to 30.3 two-stage) and cited the resolved cell; all five families now final in the manuscript.
- 2026-09-01 @claude: voice-compliance pass on the confound additions (removed registration vocabulary, companion-handle citation, and body-prose slugs; fixed stale qwen CI to [7.0, 16.7]); reframed Llama site-split paragraph in 4.8 per PI direction; added the instruction-free replication to Appendix A and the coverage table.
- 2026-09-01 @claude: built Figure 10 (instruction amplification) for Section 5 per PI request: new committed aggregate two_stage_family_summary.json in the replication cell (asserted against its Outcome), new build_instruction_amplification_fig.py with reproduction audit, Gemma depth ladder renumbered to Figure 11, Appendix C and figures/MANIFEST.md updated.
- 2026-09-01 @claude: repaired dangling cross-references left by the PI 6.5-6.7/Conclusion cut (PR #589): rerouted or dropped Section 6.5/6.6 pointers in 3.1, 3.2, 3.4, 3.5, 4.8, and the 6.4 registration paragraph; updated Appendix A row texts; SECTION_MAP entries for cells narrated only in cut sections now read NOT NARRATED, coverage table regenerated.
- 2026-09-01 @claude: verified the PI SelfAware disclosure numbers from PR #591 against data (156/29 from the frozen split manifest; 116/156 and 20/29 clean_tighten from the operating-point regeneration reproducing the headline 136/185 exactly); wrote the governed record as a post-resolve addendum in doubt-gated-caution-tighten AMENDMENT.md plus NOTEBOOK entry; added the Appendix A audit row and updated the coverage script (slug dedupe + SECTION_MAP).
