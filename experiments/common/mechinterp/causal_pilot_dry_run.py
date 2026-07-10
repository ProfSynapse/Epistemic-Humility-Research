from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


class DryRunValidationError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise DryRunValidationError(
            "PyYAML is required to load the causal-pilot dry-run config. "
            "Install pyyaml and rerun this validator."
        ) from exc

    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise DryRunValidationError(f"{path} did not load to a YAML mapping")
    return payload


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise DryRunValidationError(f"{path} did not load to a JSON object")
    return payload


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DryRunValidationError(message)


def validate_spec_guards(config: dict[str, Any]) -> None:
    require(
        config.get("spec", {}).get("status") == "readiness_spec_only",
        "spec.status must be readiness_spec_only",
    )
    require(
        config.get("model", {}).get("enable_thinking") is False,
        "model.enable_thinking must be false",
    )
    require(
        config.get("first_smoke", {})
        .get("initial_scope", {})
        .get("generation_allowed_by_this_spec")
        is False,
        "first_smoke.initial_scope.generation_allowed_by_this_spec must be false",
    )


def read_rows(rows_path: Path) -> tuple[int, dict[str, int]]:
    require(rows_path.exists(), f"rows.jsonl missing: {rows_path}")
    seen: set[str] = set()
    labels: Counter[str] = Counter()
    count = 0
    with rows_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DryRunValidationError(
                    f"{rows_path}:{line_no} is not valid JSON"
                ) from exc
            row_key = row.get("probe_pool_row_key")
            require(
                isinstance(row_key, str) and row_key,
                f"{rows_path}:{line_no} missing probe_pool_row_key",
            )
            require(
                row_key not in seen,
                f"{rows_path}:{line_no} duplicate probe_pool_row_key {row_key!r}",
            )
            seen.add(row_key)
            label = row.get("label")
            require(
                isinstance(label, str) and label,
                f"{rows_path}:{line_no} missing label",
            )
            labels[label] += 1
            count += 1
    return count, dict(labels)


def validate_row_counts(
    *,
    row_count: int,
    label_counts: dict[str, int],
    expected: dict[str, Any],
    context: str,
) -> None:
    expected_count = expected.get("row_count")
    if expected_count is not None:
        require(
            row_count == expected_count,
            f"{context} row_count mismatch: expected {expected_count}, found {row_count}",
        )
    expected_labels = expected.get("label_counts") or {}
    require(
        label_counts == expected_labels,
        f"{context} label_counts mismatch: expected {expected_labels}, found {label_counts}",
    )


def find_direction(direction_manifest: dict[str, Any], direction_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in direction_manifest.get("directions", [])
        if item.get("direction_id") == direction_id
    ]
    require(
        len(matches) == 1,
        f"direction manifest must contain exactly one {direction_id}; found {len(matches)}",
    )
    return matches[0]


def validate_direction_fields(candidate: dict[str, Any], direction: dict[str, Any]) -> None:
    allow_layer_override = bool(candidate.get("allow_direction_layer_override"))
    comparisons = {
        "role": candidate.get("role"),
        "method": candidate.get("method"),
        "contrast": candidate.get("contrast"),
        "tensor_key": candidate.get("tensor_key"),
    }
    if not allow_layer_override:
        comparisons["layer"] = candidate.get("layer")
    for key, expected in comparisons.items():
        require(
            direction.get(key) == expected,
            (
                f"{candidate.get('label', candidate.get('direction_id'))} {key} mismatch: "
                f"expected {expected!r}, found {direction.get(key)!r}"
            ),
        )
    expected_status = candidate.get("required_status", "ok")
    require(
        direction.get("status") == expected_status,
        (
            f"{candidate.get('label', candidate.get('direction_id'))} status mismatch: "
            f"expected {expected_status!r}, found {direction.get('status')!r}"
        ),
    )
    configured_hash = candidate.get("vector_sha256")
    if configured_hash:
        require(
            direction.get("vector_sha256") == configured_hash,
            (
                f"{candidate.get('label', candidate.get('direction_id'))} vector_sha256 "
                f"mismatch: expected {configured_hash!r}, found {direction.get('vector_sha256')!r}"
            ),
        )


