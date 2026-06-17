# Research Sessions

Use this when experiment work needs durable episodic memory: gates, launches,
blockers, results, handoffs, or decisions that explain where the research
trajectory is and how it got there.

Do not save every local read/edit/test trace as a session. Keep sessions to
meaningful checkpoints.

Workflow:

1. Read `reference/research-session-template.md`.
2. At the START of meaningful experiment work, create the session note stub
   before implementation or launch work begins. Do this when the work is likely
   to produce durable decisions, protocol amendments, infrastructure, gates,
   launches, blockers, results, or handoffs. If you realize mid-session that the
   work has crossed that threshold, create the stub immediately and add a
   catch-up planning checkpoint.
3. Prefer the helper so numbering, timestamps, and frontmatter are valid:

```bash
python3 .agents/skills/experiment-runner/scripts/research_session.py init \
  --session-id <lowercase-session-id> \
  --title "<Session Title>" \
  --question "<What workflow state or research question is this tracking?>" \
  --phase phase1 \
  --tag experiment-runner
```

4. Save it under `docs/sessions/0001 - <session-title>.md` or the next
   available number. If another unmerged machine already used the next number,
   intentionally skip ahead to avoid filename collisions.
5. Add checkpoints as the experiment workflow progresses.
6. Validate before committing:

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
