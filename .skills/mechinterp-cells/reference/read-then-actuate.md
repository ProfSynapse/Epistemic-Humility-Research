# Read-then-actuate: standing up the pipeline on a new model

**What this is.** The end-to-end procedure for taking an arbitrary open-weight
instruction-tuned model and (a) fitting a **known-unknown (KU) direction** in its
residual stream, (b) building a **KU readout gate** on that direction, and (c)
finding and testing an **actuator**: a site and a **boundary push (dosed write)**
along a paired write direction that makes the model hedge on questions it would
otherwise confabulate an answer to.

Steps are per-model by necessity. Row labels, direction fits, dose scale, and
the write site all have to be re-derived per family; almost nothing ports except
the procedure itself. What this file gives you is the order of operations, the
gate at each step, and the failure that step has already produced in this
program at least once.

Read this before designing an actuation cell for a family that does not have one
yet. For the individual steps it routes into
[dose-calibration.md](dose-calibration.md) (the coherent write window) and
[`../../family-atlas/reference/read-actuate-depth.md`](../../family-atlas/reference/read-actuate-depth.md)
(why a read-optimal site is not thereby a write site).

**Status, stated up front because the rest of the document is only honest against
it:**

| stage | does it transfer across model families? |
|---|---|
| Read (KU direction + readout gate) | **Yes.** Routinely AUC ≥ 0.99. Four families. |
| Dose calibration (ratio-normalized) | **Design is right, validation is thin.** One confirmatory data point. |
| Write-site selection | **UNSOLVED.** A wide depth band (rd ≈ 0.37–0.64), no selector, no mechanism. |
| Write (actuation, direction-specific, held-out) | **One qualified success, in one family.** |

Anyone who reads the program's headline as "read-then-actuate reproduces across
model families" is misreading it. What reproduces is the **read**. Sections 3, 5
and 8 are the ones that will cost you time; sections 1, 2 and 4 are close to
turnkey.

**Sourcing.** Every experimental number below is cited to an
`experiments/<slug>/AMENDMENT.md` (or the `gates.yaml` / `cell.yaml` beside it),
which is this repo's only citable source for experimental fact. Numbers whose
only home is a notebook, an analysis JSON, or a `docs/` file are marked
**NOT SOURCED** and you should treat them as folklore.

**Vocabulary is binding.** "Known-unknown (KU) direction", "KU readout gate",
"boundary push (dosed write)". Not "doubt direction".

---

## 0. What your model must satisfy before you start

There is **no minimum parameter count, benchmark score, or instruction-tuning
requirement anywhere in this program.** If a recipe gives you one, it invented
it. The real bar is operational, and it is the atlas gate `AG0a`
(`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md:269-323`):

1. **Answer capture ≥ 0.90 on split rows.** A row is captured iff
   `finish_reason != "length"`, **or** its clean grading shows a complete
   well-formed first-JSON answer and the row is not degenerate. Gemma-4-E4B ran
   **0.9286 (2614/2815)**. Note the history: this limb was originally specified
   as *EOS emission*, and gemma **failed it at 0.8849 vs 0.90** before it was
   re-specified. The re-specification came with a stopping rule - a third
   re-specification is not permitted, and a further failure resolves as "the
   mining instrument cannot cleanly mine this family". Copy that discipline.
2. **Pool power** (§1.3): ≥ 150 held-out `confab` rows and ≥ 250 held-out
   `known_correct_answered` rows.
3. **Byte-identical direction refits** under a fixed seed.

If your model cannot be made to emit parseable structured answers reliably, stop
here. Everything downstream is a role label derived from a parsed generation.

---

## 1. Build the pool

### 1.1 The three roles

Labels are **behavior-dependent, not corpus-dependent** - the same corpus row
becomes `confab` or `unknown_refused` depending on whether *your* model's raw
base answers or refuses. **You cannot port row labels between families.** Re-mine
per model.

| role | definition |
|---|---|
| `confab` | gold-**un**answerable row where the base **answers** instead of refusing |
| `known_correct_answered` | gold-answerable row where the base answers and grades **CORRECT** |
| `unknown_refused` | gold-unanswerable row where the base **refuses** (non-degenerate) |

