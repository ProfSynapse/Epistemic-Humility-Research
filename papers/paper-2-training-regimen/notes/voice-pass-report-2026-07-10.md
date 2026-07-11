# Paper 2 voice/self-containment pass — report (2026-07-10)

Branch: `paper/training-regimen-voice-pass` (base: origin/main c2e977b2). Two
commits: commit 1 = self-containment + stale cross-reference fixes; commit 2 =
structure/voice sweep + this report. Editorial pass only: no number, claim, or
scope sentence changed; conflicts found are FLAGGED below, not fixed.

## Commit 1: self-containment + cross-references

- §3.3: the recipe/run-record repo paths
  (`archive/experiment/phase1/recipes/`, `.../run_records/`) moved out of body
  prose into a new Appendix A row; body now says "committed in the repository
  (Appendix A)".
- §4.3: "(visible in Figure 6; per-arm numbers in Appendix A's artifacts)"
  reduced to "(Figure 6)"; the stack numbers' provenance already lives in the
  Appendix A stacking row.
- Stale companion cross-references fixed (editorial, flagged as judgment call
  1): §6 and §8 cited the readout paper under its old title (*The Confidence
  Is Already There*) while this paper's own References entry carries the
  current title (*It's What's on the Inside That Counts*); both in-text link
  texts and the Appendix A governance note now match the References. Their
  section pointer "§4.9" was also stale: in paper 4's current numbering §4.9
  is the workspace reading, and the pretrain-only contrast the sentences cite
  lives at §4.11 ("The signal predates post-training"). Both pointers now say
  §4.11. Verified against paper 4's current heading tree and §4.11 table
  (gates 0.9975–0.9977, i.e. "0.997+", four pre-instruction bases), so the
  cited content matches the cited section.
- Frontmatter provenance blocks untouched (exempt). Appendix B untouched
  (appendix pointers allowed).

## Commit 2: structure and voice

- Real headings: §2's three bold run-ins ("The families", "The reanalysis
  lessons", "The gaps this experiment closes") and §6's three ("The regimen,
  not the objective", "The frontier did not move", "Deployment reading")
  became `###` headings; §3.3's two bold-subject arm blocks became `####`
  subsections (SFT, DPO, KTO / GRPO) with the prose openings adjusted to
  stand alone.
- Genuine lists unbolded: §1's three "First/Second/Third" evidence-strand
  bold sentences (now plain topic sentences), §4.2's DPO/KTO bullets, and
  §3.4's four metric-definition labels (bold to italic, matching paper 3's
  setup-list style).
- Never-explain sweep: all six figure captions carried an "In plain terms:"
  re-explanation; each is compressed to a one-clause claim (same treatment
  merged for paper 3). No pre-registration lectures found in body text.
- Mechanics: em dashes 0 (before and after), "load-bearing" 0, banned
  hedge-stacks and LLM-ese 0. No edits needed on this front.

## Constraint compliance

