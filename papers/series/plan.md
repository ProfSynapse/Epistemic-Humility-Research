# Paper Series Plan: The Epistemic Humility Program

Status: planning (2026-07-10). Internal roadmap, not a draft. Supersedes the
2026-06-30 three-paper plan (its confirmatory backbone, the cross-family
replication, has since been run and landed; its paper numbering predates the
current five-paper tree). This document owns the narrative arc, the beat of
each paper, and which finding lives where. Style and voice are owned by
`papers/common/VOICE.md` (binding, including self-containment, synthesis-not-
journey, and never-explain-science-to-scientists); the AI-workflow methods
component is `papers/common/methods-ai-workflow.md`.

## The story in one sentence

Small models know more about their own ignorance than they say; training
cannot reliably push that knowledge into the mouth; you can read it out
directly instead; and you can make the model act on it, if you gate the
intervention by the model's own doubt.

## The spine: five papers, five beats

Title format is `[catchy idiom]: [subtitle naming the study]`.

| # | Paper (dir) | Title | Beat |
|---|-------------|-------|------|
| 1 | paper-1-taxonomy-framework | The Depths of Ignorance: A Taxonomy, Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in Language Models | Here is the problem space and the vocabulary. |
| 2 | paper-2-training-regimen | Teaching Small Language Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data | The front door: training the behavior in partially works and structurally disappoints. |
| 3 | paper-3-knows-but-doesnt-say | Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model | The diagnosis: the knowledge is inside, the mouth is the bottleneck. Home of the internal anatomy (the readable epistemic directions). |
| 4 | paper-4-two-signal-readout | It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models | The reading half: bypass the mouth, read the representation. Deployable today. |
| 5 | paper-5-actuation | Look Before You Speak: Operating-Point-Dependent Selectivity in Actuating Known-Unknown State (title as merged to main in PR 427; PI reconfirmed 2026-08-11) | The destination: the model acts on its own knowledge when, and only when, the write is gated by its own uncertainty readout, at the right depth. |

Build-on logic: 1 frames, 2 shows the obvious fix disappoints, 3 explains why
(and maps the internal landscape), then the diagnosis branches: 4 is "it's
readable, so read it" and 5 is "it's readable; when is it writable?". Papers 3,
4, and 5 form the core trilogy; 1 and 2 are the frame and the motivation.

## Claim ownership (one home per finding)

Rules:

- Reading-side discoveries (a direction exists, separates, transfers) live in
  paper 3 if they are part of the internal anatomy, in paper 4 if they are part
  of the deployable readout.
- Actuation results (what happens when you write) live in paper 5, always,
  including the nulls.
- A finding appears in a second paper only as one summarizing sentence with a
  citation to its home paper, never re-argued.

| Finding | Home | Notes |
|---------|------|-------|
| Taxonomy, evidence synthesis, agenda | 1 | |
| SFT/DPO/KTO/GRPO abstention comparison, calibration tradeoffs | 2 | GRPO framing: extension vs registered arm, still open |
| Internal-vs-stated gap; training resistance; channel bottleneck | 3 | |
| Internal anatomy: uncertainty axis, refusal axis (reading claims only) | 3 | Census (docs/review/paper3-direction-provenance-2026-07-10.md): the uncertainty reading is base/pretrain-validated but IS the answerability gate under another name (state the identity, do not double-count); the refusal-axis reading is real but trained-checkpoint-only (base never refuses), scope sentence must say so |
| Confab-propensity direction | 5 only | Census verdict: NOT safe as a paper 3 result (reading numbers ungoverned, checkpoint-specific to the most-trained checkpoint, governed causal outcome null). Paper 3 gets at most a one-line forward pointer |
| Caution-ablation steering result (over-refusal 0.994 to 0.030) | 5 | EXECUTED 2026-08-13 (PI ruling: "I would keep it in 5 our main point is that we don't need training BUT we do want to show it can survive training"). Paper 5 §6.6 now carries the result as trained-checkpoint durability evidence alongside the paper's raw-base headline; paper 3 section 6 keeps two summarizing sentences + citation to paper 5 §6.6, down from the prior two-paragraph treatment. Provenance caveat (lead-verified 2026-08-13): 0.994 to 0.030 (full refusal-direction ablation, phase-3 legacy actuation study, L26 coeff sweep) and 0.994 to 0.524/0.536 (`experiments/doubt-regulated-caution/AMENDMENT.md` §1/§7-8, ablating only the doubt-orthogonalized component `caution_perp`) are DIFFERENT interventions, not a numeric contradiction; paper 3's own sentence states both consistently. The real gap, flagged to the PI 2026-07-30 in `experiments/write-direction-naming-battery/AMENDMENT.md` and still open: the 0.030 run survives as archived config only (`archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`), its row-level outputs untracked, so the figure is not locally re-derivable and its source-of-record is paper prose. The component-ablation clause DOES have governed replication support (ablate arm kr 0.994 to 0.536 inside the doubt-regulated-caution run). Neither paper's number was changed as part of this ownership move. |
| Answerability gate, correctness dial, veto + decomposition (content core ~0.74) | 4 | Current after the 2026-07-10 revision arc |
| Cross-size, cross-family, seed-robustness, pretrain-origin of the readout | 4 | |
| Correctness-direction cross-checkpoint rotation and discriminative-subspace-overlap nulls (dial cold-transfer mechanism) | 4 | Both exploratory Tier-2 nulls; paper 5 §6.5 cites the pair as cross-family motivation only, never re-argued |
| Workspace localization (read-only J-lens diagnostic) | 4 (descriptive subsection) | Steering cells excluded |
| Ungated steering asymmetry; propensity-direction actuation nulls; setpoint nulls | 5 | The caveat landscape |
| Answerability-gated abstention snap (incl. multi-source replication); layer-contrast arc | 5 | The headline |
| Mid-band doubt-snap (Qwen3.5) | 5 | RUNNING; not citable until resolved |
| Cross-family actuation panel | 5 | Remaining cells await paid-launch decision |

