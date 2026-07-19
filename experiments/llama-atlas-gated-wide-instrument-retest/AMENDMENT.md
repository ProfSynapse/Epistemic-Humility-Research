# Llama atlas-sited gated caution ladder, wide-instrument retest

Status: signed 2026-07-19 (exploratory Tier-2; instrument pins in experiment.yaml).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

rr-cross-family-raw-refusal (resolved falsified 2026-07-13,
`experiments/rr-cross-family-raw-refusal/AMENDMENT.md` lines 3, 481-506) wrote the
doubt-gated caution snap at Llama-3.2-3B-Instruct's own atlas-located workspace
band {hs20, hs22, hs23} over the dose grid {2,4,6,8,12,16,20} x sigma_c and
recorded shape F: no rung cleared the FIT floors (fired-confab refused >= 0.60
AND well-formed >= 0.80) simultaneously. Best refused rung hs20 dose 16 at
263/576 = 0.457 (Wilson [0.416, 0.497]) with well-formed collapsed to 0.700 and
known-correct false-refusal 0.252; best well-formed-intact rung hs20 dose 12 at
192/576 = 0.333 (Wilson [0.296, 0.373]) with well-formed 0.939 (same doc lines
488-498). That verdict was rendered under the LOCKED 3-phrase canonical detector.
Its binding caveat (same doc lines 500-506) hand-credited idiom abstentions at the
peak rung only and still reached 0.457 < 0.60, recording llama's F as robust to
detector width, but the full certified wide instrument was never applied.

abstention-wide-instrument-calibration (resolved 2026-07-14,
`experiments/abstention-wide-instrument-calibration/AMENDMENT.md`, calibration
table) then measured llama's UNDOSED wide-instrument confab abstention at
239/1453 = 0.164 [0.146, 0.184] versus a narrow 52/1453 = 0.036, a +12.9-point
undercount, the largest of the three families, and stated the successor design
rule: a placebo/specificity criterion must be registered against the per-family
measured wide baseline, not a flat symmetric tolerance (same doc, "Design rule
for successor placebo criteria"). No llama placebo or dosed text exists on disk
(same doc, LB cell note); rr's llama dosed RunLogs were gitignored and were lost
when its worktree was removed, so a CPU-only re-read is not available and the
dose ladder must be re-generated (lead disk sweep 2026-07-18: rr worktree gone,
no branch, no matching RunLog anywhere under /home/profsynapse/code, nothing on
the frozen /mnt/f backup; only text-free committed aggregates survive).

Core question: is llama's shape-F non-actuation robust to the certified wide
instrument (detector v2 plus blinded adjudication lane), confirming a genuine
format-collapse-before-refusal-floor mechanism at the correct atlas site, or does
idiom-inclusive scoring lift a well-formed rung across the 0.60 floor, meaning
llama's F was substantially a canonical-phrase-coverage artifact the way mistral's
F was (rr lines 524-537)?

Posture: exploratory Tier-2, reported separately from the locked Phase 1 matrix
and never pooled with it, and never pooled with rr-cross-family-raw-refusal
(resolved falsified) or the qwen35 chain. This re-run CANNOT alter, upgrade, or
un-falsify rr's locked shape-F verdict, exactly as
abstention-wide-instrument-calibration's own outputs bind only future
registrations (that doc, Motivation). It produces (a) llama's dosed
wide-instrument refusal curve for paper 5's cross-family framing and the M3 third
family, and (b) a reusable, this-time-persisted dosed exhaust.

PI approval: cell and plan approved 2026-07-18 ("Sounds good on llama"); local
RTX 3090 launch pre-approved by the PI 2026-07-18 for this arc.

## Design

### Substrate

unsloth/Llama-3.2-3B-Instruct, bf16, no adapter, no quantization, at HF revision
006f5dcd1393c3add266de40994ba96225e9689d, the exact revision pinned in the fleet
`experiments/doubt-snap-cross-family-confirmatory/model_matrix.yaml` (cell
llama32_3b_instruct) and reused by the atlas and by rr (byte-checked at G0
against the atlas and rr cell configs). 28 decoder layers, 29 hidden states
(`experiments/jspace-family-atlas/AMENDMENT.md` line 141).

Hidden-state-index convention (open decision A5, pinned here at sign): indices
follow the atlas `atlas_summary.json` per-layer keys 0..28, where hidden-state
index h is the output of decoder block h and hs0 is the embedding stream. All
site names below (hs20, hs22, hs23, hs26) use this convention; the harness
asserts its hook placement against the same convention at G0.

### Atlas-located write sites and the late-site anchor

Sites are read from the atlas map, not ported. Atlas best simultaneous three-axis
read llama ~L20-23, raw-refusal read-axis peak L20-25
(`experiments/jspace-family-atlas/AMENDMENT.md` lines 178-185). The registered
ladder reproduces rr's llama sites verbatim for a direct wide-versus-narrow
comparison and adds one internal replication anchor (adjudicated 2026-07-18,
kept in-grid):

- {hs20, hs22, hs23}: rr's atlas-band sites (reproduce for wide-vs-narrow
  contrast).
