from collections import Counter
import time
from pathlib import Path

COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    'WHITE': '\033[97m'
}

CATEGORY_COLORS = {
    'event': 'WHITE',
    'success': 'GREEN',
    'error': 'RED',
    'warning': 'YELLOW',
    'info': 'CYAN'
}

class GameLogger:
    def __init__(self, player_names, total_games, verbose=False, report=False):
        self.player_names = player_names
        self.total_games = total_games
        self.verbose = verbose
        self.report = report
        self.game_logs = []
        self.current_game_log = None
        self.winners = []
        self.turn_counts = []

    def log(self, message, category='event', force_print=False):
        if self.verbose or force_print:
            print(COLORS[CATEGORY_COLORS[category]] + message + COLORS['RESET'])
        if self.report:
            if len(self.current_game_log['turns']) == 0:
                self.current_game_log['turns'] = [{'turn_num': 0, 'events': []}]
            current_turn_events = self.current_game_log['turns'][-1]['events']
            current_turn_events.append({'message': message, 'category': category})
    
    def start_game(self, game_id):
        if self.report:
            self.current_game_log = {'game_id': game_id, 'players': self.player_names, 'turns': [], 'winner': None}
        if self.verbose:
            self.log(f"\nStarting Game {game_id} with players: {', '.join(self.player_names)}", category='event')
    
    def end_game(self, winner_name, turn_counts):
        if self.report:
            self.current_game_log['winner'] = winner_name
            self.current_game_log['turn_counts'] = turn_counts
            self.game_logs.append(self.current_game_log)
        if self.verbose:
            self.log(f"Game ended. Winner: {winner_name} in {turn_counts} turns.", category='info')
        self.winners.append(winner_name)
        self.turn_counts.append(turn_counts)

    def generate_report(self):
        summary_stats = {}
        summary_stats['winners_count'] = [f'{player}: {count} ({count/self.total_games:.2%})' for player, count in Counter(self.winners).items()]
        summary_stats['avg_turns_per_player_per_game'] = f"{sum(self.turn_counts)/self.total_games/len(self.player_names):.2f}"

        self.log("\n\n\nGame Stats", category='info', force_print=True)
        self.log("------------", category='info', force_print=True)
        self.log(f"Winners ({self.total_games} games):", category='info', force_print=True)
        for w in summary_stats['winners_count']:
            self.log(w, category='success', force_print=True)
        self.log("------------", category='info', force_print=True)
        self.log("Misc Stats:", category='info', force_print=True)
        self.log(f"Total turns per player per game: {summary_stats['avg_turns_per_player_per_game']}", category='warning', force_print=True)

        if self.report:

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>godzilla-v2 game report</title>
                <style>
                    body {{ font-family: sans-serif; }}
                    .summary {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .game-tab {{ border: 1px solid #ddd; margin-bottom: 10px; }}
                    .tab-header {{ background-color: #f0f0f0; padding: 10px; cursor: pointer; }}
                    .tab-content {{ padding: 10px; display: none; }}
                    .tab-content.active {{ display: block; }}
                    h2 {{ color: #333; }}
                    h3 {{ color: #555; }}
                    p {{ margin-bottom: 5px; }}
                    .log-event strong {{ font-weight: bold; }}
                    .dice-roll {{ color: blue; }}
                    .resolve-dice {{ color: orange; }}
                    .player-state {{ color: green; }}
                    .enter-tokyo {{ color: magenta; }}
                    .start-tokyo-turn {{ color: cyan; }}
                    .game-summary-table {{ width: 100%; border-collapse: collapse; }}
                    .game-summary-table th, .game-summary-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .game-summary-table th {{ background-color: #f0f0f0; }}
                    .highlight {{ font-weight: bold; color: green; }}
                    .log-level-event {{ color: black; }}
                    .log-level-success {{ color: green; }}
                    .log-level-error {{ color: red; margin-top: 25px; }}
                    .log-level-warning {{ color: orange; }}
                    .log-level-info {{ color: blue; }}
                    
                </style>
            </head>
            <body>
                <h1>godzilla-v2 game report</h1>

                <div class="summary">
                    <h2>Game Summary</h2>
                    <p><strong>Number of Games:</strong> {self.total_games}</p>
                    <p><strong>Players:</strong> {', '.join(self.player_names)}</p>

                    <h3>Winner Statistics</h3>
                    <table class="game-summary-table">
                        <thead>
                            <tr>
                                <th>Player</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for w in summary_stats['winners_count']:
                html_content += f"""
                            <tr>
                                <td>{w}</td>
                            </tr>
                """
            html_content += f"""
                        </tbody>
                    </table>
                    <p><strong>Average Turns per Player per Game:</strong> {summary_stats['avg_turns_per_player_per_game']}</p>
                </div>

                <h2>Game Details</h2>
            """

            for game_log in self.game_logs:
                game_id = game_log['game_id']
                winner = game_log['winner']
                turn_counts = game_log['turn_counts']
                players_str = ', '.join(game_log['players'])

                html_content += f"""
                <div class="game-tab">
                    <div class="tab-header" onclick="toggleTab('game-{game_id}')">
                        <h3>Game {game_id + 1}: Winner - {winner}, Turns - {turn_counts}, Players - {players_str}</h3>
                    </div>
                    <div id="game-{game_id}" class="tab-content">
                        <p><strong>Players:</strong> {players_str}</p>
                        <p><strong>Winner:</strong> <span class="highlight">{winner}</span></p>
                        <p><strong>Turns:</strong> {turn_counts}</p>
                """
                for turn_data in game_log['turns']:
                    turn_num = turn_data['turn_num']
                    if turn_num > 0: # Skip turn 0 logs
                        html_content += f"<h4>Turn {turn_num}</h4>"
                    for event in turn_data['events']:
                        level = event['category']
                        message = event['message']

                        log_message_html = f"<div class='log-event log-level-{level}'>{message}"
                        log_message_html += "</div>"
                        html_content += log_message_html

                html_content += """
                    </div>
                </div>
                """

            html_content += """
            <script>
                function toggleTab(tabId) {
                    var content = document.getElementById(tabId);
                    if (content.style.display === "block") {
                        content.style.display = "none";
                    } else {
                        content.style.display = "block";
                    }
                }
            </script>
            </body>
            </html>
            """

            report_name = "./reports/" + "_".join(self.player_names) + time.strftime("_%Y%m%d_%H%M%S") + ".html"
            Path("reports").mkdir(parents=True, exist_ok=True)
            with open(report_name, 'w') as f:
                f.write(html_content)
            print(f"Report written to {report_name}")