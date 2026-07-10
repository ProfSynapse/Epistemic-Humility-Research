# j-space-layer-contrast-rep2-multisource

Status: resolved (2026-07-09; registered FULL PASS: G0/G1'/G2'/G3' all pass on the multi-source pool; mid-band advantage replicates off-ceiling at +19.0pp with 42:0 discordant pairs; see Outcome).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`j-space-layer-contrast-replication-qwen3-4b` (rep1) hardened the original
`j-space-calibrated-layer-contrast-qwen3-4b` result (hs23 89.2% vs hs34 66.5%
clean_tighten, +22.7pp) on a fresh held-out pool with the same directions,
gates, and calibrated doses frozen. Rep1's Outcome (see its AMENDMENT.md,
resolved on branch `agent/jspace-full-run` at commit `7cf4c444`, PR #263 --
not yet merged to `main` as of this writing) registered **G1 FAIL**: best
mid-band (hs29, 305/306 = 99.67%) beat hs34 (288/306 = 94.12%) by only
+5.6pp, below the registered +10pp bar. The adversarial post-run read of that
Outcome traced the miss to two structural causes, not to an absence of
effect:

1. **Ceiling effect.** hs34 itself reached 94.12% clean_tighten, leaving only
   5.9pp of arithmetic headroom against the +10pp bar. Every layer's rate had
   moved by almost exactly its predecessor headroom.
2. **Single-source pool.** All 306 fresh confabs came from one source
   (`kuq_ku_unknown_x`), because rep1's candidate universe -- the AH stage-0
   EXPANSION file (`ah_stage0/expansion/expansion_candidates.jsonl`) --
   structurally contains only that one unknown source. The predecessor's own
   held-out confabs, by contrast, mixed three sources (112 kuq_ku_unknown_x,
   44 kuq_ku_unknown, 29 selfaware_unanswerable); a G1 miss on a narrower,
   easier confab distribution is a weaker refutation of the mid-band thesis
   than a same-distribution miss would be.

Rep1's Outcome "Consequences carried forward" (b) is this experiment's design
mandate, quoted verbatim: *"The queued cross-family layer-contrast experiment
must replace or supplement its inherited fixed +10pp G1 bar with a
ceiling-robust contrast (CI separation plus a failure-ratio measure) and must
mine multi-source confab pools hard enough to keep the reference arm off the
ceiling."* (That sentence names the cross-family successor specifically, but
the same fix applies with equal force to a same-model rep2, and this
experiment implements it there first, on the smaller, cheaper same-model
surface, before the cross-family generalization inherits it.)