- {hs26}: the ported late write site the cross-family confirmatory used for
  llama, round(0.94 * (28-1)) = 25 -> hidden-state index 26, included as an
  in-grid internal replication of the prior weak late-site result (peak
  clean_tighten 0.184 at dose 19,
  `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 269-272),
  re-scored here under the wide instrument.

### Instrument (mechanism unchanged, scorer changed)

Write instrument identical in construction to rr and the qwen35 ladder, differing
only in the scorer. GATE: doubt readout neg_z_d = -z_d >= tau, Youden-J on FIT
confab vs known-correct only. SNAP: fired rows get an erase-and-write along the
mass-mean caution direction c_hat (mean refused minus mean confab) orthogonalized
against a LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000,
random_state=SEED) confab-propensity direction with a QR erase, scope
anchor_onward; non-fired rows unwritten. Doubt and snap projections standardized
on FIT. GEN: EOS-enabled greedy JSON, min_new_tokens=1, max_new_tokens=200,
enable_thinking=False. Construction cited from
`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` lines 145-153 and
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 163-167. Every FIT
fit runs twice and is asserted byte-identical before any artifact is written.

SCORER (the change): the primary metric is the wide-instrument
refused-or-adjudicated-abstention rate per row, exactly the two-instrument stack
of abstention-wide-instrument-calibration: detector v2 (screen, byte-identical
pins) plus a blinded adjudication lane over detector-negative rows with
clear-negative and clear-positive decoys, salted opaque ids, seeded shuffle, and
the verbatim RR2 abstention rubric. Every rate is reported as the wide rate WITH
Wilson 95% CI, alongside the narrow 3-phrase rate, the wide-minus-narrow
undercount delta, and the net lift over llama's measured undosed wide baseline
(0.164). Well-formed, degenerate, natural-stop, and mean-new-token rates are
reported per rung as in the qwen35 ladder
(`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 218-227).

### Scope: FIT-side dose-ladder characterization

