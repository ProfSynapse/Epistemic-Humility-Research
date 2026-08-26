---
aliases:
- Structural Unknown-option trigger
- Random-word control replicates Unknown-option effect
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:extra-option-structurally-triggers-abstention
  type: mechanism
  status: canonical
cause: "Adding an extra \"Unknown\" answer option (or, as a control, an unrelated random word in the same slot) to True/False questions the model could otherwise answer correctly"
effect: "Accuracy drops sharply and abstention rate rises by a similar magnitude regardless of whether the extra option is semantically \"Unknown\" or an unrelated random word, showing the trigger is the structural presence of an extra option rather than its meaning"
polarity: increases
related:
- '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
- '[[abstention-inflation]]'
relationships:
- type: supported_by
  target: '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
  target_id: paper:2507.16199
  confidence: high
- type: related_to
  target: '[[abstention-inflation]]'
  target_id: term:abstention-inflation
  confidence: high
---

Across three LLMs (DeepSeek-R1, GPT-5.4-nano, Gemini-3.1-Flash-Lite) and True/False question benchmarks (FLD, FOLIO), adding an "Unknown" option drops accuracy by 15.75 percentage points on average relative to the no-option baseline, with the abstention rate rising to 32.9% on average (S1 vs. S2, Table 1, Section 4.1.2). Multiple-choice questions with the same manipulation show only small fluctuations, ruling out question format as the driver (S3, Section 4.1.3). Critically, replacing "Unknown" with an unrelated random word in the same option slot reproduces essentially the same accuracy drop and abstention rate as the semantically meaningful "Unknown" option, while a synonym replacement ("Indeterminate", "I don't know") also reproduces the effect (S4, Section 4.1.4, Figure 3). This rules out a semantic explanation: the model is not abstaining because it recognizes "Unknown" as a meaningful label for its own uncertainty, but because the mere structural presence of an extra abstention-shaped slot triggers the behavior.
