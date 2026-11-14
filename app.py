from flask import Flask, jsonify
import subprocess, urllib.request, base64, time, os, random

app = Flask(__name__)
current_ip = "0.0.0.0"

def get_ip():
    try:
        req = urllib.request.Request("https://api.ipify.org")
        return urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    except:
        return None

def rotate_vpn():
    global current_ip
    print("[API] Menerima perintah rotasi. Mematikan VPN lama...")
    subprocess.run(["pkill", "openvpn"], capture_output=True)
    time.sleep(2)
    
    print("[API] Mengunduh config VPN Gate baru...")
    try:
        req = urllib.request.Request("http://www.vpngate.net/api/iphone/")
        res = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
        lines = res.split('\n')
        configs = []
        for line in lines:
            if line.startswith('#') or line.startswith('*'): continue
            parts = line.split(',')
            if len(parts) >= 15 and len(parts[14]) > 100:
                configs.append(parts[14])
                
        if not configs:
            print("[API] Gagal mendapatkan config dari VPN Gate")
            return False
            
        # Pilih config acak
        config = base64.b64decode(random.choice(configs)).decode('utf-8')
        with open('/tmp/vpn.ovpn', 'w') as f:
            f.write(config)
            
        print("[API] Menjalankan OpenVPN...")
        subprocess.Popen(["openvpn", "--config", "/tmp/vpn.ovpn", "--daemon"])
        
        # Tunggu sampai koneksi VPN terbentuk
        time.sleep(12)
        
        new_ip = get_ip()
        if new_ip:
            current_ip = new_ip
            print(f"[API] VPN Terhubung! IP Baru: {current_ip}")
            return True
    except Exception as e:
        print(f"[API] Error: {e}")
    return False

@app.route('/rotate', methods=['POST', 'GET'])
def api_rotate():
    # Endpoint ini akan dipanggil oleh bot Termux untuk minta IP baru
    success = rotate_vpn()
    if success:
        return jsonify({"status": "ok", "ip": current_ip})
    else:
        return jsonify({"status": "error", "msg": "Gagal rotasi"}), 500

@app.route('/status', methods=['GET'])
def api_status():
    return jsonify({"ip": current_ip})

if __name__ == '__main__':
    # Rotasi pertama saat server menyala
    rotate_vpn()
    # Jalankan API di port 8000
    app.run(host='0.0.0.0', port=8000)