Corpus in this program: TriviaQA / PopQA (gold-answerable) + KUQ
(gold-unanswerable). Reference implementation:
`experiments/j-space-cross-family-layer-contrast/mine_eval_pool.py`.

> **Trap, disclosed in-program.** The role grader reads the **whole completion**,
> not just the first JSON object, so trailing prose can reach role labels. On
> gemma, 3 of 123 rows took their refusal label from trailing prose, and 22/2815
> split rows (0.78%) disagree between whole-text and first-JSON reads
> (`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md:301-311`). Decide which
> read you want and assert it; do not inherit this by accident.

### 1.2 The split

`split_fit_heldout.py`: **FIT_FRAC = 0.40** (40% FIT / 60% held-out),
deterministic, stratified by category, per-stratum RNG seeded `f"{seed}:{cat}"`.
`SPLIT_SEED = 20260707`.

- Only `confab` and `known_correct_answered` are split.
- `unknown_refused` is **never split** - it is 100% fit-only scaffold.
- FIT fits the directions and chooses tau. Held-out produces the outcome. Nothing
  else.

**Be honest about the 0.40.** The script's own docstring says it is "the SAME
implementation choice as the Qwen3-4B predecessor, kept identical across families
for comparability, **not re-tuned per family**." It is inheritance, not
justification. It has never been shown to be a good value; it has only been shown
to be a *consistent* one.

### 1.3 Size floors

From `experiments/j-space-cross-family-layer-contrast/gates.yaml:43-53`:

> **≥ 150 held-out `confab` rows AND ≥ 250 held-out `known_correct_answered` rows.**

Realized:

| family | held-out confab | held-out known-correct |
|---|---|---|
| Qwen3.5-4B | 1,332 | 360 |
| Mistral-7B-v0.3 | 1,312 | 382 |
| Llama-3.2-3B | 872 | 334 |
| Gemma-4-E4B | 1,263 | **251** - a one-row margin over the floor |

Two things to internalize:

- **The dose-calibration pool is not this pool.** Every "usable dose" verdict in
  this entire program rests on **8 FIT confab rows and 8 FIT known-correct rows
  per cell** (`experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`).
  A tighten rate of 0.500 means *four rows out of eight*. Size your expectations
  accordingly, and budget for a larger calibration pool if you can afford it.
- **Meeting the floor by one row is meeting the floor.** Gemma's 251 is legal and
  was recorded as such. It is also fragile.

---

## 2. The read: KU direction and readout gate

This is the part that works. Reference: `build_directions.py`, `gate_fit.py`.

### 2.1 Capture

Anchor = the **final prompt token**, index `prompt_len - 1`. Capture at full
depth, float32.

> **Critical trap, and it silently produced a fully-committed wrong result.**
> Capture with `use_cache=True`. On Gemma-4-E4B (`num_hidden_layers = 42`,
> `first_kv_shared_layer_idx = 24`, `num_kv_shared_layers = 18`), blocks 24–41
> read donor K/V from blocks 22/23 **through the cache object**. Capturing with
> `use_cache=False` made hs00–hs24 bit-identical and collapsed hs25 to cos 0.732,
> decaying to 0.075 by hs42. The resulting write null (0/176) is **uninterpretable,
> not negative**, and every FIT-pool AUC derived from it was formally withdrawn
> (`experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md`, and
> `experiments/j-space-cross-family-layer-contrast/AMENDMENT.md:570-672`).
> Llama/Mistral/Qwen were unaffected (min cos 1.000000) - this bites only
> architectures with cross-block KV sharing. **Verify seam continuity across
> adjacent layers before you trust any read.**

### 2.2 The directions

Pinned `RANDOM_STATE = 20260707`. Marked LOCKED DESIGN in-repo:

1. **`u_d`** - the **KU direction**, mass-mean:
   `u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))`
2. **`pos_ctrl`** (`caution_dir`), mass-mean over FIT confab + all unknown_refused:
   `unit(mean(H[unknown_refused]) - mean(H[confab_fit]))`
