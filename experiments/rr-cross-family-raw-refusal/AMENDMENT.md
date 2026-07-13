# rr-cross-family-raw-refusal

Status: draft (not signed; do not launch). Predictions scoreboard intentionally
empty; it is filled by the PI and lead at sign.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`doubt-snap-cross-family-confirmatory` (resolved 2026-07-12, confirmatory claim
NOT promoted; `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`
lines 3, 252) launched four cells and stopped every one of them at the
registered pre-outcome FIT dose-viability rule at a single blindly ported write
site: the layer rule `round(0.94 * (num_hidden_layers - 1))`, copied from
Qwen3-4B's L34 to every family without per-family tuning (same doc lines
157-158). Its Outcome names two pieces of evidence that separate "the mechanism
does not transfer to these families" from "the registered write site is wrong":

1. A read-actuate dissociation at the ported late site (same doc lines
   307-319). The registered caution direction `c_hat` reads refused-vs-confab at
   0.84 to 0.99 AUROC in all four families, and a raw mass-mean
   refused-vs-answered direction reads 0.997 to 1.000 everywhere, yet the same
   write moves behavior strongly only on Qwen3 lineage, weakly on llama, and not
   at all on mistral. The encoding is present and linearly readable in every
   family; pushing it at the late site does not actuate refusal outside Qwen.
   The mistral cell is a true behavioral null on a correctly bracketed grid: the
   write visibly moves tokens (at dose 30, 11/876 fired answers identical to
   baseline, 638/876 well-formed) yet fired-confab conversion is 0/874 at every
   dose (same doc lines 273-278).
