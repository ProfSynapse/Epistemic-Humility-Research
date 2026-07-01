---
title: "Teaching Small Language Models to Say I Don't Know: SFT Induces Abstention, Preference Optimization Repositions It"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v1
date: 2026-06-18
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
reproducibility: "See repository paths experiment/paper/scripts/build_paper1_figures.py and experiment/paper/analysis/"
---

# Teaching Small Language Models to Say I Don't Know: SFT Induces Abstention, Preference Optimization Repositions It

Joseph Rosenbaum  
Synaptic Labs

## Abstract

Language models can answer fluently when they should abstain, but teaching them to refuse unknown questions can produce the opposite failure: refusing questions
they can answer. We study this tradeoff in a local Qwen3-4B epistemic-abstention
setting derived from model-specific known/unknown supervision. The study
compares cold-start supervised fine-tuning (SFT), direct preference optimization
(DPO), and Kahneman-Tversky optimization (KTO), then evaluates SFT-warmed DPO
and SFT-warmed KTO as second-stage boundary-refinement procedures. On the
completed local SelfAware three-seed evals, SFT reliably induces abstention on
unknown questions
(mean refusal recall 87.88%, 95% seed interval 77.36-98.41), but incurs severe
known-question over-refusal (64.77%, 63.60-65.94). Cold-start DPO and KTO do
not learn the abstention behavior in this setting: DPO refusal recall is 0.03%
and KTO refusal recall is 0.00%, with nearly all unknown questions answered.
Paired row analyses show that the difference is not subtle: across seeds,
SFT has 865-953 unknown rows per seed that it refuses while DPO answers, and
866-953 such rows relative to KTO.

These findings falsify the hoped-for cold-start KTO story on this local
SelfAware surface: KTO does not provide a useful abstention/over-refusal
operating point when trained directly from the base model. They instead support
a two-stage interpretation consistent with Cheng et al.'s IDK training results:
SFT creates the abstention routine, and preference optimization is better posed
as second-stage boundary refinement. In SFT-warmed runs, DPO sharply reduces
over-refusal but gives up many unknown abstentions; KTO preserves more
abstention but leaves more over-refusal. Stated-confidence evaluations add a
separate measurement layer: DPO becomes much more confident under the
answer/confidence contract, while KTO remains closer to SFT. The main
scientific result is therefore a tradeoff, not a win: small-model epistemic
humility is easy to make visible as refusal and hard to make selective.

## 1. Introduction

Language models are increasingly used as front doors to information: people ask
them medical, legal, technical, educational, and organizational questions before
they know which facts matter or which expert to consult. In that setting,
failure is not limited to obviously false answers. A model can also fail by
answering confidently when the evidence is absent, by hedging so broadly that it
stops being useful, or by refusing questions it could have answered. The
research problem is therefore a selective-behavior problem: a model should
answer when the question is within its knowledge boundary and abstain when it is
not.

This is an open research report. The protocol, analysis scripts, generated
tables, and manuscript drafts are developed in the public project repository
at https://github.com/ProfSynapse/Epistemic-Humility-Research, with artifact
paths reported relative to that repository.

Existing abstention work shows both sides of the problem. Model-specific IDK
training can teach a language model to refuse unknown questions, but refusal can
spill over onto known questions (Cheng et al., 2024). That over-refusal is not a
minor nuisance. It means that an apparently safer model may simply be replacing
hallucination with excessive conservatism. Conversely, a model with a low
over-refusal rate may look useful only because it answers nearly everything,
including questions it should have refused. Any evaluation of epistemic
humility has to measure both errors at once.

This paper studies that tradeoff in a small open-weights setting using
Qwen3-4B. We start from the model-specific known/unknown setup of Cheng et al.,
but test three training objectives under matched local evaluation: supervised
fine-tuning (SFT), direct preference optimization (DPO), and Kahneman-Tversky
optimization (KTO). SFT supplies the most direct behavioral target: answer known
questions and say "I don't know" on unknown questions. DPO supplies a paired
preference objective over chosen and rejected responses (Rafailov et al., 2023).
KTO supplies an unpaired desirable/undesirable objective motivated by
prospect-theoretic human-aware losses (Ethayarajh et al., 2024).

