---
schema_version: research-session/v1
session_id: 20260701T213000Z-amendment-aa-causal-confidence-steering-launch
title: "Amendment AA \u2014 causal confidence steering signed + Stage-1 launched"
status: active
created_at: '2026-07-01T21:30:00Z'
updated_at: '2026-07-02T14:45:00Z'
phase: phase1
question: "Can the trust axis be WRITTEN, not just read \u2014 and is the causal effect\
  \ position-locked (gate at the anchor, dial at the end) the way the readout amendments\
  \ decode it?"
tags:
- experiment-runner
- paper5
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'Paper 5 first experiment: Amendment AA Stage-1 in flight'
  changed_by_session: steering line moves from scaffold/design to a signed, running
    amendment
checkpoints:
- id: 001-gate
  at: '2026-07-01T21:45:00Z'
  kind: gate
  title: "Steering review \u2014 scaffold already on main, 88/88 green, Z deps satisfied"
  summary: Reviewed the Paper 5 steering experiment end-to-end. The code scaffold
    (Arm A forward-hook steering, Arm B CoT injection, direction persistence) was
    already merged to main (e53daafe + ea651726); its 88 CPU tests pass locally. All
    four Amendment-Z extraction dirs exist on disk, so the probe-direction dependency
    is satisfied. Created branch amendment-aa-confidence-steering off main @ 0046a8fd;
    relabeled the scaffold Paper 4 -> Paper 5 per the five-paper line. Fitted all
    8 unit-normed directions on CPU (gate+dial x 4 families) with persist_probe_direction.py
    seed 20260630; AUROCs reproduce Z exactly (gate 0.997-0.998, dial 0.818-0.861).
    Direction artifacts gitignored by design; fit metadata recorded in the amendment
    doc.
- id: 002-decision
  at: '2026-07-01T22:10:00Z'
  kind: decision
  title: Amendment AA pre-registration drafted, then SIGNED; Stage-1 approved
  summary: 'Drafted experiments/causal-confidence-steering/AMENDMENT.md (Tier-2):
    2 arms x 2 signals x 2 positions on a unified initial-pass + revision-pass protocol
    so anchor/early vs end/late cells share the same final-output metrics. Stage 1
    pilots Qwen3.5-4B only (native thinking, needed for Arm B); Stage 2 cross-family
    bar (>=2/3) pre-stated. Gates locked: AA-G1 gate@anchor +15pt abstention with
    <=5pt known-accuracy drop; AA-G2 Arm-B real-vs-placebo +10pt; AA-G3/G4 dial revision-discrimination
    +10pt; AA-G5 PRIMARY position-asymmetry contrast (CI excludes 0 in >=3/4 passing
    combos); coherence floor degenerate-rate <=5%. Falsifiers: channel-stays-shut
    / position-does-not-matter / no-coherent-operating-point. USER SIGNED and approved
    Stage-1 launch (cells AA-1..AA-8, Qwen3.5-4B, local Docker GPU lane) in-session
    2026-07-01.'
- id: 003-infrastructure
  at: '2026-07-01T23:20:00Z'
  kind: infrastructure
  title: Run harnesses built (delegated), merged; 181/181 CPU tests
  summary: run_arm_a.py / run_arm_b.py / steering_common.py built by a delegated worktree
    agent against the amendment as spec (pool loading from the frozen SelfAware rows
    + PopQA/TriviaQA, Amendment-Z grading, degenerate detection, paired 2000-resample
    bootstrap, position-gated hook control, internal paired real/placebo for Arm B).
    Merged into the amendment branch; 181/181 tests pass in the main tree. Host-side
    CPU dry-runs caught two launch-blocking issues BEFORE GPU time - (1) harness --datasets-root
    default resolves to experiment/datasets, not repo-root datasets/ (dial pool build
    would crash); (2) decode defaulted to temp 1.0/top_p 1.0 where the amendment cites
    the SR convention (0.7/0.9). Both pinned explicitly in the queue script.
