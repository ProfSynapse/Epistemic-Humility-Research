# Amendment SR — Sampled-decode seed-robustness of the training-free two-signal readout

**Status:** PRE-REGISTERED (2026-07-01), training-free readout, local Docker GPU
lane. Registered BEFORE any extraction. This hardens the headline magnitudes of
the [[AMENDMENT-Z-cross-family-confirmatory]] cross-family CLAIM against a
single-decode confound; it does NOT retrain anything.

Tier-2 amendment. One branch (`pr/seed-robustness-sampled-decode`, off an
up-to-date `main` — the Z scoring/extraction scripts are on `main` after PR #136),
one PR. Gates LOCKED below before the first run; goalposts do not move after the
result. **No GPU run without explicit user launch approval naming the exact
cells/seeds/lane.**

## Why this experiment

Z promoted the training-free two-signal readout — answerability **gate** (pre-gen
anchor) + correctness **dial** (post-gen answer token) + the dial **veto** on
confident hallucinations — to a cross-family claim across four families (Qwen,
Llama, Mistral, Gemma). But every Z magnitude was produced with a **single greedy
decode** (`do_sample=False`, one fixed `--seed`). Greedy is deterministic, so the
reported dial/veto AUROCs have **no decode-level variance estimate** — the only
variance in Z's CIs comes from CV folds and the bootstrap, not from the choice of
generated answers.

That is the open confound for the headline: the dial reads correct-vs-wrong on the
*answers the model actually produced*, and the veto reads trust on the *specific
hallucinated text* the model produced. Both pools are decode-dependent. A
single-seed magnitude could be a lucky (or unlucky) draw. Before the Paper 3
magnitudes are presented as stable, they need to survive **sampled decoding across
multiple seeds**.

This amendment re-runs the identical readout under **sampled decoding**
(`temp 0.7 / top_p 0.9`) across **3 seeds** on the **four confirmatory families**,
and asks whether the dial/veto magnitudes — and critically the Z SUCCESS verdict
(veto PASS ≥3/4) — are seed-stable.

## Scope: dial + veto ONLY (gate is decode-invariant)

The answerability **gate** is read at the pre-generation anchor token
(`prompt_len−1`), *before any token is sampled*. Its positive/negative pools are
fixed SelfAware known/unknown question sets. It is therefore **decode-invariant by
construction** and carries no seed variance. The gate is still emitted by each run
(it comes free in the same forward pass) and reported as an **invariance check**
(it should be effectively identical across seeds), but it is **NOT a seed-variance
target and NOT part of this amendment's pass/fail verdict.** The seed-robustness
verdict is about the **dial** and the **veto** — the two decode-dependent axes.

## Models (the locked set — the four confirmatory families ONLY)

Exactly the Z confirmatory set. **Qwen3-4B (the original W/X exploration base) is
deliberately EXCLUDED**: the entire point of the four independent families was to
give a confirmatory replication that lets the reader-facing paper stand without the
Qwen3 amendment scaffolding. Re-importing Qwen3-4B into the seed pass would drag
that scaffolding back in. Seed-hardening the confirmatory set — not the original
substrate — is what keeps Paper 3 clean.

| Family | HF repo | Scale | Z greedy dial / veto (seed 20260630) |
|--------|---------|-------|--------------------------------------|
| Meta Llama | `unsloth/Llama-3.2-3B-Instruct` | 3B | 0.861 / **0.633 (FAIL)** |
| Mistral | `mistralai/Ministral-3-3B-Instruct-2512` | 3B | 0.818 / **0.733 (PASS)** |
| Alibaba Qwen | `Qwen/Qwen3.5-4B` | 4B | 0.827 / **0.666 (marginal PASS)** |
| Google Gemma | `google/gemma-4-E4B-it` | E4B (~4B eff.) | 0.818 / **0.871 (PASS)** |

Note Qwen3.5-4B is a **distinct** newer model and STAYS — it is one of the four
confirmatory families, not the Qwen3-4B exploration base.

All four are ungated (verified in Z, 2026-06-30); no HF token required. Each still
passes the Z **compat smoke** (load, hidden-states tuple `n_layers+1`, non-
degenerate answered pool) as gate 0; an INELIGIBLE model is recorded with its
blocker and excluded from the denominator (silent substitution forbidden).

## Seeds and decode (LOCKED)

- **Seeds:** `20260701`, `20260702`, `20260703` (3 seeds).
- **Decode:** sampled — `do_sample=True`, `temperature=0.7`, `top_p=0.9`,
  `num_beams=1`. The generation RNG is seeded per run
  (`torch.manual_seed(seed)` + `transformers.set_seed(seed)`) so each seed is a
  reproducible independent draw. Everything else identical to Z:
  `enable_thinking=False`, same SYSTEM_PROMPT, chat template via the model's own
  tokenizer, `--n-answerable 2000`, `--max-attempts 3000`, `--max-new-tokens 48`,
  `--wrong-floor 30`, `--hallucination-floor 50`.
- **Readout positions:** unchanged (pre = anchor `prompt_len−1`; post = last
  answer content token; float32 on CPU).
- **Scoring:** unchanged (`amendment_x_cross_model_score.py` — CV linear readouts,
  layer-swept, 2000-bootstrap AUROC + CI per gate, CPU only). One score per
  (family × seed).

## Hypothesis

**H-SR:** The Z dial and veto magnitudes are seed-robust under sampled decoding:
across three sampled-decode seeds the per-family dial and veto AUROCs are stable,
and the Z SUCCESS verdict (veto PASS ≥3/4 families) holds on every seed.

## Locked gates

Per (family × seed), applying the identical Z bar:

- **SR-dial (per family × seed):** post-gen correctness AUROC ≥ 0.65, bootstrap
  95% CI excludes 0.50.
- **SR-veto (per family × seed):** confident-hallucination veto AUROC ≥ 0.65, CI
  excludes 0.50.
- **Adequacy (per family × seed):** ≥ 30 wrong AND ≥ 50 hallucination answered
  rows; otherwise the affected axis is UNDERPOWERED for that seed (reported,
  excluded from that axis's verdict for that seed only). A family whose pool falls
  below floor on a seed triggers `DATA_STAGE_STOP` for that run — it is not padded
  or substituted.

**Seed-stability classification (derived):**
- A family is a **seed-stable dial PASS** if SR-dial passes on **3/3** seeds.
- A family is a **seed-stable veto PASS** if SR-veto passes on **≥2/3** seeds.
- **Per-seed veto majority:** on each individual seed, count families with a veto
  PASS. The Z verdict is "≥3/4 pass."

## Success / falsifier (LOCKED before running)

- **SUCCESS (hardens the Z magnitudes):** (a) the dial is a seed-stable PASS on
  **4/4** families, AND (b) the veto is a seed-stable PASS on **≥3/4** families,
  AND (c) the per-seed veto majority is **≥3/4 on every one of the 3 seeds** (the
  headline verdict never flips with seed). This promotes the Z magnitudes from
  "single greedy decode" to "seed-robust under sampled decoding."
- **FALSIFIER:** the veto verdict is **seed-fragile** — i.e., on **≥1 seed** the
  per-seed veto majority drops below 3/4, OR **≥2 families** flip veto PASS/FAIL
  status across the 3 seeds. Either shows the single-seed Z magnitude was a decode
  artifact, and the Paper 3 magnitudes must be re-reported with the decode
  variance (or the veto claim re-scoped) rather than as stable point estimates.
- **Descriptive-only (no gate):** the across-seed spread of each AUROC
  (mean ± range, and std) is reported for the dial and veto of every family as the
  quantitative stability readout, but no spread threshold gates the amendment. The
  gate invariance check (near-identical gate AUROC across seeds) is likewise
  descriptive confirmation, not a gate.

Live-falsifier honesty note (pre-stated): the two axes most likely to flip are the
ones on the Z margin — **Llama's veto (greedy FAIL 0.633)** and **Qwen3.5's veto
(greedy marginal 0.666, CI floor 0.634)**. Sampled decoding could push either
across 0.65 in either direction. Gemma (0.871) and Ministral (0.733) are the
expected-stable passes. The falsifier is genuinely reachable; the result is not
pre-ordained.

## Method (identical readout to Z — no new training; one decode change)

For each (model, seed):
`amendment_x_cross_model_extract.py --base-model <repo> --seed <seed> --do-sample
--temperature 0.7 --top-p 0.9` builds the same mixed pool (PopQA + TriviaQA
answerable graded → dial pool; SelfAware known → gate positives + control;
SelfAware unknown forced → hallucination = veto pool) and persists pre/post hidden
states, then `amendment_x_cross_model_score.py --x-dir <out>` scores it.

### Code change (this amendment, backward-compatible)

`amendment_x_cross_model_extract.py` gains three optional flags — `--do-sample`
(default False), `--temperature` (default 1.0), `--top-p` (default 1.0) — wired
into the single `model.generate(...)` call, plus a per-run
`transformers.set_seed(args.seed)` / `torch.manual_seed(args.seed)` immediately
before the generation loop. **Default behavior is byte-for-byte unchanged**: with
no `--do-sample`, the call remains `do_sample=False, num_beams=1` exactly as Z ran
it, so Z is reproducible from the same script. The manifest records
`decode: "sampled(temp=0.7,top_p=0.9)"` and the seed so each output pool is
self-describing. No scoring change.

## Run order (single GPU, sequential — 12 runs = 4 families × 3 seeds)

Grouped by family (reuse the loaded weights across the 3 seeds where the harness
allows; otherwise reload per run):

1. `unsloth/Llama-3.2-3B-Instruct` — seeds 20260701, 20260702, 20260703
2. `mistralai/Ministral-3-3B-Instruct-2512` — seeds 20260701, 20260702, 20260703
3. `Qwen/Qwen3.5-4B` — seeds 20260701, 20260702, 20260703
4. `google/gemma-4-E4B-it` — seeds 20260701, 20260702, 20260703

Each run: (compat smoke once per family) → sampled extraction → CPU score →
append result + update session/experiment notes. Cost ≈ 3× the Z overnight queue
(12 extractions vs 4). Failures logged; the queue continues.

## §7 Results (filled per family × seed as runs complete)

**Status: QUEUE COMPLETE 2026-07-01 16:54 UTC (launched 10:11 UTC, user approval, local
Docker GPU lane) — 9/12 cells scored. Llama, Ministral, Qwen3.5 = 3/3 seeds each (all 9
eligible). Gemma-4-E4B DID NOT RUN: its compat smoke crashed on a transient 9P/DrvFS
`PermissionError [Errno 13]` at `out_dir.mkdir(...)` BEFORE the model loaded (the other 12
in-container dirs — 3 smoke + 9 seed — created fine via the same call; Gemma was last in the
queue and hit a filesystem hiccup on the Windows mount). This is a RETRYABLE INFRA FAULT, NOT
a scientific ineligibility: Gemma passed this exact greedy smoke in Z with the same
`unsloth-z:latest` image, and the pre-reg INELIGIBLE category (gated 401 / multimodal class
mismatch / FP8 dtype fail / degenerate pool) does not cover a mkdir error. Disposition: Gemma
= RE-RUN PENDING (needs explicit GPU launch approval), NOT recorded INELIGIBLE.**

**Verdict status — the 3 eligible families are unanimous and strong: dial 9/9 PASS (0.799–0.865),
gate decode-invariant (0.9964–0.9986, range <0.003/family), veto seed-stable PASS on all three
(Llama 3/3, Ministral 2/3, Qwen3.5 3/3). SUCCESS parts (a) dial and (b) veto ≥3/4 are met on the
eligible set. The verdict genuinely HINGES ON GEMMA via the strict per-seed clause (c): seed
20260702 and 20260703 are 3/3 veto PASS, but seed 20260701 sits 2 PASS (Llama, Qwen3.5) / 1 FAIL
(Ministral 0.606) — with 4 families the ≥3/4 bar needs Gemma-701 to PASS; dropping Gemma leaves
seed 701 at 2/3 (0.67 < 0.75), which does NOT clear the literal ≥3/4 bar. So the verdict is NOT
called: re-running Gemma (Z-strongest veto 0.871) is required to resolve clause (c), and it also
strengthens (b). Verdict deferred pending the Gemma re-run.**

### Per-family seed table (filling as cells land)

Gate column = decode-invariance check only (not a verdict axis). "veto PASS?" =
SR-veto ≥0.65 with CI excl 0.50.

| model | seed | dial (SR-dial) | veto (SR-veto) | adequacy | veto PASS? |
|---|---|---|---|---|---|
| Llama-3.2-3B | 20260701 | 0.827 ✓ | 0.801 | ✓ | **PASS** |
| Llama-3.2-3B | 20260702 | 0.853 ✓ | 0.684 | ✓ | **PASS** |
| Llama-3.2-3B | 20260703 | 0.865 ✓ | 0.732 | ✓ | **PASS** |
| Ministral-3-3B | 20260701 | 0.808 ✓ | 0.606 | ✓ | **FAIL** |
| Ministral-3-3B | 20260702 | 0.812 ✓ | 0.696 | ✓ | **PASS** |
| Ministral-3-3B | 20260703 | 0.799 ✓ | 0.742 | ✓ | **PASS** |
| Qwen3.5-4B | 20260701 | 0.830 ✓ | 0.659 | ✓ | **PASS** (marginal) |
| Qwen3.5-4B | 20260702 | 0.864 ✓ | 0.807 | ✓ | **PASS** |
| Qwen3.5-4B | 20260703 | 0.862 ✓ | 0.794 | ✓ | **PASS** |
| Gemma-4-E4B | 20260701 | — | — | — | *RE-RUN PENDING (9P mkdir PermissionError, infra)* |
| Gemma-4-E4B | 20260702 | — | — | — | *RE-RUN PENDING (9P mkdir PermissionError, infra)* |
| Gemma-4-E4B | 20260703 | — | — | — | *RE-RUN PENDING (9P mkdir PermissionError, infra)* |

### Seed-stability roll-up (3 eligible families; Gemma re-run pending)

| model | dial mean ± range | dial 3/3 PASS? | veto mean ± range | veto ≥2/3 PASS? | gate invariance |
|---|---|---|---|---|---|
| Llama-3.2-3B | 0.848 [0.827–0.865] | **YES (3/3)** | 0.739 [0.684–0.801] | **YES (3/3)** | 0.9964–0.9975 (Δ0.0011) |
| Ministral-3-3B | 0.806 [0.799–0.812] | **YES (3/3)** | 0.681 [0.606–0.742] | **YES (2/3)** | 0.9967–0.9975 (Δ0.0008) |
| Qwen3.5-4B | 0.852 [0.830–0.864] | **YES (3/3)** | 0.753 [0.659–0.807] | **YES (3/3)** | 0.9982–0.9986 (Δ0.0004) |
| Gemma-4-E4B | — | *pending re-run* | — | *pending re-run* | *pending re-run* |

Dial is a seed-stable PASS on **3/3 eligible** families (Gemma pending → part (a) not yet
4/4). Veto is a seed-stable PASS on **3/3 eligible** families → part (b) ≥3/4 already met on
the eligible set. Gate invariance holds (per-family across-seed range <0.0011) — sampled
decoding does not move the pre-gen anchor axis, exactly as pre-stated.

### Per-seed veto majority (3 eligible families; Gemma re-run pending)

| seed | families with veto PASS (eligible) | Gemma | ≥3/4? |
|---|---|---|---|
| 20260701 | 2/3 — Llama ✓, Qwen3.5 ✓, Ministral ✗ (0.606) | pending | **HINGES ON GEMMA** (2/4 without, needs Gemma-701 PASS for 3/4) |
| 20260702 | 3/3 — Llama ✓, Ministral ✓, Qwen3.5 ✓ | pending | **YES** (3/4 secured regardless of Gemma) |
| 20260703 | 3/3 — Llama ✓, Ministral ✓, Qwen3.5 ✓ | pending | **YES** (3/4 secured regardless of Gemma) |

### VERDICT: DEFERRED — pending Gemma-4-E4B re-run

- **Parts (a) dial and (b) veto:** met on the 3 eligible families (dial 3/3 seed-stable,
  veto 3/3 seed-stable). Adding Gemma can only strengthen (b); it is required to reach the
  literal 4/4 on (a).
- **Part (c) strict per-seed ≥3/4 majority:** seeds 702 and 703 clear it (3/4 secured);
  **seed 701 is the pinch** — 2/4 without Gemma, so Gemma-701 must post a veto PASS to reach
  3/4. Dropping Gemma leaves seed 701 at 2/3 (0.67 < 0.75 = below the literal ≥3/4 bar), so
  the verdict cannot be honestly called SUCCESS on the 3-family set.
- **Why not INELIGIBLE:** Gemma's smoke failed on a transient 9P `PermissionError` at
  `mkdir` before the model loaded — a retryable filesystem fault, not one of the pre-reg
  INELIGIBLE blockers. Gemma passed this same greedy smoke in Z with the identical image.
  Recording it INELIGIBLE would both misclassify the failure and leave (c) unresolvable.
- **Action:** re-run `gemma-4-e4b` seeds 20260701/02/03 on the local Docker GPU lane (a
  lab-notebook re-run of a pre-registered cell — not a new amendment, no goalpost change),
  then finalize the verdict. Requires explicit user launch approval before GPU use.

### Data & provenance (to fill)

- Scored result JSONs (tracked, at probe root), one per family × seed:
  `amendment_sr_{family}_seed{N}_result.json` under `experiment/phase1/probe/`.
- Extraction outputs (local only, gitignored): `sr_{family}_seed{N}/` under
  `experiment/phase1/probe/`.
- Queue log: `experiment/phase1/probe/sr_logs/PROGRESS.log`.
