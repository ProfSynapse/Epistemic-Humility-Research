---
amendment: N
slug: grpo-v3-on-contrastive-sft-base
question: >-
  Does GRPO v3 on the calibrated Amendment K base retain its stated
  calibration while repairing behavior into one coherent model?
predictions:
  orchestrator:
    call: retains K calibration and repairs behavior gate
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  PARTIAL then STOP — calibration RETAINED 4/4, behavior REPAIR FAILED 2/4;
  beta 0.05 re-run fired the margin falsifier (+3pt, not +14.5), so the
  action/knowledge decoupling is structural, not a KL artifact.
scoreboard: null
---

# Protocol Amendment N: GRPO v3 Reward on the Amendment K (Contrastive-SFT) Base

**Status:** SIGNED — user-authorized 2026-06-28 ("draft amendment/session/
experiment and the associated configs/code then get this running I think it's
worth a shot"). Approved with defaults matching Amendment J exactly (beta 0.1,
v3 reward unchanged); §3.3 knobs available without a new signature.

**Short name:** Amendment N / GRPO-on-K / RL-on-the-calibrated-base

**Scope:** Authorize one new local cell, `schema_contrastive_sft_grpo_v3_seed1`
(seed 1, local 4B lane): the **Amendment J GRPO v3 reward, unchanged**, trained on
the **Amendment K merged base instead of the clean-SFT base**. The single variable
changed from Amendment J is the base model. The objective is to install **coherent
epistemic humility** — stated-confidence calibration AND repaired behavior in one
model — by giving RL the base that already holds the calibration it cannot install
on its own, and letting RL do the behavior shaping it is built for. It does NOT
modify PROTOCOL v0.3, Amendment E (clean-SFT), Amendment J (GRPO v3 on clean-SFT),
or the K/L artifacts. Reported separately as an alternative base.

**Session note:** `archive/docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`

---

## 1. Rationale

The calibration-gap thread has produced a clean mirror-image pair of SFT bases and
a diagnosed RL failure that, read together, point at one untried cell.

**The two bases are complementary halves of the goal:**

| base | calibration (AUROC→appropriateness) | spread (std) | cell ordering | behavior gate |
|---|---|---|---|---|
| **Amendment K** (contrastive SFT) | **0.684** ✓ | 0.309 | correct (known_correct 0.67 > wrong 0.31; unk_refused 0.58 > unk_wrong 0.16) | **fails 3/4** (over_refusal 79.2, correct_on_known 36.63, truthful 30.93) |
| **Amendment L** (answer-masked) | 0.552 ✗ (chance) | 0.180 | **inverted** (unk_refused 0.666 < unk_wrong 0.696) | **passes** |
| clean-SFT / GRPO v3 | ≈0.52 ✗ | 0.047 / 0.027 | fails | passes |

[K: calibration_gap_contrastive_sft_seed1.json; L:
calibration_gap_contrastive_masked_sft_seed1.json; v3:
session 0026 cp B0 eval, line 428.]

**The RL failure was caused by the base, not the method.** Every failed RL run
(DPO, KTO, GRPO v1/v2/v3) trained on a base whose confidence channel was already
collapsed. GRPO v3 is the decisive case: its config
(`grpo_schema_clean_sft_merged_seed1_v3_full.yaml`) sets
`model_name: .../sft_schema_clean_seed1_full/.../merged-16bit` (clean-SFT,
emitted std ≈0.047, AUROC ≈0.52) and `beta: 0.1`. So v3 was asked to **manufacture**
confidence spread from a flat distribution, *against a KL term anchoring the policy
back to that flat reference*. It could not: behavior was preserved (over_refusal
65.13%, correct_on_known 52.52%) but calibration stayed collapsed (std 0.027,
AUROC 0.522, ECE 0.44) [session 0026 cp B0 eval]. The proper-score reward was
provably aligned with calibration (verified per-prompt dynamic range) and the model
still would not move — because the base and the anchor both pulled the other way.

**The untried cell.** Run the *same* GRPO v3 reward on the *K* base. The asymmetry
that makes this expected to succeed where J failed:

- On clean-SFT (J): KL anchor → flat reference (opposes calibration); proper-score
  reward → must create spread from nothing. Both fight uphill. Calibration lost.