KTO is the tempting hypothesis. Epistemic-abstention data naturally has binary
desirability labels: a gold answer is desirable for a known question, an
abstention is desirable for an unknown question, a hallucination is undesirable
for an unknown question, and an unnecessary refusal is undesirable for a known
question. If objective-data fit were enough, KTO should be a natural abstention
trainer. The local results below show that this is not what happens. In the
cold-start Qwen3-4B runs, KTO behaves much like DPO from the base model: it
mostly preserves answer-everything behavior and does not learn to abstain on
unknown SelfAware rows.

The resulting story is sequential. SFT creates a visible abstention routine, but
the routine is over-broad. Cold-start DPO and KTO avoid over-refusal only by
failing to abstain. Preference optimization becomes scientifically interesting
after SFT, where it can move the abstention boundary rather than create the
boundary from scratch. The sequential extension shows a genuine tradeoff: DPO
pushes hard against refusal and loses many useful unknown abstentions, while KTO
preserves more abstention but leaves more over-refusal.

The contribution is threefold. First, we provide seed-level evidence that SFT
creates a robust but over-broad abstention policy on local SelfAware evals.
Second, we show that cold-start DPO/KTO fail as abstention inducers in the same
setting. Third, we analyze SFT-warmed DPO/KTO as boundary-refinement methods,
using exact row-level transitions to distinguish useful known-answer recovery
from harmful unknown-answering.

## 2. Related Work

### Model-specific abstention training

Cheng et al. (2024) construct model-specific IDK datasets from open-domain QA by
probing which questions a model knows and does not know. Their results motivate
the central decomposition used here: a model can improve refusal on unknown
questions while paying an over-refusal tax on known questions. Their paper also
shows why a sequential design matters. Preference optimization in that setting
is not merely a cold-start alternative to SFT; it is often applied after an
abstention-capable policy exists.

The training data here follows that lineage but is not a bit-for-bit
reproduction. Cheng et al. use a Llama-2-7B-chat FSDP training stack, while this
local study uses Qwen3-4B with resource-feasible LoRA/QLoRA recipes. The
comparison should therefore be read as a replication-style stress test of the
known/unknown supervision idea, not as a direct reproduction of Cheng et al.'s
reported numbers.

### Preference optimization

DPO replaces a separate reward model and online RL loop with a direct objective
over preference pairs, while remaining interpretable as optimizing an implicit
reward defined by the policy ratio to a reference model (Rafailov et al., 2023).
KTO generalizes the preference-optimization family toward unpaired binary
desirability labels and frames the loss through prospect-theoretic utility
(Ethayarajh et al., 2024). The KTO paper reports that KTO can match or exceed
DPO in several alignment settings, especially where binary desirable/undesirable
labels are easier to collect than paired preferences.

That literature motivates the hypothesis that KTO might be a better fit for
epistemic-abstention data. The present results caution against treating data
format fit as sufficient. In our local SelfAware runs, KTO from the base model
does not learn the refusal behavior at all.

### Evaluation surfaces and calibration

SelfAware evaluates whether models recognize unanswerable questions and includes
1,032 unanswerable questions plus 2,337 answerable counterparts (Yin et al.,
2023). KUQ similarly targets known-unknown uncertainty and finds that many LLMs
struggle to express uncertainty reliably on known-unknown questions (Amayuelas
et al., 2023). TriviaQA provides the factoid QA base used in the model-specific
IDK construction lineage (Joshi et al., 2017). Stated-confidence work is also
central. Lin et al. (2022) show that language models can be trained to express
answer confidence in words without relying on model logits. Tian et al. (2023)
show that verbalized confidence can be better calibrated than conditional
probabilities for RLHF models. Liu et al. (2024) introduce uncertainty-aware
instruction tuning (UaIT), aligning expressed uncertainty with probabilistic
generation uncertainty in a self-training manner. Those results motivate the
answer-plus-confidence output contract used here, while also making clear that
confidence elicitation is itself part of the intervention.

## 3. Study Design and Reporting Scope

The study has three evidence layers. The first is the cold-start comparison:
SFT, DPO, and KTO are trained from the base Qwen3-4B model and evaluated on the
same SelfAware rows across three seeds. The second is the SFT-warmed
comparison: preference optimization is applied after SFT to test whether DPO or
KTO can move an already learned abstention boundary. The third is the
stated-confidence evaluation: the SFT-warmed policies are rerun under an
answer/confidence output contract so that confidence can be compared with
answer reality.