3. **`neg_ctrl`** (`u_p`, confab-propensity), logistic:
   `LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000, random_state=20260707)`
   on `StandardScaler(H)`, coefficient rescaled by `scale_`
4. **`c_hat`** - the **write** axis: `caution_dir` orthogonalized against **both**
   `u_d` and `u_p`, via QR:

```python
M = np.stack([u_d, u_p], axis=1)
Q, _ = np.linalg.qr(M)
c_hat = unit(caution_dir - Q @ (Q.T @ caution_dir))
```

**`u_d` reads; `c_hat` writes.** They are deliberately orthogonal. Do not conflate
them - and note that this means a good read at a site is not even *geometrically*
the same claim as a good write there.

Standardization stats (`mu_d`, `sigma_d`, `mu_c`, `sigma_c`) come from the same
FIT population.

### 2.3 The gate

- Score: `neg_z_d = -z_d`, where `z_d` is the projection onto `u_d` **clipped to
  [-2, +2]** and standardized by that layer's FIT `mu_d`/`sigma_d`.
- Sign: confab rows have *low* doubt. **Fire iff `neg_z_d >= tau`.**
- `tau` by **Youden's J** over `np.unique(scores)`, on FIT confab vs FIT
  known-correct.
- **AUC floor 0.90.**

### 2.4 What you should expect, and the warning that goes with it

| family | site | FIT AUC | source |
|---|---|---|---|
| Qwen3-4B | hs23 / hs26 / hs29 / hs34 | 0.9905 / 0.9970 / 0.9984 / 0.9955 | `j-space-midband-write-sweep-qwen3-4b/AMENDMENT.md:124-125` |
| Qwen3.5-4B | hs20 / hs23 / hs26 / hs30 | 0.9929 / 0.9926 / 0.9941 / 0.9960 | `qwen35-4b-midband-doubt-snap/AMENDMENT.md:189-192` |
| Llama-3.2-3B | hs20/22/23/26 | 0.999 at all four | `llama-atlas-gated-wide-instrument-retest/AMENDMENT.md` |
| Gemma-4-E4B | late site | **0.9472** - weakest on record, still clears | `gemma-4-e4b-family-atlas/AMENDMENT.md:281` |

