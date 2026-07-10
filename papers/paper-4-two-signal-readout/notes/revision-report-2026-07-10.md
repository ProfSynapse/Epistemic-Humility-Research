# Paper 4 revision report, 2026-07-10

Executing agent report for the PI-approved review memo
`docs/review/paper4-two-signal-readout-review-2026-07-10.md`, applied to
`papers/paper-4-two-signal-readout/manuscript.md` on branch
`paper/two-signal-revision`. One commit per memo item, in the memo's approved
order: 1, 5b, 2, 3, 4, 5, 6, 7.

## Commit map

| Item | Commit | Scope |
|---|---|---|
| 1. Veto construct validity (AM/AP) | `bc7a814d` | New §4.4, renumber 4.4–4.9 → 4.5–4.10, requalify abstract/5/6/8/limitations |
| 5b. J-space localization + steering requalification | `43e990d1` | New §4.9 (renumber → 4.10/4.11), §2 + §6 requalified, Appendix A row |
| 2. Related-work rebuild | `310a9f0e` | §2 rebuilt, Lin polarity fixed, Kadavath recategorized, References rebuilt |
| 3. AI-workflow methods subsection | `48092d2b` | New subsection at end of §3, all bracket slots filled |
| 4. Provenance hygiene | `28e55987` | Header seed fix, §3 gates rewrite, fusion sourcing, Appendix A rows |
| 5. Framing pass | `266a64bb` | Two axes / three readouts / two robustness classes; veto = contribution 3 |
| 6. Voice pass | `4d2bb7a9` | Memo's three rewrites, intro thought experiment + falsifier, conclusion kill paragraph |
| 7. Token-logprob limitation (fallback) | `4085fbfd` | Limitation 8 with SWAP marker, Zenn-Geiping reference |

## Per-item detail

### Item 1: veto construct-validity integration (LARGE)

New §4.4 "What the veto is made of: two nuisances and a content core."
Sources read in full before writing (READ BEFORE CITE):

- `experiments/residual-catch-veto-coverage/AMENDMENT.md` (AM): registered
  gates passed, but the pre-recorded audit found the answer-length confound;
  the coverage claim was NOT established. Reported straight as a
  gates-passed-but-confounded outcome.
- `experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md` (AP): all
  gates passed; answerability carry identified as the second nuisance;
  length-and-answerability-controlled content core **0.737**, bootstrap CI
  **[0.650, 0.815]**; margin over both nuisances **+0.244**, CI
  **[0.120, 0.367]**; 65 matched pairs, single seed.

Requalified surfaces: abstract co-headline (raw ~0.98 veto now presented as
the pre-control number; honest content signal ~0.74), pipeline stage 2 (§5),
discussion (§6), conclusion (§8), limitations 4 and 5. All internal
cross-references to renumbered sections updated (verified by grep sweep for
stale `§4.x` targets).

### Item 5b: J-space localization + steering requalification

New §4.9 "Where the signals live: a workspace reading (descriptive)",
absorbing the old Figure 7 depth-profile passage. Sources:

- `experiments/j-space-localization-qwen3-4b/AMENDMENT.md`: J-lens validated
  against the logit lens (cosine **0.9811**, top-10 overlap **0.82**,
  n=1000); workspace-like band **hs23–29**, peak **hs26**; caution directions
  verbalize as self/empty/impossible/error tokens, u_d as answer/reply
  tokens. Exploratory lab diagnostic, no gates.
- `experiments/doubt-gated-caution-tighten/AMENDMENT.md`: G1 **73.5%**
  held-out confabulation conversion, G2 known-correct cost **3.1%**.
- `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md`:
  registered FULL PASS, hs29 **92.8%** vs hs34 **73.8%** (+19.0pp), McNemar
  discordants 42:0, p=4.5e-13, cost delta +1.43pp.

The memo's three honesty fences are all in the subsection text: (i) the
J-lens characterized the actuation line's directions, not this paper's
gate/dial probes, so the claim is band overlap only; (ii) bf16 sibling of
the bnb-4bit base; (iii) exploratory, descriptive, no gates. No mechanism
claim on post-beats-pre (commitment-point missed its gates, per the memo).
§2's "strictly the reading half" boundary retained; §6 "Why not just steer?"
requalified per memo (d): ungated steering could not install missing
caution; a doubt-gated write can, on one model, exploratory, and that
reconciliation is Paper 5's. External anchor Gurnee et al. (2026) added.
Appendix A row for
`experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/`.

### Item 2: related-work rebuild

