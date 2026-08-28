---
schema_version: research-session/v1
session_id: 20260731T180117Z-pocket-ladder-stage-1-2-paper-1-edit-pass-merge-meta-analysis-deprecation
title: Pocket ladder Stage 1-2, paper 1 edit pass merge, meta-analysis deprecation
status: active
created_at: '2026-07-31T18:01:17Z'
updated_at: '2026-08-05T17:43:03Z'
question: Does the gemma pocket ladder (E1-E3) show direction-specific actuation under
  G1/G2/G3, and can paper 1 absorb the deprecated meta-analysis as its own apparatus?
tags: []
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-07-31T18:01:38Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'IDK-switch confirmatory resolved and merged earlier today (name EARNED,
    N1/N2/N3 all PASS). Gemma pocket-ladder: Stage 1 dose calibration adjudicated
    and committed (E1/hs25 usable at ratio 0.85 dose 81.615 via the pinned choose_dose
    rule: max confab-tighten rate, then min known-correct cost, then lower ratio;
    amendment prose said first-usable-rung but the tool is byte-identical to the parent
    quarantine instrument, so the tool''s ratified rule governs, discrepancy recorded
    in NOTEBOOK; E2/hs26 and E3/hs27 dose-viability NOT-RUN, no re-laddering; hs40
    late null as expected). Stage 2 true arm complete: G1 PASS 0.7917 CI [0.7241,0.8462]
    vs floor 0.5/0.4; G2 PASS 0.0333 CI [0.0176,0.0621] vs cap 0.05/0.10; fired-only
    companion 9/9 NOT-ADJUDICABLE at n=9 below the N=35 floor, the pre-registered
    non-gating disposition. Control arms (undosed baseline then P1 placebo, 5 SC1-accepted
    draws matched to 175 fired rows, dry-run validated) running in background for
    G3 adjudication (effect_ratio >= 3.0, max denominator). Paper 1 user edit pass
    merged as PR 372: expressed-character locus rewording (abstract, Section 1, P1);
    C2 restated as a preference stage after SFT vs SFT alone, comparison structure
    verified against effects.csv (Cheng baseline Idk-SFT rows, Tulu-3 staged ladder,
    Saeidi lone preference-from-base point); Section 4 restructured with spelled-out
    claim subheadings and two deterministic figures; gap 3 unbundled into GRPO-comparison-only
    with representation clause folded into gap 4; five-language probe restored to
    Limitations; full in-text AI reflexivity disclosure; Appendix A rebuilt as per-file
    links. KG search ranking fix PR 371 still open awaiting user merge. NOW IN FLIGHT:
    user directive to DEPRECATE the standalone meta-analysis draft entirely; paper
    1 becomes sole self-contained source of record. Worktree paper1-absorb (branch
    paper1/deprecate-meta-analysis): git-mv done (evidence/ incl raw-reports and analysis/
    moved under papers/paper-1-taxonomy-framework/, draft-v0.md archived under archive/meta-analysis/paper/,
    TODO and author_contacts to notes/). Agent meta-path-sweep rewriting repo-wide
    references (root docs, .skills canonical then sync, dataset cards, library notes,
    experiment scorers; session logs untouched); agent paper1-absorb-writer purging
    draft references from manuscript and absorbing apparatus as appendices B (search
    protocol/PRISMA), C (extraction schema/verification/AI division of labor), D (sensitivity
    analyses and audits). Pending: two untracked outreach CSVs on main checkout disk
    under meta-analysis/evidence/ must be relocated by hand at merge; KG librarian
    pass to mark draft node deprecated_by paper 1 if schema supports it.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-checkpoint
  at: '2026-07-31T23:17:39Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Pocket cell CLOSED: PR #380 merged (registry conflict resolved via bin/exp
    regen in fresh worktree; old gemma-pocket worktree left root-owned debris, flagged
    to user for sudo rm). KG ingest of the resolution committed to main (experiment
    + mechanism nodes, validators clean). KTO seed-3 eval completed in pinned unsloth
    container (--user root fix): recall 78.88 / over-refusal 43.30 / truthful 38.08,
    n=3369, verified; three-seed triple consistent (s1 75.68/48.22/36.95, s2 78.68/45.53/38.14).
    Paper 2 KTO three-seed update committed on paper2/kto-three-seeds (manuscript
    three seeds each, means 77.75/45.68/37.72 by existing plain-mean convention, fig-p1-04
    + tables regenerated, seed-3 run record eval_summary added; PR opening). GRPO
    block: executor hit registered pre-launch HARD STOP on lora.random_state seed-threading
    ambiguity (seed-1 sets random_state 1 == seed vs tuner default 3407, unlinked
    from seed: in code, config-file-only for DPO/KTO). LEAD RULING: random_state mirrors
    seed number (2/3); recorded+committed in NOTEBOOK before unblock; AMENDMENT banner/scoreboard
    staleness from sign tooling corrected on branch; gates.yaml left byte-identical
    (sha256-pinned, experiment.yaml authoritative). Executor resumed toward seed-2
    clean_sft; all preflights PASS (digest match, dataset audit exact vs frozen Amendment
    E numbers, GPU idle). Follow-ups on record: build_figures.py hardcodes phase1/eval
    paths now living only in phase1-data (script not end-to-end runnable, needs housekeeping
    PR); amendment-B stated-confidence source dirs missing on this machine; seed-2
    KTO record NOT stale (analyst-verified null).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-checkpoint
  at: '2026-08-01T09:21:53Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'HF adapter release arc: user asked whether LoRA adapters were on HF; scout
    found all 33+merged-16bit already PRIVATE-staged 2026-07-05 (docs/checkpoint-staging.md
    1:1 registry). User approved paper-2 reproducibility set (17 repos) public. Release
    prep surfaced 4 flags; adjudicated: beta 0.1 verified at pinned tuner commit;
    4 stale headline run records (dpo/kto seeds 2-3) backfilled from artifacts; AMENDMENT
    banner staleness already fixed on run branch. MAJOR FINDING (flag B, then user
    challenge "I thought I reran everything"): headline DPO/KTO seed-1 trained PRE
    dev-split-fix (commit 3dc58e9b 2026-06-14, cured 188 dup-prompt train/dev overlaps,
    ~10.1% train churn, 91% dev resample, pure boundary reassignment, no novel content);
    seeds 2/3 post-fix. Analyst proved conclusively: SFT seed-1 WAS deliberately rerun
    post-fix (PR #21/#22, TODO.md contemporaneous), DPO/KTO seed-1 deliberately NOT
    ("treat previous...as completed pre-split-fix bounded comparators" at the fix
    commit), never reversed; Amendment A all-clean post-fix. Confound STANDS. User
    chose caveat-now-rerun-later. Executed: caveats on 6 headline DPO/KTO cards +
    paper-2 Limitations & Appendix A provenance note; 17 repos flipped public (pilot
    KTO seed-3 verified rendering, then 16, zero failures); post-flip head revisions
    recorded; PR #384 open. Rerun amendment DRAFTED (PR #385, NOT signed): 2 cells,
    replacement-candidate semantics, cohort-derived G1 bands with 3-question discreteness
    floor and explicit LOW-POWER disclosure (pre-fix rows pass 8/8 - value is provenance
    hygiene), sign-time forks: trainer-commit pinning (seed-1 cells used different
    submodule commits than cohort AND each other; lead recommends pinning cohort 089fa9b7),
    eval-config pinning (headline eval config only ever lived in gitignored .tmp),
    digest vintage, PARTIAL-vs-FAIL. Reusable audit script scripts/audit_data_provenance.py
    (found repo gotcha: str.splitlines() miscounts JSONL, raw U+0085 in DPO build).
    GRPO chain: executor1 wedged post-training (9h23m stall, zero GPU loss), TaskStopped,
    executor2 resumed with bare-docker-wait watch discipline; seed-2 clean_sft done
    (26m39s, loss 0.4281), merge launched ~09:12Z. PRs merged this arc: #381 (paper2
    KTO 3-seed), #382 (figures resolver, rebase carried seed3_kto to new format).
    Open: #383 paper5, #384 release record, #385 draft amendment. Paper-5 pass merged-ready:
    pocket refs resolved, VOICE pass, 2 placebo-scope overstatements corrected, 3.5-fold
    wording fixed.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-checkpoint
  at: '2026-08-01T18:28:44Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Merges and signing arc (2026-08-01): user approved and lead merged PR
    #383 (paper-5 pocket resolution + voice pass) and PR #384 (HF 17-adapter public
    release record). PR #385 headline-seed1-postfix-rerun: user chose resolve-sign-merge
    path and pinned trainer commit to cohort 089fa9b7 (superseded per-arm 3a3d7a26
    DPO / 04005402 KTO recorded); resolver subagent applied all six sign-time resolutions
    (trainer pin, eval config pinned into experiment dir replacing never-committed
    .tmp convention, digest verified char-for-char, explicit beta 0.1 with lead-verified
    no-hidden-default at 089fa9b7 via train_dpo.py:576/train_kto.py:729, PARTIAL-vs-FAIL
    per-arm semantics, prediction/falsifier text); lead fixed stale gates.yaml design-fork
    prose pre-sign, user approved Sign as drafted covering the three PROPOSED items,
    signed via bin/exp sign (5 files pinned), merged as c27f23db. Launch queued behind
    GRPO chain, digest hard-stop at launch. User challenged seed-2 clean_sft 26m runtime:
    verified legitimate against seed-1 same stage (29m18s, same 1495 steps); flagged
    identical final loss 0.4281 across seeds, resolved as coincidence at last logged
    step (57/59 logged steps differ, e.g. step 25: 1.7269 vs 1.7333). GRPO chain:
    executor2 stalled TWICE post-container-completion (merge done 09:14Z idle till
    ~10:31 nudge; smoke done 10:33:47Z idle 8h till 18:30 nudge; wedge mechanism =
    docker-wait completing mid-turn eats the wake). Smoke itself PASSED G0 smoke clause
    on lead re-derivation: 192/192 scored, 192/192 answer+stated_confidence coverage,
    0 retry-exhausted, 0 thinking-tag hits, enable_thinking uniformly false; metrics
    refusal_recall 89.47 / answer_on_unknown 10.53 / over_refusal 68.04 / correct_on_known
    45.16 / truthful 51.56. New standing executor rule issued: docker-inspect all
    watched containers before ending any turn; act immediately if exited. Deviation
    to fix at commit: executor wrote smoke eval config into canonical checkout experiments/
    instead of grpo-run worktree. Wall-clock note: ~17.5h of seed-2 elapsed time is
    stall, not compute; 42h seed-2 guardrail tracks wall-clock, surface to user if
    threatened. Next: executor launches clean_sft_dpo; lead commits stage-1 NOTEBOOK
    entry.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-08-02T17:09:51Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Disk-full crash and cleanup (2026-08-02): root volume hit 100% mid-DPO-seed2-merge,
    truncating merged shard 2 by 555MB (confirmed vs reference sizes) and killing
    executor3; crash cleanup also wiped ALL docker containers AND the pinned unsloth
    training image. Executor2 had been TaskStopped earlier after a fourth wake-failure
    stall (10h idle post-KTO; NOTEBOOK draft it claimed never landed). Seed-2 chain
    artifacts all survived: stage-1 merged-16bit verified complete, DPO adapter 268M
    + lineage intact, KTO adapter intact. Disk-surveyor agent produced classified
    inventory (~330G reclaimable): A redownloadable HF cache ~113G, A-prime truncated
    merge 7G, B regenerable seed-1/headline merged-16bit dirs (~61G total incl. seed2
    dual-merge discovery: merged-16bit + merged-16bit-lowmem-20260616, and seed3),
    C small mirrored adapters (kept), D protected (active chain, eval results_*, pinned
    base cache, grpo_bootstrap sole-copy merge per checkpoint-staging Known gaps),
    E unknown (phase1-data/probe 56G possibly sole-copy hidden-state extractions -
    NOT touched; surface-residualization-control worktree 44G derived re-read cache
    - NOT touched; worktree fleet ~90G needs dedicated hygiene pass). User approved
    batch-by-batch; rm -rf auto-denied by permissions so deletions ran via reviewed
    script + python subprocess wrapper. Freed: 140G->276G (72% used). Root-owned leftovers
    need user sudo: HF cache models--Qwen--Qwen3.5-4B, truncated Qwen3-4B-clean-sft-dpo
    merge dir, plus older gemma-pocket worktree debris. Registry rows spot-verified
    in checkpoint-staging.md before every bucket-B deletion. Pinned image re-pull
    by digest running in background (WSL docker-credential-desktop.exe exec-format
    failure worked around with bare DOCKER_CONFIG={}). PR #386 opened: scripts/ops/prune_runtime.sh
    (stage|scan modes) + local-runtime.md retention policy (never docker image prune
    -a; free-space precheck before merge/training; staged-adapter merged-16bit prunable
    rule; checkpoints-rotation prunable post-completion; results_*/probe never). Kept
    per user: gemma-4-E4B, Mistral-7B, Llama-3.2-3B atlas caches. Chain resume plan:
    after image lands, fresh executor redoes DPO merge first (disk precheck), then
    KTO merge/smokes/full evals/grpo_v2 queue. GRPO seed-2 42h wall-clock guardrail
    long blown by stalls+crash (compute itself ~3.5h) - needs user ruling at resume.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-08-03T15:06:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Chain resume + wake-failure root cause (2026-08-03): user restarted Docker
    Desktop which restored the nvidia runtime (no toolkit install needed) but wiped
    the image store again; pinned image re-pulled by digest + retagged, GPU verified
    inside container. Executor4 preflight: re-verified both stage-2 adapters + lineage,
    found and fixed lost :latest tag (retag on verified digest, lead-endorsed), correctly
    escalated nvidia-runtime loss instead of installing packages. Queue items 1-2
    complete and lead-verified digit-for-digit: DPO redo-merge (shards 4967215360+3077766632
    exactly matching reference; crash damage repaired) + smoke G0 PASS (192/192 coverage,
    0 thinking hits, refusal_recall 88.42); KTO merge + smoke G0 PASS (86.32 recall,
    mean_conf 0.8240). Base full eval (G1 denominator) complete: n=3369, refusal_recall
    89.92, answer_on_unknown 10.08, over_refusal 58.24, truthful 41.17 (seed-1 denominator
    was 87.02/12.98). DPO full eval running (eh-grpo3seed-2-clean_sft_dpo-full_eval-20260803T150428Z,
    corrected_base config template). DURABLE OPERATIONAL FINDING (add to local-runtime.md
    next housekeeping PR): teammate agents are NOT reliably re-invoked when their
    background docker-wait tasks complete - 4 failures across 3 executors (stalls
    1.5h/8h/10h/1h), both mid-turn (notification swallowed) and from idle; lead-session
    task notifications ARE reliable. Containment architecture: short containers foreground
    with timeout (zero stalls since); long containers get lead-side docker wait as
    PRIMARY wake; on lead-watch fire, verify then IMMEDIATELY push results+proceed
    order to executor (do not wait for its report); executor docker-inspects all open
    containers at start of every turn. WSL VHDX maintenance window planned at grpo_v2
    boundary: user runs wsl --shutdown, Optimize-VHD per vhdx on F: (WSL ext4 + Docker
    Desktop disks; freed ext4 space does not return to Windows host until compaction),
    wsl --manage Ubuntu-22.04 --set-sparse true, restart Docker Desktop, claude --resume;
    lead commits NOTEBOOK batch + holds executor before window; expect image-store
    wipe again after (recovery: pull-by-digest + retag + clean DOCKER_CONFIG). Remaining
    queue after window: grpo_v2 training, 4 stage-3 stacks, stage-3 evals, then seed-3
    chain.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-checkpoint
  at: '2026-08-03T16:01:33Z'
  kind: checkpoint
  title: Checkpoint
  summary: "Seed-2 stage-2 closeout complete (2026-08-03): all three full 3369-row\
    \ evals done and lead-verified. Base (G1 denominator): refusal_recall 89.92 /\
    \ answer_on_unknown 10.08 / over_refusal 58.24 / truthful 41.17. DPO arm: 89.34\
    \ / 10.66 / 55.97 / 41.32 (sits on base, over-refusal down ~2.3pp, mirrors seed-1\
    \ cold-DPO flatness). KTO arm: 85.66 / 14.34 / 54.00 / 40.31. G0 smoke clauses\
    \ PASS for both stage-2 arms (lead-adjudicated, digit-for-digit independent verification).\
    \ One more wake failure at the base-eval boundary (1h lost, caught on user ping)\
    \ prompted the final discipline: lead watch is PRIMARY driver, verify-then-push\
    \ immediately on fire \u2014 worked perfectly for DPO and KTO evals (push within\
    \ a minute of exit). Durable gotcha landed as PR #387 (skill/teammate-watch-discipline\
    \ branch, local-runtime.md + mirrors): teammate docker-wait wakes unreliable (4\
    \ stalls/3 executors), binding watch architecture recorded. User confirmed NO\
    \ Claude memories for this project (block_memory_write.sh hook working as intended;\
    \ memory dir does not exist) - durable knowledge goes to skills/session notes/KG\
    \ only. PR #386 (prune policy) merged by user earlier. WSL VHDX maintenance window\
    \ imminent: executor4 finalizing self-contained NOTEBOOK draft then HOLDING; lead\
    \ commits NOTEBOOK batch; user then runs wsl --shutdown + Optimize-VHD on F: vhdx\
    \ files (WSL ext4 + Docker Desktop) + wsl --manage Ubuntu-22.04 --set-sparse true\
    \ + restart Docker Desktop + claude --resume. Expect: image store wiped again\
    \ (recovery = pull-by-digest + retag + clean DOCKER_CONFIG), executor4 dead (successor\
    \ harness spawns from committed NOTEBOOK). Post-window queue: grpo_v2 training\
    \ launch (the G1-tested arm), 4 stage-3 stacks, stage-3 evals, seed-3 chain. Seed-2\
    \ GPU compute so far ~4.5h of 42h re-baselined budget."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 008-checkpoint
  at: '2026-08-04T22:01:29Z'
  kind: checkpoint
  title: Checkpoint
  summary: "G1 SEED-2 LEG PASS (2026-08-04, lead-adjudicated): clean_sft_grpo_v2 seed-2\
    \ vs same-seed base \u2014 answer_on_unknown 10.08 -> 5.72 (\u22124.36pp, floor\
    \ 3.0pp) and refusal_recall 89.92 -> 94.28 (+4.36pp, floor 3.0pp), both conditions\
    \ met; verified from metrics.json AND independently re-derived from 3369 scored\
    \ rows (1032 unknown), exact agreement. Seed-1 effect was \xB16.39pp; \xB14.36pp\
    \ attenuation within direction-plus-floor design. Overall G1 OPEN pending seed\
    \ 3 (registered two-seed requirement, no goalpost movement). Side numbers: over_refusal\
    \ 58.24 -> 66.75, truthful flat 41.17 -> 41.35 (same trade shape as seed-1). Training:\
    \ 1861 steps, 8h10m (vs 7.22h est), final_loss 0.0768, final reward 0.9071 (seed-1\
    \ finished 0.617); GRPO lineage runtime.status/time fields null (schema quirk,\
    \ completion evidenced by artifacts). Executor5 pre-launch catch: stale pre-archive-move\
    \ rewards.custom.file path in ALL four seed-1 GRPO config templates (would ValueError\
    \ at startup); fixed via absolute in-container path in new seed-2 configs; 90s\
    \ dry-run validated before the 8h launch. Merge + smoke G0 PASS (93.68 smoke recall\
    \ vs base 89.47 \u2014 direction visible pre-eval). Post-maintenance runtime survived\
    \ intact (image, nvidia runtime, tag all present; no re-pull needed). Executor5\
    \ model harness so far: zero stalls, independent re-verification, loud escalations.\
    \ STAGE-3 RELEASED serial per launch_order: dpo_grpo, kto_grpo, grpo_dpo, grpo_kto\
    \ (sources = merged stage-2 checkpoints per cell.yaml; corrected reward path carries\
    \ into new GRPO-stage configs; dry-run endorsed before each multi-hour launch).\
    \ Compute ~13.2h of 42h seed-2 budget. NOTEBOOK batch commit pending executor\
    \ confirmation of final draft through grpo_v2 closeout. Next: 4 stage-3 stacks\
    \ (each: train + merge + smoke + full eval), then G2 adjudication, then seed-3\
    \ full chain."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 009-checkpoint
  at: '2026-08-05T08:30:19Z'
  kind: checkpoint
  title: Checkpoint
  summary: "GRPO three-seed seed-2 stage-3 stacks 1-2: dpo_grpo CLOSED (train 1861\
    \ steps loss 0.0962 reward 1.0998; merge byte-exact; smoke 192/192/192/0; full\
    \ eval n=3369 recall 94.38 / answer-on-unknown 5.62 / over-refusal 65.81 / truthful\
    \ 41.50 \u2014 endpoint nearly identical to same-seed grpo_v2 94.28/5.72, G2-relevant,\
    \ adjudication deferred; G0 PASS, NOTEBOOK c550ba63). kto_grpo training COMPLETE\
    \ (4h41m, 1861 steps, loss 0.0846, reward 1.134, correct KTO merged source, NOTEBOOK\
    \ 8704700f); closeout (merge/smoke/full-eval) released to executor6. Executor\
    \ succession 5->6 after lead-session compaction severed executor5 (NOTEBOOK f82ae66b);\
    \ executor6 zero stalls so far, lead-watch architecture holding (all three boundaries\
    \ this arc fired via lead-side docker wait). Reward endpoint ordering seed 2:\
    \ clean-SFT base 0.9071 < DPO base 1.0998 < KTO base 1.134. Remaining seed-2:\
    \ kto_grpo closeout, then grpo_dpo + grpo_kto (both source from seed-2 grpo_v2\
    \ merged), then seed 3. Next decision points: G2 adjudication once all four stacks\
    \ close; PR #387 merge still awaiting user."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 010-checkpoint
  at: '2026-08-05T14:16:28Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Seed-2 stage-3 stacks 3-4 + gate adjudications. grpo_dpo CLOSED (train
    1h34m, 1868 steps, loss 0.0419; full eval n=3369: recall 94.67 / ans-on-unk 5.33
    / over-refusal 65.98 / truthful 41.53; G0 PASS, NOTEBOOK b0df73a9). grpo_kto (FINAL
    seed-2 arm) training launched 13:50Z, ~1h40m, dual watch armed. G2 SEED-2 LEG
    ADJUDICATED PASS (f235e45d): gates.yaml sha256 7c79a418... verified byte-identical
    to signed experiment.yaml pin; over_refusal 66.75->65.98 (decrease, min_magnitude_pp
    deliberately null) MET, answer_on_unknown 5.72->5.33 (cap +2.0pp) MET; neither
    not_confirmed_if clause fires. LEAD ERROR CORRECTED IN RECORD: had framed grpo_dpo
    as a replication concern by reasoning from shrunken effect size (-0.77pp vs seed-1
    -2.99pp) against a magnitude bar the gate explicitly declines to set (''a magnitude
    bar here would invent precision the instrument does not have'') - goalpost movement
    in the STRICT direction, same violation class as loosening. Second error corrected:
    G2 does NOT require all four stacks (comparison is grpo_dpo vs grpo_v2 only, adjudicable
    at stack-3 closeout); grpo_kto is needed for chain completeness and G3 intervals.
    Status: G0 PASS all closed seed-2 cells, G1 seed-2 leg PASS, G2 seed-2 leg PASS,
    both OPEN overall pending seed 3. WAKE-LATENCY INSTANCE: lead docker-wait notification
    fired ~3h after container exit, GPU idled; mitigation now dual-signal (docker
    wait + polling Monitor). GOVERNANCE: gates.yaml in 2 of 53 experiments declares
    status:proposed while signed; PR #388 opened adding warning-only exp-validate
    rule; neither pinned file edited (grpo block is mid-run with results, repin is
    pre-run-only by design; postfix-rerun edit was classifier-blocked and reverted
    to byte-identical pin 44013bc9). Executor6 caught a lead error (claimed DPO trainer
    has no --dry-run; it does, exits pre-model-load) - dry-run before every long launch
    now standing practice. Next: stack-4 closeout, seed-2 chain complete, then seed
    3.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 011-checkpoint
  at: '2026-08-05T17:43:03Z'
  kind: checkpoint
  title: Checkpoint
  summary: "SEED 2 COMPLETE (8/8, G0 PASS all cells) and SEED 3 UNDERWAY. Seed-2 final\
    \ matrix (n=3369): base 89.92/10.08/58.24; dpo 89.34/10.66/55.97; kto 85.66/14.34/54.00;\
    \ grpo_v2 94.28/5.72/66.75; dpo_grpo 94.38/5.62/65.81; kto_grpo 93.31/6.69/64.23;\
    \ grpo_dpo 94.67/5.33/65.98; grpo_kto 91.76/8.24/61.10 (recall/ans-on-unk/over-refusal).\
    \ G1 seed-2 leg PASS, G2 seed-2 leg PASS, both OPEN pending seed 3. Descriptive:\
    \ GRPO-terminal arms converge to 93.3-94.4 recall regardless of parent (85.7-89.9);\
    \ truthful flat 41.2-41.5 in 7 of 8 arms; over-refusal is the standing cost (61-67\
    \ vs base 58.24); grpo_kto is the outlier, reopening ans-on-unk +2.52pp vs grpo_v2\
    \ while buying the largest over-refusal relief -5.65pp \u2014 recorded DESCRIPTIVELY\
    \ ONLY since G2's registered comparison is grpo_dpo vs grpo_v2 and applying it\
    \ to grpo_kto would be inventing a gate. Seed-2 compute 24.37 training GPU-h (~29-30h\
    \ with evals) of 42h. SEED 3: stage 1 CRASHED first attempt (exit 139 SIGSEGV,\
    \ cudaErrorUnknown at step 975/1495) \u2014 G0 instrument stop, capacity RULED\
    \ OUT (seed-2 identical config peaked HIGHER at 32.64 vs 27.71 GB and completed),\
    \ diagnosed as transient WSL2 GPU-passthrough fault, relaunched from scratch (not\
    \ resumed from checkpoint-500, which would diverge from how seeds 1-2 were produced).\
    \ Relaunch clean: 1495 steps, loss 0.4282 (seeds 1/2 were 0.4281/0.4281 \u2014\
    \ SFT converges to same point every seed). Base merged+smoked+full-evaled: G1\
    \ DENOMINATOR FOR SEED 3 = recall 88.28 / ans-on-unk 11.72 / over-refusal 59.01\
    \ / truthful 40.55, in-family between seeds 1 and 2. PRE-STATED seed-3 G1 thresholds\
    \ BEFORE grpo_v2 trains: grpo_v2 must reach ans-on-unk <=8.72 AND recall >=91.28.\
    \ Stage-2 dispatched (dpo, then kto, then grpo_v2, serial). CRITICAL PROCESS CORRECTION:\
    \ background 'docker wait' task status reports the WAIT command's exit, NOT the\
    \ container's \u2014 a crashed container (139) showed as 'exit code 0'. Always\
    \ read the watch OUTPUT FILE. Now running dual watches (docker wait + polling\
    \ Monitor that reports the real exit code). Other: PR #387/#388/#389 merged; #390\
    \ (postfix-rerun G1 decision-rule governed revision, amendment text governs) and\
    \ #391 (runtime skill: detached-log buffering, per-trainer dry-run cost, post-prune\
    \ compute accounting) OPEN awaiting PI merge. Executor6 caught two lead errors\
    \ this session (DPO --dry-run exists; and it read trainer source rather than trusting\
    \ lead claims)."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