2. A within-substrate mid-band success. On Qwen3.5-4B the same instrument class
   at mid-band layer hs20 (dose 8 x sigma_c) reaches refused 0.684 with
   well-formed 0.980 and known false-refusal 0.042 in-sample FIT, where the late
   site (hs30) peaks at 0.326 (same doc lines 320-329;
   `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 301-318).

The confirmatory Outcome states the successor design requirement directly (same
doc lines 331-339): any successor cross-family actuation amendment should site
its writes per family from the atlas layer map, and must register
exterior-shaped outcomes in both prediction and falsifier so a uniform FIT-stop
cannot fall between them again. This experiment is that successor.

`jspace-family-atlas` (resolved 2026-07-12;
`experiments/jspace-family-atlas/AMENDMENT.md`) supplies the per-family map. It
is a READ-ONLY mapping experiment: no steering, no interventions, no behavioral
outcomes (same doc lines 28-32), and it names the raw-refusal-axis design as one
of its dependents (same doc line 32). What the atlas established: for
Llama-3.2-3B and Mistral-7B-v0.3, an interior layer band where doubt, caution,
and raw refusal all read at held-out AUROC >= 0.80 (llama layers 15-23, mistral
7-27; same doc line 158), with the best simultaneous three-axis read at llama
~L20-23 and mistral ~L15-17, handed explicitly to any future per-family
actuation amendment (same doc lines 184-185). The raw-refusal read axis itself
peaks at 0.90 on llama L20-25 and 0.925 on mistral L15-17 (same doc lines
178-182). What the atlas did NOT establish: any actuation, steering, or
behavioral result whatever, and its registered eff_dim_frac prediction FAILED
(the profile peaks early, llama L4 and mistral L3, not interior; same doc lines
151-154). The atlas proved these sites are READABLE; whether a write at them
ACTUATES refusal is untested and is exactly this experiment's question.

Core question: does a doubt-gated caution write actuate raw refusal on the
non-Qwen families when written at their OWN atlas-located workspace-band sites,
rather than at the ported late site the confirmatory indicted?

Posture: exploratory Tier-2 cross-family actuation, reported separately from the
locked Phase 1 headline matrix and never pooled with it, and never pooled with
the resolved `doubt-snap-cross-family-confirmatory` fleet (which used a
different, ported write site and is resolved not-promoted). Each family is
scored independently. A pass on a family promotes an in-sample-selected,
held-out-confirmed actuation claim about that family at its atlas site; it is
not a headline family claim beyond that.

### Why the primary metric is raw refusal, not clean_tighten

The confirmatory measured a strict conjunction (`clean_tighten`: confab
converted to a well-formed refusal). That conjunction hides the read-actuate
question, because at a write site where refusal and JSON well-formedness are
entangled a zero can mean either "refusal did not move" or "refusal moved but
output also collapsed." The mistral late-site null is exactly this ambiguity,
resolved only by a separate token-movement check
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 273-278).
The Qwen3.5-4B mid-band ladder resolved it by registering refusal and
well-formedness as SEPARATE readouts:
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 218-227 register
(a) the strict `clean_tighten`, (b) a format-agnostic stated-confidence refusal
rate `refused`, (c) well-formed rate, plus degenerate, natural-stop, and mean
new tokens. This experiment adopts that governed metric split verbatim: the
PRIMARY metric is the format-agnostic stated-confidence refusal rate `refused`
on fired confabs (does the write actuate refusal at all at the atlas site), and
well-formed rate is reported and gated ALONGSIDE it (is that refusal clean).
This is the cleanest available test of the read-actuate dissociation: at the
site where the atlas says the refusal axis is maximally readable, does pushing
it produce refusal behavior.

## Design

### Substrates (the atlas-mapped models, at fleet-pinned revisions)

The write must land at each family's OWN atlas-located site, so the substrates
are exactly the two models the atlas mapped, at the exact HF revisions pinned in
the fleet's `model_matrix.yaml` and reused by the atlas
(`experiments/jspace-family-atlas/AMENDMENT.md` lines 40-41):

- `unsloth/Llama-3.2-3B-Instruct` (28 decoder layers; the atlas reports 29
  hidden states, `experiments/jspace-family-atlas/AMENDMENT.md` line 141).
- `mistralai/Mistral-7B-Instruct-v0.3` (32 decoder layers; the atlas reports 33
  hidden states, same line).

Both are standard causal-LM substrates for the registered raw-text activation
write path. The confirmatory's Mistral-family loader-eligibility problem (the
`Mistral3ForConditionalGeneration` conditional-generation architecture is not a
causal-LM substrate, `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`
lines 43-47) does not apply to `Mistral-7B-Instruct-v0.3`, which the fleet and
atlas both loaded as a causal LM. The exact revision hashes are transcribed into
`cell.yaml` from the fleet `model_matrix.yaml` at sign and byte-checked at G0.

Open adjudication (A1, lane sizing versus atlas coverage): the lead's lane note
sized an 8B llama, but the atlas mapped `Llama-3.2-3B-Instruct`, not an 8B
llama, and there is NO atlas-located site for any 8B llama (the confirmatory's
Llama-3.1-8B mid-tier cell was never launched or mapped). Honoring "written at
their OWN atlas-located workspace-band sites" therefore requires the 3B llama.
An 8B llama cell would need an atlas extension run first. This draft uses the 3B
llama; see A1 in the open-adjudications list handed to the lead.

### Atlas-located write sites (per family)

Write-site candidates are read from the atlas layer map, not ported. The atlas
hands the best simultaneous three-axis read as llama ~L20-23 and mistral ~L15-17
(`experiments/jspace-family-atlas/AMENDMENT.md` lines 184-185), and the
raw-refusal read axis (this experiment's target axis) peaks at llama L20-25 and
mistral L15-17 (same doc lines 178-182). The Qwen3.5-4B ladder additionally
found refusal potency monotone toward EARLIER layers within a workspace band
(hs20 > hs23 > hs26 > hs30;
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 320-321), so among
comparably-readable atlas layers the earlier ones are the more likely to
actuate.

Registered candidate layer set (small, capped at 3 per family to bound cost,
inside the atlas best-read band and leaning earlier per the potency finding):

- llama: `{20, 22, 23}` (atlas best simultaneous read L20-23; raw-refusal axis
  peak L20-25).
- mistral: `{15, 16, 17}` (atlas best simultaneous read and raw-refusal axis
  peak L15-17).

The atlas hidden-state index convention (hidden-state index versus decoder-block
index) is pinned at sign from the atlas's committed `atlas_summary.json` so the
write hooks the intended decoder block; the harness-build assignment records the
exact index mapping. FIT selects a single (layer, dose) operating point per
family from this set (see dose policy); held-out scoring runs only at the
FIT-selected operating point.

### Instrument (same mechanism class as the governed precedent, new site)

The instrument is the doubt-gated caution snap, identical in construction to the
confirmatory and the Qwen3.5-4B ladder, differing only in the per-family write
layer:

1. GATE: a doubt readout `z_d`, fired as `neg_z_d = -z_d >= tau` because
   confabulations have low doubt; `tau` is fit with Youden-J on FIT confab
   versus known-correct rows only
   (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
   145-147).
2. SNAP: fired rows receive an erase-and-write intervention along the
   model-local caution direction `c_hat`, scope `anchor_onward`; non-fired rows
   receive no write (same doc lines 149-151). `c_hat` is the mass-mean caution
   direction (mean refused minus mean confab) orthogonalized against a
   `LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000, random_state=SEED)`
   confab-propensity direction with a QR erase, and doubt and snap projections
   are standardized on FIT, exactly as
   `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 163-167.
