from board import Board
from player import Player, HumanPlayer, RandomPlayer, HeuristicPlayer
from move import Move
from move_history import MoveHistory
from game_state import GameState

import copy

class GameManager:
    def __init__(self, white_player_type: str, black_player_type: str,
                 history_enabled: bool = False, score_display_enabled: bool = False):
        # Initialize boards
        self.boards: Dict[str, Board] = {
            'past': Board('past'),
            'present': Board('present'),
            'future': Board('future')
        }
        # Initialize players
        self.players: List[Player] = [
            self.create_player('white', white_player_type),
            self.create_player('black', black_player_type)
        ]
        self.current_player_index: int = 0  # 0 for white, 1 for black
        self.turn_number: int = 1
        self.history_enabled: bool = history_enabled
        self.score_display_enabled: bool = score_display_enabled
        self.move_history: Optional[MoveHistory] = MoveHistory() if history_enabled else None

        # Place initial pieces on the boards
        self.setup_initial_pieces()
        # Set initial focus tokens
        self.players[0].focus_board = 'past'    # White focuses on 'past'
        self.players[1].focus_board = 'future'  # Black focuses on 'future'

    def create_player(self, name: str, player_type: str) -> Player:
        if player_type == 'human':
            return HumanPlayer(name)
        elif player_type == 'random':
            return RandomPlayer(name)
        elif player_type == 'heuristic':
            return HeuristicPlayer(name)
        else:
            raise ValueError(f"Unknown player type: {player_type}")

    def setup_initial_pieces(self):
        # Assuming identifiers 'A', 'B', 'C' for white, '1', '2', '3' for black
        # Place white pieces on bottom-right corner of each board
        white_identifiers = ['A', 'B', 'C']
        for idx, board_name in enumerate(['past', 'present', 'future']):
            piece = self.players[0].supply.pop(0)  # Remove from supply
            piece.identifier = white_identifiers[idx]
            piece.board = self.boards[board_name]
            piece.x = 3  # Bottom-right corner (x-coordinate)
            piece.y = 3  # Bottom-right corner (y-coordinate)
            self.boards[board_name].place_piece(piece, 3, 3)
            self.players[0].pieces.append(piece)

        # Place black pieces on top-left corner of each board
        black_identifiers = ['1', '2', '3']
        for idx, board_name in enumerate(['past', 'present', 'future']):
            piece = self.players[1].supply.pop(0)
            piece.identifier = black_identifiers[idx]
            piece.board = self.boards[board_name]
            piece.x = 0  # Top-left corner
            piece.y = 0  # Top-left corner
            self.boards[board_name].place_piece(piece, 0, 0)
            self.players[1].pieces.append(piece)

    def run_game(self):
        while True:
            current_player = self.players[self.current_player_index]
            opponent = self.players[1 - self.current_player_index]

            # Check for game end condition
            if self.check_game_end(opponent):
                print(f"{current_player.name} has won")
                replay = input("Would you like to play again? ")
                if replay.lower() == 'yes':
                    self.reset_game()
                    continue
                else:
                    break

            # Display the boards
            self.display_boards()

            # History management (undo/redo/next)
            if self.history_enabled and isinstance(current_player, HumanPlayer):
                while True:
                    command = input("Enter 'undo', 'redo', or 'next': ")
                    if command == 'undo':
                        if self.move_history.can_undo():
                            self.undo_move()
                            self.display_boards()
                        else:
                            print("Cannot undo")
                    elif command == 'redo':
                        if self.move_history.can_redo():
                            self.redo_move()
                            self.display_boards()
                        else:
                            print("Cannot redo")
                    elif command == 'next':
                        break
                    else:
                        print("Invalid command")
            else:
                # For AI players or if history is disabled
                pass

            # Save the current state for undo functionality
            if self.history_enabled:
                game_state = self.create_game_state()
                self.move_history.save_state(game_state)

            # Get the current player's move
            current_player.make_move(self)

            # Increment turn and switch player
            self.turn_number += 1
            self.current_player_index = 1 - self.current_player_index

    def reset_game(self):
        # Reinitialize the game manager
        self.__init__(
            self.players[0].player_type,
            self.players[1].player_type,
            self.history_enabled,
            self.score_display_enabled
        )

    def check_game_end(self, opponent: Player) -> bool:
        # If opponent has pieces in only one era board, current player wins
        eras_with_pieces = set()
        for piece in opponent.pieces:
            eras_with_pieces.add(piece.board.name)
        return len(eras_with_pieces) <= 1

    def display_boards(self):
        print("---------------------------------")
        # Display focus tokens and board state
        for board_name in ['past', 'present', 'future']:
            board = self.boards[board_name]
            focus = ''
            if self.players[0].focus_board == board_name:
                focus += 'white '
            if self.players[1].focus_board == board_name:
                focus += 'black'
            print(f"Board: {board_name.capitalize()} {focus}")
            board.display()
        print(f"Turn: {self.turn_number}, Current player: {self.players[self.current_player_index].name}")

    def create_game_state(self) -> GameState:
        # Deep copy of the game state
        state = GameState(
            boards=copy.deepcopy(self.boards),
            players=copy.deepcopy(self.players),
            current_player_index=self.current_player_index,
            turn_number=self.turn_number
        )
        return state

    def restore_game_state(self, state: GameState):
        self.boards = state.boards
        self.players = state.players
        self.current_player_index = state.current_player_index
        self.turn_number = state.turn_number

    def apply_move(self, move: Move):
        # Execute the move
        move.execute(self)
        # If history is enabled, save the move
        if self.history_enabled:
            self.move_history.add_move(move)

    def undo_move(self):
        if self.history_enabled and self.move_history.can_undo():
            state = self.move_history.undo(self)
            self.restore_game_state(state)
            # Adjust turn and player index
            self.turn_number -= 1
            self.current_player_index = 1 - self.current_player_index
        else:
            print("Cannot undo")

    def redo_move(self):
        if self.history_enabled and self.move_history.can_redo():
            state = self.move_history.redo(self)
            self.restore_game_state(state)
            # Adjust turn and player index
            self.turn_number += 1
            self.current_player_index = 1 - self.current_player_index
        else:
            print("Cannot redo")

    def get_valid_moves(self, player: Player) -> List[Move]:
        # Generate all valid moves for the player
        valid_moves = []
        focus_board = self.boards[player.focus_board]
        active_pieces = [piece for piece in player.pieces if piece.board == focus_board]
        for piece in active_pieces:
            possible_moves = piece.get_possible_moves(self)
            valid_moves.extend(possible_moves)
        return valid_moves

