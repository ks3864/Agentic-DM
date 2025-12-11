import os
import json
import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import argparse
import networkx as nx

# Load environment variables
load_dotenv()

DEFAULT_ADVENTURE_GUIDE = "../data/Lost Mine of Phandelver.md"

# Define Data Models with Rich Node Types
class GraphNode(BaseModel):
    id: str = Field(description="Unique snake_case identifier (e.g., 'goblin_ambush', 'sildar_hallwinter')")
    name: str = Field(description="Human-readable name")
    type: str = Field(description="One of: story_beat, location, encounter, dungeon, room, npc, quest")
    parent_id: Optional[str] = Field(None, description="ID of parent node (e.g., room belongs to dungeon)")
    description: str = Field(description="Brief summary of this node")
    boxed_text: Optional[str] = Field(None, description="Read-aloud text for the scene (if applicable)")
    npcs: List[str] = Field(default_factory=list, description="List of NPC names present (for locations/encounters)")
    monsters: List[str] = Field(default_factory=list, description="List of monster types present")
    mechanics: Optional[str] = Field(None, description="Any DC values, traps, or combat notes")
    features: List[str] = Field(default_factory=list, description="List of notable features, hazards, traps, or treasure in this location")

class GraphEdge(BaseModel):
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    type: str = Field(description="One of: leads_to, triggers, contains, unlocks, requires, involves, gives_quest")
    condition: Optional[str] = Field(None, description="Condition for this edge (e.g., 'defeat_goblins')")
    label: Optional[str] = Field(None, description="Human-readable description of the relationship")

class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Model for cross-chapter edge suggestions
class CrossChapterEdgeList(BaseModel):
    edges: List[GraphEdge] = Field(description="List of edges to connect disconnected graph components")