- id: 004-recovery
  at: '2026-07-02T00:00:00Z'
  kind: recovery
  title: Launch, 9P PermissionError abort, --user 0:0 fix, relaunch; smokes GREEN
  summary: 'amendment_aa_queue.sh launched (smoke -> AA-1/AA-3 sweeps -> mechanical
    alpha* selection per the locked rule, with a pre-stated descriptive-only fallback
    -> AA-2/AA-4 off-position -> AA-5..AA-8). First launch aborted at the very END
    of the Arm A smoke - the known 9P mount issue (container default user cannot write
    host-created results/; the GPU path itself worked, hook registered at L14, all
    144 smoke generations completed). Fixed with --user 0:0 on the docker run (the
    recorded fix), relaunched. Both smokes GREEN on relaunch: structurally clean JSONs,
    paired real/placebo contrasts, zero degenerate outputs. Smoke abstention on unknowns
    is 0.0 at alpha +/-2 (n=12) - consistent with the raw base''s answer-everything
    prior (Z: 2999/3000); the registered question lives at the full sweep (+/-4, n=300).
    AA-1 (8400 generations) in flight at close of this checkpoint.'
- id: 005-result
  at: '2026-07-02T14:45:00Z'
  kind: result
  title: AA-5 (Arm B gate@early, real+placebo) FLAT; first-person phrasing follow-up
    drafted as a Tier-2-gated proposal
  summary: 'First text-channel cell lands where all four Arm A activation cells did:
    abstention_unknown delta +0.0033 (CI [0.0, 0.010] includes 0), answer_rate_known
    1.000 in both conditions, health checks pass (degenerate ~0, coherence floor OK,
    gate adequacy 299 >= 100). Now 5/5 flat across two intervention modalities. Caveat:
    abstention near-floor in BOTH conditions on the gate pool, so detection room for
    suppression was limited; dial cells (AA-7/8) carry the headroom. Named confound
    raised by the user: the registered note is OOD telemetry ("[internal: gate 0.87
    - confident - known]"), not first-person reasoning. Drafted docs/plans/aa-followup-first-person-injection.md
    - variants V1 (full first-person + percent + commitment clause) / V2 (commitment
    only) / V3 (voice only), same harness and score-permutation placebo, prediction
    + falsifier + health gates pre-stated. Instrument ruling CORRECTED after checking
    AMENDMENT-AA authorized knobs (alpha grid + eval-subset sizes ONLY - the note
    template is not one): the phrasing variant carries a distinct mechanistic rationale
    and adds evidence cells, so it requires a NEW signed Tier-2 amendment before running,
    not tier-3 tuning under AA. AA-6 (gate@late) auto-started from the queue.'
notes:
- 'Depth-profile side finding (descriptive, from Z surfaces, user question): the gate
  is a saturated 0.997+ PLATEAU spanning ~80% of depth in ALL four families (onset
  by ~20% depth), so per-family "best gate layer" differences are argmax jitter; the
  dial is a genuinely LOCALIZED mid-to-late band (~40-80% depth, overlapping across
  families). Llama dial argmax L25/28 sits near the unembedding - if Stage 2 runs,
  pre-state a plateau-center steering variant for Llama rather than deciding mid-run.
  Candidate descriptive figure for Paper 4.'
- 'Queue mechanics: alpha* = smallest |alpha| passing effect gate + coherence floor
  vs alpha=0, ties to larger effect; if none qualifies the off-position cell still
  runs at the max-effect coherent alpha labeled ALPHA_STAR_FALLBACK, descriptive only
  (AA-G5 only gates combos whose effect gate passed) - fallback pre-stated in the
  script before any result existed.'
- 'Paper 3 absorption (parallel workstream): old regimen-paper section 7-8 depth folded
  into papers/paper-3-knows-but-doesnt-say/manuscript.md on branch paper3-absorb-confidence-depth
  (b5c9cbca, stacked on paper-line-restructure); PR follows the #142 merge. Number
  fix: GRPO-v2 appropriateness AUROC 0.520 (full eval, n=3369) replaces the behavior-subset
  0.561 (n=1233, 15 wrong).'
