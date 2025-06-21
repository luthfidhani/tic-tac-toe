import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create rooms table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    board TEXT DEFAULT '["","","","","","","","",""]',
                    current_player TEXT DEFAULT 'X',
                    game_status TEXT DEFAULT 'waiting',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create players table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    room_id TEXT,
                    player_symbol TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms (room_id)
                )
            ''')
            
            conn.commit()
    
    def create_room(self, room_id: str) -> bool:
        """Create a new room"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO rooms (room_id) VALUES (?)",
                    (room_id,)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Room already exists
    
    def get_room(self, room_id: str) -> Optional[Dict]:
        """Get room data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM rooms WHERE room_id = ?",
                (room_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'room_id': row[0],
                    'board': json.loads(row[1]),
                    'current_player': row[2],
                    'game_status': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                }
            return None
    
    def update_room(self, room_id: str, board: List[str], current_player: str, game_status: str):
        """Update room data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE rooms SET board = ?, current_player = ?, game_status = ?, updated_at = CURRENT_TIMESTAMP WHERE room_id = ?",
                (json.dumps(board), current_player, game_status, room_id)
            )
            conn.commit()
    
    def add_player(self, player_id: str, room_id: str, player_symbol: str):
        """Add player to room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO players (player_id, room_id, player_symbol) VALUES (?, ?, ?)",
                (player_id, room_id, player_symbol)
            )
            conn.commit()
    
    def get_players_in_room(self, room_id: str) -> List[Dict]:
        """Get all players in a room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT player_id, player_symbol FROM players WHERE room_id = ?",
                (room_id,)
            )
            rows = cursor.fetchall()
            return [{'player_id': row[0], 'player_symbol': row[1]} for row in rows]
    
    def remove_player(self, player_id: str):
        """Remove player from room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
            conn.commit()
    
    def delete_room(self, room_id: str):
        """Delete room and all its players"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players WHERE room_id = ?", (room_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
            conn.commit()
    
    def cleanup_empty_rooms(self):
        """Remove rooms with no players"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM rooms 
                WHERE room_id NOT IN (
                    SELECT DISTINCT room_id FROM players
                )
            """)
            conn.commit()

# Global database instance
db = Database() 