#!/bin/bash

# Jalankan SOCKS5 Proxy di background (Port 8080)
microsocks -p 8080 &

# Jalankan API Server (Port 8000)
python3 /app.py
