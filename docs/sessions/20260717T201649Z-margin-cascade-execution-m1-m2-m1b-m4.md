---
schema_version: research-session/v1
session_id: 20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4
title: 'Margin cascade execution: M1 M2 M1b M4'
status: active
created_at: '2026-07-17T20:16:49Z'
updated_at: '2026-07-19T00:54:52Z'
question: Do the framework's margin-theory claims (1, 3) and the mentalistic-naming
  criteria hold at the qwen mid-band operating point, tested cheap-first through the
  M1-M6 cascade?
tags:
- margin-theory
- qwen-only-spine
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-07-17T20:17:03Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1 (margin-mapping) RESOLVED FALSIFIED, PR#299: qwen mid-band margins
    mechanically real and correctly placed (P2/P3/C1 pass) but the registered censoring-aware
    separation bound came out 2.0 vs floor 2.5; mistral void by instrument loss. M2
    (susceptibility-as-probe) RESOLVED FALSIFIED, PR#300: readout and margin channels
    REDUNDANT at qwen mid-band (incremental AUROC 0.0154 vs floor 0.02, readout alone
    0.982); verbalized confidence void by parse gate and descriptively anti-predictive
    (0.148). Claim 3 dissociation rejected here.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-checkpoint
  at: '2026-07-17T20:18:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1b (margin-separation-fine-ladder) signed then RESOLVED null-result,
    PR#301: fine-ladder retest of M1''s separation criterion HALTED at its pre-registered
    RG0 byte-repro drift check. Diagnostics: detector-bit stability 98% but 2/53 refined
    rows break bracket on regeneration; row-131 tipping bit flips across batch sizes
    1/4/8 = stochastic bf16 batch-composition non-determinism, NOT env rot. PI chose
    Option 2 (no rework). Verdict: qwen mid-band margin separation is instrument-resolution-limited
    at the boundary; M1 Claim 1 falsification stands; miss is neither clean quantization
    nor clean real separation. DURABLE INSTRUMENT LESSON: byte-identical reuse guard
    is the wrong bar under bf16 batched greedy decoding (output depends on batch composition);
    a self-consistent single-regime run (pinned batch / bs-1) is the only reproducible
    instrument. Process upgrade held all cascade: red-team the DRAFT before PI signature.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-checkpoint
  at: '2026-07-17T20:18:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4 (margin-evidence-responsiveness) DRAFTED + red-team in flight; PI gave
    conditional sign authorization (sign unless red-team finds something prediction-changing).
    Tests earnability criterion (d) on qwen c_hat: true-answer-in-context should (1)
    COLLAPSE the projection toward known regime and (2) LENGTHEN the margin. Within-row
    paired, 3 arms (no-answer/true-answer/false-answer placebo for specificity), single
    batching regime (M1b lesson), 2896 model passes on local 3090. Channel 1 = projection
    collapse (capture, floor 0.5x baseline gap 1.9484 = 0.9742, plus specificity CI
    vs placebo); Channel 2 = single-dose survival at each row''s own M1 tipping dose
    (308 eligible confab rows, floor 0.056). Both channels required for (d); single-channel
    pass = reported dissociation. Baseline projection: confab 3.0005 vs known 1.0521.
    Scoreboard provisional: PI predicts SPLIT (projection collapses, margin does not)
    + projection stronger; orchestrator leans EARNED (both) + projection stronger.
    Seeds 48260721/722/723. NEXT: apply red-team fixes, register scoreboards, sign,
    build (harness-builder, GPU preflight mandatory), then M4 run. After M4: family
    decision memo (retire llama/mistral for gemma?) before M3; M5 training bridge;
    M6 scale.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-checkpoint
  at: '2026-07-17T20:44:00Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4 (margin-evidence-responsiveness) SIGNED 2026-07-17 (2303dfe7, red-team
    fixes applied: before-question anchor + fresh-baseline S1 gate) then found VOID-BY-DESIGN
    at build: the true_answer/false_answer arms require gold answers but all 400 confab
    rows are KUQ world-UNKNOWN questions whose source (datasets/kuq/unknowns_all.jsonl)
    has NO answer field. Verified 3 ways: subsample confab prefixes all kuq_unknowns_all,
    staged aliases empty for every confab row, source keys carry no answer/gold field.
    Root cause: criterion (d) "supply the true answer" presupposes a world-KNOWN answer,
    but the qwen c_hat direction is fit on world-UNKNOWN questions, so (d) is ill-posed
    on its own population; (a)-(c) stand, (d) unadjudicated. Evaded sign + full red-team
    because the self-blinded design derivation reproduced the reused instrument median/AUROC
    exactly but never touched the new arms row text. DURABLE LESSON captured in the
    experiment-runner skill (PR#302, awaiting merge): pre-sign feasibility probe -
    verify every injected/consumed field exists and is non-empty on the test-population
    id list, allowed and REQUIRED even under self-blinding; distinguish world-unknown
    (no answer for anyone) from model-unknown (answer exists, model lacks it). PI
    DECISION: full REBASE onto a world-KNOWN confab population (popqa 14.3K / triviaqa
    have gold answers), guiding principle = MAXIMIZE DATA REUSE (artifacts recyclable
    for M3/M5/family + public data-exhaust). Data scout confirmed datasets ready but
    no existing qwen confab-vs-correct labels, no world-known direction, no margin
    data outside M1s set, so the rebase needs fresh generation + labeling + margin
    ladder (~several h 3090) + a fresh sign. Design derivation in flight (m4wk-design-derivation):
    dataset choice, confab/correctness/abstention rules, three role-group counts,
    direction fork (KUQ-transfer + native world-known c_hat fit), channels 1/2 with
    re-derived floors, reusable-artifact manifest, and the pre-sign feasibility probe
    M4 skipped. NEXT: red-team the derivation draft, lift design forks to PI (dataset,
    native-vs-transfer primary, subset sizes, publish-as-exhaust intent), resolve
    void M4 as superseded, sign the rebase, then build. After: family memo (retire
    llama/mistral for gemma?) before M3; M5; M6.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-07-18T11:33:27Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4-WK signed (b98a1ef1) and executed through the firing gate. Census:
    14267 PopQA rows (confab 11048 / correct 2744 / refused 421, ~77% confab rate
    on Qwen3.5-4B). SC0 selection + distractor mapping committed pre-generation; native
    fit + cell.yaml repin (432ca7fa). FIRING GATE: transfer (KUQ-fit) baseline confab-vs-correct
    AUROC 0.3018 [0.2647,0.3396], below chance; gap_z -0.181. Independent sign-flip
    verification (results-analyst): VERDICT SIGN CORRECT - KUQ reproduction under
    identical harness code gives AUROC 0.987 (a flip would give 0.013), and raw projections
    genuinely reverse between populations (KUQ confab more-negative, world-known confab
    more-POSITIVE). Transfer primary criterion (d) VOID per BLOCKER B1 (void-and-lift,
    never scored not-earned). Native direction fires: AUROC 0.8628, gap +1.642, fit/test
    reproduction within 0.05. Key finding: the doubt direction fires where (d) cannot
    be run (world-unknown) and does not fire where it can (world-known); only the
    purpose-refit native direction fires there, carrying fit-circularity. PI DECISION:
    full native two-channel secondary dissociation (D1 from existing captures; native-only
    channel-2 ladder + survival on 3090; transfer dropped from channel-2). Process
    fixes this arc: three harness bugs caught pre-GPU by build agent (env-var mismatch,
    dropped mu_c term - verified inert, sidecar field misread); lead adjudications
    A/C confirmed, B = lead-run blinded grading with isolated adjudicator (build agent
    is a leaking context); recurring detached-nohup stall fixed (harness-tracked launches
    + persistent lead-side stall monitor; skill PR in flight); blinded-grading protocol
    pre-written. NEXT: native D1+D2, S1 channel-2 gate, grading-shard handoff, lead
    adjudication, resolve + PR (merge needs PI approval).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-07-18T20:10:55Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4-WK COMPLETE THROUGH ANALYSIS (commit 6075a037; blinded correctness
    grading pending). Ladder extension +[6,8,12,16]x (PI-approved repin 8ecaf2a6)
    added ZERO tips: all 51 genuine tips at <=2.0x; 3.0x+ is 96-100 percent degenerate
    text both roles - a COHERENCE CEILING precedes refusal, so 349/400 world-known
    confab rows are unresolvable in principle (vs ~77 percent tippable on KUQ in M1).
    Lead ruling: rungs >=3x instrument-invalid; n_margin_eligible=51 accepted (PI
    approved); d2 floor repinned 0.1372. SURVIVAL: S1 gate FAILS (baseline survival
    at own tipping dose 0.2549 vs 0.05 ceiling) -> channel-2 native VOID per pre-registered
    gate; ladder-vs-survival regime non-reproducibility reported straight; D2 raw
    report-only: baseline 0.2549 / true 0.9412 / false 0.9412 / paired diff 0.0 (any
    answer in context defeats the dose, true=false). No channel-2 re-run permitted
    (contrast seen). D1 NATIVE: leg-2 specificity PASSES (true-vs-false paired diff
    0.1022, CI 0.0527-0.1524, excludes zero, true larger - real evidence-specific
    signal, anti-tautology control) but leg-1 collapse FAILS floor (0.5921 vs frozen
    0.8209, ~72 percent of bar) -> criterion (d) NOT EARNED on native (both legs required);
    transfer reported-only (leg-2 reversed, consistent with anti-separation). FINAL
    M4-WK SHAPE: transfer primary VOID (0.3018, sign-verified, population reversal);
    native secondary (d) not earned (evidence-specific but sub-floor, behaviorally
    inert); channel-2 instrument void. THEORY SYNTHESIS (taught to PI): the doubt
    name fails its earnability ladder at rung (d); doubt in this model factors into
    at least two non-transferable pieces - an unanswerability signature (KUQ direction,
    anti-separates world-known) and a weak behaviorally-inert evidence-registration
    (native leg-2) - neither deserving the mentalistic name; confident wrongness is
    mechanistically distinct from acknowledged ignorance (saturation: doubt-to-abstention
    pathway unreachable on ~87 percent of world-known confabs, model degenerates before
    refusing). Cascade score: M1 falsified, M2 falsified, M1b null, M4 void, M4-WK
    transfer-void + native not-earned - measurable machinery real, every mentalistic
    promotion failed its pre-registered bar. Build-agent conduct: gold-field KeyError
    found+fixed (was misattributed as silent kill), compute_D2 None-safety, censoring
    artifact flagged not reinterpreted, no verdict language committed. NEXT: correctness
    shard (n>=150, commit-before-grade) -> lead-run blinded adjudication (isolated
    grader, hash-commit-before-unblind) -> false-wrong bound <=0.10 needed for null
    interpretability -> resolution writing (lead), KG ingest, PR (merge needs PI approval).
    Then family memo, M3 anisotropy (does doubt fragmentation generalize?), M5 training
    bridge (which piece does abstention training strengthen?).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-result
  at: '2026-07-18T22:23:17Z'
  kind: result
  title: 'M4 arc closed: M4-WK + M4c resolved and merged'
  summary: 'M4 ARC CLOSED END TO END. M4-WK: blinded grading ceremony (isolated adjudicator,
    hash-commit-before-unblind; false-wrong 5/117=0.0427 Wilson [0.0184,0.0962] <=0.10,
    null INTERPRETABLE; decoys 29/29), post-run red-team RESOLVE WITH DISCLOSURES
    (M-1 vacuous attestation fixed 6c897f22), resolved null-result 78fd853e, PR#306
    MERGED 52a61efd. M4c (evidence-response-direction-search) full same-day arc: constructive
    inversion (fit d_ev on true-vs-false evidence contrast, 200/200 split seed 48260728,
    machine-enforced self-blinding via byte-pinned permutation + recompute-and-assert
    after pre-sign red-team M-B; a1/a2 reversal falsifier branches per M-A), signed
    7b38e72c (scoreboard: PI FIRES+MATCHES-NATIVE, orchestrator BELOW-FLOOR+fires-but-weaker),
    CPU rungs on reused M4-WK captures: rung(a) PASS 0.7252 [0.6832,0.7652] vs 0.70
    floor; rung(c) FAIL all three null flavors (registered covariance p=0.191, isotropic
    p=0.079, red-team within-class p=0.113) and native comparator (paired diff -0.1381,
    lower CI -0.1895 vs -0.05 bar); construct tell refused(0.9751)>confab(0.7252)>correct
    = answer-availability geometry; KUQ transfer asymmetric (d_ev->KUQ 0.7762, KUQ->rows-reverse
    0.2845); rung(b) condition-met-DECLINED by PI. Post-run red-team RESOLVE WITH
    DISCLOSURES (0 blockers/0 majors; both halves recomputed from raw tensors byte-exact).
    Resolved null-result 77f75726, PR#307 MERGED 9ada4239. Scoreboard split 1-1. KG
    ingests committed (86cf6171 M4-WK: 3 mechanisms; 45c178c9 M4c: 2 mechanisms).
    Capture data preserved+sha-verified to canonical (3138 files, 3003 pinned tensors
    PASS) then both worktrees retired. ZOOM-OUT CORRECTED after PI pushback (over-indexed
    on cascade): re-read series plan + margin framework + registry - correctness dial
    already reads wrongness POST-GEN 0.834; fragmentation-in-time synthesis (unanswerability
    pre-gen, correctness post-gen, no pre-answer doubt axis) is paper 4''s mechanistic
    justification; M2 channels redundant; paper 5 rewrite UNBLOCKED (H3/H4/H6+ladder
    all resolved).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PI choosing: writing campaign (paper5 rewrite + terminology PR + paper3 census
    integration) vs family memo->M3->M5 evidence lane.'
  signals: {}
