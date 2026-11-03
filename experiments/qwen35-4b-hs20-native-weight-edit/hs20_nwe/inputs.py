"""Pinned-input verification, metadata-safe materialization, exact splits.

Model-visible rows carry only an allow-listed set of fields. Historical
generated text, token ids, fire flags and sensor scores are never copied.
``aliases`` and ``role`` are scoring/localization fields (the frozen render
reads ``question`` only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .config import ROLES, SOURCE_ROLE_SPELLING, Cell, Layout
from .util import (HarnessError, canonical_sha256, read_json, read_jsonl, sha256_file,
                   write_json, write_jsonl)

REUSED_MANIFEST = "experiments/qwen35-4b-midband-doubt-snap/analysis-committed/reused_rows_manifest.json"
DIRECTION_BUILD_MANIFEST = "experiments/common/directions/qwen35-4b-hs20/build_manifest.json"
INPUT_NAMES = {"dose": "fit_rows_for_dose.jsonl", "heldout": "heldout_rows_for_steer.jsonl",
               "anchor": "fit_rows_for_anchor.jsonl"}
# Allow-list of fields that may leave the source files. Everything else
# (baseline_*, fire, z_d, tau, score_neg_z_d, role_candidate, ...) is dropped.
KEEP_FIELDS = ("row_key", "question", "aliases", "source", "category_canon")
FORBIDDEN_OUTPUT_FIELDS = frozenset({
    "fire", "z_d", "tau", "score_neg_z_d", "baseline_text", "baseline_token_ids",
    "baseline_clean", "baseline_finish_reason", "baseline_old_grade",
    "baseline_terminated_naturally", "role_candidate", "out_text", "answer_text"})


def load_pins(project_root: Path) -> dict:
    """Full-length hashes and the committed roster from committed manifests."""
    reused_path = Path(project_root) / REUSED_MANIFEST
    build_path = Path(project_root) / DIRECTION_BUILD_MANIFEST
    reused, build = read_json(reused_path), read_json(build_path)
    declared = reused["reused_from"]["source_file_sha256"]
    pins = {
        "dose": declared[INPUT_NAMES["dose"]],
        "heldout": declared[INPUT_NAMES["heldout"]],
        "anchor": build["fit_rows_sha256"],
    }
    for name, value in pins.items():
        if not (isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)):
            raise HarnessError("PIN_FORMAT", f"pin for {name} is not a full lowercase sha256")
    roster = {k: [(r["row_key"], r["role"], r["split"]) for r in v] for k, v in reused["rows"].items()}
    return {"hashes": pins, "roster": roster, "counts": reused["counts"],
            "pin_sources": {"reused_rows_manifest": sha256_file(reused_path),
                            "direction_build_manifest": sha256_file(build_path)}}


def verify_input_hashes(pins: dict, inputs_dir: Path) -> dict[str, str]:
    seen = {}
    for name, filename in INPUT_NAMES.items():
        path = Path(inputs_dir) / filename
        if not path.is_file() or path.is_symlink():
            raise HarnessError("INPUT_MISSING", f"missing staged input {filename}")
        digest = sha256_file(path)
        if digest != pins["hashes"][name]:
            raise HarnessError("INPUT_HASH", f"{filename} sha256 differs from its pinned full hash")
        seen[filename] = digest
    return seen


def _role(value: str) -> str:
    if value not in SOURCE_ROLE_SPELLING:
        raise HarnessError("ROLE_SPELLING", f"unexpected source role {value!r}")
    return SOURCE_ROLE_SPELLING[value]


def _clean(row: dict, role: str) -> dict:
    missing = [f for f in ("row_key", "question") if not row.get(f)]
    if missing:
        raise HarnessError("ROW_FIELDS", f"row lacks required fields {missing}")
    out = {f: row.get(f) for f in KEEP_FIELDS if f in row}
    aliases = out.get("aliases") or []
    if not isinstance(aliases, list):
        raise HarnessError("ROW_FIELDS", "aliases must be a list")
    out["aliases"] = [str(a) for a in aliases]
    out["role"] = role
    return out


def permuted(keys: list[str], seed: int) -> list[str]:
    """Stable seeded permutation of the byte-sorted keys."""
    ordered = sorted(keys)
    order = np.random.default_rng(int(seed)).permutation(len(ordered))
    return [ordered[int(i)] for i in order]


def check_roster(pins: dict, dose: list[dict], anchor: list[dict], heldout: list[dict]) -> None:
    roster = pins["roster"]
    expected = {
        "dose": {(k, r, s) for key in ("confab_fit", "known_correct_answered_fit") for k, r, s in roster[key]},
        "anchor": {(k, r, s) for key in ("confab_fit", "known_correct_answered_fit", "unknown_refused_fit_only")
                   for k, r, s in roster[key]},
        "heldout": {(k, r, s) for key in ("confab_held_out", "known_correct_answered_held_out")
                    for k, r, s in roster[key]},
    }
    for name, rows in (("dose", dose), ("anchor", anchor), ("heldout", heldout)):
        got = {(r["row_key"], r["role"], r["split"]) for r in rows}
        if len(got) != len(rows):
            raise HarnessError("ROSTER", f"duplicate rows in {name} input")
        if got != expected[name]:
            raise HarnessError("ROSTER", f"{name} input membership differs from the committed roster")


def load_sources(pins: dict, inputs_dir: Path) -> dict[str, list[dict]]:
    verify_input_hashes(pins, inputs_dir)
    raw = {name: read_jsonl(Path(inputs_dir) / fname) for name, fname in INPUT_NAMES.items()}
    check_roster(pins, raw["dose"], raw["anchor"], raw["heldout"])
    # The dose and anchor files describe the same 1127 rows; they must agree.
    anchor_by_key = {r["row_key"]: r for r in raw["anchor"]}
    for r in raw["dose"]:
        a = anchor_by_key[r["row_key"]]
        if (r["question"], r.get("aliases") or []) != (a["question"], a.get("aliases") or []):
            raise HarnessError("INPUT_CONFLICT", "dose and anchor inputs disagree on a shared row")
    return raw


def build_populations(cell: Cell, raw: dict[str, list[dict]]) -> dict[str, Any]:
    """Pure: exact memberships from cell.yaml seeds and counts."""
    sp = cell.cell["splits"]
    cleaned: dict[str, list[dict]] = {r: [] for r in ROLES}
    for row in raw["dose"]:
        role = _role(row["role"])
        if role == "unknown_refused":
            raise HarnessError("ROLE", "dose input must not hold unknown_refused rows")
        cleaned[role].append(_clean(row, role))
    unknown_rows = [r for r in raw["anchor"] if _role(r["role"]) == "unknown_refused"]
    cleaned["unknown_refused"] = [_clean(r, "unknown_refused") for r in unknown_rows]
    by_key = {role: {r["row_key"]: r for r in rows} for role, rows in cleaned.items()}

    held_cleaned = {"confab": [], "known_correct": []}
    for row in raw["heldout"]:
        role = _role(row["role"])
        if role == "unknown_refused":
            raise HarnessError("ROLE", "held-out input must not hold unknown_refused rows")
        held_cleaned[role].append(_clean(row, role))
    held_by_key = {role: {r["row_key"]: r for r in rows} for role, rows in held_cleaned.items()}

    fit_l_n = {"confab": sp["fit_localization"]["confab"], "known_correct": sp["fit_localization"]["known_correct"],
               "unknown_refused": sp["fit_localization"]["unknown_refused"]}
    fit_s_n = {"confab": sp["fit_selection"]["confab"], "known_correct": sp["fit_selection"]["known_correct"]}
    fit_l: dict[str, list[str]] = {}
    fit_s: dict[str, list[str]] = {}
    for role in ROLES:
        order = permuted(list(by_key[role]), sp["seed"])
        n_l = fit_l_n[role]
        if role == "unknown_refused":
            if len(order) != n_l:
                raise HarnessError("COUNT", f"unknown_refused has {len(order)} rows, expected {n_l}")
            fit_l[role], fit_s[role] = order, []
            continue
        if len(order) != n_l + fit_s_n[role]:
            raise HarnessError("COUNT", f"{role} has {len(order)} FIT rows, expected {n_l + fit_s_n[role]}")
        fit_l[role], fit_s[role] = order[:n_l], order[n_l:]
        if len(fit_s[role]) != fit_s_n[role]:
            raise HarnessError("COUNT", f"{role} FIT-S size mismatch")

    screen = {role: fit_s[role][: sp["fit_screen"][role]] for role in ("confab", "known_correct")}
    for role, keys in screen.items():
        if len(keys) != sp["fit_screen"][role]:
            raise HarnessError("COUNT", f"FIT-screen {role} short")

    held_conf = permuted(list(held_by_key["confab"]), sp["heldout_seed"])[: sp["heldout"]["confab"]]
    held_known = sorted(held_by_key["known_correct"])
    if len(held_conf) != sp["heldout"]["confab"] or len(held_known) != sp["heldout"]["known_correct"]:
        raise HarnessError("COUNT", "held-out population size mismatch")

    decoy = {"known_correct": permuted(fit_l["known_correct"], sp["decoy_seed"])[: sp["decoy_known"]],
             "unknown_refused": permuted(fit_l["unknown_refused"], sp["decoy_seed"])[: sp["decoy_unknown_refused"]]}

    def pick(role: str, keys: list[str], source: dict, pop: str) -> list[dict]:
        return [{**source[role][k], "population": pop} for k in sorted(keys)]

    pops = {
        "fit_l": (pick("confab", fit_l["confab"], by_key, "fit_l") + pick("known_correct", fit_l["known_correct"], by_key, "fit_l")
                  + pick("unknown_refused", fit_l["unknown_refused"], by_key, "fit_l")),
        "fit_s": pick("confab", fit_s["confab"], by_key, "fit_s") + pick("known_correct", fit_s["known_correct"], by_key, "fit_s"),
        "fit_screen": pick("confab", screen["confab"], by_key, "fit_screen") + pick("known_correct", screen["known_correct"], by_key, "fit_screen"),
        "heldout": pick("confab", held_conf, held_by_key, "heldout") + pick("known_correct", held_known, held_by_key, "heldout"),
        "decoy": (pick("known_correct", decoy["known_correct"], by_key, "decoy")
                  + pick("unknown_refused", decoy["unknown_refused"], by_key, "decoy")),
    }
    pops["heldout_confab"] = [r for r in pops["heldout"] if r["role"] == "confab"]
    pops["heldout_known"] = [r for r in pops["heldout"] if r["role"] == "known_correct"]
    for r in pops["decoy"]:
        r["decoy_class"] = "known" if r["role"] == "known_correct" else "unknown"
    for r in pops["fit_l"]:
        r["decoy"] = False
    decoy_keys = {r["row_key"] for r in pops["decoy"]}
    for r in pops["fit_l"]:
        r["decoy"] = r["row_key"] in decoy_keys
    return pops


def check_no_leakage(pops: dict[str, list[dict]]) -> dict:
    """Disjointness and containment of the exact memberships (G0)."""
    keys = {name: {r["row_key"] for r in rows} for name, rows in pops.items()}
    problems = []
    if keys["fit_l"] & keys["fit_s"]:
        problems.append("FIT-L and FIT-S overlap")
    if not keys["fit_screen"] <= keys["fit_s"]:
        problems.append("FIT-screen is not inside FIT-S")
    if not keys["decoy"] <= keys["fit_l"]:
        problems.append("decoys are not inside FIT-L")
    if keys["decoy"] & (keys["fit_s"] | keys["heldout"]):
        problems.append("decoys leak into FIT-S or held-out")
    if keys["heldout"] & (keys["fit_l"] | keys["fit_s"]):
        problems.append("held-out overlaps FIT")
    if problems:
        raise HarnessError("LEAKAGE", "; ".join(problems))
    norm = lambda q: " ".join(q.lower().split())  # noqa: E731
    q_fit = {norm(r["question"]) for r in pops["fit_l"] + pops["fit_s"]}
    overlap = sum(1 for r in pops["heldout"] if norm(r["question"]) in q_fit)
    return {"key_overlaps": 0, "heldout_question_text_overlap_with_fit": overlap}


def materialize(project_root: Path, layout: Layout, cell: Cell, inputs_dir: Path) -> dict:
    """Write private row files and an ID-only manifest. Idempotent for equal inputs."""
    pins = load_pins(project_root)
    raw = load_sources(pins, inputs_dir)
    pops = build_populations(cell, raw)
    leakage = check_no_leakage(pops)
    out_dir = layout.local("materialize", shared=True)
    hashes: dict[str, str] = {}
    for name in ("fit_l", "fit_screen", "heldout", "heldout_confab", "heldout_known", "decoy"):
        for row in pops[name]:
            bad = FORBIDDEN_OUTPUT_FIELDS & set(row)
            if bad:
                raise HarnessError("LEAK_FIELDS", f"forbidden fields in materialized row: {sorted(bad)}")
        hashes[name] = write_jsonl(out_dir / f"{name}.jsonl", pops[name])
    manifest = {
        "schema_version": "hs20-nwe-materialize/v1", **cell.stamp(),
        "input_sha256": {INPUT_NAMES[k]: v for k, v in pins["hashes"].items()},
        "pin_sources": pins["pin_sources"], "splits": cell.cell["splits"],
        "role_source_spellings": SOURCE_ROLE_SPELLING,
        "ids": {name: {"confab": [r["row_key"] for r in rows if r["role"] == "confab"],
                       "known_correct": [r["row_key"] for r in rows if r["role"] == "known_correct"],
                       "unknown_refused": [r["row_key"] for r in rows if r["role"] == "unknown_refused"]}
                for name, rows in pops.items() if name not in ("fit_s",)},
        "counts": {name: {role: sum(1 for r in rows if r["role"] == role) for role in ROLES}
                   for name, rows in pops.items()},
        "fit_s_ids_sha256": canonical_sha256(sorted(r["row_key"] for r in pops["fit_s"])),
        "row_file_sha256": hashes, "leakage": leakage,
        "forbidden_fields_checked": sorted(FORBIDDEN_OUTPUT_FIELDS),
        "warnings": ([] if leakage["heldout_question_text_overlap_with_fit"] == 0 else
                     ["held-out question text duplicates a FIT question; reported, not refused"]),
    }
    manifest["manifest_sha256_payload"] = canonical_sha256({k: v for k, v in manifest.items()})
    write_json(out_dir / "manifest.json", manifest)
    return manifest
