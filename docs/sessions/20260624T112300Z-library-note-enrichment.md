---
schema_version: research-session/v1
session_id: 20260624T112300Z-library-note-enrichment
title: Library Note Enrichment
status: complete
created_at: '2026-06-24T11:23:00Z'
updated_at: '2026-06-24T17:44:37Z'
phase: phase1
question: How do we bring the skeleton paper notes in library/notes up to the enriched
  exemplar standard (Summary / Extracted numbers / Relevance to experiment, plus concept
  atoms and typed edges), at scale and with verified provenance?
tags:
- knowledge-graph
- kg-ingest
- library
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: The library has 121 paper notes and 208 concept atoms, but most
    paper notes are skeletons with empty analytical bodies. This session starts a
    cluster-by-cluster enrichment pass so each collected paper carries a verified
    summary, provenance-cited results, and an explicit tie to the experiment design.
  changed_by_session: Designed and piloted a Sonnet-4.6 extract-then-adversarially-verify
    enrichment workflow; patched three pilot notes to the exemplar standard; mapped
    the full backlog into two enrichment tracks.
checkpoints:
- id: 001-planning
  at: '2026-06-24T11:23:00Z'
  kind: planning
  title: Scope And Process Aligned
  summary: Aligned the goal (enrich skeleton paper notes to the exemplar standard)
    and the process (cluster by topic via the area field, full fulltext/table mining
    on Sonnet 4.6, hard adversarial verification of every extracted number, paper
    bodies plus concept atoms plus new typed edges). Inventoried the backlog.
  evidence:
  - library/notes/2606.24790--grad-detect-gradient-hallucination-detection.md
  - library/notes/2401.13275--can-ai-assistants-know-what-they-dont-know.md
  - .skills/kg-ingest/SKILL.md
  run_ids: []
  commands: []
  decisions:
  - 'Backlog: 103 of 121 notes are skeletons (empty Summary). 91 have fulltext HTML
    on disk; 12 spine papers have no source and are re-fetched from arXiv.'
  - 'Two enrichment tracks: 26 skeletons already carry the KG graph (body-only enrichment);
    77 are pre-graph stubs (need kg block, edges, Claims, atoms, AND body). The pilot
    covers both modes.'
  - Cluster by the existing note `area` field (calibration 23, verification 23, methods
    21, abstention-finetuning 18, datasets-benchmarks 12, sycophancy 11, hallucination
    8, foundations 5); no separate LLM clustering pass.
  - All extraction/verification/patch agents run on Sonnet 4.6; Opus only orchestrates
    and applies the deterministic serial note writes.
  next_steps:
  - Get the body format signed off on the three pilot notes before scaling.
  - 'Build the two-track sweep: body-only enrichment for the 26 graph-complete skeletons;
    kg-ingest graph plus body enrichment for the 77 pre-graph stubs.'
  signals: {}
- id: 002-result
  at: '2026-06-24T11:23:00Z'
  kind: result
  title: Three-Paper Pilot Patched And Verified
  summary: Ran the extract-then-verify workflow (6 Sonnet agents) over three papers
    spanning three clusters and both graph modes, then spliced the corrected bodies
    into the notes. The adversarial verify stage caught real provenance errors that
    were corrected before writing.
  evidence:
  - library/notes/2306.03341--inference-time-intervention.md
  - library/notes/2410.09724--taming-overconfidence-rlhf.md
  - library/notes/2305.18290--direct-preference-optimization.md
  run_ids: []
  commands: []
  decisions:
  - 'DPO (2305.18290, graph-complete): 8/8 numbers confirmed, body spliced as-is;
    also validated the no-source re-fetch path.'
  - 'ITI (2306.03341, pre-graph): verify caught a backwards cross-entropy comparison
    (ITI has higher CE than SFT, not lower) and a misattribution (the generation-discrimination
    gap was coined by Saunders et al., not Li et al.); both fixed before writing.'
  - 'Taming Overconfidence (2410.09724, pre-graph): verify flagged a genuine internal
    inconsistency in the paper (intro 6.44/2.73 vs Table 4.2 ~6.6/~3.1), a Figure
    3 vs Figure 6 misattribution, and a half-described PPO-M loss; all corrected in
    the note.'
  - 'Proposed graph additions held for sign-off: new atoms inference-time-intervention,
    generation-discrimination-gap, ppo-m-calibrated-reward-modeling, ppo-c-calibrated-reward-calculation,
    cdpo-calibrated-dpo; two new mechanisms; the remaining edge targets already exist
    and are reused.'
  next_steps:
  - On format approval, write the held atoms/mechanisms and patch the pre-graph note
    frontmatter (kg block, related, relationships, Claims), then run the kg-ingest
    Move 4 validator.
  - Convert the pilot workflow into the two-track cluster sweep over the remaining
    100 skeletons.
  signals: {}
