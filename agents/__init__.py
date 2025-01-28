from .random_agent import RandomAgent
from .angry_agent import AngryAgent
from .human_agent import HumanAgent
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent

AVAILABLE_AGENTS = {
    'random': RandomAgent,
    'angry': AngryAgent,
    'human': HumanAgent,
    'openai': OpenAIAgent,
    'anthropic': AnthropicAgent
}