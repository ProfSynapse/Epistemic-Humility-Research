# Experiment Provenance Cleanup Proposal

Status: implemented cleanup record, not a protocol amendment.

Session: `docs/sessions/20260708T171528Z-experiment-provenance-cleanup-architecture.md`

Implementation status:

- `research_session.py init` now defaults to
  `docs/sessions/YYYYMMDDTHHMMSSZ-<title-slug>.md`, with the same stem as
  `session_id` when `--session-id` is omitted.
- `research_session.py init --filename-mode numbered` remains available for
  legacy compatibility.
- session validation now enforces unique `session_id` values across
  `docs/sessions/`.
- `bin/exp new <slug> --type <t>` remains the experiment scaffold command and
  now stamps `created_at` into new manifests.
- `provenance_audit.py` inventories session identity debt, legacy amendments,
  experiments-first manifests, and references across repo reference files,
  including `library/`.
- `migrate_legacy_amendments.py --apply` migrated all 40 legacy amendment files
  into `experiments/<slug>/` as `type: historical-amendment`,
  `status: historical` records, wrote `docs/migration/experiment-path-map.json`,
  and rewrote active references across `docs/`, `experiment/`, `experiments/`,
  `library/`, skill docs, and scripts.
- Post-migration audit: 52 experiments-first manifests, 0 legacy amendment files,
  0 active legacy amendment link targets. Remaining legacy paths are
  compatibility metadata only: migration map, test fixtures, generated registry
  metadata, and imported manifest `legacy.path`.
- `migrate_sessions.py --apply` migrated 49 legacy numbered session-note files
  into timestamped stems, wrote `docs/migration/session-path-map.json`, preserved
  prior identity under `legacy_session`, and rewrote live references across the
  repo.
- Post-session audit: 51 session files, 0 legacy numbered filenames, 0 duplicate
  session IDs, 0 serial-only session IDs, 0 active numeric shorthand session
  references. Remaining numeric shorthand references are compatibility examples
  inside the migration tool and its tests.
- `bin/build_backlog_index.py`, project instructions, README, prediction
  scoreboard query, backlog plan, library provenance notes, and AP instrument
  comments now point at experiments-first records. AP instrument pins were
  refreshed after comment-only path updates.
- Paper production now lives under top-level `papers/`, one directory per paper
  with local `manuscript.md`, `analysis/`, `figures/`, `scripts/`, and `notes/`.
  Superseded paper drafts and retired inventories live under visible `archive/`
  rather than a hidden dot-directory.
- Experiment-family runbooks/plans now live beside their experiments under
  `experiments/<slug>/`; unresolved or superseded top-level experiment notes
  live under `archive/notes/experiments/`. The chronological log remains
  `docs/sessions/`, and KG literature/internal synthesis notes remain under
  `library/notes/`.
- Cross-cutting protocol documents now live under `docs/protocols/`; superseded
  protocol-era planning documents live under `archive/docs/protocol/`; the
  AK launch plan moved beside its governed experiment at
  `experiments/commitment-point/PLAN.md`.

## Problem

The repo had two experiment-governance eras:

- legacy governed amendments under `experiment/protocol/AMENDMENT-*.md`
- experiments-first records under `experiments/<slug>/`, with `experiment.yaml`,
  `AMENDMENT.md`, `NOTEBOOK.md`, pinned instruments, and generated registries

That split was workable, but the naming conventions carried single-player
assumptions. The pre-migration tree showed the failure mode:

- `docs/sessions/` contains duplicate filename sequence numbers:
  `0003`, `0009`, `0010`, `0031`, `0036`, and `0043`.
- two session notes share the same frontmatter `session_id: '0031'`.
- new experiments mostly use semantic slugs, but some continue the legacy
  amendment-letter habit (`ao-`, `ap-`, `aq-`), which reintroduces "next letter"
  coordination into a branch-per-experiment workflow.
- many paper drafts, notes, sessions, and amendments cite each other by exact
  path, so mass renames would break provenance and create unnecessary review
  noise.

The cleanup should make future work multiplayer-safe and end with one clean,
experiments-first organization. Legacy paths are migration inputs, not permanent
architecture.

## Recommendation

Use stable semantic IDs for identity, generated registries for order, and
timestamped filenames for append-only session memory. Do not use global sequence
numbers or amendment letters as primary IDs for new work. Migrate legacy
amendments into `experiments/<slug>/` in controlled batches, with audited
reference updates across `docs/`, `experiment/`, `experiments/`, `library/`, and
skill docs.

Concretely:

1. Treat existing legacy amendment paths as source records to migrate, not as the
   long-term home. (done for all `AMENDMENT-*.md` files)
