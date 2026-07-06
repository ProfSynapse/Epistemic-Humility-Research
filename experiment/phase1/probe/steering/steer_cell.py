#!/usr/bin/env python3
"""Declarative steering / readout cell runner (the six-block cell model).

A "cell" is one steering or readout experiment described entirely by a YAML
config. This runner reads that YAML and executes it, so a new steering amendment
is a config + a signing rather than a bespoke multi-hour harness build. It is a
generalization of the hand-built AA/AC/AG/AL/AN harnesses: the AN couple write,
the AL additive push, the readout-only extraction, and the permuted control are
all expressible as arms over the same six blocks.

The six blocks (see .skills/steering-cell/SKILL.md for the full schema):

  surface   what to generate over: rows file, generation contract (model +
            optional adapter@revision, system-prompt ref, enable_thinking, decode
            params, max_new_tokens, seed, expected config_sha), and resume
            semantics (skip rows already present in the output rows.jsonl).
  readouts  frozen direction JSONs scored at the pre-generation anchor: each
            contributes a per-row scalar (raw projection and, given mu/sigma, a
            z-score) that the law can reference. Optional readback recording.
  law       how a row is selected and actuated: a selection expression over the
            frozen per-row readout scores (or an explicit flag file, or a seeded
            permuted control), an actuation mode (additive alpha*d, or setpoint
            erase-and-write g*sigma), a gain, a position policy, and a layer.
  arms      named runs = law overrides + a row subset + a tag (baseline,
            primary, permuted control, dose ladders, bidirectional).
  smoke     n rows + a per-arm readback tolerance; the runner refuses the full
            arms until the smoke has passed and recorded a state file.
  gates     scored separately by score_gates.py over this runner's provenance.

Reuses experiment/phase1/probe/steering/confidence_steer.py (SteeringHook,
GenerationHookController via steering_common) BY IMPORT, never copied. The hook
math is the item-11-certified batched final-position, per-element-alpha engine.

CPU note: the runner imports torch/model loaders lazily inside run paths, so the
config-parse / plan / selection paths (and --plan) run without a GPU or torch.

Usage:
  python steer_cell.py plan   --config cell.yaml
  python steer_cell.py run     --config cell.yaml --arm primary --smoke
  python steer_cell.py run     --config cell.yaml --arm primary
  python steer_cell.py run     --config cell.yaml   # all arms (after smoke)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import yaml

PROBE_DIR = Path(__file__).resolve().parent.parent
STEER_DIR = Path(__file__).resolve().parent
for _p in (str(PROBE_DIR), str(STEER_DIR), str(PROBE_DIR / "eval")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Config loading + provenance
# ---------------------------------------------------------------------------

def sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(config_path: Path) -> tuple[dict, str]:
    """Return (parsed config, sha256 of the raw config bytes).

    The sha is over the raw file bytes so an amendment can pin the exact cell.yaml
    it signed; a whitespace edit changes the sha and the pin no longer matches.
    """
    raw = config_path.read_bytes()
    cfg = yaml.safe_load(raw)
    if not isinstance(cfg, dict):
        raise ValueError(f"config {config_path} did not parse to a mapping")
    return cfg, sha256_of_bytes(raw)


def _require(cfg: dict, key: str) -> Any:
    if key not in cfg:
        raise ValueError(f"config missing required block: {key!r}")
    return cfg[key]


def resolve_path(base_dir: Path, ref: str) -> Path:
    """Resolve a path in the config relative to the config file's directory,
    unless it is already absolute."""
    p = Path(ref)
    return p if p.is_absolute() else (base_dir / p).resolve()


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


# ---------------------------------------------------------------------------
# Readouts: frozen directions scored at the pre-generation anchor
# ---------------------------------------------------------------------------

class Readout:
    """One frozen direction, scored at the anchor into a per-row scalar.

    A readout JSON carries at least ``theta`` (the direction), a ``layer`` (which
    hidden_states index to read), and optional ``mu``/``sigma`` calibration used
    to z-score the raw projection. ``name`` is how the law's selection expression
    references this readout's z-score (``<name>_z``) or raw projection
    (``<name>_raw``).
    """

    def __init__(self, spec: dict, base_dir: Path):
        self.name = spec["name"]
        self.path = resolve_path(base_dir, spec["path"])
        j = json.loads(self.path.read_text(encoding="utf-8"))
        theta = np.asarray(j.get("theta", j.get("d")), dtype=np.float64)
        norm = float(np.linalg.norm(theta))
        if norm == 0.0:
            raise ValueError(f"readout {self.name}: zero-norm direction")
        # unit direction for projection; the readout is scale-free after z-scoring
        self.theta = theta
        self.unit = theta / norm
        self.layer = int(spec.get("layer", j.get("layer", j.get("best_layer"))))
        self.mu = spec.get("mu", j.get("mu"))
        self.sigma = spec.get("sigma", j.get("sigma"))
        self.direction_sha = sha256_of_file(self.path)
        self.record_readback = bool(spec.get("record_readback", False))

    def project(self, hidden_row: np.ndarray) -> float:
        """Raw projection of a single hidden-state vector onto the unit direction."""
        return float(np.asarray(hidden_row, dtype=np.float64) @ self.unit)

    def zscore(self, raw: float) -> Optional[float]:
        if self.mu is None or self.sigma in (None, 0):
            return None
        return (raw - float(self.mu)) / float(self.sigma)

    def provenance(self) -> dict:
        return {"name": self.name, "path": str(self.path), "layer": self.layer,
                "sha256": self.direction_sha,
                "has_calibration": self.mu is not None and self.sigma not in (None, 0)}


# ---------------------------------------------------------------------------
# Law: selection + actuation
# ---------------------------------------------------------------------------

_ALLOWED_ACTUATION = ("additive", "setpoint", "none")
_ALLOWED_POSITION = ("anchor_only", "anchor_onward", "answer_window", "none")


class Law:
    """Selection + actuation policy for one arm.

    selection: one of
      - expression : a Python expression over the per-row readout scores
                     (e.g. "prop_z >= 1.0"); evaluated in a sandboxed namespace
                     that exposes only the row's readout scalars + math helpers.
      - flag_file  : a JSONL/JSON file naming the flagged row_keys explicitly.
      - permuted   : a seeded count-matched uniform draw over all rows (control).
      - all        : every row (readout-only / unsteered baseline surfaces).

    actuation:
      - additive : h += alpha * d at the steered positions (AL push / Arm A).
      - setpoint : h = h - (h.d)d + g*sigma*d  (AC/AN couple erase-and-write).
      - none     : readout-only; generate untouched (AM-style extraction).
    """

    def __init__(self, spec: dict, readouts: dict[str, Readout], base_dir: Path):
        sel = spec.get("selection", {"all": True})
        self.selection = sel
        self.actuation = spec.get("actuation", "none")
        if self.actuation not in _ALLOWED_ACTUATION:
            raise ValueError(f"actuation must be one of {_ALLOWED_ACTUATION}")
        self.gain = float(spec.get("gain", 0.0))
        self.position = spec.get("position", "none")
        if self.position not in _ALLOWED_POSITION:
            raise ValueError(f"position must be one of {_ALLOWED_POSITION}")
        # which readout supplies the actuation direction (defaults to the sole one)
        act_name = spec.get("actuation_readout")
        if act_name is None and self.actuation != "none":
            if len(readouts) != 1:
                raise ValueError(
                    "actuation_readout must name a readout when >1 readout is "
                    "declared")
            act_name = next(iter(readouts))
        self.actuation_readout = act_name
        self._readouts = readouts
        self._base_dir = base_dir

    def select_keys(self, row_order: list[str], scores: dict[str, dict],
                    *, seed: int) -> list[str]:
        """Return the flagged row_keys for this arm's selection block."""
        sel = self.selection
        if "all" in sel:
            return list(row_order)
        if "flag_file" in sel:
            p = resolve_path(self._base_dir, sel["flag_file"])
            data = json.loads(p.read_text(encoding="utf-8")) if p.suffix == ".json" \
                else [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]
            if isinstance(data, dict):
                keys = data.get("flagged_keys", list(data.keys()))
            else:
                keys = [d["row_key"] if isinstance(d, dict) else d for d in data]
            keyset = set(keys)
            return [k for k in row_order if k in keyset]
        if "permuted" in sel:
            match = sel["permuted"].get("match_count")
            rng = np.random.default_rng(seed)
            n = int(match) if match is not None else len(row_order)
            n = min(n, len(row_order))
            idx = rng.choice(len(row_order), size=n, replace=False)
            return [row_order[i] for i in sorted(idx.tolist())]
        if "expression" in sel:
            expr = sel["expression"]
            return [k for k in row_order
                    if _eval_selection(expr, scores.get(k, {}))]
        raise ValueError(f"unrecognized selection block: {sel!r}")


