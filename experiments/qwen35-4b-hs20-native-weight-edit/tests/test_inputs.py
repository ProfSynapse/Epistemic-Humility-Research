"""Pinned inputs, exact memberships, no leakage, forbidden-field stripping."""

import json

import pytest

from conftest import SLUG, make_inputs
from hs20_nwe import inputs
from hs20_nwe.config import Layout
from hs20_nwe.util import HarnessError, read_jsonl


@pytest.fixture
def mat(project, cell):
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    manifest = inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))
    return project, layout, manifest


def keys(layout, name):
    return [r["row_key"] for r in read_jsonl(layout.local(f"materialize/{name}.jsonl", shared=True))]


def test_exact_memberships(mat, cell):
    _, layout, m = mat
    sp = cell.cell["splits"]
    c = m["counts"]
    assert c["fit_l"] == {"confab": 443, "known_correct": 120, "unknown_refused": 181}
    assert c["fit_s"] == {"confab": 444, "known_correct": 120, "unknown_refused": 0}
    assert c["fit_screen"] == {"confab": 96, "known_correct": 96, "unknown_refused": 0}
    assert c["heldout"] == {"confab": 300, "known_correct": 360, "unknown_refused": 0}
    assert c["decoy"] == {"confab": 0, "known_correct": sp["decoy_known"], "unknown_refused": sp["decoy_unknown_refused"]}
    assert c["fit_l"]["confab"] == sp["fit_localization"]["confab"]


def test_disjointness_and_containment(mat):
    _, layout, _ = mat
    fit_l, screen, held, decoy = (set(keys(layout, n)) for n in ("fit_l", "fit_screen", "heldout", "decoy"))
    assert not (fit_l & screen) and not (fit_l & held) and not (screen & held) and not (decoy & screen) and not (decoy & held)
    assert decoy <= fit_l
    assert set(keys(layout, "heldout_confab")) | set(keys(layout, "heldout_known")) == held


def test_split_is_seeded_and_stable(project, cell):
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    raw = inputs.load_sources(inputs.load_pins(project.root), layout.local("inputs", shared=True))
    a = inputs.build_populations(cell, raw)
    b = inputs.build_populations(cell, raw)
    assert a == b
    assert inputs.permuted(["b", "a", "c", "d"], 1) == inputs.permuted(["d", "c", "b", "a"], 1)
    assert inputs.permuted(list("abcdefgh"), 1) != inputs.permuted(list("abcdefgh"), 2)


def test_model_rows_carry_only_allowlisted_fields(mat):
    _, layout, _ = mat
    for name in ("fit_l", "fit_screen", "heldout", "decoy"):
        for row in read_jsonl(layout.local(f"materialize/{name}.jsonl", shared=True)):
            assert not (set(row) & inputs.FORBIDDEN_OUTPUT_FIELDS)
            assert set(row) <= {"row_key", "question", "aliases", "source", "category_canon", "role", "population",
                                "decoy", "decoy_class"}


def test_confab_and_unknown_have_no_aliases_known_do(mat):
    _, layout, _ = mat
    for r in read_jsonl(layout.local("materialize/heldout.jsonl", shared=True)):
        assert bool(r["aliases"]) == (r["role"] == "known_correct")


def test_bad_hash_is_refused(project, cell):
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    target = layout.local("inputs/fit_rows_for_dose.jsonl", shared=True)
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(HarnessError) as e:
        inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))
    assert e.value.code == "INPUT_HASH"


def test_missing_input_is_refused(project, cell):
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    layout.local("inputs/heldout_rows_for_steer.jsonl", shared=True).unlink()
    with pytest.raises(HarnessError) as e:
        inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))
    assert e.value.code == "INPUT_MISSING"


def test_roster_mismatch_is_refused(project, cell):
    """A file whose bytes match its pin but whose membership differs from the committed roster fails."""
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    manifest = project.root / "experiments/qwen35-4b-midband-doubt-snap/analysis-committed/reused_rows_manifest.json"
    doc = json.loads(manifest.read_text())
    doc["rows"]["confab_fit"][0]["row_key"] = "tampered:0"
    manifest.write_text(json.dumps(doc))
    with pytest.raises(HarnessError) as e:
        inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))
    assert e.value.code == "ROSTER"


def test_unexpected_role_spelling_is_refused(project, cell):
    def mutate(files):
        for rows in files.values():
            for r in rows:
                if r["role"] == "unknown_refused":
                    r["role"] = "unknown"
                    break
    make_inputs(project, cell, mutate=mutate, repin=True)
    layout = Layout(project.root, SLUG)
    with pytest.raises(HarnessError):
        inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))


def test_wrong_counts_are_refused(project, cell, monkeypatch):
    make_inputs(project, cell)
    layout = Layout(project.root, SLUG)
    bad = json.loads(json.dumps(cell.cell))
    bad["splits"]["fit_localization"]["confab"] = 442
    from dataclasses import replace

    with pytest.raises(HarnessError) as e:
        inputs.materialize(project.root, layout, replace(cell, cell=bad), layout.local("inputs", shared=True))
    assert e.value.code == "COUNT"


def test_leakage_is_detected():
    pops = {n: [{"row_key": k, "question": f"q{k}", "role": "confab"} for k in ks] for n, ks in {
        "fit_l": ["a"], "fit_s": ["b"], "fit_screen": ["b"], "decoy": ["a"], "heldout": ["b2"]}.items()}
    inputs.check_no_leakage(pops)
    pops["heldout"] = [{"row_key": "a", "question": "qa", "role": "confab"}]
    with pytest.raises(HarnessError) as e:
        inputs.check_no_leakage(pops)
    assert e.value.code == "LEAKAGE"


def test_dose_and_anchor_disagreement_is_refused(project, cell):
    def mutate(files):
        files["fit_rows_for_anchor.jsonl"][0]["question"] = "changed"
    make_inputs(project, cell, mutate=mutate, repin=True)
    layout = Layout(project.root, SLUG)
    with pytest.raises(HarnessError) as e:
        inputs.materialize(project.root, layout, cell, layout.local("inputs", shared=True))
    assert e.value.code == "INPUT_CONFLICT"