2. Treat `experiments/<slug>/experiment.yaml:slug` as the canonical ID for all
   evidence-producing work.
3. Retire new amendment letters. If a historical letter is needed, store it as
   an alias/display label, not as the filename or ID.
4. Change future session-note filenames from
   `0001 - <title>.md` to a collision-resistant UTC timestamp form:
   `YYYYMMDDTHHMMSSZ-<title-slug>.md`.
5. Keep `session_id` equal to that generated filename stem by default, for
   example `20260708T143012Z-experiment-provenance-cleanup`, not `0044`.
6. Generate human-readable order from frontmatter (`created_at`, `session_id`)
   instead of encoding order into filenames.
7. Preserve provenance during migration with generated/manually reviewed mapping
   tables from old path to new path, then update all references in one batch per
   migrated cluster.

## Identity Model

### Experiments

Canonical ID:

```yaml
slug: doubt-gated-caution-tighten
```

Canonical path:

```text
experiments/doubt-gated-caution-tighten/
```

Optional compatibility fields:

```yaml
aliases:
  - amendment-ac
legacy_label: AC
```

Rules:

- The slug is the durable ID. It must be semantic, lowercase, and unique.
- `legacy_label` is only for migrated or transitional records. It is not a
  reservation mechanism and not required for new experiments.
- New slugs should not start with a bare amendment-letter prefix such as `ar-`
  solely to claim a sequence slot.
- The generated registry may sort by slug today, but a later registry can add
  `created_at` or `signed_at` once the schema supports it. Ordering remains a
  view, not identity.

### Session Notes

Canonical ID:

```yaml
session_id: 20260708T143012Z-experiment-provenance-cleanup
```

Recommended future path:

```text
docs/sessions/20260708T143012Z-experiment-provenance-cleanup.md
```

Rules:

- `session_id` must be unique across `docs/sessions/`.
- `session_id` should be semantic, not a serial number.
- the filename timestamp is a collision-resistant sort key, not the ID.
- legacy `0001 - title.md` filenames remain only as compatibility fixtures or
  historical `legacy_session.path` metadata.

## Migration Strategy

### Phase 0: Audit Only

Added an audit command that reports, without rewriting:

- duplicate session filename sequence numbers
- duplicate `session_id` values
- session notes with serial-only IDs
- new experiment slugs that appear to reserve legacy amendment letters
- links to legacy amendment files and new `experiments/<slug>/AMENDMENT.md`
- reference counts by top-level area, especially `library/`, because literature
  notes and KG-adjacent prose can cite experiment records too

This phase gave agents a complete map before path migration landed.

### Phase 1: Tool Hardening

Updated the session helper and validator:

- default new session filenames to `YYYYMMDDTHHMMSSZ-<title-slug>.md` with the
  same generated stem as `session_id` (done)
- validate uniqueness of `session_id` across a directory (done)
- allow legacy filenames during migration

Updated the experiments helper:

- document that letters are retired for new work
- stamp `created_at` when scaffolding a manifest (done)
- keep semantic slugs as the only required identity field

### Phase 2: Migration Map And Bridge Indexes

Created generated or manually audited bridge indexes before moving historical
files:

```text
docs/migration/experiment-path-map.json
docs/migration/session-path-map.json
```

The legacy amendment index should record only navigation metadata:

- legacy label (`AN`)
- canonical path
- title/slug from frontmatter or heading
- status if already present in frontmatter
- successor experiment slug if the old line was continued under
  `experiments/<slug>/`

The migration map is the operational source for path rewrites:

```json
{
  "experiments/selected-setpoint-regulator/AMENDMENT.md": "experiments/selected-setpoint-regulator/AMENDMENT.md"
}
```

It should not restate results unless those result summaries are generated from
existing governed docs.

### Phase 3: Batch Legacy Amendment Migration

Moved legacy amendments into `experiments/<slug>/`:

1. For each legacy amendment, create an experiments-first directory with:
   `experiment.yaml`, migrated `AMENDMENT.md`, `NOTEBOOK.md`, `.gitignore`, and
   any local config/gate placeholders needed for validation.
2. Preserve the original legacy label in compatibility metadata/prose
   (`legacy_label: AN`, `aliases: [amendment-an]`) but do not make it the
   canonical ID.
3. Carry over existing frontmatter fields where present (`status`, `question`,
   `prediction`, `falsifier`, `outcome`) into the manifest shape where the schema
   supports them; leave uncertain fields blank rather than inventing provenance.
4. Update references using the migration map across all repo reference files,
   including `library/`.
5. Leave a short tombstone or generated index entry at the old location only for
   the transition PR if needed. The desired final state is no active legacy
   amendment files outside `experiments/`.
