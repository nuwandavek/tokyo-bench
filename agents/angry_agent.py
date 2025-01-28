from typing import List, Dict

from constants import DIESIDE
from player import PlayerState, Player

class AngryAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, PlayerState], reroll_n: int) -> List[bool]:
        return [x == DIESIDE.ATTACK for x in dice_results]

    def yield_tokyo(self, other_player_states: Dict[str, PlayerState]) -> bool:
        return self.state.health <= 5
