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

TURN_PROMPT_NO_TOOL = """
Given the current state of the game, you are required to play your turn.
<GameState>
{GAME_STATE}
</GameState>

Action: {ACTION}
Action description and Output format: {OUTPUT_FORMAT}
"""


ACTIONS_DESCRIPTIONS = {
    ACTIONS.KEEP_DICE: {
        "type": "function",
        "function": {
            "name": "keep_dice",
            "description": "Given a mask of the dice results, and reason why, the masked out dice are retained and the rest are rerolled.",
            "strict": True,
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
                        "description": "Mask of which dice to keep. There are 6 dice in total.",
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
        }
    },
}

ACTIONS_OUTPUT_FORMAT = {
    ACTIONS.KEEP_DICE: """You need to give a mask for which dice to keep, and which to reroll. Provide the reasoning for your choice in <reason></reason> tags. The reasoning should be 1 or 2 sentences for keeping the dice. Maybe comment on personal strategy or opponent strategy.
The mask of which dice to keep should be provided in <move></move> tags. There are 6 dice in total. Example: <move>[true, false, true, false, true, false]</move>
""",
    ACTIONS.YIELD_TOKYO: """You need to either yield Tokyo or not. Provide the reasoning for your choice in <reason></reason> tags. The reasoning should be 1 or 2 sentences for yielding Tokyo. Maybe comment on personal strategy or opponent strategy.
The choice of yielding Tokyo should be provided in <move></move> tags. Example: <move>true</move>
    """
}



def get_llm_request_args(action: ACTIONS, game_state: dict, tool_use: bool = True):
    if tool_use:
        user_prompt_content = TURN_PROMPT.format(GAME_STATE=game_state, ACTION=action.value)
        tools = [ACTIONS_DESCRIPTIONS[action]]
        tool_choice = {"type": "function", "function": {"name": action.value}}
    else:
        user_prompt_content = TURN_PROMPT_NO_TOOL.format(GAME_STATE=game_state, ACTION=action.value, OUTPUT_FORMAT=ACTIONS_OUTPUT_FORMAT[action])
        tools = None
        tool_choice = None
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt_content},
    ]

    return messages, tools, tool_choice


