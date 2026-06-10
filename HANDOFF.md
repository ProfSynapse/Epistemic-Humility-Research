# HANDOFF — Epistemic Humility Research Program

**Repo:** `ProfSynapse/Epistemic-Humility-Research` (private) · **Branch:** `main` · **Updated:** 2026-06-10
**Goal:** two arXiv submissions — (1) a meta-analysis of epistemic humility in LLM
training/fine-tuning, (2) a novel SFT-vs-DPO-vs-KTO abstention experiment run in the
Synaptic Tuner submodule. A staged 4-phase research program builds on both:
`experiment/protocol/research-trajectory.md`.

This doc is the single re-entry point. Tell the next session to
"read HANDOFF.md and continue."

---

## 1. Repo history (so paths in old commits make sense)

This repo was split out of Synaptic Tuner (`ProfSynapse/Toolset-Training`) on
2026-06-10 via `git subtree split --prefix=docs/epistemic-humility` — full
commit history preserved. Commits before the split reference
`docs/epistemic-humility/...` paths; everything now lives at repo root.
Synaptic Tuner is consumed as a git submodule at `synaptic-tuner/`
(`git submodule update --init` on first checkout).

Gitignored binaries (library/pdfs 273M, library/fulltext 38M,
scratch/rewardcal-fetch parquets 141M) were copied over locally and are
re-fetchable: `SSL_CERT_FILE=$(python3 -m certifi) python3 library/scripts/fetch_library.py --enrich`
(macOS python.org Python needs that SSL_CERT_FILE for arxiv/HF fetches; PDF
page rendering needs poppler — `/opt/homebrew/bin/pdftoppm` to scratch/, then
Read the PNG).

## 2. State of paper 1 (meta-analysis) — draft complete, awaiting user reread

`meta-analysis/paper/draft-v0.md`, ~10,800 words, 69/69 citations resolved.

- **Evidence base:** `meta-analysis/evidence/effects.csv` — 67 rows, 35
  studies, 64 verified=true. Family votes: C1 2/0, C2 3/0 (p=0.25), C3 1/0,
  C4 4/0 (p=0.125), C5 10/0 (p=0.002, exact binomial).
- **Verification discipline:** every in-text number verified against primary
  sources (PDF page renders for figure-only values); † convention retired.
- **Methods are evidence-based** (§4.4): SWiM reporting items (Campbell 2020),
  Cochrane Handbook ch. 12 direction-based vote counting + sign tests,
  Hedges & Olkin 1980 as the limitation cite, PRISMA 2020 with disclosed
  deviations, Buscemi 2006 + Khraisha 2024 grounding the single-extractor
  ~14% error-rate mitigation, Kitchenham & Charters 2007 for CS SLR norms.
- **Independent reanalyses of released artifacts** (§5.3, four worked cases,
  scripts in `meta-analysis/analysis/`): Cheng et al. outputs (exact refusal
  metrics, 43-51% label noise on "unknown" labels), AbstentionBench results
  table (8 new effects rows, study `reanalysis-2506.09038` — paired
  Tulu-3 ladder contrasts with sign tests), FActScore generations
  (descriptive only — conflates scale/corpus/vendor), CRM training-data
  audit (single confidence template, ~300 contradictory double-stacks).
- **Coverage probes done:** five-language search (English-only corpus holds),
  venue probe beyond arXiv (~4 arXiv-invisible + 3 missed arXiv papers
  logged in `evidence/prisma-flow.md` as v1 admission candidates).

**Gate:** the user's read-through of draft-v0.md. After it, in
`meta-analysis/paper/TODO.md`: v1 admission decision (high-priority: JMIR
e78432, SAPA EMNLP 2025, 2505.13988), abstract trim ~250→200 + title,
figures (Cochrane effect-direction plot per family; abstentionbench_frontier
may serve §5.3), provider-card refresh near submission (Gemini 3.1 Pro /
3.5 Flash, OpenAI successor), BibTeX + arXiv LaTeX pipeline, §8 future-work
section drafted from research-trajectory.md.

## 3. Headline findings driving the experiment

1. **KTO has never been applied to abstention/IDK/calibration training**
   (verified gap as of 2026-06). Closest prior art: Cheng et al. ICML 2024
   (Idk-SFT/DPO/PPO/BoN/HIR on Llama-2-7b-chat; no KTO, no small models,
   thin OOD).
2. Our reanalysis of Cheng's raw outputs (exact, n=11,313): Idk-SFT
   over-refuses 42.7% of known questions; DPO halves that to 23.3%.
3. Our AbstentionBench reanalysis: each Tulu-3 preference stage adds recall
   (SFT→DPO +0.08 at 8B, p=5.5e-4) with zero precision cost — but ceiling
   ~0.7 frontier, and scale doesn't move it (0.69→0.71 across 8B-405B).
4. RLHF degrades token-level calibration ~10× (GPT-4 ECE 0.007→0.074) while
   improving abstention — unreconciled tension; no paper measures both after
   the same run. KTO unmeasured on either.
5. SFT on model-unknown facts causally drives hallucination (Gekhman
   2405.05904) → training data must be split by THIS model's knowledge.

## 4. Work queue (in order)

1. **User rereads draft-v0.md** → then the TODO.md pre-submission items (§2 above).
2. **Experiment decisions (user):** model family pin (Qwen2.5 vs newer),
   Llama-2-7b-chat bridge arm in/out (recommended in), Phase-2 scope inside
   paper 2 or not, KTO mapping choice (congruence vs correctness-safe — see
   `experiment/protocol/rewardcal-kto-recipe.md`).
3. **Phase 1 execution** per `experiment/protocol/research-trajectory.md`:
   model-specific known/unknown splits via correctness probing (use a higher
   sample count — carry the 43-51% label-noise finding), SFT vs DPO vs KTO
   arms, measure refusal recall + over-refusal + truthful rate + ECE on the
   same run, OOD via KUQ/CoCoNot/AbstentionBench. Training/eval runs in the
   `synaptic-tuner/` submodule (`./run.sh status`; 3B pilot local RTX 3090
   via `python tuner.py local-run`, 7-8B confirm on HF Jobs). KTO JSONL must
   be interleaved — `synaptic-tuner/.skills/fine-tuning/reference/dataset-formats.md`.
4. **Deferred analyses:** R2 (HINT-lab checkpoints on our abstention suite —
   needs GPU inference, fold into experiment phase), S2 (Sharma sycophancy
   framings as a paper-2 eval axis — protocol design).

## 5. Provenance rules (non-negotiable for arXiv)

Every number in `effects.csv` carries source + URL + `verified` flag. Numbers
failing primary-source verification get corrected or dropped from pooled
stats — the raw reports keep the audit trail. Analysis scripts are
deterministic and re-runnable (CSV in, figures out); no hand-edited results.