def _eval_selection(expr: str, row_scores: dict) -> bool:
    """Evaluate a selection expression against one row's readout scalars.

    The namespace exposes only the row's readout scores (e.g. prop_z, prop_raw)
    plus a few math builtins. No file/OS access is reachable from the expression.
    """
    ns = {"__builtins__": {}}
    ns.update({"abs": abs, "min": min, "max": max, "True": True, "False": False})
    ns.update({k: (v if v is not None else float("nan"))
               for k, v in row_scores.items()})
    try:
        return bool(eval(expr, ns, {}))  # noqa: S307 - sandboxed namespace
    except NameError as e:
        raise ValueError(
            f"selection expression {expr!r} references an undefined readout: {e}")


# ---------------------------------------------------------------------------
# Arm
# ---------------------------------------------------------------------------

class Arm:
    def __init__(self, spec: dict, base_law: dict, readouts: dict[str, Readout],
                 base_dir: Path):
        self.tag = spec["tag"]
        merged = dict(base_law)
        merged.update(spec.get("law", {}))
        self.law = Law(merged, readouts, base_dir)
        self.row_subset = spec.get("row_subset")  # None | "flagged_only"
        self.description = spec.get("description", "")

    def provenance(self) -> dict:
        return {
            "tag": self.tag, "description": self.description,
            "actuation": self.law.actuation, "gain": self.law.gain,
            "position": self.law.position, "selection": self.law.selection,
            "row_subset": self.row_subset,
        }


