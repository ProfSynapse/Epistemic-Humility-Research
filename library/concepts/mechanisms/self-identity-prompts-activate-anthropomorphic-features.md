---
aliases:
- Self-identity prompts activate anthropomorphic AI trope features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-identity-prompts-activate-anthropomorphic-features
  type: mechanism
  status: canonical
cause: Prompting [[claude-3-sonnet]] with questions about its own nature or identity
effect: Features related to robots, destructive AI, consciousness, moral agency, emotions, and ghosts activate more strongly than on mundane control prompts such as weather questions
polarity: enables
related:
- '[[tc2024--scaling-monosemanticity]]'
- '[[claude-3-sonnet]]'
- '[[sycophancy-feature]]'
- '[[feature-steering]]'
relationships:
- type: supported_by
  target: '[[tc2024--scaling-monosemanticity]]'
  target_id: paper:tc2024
  confidence: high
- type: related_to
  target: '[[claude-3-sonnet]]'
  target_id: model:claude-3-sonnet
- type: related_to
  target: '[[sycophancy-feature]]'
  target_id: term:sycophancy-feature
---

Templeton et al. (tc2024) use SAE feature inspection to probe which concepts activate when Claude 3 Sonnet is asked about its own identity. Self-referential prompts elicit strong activation of features associated with science-fiction AI tropes -- robots, dangerous AI, consciousness, moral patienthood, and ghostly entities -- compared to neutral weather control prompts. This pattern suggests that large language models internalize culturally loaded concepts about AI identity during training, and that those representations are causally accessible via interpretability probes.
