# caution-install-bounded-site-sweep notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-08 - Seventh site hs35 added pre-sign by lead adjudication of N2

The lead accepted Registration note N2 and independently verified its evidence,
so the registered search space is now seven write sites rather than six. Added:
**hs35, decoder block 34, relative depth 0.972**, the site the historical
`caution_direction_L35` hooks.

Verified evidence, one line: `c_hat_hs34.json` and `c_hat_L34.json` both carry
`layer: 33` with sigma 13.23002622164185, so the program's inherited site hooks
block 33, while
`archive/experiment/phase1/probe/steering/build_equiv_direction.py` documents
`block = layer - 1` and sets `best_layer = block`, so `caution_direction_L35`
hooks block 34, one block later. Without hs35 the sweep would not cover the site
whose claim it revises.

Files touched: `cell.yaml` (site added to the trained substrate's site list and
to the sites block, the not-registered comment removed, A_lin scope now seven
sites), `AMENDMENT.md` (Axis 1 table and prose, A_lin control, falsifier
searched-space sentence, the no-site-outside-the-registered clause, run plan
stage 2, budget section, D1 combination count, D3, N2), `gates.yaml` (new
`registered_sites` block enumerating the space the gates are scored over),
`experiment.yaml` (question). `TODO.md` is untouched; N1 remains the lead's to
apply.

Budget revised from 15 to 25 GPU hours to **16 to 26**, about 23,200
generation-equivalents up from about 21,900. The seventh site adds roughly
1,300, about 6%, because only the smoke, calibration, and held-out ladder stages
scale with site count; mining, extraction, controls, and pair count do not.

The feasibility probe is unaffected. It measures corpus yield and generation
throughput on the trained checkpoint and never touches a site: it loads no
direction, installs no hook, and its pass criterion is a function of role counts
and corpus size only. `feasibility_probe.yaml` was not edited.

hs34 and hs35 are adjacent by construction. They are reported as two distinct
reference sites and never as a swept span, since single-block resolution is not
claimed anywhere in this design.

The experiment was and remains draft and unsigned, so this is a pre-registration
refinement rather than a change to a signed space.

### 2026-08-08 - Pre-registration of the pre-sign feasibility probe (tier 3, BLOCKS SIGNING)

Instrument config: `feasibility_probe.yaml` (pinned at signing alongside
`cell.yaml` and `gates.yaml`).

