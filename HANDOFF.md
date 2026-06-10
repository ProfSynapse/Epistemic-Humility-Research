# HANDOFF — Epistemic Humility Research Program

**Repo:** `ProfSynapse/Epistemic-Humility-Research` (private) · **Branch:** `main` · **Updated:** 2026-06-10
**This doc is the single re-entry point.** Tell a new session: "read HANDOFF.md and continue."

**Mission for the next session: prep and build out the Phase 1 experiment
pipeline** (SFT vs DPO vs KTO abstention training → paper 2). Paper 1 (the
meta-analysis) is drafted and waiting on the user's read-through; its
remaining work is listed in §4 below and is NOT the next session's focus
unless the user says so.

---

## 1. Orientation (60 seconds)

- Two arXiv-bound deliverables: **paper 1** = meta-analysis of epistemic
  humility in LLM training/fine-tuning (`meta-analysis/paper/draft-v0.md`,
  drafted); **paper 2** = the Phase 1 experiment (not started — that's the
  job now).
- The staged 4-phase program lives in
  `experiment/protocol/research-trajectory.md`. Read it first; it is the
  authoritative plan. Phase 1 = three-way SFT/DPO/KTO on model-specific IDK
  data, measuring refusal recall + over-refusal + truthful rate + ECE on
  the same run, with OOD transfer (KUQ / CoCoNot / AbstentionBench).
- Training/eval infrastructure is the **Synaptic Tuner submodule** at
  `synaptic-tuner/` (`git submodule update --init`, then
  `cd synaptic-tuner && ./run.sh status`). 3B pilot runs locally
  (RTX 3090, `python tuner.py local-run`), 7-8B confirm on HF Jobs.
  Inside the submodule, load its `.skills/fine-tuning/SKILL.md` before any
  training work; KTO JSONL must be interleaved
  (`.skills/fine-tuning/reference/dataset-formats.md`).
- Repo history: split out of Toolset-Training 2026-06-10 via
  `git subtree split` — pre-split commits reference
  `docs/epistemic-humility/...` paths; everything is now at repo root.
- macOS gotchas: python.org Python needs
  `SSL_CERT_FILE=$(python3 -m certifi)` for arxiv/HF fetches; PDF page
  renders via `/opt/homebrew/bin/pdftoppm` to `scratch/` (gitignored), then
  Read the PNG.

## 2. Phase 1 pipeline — what to build (in order)

