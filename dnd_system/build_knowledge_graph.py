import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Data Models
class GraphNode(BaseModel):
    id: str = Field(description="Unique identifier for the node (e.g., 'goblin_ambush')")
    name: str = Field(description="Human-readable name of the location or event")
    type: str = Field(description="Type of node: 'Location', 'Event', or 'Encounter'")
    description: str = Field(description="Brief summary of the scene")
    boxed_text: Optional[str] = Field(None, description="Read-aloud text for the scene")
    npcs: List[str] = Field(default_factory=list, description="List of NPCs present")
    monsters: List[str] = Field(default_factory=list, description="List of monsters present")

class GraphEdge(BaseModel):
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    type: str = Field(description="Type of connection: 'leads_to' or 'triggers'")
    condition: Optional[str] = Field(None, description="Condition to traverse (e.g., 'defeat_goblins')")

class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

def build_graph():
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Read Adventure Text
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "Lost Mine of Phandelver.md")
    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract just the "Goblin Arrows" section for now, but chunk it
    start_marker = "# Goblin Arrows"
    end_marker = "### Cragmaw Hideout" 
    
    if start_marker in text:
        text = text.split(start_marker)[1]
    if end_marker in text:
        text = text.split(end_marker)[0]

    # Simple chunking by "### " headers to get scenes
    chunks = text.split("### ")
    # Re-add the header to the chunk
    chunks = [f"### {chunk}" for chunk in chunks if chunk.strip()]
    
    print(f"Split text into {len(chunks)} chunks.")

    parser = JsonOutputParser(pydantic_object=KnowledgeGraph)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Dungeon Master assistant. Your task is to extract a structured Knowledge Graph from a D&D adventure text.\n"
                   "Identify key Scenes (Locations, Events, Encounters) as Nodes.\n"
                   "Identify transitions between them as Edges.\n"
                   "Extract read-aloud text (boxed text) exactly as is.\n"
                   "Identify NPCs and Monsters.\n\n"
                   "{format_instructions}"),
        ("user", "Adventure Text Segment:\n{text}")
    ])

    chain = prompt | llm | parser

    all_nodes = []
    all_edges = []

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            result = chain.invoke({"text": chunk, "format_instructions": parser.get_format_instructions()})
            if result.get("nodes"):
                all_nodes.extend(result["nodes"])
            if result.get("edges"):
                all_edges.extend(result["edges"])
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")

    # Deduplicate nodes by ID
    unique_nodes = {node['id']: node for node in all_nodes}.values()
    
    final_graph = {
        "nodes": list(unique_nodes),
        "edges": all_edges
    }

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), "state", "knowledge_graph.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(final_graph, f, indent=2)
        
    print(f"Successfully saved knowledge graph to {output_path}")
    print(f"Extracted {len(final_graph['nodes'])} nodes and {len(final_graph['edges'])} edges.")

if __name__ == "__main__":
    build_graph()
