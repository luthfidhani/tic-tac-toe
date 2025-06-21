import uuid
import json
from typing import Dict, List, Optional, Tuple
from database import db

class GameLogic:
    def __init__(self):
        self.winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
    
    def generate_room_id(self) -> str:
        """Generate a unique room ID"""
        return str(uuid.uuid4())[:8].upper()
    
    def generate_player_id(self) -> str:
        """Generate a unique player ID"""
        return str(uuid.uuid4())[:8]
    
    def create_room(self) -> Tuple[str, str]:
        """Create a new room and return room_id and player_id"""
        room_id = self.generate_room_id()
        player_id = self.generate_player_id()
        
        if db.create_room(room_id):
            db.add_player(player_id, room_id, 'X')
            return room_id, player_id
        else:
            # If room_id collision, try again
            return self.create_room()
    
    def join_room(self, room_id: str) -> Optional[str]:
        """Join an existing room and return player_id"""
        room = db.get_room(room_id)
        if not room:
            return None
        
        players = db.get_players_in_room(room_id)
        if len(players) >= 2:
            return None  # Room is full
        
        player_id = self.generate_player_id()
        player_symbol = 'O' if len(players) == 1 else 'X'
        db.add_player(player_id, room_id, player_symbol)
        
        # Update game status to 'playing' if room is now full
        if len(players) + 1 == 2:
            db.update_room(room_id, room['board'], 'X', 'playing')
        
        return player_id
    
    def get_game_state(self, room_id: str) -> Optional[Dict]:
        """Get current game state for a room"""
        room = db.get_room(room_id)
        if not room:
            return None
        
        players = db.get_players_in_room(room_id)
        return {
            'room_id': room_id,
            'board': room['board'],
            'current_player': room['current_player'],
            'game_status': room['game_status'],
            'players': players
        }
    
    def make_move(self, room_id: str, player_id: str, position: int) -> Optional[Dict]:
        """Make a move and return updated game state"""
        room = db.get_room(room_id)
        if not room:
            return None
        
        # Check if it's player's turn
        players = db.get_players_in_room(room_id)
        current_player_data = next((p for p in players if p['player_id'] == player_id), None)
        if not current_player_data:
            return None
        
        if room['current_player'] != current_player_data['player_symbol']:
            return None  # Not player's turn
        
        # Check if position is valid and empty
        if position < 0 or position > 8 or room['board'][position]:
            return None
        
        # Make the move
        new_board = room['board'].copy()
        new_board[position] = current_player_data['player_symbol']
        
        # Check for win or draw
        game_result = self.check_game_status(new_board)
        game_status = game_result['status']
        winning_combo = game_result['winning_combo']
        
        # Switch player if game is still ongoing
        next_player = 'O' if room['current_player'] == 'X' else 'X'
        if game_status == 'playing':
            next_player = next_player
        else:
            next_player = room['current_player']  # Keep current player if game ended
        
        # Update database
        db.update_room(room_id, new_board, next_player, game_status)
        
        return {
            'room_id': room_id,
            'board': new_board,
            'current_player': next_player,
            'game_status': game_status,
            'players': players,
            'last_move': {
                'position': position,
                'player': current_player_data['player_symbol']
            },
            'winning_combo': winning_combo
        }
    
    def check_game_status(self, board: List[str]) -> Dict:
        """Check if game is won, drawn, or still playing"""
        # Check for win
        for combo in self.winning_combinations:
            if (board[combo[0]] and 
                board[combo[0]] == board[combo[1]] and 
                board[combo[0]] == board[combo[2]]):
                return {
                    'status': 'won',
                    'winning_combo': combo
                }
        
        # Check for draw
        if all(cell for cell in board):
            return {
                'status': 'draw',
                'winning_combo': None
            }
        
        return {
            'status': 'playing',
            'winning_combo': None
        }
    
    def reset_game(self, room_id: str) -> Optional[Dict]:
        """Reset game to initial state"""
        room = db.get_room(room_id)
        if not room:
            return None
        
        # Reset board and game status
        empty_board = [''] * 9
        db.update_room(room_id, empty_board, 'X', 'playing')
        
        players = db.get_players_in_room(room_id)
        return {
            'room_id': room_id,
            'board': empty_board,
            'current_player': 'X',
            'game_status': 'playing',
            'players': players
        }
    
    def leave_room(self, room_id: str, player_id: str):
        """Handle player leaving room"""
        db.remove_player(player_id)
        
        # Check if room is now empty
        players = db.get_players_in_room(room_id)
        if not players:
            db.delete_room(room_id)
        else:
            # Update game status to waiting if only one player left
            room = db.get_room(room_id)
            if room:
                db.update_room(room_id, room['board'], room['current_player'], 'waiting')

# Global game logic instance
game_logic = GameLogic() 