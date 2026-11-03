# Model-independent weight-editor research workflow

Status: proposed execution contract, not a qualified editor runner or launch
order. Further GPU work remains held for the user's strategy discussion. The
existing deterministic hs20 sweep is a draft pilot, not an implementation of
this agent-led discovery process. Do not relabel it as an Astra run.

## Separate workflow from study

The reusable workflow has a model adapter, a host-owned policy/experiment broker,
and an append-only recorder. No experiment logic branches on a model name. A
study manifest selects the editor provider/model and supported settings. Changing
that selection creates a new editor condition with separate results.

For this research the user chose the same named editor as the source report:
`gpt-6-astra`. The paper's Experiment8 used reasoning effort `max`; propose the
same effort here and freeze it before qualification. Record requested and returned
model identity, provider profile, client version, time, settings, prompts and
source hashes. An alias is not proof of an immutable provider snapshot. A missing
setting/model must fail selection; no fallback to another model or effort.

The Qwen3.5-4B humility target, task and registered budgets differ from the
paper's Qwen3.5-0.8B math task. Matching the editor alone is not exact replication.

## Research and skill ownership

- `kg-ingest`: source report/logs, reconciled typed research nodes and retrieval.
- `experiment-runner` and `experiments`: lead-owned hypothesis, adaptive discovery
  envelope, split, budgets, stop conditions, predictions, gates and signing.
- `mechinterp-cells`: qualified capture, interventions, weight inspection, patch
  validation/export and private row outputs through the installed host boundary.
- `data-exhaust`: retain row text, token IDs, full grades and lineage privately.
- The editor: diagnose, request permitted evidence, explain and propose edits,
  compare development evidence, and select a final patch within the envelope.
- The host broker: validate requests, reserve budget, execute admitted jobs,
  validate returned evidence, retain receipts and halt on failures.
- The lead and separate evaluation lane: freeze the final choice, control
  construction, blinded grading, registered roll-up, verdict and publication.

A skill/prompt states the scientific rules. The host must enforce permissions,
budgets, paths, hashes and stage ordering independently of model compliance.
There is no per-query human approval requirement inside an already-authorized,
signed envelope. Outside-envelope requests halt instead of expanding authority.

## Inputs and permissions

Give the editor a hash-frozen input capsule, not the research checkout. Include
only selected source material, approved prior research, model metadata/weight
views and development inputs. Exclude held-out rows, their IDs/roles/prior item
outcomes, grader keys, secrets, current acceptance outputs, and host credentials.
The old pools have historical exposure; disclose reuse without exposing their
item-level results to the editor.

Use opaque development IDs resolved by the broker. A model-provided absolute path,
URL or arbitrary command is not an artifact reference. The editor cannot add
sources, expand pools, inspect evaluation storage or change protocol files.

A provider adapter must establish its available native tools and file/network
access. Ordinary subagent instructions, read-only working-directory conventions
and `synaptic.yaml` intent keys are not OS isolation. T3 model/session availability
alone does not qualify an experimental tool boundary or complete transcript
export. If an adapter cannot restrict access and retain complete emitted traffic,
it is unqualified for this study. No silent switch to a different adapter.

## Editor loop and broker requests

The state machine is:

`registered -> discovery -> final_patch_frozen -> independent_evaluation -> closed`

During discovery, the proposed request families are:

1. `inspect_weights`: bounded numeric reads over admitted tensors.
2. `analyze`: CPU-only tensor analysis in a qualified isolated workspace; no
   direct model server, GPU, network or host-shell authority.
3. `query_development`: registered generation/capture/intervention requests over
   admitted development IDs and decode settings, executed by the broker.
4. `propose_patch`: a new hash-bound patch plus its mechanistic justification,
   expected benefit, expected known-item cost and falsifying observation.
5. `compare_development`: approved paired summaries, controls and cost measures.
6. `freeze_patch`: choose one exact candidate or record no suitable edit.

These are proposed broker operations, not new stable Tuner API v1 methods. Reuse
`engine_host` and the pinned generic MechInterp CLI; import no engine internals.
Write/validate a patch in a separate artifact namespace. Keep base weights
read-only. Apply tensor, dtype, finite-value, support and realized-delta limits
before any candidate generation. Every proposal remains in the ledger, including
invalid, rejected, abandoned and reverted ones.

The discovery algorithm can be adaptive, but its allowed operations and resource
limits must be signed before feedback. Replace the old fixed-sweep registration
with that explicit envelope before calling this agent-led research. Exact
forward-query, prompt/token, model-turn, CPU-analysis, proposal and GPU-hour caps
need registration. A 'forward pass' is a batched request, not one example; cap
both calls and examples/tokens, including smoke/wiring probes and retries.

