# Phase 3 Interpretability Research Process

Status: draft process runbook
Created: 2026-06-15
Scope: operational management for Phase 3 exploratory interpretability and KG work

## Purpose

This runbook defines how to manage the Phase 3 causal interpretability arm
without blurring it into Phase 1 headline training or signed protocol claims.
It is an operations checklist for literature ingestion, typed knowledge-graph
provenance, causal-pilot gating, and evidence-tier control.

The governing context is:

- `experiment/protocol/PHASE3-control-system-protocol.md`
- `docs/plans/phase3-causal-interpretability-and-kg-plan.md`
- `docs/plans/phase3-interpretability-direction.md`
- `experiment/protocol/PROTOCOL.md` Amendment B draft text
- `.agents/skills/kg-ingest/SKILL.md`
- `.agents/skills/knowledge-graph/SKILL.md`

This document does not authorize KG ingestion, causal interventions, SAE
training, encoder training, or claim promotion by itself.

## Non-Goals

- Do not change `experiment/protocol/PROTOCOL.md`.
- Do not run KG ingestion from this document-editing task.
- Do not add, patch, or canonicalize paper notes here.
- Do not change `library/`, `.agents/skills/`, experiment code, run records, or
  training queues.
- Do not use Phase 3 outputs to rank Phase 1 arms or alter v0.3 headline
  evidence.

## Roles And Boundaries

- Main orchestrator: owns task sequencing, approvals, source-status intake, and
  final evidence-tier decisions.
- Research preparer: owns the source-status matrix for candidate papers and
  returns it separately. Until then, this runbook must not invent detailed paper
  readiness.
- KG ingestion operator: runs the `kg-ingest` workflow when the Workflow tool is
  available, applies deterministic patches, and records validation outputs.
- KG auditor: validates canonical metadata, ontology fit, unresolved targets,
  orphan notes, and graph-analysis findings using `knowledge-graph` scripts.
- Interpretability implementer: may design or run causal pilots only after the
  KG gate passes or an explicit exception is recorded.
- Phase 1 training operator: remains independent. Active seed training,
  cloud-lane prerequisites, bridge replication, and Amendment A separation take
  priority over Phase 3 exploratory work.

No specialist should edit outside their assigned scope. If a role needs a
cross-boundary change, stop and return a proposal to the orchestrator.

## Source Status Matrix

This matrix is the operational queue for the Phase 3 literature/KG gate. It is
based on the current source inventory and should be updated by the research
preparer as notes and local sources are created or fetched.

Do not promote any row to `ready_for_ingest` unless both `note_path` and
`source_path` point to existing local files.

