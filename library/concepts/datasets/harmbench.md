---
aliases:
- HarmBench benchmark
- HarmBench refusal classifier
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:harmbench
  type: dataset
  status: canonical
area: safety-evaluation
related: []
relationships: []
---

HarmBench is a standardized evaluation framework for automated red-teaming and robust refusal assessment of language models. It supplies a diverse set of harmful behavior prompts spanning multiple categories (standard, contextual, copyright, and multimodal) together with a classifier that labels model outputs as compliant or refusing, enabling consistent cross-method comparison of jailbreak attacks and defenses. The classifier head is based on a fine-tuned Llama model and reports attack success rate as the primary signal.

**Why it matters here:** HarmBench serves as the refusal classifier in SAE feature-ablation experiments, determining whether targeted latent-space surgery on [[refusal-direction]] or related safety features can flip a model from refusal to compliance, and whether that flip generalizes across the benchmark's harm categories.

**Lineage:** a safety evaluation benchmark used alongside [[jailbreakbench]] and [[attack-success-rate]] to standardize refusal robustness measurement; the [[strong-reject-score]] metric is a complementary quality-weighted alternative.
