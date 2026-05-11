#!/bin/bash

# Start servers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# Start chatbot
echo "Starting chatbot on port 8000..."
cd "$SCRIPT_DIR/chatbot"
chainlit run app.py --port 8000 > chatbot.log 2>&1 &
CHATBOT_PID=$!
echo "Chatbot started with PID: $CHATBOT_PID"
echo "$CHATBOT_PID" > "$SCRIPT_DIR/.chatbot.pid"

# Start server (Ray initialises on startup via lifespan)
echo "Starting server on port 8888..."
cd "$SCRIPT_DIR/server"
python main.py > server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"
echo "$SERVER_PID" > "$SCRIPT_DIR/.server.pid"

echo ""
echo "Services started."
echo "Server:         http://localhost:8888"
echo "Chatbot:        http://localhost:8000"
echo ""
echo "To stop services, run: ./stop.sh"