| paper_id | title | batch | topic_bucket | note_path | source_path | source_type | status | blocking_issue | mechanism_or_method_targets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2406.11717 | Refusal in Language Models Is Mediated by a Single Direction | P0 | activation/refusal direction | `library/notes/2406.11717--refusal-single-direction.md` | `library/fulltext/2406.11717.html` | `html` | `validated` | none | refusal direction; activation steering; causal direction removal |
| 2310.06824 | The Geometry of Truth | P0 | truth/known-unknown directions | `library/notes/2310.06824--geometry-of-truth.md` | `library/fulltext/2310.06824.html` | `html` | `validated` | none | truth direction; known/unknown separability; linear probes |
| 2310.01405 | Representation Engineering | P0 | RepE framing | `library/notes/2310.01405--representation-engineering.md` | `library/fulltext/2310.01405.html` | `html` | `validated` | none | representation engineering; direction-based control |
| 2308.10248 | Steering Language Models With Activation Engineering | P0 | activation addition | `library/notes/2308.10248--steering-language-models-with-activation-engineering.md` | `library/fulltext/2308.10248.html` | `html` | `validated` | none | ActAdd; activation steering baseline |
| 2312.06681 | Steering Llama 2 via Contrastive Activation Addition | P0 | contrastive activation addition | `library/notes/2312.06681--steering-llama-2-via-contrastive-activation-addition.md` | `library/fulltext/2312.06681.html` | `html` | `validated` | none | CAA; contrastive steering; transfer controls |
| 2309.16042 | Towards Best Practices of Activation Patching in Language Models | P0 | patching controls/metrics | `library/notes/2309.16042--towards-best-practices-of-activation-patching-in-language-models.md` | `library/fulltext/2309.16042.html` | `html` | `validated` | none | activation patching; corruption choice; metric controls |
| 2606.13669 | Agents-K1 | P0 | KG process spine | `library/notes/2606.13669--agents-k1.md` | `library/fulltext/2606.13669.html` | `html` | `validated` | none | typed scientific KG; claims; mechanisms; method lineage |
| 2411.11296 | Steering Language Model Refusal with Sparse Autoencoders | P0b/P1 | SAE refusal steering | `library/notes/2411.11296--steering-refusal-with-sparse-autoencoders.md` | `library/fulltext/2411.11296.html` | `html` | `source_ready` | needs full `kg-ingest` extraction before claim use | SAE refusal feature; sparse feature steering |
| 2505.23556 | Understanding Refusal in Language Models with Sparse Autoencoders | P0b/P1 | SAE refusal mechanisms | `library/notes/2505.23556--understanding-refusal-with-sparse-autoencoders.md` | `library/fulltext/2505.23556.html` | `html` | `source_ready` | needs full `kg-ingest` extraction before claim use | SAE refusal interpretation; refusal feature localization |
| 2512.16602 | Refusal Steering: Fine-grained Control over LLM Refusal Behaviour for Sensitive Topics | P0b/P1 | Qwen3-specific refusal steering | `library/notes/2512.16602--refusal-steering-sensitive-topics.md` | `library/fulltext/2512.16602.html` | `html` | `source_ready` | needs full `kg-ingest` extraction before claim use | Qwen3 refusal steering; fine-grained refusal control |
| 2602.02132 | There Is More to Refusal in Large Language Models than a Single Direction | P0b/P1 | multi-direction refusal geometry | `library/notes/2602.02132--more-to-refusal-than-single-direction.md` | `library/fulltext/2602.02132.html` | `html` | `source_ready` | needs full `kg-ingest` extraction before treating any single direction as a general refusal mechanism | refusal category geometry; single-direction caveat; over-refusal tradeoff |
| 2409.05907 | Programming Refusal with Conditional Activation Steering | P2 optional | conditional refusal steering | `missing` | `missing` | `missing` | `candidate` | optional; note and local source missing | conditional activation steering; refusal control |
| 2501.09929 | Steering Large Language Models with Feature Guided Activation Additions | P2 optional | feature-guided activation additions | `missing` | `missing` | `missing` | `candidate` | optional; note and local source missing | feature-guided activation addition; steering feature selection |

Allowed `status` values:

- `candidate`
- `note_ready`
- `source_ready`
- `ready_for_ingest`
- `ingested_pending_validation`
- `validated`
- `deferred`
- `blocked`

Immediate next batch steps:

0. Treat `experiment/protocol/PHASE3-control-system-protocol.md` as the current
   Phase 3 exploratory mechanism/control-system protocol. It does not promote
   Phase 3 outputs into Phase 1 headline evidence, arm ranking, or reward-loop
   input.
1. Use `docs/plans/phase3-mechanism-source-map.md` as the Gate 5 source map for
   the initial causal-pilot design.
2. Keep P0 graph status validated unless new source notes or concept nodes are
   added.
3. Use the preferred `kg-ingest` Workflow path for later batches if the Workflow
   tool is available.
4. If Workflow is unavailable, use the fallback proposal path in Gate 3B and
   keep write control with deterministic scripts or a narrow orchestrator-
   approved manual patch.
5. After the 2026-06-18 full local causal-pilot sweep, prioritize external
   gap-fill for `2602.02132`, `2512.16602`, `2411.11296`, and `2505.23556`
   before broadening generation sweeps or training an encoder/SAE.
