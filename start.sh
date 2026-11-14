#!/bin/bash

# Bersihkan antarmuka lama (jika restart)
for i in {0..5}; do
    ip netns del ns$i 2>/dev/null
done

# Jalankan API di background
python3 /app.py &

# Inisialisasi 6 Network Namespace
for i in {0..5}; do
    PORT=$((8080 + i))
    echo "[SYS] Menyiapkan Namespace ns$i (Proxy Port: $PORT)..."
    
    # 1. Buat namespace
    ip netns add ns$i
    
    # 2. Nyalakan loopback di dalam namespace
    ip netns exec ns$i ip link set lo up
    
    # 3. Download config VPN (di background agar cepat)
    CONFIG_PATH="/tmp/vpn_$i.ovpn"
    
    # 4. Buat script rotasi untuk namespace ini
    cat <<EOF > /tmp/rot_$i.sh
#!/bin/bash
pkill -f "openvpn.*vpn_$i.ovpn"
sleep 2
curl -s "http://www.vpngate.net/api/iphone/" | grep -v "^#" | grep -v "^\*" | awk -F, '{print \$15}' | grep -E "^[A-Za-z0-9+/=]+$" | shuf -n 1 | base64 -d > /tmp/vpn_$i.ovpn 2>/dev/null
if [ -s /tmp/vpn_$i.ovpn ]; then
    ip netns exec ns$i openvpn --config /tmp/vpn_$i.ovpn --daemon
fi
EOF
    chmod +x /tmp/rot_$i.sh
    
    # 5. Rotasi pertama
    /tmp/rot_$i.sh
    
    # 6. Jalankan microsocks di dalam namespace
    ip netns exec ns$i microsocks -p 8080 -q &
    
    # 7. Hubungkan port host ke port namespace menggunakan socat
    socat TCP-LISTEN:$PORT,fork,reuseaddr TCP:127.0.0.1:8080 &
done

echo "[SYS] Semua 6 VPN & Proxy berjalan!"
wait