# ---------------------------------------------------------------------------
# Cell: parse the whole config into structured objects
# ---------------------------------------------------------------------------

class Cell:
    def __init__(self, cfg: dict, config_sha: str, config_path: Path):
        self.cfg = cfg
        self.config_sha = config_sha
        self.base_dir = config_path.resolve().parent
        self.name = cfg.get("name", config_path.stem)

        surface = _require(cfg, "surface")
        self.rows_file = resolve_path(self.base_dir, surface["rows_file"])
        gen = surface["generation"]
        self.model = gen["model"]
        self.adapter = gen.get("adapter")
        self.adapter_revision = gen.get("adapter_revision")
        self.system_prompt_ref = gen.get("system_prompt_ref")
        self.enable_thinking = bool(gen.get("enable_thinking", False))
        self.max_new_tokens = int(gen.get("max_new_tokens", 96))
        self.seed = int(gen.get("seed", 0))
        self.decode = gen.get("decode", {"do_sample": False, "num_beams": 1})
        self.expected_config_sha = gen.get("expected_config_sha")
        self.question_field = surface.get("question_field", "question")
        self.row_key_field = surface.get("row_key_field", "row_key")

        readout_specs = cfg.get("readouts", [])
        self.readouts = {r["name"]: Readout(r, self.base_dir) for r in readout_specs}

        base_law = cfg.get("law", {})
        self.arms = [Arm(a, base_law, self.readouts, self.base_dir)
                     for a in _require(cfg, "arms")]

        smoke = cfg.get("smoke", {})
        self.smoke_n = int(smoke.get("n", 20))
        self.readback_tolerance = float(smoke.get("readback_tolerance", 0.5))
        self.offtarget_parity = float(smoke.get("offtarget_parity", 1e-3))

        out = cfg.get("outputs", {})
        # analysis dir is UNTRACKED; default under the probe analysis tree.
        default_out = (PROBE_DIR / "analysis" / "steer_cells" / self.name)
        self.out_dir = resolve_path(self.base_dir, out["dir"]) \
            if "dir" in out else default_out

    def arm(self, tag: str) -> Arm:
        for a in self.arms:
            if a.tag == tag:
                return a
        raise KeyError(f"no arm tagged {tag!r} (have {[a.tag for a in self.arms]})")

    def state_file(self) -> Path:
        return self.out_dir / "smoke_state.json"

    def manifest(self) -> dict:
        return {
            "schema_version": "steer-cell/v1",
            "name": self.name,
            "config_sha256": self.config_sha,
            "surface": {
                "rows_file": str(self.rows_file),
                "model": self.model,
                "adapter": self.adapter,
                "adapter_revision": self.adapter_revision,
                "system_prompt_ref": self.system_prompt_ref,
                "enable_thinking": self.enable_thinking,
                "max_new_tokens": self.max_new_tokens,
                "seed": self.seed,
                "decode": self.decode,
            },
            "readouts": [r.provenance() for r in self.readouts.values()],
            "arms": [a.provenance() for a in self.arms],
        }


