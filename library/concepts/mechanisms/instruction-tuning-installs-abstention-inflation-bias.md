---
aliases:
- Abstention Inflation emerges through instruction tuning
- Supervision mismatch installs a structural abstention bias
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-installs-abstention-inflation-bias
  type: mechanism
  status: canonical
cause: "Instruction tuning a base model (moving from Base to an instruction-tuned/IT variant), holding model size fixed, then comparing sensitivity to a structural \"Unknown\"-option abstention trigger"
effect: "Abstention rate under the trigger rises alongside accuracy gains in the IT model relative to its own base model, and the rise is not explained by model size, temperature, or task difficulty, indicating the bias is installed by the instruction-tuning process itself"
polarity: increases
related:
- '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
- '[[abstention-inflation]]'
- '[[extra-option-structurally-triggers-abstention]]'
- '[[instruction-tuning-causes-over-abstention]]'
relationships:
- type: supported_by
  target: '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
  target_id: paper:2507.16199
  confidence: high
- type: related_to
  target: '[[abstention-inflation]]'
  target_id: term:abstention-inflation
  confidence: high
- type: related_to
  target: '[[extra-option-structurally-triggers-abstention]]'
  target_id: mechanism:extra-option-structurally-triggers-abstention
  confidence: high
- type: related_to
  target: '[[instruction-tuning-causes-over-abstention]]'
  target_id: mechanism:instruction-tuning-causes-over-abstention
  confidence: medium
---

Ling et al. (2025) rule out stochastic noise as the explanation for Abstention Inflation before attributing it to training: 52.4% of samples showing the effect abstain on all 3 repeated draws at T=0.5, far above the 12.5% expected under random fluctuation (GPT-5.4-nano reaches 71% full-persistence); temperature sweeps from 0.0 to 2.0 leave the abstention rate essentially unchanged (S9-S10, Section 4.4). Comparing model size and alignment stage (S10, Figure 9): across four model sizes, instruction-tuned (IT) models' abstention rate under the trigger varies little with size and is not explained by size, while base models fluctuate more; and for every model size tested, moving from Base to IT raises both accuracy and abstention rate together. The authors attribute this to a supervision mismatch during instruction tuning: a training example where the model correctly abstains because the answer is genuinely unknown, and one where it abstains from difficulty or unsureness, both look identical at the label level (an abstention response receiving the same positive training signal), so instruction tuning teaches the model to imitate the surface pattern of abstention generally rather than to abstain only when genuinely uncertain.
