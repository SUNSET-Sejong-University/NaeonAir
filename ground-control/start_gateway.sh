#!/bin/bash
# WisDrone Gateway Startup Script
# Node.js bridge + Python WebSocket 동시 실행

echo "=========================================="
echo "🚀 WisDrone Gateway Starting..."
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NCUBE_DIR="$SCRIPT_DIR/ncube"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping gateway..."
    kill $BRIDGE_PID 2>/dev/null
    kill $GATEWAY_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Check dependencies
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed!"
    exit 1
fi

# Install Node dependencies if needed
if [ ! -d "$NCUBE_DIR/node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    cd "$NCUBE_DIR" && npm install
fi

# 1. Start Node.js Bridge (Mobius 연동)
echo "🌉 Starting Node.js Bridge (Port 9800)..."
cd "$NCUBE_DIR"
node gateway_bridge.js &
BRIDGE_PID=$!
sleep 2

# 2. Start Python Gateway (WebSocket)
echo "📡 Starting Python Gateway (Port 3001)..."
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/../.venv/bin/activate"
python3 gateway.py &
GATEWAY_PID=$!

echo ""
echo "=========================================="
echo "✅ Gateway started!"
echo ""
echo "   Node.js Bridge: http://localhost:9800"
echo "   WebSocket:      ws://localhost:3001"
echo ""
echo "   Bridge PID:  $BRIDGE_PID"
echo "   Gateway PID: $GATEWAY_PID"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

# Wait for processes
wait
