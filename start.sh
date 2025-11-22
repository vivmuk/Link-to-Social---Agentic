#!/bin/sh
# Start script that properly handles PORT environment variable
PORT=${PORT:-8000}
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"

