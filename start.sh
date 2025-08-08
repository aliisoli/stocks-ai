#!/bin/bash

echo "Starting AutoGen Stock Analyzer..."

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting server..."
    cd server
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    SERVER_PID=$!
    cd ..
    
    # Wait for server to start
    echo "Waiting for server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "Server is running on http://localhost:8000"
            break
        fi
        sleep 1
    done
else
    echo "Server is already running on http://localhost:8000"
fi

# Check if frontend is running
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "Starting frontend..."
    cd web
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    echo "Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo "Frontend is running on http://localhost:5173"
            break
        fi
        sleep 1
    done
else
    echo "Frontend is already running on http://localhost:5173"
fi

echo ""
echo "AutoGen Stock Analyzer is ready!"
echo "Frontend: http://localhost:5173"
echo "Server: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $SERVER_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait 