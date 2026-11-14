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
    if idx < 0 or idx > 5:
        return jsonify({"status": "error", "msg": "Worker ID 1-6"}), 400
    
    print(f"[API] Rotasi Worker {worker_id} (tun{idx})")
    
    subprocess.run(["pkill", "-f", f"gost.*:{8080+idx}"], capture_output=True)
    subprocess.run(["pkill", "-f", f"openvpn.*tun{idx}"], capture_output=True)
    time.sleep(2)
    
    config = get_vpn_config()
    if not config:
        return jsonify({"status": "error", "msg": "Gagal download config"}), 500
        
    with open(f'/tmp/vpn_{idx}.ovpn', 'w') as f:
        f.write(config)
        
    subprocess.Popen(["openvpn", "--config", f"/tmp/vpn_{idx}.ovpn", "--dev", f"tun{idx}", "--route-nopull", "--daemon"])
    time.sleep(5)
    
    subprocess.Popen(["gost", "-L", f"socks5://:{8080+idx}?interface=tun{idx}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return jsonify({"status": "ok", "msg": f"Worker {worker_id} rotated"})

@app.route('/status')
def status():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