Gemma held-out, on the clean extract
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:848-866`): **0.9996–0.9999** at
hs15/18/20/22/23, 0.9980 at hs24, 0.9770–0.9891 at hs34/38/42.

Three warnings, each of which has cost someone a run:

1. **A high KU AUC predicts essentially nothing about whether the write will
   work.** Gemma reads at ≥ 0.977 from hs5 to hs42. The cross-family experiment
   records the consequence bluntly: the read profile is **SATURATED** and
   "supplies no site-selection signal"
   (`j-space-cross-family-layer-contrast/AMENDMENT.md:650-663`).
2. **A high AUROC is not by itself evidence of a KU direction.** On the doubt
   axis, a *fixed random direction* reads up to **0.97** best-orientation at some
   layers (`jspace-family-atlas/AMENDMENT.md`); gemma's random-direction control
   is elevated and spiky mid-band (0.97 at hs24, 0.85–0.94 at hs28–34).
   You must run a random-direction read control, not just report your AUROC.
3. **Population definitions move AUROCs by ~0.1.** Cross-paper AUROC comparisons
   are meaningless without identical role definitions.

---

## 3. Choosing a write site - THE UNSOLVED STEP

Read this section as a description of an open problem, not a procedure with a
guarantee.

### 3.1 What does not work

- **The read profile.** Saturated; supplies no signal (§2.4).
- **The `eff_dim` peak rule. RETIRED, and falsified 4/4.** The prediction was that
  effective-dimensionality peaks in the interior. It peaks **early-exterior** in
  every family measured: llama layer 4/28 (0.14), mistral 3/32 (0.09), Qwen3-4B
  5/36 (0.1389), gemma 4/42 (0.095). Qwen3-4B's atlas records "FALSIFIER FIRED on
  the profile limb". Gemma's profile is additionally too flat to select anything
  (0.0046–0.0058 over 9 of 10 points, peak std 0.00141 overlapping every interior
  point) - `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:392-403`. Also note
  Qwen3.5-4B peaked at hs23 while the site that actually actuated was **hs20**.
- **A fixed relative-depth constant.** A registered rule of the form
  `round(0.94 * (num_hidden_layers - 1))`
  (`doubt-snap-cross-family-confirmatory/AMENDMENT.md:158`) sits in the dead band
  for every substrate measured. **An entire cross-family null was collected at
  rd 0.94** and is a property of the site, not of the families. This is the single
  most expensive mistake in the program's history. Do not repeat it.

### 3.2 What is available: a depth band, and a correction to how it was stated

**Always convert a site to `relative_depth = layer_idx / num_hidden_layers`
before comparing it across families.** Raw `hs` indices are not comparable
between models with different block counts, and treating them as if they were is
how the rd-0.94 rule above got registered in the first place.

The depth prior was at one point written as a narrow envelope, in
`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:370-377`:

> Relative depth **0.357–0.548** is where every family that has ever actuated in
> this program does so; **no site above rd 0.607 (llama hs17) has produced a
> usable dose in any family.**

**Do not carry that sentence forward - both halves are too narrow.** Collecting
every site that has ever actuated and converting each to a depth fraction:

| family | blocks | site | rd | what it achieved |
|---|---|---|---|---|
| mistral-7b-v0.3 | 32 | hs12 | 0.375 | usable dose |
| mistral-7b-v0.3 | 32 | hs15 | 0.469 | usable dose (held-out G1 FAIL) |
| llama-3.2-3b | 28 | hs17 | 0.607 | usable dose, held-out G1 PASS 0.7420 |
| Qwen3.5-4B | 32 | hs20 | **0.625** | **the program's one promoted actuation result** |
| Qwen3-4B | 36 | hs23 | **0.639** | held-out 0.892 [0.839, 0.929] |

The envelope 0.357–0.548 contains **only mistral's two sites.** It excludes
llama's G1 PASS, and it excludes Qwen3.5-4B hs20 - the single promoted,
direction-specific, held-out success this whole program rests on. The "nothing
above rd 0.607" clause is contradicted by both qwen sites.

(Qwen3.5-4B's block count is sourced at
`qwen35-4b-midband-doubt-snap/AMENDMENT.md:17,55` - `num_hidden_layers=32`, so
hs20 = 0.625. The other block counts are the ones already cited in §3.1. The
gemma decimals in the quoted passage are correct for gemma; it is the
cross-family generalization that is wrong.)

The honest statement of the prior is wider and weaker: **everything that has
ever actuated sits between rd ≈ 0.37 and rd ≈ 0.64, and everything tested above
rd ≈ 0.71 has failed.** That is a band about a quarter of the model deep - 8 or
9 blocks on a 32-block model. It tells you where to start sweeping. It does not
tell you which site to pick, and restating it more precisely will not change
that. See `../../family-atlas/reference/read-actuate-depth.md` for the
read/actuate depth dissociation and the per-family decay measurements behind it.

Two limits worth stating explicitly, because both make the band weaker than it
looks:

- **The upper edge has never been probed.** There is no sourced example of a
  site in rd 0.64–0.71 that either worked or failed. The nearest sourced
  failures are all deeper (llama hs20/22/23/26, rd ≥ 0.714, all failing G1). An
  interval whose boundary has never been tested is a summary of where people
  happened to look, not a measured edge.
- **No family has been tested at single-block depth resolution.** Treat any
  claim that a specific 2–3-block span is good or bad as unsupported.

### 3.3 `A_lin` - the one selector still endorsed

The **linear accessibility profile**, a training-free logit lens
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:578-598`):

> `A_lin(hs_N)` = top-1 accuracy of applying the model's final norm and
> unembedding to the cached hidden state at `hs_N`, argmax over the contrast's
> answer tokens.

Used for site selection and for confound declaration (e.g. `|ΔA_lin| > 0.10`
between two compared sites ⇒ the contrast is declared confounded by linear
accessibility at registration time). It is CPU-only over cached activations, so
it is cheap - run it.

Caveat: on gemma it came back **exactly 0.0000 at every below-seam site**, so it
selected nothing there either and the tie-break decided. `A_lin` is not a solved
selector; it is a cheap one that sometimes has signal.

