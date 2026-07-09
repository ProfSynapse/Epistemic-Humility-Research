---
title: 'Two-signal trust readout: live inference reference pipeline (gate + dial + veto)'
kg:
  id: experiment:two-signal-runtime
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: running
governance: exploratory
phase: phase1
lane: local
est_compute: 'CPU minutes to fit calibration artifacts; one RTX 3090 to load the base model for a live demo (no training)'
relationships:
  - type: tests
    target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
    target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
    confidence: high
  - type: tests
    target: '[[per-answer-correctness-linearly-readable-post-generation]]'
    target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
    confidence: high
  - type: builds_on
    target: '[[two-signal-readout]]'
    target_id: experiment:two-signal-readout
    confidence: high
  - type: builds_on
    target: '[[internal-twosignal-readout--training-free]]'
    target_id: paper:internal-twosignal
    confidence: high
related:
  - '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  - '[[per-answer-correctness-linearly-readable-post-generation]]'
  - '[[two-signal-readout]]'
  - '[[internal-twosignal-readout--training-free]]'
---

## Question & Goal

Can the validated two-signal readout (answerability gate + correctness dial +
hallucination veto) run as a single-process, live inference pipeline a user can
talk to, surfacing a calibrated, thresholdable trust number per answer, with no
modification to the base model?

This is the deployment-facing companion to the research note `two-signal-readout`
(the probe cells S/T/U/Stage1.5/W/X). It is **engineering**, not a new claim: it
packages the existing fitted readout into a runnable reference pipeline and adds
the calibration step the paper plan flagged as the cheapest do-item.

## Design

A reference pipeline (NOT production serving). One forward for the gate, generation,
one re-forward for the dial - the validated 4.2 capture path, identical to the
offline extractor surface the probes were fit on.

```
prompt --PREFILL--> gate = calibrated answerability at pre-gen anchor (L18)
            |
            +-- gate < tau_gate --> ABSTAIN
            +-- gate >= tau_gate --> GENERATE --> dial = calibrated correctness
                                                          at post-gen content tok (L20)
                                                  |
                                                  +-- trust low  --> VETO / LOW-TRUST flag
                                                  +-- trust high --> surface answer + trust
```

Components (all under `experiment/phase1/probe/`):

| file | role |
|------|------|
| `fit_calibration.py` | fit scaler+logistic+calibration-map per signal; honest nested-CV ECE; ship lower-ECE of Platt/isotonic; write portable artifact (npz + json) |
| `two_signal_runtime.py` | `TwoSignalReadout` library: load base + artifacts; `generate_with_trust(q)` runs gate/generate/dial/veto |
| `two_signal_cli.py` | talk-to-the-model REPL (`-q` one-shot); shows answerability, answer, trust, LOW-TRUST flag; `:set gate/veto` knobs |
| `experiments/common/artifacts/two_signal_calibration/` | shipped artifacts (`gate__*`, `dial__*`); ~60 KB each |

**Base model is never modified.** A signal is `sigmoid(w . normalize(h_L) + b)`
followed by a calibration map, applied in numpy on one layer's residual-stream
vector. Read-and-act-externally: the orchestration layer decides abstain/hedge/
veto/surface; no activation steering (our steering-asymmetry result says it is
unreliable). Full architecture: `docs/architecture/two-signal-readout-inference-serving.md`.

## Calibration artifacts (Qwen3-4B Instruct base)

| signal | source | layer | AUROC | ECE raw | ECE shipped | method |
|--------|--------|-------|-------|---------|-------------|--------|
| gate (answerability, pre) | Amendment W SelfAware | L18 | 0.997 | 0.0156 | 0.0105 | isotonic |
| dial (correctness, post) | Amendment S answerable | L20 | 0.834 | 0.151 | 0.023 | Platt |

Calibration is honestly evaluated with nested CV (the calibrator never sees its own
eval fold); the dial's G3 ECE miss (0.151) becomes a pass (0.023) with ranking
preserved (AUROC unchanged).

## Prerequisites & Gating

- Fitted extractions present: Amendment S stage2 (dial source) and Amendment W
  stage2 (gate source) under `experiment/phase1/probe/qwen3-4b-instruct/`.
- Artifacts built: `fit_calibration.py --signal dial` and `--signal gate` (CPU).
- Live demo: one RTX 3090 free (no parallel GPU cells); base model loads on start.
  Run inside the unsloth Docker image with `--entrypoint python`; interactive REPL
  needs `-it`, or use `-q` one-shot. Single GPU - the demo waits behind any running
  extraction (e.g. an Amendment X sweep).

## Runbook

1. **Fit artifacts (CPU):**
   `python3 experiment/phase1/probe/fit_calibration.py --signal dial`
   `python3 experiment/phase1/probe/fit_calibration.py --signal gate`
2. **Self-check (CPU, no model):** `python3 experiment/phase1/probe/two_signal_runtime.py`
   (artifacts load + apply).
3. **Live demo (GPU):**
   `python3 experiment/phase1/probe/two_signal_cli.py -q "Who wrote Dune?"` (one-shot)
   or interactive REPL inside the GPU container.

## Validation contract

- Pre-run: both artifacts resolve; npz dims match `hidden_dim`; calibration method
  recorded.
- Post-run (live): per question a `TrustResult` with gate answerability, abstain
  decision, answer (if gated through), calibrated trust, veto flag.
- Definition of done: live CLI answers a known fact with high trust, abstains on an
  unanswerable question, and flags a confident wrong answer as LOW-TRUST. (Pending
  the GPU live smoke.)

## Variations

- **By signal:** gate-only (answerability pre-filter), dial-only (post-hoc trust on
  an already-generated answer), or the full gate+dial+veto pipeline.
- **By threshold:** `--gate-threshold` (abstention aggressiveness) and
  `--veto-threshold` (LOW-TRUST flag), tunable live via `:set`; operating points come
  from the risk-coverage curve.
- **By capture path:** re-forward (4.2, implemented) vs inline mid-decode hook (4.1,
  the deployment optimization, not yet built).
- **By model:** any checkpoint with fitted gate+dial artifacts; refit per checkpoint
  (the dial direction drifts across checkpoints). Currently Qwen3-4B Instruct base.
- **Deferred:** production serving (vLLM/TGI hidden-state exposure or aux-head-in-graph).

## Outputs & provenance

- Artifacts: `experiments/common/artifacts/two_signal_calibration/{gate,dial}__qwen3-4b-instruct__*.{npz,json}`.
- Code: the three files above.
- Episodic record: `docs/sessions/20260630T204500Z-paper-series-architecture-inference-design-two-signal-runtime-build.md`.
- Design: `docs/architecture/two-signal-readout-inference-serving.md`.
- Engineering tier - not a headline claim; does not feed the locked PROTOCOL matrix.

## Status log

- 2026-06-30: created (running). Calibration artifacts built (dial ECE 0.151->0.023,
  gate 0.0156->0.0105); runtime library + CLI written; no-GPU self-check GREEN;
  compile clean. Live GPU smoke of the CLI pending the single GPU freeing from the
  Amendment X sweep.
