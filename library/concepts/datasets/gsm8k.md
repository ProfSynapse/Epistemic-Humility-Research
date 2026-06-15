---
aliases:
- Grade School Math 8K
- Graduate School Math 8K
- GSM-8K
- grade-school math
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:gsm8k
  type: dataset
  status: canonical
area: datasets
related:
- '[[math-benchmark]]'
relationships:
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
---

GSM8K is a benchmark of approximately 8,500 grade-school-level math word problems requiring multi-step arithmetic reasoning to solve correctly. Each problem is paired with a natural-language solution, making it suitable for evaluating both final-answer accuracy and reasoning chain quality. The benchmark was widely adopted after GPT-3-era models demonstrated that chain-of-thought prompting dramatically improved performance.

**Why it matters here:** GSM8K serves as the arithmetic reasoning evaluation split for [[confidence-elicitation]] experiments, where models must produce both an answer and a calibrated confidence estimate, testing whether verbalized probabilities track accuracy on structured reasoning tasks.

**Lineage:** related to [[math-benchmark]] (the broader category of mathematical reasoning evaluations).
