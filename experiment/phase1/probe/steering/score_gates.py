#!/usr/bin/env python3
"""Score declarative gates over a steer-cell's provenance JSONLs.

A gates.yaml declares named gates as calls into gate_primitives over the arm
rows.jsonl files the steer_cell runner wrote. This keeps the gate logic (which
flip counts as a kill, what the collateral ceiling is, which contrast gets a
bootstrap CI) in a signed, human-readable config rather than a fresh script per
amendment. The primitives themselves are the pure, unit-tested library in
gate_primitives.py.

The gates.yaml grammar (see .skills/steering-cell/reference/gates-schema.md):

  seed: 20260705                 # default seed for every sampling primitive
  arms:                          # map an arm tag to its rows.jsonl
    primary:  primary/gen/rows.jsonl
    control:  control/gen/rows.jsonl
  baseline:
    rows_file: ../true_a0/rows_graded.jsonl   # frozen baseline grades
    key: row_key
  predicates:                    # named row predicates over baseline+arm fields
    baseline_confab: "base.get('confab_on_unanswerable')"
    baseline_correct: "base.get('correct') is True and base.get('answered')"
    steered_not_confab: "not arm.get('confab_on_unanswerable', arm.get('refused'))"
  gates:
    G2_reach:
      kind: count_flips
      arm: primary
      before: baseline_confab
      after: steered_not_confab
      universe: flagged
      assert: "at_least(result.flips, 5)"

Every ``kind`` maps to a gate_primitives function; ``assert`` is a threshold
expression over the primitive's result dict, evaluated in a sandboxed namespace
exposing the threshold helpers (at_most/at_least/within) and the ``result``.

This scorer requires the arm rows to already be GRADED (correct /
confab_on_unanswerable fields present). Grading is the amendment's own grader
(byte-pinned to the baseline); the runner writes raw generations, the grader adds
the grade fields, then this scorer reads them. A gates.yaml may point at either
the raw rows (for grade-free gates like refusal counts) or the graded rows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

STEER_DIR = Path(__file__).resolve().parent
if str(STEER_DIR) not in sys.path:
    sys.path.insert(0, str(STEER_DIR))

import gate_primitives as gp  # noqa: E402


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def _eval(expr: str, ns: dict):
    safe = {"__builtins__": {}}
    safe.update({"abs": abs, "min": min, "max": max, "len": len,
                 "True": True, "False": False, "None": None})
    safe.update(ns)
    return eval(expr, safe, {})  # noqa: S307 - sandboxed


def _predicate(expr: str):
    """Compile a predicate over (base, arm) row dicts."""
    def pred(base: dict, arm: dict) -> bool:
        return bool(_eval(expr, {"base": base, "arm": arm}))
    return pred


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path,
                    help="the cell.yaml (for out_dir resolution + sha echo)")
    ap.add_argument("--gates", required=True, type=Path)
    args = ap.parse_args(argv)

    import steer_cell
    cfg, cell_sha = steer_cell.load_config(args.config)
    cell = steer_cell.Cell(cfg, cell_sha, args.config)

    gspec = yaml.safe_load(args.gates.read_bytes())
    gates_dir = args.gates.resolve().parent
    default_seed = int(gspec.get("seed", 0))

    def resolve(ref: str) -> Path:
        p = Path(ref)
        if p.is_absolute():
            return p
        # arm rows are relative to the cell out_dir; other files to the gates.yaml
        cand = (cell.out_dir / ref)
        return cand if cand.exists() else (gates_dir / ref).resolve()

    # load baseline + arm rows keyed by row_key
    base_spec = gspec.get("baseline", {})
    base_key = base_spec.get("key", "row_key")
    baseline = {}
    if "rows_file" in base_spec:
        for r in load_jsonl(resolve(base_spec["rows_file"])):
            baseline[r[base_key]] = r
    arms = {}
    for tag, ref in gspec.get("arms", {}).items():
        arms[tag] = {r["row_key"]: r for r in load_jsonl(resolve(ref))}

    predicates = {name: _predicate(expr)
                  for name, expr in gspec.get("predicates", {}).items()}

    def flagged_universe(arm_rows):
        return {k for k, r in arm_rows.items() if r.get("flagged")}

    def rows_for(arm_tag):
        """Aligned list of merged (base, arm) row dicts for an arm."""
        arm_rows = arms[arm_tag]
        keys = list(arm_rows.keys())
        return keys, [(baseline.get(k, {}), arm_rows[k]) for k in keys]

    results = {"cell_config_sha256": cell_sha, "gates": {}}
    overall = True

    for gname, gdef in gspec.get("gates", {}).items():
        kind = gdef["kind"]
        seed = int(gdef.get("seed", default_seed))
        if kind == "count_flips":
            arm_rows = arms[gdef["arm"]]
            before = predicates[gdef["before"]]
            after = predicates[gdef["after"]]
            uni = gdef.get("universe")
            flagged = flagged_universe(arm_rows)
            recs = [{"base": baseline.get(k, {}), "arm": arm_rows[k], "_k": k}
                    for k in arm_rows]
            res = gp.count_flips(
                recs,
                before=lambda r: before(r["base"], r["arm"]),
                after=lambda r: after(r["base"], r["arm"]),
                universe=(None if uni != "flagged"
                          else (lambda r: r["_k"] in flagged)))
        elif kind == "kill_diff_vs_control":
            t_arm = arms[gdef["treatment"]]
            c_arm = arms[gdef["control"]]
            before = predicates[gdef["before"]]
            after = predicates[gdef["after"]]
            universe_keys = [k for k in baseline
                             if before(baseline[k], t_arm.get(k, {}))]

            def ind(arm_rows):
                flagged = flagged_universe(arm_rows)
                return [1 if (k in flagged and k in arm_rows
                              and after(baseline.get(k, {}), arm_rows[k])) else 0
                        for k in universe_keys]
            res = gp.kill_diff_vs_control(ind(t_arm), ind(c_arm), seed=seed,
                                          n_boot=int(gdef.get("n_boot", 1000)))
        elif kind == "permutation_p":
            arm_tag = gdef["arm"]
            _keys, merged = rows_for(arm_tag)
            value_expr = gdef["value"]
            label_pred = predicates[gdef["label"]]
            values = [float(_eval(value_expr, {"base": b, "arm": a}))
                      for b, a in merged]
            labels = [1 if label_pred(b, a) else 0 for b, a in merged]
            res = gp.permutation_p(values, labels, seed=seed,
                                   n_perm=int(gdef.get("n_perm", 10000)),
                                   tail=gdef.get("tail", "greater"))
        elif kind == "auroc_floor":
            arm_tag = gdef["arm"]
            _keys, merged = rows_for(arm_tag)
            scores = [float(_eval(gdef["score"], {"base": b, "arm": a}))
                      for b, a in merged]
            labels = [1 if predicates[gdef["label"]](b, a) else 0
                      for b, a in merged]
            res = gp.auroc_floor(scores, labels, floor=float(gdef["floor"]),
                                 seed=seed, n_boot=int(gdef.get("n_boot", 1000)))
        else:
            raise ValueError(f"gate {gname}: unknown kind {kind!r}")

        assert_expr = gdef.get("assert")
        if assert_expr:
            verdict = _eval(assert_expr, {"result": _AttrDict(res),
                                          "at_most": gp.at_most,
                                          "at_least": gp.at_least,
                                          "within": gp.within})
            passed = bool(verdict["pass"] if isinstance(verdict, dict) else verdict)
            res = {**res, "assert": assert_expr,
                   "assert_result": verdict if isinstance(verdict, dict) else None,
                   "pass": passed}
        else:
            passed = bool(res.get("pass", res.get("ci_excludes_zero", True)))
            res = {**res, "pass": passed}
        overall = overall and passed
        results["gates"][gname] = res
        print(f"[gates] {gname}: pass={passed} {kind}", flush=True)

    results["overall_pass"] = overall
    out = cell.out_dir / "gates_report.json"
    cell.out_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"[gates] OVERALL pass={overall} -> {out}", flush=True)
    return 0 if overall else 5


class _AttrDict(dict):
    """dict whose keys are also attribute-accessible (so ``result.flips`` works
    in an assert expression)."""
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e


if __name__ == "__main__":
    sys.exit(main())
