FROM alpine:latest

# Install dependensi: Python, OpenVPN, Curl, Bash, Microsocks
RUN apk add --no-cache python3 py3-pip openvpn curl bash microsocks coreutils

# Install Flask untuk API Server
RUN pip3 install --break-system-packages flask

# Copy script ke dalam container
COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Buka 2 Port: 
# 8080 = SOCKS5 Proxy
# 8000 = API Server
EXPOSE 8080 8000

CMD ["/start.sh"]