- On K (this cell): KL anchor → **discriminating, correctly-ordered reference**
  (preserves calibration); proper-score reward → **reinforces** the spread that is
  already there. Both point the same way. Meanwhile the dominant behavior term
  (magnitude 2.0, see §3) repairs K's broken behavior against the soft beta=0.1 KL.

This is the division of labor the evidence dictates: **SFT (K) installed the
calibration RL has failed five times to install; RL repairs the behavior it is
designed to shape.** K is the correct base (not L) because K holds the
RL-impossible half (calibration) and lacks the RL-easy half (behavior); starting
from L would discard the one thing we cannot recreate and ask RL for the one thing
it has never delivered, with a KL anchor pinned to L's *inverted* confidence.

**Hypothesis.** GRPO v3 on the K base yields a single model that (a) RETAINS K's
stated-confidence calibration (AUROC→appropriateness ≥0.62, std ≥0.10, cell means
correctly ordered, ECE <0.30) and (b) REPAIRS behavior to pass the clean-SFT
behavior gate that K failed. If so, it is the first cell in the entire thread to
achieve coherent stated-confidence calibration AND behavior.

## 2. Relationship To Existing Protocols

- PROTOCOL v0.3 — locked plain-answer headline matrix. Untouched.
- Amendment E — clean-SFT base/cell. Untouched.
- Amendment J — GRPO v3 on the clean-SFT base + its (mostly negative) disposition
  stay on record. This cell is the same reward on a different base, reported
  separately; do not pool with J, the clean-SFT base, or the v0.3 headline matrix.
- Amendments K / L — the contrastive cells and their dispositions stay on record.
  This cell consumes the K merged base read-only as the GRPO starting point.
- Amendment M (quantile-balanced probe-distilled SFT) — ON HOLD. M tried to make a
  single SFT do both halves; K already did the calibration half, so the GRPO-on-K
  route is the more direct path to coherence and takes priority. M is not
  withdrawn; it remains a fallback if this cell's falsifier triggers.

## 3. Design Change

**No new code.** The reward (`experiment/phase1/grpo/humility_reward_v3.py`) and
all hyperparameters are reused from Amendment J unchanged. The v3 reward already
contains both halves this cell needs:

- a **dominant behavior term** (`_behavior_reward`): `known_correct +2.0`,
  `known_wrong −0.8`, `known_over_refusal −2.0`, `unknown_abstain +1.2`,
  `unknown_answer −1.2`, … — this is what repairs K's behavior; and
- a **proper-scoring confidence term** (Brier vs realized appropriateness,
  `confidence_weight 1.2`, `target_mode "group"`) — this is what preserves and
  reinforces K's calibration.

The two new configs are byte-identical to the Amendment J configs except for
`model.model_name` (→ K merged base) and `training.output_dir`:

- `experiment/phase1/grpo/configs/grpo_schema_contrastive_sft_merged_seed1_v3_smoke.yaml`
- `experiment/phase1/grpo/configs/grpo_schema_contrastive_sft_merged_seed1_v3_full.yaml`

K merged base (read-only GRPO start):
`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/merged-16bit`.

GRPO dataset, LoRA config, beta (0.1), LR (5e-6), batch (32), num_generations (4),
temperature (1.35), epochs (1) — all identical to J.

### 3.1 Why no new reward is needed

The earlier plan to write a behavior-repair reward was unnecessary: v3's behavior
term already rewards correct-on-known and penalizes over-refusal directly and
strongly. On the clean base those terms only *preserved* good behavior (there was
nothing to repair); on K they have a broken behavior to *repair* and the room to
do it (over_refusal 79% → target ≤67.5). Reusing v3 unchanged also makes the run
the cleanest possible test of the "base was the cause" diagnosis: J and N differ in
exactly one field.

### 3.2 The tension to watch (beta)

The KL-to-K anchor does double duty: it protects K's calibration (wanted) and also
resists moving away from K's broken behavior (unwanted). beta therefore trades
calibration-preservation against behavior-repair. beta=0.1 (the J value) is the
first shot: soft enough that the behavior reward (magnitude 2.0 ≫ 0.1·KL) can move
behavior, while still anchoring confidence to K's discriminating reference, which
the proper-score reward independently reinforces. The smoke gate (§4.1) reads
whether this balance holds before the full run commits.

### 3.3 Authorized tuning knobs

