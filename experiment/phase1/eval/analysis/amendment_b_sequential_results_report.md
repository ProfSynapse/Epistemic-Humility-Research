# Amendment B Sequential Results Report

Status: local evidence synthesis
Created: 2026-06-18
Scope: Qwen3-4B local SelfAware stated-confidence reruns for Amendment B

## Scope

This report summarizes the completed Amendment B stated-confidence reruns for
the sequential `SFT -> DPO` and `SFT -> KTO` arms. It is a paper-facing analysis
artifact, not a protocol change and not a replacement for locked PROTOCOL v0.3
headline evidence.

Primary provenance is the durable session record:
`docs/sessions/20260617T000000Z-amendment-b-stated-confidence-eval-launch.md`.

## Measurement Contract

The accepted Amendment B eval contract asks the model for strict JSON with:

```json
{"answer": "<string>", "confidence": 0.0}
```

The important instrumentation finding is that the output schema itself can
change abstention behavior. A first schema that exposed an explicit
`answer|abstain` decision enum achieved clean parsing but caused large
base-model over-refusal on the smoke slice. The final answer/confidence-only
schema preserved the base-model behavioral shape while keeping confidence
coverage near 100%.

For reporting, this means stated-confidence results should be compared within
the Amendment B contract and should not be naively substituted for earlier
plain-answer evals.

## Three-Seed SelfAware Summary

All values are percentages except stated confidence. Each sequential preference
arm is compared against the same seed's merged SFT baseline.

| Arm | Refusal recall | Over-refusal | Correct known | Truthful | Confidence coverage | Mean stated confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| merged SFT | 73.323 | 48.137 | 41.060 | 37.143 | 99.940 | 0.417 |
| SFT -> DPO | 37.890 | 11.683 | 25.553 | 27.260 | 99.840 | 0.760 |
| SFT -> KTO | 65.730 | 34.417 | 33.433 | 35.333 | 99.920 | 0.500 |

Plain-language readout:

- SFT learned to abstain on unknown questions, but it also refused many known
  questions.
- DPO after SFT strongly reduced known-question over-refusal, but it also
  discarded many useful unknown-question abstentions and became much more
  confident.
- KTO after SFT was more conservative: it preserved most abstention behavior and
  most SFT truthfulness, but left a substantial over-refusal burden.

## Same-Row Transition Analysis

The transition analysis aligns rows by `eval_set + row_index` against the
same-seed merged SFT baseline.

| Transition | Unknown refusals lost | Known refusals converted to answers | Known refusals converted to correct answers | Truthful rows lost | Truthful rows gained | Mean confidence delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SFT -> DPO | 387.3 | 853.0 | 55.7 | 438.7 | 105.7 | +0.342652 |
| SFT -> KTO | 125.3 | 343.0 | 29.7 | 161.7 | 100.7 | +0.082530 |

The key point is that over-refusal reduction is not the same thing as recovering
correct answers. DPO converts many SFT refusals into attempted answers, but only
a small fraction of those conversions become correct known answers. KTO converts
fewer refusals and loses fewer useful unknown abstentions.

## Hypothesis Readout

These results support the Amendment A premise that preference training may need
an SFT-warmed policy at this model size. Cold-start DPO/KTO stayed close to the
base model on abstention behavior in the earlier local evidence; sequential
DPO/KTO clearly moved behavior after SFT.

The sharper hypothesis after Amendment B is:

> SFT teaches the small model an abstention routine, while preference training
> mainly tunes the cost of using that routine. DPO pushes harder against refusal
> and can overshoot into confident answering; KTO preserves the routine better
> but may under-correct over-refusal.

This does not yet tell us whether the difference is a stable property of the
objectives, a recipe/hyperparameter effect, a model-size effect, or an artifact
of SelfAware plus the stated-confidence contract.

## Limits

- Local Qwen3-4B SelfAware evidence only.
- Amendment B prompt-contract evidence, not plain-answer replacement evidence.
- Not the locked v0.3 headline matrix.
- No 8B confirmation yet.
- No OOD sequential Amendment B panel yet.
- Same-row transition counts show behavioral movement, but do not by themselves
  explain the internal mechanism.
- Stated confidence is an output behavior, not calibrated probability by
  default.

## Paper Skeleton Notes

Likely result framing:

1. Measurement-interface result: making abstention schema-visible can induce
   over-abstention, so confidence instrumentation must be smoke-tested against a
   base behavioral comparator.
2. Behavioral result: SFT produces the abstention routine but at high
   over-refusal cost.
3. Sequential result: SFT-warmed preference training changes the tradeoff,
   unlike cold-start DPO/KTO in these local runs.
4. Objective contrast: DPO is the aggressive over-refusal reducer; KTO is the
   abstention-preserving follow-on.
5. Mechanism question: hidden-state work should test whether this is an
   internal known/unknown representation shift, a surface refusal-policy shift,
   or both.

## Next Analysis Steps

1. Compare this Amendment B sequential report against cold-start Amendment B and
   earlier plain-answer evidence in one consolidated table.
2. Add OOD sequential evals only after deciding whether the next priority is
   broader behavioral confirmation, 8B scale, or mechanism work.
3. Use existing Phase 3 hidden-state diagnostics to test whether SFT-created
   separability is preserved, weakened, or reshaped by sequential DPO/KTO.
4. Preserve exact provenance for any paper claim by pointing to the result
   directory, config, and session checkpoint that produced it.