3. GEN: EOS-enabled greedy JSON generation, `min_new_tokens=1`,
   `max_new_tokens=200`, `enable_thinking=False` where the family exposes it
   (same confirmatory lines 151-153).

Nothing is refit that can be reused. Directions, gate, and standardization are
fit fresh at the atlas sites (no such fit exists for llama/mistral mid-band; the
atlas fit READ directions only, and the confirmatory fit the instrument only at
the ported late site), but every FIT fit is run twice and asserted
byte-identical before any artifact is written, mirroring the confirmatory's
direction-reproducibility rule and the ladder's `fit_byte_identical`
(`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 176-178).

### Data reuse (no re-mining, no re-generation)

Row pools, baseline generations, gradings, and role assignments are reused
VERBATIM from the fleet's `llama32_3b_instruct` and `mistral7b_instruct_v03`
cells, which the atlas already established are volume-backed and reusable without
re-mining or re-generation (`experiments/jspace-family-atlas/AMENDMENT.md` lines
40-41). Populations follow the confirmatory's behavior-defined roles: answerable
candidates from TriviaQA and PopQA enter `known_correct_answered` only if the
undosed baseline answer is well-formed and correct; unanswerable candidates from
KUQ enter `unknown_refused` or `confab` by undosed baseline behavior
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 170-178).

Anchor hidden states at the atlas candidate layers are reused from the atlas's
committed full-depth captures where available (the atlas captured every decoder
layer at the final-prompt-token anchor for every row in each cell's split
manifest, with FIT/held-out labels carried through;
`experiments/jspace-family-atlas/AMENDMENT.md` lines 47-52, coverage 1.00 in both
cells, same doc lines 136-140), so direction fitting and the fired-set readout
consume existing anchors and only the dosed generation is new GPU work. The
harness-build assignment verifies the atlas capture covers the exact candidate
layers and, if a candidate layer is missing, re-captures only that layer's
anchors under the atlas convention.

Held-out power is inherited from the atlas/fleet cells and re-checked at G0:
llama held-out known 334 and confab 872, mistral known 382 and confab 1312
(`experiments/jspace-family-atlas/AMENDMENT.md` lines 136-140), both clearing the
confirmatory's held-out floors (confab >= 150, known-correct >= 250;
`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` line 176).

Containment: public commits carry ID-only manifests (row_key, role, split,
source, category_canon) and aggregate summaries only, never question text, answer
aliases, or generation text, matching the confirmatory and ladder containment
rule (confirmatory lines 176-178; ladder
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 104-113). The
`.gitignore` excludes `directions/` and `analysis/`.

### Dose policy (per family, with a pre-stated dose-viability leg)

Absolute readback units are not comparable across families, and the confirmatory
proved that even a sigma-relative mapping is only a first guess: mistral was
inert at 29 sigma while llama fired at comparable sigma, so per-cell empirical
bracketing is required before any grid is trusted
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 130-134).
The dose policy therefore has three registered parts:

1. Registered sigma-relative grid. Per (family, candidate layer), the dose grid
   is `{2, 4, 6, 8, 12, 16, 20} x sigma_c`, with `sigma_c` taken from that
   layer's fresh FIT `build_manifest.json`. This is the exact grid the
   Qwen3.5-4B ladder registered and on which the hs20 window was found
   (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` line 260). The grid
   is finalized in absolute units at sign, once FIT `sigma_c` is known, and
   never changed after any held-out outcome.
