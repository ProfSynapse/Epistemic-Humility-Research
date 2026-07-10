# Phase 3 Interpretability Direction

Status: planning note
Created: 2026-06-15
Scope: exploratory mechanism work after and alongside Phase 1 seed completion

## Purpose

This note sets the next interpretability direction for the epistemic-humility
program. It does not change the locked PROTOCOL v0.3 headline matrix, the
Amendment A / v0.4 sequential-extension track, or any Phase 1 reporting rule.
All work described here is exploratory mechanism evidence unless a later signed
protocol revision explicitly promotes a result into a claim-bearing analysis.

The current hidden-state tier has established a useful local diagnostic: SFT
shows stronger known/unknown separability than cold-start DPO/KTO, while the
sequential preference arms preserve or reshape the SFT separability. That is a
correlational signal. The next question is causal: whether directions or
features found in hidden states actually move abstention behavior, correctness,
token confidence, or stated confidence when intervened on.

## Recommended Sequence

1. Finish the seed-completion path first.

   Phase 1 seed completion remains the priority because it supplies the
   claim-bearing behavioral evidence. Phase 3 work should run in parallel only
   when it uses idle local capacity, small slices, or already-completed local
   artifacts. It must not consume orchestration attention needed for the
   headline matrix, cloud prerequisites, bridge replication, or Amendment A
   separation.

2. Run causal direction tests before training a small encoder.

   The immediate Phase 3 work should test whether simple directions already
   visible in the hidden-state diagnostics are behaviorally active. Candidate
   tests:

   - Patch or steer known-vs-unknown directions between base, SFT, cold-start
     preference, and sequential preference arms.
   - Measure effects on refusal, correctness, token confidence, and stated
     confidence using the same row ids and prompt-rendering discipline as the
     existing probe/eval artifacts.
   - Include negative controls with shuffled labels, unrelated directions, and
     prompt-format controls so a task-format detector is not mistaken for an
     epistemic-state direction.
   - Treat layer, token position, and metric choice as design variables that
     must be written down before interpreting an intervention effect.

3. Train a small SAE or encoder only if the causal tests justify it.

   A sparse autoencoder or other small encoder is justified if direction tests
   show a stable, intervention-sensitive target that a linear direction cannot
   localize well enough. The encoder should answer a specific follow-up, such as
   whether separability is concentrated in sparse features, whether SFT creates
   new features or reweights existing ones, or whether sequential DPO/KTO
   reshapes an SFT-induced feature set.

   Do not train an encoder just because hidden-state tensors exist. Without a
   causal target, an encoder risks becoming an expensive descriptive layer over
   the same correlational result.

## Ready Now

- Use the existing hidden-state extraction outputs and diagnostic linear-probe
  summaries as target selection inputs.
- Define a small causal-intervention pilot on the local 4B artifacts:
  base/SFT/cold-start DPO/cold-start KTO, plus sequential SFT->DPO and SFT->KTO
  when their artifacts are available and clearly labeled.
- Keep the pilot small: a balanced known/unknown slice, fixed
  `enable_thinking=False`, final prompt token first, and the layers already
  highlighted by the local diagnostics.
- Write outputs under the exploratory probe tree or a new clearly marked
  exploratory mechanism output tree. Link to run records and extraction
  manifests; do not mutate them.

## Requires Protocol Or Amendment Before Claim Use

- Any claim that a learned direction is the mechanism of abstention training.
- Any paper headline comparison using intervention effects.
- Any result used to choose, rank, or reinterpret Phase 1 headline arms.
- Any encoder/SAE result presented as more than exploratory mechanism evidence.
- Any reward-loop use of a probe, direction, SAE feature, or encoder output.

The safe reporting language is: "exploratory local mechanism diagnostics suggest
X; claim-bearing behavioral evidence remains governed by PROTOCOL v0.3 and any
signed amendments."

## Candidate Tools And Packages

