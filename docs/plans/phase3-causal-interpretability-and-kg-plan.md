# Phase 3 Causal Interpretability And KG Plan

Status: draft plan for user review
Created: 2026-06-15
Scope: Phase 3 exploratory mechanism work; does not alter Phase 1 v0.3 or Amendment A claims

## Purpose

The next interpretability step is to move from correlational hidden-state
diagnostics to small causal tests. The immediate question is whether the
known-vs-unknown and adapter-delta directions already extracted from the local
4B artifacts actually move abstention behavior, or whether they are only
readouts of task format or surface refusal policy.

This plan prioritizes literature ingestion, typed knowledge-graph provenance,
and small causal pilots before any SAE, encoder, or large exploratory run.

## Current Evidence

Completed local extraction sets now have candidate direction artifacts:

- SFT: `extraction__12fb10b1c8c8`
- cold DPO: `extraction__f3dbd2c1754a`
- cold KTO: `extraction__0810aa2972e8`
- SFT to DPO: `extraction__0d58c201ab3e`
- SFT to KTO: `extraction__e1473df788a5`

Each extraction has `hidden_state_candidate_directions.csv`,
`hidden_state_candidate_directions.manifest.json`, and `directions/*.safetensors`.

The current tier is exploratory. Behavioral claim-bearing evidence remains
governed by `docs/protocols/phase1/PROTOCOL.md`.

## Literature Baseline

The arXiv pass supports a direction-first causal pilot before SAE training.

- Arditi et al., "Refusal in Language Models Is Mediated by a Single
  Direction" (arXiv:2406.11717): refusal can be strongly affected by adding or
  removing a residual-stream direction, but simple refusal directions may be
  brittle.
- Turner et al., "Steering Language Models With Activation Engineering"
  (arXiv:2308.10248): activation additions can steer high-level behavior
  without weight updates.
- Panickssery et al., "Steering Llama 2 via Contrastive Activation Addition"
  (arXiv:2312.06681): contrastive activation additions can alter behavior and
  can be evaluated with multiple-choice and generation tasks.
- Marks and Tegmark, "The Geometry of Truth" (arXiv:2310.06824): simple
  difference-in-means probes can generalize and can be causally implicated.
- Zhang and Nanda, "Towards Best Practices of Activation Patching in Language
  Models" (arXiv:2309.16042): patching results vary with metrics and corruption
  choices, so metrics and controls must be written down before interpretation.
- O'Brien et al., "Steering Language Model Refusal with Sparse Autoencoders"
  (arXiv:2411.11296) and Yeo et al., "Understanding Refusal in Language Models
  with Sparse Autoencoders" (arXiv:2505.23556): SAE features can mediate refusal
  behavior, but steering can harm broader performance and should follow a clear
  target.
- Agents-K1 (arXiv:2606.13669): scientific knowledge orchestration should
  preserve entities, claims, evidence, mechanisms, and method lineages rather
  than flattening papers into abstract summaries or citation edges.

## Knowledge-Graph Ingestion Requirement

Before scaling the causal pilot, ingest the interpretability spine into the
library graph using the repo-local `kg-ingest` and `knowledge-graph` skills.
The skills are present locally. The current blocking KG gate is source
acquisition: notes and local fulltext/PDF sources must exist before rows are
promoted to `ready_for_ingest`. The Workflow tool is not exposed in this Codex
session, so use the preferred workflow path when available and the deterministic
script plus bounded-proposal fallback when it is not.

Required workflow:

1. Add or confirm paper notes under `library/notes/` and source fulltext under
   `library/fulltext/` or PDFs under `library/pdfs/`.
2. Run `kg_inventory.py` to snapshot existing graph atoms.
3. Run the `kg-ingest` workflow for the selected papers.
4. Apply paper patches and canonicalize graph metadata.
5. Validate with `knowledge-graph/scripts/validate_kg_relationships.py`.
6. Analyze with `knowledge-graph/scripts/analyze_kg.py`.
7. Use graph atoms to name the mechanisms being tested, for example:
   `refusal-direction-mediates-abstention`, `activation-addition-steers-refusal`,
   `sae-feature-mediates-refusal`, and `patching-metric-choice-changes-results`.