2. Pre-sweep empirical token-movement bracketing (per family). Before the FIT
   dose sweep runs, a fixed-strength gen-stream probe checks that the grid's
   strongest arm actually moves tokens on probe rows. If the strongest arm
   produces byte-identical output (the mistral signature, confirmatory lines
   114-141), the grid is below the family's token-movement threshold and is
   re-bracketed pre-sweep and pre-outcome to log-span the empirically bracketed
   response region, exactly as the confirmatory re-bracketed mistral. This is
   the ONLY permitted grid change, it can happen only pre-sweep and pre-outcome,
   and it never happens after a held-out outcome is known.
3. FIT dose-viability selection (the early-stop leg). The selected operating
   point per family is the (layer, dose) with the LOWEST dose whose FIT
   fired-confab `refused` >= 0.60 AND well-formed >= 0.80 AND FIT known-correct
   false-refusal <= 0.10. These FIT floors mirror the ladder's own in-sample G1
   conjunction (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines
   270-272) and the confirmatory's FIT dose-selection rule
   (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
   164-167). If NO (layer, dose) in the bracketed grid qualifies, the family
   fails FIT dose viability and is recorded as outcome shape F (see the coverage
   table); it is not silently stopped, and no grid changes afterward. This is the
   leg that stops an arithmetically unreachable prediction before the held-out
   budget is spent, and it is a NAMED exterior outcome shape rather than an
   off-table stop, which is the specific fix the confirmatory Outcome demanded
   (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
   331-339).

### Arms (four: baseline, gated primary, one placebo, one selectivity control on knowns)

Held-out scoring runs four arms per family at the FIT-selected operating point:

- `baseline`: no hook, generated once over the full held-out pool. Establishes
  undosed refusal and well-formed rates (expected near zero refusal on both
  roles, as every governed precedent observed) and is the reference for the
  G3(i) placebo comparison.
- `gated`: the real instrument. The doubt gate fires per held-out row; fired
  rows receive the `c_hat` erase-write snap at the frozen FIT-selected dose,
  `anchor_onward`; non-fired rows inherit baseline. This arm yields the primary
  `refused` and well-formed rates on fired confabs and the known-correct cost.
- `random_direction`: the same fired rows as `gated`, writing a frozen random
  placebo direction at a magnitude matched to the gated arm's realized
  projection. Isolates direction specificity. This is the confirmatory G3(i) and
  the ladder scope-statement-4 placebo
  (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 181-186,
  237-239; `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines
  348-352). Note the atlas found a norm/position confound inflates the random
  direction's READ AUROC at this anchor (up to ~0.97 on refused-vs-known;
  `experiments/jspace-family-atlas/AMENDMENT.md` lines 170-173), but G3(i)
  compares behavioral refusal RATE, not read AUROC, so the placebo comparison is
  unaffected by the read confound; the ladder observed this arm at about zero
  refusal (0.005 at its G1 cell).
- `dose_knowns_ungated`: the selectivity control on knowns. Every held-out
  known-correct row is dosed unconditionally along `c_hat` at the same frozen
  dose, gate off. This directly measures whether the WRITE is content-selective
  on knowns at this family's mid-band operating point.

Placebo/control choice and its honest scope. The confirmatory and ladder used a
`permuted_gate` arm (fire-count matched, random rows) as the gate-selectivity
placebo (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
184-186, 240-241). The ladder's red-team then established, in its binding scope
statement 3, that the confab/known selectivity belongs to the `c_hat` WRITE
direction's content dependence, not to the doubt gate: permuted-gate dosed
confabs refused at 0.669 versus the gated arm's 0.684, while directly dosed
knowns refused at only 0.056, so the gate's operational role is limiting how many
knowns get dosed, not creating the refusal selectivity
(`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 342-347). H4
(`experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`, ALL GATES PASS
2026-07-13) then showed this write content-selectivity is
OPERATING-POINT-DEPENDENT: at the resolved Qwen3-4B / L34 / dose-200 instrument
the write is NON-selective (dosing every known damaged 155/258 = 60.1% versus
3.1% gated; H4 lines 185-188), whereas at the Qwen3.5-4B mid-band operating point
directly dosed knowns refused only ~5.6%, so the write IS content-selective there
(H4 lines 206-215, binding scope statement 2). Because llama and mistral mid-band
are a THIRD, unmeasured operating point, we cannot assume either regime. The
`dose_knowns_ungated` arm measures the write's content-selectivity on knowns
directly per family rather than inheriting a value from a different substrate,
site, and dose. It is the more directly motivated selectivity-on-knowns control
than `permuted_gate` at this operating point, which is why it is the registered
fourth arm; whether to ALSO add `permuted_gate` is open adjudication A3.