FIT-side only (adjudicated 2026-07-18), mirroring rr's shape-F stage and the
qwen35 ladder posture (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md`
lines 205-227): the held-out pool is not touched. This is existence/curve
characterization under a new scorer, not a held-out or generalization claim. A
held-out plus behavioral-placebo leg is NOT part of this cell; if a well-formed
rung crosses the 0.60 wide floor (reading R2), a held-out successor is registered
fresh before running.

### Data reuse

Row pools, roles, splits, and baseline generations reused VERBATIM from the fleet
llama32_3b_instruct cell (ID-only public manifest; the atlas established these are
volume-backed, `experiments/jspace-family-atlas/AMENDMENT.md` lines 40-41).
Populations follow the confirmatory behavior-defined roles (TriviaQA/PopQA
known-correct, KUQ confab/refused). FIT anchors at each candidate layer reused
from the atlas full-depth captures if pullable; the harness-build assignment
verifies coverage and re-captures only missing layers (open decision A1, resolved
at staging and recorded in NOTEBOOK.md). Committed artifacts are ID-manifests and
aggregates only; no question, alias, answer, or generation text, and no token
ids, under `analysis-committed/`. Dosed generation text is written to gitignored
`analysis/` RunLogs and, per the lesson from rr's lost worktree (open decision
A6), is staged to the durable exhaust store
`/home/profsynapse/code/ehr-exhaust/llama-atlas-gated-wide-instrument-retest/`
BEFORE any worktree teardown, with the staging path recorded in NOTEBOOK.md.
No OpenMOSS or bridge data.

### Dose policy

Registered sigma-relative grid {2,4,6,8,12,16,20} x sigma_c per layer, sigma_c
from each layer's fresh FIT build_manifest.json, finalized in absolute units at
sign, never changed after outcome (rr dose policy part 1). A pre-sweep
token-movement bracket check runs before the ladder; if the strongest arm produces
byte-identical output the grid is re-bracketed pre-sweep and pre-outcome, the only
permitted grid change (rr dose policy part 2). No FIT-viability EARLY STOP is
registered as a scorer gate here because the whole ladder is scored (the point is
the wide curve at every rung); shape assignment happens after full scoring.

### Arms

- baseline: reused undosed generations (reference for net lift; expected
  near-zero narrow refusal, ~0.164 wide on confabs per the calibration cell).
- gated: the real instrument at every (layer, dose) rung on fired FIT confabs and
  the FIT known-correct cost population.
- random_direction: magnitude-matched frozen random placebo on the SAME fired FIT
  confabs, run at the two peak-region rungs hs20 dose 12 and hs20 dose 16
  (adjudicated 2026-07-18), to give llama its first behavioral
  direction-specificity number under the wide instrument (llama has none on
  disk). Magnitude matched to the gated realized projection; note the atlas
  norm/position read confound inflates a random direction's read AUROC but not
  its behavioral refusal RATE (`experiments/jspace-family-atlas/AMENDMENT.md`
  lines 170-173; rr lines 278-283).

## Prediction

Registered pre-run, both readings pre-stated so no result falls off the table:

- Reading R1 (shape-F robust, family contrast real): the wide instrument credits
  idiom abstentions the narrow detector missed, but no well-formed rung reaches
  wide refused >= 0.60; the well-formed-intact peak (rr hs20 dose 12, narrow
  0.333) rises materially under the wide scorer yet stays below 0.60, while the
  high-refusal rung (hs20 dose 16) remains format-broken. This confirms llama's
  read-actuate dissociation and the format-collapse mechanism
  (`library/concepts/mechanisms/llama-atlas-site-write-collapses-format-before-refusal-floor.md`)
  as robust to detector width, matching rr's hand-credit.
- Reading R2 (F was partly a coverage artifact, llama like mistral):
  idiom-inclusive wide scoring lifts a well-formed rung to wide refused >= 0.60
  with well_formed >= 0.80, meaning the atlas-sited caution write DOES actuate
  clean idiom-abstention on llama and rr's F was substantially canonical-phrase
  coverage, paralleling mistral's credited peak 0.679-0.701 (rr lines 528-537).

## Falsifier

The reading "llama does not actuate clean refusal at its atlas sites" is falsified
(R2 adopted) if some (layer, dose) rung on the locked grid reaches wide
refused >= 0.60 (Wilson LCB > 0.50) with well_formed >= 0.80 simultaneously and
known-correct wide false-refusal <= 0.10 on fired FIT confabs. If no rung does
(R1), the reading survives and llama's shape F is confirmed robust to the
certified wide instrument. Because every rung is scored (no FIT early-stop gate),
the verdict cannot fall between prediction and falsifier the way the
confirmatory's uniform G0 stop did.

## Gates

Per-cell gates in `gates.yaml`. Wilson 95% CIs on every rate.

- G0 (instrument validity; pre-outcome stop). Loader resolves at the pinned
  revision via the causal-LM path; FIT gate AUC >= 0.90 at each candidate layer,
  with the matched random-direction best-orientation read AUROC reported
  alongside as the confounded reference (atlas norm/position caveat,
  `experiments/jspace-family-atlas/AMENDMENT.md` lines 170-173) since the doubt
  read is norm/position-confounded on llama and the gate's role is row selection,
  not the actuation claim; direction refits byte-identical under the fixed seed;
  anchor coverage over all FIT rows at each candidate layer; dosed-smoke readback
  within tolerance; wide-instrument pins (detector_v2 module, patterns,
  adjudication rubric) hash-identical to
  abstention-wide-instrument-calibration's committed pins; RunLog visibly grows
  on any stage over ~15 minutes; no text under `analysis-committed/`.
- G1 (primary, wide scorer, FIT). Existence question: does any (layer, dose) rung
  reach fired-FIT-confab wide refused >= 0.60 (Wilson LCB > 0.50) AND
  well_formed >= 0.80 AND known-correct wide false-refusal <= 0.05 (Wilson UCB
  < 0.10)? Floors held identical to rr and the qwen35 ladder G1
  (`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` lines 270-272) for
  cross-experiment comparability; because llama's wide baseline is 0.164 (not
  ~0), the net lift over the paired baseline wide rate is reported and evaluated
  alongside every absolute rate. Fired-known conditional false-refusal reported
  alongside the system-level cost (rr G1 hygiene, lines 431-437).
- G-spec (direction specificity, secondary, at hs20 dose 12 and dose 16). Effect
  ratio gated-net-wide-lift / max(|random_direction net-wide-lift|, epsilon)
  >= 3.0, importing the gate-contribution-factorial S1 ratio floor 3.0 and its
  rule that the random leg is directional-only with no magnitude floor
  (`experiments/gate-contribution-factorial/AMENDMENT.md`, items 6-7), sized
  against llama's measured wide baseline per the calibration deliverable's design
  rule. Reported, not a promotion gate at this FIT tier.
- CG1 (grader calibration, per adjudication shard). Clear-negative decoy
  agreement >= 0.95 AND clear-positive decoy agreement >= 0.60; a shard failing
  either is void before unblinding and regraded once, second failure voids the
  cell and is reported straight (abstention-wide-instrument-calibration CG1).
  Import that cell's lesson: use MORE clear-positive decoys per shard or a pooled
  clear-positive floor, since a 14-decoy draw voided its QL cell on decoy-draw
  variance.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | R1: falsifier survives; llama stays shape F under the wide instrument; well-formed-intact peak rises to ~0.45-0.55 but no well-formed rung crosses 0.60. (recorded pre-run) |
| user | Approved the cell and plan and pre-approved the local GPU launch (2026-07-18) without recording a separate quantitative call. |

## Lane and cost

Local RTX 3090 (free, PI pre-approved 2026-07-18), standard-attention 3B in bf16
within 24GB. Generation volume, FIT-only: gated ladder 4 layers x 7 doses x ~577
fired confabs plus FIT known cost 4 x 7 x 222 plus random_direction at 2 rungs,
roughly 23.5k generations at max_new_tokens=200; estimate 2-4 GPU-hours including
the mandatory smoke and any A1 anchor recapture. Any paid Modal launch needs
fresh user approval. The blinded adjudication lane is CPU/agent work, no GPU.

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest. No goalpost moves: gates
and falsifier above are final as signed.
