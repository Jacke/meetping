#!/bin/bash
# Test bot startup

echo "🧪 Testing bot startup..."
echo ""

# Run bot in background
.venv/bin/python3 main.py payment-flow > /tmp/bot_test.log 2>&1 &
BOT_PID=$!

echo "📝 Bot PID: $BOT_PID"
echo "⏳ Waiting 3 seconds for startup..."
sleep 3

# Check if still running
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot started successfully!"
    echo ""
    echo "📋 Startup log:"
    head -20 /tmp/bot_test.log

    # Kill bot
    echo ""
    echo "🛑 Stopping bot..."
    kill $BOT_PID 2>/dev/null
    sleep 1
    kill -9 $BOT_PID 2>/dev/null
    echo "✅ Bot stopped"
else
    echo "❌ Bot failed to start!"
    echo ""
    echo "📋 Error log:"
    cat /tmp/bot_test.log
    exit 1
fi
