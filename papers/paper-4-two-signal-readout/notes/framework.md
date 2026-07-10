# The Two-Signal Readout Framework — working theory synthesis

*Working document, 2026-06-30. Synthesizes the O→P→Q→S→T→U→W amendment trajectory
into a theoretical frame, ahead of editing the diagnosis paper / drafting the
readout paper. (Numbering note, 2026-07-01: "Paper 2"/"Paper 3" below are the
OLD labels; in the five-paper line they are Paper 3 = "Knows but Doesn't Say"
and Paper 4 = the two-signal readout.) Not for
distribution. Numbers are single-seed (seed 1), single-model (Qwen3-4B) unless a
confirmatory replication is named.*

## 0. One-sentence thesis

**Epistemic state in a small LM is largely a readout, not a training outcome:** the
internal representation already contains two orthogonal, linearly-decodable axes —
*answerability* (read at the prompt anchor) and *per-answer correctness* (read after
the answer) — that compose into a deployable trust signal; our training relocates
behavior and *sharpens* the hallucination veto, but does not *create* the signal.

This extends Paper 2 ("Knows but Doesn't Say"), which established the gap and
*proposed* a confidence-head engine change as the remaining route. The trajectory
below shows the route works and, more strongly, that its core signal is recoverable
with no training of ours at all.

## 1. The arc, as one logical line

1. **The gap (Paper 2 R1).** The model holds a calibrated internal answerability
   estimate (known/unknown AUROC ≈ 0.997, readout ECE ≈ 0.004) but states a
   near-constant, chance-level confidence (≈ 0.52–0.56). Knows, doesn't say.
2. **The geometry (Paper 2 R2).** The internal signal is two correlated-but-separable
   axes: a graded *doubt* axis and a *caution* gate (caution-specific refuse/answer
   AUROC 0.825 after orthogonalizing out doubt).
3. **Asymmetric causality (Paper 2 R3).** Ablating the caution residual cuts
   over-refusal on known items 0.994 → 0.030 with clean specificity; no intervention
   installs abstention on true unknowns. We can relax excess caution, not install
   missing caution.
