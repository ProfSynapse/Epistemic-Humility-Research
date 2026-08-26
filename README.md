# Epistemic Humility Research

This repository is a research workspace for a single through-line:

**A frozen language model internally represents whether it can answer a
question. Can that representation be read directly, and wired to behavior?**

It is also built to be **read by agents**. Every experimental claim here is
supposed to be walkable, by a model with file access, from a sentence in a
manuscript to a signed pre-registered document and committed artifacts. If you
are reviewing this work, the intended move is not to trust any summary
(including this one): point an agent at the repository and make it find the
signed source of any number. This README is the entry point for that traversal.

## The program in five beats

1. We trained abstention into Qwen3-4B with SFT, DPO, KTO, and GRPO. Training
   moved behavior but never produced honest stated confidence (Paper 2).
2. The model's hidden states separate answerable from unanswerable questions
   near ceiling, while its stated confidence stays flat. The gap survives
   training against it (Paper 3).
3. That internal signal can be turned into deployable training-free readouts:
   a pre-generation answerability gate and a post-generation correctness dial
   (Paper 4).
4. No channel we tested makes the model *use* its own signal: writing the
   readout back, telling the model its reading in words, or paying it via a
   probe-derived reward all fail, and instruction channels turn out to be
   obedience rather than introspection (Paper 5).
5. Closing the loop externally works: a known-unknown probe gates an
   orthogonalized refusal-direction write, converting 73.5% of held-out
   confabulations to clean abstentions at 3.1% known-correct cost on Qwen3-4B,
   with both fake-part controls collapsing the effect. Write depth is its own
   variable (a calibrated mid-band site reaches 89.2% vs 66.5% late), and
   direction-specificity holds in some families and fails in others (Paper 5).

## Reading this repository with an agent

Start here:

| Read | For |
|---|---|
| [docs/research-trajectory.md](docs/research-trajectory.md) | current program map; dated, treat as a map, not a source |
| [papers/paper-5-actuation/manuscript.md](papers/paper-5-actuation/manuscript.md) | the actuation arc (the current front) |
| [experiments/REGISTRY.md](experiments/REGISTRY.md) | every experiment, status, and verdict |
| [experiments/registry.json](experiments/registry.json) | the same as structured data; parse this, do not scrape the markdown |

Graph-aware search is the intended first move, ahead of grep:

```bash
bin/search "known unknown gate write site" --limit 10   # macOS/Linux
bin\search.cmd "known unknown gate write site" --limit 10  # Windows
```

It returns ranked hits with file, line, and typed graph edges, so a claim
surfaces attached to the experiment that supports it.

**One caveat that will bite an agent.** A cell's authoritative status and
verdict live in `experiments/<slug>/experiment.yaml`, not in the `Status:`
line at the top of its `AMENDMENT.md`. That header is hand-written prose and a
few are stale. Parse the YAML; treat the header as commentary.

## The governed record

Every evidence-producing experiment lives in `experiments/<slug>/` with a
signed `AMENDMENT.md` that registers its hypothesis, numeric gate floors,
prediction, and falsifier **before the run**, and an Outcome section written
after. The amendment is the only document an experimental fact may be cited
from; manuscripts, notes, and the knowledge graph are navigation aids over it.
The registry holds 126 experiments as of 2026-08-26, misses reported as
misses: registered predictions that failed stay recorded as failures, and
several cells resolve as falsified or void.

The claim-to-evidence path, in four steps:

1. Take a number from a manuscript or summary.
2. `bin/search` the claim, or find the cell named in its provenance line.
3. Open `experiments/<slug>/AMENDMENT.md`. Read the gates and falsifier first
   (signed before the run), then the Outcome.
4. Check the artifacts under `experiments/<slug>/analysis-committed/`.

If a number cannot be walked to a signed Outcome this way, that is a defect;
report it.

Cells carrying the current actuation headline:

| Step | Cell |
|---|---|
| Find the write site | `j-space-localization-qwen3-4b`, `j-space-midband-dose-calibration-qwen3-4b`, `j-space-calibrated-layer-contrast-qwen3-4b` |
| Wire it together | `doubt-gated-caution-tighten`, `ungated-vs-gated-dose-matched`, `gate-contribution-factorial` |
| Controls and stress | `placebo-seed-distribution-census`, `wide-instrument-control-rescore` |
| Where it fails | `radial-anti-propensity-steering` |

The last two rows are where to start if you are looking for the weak point:
they include cells where the registered falsifier fired.

Questions that most efficiently probe this record:

- Does every headline number resolve to a signed Outcome? List any that do not.
- Were gates and falsifiers registered before each run? Compare sign dates to
  run artifacts.
- Where controls ran (random directions, permuted gates), did a control ever
  reproduce the effect? Find the cells where it did.
