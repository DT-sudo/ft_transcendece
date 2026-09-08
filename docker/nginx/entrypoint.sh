#!/bin/sh
# Generate a self-signed certificate on first boot, then start nginx.
#
# A self-signed cert is the right call for a local evaluation environment: it
# gives real TLS with no external dependency. The browser will warn once about
# the unknown issuer — that is expected, and the connection is still encrypted.
set -eu

CERT_DIR=/etc/nginx/certs
CERT="$CERT_DIR/planshift.crt"
KEY="$CERT_DIR/planshift.key"

mkdir -p "$CERT_DIR"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    # The alpine image ships the OpenSSL library but not always the CLI.
    if ! command -v openssl >/dev/null 2>&1; then
        echo "==> Installing openssl"
        apk add --no-cache openssl >/dev/null
    fi

    echo "==> Generating self-signed TLS certificate"
    openssl req -x509 -nodes -newkey rsa:2048 \
        -days 365 \
        -keyout "$KEY" \
        -out "$CERT" \
        -subj "/C=CZ/O=PlanShift/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:planshift.local,IP:127.0.0.1" \
        2>/dev/null
    chmod 600 "$KEY"
fi

# The HTTP->HTTPS redirect needs the port the proxy is published on, which only
# compose knows, so the config is templated rather than hard-coded.
export HTTPS_PORT="${HTTPS_PORT:-8443}"
envsubst '${HTTPS_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "==> Starting nginx (TLS on 443)"
exec nginx -g 'daemon off;'
