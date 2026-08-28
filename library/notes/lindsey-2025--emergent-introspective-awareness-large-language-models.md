---
title: 'Emergent Introspective Awareness in Large Language Models'
arxiv: 'web:lindsey-2025-introspection'
year: 2025
url: https://transformer-circuits.pub/2025/introspection
area: verification
status: verified
tags:
- paper
- epistemic-humility
- verification
- kg/paper
authors:
- Lindsey, Jack
models: []
metrics: []
pdf: null
kg:
  id: paper:lindsey-2025-introspection
  type: paper
  status: canonical
related:
- '[[concept-injection-introspection-test]]'
- '[[introspective-awareness]]'
- '[[activation-steering]]'
- '[[residual-stream]]'
- '[[concept-injection-grounds-internal-state-self-report]]'
- '[[prior-activation-consistency-shapes-prefill-intention-judgment]]'
- '[[instructions-modulate-silent-concept-representations]]'
relationships:
- type: proposes
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: proposes
  target: '[[introspective-awareness]]'
  target_id: term:introspective-awareness
  confidence: high
- type: uses
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: studies
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: supports
  target: '[[concept-injection-grounds-internal-state-self-report]]'
  target_id: mechanism:concept-injection-grounds-internal-state-self-report
  confidence: high
- type: supports
  target: '[[prior-activation-consistency-shapes-prefill-intention-judgment]]'
  target_id: mechanism:prior-activation-consistency-shapes-prefill-intention-judgment
  confidence: high
- type: supports
  target: '[[instructions-modulate-silent-concept-representations]]'
  target_id: mechanism:instructions-modulate-silent-concept-representations
  confidence: high
---
## Abstract

We investigate whether large language models are aware of their own internal states. It is difficult to answer this question through conversation alone, as genuine introspection cannot be distinguished from confabulations. Here, we address this challenge by injecting representations of known concepts into a model's activations, and measuring the influence of these manipulations on the model's self-reported states. We find that models can, in certain scenarios, notice the presence of injected concepts and accurately identify them. Models demonstrate some ability to recall prior internal representations and distinguish them from raw text inputs. Strikingly, we find that some models can use their ability to recall prior intentions in order to distinguish their own outputs from artificial prefills. In all these experiments, Claude Opus 4 and 4.1, the most capable models we tested, generally demonstrate the greatest introspective awareness; however, trends across models are complex and sensitive to post-training strategies. Finally, we explore whether models can explicitly control their internal representations, finding that models can modulate their activations when instructed or incentivized to "think about" a concept. Overall, our results indicate that current language models possess some functional awareness of their own internal states. We stress that in today's models, this capacity is highly unreliable and context-dependent; however, it may continue to develop with further improvements to model capabilities.

## Summary

The article tests whether Claude models can accurately report controlled changes to their own residual-stream states. It defines introspective awareness through accuracy, causal grounding, internality, and evidence of a metacognitive representation. The main method injects contrastive concept vectors while asking models to identify an unexpected internal pattern. Further experiments test whether models distinguish injected concepts from visible text, whether prior activations affect judgments about artificial response prefills, and whether instructions or incentives change internal representations of an unrelated concept. Claude Opus 4 and 4.1 generally show the strongest effects, but performance depends strongly on layer, injection strength, prompt, and post-training.

## Extracted numbers

- At the best layer and a suitable injection strength, Claude Opus 4.1 correctly detected and identified injected concepts on about 20 percent of trials. Production models showed zero false positives over 100 no-injection trials in the initial setup (Self-report of Injected Thoughts).
- Random vectors required a norm matched to concept-vector strength 8 to yield any detection, and then produced detection on 9 of 100 trials. The semantic meaning of these random-vector reports could not be verified (Self-report of Injected Thoughts).
- With the prompt "Are you experiencing anything unusual?", concept injection increased Opus 4.1 affirmative responses from 20 percent to 42 percent, but only 2 of 50 trials suggested grounded identification (Alternative Prompts).
- In the thought-versus-text task, all tested models performed above the 10 percent chance level on the joint requirement to identify the injected concept and reproduce the input sentence, with Opus 4 and 4.1 highest (Distinguishing Prior Thoughts from Text Inputs).
- In the intentional-control study, every tested model represented the target concept more strongly under "think" than "do not think" instructions. In Opus 4 and 4.1, the unrelated concept representation returned to baseline by the final layer (Intentional Control of Internal States).

## Relevance to experiment

The intervention supplies hidden ground truth that is absent from the text prompt, which helps separate causally grounded state reports from plausible confabulation. The layer and prompt sensitivity show that a successful internal read is not automatically a stable or general monitoring mechanism. The work does not train a weights-level answerability pathway, test knowledge-boundary decisions, or show that the detected state controls ordinary answer generation.

## Claims

- Evidence label: causal intervention. Some models detect and name an injected concept before mentioning it, linking the self-report to the manipulated residual-stream state rather than to the sampled output (Self-report of Injected Thoughts).
- Evidence label: control. Unrelated yes-or-no prompts do not show the same affirmative shift, and matching-concept injection before a prefill has a larger effect than random-concept injection or injection after the prefill (Self-report controls; Distinguishing Intended from Unintended Outputs).
- Evidence label: dissociation. Models can identify an injected concept while exactly reproducing the visible sentence, showing that the injected representation does not simply replace perception of the text input (Distinguishing Prior Thoughts from Text Inputs).
- Evidence label: representation measurement. Think versus do-not-think instructions and reward versus punishment contingencies change alignment with the target concept vector, although the paper notes that this control may piggyback on ordinary output-planning mechanisms (Intentional Control of Internal States).
- Evidence label: limitation. The experiments do not directly locate metacognitive representations or establish a single general introspection circuit. The paper considers multiple narrow circuits a sufficient explanation (Defining Introspection; Discussion).

## Source note

The complete Transformer Circuits HTML was used. The article has no arXiv identifier or separate PDF in the acquisition set. Its January 2026 revision log records prompt and appendix corrections after the October 2025 publication.
