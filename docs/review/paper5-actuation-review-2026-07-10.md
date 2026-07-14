# Paper 5 (actuation) review memo, 2026-07-10

Reviewer: read-only audit agent. Scope: papers/paper-5-actuation/manuscript.md
(draft v0, dated 2026-07-08, titled "Readable Is Not Writable") against the
governed record as of main @ 27889122, plus the signed AMENDMENT.md of the
running mid-band experiment in the qwen35-midband worktree. Every experimental
fact below was read from the named experiment's AMENDMENT.md; section or line
references are to those docs. The manuscript, registry lines, and library notes
were used as navigation only.

## TLDR verdict

The draft is closer to the new frame than the "old negative thesis" label
suggests: it already contains the gated-controller win and the layer-site
result. But it is stale in four material ways. (1) It predates the two
replication cells resolved 2026-07-09: rep1 (registered G1 fail on a
ceiling-saturated single-source pool) and rep2 (registered FULL PASS on a
multi-source pool, +19.0pp, McNemar p = 4.5e-13). The draft's own "next study"
list asks for the same-model replication that now exists. (2) It omits the
radial anti-propensity null (AL) entirely, which is the record's cleanest
"reads but does not actuate" demonstration and the second element of the PI's
requested spine. (3) It cites the sycophancy cell as a resolved "Outcome" when
that experiment is draft/unsigned and its own doc says the result is interim
and non-resolving. (4) The title, abstract framing, and synthesis section still
lead with the negative. The requested spine is fully supported by the record
with two honest adjustments: the propensity null must not lean on the
confounded AN/AO composition cells beyond what they show, and the mid-band
localization claim must carry the pool-sensitivity and within-band-ordering
caveats that rep1/rep2 established.

## 1. Inventory of actuation-relevant cells

All statuses and verdicts below are read from each experiment's AMENDMENT.md.
Tier: everything here is Tier-2 / Tier-A exploratory, never pooled with the
locked Phase 1 headline matrix.

