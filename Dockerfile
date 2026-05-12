FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_PYTHON=/usr/local/bin/python3.11

WORKDIR /app
COPY backend/pyproject.toml ./backend/
RUN cd backend && echo "3.11" > .python-version && uv sync --no-dev --python /usr/local/bin/python3.11

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Nginx escuta em 8080 (porta nao-privilegiada) para permitir USER nao-root.
# O host mapeia 4000:8080 no docker-compose.
RUN cat > /etc/nginx/sites-available/default << 'NGINX'
server {
    listen 8080;
    root /app/frontend/dist;
    index index.html;

    # Headers de seguranca
    add_header Content-Security-Policy "frame-ancestors 'self' https://inteia.com.br https://*.vercel.app" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # Ocultar versao do servidor
    server_tokens off;

    location / { try_files $uri $uri/ /index.html; }
    location /health/ {
        proxy_pass http://127.0.0.1:5001/health/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
    }
}
NGINX

# Aponta o nginx para escrever em /tmp (gravavel pelo usuario nao-root).
RUN sed -i 's|^pid .*|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf \
    && sed -i 's|^\(\s*\)access_log .*|\1access_log /dev/stdout;|' /etc/nginx/nginx.conf \
    && sed -i 's|^\(\s*\)error_log .*|\1error_log /dev/stderr;|' /etc/nginx/nginx.conf

RUN cat > /app/start.sh << 'SH'
#!/bin/bash
set -e

cd /app/backend
uv run --python python3.11 gunicorn \
  --bind "0.0.0.0:${FLASK_PORT:-5001}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-300}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app &
backend_pid=$!

sleep 2
nginx -g "daemon off;" &
nginx_pid=$!

trap 'kill -TERM "$backend_pid" "$nginx_pid" 2>/dev/null || true' TERM INT
wait -n "$backend_pid" "$nginx_pid"
exit_code=$?
kill -TERM "$backend_pid" "$nginx_pid" 2>/dev/null || true
wait "$backend_pid" "$nginx_pid" 2>/dev/null || true
exit "$exit_code"
SH
RUN chmod +x /app/start.sh

# Cria usuario nao-root e ajusta permissoes dos diretorios que nginx + gunicorn
# precisam escrever em runtime.
RUN groupadd --system --gid 10001 mirofish \
    && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin mirofish \
    && mkdir -p /var/lib/nginx/body /var/lib/nginx/proxy /var/lib/nginx/fastcgi /var/lib/nginx/uwsgi /var/lib/nginx/scgi \
    && chown -R mirofish:mirofish /app /var/lib/nginx /etc/nginx /tmp \
    && chmod -R u+rwX,g+rwX /var/lib/nginx /etc/nginx

USER mirofish

EXPOSE 8080 5001
CMD ["/app/start.sh"]
