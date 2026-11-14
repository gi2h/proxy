#!/bin/bash

# Jalankan API di background
python3 /app.py &

# Inisialisasi 6 VPN dan Proxy
for i in {0..5}; do
    PORT=$((8080 + i))
    echo "[SYS] Menyiapkan tun$i (Proxy Port: $PORT)..."
    
    # 1. Download config VPN
    curl -s "http://www.vpngate.net/api/iphone/" | grep -v "^#" | grep -v "^\*" | awk -F, '{print $15}' | grep -E "^[A-Za-z0-9+/=]+$" | shuf -n 1 | base64 -d > /tmp/vpn_$i.ovpn 2>/dev/null
    
    # 2. Jalankan OpenVPN dengan --route-nopull agar tidak mengubah route default
    openvpn --config /tmp/vpn_$i.ovpn --dev tun$i --route-nopull --daemon
    
    # Beri waktu OpenVPN untuk membuat interface tun
    sleep 3
    
    # 3. Jalankan gost dan BIND ke interface tun$i
    gost -L=socks5://:$PORT?interface=tun$i > /dev/null 2>&1 &
done

echo "[SYS] Semua 6 VPN & Proxy berjalan!"
wait
