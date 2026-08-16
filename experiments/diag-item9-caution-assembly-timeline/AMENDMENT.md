# Diagnostic Item 9 - Caution Assembly Timeline

Status: historical lab-notebook diagnostic. This is an imported diagnostics
bundle result, not an amendment and not a confirmatory claim.

Naming note (2026-08-16, PI directive): this slug and this document's prose
predate the program vocabulary rename recorded in
`papers/common/terminology.md`. The slug is a LEGACY name kept verbatim per
that file's usage rule 1. In running prose the constructs are now: doubt
direction/axis/readout -> known-unknown (KU) direction / KU (answerability)
readout; doubt gate -> KU readout gate; doubt-coupling -> KU-readout
coupling; caution direction (refuse-vs-answer contrast among knowns) ->
refusal axis; caution write -> IDK switch (validated actuator only) or
boundary push (other dosed writes). Registered text below stays verbatim
as signed.

Question: how does the known-vs-unknown caution/answerability readout develop
across the raw base, clean-SFT, clean-SFT + GRPO-v2, and clean-SFT + PAR-true
training stages?

Instrument: `experiments/diag-item9-caution-assembly-timeline/diag_item9_caution_timeline.py`, reading
the full-stack pre-generation anchor extractions produced by the diagnostics
bundle cloud wrapper. Probe discipline was PCA-128 plus saga logistic
regression, 5-fold out-of-fold AUROC, seed 20260705.

Result: the answerability/caution readout is already strong in the raw model and
remains high across later stages. Direction rotation is large from raw to
clean-SFT in mid/late layers, then much smaller across GRPO-v2 and PAR-true.
The committed table is
`analysis-committed/diag_item9_caution_timeline.md`.

Verdict: exploratory timeline banked as historical provenance; no gates, no
amendment verdict, and never pooled with the locked Phase 1 matrix.
