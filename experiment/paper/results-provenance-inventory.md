# Phase 1 Results Provenance Inventory

Status: RETIRED 2026-07-04. Superseded by the per-paper provenance appendices
(Appendix A of `paper3-knows-but-doesnt-say-draft-v0.md` and
`paper4-two-signal-readout-draft-v0.md`), which map every published number to
its protocol document and on-disk artifact. This file predates the amendment
series from C onward and is kept as a historical record of the 2026-06-18
claim-tier rules; do not use it to gate what a draft may cite.
Created: 2026-06-18
Scope (historical): claim-tier and provenance guide only; not a results source by itself

## Use Rule

Use this file to decide what a draft section may cite and what must be
reconciled first. Do not treat generated outputs, result directories, or run
records as publication-grade merely because they exist on disk.

## Claim Tiers

| Tier | Governing source | Evidence allowed | Claim language allowed | Not allowed |
|---|---|---|---|---|
| v0.3 headline | `experiment/protocol/PROTOCOL.md` signed 2026-06-10 | Pre-registered default-config v0.3 matrix only: 4B SFT/DPO/KTO headline seeds, with pre-registered analysis rules | Primary Phase 1 answer/refusal, calibration, and arm-comparison claims after reconciliation gates pass | Cherry-picked sensitivity cells, Amendment A/B results, mechanism diagnostics, incomplete 8B/bridge/panel evidence |
| v0.3 robustness | `PROTOCOL.md` section 3.1a | LR and beta sensitivity panels, one seed per cell, if completed and tied to configs/results | Robustness-only: whether headline direction appears stable to pre-registered perturbations | Headline numbers, best-cell reporting, seed-level CI claims |
| Amendment A | `PROTOCOL.md` Amendment A / v0.4 status, signed 2026-06-14 | Sequential `SFT -> DPO` and `SFT -> KTO` runs/evals, reported separately | Prospective extension claims about sequential refinement after SFT | Retroactive v0.3 headline claims or silent replacement of the v0.3 matrix |
| Amendment B / stated confidence | `experiment/protocol/AMENDMENT-B-stated-confidence-grpo.md` | Stated-confidence reruns and reports, explicitly labeled Amendment B; signed off for measurement/reporting on 2026-06-19 | Accepted stated-confidence measurement evidence and interface-effect caveats | GRPO claims, v0.3 headline replacements, claims that old plain-answer evals contain stated-confidence metrics |
| Phase 3 mechanisms | `experiment/protocol/PHASE3-control-system-protocol.md` and probe plans | Hidden-state/probe/causal-pilot artifacts with verified manifests | Exploratory local mechanism evidence, tier-labeled | Phase 1 headline evidence, arm ranking, reward-loop input, validated mechanism claims without signed promotion |

## Evidence Inventory