- id: 003-result
  at: '2026-06-24T11:46:56Z'
  kind: result
  title: Hallucination Cluster Enriched (6 notes)
  summary: 'Ran the scaled extract->verify->revise pipeline (18 Sonnet agents) over
    the 6 hallucination-cluster skeletons and applied results deterministically with
    enrich_apply.py. 2 body-only, 4 full-graph; 15 new atoms/mechanisms written. Validator:
    272 graph notes, 0 errors. Provenance lines normalized to library/fulltext paths.'
  evidence:
  - library/notes/2311.14648--calibrated-lms-must-hallucinate.md
  - library/notes/2405.01525--flame-factuality-aware-alignment.md
  - library/notes/2509.04664--why-language-models-hallucinate.md
  run_ids: []
  commands: []
  decisions:
  - Added a third 'revise' workflow stage that folds verify corrections into an applier-ready
    artifact, so notes are written deterministically (enrich_apply.py) rather than
    hand-patched.
  - Body-only notes keep their existing graph and do not get new atoms written (2403.05612
    proposed wikibios/wikiplots, intentionally skipped).
  next_steps:
  - Promote enrich_apply.py and the 3-stage workflow into the kg-ingest skill once
    proven across one more cluster.
  - 'Continue cluster-by-cluster: calibration (19), methods (17), verification (16),
    abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), then the
    2+2 small clusters.'
  signals: {}
- id: 004-result
  at: '2026-06-24T12:15:57Z'
  kind: result
  title: Calibration Cluster Enriched (19 notes)
  summary: 'Ran the generalized args-driven enrich-cluster workflow (57 Sonnet agents)
    over all 19 calibration skeletons; applied deterministically. ~70 new atoms/mechanisms
    written, zero new dangling links. Validator: 362 graph notes, 0 errors. 75 skeletons
    remain.'
  evidence:
  - library/notes/1706.04599--on-calibration-of-modern-neural-networks.md
  - library/notes/2303.08774--gpt4-technical-report.md
  - library/notes/2505.01997--restoring-calibration-aligned-llms.md
  run_ids: []
  commands: []
  decisions:
  - Generalized the workflow to read papers from args (enrich_cluster.js) so each
    cluster is one parameterized call; baked the library/fulltext provenance instruction
    in.
  - 'Hardened enrich_apply.py: normalize agent slugs (strip [[]]/paths/.md), blank
    unresolved claim links, drop bare-arxiv-id claim sources, dedupe cross-paper slugs
    by keeping first. Result: zero new dangling links across 19 papers.'
  - 'Skeleton detection via ''filled during extraction'' has false positives: 2207.05221
    was already enriched; the applier safely refused to overwrite (stub-missing no-op).'
  next_steps:
  - Promote enrich_apply.py + enrich_cluster.js into the kg-ingest skill as the standing
    enrichment path.
  - 'Continue clusters: methods (17), verification (16), abstention-finetuning (16),
    datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4).'
  signals: {}
