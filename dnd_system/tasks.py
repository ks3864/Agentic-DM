from crewai import Task


RESOLVE_MECHANICS_TASK_DESCRIPTION = """
1. CHECK HISTORY: Look at "pending_roll" and "recent_events" from the current world state.
   - If player input is a follow-up to a requested roll (e.g. "I rolled 15"), MATCH it to "pending_roll".
   - If the player is repeating an action that was JUST resolved (e.g. "Proceed" after a successful check), do NOT ask for the check again. Treat it as a confirmed move.

2. DETERMINE MECHANICS:
   - If input is a Roll Result (e.g. "15"):
      * Compare to DC.
      * Output: "Outcome: [Success/Failure]. [Consequence]."
      * If Success and roll was for movement/travel, add "Action: Move to [Next Location]".
   - If input is an Action (e.g. "Attack", "Sneak"):
      * If a check is needed and NOT in history, output "REQUEST_ROLL: [Check] (DC [X])".
      * If no check needed (or already passed), output "Action: [Action]".

OUTPUT FORMAT:
   - "REQUEST_ROLL: ..."
   - "Outcome: ... Action: ..."
   - "No mechanics needed."

Current world state: {world_state}

The player input: "{player_input}".
""".strip()

UPDATE_STATE_TASK_DESCRIPTION = """
Execute state updates based on the mechanics output.
            
1. PENDING ROLLS:
   - If "REQUEST_ROLL", set "pending_roll" in game state.
   - If "Outcome: ...", CLEAR "pending_roll" (set to null).

2. WORLD STATE & MOVEMENT:
   - If "Outcome: Success" AND consequence implies movement/progression:
      a. Use ReadGraphTool with the CURRENT location ID to find available transitions.
      b. Identify the target node ID for the transition (e.g. "leads_to").
      c. Use UpdateStateTool to set "current_location" to that NEW node ID.
      d. Add "Moved to [New Location Name]" to "recent_events".
   - If "Action: Move to [Location]" is explicitly stated, update "current_location".
   - Always log significant events to "recent_events". These include brief summaries of player actions, pending skill checks, action and skill check outcomes, and changes to character or world state.

3. GRAPH:
   - If the player moves to a new node, use UpdateGraphTool to mark the OLD node as 'visited'.

OUTPUT: Summarize exactly what changed (e.g. "Location updated to X", "Pending roll cleared").
""".strip()

GENERATE_NARRATIVE_TASK_DESCRIPTION = """
Write a narrative response to the player to progress the game based on the current scene, available transitions,
recent events, and the player's proposed action.

1. Check the current world state below for current scene details, recent events, and valid transitions. 
   - If the current node has "boxed_text", use that info in your response.
   - Only allow the player to move to locations listed in "Available Transitions".
   
   FALLBACK LOGIC:
   - If the current location has no transitions or is not found in the graph:
      a. Use AdventureRAGTool to search for the current location name and "next area" or "leads to".
      b. Infer the logical next steps from the search results.
      c. Narrate the scene based on these next steps and allow the player to proceed logically.

2. If the mechanics task output includes "REQUEST_ROLL", ask the player to make that roll. Explain why.
   IMPORTANT: If you are asking for a roll, you MUST append the string "[REQUEST_ROLL]" to the very end of your response.

3. If the mechanics task was a resolved outcome, describe the result of the player's action.

Use the AdventureRAGTool to find context about the current location and NPCs. 
IMPORTANT: When using AdventureRAGTool, pass the 'current_location' from the world state to the tool.
Ignore any results describing scenes or encounters that do not match the current location or scene.

If the player is straying from the plot, steer them back using the available transitions.

IMPORTANT: Keep your response as concise as possible, no more than 2 paragraphs. Do NOT use generic or cliche descriptions of 
the current scene or the player's adventure. Do not include unnecessary mechanics 
information in your response, especially in NPC dialogue.

Current world state: {world_state}
"""


class DndTasks:
    def resolve_mechanics(self, agent):
        return Task(
            description=RESOLVE_MECHANICS_TASK_DESCRIPTION,
            expected_output="Mechanical analysis including outcomes and required actions.",
            agent=agent
        )

    def update_state(self, agent, mechanics_task):
        return Task(
            description=UPDATE_STATE_TASK_DESCRIPTION,
            expected_output="Summary of state updates.",
            agent=agent,
            context=[mechanics_task]
        )
        
    def generate_narrative(self, agent, mechanics_task, state_task):
        return Task(
            description=GENERATE_NARRATIVE_TASK_DESCRIPTION,
            expected_output="The final narrative response to the player.",
            agent=agent,
            context=[mechanics_task, state_task]
        )
