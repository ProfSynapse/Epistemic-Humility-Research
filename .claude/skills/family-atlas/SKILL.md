---
name: family-atlas
description: Standardize the per-model layer-mapping extraction (full-depth hidden-state capture, workspace-dimension profile, three-axis held-out read panel) so any new model, family, or size entering the Epistemic-Humility program gets a fast, cheap, uniform layer atlas before any actuation design. Use when a new model/family/size enters the program, before designing any per-family actuation cell, or when an existing family's substrate changes (new revision, new checkpoint).
---

# Family Atlas

## Working hypothesis (not a fact)

This program's actuation work rests on a hypothesis, not an established
result: the three read axes this project uses everywhere --

- **doubt** (known-vs-refused),
- **caution** (refused-vs-confab), and
- **raw refusal** (refused-vs-answered) --

are assumed to be linearly readable in every instruction-tuned model. WHERE
they read (the layer band) is assumed model/family/size RELATIVE, not a
constant. The corollary: never port a layer or a depth fraction from one
family to another. Run the atlas on the new substrate first; every
per-family actuation amendment consumes that atlas's layer map as an input,
not a guess.

This hypothesis has already been tested once and partially failed on its own
terms: see `docs/atlas/family-layer-map.md` and the Gotchas section below.
Treat every number this instrument produces as evidence about THIS
hypothesis, not as a foregone conclusion it will confirm.

## When to use this skill

- A new model, family, or size enters the program and no atlas exists for it
  yet in `docs/atlas/family-layer-map.md`.
- You are about to design a per-family actuation cell (steering, erase-write,
  gated snap) and need a layer map to consume, not a ported depth fraction.
- An existing family's substrate changed (new HF revision, new checkpoint,
  new quantization) in a way that could move its workspace band.

Do not use this skill to re-litigate a family that already has a `resolved`
row in the registry with the SAME substrate revision; read that row and its
cited governed doc instead.

## The standard procedure

1. **Scaffold.** Run `bin/exp new <slug> --type probe-fit` from the repo
   root. Copy `templates/cell.yaml`, `templates/gates.yaml`, and
   `templates/AMENDMENT.skeleton.md` (as `AMENDMENT.md`) into the new
   experiment directory, replacing the generic placeholders `bin/exp new`
   wrote. One cell per substrate; a two-family run (like
   `experiments/jspace-family-atlas`) is two cells in one `cell.yaml`, not
   two experiments.
2. **Pools.** Reuse an existing experiment's committed split manifest
   verbatim whenever one exists for this substrate (row pool, baseline
   gradings, role/split assignments, unchanged). Only mine a fresh pool if
   none exists, and mine it per the program's standard roles: `confab`,
   `known_correct_answered`, `unknown_refused`, with split labels `fit`,
   `held_out`, `fit_only`. `profile_and_read_family_atlas_panel.py` reads
   rows by these exact role and split names; a pool using different role
   names needs a mapping layer before this instrument can read it.
3. **Select and bridge the capture backend.** Read
   `../experiment-runner/reference/batched-generation.md`. Prefer native vLLM
   extraction for a new atlas only after its model-specific bridge establishes
   exact prompt tokens, state indexing 0 through `num_hidden_layers`, anchor
   identity, normalization convention, numerical agreement, and profile-level
   location agreement against the HF reference. A cell extending an existing
   HF atlas remains HF unless that bridge is pre-stated and passed. If the
   generic tuner lacks vLLM capture, use the HF fallback and record the
   capability gap; do not add an experiment-owned engine.
4. **Capture.** Full-depth anchor capture: every hidden state (0 through
   `num_hidden_layers`), final-prompt-token anchor, float32, via
   `scripts/capture_family_atlas_cell.py capture`. The script reads
   `capture.engine` from `cell.yaml`; vLLM mode requires
   `VLLM_BATCH_INVARIANT=1`. Point `--render-module`
   at a copy of the source experiment's own render logic (see
   `templates/render_example.py`) so the anchor position matches that
   experiment's own convention exactly -- this is capture-only, no steering
   hooks, no re-mining, no re-generation.
5. **Profile + read panel.** `scripts/profile_and_read_family_atlas_panel.py
   score`: per-layer `eff_dim_frac` (participation-ratio profile) and the
   per-layer two-sided held-out AUROC read panel for doubt / caution /
   raw_refusal, each with a bootstrap CI, plus the standard
   random-direction control (see Gotchas). If the source pool's
   `unknown_refused` role is `fit_only` (no held-out partition at all),
   this script subdivides it deterministically into `refused_fit` /
   `refused_eval` by default; pass `--no-split-refused` if your pool
   already carries real held-out refused rows.
6. **Resolve and register.** Adjudicate the prediction/falsifier in
   `AMENDMENT.md`, run `bin/exp sign` / resolve per the `experiments` skill,
   then append one row to `docs/atlas/family-layer-map.md` citing the
   resolved doc. Never add a registry row before its governed doc is signed
   and resolved.

## Gotchas

- **Norm/position confound on the doubt axis.** The refused-vs-known
  contrast at the final-prompt-token anchor carries a norm/position
  confound: a FIXED RANDOM direction can read up to ~0.97 best-orientation
  AUROC on this same contrast at some layers (observed in both
  `jspace-family-atlas` cells). Always read the doubt axis's AUROC against
  its own layer's random-direction control value from the same
  `atlas_summary.json`, not against 0.5. Caution (refused-vs-confab) and raw
  refusal (refused-vs-answered) did NOT show this confound in the one
  resolved run (control stayed ~0.5-0.75), but check your own cell's control
  anyway -- do not assume that pattern transfers.
