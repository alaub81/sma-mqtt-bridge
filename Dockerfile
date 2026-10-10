FROM alpine:3.24 AS builder

RUN apk add --no-cache \
    bash \
    g++ \
    make \
    mosquitto-dev \
    curl-dev \
    pkgconf

WORKDIR /build
COPY ./resources/src ./src
COPY --chmod=0755 ./resources/compile.sh ./scripts/compile.sh
RUN bash ./scripts/compile.sh

FROM alpine:3.24

RUN apk add --no-cache \
    bash \
    libstdc++ \
    mosquitto-libs \
    libcurl \
    ca-certificates \
    curl \
    jq \
    openssl

WORKDIR /app
COPY --chmod=0755 --from=builder /build/src/sma_mqtt_bridge /app/sma_mqtt_bridge
COPY --chmod=0755 ./resources/docker-entrypoint.sh .

ENV SMA_CONFIG_FILE=/app/config.json \
    SMA_STATE_DIR=/app/state

VOLUME ["/app/state"]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["/app/sma_mqtt_bridge"]
