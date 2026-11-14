FROM alpine:latest

# Install dependensi
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update && apk add --no-cache \
    openvpn curl bash python3 py3-pip coreutils socat

# Download gost (Proxy yang mendukung interface binding)
RUN wget -q https://github.com/ginuerzh/gost/releases/download/v3.0.0/gost-linux-amd64-3.0.0.gz \
    && gunzip gost-linux-amd64-3.0.0.gz \
    && mv gost-linux-amd64-3.0.0 /usr/local/bin/gost \
    && chmod +x /usr/local/bin/gost

# Install Flask
RUN pip3 install --break-system-packages flask

COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Buka port API dan 6 port Proxy
EXPOSE 8000 8080 8081 8082 8083 8084 8085

CMD ["/start.sh"]