4. **Training resistance + dissociation (Paper 2 R4; N, M).** The stated-confidence
   gap survives DPO/KTO/GRPO-v1/v2/v3 + two contrastive-SFT variants. Two opposite
   training pressures fail on the same channel: RL on the calibrated base keeps stated
   calibration but cannot install knowledge-conditioned action (N, "says but doesn't
   act"; survives halving the KL anchor → structural, not anchor artifact); distilling
   the internal axis into the stated token keeps action but collapses the scalar onto
   the action (M, "acts but doesn't say"). The bottleneck is the *channel* — a single
   confidence token emitted by the LM head under next-token cross-entropy.
5. **The readout route works (O, Q, P).** A linear readout of the internal axis drives
   a policy passing all behavior+calibration gates (O, oracle ceiling: margin +95pt,
   AUROC 0.997, ECE 0.015). A head trained *through the production aux_head engine*
   reproduces that ceiling (Q, transfer AUROC 0.983). The readout is not
   dataset-specific (P: KUQ-fit answerability reads SelfAware cold at 0.983).
6. **A second axis: per-answer correctness (S, T).** Beyond answerability, a linear
   probe reads whether *this specific answer* is correct, post-generation (S, AUROC
   0.834 on the Instruct base, L20; reading *after* the answer beats before by +0.065,
   CI excludes 0 — a P(True)/self-eval win). It survives on the deployed clean-SFT→
   GRPO-v2 checkpoint (T, 0.819, L22).
7. **The correctness axis vetoes hallucination (U).** The correctness dial assigns
   hallucinated answers to unanswerable questions the lowest trust of any group (U,
   AUROC 0.980; within-SelfAware control 0.93 rules out dataset shift). Confident
   confabulation does *not* read like correctness.
8. **The two axes are a pipeline, not a fused scalar (Stage 1.5).** Gate (answerability,
   prompt anchor) and dial (correctness, post-gen) are orthogonal; fusing the scalars
   *hurts* correctness (Δ −0.014). Keep them as two stages: gate abstains on
   unanswerable, dial surfaces trust on what's answered and vetoes residual
   hallucination.
9. **The whole mechanism is training-free (W).** On the *raw* Instruct base (no
   adapter, no abstention-SFT/GRPO): gate 0.997, dial 0.834, hallucination-veto 0.754.
   Both gates pass. Training does not create the veto — it *sharpens* it (0.754 → 0.980;
   hallucination dial-mean 0.271 on base → 0.018 trained) and adds ~0 to the gate.
   Quantified: training buys +0.226 AUROC of veto sharpening, ~0 gate gain, plus
   autonomous behavioral abstention.

## 2. The mechanisms, atomized (candidate KG nodes)

These are the cause→effect claims the trajectory supports, written to become
`mechanism:` atoms (see §4). Each names its evidence amendment(s).

- **M1 — answerability-linearly-readable-pretraining.** A logistic probe on residual
  activations at the prompt anchor separates answerable from unanswerable questions
  in the *untrained* base (0.836–0.997 depending on pool), essentially unchanged by
  our training (+0.015 LoRA on matched data). *Evidence:* W (gate-on-base), P, O.
- **M2 — per-answer-correctness-readable-post-generation.** A linear probe reads
  whether the just-emitted answer is correct, peaking *after* the answer token
  (post > pre by +0.065). *Evidence:* S, T.
- **M3 — answerability-and-correctness-are-orthogonal-axes.** The two readouts are
  separable; fusing their scalars degrades correctness ranking → deploy as a
  two-stage pipeline. *Evidence:* Stage 1.5.
- **M4 — training-sharpens-not-creates-hallucination-veto.** The correctness dial
  flags confident confabulation training-free (0.754) but training sharpens it to
  lowest-of-all-trust (0.980); gate gain from training ≈ 0. *Evidence:* W vs U.
- **M5 — verbalized-confidence-channel-bottleneck.** The representation→verbalization
  gap is a property of the single LM-head confidence token under cross-entropy, not a
  knowledge deficit; two opposite training pressures fail on it → an engine change
  (dedicated head, regression loss vs the internal axis) is the route. *Evidence:*
  N, M, Paper 2 R4; ceiling shown by O, Q.
- **M6 — caution-gate-causally-steerable-asymmetrically.** Behavior is controllable
  along the caution axis (relaxable), but missing caution cannot be installed by
  steering. *Evidence:* Paper 2 R3.

## 3. Blind spots to fill before writing up (rigor audit)

Ordered by how load-bearing they are for the claims we want to make.

### Tier 1 — needed before any claim leaves "single-seed exploratory"
1. **Seed replication.** Everything is seed 1. The huge effects (gate 0.997;
   over-refusal 0.994→0.030) are low seed-risk; the *seed-sensitive* numbers are the
   ones we'd headline from this arc: dial AUROC (S 0.834 / T 0.819), the veto deltas
   (W 0.754 vs U 0.980), and the post>pre gain (+0.065). **Action:** re-fit S/T/U/W on
   ≥2 fresh seeds of the generation+extraction (the probe fit is cheap; the GPU cost is
   re-generating answers). Pre-register the replication before running.
2. **"Training-free" scoping is honest but narrow.** W's "raw base" is
   `unsloth/Qwen3-4B-bnb-4bit` — the *Instruct* base, already instruction-tuned
   upstream. So "training-free" = "no abstention-SFT / no GRPO of ours," NOT "no
   training ever." The answerability axis may be a product of upstream instruction
   tuning. **Action:** state this scoping explicitly; if feasible, add a
   pre-instruct/base-completion checkpoint read as a bound (may not exist for Qwen3-4B
   in our cache — check, else scope in prose).

### Tier 2 — hardens the correctness/veto claims
3. **Cross-dataset reference in the veto.** U-G1/W-G1 use S's PopQA/TriviaQA *correct*
   as the positive class vs SelfAware *hallucinations* — cross-dataset. The
   within-SelfAware control bounds it (0.93 trained / 0.70 base) but does not
   eliminate. **Action:** a within-source correct-vs-hallucination contrast (graded
   SelfAware answers, or a single dataset carrying both classes).
4. **Structural, ungraded hallucination label.** "unknown ∧ answered = hallucination"
   is structural. **Action:** spot-grade a sample of the 677 base / 121 trained
   "hallucinations" to confirm they are confabulations, not mislabeled-answerable.
5. **Dial calibration, not just ranking.** The dial *ranks* well (AUROC) but is poorly
   *calibrated* as a probability (S ECE 0.151, G3 missed). For a thresholdable trust
   number, ranking may suffice; for a *stated probability*, it does not. **Action:**
   decide which deliverable we claim; if probability, add a calibration map
   (isotonic/Platt) and report post-calibration ECE.

### Tier 3 — generalization, for the discussion/future-work
6. **Natural-answer surface (the shelved V question).** S/T/U/W all use forced or
   answer-encouraging prompts. The dial's behavior on the model's *own natural*
   answers is untested (V shelved as data-starved: ~96% refusal). Real gap for any
   *deployment* claim; report as a known limitation + future cell.
7. **Correctness axis causality.** The gate has causal steering evidence (R3); the
   dial is correlational only. **Action (future):** steer along the correctness axis
   and test whether reported/behavioral correctness moves.
8. **Cross-model.** All Qwen3-4B. P showed cross-*dataset*, not cross-*model*.
   **Action (future):** replicate the gate+dial existence on a second family (e.g.
   Llama-3-8B) for an existence (not magnitude) claim.

## 4. Where these land in the papers

*(Numbering below uses the current 4-paper map: Paper 1 = training regimen
[review + full SFT/DPO/KTO/GRPO experiment]; Paper 2 = "Knows but Doesn't Say";
Paper 3 = this two-signal readout; Paper 4 = steering.)*

- **Paper 2 §7–8 (R4 + Discussion).** The arc up through O/Q/P/N/M *is* the close of
  Paper 2's argument: it proposed the confidence-head engine change; O/Q show the
  ceiling and that the production engine reaches it. Fold O/Q/P as a "Result 5: the
  readout route reaches the ceiling" or a Discussion subsection; N/M already anchor §7.
- **Paper 3: the two-signal readout.** S/T/U/Stage-1.5/W/X/Z are a *distinct*
  contribution — a second axis (correctness), the orthogonality/pipeline result, the
  training-free finding, and the cross-size/cross-family replication. Title:
  *"It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for Epistemic
  Humility in Small Language Models."* Drafted at
  `papers/paper-4-two-signal-readout/manuscript.md`; this doc is its seed.
- **Paper 1 (training regimen; review from meta-analysis/paper/draft-v0.md + the
  experiment in paper1-training-regimen-draft-v1.md).** M4 (training sharpens not
  creates) and M5 (channel bottleneck) connect to the review's "coherence axis is
  unmeasured" thesis; cite the trajectory as the empirical instantiation.

## 5. KG-ingest of our own findings (atomize the trajectory)

We already partially do this: `mechanism:answerability-probe-transfers-across-qa-datasets`
is Amendment P, and estimator/probe mechanism atoms exist. The recent arc (S/T/U/
Stage-1.5/W and the M1–M6 set above) is *not* yet atomized.

**Method — the kg-ingest by-hand path, skipping Move 0's arXiv fetch** (we are the
source, so there is no arXiv id to acquire):
1. **Inventory** (Move 1): `kg_inventory.py` to reuse existing atoms (auroc,
   abstention, calibration, the existing P/estimator mechanisms) rather than duplicate.
