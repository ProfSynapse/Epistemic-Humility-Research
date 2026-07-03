# Amendment AD — Inverted (pro-answer) injection on abstention-trained checkpoints: is the shut text channel bidirectional?

**Status:** DRAFT pre-registration 2026-07-03 (user-directed in-conversation:
"redo our thought injection test with our fine tuned models … since those are
'primed' to refuse with an issue of overrefusing we likely have to do the
opposite — encourage it to answer when it knows … We predict it will have NO
change. Same setup with think injected beginning or end of thought."). NOT
SIGNED. Prediction, falsifier, gates, and band cuts below LOCK at signing;
goalposts do not move after the result.

Tier-2 amendment (per `amendment-vs-lab-notebook.md`): new evidence cells on
new checkpoints with a pre-stated prediction and falsifier. One branch off
up-to-date `main`, one PR, merged before the next amendment branches
(Amendment AC is ahead of this in the queue; AD launches only after the AC
PR merges).

## Why this experiment (the through-line)

Amendments AA and AB established that on the RAW instruct base
(Qwen3.5-4B), injecting the probe's confidence signal into the thinking
process does not move the answer/abstain/revise decision — not as
activations (AA Arm A), not as third-person telemetry (AA Arm B), not as
first-person prose with an interpretable percent and an explicit action
rule (AB V1, three positions). The AB verdict is ambiguous-leaning-negative:
the only movement anywhere was a +2.0-pt abstention trickle at ~2–3%
verbatim rule-following compliance.

Every one of those tests pushed in ONE direction on ONE kind of policy: they
tried to make a rarely-abstaining model *more cautious*. That leaves a
specific escape route for the "presence ≠ use" claim: maybe the text channel
is not shut, it is merely asymmetric — a model whose trained policy already
points one way may be movable in the direction its training left open.

Our abstention-trained checkpoints are the mirror-image test bed. The clean
SFT and GRPO-v2 checkpoints over-refuse: GRPO-v2 declined ~82% of questions
even under a forced-best-guess prompt (Amendment T §7), while its internal
answerability signal remains near-ceiling (gate readout AUROC ≈ 0.98 on
these checkpoints, Amendments P/T). So the checkpoint *knows* it knows, and
refuses anyway. If injected first-person belief can ever move the decision,
this is the easiest possible setting: the note asserts something the model's
own internals already agree with ("I actually know this one"), and it pushes
WITH the truth against a trained over-refusal habit, where the headroom is
huge (vs AB's gate cell, where baseline abstention was 0.33% and there was
almost nothing to move).

**Pre-stated prediction (user, 2026-07-03): NO change.** The injected
belief will be absorbed without acknowledgment exactly as in AB, and the
trained refusal policy will not release. A null here upgrades "presence ≠
use" to a **bidirectional, policy-independent** claim: the text channel is
shut regardless of which way you push and regardless of whether the policy
was trained toward caution. A hit would be the more surprising outcome —
it would localize the AA/AB flatness to *direction* (you can release a
trained brake but not install one), which is a genuinely new mechanism
claim and would require registered replication before promotion.

## Design

Same harness as AB (`run_arm_b.py` / `arm_b_batched.py` + `cot_inject.py`),
same frozen SelfAware gate pool (300 unknown + 300 known), same sampled
decode (temp 0.7, top_p 0.9, seed 20260701, max_new_tokens 128 initial / 96
revision), same within-batch score-permutation placebo, same Amendment-Z
grader. The manipulated factors are (a) the checkpoint and (b) the note
template family; positions reuse the existing `early` and `final` engine
paths unchanged.

### Checkpoints (2)

| ID | Checkpoint | Loading |
|---|---|---|
| AD-sft | clean SFT | merged: `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit` |
| AD-grpo | clean SFT → GRPO-v2 | AD-sft merged base + adapter `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` |

Both verified present under local `scratch/` (AC prep). Note these are the
Qwen3-4B training line, not AB's Qwen3.5-4B raw base — cross-amendment
comparisons are descriptive only (see honest-scope).

### Signal, positions, cells (2 × 2 = 4)

Signal: **gate** (answerability probe), refit per checkpoint (precondition
3). Positions: **early** (note opens the initial pass's think block; probe
read pre-answer at the anchor) and **final** (Amendment AB Revision 1
mechanics: ONE shared plain initial pass, probe read post-answer, ONE shared
thinking-enabled plain revision pass whose think content is the frozen
draft, then the note appended as the final thought and the think block
closed; the ONLY real-vs-placebo difference is the score carried by the
final thought).

Cells: AD-1 sft@early, AD-2 sft@final, AD-3 grpo@early, AD-4 grpo@final.
Each cell = real + placebo over the same 600 items (~2,400 generations per
cell; ~9,600 total — a few hours on the batched engine, one long local day
sequential).

### Inverted note templates (variant `v1r`, "release")

Same banded machinery and band cuts as AB (LOCKED: low < 0.40, mid
0.40–0.70, high > 0.70), same first-person recall-experience structure,
same placebo contract (a permuted score carries its band and rule with it).
The inversion is in WHICH action the high band names: AB's high band said
"commit rather than hedge" to a model that almost never refused; `v1r`'s
high band names the trained failure mode — refusal — as the thing to
override. The low band keeps the say-I-don't-know rule (on these
checkpoints it agrees with the trained policy, so it functions as the
within-cell contrast, not the detection surface).

