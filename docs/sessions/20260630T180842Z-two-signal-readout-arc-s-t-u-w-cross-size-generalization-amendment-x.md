---
schema_version: research-session/v1
session_id: 20260630T180842Z-two-signal-readout-arc-s-t-u-w-cross-size-generalization-amendment-x
title: Two-signal readout arc (S-T-U-W) + cross-size generalization (Amendment X)
status: active
created_at: '2026-06-30T18:08:42Z'
updated_at: '2026-06-30T18:08:42Z'
phase: phase1
question: Is the answerability-gate + correctness-dial + hallucination-veto a training-free,
  model-general readout? Arc from the correctness-readout discovery (S) through the
  deployed checkpoint (T), hallucination veto (U), orthogonal two-stage pipeline (Stage
  1.5), training-free base (W), framework synthesis + KG self-ingest, V shelving,
  and the in-flight cross-size sweep (Amendment X).
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: The deliverable (a surfaced, thresholdable trust signal that tracks
    whether THIS answer is correct) is a training-free READOUT of two orthogonal internal
    axes - answerability (gate, read at the prompt anchor) and per-answer correctness
    (dial, read post-generation) - validated on Qwen3-4B (S/T/U/Stage1.5/W). Amendment
    X is testing whether it is size-general within Qwen3 (1.7B/8B/14B); smoke GREEN,
    full sweep pending. NOTE - the anchor doc itself (research-trajectory.md, Jun
    19) is stale - it predates Paper 3 finalization and this whole arc and needs a
    governed refresh.
  changed_by_session: true
checkpoints:
- id: 001-result
  at: '2026-06-30T18:08:42Z'
  kind: result
  title: Amendment S - per-answer correctness is linearly readable post-generation
  summary: A linear probe at the post-generation content token ranks per-answer correctness
    at AUROC 0.834 (L20, Instruct base); reading AFTER the answer beats before by
    +0.065 (CI [0.040,0.090] excludes 0 - the first P(True)/self-eval win). G1+G2
    PASS, G3 (ECE-style) misses at 0.151. New free-answer surface (500 correct / 1336
    wrong).
  evidence:
  - experiments/correctness-confidence-probe/AMENDMENT.md
  - experiment/phase1/probe/amendment_s_correctness_probe_score.py
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals:
    auroc_post: 0.834
    self_eval_gain: 0.065
- id: 002-result
  at: '2026-06-30T18:08:42Z'
  kind: result
  title: Amendment T - the S readout survives on the deployed checkpoint
  summary: On the deployed clean-SFT -> GRPO-v2 checkpoint the S correctness readout
    replicates (post AUROC 0.819, L22; self-eval gain +0.074, CI excludes 0; G1+G2
    PASS, G3 0.168). Cold-transfer of the S probe = 0.679 (partial; direction drifts,
    refit per checkpoint). GRPO-v2 refused ~82% even under forced-best-guess.
  evidence:
  - experiments/correctness-readout-deployment-port/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals:
    auroc_post: 0.819
    cold_transfer: 0.679
- id: 003-result
  at: '2026-06-30T18:08:42Z'
  kind: result
  title: Amendment U - the correctness dial vetoes confident hallucinations
  summary: The dial reads hallucinations on unanswerable questions as LOWEST-trust
    (AUROC 0.980; within-SelfAware control 0.93 rules out dataset shift). Confident
    confabulation does NOT read like correctness - the veto is real. Two-signal mechanism
    complete on one trained checkpoint.
  evidence:
  - experiments/unified-two-signal-dial-veto/AMENDMENT.md
  - experiment/phase1/probe/amendment_u_two_signal_score.py
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals:
    veto_auroc: 0.98
    within_selfaware_control: 0.93
- id: 004-result
  at: '2026-06-30T18:08:42Z'
  kind: result
  title: Stage 1.5 - the two axes are an orthogonal pipeline, not a fused scalar
  summary: Gate + dial validated per-item on CPU (PR 128). The answerability and correctness
    axes are orthogonal; FUSING the scalars HURTS correctness ranking (delta -0.014,
    CI excludes 0), so they deploy as two separate stages. The gate transfers cross-prompt.
  evidence:
  - papers/paper-4-two-signal-readout/notes/framework.md
  run_ids: []
  commands: []
  decisions:
  - Keep gate and dial as separate pipeline stages; do not fuse into one scalar.
  next_steps: []
  signals:
    fusion_delta: -0.014
