from .random_agent import RandomAgent
from .angry_agent import AngryAgent
from .human_agent import HumanAgent
from .openai_gpt4o_agent import GPT4OAgent
from .anthropic_cs3pt5_agent import CS3PT5Agent
from .openai_o1mini_agent import O1MiniAgent
from .openai_o3mini_agent import O3MiniAgent
from .cerebras_r1llama70b import CerebrasR1Llama70BAgent

AVAILABLE_AGENTS = {
    'random': RandomAgent,
    'angry': AngryAgent,
    'human': HumanAgent,
    'openai_gpt4o': GPT4OAgent,
    'anthropic_cs3pt5': CS3PT5Agent,
    'openai_o1mini': O1MiniAgent,
    'openai_o3mini': O3MiniAgent,
    'cerebras_r1llama70b': CerebrasR1Llama70BAgent,
}