Honest-scope statement carried into the design (H4 binding scope statement 1,
`experiments/ungated-vs-gated-dose-matched/AMENDMENT.md` lines 196-203): the
`dose_knowns_ungated` arm's damage indicator, if reported as
not-well-formed-correct, is BROADER than refusal and must not be reported as a
refusal rate. This experiment reports the arm's known-correct clean false-refusal
rate (comparable to the gated cost) and its total damage rate SEPARATELY, and
never conflates them, exactly as H4 requires.

### Execution

Modal-first, mirroring the confirmatory execution model
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 188-202):
one detached function per family cell, baseline generation and hidden-state reuse
via the existing Synaptic-Tuner batch verbs, and activation writing via the
generic tuner `mechinterp steer` cell, with restartable per-cell configs so a
failed arm relaunches without rerunning the matrix. A local RTX 3090 lane is
viable too (both models fit bf16 in 24GB); see Lane and cost. The exact
Synaptic-Tuner submodule pin (carrying the batch verbs, config-first mechinterp
cells, batched steer generation, and `shared/utilities/run_log.py`) is set at the
harness-build assignment. A sequential-versus-batch parity smoke and a real
`mechinterp steer` plus readback smoke on the quickest eligible cell run before
any full held-out scoring, mirroring the confirmatory harness-smoke discipline
(same doc lines 61-65, 202).

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, and the harness
modules (materializer, direction-fit, dose-ladder runner, held-out scorer, render
and grader adapters, Modal wrapper). No harness code is written by this drafting
assignment; the harness build is a separate assignment gated on this draft's
review.

## Prediction

The doubt-gated caution write actuates clean raw refusal at the atlas-located
workspace-band site on at least one of the two non-Qwen families. Concretely: at
least one of {llama, mistral} reaches outcome shape A, meaning its FIT-selected
operating point survives held-out with fired-confab `refused` >= 0.60 (Wilson 95%
lower CI > 0.50) AND well-formed >= 0.80, with known-correct false-refusal <= 0.05
(Wilson 95% upper CI < 0.10) over the full held-out known-correct population, and
with the `random_direction` placebo a no-op relative to baseline (within 2 points
on both populations). This is outcome shape A in the coverage table.

The refused floor 0.60 with Wilson LCB > 0.50, the well-formed floor 0.80, and the
cost floor <= 0.05 point with Wilson UCB < 0.10 are the governed Wilson-bounded
thresholds: the fleet G1/G2
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 233-235),
the ladder G1 refused/well-formed conjunction
(`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 270-272), and the
held-out-stage Wilson template
(`experiments/qwen35-4b-midband-heldout/AMENDMENT.md` lines 262-269). The governed
effect-size reference is the resolved Qwen3-4B exploratory G1 clean_tighten
136/185 = 73.5% (Wilson LCB 66.7%) with G2 known-correct false-refusal
8/258 = 3.1% (Wilson UCB 6.0%)
(`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 14-16),
cited as calibration only and never pooled.

