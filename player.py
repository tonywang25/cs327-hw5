from abc import ABC, abstractmethod
import random

from piece import Piece
from game_manager import GameManager

class Player(ABC):
    def __init__(self, name: str):
        """
        Initialize a new player with a name, pieces, supply, and focus board
        """
        self.name = name

        # Initializelist of active pieces, 1 in each era to start
        self.pieces: List[Piece] = [
            Piece(owner=name, name=f"{name[0].upper()}_past", era="past", position=(0, 0)),
            Piece(owner=name, name=f"{name[0].upper()}_present", era="present", position=(0, 0)),
            Piece(owner=name, name=f"{name[0].upper()}_future", era="future", position=(0, 0)),
        ]

        # Initialize the supply with 4 pieces
        self.supply: List[Piece] = [Piece(owner=name, name=f"{name[0].upper()}_{i}") for i in range(1, 5)]

        # Set the initial focus board
        self.focus_board = 'past' if name == 'white' else 'future'

    @abstractmethod
    def make_move(self, game_manager):
        """
        Abstract method for making a game move.
        """
        pass

    def get_active_pieces(self, board_name: str) -> List[Piece]:
        """
        Returns the player's active pieces on the specified era board.
        """
        return [piece for piece in self.pieces if piece.era == board_name]

    def update_focus(self, new_focus: str):
        """
        Updates the player's focus board.
        """
        if new_focus not in ['past', 'present', 'future']:
            raise ValueError(f"Invalid focus board: {new_focus}")
        self.focus_board = new_focus

    def add_piece(self, piece: Piece):
        """
        Adds a piece to the player's list of pieces.
        """
        self.pieces.append(piece)

    def remove_piece(self, piece: Piece):
        """
        Removes a piece from the player's list of pieces.
        :param piece: The piece to remove.
        """
        if piece in self.pieces:
            self.pieces.remove(piece)
        else:
            raise ValueError(f"Piece {piece} not found in player's pieces.")

    def __str__(self):
        """
        String representation of the player.
        :return: The player's name, focus board, and supply.
        """
        return f"Player {self.name}, Focus: {self.focus_board}, Supply: {len(self.supply)} pieces"


class HumanPlayer(Player):
    def __init__(self, name: str):
        """
        Initialize a HumanPlayer with a given name.
        """
        super().__init__(name)

    def make_move(self, game_manager: GameManager):
        """
        Handles user input to select a piece, move directions, and next focus era.
        Executes the move using the GameManager.
        """
        # Display the boards and game state
        game_manager.display_boards()

        # Get active pieces on the current focus board
        active_pieces = self.get_active_pieces(self.focus_board)
        if not active_pieces or all(not piece.can_move(game_manager) for piece in active_pieces):
            print("No copies to move")
            # Prompt for next focus and return
            new_focus = self.prompt_focus_change()
            self.update_focus(new_focus)
            return

        # Piece selection loop
        while True:
            piece_id = input("Select a copy to move: ").strip()
            piece = self.find_piece_by_id(piece_id, active_pieces)
            if not piece:
                print("Not a valid copy")
                continue
            if piece.owner != self.name:
                print("That is not your copy")
                continue
            if piece.era != self.focus_board:
                print("Cannot select a copy from an inactive era")
                continue
            if not piece.can_move(game_manager):
                print("That copy cannot move")
                continue
            break

        # Move direction prompts
        directions = []
        for i in range(2):
            while True:
                direction = input(f"Select {'first' if i == 0 else 'second'} direction to move ['n', 'e', 's', 'w', 'f', 'b']: ").strip().lower()
                if direction not in ['n', 'e', 's', 'w', 'f', 'b']:
                    print("Not a valid direction")
                    continue
                if not game_manager.is_valid_direction(piece, direction):
                    print(f"Cannot move {direction}")
                    continue
                directions.append(direction)
                # Special case: skip second prompt if only one move is possible
                if len(directions) == 1 and piece.has_only_one_move(game_manager):
                    break
                break

        # Focus change
        new_focus = self.prompt_focus_change()

        # Create and execute the move
        move = Move(piece, directions, new_focus)
        game_manager.apply_move(move)
        print(f"Selected move: {move}")

    def find_piece_by_id(self, piece_id: str, active_pieces: List[Piece]) -> Piece:
        """
        Finds a piece by its ID from the list of active pieces.
        :param piece_id: The ID of the piece to find.
        :param active_pieces: List of active pieces to search in.
        :return: The matching piece or None if not found.
        """
        for piece in active_pieces:
            if piece.name == piece_id:
                return piece
        return None

    def prompt_focus_change(self) -> str:
        """
        Prompts the user for a new focus era and validates the input.
        :return: The new focus era.
        """
        while True:
            new_focus = input("Select the next era to focus on ['past', 'present', 'future']: ").strip().lower()
            if new_focus not in ['past', 'present', 'future']:
                print("Not a valid era")
                continue
            if new_focus == self.focus_board:
                print("Cannot select the current era")
                continue
            return new_focus


