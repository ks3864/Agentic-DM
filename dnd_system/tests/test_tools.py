import unittest
import json
import os
import shutil
from dnd_system.tools.state_tool import UpdateStateTool, ReadStateTool

class TestStateTools(unittest.TestCase):
    def setUp(self):
        # Setup a temporary state directory
        self.test_state_dir = os.path.join(os.path.dirname(__file__), "test_state")
        os.makedirs(self.test_state_dir, exist_ok=True)
        
        # Create dummy state files
        self.world_state = {
            "current_location": "Test Location",
            "pending_roll": None
        }
        self.char_state = {
            "name": "Test Char",
            "hp": 10
        }
        
        with open(os.path.join(self.test_state_dir, "world_state.json"), "w") as f:
            json.dump(self.world_state, f)
            
        with open(os.path.join(self.test_state_dir, "character_sheet.json"), "w") as f:
            json.dump(self.char_state, f)
            
        # Patch STATE_DIR in the tool module (this is a bit hacky but works for simple tests)
        import dnd_system.tools.state_tool
        self.original_state_dir = dnd_system.tools.state_tool.STATE_DIR
        dnd_system.tools.state_tool.STATE_DIR = self.test_state_dir

    def tearDown(self):
        # Restore STATE_DIR
        import dnd_system.tools.state_tool
        dnd_system.tools.state_tool.STATE_DIR = self.original_state_dir
        
        # Clean up test dir
        shutil.rmtree(self.test_state_dir)

    def test_read_state(self):
        tool = ReadStateTool()
        result = tool._run("world")
        data = json.loads(result)
        self.assertEqual(data["current_location"], "Test Location")
        
        result = tool._run("character")
        data = json.loads(result)
        self.assertEqual(data["name"], "Test Char")

    def test_update_state_with_dict(self):
        tool = UpdateStateTool()
        updates = {
            "file_type": "world",
            "updates": {
                "pending_roll": "Stealth Check"
            }
        }
        # Pass dict directly
        result = tool._run(updates)
        self.assertIn("Updated world_state.json successfully", result)
        
        # Verify update
        with open(os.path.join(self.test_state_dir, "world_state.json"), "r") as f:
            data = json.load(f)
        self.assertEqual(data["pending_roll"], "Stealth Check")

    def test_update_state_with_string(self):
        tool = UpdateStateTool()
        updates = {
            "file_type": "character",
            "updates": {
                "hp": 5
            }
        }
        # Pass string
        result = tool._run(json.dumps(updates))
        self.assertIn("Updated character_sheet.json successfully", result)
        
        # Verify update
        with open(os.path.join(self.test_state_dir, "character_sheet.json"), "r") as f:
            data = json.load(f)
        self.assertEqual(data["hp"], 5)

if __name__ == "__main__":
    unittest.main()
