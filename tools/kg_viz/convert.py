#!/usr/bin/env python3
"""Convert the typed Obsidian knowledge graph into visualization-ready forms.

This is the shared foundation for the KG-viz starter stack: both the static
web explorer (``kg-graph.html``) and the analysis notebook (``analysis.ipynb``)
consume what this module produces.

It imports the vendored ``knowledge-graph`` skill scripts (``kg_common``) to
read the library vault exactly the way ``export_kg.py`` does, then applies the
three transformations the raw export needs before it is safe to visualize:

1. INVERSE-PAIR DEDUPE. The export stores many relationships in both
   directions (e.g. ``proposes`` on the paper and ``proposed_by`` on the
   method). Loading every row doubles those edges and skews every degree /
   centrality / community metric. We collapse each true inverse pair to one
   logical edge using the ``inverse`` field of the edge ontology, while
   KEEPING genuinely-distinct directed edges and any parallel typed edges
   (this is a typed multigraph: a paper can both ``uses`` and ``evaluates_on``
   the same dataset).

2. NODE TYPING. Every node carries its ``kg.type`` (paper / method / metric /
   dataset / model / term / mechanism). For any endpoint that is not itself a
   graph note, the type is inferred from the ``kg.id`` namespace prefix.

3. METADATA HONESTY. ``confidence`` is sparse and ``status`` / ``evidence`` are
   empty across the current vault. We pass these through as-is (empty stays
   empty) so downstream visuals encode them only when present and never invent
   values.

Public API (stable contract consumed by the web page and the notebook):

    load_records(root=None) -> (nodes: list[dict], edges: list[dict])
    to_cytoscape_elements(root=None) -> {"nodes": [...], "edges": [...]}
    to_networkx(root=None) -> networkx.MultiDiGraph   # networkx imported lazily
    graph_stats(nodes, edges) -> dict

CLI:

    python tools/kg_viz/convert.py --out tools/kg_viz/data/graph.cytoscape.json
    python tools/kg_viz/convert.py --emit stats        # print summary, no file

Provenance note: this reads the vault live (no network, no cache); the SQLite
search index (.kg/index.sqlite) is NOT used. Run it from the repo root or pass
``--root`` to point at a different vault.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ── locate the vendored knowledge-graph skill scripts ──────────────────────
# tools/kg_viz/convert.py  ->  parents[2] is the repo (or worktree) root.
REPO_ROOT = Path(__file__).resolve().parents[2]
_KG_SCRIPTS = REPO_ROOT / ".agents" / "skills" / "knowledge-graph" / "scripts"
if str(_KG_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_KG_SCRIPTS))

try:
    from kg_common import (  # type: ignore  # noqa: E402
        NoteIndex,
        collect_graph_notes,
        collect_triples,
        load_ontology,
    )
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        f"Could not import kg_common from {_KG_SCRIPTS}. "
        "Run from the repo root and ensure PyYAML is installed."
    ) from exc

DEFAULT_VAULT = REPO_ROOT / "library"
DEFAULT_OUTPUT = REPO_ROOT / "tools" / "kg_viz" / "data" / "graph.cytoscape.json"

NODE_TYPES = (
    "paper",
    "method",
    "metric",
    "dataset",
    "model",
    "term",
    "mechanism",
    "gap",
    "experiment",
)


def _inverse_map(ontology: dict[str, Any]) -> dict[str, str]:
    """edge_type -> its ontology inverse (defaults to itself when unspecified)."""
    edges = ontology.get("edges", {})
    out: dict[str, str] = {}
    for edge, spec in edges.items():
        if isinstance(spec, dict):
            out[str(edge)] = str(spec.get("inverse") or edge)
    return out


def _canonical_key(
    source: str, target: str, edge_type: str, inverse: dict[str, str]
) -> tuple[str, str, str]:
    """Direction-aware identity for a logical edge.

    True inverse pairs (``X proposes Y`` / ``Y proposed_by X``) collapse to one
    key. Symmetric edges (inverse == self, e.g. ``related_to``) are treated as
    undirected. Two genuinely-different directed edges that happen to share an
    active type (``X uses Y`` vs ``Y uses X``) do NOT collapse.
    """
    inv = inverse.get(edge_type, edge_type)
    if edge_type == inv:  # symmetric / self-inverse -> undirected
        a, b = sorted((source, target))
        return (a, edge_type, b)
    primary = min(edge_type, inv)
    if edge_type == primary:
        return (source, primary, target)
    return (target, primary, source)


def _infer_type(kg_id: str, fallback: str = "") -> str:
    """Node type from kg.type when known, else the kg.id namespace prefix."""
    if fallback:
        return fallback
    if ":" in kg_id:
        prefix = kg_id.split(":", 1)[0]
        if prefix in NODE_TYPES:
            return prefix
    return "unknown"


def load_records(root: Path | str | None = None) -> tuple[list[dict], list[dict]]:
    """Read the vault and return (nodes, edges).

    nodes: {"id", "label", "type", "status"}
    edges: {"id", "source", "target", "edge_type", "confidence", "status",
            "evidence"}  with inverse pairs deduped and the first-seen
            direction / edge_type preserved.
    """
    vault = Path(root).resolve() if root else DEFAULT_VAULT.resolve()
    ontology = load_ontology()
    inverse = _inverse_map(ontology)
    index = NoteIndex.build(vault)
    notes, _findings = collect_graph_notes([], root=vault)

    nodes: dict[str, dict] = {}
    for note in notes:
        if not note.kg_id:
            continue
        nodes[note.kg_id] = {
            "id": note.kg_id,
            "label": note.title,
            "type": _infer_type(note.kg_id, note.kg_type),
            "status": str(note.kg.get("status") or ""),
        }

    triples = collect_triples(notes, ontology, index=index)
    seen: set[tuple[str, str, str]] = set()
    edges: list[dict] = []
    for t in triples:
        src, tgt = t.source_id, t.target_id
        if not src or not tgt:
            # Cannot anchor an edge without both kg.ids; skip (none today).
            continue
        key = _canonical_key(src, tgt, t.edge_type, inverse)
        if key in seen:
            continue
        seen.add(key)
        # Ensure any endpoint missing from the graph-note set still becomes a
        # node (future-proofing; the current vault has none).
        for nid in (src, tgt):
            if nid not in nodes:
                nodes[nid] = {
                    "id": nid,
                    "label": nid.split(":", 1)[-1] if ":" in nid else nid,
                    "type": _infer_type(nid),
                    "status": "",
                }
        edges.append(
            {
                "id": f"{src}|{t.edge_type}|{tgt}",
                "source": src,
                "target": tgt,
                "edge_type": t.edge_type,
                "confidence": t.confidence or "",
                "status": t.status or "",
                "evidence": list(t.evidence or []),
            }
        )

    return list(nodes.values()), edges


def to_cytoscape_elements(root: Path | str | None = None) -> dict:
    """Cytoscape.js elements object: {"nodes": [...], "edges": [...]}.

    Each element is wrapped in the canonical ``{"data": {...}}`` shape.
    """
    nodes, edges = load_records(root)
    return {
        "nodes": [{"data": n} for n in nodes],
        "edges": [{"data": e} for e in edges],
    }


def to_networkx(root: Path | str | None = None):
    """Build a ``networkx.MultiDiGraph`` (parallel typed edges preserved).

    Edge key is the edge_type so parallel typed edges between the same pair are
    distinct. networkx is imported lazily so the web/CLI path does not require
    it.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "networkx is required for to_networkx(). "
            "pip install -r tools/kg_viz/requirements.txt"
        ) from exc

    nodes, edges = load_records(root)
    g = nx.MultiDiGraph()
    for n in nodes:
        g.add_node(n["id"], type=n["type"], label=n["label"], status=n["status"])
    for e in edges:
        g.add_edge(
            e["source"],
            e["target"],
            key=e["edge_type"],
            edge_type=e["edge_type"],
            confidence=e["confidence"],
            status=e["status"],
            evidence=e["evidence"],
        )
    return g