Use package recommendations as planning candidates, not confirmed dependencies.
No package choice should override the existing prompt, split, adapter-state, and
manifest discipline.

- `nnsight`: first candidate for causal tracing, patching, and steering
  prototypes if it works cleanly with the current model/adapters.
- TransformerLens or TransformerBridge: consider only after compatibility with
  Qwen3, tokenizer behavior, and LoRA/sequential artifacts is confirmed. Useful
  for deeper activation-patching or circuit-style work if the adapter path is
  not a blocker.
- SAELens: candidate if the causal direction work identifies a stable target
  worth decomposing into sparse features.
- SAEBench and SAE-Vis: later evaluation and visualization candidates after an
  SAE exists and there is a concrete question for it to answer.
- Plain PyTorch hooks: acceptable fallback for narrow module-level interventions
  when higher-level tools fail a concrete need.

Build only the project-specific glue that the packages will not supply:
row-id alignment, prompt-byte identity, adapter-state assertions, manifest
stamping, and joins back to behavioral outcomes.

## Local Parallelism Assumptions

- The local RTX 3090 is the development, smoke, and small-slice interpretability
  lane. It should not be treated as the serial execution lane for the full
  Phase 1 matrix.
- Phase 3 local jobs are acceptable when they use already-produced adapters and
  do not block seed completion, cloud execution, or bridge setup.
- Prefer many short, restartable local jobs over one large exploratory run:
  small balanced slices, explicit manifests, and narrow intervention targets.
- Hidden-state and intervention artifacts should stay reproducible and
  gitignored when large; checked-in files should be plans, configs, schemas,
  summaries, and code, not tensor dumps.
- If a causal-intervention pilot needs more than local smoke scale, pause and
  decide whether it is still exploratory or needs a signed protocol/amendment.

## Minimal Causal Pilot

The first pilot should be deliberately small:

1. Select rows by stable ids from the same frozen known/unknown slice used by
   the hidden-state diagnostics.
2. Choose one or two candidate layers from the best diagnostic layers, plus at
   least one negative-control layer.
3. Define candidate directions from SFT-vs-base and sequential-vs-SFT deltas.
4. Apply patching or steering with a small grid of intervention strengths.
5. Score changes in refusal, correctness, token confidence, and stated
   confidence with the same deterministic evaluation discipline where possible.
6. Record null results. A direction that classifies known/unknown but does not
   move behavior is still informative: it is a representational correlate, not
   a causal handle.

Success is not "large effect." Success is a clean answer about whether the
diagnostic direction has any controlled behavioral leverage.

## Encoder Decision Gate

Train a small SAE or encoder only if all of the following hold:

- A causal pilot finds a reproducible intervention-sensitive target.
- The target cannot be adequately explained by a simple linear direction,
  layer-local delta, or prompt-format confound.
- There is a written question the encoder answers better than direction tests,
  such as feature localization, feature sharing across arms, or SFT-to-sequential
  feature reshaping.
- The training data, held-out rows, artifact paths, and evaluation metrics are
  specified before training.
- The result will remain labeled exploratory unless a signed protocol revision
  says otherwise.

Initial encoder scope should be small: one model size, one or two layers, frozen
row ids, no reward-loop use, and explicit negative controls.

## Claim-Tier Discipline

Interpretability artifacts should be reported in tiers:

- Tier 0: tooling and smoke validation. Examples: extraction succeeds,
  manifests verify, intervention code runs.
- Tier 1: correlational local diagnostics. Examples: linear probes separate
  known/unknown states on local slices.
- Tier 2: causal local diagnostics. Examples: a direction or patch changes
  refusal behavior under controlled local intervention.
- Tier 3: protocol-bearing mechanism evidence. Requires a signed protocol or
  amendment before it can support paper claims beyond exploration.

The current hidden-state findings are Tier 1. The next work should target Tier 2
on a small local pilot. Tier 3 is explicitly out of scope until signed.