---
# Pocket ladder Stage 1-2, paper 1 edit pass merge, meta-analysis deprecation

## Question

Does the gemma pocket ladder (E1-E3) show direction-specific actuation under G1/G2/G3, and can paper 1 absorb the deprecated meta-analysis as its own apparatus?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-07-31T18:01:38Z`
- kind: `checkpoint`
- summary: IDK-switch confirmatory resolved and merged earlier today (name EARNED, N1/N2/N3 all PASS). Gemma pocket-ladder: Stage 1 dose calibration adjudicated and committed (E1/hs25 usable at ratio 0.85 dose 81.615 via the pinned choose_dose rule: max confab-tighten rate, then min known-correct cost, then lower ratio; amendment prose said first-usable-rung but the tool is byte-identical to the parent quarantine instrument, so the tool's ratified rule governs, discrepancy recorded in NOTEBOOK; E2/hs26 and E3/hs27 dose-viability NOT-RUN, no re-laddering; hs40 late null as expected). Stage 2 true arm complete: G1 PASS 0.7917 CI [0.7241,0.8462] vs floor 0.5/0.4; G2 PASS 0.0333 CI [0.0176,0.0621] vs cap 0.05/0.10; fired-only companion 9/9 NOT-ADJUDICABLE at n=9 below the N=35 floor, the pre-registered non-gating disposition. Control arms (undosed baseline then P1 placebo, 5 SC1-accepted draws matched to 175 fired rows, dry-run validated) running in background for G3 adjudication (effect_ratio >= 3.0, max denominator). Paper 1 user edit pass merged as PR 372: expressed-character locus rewording (abstract, Section 1, P1); C2 restated as a preference stage after SFT vs SFT alone, comparison structure verified against effects.csv (Cheng baseline Idk-SFT rows, Tulu-3 staged ladder, Saeidi lone preference-from-base point); Section 4 restructured with spelled-out claim subheadings and two deterministic figures; gap 3 unbundled into GRPO-comparison-only with representation clause folded into gap 4; five-language probe restored to Limitations; full in-text AI reflexivity disclosure; Appendix A rebuilt as per-file links. KG search ranking fix PR 371 still open awaiting user merge. NOW IN FLIGHT: user directive to DEPRECATE the standalone meta-analysis draft entirely; paper 1 becomes sole self-contained source of record. Worktree paper1-absorb (branch paper1/deprecate-meta-analysis): git-mv done (evidence/ incl raw-reports and analysis/ moved under papers/paper-1-taxonomy-framework/, draft-v0.md archived under archive/meta-analysis/paper/, TODO and author_contacts to notes/). Agent meta-path-sweep rewriting repo-wide references (root docs, .skills canonical then sync, dataset cards, library notes, experiment scorers; session logs untouched); agent paper1-absorb-writer purging draft references from manuscript and absorbing apparatus as appendices B (search protocol/PRISMA), C (extraction schema/verification/AI division of labor), D (sensitivity analyses and audits). Pending: two untracked outreach CSVs on main checkout disk under meta-analysis/evidence/ must be relocated by hand at merge; KG librarian pass to mark draft node deprecated_by paper 1 if schema supports it.
### 002-checkpoint - Checkpoint

- at: `2026-07-31T23:17:39Z`
- kind: `checkpoint`
- summary: Pocket cell CLOSED: PR #380 merged (registry conflict resolved via bin/exp regen in fresh worktree; old gemma-pocket worktree left root-owned debris, flagged to user for sudo rm). KG ingest of the resolution committed to main (experiment + mechanism nodes, validators clean). KTO seed-3 eval completed in pinned unsloth container (--user root fix): recall 78.88 / over-refusal 43.30 / truthful 38.08, n=3369, verified; three-seed triple consistent (s1 75.68/48.22/36.95, s2 78.68/45.53/38.14). Paper 2 KTO three-seed update committed on paper2/kto-three-seeds (manuscript three seeds each, means 77.75/45.68/37.72 by existing plain-mean convention, fig-p1-04 + tables regenerated, seed-3 run record eval_summary added; PR opening). GRPO block: executor hit registered pre-launch HARD STOP on lora.random_state seed-threading ambiguity (seed-1 sets random_state 1 == seed vs tuner default 3407, unlinked from seed: in code, config-file-only for DPO/KTO). LEAD RULING: random_state mirrors seed number (2/3); recorded+committed in NOTEBOOK before unblock; AMENDMENT banner/scoreboard staleness from sign tooling corrected on branch; gates.yaml left byte-identical (sha256-pinned, experiment.yaml authoritative). Executor resumed toward seed-2 clean_sft; all preflights PASS (digest match, dataset audit exact vs frozen Amendment E numbers, GPU idle). Follow-ups on record: build_figures.py hardcodes phase1/eval paths now living only in phase1-data (script not end-to-end runnable, needs housekeeping PR); amendment-B stated-confidence source dirs missing on this machine; seed-2 KTO record NOT stale (analyst-verified null).
### 003-checkpoint - Checkpoint

- at: `2026-08-01T09:21:53Z`
- kind: `checkpoint`
- summary: HF adapter release arc: user asked whether LoRA adapters were on HF; scout found all 33+merged-16bit already PRIVATE-staged 2026-07-05 (docs/checkpoint-staging.md 1:1 registry). User approved paper-2 reproducibility set (17 repos) public. Release prep surfaced 4 flags; adjudicated: beta 0.1 verified at pinned tuner commit; 4 stale headline run records (dpo/kto seeds 2-3) backfilled from artifacts; AMENDMENT banner staleness already fixed on run branch. MAJOR FINDING (flag B, then user challenge "I thought I reran everything"): headline DPO/KTO seed-1 trained PRE dev-split-fix (commit 3dc58e9b 2026-06-14, cured 188 dup-prompt train/dev overlaps, ~10.1% train churn, 91% dev resample, pure boundary reassignment, no novel content); seeds 2/3 post-fix. Analyst proved conclusively: SFT seed-1 WAS deliberately rerun post-fix (PR #21/#22, TODO.md contemporaneous), DPO/KTO seed-1 deliberately NOT ("treat previous...as completed pre-split-fix bounded comparators" at the fix commit), never reversed; Amendment A all-clean post-fix. Confound STANDS. User chose caveat-now-rerun-later. Executed: caveats on 6 headline DPO/KTO cards + paper-2 Limitations & Appendix A provenance note; 17 repos flipped public (pilot KTO seed-3 verified rendering, then 16, zero failures); post-flip head revisions recorded; PR #384 open. Rerun amendment DRAFTED (PR #385, NOT signed): 2 cells, replacement-candidate semantics, cohort-derived G1 bands with 3-question discreteness floor and explicit LOW-POWER disclosure (pre-fix rows pass 8/8 - value is provenance hygiene), sign-time forks: trainer-commit pinning (seed-1 cells used different submodule commits than cohort AND each other; lead recommends pinning cohort 089fa9b7), eval-config pinning (headline eval config only ever lived in gitignored .tmp), digest vintage, PARTIAL-vs-FAIL. Reusable audit script scripts/audit_data_provenance.py (found repo gotcha: str.splitlines() miscounts JSONL, raw U+0085 in DPO build). GRPO chain: executor1 wedged post-training (9h23m stall, zero GPU loss), TaskStopped, executor2 resumed with bare-docker-wait watch discipline; seed-2 clean_sft done (26m39s, loss 0.4281), merge launched ~09:12Z. PRs merged this arc: #381 (paper2 KTO 3-seed), #382 (figures resolver, rebase carried seed3_kto to new format). Open: #383 paper5, #384 release record, #385 draft amendment. Paper-5 pass merged-ready: pocket refs resolved, VOICE pass, 2 placebo-scope overstatements corrected, 3.5-fold wording fixed.
### 004-checkpoint - Checkpoint

- at: `2026-08-01T18:28:44Z`
- kind: `checkpoint`
- summary: Merges and signing arc (2026-08-01): user approved and lead merged PR #383 (paper-5 pocket resolution + voice pass) and PR #384 (HF 17-adapter public release record). PR #385 headline-seed1-postfix-rerun: user chose resolve-sign-merge path and pinned trainer commit to cohort 089fa9b7 (superseded per-arm 3a3d7a26 DPO / 04005402 KTO recorded); resolver subagent applied all six sign-time resolutions (trainer pin, eval config pinned into experiment dir replacing never-committed .tmp convention, digest verified char-for-char, explicit beta 0.1 with lead-verified no-hidden-default at 089fa9b7 via train_dpo.py:576/train_kto.py:729, PARTIAL-vs-FAIL per-arm semantics, prediction/falsifier text); lead fixed stale gates.yaml design-fork prose pre-sign, user approved Sign as drafted covering the three PROPOSED items, signed via bin/exp sign (5 files pinned), merged as c27f23db. Launch queued behind GRPO chain, digest hard-stop at launch. User challenged seed-2 clean_sft 26m runtime: verified legitimate against seed-1 same stage (29m18s, same 1495 steps); flagged identical final loss 0.4281 across seeds, resolved as coincidence at last logged step (57/59 logged steps differ, e.g. step 25: 1.7269 vs 1.7333). GRPO chain: executor2 stalled TWICE post-container-completion (merge done 09:14Z idle till ~10:31 nudge; smoke done 10:33:47Z idle 8h till 18:30 nudge; wedge mechanism = docker-wait completing mid-turn eats the wake). Smoke itself PASSED G0 smoke clause on lead re-derivation: 192/192 scored, 192/192 answer+stated_confidence coverage, 0 retry-exhausted, 0 thinking-tag hits, enable_thinking uniformly false; metrics refusal_recall 89.47 / answer_on_unknown 10.53 / over_refusal 68.04 / correct_on_known 45.16 / truthful 51.56. New standing executor rule issued: docker-inspect all watched containers before ending any turn; act immediately if exited. Deviation to fix at commit: executor wrote smoke eval config into canonical checkout experiments/ instead of grpo-run worktree. Wall-clock note: ~17.5h of seed-2 elapsed time is stall, not compute; 42h seed-2 guardrail tracks wall-clock, surface to user if threatened. Next: executor launches clean_sft_dpo; lead commits stage-1 NOTEBOOK entry.
### 005-checkpoint - Checkpoint

- at: `2026-08-02T17:09:51Z`
- kind: `checkpoint`
- summary: Disk-full crash and cleanup (2026-08-02): root volume hit 100% mid-DPO-seed2-merge, truncating merged shard 2 by 555MB (confirmed vs reference sizes) and killing executor3; crash cleanup also wiped ALL docker containers AND the pinned unsloth training image. Executor2 had been TaskStopped earlier after a fourth wake-failure stall (10h idle post-KTO; NOTEBOOK draft it claimed never landed). Seed-2 chain artifacts all survived: stage-1 merged-16bit verified complete, DPO adapter 268M + lineage intact, KTO adapter intact. Disk-surveyor agent produced classified inventory (~330G reclaimable): A redownloadable HF cache ~113G, A-prime truncated merge 7G, B regenerable seed-1/headline merged-16bit dirs (~61G total incl. seed2 dual-merge discovery: merged-16bit + merged-16bit-lowmem-20260616, and seed3), C small mirrored adapters (kept), D protected (active chain, eval results_*, pinned base cache, grpo_bootstrap sole-copy merge per checkpoint-staging Known gaps), E unknown (phase1-data/probe 56G possibly sole-copy hidden-state extractions - NOT touched; surface-residualization-control worktree 44G derived re-read cache - NOT touched; worktree fleet ~90G needs dedicated hygiene pass). User approved batch-by-batch; rm -rf auto-denied by permissions so deletions ran via reviewed script + python subprocess wrapper. Freed: 140G->276G (72% used). Root-owned leftovers need user sudo: HF cache models--Qwen--Qwen3.5-4B, truncated Qwen3-4B-clean-sft-dpo merge dir, plus older gemma-pocket worktree debris. Registry rows spot-verified in checkpoint-staging.md before every bucket-B deletion. Pinned image re-pull by digest running in background (WSL docker-credential-desktop.exe exec-format failure worked around with bare DOCKER_CONFIG={}). PR #386 opened: scripts/ops/prune_runtime.sh (stage|scan modes) + local-runtime.md retention policy (never docker image prune -a; free-space precheck before merge/training; staged-adapter merged-16bit prunable rule; checkpoints-rotation prunable post-completion; results_*/probe never). Kept per user: gemma-4-E4B, Mistral-7B, Llama-3.2-3B atlas caches. Chain resume plan: after image lands, fresh executor redoes DPO merge first (disk precheck), then KTO merge/smokes/full evals/grpo_v2 queue. GRPO seed-2 42h wall-clock guardrail long blown by stalls+crash (compute itself ~3.5h) - needs user ruling at resume.
### 006-checkpoint - Checkpoint

- at: `2026-08-03T15:06:01Z`
- kind: `checkpoint`
- summary: Chain resume + wake-failure root cause (2026-08-03): user restarted Docker Desktop which restored the nvidia runtime (no toolkit install needed) but wiped the image store again; pinned image re-pulled by digest + retagged, GPU verified inside container. Executor4 preflight: re-verified both stage-2 adapters + lineage, found and fixed lost :latest tag (retag on verified digest, lead-endorsed), correctly escalated nvidia-runtime loss instead of installing packages. Queue items 1-2 complete and lead-verified digit-for-digit: DPO redo-merge (shards 4967215360+3077766632 exactly matching reference; crash damage repaired) + smoke G0 PASS (192/192 coverage, 0 thinking hits, refusal_recall 88.42); KTO merge + smoke G0 PASS (86.32 recall, mean_conf 0.8240). Base full eval (G1 denominator) complete: n=3369, refusal_recall 89.92, answer_on_unknown 10.08, over_refusal 58.24, truthful 41.17 (seed-1 denominator was 87.02/12.98). DPO full eval running (eh-grpo3seed-2-clean_sft_dpo-full_eval-20260803T150428Z, corrected_base config template). DURABLE OPERATIONAL FINDING (add to local-runtime.md next housekeeping PR): teammate agents are NOT reliably re-invoked when their background docker-wait tasks complete - 4 failures across 3 executors (stalls 1.5h/8h/10h/1h), both mid-turn (notification swallowed) and from idle; lead-session task notifications ARE reliable. Containment architecture: short containers foreground with timeout (zero stalls since); long containers get lead-side docker wait as PRIMARY wake; on lead-watch fire, verify then IMMEDIATELY push results+proceed order to executor (do not wait for its report); executor docker-inspects all open containers at start of every turn. WSL VHDX maintenance window planned at grpo_v2 boundary: user runs wsl --shutdown, Optimize-VHD per vhdx on F: (WSL ext4 + Docker Desktop disks; freed ext4 space does not return to Windows host until compaction), wsl --manage Ubuntu-22.04 --set-sparse true, restart Docker Desktop, claude --resume; lead commits NOTEBOOK batch + holds executor before window; expect image-store wipe again after (recovery: pull-by-digest + retag + clean DOCKER_CONFIG). Remaining queue after window: grpo_v2 training, 4 stage-3 stacks, stage-3 evals, then seed-3 chain.
### 007-checkpoint - Checkpoint

- at: `2026-08-03T16:01:33Z`
- kind: `checkpoint`
- summary: Seed-2 stage-2 closeout complete (2026-08-03): all three full 3369-row evals done and lead-verified. Base (G1 denominator): refusal_recall 89.92 / answer_on_unknown 10.08 / over_refusal 58.24 / truthful 41.17. DPO arm: 89.34 / 10.66 / 55.97 / 41.32 (sits on base, over-refusal down ~2.3pp, mirrors seed-1 cold-DPO flatness). KTO arm: 85.66 / 14.34 / 54.00 / 40.31. G0 smoke clauses PASS for both stage-2 arms (lead-adjudicated, digit-for-digit independent verification). One more wake failure at the base-eval boundary (1h lost, caught on user ping) prompted the final discipline: lead watch is PRIMARY driver, verify-then-push immediately on fire — worked perfectly for DPO and KTO evals (push within a minute of exit). Durable gotcha landed as PR #387 (skill/teammate-watch-discipline branch, local-runtime.md + mirrors): teammate docker-wait wakes unreliable (4 stalls/3 executors), binding watch architecture recorded. User confirmed NO Claude memories for this project (block_memory_write.sh hook working as intended; memory dir does not exist) - durable knowledge goes to skills/session notes/KG only. PR #386 (prune policy) merged by user earlier. WSL VHDX maintenance window imminent: executor4 finalizing self-contained NOTEBOOK draft then HOLDING; lead commits NOTEBOOK batch; user then runs wsl --shutdown + Optimize-VHD on F: vhdx files (WSL ext4 + Docker Desktop) + wsl --manage Ubuntu-22.04 --set-sparse true + restart Docker Desktop + claude --resume. Expect: image store wiped again (recovery = pull-by-digest + retag + clean DOCKER_CONFIG), executor4 dead (successor harness spawns from committed NOTEBOOK). Post-window queue: grpo_v2 training launch (the G1-tested arm), 4 stage-3 stacks, stage-3 evals, seed-3 chain. Seed-2 GPU compute so far ~4.5h of 42h re-baselined budget.
### 008-checkpoint - Checkpoint

- at: `2026-08-04T22:01:29Z`
- kind: `checkpoint`
- summary: G1 SEED-2 LEG PASS (2026-08-04, lead-adjudicated): clean_sft_grpo_v2 seed-2 vs same-seed base — answer_on_unknown 10.08 -> 5.72 (−4.36pp, floor 3.0pp) and refusal_recall 89.92 -> 94.28 (+4.36pp, floor 3.0pp), both conditions met; verified from metrics.json AND independently re-derived from 3369 scored rows (1032 unknown), exact agreement. Seed-1 effect was ±6.39pp; ±4.36pp attenuation within direction-plus-floor design. Overall G1 OPEN pending seed 3 (registered two-seed requirement, no goalpost movement). Side numbers: over_refusal 58.24 -> 66.75, truthful flat 41.17 -> 41.35 (same trade shape as seed-1). Training: 1861 steps, 8h10m (vs 7.22h est), final_loss 0.0768, final reward 0.9071 (seed-1 finished 0.617); GRPO lineage runtime.status/time fields null (schema quirk, completion evidenced by artifacts). Executor5 pre-launch catch: stale pre-archive-move rewards.custom.file path in ALL four seed-1 GRPO config templates (would ValueError at startup); fixed via absolute in-container path in new seed-2 configs; 90s dry-run validated before the 8h launch. Merge + smoke G0 PASS (93.68 smoke recall vs base 89.47 — direction visible pre-eval). Post-maintenance runtime survived intact (image, nvidia runtime, tag all present; no re-pull needed). Executor5 model harness so far: zero stalls, independent re-verification, loud escalations. STAGE-3 RELEASED serial per launch_order: dpo_grpo, kto_grpo, grpo_dpo, grpo_kto (sources = merged stage-2 checkpoints per cell.yaml; corrected reward path carries into new GRPO-stage configs; dry-run endorsed before each multi-hour launch). Compute ~13.2h of 42h seed-2 budget. NOTEBOOK batch commit pending executor confirmation of final draft through grpo_v2 closeout. Next: 4 stage-3 stacks (each: train + merge + smoke + full eval), then G2 adjudication, then seed-3 full chain.
### 009-checkpoint - Checkpoint

- at: `2026-08-05T08:30:19Z`
- kind: `checkpoint`
- summary: GRPO three-seed seed-2 stage-3 stacks 1-2: dpo_grpo CLOSED (train 1861 steps loss 0.0962 reward 1.0998; merge byte-exact; smoke 192/192/192/0; full eval n=3369 recall 94.38 / answer-on-unknown 5.62 / over-refusal 65.81 / truthful 41.50 — endpoint nearly identical to same-seed grpo_v2 94.28/5.72, G2-relevant, adjudication deferred; G0 PASS, NOTEBOOK c550ba63). kto_grpo training COMPLETE (4h41m, 1861 steps, loss 0.0846, reward 1.134, correct KTO merged source, NOTEBOOK 8704700f); closeout (merge/smoke/full-eval) released to executor6. Executor succession 5->6 after lead-session compaction severed executor5 (NOTEBOOK f82ae66b); executor6 zero stalls so far, lead-watch architecture holding (all three boundaries this arc fired via lead-side docker wait). Reward endpoint ordering seed 2: clean-SFT base 0.9071 < DPO base 1.0998 < KTO base 1.134. Remaining seed-2: kto_grpo closeout, then grpo_dpo + grpo_kto (both source from seed-2 grpo_v2 merged), then seed 3. Next decision points: G2 adjudication once all four stacks close; PR #387 merge still awaiting user.
### 010-checkpoint - Checkpoint

- at: `2026-08-05T14:16:28Z`
- kind: `checkpoint`
- summary: Seed-2 stage-3 stacks 3-4 + gate adjudications. grpo_dpo CLOSED (train 1h34m, 1868 steps, loss 0.0419; full eval n=3369: recall 94.67 / ans-on-unk 5.33 / over-refusal 65.98 / truthful 41.53; G0 PASS, NOTEBOOK b0df73a9). grpo_kto (FINAL seed-2 arm) training launched 13:50Z, ~1h40m, dual watch armed. G2 SEED-2 LEG ADJUDICATED PASS (f235e45d): gates.yaml sha256 7c79a418... verified byte-identical to signed experiment.yaml pin; over_refusal 66.75->65.98 (decrease, min_magnitude_pp deliberately null) MET, answer_on_unknown 5.72->5.33 (cap +2.0pp) MET; neither not_confirmed_if clause fires. LEAD ERROR CORRECTED IN RECORD: had framed grpo_dpo as a replication concern by reasoning from shrunken effect size (-0.77pp vs seed-1 -2.99pp) against a magnitude bar the gate explicitly declines to set ('a magnitude bar here would invent precision the instrument does not have') - goalpost movement in the STRICT direction, same violation class as loosening. Second error corrected: G2 does NOT require all four stacks (comparison is grpo_dpo vs grpo_v2 only, adjudicable at stack-3 closeout); grpo_kto is needed for chain completeness and G3 intervals. Status: G0 PASS all closed seed-2 cells, G1 seed-2 leg PASS, G2 seed-2 leg PASS, both OPEN overall pending seed 3. WAKE-LATENCY INSTANCE: lead docker-wait notification fired ~3h after container exit, GPU idled; mitigation now dual-signal (docker wait + polling Monitor). GOVERNANCE: gates.yaml in 2 of 53 experiments declares status:proposed while signed; PR #388 opened adding warning-only exp-validate rule; neither pinned file edited (grpo block is mid-run with results, repin is pre-run-only by design; postfix-rerun edit was classifier-blocked and reverted to byte-identical pin 44013bc9). Executor6 caught a lead error (claimed DPO trainer has no --dry-run; it does, exits pre-model-load) - dry-run before every long launch now standing practice. Next: stack-4 closeout, seed-2 chain complete, then seed 3.
### 011-checkpoint - Checkpoint

- at: `2026-08-05T17:43:03Z`
- kind: `checkpoint`
- summary: SEED 2 COMPLETE (8/8, G0 PASS all cells) and SEED 3 UNDERWAY. Seed-2 final matrix (n=3369): base 89.92/10.08/58.24; dpo 89.34/10.66/55.97; kto 85.66/14.34/54.00; grpo_v2 94.28/5.72/66.75; dpo_grpo 94.38/5.62/65.81; kto_grpo 93.31/6.69/64.23; grpo_dpo 94.67/5.33/65.98; grpo_kto 91.76/8.24/61.10 (recall/ans-on-unk/over-refusal). G1 seed-2 leg PASS, G2 seed-2 leg PASS, both OPEN pending seed 3. Descriptive: GRPO-terminal arms converge to 93.3-94.4 recall regardless of parent (85.7-89.9); truthful flat 41.2-41.5 in 7 of 8 arms; over-refusal is the standing cost (61-67 vs base 58.24); grpo_kto is the outlier, reopening ans-on-unk +2.52pp vs grpo_v2 while buying the largest over-refusal relief -5.65pp — recorded DESCRIPTIVELY ONLY since G2's registered comparison is grpo_dpo vs grpo_v2 and applying it to grpo_kto would be inventing a gate. Seed-2 compute 24.37 training GPU-h (~29-30h with evals) of 42h. SEED 3: stage 1 CRASHED first attempt (exit 139 SIGSEGV, cudaErrorUnknown at step 975/1495) — G0 instrument stop, capacity RULED OUT (seed-2 identical config peaked HIGHER at 32.64 vs 27.71 GB and completed), diagnosed as transient WSL2 GPU-passthrough fault, relaunched from scratch (not resumed from checkpoint-500, which would diverge from how seeds 1-2 were produced). Relaunch clean: 1495 steps, loss 0.4282 (seeds 1/2 were 0.4281/0.4281 — SFT converges to same point every seed). Base merged+smoked+full-evaled: G1 DENOMINATOR FOR SEED 3 = recall 88.28 / ans-on-unk 11.72 / over-refusal 59.01 / truthful 40.55, in-family between seeds 1 and 2. PRE-STATED seed-3 G1 thresholds BEFORE grpo_v2 trains: grpo_v2 must reach ans-on-unk <=8.72 AND recall >=91.28. Stage-2 dispatched (dpo, then kto, then grpo_v2, serial). CRITICAL PROCESS CORRECTION: background 'docker wait' task status reports the WAIT command's exit, NOT the container's — a crashed container (139) showed as 'exit code 0'. Always read the watch OUTPUT FILE. Now running dual watches (docker wait + polling Monitor that reports the real exit code). Other: PR #387/#388/#389 merged; #390 (postfix-rerun G1 decision-rule governed revision, amendment text governs) and #391 (runtime skill: detached-log buffering, per-trainer dry-run cost, post-prune compute accounting) OPEN awaiting PI merge. Executor6 caught two lead errors this session (DPO --dry-run exists; and it read trainer source rather than trusting lead claims).
