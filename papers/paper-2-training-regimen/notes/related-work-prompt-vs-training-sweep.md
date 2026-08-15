# Related-work sweep: prompt-vs-training / compliance-vs-internalization (2026-08-15)

Research memo feeding the paper-2 reframe's related-work section. Two sweeps
(internal library + external web), lead-verified: every claim marked
[verified] was checked by the lead against the library note file or the arXiv
abstract/HTML directly. Items marked [verify-before-cite] were reported from
search snippets only and MUST be read before any claim sentence cites them.

## Novelty verdict

No prior work found that runs our exact instrument: crossing {untrained base,
trained checkpoints} x {abstention-instructing prompt, structure-only prompt}
with survival-of-instruction-removal as the internalization criterion, and
using that criterion to separate SFT from preference/RL objectives. The
literature splits into four non-communicating groups:

1. **Base + prompt matches tuned** — for general assistant behavior, never
   abstention (URIAL, Hewitt).
2. **Prompt-to-weights** — context distillation, framed as an efficiency goal,
   not an attribution instrument (Askell; Wang 2606.11627 is the one paper
   with a removal/reintroduction cross, for privileged task hints).
3. **Prompted-vs-trained abstention with the instruction always on in every
   cell** (Cheng, TruthRL, Abstain-R1, TIAR, Reinforced Hesitation).
4. **Stagewise post-training effects on abstention with no prompt
   manipulation** (AbstentionBench Tulu analysis).

Our panel is the join of (1) and (3); the removal test is what (2) treats as
a goal rather than a measurement. Caveat: this is an absence-of-evidence call
from ~25 targeted queries (logged in the sweep transcript); an adversarial
pass trying to break the novelty claim is recommended before the word
"first" appears in the manuscript. Prefer "to our knowledge, no prior work
crosses..." phrasing regardless.

