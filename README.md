# Final Project — Agentic DM: An LLM-Powered Dungeon Master

> **Team project.** This is forked from the original team repository. See my contributions below and on the [GitHub repo](https://github.com/ryersonburdick/agenticdm).

## Overview

A modular, multi-agent framework for LLM-driven tabletop role-playing game (TTRPG) narration and adjudication. The system decomposes the traditional Dungeon Master role into specialized AI agents that collaborate to run a D&D campaign, solving the "DM Bottleneck" — the difficulty of finding a skilled human DM.

## My Contributions

**Kuang Sun** — System architect and primary developer:

- **Multi-Agent Orchestration**: Designed and implemented the core system pipeline using CrewAI, coordinating three specialized agents (Rules Lawyer, Scribe, Narrator) into a sequential turn-based loop
- **Knowledge Graph Extraction Pipeline**: Built the LLM-powered pipeline that converts unstructured adventure book PDFs into a structured Knowledge Graph of locations, NPCs, items, and connections — including the **cross-chapter bridging algorithm** that achieved 100% graph connectivity (vs. 28% with naive extraction)
- **GraphRAG Tools**: Implemented the graph-based retrieval tools that enable spatial reasoning — anchoring on a node and traversing 1-hop neighbors to retrieve physically adjacent room context
- **Data Ingestion Workflow**: Designed the document processing pipeline from raw PDF → chunked text → structured graph
- **Chainlit UI**: Built the interactive chat interface for gameplay
- **Quantitative Evaluation**: Designed and conducted the evaluation comparing GraphRAG (100% accuracy) vs. vector search baseline on spatial context retrieval

**Ryerson Burdick** — Optimization and evaluation:
- Model selection, testing, logging, and prompt engineering
- Latency reduction strategies and agent behavior refinement
- Qualitative analysis and knowledge graph visualization

## Architecture

The system uses a **Multi-Agent Orchestration Framework** with three specialized agents that run sequentially each turn:

| Agent | Role | Tools |
|-------|------|-------|
| **Rules Lawyer** | Mechanical resolution — skill checks, combat rolls, difficulty assessment | Rules-RAG (D&D 5e SRD) |
| **Scribe** | World state tracking — locations, inventory, HP, quests (structured JSON) | State Tool (read/write world state) |
| **Narrator** | Creative storytelling — synthesizes actions, mechanics, and context into narrative | Adventure Guide RAG, Graph Tool |

### Knowledge & Retrieval Layers

- **Rules-RAG**: Retrieves authoritative mechanical rules from D&D 5e Basic Rules / SRD 5.1
- **Adventure Guide RAG**: Retrieves campaign-specific narrative context from the adventure book
- **GraphRAG**: Traverses the Knowledge Graph for spatial reasoning — retrieves adjacent rooms, NPCs in a location, connected paths

### Why GraphRAG over Vector RAG?

Standard vector RAG retrieves by semantic similarity, which fails for topological queries. When asked "what is in the room *next* to this one?", vector search returns semantically similar text chunks — but not necessarily the physically adjacent room. GraphRAG anchors on the current location node and traverses edges, guaranteeing spatially correct context.

| Metric | Vector RAG (baseline) | GraphRAG (ours) |
|--------|----------------------|-----------------|
| Spatial context retrieval | Partial (misses adjacent rooms) | **100% accuracy** |
| Global connectivity | 28% (fragmented islands) | **100%** (fully connected) |

## Key Results

1. **100% graph connectivity** after cross-chapter bridging (vs. 28% with naive per-chapter extraction)
2. **100% spatial retrieval accuracy** — GraphRAG guaranteed adjacent room context on every query
3. **Qualitative improvements** — consistent world state tracking over multi-turn gameplay; seamless blending of mechanics into narrative

### Known Limitations
- **Latency**: 10–20 seconds per turn due to multi-agent cognitive loop
- **Combat**: Unreliable HP/XP state updates during extended combat encounters
- **Single-player only**: Current event loop handles one player at a time

## Tech Stack

- Python · CrewAI · LangChain · Chainlit (chat UI)
- Knowledge Graphs · GraphRAG · Vector RAG (Chroma)
- LLM-powered PDF extraction & cross-chapter bridging

## Files

- `COMS_6998_LLMs_Project_Report.pdf` — Full project report (IEEE format)
- `agenticdm-main/` — Complete source code
  - `dnd_system/build_knowledge_graph.py` — KG extraction pipeline & bridging algorithm
  - `dnd_system/agents.py` — Agent definitions (Rules Lawyer, Scribe, Narrator)
  - `dnd_system/tasks.py` — CrewAI task specifications
  - `dnd_system/main.py` — Main game loop orchestration
  - `dnd_system/app.py` — Chainlit UI integration
  - `dnd_system/tools/` — Agent tools (graph_tool, rag_tool, state_tool, dice_tool)
  - `dnd_system/ingest.py` — Document ingestion pipeline
  - `graph_interactive.html` — Interactive knowledge graph visualization
