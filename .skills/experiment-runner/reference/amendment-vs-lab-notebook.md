# Amendment vs Lab Notebook — choosing the right instrument

This is the decision guide for *how heavyweight* a piece of experiment work
should be recorded and governed. It exists because the same project can run on a
spectrum from "locked, pre-registered, confirmatory" to "iterate fast and follow
the mechanism" — and using the wrong instrument is a failure mode in both
directions:

- **Too heavyweight:** minting a signed protocol amendment for every smoke,
  diagnostic, re-run, or hyperparameter nudge. The amendment count balloons, the
  instrument stops meaning anything, and the work *feels* like sprawl even when
  it is rigorous.
- **Too lightweight:** quietly adding a new arm, metric, or reporting label to a
  governed protocol with no pre-stated falsifier — i.e. exploring and then
  presenting the result as if it were confirmatory. That is the "garden of
  forking paths," and it is what turns iteration into rifling-in-the-dark.

The instruments already exist; this guide routes work to the right one. "Lab
notebook" means the existing [research-sessions.md](research-sessions.md)
checkpoints plus [run-records.md](run-records.md) and
[experiment-notes.md](experiment-notes.md). A tier-2 amendment is now scaffolded
and tracked through the `experiments` skill (`bin/exp`): its signed
`AMENDMENT.md` prose and machine-readable `experiment.yaml` manifest live
together in `experiments/<slug>/`. See
[Where a tier-2 amendment lives](#where-a-tier-2-amendment-lives).

## The three tiers

| Tier | Instrument | Use when the work… |
|------|-----------|--------------------|
| **1. Confirmatory** | **Signed protocol revision** (new version + changelog) | changes or makes a *headline claim*: hypotheses, falsifiers, the LOCKED headline run matrix, metric definitions, or reporting/interpretation rules |
| **2. Exploratory cell** | **Amendment** (signed, falsifier pre-stated) | introduces a NEW training/eval cell or arm that will be *reported as evidence* (separately from the headline), or a generic engine capability |
| **3. Lab notebook** | **Session checkpoint + run record** (no new amendment) | is a smoke, preflight, diagnostic, analysis-only pass, a re-run of an already-authorized cell, or tuning *within knobs an existing signed amendment already authorized* |

Read top to bottom and stop at the first match. Most day-to-day work is tier 3.

### Decision questions

1. **Does it touch the governed *headline* surface — the locked default cells,
   the hypotheses/falsifiers, metric definitions, or how results are labeled and
   claimed?** → Tier 1, signed protocol revision. Do **not** absorb this into an
   amendment.
2. **Does it add a new cell/arm that will be reported as evidence, or a generic
   tuner capability?** → Tier 2, Amendment.
3. **Otherwise** (smoke / preflight / diagnostic / re-run / analysis-only /
   tuning within an amendment's authorized knobs) → Tier 3, lab notebook.

## The firewall: confirmatory vs exploratory (the part that makes volume safe)

- The **locked headline matrix** (e.g. PROTOCOL v0.3 default cells) is the **only
  confirmatory surface**. Its numbers are the claims.
- **Every amendment cell is exploratory** unless a signed protocol revision
  (tier 1) explicitly promotes it. Exploratory results are reported **separately**
  and are **never pooled with, or labeled as, headline results.**
- This firewall is *why a large number of amendments is not a rigor problem.*
  Volume of exploration is fine; contaminating the headline is not. Guard the
  wall, not the count.

## The one discipline every amendment must keep

Before the run, an amendment must state, in writing:

- a **prediction**,
- a **falsifier** — the concrete result that *kills the line*, and
- the **gates** that decide pass/fail.

Stating the kill-condition *before* seeing data is the single thing that
separates science from rifling. Corollary: **do not move the goalposts** —
redefining a gate after seeing the result voids the test. If a result is
ambiguous, report it as ambiguous; do not retune the gate to manufacture a pass.

## Where a tier-2 amendment lives

Amendments use the experiments-first layout. Do not hand-author a file under
`experiment/protocol/`; legacy amendment records live under `experiments/<slug>/`,
and cross-cutting protocol docs live under `docs/protocols/`. For a new
amendment:

1. `bin/exp new <slug> --type <t>` scaffolds `experiments/<slug>/` with an
   `AMENDMENT.md` template (Motivation, Design, Prediction, Falsifier, Gates,
   Predictions scoreboard, Outcome), a thin `experiment.yaml` manifest, and a
   `NOTEBOOK.md`.
2. Fill the prose in `AMENDMENT.md`, copy the one-sentence question, prediction,
   and falsifier into the manifest, and list the instrument config paths under
   `instrument.configs`.
3. `bin/exp sign <slug>` pins each instrument config by sha256 and flips the
   status to `signed`, refusing while the prediction or falsifier is empty. This
   is the machine-checked form of the pre-stated-falsifier discipline below.
4. At resolution, `bin/exp resolve <slug> --verdict "..."` stamps the verdict and
   the terminal status (`resolved` / `null-result` / `falsified`) and prints the
   kg-ingest checklist.

The pre-commit hook validates every manifest and keeps `experiments/REGISTRY.md`
current. See the `experiments` skill for the full schema and lifecycle.

## Promotion: exploration → claim

A successful exploratory amendment cell **does not become a claim on its own.**
Promote it:

1. Register a **confirmatory replication** *before* running it — fresh seeds, and
   ideally the larger model and/or a held-out set.
2. Only after it replicates, report it as a headline-grade result under a signed
   protocol revision (tier 1).

Exploration finds the hypothesis; the confirmatory replication earns the claim.
A single-seed exploratory win is a lead, not a result.

## Stopping rule: avoid amendment sprawl and sunk cost

- A new amendment must carry a **distinct mechanistic rationale** from prior
  attempts — not "tweak it once more." If the only change is a hyperparameter
  nudge with the *same* mechanism, it is tier-3 tuning under the existing
  amendment, not a new amendment letter.
- **Pre-commit the falsifier that ends the whole line.** When repeated,
  mechanistically-distinct attempts on the same target all fail, the persistent
  failure *is the finding* — write it up (it is a real, publishable negative)
  rather than opening yet another amendment.

## Worked routing examples

| Work | Tier | Why |
|------|------|-----|
| New training cell (e.g. a reward on a different base) reported separately | 2 Amendment | new evidence cell, exploratory; pre-state prediction + falsifier + gates |
| Generic per-row loss-masking feature in the tuner | 2 Amendment | new capability that gates a cell; keep it generic (no project logic in `synaptic-tuner/`) |
| Change a hypothesis, falsifier, or the headline matrix; relabel a result as headline | 1 Protocol revision | governed headline surface / claim |
| Smoke or preflight for an already-authorized cell | 3 Lab notebook | `gate` checkpoint + run record; the amendment already authorized it |
| Re-running an authorized cell after an OOM/crash | 3 Lab notebook | `recovery` checkpoint + run-record outcome patch |
| `beta`/reward-weight tuning the amendment explicitly listed as authorized knobs | 3 Lab notebook | a `decision` checkpoint under that amendment; log each change |
| Re-scoring or re-analyzing existing scored_rows | 3 Lab notebook | experiment note + `interpretation`/`result` checkpoint |
| A single-seed exploratory cell "worked" → make it a paper claim | 1 Protocol revision + confirmatory replication | promotion: register seeds/8B/held-out before claiming |

## Note on launch authorization (orthogonal to this guide)

This guide governs *documentation/governance weight*, not compute approval.
Launching any run — even a tier-3 smoke — still requires explicit user launch
approval naming the exact cells/seeds/lane (see
[operator-discipline.md](operator-discipline.md)). A tier-3 classification means
"no new amendment doc is needed," **not** "launch without approval." When a cell
is authorized by an existing signed amendment, its smokes/re-runs/authorized-knob
tuning fall under that amendment's authorization and need only the launch
approval, not a fresh amendment.
