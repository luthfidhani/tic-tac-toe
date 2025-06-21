# Tic-Tac-Toe Online Game

A multiplayer online Tic-Tac-Toe game built with FastAPI, WebSockets, and Alpine.js.

## Features

- 🎮 Real-time multiplayer Tic-Tac-Toe game
- 🏠 Room system with shareable IDs
- ⚡ Real-time updates via WebSocket
- 🔄 Game reset after completion
- 📱 Responsive design with Tailwind CSS
- 🚀 Single Page Application (SPA)

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, Tailwind CSS, Alpine.js
- **Database**: SQLite
- **Real-time**: WebSockets

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Server

```bash
python main.py
```

The server will run at `http://localhost:8000`

### 3. Open Browser

Open `http://localhost:8000` in your browser to start playing!

## How to Play

1. Open the game in your browser
2. Click "Create Room" to create a new room
3. Share the room ID with your friend
4. Your friend joins using the same room ID
5. Start playing Tic-Tac-Toe!

## Project Structure

```
tic-tac-toe/
├── main.py              # Main FastAPI server
├── game_logic.py        # Game logic and room management
├── database.py          # Database operations
├── static/
│   ├── index.html       # Main page
│   ├── style.css        # Custom CSS
│   └── script.js        # Alpine.js logic
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

## Screenshots
![image](https://github.com/user-attachments/assets/0a2fce2b-3ff6-4ab5-b0dc-86ce72a12a35)
![image](https://github.com/user-attachments/assets/36b5804c-243a-432b-b977-40f1a04b3b0e)

