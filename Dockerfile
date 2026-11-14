FROM alpine:latest

# Install dependensi build
RUN apk add --no-cache python3 py3-pip openvpn curl bash coreutils git make gcc musl-dev

# Build microsocks dari source
RUN git clone https://github.com/rofl0r/microsocks.git /tmp/microsocks && \
    cd /tmp/microsocks && \
    make && \
    cp microsocks /usr/local/bin/ && \
    rm -rf /tmp/microsocks

# Install Flask
RUN pip3 install --break-system-packages flask

# Copy script
COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080 8000
CMD ["/start.sh"]
