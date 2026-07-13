# Commitment-Point gen_stream Hook-Firing Check (H6)

Status: signed (2026-07-13; predictions were recorded 2026-07-11 pre-sign; local 3090 launch approved by the user 2026-07-13). Legacy
working label: **H6** (paper 5 hardening list, memo
`docs/review/paper5-actuation-review-2026-07-10.md` item H6; TODO.md row H6).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

This is an INSTRUMENT CHECK, not a behavioral experiment. Its result licenses or
invalidates a whole class of evidence: mid-generation ("answer-window",
`gen_stream`) activation-steering. It does not itself make a claim about the
model's epistemic state; it decides whether the harness that steers during
`generate()` decode actually does what it reports.

The gap it closes was diagnosed in Amendment AK (commitment-point extraction,
`experiments/commitment-point/AMENDMENT.md`, RESOLVED 2026-07-06). AK Stage 2
steered along the commitment direction in two position conditions, `anchor`
(single prefill token) and `gen_stream` (every answer-window decode step), and
its AK-G3 gate (`experiments/commitment-point/AMENDMENT.md` section 8) computed a
MISS: no dose moved the confab rate by the required ratio. But the raw rows
carried a signature that is not a plausible causal null. Read from
`experiments/commitment-point/AMENDMENT.md` section 8, lines 280-301:

- 328/328 (100%) of `gen_stream`-condition matched rows were byte-identical
  (confab, refused, answered, and `n_generated` all equal) across every one of
  the seven alphas from -2 to +2 sigma.
- The `anchor` condition, steering only the single prefill token at the same
  `alpha*sigma` dose, varied in 79/328 rows (24%).
- A per-decode-step push of up to 2 sigma sustained across the whole answer
  window changing nothing in any of 328 rows, while a single-token push of the
  same per-step magnitude already changes 24% of rows, is the signature of the
  intervention not reaching the model during decode, not a causal null.

AK section 8 further records (lines 290-301) that the pre-launch `_readback_check`
verified ONLY the `anchor` mode, via a raw `model(..., use_cache=False)` forward
call, explicitly NOT the `gen_stream` decode path; and that the CPU regression
test `test_gen_stream_is_the_answer_window_condition` exercises only the
pure-Python controller dispatch on synthetic zero-tensors, never confirming that
the registered forward hook fires during a real cached `generate()` decode loop.
AK's diagnosed mechanism: the AK Stage 2 harness
(`amendment_ak_stage2_steer.py`, an item-11-certified `SteeringHook` +
`GenerationHookController` installed on an Unsloth `FastLanguageModel.for_inference`
model; see `experiments/commitment-point/cloud/modal_ak_stage2.py` lines 9-11)
runs an optimized decode path that most likely does not route through the hooked
module's `forward()` the way the anchor-mode prefill call does.

AK section 8 (lines 303-321) therefore refused to adopt AK-G3 as a confirmed
causal null: the falsifier wording was numerically matched but "NOT treated as
adjudicated" pending exactly this hook-firing check. Until it runs, no
answer-window `gen_stream` steering evidence is usable. After it runs, either the
AK Stage 2 answer-window arm is instrument-void (and any future answer-window
claim must be produced on a path that passes this check) or the go-forward path
is a certified answer-window steering instrument.

There is a second, live reason the answer here matters beyond AK. The
doubt-gated caution snap (`experiments/doubt-gated-caution-tighten/AMENDMENT.md`,
resolved 2026-07-07 exploratory PASS) writes `c_hat` with
scope `anchor_onward` (persistent through decode, its Design point 2), i.e. it is
itself a `gen_stream`-style write, and it produced real conversions (G1 73.5%),
so SOME `gen_stream` path already fires end to end. TODO.md row 30 records that
`gen_stream_fired` was confirmed in the AO Stage-1 and dark-actuator-screen runs
on the tuner's plain-HF path (`MechInterp/cli.py run_steer`, loading plain HF
`AutoModelForCausalLM`, where `register_forward_hook` fires per decode step). So
the two candidate paths behave differently by report: the AK bespoke Unsloth path
is the suspect, the tuner plain-HF path is the presumed-good go-forward
instrument. This check certifies each with a readback, replacing "confirmed by a
smoke-flag assertion" with "verified by an on-vs-off state delta."

Posture: lab-diagnostic, exploratory. It generates no behavioral claim and is
never pooled with the locked headline matrix. Its output is a per-path
PASS/FAIL certification of a steering instrument plus a disposition for the AK
Stage 2 answer-window evidence.

## Design

The experiment runs an instrumented on-vs-off comparison of `generate()` decode,
per harness path, on a small fixed set of prompts. It measures three observable
quantities at fixed mid-generation decode positions and compares the hook
installed vs the hook a genuine no-op vs the hook absent.

### Paths under test (each certified independently)

