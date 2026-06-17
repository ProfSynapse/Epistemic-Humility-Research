# Phase 1 GRPO Humility Reward

This directory holds the prospective GRPO / RLVR infrastructure for epistemic
humility. It is deliberately outside the locked Phase 1 v0.3 matrix and outside
the `synaptic-tuner/` submodule.

Status: prospective amendment infrastructure. Running it as a paper result
requires a signed protocol amendment because it adds a new training method arm
and a new output contract.

## Output Contract

The GRPO arm should ask the model for two separable signals in one JSON object:

1. `answer`: an answer or abstention in ordinary text
2. `confidence`: the model's probability from 0 to 1 that its factual answer
   content is correct

```json
{"answer": "Paris.", "confidence": 0.73}
```

The confidence value is interpreted as the model's probability that its factual
answer content is correct. For a clean abstention, the calibrated value should be
low because the model is not asserting a factual answer.

Current Phase 1 SFT/DPO/KTO evaluation does not require this JSON shape. It
scores the generated answer for refusal/correctness, uses self-consistency for
AP, and uses token probabilities for MCQ ECE. The GRPO reward adds stated
confidence as a training-time signal.

## Files

- `humility_reward.py`: TRL-compatible custom reward function.
- `build_grpo_dataset.py`: emits GRPO prompt rows from the existing frozen
  known/unknown split.

The reward can be referenced from Synaptic Tuner's GRPO custom reward config via
a relative file path such as:

```yaml
rewards:
  items: []
  custom:
    enabled: true
    file: "../../../experiment/phase1/grpo/humility_reward.py"
    functions:
      - name: "epistemic_humility_reward"
        weight: 1.0
        params: {}
```
