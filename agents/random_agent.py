import random
from typing import List, Dict, Tuple

from helpers.constants import DIESIDE
from player import PlayerState, Player


class RandomAgent(Player):
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        return [random.choice([True, False]) for _ in range(len(dice_results))], "random is my middle name"

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return random.choice([True, False]), "random is my middle name"