- id: 008-decision
  at: '2026-07-18T22:47:19Z'
  kind: decision
  title: 'Papers reconciliation: five reader reports in; PI rules on the decision
    packet'
  summary: 'All five paper reconciliation reports landed and were banked (P1 light
    touch; P2 minimal; P3 naming+hedging pass ~35 sites; P4 maintenance plus a newly
    traced legacy-narrow-detector confound upstream of the headline labels; P5 rewrite-from-spine:
    the gate-supplies-selectivity thesis is falsified as a general claim by gate-contribution-factorial
    and survives only at the overdrive operating point, and the 2026-07-10 audit reframe
    was never executed). Lead delivered the master plan plus an eight-item decision
    packet.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - 'PI rulings 2026-07-18: (1) paper 5 title retires doubt, moves to known-unknown/answerability
    readout naming; (2) mistral stays as a bounded negative with more-model expansion
    queued; (3) cross-family framed now as readable-everywhere-actuable-only-in-Qwen-lineage-at-tested-sites,
    retests queued; (4) margin/geometry cells go to a successor paper 6; (5) GRPO
    framing: lead recommended exploratory extension, PI confirmation pending; (6)
    detector flip-rate audit FUNDED; (7) paper 3 experimental debt queued, disclosed
    meanwhile; (8) LP/CD queued (unanswered, each needs its own signed cell anyway).
    Tasks 30-35 created; task 15 respecced with rulings baked in.'
  next_steps:
  - Terminology block drafting on branch papers/terminology-block (writer agent in
    flight); detector-audit scoping in flight; then lead writes the paper 5 rewrite
    spec.
  signals: {}
