# Read-Side Timing Protocol (B-track: pre-commitment vs decision-echo)

Test *when* an axis fires relative to the emitted decision token, by READING
(never steering) the natural projection onto a direction across generated
positions. The question: does the axis separate the two behaviors BEFORE the
decision is verbalized (**pre-commitment / monitor-consistent**) or only after
the decision words are emitted (**decision-echo**)?

Two checked-in harnesses, both Tier-2, both read-only (they sidestep the
anti-steerability problem that plagues causal handles):

- **Per-head o_proj axis** (e.g. the failure axis F): `phase3_head_read_trajectory.py`
  + `phase3_head_read_trajectory_runner.py`, fed a `steering_directions.json`.
- **Residual full-vector axis** (e.g. the caution axis A2): `phase3_residual_read_trajectory.py`
  + `phase3_residual_read_trajectory_runner.py`, fed a `caution_direction.json`.

## What a read-only timing test can and cannot settle

- It CAN falsify **pure decision-echo**: a separation present at the prompt token
  or in the pre-lexical generation window cannot be an echo of refusal words that
  have not been emitted yet.
- It CANNOT distinguish a **monitor** (a state that *causes* the decision) from a
  **pre-formed internal decision** (decided-but-not-yet-verbalized). Both produce
  the same pre-commitment read. That distinction is causal — it belongs to B1
  activation patching, not a trajectory read. Say so in the writeup.

## Residual caution-axis recipe

1. **Fit the direction (GPU-free).** Raw mass-mean, NOT a whitened logistic
   normal — whitening is fit on prompt-token statistics and does not transfer to
   off-distribution generation-position residuals; the mass-mean unit vector
   applies frame-consistently across positions (and matches the failure-axis F
   construction).

   ```bash
   python .skills/mech-interp-runner/scripts/phase3_cli.py residual-caution-direction \
     --extraction-dir <SA_extraction> --behavior-rows <SA_behavior_rows> \
     --layer 35 --out <dir>/caution_direction_L35.json
   ```

   `prompt_token_auroc` in the JSON is an **in-sample** construction sanity check
   (theta is the mass-mean of those same groups); a value near the held-out A2
   AUROC confirms the raw direction captures the same axis.

2. **Run the trajectory (Docker/GPU; needs approval).** Copy
   `config/phase3_current_clean_grpo_v2_caution_residual_read_trajectory.yaml`:
   point `caution_direction` at the JSON, `rows` at the behavior rows,
   `rows_filter.label: known` (the contrast is known_refused vs
   known_correct_answered — unknown rows have no group membership and waste GPU),
   and set `output.root`. Launch the runner in Docker (see
   `resumable-gpu-sweeps.md`). It records, per row, the projection at the prompt
   token (prefill) and every generated position, decodes generated tokens to
   locate the refusal-lexicon onset, and splits prompt / generation /
   **pre-lexical** / **post-lexical** windows.

3. **Read the verdict (baked into `summary.json`).** `PRE-COMMITMENT` when the
   pre-lexical separation has the same sign as the by-construction prompt sep and
   exceeds the tolerance; `DECISION-ECHO` when pre-lexical is ~0 but post-lexical
   is large.

## Gotchas (durable)

- **Fit-prompt must match read-prompt for the prompt-token number.** If the
  direction is fit on a *full extraction* (default render, no system prompt) but
  the trajectory generates under the JSON response-confidence prompt, the axis
  still transfers but the **operating point shifts**: the standardized
  prompt-token separation collapses (seen: +0.22σ) far below the fit-prompt A2
  AUROC (0.91). The internally-consistent, robust signal is the
  **generation-internal pre-lexical contrast** (both groups read under the same
  generation prompt). Report the prompt-token number with this caveat, and treat
  the held-out A2 (fit-prompt) AUROC as the prompt-token evidence. A
  prompt-matched extraction removes the wrinkle if a clean prompt-token number is
  needed.
- **Refusal-marker lexicon must cover the model's phrasings.** `find_lexical_onset`
  splits pre/post by matching abstention phrases; a missed phrasing sends that
  refused row's WHOLE trajectory into the pre-lexical bucket, which *dilutes*
  (never inflates) the pre-lexical separation. Survey the refused rows'
  `generated_answer` for unmatched phrasings and extend `REFUSAL_MARKERS` before
  trusting the magnitude. (The clean run reached 167/168 onset coverage; the
  lone miss was a scorer edge case, not a refusal.)
- **post-lexical neg group is empty by construction.** known_correct_answered
  rows never emit the refusal lexicon, so post-lexical separation is undefined
  (nan) — expected, not a bug.
- **Layer→block mapping.** hidden_states[L] is the OUTPUT of decoder block L-1
  (block 0 is embeddings). The residual hook targets `find_decoder_layers(model)[L-1]`.
- **Container UID / output dir.** Same uid-1001 rule as every GPU step:
  pre-create + `chmod 777` the output dir on the host before launching.
