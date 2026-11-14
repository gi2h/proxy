#!/bin/bash
# Railway-friendly startup: hanya jalankan Flask API
python3 /app.py

# Jika Flask berhenti, keep container alive
while true; do sleep 3600; done