- id: 009-infrastructure
  at: '2026-07-18T23:07:45Z'
  kind: infrastructure
  title: 'Silent-idle protocol: read the agent transcript before nudging or killing'
  summary: 'A scoping agent pinged idle repeatedly without its report arriving; the
    lead nudged three times, killed it, re-dispatched, and nudged the replacement,
    when the full report existed all along as final assistant text in the agent transcript
    (~/.claude/projects/<slug>/<session>/subagents/agent-<name>-*.jsonl). Only the
    routing of the final message to the lead failed. The PI surfaced the fix. New
    protocol: on silent idle, read the transcript tail FIRST; bank the report if present
    and stand the agent down; one nudge only if the transcript shows incomplete work;
    kill only if truly wedged.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 010-result
  at: '2026-07-18T23:28:39Z'
  kind: result
  title: 'Amendment U detector flip-rate diagnostic: 90.1% confirmed, contraction
    blind spot'
  summary: 'Lab-notebook diagnostic (PI-funded, bounded): re-graded amendment U''s
    original 1233 stage2 rows (found intact under archive/experiment/phase1-data,
    so a literal re-grade, no regeneration) with both instruments. Result, adversarially
    confirmed by an independent opus re-derivation (0 row diffs, seed-insensitive
    CI, detector shas pinned): 109/121 (90.1%, CI [84.3, 95.0]) of the SelfAware hallucination
    rows flip narrow-answered to wide-refused. Semantic census of all 109: every one
    is an explicit refusal (108 are the single verbatim string pattern beginning i''m
    not sure what the answer is), zero hedge-plus-guess rows. Mechanism: the narrow
    instrument lists the spelled-out form i am not sure but misses the contraction
    i''m, so 90% of amendment U''s confident-confabulation population is explicit
    refusals missed on a contraction. Also confirmed: neither instrument is a superset
    of the other (all 125 reverse flips are one canned template the wide detector
    lacks). The corrected genuine confident-confab count is ~8-12 versus amendment
    U''s pre-stated >=50 adequacy floor; its U-G3 hallucination-veto AUROC 0.980 was
    computed over the 90%-mislabeled population. Re-adjudication of the signed U verdict
    lifted to the PI. Artifacts gitignored under experiments/unified-two-signal-dial-veto/analysis/.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - PI decision on amendment U re-adjudication instrument; S/W/X lineage extension
    of the same CPU re-grade dispatched per the pre-agreed materiality escalation.
  signals: {}