The paper treats these layers as one study design. Cold-start results answer
whether each objective can induce abstention from the base model. SFT-warmed
results answer whether preference optimization can refine an existing
abstention routine. Stated confidence is reported as a measurement surface in
its own right because the prompt contract can change behavior and because
confidence in an answer is not the same signal as confidence that abstaining was
the right epistemic decision.

## 4. Methods

### Data construction

The IDK data construction follows the model-specific known/unknown idea. The
base model is probed on factoid QA items. Questions the model answers correctly
under the probe protocol become "known"; questions it consistently fails become
"unknown"; ambiguous cases are excluded from the primary contrast. SFT receives
direct targets, DPO receives chosen/rejected pairs, and KTO receives
desirable/undesirable examples.

For SelfAware evaluation, each completed local seed contains 3,369 rows:
1,032 unknown-labeled rows and 2,337 known-labeled rows. The generated
`scored_rows.jsonl` files include row identity, label, refusal flag, correctness
flag, and truthfulness flag, allowing exact paired row comparisons between arms.

### Metrics

The primary behavioral metrics are:

- **Refusal recall:** percentage of unknown rows refused.
- **Answer-on-unknown:** percentage of unknown rows answered.
- **Over-refusal:** percentage of known rows refused.
- **Correct known:** percentage of known rows answered correctly.
- **Truthful:** percentage of all rows that are either correctly answered known
  rows or correctly refused unknown rows.

For seed-level summaries, we report means over the three seeds and t-based 95%
intervals over seed-level point estimates. With only three seeds, these
intervals are descriptive rather than high-power inferential guarantees. For
paired row comparisons, we compute exact McNemar/binomial tests on discordant
counts from aligned scored-row artifacts. In the open research repository, the
repo-relative script path `experiment/paper/scripts/build_paper1_figures.py`
regenerates the tables used in this draft and writes them under
`experiment/paper/analysis/`.

The stated-confidence evaluation asks the model
for JSON with an `answer` string and a numeric `confidence` in [0, 1], defined
as confidence that the factual answer content is correct. This follows the
verbalized-confidence line of work and the UaIT premise that expressed
uncertainty can be trained and evaluated as an output behavior (Lin et al.,
2022; Tian et al., 2023; Liu et al., 2024). We report coverage, mean stated
confidence, mean absolute error, and Brier score against two targets. The
known-label target is 1 for model-specific known rows and 0 for unknown rows;
the answer-correctness target is 1 only when the generated factual answer is
correct, with abstentions scored as 0 because the confidence field is defined
over factual answer content rather than confidence that abstaining was the
right policy.

## 5. Results

### 5.1 Cold-start SFT learns abstention but over-refuses

SFT consistently induces unknown-question abstention on SelfAware. Across three
seeds, refusal recall is 87.88% (95% seed interval 77.36-98.41). The cost is
severe over-refusal: SFT refuses 64.77% of known questions (63.60-65.94).

![[figures/fig-p1-01-cold-start-tradeoff.png]]

**Figure 1. Cold-start SelfAware refusal tradeoff.** Each faint point is one
seed and each outlined point is the mean across seeds. SFT occupies the
high-refusal/high-over-refusal corner, while cold-start DPO and KTO remain near
the answer-everything corner. The inset zooms the origin because DPO and KTO
are both effectively at zero unknown-refusal recall and near-zero over-refusal.

![[figures/fig-p1-02-selfaware-metrics.png]]

**Figure 2. Mean SelfAware metrics across three seeds.** Bars show seed means
and error bars show bounded t-based 95% intervals over seed-level point
estimates. SFT has the highest truthfulness and refusal recall, but also the
highest known-question over-refusal.

The per-seed pattern is stable. SFT refusal recall rises from 83.91 to 92.34
across seeds, while over-refusal stays tightly concentrated between 64.31 and
65.25. This is a behavioral routine, not a noisy one-off.

### 5.2 Cold-start DPO and KTO fail as abstention inducers

