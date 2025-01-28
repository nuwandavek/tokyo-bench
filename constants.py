from enum import Enum

MAX_HEALTH = 10
VICTORY_PTS_WIN = 20
DIE_COUNT = 6
ENTER_TOKYO_PTS= 1
START_TOKYO_PTS = 2

class DIESIDE(str, Enum):
    ATTACK = 'Attack'
    HEAL = 'Heal'
    ONE = '1'
    TWO = '2'
    THREE = '3'
