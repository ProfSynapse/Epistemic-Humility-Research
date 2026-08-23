---
schema_version: research-session/v1
session_id: 20260724T193620Z-gemma-use-cache-kv-seam-root-cause-and-write-criterion-staging
title: Gemma use_cache KV-seam root cause; cross-family roll-up resolved INCONCLUSIVE
status: active
created_at: "2026-07-24T19:36:20Z"
updated_at: "2026-07-24T21:30:00Z"
question: >-
  Does read-then-actuate generalize across model families, and can the
  cross-family layer-contrast experiment be resolved on the registered
  instrument once the gemma activation corruption is repaired?
tags:
  - experiment-runner
  - j-space
  - cross-family
  - gate-diagnosticity
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: >-
    j-space-cross-family-layer-contrast signed INCONCLUSIVE (2 of 4 families ran,
    below the minimum denominator of 3); gemma4-e4b staged as the third family
    pending a Tier 1 revision.
  changed_by_session: >-
    Root-caused the gemma use_cache KV-seam corruption and traced it into the
    shared j-lens instrument; resolved the cross-family roll-up on the registered
    script rather than on a remembered rule.
checkpoints:
  - id: 001-kv-seam-root-cause
    at: "2026-07-24T19:36:20Z"
    kind: observation
    title: gemma use_cache KV-seam root cause
    summary: >-
      use_cache=False starves blocks 24-41 on gemma-4-E4B, which read donor K/V
      from blocks 22/23 through the cache object; hs00-hs24 bit-identical,
      hs25 collapses to cos 0.732 and decays to 0.075 by hs42. llama/mistral/qwen
      unaffected at min cos 1.000000.
    evidence:
      - experiments/j-space-cross-family-layer-contrast/extract_anchor.py
    run_ids: []
    commands: []
    decisions: []
    next_steps: []
    signals: {}
  - id: 002-resolve-inconclusive
    at: "2026-07-24T21:30:00Z"
    kind: gate
    title: Roll-up resolved INCONCLUSIVE; Tier 1 revision drafted
    summary: >-
      cross_family_rollup.py returned inconclusive (2 families ran, 1 passed),
      contradicting a FALSIFIED verdict announced earlier from a remembered rule.
      INCONCLUSIVE signed. Three instrument defects recorded; a Tier 1 revision
      is drafted and unsigned.
    evidence:
      - experiments/j-space-cross-family-layer-contrast/AMENDMENT.md
      - docs/protocols/2026-07-24-jspace-gate-and-instrument-revision.md
      - .skills/experiment-runner/reference/gate-diagnosticity.md
    run_ids: []
    commands: []
    decisions:
      - Record INCONCLUSIVE per the registered instrument, not FALSIFIED.
      - Registered G2 PASSes stand with a non-diagnosticity caveat; no retroactive re-labelling.
      - gemma4-e4b is the third family; qwen35-4b rejected as circular.
    next_steps:
      - Obtain signature on the Tier 1 revision before editing jlens.py or re-profiling gemma.
    signals: {}
---
# Session — gemma `use_cache` KV-seam root cause; mistral roll-up on a knife edge; write-criterion staged

Date: 2026-07-24
Worktree: `ehr-worktrees/jspace-cross-family` (`exp/j-space-cross-family-layer-contrast`)
Tier: 3 throughout. **Nothing signed, nothing committed to a claims surface, no
prospective GPU cell launched.**

Program frame this session serves (standing, from the PI): the hunt is
**read-then-actuate across model families**, and whether it can be reduced to
**recipes reproducible on ~any open-weight model**.

---

## 1. Headline: a one-keyword bug invalidated every cached gemma activation

`use_cache=False` corrupts gemma-4-E4B hidden states from **hs25 onward**.

| forward call | top-1 at anchor | p | rank of `{"` (token the model actually emitted) |
|---|---|---:|---:|
| `use_cache=True` (what `.generate()` does) | `{"` | 0.8355 | **1** |
| `use_cache=False` (what extraction did) | `ah` | 0.7578 | **5228** |

Per-layer cosine, final position: **hs00–hs24 = 1.000000** (identical);
**hs25–hs42 = 0.732 → 0.075** (collapsing with depth).

