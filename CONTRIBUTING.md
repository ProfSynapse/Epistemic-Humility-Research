# Contributing

Thanks for your interest in this research program. Contributions,
corrections, and replication attempts are all welcome. This document covers
what kinds of contributions are most useful, how to make them, and the
ground rules that keep the research auditable.

## What's most useful right now

### Evidence corrections (highest value)

The meta-analysis lives or dies on the accuracy of
`meta-analysis/evidence/effects.csv`. Every row carries a source, exact
metric, model, method, URL, and a `verified` flag. If you find a row that
misstates its primary source:

1. Open an issue titled `evidence: <study> <metric>`.
2. Quote the passage (or table cell) from the primary source.
3. Say what the row currently claims and what it should say.

Rows that fail verification get corrected or dropped from pooled
statistics; the raw reports under `meta-analysis/evidence/raw-reports/`
keep the audit trail either way.

### Missed studies

If you know a paper on calibration, abstention/IDK training,
fine-tuning-induced hallucination, sycophancy under preference training, or
knowledge-boundary self-awareness that the search missed, open an issue
with the citation. Inclusion criteria are in the paper's methods section
and the search trail is in `meta-analysis/evidence/prisma-flow.md`. Note
that admission of new studies into the corpus is versioned (the corpus is
frozen per paper revision), so a valid candidate may be queued for the next
revision rather than merged immediately.

### Replication

The analysis scripts are deterministic (data in, figures out) and the
experiment pipeline is built to be re-runnable. If a script doesn't
reproduce a figure, a number, or a test result, that's a bug report we
want. Include your platform, Python version, and the exact command.

### Code

Bug fixes and improvements to the analysis scripts, dataset builders,
probe, and eval harness are welcome as PRs. Training/eval infrastructure
lives in the `synaptic-tuner` submodule, which is a separate repo with its
own contribution flow; changes there must stay experiment-agnostic.

## Ground rules

These are not bureaucracy; they are what makes the papers defensible.

- **The pre-registration is locked.** `experiment/protocol/PROTOCOL.md` is
  a signed pre-registration. PRs must not edit its hypotheses, falsifiers,
  or headline run matrix. Changes of that kind require a new signed
  revision with a changelog, agreed with the maintainer first.
- **Every number needs provenance.** A PR that adds or changes a
  quantitative claim must carry source, exact metric, model, method, and
  URL, and must not hand-edit generated results. Regenerate figures by
  running the scripts.
- **Some data must never be committed.** The OpenMOSS "Say I Don't Know"
  data and everything derived from it (including
  `experiment/phase1/data/bridge_llama2_7b_chat/`) is do-not-redistribute.
  It is gitignored on purpose. Don't commit it, don't publish it to any
  hub, and don't build anything that requires redistributing it. The same
  applies to any dataset whose `dataset.md` license line says so.
- **New datasets need a `dataset.md`.** Source, license, fetch date, and
  schema, following the existing examples under `datasets/`.

## Practical notes

- Run `git submodule update --init` after cloning if you need the training
  infrastructure.
- Large binaries (paper PDFs, full texts, parquets) are gitignored and
  re-fetchable: see the provenance section of the README.
- Tests live alongside the code they cover (`experiment/phase1/*/tests/`,
  `.claude/skills/experiment-runner/tests/`). Please run the relevant suite
  before opening a PR and say in the PR description what you ran.

## Licensing

Code and documentation in this repo are MIT-licensed (see `LICENSE`). By
contributing, you agree your contributions are licensed the same way.
Vendored datasets keep their upstream licenses, recorded in each
directory's `dataset.md`; the MIT license does not apply to them.
