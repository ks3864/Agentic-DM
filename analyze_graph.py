import json
import os

GRAPH_FILE = "dnd_system/state/knowledge_graph.json"

def analyze_graph():
    if not os.path.exists(GRAPH_FILE):
        print(f"Error: {GRAPH_FILE} not found.")
        return

    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    node_ids = {n["id"] for n in nodes}
    
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")

    # Check for missing fields
    missing_desc = [n["id"] for n in nodes if not n.get("description")]
    missing_type = [n["id"] for n in nodes if not n.get("type")]
    
    print(f"Nodes missing description: {len(missing_desc)}")
    if missing_desc:
        print(f"  Examples: {missing_desc[:5]}")
        
    print(f"Nodes missing type: {len(missing_type)}")

    # Check for broken edges
    broken_edges = []
    for edge in edges:
        if edge["source"] not in node_ids:
            broken_edges.append(f"Source {edge['source']} not found")
        if edge["target"] not in node_ids:
            broken_edges.append(f"Target {edge['target']} not found")
            
    print(f"Broken Edges: {len(broken_edges)}")
    if broken_edges:
        print(f"  Examples: {broken_edges[:5]}")

    # Check for orphans (nodes with no edges)
    connected_nodes = set()
    for edge in edges:
        if edge["source"] in node_ids:
            connected_nodes.add(edge["source"])
        if edge["target"] in node_ids:
            connected_nodes.add(edge["target"])
            
    orphans = node_ids - connected_nodes
    print(f"Orphan Nodes: {len(orphans)}")
    if orphans:
        print(f"  Examples: {list(orphans)[:5]}")

    # Check for boxed text coverage
    has_boxed_text = [n["id"] for n in nodes if n.get("boxed_text")]
    print(f"Nodes with Boxed Text: {len(has_boxed_text)} ({len(has_boxed_text)/len(nodes)*100:.1f}%)")

if __name__ == "__main__":
    analyze_graph()