def validate_component_direction_fields(component: dict[str, Any], direction: dict[str, Any], *, label: str) -> None:
    comparisons = {
        "role": component.get("role"),
        "layer": component.get("layer"),
        "tensor_key": component.get("tensor_key", "direction"),
    }
    if component.get("method") is not None:
        comparisons["method"] = component.get("method")
    if component.get("contrast") is not None:
        comparisons["contrast"] = component.get("contrast")
    for key, expected in comparisons.items():
        require(
            direction.get(key) == expected,
            (
                f"{label} component {component.get('label', component.get('direction_id'))} {key} mismatch: "
                f"expected {expected!r}, found {direction.get(key)!r}"
            ),
        )
    expected_status = component.get("required_status", "ok")
    require(
        direction.get("status") == expected_status,
        (
            f"{label} component {component.get('label', component.get('direction_id'))} status mismatch: "
            f"expected {expected_status!r}, found {direction.get('status')!r}"
        ),
    )
    configured_hash = component.get("vector_sha256")
    if configured_hash:
        require(
            direction.get("vector_sha256") == configured_hash,
            (
                f"{label} component {component.get('label', component.get('direction_id'))} vector_sha256 "
                f"mismatch: expected {configured_hash!r}, found {direction.get('vector_sha256')!r}"
            ),
        )


def validate_multi_layer_components(candidate: dict[str, Any], *, label: str) -> list[dict[str, Any]]:
    components = candidate.get("multi_layer_components")
    require(isinstance(components, list) and len(components) > 0, f"{label} multi_layer_components must be non-empty")
    summaries: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        require(isinstance(component, dict), f"{label} multi_layer_components[{index}] must be a mapping")
        direction_manifest_path = resolve_path(component["direction_manifest"])
        direction_file_path = resolve_path(component["direction_file"])
        require(direction_manifest_path.exists(), f"{label} component manifest missing: {direction_manifest_path}")
        require(direction_file_path.exists(), f"{label} component direction file missing: {direction_file_path}")
        direction_manifest = load_json(direction_manifest_path)
        direction = find_direction(direction_manifest, component["direction_id"])
        validate_component_direction_fields(component, direction, label=label)
        summaries.append(
            {
                "label": component.get("label"),
                "direction_id": component.get("direction_id"),
                "role": component.get("role"),
                "layer": component.get("layer"),
                "weight": component.get("weight", 1.0),
                "tensor_key": component.get("tensor_key", "direction"),
                "status": direction.get("status"),
                "vector_sha256": direction.get("vector_sha256"),
                "configured_vector_sha256": component.get("vector_sha256"),
                "direction_file": str(direction_file_path),
                "direction_manifest": str(direction_manifest_path),
            }
        )
    roles = {summary.get("role") for summary in summaries}
    require(len(roles) == 1, f"{label} multi_layer_components must share one role; found {sorted(roles)}")
    return summaries