- id: 005-infrastructure
  at: '2026-06-24T12:21:46Z'
  kind: infrastructure
  title: Enrichment Tooling Promoted Into kg-ingest Skill
  summary: 'Promoted the cluster-enrichment path into the kg-ingest skill: enrich_prep.py
    (acquire + clean-text), enrich_cluster.js (extract->verify->revise on Sonnet,
    args-driven), enrich_apply.py (deterministic robust applier). Documented a new
    ''Enriching existing notes (cluster backfill)'' section in SKILL.md. Synced canonical
    .skills to both mirrors; drift-check clean.'
  evidence:
  - .skills/kg-ingest/scripts/enrich_apply.py
  - .skills/kg-ingest/scripts/enrich_cluster.js
  - .skills/kg-ingest/scripts/enrich_prep.py
  - .skills/kg-ingest/SKILL.md
  run_ids: []
  commands:
  - python3 bin/sync_skills.py --write --skill kg-ingest
  decisions:
  - 'Cluster enrichment is now standing kg-ingest infra, not scratchpad tooling: prep
    -> enrich_cluster (Sonnet) -> enrich_apply -> Move 4 finalize, a topic cluster
    at a time.'
  next_steps:
  - 'Run remaining clusters via the promoted scripts: methods (17), verification (16),
    abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary
    (4).'
  signals: {}
- id: 006-result
  at: '2026-06-24T12:45:18Z'
  kind: result
  title: Methods Cluster Enriched (17 notes)
  summary: 'First cluster run entirely through the promoted kg-ingest scripts (prep/enrich_cluster/apply).
    51 Sonnet agents; 14 pre-graph + 3 body-only; ~73 new atoms/mechanisms. Validator:
    440 graph notes, 0 errors after one fix. 58 skeletons remain.'
  evidence:
  - library/notes/1707.06347--proximal-policy-optimization.md
  - library/notes/2402.03300--deepseekmath-grpo.md
  - .skills/kg-ingest/scripts/enrich_apply.py
  run_ids: []
  commands: []
  decisions:
  - 'Hardened build_type_index to read each concept''s real kg.id namespace instead
    of inferring from its directory: a pre-existing misplaced file (methods/policy-gradient.md
    declaring term:policy-gradient) had caused 3 KG332 target_id mismatches. Fixed
    the 3 edges and re-synced the skill.'
  next_steps:
  - 'Continue clusters via the skill scripts: verification (16), abstention-finetuning
    (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4).'
  signals: {}
- id: 007-checkpoint
  at: '2026-06-24T15:06:21Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Verification cluster (16 notes): harvested and applied 14 completed revise
    artifacts from workflow wf_9aca9dc1-785; the 2 that hit the session limit (2512.00218,
    2606.13669) are re-running via resume. The 14: 24 new atoms/mechanisms written,
    0 unresolved edges, 0 validator errors. Graph at 661 notes; reindex 959 files
    / 9399 nodes / 16160 edges. Three body-only notes (2308.10248, 2309.16042, 2312.06681)
    kept terse prior relevance, so the richer verified relevance was spliced in by
    hand.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Harvest the 2 re-run papers from wd3mzl49o, apply, validate, reindex.
  signals: {}
