# Paper 5 — Confidence Steering: Reading vs Writing the Trust Axis

**Status:** CODE SCAFFOLD ONLY. NOT registered. NOT authorized for GPU runs.

A signed Tier-2 Amendment with pre-stated predictions, falsifiers, and locked numerical gates
is required before any model inference. See `docs/plans/confidence-steering-experiment.md` for
the full design. Run ONLY after the Amendment is signed AND the user gives explicit launch
approval naming cells/lane.

---

## What this directory contains

| File | Role |
|---|---|
| `persist_probe_direction.py` | CPU-only. Fits gate + dial probes from an Amendment-Z extraction dir and persists unit-normed direction vectors. |
| `confidence_steer.py` | Arm A harness. Registers a forward hook that adds `alpha * d` to the residual stream at inference. Unit-testable on synthetic modules. |
| `cot_inject.py` | Arm B harness. Builds prompts with a confidence note injected into the think block (early or late), plus a placebo control. CPU / string-construction only. |
| `steering_common.py` | Shared Amendment-AA plumbing: eval pools, grading (abstention/correctness/degenerate), two-pass protocol pieces, paired bootstrap CIs, cache-aware hook gating, cell-JSON output. CPU-only at import. |
| `run_arm_a.py` | Amendment AA cells AA-1..AA-4: activation-steering orchestration (alpha sweep / alpha*, anchor vs end, alpha=0 control). GPU only inside guarded main(); `--dry-run` is CPU-only. |
| `run_arm_b.py` | Amendment AA cells AA-5..AA-8: CoT-injection orchestration (real + placebo paired internally, early vs late). GPU only inside guarded main(); `--dry-run` is CPU-only. |
| `tests/` | pytest unit tests, CPU-only, synthetic fixtures. |
| `README.md` | This file. |

---

## Design overview

The experiment is a causal test of the anchor-vs-end theory from the readout amendments:

```
2 × 2 design:

         write at →    ANCHOR / early        END / late
 signal ↓
 answerability (gate)   ← predicted effect   muted
 correctness (dial)     muted                ← predicted effect
```

**Arm A (internal steering):** `h ← h + alpha * d` at inference.

**Arm B (CoT injection):** Insert `[internal: <signal> <score> — <interp>]` into the
thinking trace of a thinking-enabled model.

**Placebo control (Arm B only):** Inject a shuffled/random score from the same
distribution to isolate the real signal from generic "be cautious" priming.

Both arms share the same PROBE DIRECTIONS produced by `persist_probe_direction.py`.
The directions come from Amendment-Z extraction dirs (one per model family).

---

## The 4 model families (Amendment Z)

| Family | Tag pattern |
|---|---|
| Llama-3.2-3B | `llama-3.2-3b` |
| Ministral-3B-3B | `ministral-3-3b` |
| Qwen3.5-4B | `qwen3.5-4b` or similar |
| Gemma-4-E4B | `gemma-4-e4b` |

Amendment Z extraction dirs live under `experiment/phase1/probe/z_<tag>/` (gitignored).

---

## Workflow: producing directions for all 4 families

After Amendment Z extraction is complete (one GPU run per family), run on CPU:

```bash
# For each model family (replace Z_TAG with the actual extraction dir tag)
python experiment/phase1/probe/steering/persist_probe_direction.py \
    --x-dir experiment/phase1/probe/z_llama-3.2-3b \
    --out-dir experiment/phase1/probe/steering/directions/llama-3.2-3b \
    --seed 20260630

python experiment/phase1/probe/steering/persist_probe_direction.py \
    --x-dir experiment/phase1/probe/z_ministral-3-3b \
    --out-dir experiment/phase1/probe/steering/directions/ministral-3-3b \
    --seed 20260630

python experiment/phase1/probe/steering/persist_probe_direction.py \
    --x-dir experiment/phase1/probe/z_qwen3.5-4b \
    --out-dir experiments/common/artifacts/two_signal_probe_directions/qwen3.5-4b \
    --seed 20260630

python experiment/phase1/probe/steering/persist_probe_direction.py \
    --x-dir experiment/phase1/probe/z_gemma-4-e4b \
    --out-dir experiment/phase1/probe/steering/directions/gemma-4-e4b \
    --seed 20260630
```

Each run produces:
- `directions/<family>/direction_gate.{safetensors,json}` — answerability direction
- `directions/<family>/direction_dial.{safetensors,json}` — correctness direction

---

## Arm A: activation steering (GPU runs — amendment required first)

```bash
# Dry-run (CPU, no generation): verify direction loads correctly
python experiment/phase1/probe/steering/confidence_steer.py \
    --model meta-llama/Llama-3.2-3B-Instruct \
    --direction experiment/phase1/probe/steering/directions/llama-3.2-3b/direction_gate.json \
    --alpha 1.0 \
    --position anchor \
    --dry-run

# Real steering run (GPU, requires signed amendment + user approval):
python experiment/phase1/probe/steering/confidence_steer.py \
    --model meta-llama/Llama-3.2-3B-Instruct \
    --direction .../direction_gate.json \
    --alpha 2.0 \
    --position anchor \
    --device cuda \
    --prompt "What is the capital of France?"
```

