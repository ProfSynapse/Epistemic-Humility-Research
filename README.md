# Epistemic Humility in LLM Training & Fine-Tuning — Research Program

Standalone research repo (split out of Synaptic Tuner 2026-06-10 with full
commit history). Two linked arXiv-bound deliverables plus a staged research
program:

1. **Meta-analysis** (`meta-analysis/`) — systematic search + quantitative
   synthesis of the literature on epistemic humility in LLM
   training/fine-tuning: calibration (ECE/Brier/AUROC), abstention/IDK
   fine-tuning, fine-tuning-induced hallucination, sycophancy under
   preference training, and knowledge-boundary self-awareness. Synthesis is
   SWiM-conformant vote counting by direction of effect + exact binomial
   sign tests + descriptive normalization (no variances exist to pool);
   every number carries a per-row `verified` flag. Paper:
   `meta-analysis/paper/draft-v0.md` (+ `TODO.md` pre-submission checklist).

2. **Experiment program** (`experiment/`) — SFT vs DPO vs KTO on
   model-specific IDK data, derived from the gaps the meta-analysis
   verified. Staged plan: `experiment/protocol/research-trajectory.md`
   (phases 1-4: three-way comparison, dose-response/data-composition,
   probe-transfer mechanism, cross-architecture generalization).

**Re-entry point for new sessions: read `HANDOFF.md` first.**

## Layout

```
.
├── README.md                  # this file
├── HANDOFF.md                 # session re-entry point
├── meta-analysis/
│   ├── evidence/              # effects.csv (per-row verified flags), raw
│   │                          #   reports, PRISMA flow, reanalysis reports
│   ├── analysis/              # deterministic scripts + generated figures
│   └── paper/                 # draft-v0.md + TODO.md
├── experiment/
│   └── protocol/              # research-trajectory.md, KTO recipes,
│                              #   future-work parking
├── library/                   # paper manifest + frontmatter notes
│   ├── pdfs/                  # gitignored; refetch via library/scripts/
│   └── fulltext/              # gitignored; same
├── datasets/                  # local eval/training data with provenance
│   └── */dataset.md           #   source, license, fetch date, schema
├── essays/                    # companion essay material
├── scratch/                   # gitignored working space (full parquets etc.)
└── synaptic-tuner/            # git submodule: training/eval infrastructure
```

## Running experiments

Training and evaluation run inside the [Synaptic
Tuner](https://github.com/ProfSynapse/Toolset-Training) submodule:

```bash
git submodule update --init          # first checkout
cd synaptic-tuner
./run.sh status                      # health check
# 3B pilot local (RTX 3090): python tuner.py local-run ...
# 7-8B confirm: HF Jobs via tuner/ handlers
```

Dataset formats (KTO interleaving requirement etc.):
`synaptic-tuner/.skills/fine-tuning/reference/dataset-formats.md`.

## Provenance rules (non-negotiable for arXiv)

- Every number in `meta-analysis/evidence/effects.csv` carries source,
  exact metric, model, method, URL, and a `verified` flag. Numbers failing
  primary-source verification get corrected or dropped from pooled stats;
  the raw reports keep the audit trail.
- Analysis scripts are deterministic and re-runnable: CSV in, figures out.
  No hand-edited results.
- Gitignored binaries are re-fetchable:
  `SSL_CERT_FILE=$(python3 -m certifi) python3 library/scripts/fetch_library.py --enrich`
