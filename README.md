# Gi2H Proxy Gateway — 6 Workers, Multi-IP

Sistem proxy dengan **6 worker** (port internal 8081–8086), masing-masing lewat
**upstream proxy berbeda** sehingga keluar dengan **IP berbeda**, dan bisa
**dirotasi on-demand** kapan saja. Dibangun dengan **GOST** + **Flask** + **Gunicorn**.

## Arsitektur

```
Client
  │  HTTPS
  ▼
Port 8080 (Gunicorn/Flask)  ← satu-satunya port publik
  │  /proxy/<worker_id>/<url>   → reverse-proxy lewat worker tsb
  │  /rotate/<id>, /status, ... → kontrol API
  ▼
6× GOST (port 8081–8086)  ← masing-masing forward ke upstream proxy berbeda
  │
  ▼
Proxy pool (list publik gratis, divalidasi TCP)
```

- Karena Railway/Render/Fly hanya membuka **satu port publik**, akses proxy
  lewat route `/proxy/<worker_id>/<url>` (HTTP method apa pun diteruskan).
- Pool proxy diambil dari list publik (proxyscrape + GitHub), divalidasi dengan
  **TCP connect ringan** (bukan curl massal) supaya tidak kena flag abuse.
- TUN/OpenVPN **tidak dipakai** (tidak didukung di container cloud tanpa
  `/dev/net/tun`).

## Endpoint

| Endpoint | Fungsi |
|---|---|
| `GET /status` | Status semua worker + IP keluar masing-masing |
| `GET /pool` | Isi proxy pool yang tervalidasi |
| `GET /rotate/<id>` | Ganti IP worker `id` (1–6) |
| `GET /rotate_all` | Ganti IP semua worker |
| `GET /refresh` | Ambil & validasi ulang proxy pool |
| `GET /exit_ip/<id>` | Cek IP keluar worker `id` |
| `GET /proxy/<id>/<url>` | Request lewat worker `id` (IP worker tsb) |

Contoh:
```bash
curl https://<domain>/status
curl https://<domain>/rotate/3
curl https://<domain>/proxy/1/https://httpbin.org/ip
```

## Konfigurasi (env)

| Var | Default | Keterangan |
|---|---|---|
| `PORT` | `8080` | Port API publik (wajib di Render/Fly) |
| `PROXY_PORTS` | `8081,8082,8083,8084,8085,8086` | Port worker internal |

## Deploy

### Render (gratis, login GitHub)
1. Buka https://render.com → **Sign in with GitHub** (akun pemilik repo `gi2h/proxy`)
2. **New +** → **Blueprint** → pilih repo `gi2h/proxy`
3. Render otomatis baca `render.yaml` → **Apply / Deploy**
4. Setelah hidup, cek: `https://proxy-xxxx.onrender.com/status`

> Catatan: tier Free sleep 15 menit tanpa request; bangun otomatis saat dipanggil
> (startup pool ~30–60 detik).

### Fly.io (login GitHub)
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# 2. Login (browser terbuka → pilih "Sign in with GitHub")
fly auth login

# 3. Deploy dari folder repo
cd proxy
fly deploy
```
App name di `fly.toml` (`gi2h-proxy`) harus unik global; kalau sudah dipakai,
ganti dulu di `fly.toml` atau biarkan flyctl menanyakannya saat `fly launch`.

> Catatan: Fly.io meminta data billing (kartu) saat signup, meski free allowance.

### Railway (kalau restriction sudah dicabut)
```bash
railway link        # pilih project
railway up -y
```
(`railway.toml` masih dipakai; migrasi ke `.railway/railway.ts` sebelum 2026-12-01.)

## Jalankan Lokal

```bash
pip3 install flask gunicorn
./start.sh          # atau: python3 app.py
```
Butuh `gost` + `curl` terinstal.

## Catatan

- Proxy gratis dari list publik **tidak stabil**; pool fluktuatif (1–10 valid
  dari 60 kandidat). Untuk IP stabil & banyak, pakai proxy berbayar/private.
- Scraping sengaja dibatasi (60 kandidat, 8 konkuren, jeda 0.7s) agar tidak
  kena flag abuse hosting.
