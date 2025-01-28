# godzilla-v2

godzilla-v2 is a super simplified king of tokyo game (derived heavily from [godzilla](https://github.com/haraschax/godzilla/)). The goal of this game is to create a benchmark for reasoning LLMs, and how they fare against classic game playing techniques.

## Simplifications from King of Tokyo
- There are no energy cubes
- There are no power cards to buy

I plan to add some version of power cards and energy later. But this simple game already offers nice dynamics, especially in a multi-player setting.


## Installation
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Running the game
```bash
# usage: game.py [-h] --players {random,angry} [{random,angry} ...] [--n_games N_GAMES] [--verbose]

# options:
#   -h, --help            show this help message and exit
#   --players {random,angry} [{random,angry} ...], -p {random,angry} [{random,angry} ...]
#                         List of players (agent names) to participate in the game.
#   --n_games N_GAMES, -n N_GAMES
#   --verbose, -v         Print game logs.
  
python game.py --players {random,angry} --n_games 10000


# you can also play as a human against an agent! (the interface needs to be improved)
python game.py --players {angry,human} --n_games 1 --verbose

```

### Available agents
```python
- random
- angry

- human #(play interactively with n_games=1 and verbose)
```

---

## Creating a new agent

- Create a file `agents/new_fancy_agent.py`
- Implement the two methods of the `Player` class: `keep_dice` and `yield_tokyo`
- Add the agent in `agent/__init__.py`