### 3.4 Practical recommendation

Sweep the band. Fit directions and calibrate a dose at **several** sites across
rd ≈ 0.37–0.64, run `A_lin` across all of them for the record, and let the dose
ladder tell you which sites are viable. Do not pick one site from a profile and
bet the run on it - that is precisely how the rd-0.94 null happened.

Concretely, for a model with `L` blocks, that band is roughly
`round(0.37*L) .. round(0.64*L)`: hs12–hs20 on a 32-block model, hs10–hs18 on a
28-block model, hs13–hs23 on a 36-block model. Sample it, do not enumerate it  -
4 to 6 sites spread across the band is the shape every successful cell in this
program has used, and single-block resolution has never been tested.

---

## 4. Dose calibration: the ratio-normalized ladder

This is the program's one genuinely portable primitive.

### 4.1 Why absolute doses do not port

Origin: mid-run revision **R2**, 2026-07-24
(`j-space-cross-family-layer-contrast/AMENDMENT.md:74-123`).

> "Llama-3.2-3b and mistral-7b-v03 both stopped at the registered G0
> dose-viability rule: **zero usable doses at any layer on the absolute ladder
> [25..200]**."

The mechanism, and it is fully general:

- Qwen3-4B's four selected doses sat at **0.37–0.60×** its per-layer median anchor
  L2 norm. Validated usable window **0.20–1.00×**; too weak at 0.12×; collapse at
  1.12–1.20×.
- The *same absolute doses* put llama's mid-band at **1.8–14.6×** and mistral's at
  **3.1–60×** their own median anchor norms.

That is the entire story: **residual-stream norms differ by an order of magnitude
between families, so an absolute dose is a different intervention in each one.**
Non-portability had already been observed *within* one family across layers.

*(The per-cell collapse rates for llama and mistral on the absolute ladder are
deferred to a notebook and are **NOT SOURCED**. The `collapse_rate_on_dosed = 1.0`
at dose 200 is sourced for **Qwen3-4B** hs23/hs26 only - do not attribute it to
llama or mistral.)*

### 4.2 The ladder

```yaml
dose_ladder:
  kind: norm_scaled_ratio
  ratios: [0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000]
  dose_rule: "dose = ratio x that site's own median anchor L2 norm, computed under that arm's own condition"
  usable_rule: "frac_readback_within_tol == 1.0 AND collapse_rate_on_dosed == 0.0 AND FIT confab clean_tighten >= 0.5"
  selection_rule: "highest FIT confab tighten, then lower known-correct cost, then lower ratio"
```

Eight geometric rungs, common ratio `20^(1/7)`. Rungs 2–5 (0.153–0.554) cover the
validated 0.20–1.00× band. The median anchor L2 norm is computed **per site, from
your own model's activations** - that is the whole point.

```python
def dose_is_usable(rec, min_confab_rate):
    return bool(rec["frac_readback_within_tol"] == 1.0
        and rec["collapse_rate_on_dosed"] == 0.0
        and rec["confab_tighten"]["rate"] >= min_confab_rate)
```

Readback tolerance: **within 5% + 0.5 absolute** of the calibrated dose, on every
dosed row. Write law: `erase_write`, position `anchor_onward`.

**Zero usable rungs at a site is a result, not a failure.** Record it as a
dose-viability NOT-RUN with the full per-rung table, and do not widen the ladder
to chase a pass. Registering the ladder in advance and leaving it alone is what
makes a null interpretable.

### 4.3 How much to trust it

The ladder **passed a back-recovery test** - it recovers Qwen3-4B's four selected
doses within one rung (all in [r3, r4], 4–14% from the nearest rung), from 296 FIT
rows. That is **one** confirmatory data point, on the family it was derived from,
introduced mid-run on 2026-07-24. **No family has yet produced a promoted held-out
actuation result using the ratio ladder.** Present it as the right design, not as
a validated calibration.

---

## 5. Placebo calibration - mandatory, per family, and this is where claims die

**If you skip this section, you have not measured what you think you measured.**
A dosed write that raises hedging tells you a vector of that magnitude at that
site changes behavior. It does not tell you the KU readout is doing the work.