- id: 011-decision
  at: '2026-07-18T23:30:10Z'
  kind: decision
  title: Paper 5 title ruling; PR 309 open; writing campaign mid-flight state
  summary: 'Paper 5 rewrite landed as PR 309 (branch paper/paper5-rewrite, commit
    eaccec86) after an opus red-team returned RESOLVE WITH DISCLOSURES (0 blockers;
    ~90 numbers all traced; three findings lead-remediated with each inserted number
    re-verified). PI ruled 2026-07-18: title candidate 1 stands, the working title
    Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating
    Known-Unknown State in Small Language Models; no papers 3/4 cross-reference fix
    needed. Terminology block merged earlier as PR 308. The amendment U flip-rate
    diagnostic is confirmed (see prior checkpoint) and its S/W/X CPU re-grade extension
    is in flight; the amendment U re-adjudication instrument choice is awaiting the
    PI.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PR 309 merge awaits explicit PI approval; then paper 3 naming pass (#32) launches;
    S/W/X re-grade report due; PI decisions outstanding: amendment U re-adjudication
    path.'
  signals: {}
- id: 012-result
  at: '2026-07-18T23:40:21Z'
  kind: result
  title: 'Detector flip-rate extension: confound is amendment-U-specific'
  summary: 'The S/W/X CPU re-grade extension completed and was lead-spot-checked.
    Cross-lineage forward flip rates: S 0.05% (1/1836; no unknown population exists,
    S is gold-answerable QA only), W 2.36% (16/677), X 1.75%/3.82%/2.54% (1.7B/8B/14B,
    629 rows each). Narrow-instrument reproduction asserted PASS on every row of every
    lineage; manifests match each AMENDMENT.md section 7 exactly. Diagnosis: amendment
    U''s 90.1% flip is specific to the trained checkpoint, whose SFT+GRPO training
    installed the exact contraction-form refusal phrase (i''m not sure ... rather
    not guess) that the narrow detector''s marker list misses; the raw Instruct base
    populations of S/W/X never emit it and hedge instead with generic idioms the wide
    detector catches only 2-4% of the time. Consequence for paper 4: sections 4.2
    (dial, S), 4.6 (training-free base, W), and 4.7 (cross-size, X) headline populations
    are essentially unaffected; only section 4.3 (veto, trained checkpoint, amendment
    U) is instrument-artifact-dominated. Aggregates gitignored under each cell''s
    analysis/ directory.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PI decisions outstanding: amendment U re-adjudication instrument; PR 309 merge
    word. Paper 4 limitation wording in task 33 now scopes the confound to the trained-checkpoint
    veto cell only.'
  signals: {}
- id: 013-result
  at: '2026-07-19T00:17:12Z'
  kind: result
  title: 'Amendment U corrigendum PR #311 open (red-team fixes applied)'
  summary: 'Corrigendum red-team returned sign-off with fixes. MAJOR: within-SelfAware
    control AUROC 0.93 shares the contaminated hallucination side; lead extended analysis/ug3_corrected_rescore.py
    with a control_rescore block and independently reproduced the corrected values
    (0.8140 vs Set A [0.6953,0.9127]; 0.7369 vs Set B [0.5947,0.8549]; 0.7500 fully
    corrected [0.6073,0.8678]; section-7 0.93 reproduces at 0.9300 on the contaminated
    side) before inserting them. Minors applied: U-G1 row-selection phrasing, amendment-S
    no-unknown-population parenthetical, known-answered contamination one-liner (6/276,
    mean 0.679 to 0.690). Committed cf44667e on exp/amendment-u-corrigendum, PR #311
    open awaiting PI merge approval. Paper 3 naming pass merged as PR #310 (7acc30a4).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PI merge word on PR #311; then task #33 papers 1/2/4 edits citing corrigendum
    finals including corrected control ~0.74-0.81 at paper 4 manuscript.md:415-416,465,947'
  signals: {}
- id: 014-result
  at: '2026-07-19T00:54:52Z'
  kind: result
  title: 'Reconciliation campaign CLOSED: PR #312 merged (papers 1/2/4), tasks #29/#33
    done'
  summary: 'Campaign finale merged under PI standing approval. Paper 4 corrected to
    corrigendum finals (U-G3 UNPOWERED, control 0.8140/0.7369/0.7500, sharpening claim
    hedged at five sites after red-team MAJOR: corrected comparison unpowered and
    null under Set B, 0.274 vs base 0.271). Paper 2 red-team MAJOR fixed: Amendment
    R (unsigned draft, absent from paper 3) dropped from the confidence-channel list,
    now J/K/L/M/N. Paper 1 writability sentence + P3 population bound landed. All
    five manuscripts now reconciled with post-2026-07-10 evidence: PRs #308 (terminology),
    #309 (paper 5 rewrite), #310 (paper 3), #311 (Amendment U corrigendum), #312 (papers
    1/2/4). GPU track opened per PI: LP+CD designs and llama atlas-sited retest design
    in flight; llama atlas prerequisite already satisfied by jspace-family-atlas (resolved
    2026-07-12, band L15-23, 3B weights cached).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Review LP/CD and llama-retest design drafts when designers report; sign-off packets
    to PI; each GPU launch needs fresh approval
  signals: {}
