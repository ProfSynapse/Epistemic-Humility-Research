# Dataset Schema

An experiment's data exhaust splits into two shapes with different release
rules. Build them separately; they go to two different HF dataset repos.

## Aggregate datasets (always publishable)

Aggregate exhaust is our own computed output over our own activations and our
own generation runs: dose-response tables, layer profiles, direction-fit
metadata, gate/readout AUROCs, manifests, and family/experiment-level reports.
It never contains source question text, aliases, or per-row generation text
(`analysis-committed/` is the repo's own containment lane, so nothing that
would need row-level license gating is ever committed there in the first
place), so aggregate builds are not gated by `reference/license-gates.md` and
do not need the row-level license check. One HF dataset per experiment.

On-disk shape produced by `scripts/build_exhaust_dataset.py` (aggregate mode)
is copy-everything: it recursively copies every file under
`experiments/<slug>/analysis-committed/`, at any depth and in whatever layout
that experiment used (a flat set of top-level files, one level of cell
subdirectories, several levels of nested phase/family subdirectories, or any
mix), preserving each file's relative path exactly:

```
<out-dir>/
  README.md                 # dataset card, rendered from the template
  PROVENANCE.json           # top-level provenance block (see below)
  final_report.json         # example: a flat top-level file, copied as-is
  <cell_id>/
    dose_fit.json             # verbatim copy of analysis-committed/<cell_id>/dose_fit.json
    gate_fit.json             # verbatim copy
    ...whatever else exists under this cell's source directory...
  <phase_or_family_dir>/
    <deeper_dir>/
      notes.md                 # non-JSON files copy through unchanged too
```

There is no per-file allowlist and no fixed cell-directory assumption: every
file that is physically present under `analysis-committed/` gets copied,
except the two structural hard exclusions below. This replaces an earlier
version of this builder that only knew a fixed 9-filename list written for
one experiment family (`doubt-snap-cross-family-confirmatory`) and only
descended one level into cell subdirectories -- every other family's
vocabulary (`final_report.json`, `family_report.json`, `calibration_report.json`,
`atlas_summary.json`, `gate_report.json`, flat layouts, deeper nesting) was
silently dropped by that allowlist. A second filter on top of the
`analysis-committed/` containment boundary does not add safety; it only risks
dropping content the boundary already cleared.

Each file is copied byte-for-byte (not re-serialized, not reformatted) from
`experiments/<slug>/analysis-committed/` into `<out-dir>/` at the same
relative path. `PROVENANCE.json`'s `files` map records every relative path
that was copied together with its sha256, so both the builder's own output
and any later consumer can confirm nothing was altered in transit. The
builder does not flatten these into one row-per-line table: the source files
have different schemas per artifact type (a dose sweep report is not shaped
like a direction vector), and forcing them into a single JSON-Lines file with
a uniform column set would either lose structure or require a
stringified-JSON escape hatch that most consumers would have to unpack
anyway. Publishing the files as-is, mirroring the source layout, follows the
same pattern already used by `eh-probe-directions` and `eh-doubt-on-command`
(mixed JSON + safetensors artifacts organized by family, not squashed into
one flat table).

### Hard exclusions (structural, not just a table entry)

Two categories are excluded regardless of anything else: OpenMOSS/Cheng IDK
data and `bridge_llama2_7b_chat`. These are enforced in code
(`scripts/build_exhaust_dataset.py`, `scripts/verify_exhaust.py`), the same
way as for row-level datasets, and apply in two ways during an aggregate
build:

- **Path-level match** (a file's relative path under `analysis-committed/`
  contains one of the excluded patterns): the file is skipped -- not
  copied -- and recorded in `PROVENANCE.json`'s `excluded` list as
  `{"path": ..., "reason": ...}`. This is an expected, auditable outcome, not
  a build failure.
- **Content-level match** (an otherwise clean-path file's content contains
  one of the excluded patterns): the build aborts entirely (`SystemExit`),
  since prohibited content appearing inside a directory that is supposed to
  already be public-safe is an anomaly a human needs to look at, not
  something to silently filter out mid-build.

