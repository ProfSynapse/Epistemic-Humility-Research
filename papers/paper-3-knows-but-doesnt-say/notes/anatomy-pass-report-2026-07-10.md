# Paper 3 anatomy integration pass — report (2026-07-10)

Branch: `paper/knows-anatomy-pass` (base: origin/main 8fcaa008). Two commits:
commit 1 = anatomy integration + A3 move-out; commit 2 = self-containment +
structure sweep + this report. Spec: the direction-provenance census
(`docs/review/paper3-direction-provenance-2026-07-10.md`); every number added
was re-read from its governed doc first (READ BEFORE CITE).

## Commit 1: anatomy integration + A3 move-out

### Doubt (census A1 + base/pretrain validation)

- Added a §4 block "The doubt axis is the answerability readout, and it
  predates our training": states the identity explicitly (doubt = the
  known-vs-unknown answerability separation read as graded confidence, the
  same signal paper 4 deploys as its gate), so the trilogy does not
  double-count one signal as two.
- Base/pretrain validation on the census's proposed scope-sentence basis:
  0.997 untrained on the raw Qwen3-4B base (read from
  `experiments/base-model-training-free-mechanism/AMENDMENT.md` §7) and 0.997+
  on four pretrain-only bases, falsifier fired on 0/4 (read from
  `experiments/pretrain-only-base-readout/AMENDMENT.md`, H_B1 SUPPORTED 4/4).
  Doc form "0.997+" used rather than the census's "0.99+".

### Caution (genuine, knowledge-orthogonal, trained-checkpoint-only)

- Added a §5 block "Caution is a trained-checkpoint construct, and cannot be
  anything else" with the required caveat: no base reading exists or can exist
  because the raw base refused 0 of 1,233 (Amendment W §7). Framed as the
  finding: training does not create doubt, but it does create caution.
- The knowledge-orthogonal reading (LEACE cost 5.4 ± 0.6 of 91, post-erasure
  0.858) was already in §5 and §9; verified against
  `experiments/knowledge-subspace-erasure/AMENDMENT.md` (SURVIVES,
  user-adjudicated 2026-07-04). Unchanged.
- A5 (checkpoint heterogeneity): added one sentence to the cross-regimen block
  stating each reading is fit on its own checkpoint's activations, no common
  checkpoint carries all of them.

### Confab-propensity (census: NOT SAFE)

- Exactly one forward-pointer sentence at the end of §5, modeled on the
  census's proposed wording: checkpoint-specific to the most-trained
  checkpoint, examined in the companion actuation paper, causal conversion
  null, excluded from this paper's signals. No separation numbers anywhere.

### A3 move-out (§6)

- §6 reduced from four steering sub-results (~45 lines) to a two-paragraph
  summary that attributes the result to the companion actuation paper and
  keeps only what §6's argument needs: 0.994 → 0.030 with clean specificity,
  the doubt-orthogonalized component carrying a large share, no intervention
  installing abstention on unknowns, leverage one-way. Section number kept;
  §7–10 not renumbered. Removed detail (caution_perp 0.994 → 0.524, L26
  generation panels, coefficient sweeps, ITI numbers) now lives only in the
  companion paper.
- Dependents updated to imported-claim framing: abstract contribution (3)
  (recast as the anatomy/origin finding + companion causal import), intro
  bullet 3 (now "Causal status, imported"), intro bullets 1–2 (gained one
  origin clause each), the intro scope note (0.994 → 0.030 replaced by the
  answer-supervised → answer-masked flip as the second example), §2 activation
  steering block, §8 ("established in the companion actuation paper"; "the
  companion actuation study could not install the hard direction"), §9
  bullet 1 (0.994 → 0.030 dropped from the single-seed list), §9 steering
  bullets (rewritten as "imported steering evidence"), conclusion ("a
  companion actuation study shows").

## Commit 2: self-containment + structure

- All internal bracketed artifact pointers stripped from body prose
  (~25 instances: `c2_*.json` / `a3_h_base_probe.json` style artifact lists,
  script paths, AMENDMENT/RUNBOOK paths, session-doc checkpoints,
  `results_amendment_*` ids, the extraction hash, "(Revision 3)"). Provenance
  preserved by Appendix A: added a §3 setup row (eval harness, stated-scalar
  readout, extraction `55254a04aa1f`), an Amendment W row, extended the Y row
  to §4, and added the §5 reconstruction script, `caution_axis_transfer.json`,
  and `action_conditioning_report.py` to their rows. Methodological facts that
  had been living inside brackets (geometry cell sizes, whitening spec,
  held-out protocol) were promoted into prose, not deleted.
- Bold run-ins converted to real headings: §2 (4 blocks), §3 (4), §4 (6),
  §5 (3), §7 (8 at `###` plus the seven-interventions pseudo-list converted to
  four `####` subsections, with the arXiv citations moved from the bold labels
  into the first sentences), §8 (6). Figure/table captions keep bold labels.
- Genuine lists unbolded: abstract (1)–(4) markers, the four intro
  contribution bullets, the eight §9 limitation lead-ins.
- Lecture trims: Figure 2 and Figure 7 captions lose their "In plain terms:"
  re-explanations (Figure 2's also overstated 0.637 as "barely beats a coin
  flip", contradicting §4's own correction); each caption keeps a one-line
  closing claim.
- Banned vocab: "load-bearing" (Mechanistic reading, §7) replaced with
  "carried". Three generic body uses of "amendment" replaced with standard
  pre-registration vocabulary ("pre-registered protocol revision",
  "exploratory pre-registered cell").

## Checks

- Census vs governed docs: no discrepancies found. All five docs the census
  cites for the numbers used here were read in full or at the cited section.
- Em dashes: 0. Banned vocab: 0 hits. External citation census: 24 inline
  arXiv citations before and after, none added or removed.
- Nothing outside `papers/paper-3-knows-but-doesnt-say/` touched.

## Judgment calls flagged for the lead

1. Companion-paper link text uses paper 5's current manuscript title
   (*Readable Is Not Writable*), in §5 (confab pointer) and §6. The series
   plan records the decided new title (*Look Before You Speak*) with the
   manuscript rewrite pending; these two link texts will need updating when
   the retitle lands.
2. §9 "Steering is single-site / few-layer" bullet was kept but rewritten as
   "The imported steering evidence is single-site / few-layer", dropping the
   L35/L26 site specifics as companion-owned detail. Alternative was deleting
   the bullet outright; I kept it because it bounds a conclusion §6 still
   imports.
3. The confab-propensity pointer sits as the closing paragraph of the §5
   "Caution is a trained-checkpoint construct" subsection rather than under
   its own heading, since one sentence does not earn a heading. It is
   two-sentence in final form (definition parenthetical + pointer), the
   minimal self-contained rendering of the census's proposed single sentence.
4. The §7 intervention pseudo-list ("1–2. … 6–7.") became `####` subsections
   under "### The seven interventions"; the numbering survives in the heading
   text ("Interventions 1–2: …") because §7's prose refers back to
   "intervention 4/5" by number.