### 5.1 The one-slide argument

Mistral-7B-v0.3, hs16, same effect, two placebo designs
(`rr3-corrected-placebo-replication/AMENDMENT.md`):

| design | random draws | denominator | effect ratio | verdict |
|---|---|---|---|---|
| RR2: flat ±2-point band | 1 (lift +7.39) | - | 5.7× | **PASS** |
| RR3 / RG1: K≥3, max-over-seeds | 3 (+13.3, −7.4, **+21.8**) | 0.218 | **1.87** | **FAIL** |

Gated lift was +40.9 points (baseline 0.286 → 0.694). A single random direction
lifted hedging by **+21.8 points** on its own. The RR3 verdict is **FALSIFIED**.

**Single-seed placebo controls flip verdicts.** Do not use one draw. The historical
single seeds later turned out to sit at roughly the **53rd percentile** of their
families' distributions - unremarkable draws that had been trusted as
characteristic.

### 5.2 The three generations, and which to use

| gen | experiment | criterion | why superseded |
|---|---|---|---|
| 1 | `qwen35-4b-midband-heldout` G3(i) | random arm within **2 points** of baseline | one draw; no notion of variance. Passed against a 0.000 baseline. |
| 2 | `rr3-corrected-placebo-replication` **RG1** | gated lift ≥ **3.0 ×** max over **K ≥ 3** fresh seeds | self-contained; a poor estimate of the tail at small K |
| 3 | `gate-contribution-factorial` **S1** | ≥ 3.0 × the **per-family census null** (K=15 max abs delta), **or** sign-opposition to the census null median | needs a census the family may not have |

**Use S1 if your family has a census. Use RG1 if it does not. Never use the flat
band** - RR3 forbids it explicitly, and gen-1 passed only because its narrow
baseline happened to be 0.000.

Census constants where they exist: **qwen 0.0833, mistral 0.2033**. **No census
exists for gemma-4-E4B, nor for the Qwen3-4B hs34 point** - two of five substrates.
**Do not borrow another family's constant.** That imports one model's
random-direction sensitivity as if it were yours, which is the exact error the
whole ratio-ladder finding is about.

### 5.3 Draw hygiene (copy this; it is not optional)

- **K ≥ 3** is a hard floor - the reference implementation *raises* below it.
- **Quality bar (SC1):** accept a draw only if `|cos(r_hat, c_hat)| ≤ 0.015` **and**
  `|cos(r_hat, u_d)| ≤ 0.015`. At `hidden_dim = 2560` only about a third of raw
  draws clear this - you need a **void-and-redraw ledger** (7 qwen and 15 mistral
  raw draws were voided in the census). Commit the ledger, voids included.
- **Magnitude match exactly**, and verify by readback against the same tolerance
  the real arm uses. A known defect to guard against: passing the gain as the
  sigma argument realizes `gain**2` instead of `gain*sigma`. The first-generation
  census runs hit this; the mis-dosed runlogs were quarantined and never graded,
  and a `sigma != gain` assertion is now pinned as a regression guard.
- **Decide what you are controlling for.** Holding the *fired rows fixed* and
  varying only the direction asks "does it matter which direction is written at
  the rows the readout selected". *Permuting* the fire set varies gate and
  direction together and asks a different question. They are not substitutes.

### 5.4 The result you should brace for

`placebo-seed-distribution-census/AMENDMENT.md`, K=15 seeds per family:

| family | verdict | fraction | median lift |
|---|---|---|---|
| qwen35_4b | SURVIVES (robust) | f_neg 14/15 = 0.933 | **−6.00** |
| mistral7b_v03 | SURVIVES (boundary) | f_pos 12/15 = 0.800, *exactly* at the floor | **+7.00** |
| llama32_3b | **NULL CONTROL DID NOT HOLD** | f_neg 12/15 = 0.800 | **−7.67** |

> **"Matched-magnitude random directions are NOT behaviorally inert anywhere."**

**Llama is not a usable null control.** A matched-magnitude random direction
*reliably suppresses* refusal in llama, so any specificity ratio computed there is
comparing quantities of opposite sign. Llama cannot be your "random directions do
nothing" demonstration.