def graph_stats(nodes: list[dict], edges: list[dict]) -> dict:
    """Summary counts for reporting / smoke verification."""
    from collections import Counter

    participating = {e["source"] for e in edges} | {e["target"] for e in edges}
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "edgeless_nodes": sum(1 for n in nodes if n["id"] not in participating),
        "node_types": dict(Counter(n["type"] for n in nodes)),
        "edge_types": dict(Counter(e["edge_type"] for e in edges).most_common()),
        "confidence": dict(
            Counter(e["confidence"] or "<empty>" for e in edges)
        ),
        "status": dict(Counter(e["status"] or "<empty>" for e in edges)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--root",
        default="",
        help="Vault root (defaults to <repo>/library).",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="Output path for Cytoscape elements JSON.",
    )
    parser.add_argument(
        "--emit",
        choices=["cytoscape", "stats"],
        default="cytoscape",
        help="cytoscape: write the elements JSON. stats: print a summary only.",
    )
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args(argv)

    root = args.root or None
    nodes, edges = load_records(root)
    stats = graph_stats(nodes, edges)

    if args.emit == "stats":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    elements = {
        "nodes": [{"data": n} for n in nodes],
        "edges": [{"data": e} for e in edges],
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(elements, ensure_ascii=False, indent=args.indent) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {out_path} :: {stats['nodes']} nodes, {stats['edges']} edges "
        f"({stats['edgeless_nodes']} edge-less)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