If the smoke shows the balance is off, the following may be adjusted WITHIN this
amendment without a new signature (they do not change the cell's identity or
gates), with each change recorded in the session note:

- `training.beta` (raise toward ~0.4 if calibration drifts; lower toward ~0.05 if
  behavior will not move);
- the `humility_reward_v3.RewardConfigV3` behavior magnitudes / `confidence_weight`
  (raise behavior magnitudes if behavior will not move; the proper-score weight if
  spread softens).

Defaults match J exactly for the first shot. Any change beyond these knobs (reward
form, dataset, base, LoRA targets) requires a new signed amendment.

## 4. Launch Sequence And Gates

1. **chmod 777** the smoke + full output dirs (container uid 1001 vs host uid 1000,
   the documented 9P/permissions gotcha).
2. **Smoke** (`..._smoke.yaml`, max_steps 12, `GRPO_REWARD_DEBUG_PATH` set):
   exit 0; reward variance present; smoke gate §4.1.
3. **Full** (`..._full.yaml`, 1 epoch ≈ 1861 optimizer steps): exit 0; adapter +
   lineage. (OOM contingency: resume from latest checkpoint with the run-timestamp
   pin, as for the J/K/L runs.)
4. **Eval** the GRPO adapter applied on the K merged base via vLLM
   (`eval_amendment_n_..._full_local_4b.yaml`, corrected-base pattern) on SelfAware
   + `calibration_gap_report.py`.

### 4.1 Smoke gate (cheap go/no-go before the full run)

From the reward-debug rows over the 12 smoke steps:

- emitted `response_confidence` std does NOT collapse off K's base — stays
  meaningfully spread (heuristic: still > ~0.10, not trending toward a constant);
- the behavior reward is live (reward variance across completions, behavior terms
  firing on known/unknown rows).

If confidence std collapses within 12 steps even on the K base, **stop before the
full run** — that is the falsifier (§4.3) arriving cheaply.

### 4.2 Calibration gate (must RETAIN) + behavior gate (must REPAIR)

Both gates evaluated on the full SelfAware eval, apples-to-apples vs K.

**Calibration (RETAIN — reuse the K/§4.1 bar):**
- emitted AUROC→appropriateness ≥ **0.62**;
- emitted std ≥ **0.10**;
- ECE-vs-appropriateness < **0.30**;
- cell means ordered: known_correct_answered > known_answered_wrong AND
  unknown_refused > unknown_answered_wrong.

**Behavior (REPAIR — the clean-SFT bar K failed):**
- truthful_pct ≥ **35.6**;
- correct_on_known_pct ≥ **42.2**;
- over_refusal_pct ≤ **67.5**;
- refusal_recall_pct ≥ **82.0**.

### 4.3 Success condition and falsifier

- **SUCCESS:** both gates PASS → first coherent-humility cell (calibration AND
  behavior). Then (optional, separate amendment) re-probe L35 to confirm the
  emitted scalar now tracks the internal doubt projection (internal→stated
  coherence), and report as the headline of the calibration-gap line.
- **PARTIAL:** calibration retained, behavior improves but misses one gate →
  tune beta / behavior magnitudes within §3.3 and re-run; report the
  calibration-vs-behavior frontier.
- **FALSIFIER:** calibration COLLAPSES on the K base too (AUROC → ~0.52, std → K's
  value lost) → the confidence collapse is intrinsic to the verbalized-token
  channel / KL dynamics and is NOT a base artifact. That redirects the program to a
  dedicated confidence head / regression readout (an engine change under a further
  amendment), and revives Amendment M only as a secondary SFT probe.

## 5. Implementation Boundary

In scope: the two GRPO YAML configs (clones of J, base + output_dir changed); one
eval config; the smoke/full runs (reusing the unchanged v3 reward); merge-free
adapter eval + `calibration_gap_report` + behavior gate; session-note checkpoints.
No change to PROTOCOL v0.3, Amendment E artifacts, the clean-SFT base, Amendment J,
the K/L artifacts, or `synaptic-tuner` (no engine change required).

## 6. Sign-Off Checklist

- approval date: 2026-06-28
- approved scope: one local seed-1 cell `schema_contrastive_sft_grpo_v3_seed1`
  (GRPO v3 reward on the Amendment K merged base), trained to completion, local 4B
  lane; two GRPO configs + one eval config; no new code
