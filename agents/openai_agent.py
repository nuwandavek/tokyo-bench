from typing import List, Dict, Tuple
from openai import OpenAI
import os
import json

from constants import DIESIDE
from player import PlayerState, Player
from llm.helpers import get_llm_request_args, ACTIONS

MODEL = 'gpt-4o'

class OpenAIAgent(Player):
    def __init__(self, idx: int, name: str):
        super().__init__(idx, name)
        key=os.getenv("OPENAI_API_KEY", None)
        assert key is not None, "Please set the OPENAI_API_KEY environment variable"
        self.client = OpenAI(api_key=key)

    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> List[bool]:
        gamestate = self.construct_gamestate(other_player_states)
        gamestate['dice_results'] = [x.value for x in dice_results]
        gamestate['roll_counter'] = roll_counter + 1
        messages, tools = get_llm_request_args(ACTIONS.KEEP_DICE, gamestate)
        response = self.client.chat.completions.create(model=MODEL, messages=messages, tools=tools,
                                                  tool_choice={"type": "function", "function": {"name": "keep_dice"}})
        llm_response = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["keep_mask"]
        assert len(llm_response) == len(dice_results), f"Expected mask of length {len(dice_results)}, got {len(llm_response)}"
        return llm_response


    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> bool:
        gamestate = self.construct_gamestate(other_player_states)
        messages, tools = get_llm_request_args(ACTIONS.YIELD_TOKYO, gamestate)
        response = self.client.chat.completions.create(model=MODEL, messages=messages, tools=tools,
                                                  tool_choice={"type": "function", "function": {"name": "yield_tokyo"}})
        llm_response = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["yield_tokyo"]
        return llm_response