## Per-paper state and open work

### Paper 1 (taxonomy)

Draft exists. Open: refresh the synthesis against the library's current state
when 3/4/5 stabilize; align vocabulary with the axis/readout terms the trilogy
settled on.

### Paper 2 (training regimen)

Headline matrix ran under the locked protocol. Open: GRPO framing decision
(report-as-extension vs register a confirmatory arm); consistency check of
calibration metrics with paper 4's dial scoping; voice/self-containment pass
(it predates the VOICE.md rules).

### Paper 3 (diagnosis)

Solid draft. Open:

- Integrate the internal-anatomy inventory (doubt, caution, confab-propensity)
  with honest per-direction scope sentences; blocked on the provenance census
  (docs/review/paper3-direction-provenance-2026-07-10.md when it lands).
- Standing reviewer-attack items from the old plan that remain live:
  competence-within-category gate control; multi-elicitation robustness for
  "doesn't say"; single-seed scoping on the training-resistance panel.
- Voice/self-containment pass under the current VOICE.md.
- Needs its own identifier eventually; paper 4's reference entry points at the
  research record until then.

### Paper 4 (readout) — most current

Went through the full 2026-07-10 revision arc (review memo, synthesis pass,
related-work rewrite, self-containment + headings, falsifier compression,
rename). Open:

- Splice the token-logprob baseline when computed (backlog LP; SWAP marker in
  limitation 8); gated on the mid-band ladder freeing the local GPU.
- Dial cold-transfer rotation inference upgraded to a direct measurement
  (backlog CD, resolved 2026-07-20 as a null-result) and followed up with a
  discriminative-subspace-overlap cell asking whether transfer rides on a
  shared subspace rather than a single axis (resolved 2026-07-20, also a
  null-result, instrument-limited on the reliability question it was built to
  answer). Both folded into §4.2 as exploratory Tier-2 nulls with label-clean
  positive findings, never pooled with the headline readout numbers; the
  answerability-vs-correctness portability contrast this pair establishes is
  also cited (as motivation, not a cross-family claim) in paper 5 §6.5.

### Paper 5 (actuation) — the rewrite target

Reframe per PI directive: the intervention more or less worked; caveats are
named as they appear, not led with. Spine: ungated pushes fail or act
asymmetrically; the propensity direction reads but does not actuate; the
doubt-gated caution write converts confabulations at high rate at small
known-correct cost, replicated on a multi-source pool; localization puts the
action in the workspace band. Open:

- Audit LANDED: docs/review/paper5-actuation-review-2026-07-10.md (22-cell
  inventory, 10-item reframe plan, hardening list). Lead spot-checked.
- SEQUENCING (PI decision 2026-07-10): rewrite AFTER hardening. The rewrite
  waits for the mid-band ladder outcome plus the three cheap local hardening
  cells (H3 multi-seed/sampled-decode snap replication; H4 registered
  ungated-vs-gated dose-matched arm; H6 commitment-point hook-firing
  instrument check), all queued behind the ladder freeing the 3090. Designs
  to be drafted and signed in the meantime so they launch the day the GPU
  frees.
- Title decided and reconfirmed (PI, 2026-08-11): "Look Before You Speak:
  Operating-Point-Dependent Selectivity in Actuating Known-Unknown State" --
  the title already merged to main in PR 427, which also applied the
  terminology rulings. An alternative ("Hold That Thought") was considered
  and declined.
- Cross-family actuation panel: awaits the PI's paid-launch decision; the
  paper's family scope is honest without it but stronger with it. H5 (AI-TRUE
  caution-lever screen) and H7 (cross-family J-lens profiles) stay optional,
  revisit after H1/H2 resolve.

## Cross-cutting

- Every paper gets the AI-workflow methods subsection adapted from
  `papers/common/methods-ai-workflow.md`.
- Every paper passes the current VOICE.md gates before it is called a draft:
  self-contained (no repo internals in body prose), synthesis-not-journey,
  real headings, no lecturing, registered facts compact.
- Provenance appendix pattern (paper 4's Appendix A) is the template for all
  five: body clean, one appendix maps numbers to artifacts.
- Publication mode (PI): blog companions for all papers; venue decision open
  (TMLR + arXiv discussed); collaborator outreach once drafts exist.

## Open decisions for the PI

2. Cross-family actuation panel: paid launch yes/no/when.
3. Paper 2 GRPO framing (extension vs registered confirmatory arm).
4. Venue + collaborator timing.
