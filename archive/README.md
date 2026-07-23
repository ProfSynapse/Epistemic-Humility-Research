# Archive

This directory holds superseded source files that should stay available for
provenance but should not be treated as the active home for new work.

Rules:

- Prefer visible `archive/` over a hidden `.archive/` so agents and reviewers can
  discover it.
- Keep a migration map in `docs/migration/` whenever files move here.
- Do not cite archive files as current sources of truth unless the citing text
  explicitly says it is referring to a superseded or retired artifact.
- Do not put generated caches or private run outputs here; use existing
  gitignored analysis/output locations for those.
