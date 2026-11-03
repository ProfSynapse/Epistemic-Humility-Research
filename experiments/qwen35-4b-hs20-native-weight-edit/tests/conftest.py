"""Shared CPU fixtures: a synthetic host project, synthetic pinned inputs, and a fake engine CLI.

Nothing here touches private data, a GPU, torch, or the network.  The fake CLI
replaces ``EngineCLI.run`` underneath the real ``Engine`` wrapper, so budget,
fd-capture and stage logic are exercised for real.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT))

from hs20_nwe.config import Cell  # noqa: E402
from hs20_nwe.util import sha256_bytes  # noqa: E402

REPO_SYNAPTIC = EXPERIMENT.parents[1] / "synaptic.yaml"
SLUG = "qwen35-4b-hs20-native-weight-edit"
DIM, INTER = 2560, 9216


@pytest.fixture(scope="session")
def cell() -> Cell:
    return Cell.load(EXPERIMENT)


def _unit(seed: int) -> np.ndarray:
    v = np.random.default_rng(seed).standard_normal(DIM)
    return v / np.linalg.norm(v)


def write_direction(path: Path, vec: np.ndarray, *, layer: int = 19, sigma: float = 1.0) -> str:
    doc = {"schema_version": "mechinterp-direction/v1", "layer": layer, "hidden_dim": DIM, "normalized": True,
           "vector": [float(x) for x in vec], "raw_norm": 1.0, "intercept": 0.0, "sigma": sigma}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def project(tmp_path, cell):
    """A host project with a pinned manifest, promoted directions and committed pin manifests."""
    root = tmp_path / "proj"
    root.mkdir()
    shutil.copy(REPO_SYNAPTIC, root / "synaptic.yaml")
    d = root / "experiments/common/directions/qwen35-4b-hs20"
    c_hat, u_d = _unit(1), _unit(2)
    # make c_hat orthogonal to u_d (as promoted)
    c_hat = c_hat - (c_hat @ u_d) * u_d
    c_hat /= np.linalg.norm(c_hat)
    sha_c = write_direction(d / "c_hat.json", c_hat, sigma=cell.cell["writer"]["sigma_c"])
    sha_u = write_direction(d / "u_d.json", u_d, sigma=1.0)
    s, w = cell.cell["sensor"], cell.cell["writer"]
    (d / "provenance.json").write_text(json.dumps({
        "directions": {"c_hat": {"source": "x/c_hat.json", "sha256": sha_c}, "u_d": {"source": "x/u_d.json", "sha256": sha_u}}}))
    build = {"layers": {"hs20": {"mu_d": s["mu_d"], "sigma_d": s["sigma_d"], "tau_frozen": s["tau"],
                                 "mu_c": w["mu_c"], "sigma_c": w["sigma_c"]}}}
    return SimpleNamespace(root=root, build=build, dir=d, c_hat=c_hat, u_d=u_d)


def make_inputs(proj, cell: Cell, *, mutate=None, repin: bool = False) -> Path:
    """Synthetic pinned inputs with the registered counts; returns the inputs dir."""
    root, build, d = proj.root, proj.build, proj.dir
    sp = cell.cell["splits"]
    n_conf = sp["fit_localization"]["confab"] + sp["fit_selection"]["confab"]
    n_known = sp["fit_localization"]["known_correct"] + sp["fit_selection"]["known_correct"]
    n_unk = sp["fit_localization"]["unknown_refused"]
    n_hconf, n_hknown = 1332, sp["heldout"]["known_correct"]
    junk = {"fire": True, "z_d": 0.1, "tau": 0.0, "score_neg_z_d": 1.0, "baseline_text": "OLD", "baseline_token_ids": [1],
            "baseline_clean": True, "baseline_finish_reason": "stop", "baseline_old_grade": {}, "baseline_terminated_naturally": True,
            "role_candidate": "x"}

    def row(i, role, split, prefix):
        return {"row_key": f"{prefix}:{i}", "role": role, "split": split, "question": f"question {prefix} {i}",
                "aliases": [f"alias{i}"] if role == "known_correct_answered" else [], "source": "kuq_unknowns_all",
                "category_canon": "c", **junk}

    fit_conf = [row(i, "confab", "fit", "kc") for i in range(n_conf)]
    fit_known = [row(i, "known_correct_answered", "fit", "kk") for i in range(n_known)]
    unk = [row(i, "unknown_refused", "fit_only", "ku") for i in range(n_unk)]
    h_conf = [row(i, "confab", "held_out", "hc") for i in range(n_hconf)]
    h_known = [row(i, "known_correct_answered", "held_out", "hk") for i in range(n_hknown)]
    files = {"fit_rows_for_dose.jsonl": fit_conf + fit_known, "heldout_rows_for_steer.jsonl": h_conf + h_known,
             "fit_rows_for_anchor.jsonl": [dict(r) for r in fit_conf + fit_known] + unk}

    clean = {k: [dict(r) for r in v] for k, v in files.items()}
    files = {k: [dict(r) for r in v] for k, v in files.items()}
    if mutate:
        mutate(files)
    inputs = root / ".synaptic/artifacts" / SLUG / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, rows in files.items():
        data = "".join(json.dumps(r) + "\n" for r in rows).encode()
        (inputs / name).write_bytes(data)
        hashes[name] = sha256_bytes(data)
    # pins come from the *unmutated* generation so a mutated file breaks the pin
    if repin:
        clean = files
    pins = {n: sha256_bytes("".join(json.dumps(r) + "\n" for r in rows).encode()) for n, rows in clean.items()}
    ro = lambda rs: [{"row_key": r["row_key"], "role": r["role"], "split": r["split"]} for r in rs]  # noqa: E731
    reused = {"reused_from": {"source_file_sha256": {"fit_rows_for_dose.jsonl": pins["fit_rows_for_dose.jsonl"],
                                                     "heldout_rows_for_steer.jsonl": pins["heldout_rows_for_steer.jsonl"]}},
              "rows": {"confab_fit": ro(fit_conf), "known_correct_answered_fit": ro(fit_known),
                       "unknown_refused_fit_only": ro(unk), "confab_held_out": ro(h_conf),
                       "known_correct_answered_held_out": ro(h_known)},
              "counts": {}}
    m = root / "experiments/qwen35-4b-midband-doubt-snap/analysis-committed"
    m.mkdir(parents=True, exist_ok=True)
    (m / "reused_rows_manifest.json").write_text(json.dumps(reused))
    build = dict(build)
    build["fit_rows_sha256"] = pins["fit_rows_for_anchor.jsonl"]
    (d / "build_manifest.json").write_text(json.dumps(build))
    return inputs


@pytest.fixture(autouse=True)
def fake_engine_binding_boundary(request, monkeypatch):
    # Fake engine tests cover orchestration; binding is tested separately.
    if request.module.__name__ in {"test_end_to_end_fake_engine", "test_no_eligible_and_cli", "test_selection_budget"}:
        from hs20_nwe import integrity, stages
        monkeypatch.setattr(stages, "require_run_admission", lambda *a: None)
        monkeypatch.setattr(integrity, "verify", lambda *a, **k: {"passed": True})
        monkeypatch.setattr(integrity, "report", lambda *a, **k: {"passed": True})


def git_commit_public(layout, name):
    import subprocess
    from hs20_nwe.commitments import public_path
    root = layout.project_root
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    if not (root / ".git").exists():
        git("init", "-q")
        git("config", "user.email", "synthetic@example.invalid")
        git("config", "user.name", "Synthetic CPU Fixture")
    git("add", "--", str(public_path(layout, name).relative_to(root)))
    git("commit", "-q", "--allow-empty", "-m", "Synthetic public commitment")


@pytest.fixture(autouse=True)
def lead_git_commits_in_adjudication_fixtures(request, monkeypatch):
    if request.module.__name__ not in {"test_adjudication", "test_end_to_end_fake_engine"}:
        return
    from hs20_nwe import adjudication as A
    for method, name in (("commit_pool", "adjudication_pool_manifest.json"),
                         ("commit_hash", "adjudication_graded_manifest.json")):
        original = getattr(A, method)
        def wrapper(layout, *args, _original=original, _name=name, **kwargs):
            result = _original(layout, *args, **kwargs)
            git_commit_public(layout, _name)
            return result
        monkeypatch.setattr(A, method, wrapper)


def synthetic_drill(cell, layout):
    from hs20_nwe.util import write_jsonl, sha256_file
    drills = []
    for module in ("extract", "generation", "localize"):
        rows = [{"row_key": f"synthetic-{module}-{i}"} for i in range(8)]
        refs = [layout.ref(f"tests/{module}-{suffix}.jsonl") for suffix in ("before", "after")]
        for ref, subset in zip(refs, (rows[:4], rows)):
            write_jsonl(layout.to_local(ref), subset)
        drills.append({"module": module, "signal": 9, "killed_pid": 123,
                       "resume_exit_code": 0, "expected_rows": 8,
                       "before_journal": refs[0], "after_journal": refs[1],
                       "before_sha256": sha256_file(layout.to_local(refs[0])),
                       "after_sha256": sha256_file(layout.to_local(refs[1]))})
    return {"schema_version": "hs20-nwe-kill-resume/v1", **cell.stamp(), "drills": drills}
