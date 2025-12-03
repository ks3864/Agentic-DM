from crewai.tools import BaseTool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../db")

class AdventureRAGTool(BaseTool):
    name: str = "Search Adventure"
    description: str = "Search the adventure book for plot points, locations, and NPC details. Input is a search query. You can optionally provide 'current_location' in the input dict to ground the search."

    def _run(self, query: str, current_location: str = None) -> str:
        try:
            # Handle if query is passed as a dict (legacy/fallback)
            if isinstance(query, dict):
                if "description" in query:
                    query_text = query["description"]
                else:
                    query_text = query.get("query", str(query))
                
                # If current_location was in the dict, use it if not provided explicitly
                if not current_location and "current_location" in query:
                    current_location = query["current_location"]
            else:
                query_text = str(query)
            
            # Prepend location to query for better relevance
            final_query = f"{current_location}: {query_text}" if current_location else query_text

            vectorstore = Chroma(
                collection_name="adventure",
                embedding_function=OpenAIEmbeddings(),
                persist_directory=DB_DIR
            )
            results = vectorstore.similarity_search(final_query, k=3)
            return "\n\n".join([f"Content: {doc.page_content}\nSource: {doc.metadata.get('filename')}" for doc in results])
        except Exception as e:
            return f"Error searching adventure: {str(e)}"

class RulesRAGTool(BaseTool):
    name: str = "Search Rules"
    description: str = "Search the D&D 5e rules for mechanics, spells, and combat rules. Input is a search query string."

    def _run(self, query: str) -> str:
        try:
            # Handle dict input if CrewAI passes it
            if isinstance(query, dict):
                if "description" in query:
                    query = query["description"]
                else:
                    query = query.get("query", str(query))
                
            vectorstore = Chroma(
                collection_name="rules",
                embedding_function=OpenAIEmbeddings(),
                persist_directory=DB_DIR
            )
            results = vectorstore.similarity_search(query, k=3)
            return "\n\n".join([f"Content: {doc.page_content}\nSource: {doc.metadata.get('filename')}" for doc in results])
        except Exception as e:
            return f"Error searching rules: {str(e)}"