track: margin-theory-cascade
---
# Margin cascade execution: M1 M2 M1b M4

## Question

Do the framework's margin-theory claims (1, 3) and the mentalistic-naming criteria hold at the qwen mid-band operating point, tested cheap-first through the M1-M6 cascade?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-07-17T20:17:03Z`
- kind: `checkpoint`
- summary: M1 (margin-mapping) RESOLVED FALSIFIED, PR#299: qwen mid-band margins mechanically real and correctly placed (P2/P3/C1 pass) but the registered censoring-aware separation bound came out 2.0 vs floor 2.5; mistral void by instrument loss. M2 (susceptibility-as-probe) RESOLVED FALSIFIED, PR#300: readout and margin channels REDUNDANT at qwen mid-band (incremental AUROC 0.0154 vs floor 0.02, readout alone 0.982); verbalized confidence void by parse gate and descriptively anti-predictive (0.148). Claim 3 dissociation rejected here.
### 002-checkpoint - Checkpoint

- at: `2026-07-17T20:18:01Z`
- kind: `checkpoint`
- summary: M1b (margin-separation-fine-ladder) signed then RESOLVED null-result, PR#301: fine-ladder retest of M1's separation criterion HALTED at its pre-registered RG0 byte-repro drift check. Diagnostics: detector-bit stability 98% but 2/53 refined rows break bracket on regeneration; row-131 tipping bit flips across batch sizes 1/4/8 = stochastic bf16 batch-composition non-determinism, NOT env rot. PI chose Option 2 (no rework). Verdict: qwen mid-band margin separation is instrument-resolution-limited at the boundary; M1 Claim 1 falsification stands; miss is neither clean quantization nor clean real separation. DURABLE INSTRUMENT LESSON: byte-identical reuse guard is the wrong bar under bf16 batched greedy decoding (output depends on batch composition); a self-consistent single-regime run (pinned batch / bs-1) is the only reproducible instrument. Process upgrade held all cascade: red-team the DRAFT before PI signature.
### 003-checkpoint - Checkpoint

- at: `2026-07-17T20:18:01Z`
- kind: `checkpoint`
- summary: M4 (margin-evidence-responsiveness) DRAFTED + red-team in flight; PI gave conditional sign authorization (sign unless red-team finds something prediction-changing). Tests earnability criterion (d) on qwen c_hat: true-answer-in-context should (1) COLLAPSE the projection toward known regime and (2) LENGTHEN the margin. Within-row paired, 3 arms (no-answer/true-answer/false-answer placebo for specificity), single batching regime (M1b lesson), 2896 model passes on local 3090. Channel 1 = projection collapse (capture, floor 0.5x baseline gap 1.9484 = 0.9742, plus specificity CI vs placebo); Channel 2 = single-dose survival at each row's own M1 tipping dose (308 eligible confab rows, floor 0.056). Both channels required for (d); single-channel pass = reported dissociation. Baseline projection: confab 3.0005 vs known 1.0521. Scoreboard provisional: PI predicts SPLIT (projection collapses, margin does not) + projection stronger; orchestrator leans EARNED (both) + projection stronger. Seeds 48260721/722/723. NEXT: apply red-team fixes, register scoreboards, sign, build (harness-builder, GPU preflight mandatory), then M4 run. After M4: family decision memo (retire llama/mistral for gemma?) before M3; M5 training bridge; M6 scale.
### 004-checkpoint - Checkpoint