- id: 005-result
  at: '2026-06-30T18:08:42Z'
  kind: result
  title: Amendment W - the full mechanism is training-free on the RAW base
  summary: On raw unsloth/Qwen3-4B-bnb-4bit (no adapter, no abstention SFT/RL) the
    full mechanism reads off - gate 0.997 + dial 0.834 + hallucination-veto 0.754
    (W-G1 0.7545, W-G2 0.997, both PASS). Task training SHARPENS the veto (0.754 ->
    0.980; halluc dial-mean 0.271 base -> 0.018 trained) and adds ~0 to the gate -
    training amplifies, it does not create, the signal. Answers "do we need training?"
    for the readout deliverable - no.
  evidence:
  - experiments/base-model-training-free-mechanism/AMENDMENT.md
  - experiment/phase1/probe/amendment_w_base_model_extract.py
  - experiment/phase1/probe/amendment_w_base_model_score.py
  run_ids: []
  commands: []
  decisions:
  - The headline shifts to "training is not needed for the readout"; de-emphasize
    retraining-on-seeds as off-message.
  next_steps: []
  signals:
    gate: 0.997
    dial: 0.834
    veto_base: 0.754
    veto_trained: 0.98
- id: 006-decision
  at: '2026-06-30T18:08:42Z'
  kind: decision
  title: Framework synthesis + KG self-ingestion of the trajectory
  summary: Wrote the theoretical framework (thesis "epistemic state in a small LM
    is largely a readout, not a training outcome") and self-ingested the arc into
    the typed KG - the first INTERNAL paper nodes (paper:internal-paper3, paper:internal-twosignal)
    plus 6 mechanism atoms (M1-M6) with supported_by edges to the internal papers
    and related_to edges into the external literature graph.
  evidence:
  - papers/paper-4-two-signal-readout/notes/framework.md
  - library/notes/internal-twosignal-readout--training-free.md
  - library/notes/internal-paper3--knows-but-doesnt-say.md
  run_ids: []
  commands: []
  decisions:
  - Atomize internal findings as first-class KG nodes so they are reusable evidence.
  next_steps: []
  signals:
    internal_paper_nodes: 2
    mechanism_atoms: 6
- id: 007-decision
  at: '2026-06-30T18:08:42Z'
  kind: decision
  title: Amendment V (natural-answer generalization) shelved
  summary: V was signed and gates locked but DEFERRED unlaunched - the natural deployment
    prompt is data-starved (~96% refusal on the deployed checkpoint, too few natural
    errors/hallucinations for a probe verdict) and W supersedes its intent by establishing
    the training-free readout directly. Reported as a SAFETY observation, not a probe
    verdict; the forced prompt was NOT substituted.
  evidence:
  - experiments/natural-answer-generalization/AMENDMENT.md
  run_ids: []
  commands: []
  decisions:
  - Shelve V; do not switch it to the forced prompt to manufacture a class.
  next_steps: []
  signals:
    refusal_rate_approx: 0.96
- id: 008-amendment
  at: '2026-06-30T18:08:42Z'
  kind: amendment
  title: Amendment X signed - cross-size generalization of the training-free readout
  summary: Reframed "seeds" (rejected - greedy decode + only-seed1-on-disk make naive
    seed reruns no-ops) to cross-MODEL/cross-SIZE generalization. User chose a Qwen3
    size sweep (1.7B/8B/14B; 4B done). Tier-2 amendment SIGNED 2026-06-30, gates LOCKED
    - per model X-G3 veto (PRIMARY) >=0.65 CI excl 0.50, X-G1 gate >=0.65, X-G2 dial
    >=0.65; adequacy >=30 wrong AND >=50 halluc. SUCCESS = all three on all three
    sizes; FALSIFIER = veto fails on >=2 of 3. Scope = size within one family; cross-family
    deferred (named limitation).
  evidence:
  - experiments/cross-model-size-sweep/AMENDMENT.md
  - experiment/phase1/probe/amendment_x_cross_model_extract.py
  - experiment/phase1/probe/amendment_x_cross_model_score.py
  run_ids: []
  commands: []
  decisions:
  - Size sweep within Qwen3 is the controlled first cut; cross-family is the next
    axis.
  next_steps: []
  signals:
    gate_threshold: 0.65
- id: 009-launch
  at: '2026-06-30T18:08:42Z'
  kind: launch
  title: Amendment X smoke on Qwen3-1.7B (local Docker GPU)
  summary: User authorized smoke + full sweep (single GPU, sequential). Launched the
    smoke (--max-attempts 60) on raw unsloth/Qwen3-1.7B-bnb-4bit via detached Docker
    with --entrypoint python. GPU pre-flight - RTX 3090 free (0 MiB); a stale 18h
    orphan container (ls /probe, 0 GPU) left alone; a stuck nvidia-smi probe killed
    (root cause - omitted --entrypoint, fixed in the launch pattern).
  evidence:
  - experiment/phase1/probe/qwen3-1.7b-bnb-4bit/amendment_x/smoke/manifest.json
  run_ids: []
  commands:
  - docker.exe run -d --name eh-amd-x-smoke-1p7b --gpus all --ipc=host --entrypoint
    python -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub
    -v 'F:\Code\Epistemic-Humility-Research:/workspace/repo' -w /workspace/repo unsloth/unsloth:latest
    experiment/phase1/probe/amendment_x_cross_model_extract.py --base-model unsloth/Qwen3-1.7B-bnb-4bit
    --out-dir experiment/phase1/probe/qwen3-1.7b-bnb-4bit/amendment_x/smoke --gate-rows
    experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/rows.jsonl
    --max-attempts 60 --wrong-floor 3 --hallucination-floor 5
  decisions: []
  next_steps: []
  signals: {}
- id: 010-validation
  at: '2026-06-30T18:08:42Z'
  kind: validation
  title: Amendment X pipeline GREEN end-to-end (extractor + scorer)
  summary: Smoke validated the full X pipeline on Qwen3-1.7B (28 layers) - download
    -> load -> generate -> grade -> dual-position extract -> manifest. answered=60
    (correct=6, wrong=32, halluc=11, known_ans=11), all four classes populated, both
    smoke floors cleared. The CPU scorer ran clean (exit 0), correctly returned DATA_STAGE_STOP
    (smoke halluc=11 < 50 - adequacy guard firing as designed) with directionally-correct
    dial means (correct 0.13 > wrong 0.036) even at tiny N.
  evidence:
  - experiment/phase1/probe/amendment_x_cross_model_score.py
  run_ids: []
  commands:
  - python3 amendment_x_cross_model_score.py --x-dir qwen3-1.7b-bnb-4bit/amendment_x/smoke
    --out <scratch>/x_smoke_score.json
  decisions: []
  next_steps: []
  signals:
    answered: 60
    correct: 6
    wrong: 32
    halluc: 11
    known_ans: 11
- id: 011-handoff
  at: '2026-06-30T18:08:42Z'
  kind: handoff
  title: Next - full Amendment X sweep, then writeup
  summary: "Pipeline is GREEN; ready for the full sweep (1.7B full -> 8B -> 14B, one\
    \ at a time on the single GPU; 8B/14B download on first load). Then per-model\
    \ score, assemble the cross-size SUCCESS/PARTIAL/FALSIFIER roll-up in AMENDMENT-X\
    \ \xA77, add fold-variance error bars (free) to S/T/U/W AUROCs, and seed Paper\
    \ 4 from the framework doc. Open governance item - refresh the stale research-trajectory.md."
  evidence:
  - experiments/cross-model-size-sweep/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Full X extraction on Qwen3-1.7B (lift caps), then Qwen3-8B, then Qwen3-14B.
  - "Score each model; write AMENDMENT-X \xA77 roll-up; no goalpost moved."
  - Refresh research-trajectory.md (governed) to reflect Paper 3 + the readout arc.
  signals: {}
legacy_session:
  id: '0030'
  path: docs/sessions/0030 - two-signal-readout-arc-s-t-u-w-cross-size-generalization-amendment-x.md
---
# Two-signal readout arc (S-T-U-W) + cross-size generalization (Amendment X)

## Question

Is the answerability-gate + correctness-dial + hallucination-veto a training-free,
model-general readout the user can threshold to decide how much to trust a response?
This session tracks the arc from the correctness-readout discovery (Amendment S),
through the deployed checkpoint (T), the hallucination veto (U), the orthogonal
two-stage pipeline (Stage 1.5), the training-free base-model result (W), the framework
synthesis + KG self-ingest, the shelving of V, and the in-flight cross-size sweep
(Amendment X: Qwen3 1.7B/8B/14B).

## Trajectory Position

This arc materially moves the program's position. The deliverable - a surfaced,
thresholdable trust signal that tracks whether THIS specific answer is correct - is now
understood as a training-free READOUT of two orthogonal internal axes (answerability at
the prompt anchor; per-answer correctness post-generation), validated on Qwen3-4B.
Amendment X is the size-generalization test within Qwen3.

The anchor doc `docs/research-trajectory.md` is stale (last touched
Jun 19; it predates Paper 3 finalization and this entire arc, and still frames "Paper 3
= Phases 2+3" with open model-pin decisions). A governed refresh is an open item
(handoff checkpoint 011); it is flagged, not silently rewritten.

## Summary

The two-signal mechanism is complete and training-free on Qwen3-4B: gate 0.997 + dial
0.834 + veto 0.754 read off the raw base; training only sharpens the veto (-> 0.980),
it does not create the signal. The findings are atomized into the KG (2 internal paper
nodes + 6 mechanism atoms) and synthesized in the framework doc (Paper 4 seed). V is
shelved (data-starved). Amendment X (cross-size) is signed with locked gates; its
pipeline is GREEN (smoke on Qwen3-1.7B passed extractor + scorer end-to-end), and the
full sweep (1.7B/8B/14B) is the next launch.

## Checkpoints

See the structured `checkpoints:` list in the frontmatter for the full, validated
record (001-result S through 011-handoff). Headline beats:

- **001-005 (results)** S -> T -> U -> Stage 1.5 -> W: correctness is post-gen
  readable (0.834), survives on the deployed checkpoint (0.819), vetoes hallucinations
  (0.980), is orthogonal to the gate (fusion hurts -0.014), and the whole mechanism is
  training-free on the raw base (gate 0.997 / dial 0.834 / veto 0.754; training sharpens
  the veto to 0.980).
- **006-007 (decisions)** framework synthesis + first internal KG paper nodes; V shelved.
- **008 (amendment)** Amendment X signed - cross-size generalization, gates locked.
- **009-010 (launch + validation)** X smoke on Qwen3-1.7B GREEN; full pipeline validated.
- **011 (handoff)** full sweep next; refresh the stale trajectory anchor.
- **012 (result+amendment)** Amendment X COMPLETE - all four sizes (1.7B/4B/8B/14B) PASS
  all three gates; size-robust, scaling non-monotonic (peaks 8B), no goalpost moved (PR #134).
- **013 (amendment+launch)** Amendment Z (cross-FAMILY confirmatory) pre-registered + launched
  as an overnight single-GPU queue on 4 ungated ~3-4B bases (Llama-3.2-3B, Ministral-3-3B,
  Qwen3.5-4B, Gemma-4-E4B) via a transformers-5.12.1 image (post-cutoff Gemma4/Qwen3.5 archs).
  SUCCESS = veto PASS >=3/4 -> cross-family CLAIM; FALSIFIER = veto fails >=2/4. First result
  (Llama-3.2-3B): gate 0.997 + dial 0.861 PASS, veto 0.633 FAIL (above chance, below the 0.65
  bar) -> PARTIAL. Emerging read: gate+dial family-general, the VETO is the model-dependent
  signal (same knob that softened X at 14B). Paper-writing HELD pending all 4 + user review.
- **014 (design)** NEW EXPERIMENT proposed (Paper 5 - "reading vs writing the trust axis"):
  causal confidence STEERING - turn the probe direction around to WRITE (activation steering)
  and/or inject the score into the CoT. Two modalities x two positions = a causal test of the
  anchor-vs-end "why" (probing = presence; steering/injection = use). Instrument ruling: new
  experiment; first run = signed Tier-2 amendment on own branch off main; not yet registered/
  launched. Design: docs/plans/confidence-steering-experiment.md.
- **015 (results, in-flight)** Amendment Z queue: 2 of 4 scored. Ministral-3-3B PASS (gate
  0.997 / dial 0.818 / veto 0.733) joins Llama-3.2-3B PARTIAL (veto 0.633 FAIL). Veto tally
  1 PASS / 1 FAIL; verdict hinges on Qwen3.5-4B (extracting) + Gemma-4-E4B (queued) - both
  must clear 0.65 for the >=3/4 SUCCESS. Descriptive split confirms the emerging read: Llama's
  hallucinations read as trustworthy (dial_mean_halluc 0.476 ~ correct 0.707) so its veto
  fails; Ministral's read low-trust (0.278 << 0.605) so its veto passes. Gate+dial family-
  general, VETO model-dependent (mirrors X's non-monotonic veto). Results table + data links
  in AMENDMENT-Z §7 (result JSONs amendment_z_{llama-3.2-3b,ministral-3-3b}_result.json).
  In parallel: steering-harness build dispatched to a background subagent in an isolated
  worktree (CPU-only scaffolding for Paper 5, no GPU/launch). Paper-writing still HELD (Llama
  veto miss => discuss-first) pending all 4 + user review.
- **016 (results, in-flight)** Amendment Z 3 of 4 scored. Qwen3.5-4B PASS (gate 0.998 / dial
  0.827 / veto 0.666 MARGINAL - CI [.634,.695] dips below 0.65 but point >=0.65 & excludes
  0.50). Veto tally 2 PASS (Ministral, Qwen3.5) / 1 FAIL (Llama). Gemma-4-E4B (multimodal,
  tf-5.12.1 image) now FULLY DECISIVE: PASS -> 3/4 SUCCESS; FAIL/INELIGIBLE -> 2/4 FALSIFIER.
  Three-family dial gradient (correct-vs-halluc gap): Ministral 0.327 clean > Qwen 0.211 ~ Llama
  0.231, but Llama fails while Qwen passes => veto tracks distribution overlap not mean gap
  (noted honestly, no goalpost moved). Steering scaffold DONE + parked (branch
  historical confidence-steering branch @ e53daafe, 88 tests green, awaits amendment+approval).
- **017 (RESULT: SUCCESS)** Amendment Z COMPLETE, 4/4 scored. Gemma-4-E4B PASS with the
  CLEANEST veto of the set (gate 0.998 / dial 0.818 / veto 0.871 [.850,.893]; dial_mean_halluc
  0.089 vs correct 0.593). FINAL veto tally 3 PASS (Ministral, Qwen3.5, Gemma-4) / 1 FAIL
  (Llama-3.2) => meets the pre-registered >=3/4 bar => SUCCESS. The training-free two-signal
  readout is promoted from W/X exploratory to a cross-FAMILY CLAIM (Qwen/Llama/Mistral/Gemma).
  Scope, honestly qualified: gate + dial family-general (4/4, gate saturated ~0.998); veto
  replicates (3/4) but is the fragile model-specific axis (Llama clean fail, Qwen marginal,
  mirrors X non-monotonic veto). No goalpost moved. Results ALIGNED with expectations.
- **018 (flagship paper drafted)** Per the /goal (write the paper once results align) and the
  user's canonical 4-paper map, wrote the STANDALONE Paper 3 (two-signal readout):
  `papers/paper-4-two-signal-readout/manuscript.md` (451 lines, full end-to-end draft).
  Co-headline framing throughout: gate + dial family-general (4/4), veto the fragile axis (3/4).
  NO amendment labels in reader-facing prose - S/T/U/W/X/Z -> result-JSON traceability confined
  to Appendix A. Cites the companion "Knows but Doesn't Say" diagnosis (Paper 2) for the
  representation-vs-verbalization gap; does NOT merge with it. Six figures generated by a new
  reproducible `papers/paper-4-two-signal-readout/scripts/build_figures.py` (reads amendment_*_result.json directly;
  descriptive-named, no amendment labels): cross-family readout, dial distribution, fragile-axis
  (size+family), post-beats-pre, training-sharpens-veto, pipeline schematic. Limitations carried
  from the framework rigor audit (single-seed magnitudes, training-free scoped to the
  instruction-tuned base, dial ranks-not-calibrated ECE 0.151, structural halluc label,
  cross-dataset veto reference, forced-answer surface, dial causality untested). Also updated
  `research-trajectory.md` Publication-shape section to the renumbered map. All committed on
  `pr/amendment-z-cross-family`. HELD for user review before any PR-merge / paper-2 filename
  reconciliation.
