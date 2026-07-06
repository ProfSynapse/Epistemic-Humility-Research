# Epistemic Humility Research

This repository is a research workspace for a single through-line:

**Can language models represent what they do and do not know, and can that
epistemic state be made visible in behavior, confidence, and deployment-time
trust decisions?**

The project started as a literature synthesis plus an abstention-training
experiment. It has since evolved into a five-paper program on calibration,
abstention, hidden-state readouts, faithful uncertainty, and the limits of
post-training.

For the current state, read [docs/research-trajectory.md](docs/research-trajectory.md)
first. The older locked Phase 1 protocol remains in `experiment/protocol/`; it is
historical and governed, not the entry point for new work.

## Current Through-Line

The short version:

1. We trained abstention on Qwen3-4B with SFT, DPO, KTO, and GRPO.
2. Training moved behavior, but exposed a persistent gap: the model's hidden
   states encode answerability clearly while its emitted confidence stays
   decoupled.
3. Mechanistic probes showed the internal signal is already present, robust, and
   often available before post-training.
4. The practical pivot is readout: use a two-signal trust pipeline that reads the
   model's internal answerability and answer-correctness signals directly.
5. The open frontier is actuation: can any channel write to, route, or obey that
   internal signal without collapsing into mere compliance or surface policy?

The working thesis is not "models do not know." It is closer to: **small open
models often know more than they say, and current training objectives move the
policy without reliably wiring that internal signal to stated confidence or
action.**

## Paper Line

The canonical paper map is maintained in
[docs/research-trajectory.md](docs/research-trajectory.md).

| Paper | Scope | Draft |
|---|---|---|
| P1 | Taxonomy, evidence synthesis, and the policy-vs-signal framework | [experiment/paper/paper1-taxonomy-framework-draft-v0.md](experiment/paper/paper1-taxonomy-framework-draft-v0.md) |
| P2 | Training regimen: SFT/DPO/KTO/GRPO for abstention | [experiment/paper/paper2-training-regimen-draft-v2.md](experiment/paper/paper2-training-regimen-draft-v2.md) |
| P3 | "Knows but Doesn't Say": internal-vs-stated confidence gap and training resistance | [experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md](experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md) |
| P4 | Training-free two-signal readout: gate, dial, and veto | [experiment/paper/paper4-two-signal-readout-draft-v0.md](experiment/paper/paper4-two-signal-readout-draft-v0.md) |
| P5 | Steering, actuation, and whether the internal signal can be routed into behavior | scaffold in progress |

Legacy figure prefixes are not paper numbers: `fig-p1-*` currently belongs to
Paper 2, `fig-p2-*` to Paper 3, and `fig-p3-*` to Paper 4.

## Main Results At A Glance

**Training regimen (Paper 2).** SFT induces abstention; DPO and KTO reposition
the boundary after SFT; GRPO amplifies the abstention routine. None escapes the
recall/over-refusal tradeoff. Emitted confidence tracks the decision to answer
more than it tracks truth.

**Internal-vs-stated gap (Paper 3).** On SelfAware, a hidden-state answerability
axis separates known from unknown items at about AUROC 0.997 and can be
well-calibrated by a one-dimensional readout. The model's own stated confidence
is near-flat and barely discriminative. The gap survives DPO, KTO, GRPO,
contrastive SFT, proper-scoring reward variants, and direct attempts to distill
the internal axis into the emitted confidence token.

**Two-signal readout (Paper 4).** A training-free trust pipeline reads two
signals from activations:

- **Gate:** pre-generation answerability, near-ceiling on the base model.
- **Dial:** post-generation answer correctness, strongest after the answer is
  produced.
- **Veto:** the dial assigns confident confabulations low trust; this signal is
  present but higher-variance across models and decodes.

The readout generalizes across Qwen3 sizes and across several model families.
Targeted training can sharpen parts of the signal, but does not create the core
readout.

**Actuation frontier (Paper 5).** Steering and text/prompt interventions show a
sharp distinction between reading a signal, obeying an external directive, and
actually using the model's own readout. Some prompt channels move policy, but
current evidence says they behave like compliance channels rather than internal
belief alignment.

## Repository Map