**The boundary is the KV seam, exactly.** Gemma-4-E4B shares K/V across layers —
blocks 24–41 read donor K/V from blocks 22/23 (`first_kv_shared_layer_idx =
24`). hs25 is the output of block 24, the *first* block that reads donor K/V.
The sharing is routed through the cache object, so disabling the cache starves
precisely the shared blocks and nothing below them. **The boundary was measured
first and only then matched to the seam** — it was not a story fitted to a
prediction, which is why it convinces.

### Blast radius, exactly delimited

`grep -rn use_cache --include=*.py` over the experiment returns **exactly one
call site**: `extract_anchor.py:123`. Generation goes through `.generate()`
(`gen_lib.py:50`, `mine_eval_pool.py:124`), cache on.

- **SOUND — every gemma generation.** Mined pool, eval rows, and the dosed
  generations behind the 0/176 null.
- **INVALID — every cached gemma activation.** Manifest
  `hidden_states_indices = [34, 38, 42, 40]`; all four are ≥25, so *none*
  survive. Probe AUC, the KU direction, and the boundary-push write direction
  for gemma are all fit on corrupted activations.
- **The 0/176 gemma null is uninterpretable — but for a specific, fixable
  reason.** The model computed correctly during dosing; the *direction we
  injected* was derived from garbage. "We wrote a meaningless vector and nothing
  happened" is not evidence that gemma cannot actuate.
- **Gemma hs ≤ 24 would be valid** — but nothing was ever extracted there.
- **The `cos_vs_gpu_cached` 0.998–0.9998 CPU-vs-GPU agreement is void as
  reassurance.** Both sides ran `use_cache=False`; they agree with each other
  and are both wrong. Consistency-is-not-correctness, confirmed.

### Family control — gemma-only

`scratchpad/use_cache_family_control.py`; results
`use_cache_family_control_results{,2}.json`.

| family | layers | min cos over all layers | top-1 agrees | verdict |
|---|---:|---:|---|---|
| llama-3.2-3b | 28 | 1.000000 | yes | UNAFFECTED |
| qwen35-4b | 32 | 1.000000 | yes | UNAFFECTED |
| mistral-7b-v03 | 32 | 1.000000 | yes | UNAFFECTED |
| gemma4-e4b | 42 | **0.075** | **no** | **CORRUPTED from hs25** |

None of the other three share K/V across layers. **The llama, mistral and qwen
read/actuate results are untouched.** This is a gemma-onboarding bug, not a
program-wide one.

**Fix:** one keyword (`use_cache=True` at `extract_anchor.py:123`) + re-extract.
Observed on transformers 5.5.0 / torch 2.9.0+cu128,
`Gemma4ForConditionalGeneration`. Whether upstream treats cache-free forward on
a KV-sharing model as a bug or as unsupported, **our extraction must not use
it.**

### Correction of the record

Earlier this session the lead reported to the PI, and wrote into `NOTEBOOK.md`,
that the **gemma live-logits gate returns NOT SOUND** and that the whole gemma
pipeline was producing garbage. **That was reported before root-cause was in
hand, and it was wrong.** The pre-registered decision rule offered only two
branches ("recon bug → gemma sound" / "live also wrong → gemma suspect") and the
truth was a third thing the rule did not anticipate. The `NOTEBOOK.md` entry has
been retitled and carries an explicit `[CORRECTION]` block; the superseded
measurements are retained because they were the route to the root cause.

### Confounds eliminated en route (each by measurement)

Reconstruction path (`live == recon` exactly, corr ≥0.9995) · render
(`ml.render` byte-identical to `apply_chat_template`; `.generate()` from it
reproduces the recorded answer exactly) · re-tokenization (llama scored both
ways, 6/6 identical) · `add_special_tokens` / `attention_mask` (identical ids,
identical garbage) · **meta-device offload** (forced full load: `n_meta_params:
0` of 1160, top-1 bit-identical — the last surviving suspect, killed). The
elimination sequence is what left `use_cache` as the only difference between the
working `.generate()` and the failing forward.

---

## 2. Mistral roll-up is balanced on a single row

`analysis/mistral-7b-v03/runlog/full/`:

