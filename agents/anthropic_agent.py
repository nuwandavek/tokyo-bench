from typing import List, Dict, Tuple
from anthropic import Anthropic
import os
import json

from constants import DIESIDE
from player import PlayerState, Player
from llm.helpers import get_llm_request_args, ACTIONS, MODEL_CLASS

MODEL = 'claude-3-5-sonnet-20241022'

class AnthropicAgent(Player):
    def __init__(self, idx: int, name: str):
        super().__init__(idx, name)
        key=os.getenv("ANTHROPIC_API_KEY", None)
        assert key is not None, "Please set the ANTHROPIC_API_KEY environment variable"
        self.client = Anthropic(api_key=key)

    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        gamestate = self.construct_gamestate(other_player_states)
        gamestate['dice_results'] = [x.value for x in dice_results]
        gamestate['roll_counter'] = roll_counter + 1
        messages, tools, tool_choice = get_llm_request_args(ACTIONS.KEEP_DICE, gamestate, model_class=MODEL_CLASS.ANTHROPIC)
        response = self.client.messages.create(model=MODEL, messages=messages, tools=tools, max_tokens=1024, tool_choice=tool_choice)
        llm_response = response.content[0].input
        assert len(llm_response["keep_mask"]) == len(dice_results), f"Expected mask of length {len(dice_results)}, got {len(llm_response["keep_mask"])}"
        return llm_response["keep_mask"], llm_response["reason"]


    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        gamestate = self.construct_gamestate(other_player_states)
        messages, tools, tool_choice = get_llm_request_args(ACTIONS.YIELD_TOKYO, gamestate, model_class=MODEL_CLASS.ANTHROPIC)
        response = self.client.messages.create(model=MODEL, messages=messages, tools=tools, tool_choice=tool_choice,  max_tokens=1024)
        llm_response = response.content[0].input
        return llm_response["yield_tokyo"], llm_response["reason"]