### Completeness

`scripts/verify_exhaust.py --experiment-dir <exp>` independently re-walks the
source `analysis-committed/` tree at verify time (not trusting anything the
builder itself recorded) and requires the staged file set plus the recorded
`excluded` list to equal it exactly, with the differing paths printed on any
mismatch. This is the check that catches a regression to the old
allowlist-style bug: a builder change that silently narrows what gets copied
again would fail this check even if the builder's own `PROVENANCE.json`
looked internally consistent. Omitting `--experiment-dir` is itself a FAIL
for an aggregate build, not a silent skip -- completeness cannot be claimed
without checking it.

## Row-level datasets (license-gated)

Row-level exhaust is per-row generation output: the text our model produced,
what arm/dose produced it, and how it graded. This is gated by
`reference/license-gates.md` because the row's `question`/prompt provenance
traces back to a source dataset whose redistribution terms matter even though
we generated the completion ourselves: the row identifies which licensed
question was asked.

Prior art: `docs/datasets/jspace-fresh-pool-public-census-plan.md`'s "Release
Boundary" section independently reached the same per-source posture for KUQ,
SelfAware, PopQA, and TriviaQA before the task #21 audit ran, and its
published release (`professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`,
via `experiments/j-space-layer-contrast-replication-qwen3-4b/build_hf_public_census.py`)
is the field-naming precedent this schema follows for the text-free category:
`row_key`, gold class/role, `source`, `category_canon`, and text-free
behavior flags (`answered`, `refused`, `correct`, `degenerate`, natural-stop
and token counts). This schema's boolean field names additionally follow this
project's own graders exactly (`experiments/doubt-snap-cross-family-confirmatory/grader.py`'s
`grade_one` and `gen_lib.py`'s `grade_clean_tighten`), rather than inventing
new names, so a row-level dataset's fields are traceable straight back to the
grading code that produced them.

Each source's verdict in `reference/license-gates.md` gives every row one of
three dispositions, decided per row (a mixed-source `rows.jsonl` file can
carry rows in more than one disposition at once):

1. **Full text** (`permitted` / `permitted-with-conditions`): the row keeps
   every field, including the two text-bearing ones. `permitted-with-conditions`
   additionally requires the built README to disclose that source's license
   condition verbatim (see the Provenance block below).
2. **Text-free** (`text-free-only`): the row keeps every field EXCEPT the
   text-bearing ones (`generation_text`, `answer_value` are dropped; nothing
   else is touched).
3. **Excluded** (`forbidden` / `pending-audit`): the row does not appear in
   the output at all, in any form. `pending-audit` (any source with no table
   entry) gets this disposition too, since it is "unaudited," not "audited as
   text-free-safe" -- a genuinely different finding.

Row-level datasets are optional: they only get built when the operator passes
`--rows-dir` pointing at locally staged JSONL (row text for a resolved
experiment typically lives on a Modal volume or an HF Jobs results repo, not
in this git checkout, so staging is a separate, deliberate step before this
builder runs).

Row schema (one JSON object per line). Text-bearing fields
(`generation_text`, `answer_value`) are shown here for the full-text case;
a text-free row omits both and keeps everything else:

```json
{
  "row_key": "triviaqa:tc_123456",
  "source": "triviaqa",
  "category_canon": "triviaqa",
  "role": "known_correct_answered",
  "split": "held_out",
  "cell_id": "llama32_3b_instruct",
  "model": "unsloth/Llama-3.2-3B-Instruct",
  "model_revision": "006f5dcd1393c3add266de40994ba96225e9689d",
  "layer": 27,
  "arm": "gated",
  "dose_or_strength": 42.0,
  "generation_text": "...",
  "answer_value": "...",
  "well_formed": true,
  "n_answer_keys": 1,
  "single_answer_key": true,
  "trailing_clean": true,
  "answered": true,
  "correct": true,
  "well_formed_correct": true,
  "refused": false,
  "semantic_refuse": false,
  "degenerate": false,
  "clean_tighten": false,
  "terminated_naturally": true,
  "seed": 20260707
}
```

