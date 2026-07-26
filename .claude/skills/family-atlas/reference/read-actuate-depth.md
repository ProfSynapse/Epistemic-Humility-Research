# Read/actuate depth dissociation

A site chosen by a READ criterion (probe AUC, this atlas's read-panel peak,
`eff_dim_frac` peak) is not thereby a good WRITE site. Read-optimal depth and
actuate-optimal depth are separate quantities, measured separately, and there
is no reason to expect them to coincide. This file documents the actuate side
so it does not get silently assumed from the atlas's read-panel output.

## The rule

Actuability - does a dosed write at this site change model behavior at all -
decays steeply with RELATIVE depth (`layer_idx / num_hidden_layers`) in every
family measured in this program so far, with no architecture-specific cause
required to produce the shape. Plain dense transformers with no shared-KV,
no gating, and no unusual normalization show the same decay.

Measured instances (dose-calibration ladders, tighten rate at each tested
site, illustrative only - not a claim about any specific family's ceiling):

| family | relative depth | tighten rate | note |
|---|---|---|---|
| llama | 0.61 | 0.875 | selected site; held-out G1 0.742 |
| llama | 0.71 | 0.375 | |
| llama | 0.82 | 0.125 | |
| llama | 0.93 | 0.125 | |
| mistral | 0.38 | 0.625 | usable dose |
| mistral | 0.47 | 0.625 | usable dose |
| mistral | 0.59 | 0.000 | |
| mistral | 0.94 | 0.000 | |

Both families' best actuation site is their SHALLOWEST tested candidate, and
both go to (or near) zero well before their deepest tested candidate. In llama
only hs17 cleared `dose_is_usable`; in mistral both hs12 and hs15 did, so
mistral's midband has two usable sites rather than one
(`midband_selected_doses` in each family's `dose_calibration_summary.json`).

A third substrate (Qwen3.5-4B, `num_hidden_layers=32`) shows the same ordering
under a DIFFERENT potency metric, so its numbers are reported separately rather
than pooled into the table above — refusal rate and well-formedness against
their registered floors, not tighten rate:

| relative depth | outcome |
|---|---|
| 0.625 (hs20) | clears both floors: refused 0.684, well_formed 0.980 |
| 0.719 (hs23) | never clears the refusal floor |
| 0.813 (hs26) | never clears the refusal floor |
| 0.938 (hs30) | no dose clears both floors at any point in the locked grid |

That experiment's own registered finding is that potency at matched relative
dose is **monotone toward earlier layers** (hs20 > hs23 > hs26 > hs30). The
same late-site failure reproduces on Qwen3.5-9B, and the mid-band-beats-late
lesson was first established on Qwen3-4B. Values are not comparable across
these metrics; the ORDERING is, and the ordering is consistent in all four
substrates.

Two selector failures are worth naming explicitly, because both look like
reasonable write criteria and neither is:

- **A registered site rule fixed at relative depth 0.94** — of the form
  `round(0.94 * (num_hidden_layers - 1))` — sits in the dead band for every
  substrate measured. A cross-family null obtained only at that site is a
  property of the site, not of the families.
- **`eff_dim_frac` peak is not the actuation optimum.** On Qwen3.5-4B the
  profile peaked at hs23, but the site that actually actuated was hs20. A
  structural workspace metric can miss the write band just as a read metric
  can.

## Therefore

1. **Always report site depth as a fraction of block count, never a raw
   index, when comparing across families or reasoning about a depth effect.**
   Raw indices are not comparable across families with different block
   counts and invite exactly this error.
2. **When a family's read-selected band sits at a relative depth where other
   families are already at (or past) the actuation floor, that is a confound
   to control for before interpreting any actuation null - not itself a
   family-specific finding.** A null observed only at relative depth ~0.8-1.0
   is weak evidence of anything architectural, because no family measured so
   far actuates that deep.
3. **Before attributing a family's actuation null to its architecture** (a
   mechanism, a gating structure, a cache topology, anything family-specific),
   **first test at the relative-depth band where other families DO
   actuate.** If the family has not been tested there, the null is
   underdetermined between "architecture-specific" and "ordinary depth decay,
   untested at the depth where it would show up."
4. **No family in this program has been tested at single-block depth
   resolution.** Treat any claim that a 2-3-block span is architecturally
   "safe" (or "unsafe") to write into as unsupported until it has been.

## Relation to the atlas's own read panel

This is a distinct claim from the "Working hypothesis" in `SKILL.md` about
WHERE the three read axes (doubt / caution / raw refusal) are linearly
readable. That hypothesis is about reads; this file is about writes, which
are measured independently and need not track the read-panel band at all.
Consult both before choosing an actuation cell's candidate site list - a
read-panel peak is a reasonable place to START looking for a write site, not
a place to stop looking.
