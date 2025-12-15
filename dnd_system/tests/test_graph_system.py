import unittest
import json
import os
import shutil
import sys
# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from dnd_system.tools.graph_tool import ReadGraphTool, UpdateGraphTool

class TestGraphSystem(unittest.TestCase):
    def setUp(self):
        # Setup a temporary state directory
        self.test_state_dir = os.path.join(os.path.dirname(__file__), "test_state_graph")
        os.makedirs(self.test_state_dir, exist_ok=True)
        
        # Create dummy graph
        self.graph_data = {
            "nodes": [
                {
                    "id": "start_node",
                    "name": "Start Location",
                    "type": "Location",
                    "description": "You are at the start.",
                    "boxed_text": "Welcome to the start.",
                    "npcs": ["Guide"],
                    "status": "active"
                },
                {
                    "id": "next_node",
                    "name": "Next Location",
                    "type": "Location",
                    "description": "You are at the next place.",
                    "status": "locked"
                }
            ],
            "edges": [
                {
                    "source": "start_node",
                    "target": "next_node",
                    "type": "leads_to",
                    "condition": "None"
                }
            ]
        }
        
        with open(os.path.join(self.test_state_dir, "knowledge_graph.json"), "w") as f:
            json.dump(self.graph_data, f)
            
        # Patch STATE_DIR in the tool module
        import dnd_system.tools.graph_tool
        self.original_state_dir = dnd_system.tools.graph_tool.STATE_DIR
        dnd_system.tools.graph_tool.STATE_DIR = self.test_state_dir

    def tearDown(self):
        # Restore STATE_DIR
        import dnd_system.tools.graph_tool
        dnd_system.tools.graph_tool.STATE_DIR = self.original_state_dir
        
        # Clean up test dir
        shutil.rmtree(self.test_state_dir)

    def test_read_graph(self):
        tool = ReadGraphTool()
        result = tool._run("start_node")
        self.assertIn("Current Scene: Start Location", result)
        self.assertIn("Welcome to the start.", result)
        self.assertIn("To 'Next Location' (next_node)", result)

    def test_update_graph(self):
        tool = UpdateGraphTool()
        result = tool._run("start_node", "completed")
        self.assertIn("Updated node 'start_node' status to 'completed'", result)
        
        # Verify update
        with open(os.path.join(self.test_state_dir, "knowledge_graph.json"), "r") as f:
            data = json.load(f)
        node = next(n for n in data["nodes"] if n["id"] == "start_node")
        self.assertEqual(node["status"], "completed")

if __name__ == "__main__":
    unittest.main()