def validate_candidate(
    candidate: dict[str, Any],
    readiness_checks: dict[str, Any],
) -> dict[str, Any]:
    label = candidate.get("label") or candidate.get("direction_id")
    extraction_manifest_path = resolve_path(candidate["extraction_manifest"])
    extraction_dir = resolve_path(candidate["extraction_dir"])
    rows_path = extraction_dir / "rows.jsonl"

    require(extraction_manifest_path.exists(), f"extraction manifest missing: {extraction_manifest_path}")

    extraction_manifest = load_json(extraction_manifest_path)
    expected_extraction = readiness_checks.get("require_extraction_manifest", {})
    require(
        extraction_manifest.get("status") == expected_extraction.get("status", "ok"),
        f"{label} extraction manifest status is not {expected_extraction.get('status', 'ok')}",
    )
    require(
        extraction_manifest.get("verified") is expected_extraction.get("verified", True),
        f"{label} extraction manifest verified flag is not {expected_extraction.get('verified', True)}",
    )

    row_count, label_counts = read_rows(rows_path)
    validate_row_counts(
        row_count=row_count,
        label_counts=label_counts,
        expected=expected_extraction,
        context=f"{label} rows.jsonl",
    )

    component_summaries: list[dict[str, Any]] | None = None
    if candidate.get("multi_layer_components") is not None:
        component_summaries = validate_multi_layer_components(candidate, label=label)
        direction = {
            "status": "ok",
            "vector_sha256": None,
        }
        direction_file_path = None
        direction_manifest_path = None
    else:
        direction_manifest_path = resolve_path(candidate["direction_manifest"])
        direction_file_path = resolve_path(candidate["direction_file"])
        require(direction_manifest_path.exists(), f"direction manifest missing: {direction_manifest_path}")
        require(direction_file_path.exists(), f"direction file missing: {direction_file_path}")
        direction_manifest = load_json(direction_manifest_path)
        direction = find_direction(direction_manifest, candidate["direction_id"])
        validate_direction_fields(candidate, direction)
        if "n_total" in direction:
            require(
                direction["n_total"] == row_count,
                f"{label} direction n_total mismatch: expected {row_count}, found {direction['n_total']}",
            )
        if "label_counts" in direction_manifest:
            require(
                direction_manifest["label_counts"] == label_counts,
                (
                    f"{label} direction manifest label_counts mismatch: "
                    f"expected {label_counts}, found {direction_manifest['label_counts']}"
                ),
            )
        if "n_labeled_rows" in direction_manifest:
            require(
                direction_manifest["n_labeled_rows"] == row_count,
                (
                    f"{label} direction manifest n_labeled_rows mismatch: "
                    f"expected {row_count}, found {direction_manifest['n_labeled_rows']}"
                ),
            )

    return {
        "label": label,
        "arm": candidate.get("arm"),
        "priority": candidate.get("priority"),
        "direction_id": candidate.get("direction_id"),
        "role": candidate.get("role"),
        "layer": candidate.get("layer"),
        "source_direction_layer": direction.get("layer"),
        "allow_direction_layer_override": bool(candidate.get("allow_direction_layer_override")),
        "method": candidate.get("method"),
        "contrast": candidate.get("contrast"),
        "tensor_key": candidate.get("tensor_key"),
        "status": direction.get("status"),
        "row_count": row_count,
        "label_counts": label_counts,
        "vector_sha256": direction.get("vector_sha256"),
        "configured_vector_sha256": candidate.get("vector_sha256"),
        "direction_file": str(direction_file_path) if direction_file_path is not None else None,
        "extraction_manifest": str(extraction_manifest_path),
        "direction_manifest": str(direction_manifest_path) if direction_manifest_path is not None else None,
        "multi_layer_components": component_summaries,
    }


