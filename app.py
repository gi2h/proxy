from flask import Flask, jsonify
import subprocess, urllib.request, base64, time, random, os

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
    print("[API] Mematikan VPN lama...")
    subprocess.run(["pkill", "openvpn"], capture_output=True)
    time.sleep(2)
    
    print("[API] Mengunduh config VPN Gate...")
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
                
        if not configs: return False
            
        config = base64.b64decode(random.choice(configs)).decode('utf-8')
        with open('/tmp/vpn.ovpn', 'w') as f:
            f.write(config)
            
        print("[API] Menjalankan OpenVPN...")
        subprocess.Popen(["openvpn", "--config", "/tmp/vpn.ovpn", "--daemon"])
        
        time.sleep(12)
        new_ip = get_ip()
        if new_ip:
            current_ip = new_ip
            print(f"[API] VPN Terhubung! IP Baru: {current_ip}")
            return True
    except Exception as e:
        print(f"[API] Error: {e}")
    return False

@app.route('/rotate')
def api_rotate():
    success = rotate_vpn()
    if success: return jsonify({"status": "ok", "ip": current_ip})
    return jsonify({"status": "error", "msg": "Gagal rotasi"}), 500

@app.route('/status')
def api_status():
    return jsonify({"ip": current_ip})

if __name__ == '__main__':
    print("[SYS] Inisialisasi awal VPN...")
    rotate_vpn()
    app.run(host='0.0.0.0', port=8000)
