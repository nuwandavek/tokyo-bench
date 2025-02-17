import random
from typing import List, Dict, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

from helpers.constants import DIESIDE, DIE_COUNT, MAX_HEALTH, VICTORY_PTS_WIN
from player import PlayerState, Player
from pathlib import Path


class PPOAgent(Player):
    def __init__(self, idx: int, name: str, hidden_dim=128, model_path=None, load_model=False):
        super().__init__(idx=idx, name=name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # player state = 3, opponent state = 3, roll counter = 1
        self.input_size = (DIE_COUNT * len(DIESIDE)) + 3 + 3 + 1
        self.net = PPONetwork(self.input_size, hidden_dim, DIE_COUNT).to(self.device)

        if load_model:
            assert model_path is not None, "Model path must be provided to load the model."
            self.load_model(model_path)

    def keep_dice(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int) -> Tuple[List[bool], str]:
        input_tensor = self.preprocess_state(dice_results, other_player_states, roll_counter)
        with torch.no_grad():
            self.net.eval()
            _, _, _, action, _ = self.net.predict(input_tensor)
            action = action.squeeze().cpu().numpy().astype(bool).tolist()
        return action, "PPO Decision"

    def yield_tokyo(self, other_player_states: Dict[str, Tuple[int, PlayerState]]) -> Tuple[bool, str]:
        return self.state.health <= 5, "PPO: Deciding whether to yield Tokyo; same as angry for now."

    def preprocess_state(self, dice_results: List[DIESIDE], other_player_states: Dict[str, Tuple[int, PlayerState]], roll_counter: int):
        # 1. Dice Results (One-Hot Encoded)
        dieside_map = {dieside: i for i, dieside in enumerate(DIESIDE)}
        one_hot = torch.zeros(DIE_COUNT, len(DIESIDE))
        for i, die in enumerate(dice_results):
            one_hot[i][dieside_map[die]] = 1
        dice_tensor = one_hot.flatten()

        # 2. Player State
        player_state = torch.tensor([
            self.state.health / MAX_HEALTH,
            self.state.victory_points / VICTORY_PTS_WIN,
            float(self.state.in_tokyo)
        ])

        # 3. Opponent State (assuming only one opponent for now)
        opponent = list(other_player_states.values())[0][1]  # Get the PlayerState of the opponent
        opponent_state = torch.tensor([
            opponent.health / MAX_HEALTH,
            opponent.victory_points / VICTORY_PTS_WIN,
            float(opponent.in_tokyo)
        ])

        # 4. Roll Counter (normalize)
        # roll_counter_tensor = torch.tensor([roll_counter / 2.0])  # Assuming max 3 rolls
        roll_counter_tensor = torch.tensor([roll_counter])

        # Concatenate all features
        combined_state = torch.cat([
            dice_tensor,
            player_state,
            opponent_state,
            roll_counter_tensor
        ])

        return combined_state.unsqueeze(0).to(self.device)  # Add batch dimension

    def load_model(self, model_path: str):
        self.net.load_state_dict(torch.load(model_path, map_location=self.device))
        self.net.eval()

class PPONetwork(nn.Module):
    def __init__(self, obs_dim, hidden_dim, dice_count):
        super(PPONetwork, self).__init__()
        self.base = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.policy_keep_dice = nn.Linear(hidden_dim, dice_count)
        # self.policy_yield_tokyo = nn.Linear(hidden_dim, 2)
        self.value_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x, decision_type='keep_dice'):
        base_out = self.base(x)
        value = self.value_head(base_out)
        if decision_type == 'keep_dice':
            logits = self.policy_keep_dice(base_out)
        # elif decision_type == 'yield_tokyo':
        #     logits = self.policy_yield_tokyo(base_out)
        else:
            raise ValueError("Invalid decision type")
        return logits, value
    
    def predict(self, x, decision_type='keep_dice'):
        logits, value = self.forward(x, decision_type)
        probs = torch.sigmoid(logits)
        dist = torch.distributions.Bernoulli(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum()
        return logits, value, probs, action, log_prob
