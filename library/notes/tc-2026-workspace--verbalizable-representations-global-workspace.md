---
title: 'Verbalizable Representations Form a Global Workspace in Language Models'
arxiv: ''
year: 2026
url: https://transformer-circuits.pub/2026/workspace/index.html
area: mechanistic-interpretability
status: verified
tags:
- paper
- epistemic-humility
- mechanistic-interpretability
- kg/paper
authors:
- Wes Gurnee
- Nicholas Sofroniew
- Adam Pearce
- Mateusz Piotrowski
- Isaac Kauvar
- Runjin Chen
- Anna Soligo
- Paul Bogdan
- Euan Ong
- Rowan Wang
- Ben Thompson
- David Abrahams
- Subhash Kantamneni
- Emmanuel Ameisen
- Joshua Batson
- Jack Lindsey
models: []
metrics: []
pdf: ''
kg:
  id: paper:tc-2026-workspace
  type: paper
  status: canonical
related:
- '[[jacobian-lens]]'
- '[[global-workspace]]'
- '[[logit-lens]]'
- '[[tuned-lens]]'
- '[[activation-patching]]'
- '[[residual-stream]]'
- '[[representational-drift]]'
- '[[mmlu]]'
- '[[claude-sonnet-4-5]]'
- '[[claude-haiku-4-5]]'
- '[[claude-opus-4-5]]'
- '[[claude-opus-4-6]]'
- '[[j-lens-vector-swap-redirects-verbal-report]]'
- '[[global-workspace-mediates-intermediate-reasoning-steps]]'
- '[[global-workspace-ablation-impairs-flexible-cognition]]'
- '[[tc-2026-workspace-commentary-dehaene-naccache--does-claude-possess-conscious-global-workspace]]'
- '[[tc-2026-workspace-commentary-butlin-shiller-plunkett-long--consciousness-cognitive-access-llms]]'
- '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
relationships:
- type: proposes
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: studies
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: studies
  target: '[[logit-lens]]'
  target_id: method:logit-lens
  confidence: high
- type: studies
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
  confidence: high
- type: uses
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: medium
- type: studies
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
- type: studies
  target: '[[representational-drift]]'
  target_id: term:representational-drift
  confidence: medium
- type: evaluates_on
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: uses
  target: '[[claude-sonnet-4-5]]'
  target_id: model:claude-sonnet-4-5
  confidence: high
- type: uses
  target: '[[claude-haiku-4-5]]'
  target_id: model:claude-haiku-4-5
  confidence: high
- type: uses
  target: '[[claude-opus-4-5]]'
  target_id: model:claude-opus-4-5
  confidence: high
- type: uses
  target: '[[claude-opus-4-6]]'
  target_id: model:claude-opus-4-6
  confidence: medium
- type: supports
  target: '[[j-lens-vector-swap-redirects-verbal-report]]'
  target_id: mechanism:j-lens-vector-swap-redirects-verbal-report
  confidence: high
- type: supports
  target: '[[global-workspace-mediates-intermediate-reasoning-steps]]'
  target_id: mechanism:global-workspace-mediates-intermediate-reasoning-steps
  confidence: high
- type: supports
  target: '[[global-workspace-ablation-impairs-flexible-cognition]]'
  target_id: mechanism:global-workspace-ablation-impairs-flexible-cognition
  confidence: high
- type: related_to
  target: '[[tc-2026-workspace-commentary-dehaene-naccache--does-claude-possess-conscious-global-workspace]]'
  target_id: paper:tc-2026-workspace-commentary-dehaene-naccache
  confidence: high
- type: related_to
  target: '[[tc-2026-workspace-commentary-butlin-shiller-plunkett-long--consciousness-cognitive-access-llms]]'
  target_id: paper:tc-2026-workspace-commentary-butlin-shiller-plunkett-long
  confidence: high
- type: related_to
  target: '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
  target_id: paper:tc-2026-workspace-commentary-nanda
  confidence: high
---
## Abstract

This piece has no formal abstract block; the introduction opens with the
paper's framing instead: "If the mind is an ocean, we spend our lives floating
at the surface. Beneath us, an enormous amount of processing takes place
without our knowledge... At any given moment, only a small fraction of this
neural activity is accessible to us." The paper's stated contribution: it
presents "evidence that language models maintain a privileged set of internal
representations, available for report, modulation, and flexible internal
reasoning, atop a much larger volume of automatic processing," identified via
a new interpretability technique, the Jacobian lens (J-lens), "which surfaces
the concepts a model is poised to verbalize at any point in its processing."