- 'Mid-run diagnostics on the flat AA-1/AA-3 Arm A sweeps (2026-07-02): (a) the perturbation
  is NOT small in amplitude - Qwen3.5-4B L14 residual norm is ~7.8 (sd 0.1, n=60 frozen
  pre-anchor states), so effective alpha ~2 is a ~27% perturbation and unscaled alpha
  4 would be ~51%; (b) the anchor-mode hook fires ONCE (prefill, last prompt token,
  one layer) while all 128 decode steps run unsteered, so the anchor cells test a
  one-token nudge - the end cells (gen_stream) steer every decode token, meaning anchor-vs-end
  differ in BOTH position and intervention surface (confound to name in section 7);
  (c) the uncertainty-proportional rule alpha*(1-probe) costs ~2x on unknowns (probe
  reads them 0.36-0.59); (d) AA-3 sign-agnostic tiny lifts (+0.011..+0.029 at BOTH
  alpha signs, none CI-excluding 0) read as perturbation noise, and the control revision-discrimination
  is ~0.008 - the unsteered revision pass has no discrimination to amplify.'
- 'Doubt-vs-caution reframe (user insight, 2026-07-02): the probes read the DOUBT/evidence
  axes; abstention is governed by the CAUTION/action gate, and Paper 2 line already
  showed these are separable (whitened cosine -0.565, caution_perp held-out AUROC
  0.825 after doubt projected out) with caution causally load-bearing (refined B1:
  ablate caution_perp -> refusal 0.994->0.524). AA Arm A flatness on a raw base (gate
  engaged ~1/3000) is the two-axis prediction: evidence variable steered, decision
  variable never consulted. FALSIFIER-1, if it lands, reads "doubt axis is not the
  action lever", not "steering does not work".'
- 'Cloud lane bring-up GREEN + Amendment Y SIGNED (2026-07-02): HF Jobs plumbing smoke
  (job 6a463f46fb6818a83db30027, Qwen3.5-0.8B-Base, 300 gate rows + 150 answerable,
  a10g-small, ~25 min) ran the full clone-at-pinned- commit -> extract -> score ->
  upload path end to end; result + manifest landed in professorsynapse/epistemic-humility-cloud-results.
  Infra on branch cloud-lane-y-smoke (22960dbf): in-job wrapper, uploader, launcher
  (huggingface_hub Jobs API; the hf CLI is typer-broken locally), and git-tracked
  distilled gate-row pools (full 1233-row frozen SelfAware set + 300-row smoke subset,
  provenance JSON). Lab-notebook instrument only. Anecdotal smoke readout (NOT Y evidence:
  off-list model, bounded rows, chat-template surface): gate 0.989 on a raw 0.8B BASE
  model, dial 0.70, veto 0.46 on n=21 correct. Amendment Y then SIGNED in-session
  with defaults (4 pairs, 3/4 bars, >=50/>=50 floors, dual-render sub-cell in, cloud-primary
  lane); paper fit = fold into program papers, and the regimen-paper section-8 pretraining-origin
  claim is downgraded to an OPEN QUESTION pre-result (user-directed). The Y draft
  + paper edit are uncommitted in the working tree ON PURPOSE: they ride the Y registration
  branch off main after the AA PR merges. Launch approval for Y cells NOT yet given.'
- "AA-2 (gate@end, fallback alpha -2.0, descriptive-only): FLAT like AA-1 \u2014 abstention_unknown\
  \ 0.0 vs control 0.0033 (delta -0.0033, CI includes 0), answer_rate_known 1.0, zero\
  \ degenerate, adequacy OK (299 unknowns answered under control). Steering EVERY\
  \ decode token still does not make the raw base abstain, so Arm A flatness is not\
  \ explained by the anchor cells' one-token surface alone \u2014 consistent with\
  \ the doubt-vs-caution two-axis reading (evidence axis written, action gate never\
  \ consulted)."
- 'Follow-up directions queued behind the AA verdict + PR (user-proposed 2026-07-02,
  none registered yet): (1) rerun AA cell structure on the TRAINED abstainer checkpoints
  (clean-SFT, SFT->GRPO-v2) where the caution gate is live (GRPO-v2 refuses ~82% forced-best-guess)
  - directions refit per checkpoint per Amendment T; cheapest and most diagnostic,
  decides whether training installs the doubt->caution wire. (2) probe-as-reward training:
  couple the ACTION policy to the frozen probe readout via RL (reward abstain when
  probe-doubt high / answer when low) - distinct from the falsified M/R channels which
  coupled REPORTING to the internal state; design downstream of (1). (3) think-end
  position cell: read/steer at the last thinking token - post-formation signal (S/T:
  post beats pre) available BEFORE any visible token, dissolving the read-late/act-early
  dilemma; plus thinking-tuning (train the model to self-emit the AA Arm B injection
  note) if Arm B moves behavior.'
