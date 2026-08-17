# Prompt-crossing held-out confirmatory: promoting the paper-2 prompt-condition claims on out-of-distribution surfaces

Status: SIGNED (2026-08-17, PI approval in-conversation). Instrument pinned; run not started. Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 2 Section 4.2 rests on three prompt-side findings that are currently
exploratory tier: the prompt-vs-training panel
(`experiments/prompt-vs-training-panel/AMENDMENT.md`, resolved 2026-08-15) and
its registered fresh-seed replication
(`experiments/prompt-crossing-completion/AMENDMENT.md`, resolved 2026-08-16,
falsifier not fired). Both cells ran on the same SelfAware rows (n=3,369) and
the same Qwen3-4B checkpoints, so the claims are single-model AND
single-dataset. This cell is the registered confirmatory promotion, route:
same model, held-out data. It reuses the screened out-of-distribution
surfaces built and adjudicated by
`experiments/ood-breadth-beyond-selfaware/AMENDMENT.md` (resolved; behavior
transfers in level; KUQ leakage screen already applied there).

Promotion contract: if PH-G1 passes, the three claims below are promoted to
confirmatory tier scoped as "Qwen3-4B, held-out surfaces", reported in paper 2
as a confirmatory companion to the Section 4.2 exploratory table, never pooled
with it and never pooled with the locked headline matrix. If any falsifier
fires, the affected claim stays exploratory and the failure is reported in the
paper with the same prominence as a pass. No goalpost moves after signing.

## Claims under promotion

- C1 (instruction gap at base): an explicit refusal instruction and a soft one
  differ by nearly the entire abstention effect on the untrained base model.
- C2 (SFT internalization signature): only SFT-trained weights carry abstention
  without any prompt affordance (structure-only contract); base, cold DPO, and
  cold KTO carry approximately none.
- C3 (erosion, not erasure): a preference stage applied after SFT reduces but
  does not erase instruction-free abstention.

## Design

Single evaluation campaign, no training. Existing local checkpoints, the
crossing's pinned scorer, greedy decoding, and per-arm full-coverage +
config-sha stamping exactly as in `prompt-crossing-completion`.

Primary gate surface: AmbigQA validation split as retained by the ood-breadth
cell (1,832 rows: 1,002 unknown-labeled, 830 known-labeled; cc-by-sa-3.0; no
training-overlap flags). Secondary descriptive surfaces (no gates, reported
straight): screened KUQ and BIG-bench known-unknowns, two arms only to bound
cost — base and cold SFT seed 1, both under the structure-only contract (the
only contract the secondary breadth serves): 2 arms x 5,586 rows = 11,172
generations.

Arms (20, all on AmbigQA; P-rc = response-confidence contract, P-plain =
plain-answer contract, P-struct = structure-only contract, prompts verbatim
from paper 2 Appendix C):

| # | Checkpoint | Prompt |
|---|---|---|
| 1-3 | base (untrained) | P-rc, P-plain, P-struct |
| 4-6 | cold SFT seeds 1-3 | P-struct |
| 7-9 | cold DPO seeds 1-3 | P-struct |
| 10-12 | cold KTO seeds 1-3 | P-struct |
| 13 | clean SFT (merged) | P-struct |
| 14 | SFT then GRPO seed 1 | P-struct |
| 15-20 | seq SFT-DPO / SFT-KTO seeds 1-3 | P-struct |

~36.6k generations primary + ~11.2k secondary = ~47.8k total; the crossing
cell ran 37k in ~10.5 h wall on the local RTX 3090, scaling to ~13.5 h here.
Budget estimate: 11-14 GPU-hours.

## Prediction

- C1: base P-rc refusal recall minus base P-plain refusal recall on AmbigQA in
  the band 50-90 percentage points (SelfAware exploratory value: 90.9 minus
  0.0).
- C2: every cold SFT seed P-struct recall in 40-80%; base P-struct scored
  recall <= 10%; every cold DPO and cold KTO seed P-struct scored recall
  <= 10%.
- C3: every seq preference arm P-struct recall at 40-100% of its same-seed
  cold-SFT parent's P-struct recall on the same surface.

## Falsifier

Fixed at signing, applied verbatim:

- F1 (kills C1 promotion): base P-rc minus base P-plain gap < 15pp on AmbigQA.
- F2 (kills C2 promotion): any cold SFT seed P-struct recall < 20%, OR base
  P-struct scored recall > 15%, OR any cold DPO/KTO seed P-struct scored
  recall >= 20%.
- F3 (kills C3 promotion): any seq preference arm P-struct recall < 25% of its
  same-seed cold-SFT parent on the same surface (erasure), with the
  parent-relative form registered because absolute held-out levels are not
  anchored by prior evidence.
- Scorer-scope caveat carried from the panel: the pinned markers undercount
  natural-language abstention under P-struct by roughly 4-6pp on SelfAware.
  Scored zeros are read with that audit note; the F2 base threshold (15%)
  already clears it. The scorer is not retuned.

Each claim promotes or fails independently; partial outcomes are reported
per-claim.

## Gates

- PH-G0 (integrity, precondition for any reading): full row coverage on every
  arm; row-stamped config_sha matches pinned config bytes; scorer parse path
  recorded; lead recomputes at least two pivotal arms from raw scored rows.
- PH-G1 (per-claim): prediction bands and falsifiers above, applied verbatim.
  Between falsifier and prediction band lies "partial", reported straight with
  no promotion.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | C1 gap 60-85pp; C2 passes with SFT seeds 45-70%; C3 passes with all six arms above 40% of parent |
| user | approved bands and sign 2026-08-17; no directional call recorded |

## Budget

11-14 GPU-hours local RTX 3090; no cloud, no training, no new data fetch
(surfaces already on disk from the ood-breadth cell).