- id: 008-checkpoint
  at: '2026-06-24T15:22:31Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Verification cluster complete: all 16/16 notes enriched and applied. The
    2 papers that had hit the session limit (2512.00218 pre-graph, 2606.13669 body-only
    Agents-K1) were recovered by resuming workflow wf_9aca9dc1-785 and applied; 2512.00218
    added 5 atoms + 2 mechanisms. Ran a session-wide dash audit: fixed em dashes /
    double-hyphens in my own prose (number-bullet takeaways in 2406.11717, 2510.09033,
    2606.13669; relevance sections of 4 body-only notes; 3 earlier-cluster concept
    files). Left verbatim quoted abstracts (## Abstract blocks) untouched to preserve
    provenance. Final: 669 graph notes, 0 validator errors; reindex 966 files / 9414
    nodes / 16216 edges.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Remaining clusters: abstention-finetuning (16), datasets-benchmarks (12), sycophancy
    (10), surveys+knowledge-boundary (4). Everything staged, not committed.'
  signals: {}
- id: 009-checkpoint
  at: '2026-06-24T16:01:43Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Abstention-finetuning cluster (16): 15 enriched and applied via workflow
    wf_5640d383-b6e. Found a misfiled note: arXiv 2402.08819 is actually ''Infinite-horizon
    optimal scheduling for feedback control'' (a networked-control-systems paper),
    not a calibration-tuning paper; its note carries the wrong arxiv id. The fetch
    was correct, so the pipeline faithfully extracted off-topic control content. Reverted
    that note to skeleton (git checkout) and deleted the 4 bogus concept files it
    spawned (voi-based-ncs-scheduling, ncs-average-cost-mdp, ncs-threshold-scheduling-structure,
    voi-decomposition-eliminates-dual-effect). 2406.08391 failed at extract (API error)
    and is re-running via resume. Dash audit fixed em dashes / double-hyphens across
    14 notes + 5 concept/README sources; regenerated README MOC (461 entries). Graph
    733 notes, 0 validator errors; reindex 1019 files / 9531 nodes / 16810 edges.
    Two pre-existing dangling refs (gradient-probe-coherence, 2309.07875) to not-yet-ingested
    papers.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - arXiv 2402.08819 is mislabeled in the library (wrong id for 'calibration-tuning-workshop');
    needs user input on correct id or relabel/removal. Excluded from enrichment.
  next_steps:
  - 'Harvest 2406.08391 from wmm182lvz, apply. Then remaining clusters: datasets-benchmarks
    (12), sycophancy (10), surveys+knowledge-boundary (4). Surface the 2402.08819
    mislabel to the user.'
  signals: {}
- id: 010-checkpoint
  at: '2026-06-24T16:41:55Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Abstention-finetuning cluster DONE: 15 papers enriched and applied (2406.08391
    recovered via resume wmm182lvz, 2 atoms + 2 mechs). Misfiled note 2402.08819 (a
    control-systems paper wrongly filed as calibration-tuning-workshop) removed per
    user decision; git rm, no dangling inbound refs. Dash audit clean. Final: 738
    graph notes, 0 validator errors; reindex 1022 files (1 removed) / 9539 nodes /
    16865 edges.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - User chose to REMOVE the misfiled 2402.08819 note (wrong arxiv id, off-topic control-systems
    paper). Done via git rm.
  next_steps:
  - 'Remaining clusters: datasets-benchmarks (12), sycophancy (10), surveys (2) +
    knowledge-boundary (2). Everything staged/not committed.'
  signals: {}
- id: 011-checkpoint
  at: '2026-06-24T16:58:39Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Datasets-benchmarks cluster DONE: all 12 enriched and applied via workflow
    wf_d2651148-eb4 (no failures, no misfiles; titles all matched note slugs). 35
    new atoms/mechs, 0 unresolved edges, 0 cross-paper dups. Dash audit fixed 3 prose
    dashes (2305.13712, 2403.03558). Final: 774 graph notes, 0 validator errors; reindex
    1050 files / 9603 nodes / 17155 edges.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Remaining clusters: sycophancy (10), surveys (2) + knowledge-boundary (2). Everything
    staged/not committed.'
  signals: {}
- id: 012-checkpoint
  at: '2026-06-24T17:32:10Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Sycophancy cluster DONE: all 10 enriched and applied via workflow wf_8c098eaa-435
    (no failures, no misfiles). 46 new atoms/mechs, 0 unresolved edges. Oversized
    2308.03958 (273k tok) truncated to 140k before the run. Dash audit fixed prose
    dashes across 3 notes + 2 concept files. Final: 830 graph notes, 0 validator errors;
    reindex 1096 files / 9705 nodes / 17548 edges.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Final cluster: surveys (2407.18418, 2409.18786) + knowledge-boundary (2606.05145,
    2606.06475) = 4 papers, running now.'
  signals: {}