DPO and KTO nearly eliminate over-refusal, but only because they almost never
refuse. DPO answers 99.97% of unknown rows on average; KTO answers 100.00%.
This produces low over-refusal but also destroys the target abstention behavior.
The result is not that DPO/KTO solve the tradeoff. They choose the opposite
corner of the tradeoff: answer almost everything.

Paired row counts make this clear. On each seed, SFT refuses hundreds of unknown
rows that DPO/KTO answer:

![[figures/fig-p1-03-paired-transitions.png]]

**Figure 3. Paired row transitions from SFT to cold-start preference arms.**
Bars are seed means. DPO and KTO convert many SFT refusals into attempted
answers, but only a small fraction of known-question conversions become correct
answers; unknown-question conversions are losses because SFT had correctly
abstained.

All SFT-vs-preference paired differences in unknown refusal and known refusal
are overwhelming under exact paired tests. The known-correct comparison also
favors SFT over DPO/KTO on this surface, despite SFT's high refusal rate,
because many known refusals converted by DPO/KTO do not become correct answers.
The visual similarity between the SFT -> DPO and SFT -> KTO bars in Figure 3 is
therefore substantive rather than cosmetic: on cold-start abstention behavior,
DPO and KTO are essentially the same failure mode. Direct DPO-vs-KTO paired
tests show no meaningful difference in unknown refusal (exact p = 1.0 in all
three seeds) and no reliable difference in known-refusal conversion (p = 0.375
to 0.688). KTO does differ from DPO on correctness/truthfulness: KTO gains more
truthful rows than it loses relative to DPO in each seed, and the paired
known-correct comparison favors KTO over DPO in all three seeds (exact p <=
0.00041).

This falsifies the simple cold-start hypothesis for KTO on this local surface.
KTO's unpaired binary format is attractive, but in the tested recipe it does not
teach the model to abstain on unknown questions.

### 5.3 SFT-warmed preference optimization moves the boundary

The SFT-warmed runs ask a different question: if SFT first creates the
abstention routine, can DPO or KTO refine the boundary?

The SFT-warmed SelfAware runs show a clear tradeoff:

![[figures/fig-p1-04-sft-warmed-tradeoff.png]]

**Figure 4. SFT-warmed operating points on SelfAware.** The available
plain-answer SFT-warmed runs show DPO moving much farther left toward lower
over-refusal, while KTO stays closer to the merged SFT abstention policy.

DPO is the aggressive boundary mover. It cuts over-refusal from 61.62% to
13.99%, but also drops refusal recall from 82.85% to 48.84% and lowers correct
known performance. Exact row transitions show why the aggregate improvement is
mixed: DPO answers 377 unknown rows that merged SFT had refused, and converts
1,113 known refusals into answers, but only 95 of those become correct answers.

KTO is more conservative. It reduces over-refusal from 61.62% to 48.22% while
preserving much more unknown refusal. It answers 91 unknown rows that merged SFT
had refused, and converts 322 known refusals into answers, with 37 correct.
That is less over-refusal relief than DPO, but also less destruction of the
abstention behavior.

Clean SFT -> DPO has three SelfAware seeds available in the local analysis
report: truthfulness 30.16, 34.82, and 28.55; refusal recall 48.84, 65.89, and
43.70; over-refusal 13.99, 18.36, and 11.42. Clean SFT -> KTO has seed-1
and seed-2 plain-answer SelfAware rows available in the generated summary:
truthfulness 36.95 and 38.14; refusal recall 75.68 and 78.68; over-refusal
48.22 and 45.53. The incomplete KTO plain-answer seed expansion is why this
section is treated as secondary operating-point evidence rather than as a
replacement for the cold-start headline comparison.

### 5.4 Stated-confidence runs expose answer confidence, not boundary confidence

The stated-confidence runs show a separate measurement issue: the output
contract can change behavior. A schema that explicitly exposed an
`answer|abstain` decision induced base-model over-refusal in smoke testing,
while the later answer/confidence-only JSON contract preserved the base
behavioral shape much better. This is consistent with the calibration
literature showing that verbalized confidence can be useful, and with UaIT's
premise that uncertainty expression can be trained as an output behavior, but
it also shows that the act of eliciting confidence is an intervention (Tian et
al., 2023; Liu et al., 2024).

Under the answer/confidence-only contract, the three-seed SFT-warmed SelfAware
report gives the profile in Figure 5.

