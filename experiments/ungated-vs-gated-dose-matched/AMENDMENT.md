# H4: Registered Ungated-vs-Gated Dose-Matched Arm for the Caution Snap

Status: signed (2026-07-13; predictions were recorded 2026-07-11 pre-sign; launch on the local 3090 approved by the user 2026-07-13).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The resolved doubt-gated caution snap makes a specific mechanistic claim: the
write itself is NON-selective, and ALL of the instrument's selectivity comes from
the doubt gate, not from the write
(`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 67-77, read in full
before drafting this). That is the paper's most-quoted mechanism sentence. As the
record stands, it rests on two pieces of evidence, neither of which is a
registered dose-every-row contrast:

1. An UNREGISTERED dose-200 diagnostic recorded in the resolved amendment's
   Motivation (that doc's lines 45-55): dosing every row in a cell
   unconditionally at dose 200 (n=80/cell, greedy, raw-base bf16) tightened
   82.5% of confabs but false-refused 36.2% of known-correct rows. Those numbers
   are explicitly gitignored diagnostic scratch cited for provenance only
   (`experiments/two-signal-caution-regulation-instruct/analysis/tighten_step3_d200_summary.json`).
   The Paper 5 review memo flags at S8 that if the paper prints them it must label
   them as the unregistered diagnostic that motivated the registered design
   (`docs/review/paper5-actuation-review-2026-07-10.md` lines 138-145).
2. The permuted-gate placebo, which matches the gate's fire COUNT but reassigns it
   to uniformly random rows; it does NOT dose every row. Permuted-gate
   known-correct cost was 59/258 = 22.9% versus the gated 8/258 = 3.1%
   (`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 313-319).

This experiment converts the mechanism sentence from a citation of unregistered
scratch into a registered contrast (Paper 5 review memo hardening item H4,
`docs/review/paper5-actuation-review-2026-07-10.md` lines 258-266). It doses ALL
held-out rows unconditionally at the snap setpoint, gate off versus gate on, on
the SAME rows at the SAME dose, so "the gate supplies the selectivity" prints as a
registered number rather than a reference to a diagnostic that was never signed.

Posture: exploratory, small, reported separately from the locked Phase 1 headline
matrix and never pooled with it. It refits NOTHING: it reuses the frozen
instrument (directions, tau, standardization, held-out split) pinned by the
resolved snap cell, and adds exactly one arm - an ungated dose-every-row arm - to
be contrasted against a matched-conditions re-run of the gated arm.

## Design

Substrate: identical to the resolved snap cell. Raw-base untrained instruct
`unsloth/Qwen3-4B` (full bf16, no 4-bit quantization), no adapter
(checkpoint_tag "raw-base"), training-free, greedy decode
(`do_sample=false, max_new_tokens=200, min_new_tokens=1, enable_thinking=false`),
matching the resolved instrument exactly.

Frozen instrument reused verbatim (no refit; consumed via `inputs:`): the held-out
split (promoted ID-only manifest, confab 185 / known-correct 258), the snap write
direction `c_hat`, the doubt sensor `u_d`, the frozen gate threshold
`tau_frozen = 0.3026445054171378`, and the FIT-pool standardization
(`mu_d`/`sigma_d` from `build_manifest.json`). Snap law `erase_write` along
`c_hat` to a fixed realized projection `dose_target = 200.0`, scope
`anchor_onward`. All identical to the resolved cell; see that cell's `cell.yaml`.

Two arms over the SAME held-out rows, SAME dose, one harness pass:

1. **Arm gate-on (gated).** The resolved instrument re-run: the doubt gate decides
   fire per row (`neg_z_d >= tau_frozen`), fired rows are snapped to `c_hat` at
   dose 200, non-fired rows are left unperturbed. This re-run under matched
   conditions is the gate-on side of the contrast; it must also reproduce the
   resolved 73.5%/3.1% (instrument-validity anchor, H4-G0).
2. **Arm gate-off (ungated).** The gate is disabled: EVERY held-out row (all 185
   confab and all 258 known-correct) is dosed unconditionally along `c_hat` at
   dose 200, scope `anchor_onward`. Same direction, same dose, same decode as the
   gated arm; the only difference is that the gate no longer decides who is dosed.

Contrast metrics, both pre-stated, both PAIRED on the same rows (the gated arm is
a subset-dosing of the same 443 held-out rows the ungated arm doses):

- **Known-correct damage rate:** fraction of the 258 held-out known-correct rows
  that become not `well_formed_correct`. Ungated versus gated. The diagnostic
  estimate is ungated ~36.2% (n=80) versus gated 3.1%: a ~33pp gap. This is the
  selectivity the gate is claimed to supply.
- **Confab conversion parity:** fraction of the 185 held-out confab rows that
  `clean_tighten`. Ungated versus gated. The ungated arm doses all confabs,
  including the few the gate does not fire on, so ungated confab conversion is an
  UPPER bound on gated conversion; the gap quantifies conversion the gate leaves
  on the table by not firing on some confabs. This certifies the gate does not buy
  its selectivity by sacrificing confab conversion.

