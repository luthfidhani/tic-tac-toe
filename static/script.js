// Alpine.js Game Application
function gameApp() {
    return {
        // Game state
        roomId: null,
        playerId: null,
        playerSymbol: null,
        opponentSymbol: null,
        board: ['', '', '', '', '', '', '', '', ''],
        currentPlayer: 'X',
        gameStatus: 'waiting', // waiting, playing, won, draw
        winner: null,
        lastMove: null,
        winningCombo: null,
        
        // UI state
        inRoom: false,
        connected: false,
        loading: false,
        roomIdToJoin: '',
        
        // WebSocket
        ws: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 5,
        
        // Toast notifications
        toast: {
            show: false,
            message: '',
            type: 'success'
        },
        
        // Initialize app
        init() {
            this.setupWebSocket();
            this.startPingInterval();
        },
        
        // WebSocket setup
        setupWebSocket() {
            if (this.ws) {
                this.ws.close();
            }
            
            // Only connect if we have room and player info
            if (!this.roomId || !this.playerId) {
                return;
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.roomId}/${this.playerId}`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this.showToast('Connected to game server', 'success');
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.handleWebSocketClose();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showToast('Connection error', 'error');
            };
        },
        
        // Handle WebSocket messages
        handleWebSocketMessage(message) {
            switch (message.type) {
                case 'game_state':
                    this.updateGameState(message.data);
                    break;
                    
                case 'game_update':
                    this.updateGameState(message.data);
                    this.showToast('Opponent made a move!', 'success');
                    break;
                    
                case 'player_joined':
                    this.updateGameState(message.data);
                    this.showToast('Opponent joined! Game starting...', 'success');
                    break;
                    
                case 'game_reset':
                    this.updateGameState(message.data);
                    this.showToast('Game has been reset!', 'success');
                    break;
                    
                case 'player_left':
                    this.updateGameState(message.data);
                    this.showToast('Opponent left the room', 'error');
                    break;
                    
                case 'error':
                    this.showToast(message.message, 'error');
                    break;
                    
                case 'pong':
                    // Keep connection alive
                    break;
            }
        },
        
        // Handle WebSocket close
        handleWebSocketClose() {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                this.showToast(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'error');
                
                setTimeout(() => {
                    this.setupWebSocket();
                }, 2000 * this.reconnectAttempts);
            } else {
                this.showToast('Connection lost. Please refresh the page.', 'error');
            }
        },
        
        // Start ping interval to keep connection alive
        startPingInterval() {
            setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000); // Ping every 30 seconds
        },
        
        // Create a new room
        async createRoom() {
            this.loading = true;
            try {
                const response = await fetch('/api/create-room', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.roomId = data.room_id;
                    this.playerId = data.player_id;
                    this.playerSymbol = 'X';
                    this.opponentSymbol = 'O';
                    this.inRoom = true;
                    
                    this.setupWebSocket();
                    this.showToast('Room created! Share the room ID with your friend.', 'success');
                } else {
                    throw new Error('Failed to create room');
                }
            } catch (error) {
                console.error('Error creating room:', error);
                this.showToast('Failed to create room. Please try again.', 'error');
            } finally {
                this.loading = false;
            }
        },
        
        // Join an existing room
        async joinRoom() {
            if (!this.roomIdToJoin.trim()) {
                this.showToast('Please enter a room ID', 'error');
                return;
            }
            
            this.loading = true;
            try {
                const response = await fetch(`/api/join-room?room_id=${this.roomIdToJoin.trim()}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.roomId = data.room_id;
                    this.playerId = data.player_id;
                    this.playerSymbol = 'O';
                    this.opponentSymbol = 'X';
                    this.inRoom = true;
                    this.roomIdToJoin = '';
                    
                    this.setupWebSocket();
                    this.showToast('Joined room successfully!', 'success');
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to join room');
                }
            } catch (error) {
                console.error('Error joining room:', error);
                this.showToast(error.message || 'Failed to join room. Please check the room ID.', 'error');
            } finally {
                this.loading = false;
            }
        },
        
        // Leave the current room
        leaveRoom() {
            if (this.ws) {
                this.ws.close();
            }
            
            this.resetGameState();
            this.showToast('Left the room', 'success');
        },
        
        // Make a move
        makeMove(position) {
            if (!this.canMakeMove(position)) {
                return;
            }
            
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'make_move',
                    position: position
                }));
            } else {
                this.showToast('Connection lost. Please refresh the page.', 'error');
            }
        },
        
        // Check if player can make a move
        canMakeMove(position) {
            return this.gameStatus === 'playing' && 
                   this.currentPlayer === this.playerSymbol && 
                   !this.board[position];
        },
        
        // Reset the game
        resetGame() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'reset_game'
                }));
            }
        },
        
        // Update game state from server
        updateGameState(data) {
            this.board = data.board;
            this.currentPlayer = data.current_player;
            this.gameStatus = data.game_status;
            this.lastMove = data.last_move || null;
            this.winningCombo = data.winning_combo || null;
            
            // Determine winner if game is won
            if (this.gameStatus === 'won' && this.lastMove) {
                this.winner = this.lastMove.player;
            }
        },
        
        // Reset game state
        resetGameState() {
            this.roomId = null;
            this.playerId = null;
            this.playerSymbol = null;
            this.opponentSymbol = null;
            this.board = ['', '', '', '', '', '', '', '', ''];
            this.currentPlayer = 'X';
            this.gameStatus = 'waiting';
            this.winner = null;
            this.lastMove = null;
            this.winningCombo = null;
            this.inRoom = false;
            this.connected = false;
        },
        
        // Copy room ID to clipboard
        async copyRoomId() {
            try {
                await navigator.clipboard.writeText(this.roomId);
                this.showToast('Room ID copied to clipboard!', 'success');
            } catch (error) {
                console.error('Failed to copy room ID:', error);
                this.showToast('Failed to copy room ID', 'error');
            }
        },
        
        // Show toast notification
        showToast(message, type = 'success') {
            this.toast = {
                show: true,
                message: message,
                type: type
            };
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                this.toast.show = false;
            }, 3000);
        },
        
        // Calculate coordinates for winning line
        getLineCoords() {
            if (!this.winningCombo) return { x1: 0, y1: 0, x2: 0, y2: 0 };
            
            const combos = {
                // Rows
                '0,1,2': { x1: 5, y1: 16.6, x2: 95, y2: 16.6 },
                '3,4,5': { x1: 5, y1: 50, x2: 95, y2: 50 },
                '6,7,8': { x1: 5, y1: 83.3, x2: 95, y2: 83.3 },
                // Cols
                '0,3,6': { x1: 16.6, y1: 5, x2: 16.6, y2: 95 },
                '1,4,7': { x1: 50, y1: 5, x2: 50, y2: 95 },
                '2,5,8': { x1: 83.3, y1: 5, x2: 83.3, y2: 95 },
                // Diagonals
                '0,4,8': { x1: 10, y1: 10, x2: 90, y2: 90 },
                '2,4,6': { x1: 90, y1: 10, x2: 10, y2: 90 },
            };
            
            return combos[this.winningCombo.join(',')] || { x1: 0, y1: 0, x2: 0, y2: 0 };
        },
        
        // Get computed properties
        get isMyTurn() {
            return this.gameStatus === 'playing' && this.currentPlayer === this.playerSymbol;
        },
        
        get gameStatusText() {
            switch (this.gameStatus) {
                case 'waiting':
                    return 'Waiting for opponent...';
                case 'playing':
                    return this.isMyTurn ? 'Your turn!' : 'Opponent\'s turn';
                case 'won':
                    return `${this.winner} wins!`;
                case 'draw':
                    return 'It\'s a draw!';
                default:
                    return '';
            }
        }
    };
} 