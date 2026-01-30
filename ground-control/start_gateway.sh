#!/bin/bash
# WisDrone Gateway Startup Script

echo "=========================================="
echo "🚀 WisDrone Gateway Starting..."
echo "=========================================="

# 현재 스크립트 위치 기준으로 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NCUBE_DIR="$SCRIPT_DIR/ncube"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    exit 1
fi

# Check dependencies
if [ ! -d "$NCUBE_DIR/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd "$NCUBE_DIR" && npm install
fi

# Start Gateway Bridge
echo "🌉 Starting Gateway Bridge (Port 9800)..."
cd "$NCUBE_DIR"
node gateway_bridge.js &
BRIDGE_PID=$!

echo ""
echo "✅ Gateway started!"
echo "   - Bridge PID: $BRIDGE_PID"
echo "   - Bridge URL: http://localhost:9800"
echo ""
echo "To stop: kill $BRIDGE_PID"
echo "=========================================="

# Keep running
wait $BRIDGE_PID