- id: 013-checkpoint
  at: '2026-06-24T17:44:37Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Final cluster DONE: surveys (2) + knowledge-boundary (2) enriched and
    applied via workflow wf_1e2c2741-d91 (no failures, no misfiles). 19 new atoms/mechs,
    0 unresolved edges. Dash audit fixed 1 bullet. WHOLE BACKFILL COMPLETE: 0 skeleton
    notes remain in library/notes. Final graph: 849 notes, 0 validator errors; reindex
    1112 files / 9740 nodes / 17698 edges.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - 'Library note enrichment finished across all clusters: pilot + hallucination +
    calibration + methods + verification (16) + abstention (15, 1 misfile removed)
    + datasets-benchmarks (12) + sycophancy (10) + surveys/knowledge-boundary (4).
    All on Sonnet 4.6 via extract->verify->revise workflow + deterministic apply.
    Everything staged, NOT committed.'
  next_steps:
  - User to review staged changes and decide on commit. The 2402.08819 misfile was
    removed; two pre-existing dangling refs (gradient-probe-coherence, 2309.07875)
    point to not-yet-ingested papers.
  signals: {}
legacy_session:
  id: library-note-enrichment
  path: docs/sessions/0010 - library-note-enrichment.md
---
# Library Note Enrichment

## Question

How do we bring the skeleton paper notes in `library/notes` up to the enriched
exemplar standard (Summary / Extracted numbers / Relevance to experiment, plus
concept atoms and typed edges), at scale and with verified provenance?

## Trajectory Position

The library has 121 paper notes and 208 concept atoms, but most paper notes are
skeletons with empty analytical bodies. This session starts a cluster-by-cluster
enrichment pass so each collected paper carries a verified summary,
provenance-cited results, and an explicit tie to the experiment design.

## Summary

Started the library enrichment effort. The plan: cluster the skeleton notes by
their `area` field, mine fulltext and results tables on Sonnet 4.6, and run an
adversarial verification stage that re-checks every extracted number against the
source before it is written. Scope is paper bodies plus concept atoms plus new
typed edges. The backlog splits into two tracks: 26 skeletons already have the KG
graph and need only the body; 77 are pre-graph stubs needing the full ingest plus
body. A three-paper pilot (one per track-mode, three clusters) proved the
pipeline: the verify stage caught a backwards metric comparison, a term
misattribution, a figure misattribution, and surfaced a real internal
inconsistency in one source paper, all corrected before the notes were patched.

## Checkpoints

### 001-planning - Scope And Process Aligned

- at: `2026-06-24T11:23:00Z`
- kind: `planning`
- summary: Aligned goal and process and inventoried the backlog (103 skeletons, 91 with fulltext, 12 spine papers re-fetched; 26 graph-complete vs 77 pre-graph).
- evidence:
  - `library/notes/2606.24790--grad-detect-gradient-hallucination-detection.md`
  - `library/notes/2401.13275--can-ai-assistants-know-what-they-dont-know.md`
  - `.skills/kg-ingest/SKILL.md`
- decisions:
  - Cluster by the existing `area` field; no separate LLM clustering pass.
  - All extraction/verification/patch agents run on Sonnet 4.6; Opus orchestrates.
  - Two enrichment tracks: body-only (26) and full ingest plus body (77).
- next steps:
  - Get body-format sign-off on the pilot before scaling.
  - Build the two-track cluster sweep.

### 002-result - Three-Paper Pilot Patched And Verified

- at: `2026-06-24T11:23:00Z`
- kind: `result`
- summary: Ran extract-then-verify (6 Sonnet agents) over ITI, Taming Overconfidence, and DPO; spliced corrected bodies after the verify stage caught real provenance errors.
- evidence:
  - `library/notes/2306.03341--inference-time-intervention.md`
  - `library/notes/2410.09724--taming-overconfidence-rlhf.md`
  - `library/notes/2305.18290--direct-preference-optimization.md`
- decisions:
  - Verify caught and we fixed: a backwards CE comparison (ITI), a term coinage misattribution (ITI), a Figure 3 vs 6 misattribution (Taming), and we flagged a real internal inconsistency in the Taming paper.
  - Proposed new atoms and mechanisms are held for sign-off; existing edge targets are reused, not duplicated.
