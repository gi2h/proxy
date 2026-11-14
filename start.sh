#!/bin/bash

# 1. Jalankan API di Port 8080
python3 /app.py &

# 2. Inisialisasi 3 VPN dan Proxy (Port 8081, 8082, 8083)
for i in {0..2}; do
    PORT=$((8081 + i))
    echo "[SYS] Menyiapkan tun$i (Proxy Port: $PORT)..."
    
    curl -s "http://www.vpngate.net/api/iphone/" | grep -v "^#" | grep -v "^\*" | awk -F, '{print $15}' | grep -E "^[A-Za-z0-9+/=]+$" | shuf -n 1 | base64 -d > /tmp/vpn_$i.ovpn 2>/dev/null
    
    openvpn --config /tmp/vpn_$i.ovpn --dev tun$i --route-nopull --daemon
    sleep 3
    
    gost -L=socks5://:$PORT?interface=tun$i > /dev/null 2>&1 &
done

echo "[SYS] Semua 3 VPN & Proxy berjalan! Menahan container..."
tail -f /dev/null