| site | rel depth | FIT (n=8, max over rungs) | held-out `clean_tighten` | G1 |
|---|---:|---:|---|---|
| hs12 | 0.375 | 0.625 | **0.2216** (289/1304, Wilson [0.1999, 0.2450]) | **FAIL, decisive** |
| hs15 | 0.469 | 0.625 | **0.5000** (246/492, Wilson [0.4560, 0.5440]) | **UNDECIDED** |

hs15 sits at *exactly* the 0.50 floor with Wilson-lower 0.4560 already clearing
the >0.40 requirement. One more failure drops it below; one more success lifts
it. **Not to be pre-adjudicated.** The lead's earlier expectation that hs15
would fail like hs12 is **retracted** — the data did not support it.

**Roll-up, both branches stated in advance** (registered arithmetic: ≥3 families
clear = SUCCESS, exactly 2 = MIXED, ≤1 = FALSIFIED; gemma NOT-RUN and
denominator-excluded, qwen3.5 back-burnered):

- **hs15 fails** → only llama clears → **FALSIFIED**
- **hs15 clears** → llama + mistral = exactly 2 → **MIXED**

This single site decides which.

### The G2 gate is vacuous, now demonstrated twice

- hs12: **fired n = 1** of 382 known-correct rows (fire rate 0.26%). Wilson on
  the fired denominator [0.000, 0.794]. The unconditional reading (2/382 =
  0.0052, upper 0.0189) "passed" on 381 rows that were **never dosed** — it
  measured baseline well-formedness, not the cost of dosing.
- hs15: **141 known-correct rows so far, 0 fired.** A zero denominator is not a
  pass.

Both are **NOT-ADJUDICABLE**, an explicit disposition distinct from PASS.

### The n=8 dose ladder has no discriminating power

hs12 and hs15 ran the identical 8-rung `RATIO_LADDER` at n=8 and the FIT scored
them **identically at 0.625 (5/8 each)**. Held-out they differ by >2×
(0.2216 vs 0.5000). A paired within-family demonstration that the max-over-rungs
n=8 estimator cannot tell a 0.22 site from a 0.50 site — independent of any
depth argument. hs12's FIT overstated by ~2.8×.

---

## 3. Cross-family actuation bake-off (CPU, 67 sourced points, 5 substrates)

`analysis/cross_family_actuation_depth.md`. **Relative depth
(`hs_index / num_hidden_layers`) is the only predictor with consistent
directional signal** (Spearman ρ −0.80 to −1.00) — but every correlation is
n=3–4 and **none is significant**. `eff_dim_frac` and probe AUC carry no
independent signal; probe AUC is pinned in 0.977–0.9998 with no rank
information to give.

**Depth gives a band, not a site**, and inside the band it fails:

- **mistral hs19 (rel 0.594, inside the predicted peak band) is 0/8 at all 8
  rungs across a 20× dose range**, while hs15 (0.469) sits at 0.625.
- **qwen3-4b-base held-out ordering is non-monotone**: hs29 (0.806) beats hs26
  (0.722), 88.1% vs 81.1%, n=185/cell — the best-powered cells in the table.

The registered late-site rule `round(0.94 × (num_hidden_layers − 1))` sits in
the **dead band for every substrate measured**. That is the instrument finding
behind the whole write-criterion line.

---

## 4. Write-criterion amendment: restructured, still UNSIGNED

Draft lives at `scratchpad/DRAFT_amendment_write_criterion.md` (proposed slug
`write-criterion-site-selection`). **No slug minted, `bin/exp new` not run,
nothing signed.** Two structural corrections to v1:

1. **v1 graded the proxy against the wrong opponent.** It had the proxy beating
   the *read* criterion — already known dead. A manufactured pass. **The rule to
   beat is RELATIVE DEPTH**, which costs nothing to compute. A computed proxy
   that cannot beat a free rule does not belong in a recipe.