- Lin et al. (2205.14334) polarity FIXED: now cited as the trained-verbalized-
  calibration precedent (the library note confirms CalibratedMath fine-tuning
  produced calibrated verbal confidence on GPT-3); the miscalibration finding
  is carried by Xiong (2306.13063), flatness by Shrivastava (2311.08877),
  RLHF nuance by Tian (2305.14975).
- Kadavath et al. (2207.05221) recategorized from activation-probe to
  prompted self-evaluation (P(IK)/P(True) are model-emitted, not probed).
- Added clusters per the memo census: gate precedent (Slobodkin 2310.11877,
  Ferrando 2411.14257), post-answer anchors (Kossen 2406.15927,
  Azaria-Mitchell 2304.13734), probing cluster (ITI 2306.03341, hyperplane
  2407.08582) with the Cheang counter-result (2510.09033, probes read recall
  not truth, AUROC 0.46–0.69 on associated hallucinations) engaged first as
  the memo directs, abstention cluster (SelectiveNet 1901.09192, R-Tuning
  2311.09677, Cheng 2401.13275, Yang 2312.07000, AbstainQA 2402.00367,
  AbstentionBench 2506.09038), pretraining anchors in §4.11 (GPT-4 report
  2303.08774, Zhu 2311.13240, He 2310.11732, Xiao 2505.01997, Ferrando),
  fusion anchors in §4.5 (Taparia 2603.24967 keep-separate vs Shrivastava
  mixing counter-anchor), decode sensitivity in §4.10 (Kuhn 2302.09664,
  SelfCheckGPT 2303.08896, Orgad 2410.02707, Taparia), ranking-vs-calibration
  in §4.2 (Guo 1706.04599, APRICOT 2403.05973), deployment cautions in §5
  (Cundy-Gleave 2505.13787, Kossen cost argument, production-gate gap).
- References rebuilt alphabetically.

### Item 3: AI-workflow methods subsection

"How this research was conducted with AI" added at the end of §3, adapted
from `papers/common/methods-ai-workflow.md`. Slot fills, all from this
paper's own record: the orchestrator's U veto band miss (predicted
0.65–0.85, actual 0.980), the AM/AP dual predictions that hit gates while
missing both confounds, SR's pre-named flip risks (both flagged cells moved
upward), the AM/AP red-team arc as the adversarial-review instance, Appendix
A as the artifact trail, and the disclosure that cells signed before
2026-07-03 carry only the orchestrator's registered prediction. No template
bracket language remains (grep-verified no `[cite` / `[Cite` in the
manuscript).

### Item 4: provenance hygiene

- Header seed note corrected: greedy deep-dive seed **20260630**; SR seeds
  **20260701–20260703** (not "seed 1" as shorthand).
- §3 gates paragraph rewritten (this is also memo rewrite 3): per-cell gate
  structure (Y's 0.90 bar and distinct falsifier; SR gating dial+veto only,
  with locked seed-stability definitions), and the program's one registered
  gate miss on the page: S's ECE **0.151** against a **<0.15** gate, missed
  by 0.001 (`experiments/correctness-confidence-probe/AMENDMENT.md`).
