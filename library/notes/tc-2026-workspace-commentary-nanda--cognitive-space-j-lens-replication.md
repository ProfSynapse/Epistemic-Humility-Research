---
title: 'Cognitive space, J-Lens replication, and interpretative meta-tokens'
arxiv: ''
year: 2026
url: https://www-cdn.anthropic.com/files/4zrzovbb/website/cc4be2488d65e54a6ed06492f8968398ddc18ebe.pdf
area: mechanistic-interpretability
status: verified
tags:
- paper
- epistemic-humility
- mechanistic-interpretability
- kg/paper
authors:
- Neel Nanda
models:
- Qwen3
metrics: []
pdf: library/pdfs/tc-2026-workspace-commentaries.pdf
kg:
  id: paper:tc-2026-workspace-commentary-nanda
  type: paper
  status: canonical
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[cognitive-space]]'
- '[[interpretative-meta-tokens]]'
- '[[qwen3]]'
- '[[model-forensics-two-step-protocol]]'
- '[[j-lens-approximates-cognitive-space-via-token-jacobians]]'
- '[[qwen-j-lens-replication-supports-cross-model-cognitive-space]]'
- '[[interpretative-meta-tokens-mediate-ambiguity-disambiguation]]'
- '[[j-lens-is-auditor-hypothesis-generation-not-verification]]'
relationships:
- type: related_to
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: studies
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: medium
- type: uses
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: proposes
  target: '[[cognitive-space]]'
  target_id: term:cognitive-space
  confidence: high
- type: proposes
  target: '[[interpretative-meta-tokens]]'
  target_id: term:interpretative-meta-tokens
  confidence: high
- type: uses
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: medium
- type: studies
  target: '[[model-forensics-two-step-protocol]]'
  target_id: method:model-forensics-two-step-protocol
  confidence: medium
- type: supports
  target: '[[j-lens-approximates-cognitive-space-via-token-jacobians]]'
  target_id: mechanism:j-lens-approximates-cognitive-space-via-token-jacobians
  confidence: high
- type: supports
  target: '[[qwen-j-lens-replication-supports-cross-model-cognitive-space]]'
  target_id: mechanism:qwen-j-lens-replication-supports-cross-model-cognitive-space
  confidence: high
- type: supports
  target: '[[interpretative-meta-tokens-mediate-ambiguity-disambiguation]]'
  target_id: mechanism:interpretative-meta-tokens-mediate-ambiguity-disambiguation
  confidence: medium
- type: supports
  target: '[[j-lens-is-auditor-hypothesis-generation-not-verification]]'
  target_id: mechanism:j-lens-is-auditor-hypothesis-generation-not-verification
  confidence: high
---

## Abstract

Nanda's commentary accepts the core scientific claim that models have a [[cognitive-space|cognitive space]] or working memory for intermediate variables during a forward pass, and treats [[jacobian-lens]] as a useful but imperfect way to access it. The commentary also reports an independent Qwen replication and a preliminary new finding: [[interpretative-meta-tokens]] that appear during ambiguous-language disambiguation and have suggestive causal effects under steering.

## Summary

The commentary separates four claims in the Anthropic paper: the scientific claim that a cognitive space exists, the methodological claim that J-lens accesses it better than logit lens, the pragmatic claim that J-lens is useful for audits, and the philosophical claim that the space is analogous to a global workspace. Nanda is most persuaded by the scientific and methodological claims, somewhat persuaded by the pragmatic audit-use claim, and explicitly does not take a strong view on the consciousness interpretation.

The first-principles model is that multi-step computation requires intermediate variables; the residual stream is the cross-layer bottleneck where those variables can be stored; and concepts that many circuits read and write should become consistent directions. J-lens works when these directions are aligned with future output-token Jacobians, but it remains noisy, token-limited, and incomplete. This makes it useful for observing working memory and generating audit hypotheses, but insufficient as stand-alone verification.

The replication section reports that Nanda, Camila Blank, and Agam Bhatia implemented J-lens on Qwen 3.6 27B. They partially replicated verbal report, CKA workspace bands, directed modulation, multilingual and typo experiments, while some harder tasks were weak or failed. The new meta-token case study finds Chinese tokens meaning roughly "what does this mean" around ambiguous sentences; negative steering on those directions reduced context recognition in preliminary tests.

## Extracted numbers

Source: external commentary PDF at `library/pdfs/tc-2026-workspace-commentaries.pdf`, Nanda section.

- Replication setup: Qwen 3.6 27B, Jacobians to the penultimate layer, 25 prompts from the Pile of length 128 tokens, skipping the first four high-norm tokens.
- Reported successful or partial replications: verbal-report swaps, CKA workspace bands, directed modulation, multilingual probing and causal effects, and typo experiments.
- Reported weak or failed replications: multihop factual recall was weak and answer swaps dominated; poetry and arithmetic failed, plausibly due to model capability or experimenter error.
- Cost note: the Anthropic paper averages over n=1000 prompts, while Nanda reports much smaller n can work; the replication used n=25, and a Qwen3.5-397B-A17B trial with n=4 took about one hour on 8 H200s.
- Meta-token case study: examples used 50 rollouts per prompt, two prompts per category, with categories pun, rhyme, and wordplay-hint; negative steering reduced context-recognition rates under an LLM judge, conditional on coherence and topicality.

## Relevance to experiment

This is the most directly actionable commentary for the J-space actuation bridge. It supports implementing a minimal J-lens on Qwen-family open weights and sanity-checking it with model-appropriate evals before trusting readouts. It also warns that J-lens should be used as an exploratory audit and hypothesis-generation tool, not as definitive proof of hidden intent or consciousness. The meta-token result suggests a concrete extension: look not only for uncertainty content tokens, but for tokens naming the computation the model is about to run.

## Claims

- J-lens works because output-token Jacobians approximate a shared cognitive space where reusable intermediate variables live, but the approximation is noisy and token-limited. (Why does J-Lens work? First principles reasoning) [[j-lens-approximates-cognitive-space-via-token-jacobians]]
- Independent Qwen 3.6 27B replication recovered several core workspace phenomena while failing or weakening on harder tasks, supporting cross-model generality with model-ability caveats. (Replicating J-Lens and Interpretative Meta-Tokens; Replication) [[qwen-j-lens-replication-supports-cross-model-cognitive-space]]
- Interpretative meta-tokens in Qwen appear around ambiguous sentences and negative steering on them reduces context disambiguation in preliminary tests, suggesting J-lens can expose algorithm-level state as well as content variables. (Case Study: Interpretative Meta-Tokens) [[interpretative-meta-tokens-mediate-ambiguity-disambiguation]]
- J-lens is useful for model-forensics hypothesis generation, especially around prompt injection, hidden deception, eval awareness, and reward-model appeasement, but it is too noisy for stand-alone verification. (Is J-Lens useful?; Analyzing the case studies in Section 5) [[j-lens-is-auditor-hypothesis-generation-not-verification]]
