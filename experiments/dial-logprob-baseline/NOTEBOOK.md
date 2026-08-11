# Dial token-logprob baseline (LP) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s header claimed a draft/not-signed (or otherwise stale) status that contradicted `experiment.yaml`'s machine state (`status: resolved`), which has read verdict "DATA-STAGE STOP, exactly as pre-registered" on record. Corrected the AMENDMENT.md header ("Status:" line) to match the machine state. Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction. No signed content (question, prediction, falsifier, gates, Outcome) touched.

- (add dated entries as the experiment progresses)
- 2026-07-18: BUILD+RUN+RESOLVE arc, single session. Harness built to the
  pinned cell/gates, 8-row GPU smoke clean, both arms run (~5 min wall,
  well under the 1 GPU-hr budget; launch pre-approved). LP-G0 fired its
  pre-registered data-stage stop: dial reproduction and inventories clean,
  but 30/3324 rows (0.9%) fail the exact answer-span round-trip by exactly
  one BPE token (generation-time token IDs were never cached; prompt side
  exact everywhere). Gate applied as written, no tolerance improvised
  post-hoc. Descriptive numbers (lead independently re-derived from per-row
  artifacts, byte-identical): S dial 0.8338 vs logprob 0.8198, margin
  +0.014 [-0.011, +0.040] (ambiguous band); T dial 0.8183 vs logprob
  0.6608, margin +0.158 [+0.122, +0.192]. Orchestrator pre-run call wrong
  on the base arm (predicted logprob 0.60-0.72, actual 0.820), reported
  straight. Verdict: DATA-STAGE STOP; descriptive-with-caveat only.
