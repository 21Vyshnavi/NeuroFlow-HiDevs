#!/usr/bin/env bash
# =============================================================================
# gen_certs.sh — Generate self-signed TLS certificate for local/dev Nginx
# For production, replace with Let's Encrypt certs via Certbot:
#   certbot certonly --standalone -d yourdomain.com
#   Then update nginx.conf to point to /etc/letsencrypt/live/yourdomain.com/
# =============================================================================
set -euo pipefail

CERT_DIR="$(dirname "$0")/nginx/certs"
mkdir -p "$CERT_DIR"

echo "Generating self-signed TLS certificate in $CERT_DIR ..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out    "$CERT_DIR/server.crt" \
    -subj   "/C=US/ST=Local/L=Local/O=NeuroFlow/CN=localhost"

chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo "Done! Cert files:"
echo "  Certificate : $CERT_DIR/server.crt"
echo "  Private key : $CERT_DIR/server.key"
echo ""
echo "To use Let's Encrypt in production, update infra/nginx/nginx.conf:"
echo "  ssl_certificate     /etc/letsencrypt/live/<domain>/fullchain.pem;"
echo "  ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;"
