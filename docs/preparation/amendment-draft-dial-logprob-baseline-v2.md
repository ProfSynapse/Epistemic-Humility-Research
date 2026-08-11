# Amendment draft — Dial token-logprob baseline, clean redo (generation-time token-ID cache)

**Status: DRAFT DESIGN, NOT SIGNED, NOT RUN.** Deliverable of a delegated design
task. Requires lead review and PI sign-off before `bin/exp new`, before any
instrument is pinned, and before any GPU launch. Nothing in this document has
been executed; no numbers below are new results — every number cited from the
predecessor cell is a resolved, governed fact, cited with its doc line.

**Proposed tier:** Tier-2 exploratory Amendment
(`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`, decision
Q2 — "introduces a NEW cell/arm that will be reported as evidence"), mirroring
the predecessor's own posture (`experiments/dial-logprob-baseline/AMENDMENT.md:36`,
"exploratory Tier-2 lab cell over existing populations. Never pooled with the
locked Phase 1 matrix or with the S/T headline readings.").

**Proposed slug:** `dial-logprob-baseline-v2`

**This is a clean redo, not a redesign.** Section 3 below is the only place
this draft departs from `experiments/dial-logprob-baseline/`'s own signed text,
and the departures are all implementation-level fixes for the one defect that
stopped the predecessor, plus one open adjudication point (§7). Everywhere
else, this document either quotes the predecessor verbatim or states "same as
v1" and points at the source line.

---

## 0. Lineage

- **Builds on:** `experiment:dial-logprob-baseline` (slug
  `dial-logprob-baseline`, resolved 2026-07-18, verdict DATA-STAGE STOP;
  `experiments/dial-logprob-baseline/experiment.yaml:30-35`).
