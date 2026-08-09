#!/usr/bin/env python3
"""experiment/phase1/eval/ood.py

OOD eval-set loaders (WS-4, architecture doc §6.5). Single responsibility: read
each on-disk OOD corpus into a uniform list of eval records the run_eval driver
feeds to the model, and expose the per-set known/unknown labeling so scorers can
compute refusal-recall / over-refusal off-domain.

A uniform eval record is:
    {
      "id": <stable id>,
      "question": <prompt text>,
      "label": "known" | "unknown" | None,   # None = no abstention label for set
      "aliases": [<normalized gold aliases>],  # for correctness, may be empty
      "source": <set name>,
    }

These loaders do NOT call the model and do NOT score; they only normalize the
on-disk schemas (§6.5) into the contract. run_eval.py attaches `generated_answer`
(+ per-choice probs for MMLU) and hands records to scorers.py.

OOD datasets share NO questions with training; the run_eval driver additionally
asserts the trained question set does not appear in any OOD set (§6.5 defensive
check) using norm_question from scorers.py.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterator

from scorers import normalize


def _norm_aliases(values: list[str]) -> list[str]:
    return [normalize(v) for v in values if v and normalize(v)]


def load_kuq(path: str | Path) -> list[dict]:
    """KUQ knowns_unknowns.jsonl: {question, answer[list], unknown: bool}.
    unknown=True -> label "unknown". Answers are long-form, not strict gold
    aliases, so correctness is not the headline here (unanswerable detection is).
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out.append(
                {
                    "id": f"kuq-{i}",
                    "question": r["question"],
                    "label": "unknown" if r.get("unknown") else "known",
                    "aliases": _norm_aliases(r.get("answer", [])),
                    "source": "kuq",
                }
            )
    return out


def load_coconot(path: str | Path) -> list[dict]:
    """CoCoNot contrast_test.jsonl: {id, category, prompt, response}. These are
    contrast (answerable) prompts -> the over-refusal headline set (§6.5), so all
    labeled "known" (refusing them is over-refusal).
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out.append(
                {
                    "id": r.get("id", f"coconot-{len(out)}"),
                    "question": r["prompt"],
                    "label": "known",  # contrast set: answering is correct behavior
                    "aliases": _norm_aliases([r["response"]] if r.get("response") else []),
                    "source": "coconot",
                }
            )
    return out


def load_popqa(path: str | Path) -> list[dict]:
    """PopQA test.jsonl long-tail: {question, possible_answers (JSON-ish str)}.
    Near-OOD; all answerable (label "known"); gold = possible_answers aliases.
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            raw = r.get("possible_answers", "[]")
            try:
                answers = ast.literal_eval(raw) if isinstance(raw, str) else raw
            except (ValueError, SyntaxError):
                answers = []
            out.append(
                {
                    "id": f"popqa-{r.get('id', len(out))}",
                    "question": r["question"],
                    "label": "known",
                    "aliases": _norm_aliases(list(answers)),
                    "source": "popqa",
                }
            )
    return out


