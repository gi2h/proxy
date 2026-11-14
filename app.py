from flask import Flask, jsonify
import subprocess, urllib.request, base64, time, random, os

app = Flask(__name__)

def get_vpn_config():
    try:
        req = urllib.request.Request("http://www.vpngate.net/api/iphone/")
        res = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
        configs = [line.split(',')[14] for line in res.split('\n') if not line.startswith(('#', '*')) and len(line.split(',')) >= 15 and len(line.split(',')[14]) > 100]
        if not configs: return None
        return base64.b64decode(random.choice(configs)).decode('utf-8')
    except: return None

@app.route('/rotate/<int:worker_id>')
def rotate(worker_id):
    idx = worker_id - 1
    if idx < 0 or idx > 2:
        return jsonify({"status": "error", "msg": "Worker ID 1-3"}), 400
    
    print(f"[API] Merotasi Worker {worker_id} (tun{idx})")
    
    subprocess.run(["pkill", "-f", f"gost.*:{8081+idx}"], capture_output=True)
    subprocess.run(["pkill", "-f", f"openvpn.*tun{idx}"], capture_output=True)
    time.sleep(2)
    
    config = get_vpn_config()
    if not config:
        return jsonify({"status": "error", "msg": "Gagal download config"}), 500
        
    with open(f'/tmp/vpn_{idx}.ovpn', 'w') as f:
        f.write(config)
        
    subprocess.Popen(["openvpn", "--config", f"/tmp/vpn_{idx}.ovpn", "--dev", f"tun{idx}", "--route-nopull", "--daemon"])
    
    # TUNGGU SAMPAI INTERFACE TUN MUNCUL
    tun_ready = False
    for _ in range(20):
        time.sleep(1)
        if os.path.exists(f"/sys/class/net/tun{idx}"):
            tun_ready = True
            break
            
    if not tun_ready:
        print(f"[API] Gagal: tun{idx} timeout")
        return jsonify({"status": "error", "msg": "VPN gagal konek"}), 500
        
    time.sleep(2) # Beri waktu IP assignment
    
    # Jalankan gost dengan -F
    subprocess.Popen(["gost", "-L", f"socks5://:{8081+idx}", "-F", f"direct?interface=tun{idx}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"[API] Worker {worker_id} siap!")
    return jsonify({"status": "ok", "msg": f"Worker {worker_id} rotated"})

@app.route('/status')
def status():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
