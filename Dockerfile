FROM alpine:latest

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update && apk add --no-cache \
    curl bash python3 py3-pip coreutils socat

RUN wget -q https://github.com/go-gost/gost/releases/download/v3.0.0/gost_3.0.0_linux_amd64.tar.gz \
    && tar -xzf gost_3.0.0_linux_amd64.tar.gz \
    && mv gost /usr/local/bin/gost \
    && chmod +x /usr/local/bin/gost \
    && rm gost_3.0.0_linux_amd64.tar.gz

RUN pip3 install --break-system-packages flask gunicorn

COPY app.py /app.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080 8081 8082 8083 8084 8085 8086

CMD ["/start.sh"]
