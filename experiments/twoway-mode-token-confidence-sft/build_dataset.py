#!/usr/bin/env python3
"""Build the two-way (ANSWER/ABSTAIN) SFT dataset by RELABELLING the frozen
Stage-S split in place.

This builder does NOT re-run the component-disjoint split. It reads the frozen
Stage-S train/dev split files (sha256-verified), keeps every row in its existing
split, and recomputes only the two-way ``mode_label`` and the rendered assistant
completion. Held-out is never opened for content (hash-only integrity), and no
output held-out file is produced: the frozen sealed held-out remains authoritative
for the future downstream experiment.

Two-way rule (AMENDMENT.md sec 3.1): ABSTAIN iff correct_count <= 10 (the existing
one-sided 95% Clopper-Pearson abstain boundary, U(10)=0.472140); ANSWER otherwise.
The only rows whose content changes are the frozen QUALIFY rows, which become
ANSWER; their supported answer text is recovered verbatim from the fixed Stage-S
QUALIFY template. Row-bearing products belong under the experiment ``analysis/``
tree and must never be committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import string
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

TWO_WAY_MODES = ("ANSWER", "ABSTAIN")
THREE_WAY_MODES = ("ANSWER", "QUALIFY", "ABSTAIN")


class ContractError(ValueError):
    """Raised when a pinned input or generated artifact violates the contract."""


@dataclass(frozen=True)
class RelabelledRow:
    split: str
    row_key: str
    mode: str            # two-way
    source_mode: str     # frozen three-way
    correct_count: int
    n_samples: int
    confidence: float
    answer_text: str | None
    system_message: str
    user_message: str
    question_id: str
    gold_aliases: list[str]
    entity_group_id: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_path(root: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root / path


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be a mapping")
    return value


def _verify_hash(path: Path, expected: str, name: str) -> str:
    if not path.is_file():
        raise ContractError(f"{name} does not exist: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ContractError(
            canonical_json(
                {
                    "error": "sha256_mismatch",
                    "input": name,
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                }
            )
        )
    return actual


def derive_abstain_boundary(n_samples: int, chance_probability: float, confidence: float) -> int:
    """Largest k whose one-sided upper binomial tail below 0.5 stays under alpha."""
    alpha = 1.0 - confidence

    def probability(count: int) -> float:
        return (
            math.comb(n_samples, count)
            * chance_probability**count
            * (1.0 - chance_probability) ** (n_samples - count)
        )

    abstain_candidates = [
        count
        for count in range(n_samples + 1)
        if sum(probability(index) for index in range(count + 1)) < alpha
    ]
    if not abstain_candidates:
        raise ContractError("configured binomial evidence rule has no abstain boundary")
    return max(abstain_candidates)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ContractError("builder config must be a mapping")
    if config.get("schema_version") != 1:
        raise ContractError("builder config schema_version must equal 1")
    if config.get("mode") != "relabel_in_place":
        raise ContractError("builder config mode must equal 'relabel_in_place'")
    for section in ("source", "labeling", "relabel", "mode_tokens", "render", "output"):
        _require_mapping(config.get(section), section)
    tokens = _require_mapping(config["mode_tokens"], "mode_tokens")
    if set(tokens) != set(TWO_WAY_MODES):
        raise ContractError(f"mode_tokens must define exactly {sorted(TWO_WAY_MODES)}")
    values = [tokens[m] for m in TWO_WAY_MODES]
    if any(not isinstance(v, str) or not v for v in values):
        raise ContractError("mode_tokens values must be non-empty strings")
    if len(set(values)) != len(values):
        raise ContractError("configured mode tokens must be unique")
    for left in values:
        for right in values:
            if left != right and right.startswith(left):
                raise ContractError(
                    f"configured mode tokens must be prefix-free; {left!r} prefixes {right!r}"
                )
    render = _require_mapping(config["render"], "render")
    answer_templates = _require_mapping(
        render.get("answer_text_templates"), "render.answer_text_templates"
    )
    if set(answer_templates) != set(TWO_WAY_MODES):
        raise ContractError(f"answer_text_templates must define exactly {sorted(TWO_WAY_MODES)}")
    if "$gold_answer" not in str(answer_templates["ANSWER"]):
        raise ContractError("ANSWER answer template must contain $gold_answer")
    if "$gold_answer" in str(answer_templates["ABSTAIN"]):
        raise ContractError("ABSTAIN answer template must not contain $gold_answer")
    return config


def _substitute(template_value: str, values: Mapping[str, str], name: str) -> str:
    try:
        return string.Template(template_value).substitute(values)
    except (KeyError, ValueError) as exc:
        raise ContractError(f"invalid or unresolved template in {name}: {exc}") from exc


def _jeffreys(correct_count: int, n_samples: int, config: Mapping[str, Any]) -> float:
    target = config["labeling"]["confidence_target"]
    if target.get("estimator") != "jeffreys_posterior_mean":
        raise ContractError("only jeffreys_posterior_mean is valid for this pinned experiment")
    alpha = float(target["alpha"])
    beta = float(target["beta"])
    return (correct_count + alpha) / (n_samples + alpha + beta)


def _extract_qualify_gold(answer_field: str, template: Mapping[str, Any]) -> str:
    prefix = str(template["prefix"])
    suffix = str(template["suffix"])
    if not (answer_field.startswith(prefix) and answer_field.endswith(suffix)):
        raise ContractError(
            canonical_json(
                {
                    "error": "qualify_template_mismatch",
                    "prefix": prefix,
                    "suffix": suffix,
                }
            )
        )
    gold = answer_field[len(prefix) : len(answer_field) - len(suffix)]
    if not gold.strip():
        raise ContractError("extracted QUALIFY gold answer is empty")
    return gold


def _load_split_rows(
    path: Path, split: str, config: Mapping[str, Any], abstain_max: int
) -> list[RelabelledRow]:
    labeling = config["labeling"]
    relabel = config["relabel"]
    qualify_template = _require_mapping(
        relabel.get("qualify_source_template"), "relabel.qualify_source_template"
    )
    assert_abstain = bool(relabel.get("assert_frozen_abstain_equals_k_le_abstain_max", True))
    assert_conf = bool(relabel.get("assert_confidence_matches_jeffreys", True))

    rows: list[RelabelledRow] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ContractError(f"invalid JSON at {split} row {line_number}: {exc}") from exc
            metadata = _require_mapping(record.get("metadata"), f"{split} row {line_number} metadata")
            conversations = record.get("conversations")
            if not isinstance(conversations, list):
                raise ContractError(f"{split} row {line_number} missing conversations")
            by_role = {c.get("role"): c.get("content") for c in conversations if isinstance(c, dict)}
            for role in ("system", "user", "assistant"):
                if role not in by_role or not isinstance(by_role[role], str):
                    raise ContractError(f"{split} row {line_number} missing {role} turn")

            row_key = metadata.get("row_key")
            if not isinstance(row_key, str) or not row_key:
                raise ContractError(f"{split} row {line_number} missing row_key")
            if row_key in seen:
                raise ContractError(f"duplicate row_key at {split} row {line_number}")
            seen.add(row_key)

            correct_count = metadata.get("correct_count")
            n_samples = metadata.get("n_samples")
            source_mode = metadata.get("mode_label")
            confidence = metadata.get("answer_confidence")
            if not isinstance(correct_count, int) or isinstance(correct_count, bool):
                raise ContractError(f"{split} row {line_number} correct_count not int")
            if not isinstance(n_samples, int) or n_samples <= 0:
                raise ContractError(f"{split} row {line_number} n_samples invalid")
            if source_mode not in THREE_WAY_MODES:
                raise ContractError(f"{split} row {line_number} unexpected source mode {source_mode!r}")
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
                raise ContractError(f"{split} row {line_number} answer_confidence not numeric")

            # Two-way label + integrity assertions.
            mode = "ABSTAIN" if correct_count <= abstain_max else "ANSWER"
            if assert_abstain and (mode == "ABSTAIN") != (source_mode == "ABSTAIN"):
                raise ContractError(
                    canonical_json(
                        {
                            "error": "frozen_abstain_not_equal_k_le_abstain_max",
                            "split": split,
                            "line": line_number,
                            "correct_count": correct_count,
                            "source_mode": source_mode,
                            "abstain_max": abstain_max,
                        }
                    )
                )
            if assert_conf:
                expected_conf = _jeffreys(correct_count, n_samples, config)
                if not math.isclose(float(confidence), expected_conf, abs_tol=1e-9):
                    raise ContractError(
                        f"{split} row {line_number} answer_confidence {confidence} != jeffreys {expected_conf}"
                    )

            # Recover the answer text for ANSWER rows from the frozen assistant turn.
            answer_text: str | None = None
            if mode == "ANSWER":
                assistant = by_role["assistant"]
                brace = assistant.find("{")
                if brace < 0:
                    raise ContractError(f"{split} row {line_number} assistant has no JSON payload")
                try:
                    payload = json.loads(assistant[brace:])
                except json.JSONDecodeError as exc:
                    raise ContractError(f"{split} row {line_number} bad assistant JSON") from exc
                field = payload.get("answer")
                if not isinstance(field, str) or not field:
                    raise ContractError(f"{split} row {line_number} assistant answer missing")
                if source_mode == "QUALIFY":
                    answer_text = _extract_qualify_gold(field, qualify_template)
                else:  # frozen ANSWER: raw gold answer already present
                    answer_text = field

            rows.append(
                RelabelledRow(
                    split=split,
                    row_key=row_key,
                    mode=mode,
                    source_mode=source_mode,
                    correct_count=correct_count,
                    n_samples=n_samples,
                    confidence=float(confidence),
                    answer_text=answer_text,
                    system_message=by_role["system"],
                    user_message=by_role["user"],
                    question_id=str(metadata.get("question_id", "")),
                    gold_aliases=list(metadata.get("gold_aliases", [])),
                    entity_group_id=str(metadata.get("entity_group_id", "")),
                )
            )
    return rows


def render_record(row: RelabelledRow, config: Mapping[str, Any]) -> dict[str, Any]:
    render = config["render"]
    tokens = config["mode_tokens"]
    token = tokens[row.mode]
    if row.mode == "ANSWER":
        answer_text = _substitute(
            render["answer_text_templates"]["ANSWER"],
            {"gold_answer": row.answer_text or ""},
            "answer_text_templates.ANSWER",
        )
    else:
        answer_text = str(render["answer_text_templates"]["ABSTAIN"])
    json_payload = canonical_json({"answer": answer_text, "answer_confidence": row.confidence})
    assistant_output = _substitute(
        render["assistant_output_template"],
        {"mode_token": token, "json_payload": json_payload},
        "assistant_output_template",
    )
    if not assistant_output.startswith(token):
        raise ContractError("rendered assistant output does not start with the configured mode token")
    occurrences = {candidate: assistant_output.count(candidate) for candidate in tokens.values()}
    if occurrences[token] != 1 or any(v for k, v in occurrences.items() if k != token):
        raise ContractError(
            canonical_json({"error": "rendered_mode_token_collision", "occurrences": occurrences})
        )
    remainder = assistant_output[len(token) :]
    payload = json.loads(remainder)
    if set(payload) != set(render["output_json"]["required_fields"]):
        raise ContractError("rendered JSON fields do not match the configured output contract")
    if row.mode == "ABSTAIN" and row.answer_text:
        raise ContractError("ABSTAIN row unexpectedly carries a gold answer")
    metadata = {
        "row_key": row.row_key,
        "question_id": row.question_id,
        "correct_count": row.correct_count,
        "n_samples": row.n_samples,
        "answer_confidence": row.confidence,
        "mode_label": row.mode,
        "source_mode_label": row.source_mode,
        "entity_group_id": row.entity_group_id,
        "split": row.split,
        "gold_aliases": row.gold_aliases,
    }
    return {
        "conversations": [
            {"role": "system", "content": row.system_message},
            {"role": "user", "content": row.user_message},
            {"role": "assistant", "content": assistant_output},
        ],
        "metadata": metadata,
    }


def _write_jsonl_atomic(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            for record in records:
                handle.write(canonical_json(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def build_dataset(config_path: Path, *, source_root: Path | None = None) -> dict[str, Any]:
    config_path = config_path.resolve()
    project_root = config_path.parents[2]
    source_root = source_root.resolve() if source_root else project_root
    config = load_config(config_path)

    labeling = config["labeling"]
    abstain_max = derive_abstain_boundary(
        int(config["source"]["identity"]["n_samples"]),
        float(labeling["chance_probability"]),
        float(labeling["one_sided_confidence"]),
    )
    configured_abstain_max = int(labeling["clopper_pearson_boundaries"]["abstain_max_correct"])
    if abstain_max != configured_abstain_max:
        raise ContractError(
            canonical_json(
                {
                    "error": "abstain_boundary_mismatch",
                    "derived": abstain_max,
                    "configured": configured_abstain_max,
                }
            )
        )

    # Provenance: verify the canonical scorer bytes (lineage parity with Stage-S)
    # even though the relabel does not normalize.
    scorer = config["source"]["canonical_scorer"]
    _verify_hash(_resolve_path(project_root, scorer["path"]), scorer["sha256"], "canonical_scorer")

    frozen = config["source"]["frozen_split"]
    frozen_dir = _resolve_path(source_root, frozen["directory"])
    source_shas: dict[str, str] = {}
    # Hash-verify every frozen file (integrity), including held-out (bytes only,
    # never parsed).
    for split in ("train", "dev", "heldout"):
        spec = frozen[split]
        source_shas[split] = _verify_hash(
            frozen_dir / spec["file"], spec["sha256"], f"frozen_{split}"
        )

    by_split: dict[str, list[RelabelledRow]] = {}
    for split in ("train", "dev"):
        rows = _load_split_rows(frozen_dir / frozen[split]["file"], split, config, abstain_max)
        if len(rows) != int(frozen[split]["rows"]):
            raise ContractError(
                canonical_json(
                    {
                        "error": "row_count_mismatch",
                        "split": split,
                        "expected": int(frozen[split]["rows"]),
                        "actual": len(rows),
                    }
                )
            )
        rows.sort(key=lambda r: r.row_key)
        by_split[split] = rows

    output_config = config["output"]
    output_directory = _resolve_path(project_root, output_config["directory"]).resolve()
    private_output_root = (config_path.parent / "analysis").resolve()
    try:
        output_directory.relative_to(private_output_root)
    except ValueError as exc:
        raise ContractError(
            "output.directory must resolve beneath this experiment's ignored analysis/ directory"
        ) from exc
    output_directory.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, Any] = {}
    mode_counts: dict[str, dict[str, int]] = {}
    for split, rows in by_split.items():
        path = output_directory / output_config["files"][split]
        _write_jsonl_atomic(path, (render_record(row, config) for row in rows))
        outputs[split] = {"file": path.name, "rows": len(rows), "sha256": sha256_file(path)}
        mode_counts[split] = dict(sorted(Counter(r.mode for r in rows).items()))

    aggregate = {
        "schema_version": 1,
        "builder": "relabel_in_place_two_way",
        "builder_config_sha256": sha256_file(config_path),
        "source_frozen_split_sha256": source_shas,
        "label_rule": {
            "abstain_max_correct": abstain_max,
            "answer_rule": "correct_count > abstain_max",
            "answer_confidence": "(correct_count + 0.5) / 33",
        },
        "mode_counts": mode_counts,
        "held_out": {
            "sha256": source_shas["heldout"],
            "access": "hash_only_never_parsed_sealed_carried_forward",
            "rows_parsed": 0,
        },
        "outputs": outputs,
    }
    manifest_path = output_directory / output_config["files"]["aggregate_manifest"]
    _write_jsonl_atomic(manifest_path, [aggregate])
    aggregate["aggregate_manifest_sha256"] = sha256_file(manifest_path)
    return aggregate


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("dataset_builder.yaml"),
    )
    parser.add_argument("--source-root", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        aggregate = build_dataset(args.config, source_root=args.source_root)
    except (ContractError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"dataset build failed: {exc}", file=sys.stderr)
        return 2
    print(canonical_json(aggregate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