| Slug | Status | Verdict (from the doc) | Role in the actuation story |
|---|---|---|---|
| causal-confidence-steering (AA) | resolved | FALSIFIER-1: no effect gate passed in any of 8 cells (activation + text, gate + dial, 2 positions) on Qwen3.5-4B | Opens the caveat landscape: naive "turn the probe around" writes and injections are flat; carries the named anchor one-token intervention-surface confound and the revision-floor instrument caveat (its section 7) |
| first-person-injection (AB) | resolved | AMBIGUOUS-LEANING-NEGATIVE: gate@early +2.0pt (CI excludes 0) vs a +10pt bar; dial@late instrument invalid (revised = 500/500 both arms); dial@final miss (-2.7pt, CI includes 0) | Strongest natural-language framing does not open the text channel; leaves a ~2pt compliance trickle |
| inverted-injection-trained-checkpoints (AD) | signed, never launched | "not launched (signed; preconditions open; shelved behind AC/AH)" | No evidence; only citable as a registered-but-unlaunched design |
| doubt-regulated-caution (AC) | resolved | AC-G1 PASS: coupled beats permuted +8.7pt, CI [+5.6, +12.0]; AC-G2 estimate +10.7pt vs constant ablate; specificity guard pass | First use-the-signal win: a doubt-proportional caution setpoint write carries information on the trained checkpoint (GRPO-v2). In-distribution, one layer, one checkpoint (its Limitations) |
| base-model-doubt-coupled-caution (AE) | resolved (STOP) | Pre-stated adequacy-floor STOP at census: raw base abstains ~93% on unknowns under the affording prompt (confabulates 21/300); primary cells under the >=150 floor; actuator question stays OPEN; result section never backfilled (frontmatter outcome) | Scope note: why the raw-base gating work moved to mined confab-rich pools rather than SelfAware |
| second-person-doubt-prime (AF) | resolved | AF-G1 PASS: true beats permuted on the selectivity gap +18.0pt, CI [+11.8, +24.7]; own-readout attribution NOT established (probe label coincides with gold 600/600 on this pool, section 8) | The one text channel that moves behavior; localizes AA/AB nulls to channel authority |
| oracle-dissociation-prime (AG) | resolved | ASYMMETRIC COMPLIANCE: wrong muzzle obeyed +34.0pt [+26.5, +41.5]; wrong release resisted (+7.9pt); asymmetry +26.1pt passes; doubt axis unmoved-to-anti-semantic, compliance travels through the caution axis (sections 9.1, 9.3) | The text channel is obedience, not belief revision; "knows it knows, obeys anyway" |
| divergent-pool-own-readout (AH) | resolved | H-COMPLIANCE certified via Addendum A1: release congruence -0.21pt, CI [-4.45, +4.10] (a precise zero); A1 positive control +50.98pt vs +20pt floor (sections 9, 10.3) | Prime uptake does not consult the model's own readout even where readout and gold diverge; closes the native-path-via-prompting question |
| probe-as-reward (AI) | resolved | NULL (G1 fail, G0 pass): TRUE congruence 59.75% vs PERMUTED 76.75%, differential -17.0pt, CI [-21.5, -12.5]; instrument valid (fresh probes 0.9948/0.9946, both arms 2934/2934 steps) (section 5) | The reward channel also does not couple the readout; extends knows-but-does-not-consult across channels |
| commitment-point (AK) | resolved | AK-G1 MISS (-0.0175 vs +0.10 bar; veto already assembled at first visible token); AK-G2 MISS (floor not cleared); AK-G3 computed MISS but confounded by a diagnosed gen_stream hook-firing bug (328/328 rows byte-identical across all 7 alphas); falsifier wording matched numerically but NOT adjudicated (section 8) | Answer-window steering evidence is unusable until the hook check runs; must not be cited as a causal null |
| radial-anti-propensity-steering (AL) | resolved | USE-THE-SIGNAL NULL (injection channel): AL-G1 PASS (collateral 0); AL-G2 MISS (0 of 116 confabs killed; dose ladder kills 0/0/1); AL-G3 MISS (kill diff 0, CI [0.00, 0.00]). Null is causal, not instrumental: readback moved -2.7133 vs commanded -2.7110, unpushed rows 1564/1564 parity (frontmatter outcome) | The spine's second element: the confab-propensity direction reads the cloud and moves by the commanded amount but does not actuate the fabricate-vs-refuse choice |
| selected-setpoint-regulator (AN) | resolved | NULL, falsifier fired, and CONFOUNDED: 0/116 kills, all 47 flagged confabs become different confabs; write landed precisely on-axis; but the actuator was a caution_perp REFIT on AI-TRUE with cosine -0.064 to AC's validated direction and was never validated as a lever (sections 11, 9 caveats) | Bounds the composition story; explicitly must NOT be read as "the caution axis cannot suppress confabulation" or as any input-vs-write-side rule (its section 11.3) |
| ao-propensity-regulated-caution (AO) | resolved | NULL (Stage 1 knob validation): no caution direction validates as a behavioral lever on AI-TRUE (all CIs include 0, point effects near zero, smoke fired); Stage 2 did not run per the falsifier (Outcome) | The clean explanation AN could not give: AI-TRUE has no validated caution lever; the doubt-gated snap story is substrate-dependent |
| dark-actuator-screen | resolved | NULL: G-instrument valid (pos_ctrl flips 79/80 confabs to coherent refusals); all nine raw candidate graduations are artifacts (grader coherence gap, under-dosed random control, off-manifold overdrive); dark subspace shelved (Outcome) | Validates the on-manifold answer/refuse lever on raw-base and rules out the off-axis subspace as an actuator source |
| doubt-gated-caution-tighten | resolved | Exploratory PASS: G1 136/185 = 73.5% clean_tighten, Wilson CI [66.7, 79.3]; G2 8/258 = 3.1% known-correct false-refusal, CI [1.6, 6.0]; G3 clean (random direction 13/185 = 7.0% vs no-op 21/185 = 11.4%; permuted gate cost 59/258 = 22.9%) (Outcome) | The central positive result: an end-to-end doubt-gated caution snap on held-out rows the direction fit and tau never touched |
| doubt-snap-cross-family-confirmatory | signed, RUNNING | No outcome. Pre-outcome notes on record: Ministral-3 loader ineligibility swap, Llama-8B access mirror swap, grader portability fix, and the 2026-07-09 Qwen3.5 dose-grid recalibration (sigma_c 2.80, registered grid was a ~38-sigma overdose) | The registered promotion vehicle for the family claim; nothing in the paper may depend on its outcome |
| j-space-localization-qwen3-4b | resolved | Lab-diagnostic: J-lens smoke passed (cosine 0.9811, top-10 overlap 0.82); workspace-like band hs23-29, peak hs26; L34 maps to hs34 just after the band; pos_ctrl/c_hat verbalize as self/empty/impossible/error tokens, u_d as answer/reply tokens, neg_ctrl noisy (Outcome) | The localization element of the spine; read-only, no gates |
| j-space-midband-write-sweep-qwen3-4b | null-result (G0 stop) | Pre-outcome stop: dose-200 smoke collapsed all dosed hs23/hs26 rows (readback accurate); absolute dose is not portable across layer sites (Outcome) | Method lesson feeding the calibration cell; not a behavioral null |
| j-space-midband-dose-calibration-qwen3-4b | resolved | FIT-only pass: usable setpoints hs23=25, hs26=75, hs29=125, hs34=175; hs23/hs26 recover below 200 (Outcome) | Enables the calibrated contrast |
| j-space-calibrated-layer-contrast-qwen3-4b | resolved | Exploratory pass: hs23 165/185 = 89.2% vs hs34 123/185 = 66.5% (+22.7pp), cost +0.78pp (9/258 vs 7/258); hs34 viable (Outcome) | First held-out layer-site win |
| j-space-layer-contrast-replication-qwen3-4b (rep1) | null-result | Registered G1 FAIL: best mid-band (hs29 99.67%) beat hs34 (94.12%) by only +5.6pp vs a 10pp bar, on a ceiling-saturated single-source fresh pool; direction replicates with CI separation at hs23/hs29; magnitude pool-dependent; both predictions wrong (Outcome) | The honest caveat cell: magnitude is unidentifiable near ceiling |
| j-space-layer-contrast-rep2-multisource (rep2) | resolved | Registered FULL PASS: hs29 205/221 = 92.8% vs hs34 163/221 = 73.8% (+19.0pp); paired McNemar 42 late-only vs 0 mid-only discordants, p = 4.5e-13; cost delta +1.43pp (hs29 2.81% vs hs34 1.38%, an absolute doubling, disclosed); hs34 inside the pre-registered interpretability window; both predictions correct (Outcome) | The registered same-model replication of the mid-band advantage, off-ceiling, multi-source |
| j-space-token-targeted-refusal-qwen3-4b | falsified | Exploratory falsification: hybrid +0.54pp over c_hat_only (bar +4pp), G3 fail; token-only arm non-inert at 88/185 = 47.6%; safe and accurate write (Outcome) | Verbalizable token targets are real actuators but redundant with the caution snap |
| aq-sycophancy-activation-actuator (AQ) | DRAFT, unsigned | No resolved verdict. Interim (explicitly non-resolving) r2 record: readout OOF AUROC 0.819 with confound caveats; actuator smoke passed after fix; anti_sycophancy_vs_control diff 0.0, CI [-5, 5]; doc states "not a final resolved verdict" (Outcome interim sections) | Adjacent supporting pattern only; currently cited too strongly by the manuscript (see staleness finding S3) |
| qwen35-4b-midband-doubt-snap | signed 2026-07-10, RUNNING (worktree qwen35-midband) | No outcome. FIT-side dose ladder at hs20/hs23/hs26 vs late hs30 on Qwen3.5-4B (hybrid linear-attention); Stage A profile peak hs23; Stage B fits AUC 0.9926-0.9960 | What it adds either way: G1 pass attributes the Qwen3.5 late-site dose-viability failure to the write site (the mid-band lesson transfers to an architecturally distinct family member); falsifier attributes it to the mechanism on this substrate (a family-dependence bound). Its outcome is NOT in; the paper may cite only that the experiment is registered and running |