- approved base: Amendment K merged-16bit (read-only GRPO start)
- excluded: any change to PROTOCOL v0.3 headline matrix, Amendment E artifacts, the
  clean-SFT base, Amendment J, or the K/L artifacts
- gates frozen: yes (§4.2 calibration-RETAIN + behavior-REPAIR; §4.1 smoke gate)
- authorized tuning knobs (no new signature): beta, v3 reward magnitudes /
  confidence_weight (§3.3), each logged in the session note
- risk acknowledged: yes (beta trades calibration-preservation against
  behavior-repair; falsifier = intrinsic channel collapse → confidence-head route)
- authorization: user, 2026-06-28 — "get this running I think it's worth a shot"

## 7. Result — seed 1, beta 0.1 (2026-06-28)

Cell `schema_contrastive_sft_grpo_v3_seed1` ran to completion (1 epoch, 1861
steps, ~8h55m). GRPO LoRA evaluated on the K merged base via vLLM (greedy, temp 0,
n=1) on SelfAware OOD; `calibration_gap_report.py` + behavior metrics.

Artifacts: adapter
`scratch/.../runs/schema_contrastive_sft_grpo_v3_seed1_full/20260628_093753/final_model`;
scored rows `experiment/phase1/eval/results_amendment_n_..._4b/grpo_v3_on_contrastive_sft_seed1__selfaware/`;
training reward debug `scratch/.../runs/grpo_on_k_full_debug.jsonl`.

**§4.2 verdict: Calibration RETAIN ✅ PASS (4/4) · Behavior REPAIR ❌ FAIL (2/4) →
PARTIAL (§4.3).** The falsifier is **NOT** triggered.

| Gate | Threshold | Got | Verdict |
|------|-----------|-----|---------|
| AUROC emitted→appropriateness | ≥ 0.62 | 0.646 | ✅ |
| emitted std | ≥ 0.10 | 0.311 | ✅ |
| ECE vs appropriateness | < 0.30 | 0.214 | ✅ |
| cells ordered (incl. unknown_refused > unknown_wrong) | — | 0.542 > 0.138 | ✅ |
| truthful | ≥ 35.6 | 31.91 | ❌ |
| correct_on_known | ≥ 42.2 | 50.46 | ✅ |
| over_refusal | ≤ 67.5 | 90.76 | ❌ |
| refusal_recall | ≥ 82.0 | 93.6 | ✅ |

Per-cell emitted means are cleanly monotone:
`known_correct 0.724 > known_refused 0.412 ≈ known_wrong 0.424 > unknown_wrong 0.138`,
and `unknown_refused 0.542 > unknown_wrong 0.138` — the exact ordering Amendment L
**inverted** is now strongly correct. Calibration survived the policy moving well
off K (training KL drifted to ~0.97, yet emitted std held at ~0.31). **The
base-was-the-cause diagnosis is confirmed for the calibration half: K is the
correct calibration substrate and GRPO RETAINS + sharpens it.**

**Why behavior did not repair (grounded in the reward debug, not inferred).**
Invalid-JSON was ruled out (94–97% valid for both answer and refuse at temp 1.35).
The driver is a **sampled-vs-greedy gap**: during training the reward was working
as designed — known→answer mean reward **+0.46** vs known→refuse **−1.28**;
unknown→refuse **+2.10** vs unknown→answer **+0.42** — and the policy **answered
knowns ~75%** of the time in rollouts (24016 answer / 7908 refuse). But the
**greedy** eval refuses knowns **91%** (answered 216 / 2337). The reward lifted
answer-probability *mass*, but the **KL anchor to K (beta 0.1) held the argmax at
K's over-refusing mode** (K base over_refusal 79% → N greedy 91%, i.e. worse). The
behavior reward is not too weak; the greedy decode has not followed it.

**Disposition: §4.3 PARTIAL.** Pre-stated routing was "tune beta / behavior
magnitudes within §3.3 and re-run." Tier-3 authorized-knob re-run logged in the
session note: **beta 0.1 → 0.05** (single variable; reward UNCHANGED — magnitudes
left intact precisely because the debug shows they are already correctly shaped, so
lowering beta is the grounded lever for the sampled-vs-greedy gap, and it least
risks the calibration we must RETAIN). Config
`experiment/phase1/grpo/configs/grpo_schema_contrastive_sft_merged_seed1_v3_beta005_full.yaml`.
Re-run gate = the same §4.2 dual gate (no goalpost change). If beta 0.05 still
leaves greedy behavior anchored, the next reading is that the gap is intrinsic to
argmax-vs-expectation decode (a real finding), pointing to a decode/objective
change rather than more beta steps.

