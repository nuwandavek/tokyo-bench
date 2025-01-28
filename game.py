import argparse
import random
import copy
from collections import Counter
from typing import List
from constants import DIESIDE, MAX_HEALTH, VICTORY_PTS_WIN, DIE_COUNT, ENTER_TOKYO_PTS, START_TOKYO_PTS
from agents import AVAILABLE_AGENTS
from player import Player
from tqdm import trange

from dotenv import load_dotenv
load_dotenv()

class Game:
    def __init__(self, players=List[Player], start_idx=0, verbose=False):
        self.players = players
        self.winner_idx = -1
        self.active_players = [True] * len(self.players)
        self.current_player_idx = start_idx
        self.verbose = verbose
        self.turns = 0

    @property
    def n_players(self):
        return len(self.players)

    @property
    def current_player(self):
        return self.players[self.current_player_idx]

    @property
    def other_players(self):
        return [player for i, player in enumerate(self.players) if i != self.current_player_idx]
    
    
    def update_player_state(self, player, delta_vp=0, delta_health=0, in_tokyo=None):
        player.increment_victory_points(delta_vp)
        player.increment_health(delta_health)
        if in_tokyo is not None:
            player.set_tokyo(in_tokyo)
        
        if self.is_player_winner(player):
            self.winner_idx = player.idx
        
        if self.is_player_dead(player):
            self.active_players[player.idx] = False

        

    def is_player_dead(self, player):
        return player.state.health == 0
    
    def is_player_winner(self, player):
        return player.state.victory_points == VICTORY_PTS_WIN


    def start_turn(self):
        if self.current_player.state.in_tokyo:
            self.update_player_state(self.current_player, delta_vp=START_TOKYO_PTS)
            if self.verbose:
                print(f'{self.current_player} starts turn in Tokyo ({self.current_player.state})')

    def roll_n_dice(self, n):
        return [random.choice([DIESIDE.ATTACK, DIESIDE.HEAL, DIESIDE.ONE, DIESIDE.TWO, DIESIDE.THREE]) for _ in range(n)]

    def roll_dice(self):
        dice_results = self.roll_n_dice(DIE_COUNT)
        if self.verbose:
            print('\nStep 1: Rolling dice...')
            print(f'roll 1: {[x.value for x in dice_results]}')
        
        for i in range(2):
            keep_mask = self.current_player.keep_dice(copy.deepcopy(dice_results), {player.name: (player.idx, player.state) for player in self.other_players}, roll_counter=i)
            dice_results = [dice_results[i] for i in range(DIE_COUNT) if keep_mask[i]] + self.roll_n_dice(DIE_COUNT - sum(keep_mask))
            if self.verbose:
                print(f'keep {i+1}: {keep_mask}')
                print(f'roll {i+2}: {[x.value for x in dice_results]}')

        return dice_results

    def resolve_victory_point_dice(self, dice):
        for dieside in [DIESIDE.ONE, DIESIDE.TWO, DIESIDE.THREE]:
          cnt = sum([x == dieside for x in dice])
          if cnt >= 3:
            self.update_player_state(self.current_player, delta_vp=int(dieside))
            self.update_player_state(self.current_player, delta_vp=cnt-3)
    
    def resolve_health_dice(self, dice):
        heals = sum([x == DIESIDE.HEAL for x in dice])
        if not self.current_player.state.in_tokyo:
          self.update_player_state(self.current_player, delta_health=heals)

    def resolve_attack_dice(self, dice):
        attack = sum([x == DIESIDE.ATTACK for x in dice])
        if attack == 0:
            return

        if self.current_player.state.in_tokyo:
            for player in self.other_players:
                self.update_player_state(player, delta_health=-attack)
        else:
            tokyo_player = next((p for p in self.other_players if p.state.in_tokyo), None)
            if tokyo_player is not None:
                self.update_player_state(tokyo_player, delta_health=-attack)
                if tokyo_player.yield_tokyo({player.name: (player.idx, player.state) for player in self.players if (player.idx != tokyo_player.idx)}):
                    self.update_player_state(tokyo_player, in_tokyo=False)

    def enter_tokyo(self):
        if any([player.state.in_tokyo for player in self.players]):
            return
        self.update_player_state(self.current_player, delta_vp=ENTER_TOKYO_PTS)
        self.update_player_state(self.current_player, in_tokyo=True)
        if self.verbose:
            print(f'\n{self.current_player} enters Tokyo ({self.current_player.state})')

    def resolve_dice(self, dice):
        self.resolve_victory_point_dice(dice)
        self.resolve_health_dice(dice)
        self.resolve_attack_dice(dice)
        if self.verbose:
            print(f'\nStep 2: Resolving dice: {[x.value for x in dice]}')
            for player in self.players:
                print(f'{player}: {player.state}')

    def check_winner(self):
        if self.winner_idx != -1:
            pass
        elif sum(self.active_players) == 1:
            self.winner_idx = self.active_players.index(True)

        if self.verbose:
            print(f'Active Players: {self.active_players}')
            if self.winner_idx != -1:
                print(f'Winner: {self.players[self.winner_idx]}')
            else:
                print('No winner yet.')

    def step(self):
        if self.active_players[self.current_player_idx]:
            if self.verbose:
                print(f'\n\n\nturn {self.turns}: {self.current_player}\'s turn ({self.current_player.state})')
            self.start_turn()
            dice = self.roll_dice()
            self.resolve_dice(dice)
            self.enter_tokyo()
            self.check_winner()
            self.turns += 1
        self.current_player_idx = (self.current_player_idx + 1) % self.n_players



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--players', '-p', nargs='+', choices=AVAILABLE_AGENTS.keys(), required=True, help='List of players (agent names) to participate in the game.')
    parser.add_argument('--n_games', '-n', type=int, default=100)
    parser.add_argument('--verbose', '-v', action='store_true', help='Print game logs.', default=False)
    args = parser.parse_args()

    assert len(args.players) >= 2, 'At least 2 players are required to play the game.'

    winners = [None] * args.n_games
    turns = [0] * args.n_games
    for i in trange(args.n_games):
        players = [AVAILABLE_AGENTS[player](idx=p, name=player) for p, player in enumerate(args.players)]
        game = Game(players=players, start_idx=i%len(args.players), verbose=args.verbose)
        while game.winner_idx == -1:
            game.step()
        turns[i] = game.turns
        winners[i] = str(game.players[game.winner_idx])
    print('Game Stats:')
    print(f'------------\nWinners ({args.n_games} games):')
    for player, count in Counter(winners).items():
        print(f'{player}: {count} ({count/args.n_games:.2%})')
    print('------------\nMisc Stats:')
    print(f'Total turns per player per game: {sum(turns)/args.n_games/len(args.players)}')