#!/usr/bin/env python3
"""Generate the substrate-coverage table for the actuation paper (Paper 5).

Every row is built from governed YAML, never from this manuscript's own
prose: for each cell slug named in Appendix A's traceability map, the
script reads experiments/<slug>/experiment.yaml with yaml.safe_load (status,
checkpoint.repo, checkpoint.revision, verdict), and falls back to the cell's
own cell.yaml / families/*.yaml / model_matrix.yaml when checkpoint.repo is
empty. The declared-vs-launched split is a hard distinction, not a summary:
where a manifest declares a matrix of checkpoints but experiment.yaml does
not encode which subset actually launched (that information lives only in
each amendment's Outcome prose), the script reports the declared count and
quotes the governed `verdict` field rather than inventing a launched number.
DECLARED-only rows support no experimental claim about the model in question.

Deterministic: no randomness, no network, CPU only. Regenerate with:

    python3 papers/paper-5-actuation/scripts/build_coverage_table.py --write

Without --write, the table prints to stdout instead of touching the
manuscript. --write replaces the block between the
`<!-- BEGIN GENERATED: substrate-coverage-table -->` and
`<!-- END GENERATED: substrate-coverage-table -->` markers in
manuscript.md, so re-running the script is idempotent and the appendix can
never drift from the governed YAML it was built from.

Two columns cannot be derived from YAML at all:

- "Manuscript section(s) citing it" names a location in THIS document's own
  prose, so it is necessarily hand-curated by reading the manuscript body
  (SECTION_MAP below), not computed from governed docs. It is verified
  against the section headers and inline citations current as of this
  script's authorship (2026-08-11; SECTION_MAP re-verified against the
  2026-08-17 restructure numbering); re-verify after any section renumbering
  or Appendix A edit.
- A handful of Appendix A slugs are `type: historical-amendment` migrations
  whose experiment.yaml explicitly instructs: "Do not infer missing machine
  fields without hand-reading AMENDMENT.md." For those the script reports
  UNRESOLVED and quotes the disclaimer verbatim rather than guessing a
  substrate from cell.yaml-style fallback files that do not exist for them.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
MANUSCRIPT = ROOT / "papers" / "paper-5-actuation" / "manuscript.md"
EXP = ROOT / "experiments"

BEGIN_MARK = "<!-- BEGIN GENERATED: substrate-coverage-table -->"
END_MARK = "<!-- END GENERATED: substrate-coverage-table -->"

# Governed-doc-fallback file names to search, in priority order, when
# experiment.yaml's checkpoint.repo is empty. Every hit is walked
# recursively for repo/model/substrate/family declarations (see
# _walk_declared below) rather than parsed against a fixed schema, because
# these files do not share one.
FALLBACK_GLOBS = ["cell.yaml", "model_matrix.yaml", "families/*.yaml", "families.yaml"]

# ---------------------------------------------------------------------------
# Manuscript section citation map (hand-curated; see module docstring).
#
# Each entry's provenance is one of:
#   backtick @<line>   - the slug (or its AMENDMENT.md path) is cited
#                         verbatim in backticks in the manuscript body at
#                         the given line, e.g. `qwen35-4b-midband-heldout`.
#   content @<line>    - the section's prose narrates the cell's numbers
#                         (matched against its Appendix A claim / AMENDMENT
#                         Outcome) without naming the slug verbatim.
#   NOT NARRATED       - no reader-facing section (1-7) discusses this cell;
#                         it exists only in the front-matter evidence_base
#                         list and the Appendix A row. Flagged in the coverage
#                         report as a provenance gap, not silently sourced.
# ---------------------------------------------------------------------------
SECTION_MAP: dict[str, str] = {
    "causal-confidence-steering": "4.1",  # content @362-368
    "first-person-injection": "4.1",  # content @370-377
    "radial-anti-propensity-steering": "4.2",  # content @399-443 (Fig 6)
    "doubt-regulated-caution": "NOT NARRATED IN BODY (front matter + Appendix A only; "
    "resolved 2026-08-13: AC remains appendix-only by PI ruling -- the paper's "
    "scope is deliberately raw-base/untrained substrates and AC is "
    "trained-lineage predecessor context -- AC is this cell's legacy amendment label)",
    "second-person-doubt-prime": "4.3",  # content @453-457
    "oracle-dissociation-prime": "4.3",  # content @461-465
    "divergent-pool-own-readout": "4.3",  # content @469-473
    "probe-as-reward": "4.4",  # content @484-499
    "doubt-gated-caution-tighten": "4.5",  # content @508-543 (first robust positive)
    "ungated-vs-gated-dose-matched": "4.5",  # backtick @520
    "qwen35-4b-midband-doubt-snap": "4.5",  # content @558-562, implicit precursor to -heldout
    "qwen35-4b-midband-heldout": "4.5",  # backtick @563
    "snap-seed-sampled-decode-replication": "4.5",  # backtick @568
    "gate-contribution-factorial": "4.8",
    "j-space-localization-qwen3-4b": "4.6",  # content @582-594
    "j-space-midband-dose-calibration-qwen3-4b": "4.6",  # content @596-598
    "j-space-calibrated-layer-contrast-qwen3-4b": "4.6",  # content @599-604
    "j-space-layer-contrast-replication-qwen3-4b": "4.6",  # content @615-620
    "j-space-layer-contrast-rep2-multisource": "4.6",  # content @621-627
    "j-space-token-targeted-refusal-qwen3-4b": "4.7",  # content @645-660
    "h6-genstream-hook-firing-check": "6.4",  # content @1273-1287 (not in Results at all)
    "jspace-family-atlas": "6.3",  # backtick @1222
    "doubt-snap-cross-family-confirmatory": "6.5",  # backtick @1361
    "dark-actuator-screen": "4.7",  # folded sentence at end of 4.7 (restructure)
    "aq-sycophancy-activation-actuator": "6.5",  # number-free future-work sentence, item 8
    "rr-cross-family-raw-refusal": "4.8, 6.5",
    "llama-atlas-gated-wide-instrument-retest": "4.8",  # content in the cross-family spectrum paragraph
    "wide-instrument-control-rescore": "4.8, 6.4",  # wide re-score of the 6.4 controls; 4.8 qwen sign-opposition at the raw-base point
    "no-abstention-prompt-gated-replication": "3.7, 5, 6.1, 6.4",  # instruction-free replication; disclosed 3.7, scoped 5/6.1, reported 6.4
    "llama-hs17-direction-specificity": "4.8, 6.5",  # llama mid-band write verified direction-specific; updates escalation items 1 and 4
    "llama-hs17-wide-instrument-rescore": "4.8, 6.5",  # wide-instrument regeneration of the hs17 operating point
    "qwen3-4b-l34-placebo-seed-census": "4.8, 6.4, 7",  # late-site 15-seed census: distributional specificity PASS, sign-consistency FAIL
    "rr2-mistral-adjudicated-refusal-confirm": "4.8, 6.5",
    "abstention-wide-instrument-calibration": "4.8, 6.5",
    "rr3-corrected-placebo-replication": "4.8, 6.5",
    "placebo-seed-distribution-census": "4.8, 6.5",
    "placebo-signflip-question-type-analysis": "4.8",
    "margin-evidence-responsiveness-worldknown": "4.6, 6.4",  # backtick @592, @1269
    "evidence-response-direction-search": "NOT NARRATED IN BODY (front matter + Appendix A only; "
    "no flagged open-work item, unlike doubt-regulated-caution)",
    "gemma4-e4b-kv-seam-quarantine": "4.8, Appendix E",
    "gemma4-e4b-pocket-ladder": "4.8, Appendix E",
    # New Appendix A rows from the 2026-08-17 restructure:
    "jlens-trained-checkpoint-midband-ablation": "6.4 (limits bullet only; body narration cut per PI ruling 2026-08-20 -- Appendix A carries the numbers)",
    "correctness-direction-rotation": "6.5",
    "correctness-subspace-overlap": "6.5",
    "correctness-geometry-scale-ladder": "6.5",  # scale-conditional sharpening, opening paragraph
    "j-space-cross-family-layer-contrast": "6.5",  # per-family mid-band held-out contrast (items 1/2/4); pointed to from the 4.8 llama caution
    "refusal-axis-ablation-confirmatory": "6.6",
    "caution-install-bounded-site-sweep": "6.6",
    "caution-ablation-rederivation": "NOT NARRATED IN BODY (front matter + Appendix A provenance row only)",
    "idk-switch-naming-confirmatory": "4.5, 4.8",
}

APPENDIX_A_ROW_RE = re.compile(
    r"^\|(?P<claim>.+?)\|\s*`experiments/(?P<slug>[a-zA-Z0-9_-]+)/AMENDMENT\.md`(?P<locator>[^|]*)\|\s*(?P<status>.+?)\|\s*$"
)


def parse_appendix_a_slugs() -> list[tuple[str, str]]:
    """Return [(slug, paper_claim), ...] in table order, parsed from
    Appendix A of manuscript.md. This is the ONLY thing read from the
    manuscript's own prose -- the slug list and each row's reader-facing
    claim text, both of which are Appendix A's own governed content, not
    narrative prose. No experimental fact (status/substrate/declared vs
    launched) is ever taken from here.
    """
    text = MANUSCRIPT.read_text()
    m = re.search(r"## Appendix A\. Traceability Map\n(.*?)\n## Appendix B", text, re.S)
    if not m:
        raise RuntimeError("Could not locate Appendix A block in manuscript.md")
    rows: list[tuple[str, str]] = []
    for line in m.group(1).splitlines():
        row = APPENDIX_A_ROW_RE.match(line)
        if row:
            rows.append((row.group("slug"), row.group("claim").strip()))
    if not rows:
        raise RuntimeError("Appendix A parse found zero rows -- table format likely changed")
    return rows


def _walk_declared(node: Any, path: tuple[str, ...] = ()) -> list[dict[str, str]]:
    """Recursively collect checkpoint-like declarations from an arbitrary
    parsed-YAML structure. Fallback config files (cell.yaml,
    model_matrix.yaml, families/*.yaml) use different schemas per
    experiment, so this walks the whole tree rather than assuming one
    layout, collecting every dict that declares at least one of
    repo/model/substrate/family/cell_id.
    """
    found: list[dict[str, str]] = []
    if isinstance(node, dict):
        # Only treat a trigger key as a declaration if its value is itself a
        # scalar. A scalar "family: qwen35-4b" is a real declaration; a
        # nested "family: {id: ..., model: ...}" is a container to recurse
        # into, not a value to stringify (stringifying it would blob the
        # whole sub-dict into one field).
        scalar_keys = {
            k for k in ("repo", "model", "substrate", "family", "cell_id")
            if k in node and not isinstance(node[k], (dict, list))
        }
        # A scalar `id:` counts as a declaration only inside a `families:`
        # block (e.g. placebo-seed-distribution-census's cell.yaml, whose
        # per-family blocks carry `id: qwen35-4b` rather than a repo/model
        # key). `id` is far too generic to trigger on globally -- opaque-id
        # fields, row ids, and the like would pollute the walk.
        id_is_declaration = (
            "families" in path
            and "id" in node
            and not isinstance(node["id"], (dict, list))
        )
        if id_is_declaration:
            scalar_keys.add("id")
        # Collect `id` only when it triggered as a families-block declaration.
        # Elsewhere `id` is a lane/arm label (e.g. abstention-wide-instrument-
        # calibration's QH/QL lanes) and collecting it would split entries
        # that dedupe identical today.
        collect_keys = ["cell_id", "family", "repo", "model", "revision", "substrate", "scale_tier"]
        if id_is_declaration:
            collect_keys.append("id")
        if scalar_keys:
            entry = {
                k: str(node[k])
                for k in collect_keys
                if k in node and not isinstance(node[k], (dict, list))
            }
            if entry:
                found.append(entry)
        for k, v in node.items():
            found.extend(_walk_declared(v, path + (str(k),)))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk_declared(item, path))
    return found


def _dedupe(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    out: list[dict[str, str]] = []
    for e in entries:
        key = tuple(sorted(e.items()))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def _format_declared(entries: list[dict[str, str]]) -> str:
    parts = []
    for e in entries:
        label = e.get("repo") or e.get("model") or e.get("substrate") or e.get("family")
        if not label and "id" in e:
            label = f"family id `{e['id']}` (HF repo/revision resolves via the fleet model_matrix.yaml)"
        label = label or "?"
        rev = e.get("revision")
        tier = f" [{e['scale_tier']}]" if "scale_tier" in e else ""
        cid = f" ({e['cell_id']})" if "cell_id" in e else ""
        s = f"{label}{tier}{cid}"
        if rev:
            s += f" @ {rev}"
        parts.append(s)
    return "; ".join(parts)


def find_fallback_files(slug: str) -> list[Path]:
    exp_dir = EXP / slug
    hits: list[Path] = []
    for pattern in FALLBACK_GLOBS:
        hits.extend(sorted(exp_dir.glob(pattern)))
    return hits


def build_row(slug: str, claim: str) -> dict[str, str]:
    exp_yaml_path = EXP / slug / "experiment.yaml"
    if not exp_yaml_path.exists():
        return {
            "slug": slug,
            "status": "MISSING",
            "substrate": f"UNRESOLVED -- {exp_yaml_path} does not exist",
            "declared_launched": "UNRESOLVED",
            "section": SECTION_MAP.get(slug, "UNMAPPED (add to SECTION_MAP)"),
        }

    data = yaml.safe_load(exp_yaml_path.read_text()) or {}
    status = str(data.get("status", "UNKNOWN"))
    checkpoint = data.get("checkpoint") or {}
    repo = str(checkpoint.get("repo") or "").strip()
    revision = str(checkpoint.get("revision") or "").strip()
    verdict = str(data.get("verdict") or "").strip()
    exp_type = str(data.get("type") or "")

    # Historical-amendment migrations: experiment.yaml itself instructs not
    # to infer a substrate from other files.
    migration = data.get("migration") or {}
    migration_note = str(migration.get("notes") or "")
    if exp_type == "historical-amendment" and not repo and migration_note:
        return {
            "slug": slug,
            "status": status,
            "substrate": (
                "UNRESOLVED -- historical-amendment migration; checkpoint fields "
                f"intentionally blank. experiment.yaml migration.notes: \"{migration_note}\""
            ),
            "declared_launched": "UNRESOLVED (hand-read AMENDMENT.md required)",
            "section": SECTION_MAP.get(slug, "UNMAPPED (add to SECTION_MAP)"),
        }

    # Real single-substrate checkpoint declared directly.
    if repo and "/" in repo:
        substrate = f"`{repo}` @ `{revision}`" if revision else f"`{repo}` (revision not recorded)"
        return {
            "slug": slug,
            "status": status,
            "substrate": substrate,
            "declared_launched": "1 declared / 1 launched (single-substrate cell)",
            "section": SECTION_MAP.get(slug, "UNMAPPED (add to SECTION_MAP)"),
        }

    # checkpoint.repo populated but not a real repo id (e.g. "cross-family
    # matrix", "(none; CPU-only re-read ...)") -- keep it verbatim, it is
    # already informative.
    if repo:
        substrate_note = f"checkpoint.repo (verbatim): \"{repo}\""
        if revision:
            substrate_note += f"; checkpoint.revision (verbatim): \"{revision}\""
    else:
        substrate_note = "checkpoint.repo empty in experiment.yaml"

    # Fall back to cell.yaml / families/*.yaml / model_matrix.yaml.
    fallback_files = find_fallback_files(slug)
    declared: list[dict[str, str]] = []
    for f in fallback_files:
        try:
            parsed = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        declared.extend(_walk_declared(parsed))
    declared = _dedupe(declared)

    if not declared:
        if fallback_files:
            inspected = ", ".join(str(f.relative_to(EXP / slug)) for f in fallback_files)
            gap = (
                f"fallback file(s) inspected ({inspected}) but no recognizable "
                "checkpoint declaration found (repo/model/substrate/family/"
                "cell_id, or families.*.id)"
            )
        else:
            gap = "no cell.yaml/families/model_matrix.yaml fallback file exists"
        return {
            "slug": slug,
            "status": status,
            "substrate": f"UNRESOLVED -- {substrate_note}; {gap}",
            "declared_launched": "UNRESOLVED (hand-read AMENDMENT.md required)",
            "section": SECTION_MAP.get(slug, "UNMAPPED (add to SECTION_MAP)"),
        }

    substrate = (
        f"{substrate_note}. DECLARED in "
        f"{', '.join(str(f.relative_to(EXP / slug)) for f in fallback_files)}: "
        f"{_format_declared(declared)}"
    )
    verdict_note = f" Governed verdict field: \"{verdict[:220]}{'...' if len(verdict) > 220 else ''}\"" if verdict else ""
    declared_launched = (
        f"DECLARED {len(declared)} checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-"
        f"separable from YAML; see AMENDMENT.md Outcome.{verdict_note}"
    )
    return {
        "slug": slug,
        "status": status,
        "substrate": substrate,
        "declared_launched": declared_launched,
        "section": SECTION_MAP.get(slug, "UNMAPPED (add to SECTION_MAP)"),
    }


def render_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "## Appendix B. Substrate Coverage Table",
        "",
        "Generated by `papers/paper-5-actuation/scripts/build_coverage_table.py` "
        "(deterministic, CPU-only, no network; regenerate with `--write`) from "
        "`experiments/<slug>/experiment.yaml`, falling back to that cell's own "
        "`cell.yaml` / `families/*.yaml` / `model_matrix.yaml` where "
        "`checkpoint.repo` is empty. Every row traces to governed YAML, never to "
        "this manuscript's own prose. **DECLARED-only rows support no claim about "
        "the model(s) they name**: a checkpoint appearing in a matrix config that "
        "the cell declared is not evidence the cell produced an outcome on that "
        "checkpoint. Where the launched subset is not separable from YAML alone, "
        "the row says so explicitly and quotes the governed `verdict` field rather "
        "than a machine-derived count.",
        "",
        BEGIN_MARK,
        "",
        "| Cell slug | experiment.yaml status | Substrate(s) | Declared vs. launched | Manuscript section(s) |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['slug']}` | {r['status']} | {r['substrate']} | {r['declared_launched']} | {r['section']} |"
        )
    lines.append("")
    lines.append(END_MARK)
    return "\n".join(lines)


def write_into_manuscript(appendix_block: str) -> None:
    text = MANUSCRIPT.read_text()
    if BEGIN_MARK not in text or END_MARK not in text:
        raise RuntimeError(
            "Coverage-table markers not found in manuscript.md. Insert the "
            "Appendix B header/intro plus markers once by hand, then rerun --write."
        )
    pre, rest = text.split(BEGIN_MARK, 1)
    _, post = rest.split(END_MARK, 1)
    inner = appendix_block.split(BEGIN_MARK, 1)[1].split(END_MARK)[0]
    new_text = pre + BEGIN_MARK + inner + END_MARK + post
    MANUSCRIPT.write_text(new_text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="Write the table block into manuscript.md")
    args = ap.parse_args()

    slug_claims = parse_appendix_a_slugs()
    rows = [build_row(slug, claim) for slug, claim in slug_claims]
    block = render_markdown(rows)

    unmapped = [r["slug"] for r in rows if r["section"].startswith("UNMAPPED")]
    if unmapped:
        raise SystemExit(f"SECTION_MAP is missing entries for: {unmapped}")

    if args.write:
        write_into_manuscript(block)
        print(f"Wrote coverage table for {len(rows)} cells into {MANUSCRIPT}")
    else:
        print(block)


if __name__ == "__main__":
    main()