- **PATH-BESPOKE**: the AK Stage 2 harness itself, `amendment_ak_stage2_steer.py`'s
  `SteeringHook` + `GenerationHookController` installed on an Unsloth
  `FastLanguageModel.for_inference` load of the raw instruct base
  (`unsloth/Qwen3-4B`), at the AK write layer L24. This is the path that produced
  the quarantined AK answer-window evidence; testing it adjudicates the AK
  confound directly.
- **PATH-TUNER**: the go-forward mechinterp `gen_stream` path,
  `MechInterp/cli.py run_steer` loading a plain-HF `AutoModelForCausalLM` and
  installing the steering hook via `register_forward_hook`. This is the path the
  doubt-gated snap and AO/dark-screen runs used and the path any future
  answer-window steering claim will use.

The tuner-path controller logic is additionally checkable on CPU with a tiny
plain-HF model (the durable integration test that TODO.md row 30 item (a) called
for). PATH-BESPOKE and the real-model readback require the actual Qwen3-4B load
and thus minutes of GPU.

### Instrumentation (independent of the steering hook)

For each path and prompt, run `generate()` (greedy, deterministic, a fixed decode
length of at least K=16 answer-window steps so multi-step firing is observable)
under three conditions:

1. **ON**: steering hook installed, commanded write nonzero (a supra-threshold
   dose, e.g. the AK 2-sigma setpoint at the write layer).
2. **NOOP**: steering hook installed, commanded write exactly zero (adds the zero
   vector).
3. **ABSENT**: no steering hook registered.

Capture three quantities, none of which is produced by the steering hook itself:

- **Firing counter**: an independent counter incremented inside the steering
  hook body on every forward call, plus, as a cross-check, an independent
  read-only `register_forward_hook` on the target module that counts its own
  invocations. Compared against the number of decode forward passes
  (`= n_generated_tokens` for cached decode).
- **Per-position hidden state at the write layer**: captured by a separate,
  read-only recording hook registered AFTER the steering hook on the same module,
  so it observes the post-steer output; recorded at every decode position.
- **Per-position logits**: captured via `return_dict_in_generate=True,
  output_scores=True`, recorded at every decode position.

### Measurement

- **Readback** at each instrumented decode position: project
  `hidden_ON - hidden_ABSENT` at the write layer onto the unit write direction;
  this is the realized write magnitude actually delivered during decode.
- **No-op delta**: `hidden_NOOP - hidden_ABSENT` and `logits_NOOP - logits_ABSENT`
  at each position; a correct instrument makes these exactly zero.
- **Behavioral divergence** (diagnostic): first decode position where the ON
  argmax token differs from the ABSENT argmax token, and the fraction of prompts
  with any divergence.

Instrument config files pinned at sign: `cell.yaml` (paths, layer, write
direction source, dose, prompt set, decode length, tolerances) and `gates.yaml`
(the thresholds below). No dataset, pool, question, or generation text is
committed; only aggregate readback/firing tables and ID-level manifests land
under `analysis-committed/`.

## Prediction

Orchestrator: PATH-BESPOKE fails H6-G1 (the Unsloth `for_inference` optimized
decode loop does not route per-step through the hooked module's `forward()`, so
the steering-hook firing count is far below the decode-step count, most likely
matching only the prefill call), confirming the AK section-8 diagnosis and
rendering the AK Stage 2 answer-window arm instrument-void. PATH-TUNER passes
H6-G1, H6-G2, and H6-G3 (plain-HF `register_forward_hook` fires on every decode
step, the readback lands the commanded write within tolerance, and the no-op
delta is exactly zero), certifying it as the go-forward answer-window steering
instrument.

PI: (empty; filled by the user at signing)

## Falsifier

For any path claimed as an answer-window steering instrument: the steering hook
does not fire on every decode forward pass (H6-G1 fail) OR does not deliver the
commanded write magnitude at the instrumented decode positions (H6-G2 fail). If
either fails for a path, all `gen_stream` answer-window steering evidence produced
on that path stays quarantined: it cannot be read as causal, and specifically the
AK Stage 2 answer-window (`gen_stream`) MISS cannot be adopted as a causal null.

## Gates

All gates are final in this draft and do not move after the run. A path is a
CERTIFIED answer-window steering instrument iff it passes H6-G1 AND H6-G2 AND
H6-G3. H6-G4 is a reported diagnostic, never a pass/fail.

- **H6-G1 (hook fires per decode step)**: on the tested path, the steering hook's
  forward-call count equals the number of decode forward passes, and that count
  is > 1 (multi-step), on 100% of the smoke sequences. The independent
  read-only counter must agree with the in-hook counter. FAIL if the count is 0,
  or equals only the single prefill call, or is below the decode-step count on
  any sequence. Justification: the AK confound is precisely a per-decode
  non-firing; the only firing pattern that supports answer-window steering is
  one call per generated token, so the gate is exact equality, not a fraction.

