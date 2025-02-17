import argparse
import json
import random
from collections import deque
from pathlib import Path
import copy
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from pydantic import BaseModel, Field
from tqdm import tqdm

from game import Game, MAX_ROLLS, DIE_COUNT
from agents.ppo_agent import PPOAgent
from agents.angry_agent import AngryAgent
from agents.random_agent import RandomAgent

class PPOTrainerConfig(BaseModel):
    # Experiment settings
    experiment_name: str = Field(..., description="Name of the training run")
    n_episodes: int = Field(default=10000, description="Number of episodes to train")
    max_steps_per_episode: int = Field(default=100, description="Maximum steps per episode")
    eval_frequency: int = Field(default=10, description="Frequency of evaluation.")
    save_frequency: int = Field(default=100, description="Frequency (in episodes) to save the model")
    device: str = Field(default="cuda" if torch.cuda.is_available() else "cpu", description="Device to train on")
    # Model settings
    hidden_dim: int = Field(default=128, description="Hidden dimension size for the PPO network")
    experiment_dir: Path = Field(default=Path("training/experiments"), description="Directory for saving models")
    load_model: bool = Field(default=False, description="Whether to load a pre-trained model")
    # PPO hyperparameters
    learning_rate: float = Field(default=3e-4, description="Learning rate")
    clip_epsilon: float = Field(default=0.2, description="PPO clipping parameter")
    value_coef: float = Field(default=0.5, description="Value loss coefficient")
    entropy_coef: float = Field(default=0.01, description="Entropy bonus coefficient")
    gamma: float = Field(default=0.99, description="Discount factor")
    gae_lambda: float = Field(default=0.95, description="GAE lambda parameter")
    batch_size: int = Field(default=32, description="Training batch size")
    ppo_epochs: int = Field(default=10, description="Number of PPO epochs per update")
    max_grad_norm: float = Field(default=0.5, description="Maximum gradient norm for clipping")


class Experience(BaseModel):
    state: torch.Tensor
    action: torch.Tensor
    reward: float
    value: torch.Tensor
    log_prob: torch.Tensor
    done: bool = False

    class Config:
        arbitrary_types_allowed = True

class PPOMemory(BaseModel):
    states: list = Field(default_factory=list)
    actions: list = Field(default_factory=list)
    rewards: list = Field(default_factory=list)
    values: list = Field(default_factory=list)
    log_probs: list = Field(default_factory=list)
    dones: list = Field(default_factory=list)
    batch_size: int = Field(default=32)

    class Config:
        arbitrary_types_allowed = True

    def add(self, exp: Experience):
        self.states.append(exp.state)
        self.actions.append(exp.action)
        self.rewards.append(exp.reward)
        self.values.append(exp.value)
        self.log_probs.append(exp.log_prob)
        self.dones.append(exp.done)

    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
        self.dones.clear()

    def get_batch(self):
        states = torch.stack(self.states)
        actions = torch.stack(self.actions)
        rewards = torch.tensor(self.rewards, dtype=torch.float32)
        values = torch.stack(self.values)
        log_probs = torch.stack(self.log_probs)
        dones = torch.tensor(self.dones, dtype=torch.float32)
        return states, actions, rewards, values, log_probs, dones

    @property
    def is_ready(self) -> bool:
        return len(self.states) >= self.batch_size


