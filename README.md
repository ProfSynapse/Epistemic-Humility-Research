# Epistemic Humility in LLM Training and Fine-Tuning

A research program on a simple question with a messy evidence base: **can we
train language models to know what they don't know, and what does that
training cost us?**

Models that confidently answer questions beyond their knowledge are the root
of much of what gets called "hallucination." A growing literature tries to
fix this by fine-tuning models to abstain ("I don't know"), to calibrate
their confidence, or to resist sycophantic agreement. But that literature is
fragmented across metrics, models, and methods, and some of its central
tensions have never been measured in a single study. This repo holds our
attempt to (a) synthesize that literature rigorously and (b) run the
experiments the synthesis says are missing.

## What we're focused on

Five threads, and the gaps between them:

- **Calibration**: does the model's confidence track its accuracy
  (ECE, Brier, AUROC)?
- **Abstention / IDK fine-tuning**: teaching models to refuse questions
  outside their knowledge, without over-refusing ones they can answer.
- **Fine-tuning-induced hallucination**: SFT on facts the model doesn't
  already know causally drives hallucination, so training data must be
  split by *this specific model's* knowledge boundary.
- **Sycophancy under preference training**: RLHF-style training can teach
  models to agree rather than to be right.
- **Knowledge-boundary self-awareness**: can a model report what it knows?

The headline tension motivating the experimental work: RLHF degrades
token-level calibration roughly 10x (GPT-4's ECE went from 0.007 to 0.074)
while *improving* abstention behavior, and no paper measures both after the
same training run. Meanwhile **KTO has never been applied to
abstention/IDK/calibration training at all** (verified gap as of June 2026).
That is the hole paper 2 fills.

## The two deliverables

1. **Meta-analysis** (`meta-analysis/`, paper 1): a systematic search and
   quantitative synthesis of the literature above. Because the primary
   studies rarely report variances, there is nothing to pool in the
   classical sense; the synthesis is SWiM-conformant vote counting by
   direction of effect, exact binomial sign tests, and descriptive
   normalization. Every number in the evidence table
   (`meta-analysis/evidence/effects.csv`) carries source, exact metric,
   model, method, URL, and a per-row `verified` flag. We also reanalyzed
   four sets of released artifacts (Cheng et al.'s model outputs,
   AbstentionBench results, FActScore generations, a reward-calibration
   training-data audit) rather than trusting reported numbers. Draft:
   `meta-analysis/paper/draft-v0.md`.

2. **Experiment program** (`experiment/`, paper 2): a controlled three-way
   comparison of **SFT vs DPO vs KTO** for abstention training, on IDK data
   split by each model's own knowledge boundary (Qwen3 4B/8B, plus a
   Llama-2-7b-chat bridge arm that replicates Cheng et al. before any novel
   result is claimed). The design is pre-registered and locked in
   `experiment/protocol/PROTOCOL.md`; the staged plan through phases 2-4
   (dose-response, probe-transfer mechanism, cross-architecture
   generalization) lives in `experiment/protocol/research-trajectory.md`.

## Navigating the repo

**If you're a returning session or collaborator picking up the work: read
`HANDOFF.md` first.** It is the single re-entry point and always reflects
current state.

```
.
├── README.md                  # this file: orientation
├── HANDOFF.md                 # live state + next steps (read this first)
├── LICENSE                    # MIT (code/docs; vendored data keeps its own)
├── CONTRIBUTING.md            # how to contribute + ground rules
├── meta-analysis/             # PAPER 1
│   ├── evidence/              #   effects.csv (per-row verified flags),
│   │                          #   reanalysis reports, PRISMA flow
│   ├── analysis/              #   deterministic scripts + generated figures
│   └── paper/                 #   draft-v0.md + TODO.md checklist
├── experiment/                # PAPER 2
│   ├── protocol/              #   PROTOCOL.md (pre-registered, LOCKED),
│   │                          #   research-trajectory.md (phases 1-4)
│   └── phase1/                #   probe/ data/ eval/ recipes/ run_records/
├── docs/                      # architecture decisions, prep research,
│                              #   peer-review records for the pipeline
├── library/                   # paper manifest + frontmatter notes
│   ├── pdfs/                  #   gitignored; refetch via library/scripts/
│   └── fulltext/              #   gitignored; same
├── datasets/                  # eval/training data, one dir per source;
│                              #   each carries dataset.md provenance
│                              #   (source, license, fetch date, schema)
├── essays/                    # companion long-form essay material
├── scratch/                   # gitignored working space
└── synaptic-tuner/            # git submodule: training/eval infrastructure
                               #   (kept experiment-agnostic)
```

Suggested reading order for a newcomer:

1. This README, then `HANDOFF.md` for current state.
2. `meta-analysis/paper/draft-v0.md` for the synthesis and the gap analysis.
3. `experiment/protocol/PROTOCOL.md` for the locked experimental design.
4. `docs/architecture/phase1-pipeline.md` for how the pipeline implements it.

## Running experiments

Training and evaluation run inside the
[Synaptic Tuner](https://github.com/ProfSynapse/Synaptic-Tuner) submodule:

```bash
git submodule update --init          # first checkout
cd synaptic-tuner
./run.sh status                      # health check
```

The Phase 1 run matrix (probe → dataset builds → matrix gate → training
cells) is driven by the experiment-runner scripts under
`.claude/skills/experiment-runner/`; dataset format requirements (KTO
interleaving etc.) are documented at
`synaptic-tuner/.skills/fine-tuning/reference/dataset-formats.md`.

## Contributing

Contributions, corrections, and replication attempts are welcome; see
[CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. The most useful ones
right now:

- **Evidence corrections**: if a number in
  `meta-analysis/evidence/effects.csv` misstates a primary source, open an
  issue with the source passage. Rows that fail verification get corrected
  or dropped; that is the point of the `verified` flag.
- **Missed studies**: papers on calibration, abstention training,
  fine-tuning-induced hallucination, or sycophancy that the search missed
  (inclusion criteria are in the paper's methods section and
  `meta-analysis/evidence/prisma-flow.md`).
- **Replication**: the analysis scripts are deterministic (CSV in, figures
  out) and the experiment pipeline is built to be re-runnable. If something
  doesn't reproduce, that's a bug report we want.

Ground rules for PRs:

- `experiment/protocol/PROTOCOL.md` is a signed pre-registration and is
  **locked**: changes to hypotheses, falsifiers, or the headline run matrix
  require a new signed revision with a changelog, not an edit.
- Every quantitative claim needs provenance (see below). PRs that add
  numbers without sources won't be merged.
- Some vendored data is do-not-redistribute (notably the OpenMOSS IDK
  data) and is deliberately gitignored. Don't commit it, and don't build
  anything that requires redistributing it.

## Provenance rules (non-negotiable for arXiv)

- Every number in `meta-analysis/evidence/effects.csv` carries source,
  exact metric, model, method, URL, and a `verified` flag. Numbers failing
  primary-source verification get corrected or dropped from pooled stats;
  the raw reports keep the audit trail.
- Analysis scripts are deterministic and re-runnable: data in, figures out.
  No hand-edited results.
- Datasets carry `dataset.md` provenance files (source, license, fetch
  date, schema).
- Gitignored binaries are re-fetchable:
  `SSL_CERT_FILE=$(python3 -m certifi) python3 library/scripts/fetch_library.py --enrich`
- Everything paper 2 produces (per-model knowledge labels, adapters, eval
  harness) gets released; paper 1 documents the field failing at exactly
  this.