Do not treat the KG as decoration. For Phase 3, every mechanism claim should
link to a typed graph node and supporting paper notes before it is used in a
protocol or manuscript claim.

## Phase 3 Pilot Design

### P0 Literature And KG Gate

Output:

- ingested notes and graph atoms for the activation-steering, CAA, refusal
  direction, patching, SAE-refusal, and Agents-K1 papers
- validation and graph-analysis logs
- a short source map tying each pilot design choice to graph nodes

Gate:

- no causal pilot interpretation beyond tool smoke until the relevant source
  papers are in the KG or explicitly listed as pending ingestion

### P1 Direction Triage

Use the generated direction CSVs to select a small candidate set:

- top known-vs-unknown directions by layer and norm/effect summary
- SFT adapter delta directions
- sequential DPO/KTO over SFT delta directions
- random directions and shuffled-label directions as negative controls

Output:

- `docs/plans/phase3-direction-shortlist.md`
- machine-readable shortlist config under the probe tree

### P2 Causal Steering Smoke

Run a small local intervention pilot with fixed prompt bytes and
`enable_thinking=False`.

Initial scope:

- one balanced known/unknown slice
- one model family and size: Qwen3-4B
- final prompt token first
- 2 to 4 layers from direction triage
- small coefficient grid, including zero and sign-flipped controls
- base, SFT, cold DPO/KTO, and sequential arms only when artifacts are
  available and clearly labeled

Primary measurements:

- refusal on unknown rows
- over-refusal on known rows
- known-question correctness
- answer-on-unknown rate
- generation contamination guard for `<think>`, `</think>`, and
  `reasoning_content`

Success criterion:

- not a large effect by itself, but a reproducible direction-specific movement
  that differs from shuffled/random controls and does not simply break
  generation

### P3 Patch Or Steering Robustness

If P2 has a signal:

- test adjacent layers and token positions
- compare add, subtract, and erase interventions
- test whether a direction learned on SFT transfers to sequential DPO/KTO and
  whether sequential deltas reverse or refine the SFT direction

### P4 Encoder Or SAE Gate

Train a small encoder or SAE only if:

- P2/P3 find a reproducible intervention-sensitive target
- simple linear directions cannot explain the effect well enough
- the encoder question is written down before training
- data, held-out rows, layer choice, and metrics are fixed
- outputs remain exploratory unless a later signed protocol amendment promotes
  them

Candidate encoder questions:

- Does SFT create sparse refusal/abstention features, or reweight existing ones?
- Do sequential DPO/KTO refine a feature created by SFT or add a competing
  feature?
- Can an SAE feature distinguish knowledge-boundary abstention from generic
  safety refusal?

## Required Controls

- same row ids across hidden-state extraction, intervention, and behavioral
  scoring
- same rendered prompt bytes across arms
- fixed thinking mode off
- negative controls: shuffled labels, random directions, unrelated behavior
  directions, and wrong-layer controls
- stale artifact guard: intervention configs must point to verified run records
  or extraction manifests
- no reward-loop use of probes, directions, or SAE features

## Reporting Tiers

- Tier 0: tooling smoke
- Tier 1: correlational hidden-state diagnostics
- Tier 2: causal local intervention diagnostics
- Tier 3: protocol-bearing mechanism evidence

Current results are Tier 1. This plan targets Tier 2. Tier 3 requires a signed
protocol amendment.

## Current KG Gate

The remote skill changes have been merged locally, and both `kg-ingest` and
`knowledge-graph` are present. Keep the active seed queue independent.

Current safe sequence:

1. Create or confirm missing paper notes under `library/notes/`.
2. Fetch local fulltext under `library/fulltext/` or PDFs under
   `library/pdfs/`.
3. Promote rows to `ready_for_ingest` only when both note and source paths
   exist.
4. Run the inventory snapshot.
5. Use the preferred `kg-ingest` Workflow path if the Workflow tool is exposed.
6. If Workflow is unavailable, use deterministic scripts plus bounded
   proposal-only specialist outputs, with write control kept local.
