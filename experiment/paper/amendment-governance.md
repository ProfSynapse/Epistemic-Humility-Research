# Protocol Amendment Governance

Status: working rule for Paper 1 protocol hygiene

Use this note when deciding whether an extension can be described as a signed
protocol amendment, a local analysis extension, or only exploratory evidence.

## Acceptance Rule

An amendment is accepted only when all of the following are true:

1. The amendment has its own file under `experiment/protocol/`.
2. The file status is changed to `SIGNED OFF`.
3. The file records the approval date and what prior protocol surfaces it does
   or does not supersede.
4. The file includes a rerun/reporting policy: which old artifacts can be reused,
   which new runs are required, and which labels must appear in tables.
5. The user explicitly approves that exact amendment in the session.
6. A session checkpoint records the approval and amendment path.
7. Any generated result tables keep the amendment separate from locked v0.3
   headline results unless the amendment explicitly supersedes v0.3.

## Current Status

| Surface | Status | Paper treatment |
|---|---|---|
| PROTOCOL v0.3 | Signed off 2026-06-10 | Governs original headline matrix. |
| Amendment A / v0.4 sequential SFT-warmed DPO/KTO | Signed off 2026-06-14 in `PROTOCOL.md` | Report separately as a prospective extension. |
| Amendment B stated-confidence / GRPO | Signed off for stated-confidence measurement/reporting on 2026-06-19 in `AMENDMENT-B-stated-confidence-grpo.md` | Report as a separate accepted measurement layer; GRPO/RLVR remains prospective and needs separate launch approval. |
| Phase 3 mechanism work | Exploratory draft protocol | Keep out of Paper 1 main results; use for a separate paper or future-work sentence only. |

## Amendment B Scope

Amendment B is accepted as a measurement/reporting amendment for stated
confidence. The accepted scope covers the answer/confidence output contract,
completed stated-confidence reruns, and confidence scoring against known/unknown
labels and factual answer correctness. It does not authorize new GRPO/RLVR
cells; those remain a separate prospective method decision.
