# PR #1 Peer Review Synthesis — phase1-pipeline

**PR**: https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/1
**Reviewed**: 2026-06-11 · research repo @ 174464d · synaptic-tuner @ f91ad37
**Panel**: reviewer-architect (design coherence), reviewer-tester (coverage), reviewer-backend (implementation), reviewer-security (adversarial)
**Verdicts**: APPROVE_WITH_MINOR · YELLOW · 1 Blocking found · PASS_WITH_CONCERNS

Full per-reviewer detail: task metadata `#56/#58/#60/#62` (`.metadata.handoff`).

## Blocking

| ID | Finding | Where | Reviewers |
|----|---------|-------|-----------|
| B1 | `correctness_safe` KTO arm emits ONLY desirable(True) rows → `ZeroDivisionError` at trainer load (kto `data_loader.py:256`, before the both-labels guard); diverges from arch §4.6 ("rebalance via weights" implies both labels) and from `build.yaml`'s `correctness_safe_undesirable_weight: 1.0`. Phase-2 rideshare arm only — verified absent from every Phase-1 matrix cell. | `build_datasets.py:394-418`, `:547-564` | backend (Blocking) + architect (independent, rated Minor pre-crash-trace) |

**Resolution path**: session-architect §4.6 row-disposition ruling → fix in builder + add a both-labels regression test → verify-only re-review.

## Minor

| ID | Finding | Where | Reviewer |
|----|---------|-------|----------|
| MA1 | SFT/DPO `known` training target is the LOWERCASED first normalized alias, not natural-case gold (`answer.value` never propagated through probe schema). Style confound on capability-tax/accuracy-retention comparison; scorer-invisible (normalization-invariant). Fix: propagate `answer.value` through probe → builder (pairs with Future FA1). | `probe.py:99-101`, `build_datasets.py:240-247` | architect |
| MT1 | McNemar statistic/p_value UNPINNED — mutation test proved dropped continuity correction survives all 3 stat tests. Paper significance claims rest on this function. Fix: known-value tests (e.g. b=10,c=0 → stat≈8.1, p≈0.004427). | `eval/stats.py` + `test_stats.py` | tester |
| MT2 | bootstrap_ci width never asserted vs analytic SE (verified correct empirically; missing regression guard). | `test_stats.py` | tester |
| MT3 | `distractor` unknown_negative_strategy branch untested (directly shapes DPO rejected / KTO False labels + manifest accounting). | `build_datasets.py:387-389` | tester |
| MT4 | `test_dry_run_main_does_not_launch` is CWD-coupled (bare relative argparse defaults vs `--matrix`'s `Path(__file__)` anchoring). | `run_matrix.py:440-443` | tester |
| MB1 | `--check-only` promises a prereq gate it never invokes (gate fns unit-tested but unwired); stale `check_matrix` docstring; record-spine fns written-but-unwired. Launch path is deliberately stubbed so no live risk. | `run_matrix.py:41,448-477` | backend |
| MB3 | DPO/KTO dev FILES diverge from SFT on dropped unknowns (questions invariant holds; manifest-traced). Confirm intended + document. | `build_datasets.py:539-544` | backend |
| MB4 | eval McNemar silently skips arm pairs with mismatched vector lengths — add warning/skip-row. | `run_eval.py:332` | backend |
| MS1 | Bridge-derived DO-NOT-REDISTRIBUTE data not gitignored at `experiment/phase1/data/` — `git add -A` footgun against OpenMOSS containment (SACROSANCT). **Elevated to fix-now by team-lead.** | `experiment/phase1/data/.gitignore` | security |
| MS2 | `zipfile.extractall` without member sanitization — zip-slip exposed during the documented re-pin window (sha pin blanked). Fix: per-member resolve + is_relative_to check. | `fetch_datasets.py:230-231` | security |
| MA3 | ADR §9.3 trainer line citations drifted (±1-3 lines); substantive claims all verify. | `phase1-pipeline.md §9.3` | architect |

## Future

| ID | Finding | Reviewer |
|----|---------|----------|
| FA1 | Add `answer_value` (natural-case gold) slot to probe→builder schema (clean fix for MA1; future-proofs Phase-4 model swaps) | architect |
| FT5 | `split_dev` boundary: dev=0 for small N/fraction — silent no-dev build; add guard + test | tester |
| FT6 | `interleave_kto` imbalance truncation untested (documented behavior; pin the contract) | tester |
| FB1 | Builder trusts probe-stored `question_norm` (guard verified non-vacuous today; latent coupling if HIR-prefixed questions ever enter the pool) | backend |
| FB2 | Provenance `verified=True` hardcoded rather than conditioned on scorer path | backend |
| FS1 | CSV formula-injection neutralization for ledger free-text fields | security |
| FS2 | `hf_jobs.py` repr-embedded URL in `python -c` — re-review trigger if repo source ever becomes untrusted | security |
| FS3 | OpenMOSS `process_sft_data.py` supply-chain note — SHA pin + opt-in gating are the appropriate controls; keep pin immutable | security |

## Clean confirmations (all four reviewers)

- **Tuner generality SACROSANCT — UPHELD**: zero experiment-specific code in synaptic-tuner; DPO is a general capability; SSOT + all leaf enumeration sites consistent.
- **PROTOCOL v0.3 conformance — UPHELD**: hard count assertions (19@4B/9@8B/2 bridge), fail-closed leakage guard, headline-defaults-only, per-arm-relative LR panel, bridge license containment at 3 enforcement points.
- **enable_thinking enforcement (ADR §9.3) — VERIFIED**: SFT masked passthrough, KTO raw-string N/A, DPO prompt-boundary, eval/probe pinned + runtime self-check.
- **Security**: HF_TOKEN env-only (never in command strings/logs/records); shlex.quote + list-form argv everywhere, no shell=True; json.loads/yaml.safe_load only; run-record filenames injection-free; FORCE_SEED_BETA_GATE_CLOSED is one-way (close-only).
- **Stats math verified correct** (bootstrap half-width 0.0203 vs analytic 0.0201; McNemar CC matches scipy) — the gaps are missing regression guards, not bugs.
- **Six closed silent-substitution instances held**; no seventh silent drop found (B1 is a hard crash, not a silent drop).
