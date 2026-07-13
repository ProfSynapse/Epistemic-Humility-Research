#!/usr/bin/env python3
"""H6 gen_stream hook-firing instrument check (shared harness for both paths).

Spec: AMENDMENT.md "Design" / "Measurement" / "Gates" (this file is the sole
prose source of truth; do not re-derive thresholds from memory). Draft, not
signed; see experiment.yaml for status. This is a lab-diagnostic INSTRUMENT
CHECK, not a behavioral experiment: it never produces or reports an
epistemic-state claim, only a per-path PASS/FAIL certification of whether
generate()-time steering actually reaches the model during decode.

Paths under test, both registered via `layer_module.register_forward_hook`,
neither modified by this file:

  PATH-BESPOKE  archive/experiment/phase1/probe/steering/confidence_steer.py
                (SteeringHook) + steering_common.py (GenerationHookController),
                intended to run on an Unsloth FastLanguageModel.for_inference
                load of unsloth/Qwen3-4B. This is the AK Stage 2 harness.
  PATH-TUNER    synaptic-tuner MechInterp.intervention (InterventionHook +
                GenerationInterventionController), intended to run on a plain
                HF AutoModelForCausalLM load. This is the go-forward
                mechinterp steering instrument.

steering_common.py's own module-level imports resolve paths via
path_compat.repo_root()'s sentinel check for
`experiment/phase1/eval/scorers.py`, which no longer exists after the
paper-reorg migration (commit e4abfc4b): `experiment/phase1/probe` and
`experiment/phase1/eval` were archived/relocated. A plain `import
steering_common` therefore raises ModuleNotFoundError before reaching the one
class this harness needs. This file does not repair that frozen archived
module (out of scope, and it is evidence-adjacent). Instead
`_load_generation_hook_controller_class` below extracts
GenerationHookController's exact source (via ast.get_source_segment) and execs
it in an isolated namespace. This reproduces the unmodified class because the
class body has no runtime dependency on the broken imports: steering_common.py
carries `from __future__ import annotations`, so the `hook: SteeringHook`
parameter hint is a lazy string, never evaluated at class-definition time.

No dataset, pool, question, or generation text is committed by this module.
Callers (the real-run CLI path) supply prompts already rendered by the
caller; row-level outputs (activations, generated text) belong under
analysis/ (gitignored), never analysis-committed/.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import torch

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
BESPOKE_STEERING_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "probe" / "steering"

for _p in (str(TUNER_DIR), str(BESPOKE_STEERING_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# --------------------------------------------------------------------------
# PATH-TUNER: real, unmodified public classes.
# --------------------------------------------------------------------------
from MechInterp.intervention import (  # noqa: E402
    InterventionHook,
    GenerationInterventionController,
    get_decoder_layer as tuner_get_decoder_layer,
)

# --------------------------------------------------------------------------
# PATH-BESPOKE: confidence_steer.py has no path_compat / archive dependency
# chain (only argparse/json/sys/pathlib/typing/numpy/torch), so it imports
# cleanly. GenerationHookController is extracted from steering_common.py by
# source (see module docstring).
# --------------------------------------------------------------------------
from confidence_steer import SteeringHook, get_decoder_layer as bespoke_get_decoder_layer  # noqa: E402


def _load_generation_hook_controller_class():
    src_path = BESPOKE_STEERING_DIR / "steering_common.py"
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(src_path))
    node = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == "GenerationHookController"
    )
    segment = ast.get_source_segment(src, node)
    if segment is None:
        raise RuntimeError(
            f"could not locate GenerationHookController source in {src_path}"
        )
    namespace: dict = {"SteeringHook": SteeringHook}
    exec(compile(segment, str(src_path), "exec"), namespace)  # noqa: S102
    return namespace["GenerationHookController"]


GenerationHookController = _load_generation_hook_controller_class()


# ==========================================================================
# Condition plumbing: normalizes the two controllers' different begin_pass /
# reset signatures behind one interface (ConditionHandle) so the
# instrumentation core below is path-agnostic.
# ==========================================================================


@dataclass
class ConditionHandle:
    label: str  # "ON" | "NOOP" | "ABSENT"
    controller: Optional[object]  # None for ABSENT (no hook registered)
    begin: Optional[Callable[[dict], None]]  # begin(enc) -> None
    reset: Optional[Callable[[], None]]


def tuner_conditions(direction: torch.Tensor, commanded_dose: float) -> dict:
    """PATH-TUNER conditions using InterventionHook(law="additive") +
    GenerationInterventionController, exactly as MechInterp/cli.py run_steer
    registers them.

    NOOP uses force_active=True at strength 0.0 so the hook's own clone/add
    code path is actually exercised (a true "adds the zero vector" test),
    not skipped as an inactive row -- InterventionHook's default active
    detection (strength != 0) would otherwise skip a zero-strength row
    entirely, which tests the controller's early-exit, not the write law.
    """

    def _make(strength: float, force_active: bool):
        hook = InterventionHook(
            law="additive", direction=direction, strength=strength,
            position="anchor_onward",
        )
        controller = GenerationInterventionController(hook)

        def begin(enc: dict) -> None:
            controller.begin_pass(
                "gen_stream", strength,
                attention_mask=enc["attention_mask"], force_active=force_active,
            )

        return controller, begin

    on_ctrl, on_begin = _make(commanded_dose, False)
    noop_ctrl, noop_begin = _make(0.0, True)
    return {
        "ON": ConditionHandle("ON", on_ctrl, on_begin, on_ctrl.reset),
        "NOOP": ConditionHandle("NOOP", noop_ctrl, noop_begin, noop_ctrl.reset),
        "ABSENT": ConditionHandle("ABSENT", None, None, None),
    }


def bespoke_conditions(direction: torch.Tensor, commanded_dose: float) -> dict:
    """PATH-BESPOKE conditions using SteeringHook + GenerationHookController,
    exactly as amendment_ak_stage2_steer.py registers them.

    Interpretive note: GenerationHookController.__call__ short-circuits to
    `return output` whenever `self.hook.alpha == 0.0`, BEFORE reaching
    `self.hook(...)`, for BOTH "off" and any nonzero mode. So this path's
    NOOP condition never touches the hidden state at all (no clone, no add):
    it is a structural identity with ABSENT by construction, not an executed
    "add the zero vector" that happens to net to zero. H6-G3 is still a
    legitimate pass for this path (the delta genuinely is exact zero), but it
    demonstrates zero about whether installing-and-adding-zero perturbs
    anything on this harness -- that question is untestable on PATH-BESPOKE
    as written. Reported as an adjudication, not silently normalized away.
    """

    def _make(alpha: float):
        hook = SteeringHook(d=direction, alpha=0.0, position="anchor")
        controller = GenerationHookController(hook)

        def begin(enc: dict) -> None:
            controller.begin_pass("gen_stream", alpha)

        return controller, begin

    on_ctrl, on_begin = _make(commanded_dose)
    noop_ctrl, noop_begin = _make(0.0)
    return {
        "ON": ConditionHandle("ON", on_ctrl, on_begin, None),
        "NOOP": ConditionHandle("NOOP", noop_ctrl, noop_begin, None),
        "ABSENT": ConditionHandle("ABSENT", None, None, None),
    }


PATH_BUILDERS = {"bespoke": bespoke_conditions, "tuner": tuner_conditions}
PATH_LAYER_RESOLVERS = {
    "bespoke": bespoke_get_decoder_layer,
    "tuner": tuner_get_decoder_layer,
}


# ==========================================================================
# Instrumentation core (path-agnostic).
# ==========================================================================


@dataclass
class PassRecord:
    condition: str
    n_generated: int
    decode_hidden: list  # per decode step, float64 (hidden_dim,) tensor
    decode_logits: list  # per decode step, float64 (vocab,) tensor
    in_hook_total_calls: Optional[int]  # controller._nth_call, None for ABSENT
    independent_total_calls: int  # the read-only recording hook's own count
    independent_decode_calls: int  # of those, the seq_len == 1 (decode) ones


def run_one_condition(model, layer_module, cond: ConditionHandle, enc: dict,
                      decode_len: int) -> PassRecord:
    """Run one generate() pass under one condition, instrumented by a single
    read-only recording hook registered AFTER cond.controller (when present)
    on the same module, so it observes the post-steer output per the
    AMENDMENT's Measurement section. This hook's own call count doubles as
    the "independent read-only register_forward_hook" firing cross-check
    (H6-G1): it is a separate object from the controller and would miss the
    exact same decode calls the controller misses if the module's forward()
    is bypassed during decode (the AK confound), while remaining logically
    independent of whatever the controller's own counter reports.
    """
    post_records: list[dict] = []

    def post_hook(module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        post_records.append({
            "seq_len": int(hidden.shape[1]),
            "hidden": hidden.detach().to(torch.float64).clone(),
        })
        return None  # read-only: never replace the output

    handles = []
    if cond.controller is not None:
        handles.append(layer_module.register_forward_hook(cond.controller))
    handles.append(layer_module.register_forward_hook(post_hook))

    in_hook_total = None
    try:
        if cond.begin is not None:
            cond.begin(enc)
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=decode_len, min_new_tokens=decode_len,
                do_sample=False, num_beams=1,
                return_dict_in_generate=True, output_scores=True,
            )
        # Read the controller's own counter BEFORE reset() zeroes it (reset()
        # sets _nth_call = 0 by contract on both controllers).
        if cond.controller is not None:
            in_hook_total = int(cond.controller._nth_call)
        if cond.reset is not None:
            cond.reset()
    finally:
        for h in handles:
            h.remove()

    prompt_len = int(enc["input_ids"].shape[1])
    n_generated = int(gen.sequences.shape[1]) - prompt_len
    decode_records = [r for r in post_records if r["seq_len"] == 1]
    decode_hidden = [r["hidden"][0, 0, :] for r in decode_records]
    decode_logits = [s[0].detach().to(torch.float64).clone() for s in (gen.scores or ())]

    return PassRecord(
        condition=cond.label, n_generated=n_generated,
        decode_hidden=decode_hidden, decode_logits=decode_logits,
        in_hook_total_calls=in_hook_total,
        independent_total_calls=len(post_records),
        independent_decode_calls=len(decode_records),
    )


def assert_recording_hook_observes_poststeer_output(
    model, layer_module, conditions_builder, direction: torch.Tensor,
    commanded_dose: float, enc: dict,
) -> dict:
    """One-off construction check (AMENDMENT.md "Interpretive caveats" #2):
    a hook registered strictly after the steering controller in the same
    module's forward-hook list must observe the REPLACED output when the
    steering hook returns a new tuple, not the module's raw pre-steer
    output. Verified directly: capture the hidden state seen by a hook
    registered BEFORE the controller (pre) and a hook registered AFTER it
    (post), under the ON condition, keeping only the LAST forward call's
    capture. Two new tokens are requested (not one) so that last call is a
    genuine decode step: gen_stream mode skips the prefill call entirely
    (both controllers' documented contract), so a single-token generate()
    would only ever exercise the never-steered prefill call and pass this
    check vacuously. If pre and post are identical at the decode step, the
    post-hook is not seeing the edit -- fail loudly, per the AMENDMENT's
    explicit instruction, rather than let G2 silently measure the wrong
    tensor.
    """
    pre_captured: dict = {}
    post_captured: dict = {}

    def pre_hook(module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        pre_captured["hidden"] = hidden.detach().to(torch.float64).clone()
        return None

    def post_hook(module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        post_captured["hidden"] = hidden.detach().to(torch.float64).clone()
        return None

    conditions = conditions_builder(direction, commanded_dose)
    on = conditions["ON"]
    pre_handle = layer_module.register_forward_hook(pre_hook)
    ctrl_handle = layer_module.register_forward_hook(on.controller)
    post_handle = layer_module.register_forward_hook(post_hook)
    try:
        on.begin(enc)
        with torch.no_grad():
            model.generate(
                **enc, max_new_tokens=2, min_new_tokens=2,
                do_sample=False, num_beams=1, return_dict_in_generate=True,
            )
        if on.reset is not None:
            on.reset()
    finally:
        pre_handle.remove()
        ctrl_handle.remove()
        post_handle.remove()

    pre_h = pre_captured.get("hidden")
    post_h = post_captured.get("hidden")
    identical = bool(pre_h is not None and post_h is not None
                    and torch.equal(pre_h, post_h))
    if identical:
        raise AssertionError(
            "recording hook observed the PRE-steer output (identical to the "
            "hook registered before the controller); the post-steer readback "
            "in G2/G3 is not measuring the delivered write. This is a "
            "harness construction failure, not a model result."
        )
    return {
        "checked": True, "identical": identical,
        "note": "post-steer recording hook confirmed to observe the replaced "
                "(post-steer) output, distinct from the pre-steer output.",
    }


# ==========================================================================
# Gate evaluation (H6-G1..G4). Thresholds transcribed from gates.yaml /
# AMENDMENT.md "Gates"; do not restate numbers here without updating both.
# ==========================================================================


def evaluate_g1(on: PassRecord, decode_len: int) -> dict:
    """HF's cached generate() produces the FIRST new token directly from the
    prefill call's own logits (no separate decode call for token 1): N new
    tokens means exactly N total forward calls on the hooked layer, of which
    N-1 are decode-only (seq_len == 1) calls; the prefill call is call #1.
    Both controllers' gen_stream mode explicitly skips call #1 and steers
    every call from #2 onward, i.e. exactly those N-1 decode calls. Ground
    truth is n_generated (the actual generated length), not the requested
    decode_len, though with min_new_tokens == max_new_tokens == decode_len
    (enforced by run_one_condition) they are equal by construction."""
    expected_decode_calls = on.n_generated - 1
    expected_total = on.n_generated
    passed = (
        on.independent_decode_calls == expected_decode_calls
        and on.independent_decode_calls > 1
        and on.in_hook_total_calls is not None
        and on.in_hook_total_calls == on.independent_total_calls
        and on.independent_total_calls == expected_total
    )
    return {
        "n_generated": on.n_generated,
        "in_hook_total_calls": on.in_hook_total_calls,
        "independent_total_calls": on.independent_total_calls,
        "independent_decode_calls": on.independent_decode_calls,
        "expected_decode_calls": expected_decode_calls,
        "expected_total_calls": expected_total,
        "passed": passed,
    }


def evaluate_g2(on: PassRecord, absent: PassRecord, direction_unit: torch.Tensor,
                commanded_dose: float, tol: float = 0.05) -> dict:
    d64 = direction_unit.to(torch.float64)
    n = min(len(on.decode_hidden), len(absent.decode_hidden))
    positions = []
    for t in range(n):
        delta = on.decode_hidden[t] - absent.decode_hidden[t]
        proj = float(delta @ d64)
        ratio = (proj / commanded_dose) if commanded_dose != 0 else float("nan")
        ok = abs(ratio - 1.0) <= tol
        positions.append({"t": t, "readback": proj, "ratio": ratio, "ok": ok})
    passed = bool(positions) and all(p["ok"] for p in positions)
    return {"commanded": commanded_dose, "positions": positions, "passed": passed}


def evaluate_g3(noop: PassRecord, absent: PassRecord,
                hidden_tol: float = 1e-6, logit_tol: float = 1e-3) -> dict:
    nh = min(len(noop.decode_hidden), len(absent.decode_hidden))
    hidden_deltas = [
        float((noop.decode_hidden[t] - absent.decode_hidden[t]).abs().max())
        for t in range(nh)
    ]
    nl = min(len(noop.decode_logits), len(absent.decode_logits))
    logit_checks = []
    for t in range(nl):
        d = (noop.decode_logits[t] - absent.decode_logits[t]).abs()
        argmax_noop = int(torch.argmax(noop.decode_logits[t]))
        argmax_absent = int(torch.argmax(absent.decode_logits[t]))
        logit_checks.append({
            "t": t, "max_abs_delta": float(d.max()),
            "argmax_match": argmax_noop == argmax_absent,
        })
    passed = (
        bool(hidden_deltas) and max(hidden_deltas) <= hidden_tol
        and bool(logit_checks)
        and all(c["argmax_match"] for c in logit_checks)
        and all(c["max_abs_delta"] <= logit_tol for c in logit_checks)
    )
    return {
        "hidden_max_abs_delta": max(hidden_deltas) if hidden_deltas else None,
        "logit_checks": logit_checks, "passed": passed,
    }


def evaluate_g4(on: PassRecord, absent: PassRecord) -> dict:
    """Diagnostic only, never gates pass/fail (AMENDMENT.md H6-G4)."""
    n = min(len(on.decode_logits), len(absent.decode_logits))
    first_divergence = None
    for t in range(n):
        if int(torch.argmax(on.decode_logits[t])) != int(torch.argmax(absent.decode_logits[t])):
            first_divergence = t
            break
    return {"first_divergence_position": first_divergence, "diverged": first_divergence is not None}


# ==========================================================================
# Per-prompt / aggregate orchestration.
# ==========================================================================


def run_prompt(path: str, model, layer_module, direction_unit: torch.Tensor,
               commanded_dose: float, enc: dict, decode_len: int) -> dict:
    conditions = PATH_BUILDERS[path](direction_unit, commanded_dose)
    records = {
        label: run_one_condition(model, layer_module, cond, enc, decode_len)
        for label, cond in conditions.items()
    }
    g1 = evaluate_g1(records["ON"], decode_len)
    g2 = evaluate_g2(records["ON"], records["ABSENT"], direction_unit, commanded_dose)
    g3 = evaluate_g3(records["NOOP"], records["ABSENT"])
    g4 = evaluate_g4(records["ON"], records["ABSENT"])
    return {"g1": g1, "g2": g2, "g3": g3, "g4": g4}


def aggregate(path: str, per_prompt: list[dict]) -> dict:
    def _all(gate: str) -> bool:
        return bool(per_prompt) and all(p[gate]["passed"] for p in per_prompt)

    n_diverged = sum(1 for p in per_prompt if p["g4"]["diverged"])
    return {
        "path": path,
        "n_prompts": len(per_prompt),
        "h6_g1_passed": _all("g1"),
        "h6_g2_passed": _all("g2"),
        "h6_g3_passed": _all("g3"),
        "certified": _all("g1") and _all("g2") and _all("g3"),
        "h6_g4_frac_prompts_with_divergence": (
            n_diverged / len(per_prompt) if per_prompt else None
        ),
        "per_prompt": per_prompt,
    }


# ==========================================================================
# Real-run model loading (GPU-gated; not exercised by the CPU smoke).
# ==========================================================================


def _require_gpu_ack(ack: bool) -> None:
    if not ack:
        raise SystemExit(
            "Refusing to run without --i-know-this-runs-on-gpu. This loads a "
            "real model and runs generate()."
        )


def load_tuner_model(model_name: str, revision: Optional[str] = None):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers as _tf

    major = int(_tf.__version__.split(".")[0])
    dtype_kw = {"dtype": torch.bfloat16} if major >= 5 else {"torch_dtype": torch.bfloat16}
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_name, revision=revision, device_map="auto", **dtype_kw
    )
    model.eval()
    return model, tokenizer


def load_bespoke_model(model_name: str):
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name, max_seq_length=2048, dtype=None, load_in_4bit=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def load_direction_json(path: Path) -> tuple[torch.Tensor, float]:
    """Loads an AK direction.json ({"theta": [...], "sigma": ...}) as a
    unit-norm float32 tensor + sigma. AK's build_commitment_perp already
    writes theta as a unit vector; this only re-normalizes defensively."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    theta = torch.tensor(record["theta"], dtype=torch.float32)
    norm = float(theta.norm())
    if norm > 0:
        theta = theta / norm
    return theta, float(record.get("sigma", 1.0))


def load_prompts_jsonl(path: Path, n: Optional[int]) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if n:
        rows = rows[:n]
    return rows


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True, choices=["bespoke", "tuner"])
    ap.add_argument("--model", required=True,
                    help="bespoke: unsloth/Qwen3-4B; tuner: any plain-HF causal LM")
    ap.add_argument("--revision", default=None)
    ap.add_argument("--layer", type=int, required=True,
                    help="decoder layer index (e.g. 24 for AK's L24)")
    ap.add_argument("--direction-json", required=True, type=Path,
                    help="AK direction.json ({theta, sigma, ...})")
    ap.add_argument("--dose-sigma", type=float, default=2.0,
                    help="commanded ON dose in sigma units (cell.yaml commanded_dose_sigma)")
    ap.add_argument("--pool", required=True, type=Path,
                    help="JSONL, one {row_key, question} per line; rendering is "
                         "the caller's own tokenizer chat template, NOT AK's "
                         "render_probe_prompt (see module docstring adjudication)")
    ap.add_argument("--n-prompts", type=int, default=20)
    ap.add_argument("--decode-len", type=int, default=16)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args(argv)

    _require_gpu_ack(args.i_know_this_runs_on_gpu)

    if args.path == "bespoke":
        model, tokenizer = load_bespoke_model(args.model)
        layer_module = bespoke_get_decoder_layer(model, args.layer)
    else:
        model, tokenizer = load_tuner_model(args.model, args.revision)
        layer_module = tuner_get_decoder_layer(model, args.layer)

    direction, sigma = load_direction_json(args.direction_json)
    commanded_dose = args.dose_sigma * sigma
    rows = load_prompts_jsonl(args.pool, args.n_prompts)

    pre_check = assert_recording_hook_observes_poststeer_output(
        model, layer_module, PATH_BUILDERS[args.path], direction, commanded_dose,
        tokenizer(rows[0]["question"], return_tensors="pt").to(next(model.parameters()).device),
    )

    per_prompt = []
    for row in rows:
        enc = tokenizer(row["question"], return_tensors="pt").to(next(model.parameters()).device)
        result = run_prompt(args.path, model, layer_module, direction, commanded_dose,
                            enc, args.decode_len)
        result["row_key"] = row.get("row_key")
        per_prompt.append(result)

    report = aggregate(args.path, per_prompt)
    report["construction_check"] = pre_check
    report["commanded_dose"] = commanded_dose
    report["sigma"] = sigma
    report["decode_len"] = args.decode_len

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"h6_{args.path}_gate_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "per_prompt"}, indent=2))
    return 0 if report["certified"] else 4


if __name__ == "__main__":
    sys.exit(main())
