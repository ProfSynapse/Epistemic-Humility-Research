"""A fake ``EngineCLI.run`` that emulates the engine's observable contract on CPU.

It reads the same generated configs the real engine would, and writes the same
artifact shapes (inspect JSON, validation receipts, capture manifests, steer
JSONL).  Behaviour of "the model" is a deterministic function of (row, condition)
so the pipeline logic - selection, controls, adjudication, roll-up - is exercised
end to end.  It proves harness logic only; it says nothing about the real engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml
from safetensors.numpy import load_file

from bf16 import realized_delta, to_bf16
from capturefix import write_capture

DIM, INTER = 2560, 9216
_W: dict[int, tuple[np.ndarray, float]] = {}

# (confab refusal, known refusal) per candidate on any population
CAND_P = {"b20_s4": (0.20, 0.00), "b20_s16": (0.55, 0.03), "b21_s4": (0.30, 0.01), "b21_s16": (0.62, 0.02),
          "b22_s4": (0.10, 0.00), "b22_s16": (0.45, 0.10)}


def weight(block: int):
    if block not in _W:
        rng = np.random.default_rng(1000 + block)
        w = to_bf16(rng.standard_normal((DIM, INTER)).astype(np.float32) * 0.02)
        # ||W||_F is inflated 2.5x (a heavier tensor than the random slice) so lambda=16 stays inside the 0.05 budget here;
        # real budgets are decided only by the real engine's receipts.
        _W[block] = (w, 2.5 * float(np.sqrt((w.astype(np.float64) ** 2).sum())))
    return _W[block]


def u01(key: str, salt: str = "") -> float:
    return int(hashlib.sha256(f"{key}|{salt}".encode()).hexdigest()[:8], 16) / 2**32


def digest(spec_sha: str, payload_sha: str) -> str:
    return hashlib.sha256(f"{spec_sha}:{payload_sha}".encode()).hexdigest()


class FakeCLI:
    def __init__(self, layout, project_root: Path):
        self.layout, self.root = layout, Path(project_root)
        self.calls: list[list[str]] = []
        self.fail_next: dict[str, int] = {}

    # EngineCLI surface -------------------------------------------------------------
    def command(self, operation, arguments=()):
        return [sys.executable, "-m", "tuner", operation, *arguments]

    def run(self, operation, arguments=(), *, timeout=None, stdout=None, stderr=None, guard_parent=False, pass_fds=()):
        self._stdout = stdout
        args = list(arguments)
        self.calls.append(args)
        assert operation == "mechinterp"
        verb = args[0]
        rc = getattr(self, "_" + verb.replace("-", "_"))(args)
        if rc:
            raise subprocess.CalledProcessError(rc, "tuner")

    # helpers -------------------------------------------------------------------------
    def _opt(self, args, name):
        return args[args.index(name) + 1]

    def _local(self, ref):
        if ref.startswith("project://"):
            return self.layout.project_local(ref)
        return self.layout.to_local(ref)

    def _emit(self, doc):
        # A subprocess writes to file descriptor 1, not to Python's sys.stdout.
        data = (json.dumps(doc) + "\n").encode()
        if getattr(self, "_stdout", None) is not None:
            self._stdout.write(data)
        else:
            os.write(1, data)

    # weights-inspect ----------------------------------------------------------------------
    def _weights_inspect(self, args):
        req = yaml.safe_load(self._local(self._opt(args, "--weights-config")).read_text())
        report = {"schema_version": req["schema_version"], "files": [], "tensors": []}
        if req.get("hash_files"):
            report["files"] = [{"name": "model.safetensors-00001-of-00002.safetensors", "size": 1, "sha256": "a" * 64},
                               {"name": "model.safetensors-00002-of-00002.safetensors", "size": 1, "sha256": "b" * 64}]
            report["index_sha256"] = "c" * 64
        for pat in req.get("tensors", []):
            block = int(pat.split("layers.")[1].split(".")[0])
            name = f"model.language_model.layers.{block}.mlp.down_proj.weight"
            report["tensors"].append({"name": name, "dtype": "bfloat16", "shape": [DIM, INTER], "nbytes": DIM * INTER * 2,
                                      "sha256": hashlib.sha256(name.encode()).hexdigest(), "file": "x"})
        report["listing_truncated"] = False
        report["revision_evidence"] = []
        if req.get("projections"):
            proj = req["projections"][0]
            block = int(proj["tensor"].split("layers.")[1].split(".")[0])
            vec_ref = proj["vector"]["direction_json"]
            vec = np.asarray(json.loads(self._local(vec_ref["path"]).read_text())["vector"], dtype=np.float64)
            w, _ = weight(block)
            report["projections"] = [{"id": proj["id"], "tensor": proj["tensor"], "kind": "dot", "axis": "cols", "dtype": "bfloat16",
                                      "shape": [DIM, INTER], "tensor_sha256": hashlib.sha256(proj["tensor"].encode()).hexdigest(),
                                      "indices": "all", "n_values": INTER, "values": (vec @ w.astype(np.float64)).tolist()}]
        self._emit({"success": True, "data": report})
        return 0

    # weights-patch ----------------------------------------------------------------------------
    def _weights_patch(self, args):
        spec_path = self._local(self._opt(args, "--weights-config"))
        spec = yaml.safe_load(spec_path.read_text())
        payload = load_file(str(self._local(spec["payload"]["path"])))
        op = spec["operations"][0]
        block = int(op["tensor"].split("layers.")[1].split(".")[0])
        w, norm = weight(block)
        delta, entries = realized_delta(w[:, op["cols"]], payload["u"], payload["v"], op["scale"])
        b = spec["budget"]
        rel = delta / norm
        if entries > b["max_modified_entries"] or rel > b["max_relative_frobenius"]:
            self._emit({"success": False, "error": {"code": "WEIGHTS_BUDGET", "message": "budget exceeded"}})
            return 1
        pd = digest(hashlib.sha256(spec_path.read_bytes()).hexdigest(), spec["payload"]["sha256"])
        if "--export" in args:
            out = self._local(spec["export"]["output_dir"])
            out.mkdir(parents=True, exist_ok=False)
            (out / "marker").write_text(spec_path.parent.name)       # the exported checkpoint "contains" this patch
            after = hashlib.sha256(f"{op['tensor']}|{spec['payload']['sha256']}|{op['scale']}|{op['cols']}".encode()).hexdigest()
            self._emit({"success": True, "data": {"mode": "export", "patch_digest": pd, "totals": {"entries": entries},
                                                   "manifest": {"tensors": [{"name": op["tensor"], "before_sha256": "0" * 64, "after_sha256": after}],
                                                                "output": {"weight_files": {}}}}})
            return 0
        after = hashlib.sha256(f"{op['tensor']}|{spec['payload']['sha256']}|{op['scale']}|{op['cols']}".encode()).hexdigest()
        receipt = {"schema_version": "mechinterp-weight-patch-receipt/v1", "patch_digest": pd, "noop": entries == 0,
                   "tensors": [{"name": op["tensor"], "entries_changed": entries, "delta_frobenius": delta, "relative_frobenius": rel,
                                "before_sha256": "0" * 64, "after_sha256": after}]}
        self._emit({"success": True, "data": {"mode": "validate", "receipt": receipt}})
        return 0

    # extract ---------------------------------------------------------------------------------------
    def _extract(self, args):
        cfg = yaml.safe_load(self._local(self._opt(args, "--mi-config")).read_text())
        rows = [json.loads(line) for line in self._local(cfg["rows_path"]).read_text().splitlines() if line.strip()]
        out = self._local(cfg["output_dir"])
        u_d = np.asarray(json.loads(self._local("project://experiments/common/directions/qwen35-4b-hs20/u_d.json").read_text())["vector"])
        from hs20_nwe.config import Cell
        from conftest import EXPERIMENT

        s = Cell.load(EXPERIMENT).cell["sensor"]

        def residual(r):
            # confab rows read doubtful (low proj) with a few misses; known rows read confident
            low = r["role"] != "known_correct" and u01(r["row_key"], "fire") < 0.9
            proj = s["mu_d"] - 2 * s["sigma_d"] if low else s["mu_d"] + 2 * s["sigma_d"]
            return proj * u_d

        def site(r, b):
            base = np.random.default_rng(int(hashlib.sha256(f"{r['row_key']}{b}".encode()).hexdigest()[:6], 16)).standard_normal(INTER) * 0.1
            return base + (1.0 if r["role"] == "confab" else 0.0)

        sites = tuple(c["layer"] for c in cfg.get("capture_sites", []))
        write_capture(out, rows, residual, site if sites else None, blocks=sites or (20, 21, 22))
        return 0

    # steer / dose-calibrate ----------------------------------------------------------------------------
    def _steer(self, args):
        return self._generate(args, kind="steer")

    def _dose_calibrate(self, args):
        return self._generate(args, kind="dose")

    def _generate(self, args, *, kind):
        key = "steer" if kind == "steer" else "dose"
        if self.fail_next.get(key):
            self.fail_next[key] -= 1
            return 1
        cfg = yaml.safe_load(self._local(self._opt(args, "--mi-config")).read_text())
        rows = [json.loads(line) for line in self._local(cfg["surface"]["rows_path"]).read_text().splitlines() if line.strip()]
        out = self._local(cfg["execution"]["output_path"])
        marker = Path(self._opt(args, "--model")) / "marker"
        exported_cand = marker.read_text() if marker.exists() else None
        done = set()
        if out.exists():
            done = {json.loads(l)["row_key"] for l in out.read_text().splitlines() if l.strip()}
        patch_digest, cand = None, None
        wp = cfg["surface"].get("weight_patch")
        if wp:
            spec_path = self._local(wp["path"])
            assert hashlib.sha256(spec_path.read_bytes()).hexdigest() == wp["sha256"]
            spec = yaml.safe_load(spec_path.read_text())
            patch_digest = digest(wp["sha256"], spec["payload"]["sha256"])
            cand = spec_path.parent.name
        cand = cand or exported_cand
        if kind == "steer":
            arm = cfg["arms"][0]
            label, strength = arm["name"], arm["strength"]
        else:
            label = "clamp"
            strength = cfg["calibration"]["doses"][0]
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a") as fh:
            for r in rows:
                if r["row_key"] in done:
                    continue
                p = self._p(cfg, kind, cand, r, strength)
                refuse = u01(r["row_key"]) < p
                text = self._text(r, refuse)
                rec = {k: v for k, v in r.items()}
                rec.update({"row_key": r["row_key"], "strength": float(strength), "active": bool(strength) and (not cfg["arms"][0].get("flag_field") if kind == "steer" else True),
                            "answer_text": text, "prompt_len": 20, "n_new_tokens": max(1, len(text) // 4), "terminated_naturally": True,
                            "arm": label})
                rec["generated_token_ids"] = [int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)] * rec["n_new_tokens"]
                if kind == "dose":
                    rec.update({"readout": "u_d", "dose": float(strength)})
                if patch_digest:
                    rec["weight_patch_digest"] = patch_digest
                fh.write(json.dumps(rec) + "\n")
        return 0

    def _p(self, cfg, kind, cand, r, strength):
        role = r["role"]
        idx = 0 if role == "confab" else 1
        if cand in CAND_P:
            base = CAND_P[cand][idx]
        elif cand and cand.startswith("seed"):
            base = (0.06, 0.01)[idx]
        elif cand in ("zero_patch", "parity"):
            base = (0.05, 0.0)[idx]
        else:
            base = (0.05, 0.0)[idx]
        if kind == "steer":
            arm = cfg["arms"][0]
            if arm.get("flag_field") and r.get(arm["flag_field"]):
                return 0.85 if idx == 0 else 0.15
            return base
        if strength > 0:                                   # known clamp on confabs: removes refusal under the patch
            return base * (0.5 if cand else 0.9)
        return base + (0.20 if cand else 0.02)             # unknown clamp on knowns

    def _text(self, r, refuse):
        if refuse:
            return '{"answer": "I don\'t know the answer", "response_confidence": 0.9}'
        if r["role"] == "unknown_refused":
            return '{"answer": "I don\'t know the answer", "response_confidence": 0.9}' if u01(r["row_key"], "unk") < 0.95 else \
                '{"answer": "A guess", "response_confidence": 0.5}'
        if r["role"] == "confab" and u01(r["row_key"], "soft") < 0.10:
            return '{"answer": "It remains unclear what the exact answer would be.", "response_confidence": 0.3}'
        if r["role"] == "known_correct" and u01(r["row_key"], "correct") < 0.95:
            return '{"answer": "%s", "response_confidence": 0.9}' % r["aliases"][0]
        return '{"answer": "An invented plausible answer", "response_confidence": 0.8}'


def make_flow(root: Path):
    """A synthetic host project + stage context wired to the fake CLI."""
    import shutil as sh
    from types import SimpleNamespace

    from conftest import EXPERIMENT, REPO_SYNAPTIC, SLUG, _unit, make_inputs, write_direction
    from hs20_nwe import stages
    from hs20_nwe.config import Cell, Layout
    from hs20_nwe.engine import Engine

    cell = Cell.load(EXPERIMENT)
    root.mkdir(parents=True)
    sh.copy(REPO_SYNAPTIC, root / "synaptic.yaml")
    d = root / "experiments/common/directions/qwen35-4b-hs20"
    u_d = _unit(2)
    c_hat = _unit(1)
    c_hat = c_hat - (c_hat @ u_d) * u_d
    c_hat /= np.linalg.norm(c_hat)
    s, w = cell.cell["sensor"], cell.cell["writer"]
    sha_c = write_direction(d / "c_hat.json", c_hat, sigma=w["sigma_c"])
    sha_u = write_direction(d / "u_d.json", u_d)
    (d / "provenance.json").write_text(json.dumps({"directions": {"c_hat": {"source": "x/c.json", "sha256": sha_c},
                                                                  "u_d": {"source": "x/u.json", "sha256": sha_u}}}))
    build = {"layers": {"hs20": {"mu_d": s["mu_d"], "sigma_d": s["sigma_d"], "tau_frozen": s["tau"], "mu_c": w["mu_c"], "sigma_c": w["sigma_c"]}}}
    proj = SimpleNamespace(root=root, build=build, dir=d, c_hat=c_hat, u_d=u_d)
    make_inputs(proj, cell)
    (root / ".synaptic/artifacts" / SLUG / "base_model").mkdir(parents=True)
    ctx = stages.Ctx(root, cell, Layout(root, SLUG), gpu_ack=True)
    cli = FakeCLI(ctx.layout, root)
    ctx.engine_override = Engine(root, [], ctx.ledger, cli=cli)
    return SimpleNamespace(ctx=ctx, cli=cli, proj=proj, root=root)
