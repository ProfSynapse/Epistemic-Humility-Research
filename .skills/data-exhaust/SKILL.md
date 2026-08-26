---
name: data-exhaust
description: Package a terminal experiment's data exhaust (aggregate stats and, where license-permitted, row-level generation text) into reproducible Hugging Face datasets, with a license gate, containment lint, and a thin uploader. Use when an experiment under experiments/<slug>/ reaches a terminal verdict (resolved, null-result, or falsified) and its analysis-committed/ artifacts should be published.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Data Exhaust

An experiment's exhaust is everything worth publishing once it reaches a
terminal verdict: the aggregate artifacts already committed under
`analysis-committed/<cell_id>/` (dose-response tables, direction fits, gate
AUROCs, manifests) and, separately and only where the license permits it, the
per-row generation text. This skill turns that exhaust into HF-ready dataset
directories, gates them, and uploads them. It never decides WHAT an experiment
found; it only packages what the experiment already produced.

## When to use

An experiment has reached a terminal status (`resolved`, `null-result`, or
`falsified` in `experiment.yaml`) and its `analysis-committed/` artifacts, or
locally staged row-level JSONL, are ready to become a public HF dataset. Do
not run this on a `draft`, `signed`, or `running` experiment: there is nothing
terminal to package yet, and publishing mid-run invites goalpost confusion
about what the released data actually represents.

## Build-time requirement (binding on every harness, not just packaging)

Exhaust can only be packaged if the run persisted it. Every generation
harness MUST write, per row or per sample, into its gitignored row-level run
log: the raw generation text, the FULL sub-grade dict its grader computes
(not just the final booleans), and the termination/readback inputs the gate
math consumes. Booleans-only run logs are a build defect: they make failure
anatomy unrecoverable without a paid re-run, and they leave response-quality
problems (degenerate output, format-checker artifacts, batched-decode
misgrading) undetectable after the fact. The cautionary case is
`experiments/snap-seed-sampled-decode-replication` (H3, 2026-07-13): its
grader computed the complete sub-grade dict and the pipeline discarded it,
so the registered falsifier fired with the failure mechanism undiagnosable
from committed artifacts and the resolve PR had to be held for a
text-persisting re-run. Containment is unchanged by this rule: text stays
under gitignored `analysis/`; only ID-manifests and aggregates go to
`analysis-committed/`; publication still runs through the license gate
below. Harness builders and pre-sign reviewers both check this: a CPU smoke
that asserts the persistence schema (text present, sub-grade dict intact)
is part of the standard suite.

This rule is now structurally enforced, not just procedural. Generation
harnesses open their row-level run log through
`experiments/common/runlog_contract.py`'s `open_generation_runlog`, which
refuses to accept any record missing non-empty text unless the harness
declares a `textless_reason` (durably recorded in the log's own meta
fingerprint). `bin/exp validate` separately requires every experiment's
`experiment.yaml` to carry a top-level `text_capture` field
(`enabled`, `not-applicable`, or `textless: <reason>`); a missing or invalid
value is a hard error. `textless:` is the only sanctioned opt-out from
either layer -- there is no way to omit text capture silently.

## Start here

| Task | Do |
|------|----|
| Understand the two dataset shapes and their fields | read [reference/dataset-schema.md](reference/dataset-schema.md) |
| Check or update a source's redistribution verdict | read [reference/license-gates.md](reference/license-gates.md) |
| Build a dataset dir | run `scripts/build_exhaust_dataset.py` (see below) |
| Gate a built dataset dir before upload | run `scripts/verify_exhaust.py` |
| Actually upload | run `scripts/upload_exhaust.py` |

## The five-move workflow

1. **License-gate.** Before building anything with row text, confirm every
   source that will appear has a verdict in
   [reference/license-gates.md](reference/license-gates.md). Each source
   resolves to one of three row dispositions: full text (`permitted` /
   `permitted-with-conditions`), text-free (`text-free-only`, row kept but
   its text-bearing fields stripped), or excluded entirely (`forbidden` /
   `pending-audit`). A source with no table entry is `pending-audit`, the
   most conservative disposition, not the text-free one. Aggregate-only
   builds do not need this step to have resolved verdicts, since they carry
   no source text, but they still run the same structural hard-exclusion
   scan.
2. **Build.** Run `build_exhaust_dataset.py` against the experiment directory.
   Aggregate shape (default) recursively copies EVERY file under
   `analysis-committed/` -- any depth, flat or celled layout -- byte-for-byte
   into `<out-dir>/`, preserving relative paths. There is no filename
   allowlist: `analysis-committed/` is already the repo's containment
   boundary, so the only filter applied is the hard-exclusion deny-list (a
   file whose relative PATH matches OpenMOSS/Cheng IDK or
   `bridge_llama2_7b_chat` is skipped and recorded with a reason; a file
   whose CONTENT matches one aborts the whole build). Row-level shape
   (`--rows-dir <dir>`) reads locally staged `<cell_id>.jsonl` files and
   gives every row one of the three dispositions above, per row, based on
   its own `source` field -- a single `rows.jsonl` can mix full-text and
   text-free rows from different sources. Excluded rows are counted, not
   written in any form. The build never writes inside the experiment's own
   directory; only `--out-dir` is touched.
