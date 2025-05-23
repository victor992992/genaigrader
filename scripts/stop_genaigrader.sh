#!/bin/bash

SESSION_NAME="genaigrader"
PROJECT_DIR="$HOME/genaigrader"

# Stop gunicorn if running
cd "$PROJECT_DIR"
if [ -f gunicorn.pid ]; then
    PID=$(cat gunicorn.pid)
    echo "🛑 Stopping gunicorn (PID: $PID)..."
    kill $PID && rm -f gunicorn.pid
    echo "✅ Gunicorn stopped."
else
    echo "ℹ️ Gunicorn PID not found. Skipping."
fi

# Stop Ollama if running
if [ -f ollama.pid ]; then
    OLLAMA_PID=$(cat ollama.pid)
    echo "🛑 Stopping Ollama (PID $OLLAMA_PID)..."
    kill "$OLLAMA_PID" && rm -f ollama.pid
    echo "✅ Ollama stopped."
else
    echo "ℹ️ Ollama PID not found. Skipping."
fi

# Kill ngrok if running inside tmux
tmux send-keys -t "$SESSION_NAME" "pkill ngrok" C-m

# Optionally kill the tmux session
tmux kill-session -t "$SESSION_NAME" 2>/dev/null
echo "🛑 Deployment stopped."