## 7.1 Re-run result — seed 1, beta 0.05 (2026-06-29)

Tier-3 authorized-knob re-run (β 0.1 → 0.05, single variable; reward UNCHANGED),
lab-notebook tier under §3.3 — NOT a new amendment, NO goalpost change. Cell
`schema_contrastive_sft_grpo_v3_beta005_seed1` ran to completion (1 epoch, 1861
steps, 6h32m). The lower KL anchor did what it was supposed to: train-time KL
roughly doubled (~0.97 → ~1.91), so the policy moved markedly further off K. Same
greedy SelfAware eval, same gate.

Artifacts: adapter
`scratch/.../runs/schema_contrastive_sft_grpo_v3_beta005_seed1_full/20260629_010141/final_model`;
scored rows `experiment/phase1/eval/results_amendment_n_beta005_..._4b/grpo_v3_beta005_on_contrastive_sft_seed1__selfaware/`;
training reward debug `scratch/.../runs/grpo_on_k_beta005_resume_debug.jsonl`
(steps ~501–1861; the run resumed from checkpoint-500 after a step-832
diagnostic-writer crash, fixed lab-notebook-tier — lone-surrogate `\ud83d` from a
degenerate low-β completion broke the debug JSONL write; `ensure_ascii=True` +
non-fatal wrap, 2 regression tests).

**§4.2 verdict: Calibration RETAIN ✅ PASS (4/4) · Behavior REPAIR ❌ FAIL (2/4) →
PARTIAL (§4.3) — a near-exact overlay of β=0.1.** Lowering KL by half changed
nothing material:

| Gate | Threshold | β=0.1 | β=0.05 | Verdict |
|------|-----------|-------|--------|---------|
| AUROC emitted→appropriateness | ≥ 0.62 | 0.646 | 0.648 | ✅ |
| emitted std | ≥ 0.10 | 0.311 | 0.312 | ✅ |
| ECE vs appropriateness | < 0.30 | 0.214 | 0.212 | ✅ |
| cells ordered (unknown_refused > unknown_wrong) | — | 0.542 > 0.138 | 0.557 > 0.132 | ✅ |
| truthful | ≥ 35.6 | 31.91 | 31.91 | ❌ |
| correct_on_known | ≥ 42.2 | 50.46 | 49.55 | ✅ |
| over_refusal | ≤ 67.5 | 90.76 | 90.59 | ❌ |
| refusal_recall | ≥ 82.0 | 93.6 | 93.6 | ✅ |

**Pre-registered margin falsifier — TRIGGERED.** The re-run pre-stated (Paper 3 §7,
before the result) that the answer-rate margin P(answer|known) − P(answer|unknown)
must open to ≥ ~14.5 pts (the separation the behavior gate implies) or the
action/knowledge decoupling is recorded as **structural**:

| | β=0.1 (greedy) | β=0.05 (greedy) | threshold |
|---|---|---|---|
| action margin P(ans\|known) − P(ans\|unknown) | +2.85 pts | **+3.02 pts** (z=2.90, p=0.004) | ≥ ~14.5 |

Halving the KL anchor moved the action margin by **0.17 pts**. The
training-trajectory margin (1361 logged steps, 6 bins) stays in a +5–9 pt band
(+5.1 → +7.2 → +8.5 → +9.4 → +7.5 → +8.6) and never trends toward opening. The
action stayed a global-propensity knob regardless of KL pressure.

**Disposition: STOP tuning β.** The β knob was the one lever that could have
explained the action decoupling as a KL artifact (the policy pinned to K's
over-refusing argmax). It demonstrably loosened the policy and the action margin
did not move. The decoupling is **structural**: "calibrated confidence,
uncalibrated action" / "says but doesn't act" is a property of the
objective+decode, not of the KL anchor. This closes the §4.3 PARTIAL→tune-and-rerun
path. The program redirects to the implied experiment — **distill the model's own
internal doubt axis (ECE 0.004) into the stated channel and supervise the
answer/abstain action against it directly** — which is a new objective/engine
change and belongs to a future amendment, not more β steps under N.