The `clean_tighten` and `well_formed_correct` metrics are the resolved cell's own
(`gen_lib.py:grade_clean_tighten`, `grader.py:grade_one`), reused unchanged. Row
text is materialized at run time by the resolved cell's `materialize_rows.py`
scheme and kept under gitignored `analysis/`; no question, alias, or generation
text is committed.

Instrument config files pinned at sign: `cell.yaml`, `gates.yaml`.

## Prediction

Dosing every known-correct row unconditionally damages far more of them than the
gated arm does (ungated known-correct damage exceeds gated by at least 15pp
absolute, McNemar p < 0.001), while ungated confab conversion is at or above gated
confab conversion and the gated arm stays within 15pp of it, so the doubt gate
supplies the instrument's selectivity without materially sacrificing conversion.

## Falsifier

Ungated known-correct damage does NOT exceed gated known-correct damage by 15pp
absolute (i.e. dosing every known-correct row is about as harmless as gating it),
which would mean the write is inherently selective and the gate is NOT what
supplies selectivity: the paper's "the write is non-selective; the gate supplies
selectivity" sentence would then be wrong and must be removed, not merely
softened.

## Gates

Reference values from the resolved snap cell
(`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 45-55, 305-319) and
its motivating diagnostic. All rates over the HELD-OUT split only (confab 185,
known-correct 258); paired comparison on the same rows. Gates cannot move after
the run.

- **H4-G0 (gate-on reproduction / instrument validity, pre-analysis; failure =>
  STOP, not an outcome).** The gate-on arm reproduces the resolved gated confab
  clean_tighten 73.5% within +/- 5pp (in [68.5%, 78.5%]) and the resolved gated
  known-correct false-refusal 3.1% within +/- 3pp (<= 6.1%) under greedy decode.
  If the gate-on arm does not reproduce, the H4 harness diverges from the resolved
  instrument and the contrast is uninterpretable: STOP and diagnose.

- **H4-G1 (gate certifies selectivity, primary).** Ungated known-correct damage
  rate exceeds gated known-correct damage rate by `>= 15pp` absolute, with a
  paired McNemar test `p < 0.001` over the 258 held-out known-correct rows.
  (Diagnostic-estimated gap ~33pp; a 15pp registered margin is comfortably below
  the expected effect yet large enough to certify a real contribution. This is the
  registered number the paper prints in place of the unregistered dose-200
  diagnostic.)

- **H4-G2 (conversion preserved / parity).** Gated confab conversion stays within
  15pp below ungated confab conversion (`gated >= ungated - 15pp`); the exact
  ungated and gated confab conversion rates and their difference are reported.
  Certifies the gate does not achieve selectivity by sacrificing more than 15pp of
  the confab conversion that dosing-everything would obtain.

## Lane and cost

Small GPU job: two greedy passes over the 443 held-out rows (185 confab + 258
known-correct) - the gated arm (subset dosed) and the ungated arm (all dosed) -
roughly 886 generations at `max_new_tokens=200`. Two options, decide at sign time:

- Local RTX 3090, well under one hour, after the mid-band dose ladder frees the
  card (free).
- Modal A10G, under one GPU-hour, order-of-magnitude about one USD at an
  approximate USD 1.10/hour on-demand A10G rate.

PLACEHOLDER(GPU availability at sign time): default to the local RTX 3090; fall
back to Modal A10G if the card is not free before the submission window.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Ungated known-correct damage ~30-40% vs gated ~3%, a >25pp gap, McNemar p far below 1e-3 (gate certified); ungated confab conversion ~80-85% vs gated ~73.5%, gap ~7-12pp, within the 15pp parity bound. |
| user | FALSIFIER FIRES: ungated dosing is about as harmless as gated; the write is inherently selective and the gate does not supply the selectivity (recorded 2026-07-11) |

## Outcome

**Resolved 2026-07-13. ALL GATES PASS. The falsifier did not fire: on this
instrument the write is non-selective and the doubt gate supplies the
selectivity.** Red-teamed pre-verdict (5 surfaces: exact-reproduction
plausibility, derived-arm validity, metric decomposition, fire-bit provenance,
cross-result consistency); all surfaces survive, with two binding scope
statements recorded below.

**Gate results** (all rates over the held-out split, 185 confab + 258
known-correct rows; lead-recomputed from `analysis/run_log.jsonl` and
independently recomputed by the red-team, both matching
`analysis-committed/ungated_vs_gated_summary.json` exactly):

- **H4-G0 PASS (instrument validity).** The gate-on arm reproduces the resolved
  cell's numbers exactly: gated confab clean_tighten 136/185 = 73.5% (tolerance
  band [68.5%, 78.5%]) and gated known-correct cost 8/258 = 3.1% (bound 6.1%).
  Identical numerators, not merely in-band: both harnesses are single-row greedy
  deterministic on the same model, prompts, hook, dose, and grader, so exact
  token-level reproduction is the expected behavior and is itself evidence that
  the reused anchors did not drift. The run is fresh, not a copy: all 443 rows
  carry live readback (mean 200.018, range 199.85-200.25) and 371/443 rows have
  baseline text differing from dosed text.
- **H4-G1 PASS (primary).** Ungated known-correct damage 155/258 = 60.1% versus
  gated 8/258 = 3.1%: a 57.0pp gap against the registered 15pp margin. Paired
  McNemar over the 258 known-correct rows: 149 discordant pairs (148
  ungated-damaged-only vs 1 gated-damaged-only), exact binomial p = 4.2e-43,
  far below the registered p < 0.001. None of the 149 discordant pairs is a
  fired row; every fired known (4/258) is concordant by construction.
- **H4-G2 PASS (parity).** Ungated confab conversion 144/185 = 77.8%, gated
  136/185 = 73.5%; the gate gives up 4.3pp of conversion, well inside the 15pp
  parity bound.

**Binding scope statement 1 (metric hygiene).** H4's damage indicator is
not-well-formed-correct, which is broader than refusal. The 155 damaged ungated
knowns decompose as 144 clean false-refusals (55.8pp), 10 answered-wrong
(3.9pp), and 1 degenerate (0.4pp). Dosing every known-correct row
unconditionally damages 60.1% of them versus 3.1% under the gate. This
registered contrast SUPERSEDES the unregistered n=80 dose-200 diagnostic
(36.2% false-refusal); the registered false-refusal component alone (55.8%) is
higher than the diagnostic estimate, consistent with the larger and different
held-out pool. 60.1% must not be reported as a refusal rate, and H4 must not
be described as reproducing the 36.2% diagnostic.

**Binding scope statement 2 (operating-point dependence).** H4 certifies that
FOR THE RESOLVED Qwen3-4B / L34 / dose-200 instrument the write is
non-selective on knowns and the doubt gate supplies the selectivity. This is
scoped to that substrate, site, and dose, and must not be generalized to the
caution-snap mechanism at large: the Qwen3.5-4B mid-band ladder's permuted-gate
result (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md`, dosed knowns
refused only ~5.6% at hs20 / 8 sigma_c) shows the write itself is
content-selective at that operating point. The two results are not in tension;
they measure different substrate, site, and dose, and together they establish
that the write's content-selectivity is operating-point-dependent. The paper
may cite H4's non-selectivity only as an L34/dose-200-scoped registered number,
never as a universal property of the caution write.

