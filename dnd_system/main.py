from crewai import Crew, Process
from agents import DndAgents
from tasks import DndTasks
from dotenv import load_dotenv
import os

import logging
import sys
import re

load_dotenv()


# class Tee(object):
#     def __init__(self, *files):
#         self.files = files

#     def write(self, obj):
#         # For the original stdout (terminal), write the object as is (with colors)
#         if self.files[0].isatty():
#             self.files[0].write(obj)
#             self.files[0].flush()
#         if len(self.files) > 1:
#             # For log file, strip ANSI codes before writing
#             ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
#             clean_obj = ansi_escape.sub('', obj)
#             self.files[1].write(clean_obj)
#             self.files[1].flush()

#     def flush(self) :
#         for f in self.files:
#             f.flush()

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
        pass

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

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [] # Clear any existing handlers

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
