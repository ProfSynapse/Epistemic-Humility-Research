# Dataset Schema

An experiment's data exhaust splits into two shapes with different release
rules. Build them separately; they go to two different HF dataset repos.

## Aggregate datasets (always publishable)

Aggregate exhaust is our own computed output over our own activations and our
own generation runs: dose-response tables, layer profiles, direction-fit
metadata, gate/readout AUROCs, and manifests. It never contains source
question text, aliases, or per-row generation text, so it is not gated by
`reference/license-gates.md` and does not need the row-level license check.
One HF dataset per experiment, one config (folder) per cell.

On-disk shape produced by `scripts/build_exhaust_dataset.py` (aggregate mode):

```
<out-dir>/
  README.md                 # dataset card, rendered from the template
  PROVENANCE.json           # top-level provenance block (see below)
  <cell_id>/
    manifest.json            # per-cell file list + sha256 + source mtimes
    dose_fit.json             # verbatim copy of analysis-committed/<cell_id>/dose_fit.json
    gate_fit.json             # verbatim copy
    g0_prep_summary.json      # verbatim copy
    build_manifest.json       # verbatim copy
    split_manifest.json       # verbatim copy (row_key/role/split/source/category_canon only)
    u_d.json                  # direction JSON, verbatim copy
    c_hat.json                # direction JSON, verbatim copy
    random_direction.json     # direction JSON, verbatim copy
    summary.json               # only if the cell has scored held-out (terminal cells)
  <cell_id_2>/
    ...
```

Not every experiment produces every file above; the builder copies whatever
exists under `analysis-committed/<cell_id>/` and records what it found (and
what it expected but did not find) in `PROVENANCE.json`. It never invents a
missing file and never pads a partial cell to look complete.

Each artifact file is copied byte-identical in content (re-serialized with
sorted keys and a trailing newline for determinism) from
`experiments/<slug>/analysis-committed/<cell_id>/`. The builder does not flatten
these into one row-per-line table: the source files have different schemas
per artifact type (a dose sweep report is not shaped like a direction vector),
and forcing them into a single JSON-Lines file with a uniform column set would
either lose structure or require a stringified-JSON escape hatch that most
consumers would have to unpack anyway. Publishing the files as-is, organized
by cell, follows the same pattern already used by `eh-probe-directions` and
`eh-doubt-on-command` (mixed JSON + safetensors artifacts organized by family,
not squashed into one flat table).

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

`PROVENANCE.json` at the top of every built dataset dir carries:

```json
{
  "experiment_slug": "doubt-snap-cross-family-confirmatory",
  "amendment_path": "experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md",
  "repo_commit_sha": "<git rev-parse HEAD at build time>",
  "instrument_config_sha256": {"cell.yaml": "...", "gates.yaml": "...", "model_matrix.yaml": "..."},
  "generation_date": "2026-07-12T00:00:00Z",
  "shape": "aggregate | rows",
  "cells": {
    "<cell_id>": {"files": ["dose_fit.json", "..."], "missing_expected": []},
    "<cell_id_row_shape>": {"n_rows_kept_with_text": 0, "n_rows_kept_text_free": 0}
  },
  "license_gate_excluded": {"<source>": "<int rows dropped entirely (forbidden or pending-audit)>"},
  "sources_present": {"<source>": "<verdict of every source that appears in at least one kept row>"}
}
```

`instrument_config_sha256` is read straight from the experiment's
`experiment.yaml` `instrument.pins` block (the same pins `bin/exp sign`
recorded), not recomputed, so the exhaust always points at the exact signed
instrument. `license_gate_excluded` is present (possibly empty) even on
aggregate builds, since the aggregate builder still runs the hard-exclusion
structural scan. `sources_present` is empty on aggregate builds; on row-level
builds it drives both the README's "License and Attribution" section and
`verify_exhaust.py`'s disclosure check for any `permitted-with-conditions`
source.
