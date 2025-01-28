from .random_agent import RandomAgent
from .angry_agent import AngryAgent


AVAILABLE_AGENTS = {
    'random': RandomAgent,
    'angry': AngryAgent,
}