**Provenance (anchor reuse, recorded at resolve per red-team hygiene note).**
The fire bit reproduces exactly from the reused L34 anchors plus the committed
frozen readout (u_d, mu_d, sigma_d, tau_frozen): confab 168/185 fired, known
4/258 fired; logged fire equals recomputed fire on all 443 rows. Checksums so
the CPU join stays reproducible if the source worktree is wiped:
`analysis/l34_anchor_extract_heldout.safetensors` sha256
`7299ac8212a734f3d99c3d1fc96617b3ba247cfb3f62709a1fa4be1c7e2fa80d`; source
artifacts in the gate-snap-tighten worktree: `l34_anchor_extract.safetensors`
sha256 `ee724687c3705f96d8c05f55cba78300cffdf69378982b8b850f52415d0772ff`,
`rows_with_text.jsonl` sha256
`02c6ca9d69342db368e19f9f057d25d1ca0f895df1e522164ff0844e8ac8c066`.

**Notes.** The pre-outcome NOTEBOOK adjudication on H4-G0's asymmetric cost
tolerance was not exercised: the gated cost landed at exactly 0.031, so no
below-floor stop occurred. The gated known damage 8/258 decomposes as 4 fired
plus 4 non-fired rows the raw model damages with no intervention, matching the
resolved cell's own 8/258.

**Predictions adjudication.** Orchestrator: directionally right (gate
certified, McNemar far below 1e-3, conversion parity held) but under-predicted
the damage magnitude (called 30-40% ungated damage and a >25pp gap; actual
60.1% and 57.0pp) and over-predicted ungated conversion (called 80-85%; actual
77.8%). User: the falsifier-fires call (write inherently selective, gate
unnecessary) is wrong on this substrate/site/dose; the ladder's permuted-gate
result shows where that intuition does hold, at the mid-band operating point.

**One-sentence verdict:** On the resolved Qwen3-4B/L34/dose-200 instrument,
dose-matched ungated dosing damages 60.1% of held-out known-correct rows versus
3.1% gated (57.0pp, McNemar p = 4.2e-43) while the gate costs only 4.3pp of
confab conversion, certifying that the doubt gate, not the write, supplies the
instrument's selectivity at that operating point.
