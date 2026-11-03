# Model-independent weight editor

Use this prospective workflow when an LLM inspects model internals, proposes
weight edits and receives bounded development feedback. It is distinct from a
fixed sweep and from a normal coding subagent with unrestricted host tools.

Read `docs/architecture/weight-editor-research-workflow.md` first. It is a proposed
contract; the model adapter, broker and transcript recorder are not yet qualified.
Do not launch an editor from this reference alone.

- Keep the reusable workflow independent of the chosen model. The study pins its
  editor identity/settings in configuration. This research selects `gpt-6-astra`
  to match the named editor in the source report; other models are separate
  study conditions, with no silent fallback.
- The lead signs an adaptive discovery envelope, hypotheses, splits, constraints,
  budgets and final gates before feedback. The editor operates inside that
  envelope and cannot edit the registration, expand access or view held-out data.
- Enforce permission/storage/budget/stage boundaries in the host broker. Skills
  and prompts alone do not enforce them. Restrict CPU analysis separately from
  the GPU worker; audit code for forbidden training/fitting.
- Use the installed `engine_host` boundary and exact MechInterp CLI pin. No
  imports of tuner internals or writes into the historical submodule.
- Capture the complete emitted editor conversation and tool/effect trail, not
  just target-model rows or a final summary. Keep raw events plus an ordered,
  hash-linked normalized journal, code, receipts, files, failures and handoffs.
- Record visible justifications and exposed reasoning summaries; do not claim
  access to hidden internal reasoning. Private editor transcripts stay on T7.
- Freeze the final patch and transcript root before independent evaluation.
  Do not feed held-out results back into the discovery conversation.
- Qualify synthetic capture, denied requests, budget enforcement, crash/resume,
  dispatch reconciliation and readable-transcript replay before live research.

This supplements existing experiment signing, generation persistence, blinded
adjudication and lead-only verdict rules. It grants no new launch authority and
does not replace any stop gate or authorize publication of private transcripts.