6. Add queryable KG atoms for `correlational probe vs causal intervention` and
   the project-specific `known/unknown direction` before using either as a
   manuscript mechanism.
7. Source-gate the next literature queue before claim use: `2605.26772`,
   `2410.16314`, `2605.04980`, `2509.23799`, and `2606.03969` if not already
   fully ingested. These are pending ingestion/source reconciliation, not fully
   claim-bearing evidence.

Validation artifact:

- P0 KG gate validated with absolute library root on Windows:
  `python .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root F:\Code\Epistemic-Humility-Research\library`
- Analyze smoke:
  `python .agents/skills/knowledge-graph/scripts/analyze_kg.py --root F:\Code\Epistemic-Humility-Research\library`
- Result: 223 graph notes, 759 typed edges, 0 unresolved targets, 0 legacy
  edges, and 0 orphan graph nodes.
- Windows note: use the absolute `--root` path for validation. A relative
  `--root library` can produce false unresolved-link warnings.
- KG search note: if repo-wide search tries to index local `.cache` or a stale
  `.kg` DB fails, rerun with a scoped root and scratch DB, for example
  `python .agents/skills/knowledge-graph/scripts/kg_search.py "query" --root library --db .tmp/kg-search/query.sqlite --limit 12`.
  On Windows, set `PYTHONIOENCODING=utf-8` if KG search output contains math or
  citation Unicode.

## File Locations

- Paper notes: `library/notes/`
- Fulltext HTML: `library/fulltext/`
- PDFs: `library/pdfs/`
- Atomic concept and mechanism notes: `library/concepts/`
- Library schema: `library/SCHEMA.md`
- KG inventory script:
  `.agents/skills/kg-ingest/scripts/kg_inventory.py`
- KG patch script:
  `.agents/skills/kg-ingest/scripts/apply_kg_patches.py`
- Canonicalization script:
  `.agents/skills/kg-ingest/scripts/migrate_to_canonical.py`
- Relationship validator:
  `.agents/skills/knowledge-graph/scripts/validate_kg_relationships.py`
- Graph analyzer:
  `.agents/skills/knowledge-graph/scripts/analyze_kg.py`
- Phase 3 process docs: `docs/plans/`
- Protocol authority: `experiment/protocol/PROTOCOL.md`

## Evidence Tiers

- Tier 0: tooling smoke. Examples: inventory runs, workflow returns structured
  output, validation scripts execute.
- Tier 1: correlational local diagnostics. Examples: hidden-state directions or
  probe summaries separate known and unknown rows.
- Tier 2: causal local diagnostics. Examples: adding, subtracting, erasing, or
  patching a direction changes behavior under controls on a local slice.
- Tier 3: protocol-bearing mechanism evidence. Requires a later signed protocol
  revision or amendment.

Phase 3 currently targets Tier 2 only. Tier 3 is out of scope until signed.

## Gate 0: Independence From Active Seed Training

Before any Phase 3 work starts, confirm:

- The task does not consume the active seed training lane.
- It does not alter Phase 1 run records, configs, adapters, or result tables.
- It does not require stashing or reverting files needed by the training queue.
- It uses idle local capacity or already-produced artifacts.
- It records outputs as exploratory mechanism work.

Exit artifact:

- A short orchestrator note or task handoff stating that Phase 3 work is
  independent of active seed training.

## Gate 1: Source Readiness

For each candidate paper, confirm:

- A paper note exists under `library/notes/`.
- Source fulltext exists under `library/fulltext/` or PDF source exists under
  `library/pdfs/`.
- The note stem and source path are recorded in the source-status matrix.
- The topic bucket is relevant to Phase 3, for example activation steering,
  refusal mechanisms, activation patching, SAE/refusal, truth directions, method
  lineage, metric controls, or Agents-K1 graph process.

Example path-resolution command from repo root:

