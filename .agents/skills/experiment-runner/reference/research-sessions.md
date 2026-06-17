# Research Sessions

Use this when experiment work needs durable episodic memory: gates, launches,
blockers, results, handoffs, or decisions that explain where the research
trajectory is and how it got there.

Do not save every local read/edit/test trace as a session. Keep sessions to
meaningful checkpoints.

Workflow:

1. Read `reference/research-session-template.md`.
2. Fill out the template as a Markdown note with YAML frontmatter.
3. Save it under `docs/sessions/0001 - <session-title>.md`.
4. Add checkpoints as the experiment workflow progresses.
5. Validate before committing:

```bash
python3 .agents/skills/experiment-runner/scripts/research_session.py validate docs/sessions
```

Runner commands can append checkpoints once the session note exists:

```bash
python3 .agents/skills/experiment-runner/scripts/run_matrix.py \
  --check-only \
  --lane local \
  --session docs/sessions/<session-id>.md
```

The pre-commit hook also validates session notes when `docs/sessions/` exists.
