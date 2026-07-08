---
schema_version: research-session/v1
session_id: 20260702T160000Z-consolidation-ext4-migration-ab-v1-verdict
title: Full branch consolidation + repo migration to ext4 + Amendment AB V1 fleet
  verdict
status: complete
created_at: '2026-07-02T16:00:00Z'
updated_at: '2026-07-03T06:30:00Z'
phase: phase1
question: Can everything in flight be merged to one current main? Can the repo escape
  the 9P mount that keeps stalling runs? Does first-person framing open the text channel
  (Amendment AB V1)?
tags:
- experiment-runner
- infrastructure
- paper5
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'main consolidated (all branches merged); repo on ext4; AB V1
    complete: ambiguous-leaning-negative, text channel stays shut'
  changed_by_session: fourth injection channel falsified at registered thresholds;
    revision_discrimination instrument found saturated (retro-affects AA-G4); dial-reads-recoverability
    nugget
checkpoints:
- id: 001-infrastructure
  at: '2026-07-02T18:00:00Z'
  kind: infrastructure
  title: /mnt/f 9P mount wedged mid-session; repo migrated to WSL ext4 without reboot
  summary: The 9P channel to F wedged (every op EIO; Windows-side volume Healthy),
    killing the first AB fleet run at its write (rc=120, nothing saved). Fixed without
    sudo password or wsl --shutdown via wsl.exe -u root mounting F at a second mountpoint
    /mnt/f2, then rsync-migrated the repo to ~/code/Epistemic-Humility-Research (verified
    drift-free, git fsck clean, worktree pointers hand-rewritten, KG index rebuilt).
    /mnt/f copy is a frozen backup. kg_index dead-mount tolerance fix merged as PR
    152.
- id: 002-decision
  at: '2026-07-02T22:00:00Z'
  kind: decision
  title: All branches merged to main (user directive); worktrees and local branches
    pruned
  summary: Final wave PRs 142 and 146-152 merged (papers restructure, Amendment Y,
    AB/AC prep, batching parity, Y-results paper pass, consolidation leftovers, kg_index
    fix). All 9 worktrees removed after artifact audit (one rescue, the pr28 review
    doc, copied to docs/review/); 33 merged local branches deleted; only main plus
    the three open-PR heads remain (132/134 for user to close, 135 draft pre-reg).
- id: 003-launch
  at: '2026-07-02T20:36:00Z'
  kind: launch
  title: AB V1 fleet relaunched from the ext4 repo on the 3090
  summary: Same three cells and flags as the lost run (AB-1 gate@early, AB-2 dial@late,
    AB-3 dial@final; unsloth/Qwen3.5-4B, note-variant v1, seed 20260701, temp 0.7
    top-p 0.9, sequential engine). AB-1 spent ~3h re-downloading the model to the
    fresh HF cache before generating.
- id: 004-result
  at: '2026-07-03T05:00:00Z'
  kind: result
  title: 'AB V1 complete: G2 miss (+2pt vs +10), dial cells flat, G3 not triggered'
  summary: AB-1 abstention delta +2.0pt CI [0.3,3.9] (real but 5x under gate; all
    7 real-arm abstentions are low-band notes enacted verbatim, ~2-3 percent compliance).
    AB-2 flat at the decision level (wrong-to-correct 8.1 vs 8.9 percent, zero answer-to-abstain).
    AB-3 flat on a valid instrument (delta -2.7pt, CI includes zero) - the commit-point
    position did not rescue the effect, so Q-B gets no reading. Verdict ambiguous-leaning-negative
    in AMENDMENT-AB section 8; goalposts unmoved.
- id: 005-observation
  at: '2026-07-03T05:30:00Z'
  kind: observation
  title: 'Instrument finding: revision_discrimination saturated under sampled decode
    (retro-affects AA-G4)'
  summary: compute_revised falls back to normalized-full-text change; sampled decode
    never reproduces text, so revised is True on every record (AB-1 600/600, AB-2
    500/500, AA-7 500/500 retroactively) and the metric reads 0 by construction. AB-G1
    reported UNMEASURABLE per the underpowered convention; AA-G4's flat reading was
    on the same dead instrument (its conclusion survives via AB-2's decision-level
    flows). Engine fix (answer-level revision detection) queued with the pre-next-amendment
    batching work. Trace capture in steering/reports/ab_v1 including the absorbed-without-acknowledgment
    pattern and the non-causal dial-predicts-recoverability gradient (14.5 vs 5.0
    percent, placebo flat).
next_actions:
- Open and merge the amendment-ab-v1-results PR (verdict + trace reports + analyzer).
- 'Pre-next-amendment engine work (user mandate): batching for everything - final
  position + per-element alpha vectors in arm_b_batched.py, GPU equivalence cell,
  and the answer-level compute_revised fix.'
- Remap /workspace/repo/ model paths in the AC configs (checkpoints verified present
  under local scratch), then AC smoke then full run.
- 'User: close superseded PRs 132 and 134; optionally reboot/remount to clear the
  dead /mnt/f mount; consider renaming F:\Code\Epistemic-Humility-Research to -OLD-MIGRATED.'
legacy_session:
  id: '0034'
  path: docs/sessions/0034 - consolidation-ext4-migration-ab-v1-verdict.md
---
# Session 0034 — consolidation, ext4 migration, AB V1 verdict

Arc: the merge-everything directive completed (main now carries every branch),
the repo escaped the 9P mount that had been stalling long runs (and killed the
first AB fleet mid-flight), and the relaunched Amendment AB V1 fleet completed
with an ambiguous-leaning-negative verdict: first-person framing does not open
the text channel at the registered thresholds. Fourth channel falsified
(activations, telemetry text, first-person text, aux-head co-train); the
write-side CoT-unfaithfulness picture for Paper 5 strengthens. Bonus findings:
the revision_discrimination instrument is saturated under sampled decode
(voiding its AA-G4 reading, conclusion survives on flows), and the dial score
non-causally predicts which wrong answers are recoverable on re-derivation.
