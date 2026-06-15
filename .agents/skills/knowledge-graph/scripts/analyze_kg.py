#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology


def node_key(value: str, fallback: str) -> str:
    return value or fallback


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
