# H9 held-out candidate inventory: is the AH union pool's complement usable?

Date: 2026-07-10. CPU-only, read-only. No GPU touched, no commits made, no
writes outside `docs/review/` in the repo (a throwaway verification script
lives in the session scratchpad, outside the repo, and is not part of this
deliverable).

Follow-up to `docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md`,
which flagged as unresolved: can the non-selected portion of the 18,496-row
AH union pool serve as a concrete held-out candidate list for an H9 draw?

## Verdict: YES, cleanly recoverable, with one hard limitation restated

The complement is fully recoverable by pure set arithmetic on two already-
on-disk JSONL files, no re-fit of any classifier needed. **Complement count:
16,834 rows.** No orphans, no row_key collisions, zero exact-text duplicates
either within the complement or between the complement and AL's fit surface.
Every complement row carries question text, a gold answerability label, and
a source tag — enough to stratify a draw to match the fit surface's source
mix. The hard limitation from the prior memo stands unchanged: **none of
these 16,834 rows has ever been forward-passed through the AI-TRUE
checkpoint**, so a draw from this list still requires the local-GPU
extraction + generation + grading pass costed in the prior memo (~15
GPU-minutes for a 500-row draw). This step resolves feasibility of the
*candidate list*, not the extraction requirement.

## 1. Where the union pool's row-level identity lives

`pool_v21_composition.json` itself does not enumerate the 18,496 union rows
— it only records the aggregate `union_n: 18496` and derived statistics. The
row-level identity source is the **builder function**, not a static file:

`archive/experiment/phase1/probe/amendments/amendment_ah_stage0_expand_pool.py:73-114`
(`build_union()`, read in full) assembles the union in memory each run from
two concrete on-disk inputs, both present and read directly for this check:

- `experiment/phase1/probe/analysis/ah_stage0/pregen/rows.jsonl` — the
  original 5,000-row mined pass. 5,000 lines, verified via `wc -l`. Per-row
  fields: `row_key, label, question, aliases, source, prompt_len, safe_key,
  config_sha`. No `category`/`category_canon` field directly on these rows.
- `experiment/phase1/probe/analysis/ah_stage0/expansion/score/scored_rows.jsonl`
  — the expansion pass. 13,496 lines, verified via `wc -l`. Per-row fields:
  `row_key, safe_key, label, source, question, aliases, category,
  category_raw, category_canon, score_L20/L24/L28, fold_scores,
  caution_dist, caution_dist_z`.
- 5,000 + 13,496 = **18,496**, matching `union_n` exactly
  (`amendment_ah_stage0_expand_pool.py:123` prints this count at build time;
  reproduced independently here by loading both files and taking the union
  of `row_key`).
- A third input, `experiment/phase1/probe/analysis/ah_stage0/expansion/mined_kuq_category_backfill.jsonl`
  (1,768 lines), supplies `category` for the original-pass `kuq_ku_unknown`
  rows only (script docstring line 23: "Category on the original 1,768 KUQ
  rows comes from the backfill sidecar"; confirmed: exactly 1,768 backfill
  keys, all of source `kuq_ku_unknown`, 100% coverage of that source in the
  mined pass).

I did NOT need to re-run `build_union()` itself (which additionally requires
fitting the AF-600 caution classifier via `load_af_caution()`, a separate
GPU-adjacent extraction dependency) because the caution axis is only used
for the caliper-MATCHING step that selects the 1,662-row pool, not for row
identity. Row identity — the only thing this check needs — is fully
determined by the union of the two JSONL files' `row_key` sets.

## 2. The complement: union minus AL's 1,662 fit rows

Verified by direct computation (script:
`/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/h9_holdout_check.py`,
session scratchpad, not part of the repo):

- `orig_keys` (5,000) and `exp_keys` (13,496) have **zero row_key overlap**
  with each other (disjoint namespaces: `ah::...` for mined, `ahx::...` for
  expansion, confirmed by direct set intersection = 0).
- Union of the two = 18,496 unique row_keys, exactly matching
  `pool_v21_composition.json`'s `union_n`.
- AL's fit surface, `experiment/phase1/probe/analysis/ah_stage0/expansion/pool_v21.jsonl`
  (1,662 lines, read directly), has **zero orphan row_keys** — every one of
  its 1,662 `row_key` values is found in the reconstructed union. This
  cross-checks that `pool_v21.jsonl` is genuinely a subset of the union, not
  a separately-drawn population that happens to share a naming scheme.
