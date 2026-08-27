#!/usr/bin/env python3
"""Build the private mode-token SFT dataset from the frozen Qwen3 probe cache.

The builder is deliberately fail-closed: source bytes, manifest provenance, row
schema, label boundaries, group leakage, and split quality are all verified
before any output is replaced. Row-bearing products belong under the experiment
``analysis/`` tree and must never be committed.
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
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, Mapping

import yaml

# Direct ``python experiments/<slug>/build_dataset.py`` execution places only
# the experiment directory on sys.path. Add this checked-in script's repo root
# so normalization is imported from the canonical probe scorer below.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.common.knowledge_probe import scoring as canonical_scoring

normalize_answer = canonical_scoring.normalize_answer
normalize_question = canonical_scoring.normalize_question
IMPORTED_SCORER_PATH = Path(canonical_scoring.__file__).resolve()


MODES = ("ANSWER", "QUALIFY", "ABSTAIN")


class ContractError(ValueError):
    """Raised when a pinned input or generated artifact violates the contract."""


@dataclass(frozen=True)
class PreparedRow:
    source: dict[str, Any]
    mode: str
    correct_count: int
    confidence: float
    identities: frozenset[str]
    group_id: str = ""


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[self.parent[index]]
            index = self.parent[index]
        return index

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


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


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ContractError("builder config must be a mapping")
    if config.get("schema_version") != 1:
        raise ContractError("builder config schema_version must equal 1")
    for section in ("source", "labeling", "mode_tokens", "render", "splits", "output"):
        _require_mapping(config.get(section), section)
    scorer = _require_mapping(
        config["source"].get("canonical_scorer"), "source.canonical_scorer"
    )
    if not isinstance(scorer.get("path"), str) or not scorer["path"]:
        raise ContractError("source.canonical_scorer.path must be a non-empty string")
    scorer_sha = scorer.get("sha256")
    if not isinstance(scorer_sha, str) or len(scorer_sha) != 64:
        raise ContractError("source.canonical_scorer.sha256 must be a 64-character string")
    try:
        int(scorer_sha, 16)
    except ValueError as exc:
        raise ContractError("source.canonical_scorer.sha256 must be hexadecimal") from exc
    validate_mode_config(config)
    validate_split_config(config)
    return config


def validate_mode_config(config: Mapping[str, Any]) -> None:
    tokens = _require_mapping(config["mode_tokens"], "mode_tokens")
    if set(tokens) != set(MODES):
        raise ContractError(f"mode_tokens must define exactly {sorted(MODES)}")
    values = []
    for mode in MODES:
        token = tokens[mode]
        if not isinstance(token, str) or not token:
            raise ContractError(f"mode_tokens.{mode} must be a non-empty string")
        values.append(token)
    if len(set(values)) != len(values):
        raise ContractError("configured mode tokens must be unique")
    for left in values:
        for right in values:
            if left != right and right.startswith(left):
                raise ContractError(
                    "configured mode tokens must be prefix-free; "
                    f"{left!r} is a prefix of {right!r}"
                )

    render = _require_mapping(config["render"], "render")
    answer_templates = _require_mapping(
        render.get("answer_text_templates"), "render.answer_text_templates"
    )
    if set(answer_templates) != set(MODES):
        raise ContractError(f"answer_text_templates must define exactly {sorted(MODES)}")
    output_template = render.get("assistant_output_template")
    if not isinstance(output_template, str):
        raise ContractError("render.assistant_output_template must be a string")
    if output_template.count("$mode_token") != 1 or output_template.count("$json_payload") != 1:
        raise ContractError(
            "assistant_output_template must contain $mode_token and $json_payload exactly once"
        )
    if not output_template.startswith("$mode_token"):
        raise ContractError("assistant_output_template must begin with $mode_token")
    user_template = render.get("user_message_template")
    if not isinstance(user_template, str) or user_template.count("$question") != 1:
        raise ContractError("user_message_template must contain $question exactly once")
    for mode, template_value in answer_templates.items():
        if not isinstance(template_value, str):
            raise ContractError(f"answer_text_templates.{mode} must be a string")
        if mode == "ABSTAIN" and "$gold_answer" in template_value:
            raise ContractError("ABSTAIN answer template must not contain $gold_answer")
        if mode != "ABSTAIN" and template_value.count("$gold_answer") != 1:
            raise ContractError(
                f"answer_text_templates.{mode} must contain $gold_answer exactly once"
            )


def validate_split_config(config: Mapping[str, Any]) -> None:
    split_config = _require_mapping(config["splits"], "splits")
    targets = _require_mapping(
        split_config.get("evaluation_targets_per_mode"),
        "splits.evaluation_targets_per_mode",
    )
    if tuple(targets) != ("dev", "heldout"):
        raise ContractError("evaluation targets must be declared in dev, heldout order")
    for split, mode_targets in targets.items():
        mode_targets = _require_mapping(
            mode_targets, f"splits.evaluation_targets_per_mode.{split}"
        )
        if set(mode_targets) != set(MODES):
            raise ContractError(f"{split} targets must define exactly {sorted(MODES)}")
        for mode, value in mode_targets.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ContractError(f"evaluation target {split}.{mode} must be a positive integer")
    if not isinstance(split_config.get("seed"), int):
        raise ContractError("splits.seed must be an integer")
    group_fraction = split_config.get("max_group_fraction")
    if (
        isinstance(group_fraction, bool)
        or not isinstance(group_fraction, (int, float))
        or not 0 < group_fraction < 1
    ):
        raise ContractError("splits.max_group_fraction must be between 0 and 1")
    count_deviation = split_config.get("max_absolute_mode_count_deviation")
    if isinstance(count_deviation, bool) or not isinstance(count_deviation, int) or count_deviation < 0:
        raise ContractError("splits.max_absolute_mode_count_deviation must be a non-negative integer")
    wilson_confidence = split_config.get("wilson_confidence")
    if (
        isinstance(wilson_confidence, bool)
        or not isinstance(wilson_confidence, (int, float))
        or not 0 < wilson_confidence < 1
    ):
        raise ContractError("splits.wilson_confidence must be between 0 and 1")


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


def verify_canonical_scorer(
    path: Path,
    expected_sha256: str,
    *,
    imported_path: Path | None = None,
) -> str:
    """Verify scorer bytes and, in production, that they are the imported module."""
    resolved = path.resolve()
    actual = _verify_hash(resolved, expected_sha256, "canonical_scorer")
    if imported_path is not None and resolved != imported_path.resolve():
        raise ContractError(
            canonical_json(
                {
                    "error": "canonical_scorer_import_path_mismatch",
                    "configured_path": str(resolved),
                    "imported_path": str(imported_path.resolve()),
                }
            )
        )
    return actual


def validate_manifest(manifest: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    identity = _require_mapping(config["source"]["identity"], "source.identity")
    sampling = _require_mapping(manifest.get("sampling"), "probe manifest sampling")
    checks = {
        "model_name": (manifest.get("model_name"), identity["model_name"]),
        "model_tag": (manifest.get("model_tag"), identity["model_tag"]),
        "probe_config_sha": (manifest.get("probe_config_sha"), identity["probe_config_sha"]),
        "n_questions": (
            manifest.get("n_questions"),
            config["source"]["probe_results"]["expected_rows"],
        ),
        "sampling.n_samples": (sampling.get("n_samples"), identity["n_samples"]),
        "sampling.temperature": (sampling.get("temperature"), identity["temperature"]),
        "sampling.top_p": (sampling.get("top_p"), identity["top_p"]),
        "sampling.seed": (sampling.get("seed"), identity["seed"]),
        "enable_thinking": (manifest.get("enable_thinking"), identity["enable_thinking"]),
    }
    mismatches = {
        field: {"actual": actual, "expected": expected}
        for field, (actual, expected) in checks.items()
        if actual != expected
    }
    if mismatches:
        raise ContractError(canonical_json({"error": "manifest_identity_mismatch", "fields": mismatches}))


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "list_string":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if expected == "list_boolean":
        return isinstance(value, list) and all(isinstance(item, bool) for item in value)
    raise ContractError(f"unsupported required schema type {expected!r}")


def derive_exact_boundaries(n_samples: int, chance_probability: float, confidence: float) -> tuple[int, int]:
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
    answer_candidates = [
        count
        for count in range(n_samples + 1)
        if sum(probability(index) for index in range(count, n_samples + 1)) < alpha
    ]
    if not abstain_candidates or not answer_candidates:
        raise ContractError("configured binomial evidence rule has no qualifying boundary")
    return max(abstain_candidates), min(answer_candidates)


def validate_label_contract(config: Mapping[str, Any]) -> tuple[int, int]:
    identity = config["source"]["identity"]
    labeling = config["labeling"]
    derived = derive_exact_boundaries(
        int(identity["n_samples"]),
        float(labeling["chance_probability"]),
        float(labeling["one_sided_confidence"]),
    )
    configured = labeling["clopper_pearson_boundaries"]
    expected = (int(configured["abstain_max_correct"]), int(configured["answer_min_correct"]))
    if derived != expected:
        raise ContractError(
            canonical_json(
                {
                    "error": "clopper_pearson_boundary_mismatch",
                    "derived": {"abstain_max_correct": derived[0], "answer_min_correct": derived[1]},
                    "configured": {"abstain_max_correct": expected[0], "answer_min_correct": expected[1]},
                }
            )
        )
    return derived


def classify(correct_count: int, greedy_correct: bool, abstain_max: int, answer_min: int) -> str:
    if correct_count <= abstain_max:
        return "ABSTAIN"
    if correct_count >= answer_min and greedy_correct:
        return "ANSWER"
    return "QUALIFY"


def _confidence(correct_count: int, n_samples: int, config: Mapping[str, Any]) -> float:
    target = config["labeling"]["confidence_target"]
    if target.get("estimator") != "jeffreys_posterior_mean":
        raise ContractError("only jeffreys_posterior_mean is valid for this pinned experiment")
    alpha = float(target["alpha"])
    beta = float(target["beta"])
    if alpha <= 0 or beta <= 0:
        raise ContractError("Jeffreys prior parameters must be positive")
    return (correct_count + alpha) / (n_samples + alpha + beta)


def load_rows(path: Path, config: Mapping[str, Any]) -> list[PreparedRow]:
    expected_schema = _require_mapping(
        config["source"]["required_row_schema"], "source.required_row_schema"
    )
    identity = config["source"]["identity"]
    expected_rows = int(config["source"]["probe_results"]["expected_rows"])
    n_samples = int(identity["n_samples"])
    abstain_max, answer_min = validate_label_contract(config)
    prepared: list[PreparedRow] = []
    seen_row_keys: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ContractError(f"invalid JSON at probe row {line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ContractError(f"probe row {line_number} must be an object")
            failures = {
                field: expected_type
                for field, expected_type in expected_schema.items()
                if field not in row or not _matches_type(row[field], str(expected_type))
            }
            if failures:
                raise ContractError(
                    canonical_json(
                        {
                            "error": "row_schema_mismatch",
                            "line": line_number,
                            "fields": failures,
                        }
                    )
                )
            if row["model_tag"] != identity["model_tag"] or row["probe_config_sha"] != identity["probe_config_sha"]:
                raise ContractError(f"probe identity mismatch at row {line_number}")
            if row["n_samples"] != n_samples or len(row["sampled_correct"]) != n_samples:
                raise ContractError(f"sample-count mismatch at row {line_number}")
            expected_question_norm = normalize_question(row["question"])
            if row["question_norm"] != expected_question_norm:
                raise ContractError(
                    canonical_json(
                        {
                            "error": "question_norm_mismatch",
                            "line": line_number,
                            "row_key_sha256": hashlib.sha256(
                                row["probe_pool_row_key"].encode("utf-8")
                            ).hexdigest(),
                        }
                    )
                )

            row_key = row["probe_pool_row_key"]
            if row_key in seen_row_keys:
                raise ContractError(f"duplicate probe_pool_row_key at row {line_number}")
            seen_row_keys.add(row_key)

            correct_count = sum(row["sampled_correct"])
            if not math.isclose(float(row["p_correct"]), correct_count / n_samples, abs_tol=1e-12):
                raise ContractError(f"p_correct disagrees with sampled_correct at row {line_number}")
            mode = classify(correct_count, row["greedy_correct"], abstain_max, answer_min)
            values = [row["answer_value"], *row["normalized_aliases"]]
            identities = frozenset(filter(None, (normalize_answer(value) for value in values)))
            if not identities:
                raise ContractError(f"row {line_number} has no non-empty normalized answer identity")
            prepared.append(
                PreparedRow(
                    source=row,
                    mode=mode,
                    correct_count=correct_count,
                    confidence=_confidence(correct_count, n_samples, config),
                    identities=identities,
                )
            )

    if len(prepared) != expected_rows:
        raise ContractError(
            canonical_json(
                {
                    "error": "row_count_mismatch",
                    "expected": expected_rows,
                    "actual": len(prepared),
                }
            )
        )
    return prepared


def attach_entity_groups(rows: list[PreparedRow]) -> list[PreparedRow]:
    union_find = UnionFind(len(rows))
    owner_by_identity: dict[str, int] = {}
    owner_by_question_id: dict[str, int] = {}
    owner_by_question_norm: dict[str, int] = {}
    for index, row in enumerate(rows):
        question_owner = owner_by_question_id.setdefault(row.source["question_id"], index)
        union_find.union(index, question_owner)
        normalized_question_owner = owner_by_question_norm.setdefault(
            row.source["question_norm"], index
        )
        union_find.union(index, normalized_question_owner)
        for identity in sorted(row.identities):
            owner = owner_by_identity.setdefault(identity, index)
            union_find.union(index, owner)

    members: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        members[union_find.find(index)].append(index)

    group_ids: dict[int, str] = {}
    for root, indices in members.items():
        identities = sorted({identity for index in indices for identity in rows[index].identities})
        group_ids[root] = hashlib.sha256("\n".join(identities).encode("utf-8")).hexdigest()[:24]

    return [
        PreparedRow(
            source=row.source,
            mode=row.mode,
            correct_count=row.correct_count,
            confidence=row.confidence,
            identities=row.identities,
            group_id=group_ids[union_find.find(index)],
        )
        for index, row in enumerate(rows)
    ]


def _stable_tie(seed: int, *parts: str) -> str:
    return hashlib.sha256((str(seed) + "|" + "|".join(parts)).encode("utf-8")).hexdigest()


def wilson_half_width_at_half(sample_size: int, confidence: float) -> float:
    """Worst-case Wilson score half-width (attained near p=0.5)."""
    if sample_size <= 0:
        raise ContractError("Wilson sample size must be positive")
    z_value = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    denominator = 1.0 + z_value**2 / sample_size
    return (
        z_value
        * math.sqrt(0.25 / sample_size + z_value**2 / (4.0 * sample_size**2))
        / denominator
    )


def allocate_groups(rows: list[PreparedRow], config: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    split_config = config["splits"]
    split_names = ("train", "dev", "heldout")
    seed = int(split_config["seed"])
    total_by_mode = Counter(row.mode for row in rows)
    evaluation_targets = {
        split: {mode: int(value) for mode, value in mode_targets.items()}
        for split, mode_targets in split_config["evaluation_targets_per_mode"].items()
    }
    target_classes = {
        "dev": evaluation_targets["dev"],
        "heldout": evaluation_targets["heldout"],
        "train": {
            mode: total_by_mode[mode]
            - evaluation_targets["dev"][mode]
            - evaluation_targets["heldout"][mode]
            for mode in MODES
        },
    }
    if any(target_classes["train"][mode] <= 0 for mode in MODES):
        raise ContractError(
            canonical_json(
                {
                    "error": "evaluation_targets_exhaust_mode",
                    "total_mode_counts": dict(total_by_mode),
                    "evaluation_targets_per_mode": evaluation_targets,
                }
            )
        )
    target_rows = {
        split: sum(target_classes[split][mode] for mode in MODES) for split in split_names
    }

    groups: dict[str, list[PreparedRow]] = defaultdict(list)
    for row in rows:
        groups[row.group_id].append(row)
    largest_group = max(len(group) for group in groups.values())
    largest_group_fraction = largest_group / len(rows)
    if largest_group_fraction > float(split_config["max_group_fraction"]):
        largest = sorted(
            (
                {
                    "group_id": group_id,
                    "size": len(group),
                    "class_counts": dict(sorted(Counter(row.mode for row in group).items())),
                }
                for group_id, group in groups.items()
            ),
            key=lambda item: (-item["size"], item["group_id"]),
        )[:10]
        raise ContractError(
            canonical_json(
                {
                    "error": "pathological_entity_groups",
                    "max_group_fraction_allowed": split_config["max_group_fraction"],
                    "largest_group_fraction": largest_group_fraction,
                    "largest_groups": largest,
                }
            )
        )

    group_summaries = []
    for group_id, members in groups.items():
        counts = Counter(row.mode for row in members)
        rarity = max(counts[mode] / total_by_mode[mode] for mode in MODES if counts[mode])
        group_summaries.append((group_id, len(members), counts, rarity))
    group_summaries.sort(key=lambda item: (-item[3], -item[1], _stable_tie(seed, item[0])))

    assigned_rows = Counter()
    assigned_classes = {split: Counter() for split in split_names}
    assignment: dict[str, str] = {}

    def objective(candidate_split: str, group_size: int, group_counts: Counter[str]) -> float:
        score = 0.0
        for split in split_names:
            row_count = assigned_rows[split] + (group_size if split == candidate_split else 0)
            score += 0.25 * ((row_count - target_rows[split]) / max(target_rows[split], 1.0)) ** 2
            for mode in MODES:
                count = assigned_classes[split][mode]
                if split == candidate_split:
                    count += group_counts[mode]
                target = target_classes[split][mode]
                score += ((count - target) / max(target, 1.0)) ** 2
        return score

    for group_id, group_size, group_counts, _ in group_summaries:
        candidates = [
            (
                round(objective(split, group_size, group_counts), 15),
                _stable_tie(seed, group_id, split),
                split,
            )
            for split in split_names
        ]
        _, _, selected = min(candidates)
        assignment[group_id] = selected
        assigned_rows[selected] += group_size
        assigned_classes[selected].update(group_counts)

    def global_objective() -> float:
        score = 0.0
        for split in split_names:
            score += 0.25 * (
                (assigned_rows[split] - target_rows[split]) / max(target_rows[split], 1.0)
            ) ** 2
            for mode in MODES:
                target = target_classes[split][mode]
                score += (
                    (assigned_classes[split][mode] - target) / max(target, 1.0)
                ) ** 2
        return score

    # The construction pass handles large/rare groups first. A deterministic
    # local refinement then corrects its myopia by moving whole groups only.
    # Every accepted move strictly decreases the same global stratification
    # objective, so the procedure cannot cycle or silently relax leakage.
    refinement_passes = 0
    refinement_moves = 0
    for pass_index in range(25):
        moves_this_pass = 0
        for group_id, group_size, group_counts, _ in group_summaries:
            current = assignment[group_id]
            current_score = global_objective()
            assigned_rows[current] -= group_size
            assigned_classes[current].subtract(group_counts)
            candidates = []
            for split in split_names:
                assigned_rows[split] += group_size
                assigned_classes[split].update(group_counts)
                score = global_objective()
                assigned_rows[split] -= group_size
                assigned_classes[split].subtract(group_counts)
                candidates.append((round(score, 15), _stable_tie(seed, group_id, split), split))
            best_score, _, selected = min(candidates)
            if best_score >= current_score - 1e-15:
                selected = current
            assigned_rows[selected] += group_size
            assigned_classes[selected].update(group_counts)
            assignment[group_id] = selected
            if selected != current:
                moves_this_pass += 1
        refinement_passes = pass_index + 1
        refinement_moves += moves_this_pass
        if moves_this_pass == 0:
            break

    class_count_deviations: dict[str, dict[str, int]] = {}
    worst_evaluation_deviation = 0
    for split in split_names:
        class_count_deviations[split] = {}
        for mode in MODES:
            deviation = assigned_classes[split][mode] - target_classes[split][mode]
            class_count_deviations[split][mode] = deviation
            if split != "train":
                worst_evaluation_deviation = max(worst_evaluation_deviation, abs(deviation))
    allowed_deviation = int(split_config["max_absolute_mode_count_deviation"])
    if worst_evaluation_deviation > allowed_deviation or any(
        assigned_classes[split][mode] == 0 for split in split_names for mode in MODES
    ):
        raise ContractError(
            canonical_json(
                {
                    "error": "entity_group_stratification_infeasible",
                    "allowed_absolute_mode_count_deviation": allowed_deviation,
                    "worst_evaluation_mode_count_deviation": worst_evaluation_deviation,
                    "target_class_counts": target_classes,
                    "split_class_counts": {
                        split: dict(sorted(assigned_classes[split].items())) for split in split_names
                    },
                    "class_count_deviations": class_count_deviations,
                    "group_count": len(groups),
                    "largest_group_size": largest_group,
                }
            )
        )

    mixed_group_ids = {
        group_id for group_id, _, counts, _ in group_summaries if sum(value > 0 for value in counts.values()) > 1
    }
    wilson_confidence = float(split_config["wilson_confidence"])
    diagnostic = {
        "group_count": len(groups),
        "mixed_group_count": len(mixed_group_ids),
        "mixed_group_split_counts": dict(
            Counter(assignment[group_id] for group_id in mixed_group_ids)
        ),
        "largest_group_size": largest_group,
        "largest_group_fraction": largest_group_fraction,
        "split_row_counts": dict(assigned_rows),
        "target_class_counts": target_classes,
        "split_class_counts": {
            split: {mode: assigned_classes[split][mode] for mode in MODES} for split in split_names
        },
        "class_count_deviations": class_count_deviations,
        "worst_evaluation_mode_count_deviation": worst_evaluation_deviation,
        "wilson_confidence": wilson_confidence,
        "wilson_worst_case_half_width": {
            split: {
                mode: wilson_half_width_at_half(assigned_classes[split][mode], wilson_confidence)
                for mode in MODES
            }
            for split in ("dev", "heldout")
        },
        "refinement_passes": refinement_passes,
        "refinement_moves": refinement_moves,
    }
    return assignment, diagnostic


def assert_identity_disjoint(rows: Iterable[PreparedRow], assignment: Mapping[str, str]) -> None:
    owner_by_identity: dict[str, str] = {}
    owner_by_question_norm: dict[str, str] = {}
    conflicts: list[dict[str, str]] = []
    question_conflicts: list[dict[str, str]] = []
    for row in rows:
        split = assignment[row.group_id]
        question_norm = row.source["question_norm"]
        previous_question_split = owner_by_question_norm.setdefault(question_norm, split)
        if previous_question_split != split:
            question_conflicts.append(
                {
                    "question_norm_sha256": hashlib.sha256(
                        question_norm.encode("utf-8")
                    ).hexdigest(),
                    "left": previous_question_split,
                    "right": split,
                }
            )
        for identity in row.identities:
            previous = owner_by_identity.setdefault(identity, split)
            if previous != split:
                conflicts.append({"identity_sha256": hashlib.sha256(identity.encode()).hexdigest(), "left": previous, "right": split})
    if conflicts or question_conflicts:
        raise ContractError(
            canonical_json(
                {
                    "error": "component_identity_leakage",
                    "answer_alias_conflict_count": len(conflicts),
                    "question_norm_conflict_count": len(question_conflicts),
                    "answer_alias_examples": conflicts[:10],
                    "question_norm_examples": question_conflicts[:10],
                }
            )
        )


def _substitute(template_value: str, values: Mapping[str, str], name: str) -> str:
    try:
        return string.Template(template_value).substitute(values)
    except (KeyError, ValueError) as exc:
        raise ContractError(f"invalid or unresolved template in {name}: {exc}") from exc


def render_record(row: PreparedRow, split: str, config: Mapping[str, Any]) -> dict[str, Any]:
    render = config["render"]
    tokens = config["mode_tokens"]
    token = tokens[row.mode]
    question = row.source["question"]
    user_message = _substitute(render["user_message_template"], {"question": question}, "user_message_template")
    metadata = {
        "row_key": row.source["probe_pool_row_key"],
        "question_id": row.source["question_id"],
        "correct_count": row.correct_count,
        "n_samples": row.source["n_samples"],
        "answer_confidence": row.confidence,
        "mode_label": row.mode,
        "entity_group_id": row.group_id,
        "split": split,
        "gold_aliases": sorted(row.identities),
    }
    conversations = [
        {"role": "system", "content": render["system_message"]},
        {"role": "user", "content": user_message},
    ]
    record = {"conversations": conversations, "metadata": metadata}
    if split == "heldout":
        return record

    answer_text = _substitute(
        render["answer_text_templates"][row.mode],
        {"gold_answer": row.source["answer_value"]},
        f"answer_text_templates.{row.mode}",
    )
    json_payload = canonical_json(
        {"answer": answer_text, "answer_confidence": row.confidence}
    )
    assistant_output = _substitute(
        render["assistant_output_template"],
        {"mode_token": token, "json_payload": json_payload},
        "assistant_output_template",
    )
    if not assistant_output.startswith(token):
        raise ContractError("rendered assistant output does not start with the configured mode token")
    token_occurrences = {candidate: assistant_output.count(candidate) for candidate in tokens.values()}
    if token_occurrences[token] != 1 or any(
        count for candidate, count in token_occurrences.items() if candidate != token
    ):
        raise ContractError(
            canonical_json(
                {
                    "error": "rendered_mode_token_collision",
                    "row_key_sha256": hashlib.sha256(metadata["row_key"].encode()).hexdigest(),
                    "mode": row.mode,
                    "occurrence_counts": token_occurrences,
                }
            )
        )
    remainder = assistant_output[len(token) :]
    try:
        payload = json.loads(remainder)
    except json.JSONDecodeError as exc:
        raise ContractError("assistant output after the configured token is not valid JSON") from exc
    required_fields = render["output_json"]["required_fields"]
    if set(payload) != set(required_fields):
        raise ContractError("rendered JSON fields do not match the configured output contract")
    if row.mode == "ABSTAIN" and row.source["answer_value"] in payload["answer"]:
        raise ContractError("ABSTAIN completion leaked the gold answer")
    record["conversations"].append({"role": "assistant", "content": assistant_output})
    return record


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


def _write_json_atomic(path: Path, value: Any) -> None:
    _write_jsonl_atomic(path, [value])


def build_dataset(config_path: Path, *, source_root: Path | None = None) -> dict[str, Any]:
    config_path = config_path.resolve()
    project_root = config_path.parents[2]
    source_root = source_root.resolve() if source_root else project_root
    config = load_config(config_path)
    source = config["source"]
    scorer_config = source["canonical_scorer"]
    scorer_path = _resolve_path(project_root, scorer_config["path"])
    scorer_sha = verify_canonical_scorer(
        scorer_path,
        scorer_config["sha256"],
        imported_path=IMPORTED_SCORER_PATH,
    )
    probe_results_path = _resolve_path(source_root, source["probe_results"]["path"])
    probe_manifest_path = _resolve_path(source_root, source["probe_manifest"]["path"])
    results_sha = _verify_hash(
        probe_results_path, source["probe_results"]["sha256"], "probe_results"
    )
    manifest_sha = _verify_hash(
        probe_manifest_path, source["probe_manifest"]["sha256"], "probe_manifest"
    )
    with probe_manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    validate_manifest(manifest, config)

    rows = attach_entity_groups(load_rows(probe_results_path, config))
    assignment, split_diagnostic = allocate_groups(rows, config)
    assert_identity_disjoint(rows, assignment)

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
    by_split: dict[str, list[PreparedRow]] = {split: [] for split in ("train", "dev", "heldout")}
    for row in rows:
        by_split[assignment[row.group_id]].append(row)
    for split in by_split:
        by_split[split].sort(key=lambda item: item.source["probe_pool_row_key"])

    output_paths: dict[str, Path] = {}
    for split, split_rows in by_split.items():
        path = output_directory / output_config["files"][split]
        _write_jsonl_atomic(path, (render_record(row, split, config) for row in split_rows))
        output_paths[split] = path

    abstain_max, answer_min = validate_label_contract(config)
    aggregate = {
        "schema_version": 1,
        "builder_config_sha256": sha256_file(config_path),
        "source": {
            "canonical_scorer_path": scorer_config["path"],
            "canonical_scorer_sha256": scorer_sha,
            "probe_results_sha256": results_sha,
            "probe_manifest_sha256": manifest_sha,
            "expected_rows": source["probe_results"]["expected_rows"],
            "model_name": source["identity"]["model_name"],
            "model_tag": source["identity"]["model_tag"],
            "probe_config_sha": source["identity"]["probe_config_sha"],
            "n_samples": source["identity"]["n_samples"],
        },
        "label_rule": {
            "chance_probability": config["labeling"]["chance_probability"],
            "one_sided_confidence": config["labeling"]["one_sided_confidence"],
            "abstain_max_correct": abstain_max,
            "answer_min_correct_with_greedy_correct": answer_min,
            "answer_confidence": "(correct_count + 0.5) / 33",
        },
        "mode_counts": {mode: sum(row.mode == mode for row in rows) for mode in MODES},
        "split_diagnostic": split_diagnostic,
        "identity_overlap_across_splits": 0,
        "normalized_question_overlap_across_splits": 0,
        "outputs": {
            split: {
                "file": path.name,
                "rows": len(by_split[split]),
                "sha256": sha256_file(path),
            }
            for split, path in output_paths.items()
        },
    }
    manifest_path = output_directory / output_config["files"]["aggregate_manifest"]
    _write_json_atomic(manifest_path, aggregate)
    aggregate["aggregate_manifest_sha256"] = sha256_file(manifest_path)
    return aggregate


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("dataset_builder.yaml"),
        help="Dataset builder YAML (default: dataset_builder.yaml beside this script)",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Optional root for resolving source inputs; outputs remain relative to the config repo",
    )
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
