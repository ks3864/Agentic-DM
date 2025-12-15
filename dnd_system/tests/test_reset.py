import os
import sys
# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
import json
import shutil
from dnd_system.app import reset_state, STATE_DIR

def test_reset():
    # 1. Modify character_sheet.json
    target_file = os.path.join(STATE_DIR, "character_sheet.json")
    
    # Ensure templates exist
    if not os.path.exists(os.path.join(STATE_DIR, "character_sheet_template.json")):
        print("Template not found!")
        return

    # Run reset first to ensure clean state
    reset_state()
    
    with open(target_file, 'r') as f:
        data = json.load(f)
    print(f"Initial HP: {data['stats']['hp']}")
    
    # Modify
    data['stats']['hp'] = 999
    with open(target_file, 'w') as f:
        json.dump(data, f)
    print("Modified HP to 999")
    
    # 2. Run reset_state
    print("Running reset_state()...")
    reset_state()
    
    # 3. Verify
    with open(target_file, 'r') as f:
        new_data = json.load(f)
    print(f"Post-reset HP: {new_data['stats']['hp']}")
    
    if new_data['stats']['hp'] == 12: # Original value
        print("SUCCESS: State reset correctly.")
    else:
        print("FAILURE: State did not reset.")

if __name__ == "__main__":
    test_reset()