```text
.
|-- README.md                  # this orientation
|-- TODO.md                    # amendment index + live backlog
|-- docs/
|   |-- research-trajectory.md # current program map; read this first
|   |-- public-artifacts.md    # Hugging Face release manifest
|   |-- sessions/              # lab/session notes and running synthesis
|   |-- architecture/          # design notes for runtime/readout systems
|   `-- review/                # review records
|-- experiment/
|   |-- paper/                 # active paper drafts, figures, analysis tables
|   |-- protocol/              # locked protocol + signed amendments
|   `-- phase1/                # training/eval/probe artifacts and scripts
|-- experiments/               # experiments-first tree for new evidence cells
|-- meta-analysis/             # original systematic synthesis and evidence table
|-- library/
|   |-- notes/                 # one research note per paper/internal result
|   |-- concepts/              # typed method/metric/dataset/model/mechanism atoms
|   |-- SCHEMA.md              # library schema
|   |-- pdfs/                  # gitignored local PDFs
|   `-- fulltext/              # gitignored local HTML/text
|-- datasets/                  # dataset cards, loaders, schemas, and fixtures
|-- synaptic-tuner/            # submodule: generic training/eval infrastructure
`-- scratch/                   # gitignored local work
```

## Knowledge Graph

The default discovery path is the local typed knowledge graph, not broad grep.
Use:

```powershell
bin\search.cmd "query terms" --limit 10
```

Paper notes in `library/notes/` link to atomic concepts in `library/concepts/`
with typed edges such as `proposes`, `evaluates_on`, `measures`, `supports`, and
`uses`. This keeps the literature and internal results queryable by method,
metric, dataset, model, and mechanism.

Useful graph commands:

```powershell
python .agents\skills\knowledge-graph\scripts\validate_kg_relationships.py --root F:\Code\Epistemic-Humility-Research\library
python .agents\skills\knowledge-graph\scripts\analyze_kg.py --root library
python .agents\skills\knowledge-graph\scripts\kg_index.py
```

For paper ingestion, use the repo skill `kg-ingest`; do not add flat paper notes
without concept atoms and typed relationships.

## Experiments And Governance

The old Phase 1 confirmatory protocol is locked:

- [experiment/protocol/PROTOCOL.md](experiment/protocol/PROTOCOL.md)

New evidence-producing work should normally go through the experiments-first or
amendment workflow, depending on the tier:

- use `experiments/` for new standalone evidence cells;
- use signed `experiment/protocol/AMENDMENT-*.md` docs for governed protocol
  extensions;
- use lab/session notes for diagnostics, smokes, reruns, and non-claim work.

Current amendment status and backlog live in [TODO.md](TODO.md). Do not infer
claim status from scratch outputs or local run products; use the signed amendment
docs, result summaries, and paper provenance appendices.

## Running Code

Training and evaluation infrastructure lives in the
[Synaptic Tuner](https://github.com/ProfSynapse/Synaptic-Tuner) submodule:

```powershell
git submodule update --init
cd synaptic-tuner
```

Keep `synaptic-tuner/` generic. Project-specific protocols, paper claims, and
Epistemic-Humility orchestration belong in the root repository, not inside the
submodule.

Before trusting an experimental number:

1. Find the signed amendment, lab note, or paper provenance row.
2. Trace config -> builder/evaluator -> generated file -> trainer/eval loader.
3. Re-run the relevant deterministic analysis script where available.
4. Keep confirmatory, exploratory, and diagnostic results separate.

## Public Artifacts

The repo-side manifest is [docs/public-artifacts.md](docs/public-artifacts.md).
Published artifacts include:

- Phase 1 Qwen3 4B training/dev data.
- Phase 1 evaluation analysis artifacts.
- Phase 1 compact knowledge labels and probe manifests.
- Cloud-lane per-cell readout results.
- Two-signal probe directions.
- Readout row surfaces.
- Amendment AH "doubt on command" exhaust.

Publication is a release gate, not a scratch dump. Do not publish restricted
bridge/OpenMOSS/Cheng raw data, local HF caches, hidden-state tensors, or
unreviewed checkpoints without explicit approval and provenance.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-value contributions are:

- primary-source corrections to evidence rows or paper claims;
- missed literature with precise citations;
- replication of figures, training cells, or graph validations;
- bug fixes to deterministic analysis, dataset, eval, or probe scripts.

Ground rules:

- Every quantitative claim needs provenance.
- Do not edit locked protocols without a signed revision.
- Do not commit restricted or gitignored data.
- Do not hand-edit generated results.
- Keep `synaptic-tuner/` experiment-agnostic.

## Maintenance Notes

This repository is intentionally research-first. Claims should point to evidence,
scripts should be reproducible, and paper prose should not depend on hidden local
state. When in doubt, update the knowledge graph, the paper provenance appendix,
or `docs/research-trajectory.md` rather than adding another untracked scratch note.
