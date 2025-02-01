from typing import List, Dict, Tuple
from constants import DIESIDE
from player import PlayerState, Player
from llm.helpers import ACTIONS

MODEL = 'cerebras/deepseek-r1-distill-llama-70b'


class CerebrasR1Llama70BAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        return self.llm_call(other_player_states, ACTIONS.KEEP_DICE, dice_results, roll_counter, MODEL, tool_use=False)

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return self.llm_call(other_player_states, ACTIONS.YIELD_TOKYO, None, None, MODEL, tool_use=False)