## Summary

The paper asks whether language models have developed a functional analog of
"access consciousness," the cognitive-science distinction between the subset
of brain activity that is consciously reportable and the much larger volume
that is not. To test this, it introduces the [[jacobian-lens]] (J-lens), which
estimates the first-order causal effect of a layer's residual-stream state on
the model's final output (a Jacobian, not a fixed or learned linear map), then
applies the unembedding matrix to that Jacobian-corrected state to produce a
vocabulary readout. The set of directions expressible as a sparse nonnegative
combination of J-lens vectors is called the J-space, or [[global-workspace]].
Workspace-like properties only emerge in an intermediate band of layers
(roughly the middle third to two-thirds of the network); early layers give
noisy readouts and late layers shade into pure output preparation.

Using this tool, the paper runs a sequence of causal-intervention experiments
(vector swaps, targeted ablations, and instructed-focus/ignore manipulations)
on Claude Sonnet 4.5, corroborated on Claude Haiku 4.5, Claude Opus 4.5, and
Claude Opus 4.6. It reports that: (1) J-lens vectors causally determine verbal
report, far more than the rest of a concept's representation; (2) models can
be instructed to load or suppress a concept in the workspace, with the effect
strengthening with model scale; (3) intermediate steps of multi-hop reasoning
that are never verbalized nonetheless occupy the workspace and causally
mediate the final answer; (4) a single workspace vector broadcasts to
multiple, independent downstream computations (a form of flexible
generalization); and (5) ablating the workspace selectively impairs flexible,
deliberate tasks while leaving routine, automatic tasks largely unaffected.
The authors are explicit that the J-lens is an approximate, single-token-only
probe, that they are not claiming a transformer literally reproduces the
brain's global workspace architecture, and that they take no position on
whether any of this bears on subjective experience; the claims are about
functional access and causal mediation, not phenomenal consciousness.

## Extracted numbers

Numbers sourced from the paper's rendered HTML at
`https://transformer-circuits.pub/2026/workspace/index.html` (compiled working
reference saved at `library/fulltext/tc-2026-workspace.md`), figures 6-29 as
cited inline; this is a web-native piece with no arXiv id or PDF, so citations
are to the paper's own figure numbers rather than table numbers.

- Verbal-report swap: J-space vector swaps move the target concept into the
  model's top-5 verbalized output on 88% of trials; an equal-magnitude swap
  confined to the same vector's non-J-space components succeeds on 5% of
  trials (Figure 6).
- The J-space component of a concept vector carries only 6-7% of that vector's
  total variance yet dominates verbal report over the remaining 93-94%
  (Figure 8).
- Directed modulation: focus instructions raise a target concept's presence in
  the J-lens readout on a substantial fraction of trials, with the effect
  increasing with model size; ignore instructions reduce presence
  substantially below focus but not to the zero baseline (Figure 10).
- Internal reasoning mediation: intermediate-concept swaps on two-hop
  factual-recall prompts succeed on 54% of trials (Claude Haiku 4.5), 70%
  (Claude Sonnet 4.5), and 70% (Claude Opus 4.5) (Figure 15).
- Intermediate-concept swaps take effect approximately 17% earlier in the
  layer stack than final-answer-token swaps on the same prompts (Figure 15).
- The J-space component of an intermediate-step probe flips the final answer
  on 61% of trials, versus 28% for the probe's non-J-space component
  (Figure 16).
- Flexible generalization / broadcast: baseline-strength country-concept swaps
  succeed in placing a target-appropriate answer at top-1 on 76 of 192 trials;
  double-strength swaps succeed on 101 of 192 trials (Figure 19).
- Layer structure: next-token accuracy, excess kurtosis, top-1 lens-token
  autocorrelation, and effective linear dimensionality all show a three-regime
  pattern (flat in early layers, rising through an intermediate ~layer-38-to-92
  band, shifting again in the final layers) (Figure 28); an ignition
  experiment on ambiguous blended inputs shows a smooth-to-sharp transition in
  activation position starting around layer 38 (Figure 29).

## Relevance to experiment

This is a representations-and-circuits paper, not a calibration or abstention
paper, and it makes no claims about hallucination rates, calibration error, or
training interventions; none of its numbers plug into an effects table the
way a benchmark paper's would. Its relevance to this vault's themes is
indirect but real, through three connections worth stating plainly rather than
stretching.

