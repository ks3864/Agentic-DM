from crewai import Agent
from tools.dice_tool import DiceTool
from tools.state_tool import ReadStateTool, UpdateStateTool
from tools.rag_tool import AdventureRAGTool, RulesRAGTool
from tools.graph_tool import ReadGraphTool, UpdateGraphTool

NARRATOR_BACKSTORY = """
You are the voice of the world. You describe scenes, act out NPCs, and weave the narrative. 
You use the adventure book to find plot points and steer the player back to the main story if 
they deviate. You always check the current location and quest status before narrating.
""".strip()

RULES_LAWYER_BACKSTORY = """
You are an expert in D&D 5e mechanics. When a player attempts an action, you determine if a check is 
needed. If a check is needed and the player HAS NOT provided a roll result, you must REQUEST the roll 
(e.g., "Please roll a DC 15 Strength check"). If the player HAS provided a roll result (e.g., "I rolled 
a 18"), you determine the outcome based on the rules. You consult the rulebooks to ensure accuracy.
""".strip()

SCRIBE_BACKSTORY = """
You are the record keeper for a D&D campaign. You update the character sheet (HP, inventory, XP) and the 
world state (location, time, quests) based on the events of the game. You ensure consistency in the data.
""".strip()

class DndAgents:
    # def dungeon_master(self):
    #     return Agent(
    #         role='Dungeon Master',
    #         goal='Orchestrate the D&D game, ensuring a fun and coherent experience.',
    #         backstory="""You are the Dungeon Master (DM) for a D&D 5e campaign. 
    #         Your job is to manage the flow of the game, delegate tasks to your specialized agents, 
    #         and synthesize their outputs into a cohesive experience for the player.
    #         You must ensure the rules are followed, the story progresses, and the state is maintained.""",
    #         allow_delegation=True,
    #         verbose=True
    #     )

    def narrator(self):
        return Agent(
            role='Narrator',
            goal='Tell a compelling story and guide the player through the adventure.',
            backstory=NARRATOR_BACKSTORY,
            # llm="gpt-5-nano",
            tools=[AdventureRAGTool(), ReadGraphTool()],
            verbose=True
        )

    def rules_lawyer(self):
        return Agent(
            role='Rules Lawyer',
            goal='Adjudicate actions based on D&D 5e rules.',
            backstory=RULES_LAWYER_BACKSTORY,
            # llm="gpt-5-nano",
            tools=[RulesRAGTool()],
            verbose=True
        )

    def scribe(self):
        return Agent(
            role='Scribe',
            goal='Maintain the game state accurately.',
            backstory=SCRIBE_BACKSTORY,
            # llm="gpt-5-nano",
            tools=[UpdateStateTool(), UpdateGraphTool(), ReadGraphTool()],
            verbose=True
        )
