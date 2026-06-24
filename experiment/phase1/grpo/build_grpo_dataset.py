#!/usr/bin/env python3
"""Build prospective GRPO dataset rows from the frozen Phase 1 split.

This is an additive dataset projection. It does not modify the locked SFT/DPO/KTO
artifacts and does not change the v0.3 matrix.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
sys.path.insert(0, str(DATA_DIR))

import build_datasets as bd  # noqa: E402


def system_prompt_for_confidence_field(confidence_field: str = "confidence") -> str:
    if confidence_field not in {"confidence", "response_confidence"}:
        raise ValueError(f"unsupported confidence field: {confidence_field!r}")
    field_description = (
        "The `response_confidence` value is your probability from 0 to 1 that "
        "your answer or abstention is the appropriate response."
        if confidence_field == "response_confidence"
        else "The `confidence` value is your probability from 0 to 1 that your "
        "answer or abstention is the appropriate response."
    )
    return (
        "Answer the user's question. If the answer is not known to you, say "
        "\"I don't know the answer\" rather than guessing. Return only a JSON object "
        f"with exactly two keys: `answer` and `{confidence_field}`. The `answer` "
        f"value is your answer or abstention text. {field_description}"
    )


DEFAULT_SYSTEM_PROMPT = system_prompt_for_confidence_field("confidence")
NORMAL_P_CORRECT = -1.0
NORMAL_AMBIGUITY_BAND = ""

SCHEMA_RESPONSE_CONFIDENCE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON object "
    "with exactly two keys: `answer` and `response_confidence`. The `answer` "
    "value is your answer or abstention text. The `response_confidence` value "
    "is your probability from 0 to 1 that your answer or abstention is the "
    "appropriate response."
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_index_from_key(key: str) -> int:
    prefix = str(key).split("|", 1)[0]
    if not prefix.isdigit():
        raise ValueError(f"frozen question key lacks source-index prefix: {key!r}")
    return int(prefix)


def _record_from_triviaqa_row(row: dict, key: str, label: str) -> dict:
    answer = row.get("answer") or {}
    aliases = answer.get("normalized_aliases") or []
    value = answer.get("value") or answer.get("normalized_value") or ""
    return {
        "probe_pool_row_key": key,
        "question_id": row.get("question_id", key),
        "question": row["question"],
        "normalized_aliases": aliases,
        "answer_value": value,
        "label": label,
    }


def _load_records_from_triviaqa_source(
    *,
    frozen: dict,
    triviaqa_train: Path,
) -> dict[str, dict]:
    """Reconstruct prompt metadata from source-index frozen keys.

    The committed frozen split stores row keys such as
    `000000000075|tc_111`. If the original probe output is not present locally,
    the source index is enough to recover the question and gold aliases from the
    local TriviaQA train JSONL while preserving the exact train/dev split.
    """
    labels_by_key = {
        **{key: "known" for key in frozen.get("known_question_keys", [])},
        **{key: "unknown" for key in frozen.get("unknown_question_keys", [])},
    }
    wanted_indices = {_source_index_from_key(key): key for key in labels_by_key}
    records: dict[str, dict] = {}

    with triviaqa_train.open(encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            key = wanted_indices.get(idx)
            if key is None:
                continue
            row = json.loads(line)
            records[key] = _record_from_triviaqa_row(row, key, labels_by_key[key])
            if len(records) == len(wanted_indices):
                break

    missing = sorted(set(labels_by_key) - set(records))
    if missing:
        raise KeyError(
            f"could not recover {len(missing)} frozen key(s) from {triviaqa_train}: "
            f"{missing[:5]}"
        )
    return records


def _rows_for_keys(records_by_key: dict[str, dict], keys: list[str], system_prompt: str) -> list[dict]:
    rows = []
    missing = []
    for key in keys:
        rec = records_by_key.get(key)
        if rec is None:
            missing.append(key)
            continue
        label = str(rec["label"]).lower()
        aliases = [bd.normalize(alias) for alias in rec.get("normalized_aliases", []) if alias]
        rows.append(
            {
                "prompt": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": rec["question"]},
                ],
                "id": key,
                "question_id": rec["question_id"],
                "label": label,
                "answerable": label == "known",
                "aliases": aliases,
                "gold_answer": bd.gold_answer(rec) if label == "known" else "",
                "unknown_type": "model_specific_unknown" if label == "unknown" else "",
                "p_correct": NORMAL_P_CORRECT,
                "ambiguity_band": NORMAL_AMBIGUITY_BAND,
            }
        )
    if missing:
        raise KeyError(f"questions_frozen references {len(missing)} missing probe key(s): {missing[:5]}")
    return rows


def _rows_for_records(records: list[dict], system_prompt: str) -> list[dict]:
    rows = []
    for rec in records:
        label = str(rec["label"]).lower()
        aliases = [bd.normalize(alias) for alias in rec.get("normalized_aliases", []) if alias]
        row = {
            "prompt": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": rec["question"]},
            ],
            "id": bd.record_key(rec),
            "question_id": rec["question_id"],
            "label": "ambiguous" if label == "discard" else label,
            "answerable": label != "unknown",
            "aliases": aliases,
            "gold_answer": bd.gold_answer(rec) if label in {"known", "discard"} else "",
            "unknown_type": "model_specific_unknown" if label == "unknown" else "",
            "p_correct": NORMAL_P_CORRECT,
            "ambiguity_band": NORMAL_AMBIGUITY_BAND,
        }
        if label == "discard" and rec.get("p_correct") is not None:
            row["p_correct"] = float(rec["p_correct"])
            row["ambiguity_band"] = "middle"
        rows.append(row)
    return rows


def _middle_discard_records(
    records_by_key: dict[str, dict],
    *,
    min_p_correct: float,
    max_p_correct: float,
) -> list[dict]:
    out = []
    for rec in records_by_key.values():
        if str(rec.get("label", "")).lower() != "discard":
            continue
        if rec.get("p_correct") is None:
            continue
        p_correct = float(rec["p_correct"])
        if min_p_correct <= p_correct <= max_p_correct:
            out.append(rec)
    return sorted(out, key=bd.record_key)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_grpo_projection(
    *,
    probe_results: Path,
    frozen_questions: Path,
    output_dir: Path,
    triviaqa_train: Path | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    confidence_field: str = "confidence",
    include_ambiguous_middle: bool = False,
    ambiguous_min_p_correct: float = 0.4,
    ambiguous_max_p_correct: float = 0.6,
    dev_fraction: float = 0.1,
    seed: int = 42,
) -> dict:
    if confidence_field not in {"confidence", "response_confidence"}:
        raise ValueError(f"unsupported confidence field: {confidence_field!r}")
    frozen = _load_json(frozen_questions)
    if probe_results.exists():
        probe_records = bd.load_probe_records(probe_results)
        records_by_key = {bd.record_key(rec): rec for rec in probe_records}
        source = str(probe_results)
    elif triviaqa_train is not None and triviaqa_train.exists():
        records_by_key = _load_records_from_triviaqa_source(
            frozen=frozen,
            triviaqa_train=triviaqa_train,
        )
        source = str(triviaqa_train)
    else:
        raise FileNotFoundError(
            f"probe results not found: {probe_results}; also no usable "
            f"TriviaQA source fallback: {triviaqa_train}"
        )

    train_rows = _rows_for_keys(records_by_key, frozen["train_question_keys"], system_prompt)
    dev_rows = _rows_for_keys(records_by_key, frozen["dev_question_keys"], system_prompt)

    ambiguous_rows = []
    if include_ambiguous_middle:
        if not probe_results.exists():
            raise FileNotFoundError(
                "--include-ambiguous-middle requires original probe_results metadata"
            )
        ambiguous_records = _middle_discard_records(
            records_by_key,
            min_p_correct=ambiguous_min_p_correct,
            max_p_correct=ambiguous_max_p_correct,
        )
        if len(ambiguous_records) < 2:
            ambiguous_train, ambiguous_dev = ambiguous_records, []
        else:
            ambiguous_train, ambiguous_dev = bd.split_dev(
                ambiguous_records,
                dev_fraction,
                seed,
            )
        train_rows.extend(_rows_for_records(ambiguous_train, system_prompt))
        dev_rows.extend(_rows_for_records(ambiguous_dev, system_prompt))
        ambiguous_rows = ambiguous_records

    train_path = output_dir / "grpo_train.jsonl"
    dev_path = output_dir / "grpo_dev.jsonl"
    write_jsonl(train_path, train_rows)
    write_jsonl(dev_path, dev_rows)

    manifest = {
        "component": "prospective GRPO dataset projection",
        "status": "not part of locked Phase 1 v0.3 matrix",
        "metadata_source": source,
        "probe_results": str(probe_results),
        "triviaqa_train_fallback": str(triviaqa_train) if triviaqa_train else None,
        "frozen_questions": str(frozen_questions),
        "train_rows": len(train_rows),
        "dev_rows": len(dev_rows),
        "system_prompt_contract": f"answer_or_abstain_plus_{confidence_field}_0_to_1",
        "confidence_field": confidence_field,
        "ambiguous_middle": {
            "included": include_ambiguous_middle,
            "rows": len(ambiguous_rows),
            "p_correct_min": ambiguous_min_p_correct,
            "p_correct_max": ambiguous_max_p_correct,
        },
        "outputs": {
            "train": str(train_path),
            "dev": str(dev_path),
        },
    }
    (output_dir / "grpo_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DATA_DIR / "config" / "build.yaml"))
    parser.add_argument("--model-tag", required=True)
    parser.add_argument("--probe-results")
    parser.add_argument("--frozen-questions")
    parser.add_argument("--triviaqa-train")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--confidence-field",
        choices=["confidence", "response_confidence"],
        default="confidence",
        help="JSON confidence key to request in the prompt.",
    )
    parser.add_argument("--include-ambiguous-middle", action="store_true")
    parser.add_argument("--ambiguous-min-p-correct", type=float, default=0.4)
    parser.add_argument("--ambiguous-max-p-correct", type=float, default=0.6)
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    inputs = config["inputs"]
    repo_root = Path(__file__).resolve().parents[3]

    def resolve(template: str) -> Path:
        return (repo_root / template.format(model_tag=args.model_tag)).resolve()

    probe_results = Path(args.probe_results) if args.probe_results else resolve(inputs["probe_results"])
    frozen_questions = (
        Path(args.frozen_questions)
        if args.frozen_questions
        else resolve("experiment/phase1/data/{model_tag}/questions_frozen.json")
    )
    triviaqa_train = (
        Path(args.triviaqa_train)
        if args.triviaqa_train
        else (repo_root / "datasets/triviaqa-rc-nocontext/train.jsonl").resolve()
    )
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else resolve("experiment/phase1/data/{model_tag}")
    )

    manifest = build_grpo_projection(
        probe_results=probe_results,
        frozen_questions=frozen_questions,
        triviaqa_train=triviaqa_train,
        output_dir=output_dir,
        system_prompt=system_prompt_for_confidence_field(args.confidence_field),
        confidence_field=args.confidence_field,
        include_ambiguous_middle=args.include_ambiguous_middle,
        ambiguous_min_p_correct=args.ambiguous_min_p_correct,
        ambiguous_max_p_correct=args.ambiguous_max_p_correct,
    )
    print(
        f"Built GRPO projection: {manifest['train_rows']} train / "
        f"{manifest['dev_rows']} dev rows in {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
