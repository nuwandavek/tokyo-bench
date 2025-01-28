from abc import ABC, abstractmethod
from typing import List, Dict
from pydantic import BaseModel, Field
from constants import MAX_HEALTH, VICTORY_PTS_WIN, DIESIDE


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
    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, PlayerState], reroll_n: int) -> List[bool]:
        """
        Returns a mask of which dice to keep and which to reroll.
        Length of the mask should be equal to the length of dice_results.
        """
        pass

    @abstractmethod
    def yield_tokyo(self, other_player_states: Dict[str, PlayerState]) -> bool:
        """
        Returns whether the player should yield Tokyo.
        """
        pass

    def __str__(self):
        return f'p{self.idx}_{self.name}'
