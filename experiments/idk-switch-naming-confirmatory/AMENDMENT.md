# idk-switch-naming-confirmatory

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`write-direction-naming-battery` resolved falsified (no name earned;
instrument void on axis G) and `form-judge-axis-g-rescore` then answered the
open axis with a validated instrument: axis G is BINARY. The caution write at
the pinned Qwen3.5-4B hs20 operating point converts prose output of every
form, committed and hedged alike, wholesale into explicit IDK (F4 screen rate
16/400 at baseline rising monotonically to 267/400 at 1.0x), with the hedged
share falling monotonically and the placebo arms flat. The PI adopted the
working label "IDK switch" for this actuator (2026-07-31) and directed a
confirmatory run so the label can be promoted to an earned name.

Posture: CONFIRMATORY naming cell under the standing promotion rule (an
exploratory win becomes a claim only via a confirmatory replication
registered before running). The replication axis is FRESH SAMPLING SEEDS:
the naming battery's Arm A consumed the entire registered P_CONFAB
population (400 rows), so no held-out row draw exists without re-running the
upstream confab screen; fresh-seed regeneration on the same registered rows
at the same pinned operating point is the registered axis, and a held-out-row
replication remains available as a future strengthening if the upstream
screen is ever re-run. All exploratory evidence (every naming-battery and
form-judge number) is disclosed as seen; the gates below are set on the
fresh generations only.

The name is earned ONLY if every gate passes. On any failure the name is not
earned, the working label remains descriptive lowercase, and there is no
rescoring or gate softening; a successor registration would be required.

## Design

Substrate: Qwen3.5-4B at the naming battery's pinned operating point (frozen
mid-band hs20 c_hat write direction, same dose calibration), regenerating
with a FRESH registered sampling seed (pinned in cell.yaml at sign, distinct
from every seed the naming battery used). Rows: the same 400 registered
P_CONFAB rows (source kuq_unknowns_all), disclosed as spent for exploratory
purposes; the fresh generations have never been sampled, screened, or graded.

Arms (reduced ladder, 4 x 400 = 1600 generations): a_baseline, a_dose_0p5,
a_dose_1, a_placebo_1. The reduced ladder is sufficient because the
name-earning claims quantify the switch at the endpoint, absence of a graded
intermediate at mid-dose, and direction specificity; the full five-rung
exploratory ladder is not re-run.

Instruments, all pinned at sign: the naming battery's validated F5
(degenerate) and F4 (explicit IDK via semantic_refuse / refused_v2) screens,
and the form-judge cell's validated blinded judge lane (pinned judge prompt
bytes, sharded context-free opus-subagent judges, salted opaque ids, pool
hash committed before grading, per-shard graded hashes committed before
unblind, positional join). Judge-lane in-run validity is gated by
clear-positive decoys per the standing protocol (floors at sign, sized to
counted candidates from the FRESH generations' own F4 screen positives); the
instrument's construct validation carries over from form-judge (G1 0.035 on
this same text distribution) and is disclosed, not re-earned. One stability
regrade shard, reported non-gating. Lead spot-check n=30 before any gate
adjudication.

Execution lane (PI decision, 2026-07-31): the LOCAL 3090 GPU, not a cloud
lane. Per the standing local-runtime invariant, every GPU verb runs inside
the pinned mechinterp runner container (image digest recorded as
instrument.runtime_image_digest at sign, a sibling of instrument.pins), and
the container entrypoint's provenance JSON line must appear in the run log.
Qwen3.5-4B fits the 3090's 24 GB comfortably at generation batch sizes.

## Gates

Name-earning gates; numeric floors registered at sign, never after. The name
"IDK switch" decomposes into three registered claims, each gated on the
fresh generations:

- N1 (IDK): the F4 explicit-IDK rate at 1.0x exceeds the fresh a_baseline F4
  rate by a margin whose CI excludes a floor set at sign (exploratory
  reference: 0.04 to 0.67; the floor will be set far below that reference
  but above noise).
- N2 (switch, no graded intermediate): the judged F2+F3 hedged share among
  non-degenerate rows does not rise above the fresh baseline share by 0.10
  or more at ANY dosed arm (the naming battery's own axis-G leg, reused as
  an upper bound), i.e. the dose response remains mode switching, not graded
  marking.
- N3 (direction specificity): the placebo arm's F4 rate stays within a
  registered band of the fresh baseline rate.

All three pass: the name IDK switch is EARNED for this actuator at this
operating point, recorded in the KG as a named actuator node. Any gate
fails: name not earned, resolution records which claim broke.

## Prediction

All three gates pass: the fresh-seed replication reproduces the mode switch
(F4 endpoint jump, no graded intermediate, placebo flat), and the name is
earned.

## Falsifier

Any name-earning gate fails on the fresh generations. Named alternatives
that are neither prediction nor falsifier: instrument-failed (judge-lane
in-run decoy floors missed; N2 unadjudicable, while N1/N3 remain adjudicable
from the deterministic screens alone and are reported), and generation-failed
(fresh-seed generations fail their own acceptance checks; nothing
adjudicated).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | All three gates pass; name earned |
| user | Aligned (stated 2026-07-31, formally registered at sign): all three gates pass; the name IDK switch is confirmed |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