- **Complement = union minus fit surface = 16,834 rows** (18,496 - 1,662).

**Complement per-source breakdown** (counts; AL fit-surface counts shown
alongside for the source mix a stratified draw would need to match):

| source | complement | AL fit surface (already used) | union total |
|---|---|---|---|
| triviaqa | 5,921 | 79 | 6,000 |
| popqa | 3,923 | 77 | 4,000 |
| kuq_ku_unknown_x | 2,745 | 751 | 3,496 |
| selfaware_answerable | 1,917 | 117 | 2,034 |
| kuq_ku_unknown | 1,313 | 455 | 1,768 |
| selfaware_unanswerable | 600 | 132 | 732 |
| kuq_ku_known | 415 | 51 | 466 |
| **total** | **16,834** | **1,662** | **18,496** |

**Complement label breakdown:** `known` (maps to `answerable`, matching
AL's `gold_class` convention exactly) 12,176; `unknown` (maps to
`unanswerable`) 4,658.

**Complement pass breakdown:** `expansion` 12,589; `mined` 4,245.

## 3. Do complement rows carry what a draw needs?

**Question text:** present on all 16,834 complement rows (both source
files carry a `question` field directly; verified no missing values).
Per project convention, this row-level text is gitignored and stays local —
it is not reproduced in this markdown file beyond a few redacted excerpts
already visible in on-disk JSONL that this report does not duplicate.

**Gold answerability class:** present as `label` (`known`/`unknown`) on all
16,834 rows, the identical field AL's own pool used to derive `gold_class`
(`experiments/radial-anti-propensity-steering/AMENDMENT.md` section 3.1
census language "90 correct / 120 wrong / 114 answerable-refused / 1,222
unanswerable-refused / 116 confab" is itself derived from this same
known/unknown split crossed with generated behavior). This is sufficient to
stratify a draw by answerability, but **not sufficient by itself to derive
confab/correct/wrong/refused behavior classes** — those require running the
question through the AI-TRUE checkpoint and grading the output, exactly the
GPU step costed in the prior memo. Nothing in the complement pre-empts that
requirement; it only fixes which QUESTIONS a draw could use.

**Aliases (needed for TriviaQA/PopQA-style correctness grading):** present
as an `aliases` field on all rows in both source files (verified: zero rows
missing the field in either file; empty lists are legitimate for
unanswerable-by-construction sources, not a data gap — 2,500/5,000 mined
rows and 3,496/13,496 expansion rows have empty `aliases`, consistent with
`unknown`-labeled rows needing no answer alias).

**Category / refusal-flavor tag (`category_canon`, used in AL's per-row
flavor breakdown):**
- Fully populated for `kuq_ku_unknown_x` complement rows via the expansion
  pass's own `category_canon` field: 2,745 rows split
  `counterfactual` 503 / `ambiguous` 280 / `false_assumption` 429 /
  `future_unknown` 597 / `unsolved_problem` 404 / `controversial` 532 (sums
  to 2,745, no missing/empty values).
- Fully populated for `kuq_ku_unknown` complement rows via the backfill
  sidecar: all 1,313 complement rows of this source have a non-empty
  backfill category (0 missing).
- **Absent** for `selfaware_answerable` (1,917), `selfaware_unanswerable`
  (600), and `kuq_ku_known` (415) complement rows — 2,932 rows total. This
  is NOT a data gap specific to the complement: AL's own fit-surface exhaust
  (`amendment_al_run/gates_report.json` `primary_flavor_breakdown`) shows a
  `"(none)"` bucket for exactly this reason — SelfAware and KUQ-known items
  were never assigned a refusal-flavor category in this program, on the fit
  surface either. A stratified draw that wants flavor coverage should draw
  from `kuq_ku_unknown` / `kuq_ku_unknown_x` for that axis and treat
  SelfAware/known-KUQ rows as flavor-`(none)`, same as AL did.

