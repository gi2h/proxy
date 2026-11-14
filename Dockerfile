FROM alpine:latest AS microsocks-build
RUN apk add --no-cache build-base git
RUN git clone --depth 1 https://github.com/rofl0r/microsocks /src \
    && make -C /src \
    && install -m 0755 /src/microsocks /usr/local/bin/microsocks

FROM alpine:latest

# Install dependensi: Python, OpenVPN, Curl, Bash
RUN apk add --no-cache python3 py3-pip openvpn curl bash coreutils

# Binary Microsocks (dibuild dari source)
COPY --from=microsocks-build /usr/local/bin/microsocks /usr/local/bin/microsocks

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
