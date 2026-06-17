# Protocol Amendments

Use this when experiment work changes or extends a governed protocol surface:
hypotheses, arms, output contracts, metrics, rerun scope, launch matrix,
reporting labels, or interpretation rules.

Protocol amendments are separate from durable session notes:

- an amendment is the governed research contract
- a session note is the episodic record of how the work unfolded

## Workflow

1. Start a research session note first when the amendment work is expected to
   produce durable protocol decisions. See `reference/research-sessions.md`.
2. Read the active protocol and any existing amendments that the new amendment
   touches.
3. Copy or follow `reference/protocol-amendment-template.md`.
4. Save the amendment under `experiment/protocol/AMENDMENT-<LETTER>-<slug>.md`.
5. Mark the status explicitly:
   - `DRAFT / NOT SIGNED`
   - `READY FOR USER SIGN-OFF / NOT SIGNED`
   - `SIGNED OFF` with approval date
6. State the relationship to prior protocol documents. Be explicit about what
   does and does not supersede the locked matrix or prior amendments.
7. Include a rerun/launch policy. If old artifacts cannot answer the new
   measurement question, say so directly.
8. Add a checkpoint to the session note with the amendment path as evidence.
9. Validate sessions and skill sync before publishing:

```bash
python3 .agents/skills/experiment-runner/scripts/research_session.py validate docs/sessions
python3 sync_skills.py --check --skill experiment-runner
```

## Guardrails

- Do not silently edit a signed protocol to absorb a new arm, metric, or output
  schema.
- Do not label amendment results as v0.3 headline results unless a later signed
  protocol explicitly supersedes v0.3.
- Do not authorize local or cloud launches from an amendment draft alone; launch
  approval must name the exact cells/seeds/lane.
- Do not put project-specific trainer logic into `synaptic-tuner/`; route
  through public tuner interfaces or flag the missing generic capability.