**Source labels:** present and consistent (`source` field, 7 distinct
values, matches the fit surface's own source vocabulary exactly).

## 4. Contamination checks

**Exact-text duplicates within the complement:** zero. Checked all 16,834
complement questions (lowercased, whitespace-trimmed) for exact repeats:
16,834 distinct texts, 0 repeated. Checked `triviaqa` (5,921) and `popqa`
(3,923) specifically, since these are the sources most likely to carry
templated or repeated trivia questions across a large mined sample: 0
repeats in either.

**Exact-text duplicates between the complement and AL's fit surface (the
critical leakage check):** zero. AL's `pool_v21.jsonl` does not carry
question text directly (confirmed: 0 of 1,662 rows have a `question` field;
"question text joined in at staging time" per
`experiments/radial-anti-propensity-steering/cloud/runpod_al_true_a0.sh:4`),
so I resolved each fit-surface `row_key` back through the reconstructed
union (100% resolved, 1,662 of 1,662) to recover its question text, then
compared that set against the complement's question-text set. **No
collisions.** This is the check that matters most for H9: if a complement
row's question text exactly matched a fit-surface row's question text under
a different `row_key`, scoring it on the frozen direction would be
effectively re-scoring a fit row under an alias. That did not happen.

**Other-checkpoint extraction overlap (informational, not a blocker):** the
entire 18,496-row union — meaning the full complement plus the fit surface
— has already been forward-passed once before, but on the **GRPO-v2
checkpoint**, not AI-TRUE:
`experiment/phase1/probe/analysis/amendment_al_prep/grpo_v2_extract_union/data/manifest.json`
records `n_pool: 18496, n_written: 18496`,
`adapter_repo: .../schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`
(a different adapter than AI-TRUE's
`amendment_ai_grpo_true_seed1/20260703_234933/final_model`). This does not
contaminate an AI-TRUE held-out draw — different checkpoint, no leakage into
the AI-TRUE fit — but it does mean every complement row is already known to
tokenize and forward-pass cleanly (the GRPO-v2 pass completed 18,496/18,496
with a determinism spot-check pass), which lowers the risk of a new AI-TRUE
extraction hitting a malformed or degenerate prompt among the draw.

**Near-duplicate (non-exact) question risk:** not checked beyond exact-text
matching. KUQ's `kuq_ku_unknown` and `kuq_ku_unknown_x` are two separate
mining passes over what may be overlapping underlying item banks
(paraphrase-level near-duplicates are plausible given the shared source
family), but the exact-text check found none, and a paraphrase-similarity
sweep is a further CPU task not attempted here — flagging as a residual,
low-severity risk for whoever finalizes the draw, not a blocker to
recoverability.

## Structured summary (for the lead)

- **Recoverable:** YES. Pure set arithmetic on two on-disk JSONL files
  (`ah_stage0/pregen/rows.jsonl`, `ah_stage0/expansion/score/scored_rows.jsonl`),
  no classifier refit needed, no GPU touched.
- **Complement count:** 16,834 rows (18,496 union − 1,662 AL fit surface).
- **Per-source counts (complement):** triviaqa 5,921; popqa 3,923;
  kuq_ku_unknown_x 2,745; selfaware_answerable 1,917; kuq_ku_unknown 1,313;
  selfaware_unanswerable 600; kuq_ku_known 415.
- **Grading-fields status:** question text 100% present; gold
  answerability label (`known`/`unknown`) 100% present; aliases field 100%
  present (empty where legitimately inapplicable); refusal-flavor category
  100% present for KUQ-unknown sources (both passes), absent for
  SelfAware/KUQ-known sources — matching the fit surface's own coverage
  pattern exactly, not a complement-specific gap. Behavior labels
  (correct/confab/refused) are absent everywhere in the complement, as
  expected, since those require a fresh AI-TRUE generation + grading pass
  (already costed in the prior memo at ~15 GPU-minutes for 500 rows).
- **Contamination flags:** none found. Zero exact-text duplicates within
  the complement; zero exact-text collisions between complement and AL's
  fit surface (the critical check); the whole union was already
  successfully forward-passed once on a different checkpoint (GRPO-v2, not
  AI-TRUE), which is informational reassurance, not a leakage path. One
  residual, unchecked, low-severity risk: paraphrase-level (non-exact)
  near-duplicates between the two KUQ mining passes were not swept.
- **Blockers for a stratified ~500-row draw:** none from the candidate-list
  side. The remaining blocker is exactly the one already named in the prior
  memo — a fresh local-GPU AI-TRUE extraction + generation + grading pass is
  required before any of these 16,834 rows can be scored against the frozen
  propensity direction, plus the one-time CPU task of re-deriving and
  freezing the AL scoring pipeline's PCA/scaler/caution-regression objects
  (never persisted; see the prior memo section 1).