## Falsifier

The claim that the doubt-gated caution write actuates clean raw refusal at
atlas-located non-Qwen sites is falsified if NEITHER family reaches shape A: that
is, both families land in shapes B, C, D, E, or F below. Each of B through F is a
distinct, pre-named way the write can fail to actuate clean refusal at the atlas
site, and shape F specifically covers the confirmatory's uniform-FIT-stop
territory (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines
293-301, 331-339) so no result can land off the table again. Each family is
scored independently and its shape recorded straight; the amendment-level verdict
is PROMOTE if at least one family is shape A, else NOT promoted.

### Outcome-shape coverage (every family maps to exactly one shape before launch)

| Shape | Per-family condition | Verdict for that family |
|---|---|---|
| A | held-out fired-confab `refused` >= 0.60 with Wilson LCB > 0.50 AND well-formed >= 0.80 AND known-correct false-refusal <= 0.05 with Wilson UCB < 0.10 AND G3(i) no-op | ACTUATES cleanly: promote an atlas-site actuation claim for that family (prediction met) |
| B | a FIT-viable dose existed, but held-out `refused` < 0.60 OR `refused` >= 0.60 with Wilson LCB <= 0.50 | NOT promoted: refusal does not transfer to held-out with the required confidence (falsifier) |
| C | held-out `refused` leg clears AND well-formed < 0.80 | NOT promoted: refusal actuates but output corruption returns, so the decoupling does not hold (falsifier) |
| D | held-out `refused` and well-formed legs clear AND (known-correct false-refusal > 0.05 OR Wilson UCB >= 0.10) | NOT promoted: actuates refusal but is not cost-safe out of sample (falsifier) |
| E | confab and cost thresholds clear BUT `random_direction` is not a no-op (refusal moves > 2 points from baseline on either population) | NOT promoted: refusal is not specific to the caution direction, so it is not attributable to the instrument (falsifier) |
| F | no (layer, dose) in the bracketed FIT grid meets the FIT dose-viability floors (fired-confab FIT `refused` >= 0.60 AND well-formed >= 0.80 AND FIT known false-refusal <= 0.10) | NOT promoted: the write does not actuate clean refusal at the atlas site even where the axis is maximally readable, confirming the read-actuate dissociation at the correct site (falsifier) |

Shapes A through F are exhaustive and mutually exclusive over a family that clears
G0 instrument validity: F captures the FIT-side non-actuation (the confirmatory's
stop territory, now on the table), and A through E partition the held-out surface
reached only when a FIT-viable dose exists. A G0 instrument-validity failure
(loader, FIT AUC, reproducibility, held-out power, parity smoke, containment) is a
pre-outcome stop recorded as such, not a held-out verdict, and does not appear as
a shape.

The `dose_knowns_ungated` arm does not define a promotion shape; it is a
characterization reported with a pre-stated reading (below) so its result cannot
be spun after the fact.

Pre-stated reading of the selectivity control on knowns (per family, reported not
gated): if `dose_knowns_ungated` known-correct clean false-refusal is LOW (the
write spares most directly dosed knowns), the write is content-selective at this
family's atlas operating point, matching the Qwen3.5-4B mid-band regime; if it is
HIGH (dosing knowns damages most of them), the write is non-selective and the
gate is what supplies selectivity, matching the Qwen3-4B / L34 / dose-200 regime.
Either reading is scoped to this family, site, and dose only, per H4 binding scope
statement 2 (`experiments/ungated-vs-gated-dose-matched/AMENDMENT.md` lines
206-215).

## Gates

Per-cell gates are in `gates.yaml`. Wilson 95% CIs (alpha 0.05) are reported on
every rate, per the PI's standing Wilson-bound preference.

