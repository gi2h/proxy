from flask import Flask, jsonify, request, Response
import subprocess, urllib.request, socket, time, random, os, re, json, threading

app = Flask(__name__)

# Jumlah worker & port (default 6). Bisa override via env PROXY_PORTS="8081,8082,..."
WORKER_PORTS = [int(p) for p in os.environ.get("PROXY_PORTS", "8081,8082,8083,8084,8085,8086").split(",")]
NUM_WORKERS = len(WORKER_PORTS)

# Pool proxy (TCP terbuka) - list of dict {proxy, raw, proxy_proto, ip}
proxy_pool = []
current = {}  # idx -> {"port": int, "proxy": str, "ip": str}
lock = threading.Lock()

PROXY_SOURCES = [
    ("socks5", "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all"),
    ("http",   "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"),
    ("http",   "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"),
    ("socks5", "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt"),
    ("socks5", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"),
]

def test_connect(proxy, proto, timeout=5):
    """Fast TCP connect check (low memory, high throughput)"""
    try:
        host, port = proxy.split(":")
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def test_exit_ip(proxy, proto, timeout=8):
    """Curl through proxy to get exit IP (only for assign)"""
    scheme = "socks5h" if proto == "socks5" else proto
    try:
        res = subprocess.run(
            ["curl", "-s", "-m", str(timeout), "-x", f"{scheme}://{proxy}", "https://checkip.amazonaws.com/"],
            capture_output=True, timeout=timeout + 2
        )
        if res.returncode == 0:
            ip = res.stdout.decode().strip()
            if re.match(r'^[\d.]+$', ip) or ':' in ip:
                return ip
    except Exception:
        pass
    return None

def refresh_pool(max_test=300):
    """Fetch & TCP-validate proxy lists, fill global proxy_pool"""
    raw = []
    for proto, url in PROXY_SOURCES:
        try:
            text = urllib.request.urlopen(url, timeout=25).read().decode('utf-8', 'ignore')
            for line in text.splitlines():
                line = line.strip()
                if re.match(r'^[\d.]+:\d+$', line):
                    raw.append((proto, line))
        except Exception:
            pass

    random.shuffle(raw)
    raw = raw[:max_test]

    found = []
    chunk = 40
    def validate(batch):
        for proto, p in batch:
            if test_connect(p, proto, timeout=4):
                with lock:
                    found.append({"proxy": f"{proto}://{p}", "raw": p, "proxy_proto": proto, "ip": None})

    threads = []
    for i in range(0, len(raw), chunk):
        t = threading.Thread(target=validate, args=(raw[i:i + chunk],))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    with lock:
        proxy_pool[:] = found
    print(f"[POOL] {len(found)} proxies TCP-validated")
    return len(found)

def start_gost(port, upstream=None):
    subprocess.run(["pkill", "-f", f"gost.*:{port}"], capture_output=True)
    cmd = ["gost", "-L", f"http://:{port}"]
    if upstream:
        cmd += ["-F", upstream]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

def pick_and_assign(i, attempts=5):
    """Pick from pool, start gost, verify exit IP (limited curl calls to avoid OOM)"""
    port = WORKER_PORTS[i]
    with lock:
        pool = proxy_pool.copy()

    random.shuffle(pool)
    for item in pool[:attempts]:
        pnorm = item["raw"]
        proto = item["proxy_proto"]
        ip = test_exit_ip(pnorm, proto, timeout=6)
        if ip:
            start_gost(port, item["proxy"])
            with lock:
                current[i] = {"port": port, "proxy": item["proxy"], "ip": ip}
            print(f"[ASSIGN] worker {i + 1} port {port} -> {item['proxy']} (ip={ip})")
            return ip
    return None

def assign_or_refresh(i, attempts=8):
    ip = pick_and_assign(i, attempts)
    if not ip:
        refresh_pool(max_test=200)
        ip = pick_and_assign(i, attempts)
    return ip

def initial_setup():
    print("[SYS] Memuat proxy pool...")
    refresh_pool(max_test=250)

    for i in range(NUM_WORKERS):
        if not assign_or_refresh(i, attempts=6):
            print(f"[SYS] worker {i + 1} gagal mendapatkan proxy, coba lagi nanti")

@app.route('/status')
def status():
    with lock:
        workers = [{"worker": i + 1, **current.get(i, {"port": WORKER_PORTS[i], "proxy": None, "ip": None})} for i in range(NUM_WORKERS)]
        return jsonify({
            "status": "ok",
            "workers": workers,
            "pool_size": len(proxy_pool)
        })

@app.route('/rotate/<int:worker_id>')
def rotate(worker_id):
    idx = worker_id - 1
    if idx < 0 or idx >= NUM_WORKERS:
        return jsonify({"status": "error", "msg": f"Worker ID 1-{NUM_WORKERS}"}), 400
    print(f"[API] Rotasi worker {worker_id}")

    ip = assign_or_refresh(idx, attempts=8)
    if not ip:
        return jsonify({"status": "error", "msg": "Gagal mendapatkan proxy bekerja"}), 500

    with lock:
        info = current.get(idx)
    return jsonify({"status": "ok", "msg": f"Worker {worker_id} rotated", "worker": worker_id, "port": info["port"], "ip": info["ip"], "proxy": info["proxy"], "pool_size": len(proxy_pool)})

@app.route('/rotate_all')
def rotate_all():
    print("[API] Rotasi semua worker")
    results = []
    for i in range(NUM_WORKERS):
        ip = assign_or_refresh(i, attempts=6)
        with lock:
            info = current.get(i)
        results.append({"worker": i + 1, "ip": info.get("ip") if info else None})
    return jsonify({"status": "ok", "results": results})

@app.route('/refresh')
def refresh():
    with lock:
        proxy_pool.clear()
    n = refresh_pool(max_test=250)
    return jsonify({"status": "ok", "pool_size": n})

@app.route('/pool')
def pool():
    with lock:
        pool_data = [{"proxy": p["proxy"], "proto": p["proxy_proto"], "ip": p.get("ip")} for p in proxy_pool[:50]]
    return jsonify({"pool_size": len(proxy_pool), "sample": pool_data})

@app.route('/exit_ip/<int:worker_id>')
def exit_ip(worker_id):
    idx = worker_id - 1
    if idx < 0 or idx >= NUM_WORKERS:
        return jsonify({"status": "error", "msg": f"Worker ID 1-{NUM_WORKERS}"}), 400
    with lock:
        info = current.get(idx)
    return jsonify({"worker": worker_id, "ip": info.get("ip") if info else None, "port": info.get("port") if info else None})

@app.route('/proxy/<int:worker_id>/<path:url>')
def proxy_request(worker_id, url):
    idx = worker_id - 1
    if idx < 0 or idx >= NUM_WORKERS:
        return jsonify({"status": "error", "msg": f"Worker ID 1-{NUM_WORKERS}"}), 400
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    port = WORKER_PORTS[idx]
    proxy_url = f"http://127.0.0.1:{port}"
    proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        target_req = urllib.request.Request(url, method=request.method)
        for key, value in request.headers:
            if key.lower() not in ('host', 'connection', 'content-length'):
                target_req.add_header(key, value)
        body = request.get_data() if request.method in ('POST', 'PUT', 'PATCH') else None
        try:
            res = opener.open(target_req, body, timeout=30)
            data = res.read()
            headers = [(k, v) for k, v in res.headers.items() if k.lower() not in ('transfer-encoding', 'connection')]
            return Response(data, status=res.status, headers=headers)
        except urllib.error.HTTPError as e:
            data = e.read()
            headers = [(k, v) for k, v in e.headers.items() if k.lower() not in ('transfer-encoding', 'connection')]
            return Response(data, status=e.code, headers=headers)
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 502

# Auto-start pool loading saat module di-import (mis. oleh gunicorn)
threading.Thread(target=initial_setup, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
