# Proxy Gateway with 3 Workers

This application provides 3 SOCKS5 proxy ports (8081, 8082, 8083) that can be rotated.

## How to Use

### Via API:
- `/status` - Check status
- `/rotate/{worker_id}` - Rotate worker (1-3)

### Ports:
- Port 8081: Worker 1
- Port 8082: Worker 2  
- Port 8083: Worker 3

## Notes:
- Uses Flask for API
- GOST for SOCKS5 proxy
- Port 8080: Flask API
- TUN interface optional (may not work in all environments)