def connect_graph_components(graph: dict, adventure_text: str, llm: ChatOpenAI) -> dict:
    """
    Use NetworkX to detect disconnected components, then use LLM to suggest
    edges that connect them based on the adventure narrative.
    """
    # Build NetworkX graph
    G = nx.DiGraph()
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    for node_id in nodes:
        G.add_node(node_id)
    for edge in graph.get("edges", []):
        G.add_edge(edge["source"], edge["target"])
    
    # Find weakly connected components
    components = list(nx.weakly_connected_components(G))
    
    if len(components) <= 1:
        print("Graph is already fully connected!")
        return graph
    
    print(f"\n{'='*50}")
    print(f"CROSS-CHAPTER LINKING")
    print(f"{'='*50}")
    print(f"Found {len(components)} disconnected components.")
    
    # Get representative nodes from each component (prefer locations/dungeons over rooms)
    component_reps = []
    for i, comp in enumerate(components):
        # Sort nodes by type priority
        type_priority = {"location": 0, "dungeon": 1, "story_beat": 2, "encounter": 3, "quest": 4, "npc": 5, "room": 6}
        sorted_nodes = sorted(comp, key=lambda n: type_priority.get(nodes.get(n, {}).get("type", "room"), 10))
        rep_id = sorted_nodes[0]
        rep_node = nodes.get(rep_id, {})
        
        # For small components (< 10 nodes), include full details to help LLM understand context
        if len(comp) < 10:
            node_details = []
            for nid in comp:
                n = nodes.get(nid, {})
                node_details.append(f"  - {nid} ({n.get('name', nid)}, {n.get('type', '?')}): {n.get('description', '')[:100]}")
            all_nodes_str = "\n".join(node_details)
        else:
            all_nodes_str = "  " + ", ".join([f"{nid} ({nodes.get(nid, {}).get('name', nid)})" for nid in list(comp)[:10]])
        
        component_reps.append({
            "component_id": i + 1,
            "size": len(comp),
            "representative_id": rep_id,
            "representative_name": rep_node.get("name", rep_id),
            "representative_type": rep_node.get("type", "unknown"),
            "all_nodes_str": all_nodes_str
        })
    
    # Extract the Overview section from the adventure text
    overview_match = re.search(r'### Overview\s*(.*?)(?=###|\Z)', adventure_text, re.DOTALL)
    overview_text = overview_match.group(1).strip() if overview_match else adventure_text[:5000]
    
    # Format component info for LLM with detailed info for small components
    component_info = "\n".join([
        f"Component {c['component_id']} ({c['size']} nodes): Representative = {c['representative_name']} ({c['representative_id']}, type: {c['representative_type']})\n{c['all_nodes_str']}"
        for c in component_reps
    ])
    
    # Create prompt for cross-chapter linking
    parser = JsonOutputParser(pydantic_object=CrossChapterEdgeList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert D&D adventure analyst. Your task is to connect disconnected parts of a knowledge graph based on the adventure's narrative flow.

**ADVENTURE OVERVIEW:**
{overview}

**DISCONNECTED COMPONENTS:**
{components}

**YOUR TASK:**
Suggest edges that would connect these components based on:
1. The narrative flow described in the Overview
2. Logical travel paths between locations
3. Quest relationships (e.g., NPC gives quest that leads to a location)
4. Story progression (e.g., completing Part 1 leads to Part 2)

**EDGE TYPES:**
- `leads_to`: Physical travel path
- `triggers`: Completing this triggers access to that
- `unlocks`: Quest completion unlocks access
- `requires`: Must complete this before that

**RULES:**
- Use ONLY node IDs from the components listed above
- Each edge must connect nodes from DIFFERENT components
- Prefer connecting the largest components first
- Add a descriptive label for each edge

{format_instructions}"""),
        ("user", "Suggest edges to connect the {num_components} disconnected components.")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "overview": overview_text,
            "components": component_info,
            "num_components": len(components),
            "format_instructions": parser.get_format_instructions()
        })
        
        new_edges = result.get("edges", [])
        
        # Validate edges (both nodes must exist)
        valid_new_edges = []
        for edge in new_edges:
            src, tgt = edge.get("source"), edge.get("target")
            if src in nodes and tgt in nodes:
                valid_new_edges.append(edge)
                print(f"  Added: {src} --[{edge.get('type')}]--> {tgt} ({edge.get('label', '')})")
            else:
                print(f"  Skipped (invalid nodes): {src} -> {tgt}")
        
        # Add to graph
        graph["edges"].extend(valid_new_edges)
        print(f"\nAdded {len(valid_new_edges)} cross-chapter edges.")
        
    except Exception as e:
        print(f"Error during cross-chapter linking: {e}")
    
    return graph

def split_by_h1(text: str) -> List[dict]:
    """Split markdown text by # (H1) headers, preserving header info."""
    sections = []
    parts = re.split(r'^(# .+)$', text, flags=re.MULTILINE)
    
    current_header = None
    for part in parts:
        if part.startswith('# '):
            current_header = part.strip()
        elif current_header and part.strip():
            sections.append({
                "header": current_header,
                "content": part.strip()
            })
    return sections


def build_graph_chapter_based(adventure_guide_path: str, test_mode: bool = False):
    """Build knowledge graph using chapter-based extraction with rich node types."""
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Read Adventure Text
    data_path_1 = adventure_guide_path
    if not os.path.exists(data_path_1):
        data_path_2 = os.path.join(os.path.dirname(__file__), adventure_guide_path)
        if not os.path.exists(data_path_2):
            raise ValueError(f"Could not find adventure guide at paths '{data_path_1}' or '{data_path_2}'")
        else:
            data_path = data_path_2
    else:
        data_path = data_path_1

    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into H1 chapters
    chapters = split_by_h1(text)
    print(f"Found {len(chapters)} H1 chapters: {[c['header'] for c in chapters]}")

    # For testing, only process "# Goblin Arrows"
    if test_mode:
        chapters = [c for c in chapters if "Goblin Arrows" in c["header"]]
        if not chapters:
            raise ValueError("Test mode: Could not find '# Goblin Arrows' chapter.")
        print(f"[Test Mode] Processing chapter: {chapters[0]['header']}")
    else:
        # Filter out appendices and credits for full extraction
        adventure_chapters = ["Goblin Arrows", "Phandalin", "Spider's Web", "Wave Echo Cave"]
        chapters = [c for c in chapters if any(ac in c["header"] for ac in adventure_chapters)]
        print(f"[Full Mode] Processing {len(chapters)} adventure chapters")

    # Setup parser and prompt
    parser = JsonOutputParser(pydantic_object=KnowledgeGraph)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Dungeon Master assistant. Extract a KNOWLEDGE GRAPH from this D&D adventure chapter.

**NODE TYPES:**
- `story_beat`: Major narrative milestones (e.g., "The Adventure Begins", "Rescued Sildar")
- `location`: Geographic places (e.g., "Triboar Trail", "Neverwinter")
- `encounter`: Combat or social encounters (e.g., "Goblin Ambush")
- `dungeon`: A composite multi-room location (e.g., "Cragmaw Hideout")
- `room`: Individual rooms within a dungeon (e.g., "Cave Mouth", "Klarg's Cave")
- `npc`: Named characters (e.g., "Gundren Rockseeker", "Sildar Hallwinter")
- `quest`: Objectives or goals (e.g., "Escort Wagon to Phandalin", "Rescue Sildar")

**EDGE TYPES:**
- `leads_to`: Physical path between locations/rooms
- `triggers`: One event causes another
- `contains`: Hierarchy (dungeon contains rooms)
- `unlocks`: Completing something unlocks access
- `requires`: Prerequisite condition
- `involves`: NPC is involved in an encounter/location
- `gives_quest`: NPC gives a quest

**RULES:**
1. Extract ALL distinct scenes, NPCs, and quests from the text.
2. For `room` nodes, set `parent_id` to the dungeon they belong to.
3. For encounters/rooms, include the `boxed_text` (read-aloud text in >> blocks).
4. For encounters/rooms, list `monsters` and `npcs` present.
5. Include `mechanics` for traps, DCs, or combat notes.
6. Connect NPCs to locations where they appear via `involves` edges.
7. Connect NPCs to quests they give via `gives_quest` edges.

**CRITICAL - ROOM FEATURES (H4 CONTENT):**
For `room` nodes, extract the `features` list from sub-sections (#### headers) including:
- **Hazards/Traps:** e.g., "Flood!" - water surge trap, "Pit" - hidden pit trap
- **Environmental Features:** e.g., "Bridge" - climbable bridge, "Fissure" - chimney connecting rooms
- **Treasure:** e.g., "Treasure" - loot found in the room
- **Developments:** e.g., "Developments" - consequences of player actions

Format each feature as: "[Feature Name]: [Brief description with DC values if applicable]"
Example features:
- "Flood: Goblins can release water surge, DC 10 Dex save or be swept to area 1, taking 1d6 damage"
- "Bridge: Spans 20 feet above stream, DC 15 Athletics to climb, AC 5, 10 HP"
- "Treasure: Potion of healing, 50 gp, jade frog statuette (40 gp)"

**CRITICAL - ROOM NAVIGATION:**
For dungeons, you MUST extract `leads_to` edges between rooms based on:
- Passages, corridors, stairs, tunnels mentioned in descriptions
- Text like "leads to", "connects to", "passage to", "stairs descend to"
- Fissures, chimneys, or secret paths that connect rooms
- References to "area X" or room numbers (e.g., "area 7" = the 7th room)

Example room connections to look for:
- "The main passage from the cave mouth climbs steeply upward" → cave_mouth leads_to steep_passage
- "A narrow opening descends into darkness" → room_a leads_to room_b
- "A fissure climbs 30 feet to area 8" → room_3 leads_to room_8

Create BIDIRECTIONAL edges where movement is possible in both directions.

{format_instructions}"""),
        ("user", "Adventure Chapter:\n{chapter_header}\n\n{chapter_content}")
    ])

    chain = prompt | llm | parser

    all_nodes = []
    all_edges = []

    for i, chapter in enumerate(chapters):
        print(f"\nProcessing chapter {i+1}/{len(chapters)}: {chapter['header']}")
        print(f"  Content length: {len(chapter['content'])} chars")
        
        try:
            result = chain.invoke({
                "chapter_header": chapter["header"],
                "chapter_content": chapter["content"],
                "format_instructions": parser.get_format_instructions()
            })
            
            nodes = result.get("nodes", [])
            edges = result.get("edges", [])
            
            print(f"  -> Extracted {len(nodes)} nodes, {len(edges)} edges")
            
            all_nodes.extend(nodes)
            all_edges.extend(edges)
            
        except Exception as e:
            print(f"  -> Error: {e}")

    # Deduplicate nodes by ID (handles exact duplicates across chapters)
    unique_nodes = {node['id']: node for node in all_nodes}
    
    # Validate and deduplicate edges
    valid_edges = []
    seen_edges = set()
    for edge in all_edges:
        src, tgt = edge.get("source"), edge.get("target")
        if src in unique_nodes and tgt in unique_nodes:
            edge_key = (src, tgt, edge.get("type"))
            if edge_key not in seen_edges:
                valid_edges.append(edge)
                seen_edges.add(edge_key)

    # Add bidirectional edges for 'leads_to' type (room navigation)
    bidirectional_edges = []
    for edge in valid_edges:
        if edge.get("type") == "leads_to":
            reverse_key = (edge.get("target"), edge.get("source"), "leads_to")
            if reverse_key not in seen_edges:
                reverse_edge = {
                    "source": edge.get("target"),
                    "target": edge.get("source"),
                    "type": "leads_to",
                    "label": f"Return path: {edge.get('label', '')}" if edge.get('label') else None
                }
                bidirectional_edges.append(reverse_edge)
                seen_edges.add(reverse_key)
    
    valid_edges.extend(bidirectional_edges)
    print(f"Added {len(bidirectional_edges)} bidirectional edges for navigation.")

    # Build initial graph
    final_graph = {
        "nodes": list(unique_nodes.values()),
        "edges": valid_edges
    }

    # Cross-chapter linking: use LLM to connect disconnected components
    if not test_mode:
        final_graph = connect_graph_components(final_graph, text, llm)

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), "state", "knowledge_graph.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(final_graph, f, indent=2)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*50}")
    print(f"Saved to: {output_path}")
    print(f"Total Nodes: {len(final_graph['nodes'])}")
    print(f"Total Edges: {len(final_graph['edges'])}")
    
    # Node type breakdown
    type_counts = {}
    for node in final_graph['nodes']:
        t = node.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"\nNode Types:")
    for t, count in sorted(type_counts.items()):
        print(f"  - {t}: {count}")

    # Edge type breakdown
    edge_type_counts = {}
    for edge in final_graph['edges']:
        t = edge.get('type', 'unknown')
        edge_type_counts[t] = edge_type_counts.get(t, 0) + 1
    print(f"\nEdge Types:")
    for t, count in sorted(edge_type_counts.items()):
        print(f"  - {t}: {count}")

    return final_graph


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--adventure-guide", 
        type=str, 
        default=DEFAULT_ADVENTURE_GUIDE, 
        help="Path to adventure guide from which to construct knowledge graph."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only process '# Goblin Arrows' chapter."
    )
    args = parser.parse_args()

    build_graph_chapter_based(args.adventure_guide, test_mode=args.test)