Structure and decision-rule clauses LOCK at signing; final surface wording
follows the AB precedent (pre-signing-step clause) — it finalizes from a
short idiom pass over THESE checkpoints' think traces (their post-SFT
reasoning register differs from the raw base) and is shown at launch
approval. Draft wording:

**Gate, high band:**
> Let me first check whether I actually know this. I am confident I have
> the knowledge needed to answer this correctly, about {pct}% sure. I
> actually know this one: I should give my answer directly rather than say
> I don't know.

**Gate, mid band:**
> Let me first check whether I actually know this. I am not fully
> confident, only about {pct}% sure I have the knowledge needed. I need to
> verify what I actually know and answer if it checks out; only if it does
> not should I say I don't know.

**Gate, low band:**
> Let me first check whether I actually know this. I am not confident I
> have the knowledge needed to answer this correctly, only about {pct}%
> sure. When I am this unsure the right move is to say I don't know rather
> than guess.

No em dashes in injected text.

### Why the placebo still identifies the effect

Gate scores are bimodal, so on a ~50/50 known/unknown pool the real arm
renders the high-band pro-answer rule almost exactly on the knowns, while
the placebo arm scatters it across knowns and unknowns alike. Generic
"answer more" priming from the mere presence of confident prose is
subtracted by the placebo; a surviving real-vs-placebo delta on knowns is
attributable to the true probe value flowing through the note. The placebo
arm's unknowns receiving high-band pro-answer notes also give the
hallucination-guard reading for free.

## Locked gates (at signing)

Bootstrap 95% CIs (2000 resamples); "vs placebo" = the paired placebo arm.

- **AD-G1 (per cell, the channel-open test):** real vs placebo
  known-question final ANSWER RATE ≥ **+10 points**, CI excludes 0, AND
  real-arm unknown-question abstention drop vs placebo ≤ **5 points**
  (the release must discriminate — freeing known answers without freeing
  hallucinations on unknowns).
- **AD-Q (answer quality, conditional on G1):** among newly-released known
  answers (real arm answers where placebo refused), accuracy reported with
  CI; descriptive, not pass/fail — it characterizes whether the released
  answers are the ones the gate said it knew.
- **Health gates (every cell):** degenerate_rate ≤ 0.05; coherence_floor_ok;
  **adequacy:** ≥ 100 known questions REFUSED under the placebo arm (the
  over-refusal headroom this design depends on; the mirror image of AB's
  "unknowns answered under control" floor). An inadequate cell is
  UNDERPOWERED — reported, excluded from the verdict, never PASS/FAIL.

## Prediction / success / falsifier (LOCK at signing)

