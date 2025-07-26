#!/bin/bash

# Palo Alto Whitelist Tool - Server Startup Script
# Für Ubuntu Server mit nohup

echo "Starting Palo Alto Whitelist Tool on Ubuntu Server..."

# Set environment variables
export PYTHONUNBUFFERED=1
export FLASK_ENV=production

# Kill any existing process
pkill -f "python.*main.py" 2>/dev/null || true

# Wait a moment
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the application with proper output handling
nohup python3 main.py \
    --host=0.0.0.0 \
    --port=5010 \
    > logs/server_stdout.log 2> logs/server_stderr.log &

# Get the process ID
PID=$!
echo "Started with PID: $PID"
echo $PID > logs/server.pid

# Wait a moment and check if it's running
sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ Server started successfully!"
    echo "📊 Check status: tail -f logs/server_stdout.log"
    echo "❌ Check errors: tail -f logs/server_stderr.log"
    echo "🌐 Access URL: http://YOUR_SERVER_IP:5010"
    echo "🛑 Stop server: kill $PID"
else
    echo "❌ Server failed to start. Check logs:"
    echo "STDOUT:"
    cat logs/server_stdout.log
    echo "STDERR:"
    cat logs/server_stderr.log
fi