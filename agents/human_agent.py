from typing import List, Dict, Tuple

from constants import DIESIDE
from player import PlayerState, Player

class HumanAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        return [x == 'y' for x in list(input("Enter like 'yyyynn': "))], "??"

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return input("Enter 'y' to yield Tokyo, 'n' to stay in Tokyo: ") == 'y', "??"