Nearest misses to pre-empt in review:
- **AbstentionBench (2506.09038)** has three of our four ingredients
  (base-vs-instruct appendix check; a system-prompt manipulation; stagewise
  SFT/DPO/RLVR on Tulu 3) but never crosses them factorially. [verified
  abstract; appendix details from sweep's HTML read]
- **Wang 2606.11627** has the removal/reintroduction cross ("context
  invariance") but no base arm and no objective comparison. [verified]
- **Ling 2507.16199** has the structure-vs-semantics prompt control but no
  trained-checkpoint crossing. [verified]

## The two papers the reframe must engage head-on

**Cheng et al. 2401.13275 (ICML 2024)** — closest abstention-specific prior
and our training-data lineage. Runs Idk-Prompting vs Idk-SFT/HIR/PPO/DPO/BoN
on the same chat models (Llama-2-7b-chat TriviaQA truthful: prompting 66.93 <
SFT 74.75 < DPO 77.89 < BoN 78.96). Two absences our instrument fills: no
pre-chat-tuning base checkpoint, and no eval with the Idk instruction
removed — so their 8-12pt "tuning beats prompting" margin cannot say how much
survives scaffold removal. Also our sharpest CONTRAST: their preference
methods beat SFT; our cold DPO/KTO track the base under every prompt. The
reconciliation is our own frame: they train from an instruction-tuned chat
model whose rollout distribution already contains abstention (preference
methods sharpen what exists); we train cold from base (nothing to sharpen).
[verified against library note 2401.13275, lines 96-98, and paper-1
draft-v0.md:159]

**Reinforced Hesitation 2511.11500** — the strongest published claim of
OPPOSITE polarity, and the first thing a reviewer will raise: 11 frontier
models abstain <1% on GSM8K despite penalty warnings up to lambda=100; zero
abstentions on MedQA across 11 models; "prompts cannot override training
that rewards any answer over no answer." Reconciliation is exactly our
instrument's point: their 11 models are all RLVR/RLHF-trained chat models,
so they show prior training SUPPRESSED prompt-elicitable abstention; the
base counterfactual is the control they omit, and our base+P-rc 90.89
directly exhibits what their models' pretraining priors presumably had
before RLVR trained it away. Together the two results bracket the claim:
prompts elicit only what training has not destroyed; training amplifies only
what prompts (or SFT) make available. [verified against library note
2511.11500, lines 113, 125-127; mechanism node
prompt-cannot-override-rlvr-abstention-deficit]

## Precedent for each leg of our finding

**Leg 1 — the instruction elicits near-ceiling abstention from the raw base
(base+P-rc 90.89):**
- URIAL / Lin et al. 2312.01552 (ICLR 2024): base and aligned models decode
  "nearly identically... on the majority of token positions"; base + 3
  stylistic ICL examples + system prompt "can match or even surpass" SFT and
  SFT+RLHF models. Domain-general precedent for our base arm. [verified
  abstract]
- Zhao et al. 2405.19874 (ICLR 2025): the counterweight — URIAL-style ICL
  still underperforms tuning on MT-Bench, decoding params are a confound.
  Cite to avoid over-claiming and to note we ran greedy T=0 everywhere.
  [verified by sweep; abstract-level]
- Hewitt et al. 2409.14254: "implicit instruction tuning" — response-only
  training and narrow-domain tuning both yield broad instruction following;
  the mapping pre-exists in the base and tuning reveals it. Cleanest framing
  citation for "elicitation, not creation." [verified abstract]
- R-Tuning 2311.09677, Table 5 "Pretrain-T" row: pretrained LLaMA-13B under
  their certainty template refuses 28.00% on SelfAware (our benchmark!) vs
  Vanilla 12.21 vs trained 96.61. The 2023 hint that base models respond to
  abstention scaffolding; low magnitude (weak template vs our explicit
  instruction; older family). Use to pre-empt "hasn't this been shown."
  [verified against library note lines 87-88]
- Jha 2601.20126: base-with-IDK-option control rows — 6.6% on MedMCQA,
  0.03% on open-ended MATH. Matches our base+P-struct ~0 almost exactly:
  weak affordance elicits nothing; our strong instruction elicits 90.89.
  Prompt STRENGTH determines whether there is any base signal — a point
  neither paper makes alone. [verified against library note lines 127-137]

**Leg 2 — only SFT internalizes; DPO/KTO/cold-GRPO track the base:**
- AbstentionBench 2506.09038 Tulu 3 stagewise: abstention improves through
  SFT and DPO, then "a surprising degradation in abstention after RLVR."
  Independent evidence that objectives behave differently on this axis.
  [verified abstract; stagewise detail from sweep HTML read]
- Raina et al. 2512.11838 ("D-STEER") [VERIFIED 2026-08-15, unrefereed
  preprint — weakest source in the set]: headline quote confirmed verbatim
  ("DPO does not teach models to believe in aligned values—it merely
  teaches them to behave as if they do"). Precision fixes: the cosine
  0.92-0.96 single-direction result is FINAL-LAYER hidden states only; the
  layers-22-30 range belongs only to the separate spectral rank~1 claim
  (sigma2/sigma1 < 0.1); subtraction "nearly restores" base behavior
  (qualitative, figure-level — never cite as clean recovery). No
  prompt-removal test, no SFT head-to-head; behavioral evidence exists
  (G-Eval, Perspective, TruthfulQA on one LLaMA-2-7B) but thin. Cite as
  concurrent mechanistic support at most.
- Chen et al. 2502.04602 (NAACL 2025): safety/detox alignment largely
  reproducible by re-styling the final projection head; reasoning is not.
  Complementary cut (depth-of-parameter-change vs our prompt-dependence).
  [sweep HTML read; spot-verify numbers before citing specifics]
- Qi et al. 2406.05946 (ICLR 2025): shallow safety alignment — trained
  change concentrated in first few output tokens. Safety-domain precedent
  for "the trained delta is thinner than it looks." [snippet-verified;
  canonical]
- Kung & Peng 2305.11383 (ACL 2023, refereed): training on
  semantics-stripped task definitions or delusive examples matches training
  on real instructions; gains "come from picking up superficial patterns,
  such as learning the output format and guessing." Training-side cousin of
  our structure-only prompt. [VERIFIED 2026-08-15; keep the LOW-RESOURCE
  qualifier — random baseline 42.6 vs IT 43 exact-match is scoped to the
  low-resource setting]

**Leg 3 — cold GRPO cannot bootstrap absent behavior (scaffolding
necessity):**
- Jha 2601.20126: "RL-only training fails to induce abstention on open-ended
  QA because the base model almost never emits IDK responses, providing
  insufficient exploration" — our mechanism, published. KG node
  rl-insufficient-exploration-blocks-open-ended-abstention. [verified]
- Yue et al. 2504.13837 (NeurIPS 2025 Oral — strongest external source in
  the set): exact quotable abstract wording: "While RLVR-trained models
  outperform their base models at small k (e.g., k = 1), the base models
  achieve a higher pass@k score when k is large. Coverage and perplexity
  analyses show that the observed reasoning abilities originate from and
  are bounded by the base model." Note: base models ACHIEVE HIGHER at large
  k (stronger than "matches"); "sampling efficiency" is our gloss, ground
  it in "originate from and are bounded by." Contrast case worth keeping:
  distillation CAN introduce new patterns. [VERIFIED 2026-08-15]
- GRPO gradient starvation 2605.07689 (preprint): degenerate group
  (all-correct or all-wrong) gives advantage exactly zero for every
  response; observed degeneracy 69.25% (54.75 all-fail / 14.50 all-pass)
  — but that number is ONE seed-42 DrGRPO run, Qwen3.5-9B on GSM8K, G=4;
  never cite as a general GRPO property. Prop. 2: D_real >= D_iid.
  (+ ExGRPO 2510.02245, EEPO 2510.05837 as the broader exploration-
  stagnation thread, still snippet-level.) [VERIFIED 2026-08-15]
- Wang 2606.11627: names "context invariance" and finds context-induced
  degradation (distilled student gets WORSE when the prompt returns).
  ACTION: check our 2x2 for this cell — SFT/warmed-GRPO checkpoints under
  P-rc vs P-struct; if an internalized checkpoint drops when the
  instruction is re-added, we have a named citation for it. [verified
  abstract]

**Leg 4 — structure-only prompt as instrument:**
- Ling et al. 2507.16199 "Abstention Inflation": abstention driven by
  structural prompt features (an "Unknown" option; even a random word in
  its slot) rather than genuine uncertainty; bias "emerges through
  instruction tuning." Independent validation that scaffold FORM does work,
  motivating our byte-controlled P-struct design. Under-cited; rank high.
  [verified abstract]

**Instruction-always-on confound in the RLVR wave (our methodological
point):**
- TruthRL 2509.25760: abstention instruction embedded in ALL eval prompts
  including the prompting baseline; no instruction-free eval of any trained
  model. [sweep HTML read of eval prompts; consistent with library note]
- Abstain-R1 2604.17073: prompting/ICL baselines exist (different or larger
  models); no removal eval. [library note + sweep concur]
- TIAR 2605.25850: all-trained baselines, no prompted-only control, no
  removal eval; NOT in our library — must be ingested before any claim
  about it goes in the paper. [sweep HTML read]
- Paper 1's own Gap 3 (manuscript.md:392-398, 444-451): none of the cluster
  is benchmarked against SFT/preference families on shared data; every
  result "measured against its own prompting or cold-start baseline." Paper
  2 closes a gap paper 1 named in print. [verified]

## Ranked citation set for the rewrite

Engage directly (full paragraphs): Cheng 2401.13275; AbstentionBench
2506.09038; Reinforced Hesitation 2511.11500; Jha 2601.20126.
Framing citations: URIAL 2312.01552; Hewitt 2409.14254; Yue 2504.13837;
Askell 2112.00861 (context distillation as the prompt-to-weights mirror of
our SFT result); Ling 2507.16199; Wang 2606.11627; R-Tuning Pretrain-T row.
Counterweights/robustness: Zhao 2405.19874; Qi 2406.05946; Chen 2502.04602.
Verify-before-cite pass COMPLETE (2026-08-15, all seven fetched from
arXiv abs/HTML, verdicts folded in above where the paper appears). The
three not covered above:
- 2604.13006 "One Token Away from Collapse" (preprint): CONFIRMED — base
  models small/noisy under lexical prompt perturbation (Qwen base +7.1%)
  while ALL instruct models collapse; table range -17.4 (Mistral-7B-Inst)
  to -48.1% (Qwen-2.5-7B-Inst). CITATION TRAP: the abstract says "14-48%"
  while the table says 17.4-48.1 — quote one consistently, label it
  per-model/table-level. Cleanest data point: same-family Qwen swing +7.1
  base vs -48.1 instruct.
- SEAT 2506.14387 (preprint): MISUSE WARNING — the "erodes aligned
  epistemic abstention" quote is real, but their "base models" are
  Llama3-8B-INSTRUCT and Qwen2.5-7B-INSTRUCT, and there is NO quantitative
  pre-finetuning abstention baseline (qualitative case study + a
  representation figure only). SEAT therefore CANNOT support "base models
  already abstain" — it supports only "fine-tuning destroys abstention
  that alignment training installed" (Full-FT drives IDK metrics to 0.000
  on PISTOL/TOFU/RWD). Do not use it for the base-model leg.
- 2601.13244 (preprint): CONFIRMED — zero-shot CoT GSM8K, base beats
  instruct with drops up to 32.67% (that figure is Llama3-70B, the MAX not
  typical); instruct recovers only with few-shot exemplars ("reliance on
  specific prompting patterns"). Bonus axis: base also wins on
  domain-shifted MedCalc.
Venue status: only Kung & Peng (ACL 2023) and Yue (NeurIPS 2025 Oral) are
refereed; the other five are unrefereed preprints — weight accordingly in
the manuscript.

## Action items

1. Library ingest gap: LIMA 2305.11206, URIAL 2312.01552, Askell
   2112.00861, Qi 2406.05946, Ling 2507.16199, AbstentionBench 2506.09038,
   Hewitt 2409.14254, Wang 2606.11627 are ABSENT from library/; TIAR
   2605.25850 is bibliography-only. kg-ingest pass needed before the
   related-work section cites them (READ BEFORE YOU CITE applies to
   external papers via ingest notes).
2. DONE (2026-08-15, results-analyst check, lead spot-verified vs
   sft_seed1__selfaware/metrics.json): NO Wang-style context-induced
   degradation in our data. For every internalized checkpoint (cold SFT
   s1-3, clean-SFT merged, SFT->GRPO v2 s1), re-adding an instructed prompt
   RAISES refusal recall (69.6->83.9, 76.9->87.4, 79.4->92.3, 69.5->87.0,
   77.4->93.4) and truthful_pct; instruction never hurts the trained
   behavior. The one metric that worsens under instruction in all five
   internalized cells is over-refusal on knowns (47.6->64.3, 56.0->64.7,
   54.8->65.3, 49.3->57.5, 58.7->66.6) — broader refusal as collateral
   cost, not the Wang signature. So cite Wang 2606.11627 as the
   nearest-instrument analogue only; do NOT claim we observe (or refute)
   context-induced degradation — our cross-contract data (SFT instructed
   readings are plain-answer, warmed arms are P-rc; no RC reading for cold
   SFT, no plain reading for warmed arms; DPO/KTO s2-3 P-struct-only)
   supports the directional statement, and the instruction-raises-
   over-refusal pattern is itself a paper-worthy operating-point note:
   the instruction buys recall at a known-side cost even on internalized
   checkpoints.
3. Adversarial pass on the novelty claim before "first"/"novel" enters the
   manuscript; default to "to our knowledge."
4. KG links at verdict ingest: contrasts
   prompt-cannot-override-rlvr-abstention-deficit and
   preference-opt-reduces-abstention-overtax; supports/anticipated-by
   rl-insufficient-exploration-blocks-open-ended-abstention; related_to
   ternary-reward-enables-abstention-over-hallucination; lineage
   method:idk-sft, method:refusal-aware-instruction-tuning. Mint candidates:
   mechanism:instruction-elicits-latent-base-abstention,
   mechanism:sft-installs-preference-methods-modulate (names provisional;
   run kg_inventory near-synonym check first).