- Fusion Δ **−0.014** sourced to the Stage 1/1.5 CPU diagnostics (PR #128)
  via `experiments/unified-two-signal-dial-veto/AMENDMENT.md` §1.1; deployed
  checkpoint named; abstract/contribution-1 "degrades both" trimmed to the
  correctness-ranking claim the record supports.
- Appendix A rows added: SR artifacts, AM, AP, diag-item9 timeline.
- SR seed-stability definitions restated at Table 2 so Ministral's 2/3 YES
  reads correctly (`experiments/sampled-decode-seed-robustness/AMENDMENT.md`).
- Internal citations: PR #205 warning-policy operating points (§5),
  `selfaware-latent-knowledge-controls` as counterweight to the TF-IDF bound
  (§4.11), `aux-head-trainable-readout` for the calibration-map limitation
  (cold-transfer AUROC 0.983, ECE 0.023), `natural-answer-generalization`
  named as the signed-but-shelved instrument in limitation 6.

### Item 5: framing pass

Definitional sentence in the abstract and as §1's vocabulary spine: two axes
(answerability, correctness) yield three readouts (gate, dial, veto); gate
and dial are one robustness class, the veto is another. Veto lifted to its
own numbered contribution (now three contributions), matching §4.7's
"central finding" language. "Two signals" swept to "two axes" at the six
bare mentions; the pretrain section's "three-signal readout" now reads
"three-readout panel". Title unchanged per memo option 3 (the scorer at
`experiments/common/readouts/amendment_x_cross_model_score.py` says two
axes; no subtitle added, left to the PI).

### Item 6: voice pass

- Memo rewrite 1: abstract finding-3 broken out of the mega-sentence.
- Memo rewrite 2: §4.2 exploratory-diagnostic wall opens with its question;
  inline provenance moved to Appendix A; added the honesty clause that the
  tracked direction is the answerability one, so extending the rotation
  story to the dial's cold transfer is inference.
- Memo rewrite 3 was delivered in item 4 (§3 gates paragraph).
- Added: intro second-person thought experiment; intro registered-falsifier
  paragraph; U veto prediction band on the page in §4.3 (0.65–0.85 predicted,
  0.980 actual, with §4.4 explaining part of the overshoot); SR's pre-named
  live-falsifier note on the page in §4.10; conclusion
  what-could-still-kill-it paragraph.
- "Critically," opener removed (§4.2); "Honestly," was already removed in
  the item 5 sweep.
- Final sweep: 0 em dashes, 0 "load-bearing", 0 banned hedge-stack/LLM-ese
  vocabulary.

### Item 7: token-logprob baseline (fallback phrasing only)

Limitation 8 added, carrying the marker
`<!-- SWAP: pending dial token-logprob baseline analysis -->` on its own
line so the lead can splice in the parallel agent's computed analysis. The
text states the gap (no token-logprob baseline for the dial; margin over
sequence probability unquantified) and fences the dial's claims to
cross-model geometry, post-answer advantage, and veto behavior. No numbers
invented; the only numbers referenced (text baseline 0.75–0.78) already
appear in §4.11 from Amendment Y. Zenn and Geiping (2026) added to
References.

## Number provenance ledger

Every number written or requalified in this revision, and the governed doc
it was read from (all docs opened and read this revision, not cited from
memory):

| Number(s) | Where in paper | Source doc |
|---|---|---|
| Content core 0.737 CI [0.650, 0.815]; margin +0.244 CI [0.120, 0.367]; 65 pairs | §4.4, abstract, limitations 4–5 | `experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md` |
| AM gates-passed, length confound, coverage not established | §4.4 | `experiments/residual-catch-veto-coverage/AMENDMENT.md` |
| Raw veto 0.980 (trained), 0.754 untrained; U band prediction 0.65–0.85 | §4.3, §3 methods-AI | `experiments/unified-two-signal-dial-veto/AMENDMENT.md` |
| Fusion Δ −0.014 (Stage 1/1.5, PR #128) | §4.5 | `experiments/unified-two-signal-dial-veto/AMENDMENT.md` §1.1 |
| Dial 0.834; gate 0.997; post-beats-pre +0.065; ECE 0.151 vs <0.15 (miss by 0.001) | §3, §4.1–4.3 | `experiments/correctness-confidence-probe/AMENDMENT.md` |
| J-lens cosine 0.9811, top-10 overlap 0.82, band hs23–29 peak hs26 | §4.9 | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md` |
| Doubt-gated tighten 73.5% (G1), 3.1% cost (G2) | §6 | `experiments/doubt-gated-caution-tighten/AMENDMENT.md` |
| Rep2 hs29 92.8% vs hs34 73.8%, +19.0pp, 42:0, p=4.5e-13, +1.43pp cost | §6 (one sentence) | `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md` |
| SR seeds 20260701–03; both flagged cells flipped upward; seed-stability definitions | header, §4.10, Table 2 | `experiments/sampled-decode-seed-robustness/AMENDMENT.md` |
| TF-IDF gate 0.964 ± 0.016, dial 0.75–0.78; era-flat 0.991–0.998; within-SelfAware ~0.59 → 0.71–0.82; Y gate bar 0.90 | §4.11, §3, limitation 2 | `experiments/pretrain-only-base-readout/AMENDMENT.md` (Y) |
| Render sensitivity 0.666 vs 0.867 (Qwen3.5-Base k-shot vs chat) | limitation 2 | `experiments/pretrain-only-base-readout/AMENDMENT.md` |
| Aux head cold-transfer AUROC 0.983, ECE 0.023 | limitation 3 | `experiments/aux-head-trainable-readout/AMENDMENT.md` |
| Cross-family veto = same dial probe cold (framing basis) | §1, §4.7 | `experiments/common/readouts/amendment_x_cross_model_score.py` + `experiments/cross-family-confirmatory/AMENDMENT.md` (Z) |

## Citation verification ledger

All added citations verified by opening the library note (not the memo's
one-line description), under `library/notes/`:

| Citation | arXiv / source | Library note | Status |
|---|---|---|---|
| Lin et al. 2022 | 2205.14334 | `2205.14334--teaching-models-uncertainty-in-words.md` | verified; polarity fix confirmed by note |
| Kadavath et al. 2022 | 2207.05221 | `2207.05221--lms-mostly-know-what-they-know.md` | verified; recategorization confirmed |
| Azaria and Mitchell 2023 | 2304.13734 | `2304.13734--internal-state-knows-lying.md` | verified |
| Li et al. 2023 (ITI) | 2306.03341 | `2306.03341--inference-time-intervention.md` | verified |
| Universal truthfulness hyperplane | 2407.08582 | `2407.08582--generalizable-truth-probes.md` | verified |
| Cheang et al. 2025 | 2510.09033 | `2510.09033--probes-read-recall-not-truth.md` | verified |
| Slobodkin et al. 2023 | 2310.11877 | `2310.11877--curious-case-hallucinatory-un-answerability-finding-truths.md` | verified |
| Ferrando et al. 2024 | 2411.14257 | `2411.14257--do-i-know-this-entity-knowledge-awareness.md` | verified |
| Kossen et al. 2024 | 2406.15927 | `2406.15927--semantic-entropy-probes.md` | verified (also the §5 cost argument) |
| SelectiveNet | 1901.09192 | `1901.09192--selectivenet-deep-neural-network-integrated-reject-option.md` | verified |
| R-Tuning | 2311.09677 | `2311.09677--r-tuning-say-i-dont-know.md` | verified |
| Cheng et al. 2024 | 2401.13275 | `2401.13275--can-ai-assistants-know-what-they-dont-know.md` | verified |
| Yang et al. 2023 | 2312.07000 | `2312.07000--alignment-for-honesty.md` | verified |
| Feng et al. 2024 (AbstainQA) | 2402.00367 | `2402.00367--dont-hallucinate-abstain.md` | verified |
| AbstentionBench | 2506.09038 | `2506.09038--abstentionbench.md` | verified |
| GPT-4 report | 2303.08774 | `2303.08774--gpt4-technical-report.md` | verified |
| Zhu et al. 2023 | 2311.13240 | `2311.13240--calibration-of-llms-and-alignment.md` | verified |
| He et al. 2023 | 2310.11732 | `2310.11732--calibration-aligned-multiple-choice.md` | verified |
| Xiao et al. 2025 | 2505.01997 | `2505.01997--restoring-calibration-aligned-llms.md` | verified |
| Taparia et al. 2026 | 2603.24967 | `2603.24967--uncertainty-source-decomposition.md` | verified |
| Shrivastava et al. 2023 | 2311.08877 | `2311.08877--llamas-know-what-gpts-dont-show.md` | verified |
| Kuhn et al. 2023 | 2302.09664 | `2302.09664--semantic-uncertainty-kuhn.md` | verified |
| Orgad et al. 2024 | 2410.02707 | `2410.02707--llms-know-more-than-they-show.md` | verified |
| Guo et al. 2017 | 1706.04599 | `1706.04599--on-calibration-of-modern-neural-networks.md` | verified |
| APRICOT | 2403.05973 | `2403.05973--calibrating-large-language-models-using-their-generations.md` | verified |
| Cundy and Gleave 2025 | 2505.13787 | `2505.13787--lie-detectors-honesty-or-evasion.md` | verified |
| Tian et al. 2023 | 2305.14975 | `2305.14975--just-ask-for-calibration.md` | verified |
| Xiong et al. 2023 | 2306.13063 | `2306.13063--can-llms-express-uncertainty.md` | verified |
| Gurnee et al. 2026 | Transformer Circuits | `tc-2026-workspace--verbalizable-representations-global-workspace.md` | verified |
| Zenn and Geiping 2026 | 2606.27359 | `2606.27359--when-likely-answers-right-sequence-probability-correctness.md` | verified |
| **Manakul et al. 2023 (SelfCheckGPT)** | **2303.08896** | **none** | **OUT-OF-LIBRARY addition, from model knowledge, per task authorization. Lead to verify metadata before merge.** |

## Memo vs governed-doc discrepancies

None found. Every memo number I relied on matched the amendment doc it
points at when read directly. The memo's five abstract-number check ("no
invalidating error") also held under my independent re-read.

## Deliberate omissions and judgment calls

1. The six J-space steering/intervention cells stay OUT per memo 5b(b); only
   the read-only localization diagnostic came in. Paper 5's spine is
   untouched; §6 carries exactly one requalifying sentence with the
   doubt-gated numbers, fenced as exploratory Tier-2 on one model.
2. No standalone mechanism section (memo 5b(c) last sentence); no mechanism
   claim on why post-beats-pre (commitment-point missed its gates).
3. Title unchanged; the optional subtitle was left as a PI decision.
4. The veto-warning-policy report
   (`experiment/phase1/probe/analysis/veto_warning_policy_20260704/report.md`)
   is gitignored and untracked; I used it only as background for §5's
   operating-point sentence and cited PR #205 in prose rather than treating
   the report as a committed artifact. Nothing gitignored was committed.
5. Item 7 delivered as the explicit-limitation fallback only, with the SWAP
   marker; no numbers computed or invented, per instruction.
6. rep1's resolved Outcome lives on unmerged PR #263 per the memo; I did not
   cite rep1 in the paper, so nothing depends on that unmerged branch.

## Verification sweeps run

- 0 em dashes, 0 "load-bearing", 0 banned vocabulary (final sweep after
  items 6 and 7).
- No stale section cross-references after the two renumberings.
- No template `[bracket]` slots left from the methods-ai-workflow adaptation.

---

## Addendum: synthesis pass, 2026-07-10 (branch `paper/two-signal-synthesis-pass`)

PI directive executed after the main revision merged (dcfa6634): the paper
carries the synthesis, the repository carries the journey, per the new
binding VOICE.md section "Synthesis, not journey". Two commits on the
manuscript, one on this report. READ BEFORE CITE re-run this pass: AP's
Outcome block (controlled core 0.737 CI [0.650, 0.815], margin +0.244 CI
[0.120, 0.367], 65 pairs, length-only 0.492/0.493, carry ~0.99, "must NOT
be cited" verdict wording) and AM's Outcome block (length-only 0.943,
medians 94 vs 24, honest core ~0.77 length-matched) were both re-read
from the amendment docs before editing.

### Commit 1: the 0.980 sweep

The confounded deployed-checkpoint veto number (0.980) and every framing
built on it (0.754 -> 0.980, +0.226) removed from: abstract veto sentence,
abstract finding 1, section 3 AI-workflow (U band miss now stated without
the landed value), 4.3 headline, 4.4 blend sentence, 4.6 sharpening, 4.11
targeted-vs-generic contrast, section 5 "~0.98 discrimination" caution,
section 6 "what training is for", conclusion, and the Figure 5 caption.
Replacements per directive: the honest characterization (content core
0.737 with CIs, carried answerability framed as operationally useful),
the raw-base 0.754 retained only where the training-free claim needs it
(abstract finding 1, 4.4 scope sentence, 4.6, Figure 5 panel A), and the
sharpening claim now carried by the confabulation dial-mean shift 0.271
-> 0.018. The U registered prediction reduced to a compact fact with a
new true statement: the controlled content core sits inside the
registered 0.65-0.85 band. Figure 5 rebuilt from its deterministic
generator (panel A: raw-base veto vs pass bar; panel B: dial-mean shift;
suptitle em dash fixed); all other figures byte-identical.

### Commit 2: de-narration

4.4 converted from chronicle to decomposition statement; the retired
intermediate estimates (0.917 CI [0.854, 0.963]; 0.862/+0.370) now live
only in the amendment docs, pointed to once. Process narration survives
solely in the section 3 AI-workflow subsection, which after the 4.4
rewrite is the unique home of the dual-prediction/confound arc (no
duplication, so nothing trimmed there per the directive's exception
clause). Section 6 and section 2 no longer narrate the program's revised
reading of the steering asymmetry; they state the reconciled fact.
Smaller conversions: 4.6 "at the time these numbers were produced",
limitation 2 "original scoping worry", limitation 5 "now exists".

### Judgment calls for lead review

1. Figure 5 panel A kept as a single raw-base bar against the 0.65 pass
   bar (the existence claim is not superseded); the trained-side AUROC
   bar is what was removed. Alternative was dropping panel A entirely.
2. The within-SelfAware 0.93 control stays in 4.3 and limitation 5: it
   is not superseded (it bounds dataset shift, and 4.4 discloses it does
   not control answerability carry).
3. 4.3 now attributes the honest characterization (0.737 core + carry)
   to the deployed veto's read; 4.4's scope fence (raw base, different
   prompt surface, single seed, never pooled) is retained and is the
   binding qualifier.
4. The section 5 operating-point caution now says "expect the ~0.74
   content core, not the headline blend" in place of "do not expect
   ~0.98 discrimination".
5. Nothing outside papers/paper-4-two-signal-readout/ was touched. The
   SWAP-marked limitation 8 block is untouched and still awaits the
   token-logprob splice.
