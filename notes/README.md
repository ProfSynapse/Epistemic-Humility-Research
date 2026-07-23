# Notes Layout

Use note type to choose the home:

- `docs/sessions/` is the chronological research log: one append-only session
  note per work session, timestamped by `session_id`.
- `library/notes/` is for literature notes and internal synthesis notes in the
  typed knowledge graph. These are evidence/context atoms, not runbooks.
- `papers/<paper>/notes/` is for paper-specific planning, citation audits,
  framing notes, and reviewer-response scratch.
- `experiments/<slug>/NOTEBOOK.md` is the lab log for one governed experiment.
- `experiments/<slug>/RUNBOOK.md` and `experiments/<slug>/PLAN.md` are the
  reusable operational specs for a governed experiment.

Do not put governed experimental facts only in this top-level notes tree. For an
experiment result, the source of truth remains `experiments/<slug>/AMENDMENT.md`;
notes can point to it or summarize cross-cutting context, but experiment-local
runbooks and plans belong beside the experiment they operate.
