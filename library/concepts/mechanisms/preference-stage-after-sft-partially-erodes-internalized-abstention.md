---
aliases:
- Warmed preference stage spends internalized abstention, DPO more than KTO
- Gap 3 (prompt-crossing-completion)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:preference-stage-after-sft-partially-erodes-internalized-abstention
  type: mechanism
  status: canonical
cause: "Applying a DPO or KTO preference-tuning stage to a checkpoint that already internalized cold-start SFT abstention (SFT -> DPO, SFT -> KTO, three seeds each), evaluated under the structure-only P-struct contract against each seed's own cold-SFT P-struct parent value (69.57% / 76.94% / 79.36%, established by prompt-vs-training-panel and pstruct-internalization-seed-robustness)."
effect: "All six sequential arms stay at or above the registered 30% internalization floor (falsifier not fired), but five of six show partial erosion relative to their same-seed parent; only kto_seed1 is preserved within +/-10pp (61.43 vs parent 69.57). Erosion is objective-dependent and large for DPO (parent-minus-arm 34.4/22.8/47.6 percentage points across seeds 1-3: arms read 35.17, 54.17, 31.78) and modest for KTO (8.1/11.8/14.0pp: arms read 61.43, 65.12, 65.41). No arm deepens beyond parent+10pp."
polarity: decreases
related:
- '[[prompt-crossing-completion]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
- '[[context-invariance]]'
relationships:
- type: supported_by
  target: '[[prompt-crossing-completion]]'
  target_id: experiment:prompt-crossing-completion
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md#outcome (PC-G1 applied verbatim; parents 69.57/76.94/79.36; floor 30%; band 10pp; falsifier NOT fired)"
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - "contrast: that mechanism measures cold-start DPO/KTO (no prior SFT), which reads 0.00% under P-struct; this mechanism measures the same two objectives applied AFTER internalizing SFT, which retain most of the parent's internalization instead"
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: high
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md#outcome (the six seq arms are read under P-struct with the abstention-eliciting instruction removed, the same context-invariance test the parent cells use)"
---

`prompt-crossing-completion` closes the open question paper 2 called "the most obvious next measurement": whether a preference stage applied to an already-internalized SFT checkpoint preserves, erodes, or deepens what SFT put in the weights. Under the fixed PC-G1 classification (30% floor, 10pp preserve/deepen band, applied verbatim to each seed's own cold-SFT parent), the floor never breaks, but the spend is real and strongly objective-dependent: DPO gives up 22.8 to 47.6 points of internalized refusal recall while KTO gives up only 8.1 to 14.0.

**Why it matters here:** this extends paper 2's Section 4.3 repositioning story from the instructed surface into the weights themselves. DPO and KTO were already known to reposition a cold-start model toward answering at the instructed surface; this shows that when applied to a warmed, internalized checkpoint they partly reposition the internalized behavior too, and DPO spends far more of it than KTO.

**Lineage:** contrasts with [[only-sft-installs-abstention-in-weights]] (the cold-start finding that DPO/KTO from scratch install nothing that survives instruction removal); this mechanism shows the same two objectives behave differently once there is internalized abstention already present to spend. Source of truth: `experiments/prompt-crossing-completion/AMENDMENT.md`, Outcome section, resolved 2026-08-16.