Field notes:

- `row_key`: `<source>:<id>` matching the project convention already used in
  `split_manifest.json` (see `experiments/doubt-snap-cross-family-confirmatory/prep_tuner_cell.py`).
- `source` is the field the license gate matches against (case-insensitive,
  aliases included); `category_canon` is the finer-grained source/category
  metadata already used in `split_manifest.json` and the J-space census.
- `cell_id`/`model`/`model_revision` pin exactly which model produced the row;
  never publish a row without its revision.
- `dose_or_strength` is the applied intervention strength (0.0 for baseline).
- `generation_text` (the raw completion) and `answer_value` (the parsed
  answer field extracted by `gen_lib.grade_clean_tighten`) are the ONLY two
  text-bearing fields; they are the ones stripped in the text-free-only
  disposition and the ones the verifier checks for absence there.
- Every other field is a graded boolean or count our own grader already
  produces, never re-derived by the exhaust builder: `well_formed`,
  `n_answer_keys`, `single_answer_key`, `trailing_clean`, `semantic_refuse`,
  `degenerate`, `clean_tighten`, `terminated_naturally` (from
  `gen_lib.grade_clean_tighten`); `answered`, `correct`, `refused`,
  `well_formed_correct` (from `grader.grade_one`). None of these are text.
- `seed` is the generation seed, for reproducibility, not a privacy field.

On-disk shape (row mode):

```
<out-dir>/
  README.md
  PROVENANCE.json
  <cell_id>/
    rows.jsonl               # rows kept full-text or text-free; excluded rows are absent
```

If a cell's rows are entirely excluded by the gate, its folder still appears
with an empty `rows.jsonl` and a note in `PROVENANCE.json`, so the release
manifest is never silently short a cell.

## Provenance block (every dataset, both shapes)

`PROVENANCE.json` at the top of every built dataset dir carries the shared
fields on both shapes, plus one shape-specific field: `files` + `excluded`
on aggregate builds, `cells` on row-level builds.

```json
{
  "experiment_slug": "doubt-snap-cross-family-confirmatory",
  "amendment_path": "experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md",
  "repo_commit_sha": "<git rev-parse HEAD at build time>",
  "instrument_config_sha256": {"cell.yaml": "...", "gates.yaml": "...", "model_matrix.yaml": "..."},
  "generation_date": "2026-07-12T00:00:00Z",
  "shape": "aggregate",
  "files": {"<relative_path_under_analysis-committed>": "<sha256 of the copied file>", "...": "..."},
  "excluded": [{"path": "<relative_path>", "reason": "hard-exclusion: relative path matches a structural pattern"}],
  "license_gate_excluded": {},
  "sources_present": {}
}
```

```json
{
  "experiment_slug": "...",
  "shape": "rows",
  "cells": {
    "<cell_id>": {"n_rows_kept_with_text": 0, "n_rows_kept_text_free": 0}
  },
  "license_gate_excluded": {"<source>": "<int rows dropped entirely (forbidden or pending-audit)>"},
  "sources_present": {"<source>": "<verdict of every source that appears in at least one kept row>"}
}
```

`instrument_config_sha256` is read straight from the experiment's
`experiment.yaml` `instrument.pins` block (the same pins `bin/exp sign`
recorded), not recomputed, so the exhaust always points at the exact signed
instrument. On aggregate builds, `files` is the complete relative-path ->
sha256 map for every file actually copied and `excluded` is the complete
list of files skipped by the path-level hard-exclusion filter (each with a
`reason`); both are exhaustive, not samples, since `verify_exhaust.py`'s
completeness check diffs them against a fresh scan of the source tree.
`license_gate_excluded` and `sources_present` are always present (possibly
empty) on aggregate builds too, since the aggregate builder still runs the
hard-exclusion structural scan; `sources_present` stays empty there because
aggregate builds carry no row-level source text. On row-level builds,
`sources_present` drives both the README's "License and Attribution" section
and `verify_exhaust.py`'s disclosure check for any `permitted-with-conditions`
source.
