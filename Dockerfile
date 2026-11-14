FROM alpine:latest

# Aktifkan repo edge untuk microsocks & install dependensi
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update && apk add --no-cache \
    openvpn curl bash microsocks python3 py3-pip coreutils

# Install Flask untuk API
RUN pip3 install --break-system-packages flask

COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Port 8080 untuk Proxy, Port 8000 untuk API
EXPOSE 8080 8000

CMD ["/start.sh"]
