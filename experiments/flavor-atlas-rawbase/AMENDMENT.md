# Flavor atlas: per-flavor known-unknown activations on the raw base

Status: draft (not signed; do not launch as confirmatory evidence).

- Slug: `flavor-atlas-rawbase`
- Type: probe-fit (exploratory atlas)
- Tier: 3 (exploratory; nothing here pools with any headline matrix)
- Substrate: `unsloth/Qwen3-4B`, revision
  `64033659d5caf1b8ed7f929b29de705e93a4d468`, raw pretrained base, no
  adapter, bf16. Same substrate as the just-resolved
  `rawbase-ambigqa-boundary-readout` cell.

## Motivation and posture

`rawbase-ambigqa-boundary-readout` resolved that the near-0.997 SelfAware
known-unknown readout at L35 anchor is flavor-specific from pretraining:
the raw base reads the AmbigQA ambiguity boundary at 0.6338, the same low
level as the trained checkpoints. The PI's follow-on directive
(2026-08-09, "see if we can find actual activations based on other known
unknown flavors") is the direct continuation: do OTHER flavors of
unanswerability each have their own separable activation signature in the
raw base, at possibly different layers, or is the pretrained
known-unknown code narrow (SelfAware-flavored only), or universal (one
code for all flavors)?

KUQ supplies the flavor labels: its unknown rows carry a `category` field
with six values (ambiguous, controversial, counterfactual, false
assumption, future unknown, unsolved problem). SelfAware (no category
field) is treated as a single seventh flavor bucket and serves as the
positive reference; AmbigQA serves as the ambiguity comparator already
measured at L35. Posture: exploratory atlas. Discovery here promotes to a
claim only via a registered confirmatory follow-up.

## Design

Three forward-only, no-generation extractions on the raw base, all layers
captured in one pass each (`layers` omitted so all 37 hidden states are
saved), anchor family only, identical render to item 26's internal panel
(`ood_breadth_response_confidence_render:render`, which consumes only
`row["question"]`):

- E1 KUQ panel: item 26's screened KUQ pool
  (`experiments/ood-breadth-beyond-selfaware/analysis/screen/kuq_screened.jsonl`,
  sha256 `4a0a3a146dd8af573f3b8dfae7fcd9e207660a2d10deaa9071dd339c5104c5cc`),
  5540 rows = 3071 known + 2469 unknown. Screened flavor counts, locked:
  ambiguous 411, controversial 490, counterfactual 403, false assumption
  368, future unknown 490, unsolved problem 307.
- E2 AmbigQA panel: item 26's identical internal panel pool
  (sha256 `b0f936583d5a2fcd7dbc1393dce754c62669cb5185a5c80fb644266875a48bfd`),
  2748 rows = 1245 known + 1503 unknown.
- E3 SelfAware panel: all of `datasets/selfaware/SelfAware.json`,
  3369 rows = 2337 answerable + 1032 unanswerable.

A deterministic panel builder (`build_flavor_panels.py`) maps each source
into the internal-panel row schema (`row_key`, `question`, `label`, plus
`flavor`), no sampling, no filtering beyond what the named source files
already contain.

Probe protocol byte-identical to item 26's pinned
`internal_panel_probe_gate._cv_auroc_with_oof` (StandardScaler + L2
LogisticRegression C=0.5, StratifiedKFold 5, seed 0, held-out out-of-fold
AUROC), applied per (flavor, layer) by `flavor_probe_sweep.py`:

- M1 flavor-by-layer map: for each KUQ flavor, probe flavor-unknowns vs
  the full KUQ known pool, at every layer (6 flavors x 37 layers), plus a
  pooled all-unknowns row.
- M2 AmbigQA layer sweep: unknown vs known at every layer (previously
  measured only at L35).
- M3 SelfAware layer sweep: reference curve at every layer.
- M4 transfer matrix: for each source flavor (6 KUQ flavors, SelfAware,
  AmbigQA), fit one probe on the full source at that source's best layer,
  then evaluate frozen on every other flavor's rows at that same layer
  (target-flavor unknowns vs the target's own known pool).

All fits are CPU over the saved extractions. GPU budget: three local
forward-only extractions, 11657 rows total, roughly 50 to 70 minutes on
the local 3090, inside the pinned mechinterp-runner image per the
2026-07-10 standing directive (digest recorded as
`instrument.runtime_image_digest`). No cloud, no training, no generation.

## Prediction

- P1: at least one of {future unknown, unsolved problem} reaches held-out
  AUROC >= 0.90 at some layer on the raw base (these are the KUQ flavors
  closest to SelfAware's epistemic-fact unanswerables).
- P2: the ambiguity flavors (KUQ ambiguous and AmbigQA) stay below 0.75
  at EVERY layer, confirming the L35 0.63 reading is not a wrong-layer
  artifact.

## Falsifier

- F1 (universal code): every flavor including both ambiguity surfaces
  reaches >= 0.90 at some layer AND every off-diagonal cell of the M4
  transfer matrix reads >= 0.85. Then there is one universal
  known-unknown code and the flavor-specific account of
  `rawbase-ambigqa-boundary-readout` is wrong as stated; both cells'
  interpretations get revised together in writing.
- F2 (dataset-specific, narrower than flavor-specific): NO KUQ flavor
  reaches 0.75 at any layer. Then the 0.997 SelfAware readout does not
  even generalize to SelfAware-like flavors drawn from a different
  dataset, and paper 3's scoping must narrow further, from
  "SelfAware-flavored unanswerability" to "the SelfAware dataset".

Any other pattern is a mixed atlas: reported descriptively, per flavor,
with no single-number verdict and no post-hoc band invention.

## Multiplicity discipline

M1 spans 222 (flavor, layer) probes plus sweeps. Per-cell AUROCs are
held-out (out-of-fold), but max-over-layers selection is post hoc, so
every "best layer" number is reported next to its full layer curve, and
any per-flavor discovery under P1 is exploratory: promoting one to a
claim requires a registered confirmatory follow-up (fresh split or fresh
surface) per the program's standing promotion rule. The 0.90 discovery
bar and every band above were fixed before any extraction ran.

## Gates

See `gates.yaml`: FG0 panel integrity (locked shas and counts above), FG1
extraction capture (n_rows = n_answered = panel size, 37 hidden states
present, for each of E1/E2/E3), FG2 runtime provenance (pinned image
digest char for char, provenance JSON line in each run log). Fail-closed:
any FG failure voids the dependent M readings before they are looked at.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | P1 and P2 both hold: future unknown and/or unsolved problem separate somewhere >= 0.90; ambiguity separates nowhere |
| user | flavor-specific activations exist for other flavors (motivating directive) |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the
one-sentence summary that also goes into `verdict:` in the manifest.
