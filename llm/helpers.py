# The goal is to give the same prompts to all the LLMs
from enum import Enum
import os

class ACTIONS(Enum):
    KEEP_DICE = "keep_dice"
    YIELD_TOKYO = "yield_tokyo"

with open("./llm/rules.md", "r") as f:
    RULES = f.read()

SYSTEM_PROMPT = f"""You are an expert player of the game godzilla-v2. Your goal is to play the best possible action given the circumstances, to eventually win the game.
<GameRules>
{RULES}
</GameRules>
"""

TURN_PROMPT = """
Given the current state of the game, you are required to play your turn.
<GameState>
{GAME_STATE}
</GameState>

Action: {ACTION}
"""

ACTIONS_DESCRIPTIONS = {
    ACTIONS.KEEP_DICE: {
        "type": "function",
        "function": {
            "name": "keep_dice",
            "description": "Given a mask of the dice results, the masked out dice are retained and the rest are rerolled.",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": ["keep_mask"],
                "properties": {
                    "keep_mask": {
                        "type": "array",
                        "items": {
                            "type": "boolean",
                            "description": "True means keeping the dice, False means rerolling the dice.",
                        },
                    },
                },
                "additionalProperties": False,
            }
        }
    },
    ACTIONS.YIELD_TOKYO: {
        "type": "function",
        "function": {
            "name": "yield_tokyo",
            "description": "Tokyo is yielded or not",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": ["yield_tokyo"],
                "properties": {
                    "yield_tokyo": {
                        "type": "boolean",
                        "description": "True means yielding Tokyo, False means staying in Tokyo.",
                    },
                },
                "additionalProperties": False,
            }
        }
    },
}

def get_llm_request_args(action: ACTIONS, game_state: dict):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TURN_PROMPT.format(GAME_STATE=game_state, ACTION=action.value)},
    ]
    tools = [ACTIONS_DESCRIPTIONS[action]]
    return messages, tools
    

