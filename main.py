import sys
from game_manager import GameManager

DEFAULT_WHITE_PLAYER = 'human'
DEFAULT_BLACK_PLAYER = 'human'
DEFAULT_HISTORY = 'off'
DEFAULT_SCORE_DISPLAY = 'off'

def parse_arguments():
    """
    Parse the given arguments in command line
    """
    args = sys.argv
    white_player = args[1] if len(args) > 1 else DEFAULT_WHITE_PLAYER
    black_player = args[2] if len(args) > 2 else DEFAULT_BLACK_PLAYER
    history = args[3] if len(args) > 3 else DEFAULT_HISTORY
    score_display = args[4] if len(args) > 4 else DEFAULT_SCORE_DISPLAY
    return white_player, black_player, history, score_display


def validate_arguments(white_player, black_player, history, score_display):
    """
    Validates that provided arguments correspond to player classes
    """
    player_types = ['human', 'heuristic', 'random']
    if white_player not in player_types:
        print(f"Invalid white player type: {white_player}")
        sys.exit(1)
    if black_player not in player_types:
        print(f"Invalid black player type: {black_player}")
        sys.exit(1)
    if history not in ['on', 'off']:
        print(f"Invalid history option: {history}")
        sys.exit(1)
    if score_display not in ['on', 'off']:
        print(f"Invalid score display option: {score_display}")
        sys.exit(1)


def main():
    white_player, black_player, history, score_display = parse_arguments()
    validate_arguments(white_player, black_player, history, score_display)

    history_enabled = history == 'on'
    score_display_enabled = score_display == 'on'

    game_manager = GameManager(
        white_player_type=white_player,
        black_player_type=black_player,
        history_enabled=history_enabled,
        score_display_enabled=score_display_enabled
    )

    game_manager.run_game()

if __name__ == '__main__':
    main()