- **The profile can peak early-exterior, not interior.** The first
  family-atlas run's prediction and falsifier both assumed the eff_dim_frac
  profile would either peak inside (20%, 85%) depth (prediction met) or be
  monotone to the last layer (falsifier met). It did neither: llama peaked
  at layer 4 of 28 (0.14 depth) and mistral at layer 3 of 32 (0.09 depth),
  then declined through the midband with a mild late uptick -- an
  early-exterior peak, a shape neither the prediction nor the falsifier
  named. The result landed in a gap: not prediction-met, not
  falsifier-triggered. Write your own prediction AND falsifier to name
  early-exterior and late-exterior peaks as explicit outcomes (see
  `templates/AMENDMENT.skeleton.md` and `templates/gates.yaml`), so your run
  cannot land in the same unnamed gap.
- **The eff_dim_frac profile is representation-variance PR, not JVP-based.**
  This instrument's profile applies the participation-ratio formula
  directly to captured hidden-state vectors (capture-only, no gradients).
  A DIFFERENT instrument in this program (`j-space-localization-qwen3-4b`,
  `qwen35-4b-midband-doubt-snap` Stage A) applies a related-looking
  effective-dimension metric to corpus-averaged JVP "push" vectors from a
  gradient-based J-lens. The two profiles are NOT numerically comparable;
  do not read a family-atlas peak layer against a JVP-profile peak layer
  from a different instrument as if they measured the same thing. The
  family-atlas profile is comparable across this instrument's OWN cells
  only.
- **Population definitions move AUROCs by ~0.1.** "Refused vs known" and
  "refused vs pooled-answered" (confab + known) are different contrasts and
  read differently -- confab is the harder negative class than known alone.
  Name the exact contrast populations in every reported number (this
  instrument already does, via the axis names `doubt` / `caution` /
  `raw_refusal` and their `contrast:` strings in `cell.yaml`); never compare
  an AUROC from this panel to a same-named-sounding number from a different
  panel without checking the population definitions match.
- **Cost is capture-only and small.** The one resolved two-cell run (llama +
  mistral, ~6,000 rows combined) came in under $2 on Modal A10G. Full-depth
  float32 capture is the expensive-looking but actually cheap part; the
  profile and read panel are CPU-only and effectively free. Budget
  accordingly before asking for spend approval.
- **A read-optimal layer is not thereby a good write site** - see
  `reference/read-actuate-depth.md`. Actuability (does a dosed write at a
  site change behavior at all) decays steeply with RELATIVE depth
  (`layer_idx / num_hidden_layers`) in every family measured so far,
  independent of this atlas's own read-panel band. Convert every site to a
  depth fraction before comparing across families, and before attributing a
  family's actuation null to its architecture, check whether that family was
  even tested at the depth band where other families still actuate.
- **A vLLM layer ID is not automatically an atlas hidden-state index.** Native
  extraction can return selected intermediate layers, but the atlas requires
  embeddings at index 0 and every block output through N under the same
  normalization convention as the HF reference. Run the full bridge before
  adopting vLLM for an established atlas. Disable chunked prefill, capture
  prompt states only unless completion states are registered, and fail back to
  HF if the peak-location invariant does not bridge.

## Gates

Every family-atlas cell gates on three checks, transcribed verbatim from
`AMENDMENT.md` into `gates.yaml` (see `templates/gates.yaml`):

- **AG0 (integrity, pre-outcome)**: capture coverage >= 95% of the cell's
  manifest rows at every layer; direction refits byte-identical under the
  fixed seed; held-out power floors hold after capture attrition.
- **AG1 (profile)**: eff_dim_frac computed at every hidden-state index;
  a 20%-row-subsample reproducibility re-run keeps the peak layer within
  +/- 1 layer of the full-sample peak.
- **AG2 (read panel)**: per-layer held-out AUROCs with bootstrap CIs for
  all three axes, plus the random-direction control. AG2 carries no
  numeric pass/fail threshold of its own; the numbers ARE the atlas. The
  prediction/falsifier in `AMENDMENT.md` are adjudicated separately at
  resolve.

## Registry

`docs/atlas/family-layer-map.md` is the standing table of every family this
program has atlased: substrate, atlas experiment slug and status, profile
peak layer, the band where all three axes clear held-out AUROC >= 0.80, and
provenance citing the governed doc each row came from. Read it before
starting a new atlas (a resolved row for the exact substrate revision means
you don't need to re-run this), and append to it only after your own
amendment resolves -- the registry is a pointer INTO governed docs, never a
second source of experimental fact.

## Files

- `scripts/capture_family_atlas_cell.py` -- GPU: full-depth anchor capture
  for one cell (`capture` subcommand).
- `scripts/profile_and_read_family_atlas_panel.py` -- CPU: eff_dim_frac
  profile + three-axis read panel + random-direction control for one
  captured cell (`score` subcommand).
- `scripts/smoke_family_atlas.py` -- local CPU smoke against synthetic
  captures; run this before trusting either script against a real capture.
- `templates/cell.yaml`, `templates/gates.yaml`,
  `templates/AMENDMENT.skeleton.md` -- fill-in templates for `bin/exp new`
  scaffolding.
- `templates/render_example.py` -- reference pattern for the per-experiment
  render module `capture_family_atlas_cell.py --render-module` loads;
  always ported and adapted per source experiment, never shared verbatim.
- `reference/read-actuate-depth.md` -- the read/actuate depth dissociation:
  why a read-panel peak is not thereby a good write site, and how to control
  for the resulting depth confound before attributing an actuation null to
  architecture.
