#!/usr/bin/env bash
set -euo pipefail

# Start Maestro Dashboard
# This script starts both the WebSocket server and serves the HTML dashboard

DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DASHBOARD_DIR")"
HOST="${DASHBOARD_HOST:-localhost}"
PORT="${DASHBOARD_PORT:-8765}"
HTTP_PORT="${DASHBOARD_HTTP_PORT:-8080}"

echo "🎭 Starting Maestro Dashboard..."
echo "📁 Dashboard directory: $DASHBOARD_DIR"
echo "📁 Project root: $PROJECT_ROOT"
echo "🌐 WebSocket server: ws://$HOST:$PORT"
echo "🌐 HTTP server: http://$HOST:$HTTP_PORT"

# Check if Python dependencies are installed
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r "$DASHBOARD_DIR/requirements.txt"
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Function to start WebSocket server
start_websocket_server() {
    echo "🚀 Starting WebSocket server..."
    cd "$PROJECT_ROOT"
    python3 "$DASHBOARD_DIR/server.py" &
    WEBSOCKET_PID=$!
    echo "📡 WebSocket server PID: $WEBSOCKET_PID"
}

# Function to start HTTP server for static files
start_http_server() {
    echo "🌐 Starting HTTP server for dashboard..."
    cd "$DASHBOARD_DIR"
    python3 -m http.server "$HTTP_PORT" &
    HTTP_PID=$!
    echo "📄 HTTP server PID: $HTTP_PID"
}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down dashboard..."
    if [ -n "${WEBSOCKET_PID:-}" ]; then
        kill "$WEBSOCKET_PID" 2>/dev/null || true
    fi
    if [ -n "${HTTP_PID:-}" ]; then
        kill "$HTTP_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start servers
start_websocket_server
sleep 2  # Give WebSocket server time to start
start_http_server

echo ""
echo "✅ Dashboard started successfully!"
echo "🌐 Open your browser to: http://$HOST:$HTTP_PORT"
echo "📡 WebSocket endpoint: ws://$HOST:$PORT"
echo ""
echo "Press Ctrl+C to stop the dashboard"

# Wait for servers
wait