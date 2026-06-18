# Phase 3 Mechanism Source Map

Status: Gate 5 source map
Created: 2026-06-15
Scope: P0 validated KG mechanisms for initial Phase 3 causal-pilot design

## Purpose

This source map ties Phase 3 pilot design choices to typed KG mechanisms and
supporting paper notes. It is an operational artifact, not a literature
summary. Mechanism claims remain exploratory unless a later signed protocol
revision promotes them.

Validation basis:

- KG validation: 223 graph notes validated
- Analyze smoke: 759 typed edges
- Unresolved targets: 0
- Legacy edges: 0
- Orphan graph nodes: 0
- Windows validation command used an absolute library root.

## Evidence Tiers

- Tier 1: correlational local diagnostics or representation readout.
- Tier 2: causal local intervention diagnostics.
- Tier 3: protocol-bearing mechanism evidence. Not active for Phase 3 P0.

## Source Map

| mechanism_id | mechanism_note | supporting_papers | pilot_design_choice | evidence_tier | caveat |
| --- | --- | --- | --- | --- | --- |
| `mechanism:refusal-direction-mediates-refusal` | `library/concepts/mechanisms/refusal-direction-mediates-refusal.md` | `library/notes/2406.11717--refusal-single-direction.md` | Include add, subtract, and erase tests for candidate refusal or abstention-adjacent directions; keep safety refusal distinct from epistemic abstention. | Tier 2 candidate | Arditi studies harmful-request safety refusal, not epistemic abstention. Treat transfer to abstention as a hypothesis to test, not as established. |
| `mechanism:activation-addition-steers-generation` | `library/concepts/mechanisms/activation-addition-steers-generation.md` | `library/notes/2308.10248--steering-language-models-with-activation-engineering.md` | Use activation addition as the first simple steering baseline before training any encoder or SAE. | Tier 2 candidate | Requires fixed prompt bytes, layer choice, token position, and coefficient grid before interpreting effects. |
| `mechanism:contrastive-activation-addition-steers-alignment-behaviors` | `library/concepts/mechanisms/contrastive-activation-addition-steers-alignment-behaviors.md` | `library/notes/2312.06681--steering-llama-2-via-contrastive-activation-addition.md` | Compare contrastive directions against plain activation-addition directions for alignment-relevant behavior movement. | Tier 2 candidate | CAA and activation addition are separate method nodes; do not collapse them in configs or reporting. |
| `mechanism:activation-patching-results-depend-on-method-choices` | `library/concepts/mechanisms/activation-patching-results-depend-on-method-choices.md` | `library/notes/2309.16042--towards-best-practices-of-activation-patching-in-language-models.md` | Predeclare corruption method, metric, clean/corrupt construction, token position, and layer before interpreting patching or steering effects. | Tier 2 guardrail | Null or unstable results may indicate metric/corruption sensitivity rather than absence of a mechanism. |
| `mechanism:truth-direction-causally-mediates-model-truth-output` | `library/concepts/mechanisms/truth-direction-causally-mediates-model-truth-output.md` | `library/notes/2310.06824--geometry-of-truth.md` | Keep truth-direction probes separate from refusal-direction probes; use known/unknown directions only after checking whether they behave like truth readouts, refusal readouts, or prompt-format readouts. | Tier 2 candidate | Truth direction, refusal direction, and generic steering vector are separate terms. Do not infer one from another without intervention evidence. |
| `mechanism:representation-engineering-enables-reading-and-control` | `library/concepts/mechanisms/representation-engineering-enables-reading-and-control.md` | `library/notes/2310.01405--representation-engineering.md` | Frame Phase 3 as representation reading plus small representation-control pilots; do not train an encoder until direction tests expose a stable target. | Tier 1 to Tier 2 bridge | RepE is a method frame, not evidence that this project's abstention direction is causal. |
| `mechanism:typed-scientific-kg-preserves-reasoning-provenance` | `library/concepts/mechanisms/typed-scientific-kg-preserves-reasoning-provenance.md` | `library/notes/2606.13669--agents-k1.md` | Require every pilot mechanism claim to link to typed KG nodes, supporting papers, and method/metric/dataset atoms before being used in interpretation. | Process guardrail | Agents-K1 is abstract-backed in the local source; keep confidence medium until full-paper ingestion confirms details. |

## Pilot-Config Implications

- Direction families must be named separately: `truth-direction`,
  `refusal-direction`, `steering-vector`, activation-addition direction, and
  contrastive-activation-addition direction.
- Negative controls should include random directions, shuffled labels,
  sign-flipped directions, wrong-layer controls, and prompt-format controls.
- Patching or steering reports should record the KG mechanism id, source paper
  ids, evidence tier, layer, token position, metric, corruption method, and
  coefficient grid.
- Phase 3 reports should say "exploratory local mechanism diagnostics" unless a
  signed protocol revision promotes the evidence tier.
