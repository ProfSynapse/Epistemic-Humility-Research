# GRPO Three-Seed Confirmatory Block

Status: **DRAFT — NOT SIGNED. Do not launch.** Signing requires the PI's explicit
approval and is performed by the lead. Nothing in this document authorizes a GPU
launch, a commit of results, or a publication.

Machine state lives in `experiment.yaml`; the pre-stated thresholds live in
`gates.yaml`; the per-seed matrix lives in `cell.yaml`. Nothing is duplicated
here.

---

## Motivation and posture

Every GRPO number currently in the response-confidence track comes from a single
seed. The DPO and KTO layers of paper 2 carry three-seed intervals; the GRPO
layer does not. This experiment closes that asymmetry by rebuilding the entire
GRPO-touching lineage at two fresh seeds (2 and 3), so that every GRPO arm paper
2 reports carries a three-seed interval computed the same way as its DPO and KTO
siblings.

The three-seeds-per-arm bar is not invented here. PROTOCOL v0.3 §3.1 fixes the
4B headline at "3 seeds per arm at the pre-registered default config (9 runs)"
and states the reason explicitly: it exists "to directly answer the field's
one-config / no-error-bars problem that paper 1 documents"
(`archive/docs/protocols/phase1/PROTOCOL.md:76-80`). A GRPO layer reported at
n=1 inside a paper whose stated methodological contribution is error bars is a
self-inflicted wound. This registration applies the same bar to the
response-confidence track.

### Posture: this is a pre-registered replication inside an EXPLORATORY track

