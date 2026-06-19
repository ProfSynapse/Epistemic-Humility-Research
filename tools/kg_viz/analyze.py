#!/usr/bin/env python3
"""Structural analysis of the typed research knowledge graph.

Deterministic, CLI-runnable companion to the static ``kg-graph.html`` explorer.
Loads the graph through the shared ``convert.py`` contract, runs analysis that
goes BEYOND what ``analyze_kg.py`` already reports, and writes artifacts:

    data/stats.json        machine-readable summary (counts, top centrality,
                           communities, lineage, components)
    data/graph.figure.png  static publication figure (node colour = type)
    data/graph.sigma.html  interactive standalone graph  (only if ipysigma is
                           installed; otherwise skipped with a notice)

Run:

    python3 tools/kg_viz/analyze.py            # writes artifacts + prints summary
    python3 tools/kg_viz/analyze.py --quiet    # artifacts only

Required: networkx, matplotlib, pandas (see requirements.txt). Optional:
ipysigma (interactive HTML), igraph+leidenalg (Leiden backend). Everything
optional degrades gracefully so the core analysis always completes.

Data realities (verified against the live vault, not assumed):
- 182 typed nodes, 0 edge-less; 619 raw directed triples dedupe to 498 logical
  edges (convert.py collapses inverse pairs).
- confidence is sparse; status / evidence are empty on every edge today, so the
  figure leads with node TYPE and we never invent metadata.
- Community detection uses Louvain (native). leiden_communities is a dispatch
  API needing an external backend, so Leiden is attempted then skipped.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# tools/kg_viz/analyze.py  ->  import the sibling convert module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert  # noqa: E402

import networkx as nx  # noqa: E402
from networkx.algorithms import community as C  # noqa: E402

TYPE_COLORS = {
    "paper": "#4e79a7",
    "method": "#f28e2b",
    "metric": "#59a14f",
    "dataset": "#e15759",
    "model": "#b07aa1",
    "term": "#76b7b2",
    "mechanism": "#edc948",
    "unknown": "#9c9c9c",
}


def project_undirected(G: "nx.MultiDiGraph") -> "nx.Graph":
    """Collapse the directed multigraph to a weighted simple graph."""
    UG = nx.Graph()
    UG.add_nodes_from(G.nodes(data=True))
    for u, v, _d in G.edges(data=True):
        if UG.has_edge(u, v):
            UG[u][v]["weight"] += 1
        else:
            UG.add_edge(u, v, weight=1)
    return UG


def run_analyze_kg() -> dict:
    """Call the knowledge-graph skill's analyze_kg.py (don't recompute)."""
    analyze_py = convert._KG_SCRIPTS / "analyze_kg.py"
    res = subprocess.run(
        [sys.executable, str(analyze_py), "--root", str(convert.REPO_ROOT),
         "--json", str(convert.DEFAULT_VAULT)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return {"error": res.stderr.strip()}
    return json.loads(res.stdout)


def centrality_table(UG: "nx.Graph"):
    import pandas as pd

    pr = nx.pagerank(UG, weight="weight")
    btw = nx.betweenness_centrality(UG)
    try:
        eig = nx.eigenvector_centrality(UG, max_iter=1000, weight="weight")
    except nx.PowerIterationFailedConvergence:
        eig = {n: float("nan") for n in UG}
    deg = dict(UG.degree())
    df = pd.DataFrame(
        {
            "type": {n: UG.nodes[n]["type"] for n in UG},
            "label": {n: UG.nodes[n]["label"] for n in UG},
            "degree": deg,
            "pagerank": pr,
            "betweenness": btw,
            "eigenvector": eig,
        }
    )
    return df, deg


def communities(UG: "nx.Graph") -> tuple[list, dict, str]:
    louvain = C.louvain_communities(UG, weight="weight", seed=42)
    comm_of = {n: i for i, c in enumerate(louvain) for n in c}
    leiden_note = "louvain (leiden backend not installed)"
    try:
        leiden = C.leiden_communities(UG, weight="weight", seed=42)
        leiden_note = f"leiden backend present: {len(leiden)} communities"
    except Exception as exc:  # noqa: BLE001 - optional backend
        leiden_note = f"leiden unavailable ({type(exc).__name__}); using louvain"
    return louvain, comm_of, leiden_note


def lineage(G: "nx.MultiDiGraph") -> "nx.DiGraph":
    return nx.DiGraph((u, v) for u, v, k in G.edges(keys=True) if k == "derived_from")


def write_figure(UG, deg, out_png: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    pos = nx.spring_layout(UG, seed=42, k=0.4)
    node_colors = [TYPE_COLORS.get(UG.nodes[n]["type"], "#9c9c9c") for n in UG]
    sizes = [20 + 7 * deg[n] for n in UG]
    fig, ax = plt.subplots(figsize=(13, 13))
    nx.draw_networkx_edges(UG, pos, alpha=0.12, width=0.5, ax=ax)
    nx.draw_networkx_nodes(
        UG, pos, node_color=node_colors, node_size=sizes,
        linewidths=0.3, edgecolors="white", ax=ax,
    )
    hubs = sorted(deg, key=deg.get, reverse=True)[:15]
    nx.draw_networkx_labels(
        UG, pos, labels={n: UG.nodes[n]["label"] for n in hubs}, font_size=7, ax=ax
    )
    present = [t for t in TYPE_COLORS if any(UG.nodes[n]["type"] == t for n in UG)]
    ax.legend(
        handles=[Patch(color=TYPE_COLORS[t], label=t) for t in present],
        loc="lower left", fontsize=9, frameon=False,
    )
    ax.set_title("Epistemic-Humility KG  (node colour = type, size = degree)")
    ax.axis("off")
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_sigma(G, deg, comm_of, out_html: Path) -> bool:
    """Export an interactive standalone HTML via ipysigma; True if written."""
    try:
        from ipysigma import Sigma
    except ImportError:
        return False
    for n in G.nodes():
        G.nodes[n]["degree"] = deg.get(n, 0)
        G.nodes[n]["community"] = comm_of.get(n, -1)
    Sigma.write_html(
        G, str(out_html),
        node_color="type", node_label="label", node_size="degree",
        edge_color="edge_type", height=620,
    )
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", default="", help="Vault root (default <repo>/library).")
    parser.add_argument(
        "--outdir", default=str(convert.REPO_ROOT / "tools" / "kg_viz" / "data"),
        help="Directory for artifacts.",
    )
    parser.add_argument("--quiet", action="store_true", help="Artifacts only, no summary.")
    args = parser.parse_args(argv)

    root = args.root or None
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    G = convert.to_networkx(root)
    UG = project_undirected(G)
    basics = run_analyze_kg()
    cent, deg = centrality_table(UG)
    louvain, comm_of, leiden_note = communities(UG)
    DG = lineage(G)

    core = nx.core_number(UG)
    kmax = max(core.values()) if core else 0

    top_pr = cent.sort_values("pagerank", ascending=False).head(10)
    top_btw = cent.sort_values("betweenness", ascending=False).head(10)

    stats = {
        "nodes": G.number_of_nodes(),
        "logical_edges": G.number_of_edges(),
        "raw_directed_edges": basics.get("edge_count"),
        "node_types": convert.graph_stats(*convert.load_records(root))["node_types"],
        "communities_louvain": len(louvain),
        "community_sizes": sorted((len(c) for c in louvain), reverse=True),
        "leiden": leiden_note,
        "connected_components": nx.number_connected_components(UG),
        "max_k_core": kmax,
        "derived_from_edges": DG.number_of_edges(),
        "top_pagerank": [
            {"id": i, "label": r.label, "type": r.type, "pagerank": round(r.pagerank, 4)}
            for i, r in top_pr.iterrows()
        ],
        "top_betweenness": [
            {"id": i, "label": r.label, "type": r.type, "betweenness": round(r.betweenness, 4)}
            for i, r in top_btw.iterrows()
        ],
    }

    write_figure(UG, deg, outdir / "graph.figure.png")
    sigma_ok = write_sigma(G, deg, comm_of, outdir / "graph.sigma.html")
    stats["interactive_html"] = "graph.sigma.html" if sigma_ok else "skipped (ipysigma not installed)"

    (outdir / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if not args.quiet:
        print(f"nodes={stats['nodes']}  logical_edges={stats['logical_edges']}  "
              f"(raw directed={stats['raw_directed_edges']})")
        print(f"communities (louvain)={stats['communities_louvain']}  "
              f"sizes={stats['community_sizes']}")
        print(f"{leiden_note}")
        print(f"connected_components={stats['connected_components']}  max_k_core={kmax}  "
              f"derived_from_edges={stats['derived_from_edges']}")
        print("top PageRank:")
        for r in stats["top_pagerank"][:5]:
            print(f"  {r['pagerank']:.4f}  {r['label']} ({r['type']})")
        print(f"artifacts -> {outdir}/  (stats.json, graph.figure.png, "
              f"{stats['interactive_html']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