- next steps:
  - On approval, write held atoms/mechanisms, patch pre-graph frontmatter, run the kg-ingest Move 4 validator.
  - Scale to the two-track cluster sweep over the remaining ~100 skeletons.
### 003-result - Hallucination Cluster Enriched (6 notes)

- at: `2026-06-24T11:46:56Z`
- kind: `result`
- summary: Ran the scaled extract->verify->revise pipeline (18 Sonnet agents) over the 6 hallucination-cluster skeletons and applied results deterministically with enrich_apply.py. 2 body-only, 4 full-graph; 15 new atoms/mechanisms written. Validator: 272 graph notes, 0 errors. Provenance lines normalized to library/fulltext paths.
- evidence:
  - `library/notes/2311.14648--calibrated-lms-must-hallucinate.md`
  - `library/notes/2405.01525--flame-factuality-aware-alignment.md`
  - `library/notes/2509.04664--why-language-models-hallucinate.md`
- decisions:
  - Added a third 'revise' workflow stage that folds verify corrections into an applier-ready artifact, so notes are written deterministically (enrich_apply.py) rather than hand-patched.
  - Body-only notes keep their existing graph and do not get new atoms written (2403.05612 proposed wikibios/wikiplots, intentionally skipped).
- next steps:
  - Promote enrich_apply.py and the 3-stage workflow into the kg-ingest skill once proven across one more cluster.
  - Continue cluster-by-cluster: calibration (19), methods (17), verification (16), abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), then the 2+2 small clusters.
### 004-result - Calibration Cluster Enriched (19 notes)

- at: `2026-06-24T12:15:57Z`
- kind: `result`
- summary: Ran the generalized args-driven enrich-cluster workflow (57 Sonnet agents) over all 19 calibration skeletons; applied deterministically. ~70 new atoms/mechanisms written, zero new dangling links. Validator: 362 graph notes, 0 errors. 75 skeletons remain.
- evidence:
  - `library/notes/1706.04599--on-calibration-of-modern-neural-networks.md`
  - `library/notes/2303.08774--gpt4-technical-report.md`
  - `library/notes/2505.01997--restoring-calibration-aligned-llms.md`
- decisions:
  - Generalized the workflow to read papers from args (enrich_cluster.js) so each cluster is one parameterized call; baked the library/fulltext provenance instruction in.
  - Hardened enrich_apply.py: normalize agent slugs (strip [[]]/paths/.md), blank unresolved claim links, drop bare-arxiv-id claim sources, dedupe cross-paper slugs by keeping first. Result: zero new dangling links across 19 papers.
  - Skeleton detection via 'filled during extraction' has false positives: 2207.05221 was already enriched; the applier safely refused to overwrite (stub-missing no-op).
- next steps:
  - Promote enrich_apply.py + enrich_cluster.js into the kg-ingest skill as the standing enrichment path.
  - Continue clusters: methods (17), verification (16), abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4).
### 005-infrastructure - Enrichment Tooling Promoted Into kg-ingest Skill

- at: `2026-06-24T12:21:46Z`
- kind: `infrastructure`
- summary: Promoted the cluster-enrichment path into the kg-ingest skill: enrich_prep.py (acquire + clean-text), enrich_cluster.js (extract->verify->revise on Sonnet, args-driven), enrich_apply.py (deterministic robust applier). Documented a new 'Enriching existing notes (cluster backfill)' section in SKILL.md. Synced canonical .skills to both mirrors; drift-check clean.
- evidence:
  - `.skills/kg-ingest/scripts/enrich_apply.py`
  - `.skills/kg-ingest/scripts/enrich_cluster.js`
  - `.skills/kg-ingest/scripts/enrich_prep.py`
  - `.skills/kg-ingest/SKILL.md`
- commands:
  - `python3 bin/sync_skills.py --write --skill kg-ingest`
- decisions:
  - Cluster enrichment is now standing kg-ingest infra, not scratchpad tooling: prep -> enrich_cluster (Sonnet) -> enrich_apply -> Move 4 finalize, a topic cluster at a time.
