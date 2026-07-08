# Paper 1 TODO

Status: draft scaffold checklist
Created: 2026-06-18

## Claim Gates

- [ ] Reconcile `archive/papers/retired/results-provenance-inventory.md` against all
  manuscript result tables before promoting any number.
- [ ] Fill the locked v0.3 headline table only from default-config SFT/DPO/KTO
  runs with approved seed treatment.
- [ ] Keep sensitivity-panel numbers out of headline claims; use them only in a
  labeled robustness figure.
- [ ] Keep Amendment A sequential results separate from v0.3 unless a later
  signed v0.4 protocol explicitly supersedes the matrix.
- [ ] Keep Amendment B stated-confidence results labeled as prompt-contract
  evidence, not as plain-answer replacement evidence.
- [ ] Keep Phase 3 hidden-state and causal-pilot evidence labeled exploratory
  unless a later signed protocol promotes it.

## Provenance Reconciliation

- [ ] For every candidate table row, record run ID, seed, config path, adapter
  path or model identity, eval config, result directory, and scored-row status.
- [ ] Resolve the Amendment A clean DPO seed-2 provenance and exclude the bad
  merge attempt from publication-grade aggregates.
- [ ] Resolve the Amendment A DPO refusal-recall aggregate discrepancy noted in
  `experiment/phase1/eval/analysis/amendment_a_transition_report.md`.
- [ ] Confirm whether all v0.3 required headline seeds are complete and
  reportable for SFT, DPO, and KTO.
- [ ] Confirm whether 8B confirmation and bridge replication are complete,
  partial, or not yet claim-bearing.
- [ ] Verify that any row-level transition table aligns rows by stable eval-set
  and row identity, not by incidental ordering alone unless documented.

## Tables and Figures

- [ ] Table 1: v0.3 headline default-config metrics by arm, with seed-level CI
  and provenance pointers.
- [ ] Figure 1: refusal recall versus over-refusal tradeoff for base, SFT, DPO,
  and KTO.
- [ ] Figure 2: seed-level variation for headline arms.
- [ ] Figure 3: sensitivity panel, explicitly labeled robustness-only.
- [ ] Table 2: Amendment A sequential results, labeled prospective extension.
- [ ] Figure 4: row-level transition counts for `SFT -> DPO` and `SFT -> KTO`.
- [ ] Table 3 or appendix: Amendment B stated-confidence prompt-contract
  results, with confidence coverage.
- [ ] Appendix table: hidden-state diagnostic readout and causal-pilot smoke
  status.

## Manuscript Writing

- [ ] Replace abstract gated paragraph with reconciled v0.3 headline result.
- [ ] Tighten Introduction after final headline result is known.
- [ ] Convert Related Work TODOs into citation-complete prose.
- [ ] Add exact hypothesis readout for H1-H4 from locked v0.3 only.
- [ ] Add H5 readout separately for Amendment A.
- [ ] Add a short measurement-interface subsection for Amendment B schema
  steering if retained in the main text.
- [ ] Decide whether mechanism diagnostics belong in main text, appendix, or
  future-work section.
- [ ] Add Data and Code Availability section once artifact release scope is
  finalized.

## Citation and Reference Work

- [ ] Build the Paper 1 bibliography from verified review (meta-analysis) references
  and method papers.
- [ ] Verify citation metadata for DPO, KTO, Cheng IDK training, calibration,
  TriviaQA, Qwen3, and every evaluation benchmark mentioned.
- [ ] Add citations for SelfAware, KUQ, CoCoNot, AbstentionBench, MMLU, PopQA,
  TruthfulQA, and any hidden-state or activation-steering claims used.
- [ ] Avoid importing Paper 1 claims without a citation or path back to the
  verified synthesis.

## Reproducibility and Safety

- [ ] Confirm no restricted data, gated model artifacts, raw private outputs, or
  ignored run products are referenced as redistributable.
- [ ] Confirm all result-producing scripts are deterministic or document the
  expected stochastic component.
- [ ] Confirm scored outputs retained for future evals include `id` or stable
  row key, label, refused, correct, truthful, and arm.
- [ ] Confirm protocol changes, if any, have explicit changelog and user
  approval before manuscript promotion.