```powershell
$ids = @("<arxiv-id-1>", "<arxiv-id-2>")
foreach ($id in $ids) {
  $note = Get-ChildItem "library/notes/${id}--*.md" -ErrorAction SilentlyContinue | Select-Object -First 1
  $notePath = if ($note) { $note.FullName } else { "none" }
  if (Test-Path "library/fulltext/${id}.html") {
    $src = "library/fulltext/${id}.html"
  } elseif (Test-Path "library/pdfs/${id}.pdf") {
    $src = "library/pdfs/${id}.pdf"
  } else {
    $src = "none"
  }
  "{0} | {1} | {2}" -f $id, $notePath, $src
}
```

Exit artifact:

- Source-status matrix rows marked `ready_for_ingest`.

## Gate 2: KG Inventory Snapshot

Before ingestion, snapshot the existing graph so new atoms reconcile against the
vault rather than duplicating concepts.

Preferred command from repo root:

```powershell
python .agents/skills/kg-ingest/scripts/kg_inventory.py > $env:TEMP/kg_inventory.json
```

If the environment requires `python3`, use:

```bash
python3 .agents/skills/kg-ingest/scripts/kg_inventory.py > /tmp/kg_inventory.json
```

Exit artifact:

- `kg_inventory.json` stored in a temporary location and referenced by the
  ingestion handoff.

## Gate 3A: Preferred KG-Ingest Workflow Path

Use this path when the Workflow tool is available.

Checklist:

1. Build a JSON payload with absolute `repoRoot`, paper descriptors, and the
   contents of the inventory snapshot.
2. Run `.agents/skills/kg-ingest/scripts/ingest_workflow.js` through the
   Workflow tool.
3. Confirm the workflow result includes `paperPatches`, `newAtoms`,
   `newMechanisms`, and `existingMechSupport`.
4. Save the workflow result JSON in a temporary or run-specific location chosen
   by the orchestrator.
5. Do not hand-edit paper notes before deterministic patch application.

Payload shape:

```json
{
  "repoRoot": "<absolute repo root>",
  "papers": [
    {
      "arxiv": "<id>",
      "noteStem": "<id>--<slug>",
      "src": "library/fulltext/<id>.html"
    }
  ],
  "existing": "<contents of kg_inventory.json as JSON>"
}
```

Exit artifacts:

- Workflow result JSON.
- Ingestion handoff listing papers, result path, and any workflow warnings.

## Gate 3B: No-Workflow Fallback Path

Use this path only when the Workflow tool is unavailable in the Codex session.
The goal is to preserve deterministic writes and prevent a specialist from
holding or rewriting the whole graph.

Fallback checklist:

1. Run the KG inventory snapshot from Gate 2.
2. For each paper batch, ask bounded specialists for proposals only:
   frontmatter patches, claims sections, new atom proposals, mechanism support
   edges, and merge candidates.
3. Require proposal-only output. Specialists must not edit files.
4. Reconcile proposals against `kg_inventory.json` before accepting a new atom.
5. Prefer existing canonical atoms and mechanisms when aliases or slugs match.
6. Apply accepted edits through deterministic scripts where possible.
7. If deterministic scripts cannot represent the proposed edit, stop and ask the
   orchestrator whether a narrow manual patch is in scope.

Proposal constraints:

- Return exact frontmatter or note-body patch proposals only.
- Preserve existing title, aliases, tags, kg metadata, descriptions, status, and
  useful prose unless the edit explicitly targets those fields.
- Use canonical relationship objects with `type` and `target`.
- Add every relationship target to `related`.
- Do not add `target_id` unless the target note was inspected and its `kg.id` is
  visible.
- Do not invent strong mechanism edges from weak evidence. Prefer a pending or
  conservative relationship when evidence is unclear.
- Do not emit a whole-vault alias map.

Exit artifacts:

- Proposal packet per paper or batch.
- Reconciliation note explaining reused atoms, new atoms, merge decisions, and
  rejected proposals.

## Gate 4: Apply, Canonicalize, Validate, Analyze

After the preferred workflow result or accepted fallback proposal is ready, use
the deterministic scripts from repo root.

Preferred commands:

