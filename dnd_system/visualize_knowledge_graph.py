import os
import json
import argparse
from typing import Dict, Any, Optional, Set

import matplotlib.pyplot as plt
import networkx as nx


def load_knowledge_graph(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(data: Dict[str, Any]) -> nx.DiGraph:
    G = nx.DiGraph()

    for node in data.get("nodes", []):
        node_id = node.get("id")
        if not node_id:
            continue
        G.add_node(
            node_id,
            label=node.get("name", node_id),
            type=node.get("type", "Unknown"),
            description=node.get("description", ""),
        )

    for edge in data.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        if not G.has_node(source):
            G.add_node(source, label=source, type="Unknown", description="")
        if not G.has_node(target):
            G.add_node(target, label=target, type="Unknown", description="")
        G.add_edge(
            source,
            target,
            type=edge.get("type", ""),
            condition=edge.get("condition"),
        )

    return G


def analyze_graph(G: nx.DiGraph) -> None:
    isolated = list(nx.isolates(G))
    weak_components = list(nx.weakly_connected_components(G))

    print(f"Total nodes: {G.number_of_nodes()}")
    print(f"Total edges: {G.number_of_edges()}")
    print(f"Weakly connected components: {len(weak_components)}")
    if len(weak_components) > 1:
        print("Component sizes:")
        for i, comp in enumerate(weak_components, start=1):
            print(f"  Component {i}: {len(comp)} nodes")
    if isolated:
        print("Isolated nodes (no incident edges):")
        for node_id in isolated:
            attrs = G.nodes[node_id]
            print(f"  {node_id} ({attrs.get('label', node_id)})")


def focus_subgraph(G: nx.DiGraph, center: Optional[str], radius: int) -> nx.DiGraph:
    if not center or center not in G:
        if center and center not in G:
            print(f"Focus node '{center}' not found in graph; showing full graph instead.")
        return G

    undirected = G.to_undirected()
    distances = nx.single_source_shortest_path_length(undirected, center, cutoff=radius)
    nodes = set(distances.keys())
    print(f"Focusing on node '{center}' with radius {radius}: {len(nodes)} nodes in subgraph.")
    return G.subgraph(nodes).copy()


def draw_graph(
    G: nx.DiGraph,
    output: str | None = None,
    show: bool = True,
    max_edge_labels: int = 200,
    start_nodes: Optional[Set[str]] = None,
    end_nodes: Optional[Set[str]] = None,
) -> None:
    node_types = {G.nodes[n].get("type", "Unknown") for n in G.nodes}
    palette = [
        "tab:blue",
        "tab:green",
        "tab:orange",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
    ]
    type_to_color = {}
    for i, t in enumerate(sorted(node_types)):
        type_to_color[t] = palette[i % len(palette)]

    node_colors = [type_to_color.get(G.nodes[n].get("type", "Unknown"), "tab:gray") for n in G.nodes]

    pos = nx.spring_layout(G, k=0.35, iterations=200)

    plt.figure(figsize=(16, 12))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=350, alpha=0.9)

    # Highlight start/end nodes on top of the base nodes
    start_nodes = start_nodes or set()
    end_nodes = end_nodes or set()

    start_nodes = {n for n in start_nodes if n in G}
    end_nodes = {n for n in end_nodes if n in G and n not in start_nodes}

    if start_nodes:
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=list(start_nodes),
            node_color="none",
            edgecolors="black",
            linewidths=2.0,
            node_size=550,
        )

    if end_nodes:
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=list(end_nodes),
            node_color="none",
            edgecolors="black",
            linewidths=2.0,
            node_shape="s",
            node_size=550,
        )

    edge_colors = []
    for u, v, d in G.edges(data=True):
        if d.get("type") == "triggers":
            edge_colors.append("tab:red")
        else:
            edge_colors.append("tab:gray")

    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, alpha=0.5, arrows=True, arrowsize=10, width=1.0)

    labels = {n: G.nodes[n].get("label", n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)

    if G.number_of_edges() <= max_edge_labels:
        edge_labels = {}
        for u, v, d in G.edges(data=True):
            cond = d.get("condition")
            if cond:
                edge_labels[(u, v)] = cond
            else:
                edge_labels[(u, v)] = d.get("type", "")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6, alpha=0.7)

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    legend_handles = []
    for t, c in sorted(type_to_color.items()):
        legend_handles.append(Patch(color=c, label=t))

    if start_nodes:
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="black",
                markerfacecolor="none",
                markersize=10,
                linewidth=0,
                label="Start Node",
            )
        )
    if end_nodes:
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="s",
                color="black",
                markerfacecolor="none",
                markersize=10,
                linewidth=0,
                label="End Node",
            )
        )

    plt.legend(handles=legend_handles, title="Node Types", loc="upper left", bbox_to_anchor=(1.02, 1.0))

    plt.axis("off")
    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=300)
        print(f"Saved graph visualization to {output}")

    if show:
        plt.show()
    else:
        plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graph-path",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "state", "knowledge_graph.json"),
        help="Path to knowledge_graph.json to visualize.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save the visualization image (e.g., graph.png).",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open an interactive window; useful in headless environments.",
    )
    parser.add_argument(
        "--max-edge-labels",
        type=int,
        default=200,
        help="Maximum number of edges for which to draw labels.",
    )
    parser.add_argument(
        "--start-node",
        action="append",
        default=None,
        help="ID of a node to highlight as a start node (can be passed multiple times).",
    )
    parser.add_argument(
        "--end-node",
        action="append",
        default=None,
        help="ID of a node to highlight as an end node (can be passed multiple times).",
    )
    parser.add_argument(
        "--focus-node",
        type=str,
        default=None,
        help="ID of a node to focus on; visualizes only nodes within a given radius.",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=2,
        help="Radius (in edges) around the focus node to include in the subgraph.",
    )

    args = parser.parse_args()

    data = load_knowledge_graph(args.graph_path)
    G = build_graph(data)

    # Determine default start/end nodes if not explicitly provided
    start_nodes: Set[str] = set(args.start_node or [])
    end_nodes: Set[str] = set(args.end_node or [])

    if not start_nodes:
        for candidate in ("start_of_adventure",):
            if candidate in G:
                start_nodes.add(candidate)
    if not end_nodes:
        for candidate in ("conclusion",):
            if candidate in G:
                end_nodes.add(candidate)

    G_view = focus_subgraph(G, args.focus_node, args.radius)

    # Restrict start/end sets to nodes that are actually in view
    start_nodes &= set(G_view.nodes)
    end_nodes &= set(G_view.nodes)

    analyze_graph(G_view)
    draw_graph(
        G_view,
        output=args.output,
        show=not args.no_show,
        max_edge_labels=args.max_edge_labels,
        start_nodes=start_nodes,
        end_nodes=end_nodes,
    )


if __name__ == "__main__":
    main()
