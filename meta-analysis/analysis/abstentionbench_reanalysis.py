#!/usr/bin/env python3
"""Secondary analyses of the AbstentionBench authors' released results table.

Input: docs/epistemic-humility/datasets/abstentionbench-results/
       abstention_performance.csv (624 rows; AbstentionBench, arXiv 2506.09038,
       facebookresearch/AbstentionBench analysis/abstention_performance.csv).
Columns: model_name_formatted, scenario_label, dataset_name_formatted,
post_training_stage (Base/SFT/DPO/PPO RLVF for the Tulu-3 ladder, Instruct for
Llama 3.1 Instruct, NaN for frontier/other), precision, recall, f1_score.

Metric semantics (abstention as the positive class):
  recall    = P(abstain | question unanswerable)        higher = better
  precision = P(unanswerable | model abstained)         low = over-refusal
              (false positives = abstaining on answerable questions)

Structure note (verified by inspection): each of the 31 benchmark subsets
belongs to EXACTLY ONE scenario_label, and each (model, scenario, dataset)
triple appears at most once. Scenario is a property of the benchmark subset,
not an experimental condition, so there is no "primary scenario" to choose;
instead, every comparison below is paired within identical
(dataset_name, scenario_label) cells, and cross-model aggregates are
restricted to the shared-subset intersection so every model is summarized
over the same scenario mix.

Analyses:
  B1 Tulu-3 post-training ladder (claims C2/C3): paired per-cell deltas of
     recall and precision for SFT-vs-Base, DPO-vs-SFT, PPO-vs-SFT at 8B and
     70B, with median delta, sign counts, and exact binomial sign test.
  B2 Scale sweep (claim C4): Llama 3.1 8B/70B/405B Instruct (and 8B/70B Base)
     median recall/precision over shared subsets; monotonicity verdict; plus
     a descriptive cross-family size spread (flagged non-comparable).
  B3 Recall-precision frontier: per-model medians over the shared-subset
     intersection, Spearman rho across models, scatter figure.

Output (deterministic, recomputable; this script is the provenance):
  meta-analysis/evidence/abstentionbench-reanalysis.md
  meta-analysis/analysis/figures/abstentionbench_frontier.png
  meta-analysis/analysis/figures/abstentionbench_ladder.png
  meta-analysis/analysis/figures/abstentionbench_scale.png

Run: python3 abstentionbench_reanalysis.py
"""

import math
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CSV = HERE.parent.parent / "datasets" / "abstentionbench-results" / "abstention_performance.csv"
OUT = HERE.parent / "evidence" / "abstentionbench-reanalysis.md"
FIGDIR = HERE / "figures"

try:
    from scipy.stats import binomtest as _binomtest
    from scipy.stats import spearmanr as _spearmanr

    def sign_test_p(k: int, n: int) -> float:
        return _binomtest(k, n, 0.5).pvalue if n else float("nan")

    def spearman(x, y):
        r = _spearmanr(x, y)
        return float(r.statistic), float(r.pvalue)

except ImportError:  # exact fallback, stdlib only

    def sign_test_p(k: int, n: int) -> float:
        if not n:
            return float("nan")
        pmf = [math.comb(n, i) * 0.5**n for i in range(n + 1)]
        return min(1.0, sum(p for p in pmf if p <= pmf[k] + 1e-12))

    def spearman(x, y):
        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            r = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2 + 1
                for k2 in range(i, j + 1):
                    r[order[k2]] = avg
                i = j + 1
            return r

        rx, ry = rank(list(x)), rank(list(y))
        n = len(rx)
        mx, my = sum(rx) / n, sum(ry) / n
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
        rho = num / den
        # t-approximation for p (n >= 10 here)
        t = rho * math.sqrt((n - 2) / (1 - rho**2))
        p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))  # normal approx
        return rho, p


# Tulu-3 ladder model names per scale, exact post_training_stage order.
LADDER = {
    "8B": {
        "Base": "Llama 3.1 8B Base",
        "SFT": "Llama 3.1 8B Tulu 3 SFT",
        "DPO": "Llama 3.1 8B Tulu 3 DPO",
        "PPO RLVF": "Llama 3.1 8B Tulu 3 PPO RLVF",
    },
    "70B": {
        "Base": "Llama 3.1 70B Base",
        "SFT": "Llama 3.1 70B Tulu 3 SFT",
        "DPO": "Llama 3.1 70B Tulu 3 DPO",
        "PPO RLVF": "Llama 3.1 70B Tulu 3 PPO RLVF",
    },
}
COMPARISONS = [("SFT", "Base"), ("DPO", "SFT"), ("PPO RLVF", "SFT")]