- G0 (instrument validity and FIT dose viability; pre-outcome stop, not a
  held-out verdict). Loaders resolve both substrates at the pinned revisions via
  the causal-LM path; FIT gate AUC >= 0.90 at each candidate layer (governed
  reference: the confirmatory G0 AUC floor,
  `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 228-231);
  direction refits byte-identical; anchor coverage (reused atlas captures) covers
  every FIT and held-out row at each candidate layer; held-out power floors hold
  (confab >= 150, known-correct >= 250); the pre-sweep token-movement bracket
  passes or triggers the one permitted pre-sweep re-bracket; a FIT dose-viable
  (layer, dose) exists (else the family is recorded as shape F); the
  batched-versus-sequential parity smoke passes; and no question text, aliases, or
  answer text appear under `analysis-committed/`.
- G1 (primary held-out gate). On fired held-out confabs: `refused` >= 0.60 with
  Wilson 95% lower CI > 0.50, AND well-formed >= 0.80, simultaneously. Cost gate:
  known-correct false-refusal over the full held-out known-correct population
  <= 0.05 point estimate with Wilson 95% upper CI < 0.10, with the fired-known
  conditional false-refusal reported alongside (mirroring the ladder cost-gate
  handling, `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 330-334,
  where the system-level 10/240 = 0.042 hid a fired-known conditional 10/13 =
  0.77). Baseline refusal on both roles reported (expected near 0).
- G3(i) (placebo, direction specificity). The `random_direction` arm's refusal
  rate is within 2 points of baseline on BOTH held-out populations
  (`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 237-239).
- Selectivity-on-knowns characterization (reported, not a promotion gate). The
  `dose_knowns_ungated` arm's known-correct clean false-refusal rate and total
  damage rate are reported separately (H4 metric-hygiene rule,
  `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md` lines 196-203) with the
  pre-stated reading above. Whether the PI elevates this to a hard gate is open
  adjudication A4.

## Lane and cost

Two lanes; any PAID launch (Modal, or any cloud) needs fresh user approval at
staging time.

- Local RTX 3090 (free). Both models fit bf16 in 24GB (Llama-3.2-3B and
  Mistral-7B-v0.3). Generation volume, per family: a FIT dose ladder over 3
  candidate layers x 7 doses on fired FIT confabs (order 10^2 to 10^3 fired rows
  per layer) plus the FIT known-correct cost population, then a single held-out
  operating point x 4 arms over the held-out pool (llama held-out 872 confab + 334
  known; mistral 1312 confab + 382 known). Order-of-magnitude total is a few x
  10^4 generations per family. These are standard-attention models, so throughput
  is far higher than the Qwen3.5-4B hybrid-linear-attention reference of ~21
  generations/min at batch_size 8
  (`experiments/qwen35-4b-midband-heldout/AMENDMENT.md` lines 159-168); the exact
  wall-time estimate is produced at the harness-build assignment once the fired
  counts and batch size are fixed. The FIT ladder is the larger cost; the held-out
  pass is one dose and one layer.
- Modal (paid). One detached A10G or A100 function per family cell, batch verbs
  for baseline and capture reuse, `mechinterp steer` for the writes, per the
  confirmatory execution model. Order-of-magnitude one GPU-hour per family cell on
  A10G at ~USD 1.10/hour, so a small number of USD for both cells; the exact figure
  is presented for approval at staging. PAID launch requires fresh user approval.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Exactly ONE family reaches shape A (lean mistral), the other lands in B or F: mid-band siting rescues actuation somewhere outside the Qwen lineage, but not uniformly; the confirmatory's family-deep silence at late sites is partly site-explained and partly not. (recorded 2026-07-13) |
| user | BOTH families reach shape A: the late-site failures were a wrong-site artifact and the ladder's mid-band actuation generalizes across families; promote both. (recorded 2026-07-13) |

## Outcome

Filled at resolve. Record, per family, the shape (A through F) that occurred, the
gate results (G0 / G1 / G3(i)) with Wilson CIs on every rate, the FIT-selected
(layer, dose), the fired held-out counts, the row-level decoupling count (fired
confabs simultaneously refused and well-formed), the `random_direction` readback
and refusal rates, the `dose_knowns_ungated` known-correct false-refusal and
total-damage rates with the pre-stated reading applied, and the one-sentence
summary that also goes into `verdict:` in the manifest.
