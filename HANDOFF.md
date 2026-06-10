# HANDOFF — Epistemic Humility Research Program

**Branch:** `claude/ai-humility-research-experiment-37za2i` · **Updated:** 2026-06-10
**Goal:** two arXiv submissions — (1) a meta-analysis of epistemic humility in LLM
training/fine-tuning, (2) a novel SFT-vs-KTO abstention experiment run in Synaptic Tuner.

This doc is the single re-entry point. Tell the next session to
"read docs/epistemic-humility/HANDOFF.md and continue."

---

## 1. UNBLOCK — DONE (2026-06-10, local macOS session)

Network blocks are moot on the local machine. Completed:

- **Library fetched**: all 95 manifest papers have PDFs + ar5iv full text
  (2309.07875 added 2026-06-10 during the dose-response re-attribution;
  `library/pdfs/`, `library/fulltext/` — gitignored, re-fetch with
  `SSL_CERT_FILE=$(python3 -m certifi) python3 docs/epistemic-humility/library/scripts/fetch_library.py --enrich`).
  Script now rate-limits (3s/request, 429 backoff) and skips already-fetched.
- **All 6 blocked datasets fetched** via `datasets/scripts/fetch_datasets.py`
  (TriviaQA, MMLU, PopQA, KUQ, CoCoNot, AbstentionBench-repo-snapshot) —
  committed with provenance `dataset.md`s.
- **Exact truthful-rate recomputation done**: Cheng et al.'s test set turned
  out to be TriviaQA unfiltered.nocontext/validation (100% question match);
  `cheng_test_gold.jsonl` + exact alias grading replaced the token-F1 proxy.
  New finding: 43-51% of answers on "unknown"-labeled questions are correct
  → label-noise caveat (now in draft 5.3).
- **Priority PDF verifications done** (GPT-4 ECE Fig 8, Cheng Table 1,
  R-Tuning Table 1, AbstentionBench 24%, Wei sycophancy, Sharma 98%/~6%):
  25/59 effects.csv rows now verified=true; 2 corrections (R-Tuning metric
  is AP score not accuracy; Wei -8.8 is Flan-PaLM-8B not 62B); daggers
  removed in draft for verified claims.

macOS gotcha: python.org Python needs `SSL_CERT_FILE=$(python3 -m certifi)`
for arxiv/HF fetches. PDF page rendering needs poppler (`brew install poppler`;
if the Read tool can't find pdftoppm, render via `/opt/homebrew/bin/pdftoppm`
to scratch/ and read the PNG).

## 2. What exists already (all committed on this branch)

| Asset | Path | State |
|---|---|---|
| Paper library: manifest (61 papers) + frontmatter notes + fetch script | `library/` | notes stubbed; PDFs pending network |
| 5 deep-research evidence reports (every extracted number + provenance) | `meta-analysis/evidence/raw-reports/` | done; numbers flagged unverified-against-PDF |
| Independent reanalysis of Cheng et al. (2401.13275) method outputs | `meta-analysis/analysis/reanalyze_idk_outputs.py` → `evidence/idk-method-reanalysis.csv` | done (exact refusal metrics) |
| Local datasets (SelfAware, TruthfulQA, 2× sycophancy evals, SaySelf, Cheng outputs) | `datasets/` | done, with licenses + frontmatter notes |
| Normalized evidence table + synthesis stats | `meta-analysis/evidence/effects.csv`, `analysis/` | see git log — being built |
| Experiment protocol (hypotheses, design, metrics, recipes) | `experiment/protocol/` | see git log — being built |

## 3. Headline findings driving the experiment

1. **KTO has never been applied to abstention/IDK/calibration training** (verified
   gap, high confidence, as of 2026-06). Closest prior art: Cheng et al. ICML 2024
   compares Idk-SFT/DPO/PPO/BoN/HIR on Llama-2-7b-chat (no KTO, no 3B, thin OOD).
2. Our reanalysis of their raw outputs (exact, n=11,313): Idk-SFT over-refuses
   42.7% of known questions; DPO halves that to 23.3% (refusal recall 84.1% vs 71.2%).
