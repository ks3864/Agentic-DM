import sys
import os

# Ensure we can import dnd_system modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import chainlit as cl
from dnd_system.main import DndGame

game = DndGame()

import random
import asyncio

import shutil

STATE_DIR = os.path.join(os.path.dirname(__file__), "state")

def reset_state():
    """Resets the game state and knowledge graph from templates."""
    templates = [
        ("character_sheet_template.json", "character_sheet.json"),
        ("world_state_template.json", "world_state.json"),
        ("knowledge_graph_template.json", "knowledge_graph.json")
    ]
    
    for template, target in templates:
        src = os.path.join(STATE_DIR, template)
        dst = os.path.join(STATE_DIR, target)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Reset {target} from {template}")
        else:
            print(f"Warning: Template {template} not found.")

@cl.on_chat_start
async def start():
    reset_state()
    cl.user_session.set("history", [])
    await cl.Message(content="Welcome to the Lost Mine of Phandelver! I am your Dungeon Master. What would you like to do?").send()

@cl.action_callback("roll_dice")
async def on_action(action: cl.Action):
    # Remove the button
    await action.remove()
    
    # Animation
    msg = cl.Message(content="Rolling dice... 🎲")
    await msg.send()
    
    for _ in range(5):
        msg.content = f"Rolling... 🎲 {random.randint(1, 20)}"
        await msg.update()
        await asyncio.sleep(0.1)
        
    result = random.randint(1, 20)
    msg.content = f"🎲 You rolled a **{result}**!"
    await msg.update()
    
    # Send result to game
    await main(cl.Message(content=f"I rolled {result}"))

@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    
    history = cl.user_session.get("history", [])
    history.append(f"Player: {message.content}")
    
    # Run the game turn asynchronously to avoid blocking
    response = await cl.make_async(game.turn)(message.content, history)
    
    # CrewAI returns a generic object, we need the string output
    output_text = str(response)
    history.append(f"DM: {output_text}")
    
    # Keep history manageable (last 10 turns)
    if len(history) > 20:
        history = history[-20:]
    cl.user_session.set("history", history)
    
    # CrewAI returns a generic object, we need the string output
    output_text = str(response)
    
    actions = []
    if "[REQUEST_ROLL]" in output_text:
        actions = [cl.Action(name="roll_dice", payload={"value": "roll"}, label="Roll Dice 🎲")]
        # Optional: Remove the tag from the display text if desired, but keeping it is fine for debugging
        # output_text = output_text.replace("[REQUEST_ROLL]", "")
    
    msg.content = output_text
    msg.actions = actions
    await msg.update()
