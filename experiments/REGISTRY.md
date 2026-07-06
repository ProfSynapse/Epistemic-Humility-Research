<!-- GENERATED - do not edit; run bin/exp regen and stage the result -->

# Experiments registry

| slug | type | status | PR | question | verdict |
| --- | --- | --- | --- | --- | --- |
| ap-veto-length-balanced-confirmatory | probe-fit | resolved |  | On the raw base, does the post-generation correctness veto (post-L20 S/W/U dial) separate hallucinated answers from good answers by CONTENT rather than by answer length, once the classes are length-balanced and the 96-token truncation artifact is removed by extending the token budget? | CONFIRMED with answerability caveat: gates all PASS; the content-trust veto adds genuine signal over BOTH length and answerability (answerability-controlled AUROC ~0.74, margin +0.24, 95% CI [0.12,0.37] excludes 0), promoting AM's ~0.77 length-matched estimate on a fresh 192-token generation. The 0.86/+0.37 headline is answerability-inflated (37% of matched halluc are unanswerable-confabs, veto ~0.99 on those) and must not be cited as the content characteristic; honest number ~0.74. |
| example-cell | steer-cell | draft |  | teaching artifact: Teaching artifact for the mechinterp-cells skill; parses against the real tuner schema and runs end to end, but is never signed and never launched as confirmatory. |  |