3. RLHF/preference training degrades token-level calibration ~10× (GPT-4 ECE
   0.007→0.074) while *improving* abstention/factuality — unreconciled tension;
   no paper measures both after the same run. KTO unmeasured on either.
4. SFT on model-unknown facts causally drives hallucination, linearly in fitted
   unknowns (Gekhman 2405.05904) → training data must be split by THIS model's
   knowledge (known/unknown splits are model-specific by construction).

**Planned experiment (pending your sign-off on the formal hypothesis doc):**
SFT vs KTO on model-specific IDK data for Qwen2.5-3B-Instruct (pilot) →
Qwen2.5-7B-Instruct (confirm), measuring truthful rate + over-refusal + ECE +
OOD transfer — directly filling gaps 1, 2, 5, 6 from
`evidence/raw-reports/05-sft-vs-preference-and-gaps.md`.

## 4. Work queue (in order)

1. ~~Enrich library + FULL verification pass~~ **DONE 2026-06-10**: 56/59
   effects.csv rows verified (31 studies); 6 corrections applied (see
   `paper/TODO.md` first checkbox for the list); 2505.19056 row RESOLVED:
   dose-response re-attributed to Bianchi 2309.07875 (safety-domain sweep;
   row stays excluded from pooled stats; gap 5 cites it qualitatively);
   draft + synthesize.py outputs updated. Lesson recorded: text-extraction
   agents misread figure-only values twice (GPT-4 Fig 8, SelfAware Fig 5) —
   always confirm figure values visually (pdftoppm render → Read the PNG).
   **Dagger elimination COMPLETE 2026-06-10**: two agent fan-outs
   (batches A+B, 32 papers, parallel Explore agents reading local PDFs)
   verified every remaining in-text value — 0 content daggers, † convention
   retired. 3 corrections folded into the draft (2401.12794 conformal-set
   accuracy direction, 2512.00218 monitorability boundary condition,
   2606.03962 "as well as"); 61/95 library notes status: verified.
2. ~~Download blocked datasets~~ **DONE 2026-06-10** (see §1). Remaining
   pendings listed in `datasets/README.md` (Natural Questions; AbstentionBench
   materialization; R-Tuning/Idk Google-Drive train sets — not needed for
   paper 1).
3. **Finish meta-analysis paper** from `meta-analysis/paper/draft-v0.md` +
   `TODO.md` checklist (PRISMA flow counts, figure regeneration,
   related-surveys positioning, abstract trim, BibTeX, author block).
4. **Experiment execution** (local GPU or HF Jobs; see
   `experiment/protocol/`): generate known/unknown splits for Qwen2.5-3B by
   10-sample correctness probing (needs an inference backend — RTX 3090 via
   `tuner.py local-run`, or cloud), build SFT + KTO JSONL per
   `.skills/fine-tuning/reference/dataset-formats.md`, train both arms,
   evaluate with the Evaluator harness, analyze, draft paper 2. NOTE: carry
   the label-noise finding (43-51% of "unknown"-labeled answered correctly in
   Cheng's data) into the protocol — consider a higher probing sample count
   or a label-noise sensitivity analysis.

## 5. Constraints discovered (so you don't re-hit them)

- `docs/research/` is **gitignored** — that's why this lives in `docs/epistemic-humility/`.
- Egress proxy blocks everything except github.com / raw.githubusercontent.com /
  pypi.org; WebSearch works (snippets only). WebFetch obeys the same allowlist.
- HF Jobs / training does not run in this container — training happens on your
  RTX 3090 or HF cloud from your machine.
- Datasets in repo so far: ~116 MB. Large downloads (TriviaQA full is GBs) should
  be subset before committing (rc.nocontext validation slice is enough).
- The PACT plugin/skills referenced in CLAUDE.md are not installed in cloud
  sessions; sessions run directly.

## 6. Provenance rules (non-negotiable for arXiv)

Every number in `effects.csv` carries source + URL + `verified` flag. Numbers
failing PDF verification get corrected or dropped from pooled stats — the raw
reports keep the audit trail of what changed.
