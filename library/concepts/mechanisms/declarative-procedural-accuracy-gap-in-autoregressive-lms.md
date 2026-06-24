---
aliases:
- declarative-knowledge advantage in LLMs
- procedural deficit in autoregressive models
- GPT-3 declarative-procedural gap
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:declarative-procedural-accuracy-gap-in-autoregressive-lms
  type: mechanism
  status: canonical
cause: "Evaluating a large autoregressive language model (GPT-3 175B) on MMLU subjects that differ in whether correct answers require recall of factual propositions (declarative knowledge) versus execution of multi-step calculations (procedural knowledge)"
effect: "The model scores higher on declarative subjects (College Medicine 47.4%, College Mathematics conceptual 35.0%) than on computation-heavy subjects (Elementary Mathematics 29.9%), with 9 of the 10 lowest-accuracy tasks being calculation-heavy STEM subjects"
polarity: mediates
related:
- '[[2009.03300--mmlu-benchmark]]'
- '[[mmlu]]'
- '[[declarative-procedural-accuracy-gap]]'
- '[[expected-calibration-error]]'
- '[[calibration-humility-gap]]'
- '[[gpt-3]]'
relationships:
- type: supported_by
  target: '[[2009.03300--mmlu-benchmark]]'
  target_id: paper:2009.03300
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: high
- type: related_to
  target: '[[declarative-procedural-accuracy-gap]]'
  target_id: term:declarative-procedural-accuracy-gap
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[calibration-humility-gap]]'
  target_id: term:calibration-humility-gap
  confidence: high
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
  confidence: high
---

Autoregressive language models trained on text corpora encounter far more declarative propositions (facts, definitions, conceptual explanations) than procedural traces (arithmetic steps, algorithm executions). As a result, pretraining installs robust retrieval pathways for declarative knowledge but weaker procedural execution circuits. On MMLU, this manifests as College Medicine outperforming Elementary Mathematics despite the latter being nominally easier by grade level. The asymmetry matters for calibration: models may be overconfident on procedural tasks where their accuracy is lowest, producing the largest calibration errors (Elementary Mathematics RMS ECE 19.4% zero-shot). Disaggregating MMLU by declarative versus procedural question type is therefore a more informative diagnostic than pooled accuracy.
