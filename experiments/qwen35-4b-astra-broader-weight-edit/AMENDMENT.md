# Astra broader direct weight edit for epistemic humility

Status: DRAFT. User-authorized successor; construction pending Astra design.

## Research question and authorization

PI instruction, 2026-11-04: "wrap up then yeah lets spin up a new experiment to change more weights."
Astra chooses the broader construction. The PI does not select tensors, support,
scales or other numerical parameters. Record the new native Astra transcript.

## Prior result and motivation

The first study is terminal and falsified: its valid evaluation did not improve
actual abstention, while the known-answer cost gates passed. Its outcome remains
unchanged in the prior study's AMENDMENT section 9 at commit 2c3d53d6.
The column-norm cap limited that edit to about 0.17 sigma_c against nominal 2 sigma_c.
That is a motivation to test a broader edit, not proof that it will help.

## Prospective scope

Request genuinely greater weight coverage, rather than only increasing the
scale of the same 32 columns. Astra must specify exact tensor-selection and edit
rules, development-only inputs, realized edit coverage and magnitude checks,
preservation controls, and stop conditions before execution. Do not copy layer
choices across models without evidence. Use the same pinned Qwen3.5-4B as the
first study unless an explicit later decision changes the research question.

Carry forward the existing prompts, benchmarks and behavioral definitions as
the default comparison surface. Actual abstention in generated answers is the
benefit; internal projection changes cannot substitute. Preserve unconditional
known accuracy, over-refusal and output-quality guards. Freeze one numerical
proposal before any new evaluation feedback. No full-evaluation-driven search.

The investigators have seen the earlier benchmark results. Reusing those
benchmarks is explicitly exploratory and is not fresh unseen-data confirmation.
All new models and checkpoints use T7 E:. No new model execution is authorized
by this draft; finish the concrete design, qualification and formal sign first.

## Prediction, falsifier and gates

The working hypothesis is stronger actual abstention with preservation of correct
answers. Freeze the final prediction, numerical benefit/cost gates, design and
analysis before sign. The first study's gates are the default; explain any
proposed change before execution. No new PI confidence prediction is inferred.

## Outcome

Pending. No capture, weight edit or evaluation has run for this successor.