```powershell
python .agents/skills/kg-ingest/scripts/apply_kg_patches.py <result.json>
python .agents/skills/kg-ingest/scripts/migrate_to_canonical.py
python .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root library
python .agents/skills/knowledge-graph/scripts/analyze_kg.py --root library
```

If running in an environment that follows the skill examples exactly:

```bash
python3 .agents/skills/kg-ingest/scripts/apply_kg_patches.py <result.json>
python3 .agents/skills/kg-ingest/scripts/migrate_to_canonical.py
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root library
python3 .agents/skills/knowledge-graph/scripts/analyze_kg.py --root library
```

Validation expectations:

- No unresolved relationship targets for newly touched notes.
- No ontology drift introduced by the batch.
- No duplicate atom or mechanism where an existing canonical note should have
  been reused.
- `related` includes every `relationships[].target`.
- Mechanism notes receive support edges from papers only when the paper actually
  supports that mechanism.

Exit artifacts:

- Validation log.
- Graph-analysis log.
- List of touched notes.
- List of unresolved issues, if any.

## Gate 5: Mechanism Source Map

Before any causal-pilot design uses a mechanism claim, create a short source map
linking pilot choices to typed graph nodes.

Minimum fields:

- `mechanism_id`
- `mechanism_note`
- `supporting_papers`
- `method_or_metric_nodes`
- `pilot_design_choice`
- `evidence_tier`
- `open_caveat`

Required rule:

- A Phase 3 mechanism claim cannot be used for pilot interpretation beyond tool
  smoke unless it links to a typed KG node and supporting paper notes, or is
  explicitly listed as pending ingestion.

Exit artifact:

- Source map stored under `docs/plans/` or another orchestrator-approved docs
  path.

## Gate 6: Causal Pilot Readiness

Only after the KG/source gate passes, confirm:

- Candidate directions point to verified extraction manifests.
- Row ids are stable and shared across extraction, intervention, and scoring.
- Prompt bytes are fixed across arms.
- `enable_thinking=False` is fixed where relevant.
- Negative controls include shuffled labels, random directions, unrelated
  behavior directions, and wrong-layer controls.
- Metrics are written down before interpreting effects.
- Outputs are labeled Tier 0 to Tier 2 exploratory mechanism evidence.
- No reward-loop use of probes, directions, SAE features, or encoder outputs is
  planned.

Exit artifact:

- Causal pilot readiness note or config reference.

Status update 2026-06-15:

- Gate 6 readiness artifact produced:
  `docs/plans/phase3-causal-pilot-readiness.md`
- First smoke config reference:
  `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml`
- This status records readiness only. It does not claim intervention results,
  causal effects, Phase 1 headline evidence, or Tier 3 mechanism evidence.

## Gate 7: Encoder Or SAE Decision

Do not train a small encoder or SAE unless all of these hold:

- A causal pilot finds a reproducible intervention-sensitive target.
- A simple linear direction cannot answer the question well enough.
- The encoder question is written before training.
- Data, held-out rows, layer choice, artifact paths, and metrics are fixed.
- The result remains exploratory unless a signed protocol revision promotes it.

Exit artifact:

- Encoder/SAE decision memo with a clear `go`, `defer`, or `stop`.

## Handoff Template

Use this template at the end of each Phase 3 process task:

```text
HANDOFF
Scope handled:
Files changed:
Files inspected:
Gates completed:
Artifacts produced:
Key decisions:
Validation/checks run:
Blockers:
Risks and follow-up:
Ready for next phase:
```

## Stop Conditions

Stop and return to the orchestrator if:

- A required source note or source file is missing.
- Workflow is unavailable and fallback proposals would require broad manual KG
  edits.
- Validation finds unresolved targets that cannot be resolved by a narrow merge
  or typo fix.
- A proposed Phase 3 run would block active seed training.
- A proposed result would be used as Phase 1 headline evidence.
- A specialist needs to edit outside their assigned scope.
- The work requires changing protocol text, KG schema, skills, code, run
  records, or training queues.