Mistral's own verdict is one seed from INDETERMINATE - a canonical-refusal-only
rescore would give 11/15. And the census discloses a join defect (SC3) under which
the verdicts would have read qwen INDETERMINATE / mistral RETIRED. Read the
caveats in that file before citing it.

---

## 6. Adjudication, and the selectivity gate that cannot be measured

Reference thresholds
(`j-space-cross-family-layer-contrast/gates.yaml`, transcribed across experiments):

- **G1 (actuation):** held-out confab `clean_tighten` **≥ 0.50**, Wilson lower
  **> 0.40**.
- **G2 (selectivity):** held-out known-correct `not_well_formed_correct`
  **≤ 0.05**, Wilson upper **< 0.10**.

### G2 is, at realistic pool sizes, unmeasurable - and you must not report it as a pass

The dosed known-correct denominator is **0 on every family**: llama hs17
**0/334**, mistral hs15 **0/382**. Rows are only dosed when the KU gate fires, and
the gate correctly almost never fires on known-correct rows. Proof of invariance
on record: `successes = 2` is identical at two mistral layers under *different
doses* - the metric is not responding to the intervention at all.

The arithmetic (`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:872-928`): a
Wilson-95%-upper cap of `< 0.10` is **unsatisfiable below N = 35**
(`wilson_upper(0, 35) = 0.0989`; at N = 34 it is 0.1015). Below that N, even a
flawless 0/n cannot clear the cap, so no observation can distinguish harmless from
harmful.

Adopt the three-way disposition:

- `n_fired_known ≥ 35` → **ADJUDICABLE**, report with Wilson interval.
- `n_fired_known < 35` → **NOT-ADJUDICABLE** - distinct from PASS and from FAIL.
  Not a pass, not a fail, and **may not be cited as evidence the intervention is
  harmless.**
- Either way, if the fired-only rate exceeds the cap while the full-population
  number passes, that goes in the headline, not a table.

> **A vacuous pass is recorded as a vacuous pass, never as a pass.**

This is the expected cost of a near-perfect readout gate: the better the KU
direction separates, the fewer known-correct rows are ever dosed, and the less
there is for a cost metric to measure. It also means **the primary safety metric
in this program has never been genuinely measured on llama, mistral, or gemma.**
If you need a real selectivity number, you need either ≥ 35 fired known-correct
rows or a different instrument.

---

## 7. Traps, each one a real historical failure

1. **`use_cache=False` on a KV-sharing architecture** silently produced a
   clean-looking, fully-committed, entirely wrong null (§2.1).
2. **An absolute dose ladder** - 2–60× off-scale on unseen families (§4.1).
3. **A fixed relative-depth site rule** - rd 0.94 wasted a whole cross-family null
   (§3.1).
4. **A single-seed placebo** - flipped a verdict from 5.7× PASS to 1.87× FAIL
   (§5.1).
5. **Borrowing another family's census constant** - the same category error as (2).
6. **Reporting a vacuous G2 pass as a pass** (§6).
7. **Grading the whole completion when you meant the first JSON object** (§1.1).
8. **Assuming the gate is doing the work.** See §8.
9. **Cheap defense worth copying:** re-grade a reused undosed baseline against its
   original calibration figure as a grader-drift check. One such check re-graded
   at 0.1624 (236/1453) against a calibration 0.164 [0.146, 0.184] - it costs
   nothing and would catch a silent grader change.

---

## 8. The honest scoreboard

### Which families have a promoted, direction-specific, held-out actuation result?

**One. Qwen3.5-4B at hs20. And it is qualified.**