Alpha sweep pattern (in a run script):
```python
from confidence_steer import load_direction, register_steering_hook, alpha_sweep

model, tokenizer = load_model_and_tokenizer(model_name, device="cuda")
hook, handle = register_steering_hook(model, direction_path, alpha=1.0, position="anchor")

results = alpha_sweep(
    alpha_values=[-2.0, -1.0, 0.0, 0.5, 1.0, 2.0, 4.0],
    generate_fn=lambda alpha: {"text": generate(model, tokenizer, prompt)},
    update_alpha_fn=lambda alpha: setattr(hook, "alpha", alpha),
)
handle.remove()
```

---

## Arm B: CoT injection (GPU runs — amendment required first)

```bash
# Demo (CPU, string construction only):
python experiment/phase1/probe/steering/cot_inject.py demo \
    --signal gate \
    --score 0.23 \
    --position early \
    --question "What is dark matter?" \
    --placebo

# Batch injection from a scored .jsonl:
python experiment/phase1/probe/steering/cot_inject.py batch \
    --input scored_items.jsonl \
    --output injected_prompts.jsonl \
    --signal gate \
    --position early

# Placebo batch:
python experiment/phase1/probe/steering/cot_inject.py batch \
    --input scored_items.jsonl \
    --output placebo_prompts.jsonl \
    --signal gate \
    --position early \
    --placebo \
    --seed 20260630
```

---

## Running the unit tests (CPU, no GPU, no model downloads)

```bash
cd experiment/phase1/probe/steering
pytest tests/ -v
```

Tests cover:
- `test_persist_probe_direction.py` — unit-norm, sane layer, calibration from synthetic fixture
- `test_confidence_steer.py` — hook shifts target layer by exactly `alpha * d`; alpha scaling
- `test_cot_inject.py` — note at correct position; placebo differs only in score value
- `test_steering_common.py` — grading, degenerate detection, pools, paired bootstrap, hook gating
- `test_run_arm_a.py` — pass gating per position, alpha* control, proportional alpha, cell JSON, dry-run
- `test_run_arm_b.py` — injection position, shared initials, placebo determinism, pairing, dry-run

Run with EXPLICIT file paths (an rtk-proxied bare directory glob can false-negative):

```bash
python3 -m pytest tests/test_persist_probe_direction.py tests/test_confidence_steer.py \
    tests/test_cot_inject.py tests/test_steering_common.py \
    tests/test_run_arm_a.py tests/test_run_arm_b.py -q
```

---

## Full cross-family GPU experiment commands (LOCKED BEHIND AMENDMENT)

The full 2×2 experiment (signal × position) for all 4 families requires:

1. Sign a Tier-2 Amendment on its own branch off up-to-date `main` with:
   - Pre-stated predictions (position-locked effects)
   - Falsifiers (both arms inert / position-indiscriminate / coherence-only)
   - Numerical gates with CIs (abstention-rate change, accuracy floor, coherence floor,
     position-asymmetry contrast)
2. User explicit launch approval naming cells/lane.

Once authorized, the per-family GPU recipe is:

```bash
# Step 1 (CPU): fit + persist directions (see above)

# Step 2 (GPU, per family × per arm × per signal × per position):
# Arm A — anchor gate steer (AA-1 shape)
python run_arm_a.py \
    --model <family_model_name> \
    --direction directions/<family>/direction_gate.json \
    --position anchor \
    --alpha-sweep=-4,-2,-1,0,1,2,4 \
    --eval-pool gate --n-unknown 300 --n-known 300 \
    --gate-rows <selfaware rows.jsonl> \
    --cell AA-1 --seed 20260701 --device cuda \
    --out results/arm_a_gate_anchor_<family>.json

# Arm A — end dial steer (AA-3 shape)
python run_arm_a.py \
    --model <family_model_name> \
    --direction directions/<family>/direction_dial.json \
    --position end \
    --alpha-sweep=-4,-2,-1,0,1,2,4 \
    --eval-pool dial --n-answerable 500 \
    --cell AA-3 --seed 20260701 --device cuda \
    --out results/arm_a_dial_end_<family>.json

# (off-position cells AA-2 / AA-4: same but --position end/anchor and
#  --alpha <alpha*> — the alpha=0 control still runs automatically)

# Arm B — early gate injection (real + placebo, paired internally)
python run_arm_b.py \
    --model <family_model_name> \
    --direction directions/<family>/direction_gate.json \
    --signal gate \
    --position early \
    --eval-pool gate --n-unknown 300 --n-known 300 \
    --gate-rows <selfaware rows.jsonl> \
    --cell AA-5 --seed 20260701 --device cuda \
    --out results/arm_b_gate_early_<family>.json

# Arm B — late dial injection (real + placebo, paired internally)
python run_arm_b.py \
    --model <family_model_name> \
    --direction directions/<family>/direction_dial.json \
    --signal dial \
    --position late \
    --eval-pool dial --n-answerable 500 \
    --cell AA-7 --seed 20260701 --device cuda \
    --out results/arm_b_dial_late_<family>.json

# CPU dry-run for any cell: append --dry-run (and optionally
# --pool-file <items.jsonl> to override the dataset sources).
```

Cross-family roll-up: SUCCESS requires the predicted position-asymmetry pattern to hold
in ≥ 3 of 4 families for both arms independently (pre-registered threshold).

---

## Design provenance

- `docs/plans/confidence-steering-experiment.md` — full design + pre-registration draft
- `experiment/phase1/probe/amendment_x_cross_model_extract.py` — model loader pattern reused
- `experiment/phase1/probe/amendment_x_cross_model_score.py` — probe scorer pattern reused
- `experiment/phase1/probe/amendment_s_correctness_probe_score.py` — `oof_probe` reused verbatim