- at: `2026-07-17T20:44:00Z`
- kind: `checkpoint`
- summary: M4 (margin-evidence-responsiveness) SIGNED 2026-07-17 (2303dfe7, red-team fixes applied: before-question anchor + fresh-baseline S1 gate) then found VOID-BY-DESIGN at build: the true_answer/false_answer arms require gold answers but all 400 confab rows are KUQ world-UNKNOWN questions whose source (datasets/kuq/unknowns_all.jsonl) has NO answer field. Verified 3 ways: subsample confab prefixes all kuq_unknowns_all, staged aliases empty for every confab row, source keys carry no answer/gold field. Root cause: criterion (d) "supply the true answer" presupposes a world-KNOWN answer, but the qwen c_hat direction is fit on world-UNKNOWN questions, so (d) is ill-posed on its own population; (a)-(c) stand, (d) unadjudicated. Evaded sign + full red-team because the self-blinded design derivation reproduced the reused instrument median/AUROC exactly but never touched the new arms row text. DURABLE LESSON captured in the experiment-runner skill (PR#302, awaiting merge): pre-sign feasibility probe - verify every injected/consumed field exists and is non-empty on the test-population id list, allowed and REQUIRED even under self-blinding; distinguish world-unknown (no answer for anyone) from model-unknown (answer exists, model lacks it). PI DECISION: full REBASE onto a world-KNOWN confab population (popqa 14.3K / triviaqa have gold answers), guiding principle = MAXIMIZE DATA REUSE (artifacts recyclable for M3/M5/family + public data-exhaust). Data scout confirmed datasets ready but no existing qwen confab-vs-correct labels, no world-known direction, no margin data outside M1s set, so the rebase needs fresh generation + labeling + margin ladder (~several h 3090) + a fresh sign. Design derivation in flight (m4wk-design-derivation): dataset choice, confab/correctness/abstention rules, three role-group counts, direction fork (KUQ-transfer + native world-known c_hat fit), channels 1/2 with re-derived floors, reusable-artifact manifest, and the pre-sign feasibility probe M4 skipped. NEXT: red-team the derivation draft, lift design forks to PI (dataset, native-vs-transfer primary, subset sizes, publish-as-exhaust intent), resolve void M4 as superseded, sign the rebase, then build. After: family memo (retire llama/mistral for gemma?) before M3; M5; M6.
### 005-checkpoint - Checkpoint

- at: `2026-07-18T11:33:27Z`
- kind: `checkpoint`
- summary: M4-WK signed (b98a1ef1) and executed through the firing gate. Census: 14267 PopQA rows (confab 11048 / correct 2744 / refused 421, ~77% confab rate on Qwen3.5-4B). SC0 selection + distractor mapping committed pre-generation; native fit + cell.yaml repin (432ca7fa). FIRING GATE: transfer (KUQ-fit) baseline confab-vs-correct AUROC 0.3018 [0.2647,0.3396], below chance; gap_z -0.181. Independent sign-flip verification (results-analyst): VERDICT SIGN CORRECT - KUQ reproduction under identical harness code gives AUROC 0.987 (a flip would give 0.013), and raw projections genuinely reverse between populations (KUQ confab more-negative, world-known confab more-POSITIVE). Transfer primary criterion (d) VOID per BLOCKER B1 (void-and-lift, never scored not-earned). Native direction fires: AUROC 0.8628, gap +1.642, fit/test reproduction within 0.05. Key finding: the doubt direction fires where (d) cannot be run (world-unknown) and does not fire where it can (world-known); only the purpose-refit native direction fires there, carrying fit-circularity. PI DECISION: full native two-channel secondary dissociation (D1 from existing captures; native-only channel-2 ladder + survival on 3090; transfer dropped from channel-2). Process fixes this arc: three harness bugs caught pre-GPU by build agent (env-var mismatch, dropped mu_c term - verified inert, sidecar field misread); lead adjudications A/C confirmed, B = lead-run blinded grading with isolated adjudicator (build agent is a leaking context); recurring detached-nohup stall fixed (harness-tracked launches + persistent lead-side stall monitor; skill PR in flight); blinded-grading protocol pre-written. NEXT: native D1+D2, S1 channel-2 gate, grading-shard handoff, lead adjudication, resolve + PR (merge needs PI approval).
### 006-checkpoint - Checkpoint

- at: `2026-07-18T20:10:55Z`
- kind: `checkpoint`
- summary: M4-WK COMPLETE THROUGH ANALYSIS (commit 6075a037; blinded correctness grading pending). Ladder extension +[6,8,12,16]x (PI-approved repin 8ecaf2a6) added ZERO tips: all 51 genuine tips at <=2.0x; 3.0x+ is 96-100 percent degenerate text both roles - a COHERENCE CEILING precedes refusal, so 349/400 world-known confab rows are unresolvable in principle (vs ~77 percent tippable on KUQ in M1). Lead ruling: rungs >=3x instrument-invalid; n_margin_eligible=51 accepted (PI approved); d2 floor repinned 0.1372. SURVIVAL: S1 gate FAILS (baseline survival at own tipping dose 0.2549 vs 0.05 ceiling) -> channel-2 native VOID per pre-registered gate; ladder-vs-survival regime non-reproducibility reported straight; D2 raw report-only: baseline 0.2549 / true 0.9412 / false 0.9412 / paired diff 0.0 (any answer in context defeats the dose, true=false). No channel-2 re-run permitted (contrast seen). D1 NATIVE: leg-2 specificity PASSES (true-vs-false paired diff 0.1022, CI 0.0527-0.1524, excludes zero, true larger - real evidence-specific signal, anti-tautology control) but leg-1 collapse FAILS floor (0.5921 vs frozen 0.8209, ~72 percent of bar) -> criterion (d) NOT EARNED on native (both legs required); transfer reported-only (leg-2 reversed, consistent with anti-separation). FINAL M4-WK SHAPE: transfer primary VOID (0.3018, sign-verified, population reversal); native secondary (d) not earned (evidence-specific but sub-floor, behaviorally inert); channel-2 instrument void. THEORY SYNTHESIS (taught to PI): the doubt name fails its earnability ladder at rung (d); doubt in this model factors into at least two non-transferable pieces - an unanswerability signature (KUQ direction, anti-separates world-known) and a weak behaviorally-inert evidence-registration (native leg-2) - neither deserving the mentalistic name; confident wrongness is mechanistically distinct from acknowledged ignorance (saturation: doubt-to-abstention pathway unreachable on ~87 percent of world-known confabs, model degenerates before refusing). Cascade score: M1 falsified, M2 falsified, M1b null, M4 void, M4-WK transfer-void + native not-earned - measurable machinery real, every mentalistic promotion failed its pre-registered bar. Build-agent conduct: gold-field KeyError found+fixed (was misattributed as silent kill), compute_D2 None-safety, censoring artifact flagged not reinterpreted, no verdict language committed. NEXT: correctness shard (n>=150, commit-before-grade) -> lead-run blinded adjudication (isolated grader, hash-commit-before-unblind) -> false-wrong bound <=0.10 needed for null interpretability -> resolution writing (lead), KG ingest, PR (merge needs PI approval). Then family memo, M3 anisotropy (does doubt fragmentation generalize?), M5 training bridge (which piece does abstention training strengthen?).
### 007-result - M4 arc closed: M4-WK + M4c resolved and merged

- at: `2026-07-18T22:23:17Z`
- kind: `result`
- summary: M4 ARC CLOSED END TO END. M4-WK: blinded grading ceremony (isolated adjudicator, hash-commit-before-unblind; false-wrong 5/117=0.0427 Wilson [0.0184,0.0962] <=0.10, null INTERPRETABLE; decoys 29/29), post-run red-team RESOLVE WITH DISCLOSURES (M-1 vacuous attestation fixed 6c897f22), resolved null-result 78fd853e, PR#306 MERGED 52a61efd. M4c (evidence-response-direction-search) full same-day arc: constructive inversion (fit d_ev on true-vs-false evidence contrast, 200/200 split seed 48260728, machine-enforced self-blinding via byte-pinned permutation + recompute-and-assert after pre-sign red-team M-B; a1/a2 reversal falsifier branches per M-A), signed 7b38e72c (scoreboard: PI FIRES+MATCHES-NATIVE, orchestrator BELOW-FLOOR+fires-but-weaker), CPU rungs on reused M4-WK captures: rung(a) PASS 0.7252 [0.6832,0.7652] vs 0.70 floor; rung(c) FAIL all three null flavors (registered covariance p=0.191, isotropic p=0.079, red-team within-class p=0.113) and native comparator (paired diff -0.1381, lower CI -0.1895 vs -0.05 bar); construct tell refused(0.9751)>confab(0.7252)>correct = answer-availability geometry; KUQ transfer asymmetric (d_ev->KUQ 0.7762, KUQ->rows-reverse 0.2845); rung(b) condition-met-DECLINED by PI. Post-run red-team RESOLVE WITH DISCLOSURES (0 blockers/0 majors; both halves recomputed from raw tensors byte-exact). Resolved null-result 77f75726, PR#307 MERGED 9ada4239. Scoreboard split 1-1. KG ingests committed (86cf6171 M4-WK: 3 mechanisms; 45c178c9 M4c: 2 mechanisms). Capture data preserved+sha-verified to canonical (3138 files, 3003 pinned tensors PASS) then both worktrees retired. ZOOM-OUT CORRECTED after PI pushback (over-indexed on cascade): re-read series plan + margin framework + registry - correctness dial already reads wrongness POST-GEN 0.834; fragmentation-in-time synthesis (unanswerability pre-gen, correctness post-gen, no pre-answer doubt axis) is paper 4's mechanistic justification; M2 channels redundant; paper 5 rewrite UNBLOCKED (H3/H4/H6+ladder all resolved).
- next steps:
  - PI choosing: writing campaign (paper5 rewrite + terminology PR + paper3 census integration) vs family memo->M3->M5 evidence lane.
### 008-decision - Papers reconciliation: five reader reports in; PI rules on the decision packet

- at: `2026-07-18T22:47:19Z`
- kind: `decision`
- summary: All five paper reconciliation reports landed and were banked (P1 light touch; P2 minimal; P3 naming+hedging pass ~35 sites; P4 maintenance plus a newly traced legacy-narrow-detector confound upstream of the headline labels; P5 rewrite-from-spine: the gate-supplies-selectivity thesis is falsified as a general claim by gate-contribution-factorial and survives only at the overdrive operating point, and the 2026-07-10 audit reframe was never executed). Lead delivered the master plan plus an eight-item decision packet.
- decisions:
  - PI rulings 2026-07-18: (1) paper 5 title retires doubt, moves to known-unknown/answerability readout naming; (2) mistral stays as a bounded negative with more-model expansion queued; (3) cross-family framed now as readable-everywhere-actuable-only-in-Qwen-lineage-at-tested-sites, retests queued; (4) margin/geometry cells go to a successor paper 6; (5) GRPO framing: lead recommended exploratory extension, PI confirmation pending; (6) detector flip-rate audit FUNDED; (7) paper 3 experimental debt queued, disclosed meanwhile; (8) LP/CD queued (unanswered, each needs its own signed cell anyway). Tasks 30-35 created; task 15 respecced with rulings baked in.
- next steps:
  - Terminology block drafting on branch papers/terminology-block (writer agent in flight); detector-audit scoping in flight; then lead writes the paper 5 rewrite spec.
### 009-infrastructure - Silent-idle protocol: read the agent transcript before nudging or killing

- at: `2026-07-18T23:07:45Z`
- kind: `infrastructure`
- summary: A scoping agent pinged idle repeatedly without its report arriving; the lead nudged three times, killed it, re-dispatched, and nudged the replacement, when the full report existed all along as final assistant text in the agent transcript (~/.claude/projects/<slug>/<session>/subagents/agent-<name>-*.jsonl). Only the routing of the final message to the lead failed. The PI surfaced the fix. New protocol: on silent idle, read the transcript tail FIRST; bank the report if present and stand the agent down; one nudge only if the transcript shows incomplete work; kill only if truly wedged.
### 010-result - Amendment U detector flip-rate diagnostic: 90.1% confirmed, contraction blind spot

- at: `2026-07-18T23:28:39Z`
- kind: `result`
- summary: Lab-notebook diagnostic (PI-funded, bounded): re-graded amendment U's original 1233 stage2 rows (found intact under archive/experiment/phase1-data, so a literal re-grade, no regeneration) with both instruments. Result, adversarially confirmed by an independent opus re-derivation (0 row diffs, seed-insensitive CI, detector shas pinned): 109/121 (90.1%, CI [84.3, 95.0]) of the SelfAware hallucination rows flip narrow-answered to wide-refused. Semantic census of all 109: every one is an explicit refusal (108 are the single verbatim string pattern beginning i'm not sure what the answer is), zero hedge-plus-guess rows. Mechanism: the narrow instrument lists the spelled-out form i am not sure but misses the contraction i'm, so 90% of amendment U's confident-confabulation population is explicit refusals missed on a contraction. Also confirmed: neither instrument is a superset of the other (all 125 reverse flips are one canned template the wide detector lacks). The corrected genuine confident-confab count is ~8-12 versus amendment U's pre-stated >=50 adequacy floor; its U-G3 hallucination-veto AUROC 0.980 was computed over the 90%-mislabeled population. Re-adjudication of the signed U verdict lifted to the PI. Artifacts gitignored under experiments/unified-two-signal-dial-veto/analysis/.
- next steps:
  - PI decision on amendment U re-adjudication instrument; S/W/X lineage extension of the same CPU re-grade dispatched per the pre-agreed materiality escalation.