2. **v1 conceded a confound unnecessarily** ("cannot separate depth from
   KV-quarantine"). True of a single-site test, false of a **scan**: scan gemma
   hs19/21/23/25/27/29 and test for a **step at 24**, with a matched
   relative-depth **llama control** (llama has no seam). A sharp index-localized
   step is what a seam produces and what a smooth depth effect cannot fake.

**Staged so the expensive half is conditional:**

- **Stage A — retrodiction. Tier 3, CPU-only, no signing, free.** Does a
  forward-pass-only per-layer proxy retrodict the within-substrate orderings we
  already have? **Decisive test: mistral hs15 (live) vs hs19 (dead zero)** — the
  one case where depth is known to fail. Gate: recovers the mistral cliff AND
  ≥3 of 4 substrate orderings. Miss → line closed, reported as closed, **Stage B
  never runs.**
- **Stage B — prospective. Tier 2, requires signing + explicit PI approval.**
  Gemma seam-straddling scan + llama control. **Not approved. Not drafted for
  signature.**

**Stage A needs no GPU and no re-extraction**: the cached mistral layers are
`[12, 15, 19, 30]` — already including the decisive hs15/hs19 pair.
**Gemma is excluded from Stage A** (all its cached activations are corrupt).

Harness `analysis/stage_a_retrodiction.py` + `analysis/stage_a_spec.md` are
**BUILT and CPU-smoke-tested, NOT YET RUN on real weights**. Two proxies scored
separately, not blended: `proxy_A` (untargeted KL at anchor) and `proxy_B_span`
(refusal-span delta-logprob, **primary**). Dose is calibration-blind (uniform
ratio ladder, no tuned dose) — load-bearing, because mistral hs19 has no usable
dose at all, so a selected-dose rule could not score the decisive pair.

### Two lead adjudications on Stage A (2026-07-24)

**Denominator stays 4 — refused a reduction.** The harness author inferred the
4th ordering substrate was gemma; it isn't. The four are llama, mistral,
qwen3.5-4b, qwen3-4b-base. Gemma never had an ordering (0/176 everywhere).
Verified on-disk inventory: anchors exist for **llama [17,20,23,26]** and
**mistral [12,15,19,30]** only; `qwen35-4b/` has no anchor manifest and
qwen3-4b-base's numbers came from a different experiment. **2 of 4 are scoreable
today.** Cutting the denominator to 3 or 2 would be goalpost movement on a gate
the lead wrote, in the direction that makes the lead's own proposal pass —
refused.

**Consequence: Stage A can currently return FAIL or NOT-YET, never PASS**, and
runs as the **falsifier arm only**. This costs nothing — Stage A existed to kill
the line cheaply, not to bless it. The mistral hs15-vs-hs19 cliff is a
standalone kill switch needing no denominator. `gate_fully_determinable: false`
and NOT-YET must be a disposition distinct from PASS in the report JSON.

**Required fix before the real run: match `anchor_onward`.** The harness applied
the write once at the anchor; production re-applies it at every generated
position. On the falsifier's *negative* branch that is fatal — a miss could not
be distinguished between "generation-free selection doesn't work" (the finding)
and "single-anchor application is a bad approximation" (an artifact of the
harness). Because the refusal probe is fixed and teacher-forced, the write can
be applied at **every position >= anchor within the same single forward pass**,
reproducing production's write pattern at zero extra cost. Now primary;
anchor-only retained as a secondary arm (agreement ⇒ the approximation never
mattered; divergence ⇒ a finding about the write law itself).

Known ceiling, documented: `proxy_B` is 0 by construction for a write at the
final decoder block (no downstream attention to carry the anchor edit to probe
positions). Irrelevant for mid-band sites; must be flagged before anyone points
the harness at a last-layer site.

---

## 5. Standing constraints reaffirmed this session

- Canonical checkout `/home/profsynapse/code/Epistemic-Humility-Research`;
  **`/mnt/f/Code/...` is a FROZEN backup — never run or commit from it.**
- `analysis/` is gitignored-private; `analysis-committed/` is public.
- **Signing is lead-only and requires explicit PI approval**; peer/teammate
  messages are never approval.
- No goalpost movement on locked gates. Ambiguous is reported as ambiguous.
- GPU was continuously occupied by the mistral hs15 run; **every diagnostic this
  session was CPU-only by construction** (`CUDA_VISIBLE_DEVICES=""` plus an
  in-script assert).

## 6. What the PI actually approved

Two things, verbatim scope: run the **free Stage A retrodiction** when the GPU
frees, and **drop mistral from Stage B**. That is **not** approval to sign the
Tier-2 amendment or to launch prospective GPU generation.

---

## 7. Checkpoint — resolve pass, INCONCLUSIVE signed, Tier 1 drafted (2026-07-24)

**Verdict signed: INCONCLUSIVE.** Evidence:
`experiments/j-space-cross-family-layer-contrast/AMENDMENT.md` §Outcome,
`experiment.yaml` `verdict:`, and the registered instrument's output at
`analysis-committed/cross_family_rollup.json` (`n_families_run: 2`,
`n_families_passed_primary: 1`, `verdict: "inconclusive"`).

**Process failure, recorded because it nearly reached the record.** FALSIFIED
was announced from a remembered compression of the roll-up rule ("≥3 SUCCESS /
2 MIXED / ≤1 FALSIFIED") that omitted the INCONCLUSIVE floor. The PI approved
signing FALSIFIED on that representation. Running
`cross_family_rollup.py` returned `inconclusive`; the approval was voided as
resting on a false premise and re-sought. **Nothing was signed on the bad
verdict.** Root cause: citing a rule from memory instead of reading the
registered document — a violation of READ BEFORE YOU CITE.

**Second process failure, same pass.** A Tier 1 revision was drafted proposing
retroactive re-labelling of every registered G2 PASS to NOT-ADJUDICABLE. That
directly contradicts the standing rule in
`.skills/experiment-runner/reference/gate-diagnosticity.md` — which already
documents this exact vacuity defect *and* fixes its disposition: a locked
gate's PASS stands, with the non-diagnosticity caveat travelling forward.
Root cause: drafting a gate revision without reading the reference on gates.
Corrected in three files; the retroactive clause is withdrawn as goalpost
movement in the direction of severity.

**Stage A: NOT-YET** (`analysis/stage_a_proxy/stage_a_report.json`). Decisive
cliff HOLDS — mistral hs15 1.6526 vs hs19 −0.7393, `arms_agree_on_cliff: true`.
2/4 orderings recovered, 0 fully scoreable, ordering gate OPEN pending qwen
extraction. Onward/anchor arms verified genuinely distinct (e.g. hs15 ratio
0.85: 5.515 vs 0.828); identical readback across arms is anchor-position-only
measurement, not a bug.

**Defects found at resolve, all three in the pending Tier 1 revision**
(`docs/protocols/2026-07-24-jspace-gate-and-instrument-revision.md`, DRAFT,
unsigned):
1. G2 non-diagnostic — 0/334 and 0/382 dosed. PASSes stand with caveat;
   G2a/G2b proposed forward-only; minimum-N floor **computed** as N=35 for
   `Wilson-upper < 0.10` (0/35 → 0.0989; 0/34 → 0.1015).
2. Registered falsifier rule conflicts between `AMENDMENT.md` (has the
   INCONCLUSIVE floor) and `experiment.yaml` `falsifier:` (does not). Both fire
   at n_run=2/n_passed=1. Resolved conservatively toward INCONCLUSIVE.
3. `jlens.py:195` uses `use_cache=False` — same KV-sharing corruption as
   `extract_anchor.py`, in the *shared* j-lens. gemma's `layer_profile.json`
   swept hs29/34/38/42, **all in the corrupt region**, so
   `midband_candidates_hs: [34,38,42]` and `effective_dim_peak_hs: 38` rest on
   corrupt activations. No-op precondition **verified** on llama-3.2-3b
   (no KV sharing): worst cos 0.999999702, max abs elementwise diff 0.000e+00.

**qwen35-4b rejected as the third family**, contrary to an earlier
recommendation of mine: `band_selection.status: not_yet_run` with
`midband_candidates_hs: null` (needs the profile stage; 1/10 layers done at
20172 s), and `families/qwen35-4b.yaml:156-161` already states it is "a
coherence check, not fresh cross-family evidence" since it re-derives on the
same doubt-snap substrate as the resolved `qwen35-4b-midband-heldout`. Using a
Qwen family to settle Qwen-lineage-specificity is circular. PI chose gemma4-e4b
with sites re-selected under the Tier 1 revision.

**PI approvals this checkpoint, verbatim scope:** record INCONCLUSIVE; run
gemma4-e4b as the third family with sites re-selected under a Tier 1 revision;
one revision covering all three defects. **Not** approval to sign the Tier 1
revision, edit `jlens.py`, or launch the gemma profile — all blocked on
signature.