This experiment is that fix, applied as a second same-model replication: same
substrate, same frozen directions/taus/doses, same four arms, but (a) a
FRESH, MULTI-SOURCE confab pool mined from the three predecessor sources'
ORIGINAL dataset loaders (not rep1's narrow AH-expansion candidate universe),
with per-source floors that make a silent collapse back to one source
structurally impossible, and (b) ceiling-robust gates (G1' McNemar paired
test plus a G3' interpretability branch) that do not depend on the reference
arm sitting comfortably below ceiling to be informative. It remains Tier-2
exploratory evidence, not a headline or cross-family claim.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit
quantization. Identical to rep1 and its predecessor.

Frozen predecessor inputs (unchanged from rep1; Amendment-style provenance):

- Per-layer `u_d` gate directions and `c_hat` write directions from
  `j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/`
  (see that experiment's AMENDMENT.md and
  `analysis-committed/build_manifest_layers.json` /
  `analysis-committed/gate_fit_layers.json` for the FIT-only construction).
- Per-layer frozen gate thresholds from
  `j-space-midband-write-sweep-qwen3-4b/analysis-committed/gate_fit_layers.json`
  (`tau_frozen`, Youden-J on the FIT split).
- FIT-selected calibrated doses from
  `j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`:
  hs23=25, hs26=75, hs29=125, hs34=175 (see that experiment's AMENDMENT.md for
  the calibration ladder and the dose-200 collapse recovery this summary also
  asserts).
- The predecessor fit/held-out split
  (`experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`,
  739 confab+known_correct_answered row keys, seed 20260707) as one of the two
  dual-exclusion sources.
- Rep1's own fresh pool
  (`experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json`,
  2,263 row keys: 306 confab + 1,957 known_correct_answered) as the second
  dual-exclusion source.

**Provenance note on rep1's Outcome.** As of this writing rep1's resolved
Outcome (the G1-fail verdict, the adversarial read, and consequence (b)
quoted above) lives only on branch `agent/jspace-full-run`
(worktree `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication`,
commit `7cf4c444`, PR #263), not yet merged to `main`. This worktree's own
branch point (`main`) carries rep1's experiment directory only through its
pre-sign census/prep state (Outcome section still blank). This experiment's
motivation section above is read from the `agent/jspace-full-run` copy and
cites that provenance explicitly per this repo's READ-BEFORE-YOU-CITE rule.

### Fresh multi-source confab pool

Mined by `mine_multisource_pool.py` from the three predecessor sources'
ORIGINAL dataset loaders directly -- NOT rep1's AH-expansion candidate
universe, which structurally contains only `kuq_ku_unknown_x`:

- `kuq_ku_unknown`: `datasets/kuq/knowns_unknowns.jsonl`, rows with
  `unknown: true` (3,437 in the raw file; same filter as
  `amendment_ah_stage0_candidates.py:load_kuq_knowns`'s unknown branch).
- `kuq_ku_unknown_x`: `datasets/kuq/unknowns_all.jsonl`, all rows, deduped
  against `kuq_ku_unknown` by normalized question (6,363 in the raw file;
  same knowns_unknowns.jsonl-first / unknowns_all.jsonl-fills-gaps priority
  as `amendment_ah_stage0_expand_candidates.py:iter_new_kuq_unknowns`).
- `selfaware_unanswerable`: `datasets/selfaware/SelfAware.json`, rows with
  `answerable: false` (1,032 in the raw file; same filter as
  `amendment_ah_stage0_candidates.py:load_selfaware`'s unanswerable branch).

**Dual exclusion.** A candidate is dropped if its normalized question text
matches any row already used by (a) the predecessor split manifest or (b)
rep1's own fresh pool manifest. Both prior manifests are ID-only (row_key,
role, source -- no question text, per this repo's public-safe containment
convention), so exclusion is resolved by looking each excluded row_key up in
the private, gitignored candidate cache its `ah::`/`ahx::` prefix names
(`ah_stage0/candidates.jsonl` for `ah::`, `ah_stage0/expansion/expansion_candidates.jsonl`
for `ahx::`), recovering its question text, and normalizing. This is a
stronger disjointness guarantee than literal row_key-string matching would be
here, since this experiment's own row_keys use a new `msrc::` scheme that
would never collide with `ah::`/`ahx::` keys regardless of content overlap.
At scaffold time this resolved all 3,002 excluded keys (739 + 2,263) to
normalized questions with zero unresolved keys (verified by direct script
run; see NOTEBOOK.md).

This fresh pool is NOT deduped against the separate, earlier AF600 frozen
probe-calibration pool (a different amendment's frozen fitting set, unrelated
to the u_d/c_hat directions used here, whose own overlap or lack thereof does
not affect anything this experiment gates on). That is a scope note, not a
limitation: AF600 non-overlap is not one of this experiment's stated
disjointness requirements.

**G0 floors (pre-registered, not tuned to the achieved result):** at least
200 total fresh confabs, AND at least 40 confabs from EACH of
`kuq_ku_unknown` and `selfaware_unanswerable` (the two harder sources; the
floor makes a silent collapse back to a single easy source structurally
impossible, the way rep1's own pool collapsed). `kuq_ku_unknown_x` has no
independent floor; it is the higher-conversion-rate bulk source that helps
meet the 200 total. The committed pool artifact is ID-only:
`analysis-committed/multisource_pool_manifest.json`, reporting the achieved
per-source composition.

### Known-correct side: verbatim reuse

Locked design (pre-stated): "REUSE rep-1's 1,957 known_correct_answered rows
and their already-extracted anchors verbatim (pre-stated; the cost side was
nowhere near ceiling and reuse saves a full generation pass)." Rep1's own
four arms' known-correct cost ranged 0.97-2.81pp, nowhere near a floor or
ceiling; there is no design reason to re-mine it for this replication.
`materialize_known_side_reuse.py` copies rep1's 1,957 `known_correct_answered`
rows (filtered from its private `analysis/fresh_eval_rows.jsonl`) and their
matching anchor tensors (filtered from its private
`analysis/fresh_anchor_extract.safetensors`, 7,828 = 1,957 x 4 tensors) into
this experiment's own private `analysis/`, and commits an ID/hash-only
provenance manifest (`analysis-committed/known_side_reuse_manifest.json`)
recording both the SOURCE file hashes and the LOCAL copy hashes -- the pin
this experiment's `cell.yaml` names. Verified at scaffold time: 1,957 rows,
7,828 tensors copied exactly as expected (see NOTEBOOK.md for the run and its
hashes).

Cross-worktree dependency, recorded not hidden: rep1's resolved private
artifacts currently live only in the `jspace-layer-replication` worktree
(branch `agent/jspace-full-run`, PR #263). If that worktree is deleted before
`materialize_known_side_reuse.py` has been run there once, this reuse pin
cannot be re-derived without re-running rep1's own mining and extraction.

### Layer contrast (unchanged mechanism from rep1)

- hs23 gated snap at absolute setpoint 25.
- hs26 gated snap at absolute setpoint 75.
- hs29 gated snap at absolute setpoint 125.
- hs34 gated snap reference at absolute setpoint 175.

For each layer, the fresh confab prompt-anchor state (extracted by
`extract_multisource_confab_anchor.py`) and the reused known-correct anchor
state (from `materialize_known_side_reuse.py`) are projected through that
layer's frozen `u_d`; rows fire iff `score_neg_z_d >= tau_frozen`. Fired rows
receive the frozen `c_hat` erase-write at the calibrated setpoint,
anchor_onward. Generation and scoring contract mirrors rep1 exactly:
EOS-enabled greedy JSON generation, `min_new_tokens=1`, `max_new_tokens=200`,
`enable_thinking=False`; clean_tighten requires a natural-stop single-object
JSON refusal; known-correct cost is `not_well_formed_correct`.

### Per-row persistence (RunLog)

Rep1's Outcome flagged missing per-row persistence as a known limitation:
its per-row intervention outcomes were never written to disk (aggregates
only), so its 16 fired-but-untightened hs34 failures could not be classified
by failure text without a GPU re-run. This experiment fixes that via the
tuner's resumable per-item RunLog (`shared/utilities/run_log.py`), wired
through `pipeline_multisource.py:run_layer` following the exact pattern
documented in `experiments/common/README-runlog.md` and already used by the
(also unmerged) cross-family scaffold. One `RunLog` per layer per mode, under
`analysis/runlog/<mode>/<layer_name>.jsonl`; `run_contrast.py` defaults to
resuming an existing log and takes `--fresh` to discard one intentionally.

**Availability gate, pre-stated:** `shared/utilities/run_log.py` lives on the
tuner branch `feature/runlog` (Synaptic-Tuner PR #141), not yet merged to
`synaptic-tuner`'s `main`. **The submodule pin must be bumped to include that
branch (or its post-merge main) before `bin/exp sign` on this experiment.**
A signed, pinned instrument cannot be patched mid-run to add resumability
after a crash has already happened, so this is a sign-time precondition, not
a nice-to-have. As of this scaffold, the submodule remains pinned to its
prior commit (no RunLog available); `pipeline_multisource.py:load_run_log_class`
fails loudly with this same message if invoked before the pin bump, rather
than silently falling back to an unlogged loop.

### Ceiling-robust gates (the core change from rep1)

See `gates.yaml` for the machine-readable form; summarized here:

- **G0** (stop, not outcome): dual exclusion resolves to zero content
  overlap against both prior pools; >=200 total fresh confabs; >=40 from
  EACH harder source; no restricted text committed; doses exactly the frozen
  four; anchor extraction covers every eval row (fresh confab + reused
  known-correct) at all four hs; smoke readback within 5%+0.5 of target;
  smoke collapse 0; RunLog file visibly grows during the smoke.
- **G1' (primary, paired, ceiling-robust)**: McNemar exact binomial test on
  paired per-row outcomes between the best mid-band arm (selected by tighten
  rate, same arm used throughout, no re-selection after seeing pairs) and
  hs34, over the same fresh confabs. PASS iff (a) late-only-failure count
  (hs34 fails, best-mid succeeds) >= 3x best-mid-only-failure count (best-mid
  fails, hs34 succeeds) AND (b) exact two-sided binomial McNemar p < 0.05 on
  the discordant pairs.
- **G2' (selectivity)**: best-mid known-correct cost minus hs34 cost <= 2pp
  (unchanged bar from rep1), PLUS the cost-per-late-only-failure-won tradeoff
  is reported explicitly and unconditionally (rep1's Outcome flagged that a
  G2 pass on a loose bar can still hide a worse cost/benefit tradeoff than
  the headline delta suggests).
- **G3' (reference off ceiling / interpretability guard)**: hs34 confab
  clean_tighten must land in [40%, 90%]. Above 90% -> the run resolves
  "uninterpretable for magnitude, direction-only" rather than pass/fail on
  G1'. Below 40% -> reference-viability failure, as in rep1's G3. This makes
  the ceiling condition a pre-registered outcome branch instead of a
  post-hoc discovery the way it was in rep1.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`mine_multisource_pool.py`, `materialize_known_side_reuse.py`,
`extract_multisource_confab_anchor.py`, `pipeline_multisource.py`,
`run_contrast.py`, `analyze_paired_outcomes.py`.

## Prediction

With rep1's frozen directions, gates, and calibrated doses unchanged, the harder-source-dominant multi-source pool will pull hs34 off the ceiling into the interpretable G3' window (roughly 55-80% clean_tighten), the best mid-band arm will beat hs34 on paired outcomes with late-only failures at least 3x mid-only failures and exact McNemar p < 0.05 (G1' pass), and the known-correct cost gap will stay within +2pp (G2' pass): the mid-band advantage replicates at meaningful magnitude.

## Falsifier

If G1' fails on an interpretable pool (G3' status = viable), the mid-band
advantage does not replicate at meaningful magnitude on a comparable
multi-source confab distribution; report straight, exactly as registered,
with no goalpost movement.

## Gates

See `gates.yaml` for the full machine-readable specification; summarized
under "Ceiling-robust gates" above.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Full pass: the harder-source-dominant pool pulls hs34 off the ceiling into roughly 55-80% (G3' interpretable), G1' McNemar passes with late-only failures well above the 3x ratio and p < 0.05, and G2' passes since the known-correct side is rep-1's exact rows. Mid-band advantage replicates at meaningful magnitude. |
| user | Full pass (agrees with orchestrator): G3' interpretable, G1' passes the 3x ratio and significance, G2' within +2pp. |

Filled at sign (2026-07-09), per locked design.

## Outcome

**Registered verdict: FULL PASS. The same-model mid-band layer-site advantage
replicates at meaningful magnitude on an interpretable multi-source pool.**
Both scoreboard predictions (orchestrator and user: full pass) were correct.
Gate results, all registered bars unchanged:

- G0 pass: dual exclusion zero overlap (independently re-verified against
  rep1's full confab pool, rep1's known side, and the predecessor split);
  221 fresh confabs (139 kuq_ku_unknown / 76 selfaware_unanswerable / 6
  kuq_ku_unknown_x, floors met); doses exactly 25/75/125/175 with readback
  frac_within_tol = 1.0 and collapse 0.0 on every arm; anchor coverage
  complete; per-row RunLog persistence operative (2,178 rows per arm, zero
  duplicate keys, identical keysets across arms).
- G1' pass: paired hs29-vs-hs34 table over the 221 confabs = 163 both / 42
  late-only-failure / 0 mid-only-failure / 16 neither; failure ratio
  infinite (>= 3x bar), exact two-sided McNemar p = 4.5e-13.
- G2' pass: known-correct cost delta +1.43pp (hs29 2.81% vs hs34 1.38%,
  n = 1,957 each) <= 2pp; registered cost-per-win readout: 0.034pp of extra
  known-correct cost per late-only failure converted.
- G3' viable: hs34 at 163/221 = 73.76% (Wilson CI 67.6-79.1%), inside the
  registered [40%, 90%] interpretability window.

Per-arm confab clean_tighten: hs23 194/221 = 87.78% (known cost 0.97%),
hs26 190/221 = 85.97% (1.99%), hs29 205/221 = 92.76% (2.81%), hs34 163/221
= 73.76% (1.38%). Best mid-band (hs29) beats hs34 by +19.0pp, consistent
with the predecessor's +22.7pp on its own mixed pool.

Adversarially audited interpretation (post-run red-team; every gate number
was reproduced from the raw per-row RunLog records before this text was
written, and the lead independently re-derived the paired table):

1. **The rep1 G1 miss is now cleanly attributable to pool ceiling.** With
   the same frozen directions, taus, and doses, the advantage reappears at
   near-predecessor magnitude the moment the reference arm has headroom
   (hs34 at 73.8% here vs 94.1% on rep1's easy single-source pool). The
   layer-site claim is supported in direction and magnitude on both
   interpretable pools.
2. **Paired dominance is genuine and fully intervention-attributable.**
   Zero mid-only failures is a real row-ID cross-tab, not a summary
   artifact; zero unfired confabs tightened in any arm, so every tightening
   event sits on a dosed row. The verdict is also invariant to mid-arm
   choice: all three mid arms independently pass McNemar against hs34
   (hs23 p = 3.7e-8, hs26 p = 1.1e-7).
3. **The advantage is source-uniform.** hs29-vs-hs34 per floored source:
   94.2% vs 79.9% on kuq_ku_unknown (n = 139), 90.8% vs 61.8% on
   selfaware_unanswerable (n = 76); the third source (n = 6) is too small
   to read.
4. **Selectivity disclosure.** hs29 is the most expensive mid arm on
   knowns and roughly doubles hs34's absolute cost (2.81% vs 1.38%); G2'
   passes on the registered delta bar, and the registered cost-per-win
   tradeoff (0.034pp per converted failure) is favorable, but the absolute
   doubling is stated here rather than hidden behind the delta.
5. **Duplicate-normalized-question disclosure.** The 221 confab rows
   contain 179 distinct normalized questions (42 dataset-native duplicate
   pairs, predominantly within kuq_ku_unknown; confirmed native to the
   source files, not a miner double-write; the registered exclusion rule
   only deduplicated across pools and against kuq_ku_unknown_x). A
   sensitivity collapse to one observation per duplicate group still
   leaves >= 30 one-directional discordants, mid-only still 0, McNemar
   p ~ 1.9e-9; the verdict is unchanged.
6. **Provenance note.** The bespoke runner emits no tuner config_sha; the
   binding per-arm provenance is the RunLog config fingerprints
   (hs23 98de6a7c..., hs26 d03f7914..., hs29 740f7ab6...,
   hs34 daee5aa3...). The RunLog `complete` meta flag never flipped on the
   four arm files despite all rows being present and the final summary
   written; recorded as a runner hygiene item, not an evidence gap.

Consequences carried forward: (a) Paper 5's layer-site section can now pair
rep1 and rep2 as a single pool-sensitivity story: magnitude is
unidentifiable near ceiling, and replicates off-ceiling; the paired-McNemar
+ interpretability-window gate design validated here is the template. (b)
The queued cross-family layer-contrast experiment inherits these
ceiling-robust gates and the multi-source mining requirement as binding,
now-tested requirements. (c) Successor pools should either register a
within-source normalized-question dedup or pre-state the duplicate
tolerance explicitly.