No gradients, optimizers, training or fitting a loss are permitted for this
study. A general Python sandbox alone cannot prove the absence of hand-written
fitting or forward simulation. Its code, operations and outputs require a
registered scientific audit. Mechanical permission checks and that audit must
not be presented as equivalent guarantees.

Freeze the final patch, selection rationale, development evidence, controls,
budget ledger and transcript root hash before evaluation. The editor has no
transition back to discovery after held-out feedback. Evaluation does not share
its mount, data or messages with the editor conversation. A later improvement is
a separately registered run.

## Transcript is an experimental artifact

Retain the editor's run itself separately from the target model's generated rows.
The recorder must persist before advancing to the next effect:

- All supplied prompts/instructions, input capsule and registered skill/config
  hashes, and exact model-visible tool results.
- Raw provider-emitted events and ordered user/assistant messages, visible
  explanations and provider-exposed reasoning summaries when present.
- Every tool request, validation decision, reservation, dispatch ID, result,
  refusal, exception category, cancellation, timeout and retry.
- Every code fragment, file/artifact reference, patch payload and validation
  receipt, plus before/after/checkpoint hashes and selection/rejection reasons.
- Provider session/turn/item IDs, timestamps, available usage, finish reason,
  requested/returned model identity and settings.
- Context truncation, compaction, handoff/resume capsules, parent/child session
  links, continuation offsets and all earlier context needed to reconstruct what
  each call received. No silent summarization or missing-page exports.

Do not claim capture of hidden internal reasoning. Require an explicit visible
proposal justification as part of the research protocol instead. Preserve every
provider-exposed summary as received, without fabricating unavailable content.
Do not save auth headers, tokens, secret values or the host's entire environment.

Keep raw provider events and a normalized journal. A normalization must not drop
unknown events; retain raw references and mark unsupported/incomplete capture.
Every record carries editor-run ID, sequence number, previous-record digest,
event digest and linked request/dispatch/artifact IDs. Flush append records
incrementally. A terminal manifest binds the complete transcript and artifacts.
A crash leaves an incomplete run, never a success inferred from a final message.

Retain a readable Markdown transcript as a derived view of that journal. It must
link code, exact tool output and artifact receipts. A T3 UI conversation or a
final-answer summary alone is insufficient. The T3 activity reader exists, but
its lossless export, pagination and resume semantics still need qualification.
The installed Codex CLI documents JSONL events; availability of `--json` does not
prove that a selected adapter exports every required field or is isolated.

Suggested private layout under a project on T7 E:, all below `.synaptic/`:

```text
artifacts/<experiment>/editor/<editor-run-id>/
  manifest.json
  capsule/manifest.json
  provider/events.jsonl
  journal/events.jsonl
  transcript.md
  turns/<turn-id>/
  proposals/<proposal-id>/
  requests/<request-id>/
  artifacts/manifest.json
  budget.jsonl
  final_selection.json
```

The readable transcript and raw editor messages can contain private research
inputs. Keep them private on T7 with the model/checkpoints. Public Git gets only
permitted IDs, hashes, aggregate evidence and sanitized summaries. Nexus keeps
work state and artifact references, not row text or raw transcripts. Transcript
retention does not authorize publishing or training on it.

## Required qualification before a live research editor

Use synthetic inputs and a fake model adapter first. Check that a request cannot
cross the data split, alter gates, write base/source files, overrun budgets, use
an unadmitted model/backend, or invoke arbitrary host tools. Check the transcript
contains exact input/output for valid and rejected requests, an artifact change,
provider failure, cancellation, unknown event and a handoff.

SIGKILL after a durably recorded dispatch, then resume. There must be no duplicate
GPU dispatch or lost budget charge. An ambiguous in-flight request requires
reconciliation by dispatch ID rather than automatic resubmission. Verify transcript
prefix/hash-chain integrity and exact raw-event retention. Separately prove raw
traffic replay can reconstruct the human-readable transcript and all patch/query
receipts; live hosted-model outputs are not claimed to regenerate bit-for-bit.

Only then use a short captured Astra qualification with synthetic public inputs,
followed by the signed real discovery envelope. Do not treat model availability,
a fake-adapter test, or a captured final answer as live qualification.

## Source references

- Author experiment protocol: https://github.com/RikiyaT/lm_understand-logs/blob/main/exp8_math/README.md
- Retained source ingest: `library/notes/web-20261102--sparks-weight-space-programming.md` on canonical EHR main.
- Existing engine boundary: `docs/architecture/tuner-api-v1-migration.md`.
- Official event-stream documentation: https://developers.openai.com/codex/noninteractive/
