#!/bin/bash
# Jalankan Microsocks (Proxy) di port 8080
microsocks -p 8080 &

# Jalankan API Server
python3 /app.py
