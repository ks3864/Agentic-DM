import sys
import os
import asyncio
# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from dnd_system.main import DndGame
from dnd_system.app import reset_state

# Mock Chainlit message
class MockMessage:
    def __init__(self, content):
        self.content = content

async def run_simulation():
    print("--- Starting Game Simulation (10 Turns) ---")
    
    # Reset state to ensure clean start
    reset_state()
    
    game = DndGame()
    
    # Pre-defined inputs to simulate the user's reported flow
    inputs = [
        "Start my mission",
        "Continue moving forward with caution.",
        "I rolled a 15 for Stealth.", # Success
        "Proceed towards the 'Goblin Ambush'.",
        "Look for ambush.",
        "I rolled a 5 for Perception.", # Fail
        "Attack the goblins!",
        "I rolled a 18 to hit.",
        "Use my potion.",
        "Check the dead horses."
    ]
    
    history = []
    
    for i, user_input in enumerate(inputs):
        print(f"\n[Turn {i+1}] User: {user_input}")
        
        # Run game turn
        response = game.turn(user_input)
        output_text = str(response)
        
        print(f"[Turn {i+1}] System: {output_text[:200]}...") # Print first 200 chars
        
        # Check for repetition (simple check)
        if i > 0 and output_text == history[-1]:
            print("!!! DETECTED EXACT REPETITION !!!")
        
        # Check for looping requests (e.g. asking for stealth check again after it was provided)
        if "Stealth Check" in output_text and i > 2:
             print("!!! POTENTIAL LOOP: Asking for Stealth Check again !!!")

        history.append(output_text)
        
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    asyncio.run(run_simulation())