## 2. Staleness audit

Ordered by importance. "Traces" means the number matches the amendment doc.

- **S1 (major, missing results). Rep1 and rep2 are absent.** The draft (dated
  2026-07-08) predates both resolutions (2026-07-09). Consequences: (a) section
  4.5's "It needs same-model replication" and section 6.5 item 1 ("Same-model
  replication") ask for work that is now done and resolved; (b) the +22.7pp
  layer-site number is presented without the pool-sensitivity story rep1/rep2
  established (magnitude unidentifiable near ceiling, replicates at +19.0pp
  off-ceiling); (c) the best mid-band layer differs by pool (hs23 on the
  original held-out, hs29 on the multi-source pool, and hs26, the profile
  peak, is the weakest mid-band arm on both replication pools), which the
  paper currently does not know; (d) rep2's disclosure that hs29's absolute
  known-correct cost doubles hs34's (2.81% vs 1.38%) belongs next to any
  claim built on it. Rep2's Outcome explicitly names Paper 5: "Paper 5's
  layer-site section can now pair rep1 and rep2 as a single pool-sensitivity
  story."
- **S2 (major, missing result). The radial anti-propensity null (AL) is
  nowhere in the paper.** It is the record's cleanest demonstration that a
  strong readout direction can be moved by exactly the commanded amount with
  zero behavioral effect (readback ratio 1.0008, 1564/1564 unpushed parity,
  0/116 kills). The PI's requested spine names it explicitly ("the propensity
  direction reads but does not actuate"). The channel map in section 5 has no
  row for it, and the abstract's channel list skips the injection-channel
  null entirely.