- **H6-G2 (write lands at the commanded magnitude)**: at each instrumented
  mid-generation decode position, the projection of `hidden_ON - hidden_ABSENT`
  onto the unit write direction equals the commanded realized magnitude within
  relative tolerance `|readback / commanded - 1| <= 0.05`, on 100% of
  instrumented positions across all prompts. Justification: prior CORRECT writes
  on this program landed far inside this band (Amendment AL readback ratio 1.0008,
  `experiments/radial-anti-propensity-steering` frontmatter as cited in the paper
  5 memo section 1; doubt-gated snap smoke read back 200.11 vs commanded 200,
  `experiments/doubt-gated-caution-tighten/AMENDMENT.md` line 302). Five percent is
  roughly 60x the observed miss of a correctly-writing hook: it absorbs
  dtype/reduction-order noise while still catching a hook that writes a fraction
  of, or none of, the commanded vector.

- **H6-G3 (no-op is a true baseline)**: with the commanded write exactly zero
  (NOOP) the hidden state and logits are identical to the hook-ABSENT run, at
  every decode position and every prompt: max absolute hidden-state delta
  `<= 1e-6` and argmax token identical with max absolute logit delta `<= 1e-3`.
  Justification: adding the zero vector is arithmetically a no-op, so a correct
  instrument reproduces the unhooked forward exactly; any nonzero delta means the
  hook perturbs merely by being present (e.g. a dtype round-trip), so its "off"
  arm is not a clean control and every on-vs-off contrast built on it is
  confounded. The tolerance allows only nondeterministic reduction-order jitter,
  not a real perturbation.

- **H6-G4 (downstream behavioral sensitivity; reported, not a gate)**: at the
  supra-threshold ON dose, the fraction of prompts whose argmax token diverges
  from ABSENT at >= 1 decode position, and the position of first divergence.
  Reported to separate two outcomes that a firing, correctly-writing hook can
  produce: a downstream behavioral change (the write moves decode) versus
  downstream invariance (the layer is behaviorally inert at this dose). Both are
  licensed measurements once G1-G3 pass, so this is descriptive; it is a gate
  only in the negative sense already covered by G1 (a hook that never fires would
  also never diverge).

## Disposition logic (pre-stated)

- If PATH-BESPOKE fails H6-G1: the AK Stage 2 answer-window (`gen_stream`) arm is
  instrument-void. AK-G3's `gen_stream` MISS is confirmed to be an instrumentation
  artifact, not a causal null; AK's falsifier second leg ("no steering asymmetry")
  stays unadjudicated on that path; and paper 5 may not cite any answer-window
  steering evidence produced on the bespoke path.
- If PATH-TUNER passes H6-G1 AND H6-G2 AND H6-G3: the tuner plain-HF path is a
  certified answer-window steering instrument. TODO.md row 30's smoke-flag
  `gen_stream_fired` claim is upgraded to a readback-verified certification, and a
  rerun of the AK Stage 2 answer-window arm on the tuner path becomes licensable
  (as a separate, later, signed experiment; not authorized here).
- If PATH-TUNER fails: no answer-window steering evidence in the program is
  currently usable, and the doubt-gated snap's `anchor_onward` decode-persistent
  write must be re-examined even though it produced conversions (the conversions
  would then require an alternative explanation, e.g. a prefill-only effect that
  persists in the KV cache without per-step re-application).

## Preconditions and approvals

1. This is a draft; the user signs before launch. Signing is not launch approval.
2. Explicit user approval for any GPU launch (standing rule). PATH-TUNER's
   controller logic is checkable on CPU with a tiny plain-HF model (no approval
   burden); PATH-BESPOKE and the real-model readback need the actual
   `unsloth/Qwen3-4B` load and thus minutes of GPU.
3. Compute: CPU for the tiny-model tuner-path controller check; minutes of GPU
   for the real-model readback and the bespoke-path reproduction.
4. Lane: PLACEHOLDER(lane assignment resolved at launch by the experiment-runner
   skill): local-3090 for the GPU minutes, or a short Modal job mirroring the AK
   Stage 2 image if the bespoke Unsloth path is easier to reproduce there.

## Interpretive caveats (pre-stated)

- A PASS certifies firing and write-fidelity of the instrument, not that any
  particular answer-window steering result is a true effect; it only makes such
  results admissible.
- The readback uses a read-only recording hook registered after the steering
  hook; if a path's architecture makes "after the steering hook" ambiguous
  (e.g. the steer replaces the module output object), the recording hook must be
  shown to observe the replaced output (a one-line construction check in the
  smoke), else G2's readback is not measuring the delivered write.
- Single model family (Qwen3-4B) and the two named harness paths only; a path not
  tested here is not certified by this experiment.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | PATH-BESPOKE fails G1 (confirms AK confound); PATH-TUNER passes G1+G2+G3 (certified go-forward instrument). |
| user | CERTIFIES CLEAN: hook fires per decode token, write lands within tolerance, no-op exact (recorded 2026-07-11) |

## Outcome

Filled at resolve. Record per-path G1/G2/G3 results, the G4 diagnostic, the AK
Stage 2 disposition, and the one-sentence summary that also goes into `verdict:`
in the manifest.