- **Motivated by:** `papers/paper-4-two-signal-readout/manuscript.md`, §9
  limitations list, item 9 ("Token-logprob baseline: computed, descriptive
  only," `manuscript.md:1252-1274`). **Correction to the commissioning brief:**
  the brief that requested this draft cites "limitation 8" and a pending
  `SWAP: pending dial token-logprob baseline analysis` marker. Neither is
  current. The splice already happened — item 9 in the manuscript as it reads
  today already carries v1's descriptive numbers with the round-trip caveat,
  and the limitation numbering has shifted since whatever draft the brief was
  written against. The item ends with the exact charter for this draft, quoted
  verbatim: "A gated version of this comparison needs a successor cell that
  caches generation-time token IDs; until then, what this paper establishes
  about the dial on the raw base remains its cross-model geometry, its
  post-answer read advantage, and its veto behavior, not that it beats the
  model's own logprobs there." (`manuscript.md:1270-1274`).
- **Splice status going forward:** paper 4's item 9 currently cites v1's
  descriptive numbers. If this cell resolves with LP-G1 gated (pass or fail),
  item 9 is rewritten to cite the gated verdict in place of the
  descriptive-with-caveat text; if this cell also data-stage-stops, item 9 is
  left as is. No other paper-4 sentence is in scope.

---

## 1. Question (verbatim from v1)

`experiments/dial-logprob-baseline/experiment.yaml:7-9`:

> What is the correctness dial's margin over the model's own answer-span token
> log-probabilities (length-normalized mean, primary) on the exact rows the
> dial was measured on (amendment S base population primary; amendment T
> deployed arm descriptive)?

Unchanged. This cell answers the same question v1 asked; only the
answer-span reconstruction mechanism differs.

---

## 2. What v1 found, and why it stopped (read from the governed doc, not memory)

Full outcome text: `experiments/dial-logprob-baseline/AMENDMENT.md:138-182`.
The facts this draft relies on, each with its line:

- LP-G0 sub-results (`AMENDMENT.md:142-152`): dial reproduction **PASSED**
  both arms (S re-fit 0.8342 vs signed 0.834; T re-fit 0.8186 vs signed
  0.819); row inventories matched source (1836 S; 1488 T); the exact
  answer-span round-trip **FAILED**: 14/1836 (S) and 16/1488 (T) rows —
  30/3324 pooled, 0.9% — off by exactly one BPE token. Prompt side exact on
  every row; 28 of 30 failures were short by one token on the answer side.
- Mechanism (`AMENDMENT.md:147-151`, and independently confirmed below in
  §3.1 by reading the generation code itself): "generation-time token IDs
  were never cached, and BPE re-tokenization of decoded text in isolation is
  not bit-stable at span boundaries." Per the gate's own pre-registered
  wording, "any mismatch is a data-stage stop, not a result" — the stop
  fired as written, no tolerance was improvised post hoc.
- Descriptive numbers, computed for transparency on the round-trip-clean rows
  only, explicitly **NOT a gated result** (`AMENDMENT.md:154-163`):
  - S base arm (n=1822, 498 correct / 1324 wrong): dial 0.8338 vs primary
    logprob 0.8198, margin **+0.014**, paired 95% CI **[-0.011, +0.040]**
    (inside the pre-stated ambiguous band; LP-G1 would not have passed).
  - T deployed arm (n=1472, 979 correct / 493 wrong): dial 0.8183 vs primary
    logprob 0.6608, margin **+0.158**, CI **[+0.122, +0.192]**.
- Prediction assessment (`AMENDMENT.md:165-175`): the orchestrator's pre-run
  call (base-arm logprob AUROC 0.60–0.72) was **WRONG** — actual 0.8198,
  nearly matching the dial. The directional read those descriptive numbers
  suggest, caveated: the dial's clear margin over sequence probability shows
  up on the deployed, abstention-trained checkpoint, not on the raw base.
  This reading is explicitly caveated by the round-trip failure and is not a
  claim.
- Gate ledger (`AMENDMENT.md:177-179`): LP-G0 FAIL (round-trip sub-criterion)
  → data-stage stop; LP-G1 never evaluated as a gate; falsifier never fired.

**Nothing about the dial reproduction, the row inventories, the design
populations, the metric definitions, the gates, or the falsifier was wrong in
v1.** The single defect was upstream of all of that: the answer-span token
IDs fed into the logprob computation were reconstructed by re-tokenizing
decoded text instead of being read from the generation call that actually
produced them.

---

## 3. The fix

### 3.1 Where the defect actually lives (confirmed by reading the source, not just the outcome prose)

v1's populations are the amendment S and amendment T stage-2 extraction rows.
Both were produced by generation loops that already compute the exact
answer-span token IDs and then throw them away before persisting anything:

`experiments/common/readouts/amendment_s_correctness_probe_extract.py:253-266`
(amendment T's extractor, `amendment_t_correctness_readout_deployment_extract.py`,
is the same pattern at its own line numbers):

```python
with torch.no_grad():
    gen = model.generate(
        **enc,
        max_new_tokens=args.max_new_tokens,
        do_sample=False,
        num_beams=1,
        eos_token_id=eos_for_gen,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        return_dict_in_generate=True,
    )
full = gen.sequences[0]
full_list = full.tolist()
new_ids = full_list[prompt_len:]                      # <- the exact answer-span token IDs
answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()   # <- only THIS gets persisted
```

`new_ids` — the literal generation-time answer-span token IDs — exists in
memory in that loop and is never written to `rows.jsonl` or any sidecar file.
Only the decoded `answer_text` string survives. v1's harness then had to
invert `tokenizer.decode` by re-tokenizing `answer_text`, which is exactly
where BPE ambiguity at span boundaries bit it. This matches the outcome
prose's mechanism statement (`AMENDMENT.md:147-151`) exactly, and confirms
the fix target: **the defect is not fixable by post-hoc reconstruction from
decoded text under any tolerance, because the information the round-trip
needs was discarded before v1 (or this cell) ever touched the data.** The
only fix is to regenerate and capture `new_ids` (or the equivalent) at
generation time, this time.

Also confirmed present on disk (checked 2026-08-11, both files read directly,
not from memory): both source row files
(`archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2/rows.jsonl`,
1836 lines; `.../qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/rows.jsonl`,
8548 lines, of which 1488 are the answered subset v1's `cell.yaml` already
filters to) and both checkpoints
(`scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/`
and `.../schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model/`)
are present.

### 3.2 The fix, precisely: regenerate and capture, do not reconstruct

Replace v1's Method steps 1–2 (`AMENDMENT.md:60-65`, "reconstruct the exact
prompt+answer token sequence... then one teacher-forced forward pass...") with
a single generation call per row that captures both the token IDs and the
per-step logits it already computes internally, so there is no reconstruction
step left to fail:

```python
gen = model.generate(
    **enc,
    max_new_tokens=48,            # inherited verbatim from S/T's own generation cap
    do_sample=False, num_beams=1,  # inherited verbatim — same greedy decode as S/T
    eos_token_id=eos_for_gen, pad_token_id=pad_id,   # inherited verbatim, per-arm from the source manifest
    return_dict_in_generate=True,
    output_scores=True,            # THE ADDITION — captures per-step logits for free
)
new_ids = gen.sequences[0].tolist()[prompt_len:]     # cached at generation, never re-tokenized
step_logits = torch.stack(gen.scores, dim=0)          # [n_steps, vocab] — same info a teacher-forced pass would recompute
```

Because decode is greedy (`do_sample=False`) and every position after the
first is conditioned on exactly the tokens the model just emitted, `gen.scores`
at step *t* IS the teacher-forced logit distribution at that position — there
is no discrepancy to reconcile. This removes v1's separate "reconstruct, then
teacher-force" two-step and replaces it with one call that cannot desynchronize
from itself. `answer_tok_len`, the length-normalized mean, sum, and min
variants (v1 §Design step 3, `AMENDMENT.md:66-70`, inherited verbatim) are all
computed from `new_ids`/`step_logits` directly, never from re-tokenized text.

**Same render, same chat template, same system prompt, same per-arm decode
kwargs as the source cell's own run manifest** — v1's requirement
(`AMENDMENT.md:60-62`) is unchanged and is now load-bearing in a new way: any
drift in render or decode settings from the original S/T run would make the
regenerated sequence a *different* generation, not a reproduction of the
cached row, and LP-G0 (redefined below) would catch that as a failure, not
silently produce a wrong number.

### 3.3 LP-G0, redefined (the fix's actual verification point)

v1's `LP-G0` (`gates.yaml:3-9`) had three sub-criteria: dial reproduction,
row-count match, and exact round-trip of `prompt_len`/`answer_tok_len`. The
first two are **unchanged and already known to pass** (they read cached
hidden states and cached metadata, neither of which the fix touches; v1
already demonstrated both pass, `AMENDMENT.md:142-146`). Only the third
sub-criterion is redefined:

- **v1:** "reconstructed sequences round-trip cached `prompt_len`/`answer_tok_len` exactly for every row; any mismatch is a data-stage stop, not a result."
- **v2:** the regenerated `answer_text` (decoded from `new_ids`, the same
  decode call the source harness itself used) **matches the cached
  `answer_text` field byte-for-byte, for every row**; any mismatch is a
  data-stage stop, not a result, applied with the same no-tolerance-improvised
  discipline v1 used.

This is a stronger check than v1's, not a weaker one: v1 could pass its
round-trip check on a row whose *content* silently differed (a re-tokenization
that produces the same token *count* but different token *identities* would
not have been caught by the old criterion). v2's criterion catches any
divergence in the regenerated answer, not just a length mismatch, and it is
exact by construction on any row it passes: if `new_ids` decodes to the
originally cached text, then `new_ids` — used directly, no re-tokenization —
*is* the correct answer-span token sequence.

**The one real risk this introduces, named up front rather than discovered
after the run:** greedy decode is only bit-reproducible if nothing else about
the forward computation changed — batch size, attention kernel, dtype, and
hardware/driver can all perturb floating-point results enough to flip an
argmax at a token boundary. v1's S/T generation ran batch-1
(`amendment_s_correctness_probe_extract.py:250`, one `tokenizer(...)` call per
row, no batching in the generation loop). **Recommendation: run v2's
regeneration batch-1 as well**, matching the exact computational shape of the
original run, to maximize the chance of exact reproduction. If some rows still
fail even under batch-1 (a numerically plausible outcome, not assumed away
here), that is a **new, legitimate LP-G0 finding to report straight** — it
would mean even same-hardware greedy regeneration is not perfectly
deterministic on this model/framework, which is itself informative and would
be reported as such, not patched over with a tolerance chosen after seeing the
mismatch count.

### 3.4 Everything else in the Method is unchanged

v1 `AMENDMENT.md:58-82`, steps 3–6, carry over verbatim:

3. Logprob variants — primary length-normalized mean answer-span token
   logprob; secondary (descriptive only) sum and min token logprob.
4. Each variant scored as AUROC for correct(1) vs wrong(0) over all rows in
   the arm, no fit, no CV.
5. Dial per-row scores recovered by re-fitting the source cell's probe
   (`amendment_s_correctness_probe_score.py` lineage) at the source cell's
   best layer (S: L20, T: L22), asserted to reproduce the signed AUROC before
   any comparison is unblinded — this is the LP-G0 dial-reproduction
   sub-criterion, already confirmed passing in v1 and expected to pass
   identically here since it operates on the same cached hidden states.
6. Paired comparison: dial AUROC minus primary-logprob AUROC, paired
   bootstrap 95% CI, 2000 resamples, seed pinned at sign.

---

## 4. Design — populations and containment (inherited verbatim)

Both arms, both populations, both models: `experiments/dial-logprob-baseline/AMENDMENT.md:43-56`
and `cell.yaml:7-27`, unchanged:

- **Arm 1 (primary), `s_base_primary`:** amendment S Instruct-base population,
  `archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2/rows.jsonl`,
  1836 rows expected (500 correct / 1336 wrong per the source inventory), model
  `unsloth/Qwen3-4B-bnb-4bit`, no adapter, dial layer L20, dial signed AUROC
  0.834 (LP-G0 reproduction target), gated by LP-G1.
- **Arm 2 (deployed, descriptive), `t_deployed_descriptive`:** amendment T
  answered population,
  `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/rows.jsonl`,
  1488 rows expected (988 correct / 500 wrong), clean-SFT merged-16bit base +
  GRPO-v2 LoRA adapter (both pinned paths in §3.1 above, verified present),
  dial layer L22, dial signed AUROC 0.819, descriptive only, no gate.

Containment (`AMENDMENT.md:83-87`, verbatim): committed artifacts are
aggregate AUROC/margin/CI JSON plus a per-variant table under
`analysis-committed/`, and an ID-manifest (row_key list only). Per-row
logprobs, per-row token IDs, answer text, and per-row dial scores stay
gitignored under `analysis/`. No question, answer, alias, or token-id content
in any committed file — this repo is public. No OpenMOSS or bridge data is
involved.

---

## 5. Frozen inputs (to be pinned at sign; sha256 to be computed fresh, not carried from v1)

Every path below is identical to v1's; only the harness script is new. At
sign time, compute and pin sha256 for:

1. Both source row files (paths in §4).
2. Both checkpoint directories (paths in §3.1), or their manifest-recorded
   identifiers if the harness resolves them by config rather than raw
   directory hash.
3. The new v2 harness module (§3.2–3.3's regenerate-and-capture script) — this
   is the one genuinely new pinned artifact.
4. `experiments/common/readouts/amendment_s_correctness_probe_score.py` (dial
   refit module, reused unchanged).
5. `cell.yaml` and `gates.yaml`, updated per §3.3/§6 below, then pinned.

**Persistence declaration, new requirement not present in v1.** v1's
`experiment.yaml:instrument.modules` is `[]` — no harness module was pinned,
consistent with a run that (per NOTEBOOK.md, cited in §8 below) finished in
about 5 minutes, well under any persistence-relevant threshold. v2's harness
is a new pinned module and, per the current schema
(`.skills/experiments/SKILL.md:109-158`), `bin/exp sign` will refuse to sign it
without a matching `instrument.persistence` entry. Given §8's budget estimate
plausibly exceeds the 15-minute `short-run` ceiling, the harness should be
built to persist incrementally — append each row's `{row_key, new_ids,
step_logits_summary, roundtrip_ok}` to a resumable runlog as it goes
(`experiments/common/README-runlog.md` convention) — both to satisfy the
schema and because it is the natural place to run LP-G0's per-row round-trip
check the moment each row completes, rather than waiting for the whole arm.

---

## 6. Prediction, falsifier, gates

**Falsifier (verbatim from v1, `AMENDMENT.md:103-109` / `gates.yaml:16`):**
unchanged. Primary-variant logprob AUROC at or above the dial AUROC on the
primary (S base) arm, margin at or below 0, with the paired 95% CI excluding
0 in that direction. This would show the dial's separation is largely
redundant with free sequence probability.

**Gates (verbatim except LP-G0's third sub-criterion, per §3.3):**

- LP-G0 (integrity precondition, pre-outcome stop): (a) refit dial reproduces
  signed source AUROC per arm within reporting precision — unchanged; (b) row
  counts match source inventories (1836 S; 1488 T) — unchanged; (c)
  **redefined**: regenerated answer_text matches cached answer_text
  byte-for-byte for every row (§3.3), not the old re-tokenization round-trip.
- LP-G1 (primary, verbatim): dial AUROC minus primary-logprob AUROC ≥ +0.05
  on the S base arm, paired 95% CI excluding 0. Floor justification unchanged
  (matches S/T's self-eval-gain convention).
- Ambiguous band (verbatim): 0 < margin < +0.05, or CI straddling 0 →
  reported as "small or uncertain margin over sequence probability"; **the
  gate is not retuned after the result**, same discipline v1 used when its
  own descriptive number landed inside this exact band.
- Arm 2 (verbatim): reported with identical statistics, descriptive only, no
  gate.

**Prediction — the one point that is NOT a clean inheritance, flagged for PI
adjudication rather than decided here (§7).**

---

## 7. Open adjudication point: what is the v2 prediction, given v1's own descriptive numbers already exist?

This is the one place a literal verbatim carry-forward would be dishonest
rather than disciplined. v1's pre-run call was "primary logprob AUROC
0.60–0.72, dial margin positive with CI excluding 0" — and that call is
**already known to be wrong** (actual descriptive base-arm logprob AUROC
0.8198, `AMENDMENT.md:165-167`, now also published in the paper-4 manuscript
itself, `manuscript.md:1264-1266`). Re-stating the same 0.60–0.72 band as v2's
blind prediction would not be a genuine pre-registration: the drafter (and
whoever signs v2) already possesses information v1's own orchestrator did
not have when it made that call, because it is sitting in this very document.
Self-blinding forbids computing the *result* before sign, not reading an
already-published, already-caveated descriptive number that motivated the
redo in the first place — but pretending not to have seen it would be worse
than acknowledging it.

**Recommendation (for the PI to accept, adjust, or override at sign, not
decided unilaterally here):** frame v2's prediction as *informed by* v1's
descriptive numbers rather than blind to them, since that is what is actually
true:

- S base arm: v2's primary logprob AUROC lands close to v1's descriptive
  0.8198 (±0.02), landing margin near +0.014 — **most likely inside the same
  pre-stated ambiguous band**, i.e., LP-G1 most likely does NOT pass. This is
  a real, stated prediction that could still be wrong (the round-trip-failing
  30 rows could be disproportionately informative, or the 0.9% of dropped
  rows could shift the estimate more than the CI width suggests), so it is
  not vacuous.
- T deployed arm (descriptive only, no gate): expect confirmation of v1's
  +0.158 [+0.122, +0.192] margin within noise.

This framing keeps the falsifier and LP-G1's threshold exactly as pre-stated
(§6) — nothing about pass/fail criteria moves — it only changes what counts as
"the orchestrator's guess" from a re-guess to an explicit statement that the
redo is expected to *confirm v1's own descriptive read at exact precision*,
which is the honest description of what this cell is actually testing.

---

## 8. Budget and launch precondition

**GPU cost estimate — derived, not measured; recommend a pass-0 timing smoke
before committing to the full run.**

- Population: 1836 + 1488 = 3324 rows total (unchanged from v1).
- v1's own governed anchors: budgeted "about 1 GPU-hour total including model
  and adapter loads and the mandatory GPU smoke" for a **single forward pass
  per row** (`AMENDMENT.md:89-91`); actual measured wall clock was **about 5
  minutes for both arms combined**, "well under the 1 GPU-hr budget"
  (`NOTEBOOK.md:11-13`).
- v2 replaces that single forward pass with up to 48 greedy decode steps per
  row (`max_new_tokens=48`, inherited verbatim from the S/T extractors'
  own default, §3.2 — this cap cannot be changed without breaking
  reproduction of the original generation). Most answers here are short
  QA-style spans and terminate on EOS well before 48 tokens. Decode steps
  after the first are cheap relative to a full prefill forward pass (KV-cache
  amortized, single-token matmuls), so a reasonable order-of-magnitude
  multiplier over the bare single-forward baseline is roughly 5–15×, not 48×.
  No governed same-hardware precedent exists for this exact multiplier — I
  could not find a measured, governed wall-clock figure for batch-1
  generation-with-scores on this 3090 to anchor it more precisely than that;
  a companion draft (`docs/preparation/amendment-draft-wrong-answer-power-fix.md`,
  §8) cites a 2.13-hour figure for a *different* 8548-attempt/128-token
  generation run, but that figure is itself flagged there as an unverified
  file-mtime estimate on a *different, non-3090 box* — not something I am
  treating as governed precedent here.
- Applying the 5–15× multiplier to v1's measured 5-minute baseline gives
  roughly 25–75 minutes of raw generation compute; adding two checkpoint/
  adapter loads and the mandatory GPU smoke (v1 used an 8-row smoke,
  `NOTEBOOK.md:11`) plausibly pushes the total to or somewhat above v1's
  original 1-hour budgeted figure.
- **Recommended budget: 1.5–2 GPU-hours**, a deliberate upward revision of
  v1's 1-hour figure since generation is strictly more expensive than the
  forward-only pass it replaces. **Recommended pass 0: a 50–100-row timing
  smoke per arm** before launching the full run, both to firm up this
  estimate empirically and to produce the `measured_smoke_wall_clock_s` value
  the persistence-declaration schema wants if `short-run` mode turns out to
  fit after all (§5).

**Launch precondition (binding, not this drafter's call to clear):**

1. The GPU is currently owned by the item-27 sweep
   (`experiments/caution-install-bounded-site-sweep`) under the repo's
   one-job-at-a-time rule. Its most recent NOTEBOOK entry
   (`experiments/caution-install-bounded-site-sweep/NOTEBOOK.md:249-258`,
   2026-08-10) records a PI-approved kill-resume drill that was blocked at
   launch with zero GPU minutes consumed and a defect found; the full sweep
   itself has not yet been approved to run. v2 cannot launch until that
   sweep's GPU tail is clear.
2. Explicit PI launch approval naming the exact cells/arms/lane, per the
   standing operator-discipline rule
   (`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md:206-215`,
   "Launching any run... still requires explicit user launch approval naming
   the exact cells/seeds/lane"). Nothing in this document is that approval.

This drafting task launches nothing and stages nothing for launch.

---

## 9. Reporting rule (mirrors v1, `AMENDMENT.md:36`)

Exploratory, Tier-2, never pooled with the locked PROTOCOL v0.3 headline
matrix or with the S/T headline readings. If v2 resolves with LP-G1 gated
(pass, fail, or ambiguous-band), paper 4 item 9
(`manuscript.md:1252-1274`) is rewritten to cite the gated verdict; the
descriptive-with-caveat text it carries today is retired at that point, not
before. If v2 also stops at LP-G0, item 9 is left exactly as it reads today
and this draft's redo is reported as a second, independent confirmation that
the round-trip defect is real and specifically located in the missing
generation-time token-ID cache (§3.1) — which would itself be worth a short
addition to item 9 noting a second attempt hit the same class of stop, if
that is in fact what happens.

---

## 10. Summary: constants touched (kept deliberately short)

1. **LP-G0's round-trip sub-criterion** — redefined from re-tokenization
   round-trip to regenerated-answer-text-matches-cached-answer-text (§3.3).
   Necessary: this is the actual fix.
2. **Method steps 1–2 merged** — one `generate(..., output_scores=True)` call
   replaces "reconstruct, then teacher-force" (§3.2). Same measured quantity,
   same primary/secondary variants; purely removes the failure-prone
   reconstruction step.
3. **New persistence declaration** for the new harness module, not present in
   v1 (§5) — a schema requirement v1's much-shorter run never triggered.
4. **GPU budget revised upward**, 1 GPU-hour (v1, forward-only) → 1.5–2
   GPU-hours (v2, generation), with a recommended timing-smoke pass 0 (§8).
5. **Prediction reframed as informed-by, not blind to, v1's descriptive
   numbers** (§7) — flagged explicitly for PI adjudication, not decided here.

Everything else — the question, the populations, the arms, the metric
definitions, LP-G1's threshold, the ambiguous band, the falsifier, and the
containment rule — transfers verbatim from
`experiments/dial-logprob-baseline/`.
