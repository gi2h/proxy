FROM alpine:latest

# Aktifkan repositori testing untuk microsocks & install dependensi
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update && apk add --no-cache \
    python3 py3-pip openvpn curl bash microsocks coreutils iproute2 socat

# Install Flask untuk API
RUN pip3 install --break-system-packages flask

COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Port 8080-8085 untuk Proxy (6 Worker)
EXPOSE 8080 8081 8082 8083 8084 8085
# Port 8000 untuk API
EXPOSE 8000

CMD ["/start.sh"]