| Evidence block | Current local artifact state | Draft use | Caveats before publication |
|---|---|---|---|
| v0.3 4B headline SFT | Run records for `sft__4b__headline__seed1..3` show completed adapters. SelfAware three-seed result dirs exist. | Candidate v0.3 headline evidence after eval/provenance reconciliation. | Need confirm final paper table uses only default-config v0.3 evals, required domains, seed aggregation, and retained per-row/scored outputs. |
| v0.3 4B headline DPO/KTO | Seed 1 run records show completed adapters; seed 2/3 run records still show `outcome.status=launched` in the provenance spine, despite downstream result dirs existing for some evals. | Local patterns may motivate discussion only after explicit stale-record reconciliation. | Do not cite as complete v0.3 headline evidence until run records, adapter paths, eval configs, result dirs, and scored rows agree. |
| v0.3 8B confirm | Protocol includes 3-seed 8B confirm. No completed 8B evidence was established in this pass. | Mention only as pending confirm scale if needed. | No 8B-backed claims. |
| v0.3 bridge | Protocol includes Llama-2-7b-chat SFT/DPO bridge replication. No completed bridge evidence was established in this pass. | Mention only as unresolved pipeline-validation gate. | No bridge-backed validation or Cheng-replication claim. |
| v0.3 sensitivity panels | Protocol pre-registers LR and beta panels as robustness-only. Completeness was not established in this pass. | Use only if later reconciled as robustness figures. | Never source headline numbers from panels. |
| Amendment A plain-answer sequential | `amendment_a_transition_report.md` summarizes SelfAware/KUQ transition evidence; `SFT -> DPO` has three clean SelfAware seeds in the report, while `sft_kto__4b__amendment_a__seed3` run record remains stale/launched. | Separate Amendment A/v0.4 extension section; row-transition claims where exact scored rows exist. | Reconcile KTO seed 3 record/result state and the report's refusal-recall arithmetic note before publication-grade tables. |
| Amendment B stated-confidence cold-start | Stated-confidence SelfAware all-arm result dirs exist for seeds 1-3 under the answer/confidence schema. Session record documents earlier confounded schema attempts. | Separate measurement-interface and stated-confidence evidence. | Exclude confounded decision-enum and first prompt artifacts from reportable evidence except as negative format-control examples. |
| Amendment B stated-confidence sequential | `amendment_b_sequential_results_report.md` reports all three SelfAware seeds for `sft_merged`, `SFT -> DPO`, and `SFT -> KTO`, with same-row transition summaries. | Accepted Amendment B stated-confidence sequential evidence, not v0.3 replacement. | Report confidence scoring separately from plain-answer results; GRPO/RLVR remains prospective. |
| Hidden-state / probe diagnostics | Hidden-state extraction dirs exist; probe plan records SFT/DPO/KTO and sequential extractions with `manifest ok`, `verified true` for named runs. | Exploratory mechanism section or future-work motivation. | Do not infer internalized humility or causal mechanism without Phase 3 controls and signed promotion. |
| Phase 3 causal/control work | Phase 3 protocol is official exploratory draft v0.1, tiering outputs as Tier 0-2 unless promoted. | Mechanism-roadmap framing and exploratory diagnostic caveats. | No reward-loop, arm-ranking, or headline use. KG/literature dependencies must be reconciled before mechanism support claims. |

## Publication Reconciliation Gates

| Gate | Required action | Blocks |
|---|---|---|
| Run-record freshness | Resolve stale/launched records against actual completed adapters and logs, especially `dpo__4b__headline__seed2/3`, `kto__4b__headline__seed2/3`, and `sft_kto__4b__amendment_a__seed3`. | Any headline or seed-complete claim using those runs. |
| Eval provenance | For every cited metric, point to the exact eval config, result directory, `metrics.json`, bootstrap/McNemar artifact when relevant, and scored rows or transition table source. | Numeric tables, row-transition claims, significance claims. |
| Claim-tier labeling | Label v0.3, Amendment A, Amendment B, and Phase 3 evidence in every table/figure caption. | Manuscript-ready results section. |
| v0.3 completeness | Confirm the intended default-config domains, three seeds per 4B arm, analysis scripts, seed aggregation, and within-run bootstrap outputs are complete. | Primary Phase 1 headline claims. |
| 8B/bridge/panel separation | Decide whether 8B confirm, bridge, and sensitivity panels are absent, pending, or separately reportable; keep them out of headline numbers unless governed. | Generalization, pipeline-validation, and robustness claims. |
| Amendment A cleanup | Reconcile clean vs excluded sequential attempts, especially bad-merge seed-2 DPO history and KTO seed-3 record state. | Sequential extension tables. |
| Amendment B sign-off | Recorded as measurement/reporting sign-off on 2026-06-19. Preserve prompt/schema confound history. | Protocol-bearing GRPO claims. |
| Mechanism controls | Verify manifests, row alignment, controls, and KG/literature reconciliation before interpreting directions causally. | Mechanism claims stronger than exploratory local diagnostics. |

## Draft Writer Guardrails

- Phrase current v0.3 evidence as pending unless the cited table passes the
  run-record and eval-provenance gates.
- Keep Amendment A as a separately signed prospective extension, not as a
  retroactive edit to the 2026-06-10 v0.3 preregistration.
- Keep Amendment B stated-confidence results separate because the output
  contract itself changed behavior in rejected smokes; accepted measurement
  status does not make these a plain-answer replacement.
- Use mechanism diagnostics to motivate hypotheses and controls, not to rank
  training arms or claim a validated internal mechanism.
- If a metric lacks a traceable config/result/scored-row path, omit the number
  or mark it as unreconciled rather than filling from memory.
