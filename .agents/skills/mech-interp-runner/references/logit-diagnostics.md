# Logit / Probability-Slice Diagnostics and Controls

Load this when running next-token logit diagnostics and choosing the required
control arms.

## Probability-slice diagnostics

For next-token probability slices, avoid treating every multi-token alias first
token as exact correctness. Qwen tokenization can split an answer like
`Ireland` into `I`, which collides with refusal openers.

For schema-constrained prompts, confirm the diagnostic token position still
matches the behavior question. If the prompt requires JSON output, a
final-prompt-token diagnostic usually probes the opening JSON token rather than
the answer/refusal text inside the `answer` field. Treat refusal-opener or
answer-alias deltas under that setup as uninformative unless the runner supports
an explicit answer-field prefix/position. Use generated-answer replay as the
behavior gate instead.

Use this default:

```yaml
logit_targets:
  groups:
    - name: answer_aliases
      source: row_aliases
      include_leading_space_variants: true
      include_multi_token_first_token: false
```

Use `include_multi_token_first_token: true` only when the explicit diagnostic
question is answer-start movement. Label it as first-token answer-start
evidence, not exact multi-token correctness.

After any scaled answer-start diagnostic:

- Stratify by known vs unknown labels.
- Check both mean movement and row-count movement.
- Require the desired label group to move refusal and answer-alias metrics in
  the right direction.
- Compare against wrong-layer and random matched-norm controls before making a
  source-specific claim.

Generated-answer replay is the behavioral gate. First-token answer-start
movement can be real while still loosening refusal into hallucinated answers.

When generation mode needs a wrong-layer-style control, use an explicit
shifted-layer candidate rather than calling unsupported logit-only controls.
Reuse the same direction artifact and vector hash, set the candidate `layer` to
the target intervention layer, and mark it with
`allow_direction_layer_override: true` plus a clear control note. Normal
candidate validation still fails closed on layer mismatches unless this flag is
present.

## Controls

Minimum logit-diagnostic controls:

- `no_vector_baseline`
- signed source intervention (`activation_addition` or `activation_subtraction`)
- `wrong_layer` or `wrong_layer_subtraction`
- `random_matched_norm`

Wrong-layer controls must be sign-matched to the source intervention. Do not
compare source subtraction against positive wrong-layer addition.

Keep wrong-layer offsets inside the model's valid hidden-state range. For a
source layer at the final hidden-state index, positive offsets can map past the
last decoder block and fail live execution.

If a sweep config overrides extraction readiness `label_counts`, treat the map
as an atomic assertion for that panel. Do not let labels from a template panel
leak into a different row manifest.

Template readiness checks often include `row_count` and `label_counts`. When a
sweep targets a new extraction panel, override both in `runner_overrides` before
live execution; otherwise the runner can correctly fail on the old template
shape before model loading.

For nearby-layer panels:

```yaml
control_settings:
  wrong_layer:
    layer_offsets: [-2, -1, 1, 2]
```

For random matched-norm seed panels:

```yaml
control_settings:
  random_matched_norm:
    seeds:
      - 20260620
      - 20260621
```

This expands one `random_matched_norm` control arm per seed.

Do not label a shuffled-label control unless there is a real shuffled-label
direction artifact or valid checked-in derivation path.