2. **Internal "paper" nodes** (the source of our edges). Create paper-type notes for
   our own work under `library/notes/`, e.g.:
   - `internal-paper3--knows-but-doesnt-say.md` (kg: type paper, status canonical),
     edges → existing + new mechanisms it supports.
   - `internal-twosignal-readout--training-free.md` for the S/T/U/W/Stage-1.5 cluster.
   Provenance points at the durable in-repo artifacts (the amendment docs +
   `amendment_*_result.json`), not scratch paths.
3. **Mechanism + claim atoms** (Move 3a, by hand): one `mechanism:` file per M1–M6 in
   `library/concepts/mechanisms/`, each with `cause`/`effect`/`polarity`, a
   `supported_by` edge to the internal paper node, and `related_to` edges into the
   existing graph (e.g. M4 `related_to` `calibration-aware-training-prevents-confidence-drift`,
   `calibration-hallucination-tradeoff`). Add `## Claims` to the paper notes with the
   amendment + result-JSON path as the evidence cite.
4. **Finalize** (Move 4): `apply_kg_patches.py` (empty patch → regen MOC + dangling
   check), `migrate_to_canonical.py`, `validate_kg_relationships.py` (the gate),
   `kg_index.py` after `git add` so `bin/search` sees them.

**Payoff:** our findings become searchable and *linkable alongside the 100+ external
mechanisms* — so we can see where M4 (training sharpens not creates a veto)
agrees with or contradicts external calibration-tuning mechanisms, and the framework
above becomes a navigable subgraph rather than prose. This is the atomization the
user asked for.

## 6. Proposed sequencing

1. Atomize the trajectory into the KG (§5) — cheap, no GPU, makes the framework
   navigable and surfaces literature contradictions to address in the writeup.
2. Pre-register + run the Tier-1 seed replication of S/T/U/W (§3.1) — the one thing
   that gates promotion of any of these numbers to a headline claim.
3. Fill Tier-2 (§3.3–3.5) opportunistically (mostly CPU/analysis).
4. Then edit Paper 2 §7–8 and seed Paper 3 from this doc; Tier-3 → future work.
