from typing import List, Dict, Tuple

from constants import DIESIDE
from player import PlayerState, Player


class AngryAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        return [x == DIESIDE.ATTACK for x in dice_results], "ANGRYYY!"

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return self.state.health <= 5, "ANGRYYY!"
