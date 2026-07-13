# Cross-family raw-refusal actuation at atlas-located workspace-band sites notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (LEAD REVIEW, pre-sign): draft reviewed against the drafter's
  report; structure, gate table, and coverage table verified against the
  committed files. Rulings on the five open adjudications:
  (A1) SUBSTRATES: Llama-3.2-3B + Mistral-7B-v0.3 ACCEPTED. The lead's task
  message sized an 8B llama, but no atlas-located site exists for any 8B
  llama; written-at-their-own-atlas-site is the binding design requirement,
  so the atlas-mapped 3B stands and no atlas extension is authorized now.
  (A2) H4 INPUT: omission from experiment.yaml inputs ACCEPTED while
  ungated-vs-gated-dose-matched sits on its unmerged branch; the input line
  is added at sign once PR #281 merges (validator enforces path existence).
  (A3) ARMS: the four registered arms stand; permuted_gate is NOT added.
  The core RR question is actuation transfer, and dose_knowns_ungated is
  the directly motivated selectivity control given H4's operating-point
  dependence result. A permuted-gate ownership test at these sites is
  named as a possible follow-up if a family lands shape A, never bolted on
  here. (A4) SELECTIVITY-ON-KNOWNS stays reported-not-gated: the sign of
  the effect at a third operating point is unknown a priori, and gating it
  would conflate the existence question with the ownership question. The
  PI may elevate it at sign. (A5) LAYER BAND: 3 candidate layers per
  family inside the atlas best-read band, leaning earlier, ACCEPTED as the
  middle course between a single-layer bet and a full-band sweep.
  Also acknowledged from the drafter's flags: RR rests only on the atlas
  read-panel layer map and readability demonstration, never on the atlas's
  failed eff_dim prediction or any atlas actuation claim. Next steps in
  order: PR #281 (H4) merges, H4 input line added, PI fills the scoreboard,
  lead countersigns, harness-build assignment, lane decision at staging
  (local 3090 preferred; any paid lane needs fresh user approval).


### 2026-07-13 DRAFT (design specialist)
- Scaffolded via `bin/exp new --type steer-cell rr-cross-family-raw-refusal` on a
  fresh worktree branch `exp/rr-cross-family-raw-refusal` off origin/main.
- This is the successor design the `doubt-snap-cross-family-confirmatory` Outcome
  demanded (that doc :331-339): write at the per-family atlas-located site, not
  the ported round(0.94*(L-1)) late site, and register exterior-shaped outcomes
  so a uniform FIT-stop cannot fall between prediction and falsifier.
- Substrates are the two atlas-mapped models only: Llama-3.2-3B-Instruct and
  Mistral-7B-Instruct-v0.3 (jspace-family-atlas :40-41, :184-185). There is no
  atlas-located site for an 8B llama, so the lead's 8B lane note cannot be honored
  without an atlas extension first (open adjudication A1).
- Primary metric is the format-agnostic `refused` rate (ladder readout b,
  qwen35-4b-midband-doubt-snap :218-227); well-formed reported and gated alongside.
- Coverage table A-F: A = clean actuation (prediction); B-F = falsifier; F = the
  FIT-dose-viability non-actuation shape (confirmatory stop territory, now on the
  table). Gate template mirrors the Wilson-bounded held-out stage.
- H4 (ungated-vs-gated-dose-matched, ALL GATES PASS 2026-07-13) is cited by
  doc:line but is not on main yet, so it is omitted from experiment.yaml `inputs`
  (validator enforces path existence); add at sign once H4 merges (open
  adjudication A2).
- Predictions scoreboard left EMPTY for the PI and lead to fill at sign.
- No harness code written; harness build is a separate assignment gated on review.
- `bin/exp validate`: OK.