3. **Verify.** Run `verify_exhaust.py --dataset-dir <out-dir> --experiment-dir
   experiments/<slug>` against the build output. It checks schema/sha256
   consistency, row counts against `PROVENANCE.json`, a containment lint over
   every file (including an independent PER-ROW re-check of each row's
   license-gate disposition, so a file mixing sources only passes if each row
   matches its own source's rule), that any `permitted-with-conditions`
   source's disclosure text actually landed in the README, that
   `license-gates.md`'s machine-readable table is well-formed and still
   carries both hard exclusions, and (aggregate shape) a completeness check
   that independently re-walks the source `analysis-committed/` tree right
   now and requires the staged files plus the recorded exclusions to equal it
   exactly -- omitting `--experiment-dir` FAILS this check rather than
   skipping it silently, so always pass it. A single failure fails the whole
   gate loudly; it does not report a partial pass.
4. **Upload.** Run `upload_exhaust.py --dataset-dir <out-dir>`. Default is a
   dry run: it prints the resolved repo id (`professorsynapse/eh-<slug>` for
   aggregate, `professorsynapse/eh-<slug>-rows` for row-level), the file list,
   and the provenance summary, and touches no network. Pass `--live` only
   after the publication gate below is satisfied, and only with `HF_TOKEN` set
   in the environment (never printed, never logged).
5. **Record.** After a real upload, copy the printed HF revision SHA into the
   experiment's `NOTEBOOK.md` and into `docs/public-artifacts.md` (see that
   file's own row format). An upload without a recorded revision is not
   finished.

## Publication gate

Do not run `upload_exhaust.py --live` until:

1. The experiment's `experiment.yaml` status is terminal (`resolved`,
   `null-result`, or `falsified`), not `draft`/`signed`/`running`.
2. `verify_exhaust.py` passed with zero errors on the exact dir about to be
   uploaded.
3. For a row-level dataset, every source appearing has an explicit
   `permitted`, `permitted-with-conditions`, or `text-free-only` verdict in
   `reference/license-gates.md` -- not `pending-audit`. For any
   `permitted-with-conditions` source, its disclosure text must actually be
   in the built README (verified, not just built).
4. The user has explicitly approved this specific upload. A prior approval
   for a different experiment or a different dataset shape does not carry
   over.

This mirrors the model-artifact publication gate in
`.skills/experiment-runner/reference/hf-publication.md`; that reference stays
the source of truth for model checkpoints, this skill is the analogous gate
for exhaust data.

## Invariants

- The public git repo never receives question text, answer aliases, row-level
  generation text, or token IDs. HF is the sanctioned text channel, and only
  for license-permitted sources. Do not commit a built dataset dir; the
  `--out-dir` you point the builder at should be a scratch location outside
  version control.
- Two hard exclusions apply regardless of anything else: OpenMOSS/Cheng IDK
  data and `bridge_llama2_7b_chat`. These are enforced structurally in code
  (`scripts/build_exhaust_dataset.py` and `scripts/verify_exhaust.py`), not
  only by the license-gates table, so an accidental table edit cannot reopen
  them.
- A source with no entry in `reference/license-gates.md` is `pending-audit`
  (excluded entirely), never `text-free-only` and never permitted. Never
  infer a permissive verdict from a different dataset's card or from memory
  of a prior release.
- `HF_TOKEN` comes from the environment only. Never print, log, or echo it.
- Quick commands:

```bash
python3 .skills/data-exhaust/scripts/build_exhaust_dataset.py \
  --experiment-dir experiments/<slug> \
  --out-dir /tmp/<slug>-exhaust-aggregate

python3 .skills/data-exhaust/scripts/verify_exhaust.py \
  --dataset-dir /tmp/<slug>-exhaust-aggregate \
  --experiment-dir experiments/<slug>   # required for the aggregate completeness check

python3 .skills/data-exhaust/scripts/upload_exhaust.py \
  --dataset-dir /tmp/<slug>-exhaust-aggregate   # dry run by default; add --live once approved
```

## Skill maintenance

Edit the canonical tree under `.skills/data-exhaust/` only. `.agents/` and
`.claude/` are generated mirrors; never hand-edit them. After canonical edits:

```bash
python3 bin/sync_skills.py --write --skill data-exhaust
python3 bin/sync_skills.py --check --skill data-exhaust
```