6. Run audit again and require the moved batch to have zero references to the old
   paths before merging.

Applied migration note: the implementation migrated all 40 legacy amendments in
one scripted pass after a dry-run audit. Each imported manifest is
marked `historical-amendment` / `historical` and includes
`migration.needs_manual_review` for fields that should be filled only after
hand-reading the migrated `AMENDMENT.md`: falsifier, exact experiment type,
instrument configs, and KG ids.

### Phase 4: Documentation Cleanup

Updated project instructions and skills:

- `.skills/experiment-runner/reference/research-sessions.md`
- `.skills/experiment-runner/reference/protocol-amendments.md`
- `.skills/experiments/SKILL.md`
- `experiments/<slug>/RUNBOOK.md` / `PLAN.md` when reusable operating notes
  need local experiment context

The docs now say:

- old path references are compatibility provenance, not the active source of truth
- new work cites `experiments/<slug>/AMENDMENT.md`
- new session notes cite `session_id` plus path on first mention
- exact paths remain acceptable evidence links because they are reviewable in git

### Phase 5: Session Migration

Cleaned session-note identity after experiment records had a stable home:

- renamed old numbered filenames into timestamped stems using the path map
- updated exact and manually reviewed shorthand references across `docs/`,
  `experiment/`, `experiments/`, `library/`, and skill docs
- preserved old identities under `legacy_session`

### Phase 6: Papers, Notes, And Archive

Separated paper production and reusable notes from the historical `experiment/`
tree:

- moved active manuscripts to `papers/paper-*/manuscript.md`
- moved paper-specific analysis, figures, and figure builders into each paper
  folder
- moved paper-specific planning/audit notes into `papers/<paper>/notes/`
- moved superseded paper drafts and retired inventories into `archive/papers/`
- moved reusable experiment-family runbook/planning notes from `experiment/notes/`
  and `notes/experiments/` into experiment-local `RUNBOOK.md` / `PLAN.md` files,
  preserving unresolved or superseded notes under `archive/notes/experiments/`
- moved protocol-era docs out of `experiment/protocol/` into `docs/protocols/`,
  `archive/docs/protocol/`, or experiment-local planning docs, with
  `docs/migration/protocol-path-map.json`
- moved low-risk committed Phase 1 probe result JSONs into their owning
  `experiments/<slug>/artifacts/` directories, with
  `docs/migration/phase1-probe-result-artifact-map.json`
- wrote `docs/migration/paper-path-map.json` and
  `docs/migration/notes-path-map.json`
- updated CI, pre-commit, KG schema docs, skill docs, README, AGENTS/CLAUDE, and
  paper figure builders to the new homes

## What Not To Do

- Do not perform future mass migrations without an audit map, explicit
  compatibility metadata, and zero active old-path references at the end.
- Do not use a central "next amendment number" file as the primary fix. It only
  moves the merge conflict to a different file and still requires serialized
  claiming.
- Do not make PR numbers the experiment ID. PR numbers are useful metadata, but
  they are assigned after branch work already began.
- Do not duplicate governed results into a new index by hand. Indexes should
  navigate to source documents, not become a second claims surface.

## Open Decisions

1. Should future experiment manifests also gain `signed_at` and `created_by`
   fields, now that `created_at` is stamped at scaffold time?
2. Should session timestamp filenames be flat under `docs/sessions/`, or grouped
   by year/month once the directory gets larger?
3. Should the experiments CLI merely warn on letter-prefixed slugs, or reject
   them unless `--legacy-label` is explicitly supplied?
4. Should bridge indexes be generated from frontmatter only, or is a one-time
   manually curated legacy amendment map acceptable?

## Near-Term Cleanup Checklist

1. Land this cleanup doc and the planning session note. (done)
2. Add read-only audit output for current duplicate session IDs, sequence
   numbers, legacy amendments, experiments-first manifests, and cross-repo
   references including `library/`. (done)
3. Update the session helper to create timestamped filenames for new notes while
   preserving legacy validation. (done)
4. Add a legacy amendment migration map. (done)
5. Migrate legacy amendments into `experiments/<slug>/`. (done)
6. Patch all path references from the migration map, including `library/`. (done)
7. Migrate session filenames/IDs after experiment references are stable. (done)
8. Move paper production to top-level `papers/` and archive superseded drafts.
   (done)
9. Move reusable experiment notes into experiment-local runbooks/plans and
   archive unresolved or superseded top-level notes. (done)
10. Move protocol-era docs out of `experiment/protocol/` and record a path map.
    (done)
11. Move low-risk committed Phase 1 probe result JSONs into experiment-local
    artifact directories. (done)
12. Decide whether to add a generated session registry.