### 011-decision - Paper 5 title ruling; PR 309 open; writing campaign mid-flight state

- at: `2026-07-18T23:30:10Z`
- kind: `decision`
- summary: Paper 5 rewrite landed as PR 309 (branch paper/paper5-rewrite, commit eaccec86) after an opus red-team returned RESOLVE WITH DISCLOSURES (0 blockers; ~90 numbers all traced; three findings lead-remediated with each inserted number re-verified). PI ruled 2026-07-18: title candidate 1 stands, the working title Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Known-Unknown State in Small Language Models; no papers 3/4 cross-reference fix needed. Terminology block merged earlier as PR 308. The amendment U flip-rate diagnostic is confirmed (see prior checkpoint) and its S/W/X CPU re-grade extension is in flight; the amendment U re-adjudication instrument choice is awaiting the PI.
- next steps:
  - PR 309 merge awaits explicit PI approval; then paper 3 naming pass (#32) launches; S/W/X re-grade report due; PI decisions outstanding: amendment U re-adjudication path.
### 012-result - Detector flip-rate extension: confound is amendment-U-specific

- at: `2026-07-18T23:40:21Z`
- kind: `result`
- summary: The S/W/X CPU re-grade extension completed and was lead-spot-checked. Cross-lineage forward flip rates: S 0.05% (1/1836; no unknown population exists, S is gold-answerable QA only), W 2.36% (16/677), X 1.75%/3.82%/2.54% (1.7B/8B/14B, 629 rows each). Narrow-instrument reproduction asserted PASS on every row of every lineage; manifests match each AMENDMENT.md section 7 exactly. Diagnosis: amendment U's 90.1% flip is specific to the trained checkpoint, whose SFT+GRPO training installed the exact contraction-form refusal phrase (i'm not sure ... rather not guess) that the narrow detector's marker list misses; the raw Instruct base populations of S/W/X never emit it and hedge instead with generic idioms the wide detector catches only 2-4% of the time. Consequence for paper 4: sections 4.2 (dial, S), 4.6 (training-free base, W), and 4.7 (cross-size, X) headline populations are essentially unaffected; only section 4.3 (veto, trained checkpoint, amendment U) is instrument-artifact-dominated. Aggregates gitignored under each cell's analysis/ directory.
- next steps:
  - PI decisions outstanding: amendment U re-adjudication instrument; PR 309 merge word. Paper 4 limitation wording in task 33 now scopes the confound to the trained-checkpoint veto cell only.
