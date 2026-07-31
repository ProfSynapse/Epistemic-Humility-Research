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
  or more at ANY c_hat-dosed arm (a_dose_0p5, a_dose_1; the naming battery's
  own axis-G leg, reused as an upper bound), i.e. the dose response remains
  mode switching, not graded marking. The placebo arm's share comparison is
  reported non-gating (build-time ruling 2, below): it doses a random
  direction, not the actuator, and its registered claim is N3.
- N3 (direction specificity): the placebo arm's F4 rate stays within a
  registered band of the fresh baseline rate.

All three pass: the name IDK switch is EARNED for this actuator at this
operating point, recorded in the KG as a named actuator node. Any gate
fails: name not earned, resolution records which claim broke.

## Build-time rulings (lead, 2026-07-31, pre-sign)

Recorded here so no ruling lives only in code comments or a subagent report.

1. Decode mode: SAMPLED, at the program's registered sampled-decode standard
   (do_sample=true, temperature=0.7, top_p=0.9, num_beams=1, RNG seeded per
   run), read from `experiments/sampled-decode-seed-robustness/AMENDMENT.md`
   "Seeds and decode (LOCKED)" and previously adopted by
   `snap-seed-sampled-decode-replication` for exactly this genre of
   fresh-seed hardening. Rationale: the naming battery generated greedily,
   and under greedy decode a fresh sampling seed is a no-op, so the
   registered replication axis (fresh sampling seeds) REQUIRES sampled
   decode. The actuator operating point (direction, layer, dose law,
   standardization) is unchanged; the decode change is a disclosed deviation
   from the naming battery's generation config, and all gates are set on the
   fresh sampled generations only (the fresh a_baseline arm is the
   comparator everywhere, so no greedy-vs-sampled comparison is ever gated).
2. N2 scope: gated arms are the c_hat-dosed arms only (a_dose_0p5,
   a_dose_1). The placebo arm's share-vs-baseline comparison is computed and
   reported, non-gating.
3. Container provenance: captured by re-invoking the runner image's own
   `print_provenance.py` (its documented downstream pattern), hard-failing
   unless the reported image digest is a real sha256 equal to
   `instrument.runtime_image_digest` pinned at sign. The builder's original
   best-effort env-var/file probe was replaced after the lead read the real
   entrypoint contract (`synaptic-tuner/docker/mechinterp-runner/`).
4. Runlog redaction: `redact_fields: []` (full rows retained in gitignored
   `analysis/runlog/`). Deviation from the naming battery's
   redact-then-rebuild-sidecar pattern, accepted because this cell knows up
   front its judge lane needs generation text; containment is satisfied by
   the gitignore boundary, and nothing text-bearing is ever committed.
5. Direction paths: `cell.yaml` readout paths corrected to the committing
   cell (`qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/`);
   the naming battery never committed a `directions/` tree. The sha256 pins
   were already correct and are unchanged (lead re-verified both).
6. Seeds: proposed generation_sampling_seed 20260802 and judge-pool seed
   20260803, binding at sign. The naming battery's registered seeds
   (48260730/48260731/48260732) are hard-excluded fail-closed in
   `pipeline.py`; form-judge's grading seeds are a different instrument and
   are avoided as hygiene, not registered exclusion. The builder's original
   pool-seed placeholder (20260731, form-judge's VOIDED attempt-1 seed) was
   replaced by the lead.

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

**Verdict (2026-07-31): all three name-earning gates PASS on the fresh
generations; the name IDK switch is EARNED for this actuator at the pinned
Qwen3.5-4B hs20 operating point.**

Run: 1600/1600 fresh generations (4 arms x 400 rows, sampled decode
temperature 0.7 top_p 0.9, generation_sampling_seed 20260802, image
sha256:45847a60...), no resume gaps, F5 degenerate 1/1600.

Gate results, adjudicated by the lead against the floors pinned in
gates.yaml at sign:

- N1 (IDK endpoint jump) PASS: a_dose_1 F4 explicit-IDK 260/400 = 0.6500
  vs fresh a_baseline 15/400 = 0.0375; diff +0.6125; primary paired
  bootstrap 95% CI [0.5650, 0.6600]; Newcombe cross-check
  [0.5591, 0.6599]. CI lower bound clears the 0.15 floor by 3.8x. The
  naming battery's exploratory +0.6275 replicates at +0.6125 under fresh
  sampling seeds and sampled decode.
- N2 (no graded intermediate) PASS: judged F2+F3 hedged share among
  non-degenerate rows, baseline 0.4150; a_dose_0p5 0.2600 (delta -0.1550),
  a_dose_1 0.1629 (delta -0.2521). Neither gated arm rises 0.10 over
  baseline; the hedged share falls monotonically with dose, the registered
  mode-switching signature. NOT-ADJUDICABLE guard clear (graded non-F4
  rows 237 and 139, both >= 50). Non-gating: a_placebo_1 share 0.4000
  (delta -0.0150).
- N3 (placebo band) PASS: |a_placebo_1 F4 0.0150 - a_baseline 0.0375| =
  0.0225, inside the 0.05 band. Non-gating bootstrap diff CI
  [-0.0425, -0.0025].

Judge-lane validity (all registered steps in registered order): pool
hashes committed before grading (21 shards, 1155 core + 25 embedded
clear-positive decoys); 21 fresh context-free opus-tier judges;
graded-file hashes committed before unblind; in-run decoy agreement
25/25 = 1.0000 (floor 0.92); lead spot-check 30/30 before gate
arithmetic; stability regrade shard (isnc_fullpool_shard_04) flip rate
4/56 = 0.0714, non-gating.

Neither named falsifier alternative fired: the judge lane was valid
(decoys perfect, so not instrument-failed) and the fresh generations
passed acceptance (no resume gaps, 1 degenerate row, so not
generation-failed).

One-sentence summary (manifest `verdict:`): fresh-seed sampled-decode
replication passes all three registered name-earning gates (N1 endpoint
jump +0.6125 CI lower 0.5650 vs floor 0.15; N2 hedged share falls at
both dosed arms; N3 placebo inside band); the name IDK switch is EARNED
at the Qwen3.5-4B hs20 operating point.
