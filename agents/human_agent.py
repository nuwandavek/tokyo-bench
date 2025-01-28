from typing import List, Dict

from constants import DIESIDE
from player import PlayerState, Player

class HumanAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, PlayerState], reroll_n: int) -> List[bool]:
        return [x == 'y' for x in list(input("Enter like 'yyyynn': "))]

    def yield_tokyo(self, other_player_states: Dict[str, PlayerState]) -> bool:
        return input("Enter 'y' to yield Tokyo, 'n' to stay in Tokyo: ") == 'y'