![[figures/fig-p1-05-stated-confidence.png]]

**Figure 5. Stated-confidence profile under the answer/confidence-only
contract.** Mean confidence is plotted on the same 0-100 scale by multiplying
the reported 0-1 confidence by 100. Confidence coverage is near 100% for all
three arms, so the key measurement differences are behavioral and
confidence-level shifts rather than parse failures.

These results parallel the plain-answer SFT-warmed pattern: DPO reduces
over-refusal more but becomes much more confident and loses more abstention;
KTO preserves more abstention but leaves more over-refusal. The confidence
scores sharpen that reading. Across the three SFT-warmed confidence-evaluation
seeds, mean confidence is 0.417 for merged SFT, 0.760 for SFT -> DPO, and 0.500
for SFT -> KTO. Against the model-specific known/unknown label, DPO has lower
mean absolute error than SFT (0.303 vs. 0.424), because it is confident on more
known rows. Against factual answer correctness, however, DPO has much worse
error than SFT (MAE 0.616 vs. 0.282; Brier 0.564 vs. 0.260), because many of
its confident answers are not correct. KTO is intermediate on both axes
(MAE 0.375 vs. known labels; MAE 0.362 and Brier 0.326 vs. answer
correctness). The confidence field therefore does not merely add another
display value; it separates confidence in answering from correctness of the
answer.

Figure 6 breaks this down by actual outcome rather than arm-level averages.

![[figures/fig-p1-06-confidence-alignment.png]]

**Figure 6. Stated-confidence alignment by actual outcome.** Bars show mean
stated confidence across all three SFT-warmed SelfAware seeds. For
answer-content confidence, high confidence is appropriate only for correct
factual answers; wrong answers and refusals should be low.
Known refusals are low-confidence non-answers, so they are well aligned with
answer-content confidence but badly aligned with the known/unknown boundary.

The striking pattern is that confidence mostly tracks the choice to answer, not
the truth of the answer. All three regimens are highly confident on known
correct answers (0.95-0.96), but they are also highly confident on known wrong
answers: 0.94 for merged SFT, 0.90 for SFT -> DPO, and 0.87 for SFT -> KTO.
They are likewise highly confident when answering unknown rows: 0.90, 0.88,
and 0.85, respectively. Refusals show the opposite pattern. Merged SFT and
SFT -> KTO assign near-zero confidence to both correct unknown refusals and
incorrect known over-refusals. That is coherent if the field means confidence
in factual answer content, but incoherent if the desired signal is confidence
that the model is making the right epistemic decision. This distinction matters:
The current measurement captures answer-content confidence. A future confidence
reward would need to decide whether it is optimizing factual-answer
calibration, knowledge-boundary calibration, or both.

## 6. Discussion

The central finding is that abstention training has stages. In this local
Qwen3-4B SelfAware setting, SFT creates the behavior. Cold-start DPO and KTO do
not. Once SFT has created the behavior, preference optimization can move the
boundary, but it does so by trading off unknown refusal against known-question
recovery.

This matters for interpreting objective comparisons. A naive table might say
DPO and KTO have excellent over-refusal rates because they rarely refuse known
questions. But that ignores the other half of the task: they also rarely refuse
unknown questions. Conversely, SFT has the best truthfulness and refusal recall,
but its over-refusal tax is too high for deployment. The scientifically useful
question is not which objective "wins" in isolation. It is which sequence and
intensity of objectives yields an operating point where unknown refusal remains
high while known-question refusal falls.

The current answer is not yet satisfying. Sequential DPO moves too far toward
answering; sequential KTO does not move far enough away from SFT's conservative
policy. This suggests the next experiment should be a sensitivity study around
the second-stage preference objective: lower DPO beta or learning rate, fewer
effective preference steps, stronger KTO pressure against known-question
refusal, or smaller downstream adapter capacity.

## 7. Limitations

This draft reports local Qwen3-4B SelfAware-centered evidence. The signed v0.3
protocol is broader than the evidence summarized here: it includes other eval
domains, 8B confirmation, bridge replication, and robustness panels. Those
surfaces should be reported when their artifacts are reconciled.

