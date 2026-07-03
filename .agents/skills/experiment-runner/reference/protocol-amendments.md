# Protocol Amendments

Use this when experiment work changes or extends a governed protocol surface:
hypotheses, arms, output contracts, metrics, rerun scope, launch matrix,
reporting labels, or interpretation rules.

**First decide whether you even need an amendment.** Not every cell, smoke, or
tweak warrants one. Read [reference/amendment-vs-lab-notebook.md](amendment-vs-lab-notebook.md)
to route the work: a *signed protocol revision* (headline surface / claims), an
*Amendment* (a new exploratory evidence cell), or a *lab-notebook* entry
(smoke / preflight / diagnostic / re-run / tuning within an amendment's authorized
knobs). Reserve amendment letters for new evidence cells and genuine contract
changes; send lighter work to the session note + run record so the amendment
series stays meaningful.

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
python3 bin/sync_skills.py --check --skill experiment-runner
```

## Guardrails

- Do not silently edit a signed protocol to absorb a new arm, metric, or output
  schema.
- Do not label amendment results as v0.3 headline results unless a later signed
  protocol explicitly supersedes v0.3. Amendment cells are **exploratory** until a
  signed protocol revision promotes them; report them separately and never pool
  them with the headline.
- Pre-state a prediction, a falsifier (the result that kills the line), and the
  pass/fail gates BEFORE the run. Do not move the goalposts after seeing the
  result; report ambiguous results as ambiguous.
- **Dual predictions (standing practice, adopted 2026-07-03):** BOTH the
  orchestrator and the user record an independent prediction in the amendment
  doc before launch. State the orchestrator's prediction (with rough
  confidence) FIRST, then elicit the user's in their own words and record it
  verbatim. After resolution, score both in `docs/prediction-scoreboard.md`
  (outcomes per party: WIN / LOSS / TIE — a TIE when the result is ambiguous,
  the gates are voided, or both predictions are equally right/wrong; ties
  score to neither side). Convergent predictions are fine — a result that
  surprises both parties carries full evidential weight and says so in the doc.
  Predictions also live in the doc's YAML **frontmatter** (`predictions:`,
  `outcome:`, `scoreboard:` — see the template) so they are queryable across
  the whole amendment series; update the frontmatter `outcome`/`scoreboard`
  fields at resolution together with the ledger. Frontmatter keys stay
  lowercase (the backlog indexer matches capitalized `Status:` lines).
- Promote an exploratory win to a claim only via a **confirmatory replication**
  registered before running it (fresh seeds, ideally the larger model / held-out
  set). A single-seed win is a lead, not a result.
- A new amendment needs a **distinct mechanistic rationale** from prior attempts.
  If it is only a hyperparameter nudge with the same mechanism, it is lab-notebook
  tuning under the existing amendment. When mechanistically-distinct attempts on
  the same target keep failing, the persistent failure is the finding — write it
  up instead of opening another amendment letter.
- Do not authorize local or cloud launches from an amendment draft alone; launch
  approval must name the exact cells/seeds/lane.
- Do not put project-specific trainer logic into `synaptic-tuner/`; route
  through public tuner interfaces or flag the missing generic capability.