- next steps:
  - Run remaining clusters via the promoted scripts: methods (17), verification (16), abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4).
### 006-result - Methods Cluster Enriched (17 notes)

- at: `2026-06-24T12:45:18Z`
- kind: `result`
- summary: First cluster run entirely through the promoted kg-ingest scripts (prep/enrich_cluster/apply). 51 Sonnet agents; 14 pre-graph + 3 body-only; ~73 new atoms/mechanisms. Validator: 440 graph notes, 0 errors after one fix. 58 skeletons remain.
- evidence:
  - `library/notes/1707.06347--proximal-policy-optimization.md`
  - `library/notes/2402.03300--deepseekmath-grpo.md`
  - `.skills/kg-ingest/scripts/enrich_apply.py`
- decisions:
  - Hardened build_type_index to read each concept's real kg.id namespace instead of inferring from its directory: a pre-existing misplaced file (methods/policy-gradient.md declaring term:policy-gradient) had caused 3 KG332 target_id mismatches. Fixed the 3 edges and re-synced the skill.
- next steps:
  - Continue clusters via the skill scripts: verification (16), abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4).
### 007-checkpoint - Checkpoint

- at: `2026-06-24T15:06:21Z`
- kind: `checkpoint`
- summary: Verification cluster (16 notes): harvested and applied 14 completed revise artifacts from workflow wf_9aca9dc1-785; the 2 that hit the session limit (2512.00218, 2606.13669) are re-running via resume. The 14: 24 new atoms/mechanisms written, 0 unresolved edges, 0 validator errors. Graph at 661 notes; reindex 959 files / 9399 nodes / 16160 edges. Three body-only notes (2308.10248, 2309.16042, 2312.06681) kept terse prior relevance, so the richer verified relevance was spliced in by hand.
- next steps:
  - Harvest the 2 re-run papers from wd3mzl49o, apply, validate, reindex.
### 008-checkpoint - Checkpoint

- at: `2026-06-24T15:22:31Z`
- kind: `checkpoint`
- summary: Verification cluster complete: all 16/16 notes enriched and applied. The 2 papers that had hit the session limit (2512.00218 pre-graph, 2606.13669 body-only Agents-K1) were recovered by resuming workflow wf_9aca9dc1-785 and applied; 2512.00218 added 5 atoms + 2 mechanisms. Ran a session-wide dash audit: fixed em dashes / double-hyphens in my own prose (number-bullet takeaways in 2406.11717, 2510.09033, 2606.13669; relevance sections of 4 body-only notes; 3 earlier-cluster concept files). Left verbatim quoted abstracts (## Abstract blocks) untouched to preserve provenance. Final: 669 graph notes, 0 validator errors; reindex 966 files / 9414 nodes / 16216 edges.
- next steps:
  - Remaining clusters: abstention-finetuning (16), datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4). Everything staged, not committed.
### 009-checkpoint - Checkpoint

- at: `2026-06-24T16:01:43Z`
- kind: `checkpoint`
- summary: Abstention-finetuning cluster (16): 15 enriched and applied via workflow wf_5640d383-b6e. Found a misfiled note: arXiv 2402.08819 is actually 'Infinite-horizon optimal scheduling for feedback control' (a networked-control-systems paper), not a calibration-tuning paper; its note carries the wrong arxiv id. The fetch was correct, so the pipeline faithfully extracted off-topic control content. Reverted that note to skeleton (git checkout) and deleted the 4 bogus concept files it spawned (voi-based-ncs-scheduling, ncs-average-cost-mdp, ncs-threshold-scheduling-structure, voi-decomposition-eliminates-dual-effect). 2406.08391 failed at extract (API error) and is re-running via resume. Dash audit fixed em dashes / double-hyphens across 14 notes + 5 concept/README sources; regenerated README MOC (461 entries). Graph 733 notes, 0 validator errors; reindex 1019 files / 9531 nodes / 16810 edges. Two pre-existing dangling refs (gradient-probe-coherence, 2309.07875) to not-yet-ingested papers.
- decisions:
  - arXiv 2402.08819 is mislabeled in the library (wrong id for 'calibration-tuning-workshop'); needs user input on correct id or relabel/removal. Excluded from enrichment.