# ---------------------------------------------------------------------------
# Selection scoring: score every readout at the anchor for every row (needs GPU
# for real models; the plan path stops before this).
# ---------------------------------------------------------------------------

def _resolve_system_prompt(ref: Optional[str], base_dir: Path) -> str:
    """Resolve the system-prompt reference to text.

    A ref may be: a literal string prefixed 'literal:', a path to a text/JSON
    file, or a dotted 'module:function' loader (e.g.
    'amendment_ah_stage0_extract:load_baseline_system_prompt'). None => "".
    """
    if not ref:
        return ""
    if ref.startswith("literal:"):
        return ref[len("literal:"):]
    if ":" in ref and "/" not in ref and not ref.endswith((".txt", ".json")):
        mod_name, fn_name = ref.split(":", 1)
        import importlib
        mod = importlib.import_module(mod_name)
        return getattr(mod, fn_name)()
    p = resolve_path(base_dir, ref)
    txt = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return json.loads(txt)
    return txt


def build_hidden_reader(cell: Cell):
    """Load the model once and return a callable that yields, for a rendered
    prompt, the hidden_states at each readout's layer at the anchor (prompt
    last-token) position, plus a steered-generation function. GPU path.
    """
    import torch  # lazy: only when actually running
    from confidence_steer import load_model_and_tokenizer

    model, tokenizer = load_model_and_tokenizer(
        cell.model, device="cuda", adapter=cell.adapter,
        adapter_revision=cell.adapter_revision)
    device = next(model.parameters()).device
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer, device, torch


# ---------------------------------------------------------------------------
# Plan (CPU, no torch): parse + report the cell without loading a model.
# ---------------------------------------------------------------------------