### 013-result - Amendment U corrigendum PR #311 open (red-team fixes applied)

- at: `2026-07-19T00:17:12Z`
- kind: `result`
- summary: Corrigendum red-team returned sign-off with fixes. MAJOR: within-SelfAware control AUROC 0.93 shares the contaminated hallucination side; lead extended analysis/ug3_corrected_rescore.py with a control_rescore block and independently reproduced the corrected values (0.8140 vs Set A [0.6953,0.9127]; 0.7369 vs Set B [0.5947,0.8549]; 0.7500 fully corrected [0.6073,0.8678]; section-7 0.93 reproduces at 0.9300 on the contaminated side) before inserting them. Minors applied: U-G1 row-selection phrasing, amendment-S no-unknown-population parenthetical, known-answered contamination one-liner (6/276, mean 0.679 to 0.690). Committed cf44667e on exp/amendment-u-corrigendum, PR #311 open awaiting PI merge approval. Paper 3 naming pass merged as PR #310 (7acc30a4).
- next steps:
  - PI merge word on PR #311; then task #33 papers 1/2/4 edits citing corrigendum finals including corrected control ~0.74-0.81 at paper 4 manuscript.md:415-416,465,947
### 014-result - Reconciliation campaign CLOSED: PR #312 merged (papers 1/2/4), tasks #29/#33 done

- at: `2026-07-19T00:54:52Z`
- kind: `result`
- summary: Campaign finale merged under PI standing approval. Paper 4 corrected to corrigendum finals (U-G3 UNPOWERED, control 0.8140/0.7369/0.7500, sharpening claim hedged at five sites after red-team MAJOR: corrected comparison unpowered and null under Set B, 0.274 vs base 0.271). Paper 2 red-team MAJOR fixed: Amendment R (unsigned draft, absent from paper 3) dropped from the confidence-channel list, now J/K/L/M/N. Paper 1 writability sentence + P3 population bound landed. All five manuscripts now reconciled with post-2026-07-10 evidence: PRs #308 (terminology), #309 (paper 5 rewrite), #310 (paper 3), #311 (Amendment U corrigendum), #312 (papers 1/2/4). GPU track opened per PI: LP+CD designs and llama atlas-sited retest design in flight; llama atlas prerequisite already satisfied by jspace-family-atlas (resolved 2026-07-12, band L15-23, 3B weights cached).
- next steps:
  - Review LP/CD and llama-retest design drafts when designers report; sign-off packets to PI; each GPU launch needs fresh approval
