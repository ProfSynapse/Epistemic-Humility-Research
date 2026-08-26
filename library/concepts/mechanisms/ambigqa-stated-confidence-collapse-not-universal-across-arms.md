---
title: ambigqa-stated-confidence-collapse-not-universal-across-arms
aliases:
- G5 FAIL, stated-confidence collapse does not transfer uniformly
- two of five arms show real emitted-confidence spread on AmbigQA
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ambigqa-stated-confidence-collapse-not-universal-across-arms
  type: mechanism
  status: canonical
cause: "In ood-breadth-beyond-selfaware (paper-3 limitations burn-down item 26), the registered G5 gate required every surviving arm to show emitted AUROC to appropriateness <= 0.65 AND emitted standard deviation <= 0.10 on the AmbigQA behavior surface, mirroring paper 3's SelfAware finding of a near-constant, collapsed stated-confidence scalar (AUROC 0.52-0.56, std about 0.015 on the held-in known set). The five arms surviving the registered G1 re-merge-parity void (A1, A3, A4, A5, A8; A2/A6/A7 voided) were scored against both conditions."
effect: "G5 FAILS as registered: A1 (0.6023/0.0490), A4 (0.4530/0.0106) and A5 (0.5007/0.0274) pass both conditions, but A3 (0.3953/0.1687) and A8 (0.3588/0.4238) pass the AUROC leg while failing the std ceiling. Two of five surviving checkpoints show real emitted-confidence spread on AmbigQA that paper 3's SelfAware-derived collapse does not predict, though the spread carries no positive appropriateness signal on either arm (both rank below chance). The registered falsifier for the cell (>=2 arms at AUROC >=0.70 together with std >0.15) does not fire, since neither high-std arm clears the 0.70 AUROC bar, so paper 3's \"collapsed near-constant\" sentence is not falsified outright, but it is not universal off SelfAware and needs a variance qualifier wherever the collapse is described without surface scope."
polarity: complicates
related:
- '[[ood-breadth-beyond-selfaware]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[verbalized-confidence]]'
- '[[selfaware]]'
- '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
relationships:
- type: supported_by
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/NOTEBOOK.md 2026-08-09T16:45Z
    Stage 8 (G5 verdict, per-arm AUROC/std pairs)"
- type: related_to
  target: '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
  target_id: mechanism:pstruct-stated-confidence-miscalibrated-near-chance
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Design (same
    AmbigQA stated-confidence channel and rows as this mechanism's surface,
    now scored under the structure-only P-struct contract for calibration
    and discrimination rather than variance)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 329-337 (the
    SelfAware collapse this gate mirrors and qualifies)"
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/AMENDMENT.md Rendering and
    scoring (the emitted-scalar channel scored by G5 is a verbalized-confidence
    instance byte-identical to paper 3's pipeline)"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: medium
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/gates.yaml g5 derivation (0.65/0.10
    thresholds derived from paper 3's SelfAware emitted-scalar levels)"
---

A secondary but registered finding from `ood-breadth-beyond-selfaware`
(paper-3 limitations burn-down item 26): paper 3's SelfAware finding that the
model's stated confidence collapses to a near-constant, weakly discriminating
scalar does not hold uniformly once the surface changes. On AmbigQA, three of
the five surviving arms replicate the collapse, but two (A3, A8) show
standard deviations of 0.1687 and 0.4238, well above the 0.10 ceiling derived
from paper 3's SelfAware levels. Neither arm's spread is useful signal (both
rank below chance on appropriateness), so this is variance without
discrimination, not a second working confidence channel.

**Why it matters here:** this keeps the registered falsifier from firing
(which needed high AUROC alongside high variance, not variance alone) while
still obliging a scope qualifier: paper 3's stated-confidence-collapse
language, wherever it is used as a universal claim rather than a SelfAware-
scoped one, needs the caveat that emitted-confidence variance is
surface-dependent even though its discriminative uselessness so far is not.

**Lineage:** secondary finding of [[ood-breadth-beyond-selfaware]], resolved
2026-08-09, alongside the headline
[[ambigqa-internal-readout-does-not-transfer-from-selfaware]] result from the
same Stage 8 adjudication. Source of truth:
`experiments/ood-breadth-beyond-selfaware/NOTEBOOK.md`, Stage 8 entry,
2026-08-09T16:45Z.