class RandomPlayer(Player):
    def __init__(self, name: str):
        """
        Initialize a RandomPlayer with a given name.
        """
        super().__init__(name)

    def make_move(self, game_manager: GameManager):
        """
        Selects a random valid move for the player and applies it.
        """
        # Get all valid moves for the player
        valid_moves = game_manager.get_valid_moves(self)
        
        if not valid_moves:
            # No valid moves, update focus to a random valid era
            print("No copies to move")
            new_focus = random.choice(['past', 'present', 'future'])
            while new_focus == self.focus_board:
                new_focus = random.choice(['past', 'present', 'future'])
            self.update_focus(new_focus)
            return

        # Select and apply a random move
        move = random.choice(valid_moves)
        game_manager.apply_move(move)
        print(f"Selected move: {move}")


class HeuristicPlayer(Player):
    def __init__(self, name: str):
        """
        Initialize a HeuristicAIPlayer with a given name.
        """
        super().__init__(name)

    def make_move(self, game_manager: GameManager):
        """
        Selects the move with the highest heuristic score and applies it.
        """
        # Get all valid moves for the player
        valid_moves = game_manager.get_valid_moves(self)

        if not valid_moves:
            # No valid moves, select focus era heuristically
            print("No copies to move")
            new_focus = self.choose_focus(game_manager)
            self.update_focus(new_focus)
            return

        # Evaluate all valid moves and find the best one(s)
        best_score = float('-inf')
        best_moves = []

        for move in valid_moves:
            score = self.evaluate_move(move, game_manager)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # Select one of the best moves at random
        selected_move = random.choice(best_moves)
        game_manager.apply_move(selected_move)
        print(f"Selected move: {selected_move}")

        # Display heuristic scores if enabled
        if game_manager.score_display_enabled:
            self.display_scores(game_manager)

    def evaluate_move(self, move: Move, game_manager: GameManager) -> int:
        """
        Evaluates a move using a heuristic function.
        Temporarily applies the move, calculates the heuristic score, then undoes the move.
        """
        # Apply the move temporarily
        game_manager.apply_move(move)

        # Calculate heuristic score
        score = self.calculate_heuristic(game_manager)

        # Undo the move
        game_manager.undo_move()
        return score

    def calculate_heuristic(self, game_manager: GameManager) -> int:
        """
        Calculates the heuristic score for the current game state.
        Components:
        - Era presence
        - Piece advantage
        - Supply count
        - Centrality of pieces
        - Focus considerations
        """
        c1, c2, c3, c4, c5 = 3, 2, 1, 1, 1  # Weighting coefficients
        era_presence = self.calculate_era_presence(game_manager)
        piece_advantage = self.calculate_piece_advantage(game_manager)
        supply = len(self.supply)
        centrality = self.calculate_centrality(game_manager)
        focus = self.calculate_focus_score(game_manager)
        return c1 * era_presence + c2 * piece_advantage + c3 * supply + c4 * centrality + c5 * focus

    def calculate_era_presence(self, game_manager: GameManager) -> int:
        """
        Counts the number of eras where the player has at least one piece.
        """
        return sum(1 for board in game_manager.boards.values() if self.get_active_pieces(board.name))

    def calculate_piece_advantage(self, game_manager: GameManager) -> int:
        """
        Calculates piece advantage: (player pieces - opponent pieces).
        """
        opponent = game_manager.get_opponent(self)
        player_pieces = sum(len(self.get_active_pieces(board.name)) for board in game_manager.boards.values())
        opponent_pieces = sum(len(opponent.get_active_pieces(board.name)) for board in game_manager.boards.values())
        return player_pieces - opponent_pieces

    def calculate_centrality(self, game_manager: GameManager) -> int:
        """
        Counts the number of player pieces in the central positions of the board.
        """
        central_positions = {(1, 1), (1, 2), (2, 1), (2, 2)}
        count = 0
        for board in game_manager.boards.values():
            for piece in self.get_active_pieces(board.name):
                if piece.position in central_positions:
                    count += 1
        return count

    def calculate_focus_score(self, game_manager: GameManager) -> int:
        """
        Calculates focus score based on pieces in the focus era.
        """
        focus_board = game_manager.boards[self.focus_board]
        return len(self.get_active_pieces(focus_board.name))

    def choose_focus(self, game_manager: GameManager) -> str:
        """
        Selects a new focus era based on heuristic evaluation.
        Prefers the era with the most player pieces.
        """
        focus_scores = {era: len(self.get_active_pieces(era)) for era in ['past', 'present', 'future']}
        return max(focus_scores, key=focus_scores.get)

    def display_scores(self, game_manager: GameManager):
        """
        Displays the heuristic components for debugging and score tracking.
        """
        print(f"Heuristic Components for {self.name}:")
        print(f"Era Presence: {self.calculate_era_presence(game_manager)}")
        print(f"Piece Advantage: {self.calculate_piece_advantage(game_manager)}")
        print(f"Supply Count: {len(self.supply)}")
        print(f"Centrality: {self.calculate_centrality(game_manager)}")
        print(f"Focus Score: {self.calculate_focus_score(game_manager)}")