- next steps:
  - Harvest 2406.08391 from wmm182lvz, apply. Then remaining clusters: datasets-benchmarks (12), sycophancy (10), surveys+knowledge-boundary (4). Surface the 2402.08819 mislabel to the user.
### 010-checkpoint - Checkpoint

- at: `2026-06-24T16:41:55Z`
- kind: `checkpoint`
- summary: Abstention-finetuning cluster DONE: 15 papers enriched and applied (2406.08391 recovered via resume wmm182lvz, 2 atoms + 2 mechs). Misfiled note 2402.08819 (a control-systems paper wrongly filed as calibration-tuning-workshop) removed per user decision; git rm, no dangling inbound refs. Dash audit clean. Final: 738 graph notes, 0 validator errors; reindex 1022 files (1 removed) / 9539 nodes / 16865 edges.
- decisions:
  - User chose to REMOVE the misfiled 2402.08819 note (wrong arxiv id, off-topic control-systems paper). Done via git rm.
- next steps:
  - Remaining clusters: datasets-benchmarks (12), sycophancy (10), surveys (2) + knowledge-boundary (2). Everything staged/not committed.
### 011-checkpoint - Checkpoint

- at: `2026-06-24T16:58:39Z`
- kind: `checkpoint`
- summary: Datasets-benchmarks cluster DONE: all 12 enriched and applied via workflow wf_d2651148-eb4 (no failures, no misfiles; titles all matched note slugs). 35 new atoms/mechs, 0 unresolved edges, 0 cross-paper dups. Dash audit fixed 3 prose dashes (2305.13712, 2403.03558). Final: 774 graph notes, 0 validator errors; reindex 1050 files / 9603 nodes / 17155 edges.
- next steps:
  - Remaining clusters: sycophancy (10), surveys (2) + knowledge-boundary (2). Everything staged/not committed.
### 012-checkpoint - Checkpoint

- at: `2026-06-24T17:32:10Z`
- kind: `checkpoint`
- summary: Sycophancy cluster DONE: all 10 enriched and applied via workflow wf_8c098eaa-435 (no failures, no misfiles). 46 new atoms/mechs, 0 unresolved edges. Oversized 2308.03958 (273k tok) truncated to 140k before the run. Dash audit fixed prose dashes across 3 notes + 2 concept files. Final: 830 graph notes, 0 validator errors; reindex 1096 files / 9705 nodes / 17548 edges.
- next steps:
  - Final cluster: surveys (2407.18418, 2409.18786) + knowledge-boundary (2606.05145, 2606.06475) = 4 papers, running now.
### 013-checkpoint - Checkpoint

- at: `2026-06-24T17:44:37Z`
- kind: `checkpoint`
- summary: Final cluster DONE: surveys (2) + knowledge-boundary (2) enriched and applied via workflow wf_1e2c2741-d91 (no failures, no misfiles). 19 new atoms/mechs, 0 unresolved edges. Dash audit fixed 1 bullet. WHOLE BACKFILL COMPLETE: 0 skeleton notes remain in library/notes. Final graph: 849 notes, 0 validator errors; reindex 1112 files / 9740 nodes / 17698 edges.
- decisions:
  - Library note enrichment finished across all clusters: pilot + hallucination + calibration + methods + verification (16) + abstention (15, 1 misfile removed) + datasets-benchmarks (12) + sycophancy (10) + surveys/knowledge-boundary (4). All on Sonnet 4.6 via extract->verify->revise workflow + deterministic apply. Everything staged, NOT committed.
- next steps:
  - User to review staged changes and decide on commit. The 2402.08819 misfile was removed; two pre-existing dangling refs (gradient-probe-coherence, 2309.07875) point to not-yet-ingested papers.
