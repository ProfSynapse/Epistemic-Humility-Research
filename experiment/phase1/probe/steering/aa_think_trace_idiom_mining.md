# AA think-trace idiom mining (AMENDMENT-AB pre-signing step)

Lab-notebook entry, 2026-07-02. Fulfils AMENDMENT-AB precondition #2: mine
the existing AA Arm B traces for Qwen3.5-4B's native uncertainty idiom and
finalize the V1 injection wording (structure, bands, and decision-rule
clauses were fixed at signing; only the recall-experience phrasing was
adjustable).

## Corpus and method

All four AA Arm B cell results (`aa5_gate_early`, `aa6_gate_late`,
`aa7_dial_late`, `aa8_dial_early`): 8,800 generations (500–600 items × real
+ placebo × initial + final passes). Regex-family counting over 20
uncertainty-expression patterns; injected-note echo detected via
`internal|gate|dial|telemetry|annotation` matching; fake-telemetry spans
stripped before the outcome-conditional pass. Outcome conditioning uses each
item's initial grade (base rates: 3,889 wrong / 502 correct / 9 abstained
across final passes).

## Findings

1. **The model riffs on the injected telemetry instead of using it.** In the
   pass that carries the injection, ~33% of generations echo the note format,
   and many *generate their own fake telemetry*, e.g.
   `[gate 1: 0.69 — still uncertain — need to verify] [gate 2: 0.77 —
   approaching threshold]` or `[gate 1: 100% confidence — no revision
   needed]` (scores the model invented). The registered note was treated as
   a style to imitate, not information to act on — direct mechanistic
   support for AA's register-mismatch reading, and for AB's premise.
2. **Introspective uncertainty talk is instruction-elicited, not
   spontaneous.** The uninjected initial passes (AA-6/AA-7, 2,200 texts) are
   almost devoid of self-referential knowledge talk (6 hits total); the
   idiom appears overwhelmingly in the revision pass, i.e. only when the
   double-check instruction invites it. Rates are equal in real and placebo
   (consistent with the registered flatness).
3. **Emitted confidence talk is anti-diagnostic on this surface.** In the
   revision pass, "I am confident (in)…" appears on 26.5% of
   initially-WRONG items vs 19.9% of initially-correct ones. The model's
   spoken confidence does not track its correctness — a fresh surface
   confirming the program's emitted-vs-internal calibration gap.
4. **Native constructions** (revision-pass register, echo-stripped):
   - `I am confident in my previous answer …` / `I am not confident in my
     previous output because …` — the dominant frame (always with a reason)
   - `I need to verify if X is correct/accurate`
   - `Let me think (through/about) this.`
   - `Wait — I'm not sure. Let me think.`
   - `I recall that X` (positive retrieval)
   - Percentages are NOT native idiom: bare `{N}% sure/confidence` occurs
     almost only inside fake-telemetry riffs; the one natural percent form
     is `I'm not 100% sure`.

## Implication for V1 wording

Anchor the templates in the model's own dominant frame — "I am (not)
confident (in my previous answer) … because/only about {pct}%" — plus its
native moves "let me think", "I need to verify", and "say I don't know".
Keep the percent (the design requires the score value to be conveyed) but
embed it as the *reason* inside the confidence frame rather than as a bare
telemetry number. Final wording is recorded in
`experiments/first-person-injection/AMENDMENT.md` §V1 templates.

## Provenance

Inputs: `experiment/phase1/probe/steering/results/aa{5,6,7,8}_*.json`
(gitignored run products; hashes in each file's `config_sha`). Analysis:
inline Python (regex families listed above), session
`01K2Xg1nGJ556Nbcpd2xEYTD`, 2026-07-02. Numbers above are descriptive
(pattern counts), not registered claims.