The word "confirmatory" in this experiment's title means *confirmatory with
respect to the seed-1 response-confidence result* — a replication whose gates and
falsifier are fixed before the run. It does **not** mean promotion to the
confirmatory headline surface. Per the tier reference
(`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md:52-58`), the
locked PROTOCOL v0.3 headline matrix is the *only* confirmatory surface, and
"every amendment cell is exploratory unless a signed protocol revision (tier 1)
explicitly promotes it." This is a tier-2 amendment. Its numbers are exploratory
response-confidence-track evidence with three-seed intervals, reported
separately from and never pooled with the v0.3 plain-answer headline. See
[Reporting and labeling rules](#reporting-and-labeling-rules).

### What seed 1 actually showed

Read from
`archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
(full 3,369-row SelfAware eval, seed 1, Qwen3-4B). All values are percentages
except mean confidence and Brier.

| Arm | truthful | refusal recall | answer-on-unknown | over-refusal | correct-on-known | mean conf | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| `clean_sft_merged` (base) | 40.58 | 87.02 | 12.98 | 57.51 | 47.23 | 0.748 | 0.364 |
| `clean_sft_dpo` | 40.69 | 87.11 | 12.89 | 56.18 | 46.09 | 0.812 | 0.408 |
| `clean_sft_kto` | 39.36 | 81.01 | 18.99 | 52.37 | 44.03 | 0.853 | 0.452 |
| `clean_sft_grpo_v1` | 39.69 | 95.54 | 4.46 | 75.70 | 61.80 | 0.747 | 0.370 |
| `clean_sft_grpo_v2` | 41.08 | 93.41 | 6.59 | 66.62 | 53.85 | 0.813 | 0.403 |
| `clean_sft_dpo_grpo` | 41.20 | 93.31 | 6.69 | 65.30 | 52.40 | 0.845 | 0.429 |
| `clean_sft_kto_grpo` | 40.84 | 92.54 | 7.46 | 66.37 | 53.56 | 0.862 | 0.448 |
| `clean_sft_grpo_dpo` | 41.64 | 93.31 | 6.69 | 63.63 | 51.76 | 0.866 | 0.445 |
| `clean_sft_grpo_kto` | 40.90 | 89.63 | 10.37 | 60.59 | 49.19 | 0.864 | 0.449 |

Three seed-1 effects are what this block is being asked to replicate.

**Effect 1 — GRPO shifts abstention.** `clean_sft_grpo_v2` against its own
same-seed base moves answer-on-unknown 12.98 → 6.59 (−6.39 pp) and refusal
recall 87.02 → 93.41 (+6.39 pp), at a cost of over-refusal 57.51 → 66.62
(+9.11 pp). This is the effect Amendment F §1 describes as GRPO being "the only
downstream path that materially shifts unknown abstention in the desired
direction, but it can raise known over-refusal"
(`experiments/grpo-centered-stacking/AMENDMENT.md:46-48`).

**Effect 2 — a preference stage after GRPO partially recovers known answers.**
`clean_sft_grpo_dpo` against same-seed `clean_sft_grpo_v2` moves over-refusal
66.62 → 63.63 (−2.99 pp) while answer-on-unknown holds at 6.59 → 6.69
(+0.10 pp). This is the effect Amendment G §1 records as the strongest seed-1
stack: it "preserved low unknown-answering like GRPO while modestly reducing
GRPO's known-row over-refusal. The gain was useful but small"
(`experiments/best-stack-replication-scale-gate/AMENDMENT.md:39-42`).

**Effect 3 — stage ordering matters; GRPO-first beats GRPO-last on over-refusal.**
Both matched pairs point the same way: `clean_sft_grpo_dpo` 63.63 vs
`clean_sft_dpo_grpo` 65.30 (−1.67 pp), and `clean_sft_grpo_kto` 60.59 vs
`clean_sft_kto_grpo` 66.37 (−5.78 pp). Effect 3 is registered as a
**secondary, descriptive** endpoint only: the DPO-pair margin is small enough
that a two-seed replication is not powered to adjudicate it, and pretending
otherwise would be manufacturing a test.

**Non-effect — stated confidence is collapsed and behavior-insensitive in every
arm.** Distinct `response_confidence` values over 3,369 rows at seed 1:
`clean_sft_dpo_grpo` 70, `clean_sft_kto_grpo` 5, `clean_sft_grpo_dpo` 38,
`clean_sft_grpo_kto` 6
(`docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md:397,475,564,730`).
Mean confidence rises across every stack (0.845–0.866) while Brier against
response-appropriateness gets *worse* (0.429–0.449 against 0.364 at the base).
Amendment G §1 states the same conclusion: "all Amendment F arms still showed
high, behavior-insensitive stated response confidence"
(`experiments/best-stack-replication-scale-gate/AMENDMENT.md:41-42`). This block
is **not** an attempt to fix that. Confidence collapse is carried forward as a
known, reported limitation, and G4 exists only so that an unexpected recovery is
routed to a new registration instead of being read as a win here.

---

## Design

### Matrix

Two fresh seeds (2 and 3). Seed 1 already exists and is reused **as data, not as
a run** — its numbers enter the three-seed aggregate, but no seed-1 artifact is
retrained or re-evaluated by this block.

Every seed rebuilds its own complete lineage from the foundation model. Amendment
G §3 already fixes this rule and it is inherited verbatim: "Each seed must
rebuild the clean response-confidence lineage for that seed. Do not combine the
seed-1 clean SFT or GRPO source with a different final-stage seed and call it a
seed replication" (`experiments/best-stack-replication-scale-gate/AMENDMENT.md:67-69`).

Per seed, eight training runs in three stages:

| Stage | Cell | Trained from | Terminal? |
|---|---|---|---|
| 1 | `clean_sft` | Qwen3-4B-bnb-4bit foundation | base/comparator |
| 2 | `clean_sft_dpo` | merged `clean_sft` | terminal |
| 2 | `clean_sft_kto` | merged `clean_sft` | terminal |
| 2 | `clean_sft_grpo_v2` | merged `clean_sft` | terminal |
| 3 | `clean_sft_dpo_grpo` | merged `clean_sft_dpo` | terminal |
| 3 | `clean_sft_kto_grpo` | merged `clean_sft_kto` | terminal |
| 3 | `clean_sft_grpo_dpo` | merged `clean_sft_grpo_v2` | terminal |
| 3 | `clean_sft_grpo_kto` | merged `clean_sft_grpo_v2` | terminal |

"Full symmetry" means all four stage-3 stacks are rebuilt, not only the seed-1
winner. Rebuilding only `clean_sft_grpo_dpo` would give the *winning* arm an
interval while leaving the arms it beat at n=1, which makes the comparison that
selected it uninterpretable.

The stage-2 GRPO arm (`clean_sft_grpo_v2`) is terminal in its own right: it is
the plain SFT→GRPO arm and it carries a paper-2 number, so it is evaluated like
any other terminal arm.

### Eval plan

Full 3,369-row SelfAware under the response-confidence contract for all eight
cells per seed (seven terminal arms plus the stage-1 base, which every gate is
measured against). Metrics are the frozen Amendment E/F set — see
[Frozen inputs](#frozen-inputs-inherited-not-relitigated) items 7 and 13.

**Intermediate-stage gate evals: PROPOSED — KEEP both tiers.** For the lead to
adjudicate at sign time.

1. *Bounded 192-row mixed SelfAware smoke after every merge, before the next
   stage launches.* This is **not** discretionary: Amendment F §8 already froze
   it ("a bounded SelfAware sanity eval must pass before a full next-stage
   launch", `experiments/grpo-centered-stacking/AMENDMENT.md:176-178`) and the
   clean-mainline runbook specifies the same gate with a 100% JSON coverage bar
   (`archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md:157-170`).
   It is also the gate that has already earned its keep: the E session note entry
   `013-invalidated` records a clean SFT→DPO smoke caught evaluating against the
   wrong base
   (`docs/sessions/20260623T093654Z-probe-scaled-response-confidence-retrain.md:578`).
   At roughly five minutes each it is the cheapest lineage-correctness insurance
   in the block. **Proposed: keep, as a G0 stop-before-outcome check.**
2. *Full 3,369-row eval on the stage-1 base and the stage-2 arms.* These are not
   truly "intermediate" — `clean_sft_dpo`, `clean_sft_kto`, and
   `clean_sft_grpo_v2` are terminal arms that paper 2 reports, and
   `clean_sft_merged` is the same-seed denominator for G1. **Proposed: keep;
   there is no genuinely optional full eval in the block.**

### Datasets

Seed-independent and already specified. The response-confidence datasets are a
function of the probe result and the target construction, not of the training
seed, so all three seeds consume byte-identical data. Built by
`archive/experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
(Amendment E §6, `experiments/probe-scaled-response-confidence/AMENDMENT.md:255`)
with `--include-ambiguous-middle`, into:

| Role | Path (uncommitted scratch) |
|---|---|
| clean SFT | `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_clean.jsonl` |
| DPO | `scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl` |
| KTO | `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl` |
| GRPO | `scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl` |

Paths from the clean-mainline runbook
(`archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md:27-37`).

**Pre-launch prerequisite:** `scratch/` is uncommitted and is not present in a
fresh worktree. Before any launch, the datasets must be rebuilt from the builder
and the clean-SFT audit re-verified against the frozen Amendment E numbers —
14,943 rows, 7,981 known / 6,414 unknown / 548 ambiguous, 2,489 unique targets,
range `[0.3508, 0.90]`
(`experiments/probe-scaled-response-confidence/AMENDMENT.md:199-206`). A
mismatch is a hard stop, not a knob.

**Pre-sign feasibility probe: RUN AND PASSED (2026-07-31).** The datasets were
rebuilt from the builder (after repairing its five stale pre-archive-move
argparse defaults, fix carried on this branch) and audited: all six frozen
clean-SFT numbers matched exactly, and the rebuild was byte-identical to the
pre-existing 2026-06-29 outputs across all eight files, confirming determinism.
Because no signed doc froze row counts for the derivative datasets, this
amendment freezes them now, from the audited manifest, as additional G0
lineage-validity constants: DPO 14,943 rows, KTO 29,886 rows, GRPO train
14,888 rows, GRPO dev 1,655 rows
(`scratch/schema_response_confidence/qwen3-4b-instruct*/response_confidence_schema_manifest.json`,
verified against on-disk line counts). Any future rebuild that deviates from
these counts is a G0 hard stop.

### Lane

Local RTX 3090, docker, **serial**, following the seed-1 precedent. Launch
pattern is the runbook's
(`archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md:62-75`):
detached `docker run` on `unsloth/unsloth:latest` with the repo bind-mounted at
`/workspace/repo`, tuner trainer entrypoints, `--no-dashboard --quiet`; evals via
`run_eval.py --config <cfg> --live-vllm`.

**Lane tension — flagged for the lead, NOT resolved here.** PROTOCOL v0.3 §3.4
scopes the 3090 as the development lane, not the matrix lane: "On the local 3090
the same matrix would be serial (tens of hours), which is why the 3090 is scoped
as the dev / smoke lane and HF Jobs as the matrix execution lane (§3.4)"
(`archive/docs/protocols/phase1/PROTOCOL.md:543-545`). This block is exactly a
matrix, it is exactly serial, and it is exactly tens of hours (see
[Budget](#budget)). Three readings, for the lead to rule on:

- The §3.4 scoping governs the *v0.3 plain-answer headline matrix* specifically,
  and an exploratory response-confidence amendment picks its own lane. Then the
  local lane is fine and the operative precedent is that all of Amendments E and
  F ran locally and serially.
- The scoping is a general lane rule. Then this block belongs on HF Jobs, and the
  registration needs a cloud-lane design that does not currently exist for the
  response-confidence track — the PROTOCOL §5 cloud prerequisites (hub-published
  Qwen3 datasets) are unmet, and the GRPO reward code path has never run on the
  cloud lane.
- Split the difference: keep it local because the reward/merge chain is only
  validated locally, and record the §3.4 deviation explicitly in the sign-off.

The draft assumes the local lane because that is what the seed-1 evidence used
and what the instrument is validated against, but this is a **lead decision, not
a drafting decision.**

---

## Frozen inputs (inherited, not relitigated)

This registration **stands on its own** and does **not** retro-sign Amendment E.
Amendment E remains DRAFT / NOT SIGNED and remains exploratory
(`experiments/probe-scaled-response-confidence/AMENDMENT.md:23`); its design
choices enter here as **frozen inputs** — fixed constants this block consumes
without re-deriving or re-opening. If any of these is wrong, this block
replicates the wrong thing faithfully; that is an accepted and stated limitation,
not a hidden one.

From **Amendment E** (`experiments/probe-scaled-response-confidence/AMENDMENT.md`):

1. **Output contract** `{"answer": "...", "response_confidence": 0.73}` — §3, :75-79.
2. **Probe-derived target**, Laplace-smoothed over 32 stochastic samples:
   `factual_p = (correct_samples + 1) / (n_samples + 2)`, sourced from the
   Qwen3-4B probe results — §3, :84-93.
3. **Target mapping** `response_confidence = 0.1 + 0.8 * response_appropriateness_p`,
   into non-endpoint `[0.1, 0.9]` — §3, :112-119.
4. **Semantic constraint**: `response_confidence` is response-*appropriateness*,
   not answer-correctness. A correct "I don't know" on a true unknown earns HIGH
   confidence — §3, :102-108.
5. **The v3 CLEAN SFT projection** as the base: appropriate completions only
   (14,943 rows = 7,981 known answers + 6,414 unknown abstentions + 548
   ambiguous-middle; 2,489 unique targets; range `[0.3508, 0.90]`). Rejected
   completions, wrong answers, and known-question over-refusals are excluded from
   SFT and reserved for DPO/KTO/GRPO — §3.3, :189-209.
6. **The contrastive SFT branch is excluded as a base.** It is exploratory
   scalar-movement evidence only — §4, :226-228, and runbook :12-13.
7. **Metric set and scalar-distribution checks**: JSON coverage, unique
   `response_confidence` count, confidence histogram by known/unknown/refusal/
   correctness, endpoint frequency, MAE/Brier against response appropriateness —
   §5, :234-241.

From **Amendment F** (`experiments/grpo-centered-stacking/AMENDMENT.md`, SIGNED
2026-06-24):

8. **The four stage-3 stack definitions** — §3 table, :75-80.
9. **GRPO source variant = GRPO v2**, named in the sign-off as the frozen source
   — §3 :82-84 and §8 :171-172.
10. **Merge-first lineage validation**, all five steps: verify the source arm
    trained cleanly; merge the source adapter; bounded sanity eval of the merged
    source; confirm the next-stage config points at the *merged source* and not
    the foundation model; record source metrics and artifact paths — §4, :88-97.
11. **Bounded sanity eval before every full next-stage launch** — §8, :176-178.
12. **Interpretation rules**: a win must beat its *immediate source*, not just
    cold-start; higher stated confidence is not an improvement without a
    calibration gain; reducing unknown answers by over-refusing known rows is not
    sufficient; a preference stage after GRPO is useful only if it recovers known
    answers without materially reopening unknown answering — §5, :132-140.
13. **The balanced behavior score is an exploratory summary only**, not a
    registered headline metric — §5, :127-130. It appears in the comparison CSV
    and must not be gated on.

From the **clean-mainline runbook**
(`archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`):

14. **Chain order** SFT → merge-16bit → evaluate merged → stage-2 trained from
    the merged path passed as `--model-name` — :5-13, :84-88.
15. **Capacity settings carried from seed-1 evidence**: DPO batch 2 / accumulation
    4 (batch 4 / accumulation 2 reached critical VRAM in the full run, :109-111);
    KTO batch 12 / accumulation 1 with a step-250 recheck and a documented
    fallback to batch 8 (:130-133) — at seed 1, batch 12 completed but peaked at
    89.22% reserved VRAM and was logged as "workable but not roomy"
    (`docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md:706-709`);
    GRPO `per_device_train_batch_size: 32`, `num_generations: 4` (:154-156).

**Also inherited: Amendment D** remains the record of the constant-target scalar
collapse that E corrects; it is DRAFT / NOT SIGNED and superseded by E
(`experiments/schema-response-confidence/AMENDMENT.md:23` and
`experiments/probe-scaled-response-confidence/AMENDMENT.md:68-71`). No D artifact
is used here.

---

## Relationship to prior registrations

**Amendment E — NOT retro-signed.** E stays DRAFT / NOT SIGNED and stays an
exploratory lineage. This block inherits E's design as frozen inputs (above) and
takes independent responsibility for its own prediction, falsifier, and gates.
Signing this experiment must not be read, cited, or reported as signing E.

**Amendment F — superseded for exactly these cells and nothing else.** F §8
excludes "seeds 2/3, 8B, cloud lanes, bridge cells, and any merged model
publication ... until seed-1 local results are interpretable"
(`experiments/grpo-centered-stacking/AMENDMENT.md:181-183`). Seed-1 local results
are now interpretable: the four stacks completed, evaluated, and produced the
comparison table above. This registration therefore lifts F's exclusion for
**seeds 2 and 3 of the local 4B response-confidence lineage only.** F's exclusion
of **8B, cloud lanes, bridge cells, and merged-model publication remains fully in
force** and is not touched. F's own seed-1 results and conclusions stand
unchanged.

**Amendment G — OVERLAPS. This is the item the lead most needs to rule on.**
`experiments/best-stack-replication-scale-gate/AMENDMENT.md` (DRAFT / NOT SIGNED)
already registers seed-2/3 replication of the *best* stack, `clean_sft_grpo_dpo`,
as arms `clean_sft_grpo_dpo_seed2` and `clean_sft_grpo_dpo_seed3` (§3, :62-69).
This experiment is a strict **superset**: same two seeds, same lineage-rebuild
rule, same metrics, but all four stacks plus all three stage-2 arms instead of
one stack. The two registrations cannot both be signed as written — they would
authorize the same GPU work twice under different gates. Proposed disposition,
for the lead: **sign this one; mark Amendment G superseded-before-signing for its
seed-replication half.** G's *other* half — the 8B scale gate and the Hugging
Face publication gate (§3, :71-76) — is not covered here and should survive as a
separate downstream registration. This draft claims **no** authority over 8B or
publication.

**PROTOCOL v0.3** remains the locked plain-answer headline protocol. Nothing here
modifies it. The §3.4 lane question above is flagged, not resolved.

---

## Prediction

> **EMPTY — filled by the PI at sign time. A drafting agent must not fill this.**

## Orchestrator prediction

> **EMPTY — filled by the lead at sign time. A drafting agent must not fill this.**

Both slots are also empty in `experiment.yaml` (`prediction:`) and in the
scoreboard below. `bin/exp sign` refuses to sign while `prediction` or
`falsifier` is empty, so the tooling enforces this.

## Falsifier

> **PROPOSED — for lead adjudication at sign time.**

If G1 does not confirm — that is, if the seed-1 GRPO abstention shift fails to
reproduce in direction at seed 2 or at seed 3 — then the seed-1 GRPO layer is a
seed artifact. No GRPO effect may then be reported in paper 2 as a stable
finding; the GRPO layer is reported as seed-1-only exploratory evidence carrying
an explicit non-replication note, and downstream GRPO work (8B, publication) is
blocked pending a mechanism explanation.

G1 is the falsifier because it is the load-bearing claim: if GRPO does not
reliably shift abstention, the stacks built on it have nothing to stack. G2
failing alone falsifies the narrower "a preference stage recovers known answers
after GRPO" claim and retires the `clean_sft_grpo_dpo` publication candidate, but
does not kill the GRPO layer itself.

## Gates

> **PROPOSED — for lead adjudication at sign time. The numbers below are
> proposals, not settled thresholds.** Machine-readable form in `gates.yaml`.

Once signed, **no gate moves after results are seen.** An ambiguous result is
reported as ambiguous.

### G0 — instrument and lineage validity (stop-before-outcome, per seed per cell)

Not a claim gate. A failure stops the cell before any outcome is read.

- The next-stage training config points at the **merged** source model, not the
  foundation model and not an adapter path (Amendment F §4 step 4).
- The 192-row bounded mixed SelfAware smoke passes with **100% JSON
  `answer` + `response_confidence` coverage** and **0 thinking-tag hits**.
- Training exits 0 with the final adapter artifacts and `training_lineage.json`
  present.
- The rebuilt dataset audit matches the frozen Amendment E clean-SFT numbers
  exactly (14,943 / 7,981 / 6,414 / 548; 2,489 unique targets).
- The containment check passes (see [Data containment](#data-containment)).

### G1 — GRPO abstention shift replicates (PRIMARY; the falsifier gate)

Per seed, `clean_sft_grpo_v2` against its **own same-seed** `clean_sft_merged`:

- answer-on-unknown **decreases by ≥ 3.0 pp**, and
- refusal recall **increases by ≥ 3.0 pp**.

**PASS** requires both conditions in **both** seed 2 and seed 3.
**NOT CONFIRMED** if either seed shows a sign flip, or a movement smaller than
3.0 pp, on either metric.

*Derivation of 3.0 pp:* the seed-1 effect is −6.39 pp / +6.39 pp
(12.98 → 6.59, 87.02 → 93.41). The floor is set at roughly half the seed-1
magnitude — large enough to exclude noise, loose enough that a genuine but
attenuated effect is not scored as a failure. It is a **direction-plus-floor**
test, not a magnitude-equivalence test; a two-seed replication cannot support the
latter.

### G2 — post-GRPO preference recovery replicates (PRIMARY)

Per seed, `clean_sft_grpo_dpo` against its **own same-seed** `clean_sft_grpo_v2`:

- over-refusal **decreases** (delta < 0, any magnitude), **and**
- answer-on-unknown does **not reopen by more than +2.0 pp**.

**PASS** requires both conditions in **both** seeds.
**NOT CONFIRMED** if either seed shows an over-refusal increase, or unknown
answering reopening by more than +2.0 pp.

*Derivation:* the seed-1 effect is −2.99 pp over-refusal at +0.10 pp unknown
answering. A magnitude floor is deliberately **not** set: at −2.99 pp the seed-1
effect is too small for a two-seed block to bound, and Amendment G §1 itself
calls the gain "useful but small". Setting a magnitude bar here would invent
precision the instrument does not have. The +2.0 pp reopening cap encodes
Amendment F's frozen rule that a post-GRPO preference stage is useful "only if it
recovers known answers without materially reopening unknown answering"
(`experiments/grpo-centered-stacking/AMENDMENT.md:139-140`).

### G3 — three-seed intervals reported (DELIVERABLE, non-gating)

Every GRPO-touching arm reports mean and 95% bootstrap CI across the three seeds
on: truthful, refusal recall, answer-on-unknown, over-refusal, correct-on-known,
refusal rate. This is the reason the block exists. It is descriptive and cannot
pass or fail.

### G4 — confidence non-recovery check (DESCRIPTIVE guard, non-gating)

Pre-stated so that a surprise cannot be retrofitted as a success. If any seed-2
or seed-3 arm shows **more than 200 distinct `response_confidence` values over
3,369 rows AND Brier against response-appropriateness below 0.35**, that is a
**new exploratory finding requiring its own registration** — not a confirmation
of anything in this block. Seed-1 reference: 5–70 distinct values, Brier
0.403–0.449.

### G5 — stage-ordering comparison (SECONDARY, descriptive, non-gating)

Report `clean_sft_grpo_dpo` against `clean_sft_dpo_grpo`, and
`clean_sft_grpo_kto` against `clean_sft_kto_grpo`, as over-refusal deltas per
seed with three-seed intervals. Explicitly **not** adjudicated: the seed-1
DPO-pair margin (−1.67 pp) is below what two added seeds can resolve. Reported as
a descriptive pattern with its interval, never as a finding.

---

## Reporting and labeling rules

1. **Exploratory, always.** Every number from this block is labeled *GRPO
   three-seed confirmatory / response-confidence track, exploratory*. It is never
   pooled with, or presented as, the PROTOCOL v0.3 plain-answer headline matrix,
   and never pooled with Amendment A/B/C/D results
   (`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md:52-58`).
2. **Paper 2 may report** the three-seed mean and CI for any GRPO-touching arm,
   provided the arm is labeled exploratory response-confidence track and the seed
   count is stated. Seed-1-only GRPO numbers must not appear in paper 2 alongside
   three-seed DPO/KTO numbers without the asymmetry being stated.
3. **Paper 2 must not** describe a G1 or G2 pass as "confirmed" in the tier-1
   sense. The permitted phrasing is *replicated across three seeds within the
   exploratory response-confidence track*. Promotion to a headline claim requires
   a signed protocol revision (tier 1), which this is not.
4. **A NOT-CONFIRMED result is reported straight**, in the same place and with
   the same prominence a pass would have received. Nulls are the point of
   pre-registration.
5. **Confidence collapse is reported as a standing limitation** in every table
   that reports these arms, whatever the behavioral gates do.
6. **Seed 1 is reused as data, not re-run.** Any three-seed aggregate states that
   seed 1 came from Amendments E/F and seeds 2–3 from this block.

---

## Budget

All figures are **measured seed-1 wall-clock**, not estimates. Sources:
E note = `docs/sessions/20260623T093654Z-probe-scaled-response-confidence-retrain.md`,
F note = `docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md`.

| Stage | Cell | Measured seed-1 | Source |
|---|---|---:|---|
| 1 | `clean_sft` train + merge + smoke | 2.4 h | E note :488→:535 (12:36:24 → 14:58) |
| 2 | `clean_sft_dpo` train | ~1.4 h | proxy: F note :541-542 `train_runtime 5068.499s` (same DPO config family) |
| 2 | `clean_sft_kto` train | 1.83 h | E note :837 `train_runtime 6580.4427s` |
| 2 | `clean_sft_grpo_v2` train | 7.22 h | E note :1594 `train_runtime 25983.384s` |
| 3 | `clean_sft_dpo_grpo` train | 4.94 h | F note :350→:373 (19:46:33 → 00:42:45) |
| 3 | `clean_sft_kto_grpo` train | 5.29 h | F note :415→:438 (01:29:50 → 06:46:57) |
| 3 | `clean_sft_grpo_dpo` train | 1.41 h | F note :541-542 `train_runtime 5068.499s` |
| 3 | `clean_sft_grpo_kto` train | 1.71 h | F note :703-704 `train_runtime 6159.447s` |
| — | **training subtotal** | **26.2 h** | |
| eval | full 3,369-row SelfAware, per arm | 0.35–0.68 h | measured 5×, see below |
| eval | × 8 arms per seed | ~4.0 h | at ~0.5 h each |
| — | merges (3 × ~0.25 h) + 192-row smokes (8 × ~0.1 h) | ~1.5 h | runbook gate pattern |
| — | **per-seed total** | **~32 h** | |
| — | **two seeds (2 and 3), serial** | **~64 h ≈ 2.7 days** | |

Measured full-eval durations (launch → result, same checkpoint chain):
`clean_sft_dpo_grpo` 28.8 min (F note :373→:394), `clean_sft_kto_grpo` 21.1 min
(:438→:461), `clean_sft_grpo_dpo` 33 min (:530→:550), `clean_sft_grpo_kto` 31 min
(:693→:716), `clean_sft_grpo_v2` 41 min (E note :1613→:1648).

For calibration against the seed-1 precedent: the entire Amendment F stage-3
block — four stacks trained and fully evaluated — ran 2026-06-24T19:46:33Z →
2026-06-25T11:50:55Z, **16.07 h wall-clock** (F note :350→:743). This block is
roughly twice that per seed because it also rebuilds stage 1 and stage 2.

**Standing guardrail.** Pause and report to the lead if cumulative burn tracks
**more than 30% over** this estimate — that is, if the seed-2 block passes ~42 h
before completing, or the two-seed total passes ~83 h. Do not silently absorb an
overrun; the 3090 lane has no elasticity, and an overrun is evidence that a
capacity assumption has broken (most likely KTO batch 12, which peaked at 89.22%
reserved VRAM at seed 1).

---

## Data containment

**This repository is PUBLIC.** These rules bind every artifact this block
produces and are checked in G0.

- **Never committed:** model weights, adapters, merged-16bit directories,
  checkpoints, optimizer state, `.cache/` contents.
- **Never committed:** the scratch datasets under
  `scratch/schema_response_confidence/` — SFT/DPO/KTO/GRPO training JSONL, in any
  seed or variant. They are rebuilt from the builder script, not stored.
- **Never committed:** generation text. No model completions, no
  `scored_rows.jsonl`, no per-row eval output, no generated answer or abstention
  strings.
- **Never committed:** question text, prompts, aliases, gold answers, distractor
  pools, or any row-level content from the SelfAware population or the probe
  pool.
- **Committed analysis is aggregate or ID-only:** metric JSON, per-arm summary
  rows, three-seed aggregates and CIs, run records naming paths and hashes,
  session notes, configs, and this directory's governed docs.
- `experiments/grpo-three-seed-confirmatory/analysis/` is gitignored by the
  scaffold `.gitignore` and stays that way. Anything promoted out of it is
  reviewed against the rules above before it is staged.
- `synaptic-tuner/` stays generic. No Epistemic-specific logic enters the
  submodule for this block.

Inherited from Amendment F §6
(`experiments/grpo-centered-stacking/AMENDMENT.md:142-153`) and Amendment E §6
(`experiments/probe-scaled-response-confidence/AMENDMENT.md:251-269`), tightened
here for the public-repo posture.

---

## Launch authority

This draft authorizes **nothing**. Before any GPU work:

1. The PI fills the prediction slot; the lead fills the orchestrator prediction.
2. The lead adjudicates the proposed gates, the falsifier, the Amendment G
   disposition, and the lane question.
3. `bin/exp sign grpo-three-seed-confirmatory` pins `cell.yaml` and `gates.yaml`.
4. A launch decision names the exact seed, cell, source checkpoint, merge path,
   destination run path, eval config, and lane.
5. The datasets are rebuilt and the audit re-verified against the frozen numbers.

Cloud lanes, 8B, bridge cells, and any model publication require separate
approvals and are **out of scope**.

---

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| PI (user) | *(empty — filled at sign time)* |
| orchestrator (lead) | *(empty — filled at sign time)* |

## Outcome

Filled at resolve. Record the G1/G2 results per seed, the three-seed intervals,
the confidence-collapse status, and the one-sentence verdict that also goes into
`verdict:` in the manifest.
