import json
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")
GRAPH_FILE = "knowledge_graph.json"

class ReadGraphTool(BaseTool):
    name: str = "Read Knowledge Graph"
    description: str = "Reads the adventure knowledge graph to find the current scene details and available transitions. Input should be the 'current_node_id' (or 'start' if unknown)."

    def _run(self, current_node_id: str) -> str:
        path = os.path.join(STATE_DIR, GRAPH_FILE)
        if not os.path.exists(path):
            return "Knowledge graph not found."
        
        try:
            with open(path, "r") as f:
                graph = json.load(f)
        except Exception as e:
            return f"Error reading graph: {e}"

        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        edges = graph.get("edges", [])

        # Normalize input
        current_node_id = current_node_id.strip()
        
        # 1. Try exact match
        if current_node_id in nodes:
            pass # Found it
        
        # 2. Try case-insensitive match
        elif any(nid.lower() == current_node_id.lower() for nid in nodes):
            for nid in nodes:
                if nid.lower() == current_node_id.lower():
                    current_node_id = nid
                    break
        
        # 3. Try finding by Name field
        elif any(n["name"].lower() == current_node_id.lower() for n in nodes.values()):
             for nid, n in nodes.items():
                if n["name"].lower() == current_node_id.lower():
                    current_node_id = nid
                    break

        # 4. Fallback for "start" or empty
        elif current_node_id.lower() in ["start", "begin", ""]:
             if "start_of_adventure" in nodes:
                 current_node_id = "start_of_adventure"
             else:
                 current_node_id = list(nodes.keys())[0]

        # 5. Last resort: Partial match (risky but helpful for "Goblin Ambush" -> "goblin_ambush")
        else:
             # Try to convert input to snake_case (e.g. "Goblin Ambush" -> "goblin_ambush")
             snake_input = current_node_id.lower().replace(" ", "_")
             if snake_input in nodes:
                 current_node_id = snake_input
             else:
                 return f"Node '{current_node_id}' not found in graph."

        current_node = nodes.get(current_node_id)
        if not current_node:
            return f"Node '{current_node_id}' not found."

        # Find outgoing edges
        options = []
        for edge in edges:
            if edge["source"] == current_node_id:
                target_node = nodes.get(edge["target"])
                target_name = target_node["name"] if target_node else edge["target"]
                options.append(f"- To '{target_name}' ({edge['target']}): {edge.get('type', 'transition')} (Condition: {edge.get('condition', 'None')})")

        output = [
            f"Current Scene: {current_node['name']} (ID: {current_node['id']})",
            f"Type: {current_node.get('type', 'Unknown')}",
            f"Description: {current_node.get('description', '')}",
            f"Boxed Text: {current_node.get('boxed_text', 'None')}",
            f"NPCs: {', '.join(current_node.get('npcs', []))}",
            f"Monsters: {', '.join(current_node.get('monsters', []))}",
            f"Features: {'; '.join(current_node.get('features', [])) or 'None'}",
            "\nAvailable Transitions:",
            "\n".join(options) if options else "No clear transitions defined."
        ]
        
        return "\n".join(output)

class UpdateGraphTool(BaseTool):
    name: str = "Update Knowledge Graph"
    description: str = "Updates the status of a node in the knowledge graph (e.g., marking it as 'visited' or 'completed'). Input: {'node_id': str, 'status': str}"

    def _run(self, node_id: str, status: str) -> str:
        path = os.path.join(STATE_DIR, GRAPH_FILE)
        if not os.path.exists(path):
            return "Knowledge graph not found."
        
        try:
            with open(path, "r") as f:
                graph = json.load(f)
            
            updated = False
            for node in graph.get("nodes", []):
                if node["id"] == node_id:
                    node["status"] = status
                    updated = True
                    break
            
            if not updated:
                return f"Node '{node_id}' not found."
            
            with open(path, "w") as f:
                json.dump(graph, f, indent=2)
                
            return f"Updated node '{node_id}' status to '{status}'."
            
        except Exception as e:
            return f"Error updating graph: {e}"
