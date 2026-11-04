"""Real engine verbs on a tiny synthetic bf16 checkpoint. SKIPPED unless torch imports.

The CPU test venv deliberately has no torch, so this file is NOT exercised there.  Run it inside the reviewed
engine image (or any engine venv that has torch) to cross-check, against the real ``weights-inspect`` /
``weights-patch --validate`` verbs, what the rest of the suite only emulates:

    python -m pytest tests/test_engine_cli_with_torch.py

It checks that (1) inspect dots equal NumPy dots, (2) the generated add_rank_one spec validates, and (3) the engine's
realized delta/entries agree with this suite's bf16 emulation.  Synthetic data only.
"""

import hashlib
import json
import shutil

import numpy as np
import pytest
import yaml

torch = pytest.importorskip("torch")
from safetensors.torch import save_file  # noqa: E402

from bf16 import realized_delta  # noqa: E402
from conftest import EXPERIMENT, SLUG  # noqa: E402
from hs20_nwe import weights  # noqa: E402
from hs20_nwe.config import Cell, Layout  # noqa: E402
from hs20_nwe.engine import Engine  # noqa: E402

OUT, IN, COLS = 64, 48, 5
NAME = "model.language_model.layers.20.mlp.down_proj.weight"


@pytest.fixture
def tiny(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    shutil.copy(EXPERIMENT.parents[1] / "synaptic.yaml", root / "synaptic.yaml")
    exp = root / "experiments" / SLUG
    shutil.copytree(EXPERIMENT / "hs20_nwe", exp / "hs20_nwe", ignore=shutil.ignore_patterns("__pycache__"))
    layout = Layout(root, SLUG)
    ckpt = layout.local("base_model", shared=True)
    ckpt.mkdir(parents=True)
    w = (torch.randn(OUT, IN, generator=torch.Generator().manual_seed(3)) * 0.05).to(torch.bfloat16)
    save_file({NAME: w}, str(ckpt / "model.safetensors"))
    return root, exp, layout, ckpt, w


def test_inspect_validate_and_realized_delta_match_numpy(tiny):
    root, exp, layout, ckpt, w = tiny
    cell = Cell.load(EXPERIMENT)
    eng = Engine(root, [exp])
    c_hat = np.random.default_rng(0).standard_normal(OUT)
    c_hat /= np.linalg.norm(c_hat)
    d = layout.local("dir", shared=True)
    d.mkdir(parents=True)
    (d / "c.json").write_text(json.dumps({"schema_version": "mechinterp-direction/v1", "vector": c_hat.tolist()}))
    sha_c = hashlib.sha256((d / "c.json").read_bytes()).hexdigest()
    req = {"schema_version": "mechinterp-weights-inspect/v1", "checkpoint": layout.ref("base_model", shared=True),
           "hash_files": True, "hash_tensors": True, "tensors": ["*layers.20.mlp.down_proj.weight"],
           "max_output_values": IN, "projections": [{"id": "col_dots_b20", "tensor": NAME, "axis": "cols", "kind": "dot",
                                                     "vector": {"direction_json": {"path": layout.ref("dir/c.json", shared=True), "sha256": sha_c}}}]}
    (layout.local("inspect", shared=True)).mkdir(parents=True)
    (layout.local("inspect/r.yaml", shared=True)).write_text(yaml.safe_dump(req))
    rc, doc = eng.run_json(["weights-inspect", "--weights-config", layout.ref("inspect/r.yaml", shared=True), "--json"],
                           layout.local("inspect/r.out.json", shared=True))
    assert rc == 0
    report = weights.unwrap(doc)
    target = report["tensors"][0]
    wnp = w.to(torch.float32).numpy().astype(np.float64)
    dots = np.asarray(report["projections"][0]["values"])
    assert np.allclose(dots, c_hat @ wnp, atol=1e-9)
    binding = weights.listing_binding(report)
    cols = [4, 1, 30, 7, 12]
    payload_path = layout.local("patches/t/payload.safetensors", shared=True)
    sha = weights.write_payload(payload_path, c_hat, dots[cols])
    spec = weights.make_spec(cell, layout, dir_rel="patches/t", tensor=target, binding=binding, scale=16.0, columns=cols,
                             payload_sha=sha, description="tiny")
    spec["budget"]["max_relative_frobenius"] = 1.0
    spec["budget"]["max_modified_entries"] = OUT * IN
    spec_path = layout.local("patches/t/spec.yaml", shared=True)
    spec_path.write_text(yaml.safe_dump(spec))
    rc, doc = eng.run_json(["weights-patch", "--weights-config", layout.ref("patches/t/spec.yaml", shared=True), "--validate", "--json"],
                           layout.local("validation/t.out.json", shared=True))
    assert rc == 0
    got = weights.parse_validation(cell, doc)
    want_delta, want_entries = realized_delta(w.to(torch.float32).numpy()[:, cols], c_hat, dots[cols], 16.0)
    assert got.entries_changed == want_entries
    assert got.delta_frobenius == pytest.approx(want_delta, rel=1e-6)
