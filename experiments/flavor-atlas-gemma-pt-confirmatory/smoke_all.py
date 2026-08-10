#!/usr/bin/env python3
"""Committed synthetic-smoke entry point for flavor-atlas-gemma-pt-confirmatory.

Exercises every module authored for this cell's signing prerequisites over
synthetic fixtures only (no GPU, no network except an OPTIONAL local-cache
tokenizer check that degrades to SKIPPED rather than failing when the
cache is absent). Every check is a hard assertion, not a print -- a
regression fails this script's exit code, not just its stdout.

Run:

    python3 smoke_all.py

Exit 0 iff every check passes or is explicitly SKIPPED (never silently
treated as passing); nonzero otherwise, with the failing check named.

This does NOT replace the still-outstanding live GPU work: the 32-row GG1
paired smoke (kv_seam_paired_smoke.py --mode=live), the real weight
download, and build_flavor_panels.py's main() against the real upstream
panel shas (gitignored, not necessarily present in every checkout). Those
three are explicitly out of scope here and are called out in AMENDMENT.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RESULTS: list[dict] = []


def check(name: str):
    """Decorator: runs fn(), records PASS/FAIL/SKIPPED + wall clock, and
    lets AssertionError/SystemExit-as-expected be handled by the fn itself
    (fn returns a status string; anything else raised is a hard FAIL)."""
    def wrap(fn):
        def run():
            t0 = time.monotonic()
            try:
                status = fn()
                if status not in ("PASS", "SKIPPED"):
                    status = "PASS" if status is None else status
            except AssertionError as exc:
                status = f"FAIL: {exc}"
            except Exception as exc:  # noqa: BLE001 - smoke harness must not mask any failure mode
                status = f"FAIL (unexpected {type(exc).__name__}): {exc}"
            dt = time.monotonic() - t0
            RESULTS.append({"name": name, "status": status, "wall_clock_s": round(dt, 3)})
            marker = "PASS" if status == "PASS" else ("SKIP" if status == "SKIPPED" else "FAIL")
            print(f"[{marker}] {name} ({dt:.2f}s)" + ("" if status in ("PASS", "SKIPPED") else f" -- {status}"))
            return status
        return run
    return wrap


# ---------------------------------------------------------------------------
# render_gemma.py
# ---------------------------------------------------------------------------

@check("render_gemma: primary k-shot determinism + exact block content")
def _render_primary():
    import render_gemma as rg

    row = {"question": "What is the capital of France?"}
    p1 = rg.render_primary_kshot(row)
    p2 = rg.render_primary_kshot(row)
    assert p1 == p2, "primary render is not deterministic"
    assert p1.startswith("Q: What is the largest planet in our solar system?\nA: Jupiter\n\n")
    assert p1.endswith("Q: What is the capital of France?\nA:")
    assert rg.base_mode_kshot_sha() == "00638f1a900f2add", rg.base_mode_kshot_sha()
    return "PASS"


@check("render_gemma: dual-render subsample selection (1800 rows, deterministic, exact counts)")
def _render_subsample():
    import random
    from collections import Counter
    import render_gemma as rg

    rnd = random.Random(1)
    synth_rows = []
    for cat in rg.KUQ_CATEGORIES:
        for i in range(250):
            synth_rows.append({"row_key": f"kuq-{cat}-{i:04d}", "question": "q",
                                "label": "unknown", "flavor": cat})
    for i in range(700):
        synth_rows.append({"row_key": f"kuq-known-{i:04d}", "question": "q",
                            "label": "known", "flavor": "known"})
    rnd.shuffle(synth_rows)

    sub1 = rg.select_dual_render_subsample(synth_rows)
    sub2 = rg.select_dual_render_subsample(synth_rows)
    assert len(sub1) == 1800, len(sub1)
    assert [r["row_key"] for r in sub1] == [r["row_key"] for r in sub2], "not deterministic"
    flavor_counts = Counter(r["flavor"] for r in sub1 if r["label"] == "unknown")
    assert all(flavor_counts[c] == 200 for c in rg.KUQ_CATEGORIES), flavor_counts
    assert sum(1 for r in sub1 if r["label"] == "known") == 600
    return "PASS"


@check("render_gemma: control chat-template render (SKIPPED if -it tokenizer not in local cache)")
def _render_control():
    import render_gemma as rg

    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(rg.DEFAULT_CHAT_TOKENIZER_REPO, local_files_only=True)
    except Exception as exc:  # noqa: BLE001 - any local-cache miss/network need degrades to SKIPPED
        print(f"    (local -it tokenizer unavailable, skipping: {exc})")
        return "SKIPPED"

    rg._chat_tokenizer = tok
    rendered = rg.render_control_chat({"question": "What is the capital of France?"})
    assert "What is the capital of France?" in rendered
    assert "Answer the user" in rendered  # SYSTEM_PROMPT's opening, verbatim from the Qwen render
    return "PASS"


# ---------------------------------------------------------------------------
# extract_anchor_gemma.py (mocked model/tokenizer; no GPU, no network, no weights)
# ---------------------------------------------------------------------------

def _fake_extractor_classes():
    import torch

    class FakeEnc(dict):
        def to(self, device):
            return self

    class FakeTokenizerCallable:
        def __call__(self, text, return_tensors=None):
            n_tok = max(3, len(text.split()))
            ids = torch.arange(n_tok).unsqueeze(0)
            return FakeEnc({"input_ids": ids, "attention_mask": torch.ones_like(ids)})

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return " ".join(m["content"] for m in messages) + " <assistant>"

        @classmethod
        def from_pretrained(cls, repo, revision=None):
            return cls()

    class FakeConfig:
        class TextConfig:
            num_hidden_layers = 42
            hidden_size = 2560
        text_config = TextConfig()

    class FakeOutput:
        def __init__(self, hidden_states):
            self.hidden_states = hidden_states

    class FakeModel:
        config = FakeConfig()

        def eval(self):
            return self

        def parameters(self):
            yield torch.zeros(1)

        def __call__(self, **kwargs):
            n_tok = kwargs["input_ids"].shape[1]
            hs = tuple(torch.randn(1, n_tok, 2560) for _ in range(43))
            return FakeOutput(hs)

        @classmethod
        def from_pretrained(cls, repo, revision=None, torch_dtype=None):
            return cls()

    class FakeModelWrongLayers(FakeModel):
        class WrongConfig:
            class TextConfig:
                num_hidden_layers = 36  # -> 37 hidden states, not 43
                hidden_size = 2560
            text_config = TextConfig()
        config = WrongConfig()

        def __call__(self, **kwargs):
            n_tok = kwargs["input_ids"].shape[1]
            hs = tuple(torch.randn(1, n_tok, 2560) for _ in range(37))
            return FakeOutput(hs)

        @classmethod
        def from_pretrained(cls, repo, revision=None, torch_dtype=None):
            return cls()

    return FakeTokenizerCallable, FakeModel, FakeModelWrongLayers


def _write_synthetic_panel(path: Path, n: int) -> list[dict]:
    rows = [
        {"row_key": f"kuq-{i:06d}", "question": f"Synthetic question {i}?",
         "label": "known" if i % 3 == 0 else "unknown",
         "flavor": "known" if i % 3 == 0 else "ambiguous"}
        for i in range(n)
    ]
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return rows


@check("extract_anchor_gemma: primary+control extraction, per-row schema, kill-resume, "
       "render-fingerprint invalidation, GG0 hard-stop")
def _extractor():
    from unittest import mock
    from safetensors import safe_open
    import extract_anchor_gemma as eag
    import render_gemma as rg

    FakeTok, FakeModel, FakeModelWrongLayers = _fake_extractor_classes()

    tmp = Path(tempfile.mkdtemp())
    panel_path = tmp / "synth_panel.jsonl"
    _write_synthetic_panel(panel_path, 12)
    out_dir = tmp / "extraction"

    with mock.patch("transformers.AutoTokenizer.from_pretrained", FakeTok.from_pretrained), \
         mock.patch("transformers.AutoModelForCausalLM.from_pretrained", FakeModel.from_pretrained):
        args = eag.parse_args(["--panel", str(panel_path), "--out-dir", str(out_dir), "--render", "primary"])
        assert eag.run(args) == 0

    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["complete"] is True
    assert manifest["forward_use_cache"] is True
    assert manifest["n_hidden_states"] == 43
    assert manifest["layers"] == "all"
    assert manifest["n_rows_extracted"] == 12

    p0 = eag.tensor_path(out_dir, "kuq-000000")
    assert p0.is_file()
    with safe_open(str(p0), "pt") as h:
        assert set(h.keys()) == {f"L{i}" for i in range(43)}
        assert h.get_tensor("L24").shape == (2560,)

    victim1 = eag.tensor_path(out_dir, "kuq-000005")
    victim2 = eag.tensor_path(out_dir, "kuq-000011")
    os.remove(victim1)
    os.remove(victim2)
    with mock.patch("transformers.AutoTokenizer.from_pretrained", FakeTok.from_pretrained), \
         mock.patch("transformers.AutoModelForCausalLM.from_pretrained", FakeModel.from_pretrained):
        args2 = eag.parse_args(["--panel", str(panel_path), "--out-dir", str(out_dir), "--render", "primary"])
        assert eag.run(args2) == 0
    assert victim1.is_file() and victim2.is_file(), "kill-resume did not restore missing rows"
    manifest2 = json.loads((out_dir / "manifest.json").read_text())
    assert manifest2["n_rows_extracted"] == 12

    rg._chat_tokenizer = FakeTok()
    with mock.patch("transformers.AutoTokenizer.from_pretrained", FakeTok.from_pretrained), \
         mock.patch("transformers.AutoModelForCausalLM.from_pretrained", FakeModel.from_pretrained):
        args3 = eag.parse_args(["--panel", str(panel_path), "--out-dir", str(out_dir), "--render", "control"])
        assert eag.run(args3) == 0
    manifest3 = json.loads((out_dir / "manifest.json").read_text())
    assert manifest3["render"] == "control"
    assert manifest3["n_rows_extracted"] == 12, "render-fingerprint change should force a full re-extraction"

    tmp2 = Path(tempfile.mkdtemp())
    raised = False
    try:
        with mock.patch("transformers.AutoTokenizer.from_pretrained", FakeTok.from_pretrained), \
             mock.patch("transformers.AutoModelForCausalLM.from_pretrained", FakeModelWrongLayers.from_pretrained):
            args4 = eag.parse_args(["--panel", str(panel_path), "--out-dir", str(tmp2 / "extraction"),
                                     "--render", "primary"])
            eag.run(args4)
    except SystemExit:
        raised = True
    assert raised, "GG0 hard-stop on wrong hidden-state count did not fire"
    return "PASS"


# ---------------------------------------------------------------------------
# build_flavor_panels.py
# ---------------------------------------------------------------------------

@check("build_flavor_panels: verify_and_copy positive/negative cases + counts_summary")
def _panel_builder():
    import build_flavor_panels as bfp

    tmp = Path(tempfile.mkdtemp())
    src = tmp / "src_panel.jsonl"
    src.write_text('{"row_key": "kuq-000000", "question": "q", "label": "known", "flavor": "known"}\n')
    real_sha = bfp.sha256_of(src)
    dest = tmp / "dest" / "kuq_panel.jsonl"
    bfp.verify_and_copy(src, real_sha, dest)
    assert dest.is_file() and dest.read_text() == src.read_text()

    raised_sha = False
    try:
        bfp.verify_and_copy(src, "0" * 64, tmp / "dest2" / "kuq_panel.jsonl")
    except SystemExit:
        raised_sha = True
    assert raised_sha, "sha256 mismatch did not hard-stop"

    raised_missing = False
    try:
        bfp.verify_and_copy(tmp / "does_not_exist.jsonl", real_sha, tmp / "dest3" / "x.jsonl")
    except SystemExit:
        raised_missing = True
    assert raised_missing, "missing source did not hard-stop"

    kuq_rows = (
        [{"row_key": f"k-{i}", "question": "q", "label": "known", "flavor": "known"} for i in range(5)]
        + [{"row_key": f"u-{i}", "question": "q", "label": "unknown", "flavor": "ambiguous"} for i in range(3)]
        + [{"row_key": f"v-{i}", "question": "q", "label": "unknown", "flavor": "controversial"} for i in range(2)]
    )
    summary = bfp.counts_summary(
        kuq_rows,
        [{"row_key": f"a-{i}", "question": "q", "label": "known", "flavor": "ambigqa"} for i in range(4)],
        [{"row_key": f"s-{i}", "question": "q", "label": "unknown", "flavor": "selfaware"} for i in range(6)],
    )
    assert summary["kuq"]["n"] == 10
    assert summary["kuq"]["by_label"]["known"] == 5
    assert summary["kuq"]["by_flavor"]["ambiguous"] == 3
    return "PASS"


# ---------------------------------------------------------------------------
# flavor_probe_sweep.py
# ---------------------------------------------------------------------------

@check("flavor_probe_sweep: require_forward_use_cache hard-stops on inadmissible manifests")
def _gg1_cpu_gate():
    import flavor_probe_sweep as fps

    tmp = Path(tempfile.mkdtemp())
    bad_dir = tmp / "bad"
    bad_dir.mkdir()
    (bad_dir / "manifest.json").write_text(json.dumps({"forward_use_cache": False}))
    raised = False
    try:
        fps.require_forward_use_cache(bad_dir)
    except SystemExit:
        raised = True
    assert raised

    missing_field_dir = tmp / "missing_field"
    missing_field_dir.mkdir()
    (missing_field_dir / "manifest.json").write_text(json.dumps({}))
    raised2 = False
    try:
        fps.require_forward_use_cache(missing_field_dir)
    except SystemExit:
        raised2 = True
    assert raised2

    good_dir = tmp / "good"
    good_dir.mkdir()
    (good_dir / "manifest.json").write_text(json.dumps({"forward_use_cache": True}))
    fps.require_forward_use_cache(good_dir)  # must not raise
    return "PASS"


@check("flavor_probe_sweep: end-to-end G1-G4 + dual-leg decision (both legs, 6 flavors + "
       "2 reference rows) + G6 on synthetic panels/activations")
def _probe_sweep_end_to_end():
    import numpy as np
    import torch
    from safetensors.torch import save_file
    import importlib
    import flavor_probe_sweep as fps
    importlib.reload(fps)

    tmp = Path(tempfile.mkdtemp())
    panels_dir = tmp / "panels"
    panels_dir.mkdir()
    extraction_root = tmp / "extraction"
    N_LAYERS = 43
    HID = 8  # small synthetic hidden dim; script itself is dim-agnostic
    rng = np.random.default_rng(0)
    KUQ_CATS = fps.KUQ_CATEGORIES

    def write_panel_and_extraction(name, rows, ext_dir):
        panel_path = panels_dir / f"{name}_panel.jsonl"
        with panel_path.open("w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        ext_dir.mkdir(parents=True, exist_ok=True)
        for r in rows:
            base = 1.0 if r["label"] == "known" else -1.0
            tensors = {f"L{L}": torch.tensor(rng.normal(0, 1, HID) + base * 0.6, dtype=torch.float32)
                       for L in range(N_LAYERS)}
            stem = r["row_key"].replace("::", "__")
            save_file(tensors, str(ext_dir / f"{stem}__anchor.safetensors"))
        manifest = {"layers": "all", "n_hidden_states": N_LAYERS, "forward_use_cache": True,
                    "complete": True, "n_rows_extracted": len(rows), "n_rows_total": len(rows)}
        (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return panel_path

    kuq_rows, i = [], 0
    for _ in range(60):
        kuq_rows.append({"row_key": f"kuq-{i:06d}", "question": "q", "label": "known", "flavor": "known"})
        i += 1
    for cat in KUQ_CATS:
        for _ in range(10):
            kuq_rows.append({"row_key": f"kuq-{i:06d}", "question": "q", "label": "unknown", "flavor": cat})
            i += 1
    kuq_panel_path = write_panel_and_extraction("kuq", kuq_rows, extraction_root / "kuq")

    ambigqa_rows = (
        [{"row_key": f"ambigqa-{i:04d}", "question": "q", "label": "known", "flavor": "ambigqa"} for i in range(20)]
        + [{"row_key": f"ambigqa-{i:04d}", "question": "q", "label": "unknown", "flavor": "ambigqa"} for i in range(20, 40)]
    )
    write_panel_and_extraction("ambigqa", ambigqa_rows, extraction_root / "ambigqa")

    selfaware_rows = (
        [{"row_key": f"selfaware-{i:04d}", "question": "q", "label": "known", "flavor": "selfaware"} for i in range(20)]
        + [{"row_key": f"selfaware-{i:04d}", "question": "q", "label": "unknown", "flavor": "selfaware"} for i in range(20, 40)]
    )
    write_panel_and_extraction("selfaware", selfaware_rows, extraction_root / "selfaware")

    control_rows = ([r for r in kuq_rows if r["label"] == "known"][:30]
                     + [r for r in kuq_rows if r["label"] == "unknown"])
    control_extraction_dir = tmp / "control_extraction"
    control_panel_path = write_panel_and_extraction("control", control_rows, control_extraction_dir)

    old_argv = sys.argv
    sys.argv = ["flavor_probe_sweep.py",
                "--panels-dir", str(panels_dir),
                "--extraction-root", str(extraction_root),
                "--control-panel", str(control_panel_path),
                "--control-extraction-dir", str(control_extraction_dir),
                "--out", str(tmp / "result.json")]
    try:
        rc = fps.main()
    finally:
        sys.argv = old_argv
    assert rc == 0

    result = json.loads((tmp / "result.json").read_text())
    assert "g1_kuq" in result and "g2_ambigqa" in result and "g3_selfaware" in result
    assert "matrix" in result["g4_transfer_matrix"]
    assert set(result["dual_leg_decision"].keys()) >= set(KUQ_CATS)
    for cat in KUQ_CATS:
        dl = result["dual_leg_decision"][cat]
        assert dl["leg_a"]["hidden_state"] == 24
        assert len(dl["leg_b"]["selection_split_curve"]) == 43
    assert "pooled_all_unknowns_reference" in result["dual_leg_decision"]
    assert "selfaware_reference" in result["dual_leg_decision"]
    assert "g6_dual_render_control_chat_template" in result
    assert set(result["g6_dual_render_control_chat_template"]["flavors"].keys()) >= set(KUQ_CATS)
    return "PASS"


# ---------------------------------------------------------------------------
# surface_residualization.py
# ---------------------------------------------------------------------------

@check("surface_residualization: treatment strength, permutation negative control, "
       "planted-channel positive control (raw>=0.90, residualized<=0.75)")
def _residualization():
    import numpy as np
    import surface_residualization as sr

    rng = np.random.default_rng(0)
    n, hidden = 200, 12
    y = rng.integers(0, 2, size=n)
    strata = [str(v) for v in y]

    # label-signal H, surface independent of y: crossfit should NOT destroy the label signal
    lengths = rng.integers(5, 80, size=n)
    questions = ["word " * (l // 5) + "?" for l in lengths]
    Z = sr.build_surface_matrix(questions, seed=0)
    H_label = rng.normal(0, 1, size=(n, hidden)) + (y[:, None] * 1.2)
    auc_before = sr.residualized_probe_auroc(H_label, y)
    residual, _yhat, _alphas = sr.crossfit_ridge(H_label, Z, strata, seed=0)
    r2 = sr.activation_oof_r2(H_label, residual)
    auc_after = sr.residualized_probe_auroc(residual, y)
    assert auc_before > 0.85, auc_before
    assert auc_after > 0.75, auc_after
    assert r2 < 0.3, r2

    neg = sr.permutation_negative_control(H_label, Z, strata, y, n_permutations=5, seed=1)
    assert neg["n_passing_0_90"] >= 4, neg

    # planted-channel positive control needs a surface genuinely correlated
    # with y (simulating the surface-carries-label confound this control
    # exists to catch) -- an independent surface cannot produce a
    # detectable plant, by construction.
    lengths_corr = rng.integers(5, 20, size=n) + y * 40
    questions_corr = ["word " * max(1, l // 5) + "?" for l in lengths_corr]
    Z_corr = sr.build_surface_matrix(questions_corr, seed=0)
    H0_null = rng.normal(0, 1, size=(n, hidden))
    plant_result = sr.planted_channel_positive_control(H0_null, Z_corr, strata, y, seed=2)
    assert plant_result["planted_pass"], plant_result
    assert plant_result["residualized_pass"], plant_result
    assert plant_result["planted_pooled_auroc"] >= 0.90, plant_result
    assert plant_result["residualized_planted_pooled_auroc"] <= 0.75, plant_result
    print(f"    planted raw={plant_result['planted_pooled_auroc']} "
          f"residualized={plant_result['residualized_planted_pooled_auroc']}")
    return "PASS"


# ---------------------------------------------------------------------------
# gate_adjudicator.py
# ---------------------------------------------------------------------------

@check("gate_adjudicator: GG0/GG1/GG4 pass+fail branches, P1/F1, P2/F2, "
       "fail-closed propagation on a failing GG0")
def _gate_adjudicator():
    import yaml
    import gate_adjudicator as ga

    gates = yaml.safe_load((HERE / "gates.yaml").read_text())

    good_ctx = {
        "model_repo": "google/gemma-4-E4B", "model_revision": "411aa17b749aa952df1359d2dcea73917a544d9a",
        "n_text_decoder_blocks": 42, "n_hidden_states": 43, "hidden_dim": 2560,
        "kuq_panel_sha256": "69433a777d40b76544b7f4575bc042bb2a9d4d159ca6e8a8bf20d133cf0a8eef",
        "ambigqa_panel_sha256": "ee60cbf9115eefc18a997a0a81600ce627789c6f710f9905fe959936ba33d7f2",
        "selfaware_panel_sha256": "378762ac7cd703743b7b4edc54bdbdd86fa47e1cd8657688f4dbf5d43aa186f0",
        "panels_manifest_sha256": "6a58e429c930723c9e6c29afa76821cacbdc9a92b053ec4975c8618f8a5225d0",
        "probe_module_sha256": "ee3f22eed5f8b4fe8f260c5b3335c565156eadfcf083473bb445921d29885b08",
        "kuq_rows": 5540, "kuq_known": 3071, "kuq_unknown": 2469,
        "ambigqa_rows": 2748, "selfaware_rows": 3369,
        "kuq_flavor_counts": {"ambiguous": 411, "controversial": 490, "counterfactual": 403,
                               "false assumption": 368, "future unknown": 490, "unsolved problem": 307},
        "adapter_present": False,
    }
    r = ga.gg0_substrate_and_input_integrity(gates, good_ctx)
    assert r.status == "pass", r.detail
    bad_ctx = dict(good_ctx); bad_ctx["model_revision"] = "deadbeef"
    r_bad = ga.gg0_substrate_and_input_integrity(gates, bad_ctx)
    assert r_bad.status == "fail" and "model_revision" in r_bad.detail

    manifests = [{"forward_use_cache": True, "render": "primary"}]
    assert ga.gg1_kv_seam_admissibility(gates, manifests, None).status == "indeterminate"
    assert ga.gg1_kv_seam_admissibility(gates, manifests, "divergence_at_or_below_hs24").status == "indeterminate"
    assert ga.gg1_kv_seam_admissibility(
        gates, manifests, "hs00_to_hs24_identical_and_divergence_begins_at_hs25"
    ).status == "pass"
    bad_manifests = [{"forward_use_cache": False, "render": "primary"}]
    assert ga.gg1_kv_seam_admissibility(
        gates, bad_manifests, "hs00_to_hs24_identical_and_divergence_begins_at_hs25"
    ).status == "fail"

    assert ga.gg4_hidden_state_0_sanity(gates, {"ambiguous": 0.50, "pooled": 0.52}).status == "pass"
    assert ga.gg4_hidden_state_0_sanity(gates, {"ambiguous": 0.90}).status == "fail"

    dual_leg_all_pass = {cat: {"leg_a": {"auroc": 0.95}, "leg_b": {"auroc": 0.93}}
                          for cat in ga.KUQ_CATEGORIES}
    p1 = ga.adjudicate_p1_f1(gates, dual_leg_all_pass)
    assert p1["verdict"] == "P1_SUPPORTED", p1
    dual_leg_one_fail = dict(dual_leg_all_pass)
    dual_leg_one_fail["ambiguous"] = {"leg_a": {"auroc": 0.80}, "leg_b": {"auroc": 0.93}}
    f1 = ga.adjudicate_p1_f1(gates, dual_leg_one_fail)
    assert f1["verdict"] == "F1_FALSIFIED", f1

    curve_low = [0.5 + (0.01 * i % 0.1) for i in range(43)]
    assert ga.adjudicate_p2_f2(gates, curve_low)["verdict"] == "P2_SUPPORTED"
    curve_high = [0.5] * 20 + [0.95] + [0.5] * 22
    assert ga.adjudicate_p2_f2(gates, curve_high)["verdict"] == "F2_FALSIFIED"

    gate_results_failing_gg0 = [
        ga.GateResult("gg0", "fail", "revision mismatch"),
        ga.GateResult("gg1", "pass"), ga.GateResult("gg2", "pass"),
        ga.GateResult("gg3", "pass"), ga.GateResult("gg4", "pass"),
    ]
    readouts = {"dual_leg_decision": dual_leg_all_pass, "ambigqa_curve": curve_low, "transfer_matrix": {}}
    final = ga.adjudicate(gates, gate_results_failing_gg0, readouts)
    assert final["p1_f1"]["verdict"] == "INDETERMINATE", final["p1_f1"]
    assert final["p2_f2"]["verdict"] == "INDETERMINATE", final["p2_f2"]

    gate_results_ok = [
        ga.GateResult("gg0", "pass"), ga.GateResult("gg1", "pass"), ga.GateResult("gg2", "pass"),
        ga.GateResult("gg3", "pass"), ga.GateResult("gg4", "pass"),
    ]
    final_ok = ga.adjudicate(gates, gate_results_ok, readouts)
    assert final_ok["p1_f1"]["verdict"] == "P1_SUPPORTED"
    assert final_ok["p2_f2"]["verdict"] == "P2_SUPPORTED"
    return "PASS"


# ---------------------------------------------------------------------------
# run_cell.py: orchestration end-to-end. surface_residualization.py and
# gate_adjudicator.py are library-only (no CLI of their own); run_cell.py
# is their first and only committed real-data caller, so this check is the
# only thing in the repo that ever drives stages 2-5 (probe sweep,
# residualization, gate adjudication, containment+write) together against
# real (if synthetic) inputs.
# ---------------------------------------------------------------------------

def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _write_extraction_fixture(ext_dir: Path, rows: list[dict], *, hid: int = 8,
                               n_hidden_states: int = 43, render: str = "primary",
                               seed: int = 0) -> dict:
    """Same synthetic-activation convention as _probe_sweep_end_to_end's
    write_panel_and_extraction, plus the extra manifest fields
    run_cell.build_run_context reads (model_repo/revision/base_form/
    hidden_size/n_hidden_layers)."""
    import numpy as np
    import torch
    from safetensors.torch import save_file

    rng = np.random.default_rng(seed)
    ext_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        base = 1.0 if r["label"] == "known" else -1.0
        tensors = {f"L{L}": torch.tensor(rng.normal(0, 1, hid) + base * 0.6, dtype=torch.float32)
                   for L in range(n_hidden_states)}
        stem = r["row_key"].replace("::", "__")
        save_file(tensors, str(ext_dir / f"{stem}__anchor.safetensors"))
    manifest = {
        "stage": "flavor_atlas_gemma_pt_confirmatory_anchor_extract",
        "model_repo": "synthetic/smoke-repo",
        "revision": "synthetic-smoke-revision",
        "base_form": "pretrain-only base, no adapter, bf16",
        "render": render,
        "hidden_size": hid,
        "n_hidden_layers": n_hidden_states - 1,
        "layers": "all",
        "n_hidden_states": n_hidden_states,
        "anchor_position": "prompt_len-1",
        "forward_use_cache": True,
        "complete": True,
        "n_rows_extracted": len(rows),
        "n_rows_total": len(rows),
    }
    (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


@check("run_cell: orchestration end-to-end (stages 2-5: probe sweep, residualization, "
       "gate adjudication, containment+write) on synthetic fixtures")
def _run_cell_orchestration_end_to_end():
    import build_flavor_panels as bfp
    import render_gemma as rg
    import run_cell as rc

    tmp = Path(tempfile.mkdtemp())
    panels_dir = tmp / "panels"
    panels_dir.mkdir()
    extraction_root = tmp / "extraction"
    control_extraction_dir = tmp / "control_extraction"

    def make_kuq_rows() -> list[dict]:
        rows, i = [], 0
        for _ in range(700):
            rows.append({"row_key": f"kuq-{i:06d}", "question": f"Synthetic kuq question {i}?",
                         "label": "known", "flavor": "known"})
            i += 1
        for cat in rg.KUQ_CATEGORIES:
            for _ in range(250):
                rows.append({"row_key": f"kuq-{i:06d}", "question": f"Synthetic kuq question {i}?",
                             "label": "unknown", "flavor": cat})
                i += 1
        return rows

    kuq_rows = make_kuq_rows()
    ambigqa_rows = (
        [{"row_key": f"ambigqa-{i:04d}", "question": f"Synthetic ambigqa question {i}?",
          "label": "known", "flavor": "ambigqa"} for i in range(20)]
        + [{"row_key": f"ambigqa-{i:04d}", "question": f"Synthetic ambigqa question {i}?",
            "label": "unknown", "flavor": "ambigqa"} for i in range(20, 40)]
    )
    selfaware_rows = (
        [{"row_key": f"selfaware-{i:04d}", "question": f"Synthetic selfaware question {i}?",
          "label": "known", "flavor": "selfaware"} for i in range(20)]
        + [{"row_key": f"selfaware-{i:04d}", "question": f"Synthetic selfaware question {i}?",
            "label": "unknown", "flavor": "selfaware"} for i in range(20, 40)]
    )

    _write_jsonl(panels_dir / "kuq_panel.jsonl", kuq_rows)
    _write_jsonl(panels_dir / "ambigqa_panel.jsonl", ambigqa_rows)
    _write_jsonl(panels_dir / "selfaware_panel.jsonl", selfaware_rows)

    _write_extraction_fixture(extraction_root / "kuq", kuq_rows)
    _write_extraction_fixture(extraction_root / "ambigqa", ambigqa_rows)
    _write_extraction_fixture(extraction_root / "selfaware", selfaware_rows)
    control_rows = rg.select_dual_render_subsample(kuq_rows)
    _write_extraction_fixture(control_extraction_dir, control_rows, render="control")

    # Stage 1 (panel verify) is deliberately NOT driven through run_cell's
    # subprocess call to build_flavor_panels.py's main() here: that main()
    # hard-enforces the REAL upstream row/flavor counts pinned in
    # gates.yaml (5540/2748/3369 with exact per-flavor splits) against a
    # real sha256 preimage -- structurally impossible to satisfy with
    # synthetic data, exactly why the existing `_panel_builder` check above
    # exercises verify_and_copy directly instead of main(). This check
    # pre-seeds panels_dir as if stage 1 had already run (mirroring that
    # same discipline) and drives every stage that is actually new this
    # pass: probe sweep, residualization, gate adjudication, containment.
    panels_manifest = {
        "gg0_status": "PASS",
        "reused_from": {
            "kuq": {"sha256": bfp.sha256_of(panels_dir / "kuq_panel.jsonl")},
            "ambigqa": {"sha256": bfp.sha256_of(panels_dir / "ambigqa_panel.jsonl")},
            "selfaware": {"sha256": bfp.sha256_of(panels_dir / "selfaware_panel.jsonl")},
        },
        "counts": bfp.counts_summary(kuq_rows, ambigqa_rows, selfaware_rows),
    }
    (panels_dir / "panels_manifest.json").write_text(json.dumps(panels_manifest, indent=2), encoding="utf-8")

    args = rc.parse_args([
        # resolve_plan's source-panel existence check looks under
        # --rawbase-panels-dir (real gitignored upstream data by default);
        # pointing it at the already-pre-seeded panels_dir keeps that check
        # meaningful (files must exist) without needing the real upstream
        # panels this synthetic smoke deliberately does not have.
        "--rawbase-panels-dir", str(panels_dir),
        "--panels-dir", str(panels_dir),
        "--extraction-root", str(extraction_root),
        "--control-extraction-dir", str(control_extraction_dir),
        "--probe-out", str(tmp / "probe_result.json"),
        "--residualization-out", str(tmp / "residualization_result.json"),
        "--committed-out", str(tmp / "analysis-committed" / "gemma_flavor_sweep.json"),
        "--n-permutations", "3",
        "--paired-smoke-outcome", "hs00_to_hs24_identical_and_divergence_begins_at_hs25",
        "--runtime-image-digest", "sha256:2471502c3110a96d4955b48eb58da41e96a90276d22c4d5f1eac2c99b60a2cf8",
        "--provenance-lines-present",
    ])

    plan = rc.resolve_plan(args)
    assert rc.missing_inputs(plan) == [], rc.missing_inputs(plan)

    extraction_manifests = rc.require_seam_admissible(plan["extractions"])
    assert len(extraction_manifests) == 4
    assert all(m.get("forward_use_cache") is True for m in extraction_manifests)

    probe_result = rc.run_probe_sweep(args)
    assert "dual_leg_decision" in probe_result
    for cat in rc.KUQ_CATEGORIES:
        assert probe_result["dual_leg_decision"][cat]["leg_a"]["hidden_state"] == 24

    residualization_result = rc.run_residualization(args, probe_result)
    assert residualization_result["n_permutations"] == 3
    assert any(v != 0.0 for v in residualization_result["treatment_r2"].values()), \
        "treatment_r2 all zero -- residualization looks stubbed"
    assert residualization_result["planted"]["planted_pooled_auroc"] > 0.0, \
        "planted control auroc is zero -- residualization looks stubbed"
    assert set(residualization_result["residualized_dual_leg_decision"].keys()) == set(rc.KUQ_CATEGORIES)

    probe_module_sha = rc.sha256_file(plan["probe_module"]["path"])
    run_context = rc.build_run_context(args, extraction_manifests, panels_manifest, probe_module_sha)
    assert run_context["kuq_rows"] == len(kuq_rows)

    gates = rc.load_yaml(rc.GATES_PATH)
    adjudication = rc.run_gate_adjudication(
        args, gates, extraction_manifests, run_context, probe_result, residualization_result,
    )
    gate_results = adjudication["gate_results"]
    # gg1/gg3 pass (real flags supplied); gg0 fails against synthetic data
    # (wrong revision/shas/row-counts) -- proving adjudication is genuinely
    # discriminating, not stubbed, and that fail-closed propagation holds
    # even when this orchestrator runs against a synthetic fixture.
    assert gate_results["gg1"]["status"] == "pass", gate_results["gg1"]
    assert gate_results["gg3"]["status"] == "pass", gate_results["gg3"]
    assert gate_results["gg0"]["status"] == "fail", gate_results["gg0"]
    assert adjudication["p1_f1"]["verdict"] == "INDETERMINATE", adjudication["p1_f1"]
    assert adjudication["p2_f2"]["verdict"] == "INDETERMINATE", adjudication["p2_f2"]

    committed = rc.build_committed_output(
        run_context, extraction_manifests, probe_result, residualization_result, adjudication,
    )
    private_texts = {r["question"] for r in kuq_rows + ambigqa_rows + selfaware_rows}
    rc.finalize_and_write(args, committed, gates, private_texts)

    assert args.committed_out.is_file(), "GG6 should have passed and the committed file should exist"
    on_disk = json.loads(args.committed_out.read_text())
    for key in ("g1_kuq", "g2_ambigqa", "g3_selfaware", "g4_transfer_matrix",
                "dual_leg_decision", "g5_residualization", "gate_adjudication", "input_shas"):
        assert key in on_disk, f"committed output missing '{key}' -- orchestration looks stubbed"
    assert on_disk["gate_adjudication"]["gate_results"]["gg6"]["status"] == "pass", \
        on_disk["gate_adjudication"]["gate_results"]["gg6"]
    blob = json.dumps(on_disk).lower()
    for q in private_texts:
        assert q.lower() not in blob, "a raw question string leaked into the committed output"
    return "PASS"


# ---------------------------------------------------------------------------
# kv_seam_paired_smoke.py + test_leg_b_selection_logic.py: already have
# their own committed CLI entry points; invoked here as subprocesses of
# the EXACT committed command so this runner also proves those commands
# work, without duplicating their logic.
# ---------------------------------------------------------------------------

@check("kv_seam_paired_smoke.py --mode=synthetic (subprocess, exact committed command)")
def _kv_seam_subprocess():
    proc = subprocess.run(
        [sys.executable, str(HERE / "kv_seam_paired_smoke.py"), "--mode=synthetic"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"exit {proc.returncode}: {proc.stdout}\n{proc.stderr}"
    payload = json.loads(proc.stdout)
    assert payload["all_pass"] is True, payload
    return "PASS"


@check("test_leg_b_selection_logic.py (subprocess, exact committed command)")
def _leg_b_subprocess():
    proc = subprocess.run(
        [sys.executable, str(HERE / "test_leg_b_selection_logic.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"exit {proc.returncode}: {proc.stdout}\n{proc.stderr}"
    return "PASS"


def main() -> int:
    checks = [
        _render_primary, _render_subsample, _render_control,
        _extractor,
        _panel_builder,
        _gg1_cpu_gate, _probe_sweep_end_to_end,
        _residualization,
        _gate_adjudicator,
        _run_cell_orchestration_end_to_end,
        _kv_seam_subprocess, _leg_b_subprocess,
    ]
    for fn in checks:
        fn()

    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_skip = sum(1 for r in RESULTS if r["status"] == "SKIPPED")
    n_fail = sum(1 for r in RESULTS if r["status"] not in ("PASS", "SKIPPED"))
    print(f"\n{n_pass} passed, {n_skip} skipped, {n_fail} failed (of {len(RESULTS)})")
    for r in RESULTS:
        if r["status"] not in ("PASS", "SKIPPED"):
            print(f"  FAILED: {r['name']}: {r['status']}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
