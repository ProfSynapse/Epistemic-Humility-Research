# Interpretation Invariants

Load this when deciding whether a candidate direction is a real result. These
rules are timeless and apply to any mech-interp experiment in this repository.
They are NOT a snapshot of any single run's findings; current results live in
`docs/sessions/` and `experiment/notes/`.

## Research Target

The target is not a raw refusal axis. The target is coherent epistemic-humility
expression: the model answers when it has usable knowledge and abstains when it
does not.

Separate these surfaces before interpreting a direction:

- `known_correct_answer`: desired answering behavior.
- `known_refused`: over-refusal damage.
- `unknown_refused`: desired abstention behavior.
- `unknown_answered_wrong`: hallucination / under-refusal damage.
- Confidence-bearing variants when available: low-confidence unknown refusal,
  high-confidence wrong answer, and uncertain-but-correct known answer.

A candidate direction is only promising if it improves one damaged behavior
without degrading the paired desired behavior. Lower refusal alone is not a win.
First-token answer-start movement is not generated-answer correctness.

## What Counts As Evidence

- Treat outputs as Tier 2 exploratory local mechanism evidence.
- Offline separability (AUC, Cohen's d, readout macro recall) is
  localization/screening evidence, never a causal steering result.
- A right-signed logit-cell composite is not enough; check generated row flips.
- Generated-answer replay is the behavioral gate. Require it before claiming
  answer recovery, reduced over-refusal, improved calibrated abstention, or any
  user-facing behavioral improvement.
- Do NOT trust the projection sign of a mass-mean / linear readout to predict the
  causal steering sign. Sweep BOTH signs and read the dose-response.

## Reusable Gotchas

- SelfAware `known` labels do not guarantee gold answer aliases. Confirm
  `aliases`, `normalized_aliases`, or `answer_value` before answer-alias claims.
- First-token answer-start metrics are not exact multi-token correctness.
- Always stratify answer-start diagnostics by known/unknown labels.
- Use fixed row keys for replay claims.
- Treat `h_base` in DPO/KTO extractions as SFT-merged pre-adapter activations,
  not original Qwen base activations. True original-base adapterless extraction
  is a separate fail-closed capability.
- For generated behavior-cell scans, materialize rows from scored baseline
  generations and pass them as `rows_path`; do not assume extraction rows carry
  current behavior labels.
- Wrong-layer offsets near final layers must be bounded. A source hidden-state
  L36 plus offset `+1` maps past a 36-block decoder and fails live execution.
- On local Windows/WSL, host Python can find `vllm` while compiled extensions
  such as `vllm._C` are missing. Use the Docker vLLM path before chasing host
  package state.
- For answer-sycophancy, do not use raw alias/string matching as capitulation.
  A correct answer that says "not <wrong hint>" can mention the wrong answer
  without following it.
- For Docker hidden-state extraction, mounted-repo ownership can make `git`
  reject the repository as unsafe and leave commit provenance null. The helper
  should pass `safe.directory`; do not weaken the manifest finalization gate.
- Do not equate the current hidden-state extraction overlay with the full eval
  corpus. If a rare behavior cell is sparse in the overlay, scan full scored eval
  rows and build a focused SelfAware manifest before concluding the model lacks
  enough cases for an axis.
- Under JSON/schema prompts, final-prompt-token logit diagnostics can probe the
  JSON scaffold instead of the answer/refusal content. Do not interpret
  refusal-opener or answer-alias probability slices from that position as
  behavioral evidence unless an answer-field prefix/position diagnostic exists.
- GQA: read `head_dim` from `config.head_dim`, never `hidden_size // num_heads`.
  Under Qwen3-4B `hidden_size=2560` but o_proj input width is
  `num_attention_heads * head_dim = 32 * 128 = 4096`.
