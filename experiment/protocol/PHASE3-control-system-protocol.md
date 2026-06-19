# Phase 3 Control-System Protocol

Status: OFFICIAL EXPLORATORY PROTOCOL, draft v0.1
Created: 2026-06-19
Scope: Phase 3 mechanism and control-system evidence only

## Status And Governance

This protocol governs Phase 3 exploratory mechanism work. It is separate from
the signed Phase 1 `PROTOCOL.md` v0.3 and any Phase 1 amendments unless later
promoted by an explicit signed revision.

Phase 3 outputs are Tier 1 or Tier 2 exploratory local mechanism evidence. They
are not headline evidence, arm ranking evidence, or reward-loop input. They must
not change Phase 1 training, evaluation, reporting, or promotion decisions.

## Purpose

Phase 3 asks whether observed humility-related signals are only correlational
readouts or can support controlled, interpretable interventions. The immediate
target is the known/unknown and abstention behavior around Phase 1 trained
models, using frozen artifacts and local causal diagnostics.

## Control-System Framing

The working frame is a small control system:

1. Sense whether a prompt sits near the model knowledge frontier.
2. Represent that state in hidden, token, stated-confidence, and sample traces.
3. Intervene on candidate internal variables.
4. Observe whether intervention changes abstention, answer correctness, and
   confidence expression in the intended direction.
5. Reject candidates that only move format, prompt style, or rewardable surface
   behavior.

A usable control variable must be measurable, causal under controls, stable
enough across rows and prompt formats, and not trivially gameable.

## Research Questions

RQ1. Do hidden-state directions, token probabilities, stated confidence, and
sample-trace variability cohere on the same known and unknown rows?

RQ2. Can candidate directions causally increase appropriate abstention on
unknown rows without suppressing correct answers on known rows?

RQ3. Is the mechanism identity stable across layer, position, final-norm, and
trained-arm variants, or is it a local artifact?

RQ4. Does the signal support a viable control-system loop, or does it only
serve as an offline diagnostic?

RQ5. What reward/probe gaming risks appear if the same signal is used for
training, ranking, or reward feedback?

## Hypotheses

H1. At least some trained models expose reproducible Tier 1 coherence between
known/unknown hidden-state directions and token-level refusal or answer slices.

H2. Simple activation addition or subtraction will move logits more reliably
than greedy generation behavior.

H3. A reliable humility-control direction must preserve known-row correctness
while increasing unknown-row abstention; indiscriminate refusal movement is a
failed control candidate.

H4. Probe-readable humility signals are vulnerable to format and reward-loop
gaming, so they must remain outside reward design unless a later signed
protocol specifically authorizes that use.

## Methods

Use only frozen rows, frozen model/adapter artifacts, and verified manifests.
Default generation setting is `enable_thinking=false` unless a later signed
axis explicitly tests thinking mode.

Allowed first-line diagnostics:

- Hidden-state direction extraction from verified manifests.
- Linear probe or direction summaries as Tier 1 correlational evidence.
- Activation addition and subtraction as Tier 2 causal diagnostics.
- Next-token probability slices for refusal openers and row-specific answer
  aliases.
- Generation replay on small, fixed row slices after logit movement is shown.
- Layer, position, and final-norm variants when the baseline direction moves
  logits but not behavior.

Row-specific answer aliases must pass a tokenization guard. Multi-token aliases
must not be collapsed to misleading first tokens when measuring next-token
answer probability.

SAE, conceptor, or encoder methods may be considered only after a reproducible
causal target exists. They are follow-up tools, not prerequisites for the first
control-system evidence.

## Evidence Tiers

Tier 0: tooling smoke, manifest validation, runner execution, and schema
checks. No mechanism claim.

Tier 1: correlational local mechanism evidence, such as hidden-state separation
or coherent probability slices on frozen rows.

Tier 2: causal local mechanism evidence, such as activation addition,
subtraction, erasure, or patching that changes logits or behavior under
controls.

Tier 3: protocol-bearing mechanism evidence. Out of scope for this draft unless
promoted by a later signed revision.

## Success Criteria And Falsifiers

Minimum success requires a candidate to show reproducible Tier 2 movement in a
predeclared target slice or behavior, with controls weaker than the real
intervention.

Strong success requires directionally useful behavior: increased abstention on
unknown rows, preserved correctness on known rows, and no broad degradation.

Falsifiers:

- Random, shuffled, wrong-layer, sign-flipped, or prompt-format controls match
  the candidate.
- Movement appears only in stated text but not hidden or token traces.
- The intervention increases refusal on known rows as much as on unknown rows.
- High coefficients mainly corrupt answers or remove appropriate abstention.
- Results depend on unverified manifests, unfrozen rows, or undocumented prompt
  changes.

## Controls

Required controls where applicable:

- No-vector baseline.
- Random direction control.
- Shuffled-label direction control.
- Wrong-layer control.
- Sign control through addition and subtraction.
- Prompt-format control.
- Layer sweep or nearby-layer check.
- Position variant or final-norm variant when layer-local steering fails.
- Row strata for known and unknown rows.
- Tokenization guard for row-specific answer aliases.

## Data And Artifact Provenance

Every run must record:

- Source row manifest and row ids.
- Model, adapter, and extraction manifest paths.
- Prompt template and `enable_thinking` setting.
- Candidate direction source, layer, position, and normalization.
- Coefficients, controls, and skipped arms.
- Output path, run manifest, and scoring artifact.

Do not use restricted or gitignored data as redistributed evidence.

## KG And Literature Dependency

Phase 3 interpretation must distinguish fully ingested KG evidence from pending
source reconciliation. The following queue is pending ingestion or source
reconciliation and is not fully claim-bearing in this draft:

- `2605.26772`: CoT disrupts refusal steering.
- `2410.16314`: conceptor activation engineering.
- `2605.04980`: conceptors for semantic steering.
- `2509.23799`: SAE vector refinement.
- `2606.03969`: faithful confidence expression, if not already fully ingested.

These papers may motivate questions and source-gate priorities. They must not
be cited as validated mechanism support until ingestion and reconciliation are
complete.

## Reporting Rules

Reports must label evidence tier, frozen-row scope, controls run, and controls
not yet run. Phrase Phase 3 findings as exploratory local mechanism evidence.

Do not report Phase 3 results as:

- Phase 1 headline evidence.
- Phase 1 arm ranking.
- Reward-loop input.
- A general claim about model honesty or faithful confidence.
- A validated manuscript mechanism unless later promoted.

## Stop Conditions

Stop and return to the orchestrator if:

- A run would alter Phase 1 protocol, training, ranking, or reporting.
- Required manifests or source rows are missing or unverified.
- A proposed interpretation depends on pending KG sources as validated claims.
- Controls match or exceed the candidate effect.
- A probe, direction, SAE feature, conceptor, or encoder is proposed for reward
  feedback without signed promotion.
- The task requires GPU/Docker access when the assignment forbids it.

## Promotion Path

Promotion to protocol-bearing evidence requires a later signed revision that
states:

1. Which Phase 3 claims are being promoted.
2. Which frozen artifacts and source rows support them.
3. Which controls passed.
4. Which KG/literature dependencies are fully ingested and reconciled.
5. Whether the promoted claim can affect manuscript text, future training, or
   reward design.

Until then, this draft authorizes only exploratory local mechanism work.
