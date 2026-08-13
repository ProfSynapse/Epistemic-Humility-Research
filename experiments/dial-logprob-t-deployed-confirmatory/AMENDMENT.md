# Dial vs token-logprob on the deployed checkpoint: gated confirmation at adequate power

Status: RESOLVED (2026-08-13; signed 2026-08-13, machine state in `experiment.yaml`). Registered content frozen at signing; see Outcome.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`dial-logprob-baseline-v3` (resolved 2026-08-13) settled the S-arm question —
on the raw base, the dial's margin over the model's own answer-span logprob
lands in the registered ambiguous band — and vindicated the fresh
single-capture instrument (0 integrity failures against v2's 15.4% round-trip
class). Its T arm, registered descriptive-only, recorded a data-stage stop at
the LP3-G0 power floor: 710 answered rows against the 1,000 floor, from the
verbatim-inherited 4,000-attempt inventory cap. The deployed-checkpoint
comparison therefore remains unmeasured under a gate, while two non-citable
descriptive reads (v1's +0.158 with the round-trip caveat; v2's unblinded
+0.1747 computed behind its LP-G0 stop) both point the same direction.

This cell asks the T-side question AS the gated primary, at a registered
attempt cap sized so the power floor is reachable. Exploratory tier (tier-2
amendment); its number is reported as exploratory evidence for paper 4's
limitation 9, never pooled with any confirmatory surface.

## Design

Verbatim reuse of the v3 instrument, single arm:

- Machinery: the `experiments/dial-logprob-baseline-v3/lp_v3_harness.py`
  pattern — single-pass vLLM 0.27.1 generation (token IDs + per-token
  logprobs from one call), teacher-forced HF extraction over the captured
  token IDs at the dial layer (the registered fallback path v3
  build-verified), source scorers and OOF dial refit imported unchanged,
  paired bootstrap unchanged (n_boot 2000). The harness is copied into this
  cell as `lp_t_harness.py` and parameterized by this cell's `cell.yaml`; no
  v3 file is modified.
- Arm: `t_deployed_confirmatory` = v3's `t_deployed_descriptive` checkpoint
  identity verbatim (merged-16bit + LoRA adapter paths copied from v3's
  `cell.yaml`), dial layer L22, greedy, EOS, `enable_thinking=False`, batch
  invariance pinned.
- Attempt cap, sized by power arithmetic (pre-stated, not tuned): v3 observed
  710 answered / 4,000 attempted (17.75%). Target ≥ 1,000 answered with
  margin for rate drift: registered cap 12,000 attempts from the same
  `build_pool` inventory (uncapped pool 25,580), expected answered ≈ 2,100.
  The cap is fixed here, before the run; it is not extended mid-run.
- Engine: vLLM 0.27.1 pinned (`instrument.engine`), same venv and env pins as
  v3 (`VLLM_WSL2_ENABLE_PIN_MEMORY=1`, `VLLM_BATCH_INVARIANT=1`).

Instrument configs pinned at sign: `cell.yaml`, `gates.yaml`,
`lp_t_harness.py`.

## Prediction

Disclosure: no blind guess is possible — v1's descriptive T read (+0.158,
round-trip caveat) and v2's unblinded stopped-cell margin (+0.1747, CI
[0.140, 0.211]) have both been seen by the registrant. Stated prediction: the
T-arm margin lands clearly positive near +0.15 and LT-G1 passes.

## Falsifier

(1) Dial-novelty falsifier, verbatim from v1/v2/v3: primary-variant logprob
AUROC at or above the dial AUROC (margin <= 0), paired 95% CI excluding 0 in
that direction. (2) The instrument fails its own LT-G0 integrity gate —
reported straight as a design-diagnosis signal, not retried.

## Gates

- LT-G0 (integrity precondition, pre-outcome stop), verbatim from v3's
  LP3-G0 with the sanity bound applied to this cell's own arm:
  (a) capture integrity per row (teacher-forced extraction consumed exactly
  the captured prompt+generated token IDs; any divergence is a stop, never a
  tolerance);
  (b) coverage: every attempted prompt gets a recorded disposition;
  (c) power floor: ≥ 1,000 answered rows, else data-stage stop (floor
  unchanged from v3; the CAP moved, not the floor);
  (d) instrument sanity: fresh T dial OOF AUROC ≥ 0.75 (v2's unblinded T
  refit read 0.8164; 0.75 is a reads-at-all bound, not a reproduction
  target).
- LT-G1 (primary, gated): dial AUROC minus primary-logprob AUROC ≥ +0.05,
  paired bootstrap 95% CI excluding 0. Ambiguous band verbatim from
  v1/v2/v3: 0 < margin < +0.05 or CI straddling 0 → reported as
  small/uncertain margin; gate never retuned after the result.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | LT-G1 PASS, margin near +0.15 |
| user | |

## Budget

Single arm: ~12,000 vLLM greedy generations (v3's T arm ran 4,000 in ~3 min;
expect ~10 min), one teacher-forced extraction pass, CPU scoring and
bootstrap in minutes. Well under one local GPU-hour on the 3090.

## Outcome

Run 2026-08-13, local RTX 3090, vLLM 0.27.1 pinned stack, single launch
(smoke suite 7/7, dry-run, and the v3-pattern real-generation pre-launch
smoke all recorded in NOTEBOOK before the launch verb).

**LT-G0 PASS on all four conditions.** (a) Capture integrity: 0
divergences across all extracted rows (the single-capture posture held, as
in v3). (b) Coverage: 8,621 attempted items, 8,621 distinct recorded
dispositions (the registered `select_attempted` stopping rule reached its
target_correct=500/target_wrong=500 targets at 8,621 attempts, inside the
registered 12,000 cap; cap not extended). (c) Power floor: 1,501 answered
rows >= 1,000 (answer rate ~17.4%, consistent with v3's observed ~17.75%
on the same checkpoint/pool convention). (d) Instrument sanity: fresh T
dial OOF AUROC 0.7962 >= 0.75 bound.

**LT-G1 PASS.** Dial AUROC 0.7962 vs primary (mean_answer_span) logprob
AUROC 0.6569: margin **+0.1393, paired bootstrap 95% CI [0.1031, 0.1755]**
(n_boot 2000, seed 20260813). The +0.05 floor is met and the CI excludes
zero; neither falsifier fired; the ambiguous band does not apply. The
registered prediction (clearly positive, near +0.15) landed as stated.
Descriptive-only secondary variants: sum_answer_span AUROC 0.7706,
min_answer_span AUROC 0.7536 (both n=1501, not gated) -- the sum variant
runs much closer to the dial than the mean variant does, a descriptive
observation only.

Paired with v3's S-arm result (raw base margin +0.0118, ambiguous band),
the program-level shape is that the dial's margin over the model's own
answer-span logprob is checkpoint-dependent: negligible on the raw base,
large and now gated on the deployed abstention-trained checkpoint. This
cell supersedes the two non-citable descriptive T reads (v1's +0.158 with
the round-trip caveat; v2's unblinded stopped-cell +0.1747) as the sole
citable deployed-checkpoint number.

**One-sentence verdict:** on the deployed abstention-trained checkpoint,
the dial beats the model's own answer-span logprob by a gated margin of
+0.1393 (95% CI [0.1031, 0.1755], n=1,501), passing LT-G1 at adequate
power.