1. **Resolve the open decisions with the user** (blocking, ask first):
   - Model family pin: Qwen2.5-3B/7B-Instruct (what the tuner presets
     target today) vs a newer open-weights generation. Criteria in
     research-trajectory.md §Model strategy. User has said Llama-2-era is
     stale/overmodeled; within-model comparison makes apples-to-oranges
     acceptable.
   - Llama-2-7b-chat **bridge arm** in/out (recommendation: in — one
     Idk-SFT + Idk-DPO replication to validate the pipeline against Cheng
     et al.'s published numbers before novel arms run).
   - How much Phase 2 rides along in paper 2 (cheapest slice = KTO
     desirable/undesirable balance ablation).
   - KTO label mapping for the calibration-flavored arm: congruence vs
     correctness-safe (`experiment/protocol/rewardcal-kto-recipe.md`).
2. **Reconcile and finalize the pre-registration.**
   `experiment/protocol/PROTOCOL.md` (v0.1) predates the trajectory
   conversation: it's 2-arm (SFT vs KTO, DPO optional) and pins Qwen2.5.
   Update it to the three-way design, the chosen model pin, the bridge
   arm, and the decisions above. Hypotheses must be registered BEFORE any
   training run. Its metric suite, power analysis, and data-construction
   recipe (§3.2-3.5) are still good starting points.
3. **Knowledge-probing pipeline** (the model-specific part): probe the
   pinned base model on a TriviaQA rc.nocontext train subset (~20k
   questions) for P_correct per question. Use a HIGHER sample count than
   Cheng's 10 and add a label-noise sensitivity analysis — we measured
   43-51% of their "unknown"-labeled questions answered correctly
   (`meta-analysis/evidence/` reanalysis). Needs a local inference backend
   (RTX 3090 via the tuner, or vLLM).
4. **Dataset builders**: known/unknown splits → SFT JSONL, DPO pairs, KTO
   unpaired binary (desirable: known+answer, unknown+abstention;
   undesirable: unknown+model's own hallucinated probe sample,
   known+abstention as the anti-over-refusal signal). KTO file interleaved
   true/false. Identical data budget across arms. Build these as
   checked-in scripts under `experiment/`, config-driven, not one-offs.
5. **Training runs**: identical LoRA budget across arms, 2 seeds at 3B,
   early stopping on dev loss (Gekhman: prolonged training on unknowns
   drives hallucination — log dynamics as a secondary analysis).
6. **Eval harness**: truthful rate + 4-quadrant matrix, refusal recall +
   over-refusal decomposition, AP over confidence-ranked answers, token
   ECE on MMLU (the abstention-calibration tension, first time on one
   run), TruthfulQA, accuracy retention; OOD on KUQ / CoCoNot /
   AbstentionBench subsets (all already local under `datasets/` with
   provenance `dataset.md`s). Analysis: paired bootstrap CIs + McNemar
   between arms; deterministic committed scripts, same provenance
   discipline as paper 1.
7. **Slot-ins from deferred analyses**: R2 (HINT-lab PPO-M/PPO-C
   checkpoints through our abstention suite) once GPU inference is up;
   S2 (Sharma's 4 sycophancy framings as an eval axis) at protocol-design
   time (`meta-analysis/evidence/sycophancy-cheng-join.md` has the paths).

## 3. Headline findings the experiment is built on

1. **KTO has never been applied to abstention/IDK/calibration training**
   (verified gap as of 2026-06). Closest prior art: Cheng et al. ICML 2024
   (Idk-SFT/DPO/PPO/BoN/HIR on Llama-2-7b-chat; no KTO, no small models,
   thin OOD).
2. Our exact reanalysis of Cheng's outputs (n=11,313): Idk-SFT over-refuses
   42.7% of known questions; DPO halves that to 23.3%.
3. Our AbstentionBench reanalysis: each Tulu-3 preference stage adds recall
   (SFT→DPO +0.08 at 8B, p=5.5e-4) at zero precision cost — but the
   frontier ceilings at ~0.7 and scale doesn't move it (0.69→0.71 across
   8B-405B).
4. RLHF degrades token-level calibration ~10× (GPT-4 ECE 0.007→0.074)
   while improving abstention — the unreconciled tension; no paper measures
   both after the same run. KTO unmeasured on either.
5. SFT on model-unknown facts causally drives hallucination (Gekhman
   2405.05904) → training data must be split by THIS model's knowledge.

## 4. Where paper 1 (meta-analysis) stands

`meta-analysis/paper/draft-v0.md`, ~10,800 words, 69/69 citations resolved.
**Gate: the user has not yet done the full read-through.** Do not restart
paper work unprompted; the draft is stable.

Done: evidence base of 67 rows / 35 studies / 64 verified=true in
`meta-analysis/evidence/effects.csv` (family votes C1 2/0, C2 3/0 p=0.25,
C3 1/0, C4 4/0 p=0.125, C5 10/0 p=0.002); every in-text number verified
against primary sources, † convention retired; methods evidence-based in
§4.4 (SWiM, Cochrane ch. 12, PRISMA 2020 with disclosed deviations,
Hedges & Olkin limitation, Buscemi/Khraisha extraction-error grounding);
four independent reanalyses of released artifacts in §5.3 (Cheng outputs,
AbstentionBench table, FActScore generations, CRM training-data audit);
PRISMA flow reconstructed; coverage probes done (English-only corpus holds
across a five-language search; venue probe logged v1 admission candidates
in `evidence/prisma-flow.md`); related-surveys positioning (§6.4); acronym
pass; author block.

Remaining (tracked in `meta-analysis/paper/TODO.md`):
- User read-through, then: v1 admission decision (high priority: JMIR
  e78432, SAPA EMNLP 2025, 2505.13988 Hallucination Tax).
- Figures: Cochrane effect-direction plot per family, §5.3 operating-point
  scatter (abstentionbench_frontier.png may serve), L1-L4 coverage map.
- Abstract trim ~250→200 + title pick; BibTeX + arXiv LaTeX pipeline.
- Provider-card refresh right before submission (§5.4 is date-scoped to
  June 2026; Gemini 3.5 Flash / 3.1 Pro already out).
- §8 future-work section drafted from research-trajectory.md.

## 5. Provenance rules (non-negotiable, apply to paper 2 as well)

Every number carries source + exact metric + model + method + `verified`
flag. Analysis scripts are deterministic and re-runnable (data in, figures
out); no hand-edited results. Datasets carry `dataset.md` provenance
(source, license, fetch date, schema). Gitignored binaries (library/pdfs
273M, fulltext 38M, scratch parquets) are re-fetchable via
`library/scripts/fetch_library.py --enrich`. No em-dashes in paper body
prose. Release everything paper 2 produces (per-model labels, adapters,
harness) — paper 1 documents the field failing at exactly this.