- **PREDICTION (pre-stated): all four cells flat.** No real-vs-placebo
  separation on known-question answer rate.
- **SUCCESS (prediction confirmed):** all adequate cells miss AD-G1 with
  health gates passing → the text channel is shut in the *permissive*
  direction too, on policies trained toward refusal. "Presence ≠ use"
  becomes bidirectional and policy-independent; reported as a reinforcing
  negative in the Paper 5 line.
- **FALSIFIER:** ANY cell passes AD-G1 → injected first-person belief CAN
  release trained over-refusal → the AA/AB flatness is direction- or
  policy-dependent, not a sealed channel. Promotion to a claim requires a
  fresh registered replication (new seed and/or second checkpoint family)
  registered before running it.
- **Ambiguity clause (AB precedent):** a real-but-small effect (CI excludes
  zero, < +10 points) is reported as ambiguous, not a pass and not a clean
  null. Position and checkpoint differences with overlapping CIs are
  descriptive only.

## Secondary readouts (descriptive, not gated)

- **Refusal→answer flip rate** among initially-refused knowns at the
  `final` position — the answer-level `compute_revised` (2026-07-03
  instrument fix) makes abstain→answer transitions directly measurable;
  AB's dial cells had ZERO answer→abstain transitions, so the symmetric
  count here is the single most interpretable number in the design.
- **Trace capture** via `analyze_ab_traces.py` (committed report per cell):
  echo/marker rates, absorbed-without-acknowledgment check, verbatim
  rule-following census — does the ~2–3% compliance trickle reappear, and
  does it reappear in the pro-answer direction?
- **Position contrast** (early vs final) per checkpoint, descriptive; AB's
  Q-B got no reading, this is a second chance at it only if something moves.

## Honest-scope caveats (pre-stated)

- Single training line (Qwen3-4B clean-SFT family), single seed per
  checkpoint; nothing generalizes without a registered replication.
- Cross-amendment comparison to AB is confounded by base version (Qwen3-4B
  vs Qwen3.5-4B) and by training; "bidirectional" in the success reading
  means "both directions have now been tested", not "on the same model".
- The schema-trained checkpoints emit structured response formats; grader
  validity on their outputs is a precondition smoke, not an assumption.
  If the grader cannot read a checkpoint's outputs, its cells are
  UNDERPOWERED, not failed.
- The gate probe is refit per checkpoint (Amendment T: directions drift
  across checkpoints; cold-transfer 0.679). A cell whose refit direction
  reads below the adequacy floor (precondition 3) does not launch.
- A hit with the note asserting what the internals already believe would
  show the channel can *corroborate*, not that it can *overwrite* — the
  claim surface is release of a trained habit, deliberately the easiest
  direction; report it as such.

## Preconditions (all must hold before launch)

1. This draft SIGNED by the user (prediction, falsifier, gates, band cuts
   locked as written).
2. Engine PR merged: batched `final` position + answer-level
   `compute_revised` (branch `engine-batching-completion`), and the
   batched-vs-sequential GPU spot check passed for the `final` position —
   otherwise the affected cells run sequential.
3. Gate probe direction refit on EACH checkpoint from its own captures
   (standard capture → `persist_probe_direction` pipeline); adequacy floor:
   held-out gate AUROC ≥ 0.90 at the read position used by the cell.
4. Per-checkpoint harness smoke (~10 rows, both positions): thinking-enabled
   rendering produces non-degenerate think content, `extract_think_content`
   parses, and the Amendment-Z grader reads answers/refusals from the
   schema-trained output format.
5. `v1r` template wording finalized from the checkpoint idiom pass and shown
   at launch approval (structure, bands, and rule clauses fixed at signing).
6. Explicit user launch approval naming cells + lane; own branch off
   up-to-date `main` after the Amendment AC PR merges; never stacked on an
   unmerged branch.

## §7 Results (filled per cell as runs complete)

*(empty until runs complete)*

## §8 Verdict (locked gates, goalposts unmoved)

*(empty until §7 is complete)*