**Tier and why.** Tier 3, lab notebook, per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`. Decision
question 3 routes preflight and diagnostic work to the lab notebook, and the
routing table places a preflight for a cell at tier 3. The same reference's
section "Pre-sign feasibility probe: every arm must be constructible from real
data" makes this specific check mandatory before signing, and records that it is
allowed and required even under a self-blinding rule, because self-blinding
forbids computing the result before signing and does not forbid confirming that
an arm can be built. That section also names the failure this rule exists to
prevent: the M4 cell defined an arm consuming a field that did not exist on its
test population, and the gap survived both signing and a full pre-sign red team
because nobody checked coverage.

**What is in doubt.** The main cell's G0a requires 150 held-out confab rows and
250 held-out known_correct_answered rows on the trained clean-SFT to GRPO-v2
checkpoint. That checkpoint over-refuses. A checkpoint that refuses may
confabulate too rarely to fill a confab pool, and may answer answerable
questions too rarely to fill a known-correct pool. Role labels are
behavior-dependent and cannot be ported from the raw-base pool
(`.skills/mechinterp-cells/reference/read-then-actuate.md`, section 1.1), so the
existing raw-base counts say nothing about this substrate. Both populations are
therefore at risk and both are probed.

**Blinding boundary, stated before the run.** The probe may compute role counts
and rates, corpus inventory counts, capture rate, and generation throughput. It
may not compute any steered quantity, any direction fit, any gate AUC, any tau,
any tighten rate, or any AUROC. Computing any of those would consume the main
cell's blind, and the probe's outputs would stop being coverage.

**Arms.** One. An undosed baseline: unsteered greedy generation, graded for role
labels. No direction is loaded and no hook is installed anywhere in this probe.

**Stages.**

| Stage | Device | What it does | Output |
|---|---|---|---|
| A, corpus inventory | CPU | counts available gold-unanswerable rows (M_u) and gold-answerable rows (M_a); verifies zero overlap with the training pools consumed by this lineage | `analysis-committed/probe_corpus_inventory.json` |
| B, role yield | GPU | draws 400 gold-unanswerable and 400 gold-answerable rows uniformly without replacement at seed 20260707, generates undosed, grades roles, records throughput | `analysis-committed/probe_role_yield.json` |

Stage B's generation contract is identical to the main cell's
`surface.generation`, so role labels come from the same instrument the main cell
will use. The role read policy is asserted as first-JSON rather than inherited,
because the grader can read the whole completion and let trailing prose reach a
role label; the gemma family atlas recorded 22 of 2815 split rows disagreeing
between the two reads.

**Why n = 400 per population.** The Wilson 95% half-width at n = 400 is about 4.0
points at p = 0.20 and about 2.1 points at p = 0.05, which is enough precision to
decide whether the corpus can supply the required pool. Drawn rows are recorded
by id so the main cell's Stage 1 mining reuses these generations rather than
repeating them, which makes the probe cost recoverable rather than additional.

**Token budget.** 800 rows at `max_new_tokens` 200 with `min_new_tokens` 1, so a
worst case of 160,000 new tokens and a realistic figure well below that, since
well-formed JSON answers terminate early.

**GPU minutes: 20 to 45, estimated.** This is an engineering estimate, not a
governed number: no governed document in this repository records wall-clock for
the predecessor cells, so no measured rate exists to cite. The estimate assumes
batched greedy generation of a 4B bf16 model on the local 3090 at roughly 25 to
50 rows per minute, plus one model load. Stage B is instrumented to record its
own measured rows-per-minute and mean new tokens precisely so this estimate can
be replaced by a measurement, both here and in the main cell's run plan.

**Pass criterion, fixed before the run.** Derivation: FIT_FRAC is 0.40, so
held-out is 60% of a pool; 150 held-out confab requires 250 total, and 250
held-out known-correct requires 417 total.

| Check | Expression | Direction |
|---|---|---|
| P1 confab supply | `wilson_lower_95(confab / 400) * M_u >= 250` | floor |
| P2 known-correct supply | `wilson_lower_95(known_correct / 400) * M_a >= 417` | floor |
| P3 capture | answer capture rate on probed rows `>= 0.90` | floor |
| P4 disjointness | training-pool overlap count `== 0` | equality |

The Wilson lower bound is used rather than the point estimate, so the probe
passes only if the corpus supplies the pool at the pessimistic end of the
estimate. P3 is the atlas AG0a bar: a checkpoint that cannot be cleanly mined
stops here.

**Disposition.** All four checks pass: signing of the main cell is unblocked,
and the measured throughput replaces the engineering estimate in the AMENDMENT
run plan. Any check fails: the main cell is not signed in its current form, the
counts are recorded here, and the lead chooses among narrowing the cell to the
raw-base substrate, enlarging or changing the corpus, or recording the transfer
question as unaskable on this checkpoint. The registered pool floors are not
lowered to obtain a pass.

**Containment.** Committed outputs are counts, rates, intervals, and throughput
only. Question text, aliases, gold answers, and generations stay under the
gitignored `analysis/` directory.

### 2026-08-08 - Draft registration filled

`AMENDMENT.md`, `experiment.yaml`, `cell.yaml`, `gates.yaml`, and
`feasibility_probe.yaml` filled from the session design draft (docs/preparation working file, not a
tracked artifact; superseded by this registration), under the lead's
adjudicated decisions: corrected transfer framing, substrate option (c), the
six-site search space, feasibility probe required and blocking, and the
superseded disposition for the un-re-derivable paper 3 section 6 citation.
Status stays draft. Three design questions were resolved at registration and are
recorded in `AMENDMENT.md` under "Design decisions at registration": calibration
pool size (D1), gate site co-located with write site (D2), and site naming
across the two index conventions (D3). Two items need the lead and are recorded
under "Registration notes for the lead": the burn-down row 27 wording (N1) and
the finding that the historical write site is one decoder block later than the
program's inherited site and therefore sits outside the adjudicated search space
(N2).
