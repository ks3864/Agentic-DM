from crewai import Crew, Process
from agents import DndAgents
from tasks import DndTasks
from dotenv import load_dotenv
import os

import logging
import sys

load_dotenv()

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # If you want the output to be visible immediately
    def flush(self) :
        for f in self.files:
            f.flush()

def setup_logging():
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game.log")
    
    # Configure standard logging
    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Redirect stdout and stderr to the log file as well
    f = open(log_file_path, 'a', encoding='utf-8')
    sys.stdout = Tee(sys.stdout, f)
    sys.stderr = Tee(sys.stderr, f)

class DndGame:
    def __init__(self):
        setup_logging()
        self.agents = DndAgents()
        self.tasks = DndTasks()
        
    def turn(self, player_input, history=[]):
        logging.info(f"Player Input: {player_input}")
        # Create Agents
        narrator = self.agents.narrator()
        rules_lawyer = self.agents.rules_lawyer()
        scribe = self.agents.scribe()
        
        # Create Tasks
        task_mechanics = self.tasks.resolve_mechanics(rules_lawyer, player_input)
        task_state = self.tasks.update_state(scribe, task_mechanics)
        task_narrative = self.tasks.generate_narrative(narrator, player_input, task_mechanics, task_state, history)
        
        # Create Crew
        crew = Crew(
            agents=[rules_lawyer, scribe, narrator],
            tasks=[task_mechanics, task_state, task_narrative],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return result

if __name__ == "__main__":
    game = DndGame()
    print("Welcome to the D&D Agentic DM! Type 'exit' to quit.")
    while True:
        user_input = input("Player: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = game.turn(user_input)
        print(f"DM: {response}")