LLAMA_SWEEP = {
    "Instruct": {8: "Llama 3.1 8B Instruct", 70: "Llama 3.1 70B Instruct", 405: "Llama 3.1 405B Instruct"},
    "Base": {8: "Llama 3.1 8B Base", 70: "Llama 3.1 70B Base"},
}

# Models excluded from cross-model aggregates: partial subset runs only.
PARTIAL_MODELS = ["TinyLlamaChat", "o1HighReasoningAPI", "o1LowReasoningAPI"]

SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)B\b")


def f2(x: float) -> str:
    return f"{x:.2f}"


def fp(p: float) -> str:
    return "n/a" if math.isnan(p) else (f"{p:.2e}" if p < 0.001 else f"{p:.4f}")


def sign_counts(deltas) -> tuple:
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    tie = sum(1 for d in deltas if d == 0)
    return pos, neg, tie


def cell_table(df: pd.DataFrame, model: str) -> pd.DataFrame:
    """One row per (dataset, scenario) cell for a model, indexed by cell."""
    sub = df[df.model_name_formatted == model]
    return sub.set_index(["dataset_name_formatted", "scenario_label"])[["recall", "precision"]]


def main() -> None:
    df = pd.read_csv(CSV)
    lines = [
        "# AbstentionBench reanalysis (auto-generated by analysis/abstentionbench_reanalysis.py)",
        "",
        "Source: facebookresearch/AbstentionBench released results table",
        "(datasets/abstentionbench-results/abstention_performance.csv, 624 rows,",
        "23 models x up to 31 benchmark subsets). Abstention recall = correctly",
        "abstaining on unanswerable questions; abstention precision = not",
        "over-flagging (low precision = abstaining on answerable questions, the",
        "over-refusal-sensitive quantity for claim C3). All comparisons are paired",
        "within identical (benchmark subset, scenario) cells; cross-model summaries",
        "use only the shared-subset intersection. Each benchmark subset belongs to",
        "exactly one scenario, so restricting to shared subsets fixes the scenario",
        "mix identically across models; no single primary scenario is selected,",
        "and none needs to be (scenario is a property of the subset, not a",
        "prompt condition).",
        "",
        "Values rounded to 2 decimals. Sign tests are exact two-sided binomial",
        "tests on delta signs with ties dropped.",
        "",
    ]

    # ---------------- B1: Tulu-3 post-training ladder ----------------
    lines += [
        "## B1. Tulu-3 post-training ladder (C2/C3)",
        "",
        "Paired per-cell deltas (later stage minus earlier stage) over the",
        "(subset, scenario) cells present in ALL FOUR stages at that scale.",
        "Positive recall delta = better abstention on unanswerable; positive",
        "precision delta = LESS over-refusal.",
        "",
    ]
    ladder_medians = {}  # for figure: {(scale, stage): (med_recall, med_precision)}
    for scale, stages in LADDER.items():
        tables = {st: cell_table(df, m) for st, m in stages.items()}
        common = set.intersection(*(set(t.index) for t in tables.values()))
        all_cells = set.union(*(set(t.index) for t in tables.values()))
        dropped = sorted(c[0] for c in all_cells - common)
        lines += [
            f"### {scale} ladder",
            "",
            f"- Cells present in all four stages: n = {len(common)} of {len(all_cells)}"
            + (f" (dropped: {', '.join(dropped)})" if dropped else ""),
            "",
            "| comparison | metric | median delta | pos / neg / tie | sign-test p (n) |",
            "|---|---|---|---|---|",
        ]
        cells = sorted(common)
        for st in stages:
            t = tables[st].loc[cells]
            ladder_medians[(scale, st)] = (t.recall.median(), t.precision.median())
        for hi, lo in COMPARISONS:
            for metric in ("recall", "precision"):
                d = (tables[hi].loc[cells, metric] - tables[lo].loc[cells, metric]).tolist()
                pos, neg, tie = sign_counts(d)
                n = pos + neg
                p = sign_test_p(pos, n)
                med = pd.Series(d).median()
                lines.append(
                    f"| {hi} vs {lo} | {metric} | {f2(med)} | {pos} / {neg} / {tie} | {fp(p)} ({n}) |"
                )
        lines += [
            "",
            "Stage medians over the same paired cells (recall / precision): "
            + "; ".join(
                f"{st} {f2(ladder_medians[(scale, st)][0])} / {f2(ladder_medians[(scale, st)][1])}"
                for st in stages
            ),
            "",
        ]

    # ---------------- B2: scale sweep ----------------
    lines += [
        "## B2. Scale sweep (C4)",
        "",
    ]
    sweep_medians = {}  # {(family, size): (recall, precision)} for figure
    for family, models in LLAMA_SWEEP.items():
        tables = {sz: cell_table(df, m) for sz, m in models.items()}
        common = sorted(set.intersection(*(set(t.index) for t in tables.values())))
        all_cells = set.union(*(set(t.index) for t in tables.values()))
        dropped = sorted(c[0] for c in set(all_cells) - set(common))
        lines += [
            f"### Llama 3.1 {family} ({' / '.join(f'{s}B' for s in models)})",
            "",
            f"- Shared cells: n = {len(common)}"
            + (f" (dropped: {', '.join(dropped)})" if dropped else ""),
            "",
            "| model | median recall | median precision |",
            "|---|---|---|",
        ]
        meds = {}
        for sz, t in tables.items():
            tt = t.loc[common]
            meds[sz] = (tt.recall.median(), tt.precision.median())
            sweep_medians[(family, sz)] = meds[sz]
            lines.append(f"| {models[sz]} | {f2(meds[sz][0])} | {f2(meds[sz][1])} |")
        sizes = sorted(meds)
        rec = [meds[s][0] for s in sizes]
        prec = [meds[s][1] for s in sizes]
        mono_r = all(rec[i] < rec[i + 1] for i in range(len(rec) - 1))
        mono_p = all(prec[i] < prec[i + 1] for i in range(len(prec) - 1))
        lines += [
            "",
            f"- Recall monotonically increasing with scale: **{'yes' if mono_r else 'no'}**"
            f" ({' -> '.join(f2(r) for r in rec)})",
            f"- Precision monotonically increasing with scale: "
            f"{'yes' if mono_p else 'no'} ({' -> '.join(f2(p) for p in prec)})",
            "",
        ]

    # Descriptive cross-family size spread (non-comparable families; flagged).
    full = df[~df.model_name_formatted.isin(PARTIAL_MODELS)]
    sized = {}
    for m in sorted(full.model_name_formatted.unique()):
        match = SIZE_RE.search(m)
        if match:
            sized[m] = float(match.group(1))
    shared = sorted(
        set.intersection(*(set(cell_table(df, m).index) for m in sized))
    )
    lines += [
        "### Cross-family size spread (descriptive only)",
        "",
        f"Models with a parameter count in their name (n = {len(sized)});",
        f"medians over the {len(shared)}-cell intersection shared by all of them.",
        "Families and post-training recipes differ, so this is NOT a controlled",
        "scale comparison; it is reported only as a descriptive check on C4.",
        "",
        "| model | size (B) | median recall | median precision |",
        "|---|---|---|---|",
    ]
    spread = []
    for m, sz in sorted(sized.items(), key=lambda kv: kv[1]):
        t = cell_table(df, m).loc[shared]
        spread.append((m, sz, t.recall.median(), t.precision.median()))
        lines.append(f"| {m} | {sz:g} | {f2(t.recall.median())} | {f2(t.precision.median())} |")
    rho_sz, p_sz = spearman([s[1] for s in spread], [s[2] for s in spread])
    lines += [
        "",
        f"- Spearman rho(size, median recall) across these {len(spread)} models: "
        f"{rho_sz:.2f} (p = {fp(p_sz)}); descriptive, confounded by recipe.",
        "",
    ]

    # ---------------- B3: recall-precision frontier ----------------
    frontier_models = sorted(full.model_name_formatted.unique())
    shared_f = sorted(
        set.intersection(*(set(cell_table(df, m).index) for m in frontier_models))
    )
    all_subsets = set(df.dataset_name_formatted.unique())
    dropped_subsets = sorted(all_subsets - {c[0] for c in shared_f})
    lines += [
        "## B3. Recall-precision frontier",
        "",
        f"Models: {len(frontier_models)} (excluded for partial coverage, 3-4",
        f"subsets only: {', '.join(PARTIAL_MODELS)}). Shared-subset intersection:",
        f"{len(shared_f)} of 31 subsets (dropped: {', '.join(dropped_subsets)}).",
        "Per-model median recall and precision over those shared cells; stage",
        "label from post_training_stage (frontier/other models have none).",
        "",
        "| model | stage | median recall | median precision |",
        "|---|---|---|---|",
    ]
    frontier = []
    for m in frontier_models:
        t = cell_table(df, m).loc[shared_f]
        stage = df.loc[df.model_name_formatted == m, "post_training_stage"].iloc[0]
        stage = stage if isinstance(stage, str) else "none"
        frontier.append((m, stage, t.recall.median(), t.precision.median()))
    for m, stage, r, p_ in sorted(frontier, key=lambda x: -x[2]):
        lines.append(f"| {m} | {stage} | {f2(r)} | {f2(p_)} |")
    rho, p_rho = spearman([x[2] for x in frontier], [x[3] for x in frontier])
    lines += [
        "",
        f"- Spearman rho(median recall, median precision) across {len(frontier)}",
        f"  models: **{rho:.2f}** (p = {fp(p_rho)}).",
        "",
        "## Limitations",
        "",
        "- This is the finest grain the authors released: per-(model, subset)",
        "  operating points, no per-question outputs, no variances. Sign tests",
        "  treat benchmark-subset cells within one model family as exchangeable",
        "  units; cells are not independent samples from a subset population.",
        "- o1 high/low-reasoning API variants (4 subsets) and TinyLlamaChat",
        "  (3 subsets) are excluded from all cross-model aggregates.",
        "- Single missing subsets (MMLU Math at 70B Base/SFT/PPO, MMLU History",
        "  at 8B Base and Mistral 7B, UMWP at 405B, GPQA-Diamond at OLMo 7B)",
        "  shrink paired-cell counts from 31 to 30 in B1 and to 27 in the",
        "  cross-model intersections; the affected cells are listed above.",
        "- The Tulu-3 ladder is one lineage per scale (no seeds); the 8B and",
        "  70B ladders are treated as separate, non-pooled replications.",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(HERE.parent.parent)}")

    # ---------------- figures ----------------
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGDIR.mkdir(parents=True, exist_ok=True)

    # B1 ladder figure
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    stage_order = list(LADDER["8B"])
    xs = range(len(stage_order))
    for ax, scale in zip(axes, LADDER):
        rec = [ladder_medians[(scale, st)][0] for st in stage_order]
        prec = [ladder_medians[(scale, st)][1] for st in stage_order]
        ax.plot(xs, rec, "o-", color="#2a7", label="median recall")
        ax.plot(xs, prec, "s--", color="#c66", label="median precision")
        ax.set_xticks(list(xs))
        ax.set_xticklabels(stage_order, fontsize=8)
        ax.set_title(f"Tulu-3 {scale} ladder (paired cells)")
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("median over paired (subset, scenario) cells")
    axes[0].legend(fontsize=8)
    fig.suptitle("AbstentionBench: abstention recall/precision across post-training stages", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGDIR / "abstentionbench_ladder.png", dpi=160)
    plt.close(fig)

    # B2 scale figure
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for family, marker in (("Instruct", "o"), ("Base", "s")):
        szs = sorted(sz for f, sz in sweep_medians if f == family)
        ax.plot(szs, [sweep_medians[(family, s)][0] for s in szs], marker + "-",
                color="#2a7", label=f"{family} recall")
        ax.plot(szs, [sweep_medians[(family, s)][1] for s in szs], marker + "--",
                color="#c66", label=f"{family} precision")
    ax.set_xscale("log")
    ax.set_xticks([8, 70, 405])
    ax.set_xticklabels(["8B", "70B", "405B"])
    ax.set_xlabel("Llama 3.1 parameters")
    ax.set_ylabel("median over shared (subset, scenario) cells")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("AbstentionBench: scale sweep, Llama 3.1 family")
    fig.tight_layout()
    fig.savefig(FIGDIR / "abstentionbench_scale.png", dpi=160)
    plt.close(fig)

    # B3 frontier figure
    stage_style = {
        "Base": ("#888", "v"),
        "SFT": ("#d90", "s"),
        "DPO": ("#2a7", "D"),
        "PPO RLVF": ("#27b", "P"),
        "Instruct": ("#a4c", "o"),
        "none": ("#c66", "o"),
    }
    fig, ax = plt.subplots(figsize=(7.5, 6))
    seen = set()
    for m, stage, r, p_ in frontier:
        color, marker = stage_style[stage]
        ax.scatter(p_, r, c=color, marker=marker, s=55, zorder=3,
                   label=stage if stage not in seen else None)
        seen.add(stage)
        ax.annotate(m, (p_, r), fontsize=6, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("median abstention precision (low = over-refusal on answerable)")
    ax.set_ylabel("median abstention recall (high = abstains when unanswerable)")
    ax.set_title(
        f"AbstentionBench frontier: {len(frontier)} models, {len(shared_f)} shared subsets\n"
        f"Spearman rho = {rho:.2f} (p = {fp(p_rho)})", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, title="post-training stage", loc="best")
    fig.tight_layout()
    fig.savefig(FIGDIR / "abstentionbench_frontier.png", dpi=160)
    plt.close(fig)
    print("wrote figures/abstentionbench_ladder.png, abstentionbench_scale.png, abstentionbench_frontier.png")


if __name__ == "__main__":
    main()