| family | held-out actuation | direction-specific? | status |
|---|---|---|---|
| **Qwen3.5-4B (hs20)** | PASS - refusal 0.678 [0.652, 0.703], format 0.977, cost 0.039 | S1 **PASS 7.27** | **PROMOTED**, qualified |
| Mistral-7B-v0.3 (hs16) | benefit PASS (0.694–0.699), cost PASS | RG1 **FAIL 1.87**; S1 **FAIL 2.03** | **not** direction-specific |
| Mistral-7B-v0.3 (hs15) | G1 **FAIL** - 0.4893 [0.4624, 0.5164] vs 0.50 floor | - | FAIL |
| Llama-3.2-3B (hs17) | G1 **PASS** - 0.7420 [0.7119, 0.7699]; G2 0.0120 but **non-diagnostic (0/334)** | **never tested** | not promotable; null control broken |
| Qwen3-4B (hs23) | 0.892 [0.839, 0.929], cost 0.035 (9/258) | no census, no S1 | not carried through modern specificity |
| Gemma-4-E4B | **NOT RUN** - instrument invalid, then re-scoped | none | open |

The cross-family experiment itself resolves **VERDICT INCONCLUSIVE** (signed
2026-07-24) because fewer than three families ran past G0.

### The qualification on the one success

Qwen's S1 ratio of 7.27 is driven by **sign-opposition** plus an unusually small
denominator (census max |delta| 0.0833): `0.6059 / 0.0833 = 7.27`. That is not the
same quality of evidence as a large ratio against a wide null.

And in the same experiment that produced it, the **gate axis was FALSIFIED in both
families** (`gate-contribution-factorial/AMENDMENT.md`):

| | baseline | permuted-gate `c_hat` | true gate |
|---|---|---|---|
| qwen | 0.0833 (111/1332) | **0.5495** (732/1332) | 0.6892 (918/1332) |
| mistral | 0.2820 (370/1312) | **0.5998** (787/1312) | 0.6944 (911/1312) |

> **"The write, not the gate, supplies most of the abstention behavior at these
> operating points."**

`Gap_Sel(c_hat)` fails its 0.20 floor in both families (qwen 0.1480 [0.1191,
0.1772], mistral 0.1285 [0.1034, 0.1556]), and the cost-protection limb fails in
both. This **falsified** an earlier claim that the write is non-selective and all
selectivity comes from the gate.

So: at current operating points, most of the effect is the dosed write, and the
KU readout gate contributes comparatively little. If your goal is a *gated*
intervention, that is the finding to design against.

### Why read-but-not-write? Four live explanations, none adjudicated

`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:954-1015`:

1. **Linear accessibility / crystallization gap** (arXiv 2604.15557) - named as
   the strongest competitor. Predicts high gate AUC with zero tighten *and* no
   window between inert and collapse.
2. **Representational entanglement** (2605.05715).
3. **Generic self-repair / Hydra effect.**
4. **Steering-vector non-identifiability** (2602.06801).

---

## 9. Minimum viable reproduction

If you want the cheapest run that produces an honest answer for a new model:

1. Mine the pool; check AG0a answer-capture ≥ 0.90 and the 150/250 held-out floors.
2. Split 40/60, `SPLIT_SEED = 20260707`, `unknown_refused` fit-only.
3. Capture anchors at full depth, float32, **`use_cache=True`**; verify no
   adjacent-layer cosine discontinuity.
4. Fit `u_d`/`c_hat` at 4–6 candidate sites spread across **rd 0.37–0.64**
   (§3.4); require gate AUC ≥ 0.90; verify byte-identical refits. Run a
   **random-direction read control** (§2.4).
5. Run `A_lin` across those sites, CPU-only, for the record.
6. Calibrate the **ratio ladder** at each site. Sites with zero usable rungs are
   NOT-RUN - record and move on.
7. **Before any held-out claim**, run K ≥ 3 (prefer 5) matched-magnitude random
   directions at the selected dose, SC1-screened with a committed redraw ledger.
   Compute the effect ratio against the max.
8. Adjudicate G1 on held-out. Report G2 with its `n_fired_known`, and label it
   **NOT-ADJUDICABLE** if that n is below 35.
9. Publish the null if it is a null. Do not widen the ladder.

Expect the read to work and the write to be hard. That asymmetry is the current
state of the finding, not a defect in your setup.

---

*Sources are `experiments/<slug>/AMENDMENT.md` and adjacent `gates.yaml`/`cell.yaml`
as cited inline. Items marked NOT SOURCED are recorded in this repo only in
notebooks, analysis JSON, or `docs/` files and should not be cited as experimental
fact.*
