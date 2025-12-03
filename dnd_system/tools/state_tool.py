from crewai.tools import BaseTool
import json
import os
from typing import Dict, Any, Union, Optional

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../state")

class ReadStateTool(BaseTool):
    name: str = "Read Game State"
    description: str = "Reads the current character sheet or world state. Input 'character' or 'world'."

    def _run(self, file_type: str) -> str:
        try:
            if "char" in file_type.lower():
                filename = "character_sheet.json"
            elif "world" in file_type.lower():
                filename = "world_state.json"
            else:
                return "Invalid file type. Specify 'character' or 'world'."
            
            path = os.path.join(STATE_DIR, filename)
            with open(path, "r") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error reading state: {str(e)}"

from pydantic import BaseModel, Field

class UpdateStateSchema(BaseModel):
    file_type: Optional[str] = Field(default=None, description="The type of file to update ('character' or 'world').")
    updates: Optional[Dict[str, Any]] = Field(default=None, description="Dictionary of fields to update.")
    json_input: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Legacy input format (JSON string or dict).")

class UpdateStateTool(BaseTool):
    name: str = "Update Game State"
    description: str = "Updates the game state. Input can be 'file_type' and 'updates' directly, OR a 'json_input' string."
    args_schema: type[BaseModel] = UpdateStateSchema

    def _run(self, file_type: str = None, updates: dict = None, json_input: Union[str, dict] = None) -> str:
        try:
            data = {}
            # 1. Check if arguments are passed directly
            if file_type and updates:
                data = {"file_type": file_type, "updates": updates}
            
            # 2. Check json_input if direct args missing
            elif json_input:
                if isinstance(json_input, dict):
                    data = json_input
                else:
                    try:
                        data = json.loads(json_input)
                    except:
                        import ast
                        try:
                            data = ast.literal_eval(json_input)
                        except:
                            return f"Error parsing input: {json_input}"
            
            # 3. Check for schema hallucination in data
            if "description" in data and "type" in data:
                 desc = data.get("description", "")
                 if "no mechanics" in desc.lower() or "no changes" in desc.lower():
                     return "No changes made."
                 # Try to recover if description IS the json
                 try:
                    data = json.loads(desc)
                 except:
                    pass

            file_type = data.get("file_type") or file_type
            updates = data.get("updates") or updates
            
            if not file_type or not updates:
                return "Missing 'file_type' or 'updates' in input."

            if "char" in file_type.lower():
                filename = "character_sheet.json"
            elif "world" in file_type.lower():
                filename = "world_state.json"
            else:
                return "Invalid file type."
            
            path = os.path.join(STATE_DIR, filename)
            
            with open(path, "r") as f:
                current_state = json.load(f)
            
            # Simple merge for top-level keys. 
            # For nested updates (like stats), the agent should provide the full nested object or we need recursive update.
            # For now, we assume the agent provides the full object for the key they are updating.
            for key, value in updates.items():
                current_state[key] = value
                
            with open(path, "w") as f:
                json.dump(current_state, f, indent=2)
                
            return f"Updated {filename} successfully."
        except Exception as e:
            return f"Error updating state: {str(e)}"