def cmd_plan(cell: Cell) -> int:
    rows = load_jsonl(cell.rows_file)
    print(json.dumps({
        "name": cell.name,
        "config_sha256": cell.config_sha,
        "n_rows": len(rows),
        "n_readouts": len(cell.readouts),
        "readouts": [r.provenance() for r in cell.readouts.values()],
        "arms": [a.provenance() for a in cell.arms],
        "out_dir": str(cell.out_dir),
        "smoke": {"n": cell.smoke_n,
                  "readback_tolerance": cell.readback_tolerance,
                  "offtarget_parity": cell.offtarget_parity},
    }, indent=2))
    if cell.expected_config_sha and cell.expected_config_sha != cell.config_sha:
        print(f"[plan] WARNING: expected_config_sha "
              f"{cell.expected_config_sha[:12]} != actual "
              f"{cell.config_sha[:12]}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Steering hook wiring (reuses confidence_steer.SteeringHook)
# ---------------------------------------------------------------------------

def _decoder_layers(model):
    from confidence_steer import get_decoder_layer
    # get_decoder_layer returns a single layer; we want the ModuleList so the
    # setpoint hook can register at an arbitrary index. Reuse its unwrap by
    # walking to the parent of layer 0.
    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    for attr_path in (["model", "layers"], ["language_model", "model", "layers"],
                      ["model", "decoder", "layers"], ["transformer", "h"]):
        obj = base
        ok = True
        for attr in attr_path:
            if not hasattr(obj, attr):
                ok = False
                break
            obj = getattr(obj, attr)
        if ok and hasattr(obj, "__getitem__"):
            return obj
    raise AttributeError("cannot locate decoder layer ModuleList")


class SetpointHook:
    """Erase-and-write couple hook: h' = h - (h.d)d + g*sigma*d at the steered
    positions. Mirrors the AC/AN couple write; kept here (not in confidence_steer)
    because it is the setpoint actuation the additive SteeringHook does not cover.

    Same activation contract as GenerationHookController: the caller sets
    ``self.g`` (per-row gain, None => no-op) and ``self.active`` around each
    generate/forward.
    """

    def __init__(self, unit_dir, sigma: float, position: str):
        import torch
        self.torch = torch
        self.unit = unit_dir  # unit-norm tensor (hidden_dim,)
        self.sigma = float(sigma)
        self.position = position  # "anchor_only" | "anchor_onward" | "answer_window"
        self.g = None
        self.active = False

    def __call__(self, module, inputs, output):
        if not self.active or self.g is None:
            return output
        torch = self.torch
        if isinstance(output, tuple):
            hidden, rest = output[0], output[1:]
        else:
            hidden, rest = output, None
        d = self.unit.to(hidden.device).to(hidden.dtype)
        setpoint = float(self.g) * self.sigma
        hidden = hidden.clone()
        _batch, seq_len, _dim = hidden.shape
        # anchor_only steers the single last prefill token; anchor_onward /
        # answer_window steer the last position of each decode step (seq_len==1
        # under KV cache) and the anchor at prefill.
        if seq_len > 1:  # prefill
            pos = slice(-1, None)
        else:  # decode step
            if self.position == "anchor_only":
                return output if rest is None else output
            pos = slice(0, 1)
        proj = (hidden[:, pos, :] @ d).unsqueeze(-1)
        hidden[:, pos, :] = hidden[:, pos, :] - proj * d + setpoint * d
        return (hidden,) + rest if rest is not None else hidden


# ---------------------------------------------------------------------------
# Run one arm (GPU). Kept compact; the heavy plumbing is imported.
# ---------------------------------------------------------------------------

def cmd_run(cell: Cell, arm_tag: Optional[str], smoke: bool,
            force_no_smoke: bool, overwrite: bool) -> int:
    from backends import render_probe_prompt  # noqa: E402
    import scorers  # noqa: E402

    model, tokenizer, device, torch = build_hidden_reader(cell)
    system_prompt = _resolve_system_prompt(cell.system_prompt_ref, cell.base_dir)
    rows = load_jsonl(cell.rows_file)
    row_order = [r[cell.row_key_field] for r in rows]
    row_by_key = {r[cell.row_key_field]: r for r in rows}

    layers = _decoder_layers(model)

    # --- score readouts at the anchor for every row (one forward each) --------
    def anchor_hidden_states(rendered: str) -> dict[int, np.ndarray]:
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        wanted = {r.layer for r in cell.readouts.values()}
        return {L: out.hidden_states[L][0, prompt_len - 1, :].float().cpu().numpy()
                for L in wanted}

    print(f"[steer-cell] scoring {len(cell.readouts)} readouts over "
          f"{len(row_order)} rows ...", flush=True)
    scores: dict[str, dict] = {}
    for k in row_order:
        rendered, _ = render_probe_prompt(
            tokenizer, system_prompt, row_by_key[k][cell.question_field],
            enable_thinking=cell.enable_thinking)
        hs = anchor_hidden_states(rendered)
        row_scores = {}
        for r in cell.readouts.values():
            raw = r.project(hs[r.layer])
            row_scores[f"{r.name}_raw"] = raw
            z = r.zscore(raw)
            if z is not None:
                row_scores[f"{r.name}_z"] = z
        scores[k] = row_scores

    arms = [cell.arm(arm_tag)] if arm_tag else cell.arms
    cell.out_dir.mkdir(parents=True, exist_ok=True)
    (cell.out_dir / "manifest.json").write_text(json.dumps(cell.manifest(), indent=2))

    # smoke-first discipline: refuse a full arm unless a smoke passed for it.
    state = {}
    if cell.state_file().exists():
        state = json.loads(cell.state_file().read_text())

    for arm in arms:
        if not smoke and not force_no_smoke and not state.get(arm.tag, {}).get("passed"):
            print(f"[steer-cell] REFUSING full arm {arm.tag!r}: no passed smoke "
                  f"on record. Run with --smoke first (or --force-no-smoke).",
                  file=sys.stderr)
            return 3
        rc = _run_arm(cell, arm, scores, row_order, row_by_key, layers,
                      model, tokenizer, device, torch, render_probe_prompt,
                      scorers, system_prompt, smoke, overwrite, state)
        if rc != 0:
            return rc

    if smoke:
        cell.state_file().write_text(json.dumps(state, indent=2))
    return 0


def _run_arm(cell, arm, scores, row_order, row_by_key, layers, model, tokenizer,
             device, torch, render_probe_prompt, scorers, system_prompt, smoke,
             overwrite, state) -> int:
    from confidence_steer import SteeringHook
    import numpy as _np

    law = arm.law
    flagged = set(law.select_keys(row_order, scores, seed=cell.seed))

    # actuation setup
    hook = handle = None
    if law.actuation != "none":
        r = cell.readouts[law.actuation_readout]
        unit = torch.from_numpy(r.unit.astype("float32"))
        if law.actuation == "additive":
            pos_map = {"anchor_only": "anchor", "anchor_onward": "all_post",
                       "answer_window": "all_post"}
            hook = SteeringHook(d=unit, alpha=law.gain,
                                position=pos_map[law.position])
        else:  # setpoint
            if r.sigma in (None, 0):
                raise ValueError(
                    f"setpoint actuation needs sigma on readout {r.name}")
            hook = SetpointHook(unit, float(r.sigma), law.position)
        handle = layers[r.layer - 1].register_forward_hook(hook)  # layer L reads hs[L]=block L-1 output

    sel_keys = ([k for k in row_order if k in flagged]
                if arm.row_subset == "flagged_only" else list(row_order))
    if smoke:
        sel_keys = sel_keys[:cell.smoke_n]

    tag_dir = cell.out_dir / ("smoke_" + arm.tag if smoke else arm.tag)
    (tag_dir / "gen").mkdir(parents=True, exist_ok=True)
    rows_path = tag_dir / "gen" / "rows.jsonl"

    done = set()
    prior = []
    if rows_path.exists() and not overwrite:
        for pr in load_jsonl(rows_path):
            done.add(pr["row_key"]); prior.append(pr)

    # readback for the smoke: verify commanded coordinate move + off-target parity
    readback = []

    def generate(rendered, gain):
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        if hook is not None:
            if isinstance(hook, SteeringHook):
                hook.alpha = gain if gain is not None else 0.0
            else:
                hook.g = gain
                hook.active = gain is not None
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=cell.max_new_tokens,
                do_sample=cell.decode.get("do_sample", False),
                num_beams=cell.decode.get("num_beams", 1),
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                return_dict_in_generate=True)
        if hook is not None and not isinstance(hook, SteeringHook):
            hook.active = False; hook.g = None
        seq = gen.sequences[0].tolist()
        text = tokenizer.decode(seq[prompt_len:], skip_special_tokens=True).strip()
        return text, prompt_len

    with rows_path.open("w", encoding="utf-8") as fh:
        for pr in prior:
            fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        for k in sel_keys:
            if k in done:
                continue
            is_flagged = k in flagged
            gain = law.gain if (is_flagged and law.actuation != "none") else None
            rendered, _ = render_probe_prompt(
                tokenizer, system_prompt, row_by_key[k][cell.question_field],
                enable_thinking=cell.enable_thinking)
            if smoke and hook is not None and is_flagged:
                _readback_row(readback, k, rendered, gain, cell, law,
                              tokenizer, model, device, torch, hook)
            text, prompt_len = generate(rendered, gain)
            refused = bool(scorers.is_stated_confidence_refusal(text))
            fh.write(json.dumps({
                "row_key": k, "arm": arm.tag, "flagged": is_flagged,
                "gain": gain, "refused": refused,
                "answer_text": text, "prompt_len": prompt_len,
                "scores": scores.get(k, {}),
            }, ensure_ascii=False) + "\n")
            fh.flush()

    if handle is not None:
        handle.remove()

    if smoke and hook is not None:
        ok, report = _smoke_verdict(readback, cell, law)
        (tag_dir / "readback.json").write_text(json.dumps(report, indent=2))
        state[arm.tag] = {"passed": bool(ok), "n": len(readback),
                          "config_sha256": cell.config_sha}
        print(f"[steer-cell] smoke arm={arm.tag} readback OK={ok} "
              f"(n={len(readback)})", flush=True)
        if not ok:
            return 4
    elif smoke:
        state[arm.tag] = {"passed": True, "n": len(sel_keys),
                          "config_sha256": cell.config_sha, "readout_only": True}
    print(f"[steer-cell] arm={arm.tag} wrote {rows_path}", flush=True)
    return 0