- Find every registered prediction the program missed. Are the misses stated
  as misses, or reframed?
- Find results the program itself later corrected or retracted, and what
  triggered each correction. This one has real answers, and it is the most
  useful single probe of whether the record is honest.

The repeatable procedures are written down as skills rather than tribal
knowledge; the two most relevant to the current work are
`.skills/mechinterp-cells/reference/read-then-actuate.md` (the end-to-end
recipe for standing the pipeline up on a new model) and `.skills/family-atlas/`
(the standardized per-family depth sweep run before any actuation attempt).

## Paper line

The canonical paper map is maintained in
[docs/research-trajectory.md](docs/research-trajectory.md).

| Paper | Scope | Draft |
|---|---|---|
| P1 | Taxonomy, evidence synthesis, and the policy-vs-signal framework | [papers/paper-1-taxonomy-framework/manuscript.md](papers/paper-1-taxonomy-framework/manuscript.md) |
| P2 | Training regimen: SFT/DPO/KTO/GRPO for abstention | [papers/paper-2-training-regimen/manuscript.md](papers/paper-2-training-regimen/manuscript.md) |
| P3 | "Knows but Doesn't Say": internal-vs-stated confidence gap and training resistance | [papers/paper-3-knows-but-doesnt-say/manuscript.md](papers/paper-3-knows-but-doesnt-say/manuscript.md) |
| P4 | Training-free two-signal readout: gate, dial, and veto | [papers/paper-4-two-signal-readout/manuscript.md](papers/paper-4-two-signal-readout/manuscript.md) |
| P5 | "Look Before You Speak": actuating known-unknown state, and where selectivity comes from | [papers/paper-5-actuation/manuscript.md](papers/paper-5-actuation/manuscript.md) |

Legacy figure prefixes are not paper numbers: `fig-p1-*` currently belongs to
Paper 2, `fig-p2-*` to Paper 3, and `fig-p3-*` to Paper 4. Paper 5's own
figures (`fig-p5-*`) are provenance-pinned in
[papers/paper-5-actuation/figures/MANIFEST.md](papers/paper-5-actuation/figures/MANIFEST.md).

## Repository map

```text
.
|-- README.md                  # this orientation
|-- TODO.md                    # live backlog
|-- docs/
|   |-- research-trajectory.md # current program map
|   |-- public-artifacts.md    # Hugging Face release manifest
|   |-- sessions/              # lab/session notes and running synthesis
|   `-- atlas/                 # per-family layer maps and registries
|-- experiments/               # experiments-first tree: one dir per cell, signed AMENDMENT.md + experiment.yaml
|-- experiment/                # locked training-regimen protocol tree (historical; no new work here)
|-- papers/                    # one directory per paper + common/ conventions + series/ planning
|-- library/                   # typed knowledge graph: notes, concept atoms, schema
|-- datasets/                  # dataset cards, loaders, schemas (raw rows never committed)
|-- .skills/                   # canonical procedures (mirrored into agent-specific dirs)
|-- archive/                   # superseded artifacts retained for provenance
`-- synaptic-tuner/            # submodule: generic training/eval infrastructure
```

## Knowledge graph

Paper notes in `library/notes/` link to atomic concepts in `library/concepts/`
with typed edges such as `proposes`, `evaluates_on`, `measures`,
`supported_by`, and `uses`, keeping literature and internal results queryable
by method, metric, dataset, model, and mechanism. `bin/search` queries it.
Validation, analysis, and indexing commands live in the `knowledge-graph`
skill; paper ingestion goes through the `kg-ingest` skill rather than flat
notes.

## Running code

Training and evaluation infrastructure lives in the
[Synaptic Tuner](https://github.com/ProfSynapse/Synaptic-Tuner) submodule:

```bash
git submodule update --init
```

Keep `synaptic-tuner/` generic. Project-specific protocols, paper claims, and
orchestration belong in the root repository, not inside the submodule.

## Public artifacts

The release manifest is [docs/public-artifacts.md](docs/public-artifacts.md):
trained adapters, probe directions, readout row surfaces, and row-level
generation exhaust published on Hugging Face. Publication is a release gate,
not a scratch dump: dataset question text and restricted sources are never
committed to this public repository, and exhaust uploads pass a license audit
first (where a source license forbids redistribution, the build script and the
audit are published instead of the rows).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-value contributions are
primary-source corrections to evidence rows or paper claims, missed literature
with precise citations, replication of figures or cells, and bug fixes to
deterministic analysis, dataset, eval, or probe scripts.

Ground rules:

- Every quantitative claim needs provenance.
- Do not edit signed protocols or amendments without a governed revision.
- Do not commit restricted or gitignored data.
- Do not hand-edit generated results.
- Keep `synaptic-tuner/` experiment-agnostic.
