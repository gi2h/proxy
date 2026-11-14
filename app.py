from flask import Flask, jsonify
import subprocess, time

app = Flask(__name__)

@app.route('/rotate/<int:worker_id>', methods=['GET'])
def rotate(worker_id):
    # worker_id dari Termux: 1-6. Index namespace: 0-5.
    idx = worker_id - 1
    if idx < 0 or idx > 5:
        return jsonify({"status": "error", "msg": "Worker ID harus 1-6"}), 400
    
    print(f"[API] Menerima perintah rotasi untuk Worker {worker_id} (ns{idx})")
    
    # Jalankan script rotasi di background (agar API tidak timeout)
    subprocess.Popen(["/tmp/rot_{}.sh".format(idx)])
    
    # Tunggu sebentar agar VPN mulai connect
    time.sleep(2)
    return jsonify({"status": "ok", "msg": f"Rotasi ns{idx} dimulai"})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "ok", "msg": "Server berjalan"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
