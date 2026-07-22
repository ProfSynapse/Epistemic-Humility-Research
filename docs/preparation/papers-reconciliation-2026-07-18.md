# Papers-vs-evidence reconciliation record (2026-07-18)

Campaign record from the five-reader reconciliation (task #29). Distilled
from reader reports; every item's source of truth is the cited manuscript
line and experiments/<slug>/AMENDMENT.md Outcome. PI decision-packet
rulings are recorded in the 2026-07-18 session-note checkpoint and baked
into tasks #15/#30-#35 and docs/preparation/paper5-rewrite-spec.md.


## Paper 1 (taxonomy) - REPORT IN. Verdict: LIGHT TOUCH (~1h edit)

MUST-FIX:
1. manuscript.md:394-401 "a planned steering study tests its causal
   writability" is false: paper 5's program ran to terminal verdicts.
   Replace with one operating-point-dependent summary sentence citing
   paper 5. DEPENDENCY: word it after paper 5's rewrite lands.
2. manuscript.md:370-376 P3 falsifier: non-transferability now partially
   tested (M4-WK reversal, void-not-falsified). Add one population-bound
   sentence; P3 not overturned.

SHOULD: 3. :343-345 "epistemic signal" is at least two dissociable signals
(answerability vs correctness) - one hedge sentence. 4. :171-173 coherence
axis "unmeasured" - acknowledge paper 3 exists. 5. :380-393 agenda tense.

NICE/CLEAR: Gaps 3-4 still accurate (GRPO decision open; M5 not run). No
mentalistic vocabulary anywhere in paper 1 (confirmed full read).

## Paper 2 (training regimen) - REPORT IN. Verdict: MINIMAL (<10 lines if SHOULDs accepted; no rework)

Structurally unaffected: margin cascade + renaming table live on the
reading/actuation side; paper 2 is purely behavioral, vocabulary confirmed
clean (only "epistemic state" :71-77, rated SAFE). Nothing stale or
contradicted. All 11 terminal-cell Outcomes read.

SHOULD:
1. :711-712 Appendix A governance note under-counts confidence-channel
   family: widen "Amendments J/K/N" to include L
   (answer-subspan-masked-contrastive-sft, behavior passed/calibration to
   chance), M (quantile-balanced-probe-distilled-sft, falsifier fired), R
   (aux-head-cotraining-native-behavior, falsified). Completeness gap, not a
   factual error. Better: replace letter list with "the full
   confidence-channel amendment set".
2. :386-393 SFT-warmed confidence signature (known-label MAE vs correctness
   MAE) is paper 4's gate/dial seam, currently parallel-but-unlabeled. Add
   one clause + forward citation. Directly answers plan.md:76 open item.
3. GRPO framing decision input (plan.md:146 #3), neutral: all 7 new
   training-side cells (B/J/K/L/M/N/R) are confidence-channel extensions
   riding on GRPO; NONE adds a second seed to the core behavioral
   SFT/DPO/KTO/GRPO comparison. Effort went to "more GRPO variants for
   confidence diagnosis," not "more seeds confirming the behavioral arm."
   PI's call.

NICE:
4. :483-491 Section 5 fusion echo: paper 2's "appropriateness" target is a
   fused construct; paper 4 shows gate+dial fusion is lossy (-0.014 AUROC).
   One hedged "consistent with" sentence.
5. :514-533 "frontier did not move" - name M5 training bridge as planned
   future work (unregistered, no numbers).

Remaining paper-2 open work is the VOICE.md self-containment pass
(plan.md:76-77), unchanged.
## Paper 3 (knows-but-doesnt-say) - REPORT IN. Verdict: NAMING+HEDGING PASS (no structural rework; ~35 mechanical renames + 4-6 new sentences; zero numbers change)

ALREADY DONE (not pending): census's three standing rulings integrated by the
2026-07-10 anatomy pass (doubt=answerability identity :372-386; caution
trained-checkpoint-only scope :451-463; confab-propensity exclusion pointer
:465-471). Verified against notes/anatomy-pass-report-2026-07-10.md.

MUST-FIX:
1. Title/abstract (:2,48,52-56,60-64,71-72): "knows"/"doubt axis" mentalistic
   naming; criterion (d) tested NOT earned on a methodologically identical
   lineage (M4-WK 0.3018 void/reversal; M4c constructive null). Not a direct
   falsification (Qwen3.5-4B hs20 vs paper 3's Qwen3-4B L35 SelfAware axis)
   but the naming critique transfers by construction. Fix: one scope sentence
   ("knows" = answerability recognition, not verified self-knowledge of own
   answer correctness) + rename doubt axis -> known-unknown (answerability)
   axis per framework table :104-115. Supersedes/sharpens terminology audit's
   paper-3 section; implement the audit's rename list.
2. :300-306 + :789-813/868-878 (NEW beyond terminology audit): "monotone
   across behavior cells" + axis-as-"factual confidence P(answer correct)"
   distillation target (AUROC~0.997) is exactly the claim shape M4/M4c tested
   and returned null on (constructive search -> generic/retrieval geometry;
   refused > confab > correct ordering). Fix: one hedge sentence after :306
   and one near :868-878 (single-model/single-population reading; cite the
   program's negative portable-evidence-axis search).

SHOULD:
3. Rename sweep, 35 occurrences (audit's list agrees but missed :267, 300,
   304, 323, 395, 402, 415, 421, 832; full list in report). Keep governed
   filenames/artifact names verbatim.
4. M4/M4c arc is entirely ABSENT (zero mentions in 1139 lines); paper 3 owns
   internal-anatomy claims per plan.md:53. Add one new §9 limitations bullet
   (2-3 sentences) citing both Outcomes, framed as naming caution transferring
   by methodology, not a direct test of this paper's axis.
5. STILL-OPEN EXPERIMENTAL DEBT (no prose fix; lift to PI): plan.md:86-88
   reviewer-attack items unaddressed (competence-within-category gate control;
   multi-elicitation robustness); training-resistance panel stays seed-1-only
   (paper 2's 3-seed matrix does not cover it). Verified via bin/search: no
   terminal cell targets these.

NICE: 6. Lift framework vocab table into papers/common/ (one canonical
mapping for papers 3/4/5) + Appendix A footnote.

DEPENDENCY: batch with paper 5 rewrite (audit ranks paper 5 higher-stakes).
## Paper 4 (two-signal readout) - REPORT IN. Verdict: MAINTENANCE PASS + ONE REAL CONFOUND DECISION

Audit correction: M4-WK IS merged to main (78fd853e, registry null-result);
terminology audit's "unmerged branch" caveat is stale. Citable now.

MUST-FIX (the one genuinely new methodological finding of the campaign):
1. :245-253 + :940-944 LEGACY REFUSAL DETECTOR CONFOUND. Paper 4's core
   headline cells (S/U/W/X extract scripts) classify answered-vs-refused via
   scorers.is_stated_confidence_refusal pinned by path_compat.locked_eval_dir()
   to archive/experiment/phase1/eval/scorers.py - a legacy NARROW detector
   never benchmarked against the wide idiom-inclusive instrument that
   abstention-wide-instrument-calibration just validated (6-13pp narrow
   undercount on sibling families). Plausible unflagged confound sitting
   upstream of the veto/dial headline numbers: some "hallucination" rows may
   be undetected hedge-idiom non-answers. NOT text-only: needs a PI decision
   on running an audit (what fraction of SelfAware hallucination rows flip
   under the wide detector) vs adding a limitation sentence citing the
   calibration cell Outcome.

SHOULD:
2. :638-639 "caution and doubt directions" -> "caution and known-unknown
   directions" (citation to paper 5's construct; precision fix).
3. :902-904 "doubt-gated caution write" -> "answerability-gated
   (known-unknown-gated) caution write".
4. :185-187 "usable self-knowledge" - the one mentalistic-adjacent phrase for
   paper 4's OWN claim; one-clause scope + optionally cite M4-WK/M4c as
   in-program instances of the Cheang et al. counter-result discussed at
   :188-197.
5. LP backlog (limitation 8, :959-968, has SWAP marker) + CD backlog (dial
   cold-transfer, :390-402, "an inference, not a measurement", no marker) -
   both GPU-gated, GPU now free: ready to LAUNCH, not text edits. Add
   matching SWAP marker at :396-400.

NICE:
6. Wide-instrument family rates model mismatch note (mistral7b-v03 vs paper
   4's Ministral-3-3B) - only if new cross-program prose is added.
7. M2 + M4c confirmed NOT touching paper 4's construct (margin/susceptibility
   line, not answerability+correctness). No action.
8. Paper 4 is the most vocabulary-compliant manuscript; own construct names
   never use "doubt".

TOTAL: no numeric/verdict/headline change from any terminal cell. Light
vocab pass + one confound decision + two unblocked GPU backlog items.
## Paper 5 (Look Before You Speak) - REPORT IN. Verdict: REWRITE-FROM-SPINE (the big job)

KEY FINDING: manuscript is a PARTIAL update - absorbed placebo/mistral/census
arc as 4.8-4.10 (through 2026-07-15) but never executed the 2026-07-10
audit's 10-item positive reframe. Title, abstract, intro, 4.1-4.7, Section 5
map, Section 6 all still draft-v0 negative frame. New 07-13..07-18 cluster
(factorial, ungated-vs-gated, M4-WK, mid-band arc, cross-family, atlas) never
seen by the manuscript.

MUST-FIX (8 items, full file:line list in report):
1-5. The central mechanism sentence "the write is not selective; the gate
   supplies selectivity" recurs at :73-75, :128-130, :758-759, :798-804 and
   is FALSIFIED as a general claim by gate-contribution-factorial (permuted
   gate abstention 0.550/0.600; Gap_Sel 0.148/0.129 vs 0.20 floor both
   families); survives only at the overdrive/L34-dose-200 operating point.
   Re-derive as operating-point-dependent (framework section 5 already
   states the reconciliation). Also :336-341 unregistered n=80 diagnostic
   must be replaced with registered 60.1%-vs-3.1%.
6-7. "doubt-coupling" :722-730 + title/abstract "doubt readout" retired by
   M4-WK (name unearned; population reversal). Rename known-unknown
   readout-coupling; title tension lifted to PI.
8. :816-843 coherence/saturation ceiling absent (M4-WK: only ~13% of
   world-known confabs tippable inside coherence-valid band; scoped hs20).

SHOULD: mid-band positive arc (held-out 0.678 + 5-seed 69.5%/4.65% cost)
absent from 4.4/4.5 - net STRENGTHENS controller; cross-family resolved
not-promoted replaces "awaited promotion vehicle" :854-881; J-space scoped
to one model (atlas eff_dim prediction failed cross-family); AQ still
unsigned, relabel or drop :407-423; mentalistic rename sweep (~11 sites);
mistral third direction-specificity failure (factorial S1 ratio 2.03).

NICE: audit spine elements AL/AN/AO/rep1/rep2 still absent; margin-program
bounds citation optional; placebo subtype sentence; voice pass.

FAVORABLE: newest evidence strengthens the actual controller (mid-band
transfer held-out + seed-robust); framework section 5 is a ready-made spine.

PI-ONLY DECISIONS (from P5): title; mistral scope (bounded negative vs
Qwen-lineage contraction); cross-family framing vs hold for llama retest
(task #7); geometry/margin cells in paper 5 limits vs successor paper.

---

# LEAD SYNTHESIS (all five reports in, 2026-07-18)

Effort ranking: P5 rewrite-from-spine >> P3 naming pass > P4 maintenance +
confound decision > P1 light touch > P2 minimal.

Cross-cutting: (a) terminology block in papers/common FIRST (P3 item 6, P5
item 13, P4 items 2-3 all draw on it); (b) paper 5 rewrite blocks paper 1
MUST-FIX 1 wording and batches with paper 3's pass; (c) three GPU items now
unblocked and feed the papers: P4 detector flip-rate audit (decision),
LP/CD backlog, llama gated retest #7 (feeds P5 cross-family framing).

Decision packet for PI:
1. Paper 5 title (doubt vs known-unknown).
2. Mistral scope in paper 5.
3. Cross-family framing now vs after llama atlas-sited retest (#7).
4. Margin/geometry cells: paper 5 limits vs successor paper.
5. GRPO framing (plan.md:146 #3) - P2's neutral summary: 7 new cells all
   confidence-channel extensions, none adds behavioral seeds.
6. Paper 4 detector confound: fund flip-rate audit vs disclose-only.
7. Paper 3 experimental debt: fund competence-gate control /
   multi-elicitation / multi-seed training-resistance, or disclose.
8. Launch LP + CD backlog on free GPU?