def load_selfaware(path: str | Path) -> list[dict]:
    """SelfAware.json: {example: [{question, answer[list], answerable: bool}]}.
    answerable=False -> "unknown" (the model should abstain).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    examples = data.get("example", [])
    out: list[dict] = []
    for r in examples:
        out.append(
            {
                "id": f"selfaware-{r.get('question_id', len(out))}",
                "question": r["question"],
                "label": "known" if r.get("answerable") else "unknown",
                "aliases": _norm_aliases(r.get("answer", []) if r.get("answerable") else []),
                "source": "selfaware",
            }
        )
    return out


def load_truthfulqa(path: str | Path) -> list[dict]:
    """TruthfulQA.csv: Type,Category,Question,Best Answer,Correct Answers,...
    All answerable (label "known"); gold aliases = Best Answer + Correct Answers
    (semicolon-split). MC1/MC2 scoring is handled separately by run_eval using
    the answer columns; here we provide the open-generation correctness aliases.
    """
    out: list[dict] = []
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            correct = row.get("Correct Answers", "") or ""
            aliases = [row.get("Best Answer", "")] + [
                a.strip() for a in correct.split(";")
            ]
            out.append(
                {
                    "id": f"truthfulqa-{i}",
                    "question": row["Question"],
                    "label": "known",
                    "aliases": _norm_aliases(aliases),
                    "source": "truthfulqa",
                    "category": row.get("Category", ""),
                }
            )
    return out


def load_mmlu(path: str | Path) -> list[dict]:
    """MMLU test.jsonl: {question, subject, choices[list], answer: int}. Carried
    as MCQ records for token-ECE (§6.4 #4): `choices` + `answer` index preserved;
    run_eval extracts per-choice token probs and the ECE scorer consumes them.
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out.append(
                {
                    "id": f"mmlu-{i}",
                    "question": r["question"],
                    "label": "known",
                    "choices": r["choices"],
                    "answer_index": r["answer"],
                    "subject": r.get("subject", ""),
                    "aliases": [],  # MCQ scored by index, not alias membership
                    "source": "mmlu",
                }
            )
    return out


def load_ambigqa(path: str | Path) -> list[dict]:
    """AmbigQA validation/train JSONL (pre-screened by ood-breadth's
    screen_ood_surfaces.py -- see experiments/ood-breadth-beyond-selfaware/
    cell.yaml surfaces.S_AMBIGQA): {id, question, annotations: {type, answer,
    qaPairs}}.

    Label rule (cell.yaml surfaces.S_AMBIGQA.label_rule): annotations.type
    containing ONLY "multipleQAs" (every annotator marked the question
    ambiguous) is gold-unanswerable ("unknown"); annotations.type containing
    ONLY "singleAnswer" with non-empty annotations.answer is answerable
    ("known"). Rows whose type list contains both labels (annotator
    disagreement) have no consensus and are dropped by the screen upstream --
    this loader still defends against seeing one (raises rather than
    mislabeling) since the screen output is the sole gate.
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            ann = r.get("annotations", {})
            types = set(ann.get("type", []))
            answers = ann.get("answer", [])
            if types == {"multipleQAs"}:
                label = "unknown"
                aliases: list[str] = []
            elif types == {"singleAnswer"}:
                flat = [a for group in answers for a in (group or [])]
                if not flat:
                    # singleAnswer with no gold text: not a consensus-answerable
                    # row per the label rule; the screen should not have
                    # retained it, so surface the defect rather than mislabel.
                    raise ValueError(
                        f"ambigqa row {r.get('id')}: singleAnswer with empty "
                        "answer list; screen should have dropped this row"
                    )
                label = "known"
                aliases = flat
            else:
                raise ValueError(
                    f"ambigqa row {r.get('id')}: mixed or unrecognized "
                    f"annotation types {sorted(types)}; screen should have "
                    "dropped this row (annotator disagreement)"
                )
            out.append(
                {
                    "id": f"ambigqa-{r['id']}",
                    "question": r["question"],
                    "label": label,
                    "aliases": _norm_aliases(aliases),
                    "source": "ambigqa",
                }
            )
    return out


def load_bigbench_known_unknowns(path: str | Path) -> list[dict]:
    """BIG-bench known_unknowns JSONL (pre-screened, train+validation merged by
    screen_ood_surfaces.py -- see cell.yaml surfaces.S_BIGBENCH): {idx, inputs,
    targets, multiple_choice_targets, multiple_choice_scores}.

    Question extraction (cell.yaml
    surfaces.S_BIGBENCH.question_extraction): first line of `inputs`, "Q: "
    prefix stripped; remaining lines are "  choice: ..." / "A:" scaffolding and
    are dropped. Label rule: targets == ["Unknown"] means unknown; multiple
    choice, no free-form gold, so aliases are always empty
    (correctness_metrics: not_computable per cell.yaml).
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            first_line = r["inputs"].split("\n", 1)[0]
            question = first_line[2:].strip() if first_line.startswith("Q:") else first_line.strip()
            targets = r.get("targets", [])
            label = "unknown" if targets == ["Unknown"] else "known"
            out.append(
                {
                    "id": f"bigbench-known-unknowns-{r.get('idx', i)}",
                    "question": question,
                    "label": label,
                    "aliases": [],
                    "source": "bigbench_known_unknowns",
                }
            )
    return out


def _sycophancy_answer_condition(prompt_template: str) -> str:
    """Classify Sharma et al. answer-sycophancy prompt templates."""
    if prompt_template == "{question}":
        return "neutral"
    if "{incorrect_answer}" in prompt_template:
        return "incorrect_hint"
    if "I don't think the answer is {correct_answer}" in prompt_template:
        return "correct_answer_denial"
    if "{correct_answer}" in prompt_template:
        return "correct_hint"
    return "other"


def load_sycophancy_answer(path: str | Path) -> list[dict]:
    """Sharma et al. answer-sycophancy eval.

    Records are variants of the same factual question under neutral, correct
    hint, correct-answer denial, and incorrect-hint pressure. All rows are
    answerable; sycophancy analysis compares correctness and incorrect-answer
    matching across prompt conditions grouped by `base_question_id`.
    """
    out: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            base = r.get("base", {})
            metadata = r.get("metadata", {})
            messages = r.get("prompt", [])
            question = messages[0]["content"] if messages else base["question"]
            base_question = base.get("question", question)
            group_id = hashlib.sha256(base_question.encode("utf-8")).hexdigest()[:16]
            prompt_template = metadata.get("prompt_template", "")
            condition = _sycophancy_answer_condition(prompt_template)
            aliases = [base.get("correct_answer", "")] + list(base.get("answer", []))
            out.append(
                {
                    "id": f"sycophancy-answer-{group_id}-{condition}-{i}",
                    "question": question,
                    "label": "known",
                    "aliases": _norm_aliases(aliases),
                    "source": "sycophancy_answer",
                    "sycophancy_task": "answer",
                    "base_question": base_question,
                    "base_question_id": group_id,
                    "base_dataset": base.get("dataset", ""),
                    "prompt_template": prompt_template,
                    "prompt_condition": condition,
                    "correct_answer": base.get("correct_answer", ""),
                    "incorrect_answer": base.get("incorrect_answer", ""),
                }
            )
    return out


def load_abstentionbench_indices(repo_dir: str | Path) -> dict:
    """AbstentionBench is a loader repo (§6.5): consume its subsampling indices
    rather than re-deriving subsets. Returns the parsed subsampling-indices.json
    so the run_eval driver can select the pinned subset deterministically.
    """
    repo = Path(repo_dir)
    indices_path = repo / "subsampling-indices.json"
    if not indices_path.exists():
        raise FileNotFoundError(
            f"AbstentionBench subsampling indices not found at {indices_path}"
        )
    return json.loads(indices_path.read_text(encoding="utf-8"))


# Registry so the config can name a set and get its loader (KISS dispatch).
OOD_LOADERS = {
    "kuq": load_kuq,
    "coconot": load_coconot,
    "popqa": load_popqa,
    "selfaware": load_selfaware,
    "truthfulqa": load_truthfulqa,
    "mmlu": load_mmlu,
    "sycophancy_answer": load_sycophancy_answer,
    "ambigqa": load_ambigqa,
    "bigbench_known_unknowns": load_bigbench_known_unknowns,
}


def load_ood_set(name: str, path: str | Path) -> list[dict]:
    """Dispatch to the named OOD loader. Raises on unknown set name."""
    if name not in OOD_LOADERS:
        raise KeyError(
            f"unknown OOD set '{name}'; known: {sorted(OOD_LOADERS)}"
        )
    return OOD_LOADERS[name](path)
