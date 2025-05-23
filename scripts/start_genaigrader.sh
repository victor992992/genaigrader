#!/bin/bash

# === CONFIGURATION ===
SESSION_NAME="genaigrader"
PORT=9898
PROJECT_DIR="$HOME/genaigrader"
ENV_FILE="$PROJECT_DIR/.env.django"
GUNICORN_SOCKET="127.0.0.1:$PORT"
GUNICORN_APP="mi_web.wsgi:application"
SETTINGS_MODULE="mi_web.settings_ngrok"
LOGFILE="gunicorn.log"

# Remove previous gunicorn PID file if any
rm -f gunicorn.pid

# Create tmux session if not exists
tmux has-session -t "$SESSION_NAME" 2>/dev/null
if [ $? != 0 ]; then
    echo "🖥️  Creating tmux session '$SESSION_NAME'..."
    tmux new-session -d -s "$SESSION_NAME"
    echo "✅ Session '$SESSION_NAME' created. To attach, run: tmux attach -t $SESSION_NAME"
    echo "To detach, press Ctrl+b then d."
fi

# Navigate to project directory
tmux send-keys -t "$SESSION_NAME" "cd $PROJECT_DIR" C-m

# Start ngrok tunnels in background
tmux send-keys -t "$SESSION_NAME" "ngrok start --all > /dev/null &" C-m
echo "🔄 Starting ngrok tunnels..."
sleep 5

# Retrieve public ngrok URL
for i in {1..10}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[] | select(.name=="backend") | .public_url' | sed 's|https://||; s|http://||')
    if [[ -n "$NGROK_URL" ]]; then
        echo "✅ ngrok public URL: $NGROK_URL"
        break
    fi
    sleep 1
done

if [[ -z "$NGROK_URL" ]]; then
    echo "❌ Could not get ngrok public URL."
    exit 1
fi

# Write env variables to be sourced
echo "export DJANGO_ALLOWED_HOSTS=\"$NGROK_URL,localhost\"" > "$ENV_FILE"

# Start ollama inside tmux
echo "🧠 Starting Ollama..."
tmux send-keys -t "$SESSION_NAME" "ollama serve > ollama.log 2>&1 & echo \$! > ollama.pid" C-m
sleep 2
echo "✅ Ollama started (PID saved in ollama.pid)."

# Run collectstatic
tmux send-keys -t "$SESSION_NAME" "source $ENV_FILE" C-m
tmux send-keys -t "$SESSION_NAME" "uv run python manage.py collectstatic --noinput --settings=$SETTINGS_MODULE" C-m

# Start gunicorn with WhiteNoise for static files
tmux send-keys -t "$SESSION_NAME" "uv run gunicorn $GUNICORN_APP \
    --bind $GUNICORN_SOCKET \
    --log-file $LOGFILE \
    --pid gunicorn.pid \
    --env DJANGO_SETTINGS_MODULE=$SETTINGS_MODULE > /dev/null 2>&1 &" C-m

echo "🟢 App running at: https://$NGROK_URL"
echo "📦 tmux session: $SESSION_NAME"
