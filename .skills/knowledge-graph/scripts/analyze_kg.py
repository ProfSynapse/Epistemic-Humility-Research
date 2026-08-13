#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology


def node_key(value: str, fallback: str) -> str:
    return value or fallback


# --- Conflict detection -----------------------------------------------------
# Borrowed in shape from semantica's conflicts module: a graph that silently
# holds two claims which cannot both be true is worse than one that flags the
# pair, because the reader cannot tell a settled reading from an unadjudicated
# one. These checks REPORT; none of them decides a winner. Adjudication is a
# lead-only judgement (see the experiment-wrapup skill).

# Polarity pairs that cannot both describe the same cause/effect relation.
# `decouples` conflicts with every value that asserts a coupling, because it
# denies exactly what they assert.
_COUPLING = {"increases", "decreases", "enables", "prevents", "causes", "mediates", "modulates", "limits"}
OPPOSING_POLARITY = {
    frozenset({"increases", "decreases"}),
    frozenset({"enables", "prevents"}),
    frozenset({"causes", "prevents"}),
    frozenset({"increases", "limits"}),
} | {frozenset({value, "decouples"}) for value in _COUPLING}

_STOP = set(
    "a an the of in on to for and is are by with from not does do that this it its as at or than more less".split()
)

# Matching thresholds. Two mechanisms contradict only if they describe the SAME
# cause acting on the SAME effect. Topic overlap is not enough: an earlier cut of
# this check matched on shared `related` atoms and produced 48 hits on a corpus
# whose real count is zero, because every calibration mechanism shares atoms with
# every other one. Cause and effect text must BOTH match.
CAUSE_THRESHOLD = 0.25
EFFECT_THRESHOLD = 0.20


def text_tokens(value: object) -> frozenset[str]:
    return frozenset(
        token for token in re.findall(r"[a-z0-9]+", str(value or "").lower()) if token not in _STOP and len(token) > 2
    )


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def detect_conflicts(notes: list, triples: list, index: NoteIndex) -> dict[str, list]:
    """Report node pairs and edges that need adjudication.

    Four checks, all read-only:
      1. opposing_polarity  - two live mechanisms on the same subject asserting
         polarities that cannot both hold.
      2. unresolved_contradicts - an explicit `contradicts` edge where neither
         endpoint has been deprecated, i.e. the flag was raised and never closed.
      3. supersession_cycle - deprecated_by chains that loop, so a reader
         following "the current revision" never terminates.
      4. supersession_chain - a successor that is itself deprecated; the reader
         must hop twice, and one hop is usually all anyone does.
      5. unadjudicated_disputed - an edge marked status: disputed carrying no
         evidence, which records a disagreement without the means to settle it.
    """
    by_id = {}
    for note in notes:
        if note.kg_id:
            by_id[note.kg_id] = note

    def is_deprecated(note) -> bool:
        kg = note.kg if isinstance(note.kg, dict) else {}
        return kg.get("status") == "deprecated" or bool(kg.get("deprecated_by"))

    # An explicit `different_from` edge between two nodes records that a human
    # already looked at the pair and ruled them distinct. Suppress those: a check
    # that keeps reporting a settled pair trains readers to ignore the report,
    # and the adjudication belongs in the graph rather than in a skip-list.
    adjudicated = set()
    for triple in triples:
        if triple.edge_type in {"different_from", "contradicts", "contradicted_by"}:
            left, right = triple.source_id or triple.source, triple.target_id or triple.target
            adjudicated.add(frozenset({left, right}))

    # 1. Opposing polarity on the same cause acting on the same effect.
    mechanisms = []
    for note in notes:
        if note.kg_type != "mechanism" or is_deprecated(note):
            continue
        polarity = note.frontmatter.get("polarity")
        if not isinstance(polarity, str):
            continue
        mechanisms.append(
            (
                note,
                polarity,
                text_tokens(note.frontmatter.get("cause")),
                text_tokens(note.frontmatter.get("effect")),
            )
        )

    opposing = []
    for i in range(len(mechanisms)):
        note_a, pol_a, cause_a, effect_a = mechanisms[i]
        for j in range(i + 1, len(mechanisms)):
            note_b, pol_b, cause_b, effect_b = mechanisms[j]
            if frozenset({pol_a, pol_b}) not in OPPOSING_POLARITY:
                continue
            cause_sim = jaccard(cause_a, cause_b)
            if cause_sim < CAUSE_THRESHOLD:
                continue
            effect_sim = jaccard(effect_a, effect_b)
            if effect_sim < EFFECT_THRESHOLD:
                continue
            left_id = note_a.kg_id or note_a.path.stem
            right_id = note_b.kg_id or note_b.path.stem
            if frozenset({left_id, right_id}) in adjudicated:
                continue
            opposing.append(
                {
                    "left": left_id,
                    "left_polarity": pol_a,
                    "right": right_id,
                    "right_polarity": pol_b,
                    "cause_similarity": round(cause_sim, 2),
                    "effect_similarity": round(effect_sim, 2),
                }
            )

    # 2. Explicit contradicts edges still open on both ends.
    unresolved = []
    for triple in triples:
        if triple.edge_type not in {"contradicts", "contradicted_by"}:
            continue
        source = by_id.get(triple.source_id)
        target = by_id.get(triple.target_id)
        if source is not None and is_deprecated(source):
            continue
        if target is not None and is_deprecated(target):
            continue
        unresolved.append(
            {"source": triple.source_id or triple.source, "target": triple.target_id or triple.target, "edge": triple.edge_type}
        )

    # 3 and 4. Supersession lineage integrity.
    successor = {}
    for note in notes:
        kg = note.kg if isinstance(note.kg, dict) else {}
        pointer = kg.get("deprecated_by")
        if note.kg_id and isinstance(pointer, str) and pointer:
            successor[note.kg_id] = pointer

    cycles, chains = [], []
    for start in successor:
        seen, node = [], start
        while node in successor:
            if node in seen:
                cycles.append({"cycle": seen[seen.index(node):] + [node]})
                break
            seen.append(node)
            node = successor[node]
        else:
            if len(seen) > 1:
                chains.append({"from": start, "hops": seen + [node], "head": node})

    # dedupe cycles reported once per member
    unique_cycles, seen_cycles = [], set()
    for entry in cycles:
        key = frozenset(entry["cycle"])
        if key not in seen_cycles:
            seen_cycles.add(key)
            unique_cycles.append(entry)

    # 5. Disputed edges with no evidence to settle them.
    disputed = []
    for note in notes:
        for entry in note.frontmatter.get("relationships") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("status") != "disputed":
                continue
            if entry.get("evidence"):
                continue
            disputed.append(
                {
                    "note": note.kg_id or note.path.stem,
                    "edge": entry.get("type"),
                    "target": entry.get("target_id") or entry.get("target"),
                }
            )

    return {
        "opposing_polarity": opposing,
        "unresolved_contradicts": unresolved,
        "supersession_cycles": unique_cycles,
        "supersession_chains": chains,
        "unadjudicated_disputed": disputed,
    }


