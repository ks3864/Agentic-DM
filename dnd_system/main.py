from crewai import Crew, Process
from agents import DndAgents
from tasks import DndTasks
from dotenv import load_dotenv
import os

import logging
import sys
import re

from tools.state_tool import ReadStateTool

load_dotenv()

# This class redirects stdout to the logging system.
class StreamToLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().split('\n'):
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        if len(self.logger.handlers) > 0:
            self.logger.handlers[0].flush()

def setup_logging():
    # Store original stdout
    original_stdout = sys.stdout
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game.log")

    # Custom formatter to apply different formats and strip ANSI codes
    class ConditionalFormatter(logging.Formatter):
        def __init__(self):
            super().__init__()
            self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            self.default_format = '[%(levelname)s] %(asctime)s: %(message)s'
            self.stdout_format = '%(message)s'

        def format(self, record):
            is_stdout = record.name == 'STDOUT'
            
            # For the file handler, always strip ANSI
            if isinstance(self, FileFormatter):
                record.msg = self.ansi_escape.sub('', str(record.msg))
                if is_stdout:
                    formatter = logging.Formatter(self.stdout_format)
                else:
                    formatter = logging.Formatter(self.default_format)
            # For the console handler, keep ANSI colors
            else:
                if is_stdout:
                    formatter = logging.Formatter(self.stdout_format)
                else:
                    formatter = logging.Formatter(self.default_format)
            return formatter.format(record)

    class FileFormatter(ConditionalFormatter):
        pass

    # Filter to flush handlers after each log
    class FlushFilter(logging.Filter):
        def filter(self, record):
            for handler in logging.getLogger().handlers:
                handler.flush()
            return True

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [] # Clear any existing handlers
    root_logger.addFilter(FlushFilter())

    # Console handler writing to original stdout
    console_handler = logging.StreamHandler(original_stdout)
    console_handler.setFormatter(ConditionalFormatter())
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(FileFormatter())
    root_logger.addHandler(file_handler)

    # Redirect stdout and stderr to the logging system
    stdout_logger = logging.getLogger('STDOUT')
    sys.stdout = StreamToLogger(stdout_logger, logging.INFO)
    sys.stderr = StreamToLogger(stdout_logger, logging.ERROR)


class DndGame:
    def __init__(self):
        setup_logging()
        self.agents = DndAgents()
        self.tasks = DndTasks()

        # For reading game state
        self.state_tool = ReadStateTool()

        # Create Agents
        self.narrator = self.agents.narrator()
        self.rules_lawyer = self.agents.rules_lawyer()
        self.scribe = self.agents.scribe()
        
        # Create Tasks
        self.task_mechanics = self.tasks.resolve_mechanics(self.rules_lawyer)
        self.task_state = self.tasks.update_state(self.scribe, self.task_mechanics)
        self.task_narrative = self.tasks.generate_narrative(self.narrator, self.task_mechanics, self.task_state)

        # Create crew
        self.crew = Crew(
            agents=[self.rules_lawyer, self.scribe, self.narrator],
            tasks=[self.task_mechanics, self.task_state, self.task_narrative],
            process=Process.sequential,
            verbose=True,
            tracing=True,
            memory=False
        )
        
    def turn(self, player_input, history=[]):
        logging.info(f"Player Input: {player_input}")

        # Get current world state and event history to provide context
        # to agents
        world_state = self.state_tool._run("world")
        character_state = self.state_tool._run("character")
        history_text = "\n".join(history[-12:])  # Last 6 turns (12 messages)
        
        # Extract story_context from world_state JSON
        import json
        try:
            world_data = json.loads(world_state) if isinstance(world_state, str) else world_state
            story_context = world_data.get("story_context", "Adventure in the Sword Coast region.")
        except:
            story_context = "Adventure in the Sword Coast region."

        inputs = {
            "player_input": player_input,
            "history": history_text,
            "world_state": world_state,
            "character_state": character_state,
            "story_context": story_context
        }
        
        result = self.crew.kickoff(inputs=inputs)
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