- **S3 (major, provenance). Section 4.7 and Appendix A cite the sycophancy
  cell as a resolved outcome.** The AQ doc is draft/unsigned and its own
  Outcome section says each interim record "is not a final verdict and does
  not update experiment.yaml:verdict." The numbers the manuscript quotes
  (control diff 0, write fired, neutral guardrail pass) do appear in the
  interim r2 record, so they are not invented, but presenting them as an
  "Outcome ... Supporting exploratory null" overstates their status. Either
  drop the paragraph or label it an interim, unsigned pilot and say so in
  Appendix A.
- **S4 (moderate, missing results). AN and AO are absent.** These bound what
  the paper may claim about the gated-write mechanism's generality: on the
  AI-TRUE checkpoint, no caution direction validates as a behavioral lever
  (AO Stage 1, clean), and the propensity-selected caution-actuated
  composition null (AN) is confounded by an unvalidated refit actuator
  (cosine -0.064 to the validated direction). The paper's current story
  ("the gate supplies selectivity, the snap supplies refusal") implicitly
  generalizes across substrates; the record says the snap needs a validated
  lever per checkpoint and that at least one checkpoint lacks one. AN's own
  section 11.3 also pre-empts a tempting overgeneralization the paper should
  inherit: do not read the nulls through any "input-side actuates, write-side
  nulls" lens, because AC is a write-side pass.
- **S5 (moderate). AC is confined to a table row.** Appendix C even asks
  "Decide whether AC belongs in the main result body." Under the new frame the
  answer is yes: AC is the first use-the-signal win (+8.7pt over permuted, CI
  [+5.6, +12.0], on the trained checkpoint, with the same erase-write
  mechanism the raw-base snap uses), and it is the natural opening of the
  "gated and regulated writes work" half of the paper. Its in-distribution
  limitation (direction and gains fit on the evaluated row population) must
  travel with it.
- **S6 (moderate). The falsifier-and-prediction machinery is off the page.**
  VOICE.md's empirical spine section requires registered predictions,
  including misses, and a named kill criterion per headline result. The
  record is rich here: both parties wrong on rep1's magnitude, both right on
  rep2, the user's full-confidence misses on AL-G2/G3 and AN, both wrong on
  AI, both right on AH (H-compliance). None of this appears.