def materialize_planned_arms(config: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    coefficients = config.get("coefficient_grid", {}).get("values", [])
    controls = config.get("controls", {}).get("required", [])
    planned: list[dict[str, Any]] = []
    for candidate in candidates:
        for coefficient in coefficients:
            for control in controls:
                if control == "no_vector_baseline":
                    effective_direction_id = None
                    effective_coefficient = 0.0
                else:
                    effective_direction_id = candidate["direction_id"]
                    effective_coefficient = coefficient
                planned.append({
                    "arm_id": (
                        f"{candidate['label']}__coef_{str(coefficient).replace('-', 'neg_').replace('.', 'p')}"
                        f"__control_{control}"
                    ),
                    "candidate_label": candidate["label"],
                    "direction_id": effective_direction_id,
                    "coefficient": effective_coefficient,
                    "grid_coefficient": coefficient,
                    "control": control,
                    "is_zero_no_vector_baseline": control == "no_vector_baseline",
                    "is_sign_flip_control": control == "sign_flip" and coefficient < 0,
                    "generation_executed": False,
                })
    return planned


def build_outputs(
    *,
    config: dict[str, Any],
    config_path: Path,
    output_root: Path,
    candidate_summaries: list[dict[str, Any]],
    planned_arms: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    metrics_plan = {
        "primary": config.get("metrics", {}).get("primary", []),
        "contamination": config.get("metrics", {}).get("contamination", []),
        "classification_notes": config.get("metrics", {}).get("classification_notes", {}),
        "generation_executed": False,
    }
    manifest = {
        "dry_run": True,
        "generation_executed": False,
        "evidence_tier_current": config.get("spec", {}).get("evidence_tier_current"),
        "evidence_tier_if_intervention_runs": config.get("spec", {}).get(
            "evidence_tier_if_intervention_runs"
        ),
        "config_path": str(config_path.resolve()),
        "output_root": str(output_root.resolve()),
        "candidate_summaries": candidate_summaries,
        "row_counts": {
            item["label"]: {
                "row_count": item["row_count"],
                "label_counts": item["label_counts"],
            }
            for item in candidate_summaries
        },
        "controls": config.get("controls", {}),
        "metrics": config.get("metrics", {}),
        "stop_conditions": config.get("stop_conditions", []),
        "planned_arm_count": len(planned_arms),
        "output_files": {
            "dry_run_manifest": config.get("output", {}).get("dry_run_manifest"),
            "planned_arms_file": config.get("output", {}).get("planned_arms_file"),
            "metrics_plan_file": config.get("output", {}).get("metrics_plan_file"),
        },
    }
    return manifest, planned_arms, metrics_plan


def write_outputs(
    *,
    output_root: Path,
    config: dict[str, Any],
    dry_run_manifest: dict[str, Any],
    planned_arms: list[dict[str, Any]],
    metrics_plan: dict[str, Any],
) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    output_config = config.get("output", {})
    outputs = [
        (output_config.get("dry_run_manifest", "dry_run_manifest.json"), dry_run_manifest),
        (output_config.get("planned_arms_file", "planned_arms.json"), planned_arms),
        (output_config.get("metrics_plan_file", "metrics_plan.json"), metrics_plan),
    ]
    written: list[Path] = []
    for filename, payload in outputs:
        path = output_root / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def run(config_path: Path, output_root_override: Path | None = None, no_write: bool = False) -> dict[str, Any]:
    config = load_yaml(config_path)
    validate_spec_guards(config)
    candidate_summaries = [
        validate_candidate(candidate, config.get("readiness_checks", {}))
        for candidate in config.get("candidate_directions", [])
    ]
    require(candidate_summaries, "candidate_directions must contain at least one entry")
    planned_arms = materialize_planned_arms(config, candidate_summaries)
    output_root = (
        output_root_override.resolve()
        if output_root_override is not None
        else resolve_path(config.get("output", {}).get("root", "mechinterp_causal_pilot_dry_run"))
    )
    dry_run_manifest, planned_arms_payload, metrics_plan = build_outputs(
        config=config,
        config_path=config_path,
        output_root=output_root,
        candidate_summaries=candidate_summaries,
        planned_arms=planned_arms,
    )
    written: list[Path] = []
    if not no_write:
        written = write_outputs(
            output_root=output_root,
            config=config,
            dry_run_manifest=dry_run_manifest,
            planned_arms=planned_arms_payload,
            metrics_plan=metrics_plan,
        )
    return {
        "ok": True,
        "no_write": no_write,
        "output_root": str(output_root),
        "written": [str(path) for path in written],
        "planned_arm_count": len(planned_arms_payload),
        "generation_executed": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="mechinterp causal-pilot no-generation dry-run validator")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args.config, args.output_root, args.no_write)
    except DryRunValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