def _readback_row(readback, k, rendered, gain, cell, law, tokenizer, model,
                  device, torch, hook):
    """Record commanded vs observed anchor coordinate move for a flagged row."""
    from confidence_steer import SteeringHook
    r = cell.readouts[law.actuation_readout]
    unit64 = r.unit.astype("float64")
    enc = tokenizer(rendered, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])

    def anchor_proj(active_gain):
        if isinstance(hook, SteeringHook):
            hook.alpha = active_gain if active_gain is not None else 0.0
        else:
            hook.g = active_gain; hook.active = active_gain is not None
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        if not isinstance(hook, SteeringHook):
            hook.active = False; hook.g = None
        h = out.hidden_states[r.layer][0, prompt_len - 1, :].float().cpu().numpy()
        return float(h.astype("float64") @ unit64)

    p0 = anchor_proj(None)
    p1 = anchor_proj(gain)
    if law.actuation == "setpoint":
        commanded = float(gain) * float(r.sigma)
        err = abs(p1 - commanded)
    else:  # additive: commanded move is alpha (unit direction)
        commanded = float(gain)
        err = abs((p1 - p0) - commanded)
    readback.append({"row_key": k, "gain": gain, "coord_baseline": round(p0, 4),
                     "coord_steered": round(p1, 4), "commanded": round(commanded, 4),
                     "abs_error": round(err, 4)})


