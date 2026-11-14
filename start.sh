#!/bin/bash
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 2 --timeout 180 --max-requests 500 --max-requests-jitter 50 app:app
