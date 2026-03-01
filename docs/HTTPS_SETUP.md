# HTTPS Setup Guide for Gizmo MY-AI

Two options are documented here: **Caddy** (recommended) and **Certbot + Nginx**.

---

## Option A — Caddy (Recommended)

Caddy automatically handles TLS certificate provisioning and renewal via
Let's Encrypt.  No manual certificate management required.

### Install

```bash
sudo dnf install caddy
```

### Configure — `/etc/caddy/Caddyfile`

```caddyfile
gizmohub.ai {
    reverse_proxy localhost:7860

    header {
        X-Frame-Options SAMEORIGIN
        X-Content-Type-Options nosniff
        Referrer-Policy strict-origin-when-cross-origin
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        -Server
    }

    log {
        output file /var/log/caddy/gizmohub.log
        format json
    }
}
```

### Start

```bash
sudo systemctl enable --now caddy
```

Caddy will automatically obtain a certificate on first request.

---

## Option B — Certbot + Nginx

### Install

```bash
sudo dnf install nginx certbot python3-certbot-nginx
```

### Obtain Certificate

```bash
sudo certbot --nginx -d gizmohub.ai -d www.gizmohub.ai
```

### Nginx Config — `/etc/nginx/conf.d/gizmohub.conf`

```nginx
server {
    listen 443 ssl http2;
    server_name gizmohub.ai www.gizmohub.ai;

    ssl_certificate     /etc/letsencrypt/live/gizmohub.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gizmohub.ai/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers (no CSP — Gradio uses inline scripts)
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy strict-origin-when-cross-origin;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # WebSocket support (required for Gradio streaming)
    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name gizmohub.ai www.gizmohub.ai;
    return 301 https://$host$request_uri;
}
```

### Start

```bash
sudo systemctl enable --now nginx
```

### Auto-renew

Certbot installs a systemd timer automatically.  Verify:

```bash
sudo systemctl status certbot-renew.timer
```

---

## Verify HTTPS

```bash
curl -I https://gizmohub.ai
# Expected: HTTP/2 200 (or 302 redirect to login)

# Check certificate details
echo | openssl s_client -connect gizmohub.ai:443 2>/dev/null | openssl x509 -noout -dates
```

---

## Security Notes

- **No Content-Security-Policy** is set because Gradio uses inline scripts and
  WebSocket connections that a strict CSP would block.
- Direct access to port 7860 is blocked by the firewall (see `DOMAIN_SETUP.md`).
- All secrets live in `user_data/google_oauth.env` (gitignored).