def _smoke_verdict(readback, cell, law) -> tuple[bool, dict]:
    if not readback:
        return True, {"n": 0, "note": "no flagged rows in smoke selection"}
    max_err = max(r["abs_error"] for r in readback)
    write_ok = max_err <= cell.readback_tolerance
    return bool(write_ok), {
        "arm_actuation": law.actuation, "n_flagged": len(readback),
        "max_abs_error": round(max_err, 4),
        "readback_tolerance": cell.readback_tolerance,
        "write_ok": bool(write_ok), "rows": readback,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "run"):
        sp = sub.add_parser(name)
        sp.add_argument("--config", required=True, type=Path)
        if name == "run":
            sp.add_argument("--arm", default=None, help="run one arm by tag")
            sp.add_argument("--smoke", action="store_true",
                            help="smoke: N rows + readback, records a pass state")
            sp.add_argument("--force-no-smoke", action="store_true",
                            help="run a full arm without a recorded smoke pass")
            sp.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    # xet guards inside the entrypoint (parity with the Modal wrapper).
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

    cfg, sha = load_config(args.config)
    cell = Cell(cfg, sha, args.config)

    if args.cmd == "plan":
        # plan is a CPU diagnostic; a sha mismatch is a WARNING (emitted inside
        # cmd_plan), not fatal, so an author can inspect an edited cell.
        return cmd_plan(cell)

    # run is the confirmatory surface: an edited signed cell is fatal before any
    # model load, so a run never diverges from the sha the amendment pinned.
    if cell.expected_config_sha and cell.expected_config_sha != sha:
        print(f"[steer-cell] FATAL: config sha {sha[:12]} != expected "
              f"{cell.expected_config_sha[:12]} (the signed cell was edited)",
              file=sys.stderr)
        return 2
    return cmd_run(cell, args.arm, args.smoke, args.force_no_smoke, args.overwrite)


if __name__ == "__main__":
    sys.exit(main())
