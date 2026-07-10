#!/usr/bin/env python3
"""Two-signal trust readout: live inference reference pipeline (library).

Loads a base model + the fitted gate/dial artifacts (from fit_calibration.py) and
runs the deployable two-stage pipeline end-to-end on a single prompt:

    gate (answerability, pre-gen anchor)  ->  abstain | generate
                                                          |
                                          dial (correctness, post-gen) -> calibrated trust
                                                          |
                                          veto = low trust on a generated answer

This is a REFERENCE pipeline, not production serving (see
docs/architecture/two-signal-readout-inference-serving.md, sections 8 & 10). It
uses the validated re-forward capture path (4.2): one prompt-only forward for the
gate, generation, then one forward over [prompt + answer] for the dial. That is
identical to how the offline extractors produced the activations the probes were
fit on, so the live reads match the validated surface exactly.

The base model is never modified. The "probe" is a numpy dot product on one
layer's residual-stream vector plus a calibration map; nothing is injected into
the weights or the generation (the read-and-act-externally stance).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_DIR = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_DIR / "archive/experiment/phase1/probe"
EVAL_DIR = REPO_DIR / "experiment/phase1/eval"
for _p in (str(PROBE_DIR), str(EVAL_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Reuse the EXACT generation surface the dial was fit on.
from amendment_s_correctness_probe_extract import (  # noqa: E402
    SYSTEM_PROMPT, MODEL_NAME, _content_end_index,
)
from backends import render_probe_prompt  # noqa: E402

ARTIFACT_DIR = REPO_DIR / "experiments" / "common" / "artifacts" / "two_signal_calibration"
_EPS = 1e-6


def _logit(p):
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class ProbeArtifact:
    """A fitted linear readout + calibration map for one signal at one layer."""
    signal: str            # 'gate' | 'dial'
    position: str          # 'pre' | 'post'
    layer: int
    mean: np.ndarray       # scaler mean   [d]
    scale: np.ndarray      # scaler scale  [d]
    coef: np.ndarray       # logistic coef [d]
    intercept: float
    calibration: dict      # {'method': 'platt', a, b} | {'method':'isotonic','x','y'}
    auroc: float
    ece_calibrated: float

    @classmethod
    def load(cls, manifest_path: Path) -> "ProbeArtifact":
        m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        arr = np.load(Path(manifest_path).with_suffix(".npz"))
        cal = dict(m["calibration"])
        if cal["method"] == "isotonic":
            cal = {"method": "isotonic", "x": arr["cal_x"], "y": arr["cal_y"]}
        return cls(
            signal=m["signal"], position=m["position"], layer=int(m["layer"]),
            mean=arr["scaler_mean"], scale=arr["scaler_scale"], coef=arr["logreg_coef"],
            intercept=float(m["logreg_intercept"]), calibration=cal,
            auroc=float(m["metrics"]["auroc"]),
            ece_calibrated=float(m["metrics"]["ece_shipped"]),
        )

    def raw_prob(self, h: np.ndarray) -> float:
        """P(positive class) before calibration, for one hidden vector h [d]."""
        z = (h.astype(np.float64) - self.mean) / self.scale
        return float(_sigmoid(z @ self.coef + self.intercept))

    def calibrated(self, h: np.ndarray) -> float:
        """Calibrated probability for one hidden vector h [d]."""
        p = self.raw_prob(h)
        c = self.calibration
        if c["method"] == "platt":
            return float(_sigmoid(c["a"] * _logit(np.array([p]))[0] + c["b"]))
        return float(np.interp(p, c["x"], c["y"]))


@dataclass
class TrustResult:
    question: str
    gate_answerability: float      # calibrated P(answerable)
    gate_pass: bool
    abstained: bool
    answer: str | None
    trust: float | None            # calibrated P(answer correct); None if abstained
    trust_raw: float | None
    vetoed: bool                   # generated but trust below veto threshold
    decision: str                  # 'abstain' | 'answer' | 'answer_low_trust'

    def render(self) -> str:
        if self.abstained:
            return (f"[ABSTAIN]  answerability={self.gate_answerability:.2f} "
                    f"(< gate threshold)\n  \"I don't know.\"")
        flag = "  [LOW-TRUST / possible confabulation]" if self.vetoed else ""
        return (f"answerability={self.gate_answerability:.2f}  "
                f"trust={self.trust:.2f}{flag}\n  {self.answer}")


class TwoSignalReadout:
    """Live two-signal pipeline over a base model + gate/dial artifacts."""

    def __init__(self, model_name: str = MODEL_NAME,
                 gate_artifact: Path | None = None,
                 dial_artifact: Path | None = None,
                 gate_threshold: float = 0.5,
                 veto_threshold: float = 0.3,
                 max_new_tokens: int = 48,
                 device: str = "cuda"):
        self.model_name = model_name
        self.gate = ProbeArtifact.load(gate_artifact or _default_artifact("gate"))
        self.dial = ProbeArtifact.load(dial_artifact or _default_artifact("dial"))
        assert self.gate.position == "pre" and self.dial.position == "post"
        self.gate_threshold = gate_threshold
        self.veto_threshold = veto_threshold
        self.max_new_tokens = max_new_tokens
        self.device = device
        self._model = None
        self._tok = None

    # -- model lifecycle (lazy; GPU only touched on first use) ---------------
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"[runtime] loading {self.model_name} ...", flush=True)
        self._tok = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype=torch.bfloat16, device_map=self.device)
        self._model.eval()
        tok = self._tok
        self._special_ids = set(tok.all_special_ids or [])
        if tok.eos_token_id is not None:
            self._special_ids.add(tok.eos_token_id)
        im_end = tok.convert_tokens_to_ids("<|im_end|>")
        self._im_end = im_end if isinstance(im_end, int) and im_end >= 0 else None
        if self._im_end is not None:
            self._special_ids.add(self._im_end)
        if self._im_end is not None and tok.eos_token_id is not None:
            self._eos_for_gen = [tok.eos_token_id, self._im_end]
        else:
            self._eos_for_gen = self._im_end if self._im_end is not None else tok.eos_token_id
        return self

    def _hidden_at(self, input_ids, position_index: int, layer: int) -> np.ndarray:
        """One forward; return layer-L residual-stream vector at a token position."""
        import torch
        attn = torch.ones_like(input_ids)
        with torch.no_grad():
            out = self._model(input_ids=input_ids, attention_mask=attn,
                              output_hidden_states=True, use_cache=False)
        return out.hidden_states[layer][0, position_index, :].float().cpu().numpy()

    def generate_with_trust(self, question: str) -> TrustResult:
        if self._model is None:
            self.load()
        import torch
        tok = self._tok
        rendered, _mode = render_probe_prompt(tok, SYSTEM_PROMPT, question,
                                              enable_thinking=False)
        enc = tok(rendered, return_tensors="pt").to(self.device)
        prompt_ids = enc["input_ids"]
        prompt_len = int(prompt_ids.shape[1])

        # --- STAGE 1: GATE (answerability at the pre-gen anchor) ---
        h_pre = self._hidden_at(prompt_ids, prompt_len - 1, self.gate.layer)
        gate_p = self.gate.calibrated(h_pre)
        if gate_p < self.gate_threshold:
            return TrustResult(question, gate_p, False, True, None, None, None,
                               False, "abstain")

        # --- STAGE 2: GENERATE ---
        with torch.no_grad():
            gen = self._model.generate(
                **enc, max_new_tokens=self.max_new_tokens, do_sample=False, num_beams=1,
                eos_token_id=self._eos_for_gen,
                pad_token_id=tok.pad_token_id or tok.eos_token_id,
                return_dict_in_generate=True)
        full = gen.sequences[0]
        full_list = full.tolist()
        answer = tok.decode(full_list[prompt_len:], skip_special_tokens=True).strip()
        content_end = _content_end_index(full_list, prompt_len, self._special_ids)
        if content_end is None or not answer:
            return TrustResult(question, gate_p, True, False, answer or "", None, None,
                               False, "answer")  # empty answer; no dial read

        # --- STAGE 3: DIAL (correctness at the last answer content token) ---
        fwd_ids = full[: content_end + 1].unsqueeze(0).to(self.device)
        h_post = self._hidden_at(fwd_ids, content_end, self.dial.layer)
        trust_raw = self.dial.raw_prob(h_post)
        trust = self.dial.calibrated(h_post)
        vetoed = trust < self.veto_threshold
        return TrustResult(question, gate_p, True, False, answer, trust, trust_raw,
                           vetoed, "answer_low_trust" if vetoed else "answer")


def _default_artifact(signal: str) -> Path:
    hits = sorted(ARTIFACT_DIR.glob(f"{signal}__*.json"))
    if not hits:
        raise FileNotFoundError(
            f"no {signal} artifact in {ARTIFACT_DIR}; run fit_calibration.py --signal {signal}")
    return hits[0]


if __name__ == "__main__":
    # Tiny self-check that does NOT load the model: artifacts load + apply on a
    # random vector (shape/calibration sanity). Live use is via two_signal_cli.py.
    g = ProbeArtifact.load(_default_artifact("gate"))
    d = ProbeArtifact.load(_default_artifact("dial"))
    rng = np.random.default_rng(0)
    print(f"gate  L{g.layer} dim={g.mean.shape[0]} auroc={g.auroc} "
          f"ece_cal={g.ece_calibrated} cal={g.calibration['method']} "
          f"-> P={g.calibrated(rng.standard_normal(g.mean.shape[0])):.3f}")
    print(f"dial  L{d.layer} dim={d.mean.shape[0]} auroc={d.auroc} "
          f"ece_cal={d.ece_calibrated} cal={d.calibration['method']} "
          f"-> P={d.calibrated(rng.standard_normal(d.mean.shape[0])):.3f}")
    print("artifacts load + apply OK (model not loaded; use two_signal_cli.py for live)")
