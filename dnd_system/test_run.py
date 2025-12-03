from dnd_system.main import DndGame
import sys
import os

# Ensure imports work
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

game = DndGame()
print("--- Turn 1: I try to hide ---")
try:
    result = game.turn("I try to hide in the bushes.")
    print(result)
except Exception as e:
    print(f"Error: {e}")

print("\n--- Turn 2: I rolled 18 ---")
try:
    result = game.turn("I rolled 18 for stealth.")
    print(result)
except Exception as e:
    print(f"Error: {e}")
