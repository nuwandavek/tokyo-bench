import json
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field
from constants import MAX_HEALTH, VICTORY_PTS_WIN, DIESIDE
from llm.helpers import ACTIONS, get_llm_request_args
from litellm import completion


class PlayerState(BaseModel):
    health: int = Field(default=MAX_HEALTH, ge=0, le=MAX_HEALTH)
    victory_points: int = Field(default=0, ge=0, le=VICTORY_PTS_WIN)
    in_tokyo: bool = Field(default=False)


class Player(ABC):
    def __init__(self, idx: int, name: str):
        self.idx = idx
        self._name = name
        self._state = PlayerState()
        self.max_health = MAX_HEALTH
        self.max_victory_points = VICTORY_PTS_WIN
        self.min_health = 0
        self.min_victory_points = 0
    
    @property
    def name(self):
        return self._name
    
    @property
    def state(self):
        return self._state.model_copy(deep=True)
    
    def increment_health(self, n: int):
        self._state.health = max(self.min_health, min(self.max_health, self._state.health + n))
    
    def increment_victory_points(self, n: int):
        self._state.victory_points = max(self.min_victory_points, min(self.max_victory_points, self._state.victory_points + n))
    
    def set_tokyo(self, in_tokyo: bool):
        self._state.in_tokyo = in_tokyo
    
    @abstractmethod
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        """
        Returns a mask of which dice to keep and which to reroll, and reason
        Length of the mask should be equal to the length of dice_results.
        """
        pass

    @abstractmethod
    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        """
        Returns whether the player should yield Tokyo, and reason
        """
        pass

    def __str__(self):
        return f'p{self.idx}_{self.name}'

    def construct_gamestate(self, other_player_states: Dict[str, Tuple[int, PlayerState]]):
        return {
            'ego_agent': {'name': self.name, 'idx': self.idx, 'state': self.state.model_dump()},
            'other_agents': [{'name': name, 'idx': idx, 'state': state} for name, (idx, state) in other_player_states.items()]
            }
    
    def llm_call(self, other_player_states: Dict[str, Tuple[int, PlayerState]], action: ACTIONS, dice_results: List[DIESIDE], roll_counter: int, model: str):
        gamestate = self.construct_gamestate(other_player_states)
        if action == ACTIONS.KEEP_DICE:
            gamestate['dice_results'] = [x.value for x in dice_results]
            gamestate['roll_counter'] = roll_counter + 1
        
        messages, tools, tool_choice = get_llm_request_args(action, gamestate)
        response = completion(model=model, messages=messages, tools=tools, tool_choice=tool_choice)
        llm_response = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        if action == ACTIONS.KEEP_DICE:
            assert len(llm_response["keep_mask"]) == len(dice_results), f"Expected mask of length {len(dice_results)}, got {len(llm_response["keep_mask"])}"
            return llm_response["keep_mask"], llm_response["reason"]
        elif action == ACTIONS.YIELD_TOKYO:
            return llm_response["yield_tokyo"], llm_response["reason"]

    