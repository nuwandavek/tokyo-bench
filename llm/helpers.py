# The goal is to give the same prompts to all the LLMs
from enum import Enum
import json

class ACTIONS(Enum):
    KEEP_DICE = "keep_dice"
    YIELD_TOKYO = "yield_tokyo"

with open("./llm/rules.md", "r") as f:
    RULES = f.read()

SYSTEM_PROMPT = f"""You are an expert player of the game tokyo-bench. Your goal is to play the best possible action given the circumstances, to eventually win the game.
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
        "name": "keep_dice",
        "description": "Given a mask of the dice results, and reason why, the masked out dice are retained and the rest are rerolled.",
        # "strict": True,
        "parameters": {
            "type": "object",
            "required": ["reason", "keep_mask"],
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "1 or 2 sentence reason for keeping the dice. Maybe comment on personal strategy or opponent strategy.",
                },
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
    },
    ACTIONS.YIELD_TOKYO: {
        "name": "yield_tokyo",
        "description": "Tokyo is yielded or not",
        # "strict": True,
        "parameters": {
            "type": "object",
            "required": ["reason", "yield_tokyo"],
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "1 or 2 sentence reason for yielding Tokyo. Maybe comment on personal strategy or opponent strategy.",
                },
                "yield_tokyo": {
                    "type": "boolean",
                    "description": "True means yielding Tokyo, False means staying in Tokyo.",
                },
            },
            "additionalProperties": False,
        }
    },
}

class MODEL_CLASS(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

def get_llm_request_args(action: ACTIONS, game_state: dict, model_class=None):
    assert model_class is not None, "Please specify the model class"
    messages = [
        {"role": "user", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TURN_PROMPT.format(GAME_STATE=game_state, ACTION=action.value)},
    ]

    if model_class == MODEL_CLASS.ANTHROPIC:
        tools = [json.loads(json.dumps(ACTIONS_DESCRIPTIONS[action]).replace("parameters", "input_schema"))]
        tool_choice = {"type": "tool", "name": action.value}
        return messages, tools, tool_choice
    elif model_class == MODEL_CLASS.OPENAI:
        tools = [{"type": "function", "function": ACTIONS_DESCRIPTIONS[action]}]
        tool_choice = {"type": "function", "function": {"name": action.value}}
    return messages, tools, tool_choice
    

