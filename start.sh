#!/bin/bash

# 1. Jalankan API di Port 8080 (Sesuai kemauan Railway)
python3 /app.py &

# 2. Inisialisasi 3 VPN dan Proxy (Port 8081 - 8083)
for i in {0..2}; do
    PORT=$((8081 + i))
    echo "[SYS] Menyiapkan tun$i (Proxy Port: $PORT)..."
    
    # Download config VPN
    curl -s "http://www.vpngate.net/api/iphone/" | grep -v "^#" | grep -v "^\*" | awk -F, '{print $15}' | grep -E "^[A-Za-z0-9+/=]+$" | shuf -n 1 | base64 -d > /tmp/vpn_$i.ovpn 2>/dev/null
    
    # Jalankan OpenVPN
    openvpn --config /tmp/vpn_$i.ovpn --dev tun$i --route-nopull --daemon
    sleep 3
    
    # Jalankan gost dan BIND ke interface tun$i
    gost -L=socks5://:$PORT?interface=tun$i > /dev/null 2>&1 &
done

echo "[SYS] Semua 3 VPN & Proxy berjalan!"
wait
