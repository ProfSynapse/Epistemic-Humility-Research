---
aliases:
- narrow pattern detector undercounts baseline abstention, margin varies by family
- detector-v2-only baseline reading needs a per-family correction, not a fixed offset
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:detector-v2-undercounts-baseline-abstention-by-family-varying-margins
  type: mechanism
  status: canonical
cause: "Detector v2 (RR2's frozen pattern-match screen, byte-identical pins) is compared against the wide two-instrument stack (detector v2 OR blinded context-free adjudication) on the same UNDOSED baseline confab rows, across three families: Qwen3.5-4B, Llama-3.2-3B-Instruct, and Mistral-7B-Instruct-v0.3 (cited from RR2)."
effect: "The narrow detector-v2-only rate undercounts the wide-instrument baseline rate in every family measured, by a margin that itself varies by family: 6.1 points for qwen (0.044 vs 0.104), 12.9 points for llama (0.036 vs 0.164), and 12.2 points for mistral (0.159 vs 0.280, cited). The undercount is present and substantial everywhere measured, but its size is not constant, so a narrow-detector-only baseline reading cannot be corrected across families by a single fixed offset."
polarity: decreases
related:
- '[[abstention-wide-instrument-calibration]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
- '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Calibration table, Undercount column)
- type: related_to
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: medium
- type: different_from
  target: '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
  target_id: mechanism:undosed-wide-instrument-baseline-abstention-is-family-graded
  confidence: high
  note: "Complementary, not opposing, despite inverse polarity on a similar cause: this atom compares the narrow screen against the wide stack, the target reports the wide stack's own family grading. Both hold on the same run."
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A companion finding to `canonical-phrase-detector-undercounts-cross-family-abstention-idioms`,
measured on a different population and a different narrow instrument:
that mechanism established the undercount on DOSED (peak-write) rows against
the original locked 3-phrase canonical detector, for mistral, with llama
staying robust to the same width-crediting exercise there. This mechanism
measures the UNDOSED baseline population against detector v2 (already wider
than the 3-phrase set) across all three families and finds a substantial
undercount in every one of them, llama included (12.9 points), with the
margin itself varying by family rather than settling to a shared constant.
The two findings are read as related, not identical: narrow-instrument
undercount of abstention is a recurring validity threat whose exact size
depends on the population and instrument pairing being compared, and neither
finding licenses transferring the other's correction offset.