First, the paper's central distinction, between what a model represents and
what it will verbalize or act on, is exactly the gap that self-report-based
calibration and hallucination-detection methods (verbalized confidence,
[[introspective-uncertainty-quantification]]-style methods) have to reason
about. The paper's finding that a concept can be present in the model's
internal readout at "comparable rates" across tasks while causally driving
some outputs and not others (Figure 20) is a mechanistic instance of a warning
this vault already carries in a different form: that a probe or readout being
correlated with a property does not mean the property is used the same way
downstream (compare [[high-probe-accuracy-does-not-imply-causal-use]] and
[[layer-property-usage-diverges-from-probe-localization]]). This paper adds a
new, causally-grounded instance of that general pattern, specific to what gets
verbalized versus what stays latent.

Second, the finding that the workspace selectively mediates flexible,
deliberate tasks while automatic tasks survive ablation (Figure 21) bears on
interpretability-based hallucination or uncertainty detection: if a probe or
intervention targets the wrong regime (automatic vs. workspace-mediated
processing), it may miss the representations that actually drive a model's
answer on a given task. This is a plausible mechanistic hypothesis for why
activation-probe-based knowledge-boundary or confidence signals sometimes
generalize poorly across task types, though the paper itself does not test
calibration or hallucination directly and this connection should be read as a
hypothesis this paper motivates, not a result it establishes.

Third, the paper's method (a causal Jacobian correction to the logit lens)
is a direct methodological descendant of the [[tuned-lens]] line of work
already in this vault ([[representational-drift-breaks-logit-lens]]), and
strengthens the general case that naive intermediate-layer readouts
([[logit-lens]]) are unreliable diagnostics for what a model is representing,
a caution relevant to any future work in this program that tries to read
calibration- or knowledge-boundary-relevant signals directly off intermediate
activations.

## Claims

- Swapping a concept's J-lens vector for a different concept's at a matched
  layer causally redirects the model's verbalized output toward the
  swapped-in concept on 88% of trials, versus 5% for an equal-magnitude swap
  confined to the same vector's non-J-space components; the J-space component
  carries only 6-7% of the vector's variance yet dominates report (Figure 6;
  Figure 8) [[j-lens-vector-swap-redirects-verbal-report]]
- An intermediate, never-verbalized step of multi-hop reasoning is
  nonetheless represented in the J-space and causally mediates the final
  answer: intermediate-concept swaps succeed on 54% (Haiku 4.5) to 70%
  (Sonnet 4.5, Opus 4.5) of trials and take effect roughly 17% earlier in the
  layer stack than answer-token swaps (Figure 13; Figure 15; Figure 16)
  [[global-workspace-mediates-intermediate-reasoning-steps]]
- Ablating the J-space component of activations sharply degrades flexible,
  deliberate tasks (multi-hop reasoning, translation, summarization,
  no-chain-of-thought math) while leaving automatic tasks (sentiment
  classification, MMLU, CoLA, extractive QA) at or near the unablated
  baseline, and chain-of-thought math is far more robust to the ablation than
  direct math answers (Figure 20; Figure 21; Figure 24)
  [[global-workspace-ablation-impairs-flexible-cognition]]
- The workspace shows a three-regime layer structure (early "sensory," a
  middle band with rising next-token accuracy, kurtosis, and effective
  dimensionality, and a late "motor" shift), and an ignition-style experiment
  on ambiguous blended inputs shows activation position switching sharply
  between discrete interpretations once the middle band is reached, rather
  than varying smoothly as it does in early layers (Figure 28; Figure 29)
  [[global-workspace]]

## External commentary

- [[tc-2026-workspace-commentary-dehaene-naccache--does-claude-possess-conscious-global-workspace]]: cognitive-neuroscience commentary relating J-space to the global neuronal workspace, with proposed ignition, bottleneck, trace-conditioning, inclusion/exclusion, and self-monitoring tests.
- [[tc-2026-workspace-commentary-butlin-shiller-plunkett-long--consciousness-cognitive-access-llms]]: Eleos AI Research commentary separating [[cognitive-access]], [[phenomenal-consciousness]], [[privileged-stream|privileged stream]], and [[ai-moral-status]] implications.
- [[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]: interpretability commentary and Qwen replication framing J-space as a [[cognitive-space|cognitive space]], with [[interpretative-meta-tokens]] as a preliminary extension.
