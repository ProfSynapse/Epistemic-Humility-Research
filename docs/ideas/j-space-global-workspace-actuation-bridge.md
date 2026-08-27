# J-space (global workspace) as an actuation bridge

Status: H1 localization resolved 2026-07-07; FIT-only dose calibration resolved
2026-07-08; calibrated held-out bridge actuation contrast is next. This note is
an idea home, not a signed protocol.

## Source

"Verbalizable Representations Form a Global Workspace in Language Models."
Gurnee, Sofroniew, Lindsey (Anthropic), 2026-07-06.
https://transformer-circuits.pub/2026/workspace/index.html
(Ingested into the library as
`library/notes/tc-2026-workspace--verbalizable-representations-global-workspace.md`.)

External commentary bundle:
https://www-cdn.anthropic.com/files/4zrzovbb/website/cc4be2488d65e54a6ed06492f8968398ddc18ebe.pdf

Atomized commentary notes:

- [[tc-2026-workspace-commentary-dehaene-naccache--does-claude-possess-conscious-global-workspace]]
- [[tc-2026-workspace-commentary-butlin-shiller-plunkett-long--consciousness-cognitive-access-llms]]
- [[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]

Commentary atoms most relevant to this actuation bridge:

- [[cognitive-access]]
- [[privileged-stream]]
- [[cognitive-space]]
- [[interpretative-meta-tokens]]
- [[j-space-parallels-gnw-but-leaves-ignition-and-autonomy-open]]
- [[j-space-supports-privileged-set-not-yet-full-workspace]]
- [[j-lens-approximates-cognitive-space-via-token-jacobians]]
- [[qwen-j-lens-replication-supports-cross-model-cognitive-space]]
- [[j-lens-is-auditor-hypothesis-generation-not-verification]]

The J-lens (Jacobian lens) is the average linearized effect of an activation on
the model's next-token likelihood, averaged over positions and ~1000 prompts. It
identifies J-space: a small, privileged set of verbalizable representations (on
the order of 10 to 25 concepts active per position, under 10% of activation
variance) that are reportable, subject to directed control, and that causally
mediate internal reasoning. They demonstrate causal steering by swapping and
injecting J-lens vectors (multi-hop reasoning redirect 54 to 70%), and the
decisive result: when a concept vector is decomposed into its J-space and
non-J-space parts, only the J-space component drives verbal report (59% vs 5%).
J-space sits in mid-to-late layers; the final layers are a next-token "motor
regime" with near-zero workspace content.

## Why it matters to this program

Our signature finding across the actuation arc is a split: the epistemic readout
(doubt/knownness, correctness, confab-propensity) is portable and strong
everywhere, while actuation (writing to steer behavior) works on exactly one
checkpoint (AC on the GRPO-v2 lineage) and comes back null or fragile elsewhere
(AI-TRUE triple null across AL/AN/AO; dark subspace null; raw-base caution lever
exists but only crudely tightens with a narrow coherent window and collapse at
high dose).

The workspace result offers a mechanistic reason for that exact split: not all
activation directions are causally equal. A well-fit read direction is not
necessarily in the broadcast channel, so writing along it does not enter
downstream computation. That is read-linked but write-inert, which is the 59% vs
5% J-space / non-J-space asymmetry, and it maps almost one-to-one onto our
readout-portable / actuation-fragile gap. Writing to the workspace instead of to
an arbitrary residual direction is the "write to the workspace, not the thinking
or the output" bridge.

## Hypotheses

- H1 (localize, cheap read): are our epistemic signals J-space concepts? Compute
  the J-lens on Qwen3-4B and check whether the validated caution / doubt /
  confab-propensity directions verbalize as uncertainty tokens ("I don't know",
  "not sure"). If yes, the doubt signal is a workspace concept and abstention has
  a verbalizable substrate. No training, read-only.
- H2 (bridge, the actuation test): does injecting an abstention / "I don't know"
  J-lens vector into the workspace beat our erase-write on a residual caution
  direction, measured on selectivity? This runs on the SAME both-tail surface as
  the two-signal experiment (309 unanswerable confabs to tighten, 149 answerable
  refusals to release), so it is a clean head-to-head: workspace injection vs
  residual write.
- H3 (explains the nulls): the AI-TRUE, dark-subspace, and raw-base actuation
  failures happen because those writes were outside the J-space. Re-running
  actuation as J-space injection could succeed where residual writes failed.
- H4 (explains PAR / aux-head): the paper's counterfactual reflection training
  (train the model to articulate what it would say if asked, behavior improves in
  uninterrupted contexts, ablating those J-space concepts reverts the gains) is a
  near-twin of probe-as-reward (AI) and the aux-head (Q). It predicts PAR works by
  populating the J-space with the target concept, and that AI-TRUE actuation may be
  dead because training moved the readout without making caution a broadcast
  workspace vector. Testable by J-lens on the AI-TRUE checkpoint.

## Sharp, cheap prediction it hands us

J-space is mid-to-late but not final; the last layers are a next-token motor
regime. Our actuation writes at L34 of 36, which is likely IN the motor regime,
past the workspace. That could be why the L34 pos_ctrl only crudely flips with a
narrow coherent window and collapses at high dose. The hypothesis predicts that
mid-layer injection (roughly L14 to L28) would be more selective and less
collapse-prone than L34. This is directly testable and would reframe our layer
choice for every actuation cell, including the two-signal experiment.

## First experiments, cheap to expensive

1. **DONE 2026-07-07**: Reimplemented a minimal J-lens on open-weight
   Qwen3-4B via Jacobian-vector products and validated it against the
   final-layer logit/unembed baseline. Full-corpus Modal smoke:
   mean cosine 0.9811, mean top-10 overlap 0.82, top-1 match 3/5.
2. **DONE 2026-07-07**: H1 read on same-substrate bf16 directions. `pos_ctrl`
   and `c_hat` verbalize as self/absence/error/impossibility-like; `u_d` is
   answer/reply-like; `neg_ctrl` is a noisy local null. Layer profile localizes
   the Qwen3-4B workspace-like effective-dimensionality band to hs=23-29,
   peaking at hs=26; L34 maps to hs=34 and is just after that band.
3. **G0 stop 2026-07-07**: Initial mid-band layer sweep at absolute dose 200
   prepared successfully and read back accurately, but collapsed hs23/hs26
   before held-out outcome. This identified dose portability as the immediate
   failure mode.
4. **DONE 2026-07-08**: FIT-only dose calibration recovered usable
   non-collapsing setpoints for all layers: hs23=25, hs26=75, hs29=125,
   hs34=175. This keeps the layer-site hypothesis alive but does not test
   held-out mid-band superiority.
5. Calibrated held-out layer contrast: compare hs23=25, hs26=75, hs29=125
   against hs34=175 on the two-signal both-tail surface.
6. H2 injection head-to-head: workspace injection of an abstention concept vs
   erase-write caution, same surface, same selectivity gates.

## H1 result update (2026-07-07)

The J-space localization experiment resolved as an exploratory lab diagnostic:
`experiments/j-space-localization-qwen3-4b/AMENDMENT.md`. The result strengthens
the bridge hypothesis enough to justify a causal successor, but it does not by
itself prove that J-space writes will work.

The actionable refinement is layer choice. The original idea predicted that L34
may be late/motor-adjacent; the actual Qwen3-4B profile put the
effective-dimensionality peak at hs=26, with a broader hs=23-29 band and decline
by hs=35/36. Therefore the next write test should not simply repeat L34 with a
new vector. It should compare mid-band writes, especially hs=23/26/29, against
the existing L34/hs34 site on identical gates.

## Dose-calibration update (2026-07-08)

The first causal successor exposed an instrumental assumption: absolute dose 200
is not portable across layer sites. hs23 and hs26 collapsed at dose 200, so the
held-out contrast stopped at G0. A FIT-only calibration then recovered usable
setpoints for every site: hs23=25, hs26=75, hs29=125, hs34=175. The correct next
test is therefore not "does dose 200 work mid-band?" but "with calibrated
setpoints, do mid-band writes beat or differ from hs34 on held-out rows?"

## Feasibility and caveats

- The paper uses Claude Sonnet/Haiku/Opus 4.5 and 4.6; the method must be
  reimplemented for Qwen3-4B. This is feasible on open weights and is arguably
  easier for us than for external readers.
- Cost: the Jacobian is averaged over layers, positions, and ~1000 prompts. Use
  JVPs, not full Jacobians. Feasible on the local 3090 for a 4B model, but scope
  the compute before committing.
- Layer scaling: the paper's J-space is layers ~38 to 92 of ~100; on Qwen3-4B's 36
  layers the analog is mid-to-late, not the final block.
- The paper is careful that workspace structure does not imply phenomenal
  consciousness; keep that discipline in any writeup. The relevance here is
  strictly mechanistic (a causally-central write locus), not philosophical.
