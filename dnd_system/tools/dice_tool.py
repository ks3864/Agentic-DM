from crewai.tools import BaseTool
import random

class DiceTool(BaseTool):
    name: str = "Roll Dice"
    description: str = "Rolls dice using D&D notation (e.g., '1d20+5'). Returns the total and individual rolls."

    def _run(self, expression: str) -> str:
        try:
            # Remove spaces
            expression = expression.replace(" ", "")
            
            # Handle modifiers
            if '+' in expression:
                parts = expression.split('+')
                modifier = int(parts[1])
                dice_part = parts[0]
            elif '-' in expression:
                parts = expression.split('-')
                modifier = -int(parts[1])
                dice_part = parts[0]
            else:
                modifier = 0
                dice_part = expression
            
            if 'd' not in dice_part:
                return "Invalid format. Use XdY+Z (e.g., 1d20+2)"
            
            num_dice_str, die_type_str = dice_part.split('d')
            num_dice = int(num_dice_str) if num_dice_str else 1
            die_type = int(die_type_str)
            
            rolls = [random.randint(1, die_type) for _ in range(num_dice)]
            total = sum(rolls) + modifier
            
            return f"Rolled {expression}: {rolls} + {modifier} = {total}"
        except Exception as e:
            return f"Error rolling dice: {str(e)}"
