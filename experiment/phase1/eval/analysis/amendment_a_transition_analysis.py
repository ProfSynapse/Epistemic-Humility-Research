"""Amendment A transition analysis from persisted local eval artifacts.

The live eval driver currently persists aggregate metrics and McNemar paired
truthful flips, but not per-row generations. That means exact row-level
refusal/correctness transitions cannot be reconstructed after the run. This
script reports exact values where the persisted artifacts support them and
tight feasible bounds where row-level identity is missing.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[4]
SELFWARE = REPO / "experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b"
BROADER = REPO / "experiment/phase1/eval/results_amendment_a_broader_ood_local_4b"


@dataclass(frozen=True)
class ArmCounts:
    n_unknown: int
    n_known: int
    u_refuse: int
    u_answer: int
    k_refuse: int
    k_correct: int
    k_incorrect: int


@dataclass(frozen=True)
class PairBounds:
    pair: str
    eval_set: str
    exact_truthful_a_not_b: int
    exact_truthful_b_not_a: int
    unknown_a_refuse_b_answer: tuple[int, int]
    known_a_refuse_b_answer: tuple[int, int]
    known_a_refuse_b_correct: tuple[int, int]
    known_a_correct_b_bad: tuple[int, int]


def _load_counts(root: Path, arm: str, eval_set: str) -> ArmCounts:
    payload = json.loads((root / f"{arm}__{eval_set}" / "metrics.json").read_text(encoding="utf-8"))
    c = payload["counts"]
    return ArmCounts(
        n_unknown=int(c["n_unknown_labeled"]),
        n_known=int(c["n_known_labeled"]),
        u_refuse=int(c["refuse_on_unknown"]),
        u_answer=int(c["answered_unknown"]),
        k_refuse=int(c["refuse_on_known"]),
        k_correct=int(c["correct_known"]),
        k_incorrect=int(c["answered_known"]) - int(c["correct_known"]),
    )


def _load_mcnemar(root: Path, eval_set: str, arm_a: str, arm_b: str) -> tuple[int, int]:
    with (root / "comparisons" / "mcnemar.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["eval_set"] == eval_set and row["arm_a"] == arm_a and row["arm_b"] == arm_b:
                return int(row["b_a_not_b"]), int(row["c_b_not_a"])
    raise KeyError((eval_set, arm_a, arm_b))


def _unknown_tables(a: ArmCounts, b: ArmCounts) -> Iterable[tuple[int, int]]:
    """Yield possible (a_refuse_b_answer, a_answer_b_refuse) unknown transitions."""
    lo_rr = max(0, a.u_refuse + b.u_refuse - a.n_unknown)
    hi_rr = min(a.u_refuse, b.u_refuse)
    for rr in range(lo_rr, hi_rr + 1):
        yield a.u_refuse - rr, b.u_refuse - rr


@dataclass(frozen=True)
class KnownBounds:
    recovery_answer: tuple[int, int]
    recovery_correct: tuple[int, int]
    degrade: tuple[int, int]


def _known_table_bounds(
    a: ArmCounts,
    b: ArmCounts,
    *,
    known_a_not_b: int,
) -> KnownBounds | None:
    """Compute exact integer bounds for the known-row 3x3 transition table.

    States are R, C, I for arm A rows and R, C, I for arm B columns. Margins are
    fixed by each arm's aggregate counts. The persisted McNemar truthful flip,
    after assigning the unknown component, fixes C->C. We then enumerate the
    remaining feasible integer tables through two free variables:

      b = R->C
      d = C->R

    For each feasible (b, d), the remaining free cell c = R->I has a closed
    integer interval. This avoids external LP dependencies while keeping the
    result exact for the count constraints.
    """
    cc = a.k_correct - known_a_not_b
    if cc < 0 or cc > min(a.k_correct, b.k_correct):
        return None

    # Known A correct but B bad: C->R + C->I. Once C->C is fixed, this equals
    # the known-side A-not-B truthful flip for this unknown allocation.
    degrade = known_a_not_b

    u = b.k_correct - cc  # R->C + I->C
    t = known_a_not_b  # C->R + C->I
    if u < 0 or t < 0:
        return None

    b_lo = max(0, u - a.k_incorrect)
    b_hi = min(u, a.k_refuse)
    d_lo = max(0, t - b.k_incorrect)
    d_hi = min(t, b.k_refuse)

    min_answer: int | None = None
    max_answer: int | None = None
    min_correct: int | None = None
    max_correct: int | None = None

    for rc in range(b_lo, b_hi + 1):
        for cr in range(d_lo, d_hi + 1):
            ci = t - cr
            if ci < 0 or ci > b.k_incorrect:
                continue
            ic = u - rc
            if ic < 0 or ic > a.k_incorrect:
                continue

            # Let ri = R->I. Non-negativity of R->R, I->R, and I->I gives a
            # feasible interval for ri.
            ri_lo = max(0, a.k_refuse - rc + cr - b.k_refuse)
            ri_hi = min(a.k_refuse - rc, b.k_incorrect - ci)
            if ri_lo > ri_hi:
                continue

            correct = rc
            min_correct = correct if min_correct is None else min(min_correct, correct)
            max_correct = correct if max_correct is None else max(max_correct, correct)

            answer_lo = rc + ri_lo
            answer_hi = rc + ri_hi
            min_answer = answer_lo if min_answer is None else min(min_answer, answer_lo)
            max_answer = answer_hi if max_answer is None else max(max_answer, answer_hi)

    if min_answer is None or max_answer is None or min_correct is None or max_correct is None:
        return None

    return KnownBounds(
        recovery_answer=(min_answer, max_answer),
        recovery_correct=(min_correct, max_correct),
        degrade=(degrade, degrade),
    )


def _round_bounds(values: list[tuple[int, int]]) -> tuple[int, int]:
    lo = min(v[0] for v in values)
    hi = max(v[1] for v in values)
    return lo, hi


def compute_pair(root: Path, eval_set: str, arm_a: str, arm_b: str) -> PairBounds:
    a = _load_counts(root, arm_a, eval_set)
    b = _load_counts(root, arm_b, eval_set)
    a_not_b, b_not_a = _load_mcnemar(root, eval_set, arm_a, arm_b)

    unknown_ab_bounds: list[tuple[int, int]] = []
    known_recovery_answer_bounds: list[tuple[int, int]] = []
    known_recovery_correct_bounds: list[tuple[int, int]] = []
    known_degrade_bounds: list[tuple[int, int]] = []

    for u_a_refuse_b_answer, u_a_answer_b_refuse in _unknown_tables(a, b):
        known_a_not_b = a_not_b - u_a_refuse_b_answer
        known_b_not_a = b_not_a - u_a_answer_b_refuse
        if known_a_not_b < 0 or known_b_not_a < 0:
            continue
        # In the known table, known_b_not_a is implied by column C and C->C.
        if known_b_not_a != b.k_correct - (a.k_correct - known_a_not_b):
            continue
        known_bounds = _known_table_bounds(a, b, known_a_not_b=known_a_not_b)
        if known_bounds:
            unknown_ab_bounds.append((u_a_refuse_b_answer, u_a_refuse_b_answer))
            known_recovery_answer_bounds.append(known_bounds.recovery_answer)
            known_recovery_correct_bounds.append(known_bounds.recovery_correct)
            known_degrade_bounds.append(known_bounds.degrade)

    if not unknown_ab_bounds:
        raise RuntimeError(f"No feasible tables for {eval_set} {arm_a}->{arm_b}")

    return PairBounds(
        pair=f"{arm_a}->{arm_b}",
        eval_set=eval_set,
        exact_truthful_a_not_b=a_not_b,
        exact_truthful_b_not_a=b_not_a,
        unknown_a_refuse_b_answer=_round_bounds(unknown_ab_bounds),
        known_a_refuse_b_answer=_round_bounds(known_recovery_answer_bounds),
        known_a_refuse_b_correct=_round_bounds(known_recovery_correct_bounds),
        known_a_correct_b_bad=_round_bounds(known_degrade_bounds),
    )


def _fmt_bounds(bounds: tuple[int, int]) -> str:
    return str(bounds[0]) if bounds[0] == bounds[1] else f"{bounds[0]}-{bounds[1]}"


def render_markdown() -> str:
    pairs = [
        compute_pair(SELFWARE, "selfaware", "sft_merged", "sft_dpo"),
        compute_pair(SELFWARE, "selfaware", "sft_merged", "sft_kto"),
        compute_pair(SELFWARE, "selfaware", "sft_dpo", "sft_kto"),
        compute_pair(BROADER, "kuq", "sft_merged", "sft_dpo"),
        compute_pair(BROADER, "kuq", "sft_merged", "sft_kto"),
        compute_pair(BROADER, "kuq", "sft_dpo", "sft_kto"),
    ]

    lines = [
        "# Amendment A Transition Analysis",
        "",
        "Source artifacts: persisted local `metrics.json` and `comparisons/mcnemar.csv` files from the Amendment A SelfAware full and broader OOD eval directories.",
        "",
        "Row-identity caveat: the live eval outputs in these result directories do not include `generations.jsonl` or another per-row prediction file. Exact row-level transitions cannot be reconstructed from the persisted artifacts. McNemar truthful flips are exact because the eval driver persisted paired truthful-vector discordance counts. The narrower refusal/correctness transitions below are tight feasible count ranges implied by the per-arm margins plus those exact McNemar counts.",
        "",
        "## SelfAware Full",
        "",
        "| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for p in pairs[:3]:
        lines.append(
            f"| `{p.pair}` | {p.exact_truthful_a_not_b} | {p.exact_truthful_b_not_a} | "
            f"{_fmt_bounds(p.unknown_a_refuse_b_answer)} | {_fmt_bounds(p.known_a_refuse_b_answer)} | "
            f"{_fmt_bounds(p.known_a_refuse_b_correct)} | {_fmt_bounds(p.known_a_correct_b_bad)} |"
        )
    lines.extend([
        "",
        "## KUQ Supporting Slice",
        "",
        "| Pair | Exact truthful A not B | Exact truthful B not A | Unknown A refused, B answered | Known A refused, B answered | Known A refused, B answered correctly | Known A correct, B bad |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for p in pairs[3:]:
        lines.append(
            f"| `{p.pair}` | {p.exact_truthful_a_not_b} | {p.exact_truthful_b_not_a} | "
            f"{_fmt_bounds(p.unknown_a_refuse_b_answer)} | {_fmt_bounds(p.known_a_refuse_b_answer)} | "
            f"{_fmt_bounds(p.known_a_refuse_b_correct)} | {_fmt_bounds(p.known_a_correct_b_bad)} |"
        )
    lines.extend([
        "",
        "Interpretation guardrail: CoCoNot, TruthfulQA, and PopQA in the broader directory remain useful for aggregate refusal/over-refusal pressure, but not for the SelfAware known/unknown transition questions. CoCoNot answer aliases are empty in the local contrast file, so correctness is intentionally not interpreted there.",
        "",
        "## Interpretation",
        "",
        "Sequential DPO is mixed, not a clean recovery. On full SelfAware it reduced known over-refusal sharply, but the persisted evidence implies at least 348 and at most 424 unknown rows where `sft_merged` correctly refused and `sft_dpo` answered instead. KUQ supports the same direction: at least 55 of the 58 exact `sft_merged`-truthful / `sft_dpo`-untruthful flips came from unknown rows where DPO answered after SFT refused.",
        "",
        "The known-question recovery side is weaker than the aggregate over-refusal drop suggests. Full SelfAware has 1,111 fewer known refusals for `sft_dpo` than `sft_merged`, but only 70 additional known correct answers in the aggregate. The feasible row-level bounds allow 0-146 known rows where SFT refused and DPO answered correctly, so the current persisted artifacts cannot prove that most over-refusal reduction became useful correct recovery. It could include substantial incorrect answering.",
        "",
        "Sequential KTO is closer to SFT than DPO. On full SelfAware it can account for 71-124 unknown SFT-refusal to KTO-answer losses, versus 348-424 for DPO, and its exact truthful loss against SFT is much smaller (124 vs 424). The cost is that KTO retains high known over-refusal: aggregate SelfAware over-refusal is 48.31 for KTO versus 13.95 for DPO and 61.49 for SFT.",
        "",
        "## Recommendations",
        "",
        "Use this as bounded local Amendment A evidence only. Do not fold it into v0.3 headline/protocol claims.",
        "",
        "The next experimental direction is sensitivity around the sequential preference stage rather than a binary keep/drop decision. DPO deserves lower-intensity variants because it has the desired over-refusal pressure but overshoots into unknown-answering and lower known correctness. Reasonable axes are lower DPO beta, lower LR, fewer effective epochs/steps, and possibly smaller downstream LoRA rank/alpha if the goal is a gentler correction to SFT.",
        "",
        "KTO deserves a separate sensitivity axis only if the priority is preserving abstention first. It retained more unknown refusal but did not reduce over-refusal enough in this local run, so KTO variants should target stronger known-question recovery without collapsing unknown refusal.",
        "",
        "Future live eval runs should persist `generations.jsonl` or a compact per-row scored table (`id`, question/order key, label, refused, correct, truthful) for each arm. Without that, exact transition analysis is limited to McNemar truthful flips plus feasible bounds from aggregate margins.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    text = render_markdown()
    if args.write_report:
        out = Path(__file__).with_name("amendment_a_transition_report.md")
        out.write_text(text, encoding="utf-8")
        print(out)
    else:
        print(text)


if __name__ == "__main__":
    main()
