# Backlog index — design plan

## Problem

`TODO.md` at the repo root went stale (last substantive edit ~2026-06-26, before
roughly 20 amendments landed). The project actually runs on **amendments**:
pre-registered experiment cells under `experiment/protocol/AMENDMENT-*.md`, each
with a `Status:` line and (when run) a `## 8. Result` / `VERDICT:` section,
executed one-at-a-time (one amendment = one branch = one PR, merged before the
next branches). Proposed/queued work accretes in three scattered places —
protocol docs, `docs/sessions/*.md` notes, and the user's memory notes — with no
single prioritized index and no cheap way to keep one current.

## Design decision

**Two files, one generated and one hand-curated, joined in `TODO.md`.**

- `bin/build_backlog_index.py` (stdlib only, deterministic, idempotent) scans
  `experiment/protocol/*.md`, extracts each doc's `Status:` line and any
  `## 8. Result` / `## Result` / `VERDICT:` verdict, classifies it into a small
  fixed status vocabulary, and writes a table between fenced markers inside
  `TODO.md`:

  ```
  <!-- BEGIN GENERATED: amendment-index (do not edit by hand) -->
  ... table ...
  <!-- END GENERATED: amendment-index -->
  ```

  Anything outside those markers is preserved verbatim on every run, so the
  hand-curated backlog and any prose survive regeneration.

- The **hand-curated prioritized backlog** lives in the same `TODO.md`, outside
  the generated fence, under `## Prioritized backlog`. One line per item:
  what / why, tier, blocking dependency, rough cost. Seeded from the survey.

### Why TODO.md rather than a new INDEX.md

`TODO.md` already exists at the repo root and is the conventional first-look
file; splitting into `docs/backlog/INDEX.md` + a pointer adds a hop for no gain.
The generated/curated split is achieved with fence markers *within* one file,
which is the standard idempotent-codegen pattern and keeps everything a reader
wants in one place. `docs/backlog/PLAN.md` (this file) documents the design and
conventions; it is not regenerated.

### Status vocabulary (source of truth = the doc's own `Status:` line)

The script does not consult session notes or PR state — the doc's committed
`Status:` line is what the author committed, and that is what we index. It maps
free-text status prefixes to a fixed set:

| Bucket | Matches (case-insensitive prefix on the Status line) |
|--------|------------------------------------------------------|
| `RESOLVED` | `RESOLVED`, `COMPLETE` |
| `SHELVED`  | `SHELVED` |
| `SIGNED`   | `SIGNED`, `PRE-REGISTERED`, `READY FOR` |
| `DRAFT`    | `DRAFT`, `NOT SIGNED` |

A `VERDICT:`/`## 8. Result` verdict token (SUCCESS / FALSIFIED / PASS / FAIL /
POSITIVE / NEGATIVE / ambiguous), when present in the doc, is extracted into a
separate `Verdict` column. This is deliberately additive: a doc can be `SIGNED`
in its Status line yet already carry a verdict in a later session — that mismatch
is visible in the table rather than silently resolved. (Several run-in-session
amendments — AA, AB — declare `SIGNED` in the doc but their verdicts live in
session notes; the table shows `SIGNED` with an empty Verdict, which is the
honest committed-doc state.)

## Keeping it current (cheap conventions)

1. When an amendment doc's `Status:` line or `## 8. Result` changes, re-run
   `python3 bin/build_backlog_index.py --write` and commit the refreshed
   `TODO.md` in the same PR. `--check` (no write, non-zero exit on drift) can
   gate CI/pre-commit later.
2. When a new follow-up is minted in a session, add **one line** to the
   `## Prioritized backlog` section by hand. It is prose, never generated.
3. New amendment docs are picked up automatically by filename glob — no script
   edit needed.

## Files

- `bin/build_backlog_index.py` — the generator (new).
- `TODO.md` — rewritten: generated amendment-status table + hand-curated backlog.
- `docs/backlog/PLAN.md` — this design doc.
- `.skills/experiment-runner/SKILL.md` + `reference/backlog-index.md` — codified
  process, synced to the `.agents`/`.claude` mirrors via `bin/sync_skills.py`.
