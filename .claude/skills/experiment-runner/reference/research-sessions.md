# Research Sessions

Use this when experiment work needs durable episodic memory: gates, launches,
blockers, results, handoffs, or decisions that explain where the research
trajectory is and how it got there.

Do not save every local read/edit/test trace as a session. Keep sessions to
meaningful checkpoints.

Allowed checkpoint kinds:

- `planning`: intended plan, matrix choice, or work-session setup before action.
- `gate`: prerequisite, safety, count, or readiness gate result.
- `launch`: actual run or job launch event.
- `observation`: factual observation from logs, artifacts, metrics, or traces.
- `decision`: durable choice that changes what happens next.
- `result`: completed run, analysis, or workflow outcome.
- `blocker`: issue that prevents progress until resolved.
- `handoff`: state transfer to another worker, phase, machine, or future session.
- `checkpoint`: generic state marker when a more specific kind does not fit.
- `recovery`: restart, resume, repair, or rollback after interruption or failure.
- `validation`: verification check, audit result, or independent confirmation.
- `heartbeat`: brief liveness/progress marker for long-running work.
- `interpretation`: meaning assigned to results, patterns, or evidence.
- `amendment`: correction or update to an earlier checkpoint or session claim.
- `infrastructure`: environment, tooling, dependency, or platform change relevant to the research run.

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
  --title "<Session Title>" \
  --question "<What workflow state or research question is this tracking?>" \
  --tag experiment-runner
```

4. By default, the helper saves the note under
   `docs/sessions/YYYYMMDDTHHMMSSZ-<title-slug>.md` and uses the same stem as
   `session_id`. The timestamped stem is both the multiplayer-safe sort key and
   the durable machine identity. You may pass `--session-id` when resuming or
   intentionally naming a known thread, but do not append a second date suffix.
   Legacy numbered filenames remain valid for existing notes and can still be
   requested with `--filename-mode numbered`, but do not use them for new work.
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

Validation enforces that every `session_id` is unique across `docs/sessions/`.
Legacy filename sequence numbers are not treated as identity and may collide in
old notes during migration; new notes should use the timestamped filename form so
that filename collisions do not occur in parallel branches.
