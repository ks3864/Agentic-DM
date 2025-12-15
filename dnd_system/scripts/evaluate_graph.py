import json
import networkx as nx
import os

def analyze_graph(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    print(f"--- Graph Analysis for {os.path.basename(file_path)} ---")
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")

    G = nx.DiGraph()
    
    # Add nodes
    for node in nodes:
        G.add_node(node['id'], type=node.get('type'))

    # Add edges
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], type=edge.get('type'))

    # Connectivity (Undirected view for component analysis)
    # We convert to undirected because 'navigability' usually implies return paths are possible 
    # or at least that the clusters are linked. Strong connectivity in a directed graph is strict, 
    # but for "is the map fragmented?", weak connectivity (undirected) is the standard check.
    UG = G.to_undirected()
    
    components = list(nx.connected_components(UG))
    num_components = len(components)
    largest_component = max(components, key=len)
    percentage_connected = (len(largest_component) / len(nodes)) * 100 if nodes else 0

    print(f"\n--- Connectivity Metrics ---")
    print(f"Number of Connected Components: {num_components}")
    print(f"Largest Component Size: {len(largest_component)} nodes")
    print(f"Connectivity Score: {percentage_connected:.2f}% (Nodes in largest component)")
    
    if num_components > 1:
        print("\nNote: The graph is fragmented. The smaller components are:")
        for i, comp in enumerate(components):
            if comp != largest_component:
                print(f"  Component {i+1} ({len(comp)} nodes): {list(comp)}")

    # Density
    density = nx.density(G)
    print(f"\nGraph Density: {density:.4f}")

    # Isolated nodes
    isolated = list(nx.isolates(G))
    if isolated:
        print(f"Isolated Nodes (0 edges): {len(isolated)}")
        # print(f"  IDs: {isolated}")
    else:
        print("No isolated nodes.")

if __name__ == "__main__":
    analyze_graph(r"d:\COMS6998_LLM_GenAI\agenticdm\dnd_system\state\knowledge_graph.json")
