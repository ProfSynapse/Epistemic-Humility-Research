---
title: detector-v2-overfires-on-random-arm-text
aliases:
- detector_v2 over-fires on hedged or degenerate random-arm text
- judge-sensitivity failure tracked the decoy source, not the judges
- clear-positive decoy soundness depends on source arm
tags:
- kg/mechanism
- concept
- mechanism
- instrumentation
kg:
  id: mechanism:detector-v2-overfires-on-random-arm-text
  type: mechanism
  status: canonical
cause: "Clear-positive judge-calibration decoys are drawn from rows the frozen detector_v2 pattern instrument marks refused, sourced from random-direction or no-abstention-prompt arms (hedged or degenerate steered text), versus from with-prompt gated-arm overt refusals (experiments/no-abstention-prompt-gated-replication judge lanes, v1 vs v2)."
effect: "Context-free blind judges reject random/no-prompt-arm detector-refused rows en masse while catching clear negatives perfectly: llama's 6 native random-arm positives were caught 0/6 across two independent attempts and qwen3.5-4b's 20 random-arm positives were missed on 40-80% per shard (both v1 lanes VOID_CELL_TERMINAL under the registered cascade), while with-prompt gated-arm overt-refusal decoys from the same instrument definition were caught 79/80 across four families. The sensitivity failure tracks the decoy source, not the judges: detector_v2's patterns fire on hedged or degenerate random-arm text that a semantic reader does not classify as abstention, so detector-only abstention counts on random-arm or no-prompt text should be read as an upper bound, and clear-positive decoy pools must be sourced from overt refusals."
polarity: complicates
related:
- '[[no-abstention-prompt-gated-replication]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[abstention-instruction-amplifies-the-gated-write]]'
relationships:
- type: supported_by
  target: '[[no-abstention-prompt-gated-replication]]'
  target_id: experiment:no-abstention-prompt-gated-replication
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md#outcome
    (Descriptive finding 3; G1b and G3 instrument disclosures)
  - experiments/no-abstention-prompt-gated-replication/NOTEBOOK.md (v1
    VOID_CELL_TERMINAL records and the v2 pre-statement)
- type: related_to
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/cell.yaml
    (grading.pinned_instrument; detector_v2 and the decoy-carve definitions
    are that cell's pinned instruments, reused unmodified)
---

# detector_v2 over-fires on hedged or degenerate random-arm text

An instrumentation finding, not a behavioral claim: the pattern detector's
refused==True on random-direction-arm or no-prompt-arm text frequently does
not survive semantic review, while the same instrument's hits on with-prompt
gated-arm text do. Consequences for future cells: (1) source clear-positive
judge-calibration decoys from overt refusals, never from random-arm detector
hits; (2) treat detector-only abstention rates on steered or no-prompt text
as upper bounds pending judge confirmation; (3) a VOID_CELL_TERMINAL on
clear-positive agreement can indicate unsound decoys rather than insensitive
judges, and the two are distinguishable by re-running with decoys of known
soundness, as the v1/v2 contrast here did.
