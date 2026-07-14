---
title: Causal Intervention
aliases:
  - activation intervention
  - causal control test
tags:
  - kg/method
  - concept
  - method
kg:
  id: method:causal-intervention
  type: method
  status: canonical
area: methods
related:
  - '[[activation-addition]]'
  - '[[activation-patching]]'
  - '[[correlational-probe]]'
relationships:
  - type: related_to
    target: '[[activation-addition]]'
    target_id: method:activation-addition
    confidence: high
  - type: related_to
    target: '[[activation-patching]]'
    target_id: method:activation-patching
    confidence: high
  - type: different_from
    target: '[[correlational-probe]]'
    target_id: method:correlational-probe
    confidence: high
---

A causal intervention modifies activations, weights, prompts, or another model
state and measures whether behavior changes under controls. mechanism program uses this
node for local activation-addition, subtraction, patching, and future
adapterless-base intervention tests.