- GRPO framing (extension vs registered arm): left verbatim everywhere. It
  lives at §3.1 evidence-layer 3 ("GRPO (single seed, exploratory)"), the
  §4.3 opener ("All GRPO comparisons below are single-seed under the
  response-confidence contract"), §7 ("the GRPO layer, its stacks... are
  single-seed and exploratory"), and the Appendix A governance notes
  ("Amendments A/B are signed prospective extensions; Amendments D/E/F/J are
  exploratory single-seed evidence cells").
- Headline vs sensitivity panel: no blurring found. The only headline-matrix
  numbers in the body are the §4.1 three-seed cold-start block, mapped to
  PROTOCOL v0.3 in Appendix A; no LR/beta sensitivity-panel number appears
  anywhere in the paper.
- READ BEFORE CITE: no number was reworded in a way that required re-tracing;
  the two cross-reference fixes were verified against paper 4's current
  manuscript directly.

## Checks

- Em dashes: 0. Banned vocab: 0. "In plain terms": 6 before, 0 after.
- Citation census: author-year parenthetical count identical before and after
  (15 on the same extraction pattern); no citation added or removed; the two
  companion-title link-text changes align in-text names with the existing
  References entries.
- Heading tree: `##` sections unchanged and unrenumbered; new `###`/`####`
  only.
- Nothing outside `papers/paper-2-training-regimen/` touched.

## FLAGS (not fixed, per hard constraints)

1. Seed-count conflict, abstract vs body. The abstract says the SFT-warmed
   preference comparison ran "three seeds each" (DPO and KTO), but §3.1 says
   "three seeds for DPO, two for KTO", §4.2 reports "two-seed SFT-KTO" means,
   and §7 says "SFT-warmed KTO has two plain-answer seeds". One of these is
   wrong (presumably the abstract); left verbatim for the lead/PI to
   adjudicate.
2. Intro grammar: "argues that contention from the published evidence: a
   systematic extraction of 78 quantitative effects..." (§1) parses awkwardly
   ("argues that contention"). Left verbatim because any smoothing touches a
   claim-adjacent sentence about the synthesis's scope.
3. §4.3's parenthetical "(the first reward variant reached 97.87% on an
   earlier SFT base)" cites a different-base number inside a range statement.
   It is an arm (the schema-contract base, Appendix A row D), not a
   superseded measurement, so it stays under synthesis-not-journey; noting it
   here because the phrase "an earlier SFT base" is the one place the paper
   gestures at chronology.

## Plan.md consistency check (REPORT-ONLY, no edits)

Does paper 2's calibration-metric language conflict with paper 4's dial
scoping (§4.2 there)? No direct conflict. Paper 2's calibration metrics
(§3.4: emitted-confidence std, AUROC against appropriateness and against
correctness-given-answered, ECE, Brier) all describe the STATED channel, and
its only internal-probe claims are gate-axis claims (the 0.972-vs-0.637
like-for-like in §5 and §6, and the §4.11 pretrain-origin citation), which
match paper 4's gate numbers. Paper 4's ranking-not-probability fence is
about the internal correctness dial (dial ECE 0.151, "We claim the ranking,
not the probability"), an object paper 2 never mentions. One soft tension:
paper 2's Deployment reading item (iv) says "a linear probe of the hidden
states is a dramatically better uncertainty signal than anything the model
will tell you", unscoped as to axis and silent on ranking-vs-probability; a
reader could take it as promising a calibrated probability, which paper 4
explicitly declines to claim for the dial (the calibrated 1-D readout, ECE
0.004, is a doubt-axis result owned by paper 3). If the lead wants it
tightened, "better ranking signal" or an explicit gate-axis scope would close
the gap; no edit made.

## Judgment calls

1. Fixing the stale companion title + section pointers (commit 1) was treated
   as editorial citation-consistency, not a claim change; called out here
   because it touches citation text.
2. Whole-sentence bold emphasis kept: the four thesis knives ("abstention
   must be induced...", "DPO buys back usefulness...", "SFT induces,
   preference optimization repositions, GRPO amplifies", "emitted confidence
   tracks the decision to answer...") and the "polite liar" term-of-art bold.
   Read as deliberate emphasis, which VOICE.md does not ban; the ban targets
   run-ins and pseudo-headings.
3. The two compact process parentheticals kept as registered facts: the
   §3.3 reward-revision sentence (both variants appear in §4.3's table, so
   the reader needs the distinction) and the §3.4 schema-contract drop (it
   justifies the same-contract baseline rule). Neither is a narrated arc.
4. §2's new subsections are unnumbered `###` (matching paper 3's style)
   while §3/§4 keep their pre-existing numbered subsections; I did not
   renumber anything.
5. Figure-caption compressions keep one plain-language claim clause each
   rather than deleting outright, so every caption still reads as a complete
   claim without the body.
