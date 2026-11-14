#!/bin/bash
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 180 app:app