- "HF publication wave 2 executed (2026-07-02, user-approved): cloud-results card\
  \ published (rev af730952), eh-probe-directions (rev 033ae541; AA gate/ dial fits,\
  \ 4 families) and eh-readout-rows (rev 808dd123; 31 folders, 79,015 rows \u2014\
  \ S/T/U/W/X/Z/SR/P surfaces + frozen probe pools, NO hidden states, no Cheng/OpenMOSS\
  \ content) now live. Manifest+README updated on branch hf-publication-wave2 (fd06cc90,\
  \ 5931e55b). Note: the auto-mode classifier correctly blocked the first bulk-upload\
  \ attempt pending explicit user content review \u2014 publishing curated private-repo\
  \ data needs the user to see the exact contents, not a general go-ahead."
- 'Amendment Y fleet interim (5/10 cells landed, 0 failures, all PASS): pretrain-only
  bases olmo-3-7b (gate 0.9975/dial 0.844/veto 0.803/ctl 0.791) and llama-3.2-3b (0.9972/0.824/0.835/0.771)
  both PASS -> Arm A 2/4 toward the >=3/4 bar. Era ladder: gpt2-xl 2019 (0.991/0.794/0.794)
  and pythia-2.8b 2023 (0.993/0.821/0.751) formally PASS but their within-SelfAware
  control is ~0.59 (near chance) vs ~0.77-0.80 on 2024+ bases. EMERGING READING: gate/
  dial are era-invariant back to GPT-2; what improves with era is the WITHIN- DISTRIBUTION
  veto (control column), i.e. old models fake the veto with dataset cues. Qwen chat-render
  sub-cell: 0.9977/0.851/0.867/0.796.'
- 'Text-only baseline control (committed cceaaf76 on the Y branch, amendment_y_text_baseline.py
  + result JSON): TF-IDF+LR on question surface alone reads gate 0.964 (frozen SelfAware
  pool) and dial 0.75-0.78 (Z rows per family). REFRAME: much of the absolute gate
  AUROC is benchmark surface (SelfAware unknowns are lexically distinctive); the model
  signal is the MARGIN above the text ceiling (error mass 3.6% -> 0.2% on modern bases,
  and the margin itself grows with era: gpt2 0.991 < pythia 0.993 < modern ~0.998)
  plus the S/T pre-vs-post gap which surface cannot produce. Softens "era-invariant
  readout" into "era-invariant surface component + era-growing hidden-state margin
  and within-dist veto".'
- 'Cloud-lane artifact gap found+fixed (e2fa5c04 on Y branch): the Y fleet uploads
  only result+manifest and DISCARDS rows.jsonl (~1.4 MB), which blocks per-cell text
  baselines and grading audits. hf_jobs_cell.sh now ships rows.jsonl; skill reference
  cloud-lane.md gained the probe-cell lane section (artifact-completeness contract,
  extractor-DONE vs job-RUNNING status semantics, timeout-as-cost-ceiling).'
legacy_session:
  id: '0032'
  path: docs/sessions/0032 - amendment-aa-causal-confidence-steering-launch.md
---
# Session 0032 — Amendment AA: causal confidence steering (Paper 5)

Arc: steering review -> direction fits -> Tier-2 pre-registration -> user
signature + Stage-1 launch approval -> harness build (delegated) -> queue launch
-> 9P permission recovery -> smokes green -> AA-1 sweep in flight.

See checkpoints in frontmatter. Amendment:
`experiments/causal-confidence-steering/AMENDMENT.md`. Queue:
`experiment/phase1/probe/steering/amendment_aa_queue.sh`. Progress log:
`experiment/phase1/probe/steering/aa_logs/PROGRESS.log`.