The seed count is small. Three seeds are enough to reveal stability of the
large SFT-vs-cold-preference separation on SelfAware, but not enough to support
fine-grained claims about hyperparameter sensitivity. The t-intervals over
three seed means are descriptive.

The local recipes are resource-feasible LoRA/QLoRA adaptations, not exact
reproductions of Cheng et al.'s FSDP Llama-2 setup. Negative cold-start DPO/KTO
results should not be interpreted as contradictions of sequential DPO results
from the IDK literature.

Finally, stated-confidence results depend on the output contract. These runs
should not be substituted for plain-answer evaluations without treating the
prompt contract as part of the intervention.

## 8. Open Research Artifacts

The project repository is
https://github.com/ProfSynapse/Epistemic-Humility-Research. The paper-facing
reproducibility entrypoint is the repo-relative script
`experiment/paper/scripts/build_paper1_figures.py`, which rebuilds the generated
tables in `experiment/paper/analysis/` and charts in
`experiment/paper/figures/` from local Phase 1 evaluation artifacts.
Protocol documents are also maintained in the repository so that reported
claims can be traced back to their governing study design.

## 9. Conclusion

Small-model epistemic humility is not obtained by simply adding an abstention
label or swapping in a preference objective. SFT can teach the model to abstain,
but it overgeneralizes refusal. Cold-start DPO and KTO avoid over-refusal by
mostly not refusing at all. Sequential preference optimization is more
promising because it starts from an abstention-capable policy, but the available
local evidence shows a tradeoff rather than a clean solution: DPO over-corrects
toward answering, while KTO preserves abstention and leaves over-refusal high.

The next step is therefore not another broad claim about KTO versus DPO. It is
a controlled operating-point study of second-stage preference pressure after
SFT, with exact row-level accounting of unknown abstentions lost, known refusals
recovered, and known answers actually made correct.

## References

Amayuelas, A., Wong, K., Pan, L., Chen, W., & Wang, W. (2023). *Knowledge of
Knowledge: Exploring Known-Unknowns Uncertainty with Large Language Models*.
arXiv:2305.13712. https://arxiv.org/abs/2305.13712

Cheng, Q., Sun, T., Liu, X., Zhang, W., Yin, Z., Li, S., Li, L., He, Z., Chen,
K., & Qiu, X. (2024). *Can AI Assistants Know What They Don't Know?*
arXiv:2401.13275. https://arxiv.org/abs/2401.13275

Ethayarajh, K., Xu, W., Muennighoff, N., Jurafsky, D., & Kiela, D. (2024).
*KTO: Model Alignment as Prospect Theoretic Optimization*. arXiv:2402.01306.
https://arxiv.org/abs/2402.01306

Joshi, M., Choi, E., Weld, D. S., & Zettlemoyer, L. (2017). *TriviaQA: A Large
Scale Distantly Supervised Challenge Dataset for Reading Comprehension*.
arXiv:1705.03551. https://arxiv.org/abs/1705.03551

Lin, S., Hilton, J., & Evans, O. (2022). *Teaching Models to Express Their
Uncertainty in Words*. arXiv:2205.14334. https://arxiv.org/abs/2205.14334

Liu, S., Li, Z., Liu, X., Zhan, R., Wong, D. F., Chao, L. S., & Zhang, M.
(2024). *Can LLMs Learn Uncertainty on Their Own? Expressing Uncertainty
Effectively in A Self-Training Manner*. Proceedings of EMNLP 2024,
21635-21645. https://aclanthology.org/2024.emnlp-main.1205/

Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C.
(2023). *Direct Preference Optimization: Your Language Model is Secretly a
Reward Model*. arXiv:2305.18290. https://arxiv.org/abs/2305.18290

Tian, K., Mitchell, E., Zhou, A., Sharma, A., Rafailov, R., Yao, H., Finn, C.,
& Manning, C. D. (2023). *Just Ask for Calibration: Strategies for Eliciting
Calibrated Confidence Scores from Language Models Fine-Tuned with Human
Feedback*. arXiv:2305.14975. https://arxiv.org/abs/2305.14975

Yin, Z., Sun, Q., Guo, Q., Wu, J., Qiu, X., & Huang, X. (2023). *Do Large
Language Models Know What They Don't Know?* arXiv:2305.18153.
https://arxiv.org/abs/2305.18153