class PPOTrainer:
    def __init__(self, config: PPOTrainerConfig):
        self.config = config
        self.experiment_dir = self.config.experiment_dir / config.experiment_name
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        idxs = [0, 1]
        random.shuffle(idxs)
        self.ppo_agent = PPOAgent(
            idx=idxs[0],
            name=config.experiment_name,
            hidden_dim=config.hidden_dim,
            model_path=str(self.experiment_dir / "policy.pth"),
            load_model=config.load_model
        )
        self.opponent_agent = AngryAgent(idx=idxs[1], name="angry")

        self.optimizer = optim.Adam(self.ppo_agent.net.parameters(), lr=config.learning_rate)
        self.memory = PPOMemory(batch_size=config.batch_size)
        self.episode_rewards = deque(maxlen=100)

    def compute_gae(self, rewards, values, dones, next_value):
        advantages = torch.zeros_like(rewards)
        gae = 0
        for t in reversed(range(len(rewards))):
            next_non_terminal = 1.0 - (dones[t + 1] if t + 1 < len(dones) else 0.0)
            next_val = values[t + 1] if t + 1 < len(values) else next_value
            delta = rewards[t] + self.config.gamma * next_val * next_non_terminal - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * next_non_terminal * gae
            advantages[t] = gae
        returns = advantages + values
        return advantages, returns

    def update_policy(self):
        states, actions, rewards, values, old_log_probs, dones = self.memory.get_batch()
        states = states.to(self.config.device)
        actions = actions.to(self.config.device)
        rewards = rewards.to(self.config.device)
        values = values.to(self.config.device).squeeze(-1)
        old_log_probs = old_log_probs.to(self.config.device)
        dones = dones.to(self.config.device)

        with torch.no_grad():
            # Get next value (for the final state)
            _, next_value = self.ppo_agent.net(states[-1].unsqueeze(0), decision_type='keep_dice')
            next_value = next_value.squeeze(0)
            advantages, returns = self.compute_gae(rewards, values, dones, next_value)
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        for _ in range(self.config.ppo_epochs):
            logits, current_values = self.ppo_agent.net(states, decision_type='keep_dice')
            current_values = current_values.squeeze(-1)
            probs = torch.sigmoid(logits)
            dist = torch.distributions.Bernoulli(probs)
            current_log_probs = dist.log_prob(actions).sum(dim=1)
            entropy = dist.entropy().sum(dim=1).mean()

            ratios = torch.exp(current_log_probs - old_log_probs)
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages

            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(current_values, returns)
            entropy_loss = -entropy

            total_loss = policy_loss + self.config.value_coef * value_loss + self.config.entropy_coef * entropy_loss

            self.optimizer.zero_grad()
            total_loss.backward()
            nn.utils.clip_grad_norm_(self.ppo_agent.net.parameters(), self.config.max_grad_norm)
            self.optimizer.step()

            # (Simple logging to the console)
            print(f"Losses -> Policy: {policy_loss.item():.4f}, Value: {value_loss.item():.4f}, Entropy: {entropy.item():.4f}, Total: {total_loss.item():.4f}")

        self.memory.clear()

    def train(self):
        progress_bar = tqdm(range(self.config.n_episodes))
        for episode in progress_bar:
            self.ppo_agent.reset()
            self.opponent_agent.reset()
            self.memory.clear()

            game = Game(players=[self.ppo_agent, self.opponent_agent], start_idx=random.choice([0, 1]))
            episode_reward = 0

            while game.winner_idx == -1 and game.turns < self.config.max_steps_per_episode:
                if game.current_player == self.ppo_agent and game.active_players[self.ppo_agent.idx]:
                    self.ppo_agent.net.eval()
                    with torch.no_grad():
                        # have to roll out the game to get all intermediate states
                        other_states = {p.name: (p.idx, p.state) for p in game.other_players}
                        game.start_turn()
                        dice_results, keep_mask = [], []
                        for i in range(MAX_ROLLS):
                            dice_results = [die for d, die in enumerate(dice_results) if keep_mask[d]] + self.roll_n_dice(DIE_COUNT - sum(keep_mask))
                            if i < MAX_ROLLS - 1:
                                input_tensor = self.ppo_agent.preprocess_state(copy.deepcopy(dice_results), other_states, i)
                                logits, value, probs, action, log_prob = self.ppo_agent.net.predict(input_tensor)
                                keep_mask = action.squeeze().cpu().numpy().astype(bool).tolist()
                            
                            if i == 0:
                                reward = 0
                                exp = Experience(
                                    state=input_tensor.squeeze(0),
                                    action=action.squeeze(0),
                                    reward=reward,
                                    value=value.squeeze(0),
                                    log_prob=log_prob,
                                    done=(game.winner_idx != -1)
                                )
                                self.memory.add(exp)
                        game.resolve_dice(dice_results)
                        reward = 0 if game.winner_idx == -1 else 1 if game.winner_idx == self.ppo_agent.idx else -1
                        exp = Experience(
                            state=input_tensor.squeeze(0),
                            action=action.squeeze(0),
                            reward=reward,
                            value=value.squeeze(0),
                            log_prob=log_prob,
                            done=(game.winner_idx != -1)
                        )
                        self.memory.add(exp)
                    game.enter_tokyo()
                    game.check_winner()
                    game.turns += 1
                    game.next_player()
                    
                    episode_reward += reward

                    if self.memory.is_ready:
                        self.update_policy()

                else:
                    game.step()

            self.episode_rewards.append(episode_reward)
            avg_reward = sum(self.episode_rewards) / len(self.episode_rewards)
            progress_bar.set_description(f"Episode {episode}, Avg Reward: {avg_reward:.2f}")

            if episode % self.config.save_frequency == 0:
                model_save_path = self.experiment_dir / f"policy_{episode}.pth"
                torch.save(self.ppo_agent.net.state_dict(), model_save_path)
                mem_log_path = self.experiment_dir / f"memory_{episode}.json"
                with open(mem_log_path, "w") as f:
                    # Save a JSON summary of the memory length and recent rewards
                    json.dump({"episode": episode}, f, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="ppo_vs_angry", help="Name of the experiment")
    parser.add_argument("--n_episodes", type=int, default=10000, help="Number of training episodes")
    args = parser.parse_args()

    config = PPOTrainerConfig(
        experiment_name=args.experiment_name,
        n_episodes=args.n_episodes,
    )

    trainer = PPOTrainer(config)
    trainer.train()

if __name__ == "__main__":
    main()
