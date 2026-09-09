# Bounded chat with a trained model

Status: requested capability; design only, not a runnable deployment.
Verified output retrieval is implemented separately and under review. Chat
serving is not implemented. This plan grants no live resource authorization.
Updated: 2026-09-09.

## User outcome

Select a verified training run, choose local or Modal, and talk to the trained
model. The same inference interface should support evaluation. Starting a chat
session must not publish the model or change the training run's authority.

## Reuse and ownership

The engine's `tuner/handlers/inference_handler.py` has an unfinished vLLM chat
path. `Evaluator/vllm_setup.py` already provides server startup, readiness, and
owned-process shutdown; `Evaluator/openai_compat_client.py` provides the chat
protocol. Extract the reusable lifecycle into a provider-neutral inference
service consumed by both entrypoints. Do not build another inference server.

Keep model, tokenizer, base revision, LoRA settings, chat template, decoding,
GPU requirements, and exact runtime pins in a reviewed profile. The current
evaluator helper contains automatic hardware and model-specific choices; these
must become explicit profile choices for this path, not copied assumptions.

The Host owns selection, credentials, approval, session records, and local
output placement. The engine owns inference contracts and provider adapters.
Keep the fixed Modal training deployment and public training API unchanged.

## Model preparation

Consume the verified retrieval inventory. Recheck bytes while materializing
the model and tokenizer archives into private session scratch. Reject traversal,
links, extra files, malformed tensors/configuration, and base revision mismatch.
Prove the adapter and tokenizer load before reporting a ready session. Retrieval
alone is not this proof. For Modal, obtain the same authenticated run inventory
without trusting mutable Volume paths. Materialize from the dedicated Volume
into private Sandbox scratch on the provider, then verify selected bytes before
loading. Model weights must not transit the laptop or require manual upload.

The current smoke inventory bounds are 64 MiB per file and 256 MiB total.
Larger adapters or merged models need explicit reviewed bounds and tests; this
initial retrieval limit is not a claim of general large-model support.

## Local lifecycle

Bind the server to loopback. Track only the process started by the session.
Provide explicit start/status/stop and interactive exit. Never kill an existing
unowned server. Test failed startup, Ctrl-C, parent death, stale process identity,
and a hard session deadline. Enforce expiry in the server supervisor, not only
the interactive client. Tie process lifetime to OS ownership so controller
death cannot orphan the server or its GPU worker descendants. Initially support
only platforms where both deadline and process-tree cleanup are proved; the
current evaluator subprocess helper alone does not establish that guarantee.
Reuse the evaluator chat client with full message
history; do not introduce dataset-specific parsing or generation repairs.

## Modal lifecycle and cost ceiling

Use a finite-lived Sandbox, not a permanent endpoint. Modal documents a Sandbox
maximum lifetime controlled by `timeout`; once finished, it cannot execute more
commands. This lifetime is provider-enforced rather than a laptop timer.
See [Sandbox lifecycle](https://modal.com/docs/guide/sandboxes).

Propose a 30-minute default, with the exact lifetime and quoted resource ceiling
shown before startup. Require one GPU and one session, no automatic renewal or
recreation. The GPU remains allocated while the Sandbox runs; this is not
scale-to-zero serving. Include startup and model preparation in the cost plan.
Idle exit may stop earlier, but it must never replace the absolute timeout.

Use authenticated Sandbox connectivity, not an unauthenticated tunnel URL.
Keep connection credentials out of argv, logs, documents, and persisted session
records. Reuse the existing Host authentication mechanism and hold Sandbox
Connect credentials in memory only. This increment creates no credential file
or credential schema. See [Sandbox networking](https://modal.com/docs/guide/sandbox-networking).

Record creation intent before the provider call and bind the returned Sandbox
ID, source inventory, profile, and expiry. An ambiguous create result must not
trigger another creation. Status never creates resources. Manual stop targets
only the recorded session. An unavailable provider read remains unknown, not
confirmed stopped; no automatic replacement is permitted. Renewal needs a new
finite-session approval.

## Required proof before live use

Verify every adapter call against the pinned SDK, not only latest documentation.
Pin and test the inference image, vLLM version, model compatibility, and GPU
profile independently from the training image. Fake-provider tests must prove
expiry is sent on every creation, unknown outcomes do not retry creation, stop
is ownership-bound, and secrets cannot enter output. A bounded live proof must
then verify chat, early stop, and provider timeout after the client disconnects.

No live serving resource, GPU charge, new endpoint, or publication is authorized
by this design document itself. Retrieval implementation and this serving
capability remain separately reviewable changes.
