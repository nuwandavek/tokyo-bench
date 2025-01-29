from typing import List, Dict, Tuple
from constants import DIESIDE
from player import PlayerState, Player
from llm.helpers import ACTIONS

MODEL = 'claude-3-5-sonnet-20241022'

class AnthropicAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        return self.llm_call(other_player_states, ACTIONS.KEEP_DICE, dice_results, roll_counter, MODEL)

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return self.llm_call(other_player_states, ACTIONS.YIELD_TOKYO, None, None, MODEL)