def analyze(paths: list[Path], root: Path, ontology_path: Path | None) -> dict[str, object]:
    ontology = load_ontology(ontology_path) if ontology_path else load_ontology()
    index = NoteIndex.build(root)
    notes, findings = collect_graph_notes(paths, root=root)
    triples = collect_triples(notes, ontology, index=index)

    edge_counts = Counter(triple.edge_type for triple in triples)
    source_counts = Counter(node_key(triple.source_id, triple.source) for triple in triples)
    target_counts = Counter(node_key(triple.target_id, triple.target) for triple in triples)
    degree_counts = source_counts + target_counts

    known_nodes = {node_key(note.kg_id, note.title): note for note in notes}
    outgoing_nodes = set(source_counts)
    incoming_nodes = set(target_counts)
    orphan_nodes = sorted(key for key in known_nodes if key not in outgoing_nodes and key not in incoming_nodes)
    unresolved = [triple.as_dict() for triple in triples if not triple.target_path]
    legacy = [triple.as_dict() for triple in triples if triple.legacy]

    by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    for triple in triples:
        by_source[node_key(triple.source_id, triple.source)].append(triple.as_dict())

    return {
        "graph_notes": len(notes),
        "edge_count": len(triples),
        "edge_types": dict(edge_counts.most_common()),
        "top_degree": degree_counts.most_common(20),
        "top_outgoing": source_counts.most_common(20),
        "top_incoming": target_counts.most_common(20),
        "orphan_nodes": orphan_nodes,
        "unresolved_targets": unresolved,
        "legacy_edges": legacy,
        "conflicts": detect_conflicts(notes, triples, index),
        "scan_findings": [finding.as_dict() for finding in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze exported Obsidian knowledge graph metadata.")
    parser.add_argument("paths", nargs="*", help="Markdown files or folders. Defaults to the vault root.")
    parser.add_argument("--root", default=".", help="Vault root. Defaults to current directory.")
    parser.add_argument("--ontology", default="", help="Path to edge ontology YAML.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ontology_path = Path(args.ontology).resolve() if args.ontology else None
    report = analyze([Path(path) for path in args.paths], root, ontology_path)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"Graph notes: {report['graph_notes']}")
    print(f"Typed edges: {report['edge_count']}")
    print("\nTop edge types:")
    for edge, count in list(report["edge_types"].items())[:20]:
        print(f"  {edge}: {count}")
    print("\nTop degree nodes:")
    for node, count in report["top_degree"]:
        print(f"  {node}: {count}")
    print(f"\nUnresolved targets: {len(report['unresolved_targets'])}")
    print(f"Legacy edges: {len(report['legacy_edges'])}")
    print(f"Orphan graph nodes: {len(report['orphan_nodes'])}")

    conflicts = report["conflicts"]
    labels = {
        "opposing_polarity": "opposing-polarity mechanism pairs",
        "unresolved_contradicts": "open `contradicts` edges",
        "supersession_cycles": "supersession cycles",
        "supersession_chains": "multi-hop supersession chains",
        "unadjudicated_disputed": "disputed edges with no evidence",
    }
    total = sum(len(conflicts[key]) for key in labels)
    print(f"\nConflicts needing adjudication: {total}")
    for key, label in labels.items():
        rows = conflicts[key]
        if not rows:
            continue
        print(f"  {label}: {len(rows)}")
        for row in rows[:10]:
            if key == "opposing_polarity":
                print(
                    f"    {row['left']} [{row['left_polarity']}]  vs  {row['right']} [{row['right_polarity']}]"
                    f"  (cause {row['cause_similarity']}, effect {row['effect_similarity']})"
                )
            elif key == "unresolved_contradicts":
                print(f"    {row['source']} -{row['edge']}-> {row['target']}")
            elif key == "supersession_cycles":
                print(f"    {' -> '.join(row['cycle'])}")
            elif key == "supersession_chains":
                print(f"    {row['from']} -> ... -> {row['head']} ({len(row['hops'])} hops)")
            else:
                print(f"    {row['note']} -{row['edge']}-> {row['target']}")
        if len(rows) > 10:
            print(f"    ... and {len(rows) - 10} more (use --json for the full list)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
