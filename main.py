from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import logging
from typing import Dict, List
from game_logic import game_logic
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tic-Tac-Toe Online", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(f"Client connected to room {room_id}")
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        logger.info(f"Client disconnected from room {room_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    self.active_connections[room_id].remove(connection)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

# REST API endpoints
@app.post("/api/create-room")
async def create_room():
    """Create a new game room"""
    room_id, player_id = game_logic.create_room()
    return {
        "room_id": room_id,
        "player_id": player_id,
        "message": "Room created successfully"
    }

@app.post("/api/join-room")
async def join_room(room_id: str):
    """Join an existing room"""
    player_id = game_logic.join_room(room_id)
    if not player_id:
        raise HTTPException(status_code=404, detail="Room not found or full")
    
    return {
        "room_id": room_id,
        "player_id": player_id,
        "message": "Joined room successfully"
    }

@app.get("/api/game-state/{room_id}")
async def get_game_state(room_id: str):
    """Get current game state"""
    state = game_logic.get_game_state(room_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return state

@app.post("/api/make-move")
async def make_move(room_id: str, player_id: str, position: int):
    """Make a move in the game"""
    result = game_logic.make_move(room_id, player_id, position)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid move")
    return result

@app.post("/api/reset-game/{room_id}")
async def reset_game(room_id: str):
    """Reset the game"""
    result = game_logic.reset_game(room_id)
    if not result:
        raise HTTPException(status_code=404, detail="Room not found")
    return result

# WebSocket endpoint
@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await manager.connect(websocket, room_id)
    
    try:
        # Send initial game state
        game_state = game_logic.get_game_state(room_id)
        if game_state:
            await manager.send_personal_message(
                json.dumps({
                    "type": "game_state",
                    "data": game_state
                }), 
                websocket
            )
            
            # Check if this is the second player joining (room just became full)
            players = db.get_players_in_room(room_id)
            if len(players) == 2 and game_state['game_status'] == 'playing':
                # Broadcast to all players that the game has started
                await manager.broadcast_to_room(
                    json.dumps({
                        "type": "player_joined",
                        "data": game_state
                    }),
                    room_id
                )
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "make_move":
                # Handle move
                result = game_logic.make_move(room_id, player_id, message["position"])
                if result:
                    # Broadcast updated game state to all players in room
                    await manager.broadcast_to_room(
                        json.dumps({
                            "type": "game_update",
                            "data": result
                        }),
                        room_id
                    )
                else:
                    # Send error to the player who made invalid move
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid move"
                        }),
                        websocket
                    )
            
            elif message["type"] == "reset_game":
                # Handle game reset
                result = game_logic.reset_game(room_id)
                if result:
                    await manager.broadcast_to_room(
                        json.dumps({
                            "type": "game_reset",
                            "data": result
                        }),
                        room_id
                    )
            
            elif message["type"] == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        # Handle player leaving
        game_logic.leave_room(room_id, player_id)
        
        # Notify other players
        remaining_state = game_logic.get_game_state(room_id)
        if remaining_state:
            await manager.broadcast_to_room(
                json.dumps({
                    "type": "player_left",
                    "data": remaining_state
                }),
                room_id
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 