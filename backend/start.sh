#!/bin/bash

echo ">>> Starting server..."
uvicorn main:app --host 0.0.0.0 --port $PORT