- **S7 (minor). Frontmatter evidence_base is stale and inconsistent.** It
  mixes old root-level filenames (AMENDMENT-AB-first-person-injection.md
  style) with experiments/<slug>/ paths, and omits AL, AN, AO, AE, rep1,
  rep2, and the dark screen (the last is in Appendix A but not the
  frontmatter).
- **S8 (minor). Numbers that do trace.** I re-checked every quantitative claim
  in the draft against its doc: the AA/AB/AF/AG/AH/AI numbers, the gate-and-
  snap numbers (73.5% [66.7, 79.3]; 3.1% [1.6, 6.0]; 13/185 random; 59/258
  permuted; FIT AUC 0.9955), the J-lens smoke and band numbers, the
  calibration setpoints, the layer-contrast numbers (89.2% vs 66.5%, +0.78pp),
  and the token-target numbers (47.6%, +0.54pp, +0.39pp) all trace. Two
  presentation nits: section 4.4 quotes the random-direction arm (13/185)
  without the no-op baseline (21/185 = 11.4%), which is the comparison the
  doc's G3 actually uses; and section 4.4's ungated dose-200 characterization
  ("tightened confab rows well but also caused many known-correct rows to
  refuse") rests on the diagnostic table recorded in the amendment's
  Motivation (82.5% tighten, 36.2% false-refuse at dose 200), which is
  explicitly gitignored diagnostic scratch cited for provenance; if the paper
  prints those numbers it must label them as the unregistered diagnostic that
  motivated the registered design (see hardening item H4).
- **S9 (minor). Residual negative-thesis framing.** The title, the abstract's
  "the answer is mixed," the introduction's block-quoted thesis ("Readable is
  not writable"), and section 5's framing all put the failure first. Under
  the re-scope these become the caveat structure inside a paper whose
  headline is the working controller.
- **S10 (informational). The running cells are correctly absent.** Nothing in
  the draft depends on doubt-snap-cross-family-confirmatory or
  qwen35-4b-midband-doubt-snap outcomes. Keep it that way; both may be named
  as registered and running.

## 3. Reframe plan (ordered)

Verification first: the PI's spine holds against the record, with two
adjustments. (a) "Ungated pushes fail or act asymmetrically" is supported by
AA/AB (flat, with the anchor-surface and revision-floor instrument caveats
named in AA section 7 and AB section 8), AF/AG/AH (authority moves policy;
asymmetric compliance; zero own-readout congruence), AI (reward null), AL
(propensity push null with verified injection), the dark screen (no off-axis
lever), and the non-selectivity of the unconditional caution write. (b) "The
propensity direction reads but does not actuate" is AL, clean; AN and AO may
only be cited as bounding the composition attempts, with AN's dead-actuator
confound stated. (c) "The doubt-gated caution write converts confabulations at
high rate with small known-correct cost, replicated on the multi-source pool"
is supported: 73.5%/3.1% on the original held-out; 89.2%/3.5% at the
calibrated mid-band site; 92.8%/2.81% (hs29) vs 73.8%/1.38% (hs34) on rep2's
multi-source pool with McNemar p = 4.5e-13. Note the replications are of the
gated snap at contrasted layer sites; every arm in every pool is the gated
instrument, so the conversion behavior itself has now been observed on three
disjoint row pools of the same model. (d) "Localization (workspace band)" is
supported in direction on all pools, with magnitude pool-dependent and the
within-band ordering unstable (hs23 best on pool 1, hs29 on pool 3, hs26
never best despite being the profile peak). Where the record says otherwise
than a flat version of the spine, I say so inline below.

The ordered revision plan:

1. **Retitle and rewrite the abstract to the positive frame.** Lead with the
   result: a training-free controller that reads the model's own doubt state,
   fires selectively, and writes a caution setpoint converts roughly three
   quarters to nine tenths of held-out confabulations into clean refusals at
   1.4 to 3.5 percent known-correct cost, replicated across three disjoint
   pools on one model. Then name the caveat landscape as the finding's
   structure, not as the headline.
2. **Restructure section 4 into the spine order.** 4.A: the caveat landscape,
   compressed (naive writes and text injection flat; system-prompt authority
   works but is compliance, asymmetric, and consults nothing; reward trains
   correlates, not consultation; the propensity direction moves but does not
   actuate; no off-axis dark lever; the unconditional caution write is not
   selective). One subsection each, a paragraph or two, numbers in sentences.
   4.B: gated and regulated writes work: AC first (trained checkpoint,
   proportional coupling, +8.7pt over permuted), then the raw-base doubt-gated
   snap as the main result with its full gate table. 4.C: localization and
   replication: J-lens band, dose calibration as a method note, the calibrated
   contrast, then rep1 and rep2 together as one pool-sensitivity story
   (rep2's Outcome supplies the template sentence). 4.D: what does not help
   and what is open: token-target redundancy, release-direction null,
   substrate dependence (AO), the two running registered cells.
3. **Add AL as a first-class result** (spine element 2), with the injection-
   fidelity numbers that make it a causal null rather than an instrument
   failure.
4. **Fold AN/AO into a "substrate and lever validation" caveat subsection.**
   The honest sentence: the gated write requires a caution direction validated
   as a behavioral lever on the target checkpoint; on one trained checkpoint
   (AI-TRUE) no such lever validates, and the composition null there is
   uninterpretable beyond that. Inherit AN's explicit warning against an
   input-side-vs-write-side rule.
5. **Rewrite the synthesis map (section 5)** to the new order: rows for the
   propensity push and the composition attempts; the gated snap row updated
   with the three-pool numbers; a localization row carrying the pool-
   dependence caveat.
6. **Label every claim's evidential tier explicitly, per the promotion
   rule.** Everything in this paper is exploratory. Within that: the same-model
   mid-band advantage now has a pre-registered same-model replication (rep2
   passed its registered gates), so it may be asserted flatly at same-model
   scope; the gated-snap mechanism may be asserted at raw-base Qwen3-4B scope
   across three pools; the family-level claim is unpromoted, and its
   registered confirmatory (the cross-family panel) is running and must be
   described as such with zero dependence on its outcome. AC stays a
   single-run, in-distribution exploratory positive.
7. **Fix the AQ citation** (S3): drop or relabel as an unsigned interim pilot.
8. **Add the registered-prediction and falsifier layer** (S6): one compact
   registered fact per experiment (call, outcome, miss or hit), and one kill
   criterion sentence per headline result.
9. **Update frontmatter, Appendix A, and Appendix C**: add AL/AN/AO/AE/rep1/
   rep2 rows, correct AQ's status, delete the now-done items from the
   next-study list, and normalize source paths to experiments/<slug>/.
10. **Voice pass** (section 6 of this memo).

## 4. Hardening list

Ordered by expected value per cost. Cost classes: CPU, local-3090, cloud-paid.

- **H1. Resolve the cross-family doubt-snap panel (cloud-paid, already
  running).** Hardens: the family-generality claim, which is the single
  biggest scope limit on the headline. This is the registered promotion
  vehicle; the paper's strongest possible upgrade is simply waiting for it.
  If it resolves before submission, the paper's tier language changes
  materially in either direction (its falsifier is pre-stated: 2+ small-tier
  family fails kills the headline family claim).
- **H2. Resolve the running Qwen3.5 mid-band cell (local-3090, already
  running).** Hardens: the localization story's generality either way. A pass
  attributes the Qwen3.5 late-site dose collapse to the write site and gives
  the workspace-band account its first cross-substrate support on an
  architecturally distinct (hybrid linear-attention) member; the falsifier
  bounds the mechanism to substrates where a coherent dose window exists.
- **H3. Multi-seed / sampled-decode replication of the gate-and-snap cell
  (local-3090, one evening).** Every resolved snap run is greedy, single
  seed. The program's own precedent (the seed-robustness amendment cited in
  AA/AE: greedy understates effects) makes this the cheapest credibility gap
  to close on the central number. Register fresh seeds and a sampled-decode
  arm on the existing held-out split before flat-asserting the 73.5%/3.1%
  pair anywhere outside "one greedy decode."
- **H4. A registered ungated-vs-gated dose-matched arm (local-3090, small).**
  The "the write is not selective; the gate supplies selectivity" claim
  currently rests on (a) the unregistered dose-200 diagnostic recorded in the
  amendment's Motivation and (b) the permuted-gate placebo, which matches fire
  COUNT, not dose-every-row. A small registered arm that doses all held-out
  rows unconditionally at the same setpoint would let the paper print the
  non-selectivity contrast as a registered number instead of citing
  diagnostic scratch. Cheap and directly hardens the paper's most-quoted
  mechanism sentence.
- **H5. Validate a caution lever on AI-TRUE and re-run the composition
  (local-3090, a few GPU-hours).** The AN section 6 knob screen was designed
  and deferred; AO then showed the two obvious candidates are dead. Running
  the screen (or accepting AO as the answer) converts the AN confound into
  a clean statement either way and hardens the substrate-dependence caveat
  from "one confounded null plus one Stage-1 null" to a characterized
  boundary.
- **H6. The AK gen_stream hook-firing check (CPU + minutes of GPU).** Compare
  logits/hidden states with and without the hook mid-generate(). Until then
  the paper cannot use any answer-window steering evidence; after it, either
  Stage 2 reruns or the confound note becomes a closed instrument bug. Low
  cost, mostly removes a dangling asterisk.
- **H7. Cross-family J-lens localization profiles (cloud-paid or local,
  moderate).** The workspace-band account has a 1000-prompt profile on one
  model and a 12-prompt screening profile on a second (inside the running
  cell). If H1/H2 resolve favorably, a proper profile on the passing families
  is the natural mechanistic companion; without it the paper should keep the
  J-space interpretation clearly marked as one model's characterization.
- **H8. Not needed (the record already satisfies it):** same-model replication
  of the layer contrast (rep1 + rep2 exist and are resolved); a fresh-pool
  replication of the gated snap (rep1/rep2 pools are disjoint from the
  original split by registered dual exclusion); positive-control validation
  of the raw-base caution lever (dark screen G-instrument, 79/80).

## 5. Title candidates

House format, sibling register: "Knows but Doesn't Say", "It's What's on the
Inside That Counts".

The lead's candidate, **"When in Doubt, Don't"**, is strong and I would keep
it as the front-runner: it names the exact mechanism (the doubt readout gates
the intervention; fired rows refuse), it is four words, and it reads positive
(the controller works) rather than negative. Two mild costs: it compresses
away the write/actuation half (a reader could take it for a purely behavioral
abstention paper), and the imperative mood is a small register shift from the
declarative siblings. A subtitle naming the write fixes the first.

1. **When in Doubt, Don't: Doubt-Gated Activation Writes That Turn
   Confabulation into Refusal** (recommended pairing for the lead's idiom)
2. **Hold That Thought: Selective Abstention from Doubt-Gated Caution Writes
   in a Small Language Model** (idiom does double duty: refraining from
   speech and intervening on a thought in flight)
3. **Bite Your Tongue: Installing Selective Refusal with Doubt-Gated
   Hidden-State Writes** (closest to the mechanism: the model is made to
   withhold what it was about to fabricate)
4. **Look Before You Speak: Gating Caution Writes on a Model's Own Doubt
   Readout** (emphasizes the read-then-write control loop)
5. **Saying Isn't Steering: Why Telling a Model Its Own Doubt Fails and
   Writing It Works** (leads with the caveat landscape; only if the PI wants
   the contrast in the title rather than the win)
6. **A Word in the Right Ear: Channel, Gate, and Write-Site Constraints on
   Actuating Epistemic State** (keeps the current subtitle's scope; the idiom
   points at both channel authority and write location)

Avoid keeping "Readable Is Not Writable" even as subtitle material; the
record now shows readable state IS writable under the right gate, site, and
dose, which makes the old title not merely negative but wrong at the margin.

## 6. Voice and structure violations (worst first, one-line fixes)

Read against papers/common/VOICE.md in full, including the newer binding
sections (Synthesis-not-journey, External-facing self-containment, real
headings, never-explain-science-to-scientists).

1. **Bold run-ins throughout** ("**Interpretation.** ...", "**Activation
   writes.** ...", "**alignment:** ..."): banned by "Real headings, not bold
   run-ins." Fix: promote to real subheadings where the block deserves one,
   otherwise fold into prose; the recurring "Interpretation." blocks become
   the closing sentences of their sections.
2. **No registered predictions or kill criteria on the page**: the empirical
   spine section requires both, including misses. Fix: a one-row registered
   fact per experiment (call, result) and one falsifier sentence per headline
   result; rep1 (both wrong) and rep2 (both right) are the natural showcase
   pair.
3. **Internal instrument names in body prose**: `c_hat` (sections 3.2, 4.6,
   and the section 5 table), "signed amendment or experiment-local AMENDMENT"
   (section 3), and the internal-lineage phrase "the inherited L34 write
   site". Fix: "the caution write direction", "a pre-registered experiment",
   "the late-layer write site used in earlier work"; labels live only in the
   provenance appendix.
4. **Journey narration in the results spine** ("The first actuation attempt
   asked...", "The next question was...", "A natural objection is that... We
   therefore tested"): synthesis-not-journey says state what is true and how
   we know, not the order we learned it. Fix: open each results subsection
   with the question it answers, present the controlled number, and cut the
   connective tissue; the reframe's spine ordering does most of this.
5. **Self-containment leak in Appendix A's framing**: the appendix says
   reader-facing prose "should eventually move" labels out; VOICE makes that
   binding now, with repo pointers confined to one provenance appendix. Fix:
   do the conversion in this rewrite, not eventually.
6. **Terms of art not all defined at first use**: "erase-write", "anchor",
   "hs=23" indexing, and "clean tightening" arrive before or without their
   plain-language definitions ("clean tightening" is defined only in section
   3.3 after being used in the abstract). Fix: one inline definition each at
   first body use; the abstract may use plainer words ("converted into
   well-formed refusals").
7. **Missing long-then-short rhythm and the falsification bookends**: the
   introduction never states what would have falsified the thesis, and the
   conclusion does not state what still could (the cross-family panel's
   pre-stated falsifier is sitting right there). Fix: one sentence each.
8. **Hedge audit is otherwise clean**: no em dashes found, no "load-bearing",
   no banned hedge stacks; "The evidence remains exploratory" fencing is the
   house style and should survive the reframe.

## 7. Provenance notes for the rewriter

- Rep2's known-correct side reuses rep1's 1,957 rows and anchors verbatim
  (pre-stated in its Design); its cost numbers are therefore not independent
  of rep1's on that side. Say "fresh confab pool, reused known-correct pool"
  if both are quoted.
- Rep2 contains 42 dataset-native duplicate normalized questions among 221
  confabs; the doc's sensitivity collapse leaves the verdict unchanged
  (McNemar p ~ 1.9e-9). Carry the disclosure if the row count is printed.
- The doubt-gated-caution-tighten G2 pool was power-fixed by pre-sign mining
  (89 to 430 known-correct rows); the mining is documented in the signed doc
  and is not a post-hoc change.
- AE's STOP means the paper should not claim the raw base "confabulates
  freely" on SelfAware under an abstention-affording prompt; it abstains
  ~93% there. The confab-rich surfaces in the snap experiments are mined
  pools, and one sentence should say so.
- AB retroactively invalidated one AA dial instrument (revision detection
  saturated in AA-7 as well); if AA's dial-side nulls are quoted, quote them
  through AB's corrected reading (decision-level flows flat), as the AB
  section 8 note requires.
